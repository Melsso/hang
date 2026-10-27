import asyncio
import json
import sys
import uuid

import httpx
import websockets

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://dev.localtest.me:8080"
WS_URL = BASE.replace("http", "ws", 1) + "/api/ws/conversations"
PASSWORD = "smoke-password-123"


def make_user(tag: str) -> tuple[httpx.Client, int]:
    client = httpx.Client(base_url=BASE, timeout=10)
    email = f"smoke_{tag}_{uuid.uuid4().hex[:8]}@example.com"
    r = client.post("/api/auth/register", json={
        "first_name": tag, "last_name": "Smoke", "email": email,
        "birthdate": "1995-06-15", "bio": "smoke test", "gender": "other",
        "country": "DE", "interested_in": "everyone", "interests": ["music"],
        "password": PASSWORD,
    })
    assert r.status_code == 201, f"register: {r.status_code} {r.text}"
    r = client.post("/api/auth/login", json={"email": email, "password": PASSWORD})
    assert r.status_code == 200, f"login: {r.status_code} {r.text}"
    session = client.get("/api/auth/session").json()
    assert session["authenticated"] is True, session
    return client, session["user_id"]


async def wait_ready(ws) -> None:
    while json.loads(await asyncio.wait_for(ws.recv(), 10)).get("type") != "ready":
        pass


async def roundtrip(cid: int, token_a: str, token_b: str) -> None:
    def headers(token: str):
        return {"Cookie": f"access_token={token}"}

    async with websockets.connect(WS_URL, additional_headers=headers(token_a)) as wa, \
               websockets.connect(WS_URL, additional_headers=headers(token_b)) as wb:
        await asyncio.gather(wait_ready(wa), wait_ready(wb))
        await wa.send(json.dumps({"conversation_id": cid, "content": "smoke"}))
        while True:
            event = json.loads(await asyncio.wait_for(wb.recv(), 10))
            if event.get("type") == "message":
                assert event["message"]["content"] == "smoke"
                return


def main() -> None:
    a, a_id = make_user("alice")
    b, b_id = make_user("bob")

    r = a.post("/api/swipes/swipe-action", json={"to_user_id": b_id, "swipe_type": "like"})
    assert r.status_code == 200 and r.json()["conversation"] is None, r.text
    r = b.post("/api/swipes/swipe-action", json={"to_user_id": a_id, "swipe_type": "like"})
    assert r.status_code == 200 and r.json()["conversation"], r.text
    cid = r.json()["conversation"]["conversation_id"]

    asyncio.run(roundtrip(cid, a.cookies["access_token"], b.cookies["access_token"]))
    print("smoke test passed")


if __name__ == "__main__":
    main()