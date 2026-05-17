"""Track when users last viewed messages in each job thread"""

from sqlalchemy import Column, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import Base, TenantMixin
from datetime import datetime, timezone
import uuid


class MessageLastSeen(Base, TenantMixin):
    """Per-user per-job timestamp of when messages were last viewed"""

    __tablename__ = "message_last_seen"
    __table_args__ = (
        UniqueConstraint("user_id", "job_id", name="uq_user_job_last_seen"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id"), nullable=False, index=True)
    last_seen_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    # tenant_id from TenantMixin (no TimestampMixin needed -- last_seen_at serves as timestamp)
