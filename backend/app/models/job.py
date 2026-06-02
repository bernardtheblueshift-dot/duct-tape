"""Job model with lifecycle state management"""

from sqlalchemy import Column, String, Enum
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import Base, TenantMixin, TimestampMixin
from sqlalchemy import DateTime
import uuid
import enum


class JobState(str, enum.Enum):
    """Job lifecycle states"""

    INTAKE = "intake"
    SIMMER = "simmer"
    ACTIVE = "active"
    COMPLETE = "complete"


class JobSource(str, enum.Enum):
    """How the job request was received"""

    DIRECT = "direct"
    EMAIL = "email"
    PHONE = "phone"
    REFERRAL = "referral"
    WEBSITE = "website"
    OTHER = "other"


class Job(Base, TenantMixin, TimestampMixin):
    """Job model with state machine and timezone-aware scheduling"""

    __tablename__ = "jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    venue = Column(String, nullable=True)
    scheduled_start = Column(DateTime(timezone=True), nullable=True)
    scheduled_end = Column(DateTime(timezone=True), nullable=True)
    state = Column(Enum(JobState), nullable=False, default=JobState.INTAKE)
    # Intake metadata
    source = Column(Enum(JobSource), nullable=True)
    contact_name = Column(String, nullable=True)
    contact_email = Column(String, nullable=True)
    contact_phone = Column(String, nullable=True)
    # tenant_id from TenantMixin
    # created_at, updated_at from TimestampMixin
