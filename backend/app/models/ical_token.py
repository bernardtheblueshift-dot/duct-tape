"""ICalToken model for iCal feed authentication"""

from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import Base, TenantMixin, TimestampMixin
import uuid
import secrets


class ICalToken(Base, TenantMixin, TimestampMixin):
    """Long-lived token for iCal feed URL authentication"""

    __tablename__ = "ical_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    crew_id = Column(
        UUID(as_uuid=True), ForeignKey("crew_profiles.id"), nullable=False
    )
    token = Column(String, unique=True, nullable=False, index=True)
    expires_at = Column(
        DateTime(timezone=True), nullable=True
    )  # NULL = never expires
    last_accessed = Column(DateTime(timezone=True), nullable=True)
    # tenant_id from TenantMixin
    # created_at, updated_at from TimestampMixin

    @staticmethod
    def create_for_crew(crew_id: uuid.UUID, tenant_id: uuid.UUID) -> "ICalToken":
        """Create non-expiring iCal token for crew member"""
        return ICalToken(
            crew_id=crew_id,
            tenant_id=tenant_id,
            token=secrets.token_urlsafe(32),
            expires_at=None,  # No expiry by default, revocable
        )
