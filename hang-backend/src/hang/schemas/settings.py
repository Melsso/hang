from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from typing import Optional


class BlockedUserResponse(BaseModel):
    user_id: int
    first_name: str
    last_name: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ReportResponse(BaseModel):
    first_name: str
    last_name: str
    reported_id: int
    reason: str
    message: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PasswordChange(BaseModel):
    old_password: str
    new_password: str = Field(min_length=8, max_length=72)


class DeleteReportRequest(BaseModel):
    reported_user_id: int
