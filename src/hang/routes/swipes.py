from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from typing import Annotated
from collections import defaultdict

from hang.schemas.swipes import SwipeType, SwipeCreate, SwipeResponse
from hang.schemas.users import UserSwipeProfile
from hang.schemas.conversations import ConversationResponse
from hang.models.db_models import User, Swipe, UserImage, Conversation

from hang.helpers.template_helpers import render
from hang.helpers.users import get_current_user
from hang.helpers.database import get_db
from hang.helpers.storage import build_image_url


swipe_router = APIRouter(prefix="/swipes", tags=["swipes"])


@swipe_router.get("/home")
def home_get(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    user_id = user.user_id

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

    if not candidates:
        return render(request=request, template="home.html", context={"profiles": []})

    candidate_ids = [u.user_id for u in candidates]
    images = (
        db.query(UserImage)
        .filter(UserImage.user_id.in_(candidate_ids))
        .order_by(UserImage.position)
        .all()
    )

    image_map = defaultdict(list)
    for img in images:
        image_map[img.user_id].append(img)

    def score(u: User):
        score = 0

        if u.country == user.country:
            score += 3

        score += len(set(u.interests) & set(user.interests))

        if user.interested_in.value == "everyone":
            score += 2
        elif user.interested_in.value == u.gender.value:
            score += 4

        return score

    profiles = []
    for u in candidates:
        profile = UserSwipeProfile.model_validate(u).model_dump(mode="json")
        profile["images"] = [
            {
                "image_id": img.image_id,
                "image_url": build_image_url(img.image_key),
                "position": img.position,
            }
            for img in image_map.get(u.user_id, [])
        ]
        profile["score"] = score(u)
        profiles.append(profile)

    profiles.sort(key=lambda x: x["score"], reverse=True)
    return render(
        request=request,
        template="home.html",
        context={"profiles": profiles},
    )


@swipe_router.post("/swipe-action")
def swipe_post(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    swipeData: SwipeCreate,
):
    swipe = Swipe(
        from_user_id=user.user_id,
        to_user_id=swipeData.to_user_id,
        swipe_type=swipeData.swipe_type,
    )
    db.add(swipe)
    db.commit()
    conversation_out = None

    if swipeData.swipe_type in [SwipeType.like, SwipeType.super_like]:
        reciprocal_swipe = (
            db.query(Swipe)
            .filter(Swipe.from_user_id == swipeData.to_user_id)
            .filter(Swipe.to_user_id == user.user_id)
            .filter(Swipe.swipe_type.in_([SwipeType.like, SwipeType.super_like]))
            .first()
        )

        if reciprocal_swipe:
            conversation = Conversation(
                user1_id=user.user_id, user2_id=swipeData.to_user_id
            )
            db.add(conversation)
            db.commit()
            db.refresh(conversation)

            conversation_out = ConversationResponse.model_validate(conversation)

    # TODO this model is not it
    return SwipeResponse(success=True, conversation=conversation_out)
