"""Pydantic schemas for Job API requests and responses"""

from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from uuid import UUID
from app.models.job import JobState


class CrewAssignmentSummary(BaseModel):
    """Summary of crew assignment for embedding in JobResponse"""

    id: UUID
    crew_id: UUID
    crew_name: str
    role: str | None
    status: str  # Use str to avoid circular import with AssignmentState


class EquipmentAssignmentSummary(BaseModel):
    """Summary of equipment assignment for embedding in JobResponse"""

    id: UUID
    equipment_id: UUID
    equipment_name: str
    quantity_assigned: int


class MessageSummary(BaseModel):
    """Summary of message for embedding in CoordinationSummary"""

    id: UUID
    user_id: UUID
    content: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TaskSummary(BaseModel):
    """Summary of task for embedding in CoordinationSummary"""

    id: UUID
    title: str
    status: str  # Use str to avoid importing TaskStatus (same pattern as CrewAssignmentSummary)
    priority: str
    assignee_id: UUID | None
    deadline: datetime | None

    model_config = ConfigDict(from_attributes=True)


class FileSummary(BaseModel):
    """Summary of file for embedding in CoordinationSummary"""

    id: UUID
    original_filename: str
    mime_type: str
    file_size: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CoordinationSummary(BaseModel):
    """Summary of coordination data (messages, tasks, files) for embedding in JobResponse"""

    message_count: int = 0
    recent_messages: list[MessageSummary] = []
    task_total: int = 0
    task_todo: int = 0
    task_in_progress: int = 0
    task_done: int = 0
    task_overdue: int = 0
    file_count: int = 0
    recent_files: list[FileSummary] = []


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
    # Phase 5: Coordination Layer - real summary data
    coordination: CoordinationSummary = CoordinationSummary()

    model_config = ConfigDict(from_attributes=True)


class JobTransitionRequest(BaseModel):
    """Request schema for job state transitions"""

    new_state: JobState
