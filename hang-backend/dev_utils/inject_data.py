from datetime import datetime, timezone, date
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from passlib.hash import bcrypt

from src.hang.schemas.config import conf

from src.hang.models.db_models import (
    User,
    Swipe,
    Conversation,
    Message,
    UserImage,
    Base,
)

from src.hang.schemas.swipes import SwipeType
from src.hang.core.storage import get_storage
from pathlib import Path
import mimetypes


LOCAL_RESOURCES = Path("dev_utils/resources").resolve()
HASHED_PASSWORD = bcrypt.hash("test123")


def create_users(db):
    users = [
        User(
            first_name="Sofiane",
            last_name="Doe",
            email="s@s.s",
            password=HASHED_PASSWORD,
            country="US",
            birthdate=date(1995, 5, 10),
            bio="I love hiking and music",
            gender="male",
            interested_in="female",
            interests=["music", "sports", "fitness"],
            is_active=True,
        ),
        User(
            first_name="Emma",
            last_name="Smith",
            email="e@e.e",
            password=HASHED_PASSWORD,
            country="UK",
            birthdate=date(1995, 5, 10),
            bio="Coffee addict & designer",
            gender="female",
            interested_in="male",
            interests=["music", "sports", "fitness"],
            is_active=True,
        ),
        User(
            first_name="Sam",
            last_name="Brown",
            email="ss@s.s",
            password=HASHED_PASSWORD,
            country="DE",
            birthdate=date(1995, 5, 10),
            bio="Gym, tech, travel",
            gender="other",
            interested_in="everyone",
            interests=["music", "sports", "fitness"],
            is_active=True,
        ),
        User(
            first_name="Lea",
            last_name="Brown",
            email="l@l.l",
            password=HASHED_PASSWORD,
            country="DE",
            birthdate=date(1995, 5, 10),
            bio="Gym, tech, travel",
            gender="other",
            interested_in="everyone",
            interests=["music", "sports", "fitness"],
            is_active=True,
        ),
    ]

    db.add_all(users)
    db.commit()

    for u in users:
        db.refresh(u)

    return users


def create_user_images(db, users):
    storage = get_storage()
    image_path = LOCAL_RESOURCES / "default_user.png"

    if not image_path.exists():
        raise FileNotFoundError(f"Missing default image: {image_path}")

    with open(image_path, "rb") as f:
        contents = f.read()

    content_type = (
        mimetypes.guess_type(image_path.name)[0] or "application/octet-stream"
    )

    user_images = []

    for user in users:
        key = f"users/{user.user_id}/default_user.png"

        storage.upload(
            key=key,
            contents=contents,
            ext=content_type,
        )

        user_images.append(
            UserImage(
                user_id=user.user_id,
                image_key=key,
                position=0,
            )
        )

    db.add_all(user_images)
    db.commit()


def create_swipes(db, users):
    swipes = [
        Swipe(
            from_user_id=users[0].user_id,
            to_user_id=users[1].user_id,
            swipe_type=SwipeType.like,
        ),
        Swipe(
            from_user_id=users[1].user_id,
            to_user_id=users[0].user_id,
            swipe_type=SwipeType.like,
        ),
        Swipe(
            from_user_id=users[0].user_id,
            to_user_id=users[2].user_id,
            swipe_type=SwipeType.pass_,
        ),
    ]

    db.add_all(swipes)
    db.commit()


def create_conversation(db, users):
    convo = Conversation(
        user1_id=users[0].user_id,
        user2_id=users[1].user_id,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    db.add(convo)
    db.commit()
    db.refresh(convo)

    return convo


def create_messages(db, convo, users):
    messages = [
        Message(
            conversation_id=convo.conversation_id,
            sender_id=users[0].user_id,
            content="Hey Emma 👋",
        ),
        Message(
            conversation_id=convo.conversation_id,
            sender_id=users[1].user_id,
            content="Hey!",
        ),
    ]

    db.add_all(messages)
    db.commit()


def main():
    DATABASE_URL = (
        f"postgresql+psycopg://{conf.DB_USER}:{conf.DB_PASSWORD}"
        f"@{conf.DB_HOST}:{conf.DB_PORT}/{conf.DB_NAME}"
    )
    engine = create_engine(DATABASE_URL, echo=False)

    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))

    Base.metadata.create_all(bind=engine)
    db = sessionmaker(bind=engine, autoflush=False, autocommit=False)()

    try:
        print("Seeding users...")
        users = create_users(db)

        print("Seeding user images...")
        create_user_images(db, users)

        print("Seeding swipes...")
        create_swipes(db, users)

        print("Creating conversation...")
        convo = create_conversation(db, users)

        print("Adding messages...")
        create_messages(db, convo, users)

        print("DONE ✅ Mock data inserted.")

    finally:
        db.close()


if __name__ == "__main__":
    main()
