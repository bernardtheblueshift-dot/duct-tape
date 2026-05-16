"""Message model for job communication with file attachments"""

from sqlalchemy import Column, String, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.base import Base, TenantMixin, TimestampMixin
import uuid


class Message(Base, TenantMixin, TimestampMixin):
    """Message in job conversation thread"""

    __tablename__ = "messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(
        UUID(as_uuid=True), ForeignKey("jobs.id"), nullable=False, index=True
    )
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)  # Markdown content
    reply_to_id = Column(
        UUID(as_uuid=True), ForeignKey("messages.id"), nullable=True
    )  # Thread reply support

    # Relationship to files via association table
    files = relationship("JobFile", secondary="message_files", back_populates="messages")
    # tenant_id from TenantMixin
    # created_at, updated_at from TimestampMixin
