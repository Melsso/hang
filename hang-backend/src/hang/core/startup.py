import asyncio
from contextlib import asynccontextmanager

from hang.core.database import init_db
from hang.helpers.ws import redis_subscriber
from hang.helpers.ws import ws_heartbeat_loop


@asynccontextmanager
async def lifespan(app):
    _ = asyncio.create_task(asyncio.to_thread(init_db))

    bg = [
        asyncio.create_task(redis_subscriber(), name="redis_subscriber"),
        asyncio.create_task(ws_heartbeat_loop(), name="ws_heartbeat"),
    ]
    app.state.bg_tasks = bg

    yield

    for t in bg:
        t.cancel()

    await asyncio.gather(*bg, return_exceptions=True)
