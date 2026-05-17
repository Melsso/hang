from pydantic import BaseModel, Field
from datetime import datetime
from typing import List


class MessagePreview(BaseModel):
    message_id: int
    sender_id: int
    content: str
    created_at: datetime


class MessageListResponse(BaseModel):
    conversation_id: int
    current_user_id: int
    messages: List[MessagePreview] = Field(default_factory=list)
