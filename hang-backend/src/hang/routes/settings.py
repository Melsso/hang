from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Annotated
import logging

from hang.schemas.users import BlockUserCreate
from hang.schemas.settings import (
    BlockedUserResponse,
    ReportResponse,
    DeleteReportRequest,
    PasswordChange,
)
from hang.models.db_models import User

from hang.core.database import get_db
from hang.core.storage import StorageService, get_storage
from hang.core.middleware import limiter
from hang.helpers.users import get_current_user
from hang.helpers.settings import (
    get_blocked_users,
    unblock_user,
    get_user_reports,
    delete_report,
    delete_user,
    change_password,
)
from hang.core.limits import FREQUENT, WRITE, AUTH, DELETE_ACCOUNT


settings_router = APIRouter(prefix="/settings", tags=["settings"])
logger = logging.getLogger("Hang")


@settings_router.get("/reports", response_model=list[ReportResponse])
@limiter.limit(FREQUENT)
def get_reports(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    reports = get_user_reports(db=db, user_id=user.user_id)

    return reports


@settings_router.post("/report-delete")
@limiter.limit(WRITE)
def delete_report_post(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    payload: DeleteReportRequest,
):
    ok = delete_report(
        db=db,
        reporter_id=user.user_id,
        reported_id=payload.reported_user_id,
    )
    if not ok:
        return JSONResponse(
            status_code=400,
            content={"success": False},
        )

    return {"success": ok}


@settings_router.get("/blocks", response_model=list[BlockedUserResponse])
@limiter.limit(FREQUENT)
def blocked_lst_get(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    blocked = get_blocked_users(db=db, user_id=user.user_id)

    return blocked


@settings_router.post("/unblock")
@limiter.limit(WRITE)
def unblock_post(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    payload: BlockUserCreate,
):
    ok = unblock_user(
        db=db,
        blocker_id=user.user_id,
        blocked_id=payload.blocked_user_id,
    )
    if not ok:
        return JSONResponse(
            status_code=400,
            content={"success": False},
        )

    return {"success": ok}


@settings_router.post("/change-password")
@limiter.limit(AUTH)
def change_user_password(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    pass_data: PasswordChange,
):
    success, msg = change_password(db=db, user=user, pass_data=pass_data)
    if not success:
        return JSONResponse(
            status_code=400,
            content={"success": False, "msg": msg},
        )

    return {
        "success": True,
        "msg": msg,
    }


@settings_router.post("/delete-account")
@limiter.limit(DELETE_ACCOUNT)
def delete_user_post(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    storage: Annotated[StorageService, Depends(get_storage)],
):
    ok = delete_user(db=db, user=user, storage=storage)
    if not ok:
        return JSONResponse(
            status_code=400,
            content={"success": False},
        )
    response = JSONResponse(content={"success": True})
    response.delete_cookie(key="access_token", httponly=True, samesite="lax")
    return response
