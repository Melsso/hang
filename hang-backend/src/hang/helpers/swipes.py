from sqlalchemy.orm import Session, aliased, selectinload
from sqlalchemy import select, func, and_, or_
from enum import Enum
from sqlalchemy.exc import IntegrityError

from typing import Optional, Any

import logging

from hang.schemas.swipes import SwipeType, SwipeCreate
from hang.schemas.users import UserSwipeProfile

from hang.models.db_models import User, Swipe, Conversation, UserBlock

from hang.helpers.users import is_blocked

logger = logging.getLogger("Hang")


class SwipeOutcome(str, Enum):
    ok = "ok"
    duplicate = "duplicate"
    invalid = "invalid"
    error = "error"


CANDIDATE_POOL = 200
PAGE_SIZE = 20


def fetch_candidate_profiles(db: Session, user_id: int) -> list[User]:
    swiped_subq = select(Swipe.to_user_id).where(Swipe.from_user_id == user_id)

    Block1 = aliased(UserBlock)
    Block2 = aliased(UserBlock)

    candidates = (
        db.query(User)
        .options(selectinload(User.images))
        .outerjoin(
            Block1, (Block1.blocker_id == user_id) & (Block1.blocked_id == User.user_id)
        )
        .outerjoin(
            Block2, (Block2.blocker_id == User.user_id) & (Block2.blocked_id == user_id)
        )
        .filter(User.user_id != user_id)
        .filter(User.is_active.is_(True))
        .filter(~User.user_id.in_(swiped_subq))
        .filter(Block1.id.is_(None))
        .filter(Block2.id.is_(None))
        .filter(
            User.bio != "",
            User.birthdate.is_not(None),
            func.cardinality(User.interests) > 0,
        )
        .order_by(func.random())
        .limit(CANDIDATE_POOL)
        .all()
    )

    return candidates


def calc_user_score(candidate: User, user: User) -> int:
    score = 0

    if candidate.country == user.country:
        score += 3

    score += len(set(candidate.interests) & set(user.interests))

    if user.interested_in.value == "everyone":
        score += 2
    elif user.interested_in.value == candidate.gender.value:
        score += 4

    return score


def generate_suggested_profiles(db, user, storage) -> list[dict[str, Any]]:
    candidates = fetch_candidate_profiles(db=db, user_id=user.user_id)
    top = sorted(candidates, key=lambda c: calc_user_score(c, user), reverse=True)[
        :PAGE_SIZE
    ]
    profiles = []
    for candidate in top:
        profile = UserSwipeProfile.model_validate(candidate).model_dump(mode="json")
        for img in profile["images"]:
            img["image_url"] = storage.build_image_url(img["image_key"])
        profile["score"] = calc_user_score(candidate=candidate, user=user)
        profiles.append(profile)
    return profiles


def is_match(db: Session, user_id: int, target_user_id: int) -> bool:
    return (
        db.query(Swipe)
        .filter(Swipe.from_user_id == target_user_id)
        .filter(Swipe.to_user_id == user_id)
        .filter(Swipe.swipe_type.in_([SwipeType.like, SwipeType.super_like]))
        .first()
        is not None
    )


def process_swipe(
    db: Session, swipeData: SwipeCreate, user: User
) -> tuple[SwipeOutcome, Optional[Conversation]]:
    target_id = swipeData.to_user_id
    target_ok = (
        target_id != user.user_id
        and db.query(User.user_id)
        .filter(User.user_id == target_id, User.is_active.is_(True))
        .first()
        is not None
        and not is_blocked(db, user.user_id, target_id)
    )
    if not target_ok:
        return SwipeOutcome.invalid, None

    try:
        db.add(
            Swipe(
                from_user_id=user.user_id,
                to_user_id=target_id,
                swipe_type=swipeData.swipe_type,
            )
        )
        db.flush()
    except IntegrityError:
        db.rollback()
        return SwipeOutcome.duplicate, None

    try:
        conversation = None
        if swipeData.swipe_type in (SwipeType.like, SwipeType.super_like) and is_match(
            db=db, user_id=user.user_id, target_user_id=target_id
        ):
            try:
                with db.begin_nested():
                    conversation = Conversation(
                        user1_id=user.user_id, user2_id=target_id
                    )
                    db.add(conversation)
            except IntegrityError:
                conversation = (
                    db.query(Conversation)
                    .filter(
                        or_(
                            and_(
                                Conversation.user1_id == user.user_id,
                                Conversation.user2_id == target_id,
                            ),
                            and_(
                                Conversation.user1_id == target_id,
                                Conversation.user2_id == user.user_id,
                            ),
                        )
                    )
                    .first()
                )

        db.commit()
        if conversation:
            db.refresh(conversation)
        return SwipeOutcome.ok, conversation

    except Exception as exc:
        db.rollback()
        logger.error(
            "hang_event",
            extra={
                "event": "db_swipe_create",
                "status": "failed",
                "error_type": type(exc).__name__,
                "error_message": str(exc),
                "context": {"location": "process_swipe", "user_id": user.user_id},
            },
        )
        return SwipeOutcome.error, None
