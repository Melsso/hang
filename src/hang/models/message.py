from pydantic import BaseModel, Field
from datetime import timezone, datetime


class Message(BaseModel):
    message_id: int
    sender_id: int
    conversation_id: int
    text: str
    is_read: bool = False
    reply_to_id: int | None = None

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class MessageCreate(BaseModel):
    conversation_id: int
    sender_id: int
    text: str
    reply_to_id: int | None = None


class MessageResponse(BaseModel):
    message_id: int
    conversation_id: int
    sender_id: int
    text: str
    is_read: bool
    reply_to_id: int | None

    created_at: datetime


class MessageUpdate(BaseModel):
    content: str | None = None
    is_read: bool | None = None
