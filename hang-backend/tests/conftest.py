import pytest

from testcontainers.postgres import PostgresContainer
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from fastapi import HTTPException
from fastapi.testclient import TestClient

from hang.main import app
from hang.core.database import get_db
from hang.helpers.users import get_current_user
from hang.core.storage import get_storage
from hang.models.db_models import Base, User

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
        populate_db(session, request.param)

    yield session

    session.close()
    outer_transaction.rollback()
    connection.close()


@pytest.fixture
def current_user_email(request):
    return getattr(request, "param", None)


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
