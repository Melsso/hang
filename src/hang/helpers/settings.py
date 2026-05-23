from sqlalchemy.orm import Session, selectinload
from typing import Tuple
from datetime import datetime, timezone

import logging

from hang.core.storage import StorageService

from hang.models.db_models import User, UserBlock, UserReport
from hang.schemas.settings import ReportResponse, PasswordChange

from hang.helpers.auth import verify_password, hash_password

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


def change_password(
    db: Session, user: User, pass_data: PasswordChange
) -> Tuple[bool, str]:
    if user.auth_provider != "local":
        return False, "Google users cannot change password"

    if not user.password_hash:
        return False, "No password set"

    if not verify_password(pass_data.old_password, user.password):
        return False, "Wrong password"

    if verify_password(pass_data.new_password, user.password):
        return False, "New and old password are identical"

    new_hash = hash_password(password=pass_data.new_password)
    user.password = new_hash
    user.updated_at = datetime.now(timezone.utc)

    db.add(user)
    db.commit()

    return True, ""


def delete_user(db: Session, user: User, storage: StorageService) -> bool:
    img_keys = [img.image_key for img in user.images]

    try:
        db.delete(user)
        db.commit()

    except Exception:
        db.rollback()
        raise

    if img_keys:
        storage.delete_many(keys=img_keys)

    return True
