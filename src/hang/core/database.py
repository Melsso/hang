# core/db.py
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import time
import logging

from hang.schemas.config import settings
from hang.models.db_models import Base

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
                f"postgresql+psycopg://{settings.DB_USER}:{settings.DB_PASSWORD}"
                f"@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
            )
            engine = create_engine(DATABASE_URL, echo=False)

            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))

            Base.metadata.create_all(bind=engine)
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
            time.sleep(30)


def get_db():
    if SessionLocal is None:
        raise RuntimeError("DB not initialized yet")

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
