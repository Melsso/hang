# Hang

A real-time social discovery app: create a profile, swipe, match on mutual likes, and chat live.
Built as a demonstration of a horizontally scalable real-time backend: stateless FastAPI replicas behind an
ingress controller, WebSockets fanned out through Redis pub/sub, PostgreSQL, and Prometheus and Grafana
monitoring, deployed to Kubernetes (kind) in three environments.

Version 0.2.0 · [Changelog](./CHANGELOG.md) · [Load test report](./hang-backend/LOAD_TEST.md) · MIT

## Demo

https://github.com/user-attachments/assets/f6411c14-d90f-4967-961b-bea334b05726

## Features

- **Auth:** email/password and Google OAuth, JWT in an HTTP-only cookie, 18+ enforced. Google sign-in requires
  a verified email and never takes over an existing password account.
- **Profiles:** images (reorder, delete, up to 6), bio, country, interests, preferences.
- **Swipes:** like / pass / super like. The feed is scored by country, shared interests and preference,
  and returns up to 20 profiles at a time. A mutual like creates exactly one conversation.
- **Match notifications:** a match overlay for the person who completes the match; the other person gets
  a live toast if they are on the Conversations page, and a dot on Conversations (plus a "New match"
  pill) until they open it. Nothing is queued: the state lives on the conversation.
- **Chat:** WebSocket rooms per conversation, typing indicators, read receipts, cursor-based message pagination.
  The client reconnects with backoff and refetches state after every reconnect.
- **Safety and account:** block, report, unblock, change password, delete account.
- **Operations:** shared rate limits, health and readiness endpoints, Prometheus metrics, Grafana dashboard,
  JSON logs, CI.

Google sign-ups start without a birthdate, so their feed is locked (with a "Please complete your
profile" toast) until they set one in their profile.

## Architecture

```text
                      Browser
                         │  https://<env>.localtest.me:8443
                         ▼
          ┌─────────────────────────────┐
          │  ingress-nginx (kind)       │  TLS with a local mkcert wildcard certificate
          └──────┬──────────────┬───────┘
                 │ /            │ /api (REST + WebSockets)
                 ▼              ▼
          ┌──────────┐   ┌───────────────────────────┐
          │ frontend │   │ api-1 … api-N (stateless) │
          │ (nginx)  │   └─────┬──────────┬──────────┘
          └──────────┘         │          │          │
                               ▼          ▼          ▼
                         PostgreSQL     Redis    S3-compatible
                         (data)         db0: pub/sub    object storage
                                        db1: rate limits (Cloudflare R2 / S3)

   Prometheus ── pod discovery in dev, qa, prod ──▶ Grafana   (monitoring namespace)
```

A message is persisted by the replica that receives it, then published to `conversation:<id>` in Redis.
Every replica subscribes to `conversation:*` and `user:*` and delivers to the sockets it holds. Match
events use the per-user channel, so they reach the right user on whichever replica holds their socket.

PostgreSQL, Redis and object storage run **outside** the cluster, by design: the cluster holds stateless
workloads and the data lives elsewhere, the way a managed database would be used. Postgres and Redis run as
Docker containers on the `kind` Docker network.

## Environments

One cluster (1 control-plane node and 3 workers), three namespaces. Kustomize overlays in `k8s/overlays/`
set the differences.

| Env | URL | API / frontend replicas | Nodes | Postgres container | Database | Redis container |
|---|---|---|---|---|---|---|
| dev | https://dev.localtest.me:8443 | 2 / 1 | shared pool | `hang-db` | `hang_dev` | `hang-redis-dev` |
| qa | https://qa.localtest.me:8443 | 2 / 1 | shared pool | `hang-db` | `hang_qa` | `hang-redis-qa` |
| prod | https://prod.localtest.me:8443 | 3 / 2 | dedicated prod node | `hang-db-prod` | `hang_prod` | `hang-redis-prod` |

- `*.localtest.me` resolves to 127.0.0.1, so no hosts file changes are needed.
- The prod node is tainted and labelled `hang/pool=prod`, and only prod pods tolerate it. This isolates
  compute, so dev and qa load cannot starve prod. It is not high availability: the prod pool is one node.
- Each environment has its own API secret, Redis and bucket. Use a separate storage bucket per environment,
  because image keys are `users/<id>/...` and would collide.

Other cluster components, all in `k8s/`: `base/` (api and frontend deployments, services, ingress),
`monitoring/` (Prometheus, Grafana) and `overlays/`.

### Health checks

| Endpoint | Probe | Checks |
|---|---|---|
| `/health` | liveness | The process responds and the Redis subscriber and WebSocket heartbeat tasks are still running. |
| `/ready` | startup and readiness | PostgreSQL reachable with the `users` table present, and Redis answers `PING`. |

Neither depends on a dependency in liveness, so a database or Redis outage does not restart every pod.
Both sit at the root, are not routed by the ingress, and are excluded from metrics and request logs.

## Tech stack

Backend: Python 3.11, FastAPI, SQLAlchemy 2, PostgreSQL, Redis, slowapi, Authlib, boto3, Pydantic.
Frontend: React 19, TypeScript, Vite, Tailwind CSS 4, React Router 7, Framer Motion, dnd-kit.
Infra: Docker, Kubernetes (kind, Kustomize, ingress-nginx), Prometheus, Grafana, GitHub Actions.

## Running locally

Requirements: Docker, [kind](https://kind.sigs.k8s.io/), kubectl, [mkcert](https://github.com/FiloSottile/mkcert)
and openssl. On macOS: `brew install kind kubectl mkcert`. Poetry and Node 22 are needed only to run tests or
the frontend dev server.

1. Clone:
```bash
   git clone https://github.com/Melsso/hang
   cd hang
```

2. Start one or more environments (default `dev`):
```bash
   ./start.sh            # dev
   ./start.sh dev qa     # several
```
   The script generates missing env files (asking once for storage and Google values, both optional),
   starts Postgres and Redis, creates the databases and applies `infra/init.sql`, builds both images,
   creates the cluster with ingress and TLS, loads the images, deploys the overlays and the monitoring stack,
   and waits for the rollouts. `mkcert -install` may ask for your password once.

3. Open:
   - App: https://dev.localtest.me:8443 (or `qa` / `prod`)
   - Grafana: https://grafana.localtest.me:8443

   Grafana allows anonymous viewing, and you can log in as `admin` / `admin` to edit. This is acceptable
   because the cluster only listens on 127.0.0.1. The host port defaults to 8443; set `HTTPS_PORT` to change
   it, and update the Google redirect URIs to match.

4. Stop:
```bash
   ./stop.sh            # deletes the cluster, stops Postgres and Redis (data is kept)
   ./stop.sh --purge    # also removes those containers and their data
```

Running `./start.sh` again rebuilds the images and restarts the deployments, so code changes show up. It never
reinitialises a database that already has the schema.

### Configuration

`scripts/setup-env.sh` generates these gitignored files from the committed `*.example` templates:
`infra/.db.dev.env`, `infra/.db.prod.env`, and `api.env` and `api.secret.env` in each overlay. It skips files
that exist; `--force` regenerates the API files (new `SECRET_KEY`, which invalidates sessions). Database
credentials are never regenerated, because Postgres only reads them when a container is first created. If a
database container rejects the user, recreate it with `./stop.sh --purge`.

Without storage values, the app runs but picture uploads fail. Without Google values, email and password login
still works. The variable list is in [hang-backend/README.md](./hang-backend/README.md#configuration).

### Schema

There are no migrations, deliberately: the schema is fixed for this project. `infra/init.sql` is the only
source of truth, applied by `start.sh` to any database that lacks the `users` table. The API only connects
and never creates tables. After a model change, regenerate the file with
`pg_dump --schema-only --no-owner --no-privileges` and recreate the database.

## Demo data

```bash
scripts/seed-demo.sh dev
```

Creates two demo accounts (`jake@hang-demo.com` and `sam@hang-demo.com`, password `demo-password-123`) and
twelve more profiles to fill the feed. Five of them have already liked both demo accounts, so liking them back
produces an instant match. Pictures come from `hang-backend/dev_utils/resources/male` and `.../female` (you
provide them; one per user) and are uploaded to that environment's storage bucket, so this needs real storage
values. The script is re-runnable: it deletes the previous demo users first.

To use two accounts at once, log in from two different browsers (or a normal and a private window), since
the session is a cookie shared by all windows of one browser profile.

## Testing

```bash
cd hang-backend
poetry install
poetry run ruff check .
poetry run mypy .
poetry run pytest tests/unit_tests          # needs Docker for testcontainers
poetry run pytest tests/integration_tests   # must run as a separate session
```

Frontend:

```bash
cd hang-frontend
npm ci
npm run format:check
npm run lint
npm test
npm run build
```

CI (`.github/workflows/`) runs backend and frontend checks, renders every Kustomize overlay, deploys the dev
overlay to a kind cluster and runs `scripts/smoke_test.py` through the ingress (two users match, and one
WebSocket message is delivered). Pushing a `v*` tag creates a GitHub release and publishes the backend and
frontend images to GHCR.

## Load testing

The WebSocket layer was tested through the ingress controller in the `prod` environment, across three API
replicas, with real Redis fan-out and real Postgres writes. Delivery is counted only when the other
participant in a conversation receives it. The run delivered all 190,000 messages at up to 2,000 concurrent
connections, with p99 latency of 551.9 ms at the 2,000-connection level. Methodology, environment, results,
limitations and reproduction steps are in [hang-backend/LOAD_TEST.md](./hang-backend/LOAD_TEST.md).

```bash
scripts/loadtest.sh prod
```

## Project structure

```text
hang/
├── hang-backend/        FastAPI service, tests, load test and demo seed tooling
├── hang-frontend/       React + TypeScript app, its tests, Dockerfile and nginx config
├── infra/               init.sql (database schema) and generated database env files
├── k8s/
│   ├── base/            API and frontend deployments, services, ingress
│   ├── overlays/        dev, qa, prod (replicas, resources, node placement, secrets)
│   ├── monitoring/      Prometheus and Grafana
│   └── loadtest/        load test Job template
├── scripts/             cluster-up, setup-env, loadtest, seed-demo, smoke_test, shared lib
├── .github/workflows/   backend-ci, frontend-ci, k8s-ci, release
├── start.sh             one command from a clean checkout to running environments
├── stop.sh
├── CHANGELOG.md
└── LICENSE
```

## Known limitations

- **Local only.** The cluster is kind on one machine. There is no cloud deployment.
- **Prod isolation is not high availability.** One dedicated node, no failover.
- **Postgres and Redis have no backups or named volumes.** `./stop.sh` keeps the containers and their data;
  removing them deletes it.
- **Delivery over Redis pub/sub is fire-and-forget.** There are no acknowledgements and no offline delivery.
  Match events for offline users are not queued; they see the dot on their next page load. After a
  reconnect, the client refetches the conversation list and the open conversation to catch up.
- Access tokens last `ACCESS_TOKEN_EXPIRE_MINUTES` (30 by default) and there is no refresh flow. An expired
  session redirects to the login page.
- The notification dot refreshes on navigation. Only the Conversations page holds a WebSocket.
- Grafana is anonymous-viewer by default, which is only safe because the cluster listens on loopback.

## License

MIT, see [LICENSE](./LICENSE).