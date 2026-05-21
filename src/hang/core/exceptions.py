import logging

from fastapi import Request, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import RedirectResponse
from pydantic import ValidationError

from hang.helpers.template_helpers import render

logger = logging.getLogger("Hang")


def register_exception_handlers(app):

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):

        logger.warning(
            "error_event",
            extra={
                "event": "error",
                "error_type": "HTTPException",
                "error_message": str(exc.detail),
                "location": "http_exception_handler",
                "context": {
                    "path": request.url.path,
                    "status_code": exc.status_code,
                },
            },
        )

        if exc.status_code in (401, 403):
            return RedirectResponse(
                url="/api/auth/login",
                status_code=303,
            )

        return render(
            request,
            "error.html",
            {"errors": [exc.detail]},
            status_code=exc.status_code,
        )

    @app.exception_handler(RequestValidationError)
    async def request_validation_handler(request: Request, exc: RequestValidationError):

        logger.warning(
            "error_event",
            extra={
                "event": "error",
                "error_type": "RequestValidationError",
                "error_message": "Invalid request payload",
                "location": "request_validation_handler",
                "context": {
                    "path": request.url.path,
                    "errors": exc.errors(),
                },
            },
        )

        return render(
            request,
            "error.html",
            {"errors": exc.errors()},
            status_code=422,
        )

    @app.exception_handler(ValidationError)
    async def pydantic_validation_handler(request: Request, exc: ValidationError):

        logger.warning(
            "error_event",
            extra={
                "event": "error",
                "error_type": "ValidationError",
                "error_message": "Pydantic validation error",
                "location": "pydantic_validation_handler",
                "context": {
                    "path": request.url.path,
                    "errors": exc.errors(),
                },
            },
        )

        return render(
            request,
            "error.html",
            {"errors": exc.errors()},
            status_code=422,
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        print("##########################################")
        print("ZEBI")
        logger.exception(
            "error_event",
            extra={
                "event": "error",
                "error_type": type(exc).__name__,
                "error_message": str(exc),
                "location": "general_exception_handler",
                "context": {
                    "path": request.url.path,
                },
            },
        )

        return render(
            request,
            "error.html",
            {"errors": ["Something unexpected happened."]},
            status_code=500,
        )
