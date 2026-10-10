from fastapi import WebSocket
from starlette.websockets import WebSocketDisconnect

from collections import defaultdict
from jose import jwt, JWTError
import json
import time
import asyncio
from prometheus_client import Gauge

import logging

from hang.schemas.conversations import MessagePreview
from hang.schemas.config import conf
from hang.models.db_models import User, Conversation
from hang.helpers.users import is_blocked
from hang.core.redis import redis_client
from hang.core.database import get_db_session
from hang.helpers.messages import send_message_flow, mark_conversation_messages_read


logger = logging.getLogger("Hang")


class ConnectionManager:
    def __init__(self):
        self.user_sockets: dict[int, list[WebSocket]] = defaultdict(list)
        self.rooms: dict[int, list[WebSocket]] = defaultdict(list)
        self.last_seen: dict[WebSocket, float] = {}

    async def connect_user(self, user_id: int, websocket: WebSocket):
        self.user_sockets[user_id].append(websocket)
        self.last_seen[websocket] = time.time()

    def disconnect_user(self, user_id: int, websocket: WebSocket):
        if websocket in self.user_sockets[user_id]:
            self.user_sockets[user_id].remove(websocket)

        self.last_seen.pop(websocket, None)

        if not self.user_sockets[user_id]:
            self.user_sockets.pop(user_id, None)

        self._remove_from_rooms(websocket)

    def join_room(self, conversation_id: int, websocket: WebSocket):
        if websocket not in self.rooms[conversation_id]:
            self.rooms[conversation_id].append(websocket)

    def leave_room(self, conversation_id: int, websocket: WebSocket):
        if websocket in self.rooms[conversation_id]:
            self.rooms[conversation_id].remove(websocket)

        if not self.rooms[conversation_id]:
            self.rooms.pop(conversation_id, None)

    async def broadcast(self, conversation_id: int, message: dict):
        sockets = list(self.rooms.get(conversation_id, ()))
        if not sockets:
            return

        logger.info(
            "hang_event",
            extra={
                "event": "ws_broadcast",
                "status": "success",
                "context": {
                    "conversation_id": conversation_id,
                    "connections": len(sockets),
                },
            },
        )

        results = await asyncio.gather(
            *(ws.send_json(message) for ws in sockets), return_exceptions=True
        )
        for ws, result in zip(sockets, results):
            if isinstance(result, Exception):
                logger.warning(
                    "hang_event",
                    extra={
                        "event": "ws_send_failed",
                        "status": "evicted",
                        "error_type": type(result).__name__,
                        "context": {"conversation_id": conversation_id},
                    },
                )
                self._remove_ws(ws)
                self._remove_ws(ws)

    async def cleanup(self, timeout: float = 60):
        now = time.time()
        stale = [ws for ws, t in self.last_seen.items() if now - t > timeout]
        for ws in stale:
            self._remove_ws(ws)
            try:
                await ws.close(code=1001)
            except Exception:
                pass

    async def ping_all(self):
        for ws in list(self.last_seen.keys()):
            try:
                await ws.send_json({"type": "ping"})
            except Exception:
                self._remove_ws(ws)

    def mark_pong(self, websocket: WebSocket):
        if websocket in self.last_seen:
            self.last_seen[websocket] = time.time()

    def _remove_ws(self, websocket: WebSocket):
        self.last_seen.pop(websocket, None)
        self._remove_from_rooms(websocket)
        self._remove_from_users(websocket)

    def _remove_from_rooms(self, websocket: WebSocket):
        for room_id, sockets in list(self.rooms.items()):
            if websocket in sockets:
                sockets.remove(websocket)

            if not sockets:
                self.rooms.pop(room_id, None)

    def _remove_from_users(self, websocket: WebSocket):
        for user_id, sockets in list(self.user_sockets.items()):
            if websocket in sockets:
                sockets.remove(websocket)

            if not sockets:
                self.user_sockets.pop(user_id, None)

    async def deliver_to_user(self, user_id: int, payload: dict):
        sockets = list(self.user_sockets.get(user_id, ()))
        if not sockets:
            return

        if payload.get("type") == "match":
            conversation_id = payload.get("conversation_id")
            if isinstance(conversation_id, int):
                for ws in sockets:
                    ws.state.conversation_ids.add(conversation_id)
                    self.join_room(conversation_id, ws)

        results = await asyncio.gather(
            *(ws.send_json(payload) for ws in sockets), return_exceptions=True
        )
        for ws, result in zip(sockets, results):
            if isinstance(result, Exception):
                self._remove_ws(ws)


manager = ConnectionManager()
Gauge(
    "hang_ws_connections", "Open websocket connections on this instance"
).set_function(lambda: len(manager.last_seen))


async def ws_heartbeat_loop():
    while True:
        try:
            await manager.ping_all()
            await manager.cleanup(timeout=60)
        except Exception:
            logger.exception("ws heartbeat iteration failed")
        await asyncio.sleep(30)


def _persist_message(conversation_id: int, user_id: int, content: str) -> dict | None:
    with get_db_session() as db:
        conv = (
            db.query(Conversation)
            .filter(Conversation.conversation_id == conversation_id)
            .first()
        )
        if conv is None:
            return None
        other_id = conv.user2_id if conv.user1_id == user_id else conv.user1_id
        if is_blocked(db, user_id, other_id):
            return None
        message = send_message_flow(
            db=db, conversation_id=conversation_id, sender_id=user_id, content=content
        )
        payload = {
            **MessagePreview.model_validate(message).model_dump(mode="json"),
            "conversation_id": conversation_id,
        }
        db.commit()
    return payload


def _mark_read(conversation_id: int, user_id: int) -> None:
    with get_db_session() as db:
        mark_conversation_messages_read(
            db=db, conversation_id=conversation_id, user_id=user_id
        )


async def handle_ws_message(*, websocket: WebSocket, user_id: int, raw: str):
    manager.mark_pong(websocket)

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return
    if not isinstance(data, dict):
        return

    msg_type = data.get("type")
    if msg_type == "pong":
        return

    conversation_id = data.get("conversation_id")
    if not isinstance(conversation_id, int):
        return

    if conversation_id not in websocket.state.conversation_ids:
        await websocket.close(code=1008)
        raise WebSocketDisconnect(code=1008)

    if msg_type == "typing":
        await publish_event(
            conversation_id,
            {
                "type": "typing",
                "user_id": user_id,
                "conversation_id": conversation_id,
                "is_typing": bool(data.get("is_typing", False)),
            },
        )
        return

    if msg_type == "read":
        await asyncio.to_thread(_mark_read, conversation_id, user_id)
        await publish_event(
            conversation_id,
            {
                "type": "read",
                "conversation_id": conversation_id,
                "user_id": user_id,
            },
        )
        return

    content = data.get("content")
    if not isinstance(content, str) or not content.strip() or len(content) > 1000:
        return

    payload = await asyncio.to_thread(
        _persist_message, conversation_id, user_id, content
    )
    if payload is None:
        await websocket.send_json(
            {
                "type": "error",
                "conversation_id": conversation_id,
                "reason": "conversation_unavailable",
            }
        )
        return
    await publish_event(conversation_id, {"type": "message", "message": payload})


def get_current_user_ws(ws: WebSocket) -> int | None:
    token = ws.cookies.get("access_token")
    if not token:
        return None
    try:
        payload = jwt.decode(token, conf.SECRET_KEY, algorithms=[conf.ALGORITHM])
        sub = payload.get("sub")
        if sub is None:
            return None
        user_id = int(sub)
    except (JWTError, ValueError):
        return None

    with get_db_session() as db:
        exists = db.query(User.user_id).filter(User.user_id == user_id).first()
    return user_id if exists else None


async def publish_event(conversation_id: int, payload: dict):
    channel = f"conversation:{conversation_id}"

    await redis_client.publish(
        channel,
        json.dumps(payload),
    )


async def redis_subscriber():
    while True:
        pubsub = redis_client.pubsub()
        try:
            await pubsub.psubscribe("conversation:*", "user:*")
            async for message in pubsub.listen():
                if message["type"] not in ("message", "pmessage"):
                    continue
                try:
                    kind, _, raw_id = message["channel"].partition(":")
                    target_id = int(raw_id)
                    data = json.loads(message["data"])
                    if kind == "conversation":
                        await manager.broadcast(target_id, data)
                    elif kind == "user":
                        await manager.deliver_to_user(target_id, data)
                except Exception as exc:
                    logger.error(
                        "hang_event",
                        extra={
                            "event": "redis pub sub",
                            "status": "failed",
                            "error_type": type(exc).__name__,
                            "error_message": str(exc),
                            "context": {"location": "redis_subscriber"},
                        },
                    )
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("redis subscriber lost connection, retrying")
            await asyncio.sleep(1)
        finally:
            try:
                await pubsub.aclose()
            except Exception:
                pass


async def publish_user_event(user_id: int, payload: dict) -> None:
    try:
        await redis_client.publish(f"user:{user_id}", json.dumps(payload))
    except Exception:
        logger.exception("user event publish failed", extra={"user_id": user_id})
