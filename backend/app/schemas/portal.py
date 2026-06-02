"""Pydantic schemas for crew portal API"""

from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from uuid import UUID
from app.schemas.notification import NotificationCounts


class PortalAssignmentItem(BaseModel):
    """Single assignment in dashboard view"""

    assignment_id: UUID
    job_id: UUID
    job_title: str
    job_venue: str | None
    scheduled_start: datetime | None
    scheduled_end: datetime | None
    role: str | None
    status: str  # AssignmentState value

    model_config = ConfigDict(from_attributes=True)


class PortalDashboardResponse(BaseModel):
    """Dashboard data returned on crew login"""

    upcoming: list[PortalAssignmentItem]  # Future assignments, sorted by scheduled_start ASC
    recent: list[PortalAssignmentItem]  # Last 7 days completed, sorted by scheduled_start DESC
    counts: NotificationCounts  # Reuse existing schema

    model_config = ConfigDict(from_attributes=True)


class PortalFileItem(BaseModel):
    """File metadata for portal job detail"""

    id: UUID
    original_filename: str
    mime_type: str
    file_size: int
    uploaded_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PortalJobDetailResponse(BaseModel):
    """Job detail visible to assigned crew"""

    id: UUID
    title: str
    description: str | None
    venue: str | None
    scheduled_start: datetime | None
    scheduled_end: datetime | None
    state: str
    crew_role: str | None
    assignment_id: UUID
    assignment_status: str
    files: list[PortalFileItem]

    model_config = ConfigDict(from_attributes=True)


class PortalProfileUpdate(BaseModel):
    """Crew self-service profile update - restricted fields only"""

    phone: str | None = None
    bio: str | None = None


class PortalDeclineRequest(BaseModel):
    """Optional reason when declining assignment"""

    declined_reason: str | None = None


class PortalAssignmentDetail(BaseModel):
    """Assignment with job context for portal list"""

    id: UUID
    job_id: UUID
    job_title: str
    job_venue: str | None
    scheduled_start: datetime | None
    scheduled_end: datetime | None
    role: str | None
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
