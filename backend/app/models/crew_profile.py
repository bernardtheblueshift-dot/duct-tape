"""Crew profile model with skills, rates, and reliability tracking"""

from sqlalchemy import Column, String, ForeignKey, Integer, Numeric, DateTime
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from app.models.base import Base, TenantMixin, TimestampMixin
import uuid


class CrewProfile(Base, TenantMixin, TimestampMixin):
    """Crew profile - one-to-one with User, holds production-specific data"""

    __tablename__ = "crew_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, unique=True
    )  # 1:1 with User
    phone = Column(String, nullable=True)
    bio = Column(String, nullable=True)
    hourly_rate = Column(Numeric(10, 2), nullable=True)  # Decimal for currency
    skills = Column(
        ARRAY(String), nullable=False, server_default="{}"
    )  # PostgreSQL TEXT[] for free-text tags
    archived_at = Column(
        DateTime(timezone=True), nullable=True
    )  # Soft delete timestamp
    rating_average = Column(
        Numeric(3, 2), nullable=True
    )  # Cached average, 0.00-5.00
    rating_count = Column(Integer, nullable=False, default=0)  # Cached count
    # tenant_id from TenantMixin
    # created_at, updated_at from TimestampMixin
