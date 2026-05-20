from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session
from typing import Annotated

from hang.helpers.ws import manager, handle_ws_message, get_current_user_ws
from hang.helpers.database import get_db
from hang.helpers.conversations import get_user_conversation

ws_router = APIRouter(prefix="/ws", tags=["ws"])


@ws_router.websocket("/conversations")
async def conversation_ws(
    websocket: WebSocket,
    db: Annotated[Session, Depends(get_db)],
):
    await websocket.accept()

    user = get_current_user_ws(ws=websocket, db=db)

    await manager.connect_user(user_id=user.user_id, websocket=websocket)

    try:
        while True:
            raw = await websocket.receive_text()

            data = None
            try:
                import json

                data = json.loads(raw)
            except Exception:
                continue

            conversation_id = data.get("conversation_id")

            if conversation_id:
                conversation = get_user_conversation(
                    db=db, user_id=user.user_id, conversation_id=conversation_id
                )

                if conversation:
                    manager.join_room(conversation_id, websocket)

            await handle_ws_message(
                db=db, websocket=websocket, user_id=user.user_id, raw=raw
            )

    except WebSocketDisconnect:
        manager.disconnect_user(user.user_id, websocket)

    except Exception:
        manager.disconnect_user(user.user_id, websocket)
        raise
