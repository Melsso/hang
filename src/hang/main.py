from fastapi import FastAPI, Depends, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
import pycountry

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
from hang.models.message import MessagePreview, MessageListResponse
from hang.schemas.schemas import Base, UserDB, SwipeDB, ConversationDB, MessageDB
from hang.helpers.database import engine, get_db
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
# TODO move these paths into settings config class
app.mount("/static", StaticFiles(directory="src/hang/static"), name="static")
app.mount("/resources", StaticFiles(directory="src/hang/resources"), name="uploads")

register_exception_handlers(app)
COUNTRIES = [{"code": c.alpha_2, "name": c.name} for c in pycountry.countries]


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
        request, "register.html", {"countries": COUNTRIES, "interests": Interests}
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
def home_get(request: Request, user=Depends(get_current_user), db=Depends(get_db)):
    users = (
        db.query(UserDB)
        .filter(UserDB.user_id != user.user_id)
        .filter(UserDB.is_active)
        .all()
    )
    profiles = [UserSwipeProfile.model_validate(u) for u in users]

    return render(
        request,
        "home.html",
        {"profiles": [p.model_dump(mode="json") for p in profiles]},
    )


@app.get("/profile")
def profile_get(request: Request, edit: bool = False, user=Depends(get_current_user)):
    user_resp = UserResponse.model_validate(user)
    return render(
        request,
        "profile.html",
        {
            "user": user_resp.model_dump(mode="json"),
            "edit_mode": edit,
            "countries": COUNTRIES,
            "interests": Interests,
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
            return render(
                request,
                "profile.html",
                {
                    "errors": ["Email already in use"],
                    "user": UserResponse.model_validate(user).model_dump(mode="json"),
                    "edit_mode": True,
                },
            )

    for key, value in update_data.items():
        if getattr(user, key) != value:
            setattr(user, key, value)
    db.commit()
    db.refresh(user)

    user_resp = UserResponse.model_validate(user)
    return render(
        request,
        "profile.html",
        {"user": user_resp.model_dump(mode="json"), "edit_mode": False},
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
            other_user_image = other_user.images[0].image_url

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
