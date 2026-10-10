from sqlalchemy.orm import Session

from typing import Optional

from hang.schemas.conversations import MessagePreview
from hang.models.db_models import Message, Conversation


def get_conversation_messages(
    db: Session,
    conversation_id: int,
    limit: int = 20,
    before_message_id: Optional[int] = None,
) -> tuple[list[MessagePreview], Optional[int], bool]:
    query = db.query(Message).filter(Message.conversation_id == conversation_id)

    if before_message_id is not None:
        query = query.filter(Message.message_id < before_message_id)

    messages = query.order_by(Message.message_id.desc()).limit(limit + 1).all()
    has_more = len(messages) > limit
    if has_more:
        messages = messages[:limit]

    next_cursor = messages[-1].message_id if messages and has_more else None
    messages.reverse()

    return ([MessagePreview.model_validate(m) for m in messages], next_cursor, has_more)


def create_message(
    db: Session, conversation_id: int, sender_id: int, content: str
) -> Message:
    message = Message(
        conversation_id=conversation_id,
        sender_id=sender_id,
        content=content,
        is_read=False,
    )

    db.add(message)
    db.flush()

    return message


def mark_conversation_messages_read(
    db: Session,
    conversation_id: int,
    user_id: int,
) -> None:
    (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .filter(Message.sender_id != user_id)
        .filter(Message.is_read.is_(False))
        .update({"is_read": True})
    )
    db.commit()


def send_message_flow(
    db: Session, conversation_id: int, sender_id: int, content: str
) -> Message:

    message = create_message(
        db=db,
        conversation_id=conversation_id,
        sender_id=sender_id,
        content=content,
    )

    (
        db.query(Conversation)
        .filter(Conversation.conversation_id == conversation_id)
        .update({"last_message_id": message.message_id})
    )

    return message
