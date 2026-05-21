from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from typing import Annotated

from hang.schemas.swipes import SwipeCreate
from hang.schemas.conversations import ConversationResponse
from hang.models.db_models import User

from hang.core.database import get_db
from hang.core.storage import get_storage, StorageService

from hang.helpers.template_helpers import render
from hang.helpers.users import get_current_user
from hang.helpers.swipes import generate_suggested_profiles, process_swipe

swipe_router = APIRouter(prefix="/swipes", tags=["swipes"])


@swipe_router.get("/home")
def home_get(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    storage: Annotated[StorageService, Depends(get_storage)],
):
    profiles = generate_suggested_profiles(db=db, user=user, storage=storage)

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

    conversation = process_swipe(db=db, swipeData=swipeData, user=user)
    conv_resp = ConversationResponse.model_validate(conversation)
    return conv_resp
