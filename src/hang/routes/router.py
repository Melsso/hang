from fastapi import APIRouter

router = APIRouter()

@router.get("/users")
def get_users():
    return []


@router.get("/")
def get_default():
    return {"status": "ok", "code": 200}