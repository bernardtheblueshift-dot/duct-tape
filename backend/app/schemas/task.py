"""Pydantic schemas for Task API requests and responses"""

from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from uuid import UUID
from app.models.task import TaskStatus, TaskPriority


class TaskCreate(BaseModel):
    """Request schema for creating a task"""

    title: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    assignee_id: UUID | None = None
    priority: TaskPriority = TaskPriority.MEDIUM
    deadline: datetime | None = None
    message_id: UUID | None = None  # Link to origin message


class TaskUpdate(BaseModel):
    """Request schema for updating a task (all fields optional for partial updates)"""

    title: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = None
    assignee_id: UUID | None = None
    priority: TaskPriority | None = None
    deadline: datetime | None = None
    # status excluded - use dedicated status transition endpoint


class TaskStatusUpdate(BaseModel):
    """Request schema for task status transitions"""

    status: TaskStatus


class TaskResponse(BaseModel):
    """Response schema with all task fields"""

    id: UUID
    job_id: UUID
    title: str
    description: str | None
    assignee_id: UUID | None
    status: TaskStatus
    priority: TaskPriority
    deadline: datetime | None
    message_id: UUID | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
