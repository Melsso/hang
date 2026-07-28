import pytest


def test_app_boots(app):
    assert app is not None
    assert app.title == "Hang"


def test_db_connectivity(app):
    from hang.core.database import init_db, get_db
    from sqlalchemy import text

    init_db()

    db_gen = get_db()
    db = next(db_gen)
    try:
        result = db.execute(text("SELECT 1")).scalar()
        assert result == 1
    finally:
        db_gen.close()


@pytest.mark.anyio
async def test_redis_connectivity(app):
    import hang.core.redis as redis_core

    pong = await redis_core.ping()
    assert pong is True


def test_storage_connectivity(app, ensure_bucket):
    from hang.core.storage import storage_service

    key = "smoke-test/wiring-check.txt"

    storage_service.upload(key=key, contents=b"hello", ext="txt")

    obj = storage_service.s3.get_object(Bucket=storage_service.bucket, Key=key)
    assert obj["Body"].read() == b"hello"

    storage_service.delete_many(keys=[key])

    with pytest.raises(Exception):
        storage_service.s3.get_object(Bucket=storage_service.bucket, Key=key)


def test_rate_limiter_attached(app):
    from slowapi import Limiter

    assert hasattr(app.state, "limiter")
    assert isinstance(app.state.limiter, Limiter)


def test_middleware_stack_registered(app):
    from starlette.middleware.sessions import SessionMiddleware
    from slowapi.middleware import SlowAPIMiddleware

    middleware_classes = [m.cls for m in app.user_middleware]
    assert SessionMiddleware in middleware_classes
    assert SlowAPIMiddleware in middleware_classes


def test_routers_registered(app):
    paths = {route.path for route in app.routes}

    assert "/api/auth/login" in paths
    assert "/api/users/profile" in paths
    assert "/api/swipes/home" in paths
    assert "/api/conversations" in paths
    assert "/api/settings/blocks" in paths
    assert "/api/ws/conversations" in paths


@pytest.mark.anyio
async def test_ws_manager_and_heartbeat_wired(app):
    import hang.helpers.ws as ws_helpers

    assert ws_helpers.manager is not None
    await ws_helpers.manager.ping_all()
    ws_helpers.manager.cleanup()


def test_oauth_client_registered(app):
    from hang.core.oauth import oauth_serv

    assert oauth_serv.google is not None


def test_prometheus_instrumentation_attached(app):
    paths = {route.path for route in app.routes}
    assert "/metrics" in paths
