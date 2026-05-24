from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from typing import Annotated, Optional

from hang.schemas.swipes import SwipeCreate
from hang.schemas.conversations import ConversationResponse
from hang.models.db_models import User

from hang.core.database import get_db
from hang.core.storage import get_storage, StorageService
from hang.core.middleware import limiter

from hang.helpers.template_helpers import render
from hang.helpers.users import get_current_user, is_profile_incomplete
from hang.helpers.swipes import generate_suggested_profiles, process_swipe

swipe_router = APIRouter(prefix="/swipes", tags=["swipes"])


@swipe_router.get("/home")
@limiter.limit("5/minute")
def home_get(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    storage: Annotated[StorageService, Depends(get_storage)],
):
    if is_profile_incomplete(user=user):
        return RedirectResponse(
            url="/api/users/profile?edit=true&onboarding=true", status_code=303
        )

    profiles = generate_suggested_profiles(db=db, user=user, storage=storage)

    return render(
        request=request,
        template="home.html",
        context={"profiles": profiles},
    )


@swipe_router.post("/swipe-action", response_model=Optional[ConversationResponse])
@limiter.limit("25/minute")
def swipe_post(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    swipeData: SwipeCreate,
):
    conversation = process_swipe(db=db, swipeData=swipeData, user=user)
    if not conversation:
        return None

    return conversation
