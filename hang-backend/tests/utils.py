from sqlalchemy.orm import Session
from datetime import date


def populate_db(db: Session, data: dict) -> dict:
    created: dict = {}

    for model, rows in data.items():
        created[model] = []
        for row in rows:
            resolved_row = {
                key: (value(created) if callable(value) else value)
                for key, value in row.items()
            }
            obj = model(**resolved_row)
            db.add(obj)
            db.flush()
            created[model].append(obj)

    db.commit()
    return created


def make_user_row(
    email,
    first_name,
    auth_provider="local",
    oauth_id="",
    country="DE",
    password="",
    interests=None,
    gender="male",
    interested_in="female",
    birthdate=date(1995, 6, 15),
):
    return {
        "first_name": first_name,
        "last_name": "Test",
        "email": email,
        "gender": gender,
        "auth_provider": auth_provider,
        "oauth_id": oauth_id,
        "password": password,
        "interested_in": interested_in,
        "interests": interests or ["sports"],
        "birthdate": birthdate,
        "country": country,
        "bio": "some-bio",
    }
