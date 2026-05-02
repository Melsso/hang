from pydantic import BaseModel, Field
from datetime import datetime, timezone


class Conversation(BaseModel):
    conversation_id: int
    user1_id: int
    user2_id: int

    last_message_id: int | None = None

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ConversationCreate(BaseModel):
    user1_id: int
    user2_id: int


class ConversationResponse(BaseModel):
    conversation_id: int
    user1_id: int
    user2_id: int

    last_message_id: int | None

    created_at: datetime
    updated_at: datetime


class ConversationUpdate(BaseModel):
    last_message_id: int | None = None