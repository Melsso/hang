import pytest

from hang.models.db_models import User, Conversation, Message, UserImage, UserBlock
from tests.utils import make_user_row


@pytest.mark.parametrize(
    "db",
    [
        {
            User: [
                make_user_row("john@test.com", "John"),
                make_user_row("jane@test.com", "Jane"),
            ],
            Conversation: [
                {
                    "user1_id": lambda created: created[User][0].user_id,
                    "user2_id": lambda created: created[User][1].user_id,
                },
            ],
            Message: [
                {
                    "conversation_id": lambda created: (
                        created[Conversation][0].conversation_id
                    ),
                    "sender_id": lambda created: created[User][1].user_id,
                    "content": "hey!",
                    "is_read": False,
                },
            ],
        }
    ],
    indirect=True,
)
@pytest.mark.parametrize("current_user_email", ["john@test.com"], indirect=True)
def test_conversations_list_basic(client, db):
    conversation = db.info["seeded"][Conversation][0]
    message = db.info["seeded"][Message][0]
    jane = db.info["seeded"][User][1]

    conversation.last_message_id = message.message_id
    db.commit()

    response = client.get("/api/conversations")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1

    preview = body[0]
    assert preview["conversation_id"] == conversation.conversation_id
    assert preview["other_user_id"] == jane.user_id
    assert preview["other_user_name"] == "Jane"
    assert preview["last_message"] == "hey!"
    assert preview["unread_count"] == 1
    assert preview["other_user_img_url"] is None


@pytest.mark.parametrize(
    "db",
    [
        {
            User: [
                make_user_row("john@test.com", "John"),
                make_user_row("jane@test.com", "Jane"),
            ],
            Conversation: [
                {
                    "user1_id": lambda created: created[User][0].user_id,
                    "user2_id": lambda created: created[User][1].user_id,
                },
            ],
            UserImage: [
                {
                    "user_id": lambda created: created[User][1].user_id,
                    "image_key": "jane-key.png",
                    "position": 0,
                },
            ],
            Message: [
                {
                    "conversation_id": lambda created: (
                        created[Conversation][0].conversation_id
                    ),
                    "sender_id": lambda created: created[User][1].user_id,
                    "content": "first",
                    "is_read": True,
                },
                {
                    "conversation_id": lambda created: (
                        created[Conversation][0].conversation_id
                    ),
                    "sender_id": lambda created: created[User][1].user_id,
                    "content": "second",
                    "is_read": False,
                },
                {
                    "conversation_id": lambda created: (
                        created[Conversation][0].conversation_id
                    ),
                    "sender_id": lambda created: created[User][1].user_id,
                    "content": "third",
                    "is_read": False,
                },
            ],
        }
    ],
    indirect=True,
)
@pytest.mark.parametrize("current_user_email", ["john@test.com"], indirect=True)
def test_conversations_list_unread_count_and_image(client, db):
    conversation = db.info["seeded"][Conversation][0]
    last_message = db.info["seeded"][Message][-1]

    conversation.last_message_id = last_message.message_id
    db.commit()

    response = client.get("/api/conversations")

    assert response.status_code == 200
    preview = response.json()[0]

    assert preview["unread_count"] == 2
    assert preview["last_message"] == "third"
    assert preview["other_user_img_url"] == "https://fake-storage.test/jane-key.png"


@pytest.mark.parametrize(
    "db",
    [
        {
            User: [
                make_user_row("john@test.com", "John"),
                make_user_row("jane@test.com", "Jane"),
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
@pytest.mark.parametrize("current_user_email", ["john@test.com"], indirect=True)
def test_conversations_list_excludes_blocked(client, db):
    response = client.get("/api/conversations")

    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.parametrize(
    "db",
    [
        {
            User: [
                make_user_row("john@test.com", "John"),
                make_user_row("jane@test.com", "Jane"),
            ],
            Conversation: [
                {
                    "user1_id": lambda created: created[User][0].user_id,
                    "user2_id": lambda created: created[User][1].user_id,
                },
            ],
            Message: [
                {
                    "conversation_id": lambda created: (
                        created[Conversation][0].conversation_id
                    ),
                    "sender_id": lambda created: created[User][1].user_id,
                    "content": f"message {i}",
                    "is_read": False,
                }
                for i in range(25)
            ],
        }
    ],
    indirect=True,
)
@pytest.mark.parametrize("current_user_email", ["john@test.com"], indirect=True)
def test_messages_first_page_paginates_and_marks_read(client, db):
    conversation = db.info["seeded"][Conversation][0]

    response = client.get(f"/api/conversations/{conversation.conversation_id}/messages")

    assert response.status_code == 200
    body = response.json()

    assert body["conversation_id"] == conversation.conversation_id
    assert len(body["messages"]) == 20
    assert body["has_more"] is True
    assert body["next_cursor"] is not None

    assert body["messages"][0]["content"] == "message 5"
    assert body["messages"][-1]["content"] == "message 24"

    unread_remaining = (
        db.query(Message)
        .filter(Message.conversation_id == conversation.conversation_id)
        .filter(Message.is_read.is_(False))
        .count()
    )
    assert unread_remaining == 0


@pytest.mark.parametrize(
    "db",
    [
        {
            User: [
                make_user_row("john@test.com", "John"),
                make_user_row("jane@test.com", "Jane"),
            ],
            Conversation: [
                {
                    "user1_id": lambda created: created[User][0].user_id,
                    "user2_id": lambda created: created[User][1].user_id,
                },
            ],
            Message: [
                {
                    "conversation_id": lambda created: (
                        created[Conversation][0].conversation_id
                    ),
                    "sender_id": lambda created: created[User][1].user_id,
                    "content": f"message {i}",
                    "is_read": False,
                }
                for i in range(25)
            ],
        }
    ],
    indirect=True,
)
@pytest.mark.parametrize("current_user_email", ["john@test.com"], indirect=True)
def test_messages_second_page_does_not_mark_read(client, db):
    conversation = db.info["seeded"][Conversation][0]
    all_messages = sorted(db.info["seeded"][Message], key=lambda m: m.message_id)
    cursor = all_messages[5].message_id

    response = client.get(
        f"/api/conversations/{conversation.conversation_id}/messages",
        params={"before_message_id": cursor},
    )

    assert response.status_code == 200
    body = response.json()

    assert len(body["messages"]) == 5
    assert body["has_more"] is False
    assert body["next_cursor"] is None

    unread_remaining = (
        db.query(Message)
        .filter(Message.conversation_id == conversation.conversation_id)
        .filter(Message.is_read.is_(False))
        .count()
    )
    assert unread_remaining == 25


@pytest.mark.parametrize(
    "db",
    [
        {
            User: [
                make_user_row("john@test.com", "John"),
                make_user_row("jane@test.com", "Jane"),
                make_user_row("amy@test.com", "Amy"),
            ],
            Conversation: [
                {
                    "user1_id": lambda created: created[User][1].user_id,
                    "user2_id": lambda created: created[User][2].user_id,
                },
            ],
        }
    ],
    indirect=True,
)
@pytest.mark.parametrize("current_user_email", ["john@test.com"], indirect=True)
def test_messages_not_your_conversation(client, db):
    conversation = db.info["seeded"][Conversation][0]

    response = client.get(f"/api/conversations/{conversation.conversation_id}/messages")

    assert response.status_code == 403
    assert response.json()["detail"] == {
        "redirect_url": "/api/swipes/home",
        "reason": "no_conversation_access",
    }
