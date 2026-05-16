"""Crew rating model for post-job reliability tracking"""

from sqlalchemy import Column, String, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import Base, TenantMixin, TimestampMixin
import uuid


class CrewRating(Base, TenantMixin, TimestampMixin):
    """Crew rating per job - one rating per crew per job"""

    __tablename__ = "crew_ratings"
    __table_args__ = (
        UniqueConstraint("crew_id", "job_id", name="uq_crew_job_rating"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    crew_id = Column(
        UUID(as_uuid=True), ForeignKey("crew_profiles.id"), nullable=False
    )
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id"), nullable=False)
    rated_by = Column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )  # Admin who rated
    stars = Column(Integer, nullable=False)  # 1-5, validated at schema level
    notes = Column(String, nullable=True)
    # tenant_id from TenantMixin
    # created_at, updated_at from TimestampMixin
