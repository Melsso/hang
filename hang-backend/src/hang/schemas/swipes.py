from pydantic import BaseModel
from typing import Optional
from enum import Enum

from hang.schemas.conversations import ConversationResponse


class SwipeType(str, Enum):
    like = "like"
    pass_ = "pass"
    super_like = "super_like"


class SwipeCreate(BaseModel):
    to_user_id: int
    swipe_type: SwipeType


class SwipeResponse(BaseModel):
    success: bool
    conversation: Optional[ConversationResponse] = None
