# Hang Backend

Stateless FastAPI service providing the REST API and the WebSocket endpoint. Any number of replicas can
run behind the ingress controller. The API only connects to PostgreSQL and never creates schema.

## Components

| Component | Purpose |
|---|---|
| FastAPI | REST and WebSockets |
| SQLAlchemy 2 + PostgreSQL | Persistent data (schema from `infra/init.sql`, no migrations) |
| Redis db 0 | Pub/sub for real-time events |
| Redis db 1 | Rate limit counters (shared by all replicas) |
| JWT (python-jose) | Auth, stored in an HTTP-only cookie |
| Authlib | Google OAuth |
| boto3 | S3-compatible image storage (Cloudflare R2 / S3) |
| prometheus-fastapi-instrumentator | `/metrics` |

## Layout

```text
hang-backend/
├── src/hang/
│   ├── core/        app factory, database, middleware, limits, logging, oauth, redis, startup, storage
│   ├── helpers/     business logic: auth, users, swipes, conversations, messages, settings, ws
│   ├── models/      SQLAlchemy models
│   ├── routes/      auth, users, swipes, conversations, settings, ws, health
│   ├── schemas/     Pydantic schemas and settings
│   └── main.py
├── tests/
│   ├── unit_tests/         unit tests (testcontainers Postgres and Redis)
│   └── integration_tests/  infrastructure wiring tests (testcontainers + in-process S3 via moto)
├── dev_utils/       load test seed and client, demo seed
├── Dockerfile.hang      API image (multi-stage, non-root)
├── Dockerfile.loadtest  load test and demo seed image
├── LOAD_TEST.md
├── logging.json
└── pyproject.toml
```

## API

All routes are under `/api`, except the health and metrics endpoints. Authenticated routes read the
`access_token` cookie.

| Area | Endpoints |
|---|---|
| Auth | `GET /auth/session`, `POST /auth/register`, `POST /auth/login`, `POST /auth/logout`, `GET /auth/login/google`, `GET /auth/login/google/callback` |
| Users | `GET /users/profile`, `POST /users/profile`, `GET /users/profile/{user_id}` (matched users only), `POST /users/profile/upload-image`, `POST /users/profile/block`, `POST /users/profile/report-create` |
| Swipes | `GET /swipes/home` (up to 20 scored profiles), `POST /swipes/swipe-action` (`like`, `pass`, `super_like`) |
| Conversations | `GET /conversations`, `GET /conversations/{id}/messages?before_message_id=`, `POST /conversations/delete/{id}`, `GET /conversations/notifications` |
| Settings | `GET /settings/blocks`, `POST /settings/unblock`, `GET /settings/reports`, `POST /settings/report-delete`, `POST /settings/change-password`, `POST /settings/delete-account` |
| WebSocket | `/ws/conversations` |
| Health | `GET /health`, `GET /ready` (root, not under `/api`, not routed by the ingress) |
| Metrics | `GET /metrics` (root, not under `/api`) |

Google sign-in requires a verified email. It refuses to sign in to an existing password account, and a refused
sign-in redirects to `/login?error=google`.

### Health endpoints

| Endpoint | Used for | Checks |
|---|---|---|
| `/health` | liveness | The process responds, and the `redis_subscriber` and `ws_heartbeat` background tasks are still running. Returns 503 with the names of any dead tasks. |
| `/ready` | startup and readiness | PostgreSQL reachable with the `users` table present (2 s timeout), and Redis answers `PING` (1 s timeout). Returns 503 with per-check results otherwise. |

Neither endpoint is counted in metrics or written to the request log.

### Rate limits

Defined in `core/limits.py`. Authenticated requests are keyed by user id, anonymous ones by client IP.
Counters live in Redis, so limits are shared across replicas.

| Tier | Limit | Used for |
|---|---|---|
| `AUTH` | 5/min | login, register, Google OAuth, change password |
| `WRITE` | 15/min | profile updates, uploads, block, report, unblock, delete conversation, logout |
| `FREQUENT` | 60/min | reads, feed, swiping, messages, session |
| `DELETE_ACCOUNT` | 1/min | delete account |

### WebSocket protocol

Connect to `/api/ws/conversations` with the auth cookie. Unauthenticated connections are rejected
before `accept()` (close code 1008).

Server to client:

| Frame | Meaning |
|---|---|
| `{"type":"ready"}` | The socket is registered in all its rooms; safe to send |
| `{"type":"ping"}` | Reply with `{"type":"pong"}`; sockets silent for 60 s are closed (1001) |
| `{"type":"message","message":{...,"conversation_id":N}}` | New message |
| `{"type":"typing","conversation_id":N,"user_id":N,"is_typing":bool}` | Typing state |
| `{"type":"read","conversation_id":N,"user_id":N}` | Messages read |
| `{"type":"error","conversation_id":N,"reason":"conversation_unavailable"}` | Send rejected (blocked or deleted) |
| `{"type":"match","conversation_id":N,"user_id":N,"name":"..."}` | Travels on the per-user Redis channel and is not queued |

Client to server (all except `pong` require `conversation_id`):

```json
{"conversation_id": 1, "content": "hello"}
{"type": "typing", "conversation_id": 1, "is_typing": true}
{"type": "read", "conversation_id": 1}
{"type": "pong"}
```

Content must be a non-empty string of at most 1000 characters. Malformed frames are ignored. Messaging a
conversation the socket doesn't belong to closes it (1008).

Redis pub/sub does not replay, so a client that was disconnected can miss events. Clients should refetch
state after reconnecting; the frontend does this.

## Configuration

Read from the environment or `.api.env` in the working directory. In Kubernetes they are injected from each
overlay's `api.env` and `api.secret.env`, which `scripts/setup-env.sh` generates.

| Variable | Description |
|---|---|
| `DB_USER` `DB_PASSWORD` `DB_NAME` `DB_HOST` `DB_PORT` | PostgreSQL connection |
| `DB_POOL_SIZE` `DB_MAX_OVERFLOW` | Connection pool per replica (defaults 5 and 5) |
| `REDIS_HOST` `REDIS_PORT` | Redis connection |
| `SECRET_KEY` `ALGORITHM` `ACCESS_TOKEN_EXPIRE_MINUTES` | JWT signing and lifetime |
| `COOKIE_SECURE` | `Secure` flag on the auth cookie (default `false`) |
| `MAX_IMAGES` `MAX_IMAGE_SIZE` `ALLOWED_IMAGE_TYPES` | Upload limits (`ALLOWED_IMAGE_TYPES` is comma separated) |
| `R2_ACCESS_KEY_ID` `R2_SECRET_ACCESS_KEY` `R2_BUCKET_NAME` `R2_ENDPOINT` | S3-compatible storage |
| `GOOGLE_CLIENT_ID` `GOOGLE_CLIENT_SECRET` `GOOGLE_REDIRECT_URI` | Google OAuth |
| `RATE_LIMIT_STORAGE_URI` | Optional override, mainly for tests (`memory://`). Defaults to Redis db 1 |

Each replica can open up to `DB_POOL_SIZE + DB_MAX_OVERFLOW` connections, so the total across replicas
must stay below the Postgres `max_connections`.

## Running

Normally through the root `start.sh` (see the root README). To run the API directly, you need Postgres with
`infra/init.sql` applied, Redis, and a populated `.api.env`:

```bash
poetry install
poetry run uvicorn hang.main:app --reload --app-dir src
```

## Testing

```bash
poetry run ruff check .
poetry run mypy .
poetry run pytest tests/unit_tests          # needs Docker
poetry run pytest tests/integration_tests   # separate session, needs Docker
```

Unit tests use Postgres and Redis from testcontainers. Integration tests use the same plus an in-process S3
server (moto). Do not run both suites in one pytest session: the integration tests configure the environment
before the app is imported, and the unit tests import it earlier.

## Load testing

`scripts/loadtest.sh <env>` builds `Dockerfile.loadtest` and runs the seed script and client as a Kubernetes
Job in the target namespace. See [LOAD_TEST.md](./LOAD_TEST.md).

## Design notes

- **Statelessness:** replicas share nothing except Postgres, Redis and object storage.
- **Connect-only startup:** the API never creates schema. `/ready` reports not-ready until the database
  answers and the `users` table exists, so a pod started before the schema is applied gets no traffic.
- **Probe split:** liveness checks only the process and its background tasks. Redis and Postgres belong to
  readiness, so a dependency outage removes pods from service instead of restarting all of them.
- **Event loop discipline:** synchronous DB work on the WebSocket path runs in worker threads; sessions are
  acquired per operation, never held for a socket's lifetime.
- **Join before accept:** authentication and room lookup happen before `accept()`, and a `ready` frame
  confirms registration.
- **Authorization at send time:** blocks and deleted conversations are checked per message.
- **Idempotent swipes:** a unique swipe pair and a unique conversation pair (order-independent index)
  make duplicate and concurrent requests safe.
- **Account linking:** Google sign-in never converts an existing password account, because registration does
  not verify emails and a pre-registered password would otherwise survive the takeover.
- **Image:** multi-stage build with a pinned Poetry version. The runtime image has no build tools and runs as
  UID 10001; the Kubernetes pod spec enforces `runAsNonRoot`, drops all capabilities and uses the
  `RuntimeDefault` seccomp profile.
- **Observability:** structured JSON logs with request ids, Prometheus metrics, and a gauge of open
  WebSockets per replica.