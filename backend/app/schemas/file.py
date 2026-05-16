"""Pydantic schemas for File API responses"""

from pydantic import BaseModel, ConfigDict
from datetime import datetime
from uuid import UUID


class FileResponse(BaseModel):
    """Response schema for uploaded files"""

    id: UUID
    job_id: UUID
    uploader_id: UUID
    original_filename: str
    mime_type: str
    file_size: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
