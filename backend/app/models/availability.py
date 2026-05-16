"""Availability pattern model for crew recurring schedule"""

from sqlalchemy import Column, ForeignKey, Integer, Boolean, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import Base, TenantMixin, TimestampMixin
import uuid


class AvailabilityPattern(Base, TenantMixin, TimestampMixin):
    """Crew recurring availability by day of week"""

    __tablename__ = "availability_patterns"
    __table_args__ = (UniqueConstraint("crew_id", "day_of_week", name="uq_crew_day"),)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    crew_id = Column(
        UUID(as_uuid=True), ForeignKey("crew_profiles.id"), nullable=False
    )
    day_of_week = Column(
        Integer, nullable=False
    )  # 0=Monday, 6=Sunday (Python convention)
    is_available = Column(Boolean, nullable=False, default=True)
    # tenant_id from TenantMixin
    # created_at, updated_at from TimestampMixin
