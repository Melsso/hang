import asyncio

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from sqlalchemy import text

import hang.core.database as database
from hang.core.redis import ping

health_router = APIRouter(tags=["health"], include_in_schema=False)


def _db_ready() -> bool:
    with database.get_db_session() as db:
        return bool(
            db.execute(text("SELECT to_regclass('public.users') IS NOT NULL")).scalar()
        )


@health_router.get("/health")
async def health(request: Request):
    tasks = getattr(request.app.state, "bg_tasks", [])
    dead = [t.get_name() for t in tasks if t.done()]
    if dead:
        return JSONResponse(
            status_code=503, content={"status": "unhealthy", "dead_tasks": dead}
        )
    return {"status": "ok"}


@health_router.get("/ready")
async def ready():
    checks: dict[str, bool] = {}
    try:
        checks["db"] = await asyncio.wait_for(asyncio.to_thread(_db_ready), timeout=2)
    except Exception:
        checks["db"] = False
    try:
        checks["redis"] = bool(await asyncio.wait_for(ping(), timeout=1))
    except Exception:
        checks["redis"] = False

    ok = all(checks.values())
    return JSONResponse(
        status_code=200 if ok else 503,
        content={"status": "ready" if ok else "not_ready", "checks": checks},
    )
