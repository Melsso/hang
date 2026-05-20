from fastapi import Request, HTTPException
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from fastapi.responses import RedirectResponse

from hang.helpers.template_helpers import render


# TODO rework this, super inconsistent and random behavior, need to define proper exceptions
def register_exception_handlers(app):

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):

        if exc.status_code in (401, 403):
            return RedirectResponse(url="/api/auth/login", status_code=303)

        return render(
            request,
            "error.html",
            {"errors": [exc.detail], "form": {}},
            status_code=exc.status_code,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_handler(request: Request, exc: RequestValidationError):

        form = getattr(request.state, "form_data", {})

        return render(
            request,
            "register.html",
            {"errors": exc.errors(), "form": form},
            status_code=422,
        )

    @app.exception_handler(ValidationError)
    async def pydantic_handler(request: Request, exc: ValidationError):

        form = getattr(request.state, "form_data", {})

        return render(
            request,
            "login.html",
            {"errors": exc.errors(), "form": form},
            status_code=422,
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):

        return render(
            request,
            "login.html",
            {"errors": ["Something unexpected happened."]},
            status_code=500,
        )
