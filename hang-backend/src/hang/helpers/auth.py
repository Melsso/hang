from passlib.context import CryptContext
from jose import jwt
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from fastapi import Response
from typing import Optional

from hang.schemas.config import conf
from hang.models.db_models import User


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict):
    to_encode = data.copy()

    expire = datetime.now(timezone.utc) + timedelta(
        minutes=conf.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    to_encode.update({"exp": expire})

    return jwt.encode(to_encode, conf.SECRET_KEY, algorithm=conf.ALGORITHM)


def authenticate_user_local(db: Session, email: str, password: str) -> Optional[User]:
    user = db.query(User).filter(User.email == email).first()

    if not user:
        return None

    if user.auth_provider != "local":
        return None

    if not user.password:
        return None

    if not verify_password(password, user.password):
        return None

    return user


def authenticate_user_google(db: Session, google_user_info: dict) -> Optional[User]:
    try:
        if google_user_info.get("email_verified") is not True:
            return None

        email = google_user_info["email"].lower()
        user = db.query(User).filter(User.email == email).first()

        if user is None:
            user = User(
                email=email,
                first_name=google_user_info.get("given_name", ""),
                last_name=google_user_info.get("family_name", ""),
                auth_provider="google",
                oauth_id=google_user_info["sub"],
                password=None,
                bio="",
                gender="other",
                interested_in="everyone",
                interests=[],
                birthdate=None,
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            return user

        if user.auth_provider != "google":
            return None

        if user.oauth_id != google_user_info["sub"]:
            user.oauth_id = google_user_info["sub"]
            db.commit()
        return user

    except Exception:
        db.rollback()
        return None


def set_auth_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        samesite="lax",
        secure=conf.COOKIE_SECURE,
        max_age=conf.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
