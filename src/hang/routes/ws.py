from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session
from typing import Annotated
import uuid
import time
import logging

from hang.core.database import get_db
from hang.helpers.ws import manager, handle_ws_message, get_current_user_ws
from hang.helpers.conversations import get_all_user_conversations


ws_router = APIRouter(prefix="/ws", tags=["ws"])
logger = logging.getLogger("Hang")


@ws_router.websocket("/conversations")
async def conversation_ws(
    websocket: WebSocket,
    db: Annotated[Session, Depends(get_db)],
):
    await websocket.accept()
    connection_id = str(uuid.uuid4())
    start_time = time.time()

    user = get_current_user_ws(ws=websocket, db=db)
    websocket.state.connection_id = connection_id
    websocket.state.user_id = user.user_id

    logger.info(
        "hang_event",
        extra={
            "event": "ws_open",
            "status": "success",
            "connection_id": connection_id,
            "user_id": user.user_id,
        },
    )

    await manager.connect_user(user_id=user.user_id, websocket=websocket)
    conversations = get_all_user_conversations(db=db, user_id=user.user_id)

    for c in conversations:
        manager.join_room(c.conversation_id, websocket)
        logger.info(
            "hang_event",
            extra={
                "event": "ws_join_room",
                "status": "success",
                "connection_id": connection_id,
                "user_id": user.user_id,
                "context": {"conversation_id": c.conversation_id},
            },
        )

    try:
        while True:
            raw = await websocket.receive_text()

            await handle_ws_message(
                db=db, websocket=websocket, user_id=user.user_id, raw=raw
            )

    except WebSocketDisconnect:
        duration = time.time() - start_time
        logger.info(
            "hang_event",
            extra={
                "event": "ws_close",
                "status": "success",
                "connection_id": connection_id,
                "user_id": user.user_id,
                "context": {"duration_sec": round(duration, 2)},
            },
        )
        manager.disconnect_user(user.user_id, websocket)

    except Exception:
        manager.disconnect_user(user.user_id, websocket)
        raise
