import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import uuid
import time
import logging

from hang.helpers.ws import manager, handle_ws_message, get_current_user_ws
from hang.helpers.conversations import get_all_user_conversations


ws_router = APIRouter(prefix="/ws", tags=["ws"])
logger = logging.getLogger("Hang")


@ws_router.websocket("/conversations")
async def conversation_ws(websocket: WebSocket):
    user_id = await asyncio.to_thread(get_current_user_ws, websocket)
    if user_id is None:
        logger.warning(
            "hang_event",
            extra={
                "event": "ws_rejected",
                "status": "unauthorized",
                "context": {"reason": "invalid_or_missing_token"},
            },
        )
        await websocket.close(code=1008)
        return

    cids = set(await asyncio.to_thread(get_all_user_conversations, user_id))
    websocket.state.conversation_ids = cids

    await websocket.accept()

    connection_id = str(uuid.uuid4())
    start_time = time.time()

    try:
        await manager.connect_user(user_id=user_id, websocket=websocket)
        for cid in cids:
            manager.join_room(cid, websocket)
        await websocket.send_json({"type": "ready"})

        logger.info(
            "hang_event",
            extra={
                "event": "ws_open",
                "status": "success",
                "user_id": user_id,
                "context": {
                    "connection_id": connection_id,
                    "rooms": len(cids),
                },
            },
        )

        while True:
            raw = await websocket.receive_text()
            try:
                await handle_ws_message(websocket=websocket, user_id=user_id, raw=raw)
            except WebSocketDisconnect:
                raise
            except Exception:
                logger.exception(
                    "ws message handling failed",
                    extra={"user_id": user_id},
                )
    except WebSocketDisconnect:
        pass  # normal close, handled in finally
    finally:
        manager.disconnect_user(user_id, websocket)
        logger.info(
            "hang_event",
            extra={
                "event": "ws_close",
                "status": "success",
                "user_id": user_id,
                "context": {
                    "connection_id": connection_id,
                    "duration_sec": round(time.time() - start_time, 2),
                },
            },
        )
