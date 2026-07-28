# Load Testing

## What this tests

The websocket layer end to end: real connections through Nginx, real Redis pub/sub fan-out across multiple scaled API instances, real Postgres queries — not mocked. Delivery is measured cross-connection (a message only counts as delivered when the *other* participant in a conversation receives it), which specifically validates that the Redis pub/sub broadcast works correctly under concurrent load, not just between two people talking to the same backend instance.

Tooling: `dev_utils/load_test_seed.py` seeds matched user pairs and conversations directly into Postgres (bypassing the rate-limited `/auth` endpoints, since seeding test data shouldn't be rate-limited against itself) and issues real JWTs using the same signing logic the login endpoint uses. `dev_utils/load_test_client.py` then opens real websocket connections through Nginx for each pair, sends messages, and measures delivery + latency.

## A real bug this found

The first attempt at this test — a burst of 100 simultaneous connections — failed almost entirely, with most connections timing out and server logs showing a strange, exact 30-second wave pattern of connections closing. The cause: `get_db()` was called once per websocket connection and the same database session was held for the connection's entire lifetime, rather than being scoped to individual queries. That accidentally tied "how many websocket connections can be open" to "how many database connections are in the pool" — with SQLAlchemy's default pool (15 connections), only ~15 concurrent users could actually connect per instance, regardless of how idle the rest of the time those connections spent. Real idle websocket connections should cost almost nothing; this bug made them as expensive as a live, held-open database connection.

Fix: database sessions are now acquired per-query (once for auth, once for the initial conversation fetch, again for each incoming message) rather than held for the socket's whole lifetime. After the fix, the same 100-connection burst succeeded with zero failures, which is what led to testing further at larger scales below.

## Sweep methodology

Connections are ramped up gradually (10 pairs/second by default) rather than opened in one instantaneous burst, since that's closer to how real traffic actually arrives. Each level runs for the same message pattern (50 messages/user, sent back-to-back with no artificial delay) before the next level starts, with a cooldown between levels so one level's teardown can't bleed into the next level's connect phase.

## Results

| Connections | Delivery rate | p50 (ms) | p95 (ms) | p99 (ms) | Throughput (msg/s) |
|---|---|---|---|---|---|
| 100 | 100% | 66.4 | 225.8 | 336.1 | 143.1 |
| 200 | 100% | 48.2 | 86.8 | 94.2 | 250.4 |
| 500 | 100% | 49.5 | 90.4 | 153.4 | 454.9 |
| 1,000 | 100% | 58.7 | 181.4 | 277.1 | 624.8 |
| 2,000 | 100% | 68.3 | 173.3 | 280.7 | 769.0 |

Zero dropped messages at every level tested, up to 2,000 concurrent connections across 3 API instances on a single laptop.

## Honest interpretation

The 100-connection row having worse tail latency (p95 226ms, p99 336ms) than the 200-connection row right after it (p95 87ms, p99 94ms) is almost certainly a cold-start artifact — the first run in the sequence pays warmup costs (fresh database connections, uncached query plans, TCP slow start) that later runs don't. It isn't evidence that fewer connections perform worse; it's a reminder not to over-read a single data point, the same lesson learned earlier while benchmarking the HNSW index in a separate project.

The real signal is between 1,000 and 2,000 connections: throughput only grew about 23% (625 → 769 msg/s) despite doubling the connection count, while median latency crept up (59ms → 68ms). That's the shape of a system approaching a soft capacity limit, not one that's failed yet — delivery stayed perfect and tail latency didn't blow up further, but the sub-linear throughput growth suggests somewhere in the 1,000–2,000 connection range is where this particular setup (3 instances, single laptop, current Postgres/Redis/Nginx tuning) starts working harder for each additional connection.

One caveat on the throughput numbers specifically: `duration_seconds` includes the connection ramp-up period (at 10 pairs/second, ramping up 1,000 pairs takes roughly 100 seconds by itself), not just steady-state running time. That means reported throughput is somewhat understated at the higher levels, since a meaningful fraction of the measured window has fewer than the final connection count actually active.

## What this doesn't test

- Behavior over long sustained duration (this is burst/ramp testing over tens of seconds to a couple minutes, not a multi-hour soak test for slow leaks)
- Behavior under real internet conditions (packet loss, variable latency) rather than localhost
- Horizontal scaling beyond 3 instances, or behavior when instances are added/removed while traffic is live
- Nginx and Postgres/Redis are running with the project's current tuning (e.g. `nginx worker_connections` raised to 4096); results would differ under different infra sizing

## Reproducing this

```
DB_HOST=localhost poetry run python -m dev_utils.load_test_seed --pairs 1000

DB_HOST=localhost REDIS_HOST=localhost poetry run python dev_utils/load_test_client.py \
  --sweep "50,100,250,500,1000" \
  --messages-per-user 50 --message-interval 0 --drain-seconds 30
```