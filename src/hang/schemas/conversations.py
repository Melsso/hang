from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from typing import List


class ConversationPreview(BaseModel):
    conversation_id: int
    other_user_id: int
    other_user_name: str
    other_user_img_url: str | None = None
    last_message: str | None
    updated_at: datetime


class ConversationResponse(BaseModel):
    conversation_id: int
    user1_id: int
    user2_id: int

    last_message_id: int | None

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MessagePreview(BaseModel):
    message_id: int
    sender_id: int
    content: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MessageListResponse(BaseModel):
    conversation_id: int
    current_user_id: int
    messages: List[MessagePreview] = Field(default_factory=list)
