from fastapi import FastAPI, Depends, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from hang.models.user import UserCreate, UserLogin, UserResponse
from hang.schemas.schemas import Base, UserDB
from hang.helpers.database import engine, get_db
from hang.helpers.exceptions import register_exception_handlers
from hang.helpers.template_helpers import render, form_to_model
from hang.helpers.auth import verify_password, hash_password, create_access_token, get_current_user


Base.metadata.create_all(bind=engine)


app = FastAPI()
app.mount("/static", StaticFiles(directory="src/hang/static"), name="static")
register_exception_handlers(app)


@app.get("/")
def landing_get(request: Request):
    return render(
        request,
        "landing.html",
        {
            "form": {},
            "errors": []
        }
    )

@app.get("/login")
def login_get(request: Request):
    return render(
        request,
        "login.html",
        {"form": {}}
    )


@app.post("/login")
def login_post(
    request: Request,
    userData: UserLogin = Depends(form_to_model(UserLogin)),
    db: Session = Depends(get_db)
):
    email = userData.email.lower()

    user = db.query(UserDB).filter(UserDB.email == email).first()

    if not user or not verify_password(userData.password, user.password):
        return render(request, "login.html", {
            "errors": ["Invalid credentials"]
        })

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


@app.get("/register")
def register_get(request: Request):
    return render(
        request,
        "register.html",
        {"form": {}}
    )


@app.post("/register")
def register_post(
    request: Request,
    userData: UserCreate = Depends(form_to_model(UserCreate)),
    db: Session = Depends(get_db)
):
    email = userData.email.lower()
    existing_user = db.query(UserDB).filter(UserDB.email == email).first()
    if existing_user:
        return render(request, "register.html", {
            "errors": ["Email already in use"]
        })

    hashed_password = hash_password(userData.password)

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


@app.get("/home")
def home_get(request: Request, user=Depends(get_current_user)):
    return render(
        request,
        "home.html",
        {
            "form": {},
            "errors": []
        }
    )


@app.get("/profile")
def profile_get(request: Request, user=Depends(get_current_user)):

    user_resp = UserResponse.model_validate(user)
    return render(
        request,
        "profile.html",
        {
            "form": {},
            "errors": [],
            "user": user_resp.model_dump()
        }
    )


@app.post("/logout")
def logout_post():
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie("access_token")
    return response