from fastapi import Depends, Request, HTTPException, UploadFile
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from jose import jwt, JWTError

from typing import Annotated, Optional
from uuid import uuid4
import imghdr

from hang.schemas.users import UserResponse
from hang.schemas.config import settings
from hang.models.db_models import User, UserImage

from hang.helpers.database import get_db
from hang.helpers.storage import build_image_url, delete_s3_elements, upload_s3_elements


# TODO rework slightly, doesnt need to raise exception, that should be done explicitly in endpoint
def get_current_user(request: Request, db: Annotated[Session, Depends(get_db)]) -> User:
    token = request.cookies.get("access_token")

    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )

        user_id = payload.get("sub")

        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")

        user = db.query(User).filter(User.user_id == int(user_id)).first()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        return user

    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


def create_user_resp_data(user: User) -> dict:
    user_resp_data = UserResponse.model_validate(user).model_dump(mode="json")

    for img in user_resp_data["images"]:
        img["image_url"] = build_image_url(img["image_key"])

    return user_resp_data


def check_email_availability(db: Session, email: str, user_id: Optional[int]) -> bool:
    query = db.query(User).filter(User.email == email.lower())
    if user_id is not None:
        query = query.filter(User.user_id != user_id)

    return query.first() is None


def apply_profile_field_updates(user: User, update_data: dict) -> None:
    for key, value in update_data.items():
        if key in {"deleted_images", "images"}:
            continue

        if getattr(user, key, None) != value:
            setattr(user, key, value)


def apply_image_updates(user: User, update_data: dict, db: Session) -> list[str]:
    deleted_img_ids = set(update_data.get("deleted_images") or [])
    keys_to_delete = []

    images_to_delete = [img for img in user.images if img.image_id in deleted_img_ids]

    for img in images_to_delete:
        db.delete(img)
        keys_to_delete.append(img.image_key)

    image_updates = update_data.get("images") or []

    if image_updates:
        image_map = {
            img.image_id: img
            for img in user.images
            if img.image_id not in deleted_img_ids
        }

        for img_update in image_updates:
            img_id = img_update.get("image_id")
            position = img_update.get("position")
            img = image_map.get(img_id)

            if img and position is not None:
                img.position = position

        user.images.sort(key=lambda x: x.position)

    return keys_to_delete


def update_profile_info(db: Session, update_data: dict, user: User) -> None:
    apply_profile_field_updates(user, update_data)

    keys_to_delete = apply_image_updates(user, update_data, db)

    db.commit()
    db.refresh(user)

    delete_s3_elements(keys=keys_to_delete)


async def inspect_and_collect_files(
    files: list[UploadFile], current_count: int
) -> tuple[list[str], list[tuple[bytes, str]]]:
    errs: list[str] = []
    file_payloads: list[tuple[bytes, str]] = []

    if current_count + len(files) > settings.MAX_IMAGES:
        errs.append(f"Maximum of {settings.MAX_IMAGES} images allowed")
        return errs, file_payloads

    for f in files:
        contents = await f.read()

        if not contents:
            errs.append("Empty file provided.")
            continue

        if len(contents) > settings.MAX_IMAGE_SIZE:
            errs.append("File too large.")
            continue

        ext = imghdr.what(None, h=contents)

        if ext not in settings.ALLOWED_IMAGE_TYPES:
            errs.append("Image type not allowed.")
            continue

        file_payloads.append((contents, ext))

    return errs, file_payloads


def process_file_payloads(
    db: Session, file_payloads: list[tuple[bytes, str]], user: User
) -> Optional[list[str]]:
    next_position = max((img.position for img in user.images), default=-1) + 1

    elements_to_upload: list[tuple[str, bytes, str]] = []
    uploaded_keys: list[str] = []
    images_to_add: list[UserImage] = []

    for contents, ext in file_payloads:
        filename = f"{uuid4().hex}.{ext}"
        key = f"users/{user.user_id}/images/{filename}"

        elements_to_upload.append((key, contents, ext))
        uploaded_keys.append(key)

        images_to_add.append(
            UserImage(
                user_id=user.user_id,
                image_key=key,
                position=next_position,
            )
        )

        next_position += 1

    try:
        upload_s3_elements(files=elements_to_upload)

        for img in images_to_add:
            db.add(img)

        db.commit()

    except SQLAlchemyError:
        db.rollback()
        if uploaded_keys:
            delete_s3_elements(keys=uploaded_keys)

        return ["Failed to save uploaded images."]

    except Exception:
        if uploaded_keys:
            delete_s3_elements(keys=uploaded_keys)

        return ["Failed to upload images."]

    return None
