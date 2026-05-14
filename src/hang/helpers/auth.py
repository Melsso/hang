from fastapi import Depends, Request
from fastapi.responses import RedirectResponse
from passlib.context import CryptContext
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone


from hang.models.config import settings
from hang.schemas.schemas import UserDB
from hang.database.database import get_db


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict):
    to_encode = data.copy()

    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})

    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def get_current_user(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get("access_token")
    print(type(token))
    if not token:
        return RedirectResponse("/login", status_code=302)

    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )

        user_id = int(payload.get("sub"))
        user = db.query(UserDB).filter(UserDB.user_id == user_id).first()
        if not user:
            return RedirectResponse("/login", status_code=302)
        return user

    except JWTError as e:
        print("JWT FAILED:", repr(e))
        return RedirectResponse("/login", status_code=302)
