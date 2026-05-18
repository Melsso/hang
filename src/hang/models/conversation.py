from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from typing import List


class ConversationPreview(BaseModel):
    conversation_id: int
    other_user_id: int
    other_user_name: str
    other_user_image: str | None = None
    last_message: str | None
    updated_at: datetime


class ConversationListResponse(BaseModel):
    success: bool
    conversations: List[ConversationPreview] = Field(default_factory=list)


class ConversationResponse(BaseModel):
    conversation_id: int
    user1_id: int
    user2_id: int

    last_message_id: int | None

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
