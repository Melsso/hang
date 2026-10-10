from fastapi import HTTPException
from sqlalchemy.orm import Session, aliased, selectinload
from sqlalchemy import or_, and_, func
import logging

from hang.schemas.conversations import ConversationPreview
from hang.models.db_models import User, Conversation, Message, UserBlock, Swipe

from hang.core.storage import StorageService
from hang.core.database import get_db_session


logger = logging.getLogger("Hang")


def fetch_conversations_list(
    db: Session, user_id: int, storage: StorageService
) -> list[ConversationPreview]:
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
        .filter(BlockA.id.is_(None))
        .filter(BlockB.id.is_(None))
        .order_by(Conversation.updated_at.desc())
        .all()
    )

    if not conversations:
        return []

    conv_ids = [c.conversation_id for c in conversations]
    other_ids = {
        c.user2_id if c.user1_id == user_id else c.user1_id for c in conversations
    }

    users = {
        u.user_id: u
        for u in db.query(User)
        .options(selectinload(User.images))
        .filter(User.user_id.in_(other_ids))
        .all()
    }

    last_ids = [c.last_message_id for c in conversations if c.last_message_id]
    last_message_map = (
        {
            m.message_id: m
            for m in db.query(Message).filter(Message.message_id.in_(last_ids)).all()
        }
        if last_ids
        else {}
    )

    unread_map = {
        cid: n
        for cid, n in db.query(Message.conversation_id, func.count(Message.message_id))
        .filter(
            Message.conversation_id.in_(conv_ids),
            Message.sender_id != user_id,
            Message.is_read.is_(False),
        )
        .group_by(Message.conversation_id)
        .all()
    }

    result = []
    for c in conversations:
        other_id = c.user2_id if c.user1_id == user_id else c.user1_id
        other = users.get(other_id)
        if other is None:
            continue
        last = last_message_map.get(c.last_message_id) if c.last_message_id else None
        result.append(
            ConversationPreview(
                conversation_id=c.conversation_id,
                other_user_id=other_id,
                other_user_name=other.first_name,
                other_user_img_url=storage.build_image_url(other.images[0].image_key)
                if other.images
                else None,
                last_message=last.content if last else None,
                last_message_at=last.created_at if last else None,
                unread_count=unread_map.get(c.conversation_id, 0),
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


def get_all_user_conversations(user_id: int) -> list[int]:
    with get_db_session() as db:
        conversations = (
            db.query(Conversation)
            .filter(
                (Conversation.user1_id == user_id) | (Conversation.user2_id == user_id)
            )
            .all()
        )
        filtered: list[int] = []

        blocks = (
            db.query(UserBlock)
            .filter(
                or_(UserBlock.blocker_id == user_id, UserBlock.blocked_id == user_id)
            )
            .all()
        )
        blocked_ids = {
            b.blocked_id if b.blocker_id == user_id else b.blocker_id for b in blocks
        }

        return [
            c.conversation_id
            for c in conversations
            if (c.user2_id if c.user1_id == user_id else c.user1_id) not in blocked_ids
        ]

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
