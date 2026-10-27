# Changelog

All notable changes to this project are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [0.2.0] - In Development

### Added
- health and readiness endpoints in backend.
- Database is now created through `init.sql` script.
- Retry mechanism for websocket disconnects.
- Test run step for frontend CI.
- DB MAX POOLSIZE and DB OVERFLOW are now set through the config schema with defaults.
- Dockerignore files for both frontend and backend.
- Env and lib provisioning scripts that are called by `start.sh` to ensure proper env setup.
- K8s infrastructure with base deployments for frontend and backend with their services, an ingress, and a base kustomization file.
- K8s environment overlays: dev, qa, and prod. All of which have their own configuration and patching as well as secrets injection.
- K8s monitoring with Prometheus and Grafana wired in.

### Changed
- Moved unit tests under `tests/unit_tests`, moved `smoke_tests` to `tests/integration_tests`, updated backend CI accordingly.
- Frontend dockerfile build as well as nginx conf now moved to frontend.
- Moved Prometheus and Grafana infra set up to k8s.
- Rewrote `start.sh` and `stop.sh` to match new infra.

### Fixed
- 401 redirect without warning when auth session token expires.

### Removed
- Backend api no longer creates database tables and only connects to it with retry mechanism.
- Nginx config and frontend dockerfile builder from `infra/nginx`.
- Docker compose file set up being removed in favor of new incoming k8 set up.


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