from sqlalchemy.orm import Session
from typing import Optional

from hang.schemas.swipes import SwipeType, SwipeCreate
from hang.schemas.users import UserSwipeProfile
from hang.models.db_models import User, Swipe, Conversation

from hang.core.storage import StorageService


def fetch_candidate_profiles(db: Session, user_id: int) -> list[User]:
    swiped_subq = (
        db.query(Swipe.to_user_id).filter(Swipe.from_user_id == user_id).subquery()
    )

    candidates = (
        db.query(User)
        .filter(User.user_id != user_id)
        .filter(User.is_active.is_(True))
        .filter(~User.user_id.in_(swiped_subq))
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


def generate_suggested_profiles(
    db: Session, user: User, storage: StorageService
) -> Optional[list[UserSwipeProfile]]:
    profiles: list[UserSwipeProfile] = []

    candidates = fetch_candidate_profiles(db=db, user_id=user.user_id)
    if not candidates:
        return []

    for candidate in candidates:
        profile = UserSwipeProfile.model_validate(candidate).model_dump(mode="json")

        for img in profile["images"]:
            img["image_url"] = storage.build_image_url(img["image_key"])

        profile["score"] = calc_user_score(candidate=candidate, user=user)

        profiles.append(profile)

    profiles.sort(key=lambda x: x["score"], reverse=True)

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
) -> Optional[Conversation]:
    # TODO exception handling
    try:
        swipe = Swipe(
            from_user_id=user.user_id,
            to_user_id=swipeData.to_user_id,
            swipe_type=swipeData.swipe_type,
        )
        db.add(swipe)

        conversation = None

        if swipeData.swipe_type in [SwipeType.like, SwipeType.super_like]:
            if is_match(
                db=db,
                user_id=user.user_id,
                target_user_id=swipeData.to_user_id,
            ):
                conversation = Conversation(
                    user1_id=user.user_id,
                    user2_id=swipeData.to_user_id,
                )
                db.add(conversation)
                db.flush()

        db.commit()

        if conversation:
            db.refresh(conversation)

        return conversation

    except Exception:
        db.rollback()
        return None
