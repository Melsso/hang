# Load Testing

## What this tests

The WebSocket layer end to end: real connections through nginx, three API replicas, real Redis pub/sub
fan-out and real Postgres writes. A message counts as delivered only when the other participant in the
conversation receives it, which validates cross-replica fan-out under concurrent load.

Tooling, all in `dev_utils/`:
- `load_test_seed.py` inserts matched user pairs and conversations directly into Postgres (bypassing the
  rate-limited auth endpoints) and issues JWTs with the same signing logic as login.
- `load_test_client.py` opens a connection per user, waits for the server's `ready` frame, sends messages,
  and measures delivery and latency. It also counts server `error` frames.
- `run_loadtest.sh` builds `Dockerfile.loadtest` and runs both inside the Docker network, because Postgres
  and Redis are not published to the host.

## Environment

- MacBook Air (Apple M4), 16 GB RAM
- Docker Desktop VM limits: `<fill in CPU / memory from Docker Desktop → Settings → Resources>`
- Everything ran on one machine: 3 API replicas, nginx, Postgres, Redis and the load generator
- Connection ramp: 10 pairs per second. Each user sends 50 messages back to back, then a 30 s drain

## Results

| Connections | Messages | Delivery | p50 (ms) | p95 (ms) | p99 (ms) |
|---|---|---|---|---|---|
| 100 | 5,000 | 100% | 44.2 | 79.5 | 110.6 |
| 200 | 10,000 | 100% | 43.7 | 78.1 | 99.5 |
| 500 | 25,000 | 100% | 43.7 | 78.7 | 93.9 |
| 1,000 | 50,000 | 100% | 42.8 | 76.8 | 81.1 |
| 2,000 | 100,000 | 100% | 43.0 | 77.1 | 82.3 |

190,000 messages in total, zero undelivered, zero server error frames, zero connection failures.

## Interpretation

- Median latency stayed flat at about 43 ms across a 20x increase in connections. Tail latency is flat
  from 200 to 2,000 connections (p99 82 ms at the top).
- No saturation was reached, so this run does not establish a capacity limit.
- The higher p99 on the first row (110.6 ms) is most likely cold-start cost: the first level pays for
  fresh DB connections, uncached plans and TCP warmup.
- Throughput is deliberately not reported. Run duration includes the connection ramp and the drain, so
  messages per second reflects the test parameters, not server capacity.
- Latency is measured at the client, which is a single Python process on the same machine as the whole
  stack, so client event-loop delay is included.

## Two bugs this found

**1. Database session held for the lifetime of each socket.** The first attempt, a burst of 100
connections, failed almost entirely, with an exact 30-second wave of closing connections in the logs.
`get_db()` was called once per WebSocket and the session was held until disconnect, which tied the number
of open sockets to the SQLAlchemy pool (15 connections), capping concurrency at about 15 users per
instance. Fix: sessions are acquired per operation.

**2. Messages lost before a socket was registered in its rooms.** After moving database lookups off the
event loop with `asyncio.to_thread`, reruns showed 0.2 to 0.3% of messages undelivered at 500+
connections, with no errors in any log. The socket was accepted before its room lookup finished, so a
fast sender's message could be published before the receiver was in the room, and Redis pub/sub does not
replay. A duplicated setup block in the handler made the window worse. Fix: authenticate and load rooms
before `accept()`, register once, send a `ready` frame, and have the load client wait for it. After the
fix every level delivered 100%.

## What this doesn't test

- Long sustained runs (this is ramp-and-burst over seconds to minutes, not a soak test).
- Real internet conditions: everything is on one machine over a Docker network.
- More than 3 replicas, or replicas added or removed during traffic.
- Steady chat-like traffic: each pair sends 100 messages back to back.
- Other infrastructure sizing: results depend on the current nginx, Postgres and Redis configuration.

## Reproducing

Run from `hang-backend`:

```bash
NETWORK=hang-network DB_HOST=hang-db-local REDIS_HOST=hang-redis-local ./dev_utils/run_loadtest.sh
```

The stack must be running (`./start.sh 3`). The script seeds 1,000 pairs, runs the sweep at
50, 100, 250, 500 and 1,000 pairs (100 to 2,000 connections), and writes `load_test_users.json`
(contains valid JWTs, gitignored) and `load_test_results.json` into `dev_utils/`.

Seeding adds 2,000 users named `LoadTest...`. Remove them before demoing, since they appear in the feed:

```bash
docker exec hang-db-local psql -U <POSTGRES_USER> -d <POSTGRES_DB> \
  -c "DELETE FROM users WHERE email LIKE 'loadtest_%@example.com';"
```