from fastapi import APIRouter, Depends, UploadFile, File, Request
from sqlalchemy.orm import Session
from typing import Annotated

from hang.schemas.users import UserUpdate, Interests
from hang.schemas.config import settings
from hang.models.db_models import User

from hang.core.database import get_db
from hang.core.storage import StorageService, get_storage

from hang.helpers.template_helpers import render, form_to_model
from hang.helpers.users import (
    create_user_resp_data,
    check_email_availability,
    update_profile_info,
    inspect_and_collect_files,
    process_file_payloads,
    get_current_user,
)

user_router = APIRouter(prefix="/users", tags=["users"])


@user_router.get("/profile")
def profile_get(
    request: Request,
    user: Annotated[User, Depends(get_current_user)],
    storage: Annotated[StorageService, Depends(get_storage)],
    edit: bool = False,
):
    user_resp_data = create_user_resp_data(user=user, storage=storage)

    return render(
        request=request,
        template="profile.html",
        context={
            "user": user_resp_data,
            "edit_mode": edit,
            "viewer_mode": False,
            "countries": settings.COUNTRIES,
            "interests": Interests,
        },
    )


@user_router.post("/profile")
def profile_post(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    storage: Annotated[StorageService, Depends(get_storage)],
    userData: Annotated[UserUpdate, Depends(form_to_model(UserUpdate))],
):
    update_data = userData.model_dump(exclude_unset=True)
    if "email" in update_data and not check_email_availability(
        db=db, email=update_data["email"], user_id=user.user_id
    ):
        return render(
            request=request,
            template="profile.html",
            context={
                "user": create_user_resp_data(user=user, storage=storage),
                "edit_mode": True,
                "viewer_mode": False,
                "countries": settings.COUNTRIES,
                "interests": Interests,
                "errors": ["Email already in use"],
            },
        )

    update_profile_info(db=db, update_data=update_data, user=user, storage=storage)

    return render(
        request=request,
        template="profile.html",
        context={
            "user": create_user_resp_data(user=user, storage=storage),
            "edit_mode": False,
            "viewer_mode": False,
        },
    )


@user_router.get("/profile/{user_id}")
def visit_profile_get(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    storage: Annotated[StorageService, Depends(get_storage)],
    user_id: int,
):
    target_user = db.query(User).filter(User.user_id == user_id).first()

    return render(
        request=request,
        template="profile.html",
        context={
            "user": create_user_resp_data(user=target_user, storage=storage),
            "edit_mode": False,
            "viewer_mode": True,
        },
    )


@user_router.post("/profile/upload-image")
async def profile_image_upload_post(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    storage: Annotated[StorageService, Depends(get_storage)],
    files: list[UploadFile] = File(...),
):
    errs, file_payloads = await inspect_and_collect_files(
        files=files, current_count=len(user.images)
    )
    if errs:
        return render(
            request=request,
            template="profile.html",
            context={
                "user": create_user_resp_data(user, storage=storage),
                "edit_mode": False,
                "viewer_mode": False,
                "errors": errs,
            },
        )

    errs = process_file_payloads(
        db=db, file_payloads=file_payloads, user=user, storage=storage
    )

    fresh_user = db.query(User).filter(User.user_id == user.user_id).first()
    return render(
        request=request,
        template="profile.html",
        context={
            "user": create_user_resp_data(user=fresh_user, storage=storage),
            "edit_mode": False,
            "viewer_mode": False,
            "errors": errs or [],
        },
    )
