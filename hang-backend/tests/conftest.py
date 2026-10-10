import pytest

from contextlib import contextmanager
from testcontainers.postgres import PostgresContainer
from testcontainers.redis import RedisContainer
import redis.asyncio as aioredis

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from fastapi import HTTPException
from fastapi.testclient import TestClient
import os

os.environ.setdefault("RATE_LIMIT_STORAGE_URI", "memory://")

from hang.main import app
from hang.core.database import get_db
from hang.core.storage import get_storage
from hang.helpers.users import get_current_user
import hang.helpers.ws as ws_helpers
import hang.helpers.conversations as conv_helpers
from hang.models.db_models import Base, User
from hang.schemas.config import conf

from tests.utils import populate_db
from tests.fakes import FakeStorageService


@pytest.fixture(scope="session")
def postgres_container():
    with PostgresContainer("postgres:16") as postgres:
        yield postgres


@pytest.fixture(scope="session")
def engine(postgres_container):
    url = postgres_container.get_connection_url()
    url = url.replace(
        "postgresql+psycopg2://",
        "postgresql+psycopg://",
    )

    engine = create_engine(url, pool_pre_ping=True)
    Base.metadata.create_all(engine)

    yield engine

    engine.dispose()


@pytest.fixture
def db(engine, request):
    connection = engine.connect()
    outer_transaction = connection.begin()

    Session = sessionmaker(
        bind=connection,
        autoflush=False,
        autocommit=False,
        join_transaction_mode="create_savepoint",
    )

    session = Session()

    if hasattr(request, "param"):
        session.info["seeded"] = populate_db(session, request.param)

    yield session

    session.close()
    outer_transaction.rollback()
    connection.close()


@pytest.fixture(autouse=True)
def mock_db_session(monkeypatch, db):

    @contextmanager
    def fake_get_db_session():
        yield db

    monkeypatch.setattr(ws_helpers, "get_db_session", fake_get_db_session)
    monkeypatch.setattr(conv_helpers, "get_db_session", fake_get_db_session)


@pytest.fixture
def current_user_email(request):
    return getattr(request, "param", None)


@pytest.fixture(autouse=True)
def mock_conf(monkeypatch):
    monkeypatch.setattr(conf, "MAX_IMAGES", 6)
    monkeypatch.setattr(conf, "MAX_IMAGE_SIZE", 5_000_000)
    monkeypatch.setattr(conf, "ALLOWED_IMAGE_TYPES", ["png", "jpeg", "jpg"])


@pytest.fixture(autouse=True)
def reset_rate_limiter():
    app.state.limiter.reset()
    yield
    app.state.limiter.reset()


@pytest.fixture
def client(db, current_user_email):

    def override_get_db():
        yield db

    def override_get_current_user():
        query = db.query(User)
        if current_user_email:
            query = query.filter(User.email == current_user_email)
        user = query.first()
        if user is None:
            raise HTTPException(status_code=401, detail="Not authenticated")
        return user

    def override_get_storage():
        return FakeStorageService()

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user
    app.dependency_overrides[get_storage] = override_get_storage

    client = TestClient(app)

    yield client

    app.dependency_overrides.clear()


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="session")
def redis_container():
    with RedisContainer("redis:7-alpine") as redis:
        yield redis


@pytest.fixture
def test_redis_client(redis_container, monkeypatch):
    rc = aioredis.Redis(
        host=redis_container.get_container_host_ip(),
        port=int(redis_container.get_exposed_port(6379)),
        decode_responses=True,
    )

    monkeypatch.setattr(ws_helpers, "redis_client", rc)

    yield rc
