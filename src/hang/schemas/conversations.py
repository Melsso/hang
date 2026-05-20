from pydantic import BaseModel, ConfigDict
from datetime import datetime


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
