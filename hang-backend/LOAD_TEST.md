# Load Testing

## What this tests

The WebSocket layer end to end: real connections through the ingress controller, three API replicas, Redis
pub/sub fan-out and Postgres writes. A message counts as delivered only when the other participant in the
conversation receives it.

Tooling:
- `scripts/loadtest.sh` builds `hang-backend/Dockerfile.loadtest`, loads it into the kind cluster and runs it
  as a Kubernetes Job in the target namespace. It deletes the seeded users afterwards.
- `dev_utils/load_test_seed.py` inserts matched user pairs and conversations directly into Postgres
  (bypassing the rate-limited auth endpoints) and issues JWTs with the same signing logic as login.
- `dev_utils/load_test_client.py` opens a connection per user, waits for the server's `ready` frame, sends
  messages, and measures delivery and latency. It also counts server `error` frames.

## Environment

Run date: 2026-10-27, `prod` overlay.

- MacBook Air (Apple M4), 16 GB RAM
- Docker Desktop VM: 10 CPUs, 8 GB memory, 1 GB swap, Resource Saver enabled
- kind cluster with 1 control-plane node and 3 workers. One worker is tainted and labelled for `prod`; the
  other two are shared.
- Hang API: 3 replicas on the prod worker (requests 250m CPU / 384Mi, memory limit 768Mi). DB pool of 5 plus
  5 overflow per replica.
- Load generator: one pod on a shared worker (requests 500m CPU / 512Mi, memory limit 1Gi)
- Postgres 16 and Redis 7 run as Docker containers on the same VM, outside the cluster
- Path: generator pod, ingress-nginx controller (plain HTTP, port 80), API pods, Redis and Postgres
- Connection ramp: 10 pairs per second. Each user sends 50 messages back to back, then a 30 s drain.
  10 s pause between levels.

## Results

| Connections | Messages | Delivery | p50 (ms) | p95 (ms) | p99 (ms) | Max (ms) |
|---|---|---|---|---|---|---|
| 100 | 5,000 | 100% | 86.8 | 225.9 | 277.7 | 344.0 |
| 200 | 10,000 | 100% | 65.3 | 137.9 | 163.1 | 192.2 |
| 500 | 25,000 | 100% | 62.5 | 150.5 | 211.2 | 338.1 |
| 1,000 | 50,000 | 100% | 69.6 | 175.3 | 266.3 | 532.9 |
| 2,000 | 100,000 | 100% | 88.8 | 314.5 | 551.9 | 1,032.5 |

190,000 messages in total, none undelivered, zero server error frames, zero connection failures.

## Notes on the measurements

- Latency is measured at the client, a single Python process in a pod on the same VM as the rest of the stack,
  so client event-loop delay is included.
- Each level was run once. Values are not monotonic in connection count: the 100-connection level, which ran
  first, has higher p50 and p95 than the 200 and 500 levels. The run does not isolate the reason.
- p95, p99 and max are highest at the 1,000 and 2,000 connection levels. The generator, ingress, API pods,
  Redis and Postgres share the VM's CPUs and no per-component measurements were recorded, so the run does not
  show which part contributes to the tail.
- Throughput is not reported. Run duration includes the connection ramp and the drain, so messages per second
  reflects the test parameters, not server capacity.
- Database connection counts were not recorded during the run.

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
- Real internet conditions: everything is on one machine.
- More than 3 replicas, or replicas added or removed during traffic.
- Steady chat-like traffic: each pair sends 100 messages back to back.
- TLS termination: the generator talks plain HTTP to the ingress controller.
- Postgres and Redis running on separate hosts or inside the cluster.

## Reproducing

The cluster must be up with the target environment deployed:

```bash
./start.sh prod
scripts/loadtest.sh prod
```

The script seeds 1,000 pairs (2,000 users named `LoadTest...`), runs the sweep at 50, 100, 250, 500 and 1,000
pairs, streams the log to `.local/loadtest-<env>-<timestamp>.log`, and deletes the seeded users when it
exits. The sweep summary table is at the end of that log.