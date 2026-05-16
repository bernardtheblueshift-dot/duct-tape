"""Task model with status and priority tracking"""

from sqlalchemy import Column, String, ForeignKey, Enum, DateTime
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import Base, TenantMixin, TimestampMixin
import uuid
import enum


class TaskStatus(str, enum.Enum):
    """Task lifecycle states"""

    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"


class TaskPriority(str, enum.Enum):
    """Task priority levels"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class Task(Base, TenantMixin, TimestampMixin):
    """Task for job coordination and tracking"""

    __tablename__ = "tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(
        UUID(as_uuid=True), ForeignKey("jobs.id"), nullable=False, index=True
    )
    title = Column(String(200), nullable=False)
    description = Column(String, nullable=True)
    assignee_id = Column(
        UUID(as_uuid=True), ForeignKey("crew_profiles.id"), nullable=True
    )
    status = Column(Enum(TaskStatus), nullable=False, default=TaskStatus.TODO)
    priority = Column(Enum(TaskPriority), nullable=False, default=TaskPriority.MEDIUM)
    deadline = Column(DateTime(timezone=True), nullable=True)
    message_id = Column(
        UUID(as_uuid=True), ForeignKey("messages.id"), nullable=True
    )  # Link to origin message
    # tenant_id from TenantMixin
    # created_at, updated_at from TimestampMixin
