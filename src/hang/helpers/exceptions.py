from fastapi import Request, HTTPException
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from fastapi.responses import RedirectResponse

from hang.helpers.template_helpers import render


def register_exception_handlers(app):

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):

        if exc.status_code == 401:
            return RedirectResponse(url="/login", status_code=303)

        # TODO this is random, make this intentional
        return render(
            request,
            "error.html",
            {"errors": [exc.detail], "form": {}},
            status_code=exc.status_code,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_handler(request: Request, exc: RequestValidationError):

        errors = exc.errors()
        form = getattr(request.state, "form_data", {})

        return render(
            request, "register.html", {"errors": errors, "form": form}, status_code=422
        )

    @app.exception_handler(ValidationError)
    async def pydantic_handler(request: Request, exc: ValidationError):

        errors = exc.errors()
        form = getattr(request.state, "form_data", {})

        return render(
            request, "login.html", {"errors": errors, "form": form}, status_code=422
        )
