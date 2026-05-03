from fastapi import APIRouter, Form, Depends, Request
from src.hang.models.user import UserCreate, UserLogin
from src.hang.helpers.jinja_template import render

router = APIRouter()


def form_to_model(model: type):
    async def dependency(request: Request):
        form = await request.form()
        data = dict(form)
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
    user: UserLogin = Depends(form_to_model(UserLogin))
):
    return {"status": "login_ok", "user": user}


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
    userData: UserCreate = Depends(form_to_model(UserCreate))
):
    return userData