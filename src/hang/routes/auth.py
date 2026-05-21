from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from typing import Annotated

from hang.schemas.users import Interests, UserCreate, UserLogin
from hang.schemas.config import conf
from hang.models.db_models import User

from hang.core.database import get_db
from hang.helpers.template_helpers import render, form_to_model
from hang.helpers.auth import create_access_token, authenticate_user
from hang.helpers.users import register_user, get_current_user


auth_router = APIRouter(prefix="/auth", tags=["auth"])


@auth_router.get("/")
def landing_get(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
):
    try:
        get_current_user(request, db)

        return RedirectResponse(
            url="/api/swipes/home",
            status_code=303,
        )

    except HTTPException:
        pass
    return render(request=request, template="landing.html")


@auth_router.get("/login")
def login_get(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
):
    try:
        get_current_user(request, db)

        return RedirectResponse(
            url="/api/swipes/home",
            status_code=303,
        )

    except HTTPException:
        pass
    return render(request=request, template="login.html")


@auth_router.post("/login")
def login_post(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    userData: Annotated[UserLogin, Depends(form_to_model(UserLogin))],
):
    user = authenticate_user(db, userData.email.lower(), userData.password)

    if not user:
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
def register_get(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
):
    try:
        get_current_user(request, db)

        return RedirectResponse(
            url="/api/swipes/home",
            status_code=303,
        )

    except HTTPException:
        pass
    return render(
        request=request,
        template="register.html",
        context={"countries": conf.COUNTRIES, "interests": Interests},
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

    usr = register_user(db, userData)
    if not usr:
        return render(
            request=request,
            template="register.html",
            context={"errors": ["Something unexpected happened."]},
        )
    return RedirectResponse(url="/api/auth/login", status_code=303)
