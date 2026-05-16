"""Equipment CRUD endpoints with inventory search, condition tracking, and admin-only write operations"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from typing import List

from app.database import get_db
from app.dependencies import get_current_tenant
from app.core.permissions import require_admin
from app.models.equipment import Equipment, EquipmentCondition
from app.models.assignment import EquipmentAssignment
from app.schemas.equipment import EquipmentCreate, EquipmentUpdate, EquipmentResponse
from app.models.user import User
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/equipment", tags=["equipment"])


class ConditionUpdateRequest(BaseModel):
    """Request schema for updating equipment condition"""

    condition: EquipmentCondition


@router.post("/", response_model=EquipmentResponse, status_code=status.HTTP_201_CREATED)
async def create_equipment(
    equipment_data: EquipmentCreate,
    current_user: User = Depends(require_admin),
    tenant_id: str = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """
    Create new equipment item (admin only).

    Equipment is automatically associated with current tenant via RLS context.
    All fields except name are optional.
    Quantity defaults to 1, condition defaults to GOOD.
    """
    equipment = Equipment(
        **equipment_data.model_dump(),
        tenant_id=tenant_id,
    )
    db.add(equipment)
    await db.commit()
    await db.refresh(equipment)
    return equipment


@router.get("/", response_model=List[EquipmentResponse])
async def list_equipment(
    search: str | None = None,
    category: str | None = None,
    condition: EquipmentCondition | None = None,
    tenant_id: str = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """
    List equipment inventory with optional search and filtering.

    Query parameters:
    - search: Case-insensitive search across name and notes
    - category: Filter by category (case-insensitive partial match)
    - condition: Filter by condition (good/fair/poor/maintenance)

    Results ordered by name ascending.
    RLS automatically filters by tenant.
    """
    query = select(Equipment)

    # Apply search filter across name and notes
    if search:
        search_pattern = f"%{search}%"
        query = query.where(
            or_(
                Equipment.name.ilike(search_pattern),
                Equipment.notes.ilike(search_pattern),
            )
        )

    # Apply category filter
    if category:
        query = query.where(Equipment.category.ilike(f"%{category}%"))

    # Apply condition filter
    if condition:
        query = query.where(Equipment.condition == condition)

    # Order by name ascending
    query = query.order_by(Equipment.name.asc())

    result = await db.execute(query)
    equipment_items = result.scalars().all()
    return equipment_items


@router.get("/{equipment_id}", response_model=EquipmentResponse)
async def get_equipment(
    equipment_id: str,
    tenant_id: str = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """
    Get equipment item by ID.

    RLS automatically filters by tenant.
    """
    result = await db.execute(select(Equipment).where(Equipment.id == equipment_id))
    equipment = result.scalar_one_or_none()

    if not equipment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Equipment not found",
        )

    return equipment


@router.patch("/{equipment_id}", response_model=EquipmentResponse)
async def update_equipment(
    equipment_id: str,
    equipment_update: EquipmentUpdate,
    current_user: User = Depends(require_admin),
    tenant_id: str = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """
    Update equipment fields (admin only).

    Only updates fields provided in request (partial updates supported).
    RLS automatically filters by tenant.
    """
    result = await db.execute(select(Equipment).where(Equipment.id == equipment_id))
    equipment = result.scalar_one_or_none()

    if not equipment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Equipment not found",
        )

    # Update only provided fields
    update_data = equipment_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(equipment, key, value)

    await db.commit()
    await db.refresh(equipment)
    return equipment


@router.delete("/{equipment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_equipment(
    equipment_id: str,
    current_user: User = Depends(require_admin),
    tenant_id: str = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete equipment item (admin only).

    Deletion is blocked if equipment has active assignments to prevent orphaned data.
    Returns 409 Conflict if assignments exist.
    RLS automatically filters by tenant.
    """
    result = await db.execute(select(Equipment).where(Equipment.id == equipment_id))
    equipment = result.scalar_one_or_none()

    if not equipment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Equipment not found",
        )

    # Check for active assignments
    assignment_result = await db.execute(
        select(EquipmentAssignment).where(
            EquipmentAssignment.equipment_id == equipment_id
        )
    )
    assignments = assignment_result.scalars().all()

    if assignments:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot delete equipment with active assignments",
        )

    await db.delete(equipment)
    await db.commit()


@router.patch("/{equipment_id}/condition", response_model=EquipmentResponse)
async def update_equipment_condition(
    equipment_id: str,
    condition_update: ConditionUpdateRequest,
    current_user: User = Depends(require_admin),
    tenant_id: str = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """
    Update equipment condition/status (admin only).

    Separate endpoint for quick status updates (e.g., marking gear for maintenance).
    Allows updating condition without providing other fields.
    RLS automatically filters by tenant.
    """
    result = await db.execute(select(Equipment).where(Equipment.id == equipment_id))
    equipment = result.scalar_one_or_none()

    if not equipment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Equipment not found",
        )

    equipment.condition = condition_update.condition
    await db.commit()
    await db.refresh(equipment)
    return equipment
