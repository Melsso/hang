from fastapi import Request
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError

from src.hang.helpers.jinja_template import render


def register_exception_handlers(app):

    @app.exception_handler(RequestValidationError)
    async def validation_handler(request: Request, exc: RequestValidationError):

        errors = exc.errors()
        form = getattr(request.state, "form_data", {})
        path = request.url.path

        template_map = {
            "/register": "register.html",
            "/login": "login.html"
        }

        return render(
            request,
            template_map.get(path, "register.html"),
            {
                "errors": errors,
                "form": form
            },
            status_code=422
        )

    @app.exception_handler(ValidationError)
    async def pydantic_handler(request: Request, exc: ValidationError):

        errors = exc.errors()
        form = getattr(request.state, "form_data", {})
        path = request.url.path

        template_map = {
            "/register": "register.html",
            "/login": "login.html"
        }

        return render(
            request,
            template_map.get(path, "register.html"),
            {
                "errors": errors,
                "form": form
            },
            status_code=422
        )