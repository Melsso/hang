import logging
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from fastapi import Request, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import RedirectResponse
from pydantic import ValidationError


logger = logging.getLogger("Hang")


def register_exception_handlers(app):
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        logger.warning(
            "hang_event",
            extra={
                "event": "http_request",
                "status": "unauthorized",
                "context": {
                    "location": "http_exception_handler",
                    "reason": "unauthenticated_access",
                },
                "status_code": exc.status_code == 401,
                "path": request.url.path,
                "method": request.method,
            },
        )

        if exc.status_code == 401:
            return RedirectResponse(url="/api/auth/login", status_code=303)

        if exc.status_code == 403:
            redirect_url = None
            if isinstance(exc.detail, dict):
                redirect_url = exc.detail.get("redirect_url")

            return RedirectResponse(
                url=redirect_url or "/api/swipes/home", status_code=303
            )

    @app.exception_handler(RequestValidationError)
    async def request_validation_handler(request: Request, exc: RequestValidationError):
        logger.warning(
            "hang_event",
            extra={
                "event": "http_request",
                "status": "validation_error",
                "status_code": 400,
                "path": request.url.path,
                "method": request.method,
                "context": {
                    "location": "request_validation_handler",
                    "reason": "invalid_request_format",
                },
            },
        )

        return RedirectResponse(
            url=request.headers.get("referer") or "/api/swipes/home/", status_code=303
        )

    @app.exception_handler(ValidationError)
    async def pydantic_validation_handler(request: Request, exc: ValidationError):

        logger.warning(
            "hang_event",
            extra={
                "event": "http_request",
                "status": "validation_error",
                "status_code": 422,
                "path": request.url.path,
                "method": request.method,
                "context": {
                    "location": "pydantic_validation_handler",
                    "error_type": "ValidationError",
                    "errors": exc.errors(),
                },
            },
        )

        return {}

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        logger.exception(
            "hang_event",
            extra={
                "event": "http_request",
                "status": "internal_error",
                "status_code": 500,
                "path": request.url.path,
                "method": request.method,
                "context": {
                    "location": "general_exception_handler",
                    "error_type": type(exc).__name__,
                    "error_message": str(exc),
                },
            },
        )

        return RedirectResponse(url="/api/swipes/home", status_code=303)
