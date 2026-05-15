from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import Base, TimestampMixin
import uuid


class Tenant(Base, TimestampMixin):
    __tablename__ = "tenants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)  # Company/organization name
    timezone = Column(String, nullable=False, default="UTC")  # Default tenant timezone
