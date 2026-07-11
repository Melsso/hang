import pytest
from datetime import date
from unittest.mock import AsyncMock, patch
from fastapi.responses import RedirectResponse

from hang.models.db_models import User
from hang.helpers.auth import hash_password


def test_register_success(client, db):
    response = client.post(
        "/api/auth/register",
        json={
            "first_name": "John",
            "last_name": "Doe",
            "email": "new-user@test.com",
            "birthdate": "1995-06-15",
            "bio": "hello",
            "gender": "male",
            "country": "DE",
            "interested_in": "female",
            "interests": ["sports"],
            "password": "a-strong-password-123",
        },
    )

    assert response.status_code == 201
    assert response.json()["registered"] is True

    created_user = db.query(User).filter(User.email == "new-user@test.com").first()
    assert created_user is not None
    assert created_user.first_name == "John"
    assert created_user.password != "a-strong-password-123"


@pytest.mark.parametrize(
    "db",
    [
        {
            User: [
                {
                    "first_name": "Existing",
                    "last_name": "User",
                    "email": "taken@test.com",
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
def test_register_email_already_in_use(client, db):
    response = client.post(
        "/api/auth/register",
        json={
            "first_name": "Someone",
            "last_name": "Else",
            "email": "taken@test.com",
            "birthdate": "1995-06-15",
            "bio": "hello",
            "gender": "male",
            "country": "DE",
            "interested_in": "female",
            "interests": ["sports"],
            "password": "a-strong-password-123",
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Email already in use"

    matches = db.query(User).filter(User.email == "taken@test.com").all()
    assert len(matches) == 1


def test_register_email_case_insensitive(client, db):
    response = client.post(
        "/api/auth/register",
        json={
            "first_name": "John",
            "last_name": "Doe",
            "email": "MixedCase@Test.com",
            "birthdate": "1995-06-15",
            "bio": "hello",
            "gender": "male",
            "country": "DE",
            "interested_in": "female",
            "interests": ["sports"],
            "password": "a-strong-password-123",
        },
    )

    assert response.status_code == 201
    created_user = db.query(User).filter(User.email == "mixedcase@test.com").first()
    assert created_user is not None


@pytest.mark.parametrize(
    "db",
    [
        {
            User: [
                {
                    "first_name": "John",
                    "last_name": "Doe",
                    "email": "john@test.com",
                    "password": hash_password("test123"),
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
def test_login_local(client, db):
    response = client.post(
        "/api/auth/login",
        json={
            "email": "john@test.com",
            "password": "test123",
        },
    )
    assert response.status_code == 200
    assert response.json() == {"authenticated": True}

    cookies = response.cookies

    assert "access_token" in cookies
    assert cookies["access_token"]

    response = client.post(
        "/api/auth/login",
        json={
            "email": "john@test.com",
            "password": "wrong-password",
        },
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid credentials"}

    response = client.post(
        "/api/auth/login",
        json={
            "email": "missing@example.com",
            "password": "password123",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"


def test_google_login_redirect(client):
    with patch(
        "hang.core.oauth.oauth_serv.google.authorize_redirect",
        new_callable=AsyncMock,
    ) as mock_redirect:
        mock_redirect.return_value = RedirectResponse(
            "https://accounts.google.com/o/oauth2/auth"
        )

        response = client.get("/api/auth/login/google", follow_redirects=False)

        assert response.status_code == 307
        assert (
            response.headers["location"] == "https://accounts.google.com/o/oauth2/auth"
        )
        mock_redirect.assert_called_once()


def test_google_callback_creates_user(client, db):
    fake_token = {
        "userinfo": {
            "email": "google@test.com",
            "given_name": "John",
            "family_name": "Google",
            "sub": "google-123",
        }
    }

    with patch(
        "hang.core.oauth.oauth_serv.google.authorize_access_token",
        new_callable=AsyncMock,
    ) as mock_token:
        mock_token.return_value = fake_token

        response = client.get(
            "/api/auth/login/google/callback",
            follow_redirects=False,
        )

    assert response.status_code == 307
    assert response.headers["location"] == "/swipes"

    user = db.query(User).filter(User.email == "google@test.com").first()

    assert user is not None
    assert user.email == "google@test.com"
    assert user.first_name == "John"
    assert user.last_name == "Google"
    assert user.auth_provider == "google"
    assert user.oauth_id == "google-123"
    assert user.password is None
    assert "access_token" in response.cookies


@pytest.mark.parametrize(
    "db",
    [
        {
            User: [
                {
                    "email": "google@test.com",
                    "first_name": "Old",
                    "last_name": "Name",
                    "auth_provider": "google",
                    "oauth_id": "old-id",
                    "gender": "male",
                    "interested_in": "female",
                    "interests": [],
                    "birthdate": date(1995, 6, 15),
                }
            ]
        }
    ],
    indirect=True,
)
def test_google_callback_existing_user(client, db):
    fake_token = {
        "userinfo": {
            "email": "google@test.com",
            "given_name": "John",
            "family_name": "Google",
            "sub": "new-google-id",
        }
    }

    with patch(
        "hang.core.oauth.oauth_serv.google.authorize_access_token",
        new_callable=AsyncMock,
    ) as mock_token:
        mock_token.return_value = fake_token

        response = client.get(
            "/api/auth/login/google/callback",
            follow_redirects=False,
        )

    assert response.status_code == 307
    assert response.headers["location"] == "/swipes"

    user = db.query(User).filter(User.email == "google@test.com").first()

    assert user.oauth_id == "new-google-id"
    assert user.auth_provider == "google"


def test_google_callback_auth_failure(client):
    fake_token = {
        "userinfo": {
            "email": "g@test.com",
            "sub": "google",
        }
    }

    with (
        patch(
            "hang.core.oauth.oauth_serv.google.authorize_access_token",
            new_callable=AsyncMock,
        ) as mock_token,
        patch(
            "hang.routes.auth.authenticate_user_google",
            return_value=None,
        ),
    ):
        mock_token.return_value = fake_token

        response = client.get(
            "/api/auth/login/google/callback",
            follow_redirects=False,
        )

    assert response.status_code == 307
    assert response.headers["location"] == "/login"


def test_logout(client, db):
    response = client.post("/api/auth/logout")

    assert response.status_code == 200
    assert response.json()["success"] is True
    assert "access_token" not in client.cookies
