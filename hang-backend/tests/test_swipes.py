import pytest

from hang.models.db_models import User, Swipe, Conversation
from tests.utils import make_user_row


@pytest.mark.parametrize(
    "db",
    [
        {
            User: [
                make_user_row(
                    "john@test.com",
                    "John",
                    country="DE",
                    interests=["sports", "music"],
                    gender="male",
                    interested_in="female",
                ),
                make_user_row(
                    "jane@test.com",
                    "Jane",
                    country="DE",
                    interests=["sports", "outdoor"],
                    gender="female",
                    interested_in="male",
                ),
                make_user_row(
                    "amy@test.com",
                    "Amy",
                    country="US",
                    interests=["cooking"],
                    gender="female",
                    interested_in="male",
                ),
            ]
        }
    ],
    indirect=True,
)
@pytest.mark.parametrize("current_user_email", ["john@test.com"], indirect=True)
def test_home_returns_scored_candidates(client, db):
    john = db.query(User).filter(User.email == "john@test.com").first()
    jane = db.query(User).filter(User.email == "jane@test.com").first()
    amy = db.query(User).filter(User.email == "amy@test.com").first()

    response = client.get("/api/swipes/home")

    assert response.status_code == 200

    profiles = response.json()

    ids = {p["user_id"] for p in profiles}
    assert ids == {jane.user_id, amy.user_id}
    assert john.user_id not in ids

    assert profiles[0]["user_id"] == jane.user_id
    assert profiles[1]["user_id"] == amy.user_id


@pytest.mark.parametrize(
    "db",
    [
        {
            User: [
                make_user_row("john@test.com", "John"),
                make_user_row(
                    "jane@test.com", "Jane", gender="female", interested_in="male"
                ),
            ]
        }
    ],
    indirect=True,
)
@pytest.mark.parametrize("current_user_email", ["john@test.com"], indirect=True)
def test_home_excludes_already_swiped(client, db):
    john = db.query(User).filter(User.email == "john@test.com").first()
    jane = db.query(User).filter(User.email == "jane@test.com").first()

    db.add(Swipe(from_user_id=john.user_id, to_user_id=jane.user_id, swipe_type="pass"))
    db.commit()

    response = client.get("/api/swipes/home")

    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.parametrize(
    "db",
    [
        {
            User: [
                make_user_row(
                    "john@test.com",
                    "John",
                    gender="male",
                    interested_in="female",
                    interests=["sports"],
                    birthdate=None,
                )
            ]
        }
    ],
    indirect=True,
)
@pytest.mark.parametrize("current_user_email", ["john@test.com"], indirect=True)
def test_home_forbidden_when_profile_incomplete(client, db):
    response = client.get("/api/swipes/home")

    assert response.status_code == 403
    assert response.json()["detail"] == "Profile incomplete"


@pytest.mark.parametrize(
    "db",
    [
        {
            User: [
                make_user_row("john@test.com", "John"),
                make_user_row(
                    "jane@test.com", "Jane", gender="female", interested_in="male"
                ),
            ]
        }
    ],
    indirect=True,
)
@pytest.mark.parametrize("current_user_email", ["john@test.com"], indirect=True)
def test_swipe_pass_no_match(client, db):
    jane = db.query(User).filter(User.email == "jane@test.com").first()

    response = client.post(
        "/api/swipes/swipe-action",
        json={"to_user_id": jane.user_id, "swipe_type": "pass"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["conversation"] is None

    swipe = (
        db.query(Swipe)
        .filter(
            Swipe.from_user_id
            == db.query(User).filter(User.email == "john@test.com").first().user_id,
            Swipe.to_user_id == jane.user_id,
        )
        .first()
    )
    assert swipe is not None
    assert swipe.swipe_type == "pass"


@pytest.mark.parametrize(
    "db",
    [
        {
            User: [
                make_user_row("john@test.com", "John"),
                make_user_row(
                    "jane@test.com", "Jane", gender="female", interested_in="male"
                ),
            ]
        }
    ],
    indirect=True,
)
@pytest.mark.parametrize("current_user_email", ["john@test.com"], indirect=True)
def test_swipe_like_no_mutual_no_conversation(client, db):
    jane = db.query(User).filter(User.email == "jane@test.com").first()

    response = client.post(
        "/api/swipes/swipe-action",
        json={"to_user_id": jane.user_id, "swipe_type": "like"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["conversation"] is None

    assert db.query(Conversation).count() == 0


@pytest.mark.parametrize(
    "db",
    [
        {
            User: [
                make_user_row("john@test.com", "John"),
                make_user_row(
                    "jane@test.com", "Jane", gender="female", interested_in="male"
                ),
            ]
        }
    ],
    indirect=True,
)
@pytest.mark.parametrize("current_user_email", ["john@test.com"], indirect=True)
def test_swipe_like_mutual_creates_conversation(client, db):
    john = db.query(User).filter(User.email == "john@test.com").first()
    jane = db.query(User).filter(User.email == "jane@test.com").first()

    db.add(Swipe(from_user_id=jane.user_id, to_user_id=john.user_id, swipe_type="like"))
    db.commit()

    response = client.post(
        "/api/swipes/swipe-action",
        json={"to_user_id": jane.user_id, "swipe_type": "like"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["conversation"] is not None
    assert body["conversation"]["user1_id"] == john.user_id
    assert body["conversation"]["user2_id"] == jane.user_id

    conversation = (
        db.query(Conversation)
        .filter(
            Conversation.user1_id == john.user_id,
            Conversation.user2_id == jane.user_id,
        )
        .first()
    )
    assert conversation is not None
