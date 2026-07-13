from fastapi import APIRouter, Depends, Request, Response, HTTPException
from sqlalchemy.orm import Session
from typing import Annotated, Optional

from hang.schemas.conversations import MessageListResponse, ConversationPreview
from hang.models.db_models import User

from hang.core.database import get_db
from hang.core.middleware import limiter
from hang.core.storage import StorageService, get_storage

from hang.helpers.users import get_current_user
from hang.helpers.messages import (
    get_conversation_messages,
    mark_conversation_messages_read,
)
from hang.helpers.conversations import (
    fetch_conversations_list,
    get_user_conversation,
    delete_conversation,
)

conversation_router = APIRouter(prefix="/conversations", tags=["conversations"])


@conversation_router.get("", response_model=list[ConversationPreview])
@limiter.limit("5/minute")
def conversations_get(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    storage: Annotated[StorageService, Depends(get_storage)],
):
    conv_lst = fetch_conversations_list(db=db, user_id=user.user_id, storage=storage)
    return conv_lst


@conversation_router.post("/delete/{conversation_id}")
@limiter.limit("5/minute")
def conversation_delete(
    request: Request,
    conversation_id: int,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    code, detail = delete_conversation(
        db=db, conversation_id=conversation_id, user_id=user.user_id
    )
    if code != 204:
        raise HTTPException(status_code=code, detail=detail)

    return Response(status_code=204)


@conversation_router.get(
    "/{conversation_id}/messages", response_model=MessageListResponse
)
@limiter.limit("20/minute")
def messages_by_conv_id_get(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    conversation_id: int,
    before_message_id: Optional[int] = None,
):
    conversation = get_user_conversation(
        db=db, user_id=user.user_id, conversation_id=conversation_id
    )

    messages, next_cursor, has_more = get_conversation_messages(
        db=db,
        conversation_id=conversation.conversation_id,
        before_message_id=before_message_id,
    )

    if before_message_id is None:
        mark_conversation_messages_read(
            db=db, conversation_id=conversation.conversation_id, user_id=user.user_id
        )

    return MessageListResponse(
        conversation_id=conversation.conversation_id,
        current_user_id=user.user_id,
        messages=messages,
        next_cursor=next_cursor,
        has_more=has_more,
    )
