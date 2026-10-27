import pytest

from hang.models.db_models import User, UserBlock, UserReport

from hang.helpers.auth import pwd_context
from unit_tests.utils import make_user_row


@pytest.mark.parametrize(
    "db",
    [
        {
            User: [
                make_user_row("john@test.com", "John"),
                make_user_row("jane@test.com", "Jane"),
            ]
        }
    ],
    indirect=True,
)
@pytest.mark.parametrize("current_user_email", ["john@test.com"], indirect=True)
def test_block_user(client, db):
    jane = db.query(User).filter(User.email == "jane@test.com").first()

    response = client.post(
        "/api/users/profile/block",
        json={"blocked_user_id": jane.user_id},
    )

    assert response.status_code == 200
    assert response.json()["status"] is True

    john = db.query(User).filter(User.email == "john@test.com").first()
    block = (
        db.query(UserBlock)
        .filter(
            UserBlock.blocker_id == john.user_id, UserBlock.blocked_id == jane.user_id
        )
        .first()
    )
    assert block is not None


@pytest.mark.parametrize(
    "db",
    [
        {
            User: [
                make_user_row("john@test.com", "John"),
                make_user_row("jane@test.com", "Jane"),
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
@pytest.mark.parametrize("current_user_email", ["john@test.com"], indirect=True)
def test_unblock_user(client, db):
    jane = db.query(User).filter(User.email == "jane@test.com").first()

    response = client.post(
        "/api/settings/unblock",
        json={"blocked_user_id": jane.user_id},
    )

    assert response.status_code == 200
    assert response.json()["success"] is True

    john = db.query(User).filter(User.email == "john@test.com").first()
    block = (
        db.query(UserBlock)
        .filter(
            UserBlock.blocker_id == john.user_id, UserBlock.blocked_id == jane.user_id
        )
        .first()
    )
    assert block is None


@pytest.mark.parametrize(
    "db",
    [
        {
            User: [
                make_user_row("john@test.com", "John"),
                make_user_row("jane@test.com", "Jane"),
            ]
        }
    ],
    indirect=True,
)
@pytest.mark.parametrize("current_user_email", ["john@test.com"], indirect=True)
def test_unblock_user_not_blocked_fails(client, db):
    jane = db.query(User).filter(User.email == "jane@test.com").first()

    response = client.post(
        "/api/settings/unblock",
        json={"blocked_user_id": jane.user_id},
    )

    assert response.status_code == 400
    assert response.json()["success"] is False


@pytest.mark.parametrize(
    "db",
    [
        {
            User: [
                make_user_row("john@test.com", "John"),
                make_user_row("jane@test.com", "Jane"),
                make_user_row("amy@test.com", "Amy"),
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
@pytest.mark.parametrize("current_user_email", ["john@test.com"], indirect=True)
def test_get_blocked_users_list(client, db):
    jane = db.query(User).filter(User.email == "jane@test.com").first()

    response = client.get("/api/settings/blocks")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["user_id"] == jane.user_id
    assert body[0]["first_name"] == "Jane"


@pytest.mark.parametrize(
    "db",
    [
        {
            User: [
                make_user_row("john@test.com", "John"),
                make_user_row("jane@test.com", "Jane"),
            ]
        }
    ],
    indirect=True,
)
@pytest.mark.parametrize("current_user_email", ["john@test.com"], indirect=True)
def test_report_user(client, db):
    jane = db.query(User).filter(User.email == "jane@test.com").first()

    response = client.post(
        "/api/users/profile/report-create",
        json={
            "reported_user_id": jane.user_id,
            "reason": "harassment",
            "message": "sent inappropriate messages",
        },
    )

    assert response.status_code == 200
    assert response.json()["success"] is True

    john = db.query(User).filter(User.email == "john@test.com").first()
    report = (
        db.query(UserReport)
        .filter(
            UserReport.reporter_id == john.user_id,
            UserReport.reported_id == jane.user_id,
        )
        .first()
    )
    assert report is not None
    assert report.reason == "harassment"
    assert report.message == "sent inappropriate messages"
    assert report.status == "open"


@pytest.mark.parametrize(
    "db",
    [
        {
            User: [
                make_user_row("john@test.com", "John"),
                make_user_row("jane@test.com", "Jane"),
            ],
            UserReport: [
                {
                    "reporter_id": lambda created: created[User][0].user_id,
                    "reported_id": lambda created: created[User][1].user_id,
                    "reason": "spam",
                },
            ],
        }
    ],
    indirect=True,
)
@pytest.mark.parametrize("current_user_email", ["john@test.com"], indirect=True)
def test_delete_report(client, db):
    jane = db.query(User).filter(User.email == "jane@test.com").first()

    response = client.post(
        "/api/settings/report-delete",
        json={"reported_user_id": jane.user_id},
    )

    assert response.status_code == 200
    assert response.json()["success"] is True

    john = db.query(User).filter(User.email == "john@test.com").first()
    remaining = (
        db.query(UserReport)
        .filter(
            UserReport.reporter_id == john.user_id,
            UserReport.reported_id == jane.user_id,
        )
        .first()
    )
    assert remaining is None


@pytest.mark.parametrize(
    "db",
    [
        {
            User: [
                make_user_row("john@test.com", "John"),
                make_user_row("jane@test.com", "Jane"),
            ]
        }
    ],
    indirect=True,
)
@pytest.mark.parametrize("current_user_email", ["john@test.com"], indirect=True)
def test_delete_report_nonexistent_fails(client, db):
    jane = db.query(User).filter(User.email == "jane@test.com").first()

    response = client.post(
        "/api/settings/report-delete",
        json={"reported_user_id": jane.user_id},
    )

    assert response.status_code == 400
    assert response.json()["success"] is False


@pytest.mark.parametrize(
    "db",
    [
        {
            User: [
                make_user_row("john@test.com", "John"),
                make_user_row("jane@test.com", "Jane"),
                make_user_row("amy@test.com", "Amy"),
            ],
            UserReport: [
                {
                    "reporter_id": lambda created: created[User][0].user_id,
                    "reported_id": lambda created: created[User][1].user_id,
                    "reason": "spam",
                    "message": "posting ads",
                },
                {
                    "reporter_id": lambda created: created[User][2].user_id,
                    "reported_id": lambda created: created[User][1].user_id,
                    "reason": "harassment",
                },
            ],
        }
    ],
    indirect=True,
)
@pytest.mark.parametrize("current_user_email", ["john@test.com"], indirect=True)
def test_get_reports_only_own(client, db):
    jane = db.query(User).filter(User.email == "jane@test.com").first()

    response = client.get("/api/settings/reports")

    assert response.status_code == 200
    body = response.json()

    assert len(body) == 1
    assert body[0]["reported_id"] == jane.user_id
    assert body[0]["reason"] == "spam"
    assert body[0]["message"] == "posting ads"
    assert body[0]["first_name"] == "Jane"


@pytest.mark.parametrize(
    "db",
    [
        {
            User: [
                {
                    **make_user_row("john@test.com", "John"),
                    "auth_provider": "local",
                    "password": pwd_context.hash("old-correct-password"),
                }
            ]
        }
    ],
    indirect=True,
)
@pytest.mark.parametrize("current_user_email", ["john@test.com"], indirect=True)
def test_change_password_success(client, db):
    response = client.post(
        "/api/settings/change-password",
        json={
            "old_password": "old-correct-password",
            "new_password": "new-strong-password",
        },
    )

    assert response.status_code == 200
    assert response.json()["success"] is True

    updated_user = db.query(User).filter(User.email == "john@test.com").first()
    assert pwd_context.verify("new-strong-password", updated_user.password)
    assert not pwd_context.verify("old-correct-password", updated_user.password)


@pytest.mark.parametrize(
    "db",
    [
        {
            User: [
                {
                    **make_user_row("john@test.com", "John"),
                    "auth_provider": "local",
                    "password": pwd_context.hash("old-correct-password"),
                }
            ]
        }
    ],
    indirect=True,
)
@pytest.mark.parametrize("current_user_email", ["john@test.com"], indirect=True)
def test_change_password_wrong_old_password(client, db):
    response = client.post(
        "/api/settings/change-password",
        json={"old_password": "totally-wrong", "new_password": "new-strong-password"},
    )

    assert response.status_code == 400
    assert response.json()["success"] is False

    updated_user = db.query(User).filter(User.email == "john@test.com").first()
    assert pwd_context.verify("old-correct-password", updated_user.password)


@pytest.mark.parametrize(
    "db",
    [{User: [make_user_row("john@test.com", "John")]}],
    indirect=True,
)
@pytest.mark.parametrize("current_user_email", ["john@test.com"], indirect=True)
def test_delete_account(client, db):
    response = client.post("/api/settings/delete-account")

    assert response.status_code == 200
    assert response.json()["success"] is True

    remaining = db.query(User).filter(User.email == "john@test.com").first()
    assert remaining is None
