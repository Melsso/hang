from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from typing import Annotated

from hang.schemas.users import Interests, UserCreate, UserLogin
from hang.schemas.config import conf
from hang.models.db_models import User

from hang.core.database import get_db
from hang.core.oauth import oauth_serv
from hang.core.middleware import limiter
from hang.helpers.template_helpers import render, form_to_model
from hang.helpers.auth import (
    create_access_token,
    authenticate_user_local,
    authenticate_user_google,
)
from hang.helpers.users import register_user, get_current_user


auth_router = APIRouter(prefix="/auth", tags=["auth"])


@auth_router.get("/")
@limiter.limit("5/minute")
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
@limiter.limit("5/minute")
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


@auth_router.get("/login/google")
@limiter.limit("5/minute")
async def login_get_google(
    request: Request,
):
    redirect_uri = conf.GOOGLE_REDIRECT_URI
    return await oauth_serv.google.authorize_redirect(request, redirect_uri)


@auth_router.get("/login/google/callback")
@limiter.limit("5/minute")
async def login_get_google_callback(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
):
    token = await oauth_serv.google.authorize_access_token(request)

    user_info = token.get("userinfo")
    if not user_info:
        user_info = await oauth_serv.google.parse_id_token(request, token)

    user = authenticate_user_google(db=db, google_user_info=user_info)
    if not user:
        return render(
            request=request,
            template="login.html",
            context={"errors": ["Something went wrong, please try again later."]},
        )

    token = create_access_token({"sub": str(user.user_id), "email": user.email})
    response = RedirectResponse(url="/api/swipes/home")
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=False,
        samesite="lax",
    )

    return response


@auth_router.post("/login")
@limiter.limit("5/minute")
def login_post(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    userData: Annotated[UserLogin, Depends(form_to_model(UserLogin))],
):
    user = authenticate_user_local(db, userData.email.lower(), userData.password)

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
@limiter.limit("5/minute")
def logout_post(request: Request):
    response = RedirectResponse(url="/api/auth/login", status_code=303)

    response.delete_cookie("access_token")

    return response


@auth_router.get("/register")
@limiter.limit("5/minute")
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
@limiter.limit("5/minute")
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
