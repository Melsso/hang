from starlette.middleware.sessions import SessionMiddleware
from fastapi import Request
from slowapi.util import get_remote_address
from slowapi.middleware import SlowAPIMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

import time
import uuid
import logging

from hang.schemas.config import conf


logger = logging.getLogger("Hang")
PROBE_PATHS = {"/health", "/ready"}


async def log_requests(request: Request, call_next):
    if request.url.path in PROBE_PATHS:
        return await call_next(request)


def rate_limit_key(request: Request) -> str:
    user_id = getattr(request.state, "user_id", None)
    if user_id is not None:
        return f"user:{user_id}"
    return get_remote_address(request)


limiter = Limiter(
    key_func=rate_limit_key,
    storage_uri=conf.RATE_LIMIT_STORAGE_URI
    or f"redis://{conf.REDIS_HOST}:{conf.REDIS_PORT}/1",
    in_memory_fallback_enabled=True,
)


def register_middleware(app):
    app.state.limiter = limiter
    app.add_middleware(SlowAPIMiddleware)
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    app.add_middleware(
        SessionMiddleware,
        secret_key=conf.SECRET_KEY,
    )

    @app.middleware("http")
    async def log_requests(request: Request, call_next):

        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        start = time.time()

        response = await call_next(request)

        duration = round((time.time() - start) * 1000, 2)

        logger.info(
            "hang_event",
            extra={
                "event": "http_request",
                "status": "complete",
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": duration,
            },
        )

        return response
