from pydantic import BaseModel
from enum import Enum


class SwipeType(str, Enum):
    like = "like"
    pass_ = "pass"
    super_like = "super_like"


class SwipeCreate(BaseModel):
    to_user_id: int
    swipe_type: SwipeType
