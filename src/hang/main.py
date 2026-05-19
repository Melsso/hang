from fastapi import FastAPI, Depends, Request, UploadFile, File
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from typing import List
from collections import defaultdict
from uuid import uuid4
import imghdr


from hang.models.user import (
    UserCreate,
    UserLogin,
    UserResponse,
    UserUpdate,
    Interests,
    UserSwipeProfile,
)
from hang.models.swipe import SwipeCreate, SwipeType, SwipeResponse
from hang.models.conversation import (
    ConversationResponse,
    ConversationPreview,
    ConversationListResponse,
)
from hang.models.config import settings
from hang.models.message import MessagePreview, MessageListResponse
from hang.schemas.schemas import (
    Base,
    UserDB,
    SwipeDB,
    ConversationDB,
    MessageDB,
    UserImageDB,
)
from hang.helpers.database import engine, get_db
from hang.helpers.storage import s3, build_image_url
from hang.helpers.exceptions import register_exception_handlers
from hang.helpers.template_helpers import render, form_to_model
from hang.helpers.auth import (
    verify_password,
    hash_password,
    create_access_token,
    get_current_user,
)


Base.metadata.create_all(bind=engine)

app = FastAPI()
app.mount("/static", StaticFiles(directory=settings.STATIC_DIRECTORY), name="static")

register_exception_handlers(app)


@app.get("/")
def landing_get(request: Request):
    return render(request, "landing.html")


@app.get("/login")
def login_get(request: Request):
    return render(request, "login.html")


@app.post("/login")
def login_post(
    request: Request,
    userData: UserLogin = Depends(form_to_model(UserLogin)),
    db: Session = Depends(get_db),
):
    email = userData.email.lower()

    user = db.query(UserDB).filter(UserDB.email == email).first()

    if not user or not verify_password(userData.password, user.password):
        return render(request, "login.html", {"errors": ["Invalid credentials"]})

    token = create_access_token({"sub": str(user.user_id), "email": user.email})

    response = RedirectResponse(url="/home", status_code=303)

    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        samesite="lax",
        secure=False,  # True for HTTPS laterrs
        max_age=60 * 60,
    )

    return response


@app.get("/register")
def register_get(request: Request):
    return render(
        request,
        "register.html",
        {"countries": settings.COUNTRIES, "interests": Interests},
    )


@app.post("/register")
def register_post(
    request: Request,
    userData: UserCreate = Depends(form_to_model(UserCreate)),
    db: Session = Depends(get_db),
):
    email = userData.email.lower()
    existing_user = db.query(UserDB).filter(UserDB.email == email).first()
    if existing_user:
        return render(request, "register.html", {"errors": ["Email already in use"]})

    hashed_password = hash_password(userData.password)

    new_user = UserDB(
        first_name=userData.first_name,
        last_name=userData.last_name,
        email=email,
        password=hashed_password,
        birthdate=userData.birthdate,
        bio=userData.bio,
        country=userData.country,
        gender=userData.gender,
        interested_in=userData.interested_in,
        interests=userData.interests,
        is_active=True,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return RedirectResponse(url="/login", status_code=303)


@app.get("/home")
def home_get(
    request: Request,
    user=Depends(get_current_user),
    db=Depends(get_db),
):
    user_id = user.user_id

    swiped_subq = (
        db.query(SwipeDB.to_user_id).filter(SwipeDB.from_user_id == user_id).subquery()
    )
    candidates = (
        db.query(UserDB)
        .filter(UserDB.user_id != user_id)
        .filter(UserDB.is_active.is_(True))
        .filter(~UserDB.user_id.in_(swiped_subq))
        .all()
    )

    if not candidates:
        return render(request, "home.html", {"profiles": []})

    candidate_ids = [u.user_id for u in candidates]
    images = (
        db.query(UserImageDB)
        .filter(UserImageDB.user_id.in_(candidate_ids))
        .order_by(UserImageDB.position)
        .all()
    )

    image_map = defaultdict(list)
    for img in images:
        image_map[img.user_id].append(img)

    def score(u: UserDB):
        score = 0

        if u.country == user.country:
            score += 3

        score += len(set(u.interests) & set(user.interests))

        if user.interested_in.value == "everyone":
            score += 2
        elif user.interested_in.value == u.gender.value:
            score += 4

        return score

    profiles = []
    for u in candidates:
        profile = UserSwipeProfile.model_validate(u).model_dump(mode="json")
        profile["images"] = [
            {
                "image_id": img.image_id,
                "image_url": build_image_url(img.image_key),
                "position": img.position,
            }
            for img in image_map.get(u.user_id, [])
        ]
        profile["score"] = score(u)
        profiles.append(profile)

    profiles.sort(key=lambda x: x["score"], reverse=True)
    return render(
        request,
        "home.html",
        {"profiles": profiles},
    )


@app.get("/profile")
def profile_get(request: Request, edit: bool = False, user=Depends(get_current_user)):
    user_resp = UserResponse.model_validate(user).model_dump(mode="json")
    for img in user_resp["images"]:
        img["image_url"] = build_image_url(img["image_key"])
    return render(
        request,
        "profile.html",
        {
            "user": user_resp,
            "edit_mode": edit,
            "viewer_mode": False,
            "countries": settings.COUNTRIES,
            "interests": Interests,
        },
    )


@app.get("/profile/{user_id}")
def visit_profile_get(
    user_id: int, request: Request, user=Depends(get_current_user), db=Depends(get_db)
):
    target_user = db.query(UserDB).filter(UserDB.user_id == user_id).first()
    target_user_resp = UserResponse.model_validate(target_user).model_dump(mode="json")
    for img in target_user_resp["images"]:
        img["image_url"] = build_image_url(img["image_key"])
    return render(
        request,
        "profile.html",
        {
            "user": target_user_resp,
            "edit_mode": False,
            "viewer_mode": True,
        },
    )


@app.post("/profile")
def profile_post(
    request: Request,
    userData=Depends(form_to_model(UserUpdate)),
    user=Depends(get_current_user),
    db=Depends(get_db),
):
    update_data = userData.model_dump(exclude_unset=True)
    if "email" in update_data:
        update_data["email"] = update_data["email"].lower()
        existing_user = (
            db.query(UserDB)
            .filter(UserDB.email == update_data["email"])
            .filter(UserDB.user_id != user.user_id)
            .first()
        )
        if existing_user:
            user_resp = UserResponse.model_validate(user).model_dump(mode="json")
            for img in user_resp["images"]:
                img["image_url"] = build_image_url(img["image_key"])
            return render(
                request,
                "profile.html",
                {
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
        request,
        "profile.html",
        {
            "user": user_resp,
            "edit_mode": False,
            "viewer_mode": False,
        },
    )


@app.post("/profile/upload-image")
async def profile_image_upload_post(
    request: Request,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
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
        fresh_user = db.query(UserDB).filter(UserDB.user_id == user.user_id).first()
        user_resp = UserResponse.model_validate(fresh_user).model_dump(mode="json")
        for img in user_resp["images"]:
            img["image_url"] = build_image_url(img["image_key"])
        return render(
            request,
            "profile.html",
            {
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
                UserImageDB(
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

        fresh_user = db.query(UserDB).filter(UserDB.user_id == user.user_id).first()
        user_resp = UserResponse.model_validate(fresh_user).model_dump(mode="json")
        for img in user_resp["images"]:
            img["image_url"] = build_image_url(img["image_key"])
        return render(
            request,
            "profile.html",
            {
                "user": user_resp,
                "errors": ["Unexpected error happened."],
                "edit_mode": False,
                "viewer_mode": False,
                "countries": settings.COUNTRIES,
                "interests": Interests,
            },
        )

    fresh_user = db.query(UserDB).filter(UserDB.user_id == user.user_id).first()
    user_resp = UserResponse.model_validate(fresh_user).model_dump(mode="json")
    for img in user_resp["images"]:
        img["image_url"] = build_image_url(img["image_key"])

    return render(
        request,
        "profile.html",
        {
            "user": user_resp,
            "errors": [],
            "edit_mode": False,
            "viewer_mode": False,
            "countries": settings.COUNTRIES,
            "interests": Interests,
        },
    )


@app.post("/logout")
def logout_post():
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie("access_token")
    return response


@app.post("/swipe")
def swipe_post(
    request: Request,
    swipeData: SwipeCreate,
    user=Depends(get_current_user),
    db=Depends(get_db),
):
    swipe = SwipeDB(
        from_user_id=user.user_id,
        to_user_id=swipeData.to_user_id,
        swipe_type=swipeData.swipe_type,
    )
    db.add(swipe)
    db.commit()
    conversation_out = None

    if swipeData.swipe_type in [SwipeType.like, SwipeType.super_like]:
        reciprocal_swipe = (
            db.query(SwipeDB)
            .filter(SwipeDB.from_user_id == swipeData.to_user_id)
            .filter(SwipeDB.to_user_id == user.user_id)
            .filter(SwipeDB.swipe_type.in_([SwipeType.like, SwipeType.super_like]))
            .first()
        )

        if reciprocal_swipe:
            conversation = ConversationDB(
                user1_id=user.user_id, user2_id=swipeData.to_user_id
            )
            db.add(conversation)
            db.commit()
            db.refresh(conversation)

            conversation_out = ConversationResponse.model_validate(conversation)

    return SwipeResponse(success=True, conversation=conversation_out)


@app.get("/conversations")
def conversations_get(
    request: Request,
    user=Depends(get_current_user),
    db=Depends(get_db),
):
    conversations = (
        db.query(ConversationDB)
        .filter(
            (ConversationDB.user1_id == user.user_id)
            | (ConversationDB.user2_id == user.user_id)
        )
        .order_by(ConversationDB.updated_at.desc())
        .all()
    )

    result = []

    for c in conversations:
        other_user_id = c.user2_id if c.user1_id == user.user_id else c.user1_id

        other_user = db.query(UserDB).filter(UserDB.user_id == other_user_id).first()
        other_user_image = None
        if other_user and other_user.images:
            other_user_image = build_image_url(other_user.images[0].image_key)

        result.append(
            ConversationPreview(
                conversation_id=c.conversation_id,
                other_user_id=other_user_id,
                other_user_name=other_user.first_name,
                other_user_image=other_user_image,
                last_message=c.last_message_id and "Last message placeholder",
                updated_at=c.updated_at,
            )
        )

    response = ConversationListResponse(success=True, conversations=result)

    return render(
        request,
        "conversations.html",
        {"conversations": response.model_dump(mode="json")},
    )


@app.get("/conversations/{conversation_id}")
def conversations_by_id_get(
    conversation_id: int,
    request: Request,
    user=Depends(get_current_user),
    db=Depends(get_db),
):
    conversation = (
        db.query(ConversationDB)
        .filter(ConversationDB.conversation_id == conversation_id)
        .first()
    )

    if not conversation:
        return {"error": "not found"}

    if user.user_id not in [conversation.user1_id, conversation.user2_id]:
        return {"error": "forbidden"}

    messages = (
        db.query(MessageDB)
        .filter(MessageDB.conversation_id == conversation_id)
        .order_by(MessageDB.created_at.asc())
        .all()
    )

    result = [
        MessagePreview(
            message_id=m.message_id,
            sender_id=m.sender_id,
            content=m.content,
            created_at=m.created_at,
        )
        for m in messages
    ]

    return MessageListResponse(
        conversation_id=conversation_id, current_user_id=user.user_id, messages=result
    )
