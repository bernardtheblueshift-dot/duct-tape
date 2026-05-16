"""File model for job attachments with storage metadata"""

from sqlalchemy import Column, String, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.base import Base, TenantMixin, TimestampMixin
import uuid


class JobFile(Base, TenantMixin, TimestampMixin):
    """File attached to job messages"""

    __tablename__ = "job_files"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(
        UUID(as_uuid=True), ForeignKey("jobs.id"), nullable=False, index=True
    )
    uploader_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    original_filename = Column(String(255), nullable=False)
    storage_path = Column(String, nullable=False)  # Path on disk
    mime_type = Column(String(100), nullable=False)
    file_size = Column(Integer, nullable=False)  # Bytes

    # Relationship to messages via association table
    messages = relationship("Message", secondary="message_files", back_populates="files")
    # tenant_id from TenantMixin
    # created_at, updated_at from TimestampMixin
