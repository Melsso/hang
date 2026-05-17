from pydantic import BaseModel
from enum import Enum
from hang.models.conversation import ConversationResponse


class SwipeType(str, Enum):
    like = "like"
    pass_ = "pass"
    super_like = "super_like"


class SwipeCreate(BaseModel):
    to_user_id: int
    swipe_type: SwipeType


class SwipeResponse(BaseModel):
    success: bool
    conversation: ConversationResponse | None = None
