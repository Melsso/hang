from passlib.context import CryptContext
from jose import jwt
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone

from typing import Optional

from hang.schemas.config import settings
from hang.schemas.users import UserCreate
from hang.models.db_models import User


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict):
    to_encode = data.copy()

    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    to_encode.update({"exp": expire})

    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    user = db.query(User).filter(User.email == email).first()

    if not user or not verify_password(password, user.password):
        return None

    return user


def register_user(db: Session, user_data: UserCreate) -> Optional[User]:
    new_user = User(
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        email=user_data.email.lower(),
        password=hash_password(user_data.password),
        birthdate=user_data.birthdate,
        bio=user_data.bio,
        country=user_data.country,
        gender=user_data.gender,
        interested_in=user_data.interested_in,
        interests=user_data.interests,
        is_active=True,
    )

    # TODO look into exception handling here
    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
    except Exception:
        db.rollback()
        return None

    return new_user
