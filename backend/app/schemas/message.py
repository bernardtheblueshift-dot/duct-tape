"""Pydantic schemas for Message API requests and responses"""

from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from uuid import UUID


class MessageCreate(BaseModel):
    """Request schema for creating a message"""

    content: str = Field(..., min_length=1)
    reply_to_id: UUID | None = None
    file_ids: list[UUID] = []  # Existing JobFile IDs to attach


class MessageResponse(BaseModel):
    """Response schema with all message fields"""

    id: UUID
    job_id: UUID
    user_id: UUID
    content: str
    reply_to_id: UUID | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MessageSearchParams(BaseModel):
    """Query parameters for message search"""

    search: str | None = None  # ILIKE search on content
