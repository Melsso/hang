from contextlib import contextmanager
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import time
import logging

from hang.schemas.config import conf

logger = logging.getLogger("Hang")

engine = None
SessionLocal = None


def init_db():
    global engine, SessionLocal

    while True:
        try:
            logger.info(
                "hang_event",
                extra={
                    "event": "db_init",
                    "status": "starting",
                    "context": {"location": "init_db"},
                },
            )
            DATABASE_URL = (
                f"postgresql+psycopg://{conf.DB_USER}:{conf.DB_PASSWORD}"
                f"@{conf.DB_HOST}:{conf.DB_PORT}/{conf.DB_NAME}"
            )
            engine = create_engine(
                DATABASE_URL,
                echo=False,
                pool_size=conf.DB_POOL_SIZE,
                max_overflow=conf.DB_MAX_OVERFLOW,
                pool_pre_ping=True,
            )

            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))

            SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

            logger.info(
                "hang_event",
                extra={
                    "event": "db_init",
                    "status": "success",
                    "context": {"location": "init_db"},
                },
            )
            break

        except Exception as exc:
            logger.error(
                "hang_event",
                extra={
                    "event": "db_init",
                    "status": "failed",
                    "error_type": type(exc).__name__,
                    "error_message": str(exc),
                    "context": {"location": "init_db"},
                },
            )
            time.sleep(2)


def get_db():
    if SessionLocal is None:
        raise RuntimeError("DB not initialized yet")

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_session():
    if SessionLocal is None:
        raise RuntimeError("DB not initialized yet")

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
