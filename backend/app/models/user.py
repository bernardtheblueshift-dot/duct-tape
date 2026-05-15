from sqlalchemy import Column, String, Boolean, Enum
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import Base, TenantMixin, TimestampMixin
import uuid
import enum


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    CREW = "crew"


class User(Base, TenantMixin, TimestampMixin):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, nullable=False, unique=True, index=True)
    hashed_password = Column(String, nullable=False)
    is_active = Column(
        Boolean, default=False, nullable=False
    )  # False until email verified
    role = Column(Enum(UserRole), nullable=False, default=UserRole.CREW)
    timezone = Column(
        String, nullable=False, default="UTC"
    )  # User's preferred timezone
    # tenant_id from TenantMixin
    # created_at, updated_at from TimestampMixin
