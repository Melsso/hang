from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.orm import Session
from typing import Annotated

from hang.schemas.swipes import SwipeCreate, SwipeResponse
from hang.schemas.users import UserSwipeProfile
from hang.schemas.conversations import ConversationResponse
from hang.models.db_models import User

from hang.core.database import get_db
from hang.core.storage import get_storage, StorageService
from hang.core.middleware import limiter

from hang.helpers.users import get_current_user, is_profile_incomplete
from hang.helpers.swipes import generate_suggested_profiles, process_swipe

swipe_router = APIRouter(prefix="/swipes", tags=["swipes"])


@swipe_router.get("/home", response_model=list[UserSwipeProfile])
@limiter.limit("25/minute")
def home_get(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    storage: Annotated[StorageService, Depends(get_storage)],
):
    if is_profile_incomplete(user=user):
        raise HTTPException(status_code=403, detail="Profile incomplete")

    profiles = generate_suggested_profiles(db=db, user=user, storage=storage)

    return profiles


@swipe_router.post("/swipe-action", response_model=SwipeResponse)
@limiter.limit("25/minute")
def swipe_post(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    swipeData: SwipeCreate,
):
    conversation = process_swipe(db=db, swipeData=swipeData, user=user)
    conversation_response = None

    if conversation:
        conversation_response = ConversationResponse.model_validate(conversation)

    return SwipeResponse(success=True, conversation=conversation_response)
