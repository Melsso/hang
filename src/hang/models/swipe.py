from pydantic import BaseModel, Field
from datetime import datetime, timezone
from enum import Enum


class SwipeType(str, Enum):
    like = "like"
    pass_ = "pass"
    super_like = "super_like"


class Swipe(BaseModel):
    swipe_id: int
    from_user_id: int
    to_user_id: int
    swipe_type: SwipeType

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class SwipeCreate(BaseModel):
    from_user_id: int
    to_user_id: int
    swipe_type: SwipeType


class SwipeResponse(BaseModel):
    swipe_id: int
    from_user_id: int
    to_user_id: int
    swipe_type: SwipeType

    is_match: bool = False

    created_at: datetime
