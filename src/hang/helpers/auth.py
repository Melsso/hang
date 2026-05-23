from passlib.context import CryptContext
from jose import jwt
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone

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

    if not user.password_hash:
        return None

    if not verify_password(password, user.password):
        return None

    return user


def authenticate_user_google(db: Session, google_user_info: dict) -> Optional[User]:
    try:
        email = google_user_info["email"]
        user = db.query(User).filter(User.email == email).first()

        if not user:
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
        else:
            user.auth_provider = "google"
            user.oauth_id = google_user_info["sub"]
            db.commit()

        return user

    except Exception:
        # TODO log failure
        db.rollback()
        return None
