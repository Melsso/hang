from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from typing import Annotated
import logging

from hang.schemas.users import BlockUserCreate
from hang.schemas.settings import (
    BlockedUserResponse,
    ReportResponse,
    DeleteReportRequest,
)
from hang.models.db_models import User

from hang.core.database import get_db

from hang.helpers.template_helpers import render
from hang.helpers.users import get_current_user
from hang.helpers.settings import (
    get_blocked_users,
    unblock_user,
    get_user_reports,
    delete_report,
)


settings_router = APIRouter(prefix="/settings", tags=["settings"])
logger = logging.getLogger("Hang")


@settings_router.get("/")
def settings_get(
    request: Request,
    user: Annotated[User, Depends(get_current_user)],
):
    return render(request=request, template="settings.html")


@settings_router.get("/reports")
def get_reports(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    reports = get_user_reports(db=db, user_id=user.user_id)

    report_resp = [ReportResponse.model_validate(r).model_dump() for r in reports]
    return render(
        request=request, template="settings.html", context={"reports": report_resp}
    )


@settings_router.post("/report-delete")
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

    return {"success": ok}


@settings_router.get("/blocks")
def blocked_lst_get(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    blocked = get_blocked_users(db=db, user_id=user.user_id)

    blocked_users_resp = [
        BlockedUserResponse.model_validate(u).model_dump() for u in blocked
    ]
    return render(
        request=request,
        template="settings.html",
        context={"blocks": blocked_users_resp},
    )


@settings_router.post("/unblock")
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

    return {"success": ok}
