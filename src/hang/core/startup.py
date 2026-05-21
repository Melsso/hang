import asyncio

from hang.core.database import init_db
from hang.helpers.ws import ws_heartbeat_loop


def register_startup_events(app):

    @app.on_event("startup")
    async def startup():
        asyncio.create_task(asyncio.to_thread(init_db))
        asyncio.create_task(ws_heartbeat_loop())
