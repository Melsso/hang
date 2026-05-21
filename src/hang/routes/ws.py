from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session
from typing import Annotated

from hang.helpers.ws import manager, handle_ws_message, get_current_user_ws
from hang.helpers.database import get_db
from hang.helpers.conversations import get_all_user_conversations

ws_router = APIRouter(prefix="/ws", tags=["ws"])


@ws_router.websocket("/conversations")
async def conversation_ws(
    websocket: WebSocket,
    db: Annotated[Session, Depends(get_db)],
):
    await websocket.accept()

    user = get_current_user_ws(ws=websocket, db=db)

    await manager.connect_user(user_id=user.user_id, websocket=websocket)
    conversations = get_all_user_conversations(db=db, user_id=user.user_id)

    for c in conversations:
        manager.join_room(c.conversation_id, websocket)

    try:
        while True:
            raw = await websocket.receive_text()

            await handle_ws_message(
                db=db, websocket=websocket, user_id=user.user_id, raw=raw
            )

    except WebSocketDisconnect:
        manager.disconnect_user(user.user_id, websocket)

    except Exception:
        manager.disconnect_user(user.user_id, websocket)
        raise
