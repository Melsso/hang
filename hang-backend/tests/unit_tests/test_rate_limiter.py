import pytest

from hang.models.db_models import User
from hang.helpers.auth import pwd_context
from unit_tests.utils import make_user_row
from hang.core.limits import AUTH, FREQUENT


def _count(limit: str) -> int:
    return int(limit.split("/")[0])


def test_login_rate_limited(client, db):
    for _ in range(_count(AUTH)):
        response = client.post(
            "/api/auth/login",
            json={"email": "nobody@test.com", "password": "whatever"},
        )
        assert response.status_code == 401

    response = client.post(
        "/api/auth/login",
        json={"email": "nobody@test.com", "password": "whatever"},
    )
    assert response.status_code == 429


def test_register_rate_limited(client, db):
    payload = {
        "first_name": "John",
        "last_name": "Doe",
        "email": "repeat@test.com",
        "birthdate": "1995-06-15",
        "bio": "hello",
        "gender": "male",
        "country": "DE",
        "interested_in": "female",
        "interests": ["sports"],
        "password": "a-strong-password-123",
    }

    for _ in range(_count(AUTH)):
        response = client.post("/api/auth/register", json=payload)
        assert response.status_code in (201, 409)

    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 429


@pytest.mark.parametrize(
    "db",
    [{User: [make_user_row("john@test.com", "John")]}],
    indirect=True,
)
@pytest.mark.parametrize("current_user_email", ["john@test.com"], indirect=True)
def test_profile_get_rate_limited(client, db):
    for _ in range(_count(FREQUENT)):
        response = client.get("/api/users/profile")
        assert response.status_code == 200

    response = client.get("/api/users/profile")
    assert response.status_code == 429


@pytest.mark.parametrize(
    "db",
    [
        {
            User: [
                {
                    **make_user_row("john@test.com", "John"),
                    "auth_provider": "local",
                    "password": pwd_context.hash("correct-password"),
                }
            ]
        }
    ],
    indirect=True,
)
@pytest.mark.parametrize("current_user_email", ["john@test.com"], indirect=True)
def test_change_password_rate_limited(client, db):
    for _ in range(_count(AUTH)):
        response = client.post(
            "/api/settings/change-password",
            json={"old_password": "wrong", "new_password": "whatever"},
        )
        assert response.status_code == 400

    response = client.post(
        "/api/settings/change-password",
        json={"old_password": "wrong", "new_password": "whatever"},
    )
    assert response.status_code == 429


@pytest.mark.parametrize(
    "db",
    [{User: [make_user_row("john@test.com", "John")]}],
    indirect=True,
)
@pytest.mark.parametrize("current_user_email", ["john@test.com"], indirect=True)
def test_conversations_list_rate_limited(client, db):
    for _ in range(_count(FREQUENT)):
        response = client.get("/api/conversations")
        assert response.status_code == 200

    response = client.get("/api/conversations")
    assert response.status_code == 429
