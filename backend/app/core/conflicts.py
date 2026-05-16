"""Conflict detection for crew assignments and equipment availability"""

from datetime import datetime
from uuid import UUID
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import (
    CrewAssignment,
    AssignmentState,
    Job,
    Equipment,
    EquipmentAssignment,
    AvailabilityPattern,
)


async def check_crew_conflicts(
    db: AsyncSession,
    crew_id: UUID,
    start: datetime,
    end: datetime,
    exclude_assignment_id: UUID | None = None,
) -> list:
    """
    Check for time conflicts in crew assignments.

    Args:
        db: Database session
        crew_id: Crew profile UUID
        start: Start time of proposed assignment
        end: End time of proposed assignment
        exclude_assignment_id: Optional assignment ID to exclude (for updates)

    Returns:
        List of conflicting CrewAssignment objects
    """
    # Build query for overlapping assignments
    query = (
        select(CrewAssignment)
        .join(Job, CrewAssignment.job_id == Job.id)
        .where(
            CrewAssignment.crew_id == crew_id,
            CrewAssignment.status == AssignmentState.CONFIRMED,
            Job.scheduled_start.is_not(None),
            Job.scheduled_end.is_not(None),
            Job.scheduled_start < end,
            Job.scheduled_end > start,
        )
    )

    # Exclude specific assignment if updating
    if exclude_assignment_id is not None:
        query = query.where(CrewAssignment.id != exclude_assignment_id)

    result = await db.execute(query)
    return list(result.scalars().all())


async def check_equipment_availability(
    db: AsyncSession,
    equipment_id: UUID,
    start: datetime,
    end: datetime,
    exclude_assignment_id: UUID | None = None,
) -> dict:
    """
    Check equipment pool availability during a time range.

    Args:
        db: Database session
        equipment_id: Equipment UUID
        start: Start time of proposed assignment
        end: End time of proposed assignment
        exclude_assignment_id: Optional assignment ID to exclude (for updates)

    Returns:
        Dict with total_quantity, assigned_quantity, available_quantity, and assignments list
    """
    # Get equipment record
    equipment_result = await db.execute(
        select(Equipment).where(Equipment.id == equipment_id)
    )
    equipment = equipment_result.scalar_one_or_none()

    if equipment is None:
        raise ValueError(f"Equipment {equipment_id} not found")

    # Build query for overlapping assignments
    query = (
        select(EquipmentAssignment)
        .join(Job, EquipmentAssignment.job_id == Job.id)
        .where(
            EquipmentAssignment.equipment_id == equipment_id,
            Job.scheduled_start.is_not(None),
            Job.scheduled_end.is_not(None),
            Job.scheduled_start < end,
            Job.scheduled_end > start,
        )
    )

    # Exclude specific assignment if updating
    if exclude_assignment_id is not None:
        query = query.where(EquipmentAssignment.id != exclude_assignment_id)

    result = await db.execute(query)
    overlapping_assignments = list(result.scalars().all())

    # Sum quantity assigned across all overlapping assignments
    assigned_quantity = sum(
        assignment.quantity_assigned for assignment in overlapping_assignments
    )

    return {
        "total_quantity": equipment.quantity,
        "assigned_quantity": assigned_quantity,
        "available_quantity": equipment.quantity - assigned_quantity,
        "assignments": overlapping_assignments,
    }


async def check_crew_availability_patterns(
    db: AsyncSession, crew_id: UUID, target_date: datetime
) -> bool:
    """
    Check if crew is available based on their recurring availability patterns.

    Args:
        db: Database session
        crew_id: Crew profile UUID
        target_date: Date to check availability for

    Returns:
        True if available (no blocking pattern), False if unavailable
    """
    day_of_week = target_date.weekday()

    # Query for blocking availability pattern
    query = select(AvailabilityPattern).where(
        AvailabilityPattern.crew_id == crew_id,
        AvailabilityPattern.day_of_week == day_of_week,
        AvailabilityPattern.is_available == False,
    )

    result = await db.execute(query)
    blocking_pattern = result.scalar_one_or_none()

    # If no blocking pattern exists, crew is available
    return blocking_pattern is None
