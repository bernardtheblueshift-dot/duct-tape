"""Pydantic schemas for Job API requests and responses"""

from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from uuid import UUID
from app.models.job import JobState


class CrewAssignmentSummary(BaseModel):
    """Summary of crew assignment for embedding in JobResponse"""

    id: UUID
    crew_id: UUID
    role: str | None
    status: str  # Use str to avoid circular import with AssignmentState

    model_config = ConfigDict(from_attributes=True)


class EquipmentAssignmentSummary(BaseModel):
    """Summary of equipment assignment for embedding in JobResponse"""

    id: UUID
    equipment_id: UUID
    quantity_assigned: int

    model_config = ConfigDict(from_attributes=True)


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

    id: UUID
    title: str
    description: str | None
    venue: str | None
    scheduled_start: datetime | None
    scheduled_end: datetime | None
    state: JobState
    created_at: datetime
    updated_at: datetime

    # Phase 3: Resource Management - populated with real data
    assigned_crew: list[CrewAssignmentSummary] = []
    assigned_gear: list[EquipmentAssignmentSummary] = []
    # Placeholder sections for future phases (JOBS-06)
    messages: list = []  # Phase 5: Coordination Layer
    tasks: list = []  # Phase 5: Coordination Layer
    files: list = []  # Phase 5: Coordination Layer

    model_config = ConfigDict(from_attributes=True)


class JobTransitionRequest(BaseModel):
    """Request schema for job state transitions"""

    new_state: JobState
