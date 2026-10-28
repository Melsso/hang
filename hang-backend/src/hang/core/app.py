from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

from hang.core.logging import setup_logging
from hang.core.middleware import register_middleware
from hang.core.startup import lifespan

from hang.routes.auth import auth_router
from hang.routes.health import health_router
from hang.routes.users import user_router
from hang.routes.swipes import swipe_router
from hang.routes.conversations import conversation_router
from hang.routes.settings import settings_router
from hang.routes.ws import ws_router


def create_app() -> FastAPI:

    setup_logging()

    app = FastAPI(
        title="Hang", description="Dating App", version="0.2.0", lifespan=lifespan
    )

    Instrumentator(excluded_handlers=["/health", "/ready", "/metrics"]).instrument(
        app
    ).expose(app)

    register_middleware(app)

    app.include_router(auth_router, prefix="/api")
    app.include_router(health_router)
    app.include_router(user_router, prefix="/api")
    app.include_router(swipe_router, prefix="/api")
    app.include_router(conversation_router, prefix="/api")
    app.include_router(settings_router, prefix="/api")
    app.include_router(ws_router, prefix="/api")

    return app
