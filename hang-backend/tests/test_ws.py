import asyncio
import json
import time
import pytest
from types import SimpleNamespace
from typing import Any, Iterable, cast
from fastapi import WebSocket
from starlette.websockets import WebSocketDisconnect

from hang.models.db_models import User, Conversation, Message, UserBlock

import hang.helpers.ws as ws_helpers
from hang.helpers.auth import create_access_token
from tests.utils import make_user_row


def _wait_for(predicate, timeout: float = 2.0) -> bool:
    end = time.time() + timeout
    while time.time() < end:
        if predicate():
            return True
        time.sleep(0.02)
    return False


class FakeWS:
    def __init__(self, conversation_ids: Iterable[int] = ()):
        self.state = SimpleNamespace(conversation_ids=set(conversation_ids))
        self.sent: list[dict] = []
        self.close_code: int | None = None

    async def send_json(self, data):
        self.sent.append(data)

    async def close(self, code: int = 1000):
        self.close_code = code


def as_ws(fake: FakeWS) -> WebSocket:
    return cast(WebSocket, fake)


def chat_seed(with_block: bool = False) -> dict:
    seed: dict = {
        User: [
            make_user_row("john@test.com", "John"),
            make_user_row("jane@test.com", "Jane"),
        ],
        Conversation: [
            {
                "user1_id": lambda c: c[User][0].user_id,
                "user2_id": lambda c: c[User][1].user_id,
            }
        ],
    }
    if with_block:
        seed[UserBlock] = [
            {
                "blocker_id": lambda c: c[User][1].user_id,
                "blocked_id": lambda c: c[User][0].user_id,
            }
        ]
    return seed


@pytest.fixture
def published(monkeypatch):
    events: list[tuple[int, dict]] = []

    async def fake_publish(conversation_id, payload):
        events.append((conversation_id, payload))

    monkeypatch.setattr(ws_helpers, "publish_event", fake_publish)
    return events


@pytest.mark.parametrize(
    "db",
    [{User: [make_user_row("john@test.com", "John")]}],
    indirect=True,
)
def test_ws_connect_with_valid_cookie_is_accepted(client, db):
    john = db.query(User).filter(User.email == "john@test.com").first()
    uid = john.user_id
    token = create_access_token({"sub": str(uid), "email": john.email})
    client.cookies.set("access_token", token)

    with client.websocket_connect("/api/ws/conversations"):
        assert _wait_for(lambda: len(ws_helpers.manager.user_sockets.get(uid, [])) == 1)

    assert _wait_for(lambda: uid not in ws_helpers.manager.user_sockets)


def test_ws_connect_without_cookie_is_rejected(client, db):
    with pytest.raises(WebSocketDisconnect) as exc:
        with client.websocket_connect("/api/ws/conversations"):
            pass
    assert exc.value.code == 1008


def test_ws_connect_with_garbage_token_is_rejected(client, db):
    client.cookies.set("access_token", "not-a-real-jwt")
    with pytest.raises(WebSocketDisconnect) as exc:
        with client.websocket_connect("/api/ws/conversations"):
            pass
    assert exc.value.code == 1008


def test_ws_connect_for_deleted_user_is_rejected(client, db):
    client.cookies.set("access_token", create_access_token({"sub": "999999"}))
    with pytest.raises(WebSocketDisconnect) as exc:
        with client.websocket_connect("/api/ws/conversations"):
            pass
    assert exc.value.code == 1008


@pytest.mark.anyio
async def test_cleanup_evicts_and_closes_stale_socket():
    mgr = ws_helpers.ConnectionManager()
    ws = FakeWS()
    await mgr.connect_user(1, as_ws(ws))
    mgr.join_room(10, as_ws(ws))
    mgr.last_seen[as_ws(ws)] -= 120

    await mgr.cleanup(timeout=60)

    assert as_ws(ws) not in mgr.last_seen
    assert 10 not in mgr.rooms
    assert 1 not in mgr.user_sockets
    assert ws.close_code == 1001


@pytest.mark.anyio
async def test_pong_keeps_socket_alive():
    ws = FakeWS()
    await ws_helpers.manager.connect_user(1, as_ws(ws))
    try:
        ws_helpers.manager.last_seen[as_ws(ws)] -= 100
        await ws_helpers.handle_ws_message(
            websocket=as_ws(ws), user_id=1, raw='{"type":"pong"}'
        )
        assert time.time() - ws_helpers.manager.last_seen[as_ws(ws)] < 5
    finally:
        ws_helpers.manager.disconnect_user(1, as_ws(ws))


def test_pong_does_not_resurrect_evicted_socket():
    mgr = ws_helpers.ConnectionManager()
    mgr.mark_pong(as_ws(FakeWS()))
    assert mgr.last_seen == {}


@pytest.mark.anyio
async def test_broadcast_survives_dead_socket_and_does_not_leak_rooms():
    class Dead:
        async def send_json(self, data):
            raise RuntimeError("closed")

    mgr = ws_helpers.ConnectionManager()
    dead, good = Dead(), FakeWS()
    mgr.join_room(1, cast(WebSocket, dead))
    mgr.join_room(1, as_ws(good))

    await mgr.broadcast(1, {"type": "x"})
    assert good.sent == [{"type": "x"}]
    assert cast(WebSocket, dead) not in mgr.rooms.get(1, [])

    await mgr.broadcast(2, {"type": "x"})
    assert 2 not in mgr.rooms


@pytest.mark.anyio
@pytest.mark.parametrize("db", [chat_seed()], indirect=True)
async def test_message_is_persisted_and_published(db, published):
    john = db.info["seeded"][User][0]
    conv = db.info["seeded"][Conversation][0]
    ws = FakeWS({conv.conversation_id})

    await ws_helpers.handle_ws_message(
        websocket=as_ws(ws),
        user_id=john.user_id,
        raw=json.dumps({"conversation_id": conv.conversation_id, "content": "hello"}),
    )

    assert len(published) == 1
    cid, event = published[0]
    assert cid == conv.conversation_id
    assert event["type"] == "message"
    assert event["message"]["content"] == "hello"
    assert event["message"]["sender_id"] == john.user_id
    db.refresh(conv)
    assert conv.last_message_id == event["message"]["message_id"]


@pytest.mark.anyio
@pytest.mark.parametrize("db", [chat_seed(with_block=True)], indirect=True)
async def test_message_to_blocked_conversation_is_rejected(db, published):
    john = db.info["seeded"][User][0]
    conv = db.info["seeded"][Conversation][0]
    ws = FakeWS({conv.conversation_id})

    await ws_helpers.handle_ws_message(
        websocket=as_ws(ws),
        user_id=john.user_id,
        raw=json.dumps({"conversation_id": conv.conversation_id, "content": "hi"}),
    )

    assert ws.sent == [
        {
            "type": "error",
            "conversation_id": conv.conversation_id,
            "reason": "conversation_unavailable",
        }
    ]
    assert published == []
    assert db.query(Message).count() == 0


@pytest.mark.anyio
@pytest.mark.parametrize("content", ["", "   ", "x" * 1001, 123, None])
@pytest.mark.parametrize("db", [chat_seed()], indirect=True)
async def test_invalid_content_is_ignored(db, published, content):
    john = db.info["seeded"][User][0]
    conv = db.info["seeded"][Conversation][0]

    await ws_helpers.handle_ws_message(
        websocket=as_ws(FakeWS({conv.conversation_id})),
        user_id=john.user_id,
        raw=json.dumps({"conversation_id": conv.conversation_id, "content": content}),
    )

    assert published == []
    assert db.query(Message).count() == 0


@pytest.mark.anyio
@pytest.mark.parametrize(
    "raw", ["not json", "[]", "42", "{}", '{"conversation_id": "7"}']
)
async def test_malformed_frames_are_ignored(raw, published):
    await ws_helpers.handle_ws_message(websocket=as_ws(FakeWS({7})), user_id=1, raw=raw)
    assert published == []


@pytest.mark.anyio
async def test_message_to_unjoined_conversation_closes_socket(published):
    ws = FakeWS(set())
    with pytest.raises(WebSocketDisconnect):
        await ws_helpers.handle_ws_message(
            websocket=as_ws(ws),
            user_id=1,
            raw=json.dumps({"conversation_id": 5, "content": "hi"}),
        )
    assert ws.close_code == 1008
    assert published == []


@pytest.mark.anyio
async def test_publish_event_reaches_room_subscribers(test_redis_client):
    received = []

    class FakeWebSocket:
        async def send_json(self, data):
            received.append(data)

    fake_ws = FakeWebSocket()
    conversation_id = 999999
    ws_helpers.manager.join_room(conversation_id, cast(WebSocket, fake_ws))

    subscriber_task = asyncio.create_task(ws_helpers.redis_subscriber())
    try:
        await asyncio.sleep(0.2)

        await ws_helpers.publish_event(
            conversation_id, {"type": "message", "content": "hi"}
        )

        for _ in range(20):
            if received:
                break
            await asyncio.sleep(0.1)

        assert received == [{"type": "message", "content": "hi"}]
    finally:
        subscriber_task.cancel()
        ws_helpers.manager.leave_room(conversation_id, cast(WebSocket, fake_ws))


@pytest.mark.anyio
async def test_publish_event_does_not_leak_to_other_rooms(test_redis_client):
    received_a: list[dict[str, Any]] = []
    received_b: list[dict[str, Any]] = []

    class FakeWebSocket:
        def __init__(self, sink):
            self.sink = sink

        async def send_json(self, data):
            self.sink.append(data)

    ws_a = FakeWebSocket(received_a)
    ws_b = FakeWebSocket(received_b)

    ws_helpers.manager.join_room(111, cast(WebSocket, ws_a))
    ws_helpers.manager.join_room(222, cast(WebSocket, ws_b))

    subscriber_task = asyncio.create_task(ws_helpers.redis_subscriber())
    try:
        await asyncio.sleep(0.2)

        await ws_helpers.publish_event(
            111, {"type": "message", "content": "only for room 111"}
        )

        for _ in range(20):
            if received_a:
                break
            await asyncio.sleep(0.1)

        assert received_a == [{"type": "message", "content": "only for room 111"}]
        assert received_b == []
    finally:
        subscriber_task.cancel()
        ws_helpers.manager.leave_room(111, cast(WebSocket, ws_a))
        ws_helpers.manager.leave_room(222, cast(WebSocket, ws_b))


@pytest.mark.anyio
async def test_match_event_joins_live_sockets_to_the_new_room():
    mgr = ws_helpers.ConnectionManager()
    ws = FakeWS({1})
    await mgr.connect_user(5, as_ws(ws))
    mgr.join_room(1, as_ws(ws))

    payload = {"type": "match", "conversation_id": 9, "user_id": 2, "name": "Jane"}
    await mgr.deliver_to_user(5, payload)

    assert 9 in ws.state.conversation_ids
    assert as_ws(ws) in mgr.rooms[9]
    assert ws.sent == [payload]


@pytest.mark.anyio
async def test_user_event_for_offline_user_is_dropped():
    mgr = ws_helpers.ConnectionManager()
    await mgr.deliver_to_user(123, {"type": "match", "conversation_id": 1})
    assert 123 not in mgr.user_sockets
