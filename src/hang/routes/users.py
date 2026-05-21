from fastapi import APIRouter, Depends, UploadFile, File, Request, HTTPException
from sqlalchemy.orm import Session
from typing import Annotated
import logging

from hang.schemas.users import (
    UserUpdate,
    Interests,
    ReportUserCreate,
    BlockUserCreate,
)
from hang.schemas.config import conf
from hang.models.db_models import User

from hang.core.database import get_db
from hang.core.storage import StorageService, get_storage

from hang.helpers.template_helpers import render, form_to_model
from hang.helpers.conversations import verify_conversation
from hang.helpers.users import (
    create_user_resp_data,
    check_email_availability,
    update_profile_info,
    inspect_and_collect_files,
    process_file_payloads,
    get_current_user,
    block_user,
    is_blocked,
    report_user,
)


user_router = APIRouter(prefix="/users", tags=["users"])
logger = logging.getLogger("Hang")


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
            "countries": conf.COUNTRIES,
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
                "countries": conf.COUNTRIES,
                "interests": Interests,
                "errors": ["Email already in use"],
            },
        )

    try:
        update_profile_info(db=db, update_data=update_data, user=user, storage=storage)
    except Exception as exc:
        logger.error(
            "hang_event",
            extra={
                "event": "user_update",
                "status": "failed",
                "error_type": type(exc).__name__,
                "error_message": str(exc),
                "context": {"location": "profile_post"},
            },
        )

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
    if is_blocked(db, user.user_id, user_id):
        raise HTTPException(
            status_code=403,
            detail={
                "redirect_url": request.headers.get("referer"),
                "reason": "user_blocked",
            },
        )

    if not verify_conversation(user.user_id, user_id):
        raise HTTPException(
            status_code=403,
            detail={
                "redirect_url": request.headers.get("referer"),
                "reason": "no_conversation_access",
            },
        )

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


@user_router.post("/profile/report-create")
def report_post(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    payload: ReportUserCreate,
):
    ok = report_user(
        db=db,
        reporter_id=user.user_id,
        reported_id=payload.reported_user_id,
        reason=payload.reason,
        message=payload.message,
    )

    return {"success": ok}


@user_router.post("/profile/block")
def block_post(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    payload: BlockUserCreate,
):
    ok = block_user(
        db=db,
        blocker_id=user.user_id,
        blocked_id=payload.blocked_user_id,
    )
    if ok:
        return render(
            request=request,
            template="profile.html",
            context={
                "user": create_user_resp_data(user=user, storage=get_storage()),
                "edit_mode": False,
                "viewer_mode": False,
                "countries": conf.COUNTRIES,
                "interests": Interests,
            },
        )
    return {"status": ok}


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
