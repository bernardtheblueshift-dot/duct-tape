from sqlalchemy import Column, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase
from datetime import datetime, timezone
import uuid


class Base(DeclarativeBase):
    """Base class for all database models"""

    pass


class TenantMixin:
    """Add to all tenant-scoped models to enable RLS filtering"""

    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)


class TimestampMixin:
    """Add created_at and updated_at timestamps to models"""

    created_at = Column(
        DateTime(timezone=True),  # Uses TIMESTAMPTZ in PostgreSQL
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
