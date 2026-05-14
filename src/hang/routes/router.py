from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import JSONResponse, RedirectResponse
from passlib.context import CryptContext
from jose import jwt
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone

from src.hang.models.user import UserCreate, UserLogin
from src.hang.models.config import settings
from src.hang.helpers.jinja_template import render
from src.hang.database.database import get_db
from src.hang.schemas.schemas import UserDB


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
router = APIRouter()

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict):
    to_encode = data.copy()

    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})

    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def form_to_model(model: type):
    async def dependency(request: Request):
        form = await request.form()
        data = dict(form)

        if "interests" in data and isinstance(data["interests"], str):
            data["interests"] = [
                item.strip()
                for item in data["interests"].split(",")
                if item.strip()
            ]

        request.state.form_data = data
        return model.model_validate(data)
    return dependency


@router.get("/")
def landing_get(request: Request):
    return render(
        request,
        "landing.html",
        {
            "form": {},
            "errors": []
        }
    )

@router.get("/login")
def login_get(request: Request):
    return render(
        request,
        "login.html",
        {"form": {}}
    )


@router.post("/login")
def login_post(
    request: Request,
    userData: UserLogin = Depends(form_to_model(UserLogin)),
    db: Session = Depends(get_db)
):
    email = userData.email.lower()

    user = db.query(UserDB).filter(UserDB.email == email).first()

    if not user or not verify_password(userData.password, user.password):
        raise HTTPException(status_code=400, detail="Invalid credentials")

    token = create_access_token({
        "sub": str(user.user_id),
        "email": user.email
    })

    response = RedirectResponse(url="/home", status_code=303)

    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        samesite="lax",
        secure=False,   # True for HTTPS laterrs
        max_age=60 * 60
    )

    return response


@router.get("/register")
def register_get(request: Request):
    return render(
        request,
        "register.html",
        {"form": {}}
    )


@router.post("/register")
def register_post(
    request: Request,
    userData: UserCreate = Depends(form_to_model(UserCreate)),
    db: Session = Depends(get_db)
):
    email = userData.email.lower()
    existing_user = db.query(UserDB).filter(UserDB.email == email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = pwd_context.hash(userData.password)

    new_user = UserDB(
        first_name=userData.first_name,
        last_name=userData.last_name,
        email=email,
        password=hashed_password,
        birthdate=userData.birthdate,
        bio=userData.bio,
        gender=userData.gender,
        interested_in=userData.interested_in,
        interests=userData.interests,
        is_active=True
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return RedirectResponse(url="/login", status_code=303)


@router.get("/home")
def home_get(request: Request):
    return render(
        request,
        "home.html",
        {
            "form": {},
            "errors": []
        }
    )
