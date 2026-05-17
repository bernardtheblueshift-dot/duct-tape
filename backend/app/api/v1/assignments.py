"""Assignment endpoints for crew and equipment with conflict detection"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from uuid import UUID

from app.database import get_db
from app.dependencies import get_current_tenant, get_current_user
from app.core.permissions import require_admin, require_active
from app.core.conflicts import (
    check_crew_conflicts,
    check_equipment_availability,
    check_crew_availability_patterns,
)
from app.models import (
    CrewAssignment,
    EquipmentAssignment,
    AssignmentState,
    ASSIGNMENT_TRANSITIONS,
    Job,
    CrewProfile,
    Equipment,
    User,
)
from app.schemas.assignment import (
    CrewAssignmentCreate,
    CrewAssignmentResponse,
    EquipmentAssignmentCreate,
    EquipmentAssignmentResponse,
    AssignmentTransitionRequest,
    ConflictWarning,
    ConflictDetail,
)
from app.tasks.email import send_assignment_email

router = APIRouter(prefix="/api/v1/assignments", tags=["assignments"])


@router.post("/crew", response_model=CrewAssignmentResponse, status_code=status.HTTP_201_CREATED)
async def assign_crew_to_job(
    assignment_data: CrewAssignmentCreate,
    current_user: User = Depends(require_admin),
    tenant_id: str = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """
    Assign crew to job (admin only).

    Validates job and crew exist, checks for conflicts, and creates assignment.
    If conflicts detected and force=False, returns 409 with conflict details.
    If force=True, proceeds with assignment and stores override_reason.
    """
    # Validate job exists
    job_result = await db.execute(
        select(Job).where(Job.id == assignment_data.job_id)
    )
    job = job_result.scalar_one_or_none()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )

    # Validate crew exists
    crew_result = await db.execute(
        select(CrewProfile).where(CrewProfile.id == assignment_data.crew_id)
    )
    crew = crew_result.scalar_one_or_none()

    if not crew:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Crew profile not found",
        )

    # Check if crew already assigned to this job
    existing_result = await db.execute(
        select(CrewAssignment).where(
            CrewAssignment.crew_id == assignment_data.crew_id,
            CrewAssignment.job_id == assignment_data.job_id,
        )
    )
    existing = existing_result.scalar_one_or_none()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Crew already assigned to this job",
        )

    # Check for conflicts if job has schedule
    if job.scheduled_start and job.scheduled_end:
        # Check time conflicts
        conflicts = await check_crew_conflicts(
            db, assignment_data.crew_id, job.scheduled_start, job.scheduled_end
        )

        # Check availability patterns
        is_available = await check_crew_availability_patterns(
            db, assignment_data.crew_id, job.scheduled_start
        )

        # Handle availability pattern block
        if not is_available and not assignment_data.force:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Crew is marked unavailable on this day",
            )

        # Handle time conflicts
        if conflicts and not assignment_data.force:
            # Build conflict details
            conflict_details = []
            for conflict_assignment in conflicts:
                # Get job details for each conflict
                conflict_job_result = await db.execute(
                    select(Job).where(Job.id == conflict_assignment.job_id)
                )
                conflict_job = conflict_job_result.scalar_one_or_none()

                if conflict_job:
                    conflict_details.append(
                        ConflictDetail(
                            job_id=conflict_job.id,
                            job_title=conflict_job.title,
                            scheduled_start=conflict_job.scheduled_start,
                            scheduled_end=conflict_job.scheduled_end,
                        )
                    )

            # Return 409 with structured conflict warning
            conflict_warning = ConflictWarning(
                message="Crew has scheduling conflicts",
                conflicts=conflict_details,
            )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=conflict_warning.model_dump(),
            )

    # Create assignment
    assignment = CrewAssignment(
        crew_id=assignment_data.crew_id,
        job_id=assignment_data.job_id,
        role=assignment_data.role,
        status=AssignmentState.PENDING,
        override_reason=assignment_data.override_reason if assignment_data.force else None,
        tenant_id=tenant_id,
    )

    db.add(assignment)
    await db.commit()
    await db.refresh(assignment)

    # Send email notification to assigned crew member
    crew_user_result = await db.execute(
        select(User).where(User.id == crew.user_id)
    )
    crew_user = crew_user_result.scalar_one_or_none()
    if crew_user:
        try:
            send_assignment_email.delay(
                email=crew_user.email,
                job_title=job.title,
                job_id=str(job.id),
                role=assignment.role,
                venue=job.venue,
                scheduled_start=str(job.scheduled_start) if job.scheduled_start else None,
                scheduled_end=str(job.scheduled_end) if job.scheduled_end else None,
            )
        except Exception:
            pass

    return assignment


@router.post("/equipment", response_model=EquipmentAssignmentResponse, status_code=status.HTTP_201_CREATED)
async def assign_equipment_to_job(
    assignment_data: EquipmentAssignmentCreate,
    current_user: User = Depends(require_admin),
    tenant_id: str = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """
    Assign equipment to job (admin only).

    Validates job and equipment exist, checks availability.
    Returns 409 if insufficient quantity available (hard block, no override).
    """
    # Validate job exists
    job_result = await db.execute(
        select(Job).where(Job.id == assignment_data.job_id)
    )
    job = job_result.scalar_one_or_none()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )

    # Validate equipment exists
    equipment_result = await db.execute(
        select(Equipment).where(Equipment.id == assignment_data.equipment_id)
    )
    equipment = equipment_result.scalar_one_or_none()

    if not equipment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Equipment not found",
        )

    # Check if equipment already assigned to this job
    existing_result = await db.execute(
        select(EquipmentAssignment).where(
            EquipmentAssignment.equipment_id == assignment_data.equipment_id,
            EquipmentAssignment.job_id == assignment_data.job_id,
        )
    )
    existing = existing_result.scalar_one_or_none()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Equipment already assigned to this job",
        )

    # Check availability if job has schedule
    if job.scheduled_start and job.scheduled_end:
        availability = await check_equipment_availability(
            db, assignment_data.equipment_id, job.scheduled_start, job.scheduled_end
        )

        # Hard block if insufficient quantity
        if availability["available_quantity"] < assignment_data.quantity_assigned:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "message": "Insufficient equipment available",
                    "total_quantity": availability["total_quantity"],
                    "assigned_quantity": availability["assigned_quantity"],
                    "available_quantity": availability["available_quantity"],
                    "requested": assignment_data.quantity_assigned,
                },
            )

    # Create assignment
    assignment = EquipmentAssignment(
        equipment_id=assignment_data.equipment_id,
        job_id=assignment_data.job_id,
        quantity_assigned=assignment_data.quantity_assigned,
        tenant_id=tenant_id,
    )

    db.add(assignment)
    await db.commit()
    await db.refresh(assignment)
    return assignment


@router.post("/crew/{assignment_id}/transition", response_model=CrewAssignmentResponse)
async def transition_crew_assignment(
    assignment_id: UUID,
    transition_data: AssignmentTransitionRequest,
    current_user: User = Depends(require_active),
    tenant_id: str = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """
    Transition crew assignment state (crew or admin).

    Crew can confirm/decline their own assignments.
    Admin can transition any assignment.
    Validates transition is allowed by state machine.
    """
    # Get assignment
    assignment_result = await db.execute(
        select(CrewAssignment).where(CrewAssignment.id == assignment_id)
    )
    assignment = assignment_result.scalar_one_or_none()

    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found",
        )

    # Check permission: crew can only transition their own assignments
    crew_result = await db.execute(
        select(CrewProfile).where(CrewProfile.id == assignment.crew_id)
    )
    crew = crew_result.scalar_one_or_none()

    # Allow if user is admin OR user is the assigned crew member
    from app.models.user import UserRole
    is_admin = current_user.role == UserRole.ADMIN
    is_assigned_crew = crew and crew.user_id == current_user.id

    if not (is_admin or is_assigned_crew):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot transition another crew member's assignment",
        )

    # Validate transition is allowed
    allowed_transitions = ASSIGNMENT_TRANSITIONS.get(assignment.status, [])
    if transition_data.new_status not in allowed_transitions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid transition: {assignment.status.value} -> {transition_data.new_status.value}",
        )

    # Update status
    assignment.status = transition_data.new_status

    # Store declined reason if provided
    if transition_data.new_status == AssignmentState.DECLINED:
        assignment.declined_reason = transition_data.declined_reason

    await db.commit()
    await db.refresh(assignment)
    return assignment


@router.get("/job/{job_id}/crew", response_model=List[CrewAssignmentResponse])
async def list_crew_assignments_for_job(
    job_id: UUID,
    current_user: User = Depends(require_active),
    tenant_id: str = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """
    List all crew assignments for a job (any authenticated user).

    Returns all crew assignments regardless of status.
    """
    # Validate job exists
    job_result = await db.execute(
        select(Job).where(Job.id == job_id)
    )
    job = job_result.scalar_one_or_none()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )

    # Query assignments
    result = await db.execute(
        select(CrewAssignment).where(CrewAssignment.job_id == job_id)
    )
    assignments = result.scalars().all()
    return list(assignments)


@router.get("/job/{job_id}/equipment", response_model=List[EquipmentAssignmentResponse])
async def list_equipment_assignments_for_job(
    job_id: UUID,
    current_user: User = Depends(require_active),
    tenant_id: str = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """
    List all equipment assignments for a job (any authenticated user).
    """
    # Validate job exists
    job_result = await db.execute(
        select(Job).where(Job.id == job_id)
    )
    job = job_result.scalar_one_or_none()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )

    # Query assignments
    result = await db.execute(
        select(EquipmentAssignment).where(EquipmentAssignment.job_id == job_id)
    )
    assignments = result.scalars().all()
    return list(assignments)


@router.delete("/crew/{assignment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_crew_assignment(
    assignment_id: UUID,
    current_user: User = Depends(require_admin),
    tenant_id: str = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete crew assignment (admin only).
    """
    assignment_result = await db.execute(
        select(CrewAssignment).where(CrewAssignment.id == assignment_id)
    )
    assignment = assignment_result.scalar_one_or_none()

    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found",
        )

    await db.delete(assignment)
    await db.commit()


@router.delete("/equipment/{assignment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_equipment_assignment(
    assignment_id: UUID,
    current_user: User = Depends(require_admin),
    tenant_id: str = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete equipment assignment (admin only).
    """
    assignment_result = await db.execute(
        select(EquipmentAssignment).where(EquipmentAssignment.id == assignment_id)
    )
    assignment = assignment_result.scalar_one_or_none()

    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found",
        )

    await db.delete(assignment)
    await db.commit()
