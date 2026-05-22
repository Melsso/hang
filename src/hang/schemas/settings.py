from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional


class BlockedUserResponse(BaseModel):
    user_id: int
    first_name: str
    last_name: str

    model_config = ConfigDict(from_attributes=True)


class ReportResponse(BaseModel):
    first_name: str
    last_name: str
    reported_id: int
    reason: str
    message: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DeleteReportRequest(BaseModel):
    reported_user_id: int
