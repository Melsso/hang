"""Seed demo accounts and profiles for recording the demo.

Re-runnable: the demo users (emails @hang-demo.com) are deleted and recreated each
run, along with their swipes, conversations, messages and uploaded images. That gives
you a clean slate for every take.

Pictures are taken from dev_utils/resources/male and dev_utils/resources/female
(.jpg, .jpeg, .png). Each user gets one picture from the pool matching their gender,
handed out in filename order. Users with gender "other" take from whichever pool has
more pictures left.
"""

import argparse
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from uuid import uuid4

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from hang.core.storage import StorageService
from hang.helpers.auth import hash_password
from hang.models.db_models import Base, Swipe, User, UserImage
from hang.schemas.config import conf
from hang.schemas.swipes import SwipeType
from hang.schemas.users import Gender, InterestedIn, Interests

DEMO_DOMAIN = "hang-demo.com"
IMAGE_EXTS = {".jpg": "jpeg", ".jpeg": "jpeg", ".png": "png"}


@dataclass(frozen=True)
class Persona:
    first_name: str
    last_name: str
    gender: Gender
    interested_in: InterestedIn
    country: str
    age: int
    interests: tuple[Interests, ...]
    bio: str
    likes_demo: bool = False


DEMO_ACCOUNTS = [
    Persona(
        "Jake",
        "Demo",
        Gender.male,
        InterestedIn.everyone,
        "DE",
        27,
        (Interests.music, Interests.travel, Interests.tech, Interests.food),
        "Backend dev by day, amateur chef by night. Always up for a new city.",
    ),
    Persona(
        "Sam",
        "Demo",
        Gender.female,
        InterestedIn.everyone,
        "DE",
        26,
        (Interests.music, Interests.photography, Interests.travel, Interests.nature),
        "Photographer chasing good light. Coffee first, plans second.",
    ),
]

PERSONAS = [
    Persona(
        "Mia",
        "Keller",
        Gender.female,
        InterestedIn.everyone,
        "DE",
        25,
        (Interests.music, Interests.art, Interests.nightlife),
        "Vinyl collector and gallery hopper. Ask me about my last concert.",
        True,
    ),
    Persona(
        "Leo",
        "Fischer",
        Gender.male,
        InterestedIn.everyone,
        "DE",
        29,
        (Interests.fitness, Interests.outdoor, Interests.cooking),
        "Climbing on weekends, meal prepping on Sundays.",
        True,
    ),
    Persona(
        "Nora",
        "Berg",
        Gender.female,
        InterestedIn.everyone,
        "SE",
        28,
        (Interests.reading, Interests.nature, Interests.pets),
        "Two cats, too many books, one very patient bookshelf.",
        True,
    ),
    Persona(
        "Jonas",
        "Weber",
        Gender.male,
        InterestedIn.everyone,
        "DE",
        31,
        (Interests.gaming, Interests.tech, Interests.movies),
        "Indie games, sci-fi, and defending pineapple on pizza.",
        True,
    ),
    Persona(
        "Elena",
        "Rossi",
        Gender.female,
        InterestedIn.everyone,
        "IT",
        27,
        (Interests.food, Interests.travel, Interests.fashion),
        "Pasta snob. Will rate your carbonara honestly.",
        True,
    ),
    Persona(
        "Tom",
        "Hughes",
        Gender.male,
        InterestedIn.everyone,
        "GB",
        30,
        (Interests.sports, Interests.cars, Interests.music),
        "Football on Saturdays, track days when I can afford them.",
    ),
    Persona(
        "Clara",
        "Dubois",
        Gender.female,
        InterestedIn.everyone,
        "FR",
        26,
        (Interests.art, Interests.photography, Interests.fashion),
        "Film photography and thrifted jackets.",
    ),
    Persona(
        "Marco",
        "Silva",
        Gender.male,
        InterestedIn.everyone,
        "PT",
        28,
        (Interests.outdoor, Interests.nature, Interests.travel),
        "Surf at sunrise, hike on days off, always chasing a view.",
    ),
    Persona(
        "Lena",
        "Novak",
        Gender.female,
        InterestedIn.everyone,
        "PL",
        24,
        (Interests.fitness, Interests.cooking, Interests.pets),
        "Yoga, smoothies and one very energetic dog.",
    ),
    Persona(
        "Daniel",
        "Meyer",
        Gender.male,
        InterestedIn.everyone,
        "NL",
        32,
        (Interests.tech, Interests.reading, Interests.movies),
        "Software engineer who actually likes the sequel.",
    ),
    Persona(
        "Sofia",
        "Garcia",
        Gender.female,
        InterestedIn.everyone,
        "ES",
        29,
        (Interests.nightlife, Interests.music, Interests.travel),
        "Salsa on Fridays, brunch on Sundays, nothing planned between.",
    ),
    Persona(
        "Kai",
        "Lindgren",
        Gender.other,
        InterestedIn.everyone,
        "SE",
        27,
        (Interests.gaming, Interests.art, Interests.tech),
        "Pixel artist and board game host.",
    ),
]


class PicturePool:
    def __init__(self, label: str, directory: Path) -> None:
        self.label = label
        self.files = (
            sorted(
                p
                for p in directory.iterdir()
                if p.is_file() and p.suffix.lower() in IMAGE_EXTS
            )
            if directory.is_dir()
            else []
        )
        self.cursor = 0
        self.warned = False

    def remaining(self) -> int:
        return max(len(self.files) - self.cursor, 0)

    def take(self) -> Path | None:
        if not self.files:
            return None
        if self.cursor >= len(self.files) and not self.warned:
            print(f"  warning: '{self.label}' pictures ran out, reusing from the start")
            self.warned = True
        path = self.files[self.cursor % len(self.files)]
        self.cursor += 1
        return path


def pick_pool(gender: Gender, male: PicturePool, female: PicturePool) -> PicturePool:
    if gender == Gender.male:
        return male
    if gender == Gender.female:
        return female
    return male if male.remaining() >= female.remaining() else female


def email_for(persona: Persona) -> str:
    return f"{persona.first_name.lower()}@{DEMO_DOMAIN}"


def purge(db: Session, like_pattern: str, storage: StorageService) -> int:
    users = db.query(User).filter(User.email.like(like_pattern)).all()
    keys = [img.image_key for u in users for img in u.images]
    db.query(User).filter(User.email.like(like_pattern)).delete(
        synchronize_session=False
    )
    db.commit()
    if keys:
        storage.delete_many(keys=keys)
    return len(users)


def attach_image(db: Session, storage: StorageService, user: User, path: Path) -> bool:
    contents = path.read_bytes()
    if len(contents) > conf.MAX_IMAGE_SIZE:
        print(f"  skipping {path.name}: larger than MAX_IMAGE_SIZE")
        return False
    ext = IMAGE_EXTS[path.suffix.lower()]
    key = f"users/{user.user_id}/images/{uuid4().hex}.{ext}"
    storage.upload(key=key, contents=contents, ext=ext)
    db.add(UserImage(user_id=user.user_id, image_key=key, position=0))
    return True


def build_user(persona: Persona, password_hash: str) -> User:
    return User(
        first_name=persona.first_name,
        last_name=persona.last_name,
        email=email_for(persona),
        password=password_hash,
        auth_provider="local",
        country=persona.country,
        birthdate=date.today() - timedelta(days=int(persona.age * 365.25) + 30),
        bio=persona.bio,
        gender=persona.gender,
        interested_in=persona.interested_in,
        interests=[i.value for i in persona.interests],
        is_active=True,
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Seed demo users for recording the demo."
    )
    parser.add_argument("--password", default="demo-password-123")
    parser.add_argument(
        "--resources-dir",
        default="dev_utils/resources",
        help="Directory containing the 'male' and 'female' picture folders.",
    )
    parser.add_argument(
        "--purge-loadtest",
        action="store_true",
        help="Also delete load test users (loadtest_*@example.com).",
    )
    args = parser.parse_args()

    database_url = (
        f"postgresql+psycopg://{conf.DB_USER}:{conf.DB_PASSWORD}"
        f"@{conf.DB_HOST}:{conf.DB_PORT}/{conf.DB_NAME}"
    )
    engine = create_engine(database_url, echo=False)
    Base.metadata.create_all(bind=engine)
    db = sessionmaker(bind=engine, autoflush=False, autocommit=False)()
    storage = StorageService()

    resources = Path(args.resources_dir)
    male_pool = PicturePool("male", resources / "male")
    female_pool = PicturePool("female", resources / "female")
    print(
        f"Pictures found: {len(male_pool.files)} male, {len(female_pool.files)} female "
        f"(in {resources})"
    )

    try:
        removed = purge(db, f"%@{DEMO_DOMAIN}", storage)
        print(f"Removed {removed} previous demo users")
        if args.purge_loadtest:
            removed = purge(db, "loadtest\\_%@example.com", storage)
            print(f"Removed {removed} load test users")

        password_hash = hash_password(args.password)
        everyone = DEMO_ACCOUNTS + PERSONAS
        users = {p.first_name: build_user(p, password_hash) for p in everyone}
        db.add_all(users.values())
        db.flush()

        uploaded = 0
        for persona in everyone:
            picture = pick_pool(persona.gender, male_pool, female_pool).take()
            if picture is not None and attach_image(
                db, storage, users[persona.first_name], picture
            ):
                uploaded += 1

        demo_ids = [users[p.first_name].user_id for p in DEMO_ACCOUNTS]
        for persona in PERSONAS:
            if persona.likes_demo:
                for demo_id in demo_ids:
                    db.add(
                        Swipe(
                            from_user_id=users[persona.first_name].user_id,
                            to_user_id=demo_id,
                            swipe_type=SwipeType.like,
                        )
                    )

        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

    print(f"Created {len(users)} users, uploaded {uploaded} images")
    print("\nDemo logins:")
    for p in DEMO_ACCOUNTS:
        print(f"  {email_for(p)} / {args.password}")
    likers = ", ".join(p.first_name for p in PERSONAS if p.likes_demo)
    print(
        f"\nAlready liked both demo accounts (like them back for an instant match): {likers}"
    )
    if uploaded == 0:
        print(
            f"\nNo pictures found in {resources}; profiles will show the default avatar."
        )


if __name__ == "__main__":
    main()
