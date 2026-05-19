from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from typing import Annotated

from hang.schemas.users import Interests, UserCreate, UserLogin
from hang.schemas.config import settings
from hang.models.db_models import User

from hang.helpers.template_helpers import render, form_to_model
from hang.helpers.auth import verify_password, create_access_token, hash_password
from hang.helpers.database import get_db


auth_router = APIRouter(prefix="/auth", tags=["auth"])


@auth_router.get("/login")
def login_get(request: Request):
    # TODO can potentially check token, if active redir to home page isntead
    return render(request=request, template="login.html")


@auth_router.post("/login")
def login_post(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    userData: Annotated[UserLogin, Depends(form_to_model(UserLogin))],
):
    email = userData.email.lower()

    user = db.query(User).filter(User.email == email).first()

    if not user or not verify_password(userData.password, user.password):
        return render(
            request=request,
            template="login.html",
            context={"errors": ["Invalid credentials"]},
        )

    token = create_access_token({"sub": str(user.user_id), "email": user.email})

    response = RedirectResponse(url="/api/swipes/home", status_code=303)

    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        samesite="lax",
        secure=False,  # True for HTTPS laterrs
        max_age=60 * 60,
    )

    return response


@auth_router.post("/logout")
def logout_post(request: Request):
    response = RedirectResponse(url="/api/auth/login", status_code=303)

    response.delete_cookie("access_token")

    return response


@auth_router.get("/register")
def register_get(request: Request):
    return render(
        request=request,
        template="register.html",
        context={"countries": settings.COUNTRIES, "interests": Interests},
    )


@auth_router.post("/register")
def register_post(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    userData: Annotated[UserCreate, Depends(form_to_model(UserCreate))],
):
    email = userData.email.lower()
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        return render(
            request=request,
            template="register.html",
            context={"errors": ["Email already in use"]},
        )

    hashed_password = hash_password(userData.password)

    new_user = User(
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

    return RedirectResponse(url="/api/auth/login", status_code=303)
