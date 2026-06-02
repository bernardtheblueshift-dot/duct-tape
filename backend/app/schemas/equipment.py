"""Pydantic schemas for equipment inventory operations"""

from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from uuid import UUID
from app.models.equipment import EquipmentCondition, OwnershipType


class EquipmentCreate(BaseModel):
    """Request schema for creating equipment"""

    name: str = Field(..., min_length=1, max_length=200)
    category: str | None = None
    quantity: int = Field(1, ge=1)
    condition: EquipmentCondition = EquipmentCondition.GOOD
    notes: str | None = None
    serial_number: str | None = None
    ownership: OwnershipType = OwnershipType.OWNED
    rental_vendor: str | None = None
    rental_cost_per_day: float | None = Field(None, ge=0)
    rental_start: datetime | None = None
    rental_end: datetime | None = None


class EquipmentUpdate(BaseModel):
    """Request schema for updating equipment (all fields optional)"""

    name: str | None = Field(None, min_length=1, max_length=200)
    category: str | None = None
    quantity: int | None = Field(None, ge=1)
    condition: EquipmentCondition | None = None
    notes: str | None = None
    serial_number: str | None = None
    ownership: OwnershipType | None = None
    rental_vendor: str | None = None
    rental_cost_per_day: float | None = Field(None, ge=0)
    rental_start: datetime | None = None
    rental_end: datetime | None = None


class EquipmentResponse(BaseModel):
    """Response schema with all equipment fields"""

    id: UUID
    name: str
    category: str | None
    quantity: int
    condition: EquipmentCondition
    notes: str | None
    serial_number: str | None
    ownership: OwnershipType
    rental_vendor: str | None
    rental_cost_per_day: float | None
    rental_start: datetime | None
    rental_end: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
