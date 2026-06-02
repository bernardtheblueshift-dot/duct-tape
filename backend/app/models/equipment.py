"""Equipment inventory model with quantity, condition, and ownership tracking"""

from sqlalchemy import Column, String, Integer, Enum, Float, DateTime
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


class OwnershipType(str, enum.Enum):
    """Whether equipment is owned or rented"""

    OWNED = "owned"
    RENTED = "rented"


class Equipment(Base, TenantMixin, TimestampMixin):
    """Equipment inventory with pool tracking, condition, and rental management"""

    __tablename__ = "equipment"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    category = Column(String, nullable=True)
    quantity = Column(Integer, nullable=False, default=1)
    condition = Column(
        Enum(EquipmentCondition), nullable=False, default=EquipmentCondition.GOOD
    )
    notes = Column(String, nullable=True)
    serial_number = Column(String, nullable=True)
    # Ownership & rental tracking
    ownership = Column(
        Enum(OwnershipType), nullable=False, default=OwnershipType.OWNED
    )
    rental_vendor = Column(String, nullable=True)
    rental_cost_per_day = Column(Float, nullable=True)
    rental_start = Column(DateTime(timezone=True), nullable=True)
    rental_end = Column(DateTime(timezone=True), nullable=True)
    # tenant_id from TenantMixin
    # created_at, updated_at from TimestampMixin
