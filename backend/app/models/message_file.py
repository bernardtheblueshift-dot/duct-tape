"""Association table for many-to-many Message <-> JobFile relationship"""

from sqlalchemy import Table, Column, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import Base

message_files = Table(
    "message_files",
    Base.metadata,
    Column(
        "message_id",
        UUID(as_uuid=True),
        ForeignKey("messages.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "file_id",
        UUID(as_uuid=True),
        ForeignKey("job_files.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)
