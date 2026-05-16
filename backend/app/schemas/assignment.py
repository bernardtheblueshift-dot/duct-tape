"""Pydantic schemas for crew and equipment assignment operations"""

from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from uuid import UUID
from app.models.assignment import AssignmentState


class CrewAssignmentCreate(BaseModel):
    """Request schema for creating crew assignment"""

    crew_id: UUID
    job_id: UUID
    role: str | None = None
    force: bool = False  # Override conflict warnings
    override_reason: str | None = None


class CrewAssignmentResponse(BaseModel):
    """Response schema for crew assignment"""

    id: UUID
    crew_id: UUID
    job_id: UUID
    role: str | None
    status: AssignmentState
    override_reason: str | None
    declined_reason: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EquipmentAssignmentCreate(BaseModel):
    """Request schema for creating equipment assignment"""

    equipment_id: UUID
    job_id: UUID
    quantity_assigned: int = Field(1, ge=1)


class EquipmentAssignmentResponse(BaseModel):
    """Response schema for equipment assignment"""

    id: UUID
    equipment_id: UUID
    job_id: UUID
    quantity_assigned: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AssignmentTransitionRequest(BaseModel):
    """Request schema for assignment state transitions"""

    new_status: AssignmentState
    declined_reason: str | None = None


class ConflictDetail(BaseModel):
    """Details of a single conflict"""

    job_id: UUID
    job_title: str
    scheduled_start: datetime | None
    scheduled_end: datetime | None


class ConflictWarning(BaseModel):
    """Warning response when conflicts are detected"""

    message: str
    conflicts: list[ConflictDetail]
