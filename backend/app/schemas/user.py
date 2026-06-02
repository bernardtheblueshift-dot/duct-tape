from pydantic import BaseModel, EmailStr, ConfigDict
from datetime import datetime
from uuid import UUID


class UserResponse(BaseModel):
    id: UUID
    email: EmailStr
    name: str
    role: str  # "admin" or "crew"
    is_active: bool
    timezone: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
