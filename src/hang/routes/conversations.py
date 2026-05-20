from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from typing import Annotated

from hang.schemas.conversations import MessageListResponse
from hang.models.db_models import User

from hang.helpers.template_helpers import render
from hang.helpers.database import get_db
from hang.helpers.users import get_current_user
from hang.helpers.conversations import (
    fetch_conversations_list,
    get_user_conversation,
    get_conversation_messages,
)

conversation_router = APIRouter(prefix="/conversations", tags=["conversations"])


@conversation_router.get("")
def conversations_get(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    conv_lst = fetch_conversations_list(db=db, user_id=user.user_id)

    return render(
        request=request,
        template="conversations.html",
        context={"conversations": [c.model_dump(mode="json") for c in conv_lst]},
    )


@conversation_router.get("/{conversation_id}/messages")
def messages_by_conv_id_get(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    conversation_id: int,
):
    conversation = get_user_conversation(
        db=db, user_id=user.user_id, conversation_id=conversation_id
    )
    if not conversation:
        return None

    msg_lst = get_conversation_messages(db=db, conversation_id=conversation_id)

    return MessageListResponse(
        conversation_id=conversation_id, current_user_id=user.user_id, messages=msg_lst
    )
