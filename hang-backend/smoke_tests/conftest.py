import os
import pytest


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="session")
def postgres_container():
    from testcontainers.postgres import PostgresContainer

    with PostgresContainer("postgres:16") as pg:
        yield pg


@pytest.fixture(scope="session")
def redis_container():
    from testcontainers.redis import RedisContainer

    with RedisContainer("redis:7-alpine") as r:
        yield r


@pytest.fixture(scope="session")
def minio_container():
    from testcontainers.minio import MinioContainer

    with MinioContainer() as m:
        yield m


@pytest.fixture(scope="session")
def app_env(postgres_container, redis_container, minio_container):
    os.environ["DB_USER"] = postgres_container.username
    os.environ["DB_PASSWORD"] = postgres_container.password
    os.environ["DB_NAME"] = postgres_container.dbname
    os.environ["DB_HOST"] = "localhost"
    os.environ["DB_PORT"] = str(postgres_container.get_exposed_port(5432))

    os.environ["REDIS_HOST"] = "localhost"
    os.environ["REDIS_PORT"] = str(redis_container.get_exposed_port(6379))

    os.environ["SECRET_KEY"] = "smoke-test-secret"
    os.environ["ALGORITHM"] = "HS256"
    os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "30"

    os.environ["MAX_IMAGES"] = "6"
    os.environ["MAX_IMAGE_SIZE"] = "5000000"
    os.environ["ALLOWED_IMAGE_TYPES"] = "png,jpeg,jpg"

    os.environ["R2_ACCESS_KEY_ID"] = "minioadmin"
    os.environ["R2_SECRET_ACCESS_KEY"] = "minioadmin"
    os.environ["R2_BUCKET_NAME"] = "smoke-test-bucket"
    os.environ["R2_ENDPOINT"] = (
        f"http://localhost:{minio_container.get_exposed_port(9000)}"
    )

    os.environ["GOOGLE_CLIENT_ID"] = "smoke-test"
    os.environ["GOOGLE_CLIENT_SECRET"] = "smoke-test"
    os.environ["GOOGLE_REDIRECT_URI"] = "https://example.test/callback"

    yield


@pytest.fixture(scope="session")
def ensure_bucket(app_env, minio_container):
    import boto3

    client = boto3.client(
        "s3",
        endpoint_url=os.environ["R2_ENDPOINT"],
        aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"],
        region_name="auto",
    )
    client.create_bucket(Bucket=os.environ["R2_BUCKET_NAME"])
    yield


@pytest.fixture(scope="session")
def app(app_env):
    from hang.main import create_app

    return create_app()
