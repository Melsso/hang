import hang.routes.health as health_routes


class _DoneTask:
    def done(self):
        return True

    def get_name(self):
        return "redis_subscriber"


def test_health_ok(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_health_reports_dead_task(client, monkeypatch):
    monkeypatch.setattr(client.app.state, "bg_tasks", [_DoneTask()], raising=False)
    r = client.get("/health")
    assert r.status_code == 503
    assert r.json()["dead_tasks"] == ["redis_subscriber"]


def test_ready_ok(client, monkeypatch):
    async def ok():
        return True

    monkeypatch.setattr(health_routes, "_db_ready", lambda: True)
    monkeypatch.setattr(health_routes, "ping", ok)
    assert client.get("/ready").status_code == 200


def test_ready_503_when_redis_down(client, monkeypatch):
    async def down():
        raise ConnectionError

    monkeypatch.setattr(health_routes, "_db_ready", lambda: True)
    monkeypatch.setattr(health_routes, "ping", down)
    r = client.get("/ready")
    assert r.status_code == 503
    assert r.json()["checks"] == {"db": True, "redis": False}


def test_ready_503_when_schema_missing(client, monkeypatch):
    async def ok():
        return True

    monkeypatch.setattr(health_routes, "_db_ready", lambda: False)
    monkeypatch.setattr(health_routes, "ping", ok)
    assert client.get("/ready").status_code == 503
