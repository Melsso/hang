from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from typing import Annotated

from hang.schemas.conversations import ConversationPreview, ConversationListResponse
from hang.models.db_models import User, Conversation

from hang.helpers.template_helpers import render
from hang.helpers.database import get_db
from hang.helpers.auth import (
    get_current_user,
)  # TODO this should be in users helpers not auth
from hang.helpers.storage import build_image_url


conversation_router = APIRouter(prefix="/conversations", tags=["conversations"])


@conversation_router.get("")
def conversations_get(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    conversations = (
        db.query(Conversation)
        .filter(
            (Conversation.user1_id == user.user_id)
            | (Conversation.user2_id == user.user_id)
        )
        .order_by(Conversation.updated_at.desc())
        .all()
    )

    result = []

    for c in conversations:
        other_user_id = c.user2_id if c.user1_id == user.user_id else c.user1_id

        other_user = db.query(User).filter(User.user_id == other_user_id).first()
        other_user_image = None
        if other_user and other_user.images:
            other_user_image = build_image_url(other_user.images[0].image_key)

        result.append(
            ConversationPreview(
                conversation_id=c.conversation_id,
                other_user_id=other_user_id,
                other_user_name=other_user.first_name,
                other_user_image=other_user_image,
                last_message=c.last_message_id and "Last message placeholder",
                updated_at=c.updated_at,
            )
        )

    conv_lst_resp = ConversationListResponse(
        success=True, conversations=result
    ).model_dump(mode="json")

    return render(
        request=request,
        template="conversations.html",
        context={"conversations": conv_lst_resp},
    )
