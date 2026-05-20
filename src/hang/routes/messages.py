from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from typing import Annotated

from hang.schemas.messages import MessageListResponse, MessagePreview
from hang.models.db_models import User, Conversation, Message

from hang.helpers.database import get_db
from hang.helpers.users import get_current_user


message_router = APIRouter(prefix="/messages", tags=["messages"])


@message_router.get("/conversation/{conversation_id}")
def messages_by_conv_id_get(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    conversation_id: int,
):
    conversation = (
        db.query(Conversation)
        .filter(Conversation.conversation_id == conversation_id)
        .first()
    )

    if not conversation:
        return {"error": "not found"}

    if user.user_id not in [conversation.user1_id, conversation.user2_id]:
        return {"error": "forbidden"}

    messages = (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc())
        .all()
    )

    result = [
        MessagePreview(
            message_id=m.message_id,
            sender_id=m.sender_id,
            content=m.content,
            created_at=m.created_at,
        )
        for m in messages
    ]

    return MessageListResponse(
        conversation_id=conversation_id, current_user_id=user.user_id, messages=result
    )
