import argparse
import asyncio
import json
import statistics
import time
import uuid
from typing import Any
from pathlib import Path

import websockets

MARKER_PREFIX = "LOADTEST"


class Results:
    def __init__(self) -> None:
        self.connections_attempted = 0
        self.connections_succeeded = 0
        self.connection_errors: list[str] = []
        self.messages_sent = 0
        self.latencies_ms: list[float] = []
        self.undelivered = 0
        self.server_errors = 0

    def record_connection_attempt(self, count: int) -> None:
        self.connections_attempted += count

    def record_connection_success(self, count: int) -> None:
        self.connections_succeeded += count

    def record_connection_failure(self, error: str) -> None:
        self.connection_errors.append(error)

    def record_sent(self) -> None:
        self.messages_sent += 1

    def record_delivery(self, latency_seconds: float) -> None:
        self.latencies_ms.append(latency_seconds * 1000)

    def record_undelivered(self, count: int) -> None:
        self.undelivered += count

    def record_server_error(self) -> None:
        self.server_errors += 1

    def summary(self, duration_seconds: float) -> dict:
        delivered = len(self.latencies_ms)
        result: dict[str, Any] = {
            "connections_attempted": self.connections_attempted,
            "connections_succeeded": self.connections_succeeded,
            "connection_failures": len(self.connection_errors),
            "messages_sent": self.messages_sent,
            "messages_delivered_cross_connection": delivered,
            "messages_undelivered": self.undelivered,
            "server_error_frames": self.server_errors,
            "delivery_rate": (
                delivered / self.messages_sent if self.messages_sent else 0.0
            ),
            "duration_seconds": duration_seconds,
            "throughput_msgs_per_sec": (
                self.messages_sent / duration_seconds if duration_seconds else 0.0
            ),
        }

        if delivered >= 2:
            sorted_latencies = sorted(self.latencies_ms)
            quantiles = statistics.quantiles(sorted_latencies, n=100)
            result["latency_ms"] = {
                "min": sorted_latencies[0],
                "p50": quantiles[49],
                "p95": quantiles[94],
                "p99": quantiles[98],
                "max": sorted_latencies[-1],
                "mean": statistics.mean(sorted_latencies),
            }
        elif delivered == 1:
            result["latency_ms"] = {"single_sample": self.latencies_ms[0]}
        else:
            result["latency_ms"] = None

        if self.connection_errors:
            result["sample_connection_errors"] = self.connection_errors[:5]

        return result


async def connect_with_cookie(url: str, token: str):
    headers = [("Cookie", f"access_token={token}")]
    try:
        return await websockets.connect(
            url, additional_headers=headers, open_timeout=35
        )
    except TypeError:
        return await websockets.connect(url, extra_headers=headers, open_timeout=35)


async def wait_ready(ws) -> None:
    while True:
        raw = await asyncio.wait_for(ws.recv(), timeout=35)
        if json.loads(raw).get("type") == "ready":
            return


async def run_pair(pair: dict, args, results: Results) -> None:
    conversation_id = pair["conversation_id"]
    results.record_connection_attempt(2)

    sockets: list = []
    listen_tasks: list[asyncio.Task] = []
    pending: dict[str, float] = {}

    async def listener(ws, label: str) -> None:
        try:
            async for raw in ws:
                try:
                    data = json.loads(raw)
                except json.JSONDecodeError:
                    continue
                kind = data.get("type")
                if kind == "ping":
                    await ws.send(json.dumps({"type": "pong"}))
                    continue
                if kind == "error":
                    results.record_server_error()
                    continue
                if kind != "message":
                    continue
                parts = data.get("message", {}).get("content", "").split("::")
                if len(parts) != 3 or parts[0] != MARKER_PREFIX:
                    continue
                _, msg_id, sender_label = parts
                if sender_label == label:
                    continue
                send_time = pending.pop(msg_id, None)
                if send_time is not None:
                    results.record_delivery(time.monotonic() - send_time)
        except websockets.exceptions.ConnectionClosed:
            pass

    async def sender(ws, label: str) -> None:
        for _ in range(args.messages_per_user):
            msg_id = uuid.uuid4().hex
            pending[msg_id] = time.monotonic()
            await ws.send(
                json.dumps(
                    {
                        "conversation_id": conversation_id,
                        "content": f"{MARKER_PREFIX}::{msg_id}::{label}",
                    }
                )
            )
            results.record_sent()
            await asyncio.sleep(args.message_interval)

    try:
        try:
            ws_a = await connect_with_cookie(args.url, pair["user_a"]["access_token"])
            sockets.append(ws_a)
            ws_b = await connect_with_cookie(args.url, pair["user_b"]["access_token"])
            sockets.append(ws_b)
            await asyncio.gather(wait_ready(ws_a), wait_ready(ws_b))
        except Exception as exc:
            results.record_connection_failure(f"conversation {conversation_id}: {exc}")
            return

        results.record_connection_success(2)

        listen_tasks = [
            asyncio.create_task(listener(ws_a, "a")),
            asyncio.create_task(listener(ws_b, "b")),
        ]

        outcomes = await asyncio.gather(
            sender(ws_a, "a"), sender(ws_b, "b"), return_exceptions=True
        )
        for outcome in outcomes:
            if isinstance(outcome, Exception):
                results.record_connection_failure(
                    f"conversation {conversation_id}: sender: {outcome!r}"
                )

        await asyncio.sleep(args.drain_seconds)
        results.record_undelivered(len(pending))
    finally:
        for task in listen_tasks:
            task.cancel()
        await asyncio.gather(*listen_tasks, return_exceptions=True)
        for ws in sockets:
            try:
                await ws.close()
            except Exception:
                pass


async def run_load_test(pairs: list[dict], args) -> dict:
    print(
        f"Running load test: {len(pairs)} conversation pairs "
        f"({len(pairs) * 2} websocket connections), "
        f"{args.messages_per_user} messages/user, target {args.url}"
    )

    results = Results()

    start = time.monotonic()
    tasks = []
    for pair in pairs:
        tasks.append(asyncio.create_task(run_pair(pair, args, results)))
        if args.pairs_per_second > 0:
            await asyncio.sleep(1 / args.pairs_per_second)
    await asyncio.gather(*tasks, return_exceptions=True)
    duration = time.monotonic() - start

    summary = results.summary(duration)
    summary["pairs"] = len(pairs)
    summary["connections"] = len(pairs) * 2
    return summary


async def main_async(args) -> None:
    all_pairs = json.loads(Path(args.pairs_file).read_text())["pairs"]

    if args.sweep:
        sizes = [int(s) for s in args.sweep.split(",")]
        sweep_results = []
        output_path = Path(args.output)

        for size in sizes:
            if size > len(all_pairs):
                print(
                    f"skipping {size} pairs: only {len(all_pairs)} seeded. "
                    f"Re-run load_test_seed with --pairs {size} or higher first."
                )
                continue

            summary = await run_load_test(all_pairs[:size], args)
            print(json.dumps(summary, indent=2))
            sweep_results.append(summary)
            output_path.write_text(json.dumps(sweep_results, indent=2))

            if args.cooldown_seconds > 0 and size != sizes[-1]:
                print(f"cooling down {args.cooldown_seconds}s before next size...")
                await asyncio.sleep(args.cooldown_seconds)

        print("\nsweep summary:")
        header = (
            f"{'connections':>12} {'delivery_rate':>14} {'p50_ms':>8} "
            f"{'p95_ms':>8} {'p99_ms':>8} {'msgs/sec':>10} {'srv_err':>8}"
        )
        print(header)
        for s in sweep_results:
            lat = s.get("latency_ms") or {}
            print(
                f"{s['connections']:>12} {s['delivery_rate']:>14.3f} "
                f"{lat.get('p50', 0):>8.1f} {lat.get('p95', 0):>8.1f} "
                f"{lat.get('p99', 0):>8.1f} {s['throughput_msgs_per_sec']:>10.1f} "
                f"{s['server_error_frames']:>8}"
            )

        print(f"\nSweep results written to {output_path}")
        return

    pairs = all_pairs[: args.max_pairs] if args.max_pairs else all_pairs
    summary = await run_load_test(pairs, args)
    print(json.dumps(summary, indent=2))

    output_path = Path(args.output)
    output_path.write_text(json.dumps(summary, indent=2))
    print(f"\nResults written to {output_path}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Load test the hang websocket layer: opens real connections through "
            "nginx, sends messages, and measures cross-connection delivery "
            "latency to validate the Redis pub/sub fan-out under concurrent load."
        )
    )
    parser.add_argument("--pairs-file", default="dev_utils/load_test_users.json")
    parser.add_argument("--url", default="ws://hang-nginx:80/api/ws/conversations")
    parser.add_argument("--messages-per-user", type=int, default=20)
    parser.add_argument("--message-interval", type=float, default=0.4)
    parser.add_argument("--drain-seconds", type=float, default=3.0)
    parser.add_argument("--max-pairs", type=int, default=None)
    parser.add_argument(
        "--pairs-per-second",
        type=float,
        default=10.0,
        help="How many conversation pairs (2 connections each) to start per second, "
        "instead of opening all connections in one instantaneous burst.",
    )
    parser.add_argument(
        "--sweep",
        default=None,
        help="Comma-separated list of pair counts to run sequentially, e.g. "
        "'25,50,125,250,500,1000'. Each level uses the same message settings; "
        "requires enough pairs seeded to cover the largest size.",
    )
    parser.add_argument(
        "--cooldown-seconds",
        type=float,
        default=10.0,
        help="Pause between sweep levels to let connections/sockets fully close.",
    )
    parser.add_argument("--output", default="dev_utils/load_test_results.json")
    args = parser.parse_args()

    asyncio.run(main_async(args))


if __name__ == "__main__":
    main()
