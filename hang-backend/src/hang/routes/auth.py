from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy.orm import Session
from typing import Annotated
import logging

from hang.schemas.users import UserStateResponse, UserCreate, UserLogin
from hang.schemas.config import conf
from hang.models.db_models import User

from hang.core.database import get_db
from hang.core.oauth import oauth_serv
from hang.core.middleware import limiter
from hang.helpers.auth import (
    create_access_token,
    authenticate_user_local,
    authenticate_user_google,
)
from hang.helpers.users import register_user, get_current_user, is_profile_incomplete


auth_router = APIRouter(prefix="/auth", tags=["auth"])
logger = logging.getLogger("Hang")


@auth_router.get("/session", response_model=UserStateResponse)
def session_status(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
):
    resp = UserStateResponse(
        authenticated=False, user_id=None, onboarding_required=False
    )
    try:
        user = get_current_user(request=request, db=db)
        resp.authenticated = True
        resp.user_id = user.user_id
        resp.onboarding_required = is_profile_incomplete(user=user)
        return resp
    except Exception as exc:
        logger.exception(
            "hang_event",
            extra={
                "event": "http_request",
                "status": "internal_error",
                "status_code": 500,
                "path": request.url.path,
                "method": request.method,
                "context": {
                    "location": "general_exception_handler",
                    "error_type": type(exc).__name__,
                    "error_message": str(exc),
                },
            },
        )
        return resp


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
        return RedirectResponse(url="/login")

    token = create_access_token({"sub": str(user.user_id), "email": user.email})
    response = RedirectResponse(url="/swipes")

    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        samesite="lax",
        secure=False,
        max_age=60 * 60,
    )

    return response


@auth_router.post("/login")
@limiter.limit("5/minute")
def login_post(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    userData: UserLogin,
):
    user = authenticate_user_local(db, userData.email.lower(), userData.password)

    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({"sub": str(user.user_id), "email": user.email})

    response = JSONResponse(
        content={
            "authenticated": True,
        }
    )

    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        samesite="lax",
        secure=False,  # True in production HTTPS
        max_age=60 * 60,
    )

    return response


@auth_router.post("/logout")
@limiter.limit("5/minute")
def logout_post(request: Request):
    response = JSONResponse(content={"success": True})

    response.delete_cookie(
        key="access_token",
        httponly=True,
        samesite="lax",
    )

    return response


@auth_router.post("/register")
@limiter.limit("5/minute")
def register_post(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    userData: UserCreate,
):
    email = userData.email.lower()
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        raise HTTPException(status_code=409, detail="Email already in use")

    usr, msg = register_user(db, userData)
    if not usr:
        raise HTTPException(status_code=400, detail=msg or "Registration failed")

    return JSONResponse(
        status_code=201,
        content={
            "registered": True,
        },
    )
