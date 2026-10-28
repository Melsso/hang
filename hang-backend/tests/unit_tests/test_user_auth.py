import pytest
from types import SimpleNamespace
from typing import cast
from unittest.mock import AsyncMock, patch

from fastapi import HTTPException, Request
from fastapi.responses import RedirectResponse

from hang.models.db_models import User
from hang.helpers.auth import hash_password, create_access_token
from hang.helpers.users import get_current_user
from unit_tests.utils import make_user_row


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


def _google_token(email="google@test.com", verified=True):
    return {
        "userinfo": {
            "email": email,
            "given_name": "J",
            "family_name": "G",
            "sub": "g-1",
            "email_verified": verified,
        }
    }


def _callback(client, token):
    with patch(
        "hang.core.oauth.oauth_serv.google.authorize_access_token",
        new_callable=AsyncMock,
    ) as m:
        m.return_value = token
        return client.get("/api/auth/login/google/callback", follow_redirects=False)


@pytest.mark.parametrize(
    "db",
    [
        {
            User: [
                make_user_row(
                    "taken@test.com",
                    "Existing",
                    password=hash_password("test123"),
                    country="DE",
                    interests=["sports"],
                    gender="male",
                    interested_in="female",
                ),
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


VALID_REGISTER = {
    "first_name": "John",
    "last_name": "Doe",
    "email": "v@test.com",
    "birthdate": "1995-06-15",
    "bio": "hello",
    "gender": "male",
    "country": "DE",
    "interested_in": "female",
    "interests": ["sports"],
    "password": "a-strong-password-123",
}


@pytest.mark.parametrize(
    "patch_data",
    [
        {"bio": "x" * 501},
        {"country": "XX"},
        {"password": "short"},
        {"first_name": "  "},
    ],
)
def test_register_validation(client, db, patch_data):
    response = client.post("/api/auth/register", json={**VALID_REGISTER, **patch_data})
    assert response.status_code == 422


@pytest.mark.parametrize(
    "db",
    [
        {
            User: [
                make_user_row(
                    "john@test.com",
                    "John",
                    password=hash_password("test123"),
                    country="DE",
                    interests=["sports"],
                    gender="male",
                    interested_in="female",
                ),
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
            "email_verified": True,
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
                make_user_row(
                    "google@test.com",
                    "Old",
                    auth_provider="google",
                    oauth_id="old-id",
                    country="DE",
                    interests=["sports", "music"],
                    gender="male",
                    interested_in="female",
                )
            ],
        }
    ],
    indirect=True,
)
def test_google_callback_existing_user(client, db):
    fake_token = {
        "userinfo": {
            "email": "google@test.com",
            "email_verified": True,
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
            "email_verified": True,
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
    assert response.headers["location"] == "/login?error=google"


def test_logout(client, db):
    response = client.post("/api/auth/logout")

    assert response.status_code == 200
    assert response.json()["success"] is True
    assert "access_token" not in client.cookies


def test_get_current_user_deleted_user_is_401(db):
    token = create_access_token({"sub": "999999"})
    request = cast(
        Request,
        SimpleNamespace(cookies={"access_token": token}, state=SimpleNamespace()),
    )

    with pytest.raises(HTTPException) as exc:
        get_current_user(request, db)

    assert exc.value.status_code == 401


def test_session_without_cookie_is_unauthenticated(client, db):
    response = client.get("/api/auth/session")
    assert response.status_code == 200
    assert response.json() == {
        "authenticated": False,
        "user_id": None,
        "onboarding_required": False,
    }


@pytest.mark.parametrize(
    "db", [{User: [make_user_row("john@test.com", "John")]}], indirect=True
)
def test_session_with_valid_cookie_is_authenticated(client, db):
    john = db.info["seeded"][User][0]
    client.cookies.set("access_token", create_access_token({"sub": str(john.user_id)}))

    body = client.get("/api/auth/session").json()

    assert body["authenticated"] is True
    assert body["user_id"] == john.user_id
    assert body["onboarding_required"] is False


@pytest.mark.parametrize(
    "db",
    [
        {
            User: [
                make_user_row(
                    "john@test.com", "John", password=hash_password("test123")
                )
            ]
        }
    ],
    indirect=True,
)
def test_google_callback_does_not_take_over_local_account(client, db):
    r = _callback(client, _google_token(email="john@test.com"))
    assert r.headers["location"] == "/login?error=google"

    user = db.query(User).filter(User.email == "john@test.com").first()
    assert user.auth_provider == "local"
    assert user.oauth_id == ""
    login = client.post(
        "/api/auth/login", json={"email": "john@test.com", "password": "test123"}
    )
    assert login.status_code == 200


def test_google_callback_unverified_email_rejected(client, db):
    r = _callback(client, _google_token(verified=False))
    assert r.headers["location"] == "/login?error=google"
    assert "access_token" not in r.cookies
    assert db.query(User).filter(User.email == "google@test.com").first() is None
