from sqlalchemy.orm import Session

import logging

from hang.models.db_models import User, UserBlock, UserReport


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


def get_user_reports(db: Session, user_id: int) -> list[UserReport]:
    return (
        db.query(UserReport)
        .filter(UserReport.reporter_id == user_id)
        .order_by(UserReport.created_at.desc())
        .all()
    )


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
