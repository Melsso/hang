from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
import asyncio

from hang.schemas.config import settings

from hang.helpers.exceptions import register_exception_handlers
from hang.helpers.template_helpers import render
from hang.helpers.ws import ws_heartbeat_loop

from hang.routes.auth import auth_router
from hang.routes.users import user_router
from hang.routes.swipes import swipe_router
from hang.routes.conversations import conversation_router
from hang.routes.ws import ws_router


app = FastAPI(title="Hang", description="Dating App", version="1.0.0")

app.include_router(auth_router, prefix="/api")
app.include_router(user_router, prefix="/api")
app.include_router(swipe_router, prefix="/api")
app.include_router(conversation_router, prefix="/api")
app.include_router(ws_router, prefix="/api")

app.mount("/static", StaticFiles(directory=settings.STATIC_DIRECTORY), name="static")

register_exception_handlers(app)


@app.on_event("startup")
async def startup():
    asyncio.create_task(ws_heartbeat_loop())


@app.get("/")
def landing_get(request: Request):
    return render(request=request, template="landing.html")
