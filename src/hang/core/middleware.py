import time
import uuid
import logging
from fastapi import Request


logger = logging.getLogger("Hang")


def register_middleware(app):

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
