from sqlalchemy.orm import Session
from typing import Optional

from hang.schemas.conversations import ConversationPreview
from hang.models.db_models import User, Conversation, Message

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

    last_message_ids = [c.last_message_id for c in conversations if c.last_message_id]

    last_messages = (
        db.query(Message).filter(Message.message_id.in_(last_message_ids)).all()
    )

    last_message_map = {m.message_id: m for m in last_messages}

    unread_rows = (
        db.query(
            Message.conversation_id,
        )
        .filter(
            Message.conversation_id.in_([c.conversation_id for c in conversations]),
            Message.sender_id != user_id,
            Message.is_read.is_(False),
        )
        .all()
    )

    unread_map = {}
    for row in unread_rows:
        conv_id = row[0]
        unread_map[conv_id] = unread_map.get(conv_id, 0) + 1

    result = []

    for c in conversations:
        other_user_id = c.user2_id if c.user1_id == user_id else c.user1_id

        other_user = db.query(User).filter(User.user_id == other_user_id).first()

        other_user_img_url = None
        if other_user and other_user.images:
            other_user_img_url = build_image_url(other_user.images[0].image_key)

        last_msg_obj = last_message_map.get(c.last_message_id)

        unread_count = unread_map.get(c.conversation_id, 0)

        result.append(
            ConversationPreview(
                conversation_id=c.conversation_id,
                other_user_id=other_user_id,
                other_user_name=other_user.first_name,
                other_user_img_url=other_user_img_url,
                last_message=last_msg_obj.content if last_msg_obj else None,
                last_message_at=last_msg_obj.created_at if last_msg_obj else None,
                unread_count=unread_count,
                updated_at=c.updated_at,
            )
        )

    return result


# TODO raise exception rather than returning none in future
def get_user_conversation(
    db: Session, user_id: int, conversation_id: int
) -> Optional[Conversation]:
    conversation = (
        db.query(Conversation)
        .filter(Conversation.conversation_id == conversation_id)
        .first()
    )

    if not conversation:
        return None

    if user_id not in [conversation.user1_id, conversation.user2_id]:
        return None

    return conversation


def get_all_user_conversations(
    db: Session, user_id: int
) -> Optional[list[Conversation]]:
    return (
        db.query(Conversation)
        .filter((Conversation.user1_id == user_id) | (Conversation.user2_id == user_id))
        .all()
    )
