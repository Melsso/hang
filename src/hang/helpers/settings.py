from sqlalchemy.orm import Session, selectinload

import logging

from hang.models.db_models import User, UserBlock, UserReport
from hang.schemas.settings import ReportResponse

logger = logging.getLogger("Hang")


def unblock_user(db: Session, blocker_id: int, blocked_id: int) -> bool:
    block = (
        db.query(UserBlock)
        .filter(
            UserBlock.blocker_id == blocker_id,
            UserBlock.blocked_id == blocked_id,
        )
        .first()
    )

    if not block:
        return False

    db.delete(block)
    db.commit()

    return True


def get_user_reports(db: Session, user_id: int) -> list[ReportResponse]:
    reports = (
        db.query(UserReport)
        .options(selectinload(UserReport.reported))
        .filter(UserReport.reporter_id == user_id)
        .order_by(UserReport.created_at.desc())
        .all()
    )

    return [
        ReportResponse(
            first_name=r.reported.first_name,
            last_name=r.reported.last_name,
            reported_id=r.reported_id,
            reason=r.reason,
            message=r.message,
            created_at=r.created_at,
        )
        for r in reports
    ]


def delete_report(db: Session, reporter_id: int, reported_id: int) -> bool:
    report = (
        db.query(UserReport)
        .filter(
            UserReport.reporter_id == reporter_id,
            UserReport.reported_id == reported_id,
        )
        .first()
    )

    if not report:
        return False

    db.delete(report)
    db.commit()

    return True


def get_blocked_users(db: Session, user_id: int) -> list[User]:
    rows = (
        db.query(User)
        .join(UserBlock, User.user_id == UserBlock.blocked_id)
        .filter(UserBlock.blocker_id == user_id)
        .all()
    )

    return rows
