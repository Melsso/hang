from sqlalchemy.orm import Session

from hang.schemas.conversations import MessagePreview
from hang.models.db_models import Message, Conversation


def get_conversation_messages(
    db: Session, conversation_id: int
) -> list[MessagePreview]:
    messages = (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc())
        .all()
    )

    return [MessagePreview.model_validate(m) for m in messages]


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


def update_last_message(conversation: Conversation, message: Message) -> None:
    conversation.last_message_id = message.message_id


def mark_message_read(message: Message) -> None:
    message.is_read = True


def mark_conversation_messages_read(
    db: Session, conversation_id: int, user_id: int
) -> None:
    (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .filter(Message.sender_id != user_id)
        .filter(Message.is_read.is_(False))
        .update({"is_read": True})
    )


def send_message_flow(
    db: Session, conversation: Conversation, sender_id: int, content: str
) -> Message:

    message = create_message(
        db=db,
        conversation_id=conversation.conversation_id,
        sender_id=sender_id,
        content=content,
    )

    update_last_message(conversation=conversation, message=message)

    db.commit()
    db.refresh(message)

    return message
