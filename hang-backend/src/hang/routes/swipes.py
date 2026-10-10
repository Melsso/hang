from fastapi import APIRouter, Depends, Request, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Annotated, Any

from hang.schemas.swipes import SwipeCreate, SwipeResponse
from hang.schemas.conversations import ConversationResponse
from hang.models.db_models import User

from hang.core.database import get_db
from hang.core.storage import get_storage, StorageService
from hang.core.middleware import limiter
from hang.helpers.users import get_current_user, is_profile_incomplete
from hang.helpers.swipes import generate_suggested_profiles, process_swipe, SwipeOutcome
from hang.helpers.ws import publish_user_event
from hang.core.limits import FREQUENT

swipe_router = APIRouter(prefix="/swipes", tags=["swipes"])


@swipe_router.get("/home", response_model=list[dict[str, Any]])
@limiter.limit(FREQUENT)
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
@limiter.limit(FREQUENT)
def swipe_post(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    swipeData: SwipeCreate,
):
    outcome, conversation = process_swipe(db=db, swipeData=swipeData, user=user)
    if outcome is SwipeOutcome.invalid:
        raise HTTPException(status_code=400, detail="Invalid swipe target")
    if outcome is SwipeOutcome.error:
        raise HTTPException(status_code=500, detail="Could not record swipe")

    if conversation is not None and conversation.user1_id == user.user_id:
        background_tasks.add_task(
            publish_user_event,
            swipeData.to_user_id,
            {
                "type": "match",
                "conversation_id": conversation.conversation_id,
                "user_id": user.user_id,
                "name": user.first_name,
            },
        )

    return SwipeResponse(
        success=True,
        conversation=(
            ConversationResponse.model_validate(conversation) if conversation else None
        ),
    )
