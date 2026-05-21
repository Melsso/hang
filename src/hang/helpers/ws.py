from fastapi import WebSocket, Depends, HTTPException

from sqlalchemy.orm import Session
from collections import defaultdict
from typing import Annotated
from jose import jwt, JWTError
import json
import time
import asyncio
import logging

from hang.schemas.conversations import MessagePreview
from hang.schemas.config import settings
from hang.models.db_models import User

from hang.core.database import get_db
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
    db: Session,
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

        await manager.broadcast(
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

        mark_conversation_messages_read(
            db=db,
            conversation_id=conversation_id,
            user_id=user_id,
        )
        await manager.broadcast(
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

    await manager.broadcast(
        conversation_id,
        {
            "type": "message",
            "message": payload,
        },
    )


def get_current_user_ws(ws: WebSocket, db: Annotated[Session, Depends(get_db)]) -> User:
    token = ws.cookies.get("access_token")

    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )

        user_id = payload.get("sub")

        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")

        user = db.query(User).filter(User.user_id == int(user_id)).first()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        return user

    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
