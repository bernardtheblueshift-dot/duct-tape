"""Pydantic schemas for Job API requests and responses"""

from pydantic import BaseModel, Field
from datetime import datetime
from app.models.job import JobState


class JobCreate(BaseModel):
    """Request schema for creating job"""

    title: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    venue: str | None = None
    scheduled_start: datetime | None = None
    scheduled_end: datetime | None = None


class JobUpdate(BaseModel):
    """Request schema for updating job (all fields optional for partial updates)"""

    title: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = None
    venue: str | None = None
    scheduled_start: datetime | None = None
    scheduled_end: datetime | None = None
    # state excluded - use transition endpoint


class JobResponse(BaseModel):
    """Response schema with all job fields + placeholders for future phases"""

    id: str
    title: str
    description: str | None
    venue: str | None
    scheduled_start: datetime | None
    scheduled_end: datetime | None
    state: JobState
    created_at: datetime
    updated_at: datetime

    # Placeholder sections for future phases (JOBS-06)
    assigned_crew: list = []  # Phase 3: Resource Management
    assigned_gear: list = []  # Phase 3: Resource Management
    messages: list = []  # Phase 5: Coordination Layer
    tasks: list = []  # Phase 5: Coordination Layer
    files: list = []  # Phase 5: Coordination Layer

    class Config:
        from_attributes = True  # Allows returning SQLAlchemy models directly


class JobTransitionRequest(BaseModel):
    """Request schema for job state transitions"""

    new_state: JobState
