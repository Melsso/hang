from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import uuid
import time
import logging

from hang.helpers.ws import manager, handle_ws_message, get_current_user_ws
from hang.helpers.conversations import get_all_user_conversations


ws_router = APIRouter(prefix="/ws", tags=["ws"])
logger = logging.getLogger("Hang")


@ws_router.websocket("/conversations")
async def conversation_ws(
    websocket: WebSocket,
):
    try:
        await websocket.accept()
        connection_id = str(uuid.uuid4())
        start_time = time.time()

        user_id = get_current_user_ws(ws=websocket)

        logger.info(
            "hang_event",
            extra={
                "event": "ws_open",
                "status": "success",
                "connection_id": connection_id,
                "user_id": user_id,
            },
        )

        await manager.connect_user(user_id=user_id, websocket=websocket)
        cids = set(get_all_user_conversations(user_id=user_id))
        websocket.state.conversation_ids = cids

        for cid in cids:
            manager.join_room(cid, websocket)
            logger.info(
                "hang_event",
                extra={
                    "event": "ws_join_room",
                    "status": "success",
                    "connection_id": connection_id,
                    "user_id": user_id,
                    "context": {"conversation_id": cid},
                },
            )

        while True:
            raw = await websocket.receive_text()

            await handle_ws_message(websocket=websocket, user_id=user_id, raw=raw)

    except WebSocketDisconnect:
        duration = time.time() - start_time
        logger.info(
            "hang_event",
            extra={
                "event": "ws_close",
                "status": "success",
                "connection_id": connection_id,
                "user_id": user_id,
                "context": {"duration_sec": round(duration, 2)},
            },
        )
        manager.disconnect_user(user_id, websocket)

    except Exception:
        manager.disconnect_user(user_id, websocket)
        raise
