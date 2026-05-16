"""Equipment inventory model with quantity and condition tracking"""

from sqlalchemy import Column, String, Integer, Enum
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import Base, TenantMixin, TimestampMixin
import uuid
import enum


class EquipmentCondition(str, enum.Enum):
    """Equipment condition states"""

    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    MAINTENANCE = "maintenance"


class Equipment(Base, TenantMixin, TimestampMixin):
    """Equipment inventory with pool tracking and condition management"""

    __tablename__ = "equipment"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    category = Column(String, nullable=True)  # Free-text, tenant-scoped
    quantity = Column(Integer, nullable=False, default=1)  # Pool tracking
    condition = Column(
        Enum(EquipmentCondition), nullable=False, default=EquipmentCondition.GOOD
    )
    notes = Column(String, nullable=True)
    serial_number = Column(String, nullable=True)  # Optional per-unit tracking
    # tenant_id from TenantMixin
    # created_at, updated_at from TimestampMixin
