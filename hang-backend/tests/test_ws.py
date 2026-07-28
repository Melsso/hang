import asyncio
import pytest
from typing import Any, cast
from fastapi import WebSocket

from hang.models.db_models import User

import hang.helpers.ws as ws_helpers
from hang.helpers.auth import create_access_token
from tests.utils import make_user_row


@pytest.mark.parametrize(
    "db",
    [{User: [make_user_row("john@test.com", "John")]}],
    indirect=True,
)
def test_ws_connect_with_valid_cookie_is_accepted(client, db):
    john = db.query(User).filter(User.email == "john@test.com").first()
    token = create_access_token({"sub": str(john.user_id), "email": john.email})
    client.cookies.set("access_token", token)

    with client.websocket_connect("/api/ws/conversations") as _:
        assert john.user_id in ws_helpers.manager.user_sockets
        assert len(ws_helpers.manager.user_sockets[john.user_id]) == 1


def test_ws_connect_without_cookie_is_rejected(client, db):
    with pytest.raises(Exception):
        with client.websocket_connect("/api/ws/conversations"):
            pass


def test_ws_connect_with_garbage_token_is_rejected(client, db):
    client.cookies.set("access_token", "not-a-real-jwt")
    with pytest.raises(Exception):
        with client.websocket_connect("/api/ws/conversations"):
            pass


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
