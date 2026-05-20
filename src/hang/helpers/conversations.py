from sqlalchemy.orm import Session
from typing import Optional

from hang.schemas.conversations import ConversationPreview
from hang.models.db_models import User, Conversation

from hang.helpers.storage import build_image_url


def fetch_conversations_list(
    db: Session, user_id: int
) -> Optional[list[ConversationPreview]]:
    conversations = (
        db.query(Conversation)
        .filter((Conversation.user1_id == user_id) | (Conversation.user2_id == user_id))
        .order_by(Conversation.updated_at.desc())
        .all()
    )

    result = []

    for c in conversations:
        other_user_id = c.user2_id if c.user1_id == user_id else c.user1_id

        other_user = db.query(User).filter(User.user_id == other_user_id).first()
        other_user_img_url = None

        if other_user and other_user.images:
            other_user_img_url = build_image_url(other_user.images[0].image_key)

        result.append(
            ConversationPreview(
                conversation_id=c.conversation_id,
                other_user_id=other_user_id,
                other_user_name=other_user.first_name,
                other_user_img_url=other_user_img_url,
                last_message=c.last_message_id and "Last message placeholder",
                updated_at=c.updated_at,
            )
        )

    return result
