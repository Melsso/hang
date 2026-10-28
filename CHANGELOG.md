# Changelog

All notable changes to this project are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).


## [0.2.0] - 28.10.2026

### Added
- `/health` (liveness) and `/ready` (readiness) endpoints, wired into startup, readiness and liveness probes.
- `infra/init.sql` as the single source of the database schema, applied by `start.sh`.
- WebSocket reconnect with exponential backoff and jitter, and a resync of conversations after each reconnect.
- `DB_POOL_SIZE` and `DB_MAX_OVERFLOW` settings with defaults.
- `.dockerignore` files for the frontend and backend.
- `scripts/setup-env.sh`, `scripts/cluster-up.sh` and `scripts/lib.sh`, called by `start.sh` to provision env files, the cluster, ingress and TLS.
- Kubernetes base manifests (API and frontend deployments, services, ingress) and dev, qa and prod overlays with their own configuration, scaling and secrets.
- Kubernetes monitoring: Prometheus and Grafana with pod discovery across the three environments.
- `scripts/loadtest.sh` and `k8s/loadtest/job.yml.tmpl`: the load test as an in-cluster Job.
- `scripts/seed-demo.sh` for demo data.
- Kubernetes CI workflow that renders every overlay, deploys dev to kind and runs `scripts/smoke_test.py`.
- Frontend test step in CI.
- GHCR image publishing for backend and frontend on version tags.

### Changed
- Moved unit tests under `tests/unit_tests` and `smoke_tests` to `tests/integration_tests`; updated backend CI.
- Frontend Dockerfile and nginx config now live in `hang-frontend`.
- Prometheus and Grafana moved from Docker to Kubernetes.
- Rewrote `start.sh` and `stop.sh` around the new infrastructure.
- API image is multi-stage, pins Poetry and runs as a non-root user.
- Google sign-in requires a verified email and no longer converts an existing password account.
- Prod pods are pinned to a tainted node pool and dev/qa to the shared pool.
- Postgres starts with `max_connections=200`.
- Load test runs inside the cluster; `LOAD_TEST.md` rewritten with new results.

### Fixed
- Expired sessions redirected without explanation; all API calls now go through `apiFetch`, which redirects to login with a message.
- Missing colon in the frontend deployment's memory limit.
- `.api.env.example` contained Python instead of an env value.

### Removed
- The API no longer creates database tables; it only connects, with retry.
- `infra/nginx` (config and frontend Dockerfile), the Docker Compose setup, `k8s/kind-config.yml`, `infra/.db.env.example`, and the `infra/grafana` and `infra/prometheus` directories.
- `dev_utils/run_loadtest.sh`, `dev_utils/run_demo_seed.sh` and the `--purge-loadtest` option.


## [0.1.0] - 2026-10-10

First tagged version.

### Added
- Email/password and Google OAuth authentication with HTTP-only cookie sessions.
- Profiles with images (drag to reorder, delete), interests, country and preferences.
- Swipe feed (like / pass / super like), scored by country, shared interests and preference, capped at 20 profiles per fetch.
- Matching on mutual likes, with a unique conversation per user pair.
- Match notifications: a match overlay for the swiper, a live toast and "New match" pill for the other user when online, and a dot on Conversations for new matches and unread messages (stored per conversation, nothing is queued).
- Real-time messaging over WebSockets: rooms per conversation, typing indicators, read receipts, cursor-based pagination.
- Redis pub/sub fan-out so any API replica can deliver to any connected client, including per-user channels (`user:<id>`) for match events.
- WebSocket heartbeat (ping/pong), stale-socket eviction, and a `ready` frame sent once a socket is registered in its rooms.
- Block, report, unblock, change password and delete account.
- Frontend route guards backed by `/api/auth/session`, and a "Please complete your profile" toast when the feed is locked.
- Shared tiered rate limits (`core/limits.py`) stored in Redis, keyed by user id or client IP.
- Prometheus metrics, a Grafana dashboard (request rate, p95 latency, 5xx rate, open WebSockets) and structured JSON logs.
- Load test tooling that runs inside the Docker network, with a readiness handshake and server error frame counting.
- Demo seed script (`dev_utils/demo_seed.py`) that creates two demo accounts and a populated feed with pictures.
- Backend unit tests, smoke tests (Postgres and Redis from testcontainers, S3 from moto) and frontend unit tests (Vitest + Testing Library).
- GitHub Actions: backend CI, frontend CI (lint, test, build) and tag-based GitHub releases.
- `.dockerignore` to keep the nginx image build context small.

### Changed
- Authentication happens before `accept()`; rejected sockets close with code 1008.
- Room membership is loaded before `accept()` and registered once.
- DB work in the message path runs in worker threads instead of blocking the event loop.
- Messages are checked against blocks and deleted conversations at send time, not only at connect time.
- Validation: name, bio, country code, password length and message length limits.
- `swipe-action` returns 400 for invalid targets and is idempotent for duplicates.
- Conversation and unread queries use eager loading and `GROUP BY` instead of per-row queries.
- Cookie lifetime follows `ACCESS_TOKEN_EXPIRE_MINUTES`; `Secure` flag follows `COOKIE_SECURE`.
- Uvicorn trusts forwarded headers; nginx sets `X-Forwarded-For` from the real peer address.
- nginx accepts request bodies up to 32 MB (multi-image uploads).
- Prometheus discovers scaled API replicas through DNS service discovery.
- `/api/auth/session` returns an unauthenticated response instead of logging an error.
- Frontend uses relative URLs and derives `ws://` / `wss://` from the page origin.
- Frontend lint is clean and enforced in CI; the nginx image installs with `npm ci`.

### Fixed
- Browser sockets were evicted after about 60 seconds because the client never answered pings.
- Super like always returned 422 (`super-like` vs `super_like`).
- Profile update swallowed its own 400 and returned the unsaved state.
- WebSocket handler raised `UnboundLocalError` on failed authentication.
- Broadcast created an empty room entry per conversation and one dead socket skipped the rest.
- Redis subscriber and heartbeat loop did not recover from errors.
- Messages could be lost when a sender was active before the receiver was registered in its rooms.
- A conversation created while a socket was open was not joined, so its first message closed the socket.
- Reports modal removed every row on delete.
- Delete account did not clear the cookie or leave the page.
- Google accounts without a birthdate could not load their profile, and their locked feed gave no explanation.
- Grafana 5xx and latency queries, and the unreachable Prometheus target.
- Test image pulls (MinIO) replaced with an in-process S3 server.

### Removed
- `core/exceptions.py` (never registered).
- Unused dependencies: `alembic`, `pathlib`, `jinja2`, `minio`.
- Unused `COUNTRIES` and `DEBUG` settings.
- Unused CSS, dead components and debug logging in the frontend.