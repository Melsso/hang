from starlette.middleware.sessions import SessionMiddleware
from fastapi import Request
from slowapi.util import get_remote_address
from slowapi.middleware import SlowAPIMiddleware
from slowapi import Limiter

import time
import uuid
import logging

from hang.schemas.config import conf


logger = logging.getLogger("Hang")
limiter = Limiter(key_func=get_remote_address)


def register_middleware(app):
    app.state.limiter = limiter
    app.add_middleware(SlowAPIMiddleware)

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
