import argparse
import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from jose import jwt
from passlib.hash import bcrypt
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from hang.schemas.config import conf
from hang.models.db_models import User, Conversation, Base

HASHED_PASSWORD = bcrypt.hash("loadtest123")
OUTPUT_PATH = Path("dev_utils/load_test_users.json")


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=conf.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, conf.SECRET_KEY, algorithm=conf.ALGORITHM)


def build_users(pair_count: int, run_id: str) -> list[User]:
    users = []

    for i in range(pair_count * 2):
        users.append(
            User(
                first_name=f"LoadTest{run_id}_{i}",
                last_name="User",
                email=f"loadtest_{run_id}_{i}@example.com",
                password=HASHED_PASSWORD,
                country="DE",
                birthdate=date(1995, 1, 1),
                bio="load test user",
                gender="other",
                interested_in="everyone",
                interests=["testing"],
                is_active=True,
            )
        )

    return users


def build_conversations(users: list[User]) -> list[Conversation]:
    conversations = []
    for i in range(0, len(users), 2):
        conversations.append(
            Conversation(
                user1_id=users[i].user_id,
                user2_id=users[i + 1].user_id,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
        )
    return conversations


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Seed matched user pairs and conversations directly in the DB, "
            "and issue real access tokens for load testing the websocket layer. "
            "Bypasses /auth/register and /auth/login entirely, since those are "
            "rate limited and not what this test is measuring."
        )
    )
    parser.add_argument("--pairs", type=int, default=50)
    args = parser.parse_args()
    run_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

    database_url = (
        f"postgresql+psycopg://{conf.DB_USER}:{conf.DB_PASSWORD}"
        f"@{conf.DB_HOST}:{conf.DB_PORT}/{conf.DB_NAME}"
    )
    engine = create_engine(database_url, echo=False)
    Base.metadata.create_all(bind=engine)
    db = sessionmaker(bind=engine, autoflush=False, autocommit=False)()

    try:
        print(f"Load test run id: {run_id}")
        print(f"Creating {args.pairs * 2} users...")
        users = build_users(args.pairs, run_id)
        db.add_all(users)
        db.commit()
        for u in users:
            db.refresh(u)

        print(f"Creating {args.pairs} matched conversations...")
        conversations = build_conversations(users)
        db.add_all(conversations)
        db.commit()
        for c in conversations:
            db.refresh(c)

        print("Issuing access tokens...")
        pairs = []
        for i, convo in enumerate(conversations):
            user_a = users[i * 2]
            user_b = users[i * 2 + 1]
            token_a = create_access_token(
                {"sub": str(user_a.user_id), "email": user_a.email}
            )
            token_b = create_access_token(
                {"sub": str(user_b.user_id), "email": user_b.email}
            )
            pairs.append(
                {
                    "conversation_id": convo.conversation_id,
                    "user_a": {"user_id": user_a.user_id, "access_token": token_a},
                    "user_b": {"user_id": user_b.user_id, "access_token": token_b},
                }
            )

        OUTPUT_PATH.write_text(json.dumps({"pairs": pairs}, indent=2))
        print(f"Wrote {len(pairs)} conversation pairs to {OUTPUT_PATH}")
        print("DONE.")

    finally:
        db.close()


if __name__ == "__main__":
    main()
