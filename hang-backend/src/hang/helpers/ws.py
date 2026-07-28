from fastapi import WebSocket
from starlette.websockets import WebSocketDisconnect

from collections import defaultdict
from jose import jwt, JWTError
import json
import time
import asyncio
import logging

from hang.schemas.conversations import MessagePreview
from hang.schemas.config import conf
from hang.models.db_models import User

from hang.core.redis import redis_client
from hang.core.database import get_db_session
from hang.helpers.messages import send_message_flow, mark_conversation_messages_read
from hang.helpers.conversations import get_user_conversation


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
        logger.info(
            "hang_event",
            extra={
                "event": "ws_broadcast",
                "status": "success",
                "context": {
                    "conversation_id": conversation_id,
                    "connections": len(self.rooms[conversation_id]),
                },
            },
        )

        for ws in list(self.rooms[conversation_id]):
            await ws.send_json(message)

    async def ping_all(self):
        for ws in list(self.last_seen.keys()):
            try:
                await ws.send_json({"type": "ping"})
            except Exception:
                self._remove_ws(ws)

    def mark_pong(self, websocket: WebSocket):
        self.last_seen[websocket] = time.time()

    def cleanup(self, timeout: float = 60):
        now = time.time()
        stale = [ws for ws, t in self.last_seen.items() if now - t > timeout]

        for ws in stale:
            self._remove_ws(ws)

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


manager = ConnectionManager()


async def ws_heartbeat_loop():
    while True:
        await manager.ping_all()
        manager.cleanup(timeout=60)
        await asyncio.sleep(30)


async def handle_ws_message(
    *,
    websocket: WebSocket,
    user_id: int,
    raw: str,
):
    data = json.loads(raw)

    if data.get("type") == "pong":
        manager.mark_pong(websocket)
        return

    if data.get("type") == "typing":
        conversation_id = data.get("conversation_id")
        is_typing = data.get("is_typing", False)

        if not conversation_id:
            return

        await publish_event(
            conversation_id,
            {
                "type": "typing",
                "user_id": user_id,
                "conversation_id": conversation_id,
                "is_typing": is_typing,
            },
        )
        return

    if data.get("type") == "read":
        conversation_id = data.get("conversation_id")

        if not conversation_id:
            return

        with get_db_session() as db:
            mark_conversation_messages_read(
                db=db,
                conversation_id=conversation_id,
                user_id=user_id,
            )

        await publish_event(
            conversation_id,
            {
                "type": "read",
                "conversation_id": conversation_id,
                "user_id": user_id,
            },
        )
        return

    conversation_id = data.get("conversation_id")
    content = data.get("content")

    if not conversation_id or not content:
        return

    conversation = None
    with get_db_session() as db:
        conversation = get_user_conversation(
            db=db,
            user_id=user_id,
            conversation_id=conversation_id,
        )

        if not conversation:
            await websocket.close(code=1008)
            return

        message = send_message_flow(
            db=db,
            conversation=conversation,
            sender_id=user_id,
            content=content,
        )

        payload = {
            **MessagePreview.model_validate(message).model_dump(mode="json"),
            "conversation_id": conversation.conversation_id,
        }

    await publish_event(
        conversation_id,
        {
            "type": "message",
            "message": payload,
        },
    )


def get_current_user_ws(ws: WebSocket) -> int:
    token = ws.cookies.get("access_token")

    if not token:
        raise WebSocketDisconnect(code=1008)

    try:
        payload = jwt.decode(token, conf.SECRET_KEY, algorithms=[conf.ALGORITHM])

        user_id = payload.get("sub")

        if not user_id:
            raise WebSocketDisconnect(code=1008)

        uid = None
        with get_db_session() as db:
            user = db.query(User).filter(User.user_id == int(user_id)).first()
            uid = user.user_id

        if not user or not uid:
            raise WebSocketDisconnect(code=1008)

        return uid

    except JWTError:
        raise WebSocketDisconnect(code=1008)


async def publish_event(conversation_id: int, payload: dict):
    channel = f"conversation:{conversation_id}"

    await redis_client.publish(
        channel,
        json.dumps(payload),
    )


async def redis_subscriber():
    pubsub = redis_client.pubsub()

    await pubsub.psubscribe("conversation:*")

    async for message in pubsub.listen():
        if message["type"] not in ("message", "pmessage"):
            continue

        try:
            channel = message["channel"]
            data = json.loads(message["data"])

            conversation_id = int(channel.split(":")[1])

            await manager.broadcast(conversation_id, data)

        except Exception:
            continue
