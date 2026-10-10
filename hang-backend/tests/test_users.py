import pytest
import io
from datetime import date, timedelta
from PIL import Image

from hang.models.db_models import User, Conversation, UserReport, UserBlock, UserImage
from hang.schemas.config import conf
from tests.utils import make_user_row


def make_test_png() -> bytes:
    img = Image.new("RGB", (1, 1), color=(255, 0, 0))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


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
                )
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
                make_user_row(
                    "john@test.com",
                    "John",
                    country="DE",
                    interests=["sports"],
                    gender="male",
                    interested_in="female",
                )
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
                make_user_row(
                    "john@test.com",
                    "John",
                    country="DE",
                    interests=["sports"],
                    gender="male",
                    interested_in="female",
                ),
                make_user_row(
                    "jane@test.com",
                    "Jane",
                    country="DE",
                    interests=["music", "hiking"],
                    gender="female",
                    interested_in="male",
                ),
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
                make_user_row(
                    "john@test.com",
                    "John",
                    country="DE",
                    interests=["sports"],
                    gender="male",
                    interested_in="female",
                ),
                make_user_row(
                    "jane@test.com",
                    "Jane",
                    country="DE",
                    interests=["music"],
                    gender="female",
                    interested_in="male",
                ),
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
                make_user_row(
                    "john@test.com",
                    "John",
                    country="DE",
                    interests=["sports"],
                    gender="male",
                    interested_in="female",
                ),
                make_user_row(
                    "jane@test.com",
                    "Jane",
                    country="DE",
                    interests=["music"],
                    gender="female",
                    interested_in="male",
                ),
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
                make_user_row(
                    "john@test.com",
                    "John",
                    country="DE",
                    interests=["sports"],
                    gender="male",
                    interested_in="female",
                ),
                make_user_row(
                    "jane@test.com",
                    "Jane",
                    country="DE",
                    interests=["music"],
                    gender="female",
                    interested_in="male",
                ),
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
                make_user_row(
                    "john@test.com",
                    "John",
                    country="DE",
                    interests=["sports"],
                    gender="male",
                    interested_in="female",
                ),
                make_user_row(
                    "jane@test.com",
                    "Jane",
                    country="DE",
                    interests=["music"],
                    gender="female",
                    interested_in="male",
                ),
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
                make_user_row(
                    "john@test.com",
                    "John",
                    country="DE",
                    interests=["sports"],
                    gender="male",
                    interested_in="female",
                ),
                make_user_row(
                    "jane@test.com",
                    "Jane",
                    country="DE",
                    interests=["music"],
                    gender="female",
                    interested_in="male",
                ),
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


@pytest.mark.parametrize(
    "db",
    [
        {
            User: [
                make_user_row(
                    "john@test.com",
                    "John",
                    country="DE",
                    interests=["sports"],
                    gender="male",
                    interested_in="female",
                ),
            ],
            UserImage: [
                {
                    "user_id": lambda created: created[User][0].user_id,
                    "image_key": "some-key",
                    "position": 0,
                },
                {
                    "user_id": lambda created: created[User][0].user_id,
                    "image_key": "some-other-key",
                    "position": 1,
                },
            ],
        }
    ],
    indirect=True,
)
@pytest.mark.parametrize("current_user_email", ["john@test.com"], indirect=True)
def test_profile_update_info(client, db):
    seeded_images = db.info["seeded"][UserImage]
    img1, img2 = seeded_images[0], seeded_images[1]

    response = client.post(
        "/api/users/profile",
        json={
            "first_name": "Jonathan",
            "bio": "Updated bio text",
            "images": [
                {"image_id": img1.image_id, "position": 1},
                {"image_id": img2.image_id, "position": 0},
            ],
        },
    )
    assert response.status_code == 200
    assert response.json()["first_name"] == "Jonathan"
    assert response.json()["email"] == "john@test.com"
    assert response.json()["bio"] == "Updated bio text"
    assert response.json()["images"][0] == {
        "image_id": img2.image_id,
        "image_key": img2.image_key,
        "position": img2.position,
        "image_url": "https://fake-storage.test/some-other-key",
    }
    assert response.json()["images"][1] == {
        "image_id": img1.image_id,
        "image_key": img1.image_key,
        "position": img1.position,
        "image_url": "https://fake-storage.test/some-key",
    }

    updated_user = db.query(User).filter(User.email == "john@test.com").first()
    assert updated_user.first_name == "Jonathan"
    assert updated_user.bio == "Updated bio text"
    assert img1.position == 1
    assert img2.position == 0


@pytest.mark.parametrize(
    "db",
    [
        {
            User: [
                make_user_row(
                    "john@test.com",
                    "John",
                    country="DE",
                    interests=["sports"],
                    gender="male",
                    interested_in="female",
                ),
            ],
            UserImage: [
                {
                    "user_id": lambda created: created[User][0].user_id,
                    "image_key": "some-key",
                    "position": 0,
                },
                {
                    "user_id": lambda created: created[User][0].user_id,
                    "image_key": "some-other-key",
                    "position": 1,
                },
            ],
        }
    ],
    indirect=True,
)
@pytest.mark.parametrize("current_user_email", ["john@test.com"], indirect=True)
def test_profile_update_info_del_img(client, db):
    seeded_images = db.info["seeded"][UserImage]
    img1, img2 = seeded_images[0], seeded_images[1]

    response = client.post(
        "/api/users/profile",
        json={"images": [], "deleted_images": [img1.image_id]},
    )
    assert response.status_code == 200
    assert response.json()["email"] == "john@test.com"
    assert len(response.json()["images"]) == 1
    assert response.json()["images"][0] == {
        "image_id": img2.image_id,
        "image_key": img2.image_key,
        "position": img2.position,
        "image_url": "https://fake-storage.test/some-other-key",
    }

    response = client.post(
        "/api/users/profile",
        json={"images": [], "deleted_images": [img2.image_id]},
    )

    assert len(response.json()["images"]) == 0
    assert response.json()["images"] == []


@pytest.mark.parametrize(
    "db",
    [
        {
            User: [
                make_user_row(
                    "john@test.com",
                    "John",
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
@pytest.mark.parametrize("current_user_email", ["john@test.com"], indirect=True)
def test_profile_upload_image(client, db):
    response = client.post(
        "/api/users/profile/upload-image",
        files=[
            ("files", ("test.png", io.BytesIO(make_test_png()), "image/png")),
        ],
    )

    assert response.status_code == 200

    body = response.json()
    assert len(body["images"]) == 1

    image = body["images"][0]
    assert image["position"] == 0
    assert image["image_key"].startswith(f"users/{body['user_id']}/images/")
    assert image["image_key"].endswith(".png")
    assert image["image_url"] == f"https://fake-storage.test/{image['image_key']}"

    updated_user = db.query(User).filter(User.email == "john@test.com").first()
    assert len(updated_user.images) == 1
    assert updated_user.images[0].image_key == image["image_key"]
    assert updated_user.images[0].position == 0


@pytest.mark.parametrize(
    "db",
    [
        {
            User: [
                make_user_row(
                    "john@test.com",
                    "John",
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
@pytest.mark.parametrize("current_user_email", ["john@test.com"], indirect=True)
def test_upload_multiple_images(client, db):
    response = client.post(
        "/api/users/profile/upload-image",
        files=[
            ("files", ("first.png", io.BytesIO(make_test_png()), "image/png")),
            ("files", ("second.png", io.BytesIO(make_test_png()), "image/png")),
            ("files", ("third.png", io.BytesIO(make_test_png()), "image/png")),
        ],
    )

    assert response.status_code == 200

    body = response.json()
    assert len(body["images"]) == 3

    positions = sorted(img["position"] for img in body["images"])
    assert positions == [0, 1, 2]

    keys = {img["image_key"] for img in body["images"]}
    assert len(keys) == 3

    updated_user = db.query(User).filter(User.email == "john@test.com").first()
    assert len(updated_user.images) == 3


@pytest.mark.parametrize(
    "db",
    [
        {
            User: [
                make_user_row(
                    "john@test.com",
                    "John",
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
@pytest.mark.parametrize("current_user_email", ["john@test.com"], indirect=True)
@pytest.mark.parametrize(
    "filename, content, content_type, expected_error",
    [
        (
            "test.txt",
            b"this is definitely not an image file",
            "text/plain",
            "Could not detect image type.",
        ),
        ("empty.png", b"", "image/png", "Empty file provided."),
        (
            "big.png",
            b"a" * (conf.MAX_IMAGE_SIZE + 1),
            "image/png",
            "File too large.",
        ),
    ],
)
def test_upload_image_invalid_cases(
    client, db, filename, content, content_type, expected_error
):
    response = client.post(
        "/api/users/profile/upload-image",
        files=[("files", (filename, io.BytesIO(content), content_type))],
    )

    assert response.status_code == 400
    assert expected_error in response.json()["detail"]

    updated_user = db.query(User).filter(User.email == "john@test.com").first()
    assert len(updated_user.images) == 0


@pytest.mark.parametrize(
    "db",
    [
        {
            User: [
                make_user_row(
                    "john@test.com",
                    "John",
                    country="DE",
                    interests=["sports"],
                    gender="male",
                    interested_in="female",
                ),
            ],
            UserImage: [
                {
                    "user_id": lambda created: created[User][0].user_id,
                    "image_key": f"seed-key-{i}",
                    "position": i,
                }
                for i in range(conf.MAX_IMAGES)
            ],
        }
    ],
    indirect=True,
)
@pytest.mark.parametrize("current_user_email", ["john@test.com"], indirect=True)
def test_upload_image_exceeds_max_count(client, db):
    response = client.post(
        "/api/users/profile/upload-image",
        files=[("files", ("test.png", io.BytesIO(make_test_png()), "image/png"))],
    )

    assert response.status_code == 400
    assert f"Maximum of {conf.MAX_IMAGES} images allowed" in response.json()["detail"]

    updated_user = db.query(User).filter(User.email == "john@test.com").first()
    assert len(updated_user.images) == conf.MAX_IMAGES


@pytest.mark.parametrize(
    "db", [{User: [make_user_row("john@test.com", "John")]}], indirect=True
)
@pytest.mark.parametrize("current_user_email", ["john@test.com"], indirect=True)
def test_profile_update_under_18_is_rejected_and_not_persisted(client, db):
    original = db.query(User).filter(User.email == "john@test.com").first().birthdate
    too_young = date.today() - timedelta(days=365 * 10)

    response = client.post(
        "/api/users/profile", json={"birthdate": too_young.isoformat()}
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "You must be over 18 years old."

    db.expire_all()
    assert (
        db.query(User).filter(User.email == "john@test.com").first().birthdate
        == original
    )


@pytest.mark.parametrize(
    "db",
    [{User: [make_user_row("g@test.com", "Google", birthdate=None)]}],
    indirect=True,
)
@pytest.mark.parametrize("current_user_email", ["g@test.com"], indirect=True)
def test_user_without_birthdate_can_load_and_set_it(client, db):
    response = client.get("/api/users/profile")
    assert response.status_code == 200
    assert response.json()["birthdate"] is None

    response = client.post("/api/users/profile", json={"birthdate": "1995-06-15"})
    assert response.status_code == 200
    assert response.json()["birthdate"] == "1995-06-15"


@pytest.mark.parametrize(
    "db", [{User: [make_user_row("john@test.com", "John")]}], indirect=True
)
@pytest.mark.parametrize("current_user_email", ["john@test.com"], indirect=True)
@pytest.mark.parametrize(
    "patch", [{"bio": "x" * 501}, {"country": "XX"}, {"first_name": ""}]
)
def test_profile_update_validation(client, db, patch):
    assert client.post("/api/users/profile", json=patch).status_code == 422
