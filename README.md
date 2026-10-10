# Hang

A real-time social discovery app: create a profile, swipe, match on mutual likes, and chat live.
Built as a demonstration of a horizontally scalable real-time backend: FastAPI behind nginx, several
stateless API replicas, WebSockets fanned out through Redis pub/sub, PostgreSQL, and a Prometheus and
Grafana monitoring stack, all running in Docker.

> **Demo video:** _coming soon_ <!-- DEMO_VIDEO_URL -->

Version 0.1.0 · [Changelog](./CHANGELOG.md) · [Load test report](./hang-backend/LOAD_TEST.md) · MIT

## Features

- **Auth:** email/password and Google OAuth, JWT in an HTTP-only cookie, 18+ enforced.
- **Profiles:** images (reorder, delete, up to 6), bio, country, interests, preferences.
- **Swipes:** like / pass / super like. The feed is scored by country, shared interests and preference,
  and returns up to 20 profiles at a time. A mutual like creates exactly one conversation.
- **Chat:** WebSocket rooms per conversation, typing indicators, read receipts, cursor-based message pagination.
- **Safety and account:** block, report, unblock, change password, delete account.
- **Operations:** shared rate limits, Prometheus metrics, Grafana dashboard, JSON logs, CI.

Google sign-ups start without a birthdate, so their feed is empty until they set one in their profile.

## Architecture

```text
                    Browser
                       │
                       ▼
              ┌─────────────────┐
              │      nginx      │  serves the React build, proxies /api, upgrades WebSockets
              └────────┬────────┘
                       │  api:8000 (Docker DNS, N replicas)
          ┌────────────┼────────────┐
          ▼            ▼            ▼
      ┌───────┐    ┌───────┐    ┌───────┐
      │ api-1 │    │ api-2 │    │ api-N │   stateless FastAPI: REST + WebSockets
      └───┬───┘    └───┬───┘    └───┬───┘
          └────────────┼────────────┘
        ┌──────────────┼──────────────────┐
        ▼              ▼                  ▼
   PostgreSQL     Redis                S3-compatible
   (data)         db0: pub/sub         object storage
                  db1: rate limits     (Cloudflare R2 / S3)

   Prometheus ──scrapes /metrics on every api replica──▶ Grafana
```

A message is persisted by the replica that receives it, then published to `conversation:<id>` in Redis.
Every replica subscribes to `conversation:*` and delivers to the sockets it holds in that room.

## Services

| Service | Container | Notes |
|---|---|---|
| nginx + React build | `hang-nginx` | Published on `localhost:8000` |
| API | `api` (scaled) | Not published; reached through nginx |
| PostgreSQL 16 | `hang-db-local` | Started by `start.sh`, not published |
| Redis 7 | `hang-redis-local` | Started by `start.sh`, not published |
| Prometheus | `hang-prometheus` | Not published |
| Grafana | `hang-grafana` | Published on `localhost:3000` |

All containers share the external Docker network `hang-network`.

## Tech stack

Backend: Python 3.11, FastAPI, SQLAlchemy 2, PostgreSQL, Redis, slowapi, Authlib, boto3, Pydantic.
Frontend: React 19, TypeScript, Vite, Tailwind CSS 4, React Router 7, Framer Motion, dnd-kit.
Infra: Docker, nginx, Prometheus, Grafana, GitHub Actions.

## Running locally

Requirements: Docker, plus Poetry and Node 22 if you want to run tests or the frontend dev server.

1. Clone:
```bash
   git clone https://github.com/Melsso/hang
   cd hang
```

2. Create the env files:
```bash
   cp hang-backend/.api.env.example hang-backend/.api_env
   cp hang-backend/.db.env.example infra/.db_env
```

3. Fill them in. When running through `start.sh`:

   | Variable | Value |
   |---|---|
   | `DB_HOST` | `hang-db-local` |
   | `DB_PORT` | `5432` |
   | `REDIS_HOST` | `hang-redis-local` |
   | `REDIS_PORT` | `6379` |
   | `DB_USER` / `DB_PASSWORD` / `DB_NAME` | must equal `POSTGRES_USER` / `POSTGRES_PASSWORD` / `POSTGRES_DB` in `infra/.db_env` |
   | `SECRET_KEY` | `openssl rand -hex 32` |
   | `COOKIE_SECURE` | `false` locally, `true` behind HTTPS |
   | `GOOGLE_REDIRECT_URI` | `http://localhost:8000/api/auth/login/google/callback` (register it in the Google console) |
   | `R2_*` | credentials for any S3-compatible bucket |

   The full list is in [hang-backend/README.md](./hang-backend/README.md#configuration).

4. Start with the number of API replicas you want:
```bash
   ./start.sh 3
```
   This creates the network, starts Redis and Postgres (building their images if needed), then builds and starts the compose stack.

5. Open:
   - App: http://localhost:8000
   - Grafana: http://localhost:3000 (default `admin` / `admin`; the Prometheus datasource and dashboard are provisioned)

6. Stop everything:
```bash
   ./stop.sh
```

Postgres has no volume by default. `stop.sh` only stops the containers, so data survives that, but removing
the `hang-db-local` container deletes it. To keep data across removals, add
`-v hang_postgres_data:/var/lib/postgresql/data` to the Postgres `docker run` in `start.sh`.

The schema is created with `create_all` on startup and there are no migrations. After a model change,
recreate the database container.

## Testing

```bash
cd hang-backend
poetry install
poetry run ruff check .
poetry run mypy .
poetry run pytest                 # unit tests (tests/), needs Docker for testcontainers
poetry run pytest smoke_tests     # infrastructure smoke tests, must run as a separate session
```

Frontend:

```bash
cd hang-frontend
npm ci
npm run lint
npm run build
```

## Load testing

The WebSocket layer was tested end to end through nginx, across three API replicas, with real Redis
fan-out and real Postgres writes. Delivery is counted only when the other participant in a conversation
receives the message.

**100% delivery across 190,000 messages at up to 2,000 concurrent connections, p99 under 111 ms.**
The test also found two real bugs. Methodology, results, caveats and reproduction steps are in
[hang-backend/LOAD_TEST.md](./hang-backend/LOAD_TEST.md).

## Project structure

```text
hang/
├── hang-backend/        FastAPI service, tests, load test tooling
├── hang-frontend/       React + TypeScript app
├── infra/
│   ├── nginx/           nginx image (builds the frontend) and config
│   ├── prometheus/      Prometheus image and scrape config
│   ├── grafana/         Grafana image, provisioning and dashboard
│   ├── Dockerfile.db    PostgreSQL image
│   └── Dockerfile.redis Redis image
├── .github/workflows/   backend-ci, frontend-ci, release
├── docker-compose.yml   nginx, api, prometheus, grafana
├── start.sh             creates network, Redis, Postgres, then the compose stack
├── stop.sh
├── CHANGELOG.md
└── LICENSE
```

## Known limitations

- nginx resolves `api:8000` once at startup. If the API containers are recreated with new addresses,
  restart nginx (`docker restart hang-nginx`).
- Access tokens last `ACCESS_TOKEN_EXPIRE_MINUTES` (30 by default) and there is no refresh flow.
- Delivery over Redis pub/sub is fire-and-forget: there are no acknowledgements or offline delivery.
- Single-host Docker deployment only; there is no cloud deployment.

## License

MIT, see [LICENSE](./LICENSE).