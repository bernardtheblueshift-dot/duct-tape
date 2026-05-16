"""Pydantic schemas for crew profile, availability, and rating operations"""

from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from uuid import UUID


class CrewProfileCreate(BaseModel):
    """Request schema for creating crew profile"""

    user_id: UUID
    phone: str | None = None
    bio: str | None = None
    hourly_rate: float | None = Field(None, ge=0)
    skills: list[str] = []


class CrewProfileUpdate(BaseModel):
    """Request schema for updating crew profile (all fields optional)"""

    phone: str | None = None
    bio: str | None = None
    hourly_rate: float | None = Field(None, ge=0)
    skills: list[str] | None = None


class CrewProfileResponse(BaseModel):
    """Response schema with all crew profile fields"""

    id: UUID
    user_id: UUID
    phone: str | None
    bio: str | None
    hourly_rate: float | None
    skills: list[str]
    archived_at: datetime | None
    rating_average: float | None
    rating_count: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AvailabilityPatternCreate(BaseModel):
    """Request schema for creating availability pattern"""

    day_of_week: int = Field(..., ge=0, le=6)
    is_available: bool


class AvailabilityPatternResponse(BaseModel):
    """Response schema for availability pattern"""

    id: UUID
    crew_id: UUID
    day_of_week: int
    is_available: bool

    model_config = ConfigDict(from_attributes=True)


class CrewRatingCreate(BaseModel):
    """Request schema for creating crew rating"""

    stars: int = Field(..., ge=1, le=5)
    notes: str | None = None


class CrewRatingResponse(BaseModel):
    """Response schema for crew rating"""

    id: UUID
    crew_id: UUID
    job_id: UUID
    rated_by: UUID
    stars: int
    notes: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SkillsMatrixEntry(BaseModel):
    """Single crew entry in skills matrix"""

    id: UUID
    email: str
    skills: dict[str, bool]


class SkillsMatrixResponse(BaseModel):
    """Skills matrix showing crew capabilities across skill tags"""

    skills: list[str]  # All unique skill tags in tenant
    crew: list[SkillsMatrixEntry]  # Crew members with skill boolean matrix
