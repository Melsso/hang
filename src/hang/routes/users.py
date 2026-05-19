from fastapi import APIRouter, Depends, UploadFile, File, Request
from sqlalchemy.orm import Session
from uuid import uuid4
from typing import List, Annotated
import imghdr

from hang.schemas.users import UserResponse, UserUpdate, Interests
from hang.schemas.config import settings
from hang.models.db_models import User, UserImage

from hang.helpers.template_helpers import render, form_to_model
from hang.helpers.database import get_db
from hang.helpers.auth import (
    get_current_user,
)  # TODO this should be in users helpers not auth
from hang.helpers.storage import s3, build_image_url


user_router = APIRouter(prefix="/users", tags=["users"])


@user_router.get("/profile")
def profile_get(
    request: Request,
    user: Annotated[User, Depends(get_current_user)],
    edit: bool = False,
):
    user_resp = UserResponse.model_validate(user).model_dump(mode="json")

    for img in user_resp["images"]:
        img["image_url"] = build_image_url(img["image_key"])

    return render(
        request=request,
        template="profile.html",
        context={
            "user": user_resp,
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
    userData: Annotated[UserUpdate, Depends(form_to_model(UserUpdate))],
):
    update_data = userData.model_dump(exclude_unset=True)
    if "email" in update_data:
        update_data["email"] = update_data["email"].lower()
        existing_user = (
            db.query(User)
            .filter(User.email == update_data["email"])
            .filter(User.user_id != user.user_id)
            .first()
        )
        if existing_user:
            user_resp = UserResponse.model_validate(user).model_dump(mode="json")
            for img in user_resp["images"]:
                img["image_url"] = build_image_url(img["image_key"])

            return render(
                request=request,
                template="profile.html",
                context={
                    "errors": ["Email already in use"],
                    "user": user_resp,
                    "edit_mode": True,
                    "viewer_mode": False,
                },
            )

    for key, value in update_data.items():
        if key in {"deleted_images", "images"}:
            continue

        if getattr(user, key, None) != value:
            setattr(user, key, value)

    deleted_img_ids = set(update_data.get("deleted_images") or [])
    images_to_delete = [img for img in user.images if img.image_id in deleted_img_ids]

    keys_to_delete = []
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

    db.commit()
    db.refresh(user)
    for key in keys_to_delete:
        s3.delete_object(Bucket=settings.R2_BUCKET_NAME, Key=key)

    user_resp = UserResponse.model_validate(user).model_dump(mode="json")
    for img in user_resp["images"]:
        img["image_url"] = build_image_url(img["image_key"])

    return render(
        request=request,
        template="profile.html",
        context={
            "user": user_resp,
            "edit_mode": False,
            "viewer_mode": False,
        },
    )


@user_router.get("/profile/{user_id}")
def visit_profile_get(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    user_id: int,
):
    target_user = db.query(User).filter(User.user_id == user_id).first()
    target_user_resp = UserResponse.model_validate(target_user).model_dump(mode="json")
    for img in target_user_resp["images"]:
        img["image_url"] = build_image_url(img["image_key"])

    return render(
        request=request,
        template="profile.html",
        context={
            "user": target_user_resp,
            "edit_mode": False,
            "viewer_mode": True,
        },
    )


@user_router.post("/profile/upload-image")
async def profile_image_upload_post(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    files: List[UploadFile] = File(...),
):
    errs: List[str] = []

    current_count = len(user.images)

    if current_count + len(files) > settings.MAX_IMAGES:
        errs.append(f"Maximum of {settings.MAX_IMAGES} images allowed")

    file_payloads = []

    for f in files:
        contents = await f.read()

        if not contents:
            errs.append("Empty file provided.")

        if len(contents) > settings.MAX_IMAGE_SIZE:
            errs.append("File too large.")

        ext = imghdr.what(None, h=contents)

        if ext not in settings.ALLOWED_IMAGE_TYPES:
            errs.append("Image type not allowed.")

        file_payloads.append((contents, ext))

    if errs:
        fresh_user = db.query(User).filter(User.user_id == user.user_id).first()
        user_resp = UserResponse.model_validate(fresh_user).model_dump(mode="json")
        for img in user_resp["images"]:
            img["image_url"] = build_image_url(img["image_key"])

        return render(
            request=request,
            template="profile.html",
            context={
                "user": user_resp,
                "errors": errs,
                "edit_mode": False,
                "viewer_mode": False,
                "countries": settings.COUNTRIES,
                "interests": Interests,
            },
        )

    next_position = max((img.position for img in user.images), default=-1) + 1
    uploaded_keys = []
    try:
        for contents, ext in file_payloads:
            filename = f"{uuid4().hex}.{ext}"
            key = f"users/{user.user_id}/images/{filename}"

            s3.put_object(
                Bucket=settings.R2_BUCKET_NAME,
                Key=key,
                Body=contents,
                ContentType=f"image/{ext}",
            )
            uploaded_keys.append(key)

            db.add(
                UserImage(
                    user_id=user.user_id,
                    image_key=key,
                    position=next_position,
                )
            )
            next_position += 1

        db.commit()

    except Exception:
        db.rollback()
        for key in uploaded_keys:
            s3.delete_object(Bucket=settings.R2_BUCKET_NAME, Key=key)

        fresh_user = db.query(User).filter(User.user_id == user.user_id).first()
        user_resp = UserResponse.model_validate(fresh_user).model_dump(mode="json")
        for img in user_resp["images"]:
            img["image_url"] = build_image_url(img["image_key"])

        return render(
            request=request,
            template="profile.html",
            context={
                "user": user_resp,
                "errors": ["Unexpected error happened."],
                "edit_mode": False,
                "viewer_mode": False,
                "countries": settings.COUNTRIES,
                "interests": Interests,
            },
        )

    fresh_user = db.query(User).filter(User.user_id == user.user_id).first()
    user_resp = UserResponse.model_validate(fresh_user).model_dump(mode="json")
    for img in user_resp["images"]:
        img["image_url"] = build_image_url(img["image_key"])

    return render(
        request=request,
        template="profile.html",
        context={
            "user": user_resp,
            "errors": [],
            "edit_mode": False,
            "viewer_mode": False,
            "countries": settings.COUNTRIES,
            "interests": Interests,
        },
    )
