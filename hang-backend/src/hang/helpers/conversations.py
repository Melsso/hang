from fastapi import HTTPException
from sqlalchemy.orm import Session, aliased
from sqlalchemy import or_, and_
from typing import Optional
import logging

from hang.schemas.conversations import ConversationPreview
from hang.models.db_models import User, Conversation, Message, UserBlock, Swipe

from hang.core.storage import StorageService
from hang.helpers.users import is_blocked


logger = logging.getLogger("Hang")


def fetch_conversations_list(
    db: Session, user_id: int, storage: StorageService
) -> Optional[list[ConversationPreview]]:
    BlockA = aliased(UserBlock)
    BlockB = aliased(UserBlock)
    conversations = (
        db.query(Conversation)
        .outerjoin(
            BlockA,
            (BlockA.blocker_id == user_id)
            & (
                (BlockA.blocked_id == Conversation.user1_id)
                | (BlockA.blocked_id == Conversation.user2_id)
            ),
        )
        .outerjoin(
            BlockB,
            (
                (BlockB.blocker_id == Conversation.user1_id)
                | (BlockB.blocker_id == Conversation.user2_id)
            )
            & (BlockB.blocked_id == user_id),
        )
        .filter((Conversation.user1_id == user_id) | (Conversation.user2_id == user_id))
        .filter(BlockA.id.is_(None))  # I did not block them
        .filter(BlockB.id.is_(None))  # they did not block me
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
            other_user_img_url = storage.build_image_url(other_user.images[0].image_key)

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


def get_user_conversation(
    db: Session, user_id: int, conversation_id: int
) -> Conversation:
    conversation = (
        db.query(Conversation)
        .filter(Conversation.conversation_id == conversation_id)
        .first()
    )

    if not conversation:
        raise HTTPException(
            status_code=403,
            detail={
                "redirect_url": "/api/swipes/home",
                "reason": "no_conversation_found",
            },
        )

    if user_id not in (conversation.user1_id, conversation.user2_id):
        raise HTTPException(
            status_code=403,
            detail={
                "redirect_url": "/api/swipes/home",
                "reason": "no_conversation_access",
            },
        )

    other_user_id = (
        conversation.user2_id
        if conversation.user1_id == user_id
        else conversation.user1_id
    )

    blocked = (
        db.query(UserBlock)
        .filter(
            or_(
                and_(
                    UserBlock.blocker_id == user_id,
                    UserBlock.blocked_id == other_user_id,
                ),
                and_(
                    UserBlock.blocker_id == other_user_id,
                    UserBlock.blocked_id == user_id,
                ),
            )
        )
        .first()
    )

    if blocked:
        raise HTTPException(
            status_code=403,
            detail={
                "redirect_url": "/api/swipes/home",
                "reason": "user_blocked",
            },
        )

    return conversation


def get_all_user_conversations(db: Session, user_id: int) -> list[Conversation]:
    conversations = (
        db.query(Conversation)
        .filter((Conversation.user1_id == user_id) | (Conversation.user2_id == user_id))
        .all()
    )

    filtered = []

    for c in conversations:
        other_user_id = c.user2_id if c.user1_id == user_id else c.user1_id

        if is_blocked(db, user_id, other_user_id):
            continue

        filtered.append(c)

    return filtered


def verify_conversation(db: Session, user1_id: int, user2_id: int) -> bool:
    return (
        db.query(Conversation)
        .filter(
            ((Conversation.user1_id == user1_id) & (Conversation.user2_id == user2_id))
            | (
                (Conversation.user1_id == user2_id)
                & (Conversation.user2_id == user1_id)
            )
        )
        .first()
        is not None
    )


def delete_conversation(db: Session, conversation_id: int, user_id: int):
    conversation = (
        db.query(Conversation)
        .filter(Conversation.conversation_id == conversation_id)
        .first()
    )
    if not conversation:
        return 404, "Conversation not found"
    if user_id not in (conversation.user1_id, conversation.user2_id):
        return 403, "Not authorized to delete this conversation"

    try:
        db.query(Swipe).filter(
            or_(
                and_(
                    Swipe.from_user_id == conversation.user1_id,
                    Swipe.to_user_id == conversation.user2_id,
                ),
                and_(
                    Swipe.from_user_id == conversation.user2_id,
                    Swipe.to_user_id == conversation.user1_id,
                ),
            )
        ).delete(synchronize_session=False)
        db.delete(conversation)
        db.commit()
        return 204, "Conversation deleted"
    except Exception as exc:
        db.rollback()
        logger.error(
            "hang_event",
            extra={
                "event": "db_conversation_delete",
                "status": "failed",
                "error_type": type(exc).__name__,
                "error_message": str(exc),
                "context": {
                    "location": "delete_conversation",
                    "user_id": user_id,
                    "conversation_id": conversation_id,
                },
            },
        )
        return 500, "Could not delete conversation"
