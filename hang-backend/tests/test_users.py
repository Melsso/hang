import pytest
from datetime import date

from hang.models.db_models import User, Conversation, UserReport, UserBlock


@pytest.mark.parametrize(
    "db",
    [
        {
            User: [
                {
                    "first_name": "John",
                    "last_name": "Doe",
                    "email": "john@test.com",
                    "gender": "male",
                    "interested_in": "female",
                    "interests": ["sports"],
                    "birthdate": date(1995, 6, 15),
                }
            ]
        }
    ],
    indirect=True,
)
def test_profile(client, db):
    response = client.get("/api/users/profile")
    assert response.status_code == 200
    assert response.json()["email"] == "john@test.com"


@pytest.mark.parametrize(
    "db",
    [
        {
            User: [
                {
                    "first_name": "John",
                    "last_name": "Doe",
                    "email": "john@test.com",
                    "gender": "male",
                    "interested_in": "female",
                    "interests": ["sports"],
                    "birthdate": date(1995, 6, 15),
                }
            ]
        }
    ],
    indirect=True,
)
@pytest.mark.parametrize("current_user_email", ["john@test.com"], indirect=True)
def test_profile_as_specific_single_user(client, db):
    response = client.get("/api/users/profile")
    assert response.status_code == 200
    assert response.json()["email"] == "john@test.com"


@pytest.mark.parametrize(
    "db",
    [
        {
            User: [
                {
                    "first_name": "John",
                    "last_name": "Doe",
                    "email": "john@test.com",
                    "gender": "male",
                    "interested_in": "female",
                    "interests": ["sports"],
                    "birthdate": date(1995, 6, 15),
                },
                {
                    "first_name": "Jane",
                    "last_name": "Smith",
                    "email": "jane@test.com",
                    "gender": "female",
                    "interested_in": "male",
                    "interests": ["music", "hiking"],
                    "birthdate": date(1995, 6, 15),
                },
            ]
        }
    ],
    indirect=True,
)
def test_profile_multiple_users(client, db):
    response = client.get("/api/users/profile")
    assert response.status_code == 200
    assert response.json()["email"] == "john@test.com"


@pytest.mark.parametrize(
    "db",
    [
        {
            User: [
                {
                    "first_name": "John",
                    "last_name": "Doe",
                    "email": "john@test.com",
                    "gender": "male",
                    "interested_in": "female",
                    "interests": ["sports"],
                    "birthdate": date(1995, 6, 15),
                },
                {
                    "first_name": "Jane",
                    "last_name": "Smith",
                    "email": "jane@test.com",
                    "gender": "female",
                    "interested_in": "male",
                    "interests": ["music"],
                    "birthdate": date(1995, 6, 15),
                },
            ]
        }
    ],
    indirect=True,
)
@pytest.mark.parametrize("current_user_email", ["jane@test.com"], indirect=True)
def test_profile_as_specific_user(client, db):
    response = client.get("/api/users/profile")
    assert response.status_code == 200
    assert response.json()["email"] == "jane@test.com"


@pytest.mark.parametrize(
    "db",
    [
        {
            User: [
                {
                    "first_name": "John",
                    "last_name": "Doe",
                    "email": "john@test.com",
                    "gender": "male",
                    "interested_in": "female",
                    "interests": ["sports"],
                    "birthdate": date(1995, 6, 15),
                },
                {
                    "first_name": "Jane",
                    "last_name": "Smith",
                    "email": "jane@test.com",
                    "gender": "female",
                    "interested_in": "male",
                    "interests": ["music"],
                    "birthdate": date(1995, 6, 15),
                },
            ]
        }
    ],
    indirect=True,
)
@pytest.mark.parametrize("current_user_email", ["jane@test.com"], indirect=True)
def test_other_profile_no_match(client, db):
    john = db.query(User).filter(User.email == "john@test.com").first()
    response = client.get(f"/api/users/profile/{john.user_id}")

    assert response.status_code == 403


@pytest.mark.parametrize(
    "db",
    [
        {
            User: [
                {
                    "first_name": "John",
                    "last_name": "Doe",
                    "email": "john@test.com",
                    "gender": "male",
                    "interested_in": "female",
                    "interests": ["sports"],
                    "birthdate": date(1995, 6, 15),
                },
                {
                    "first_name": "Jane",
                    "last_name": "Smith",
                    "email": "jane@test.com",
                    "gender": "female",
                    "interested_in": "male",
                    "interests": ["music"],
                    "birthdate": date(1995, 6, 15),
                },
            ],
            Conversation: [
                {
                    "user1_id": lambda created: created[User][0].user_id,
                    "user2_id": lambda created: created[User][1].user_id,
                },
            ],
        }
    ],
    indirect=True,
)
@pytest.mark.parametrize("current_user_email", ["jane@test.com"], indirect=True)
def test_other_profile_with_match(client, db):
    john = db.query(User).filter(User.email == "john@test.com").first()
    response = client.get(f"/api/users/profile/{john.user_id}")

    assert response.status_code == 200
    assert response.json()["email"] == "john@test.com"


@pytest.mark.parametrize(
    "db",
    [
        {
            User: [
                {
                    "first_name": "John",
                    "last_name": "Doe",
                    "email": "john@test.com",
                    "gender": "male",
                    "interested_in": "female",
                    "interests": ["sports"],
                    "birthdate": date(1995, 6, 15),
                },
                {
                    "first_name": "Jane",
                    "last_name": "Smith",
                    "email": "jane@test.com",
                    "gender": "female",
                    "interested_in": "male",
                    "interests": ["music"],
                    "birthdate": date(1995, 6, 15),
                },
            ],
            Conversation: [
                {
                    "user1_id": lambda created: created[User][0].user_id,
                    "user2_id": lambda created: created[User][1].user_id,
                },
            ],
            UserBlock: [
                {
                    "blocker_id": lambda created: created[User][0].user_id,
                    "blocked_id": lambda created: created[User][1].user_id,
                },
            ],
        }
    ],
    indirect=True,
)
@pytest.mark.parametrize("current_user_email", ["jane@test.com"], indirect=True)
def test_other_profile_blocked(client, db):
    john = db.query(User).filter(User.email == "john@test.com").first()
    response = client.get(f"/api/users/profile/{john.user_id}")

    assert response.status_code == 403


@pytest.mark.parametrize(
    "db",
    [
        {
            User: [
                {
                    "first_name": "John",
                    "last_name": "Doe",
                    "email": "john@test.com",
                    "gender": "male",
                    "interested_in": "female",
                    "interests": ["sports"],
                    "birthdate": date(1995, 6, 15),
                },
                {
                    "first_name": "Jane",
                    "last_name": "Smith",
                    "email": "jane@test.com",
                    "gender": "female",
                    "interested_in": "male",
                    "interests": ["music"],
                    "birthdate": date(1995, 6, 15),
                },
            ],
            Conversation: [
                {
                    "user1_id": lambda created: created[User][0].user_id,
                    "user2_id": lambda created: created[User][1].user_id,
                },
            ],
            UserReport: [
                {
                    "reporter_id": lambda created: created[User][0].user_id,
                    "reported_id": lambda created: created[User][1].user_id,
                    "reason": "Some Reason",
                },
            ],
        }
    ],
    indirect=True,
)
@pytest.mark.parametrize("current_user_email", ["jane@test.com"], indirect=True)
def test_other_profile_reported(client, db):
    john = db.query(User).filter(User.email == "john@test.com").first()
    response = client.get(f"/api/users/profile/{john.user_id}")

    assert response.status_code == 200
    assert response.json()["email"] == "john@test.com"
