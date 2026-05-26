from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from prometheus_fastapi_instrumentator import Instrumentator

from hang.schemas.config import conf

from hang.core.logging import setup_logging
from hang.core.middleware import register_middleware
from hang.core.startup import register_startup_events
from hang.core.exceptions import register_exception_handlers

from hang.routes.auth import auth_router
from hang.routes.users import user_router
from hang.routes.swipes import swipe_router
from hang.routes.conversations import conversation_router
from hang.routes.settings import settings_router
from hang.routes.ws import ws_router


def create_app() -> FastAPI:

    setup_logging()

    app = FastAPI(
        title="Hang",
        description="Dating App",
        version="1.0.0",
    )

    Instrumentator().instrument(app).expose(app)

    register_middleware(app)

    app.include_router(auth_router, prefix="/api")
    app.include_router(user_router, prefix="/api")
    app.include_router(swipe_router, prefix="/api")
    app.include_router(conversation_router, prefix="/api")
    app.include_router(settings_router, prefix="/api")
    app.include_router(ws_router, prefix="/api")

    app.mount(
        "/static",
        StaticFiles(directory=conf.STATIC_DIRECTORY),
        name="static",
    )

    register_exception_handlers(app)

    register_startup_events(app)

    return app
