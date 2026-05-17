"""Job CRUD endpoints with admin-only write operations and RLS tenant isolation"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, func
from datetime import datetime, timezone
from typing import List
from uuid import UUID

from app.database import get_db
from app.dependencies import get_current_tenant
from app.core.permissions import require_admin
from app.models.job import Job, JobState
from app.schemas.job import JobCreate, JobUpdate, JobResponse, JobTransitionRequest, CoordinationSummary, MessageSummary, FileSummary
from app.models.user import User
from app.core.state_machine import can_transition
from app.models import Message, Task, TaskStatus, JobFile
from app.tasks.email import send_job_update_email

router = APIRouter(prefix="/api/v1/jobs", tags=["jobs"])


async def build_coordination_summary(
    job_id: UUID, db: AsyncSession
) -> CoordinationSummary:
    """Build full coordination summary for a single job (detail view)"""

    # Message count
    message_count_result = await db.execute(
        select(func.count(Message.id)).where(Message.job_id == job_id)
    )
    message_count = message_count_result.scalar() or 0

    # Recent 3 messages
    recent_messages_result = await db.execute(
        select(Message)
        .where(Message.job_id == job_id)
        .order_by(Message.created_at.desc())
        .limit(3)
    )
    recent_messages = [
        MessageSummary(
            id=msg.id,
            user_id=msg.user_id,
            content=msg.content,
            created_at=msg.created_at,
        )
        for msg in recent_messages_result.scalars().all()
    ]

    # Task counts by status
    task_counts_result = await db.execute(
        select(Task.status, func.count(Task.id))
        .where(Task.job_id == job_id)
        .group_by(Task.status)
    )
    task_counts = {status: count for status, count in task_counts_result.all()}

    # Overdue count (deadline < now AND status != DONE)
    overdue_count_result = await db.execute(
        select(func.count(Task.id)).where(
            Task.job_id == job_id,
            Task.deadline < datetime.now(timezone.utc),
            Task.status != TaskStatus.DONE,
        )
    )
    overdue_count = overdue_count_result.scalar() or 0

    # File count
    file_count_result = await db.execute(
        select(func.count(JobFile.id)).where(JobFile.job_id == job_id)
    )
    file_count = file_count_result.scalar() or 0

    # Recent 3 files
    recent_files_result = await db.execute(
        select(JobFile)
        .where(JobFile.job_id == job_id)
        .order_by(JobFile.created_at.desc())
        .limit(3)
    )
    recent_files = [
        FileSummary(
            id=file.id,
            original_filename=file.original_filename,
            mime_type=file.mime_type,
            file_size=file.file_size,
            created_at=file.created_at,
        )
        for file in recent_files_result.scalars().all()
    ]

    return CoordinationSummary(
        message_count=message_count,
        recent_messages=recent_messages,
        task_total=sum(task_counts.values()),
        task_todo=task_counts.get(TaskStatus.TODO, 0),
        task_in_progress=task_counts.get(TaskStatus.IN_PROGRESS, 0),
        task_done=task_counts.get(TaskStatus.DONE, 0),
        task_overdue=overdue_count,
        file_count=file_count,
        recent_files=recent_files,
    )


async def batch_coordination_summaries(
    job_ids: list[UUID], db: AsyncSession
) -> dict[UUID, CoordinationSummary]:
    """Batch query coordination summaries for list view (counts only, no recent items)"""

    if not job_ids:
        return {}

    # Message counts per job
    message_counts_result = await db.execute(
        select(Message.job_id, func.count(Message.id))
        .where(Message.job_id.in_(job_ids))
        .group_by(Message.job_id)
    )
    message_counts = {job_id: count for job_id, count in message_counts_result.all()}

    # Task counts per job per status
    task_counts_result = await db.execute(
        select(Task.job_id, Task.status, func.count(Task.id))
        .where(Task.job_id.in_(job_ids))
        .group_by(Task.job_id, Task.status)
    )
    task_counts_by_job = {}
    for job_id, status, count in task_counts_result.all():
        if job_id not in task_counts_by_job:
            task_counts_by_job[job_id] = {}
        task_counts_by_job[job_id][status] = count

    # Overdue counts per job
    overdue_counts_result = await db.execute(
        select(Task.job_id, func.count(Task.id))
        .where(
            Task.job_id.in_(job_ids),
            Task.deadline < datetime.now(timezone.utc),
            Task.status != TaskStatus.DONE,
        )
        .group_by(Task.job_id)
    )
    overdue_counts = {job_id: count for job_id, count in overdue_counts_result.all()}

    # File counts per job
    file_counts_result = await db.execute(
        select(JobFile.job_id, func.count(JobFile.id))
        .where(JobFile.job_id.in_(job_ids))
        .group_by(JobFile.job_id)
    )
    file_counts = {job_id: count for job_id, count in file_counts_result.all()}

    # Build summaries for each job
    summaries = {}
    for job_id in job_ids:
        task_counts = task_counts_by_job.get(job_id, {})
        summaries[job_id] = CoordinationSummary(
            message_count=message_counts.get(job_id, 0),
            recent_messages=[],  # Skip recent items in list view for performance
            task_total=sum(task_counts.values()),
            task_todo=task_counts.get(TaskStatus.TODO, 0),
            task_in_progress=task_counts.get(TaskStatus.IN_PROGRESS, 0),
            task_done=task_counts.get(TaskStatus.DONE, 0),
            task_overdue=overdue_counts.get(job_id, 0),
            file_count=file_counts.get(job_id, 0),
            recent_files=[],  # Skip recent items in list view for performance
        )

    return summaries


@router.post("/", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def create_job(
    job_data: JobCreate,
    current_user: User = Depends(require_admin),
    tenant_id: str = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """
    Create new job (admin only).

    Job is automatically associated with current tenant via RLS context.
    State defaults to INTAKE.
    """
    job = Job(
        **job_data.model_dump(),
        tenant_id=tenant_id,
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)
    return job


@router.get("/", response_model=List[JobResponse])
async def list_jobs(
    search: str | None = None,
    state: JobState | None = None,
    venue: str | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    tenant_id: str = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """
    List jobs with optional search and filtering.

    Query parameters:
    - search: Case-insensitive search across title, description, venue
    - state: Filter by job state (intake/simmer/active/complete)
    - venue: Filter by venue (case-insensitive partial match)
    - start_date: Jobs scheduled on or after this date
    - end_date: Jobs scheduled on or before this date

    Results ordered by scheduled_start descending (most recent first).
    Populates assigned_crew and assigned_gear for each job.
    RLS automatically filters by tenant.
    """
    from app.models import CrewAssignment, EquipmentAssignment
    from app.schemas.job import CrewAssignmentSummary, EquipmentAssignmentSummary

    query = select(Job)

    # Apply search filter across multiple fields
    if search:
        search_pattern = f"%{search}%"
        query = query.where(
            or_(
                Job.title.ilike(search_pattern),
                Job.description.ilike(search_pattern),
                Job.venue.ilike(search_pattern),
            )
        )

    # Apply state filter
    if state:
        query = query.where(Job.state == state)

    # Apply venue filter
    if venue:
        query = query.where(Job.venue.ilike(f"%{venue}%"))

    # Apply date range filters
    if start_date:
        query = query.where(Job.scheduled_start >= start_date)

    if end_date:
        query = query.where(Job.scheduled_start <= end_date)

    # Order by scheduled_start descending (most recent first)
    query = query.order_by(Job.scheduled_start.desc())

    result = await db.execute(query)
    jobs = list(result.scalars().all())

    # Batch query assignments for all jobs
    if jobs:
        job_ids = [job.id for job in jobs]

        # Query all crew assignments
        crew_result = await db.execute(
            select(CrewAssignment).where(CrewAssignment.job_id.in_(job_ids))
        )
        all_crew_assignments = crew_result.scalars().all()

        # Query all equipment assignments
        equipment_result = await db.execute(
            select(EquipmentAssignment).where(EquipmentAssignment.job_id.in_(job_ids))
        )
        all_equipment_assignments = equipment_result.scalars().all()

        # Group assignments by job_id
        crew_by_job = {}
        for ca in all_crew_assignments:
            if ca.job_id not in crew_by_job:
                crew_by_job[ca.job_id] = []
            crew_by_job[ca.job_id].append(
                CrewAssignmentSummary(
                    id=ca.id,
                    crew_id=ca.crew_id,
                    role=ca.role,
                    status=ca.status.value,
                )
            )

        equipment_by_job = {}
        for ea in all_equipment_assignments:
            if ea.job_id not in equipment_by_job:
                equipment_by_job[ea.job_id] = []
            equipment_by_job[ea.job_id].append(
                EquipmentAssignmentSummary(
                    id=ea.id,
                    equipment_id=ea.equipment_id,
                    quantity_assigned=ea.quantity_assigned,
                )
            )

        # Batch query coordination summaries
        summaries = await batch_coordination_summaries(job_ids, db)

        # Build response with assignment data
        return [
            {
                "id": job.id,
                "title": job.title,
                "description": job.description,
                "venue": job.venue,
                "scheduled_start": job.scheduled_start,
                "scheduled_end": job.scheduled_end,
                "state": job.state,
                "created_at": job.created_at,
                "updated_at": job.updated_at,
                "assigned_crew": crew_by_job.get(job.id, []),
                "assigned_gear": equipment_by_job.get(job.id, []),
                "coordination": summaries.get(job.id, CoordinationSummary()),
            }
            for job in jobs
        ]

    return []


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: str,
    tenant_id: str = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """
    Get job by ID with populated assignments and placeholder sections.

    Returns job with:
    - assigned_crew (Phase 3) - populated from CrewAssignment
    - assigned_gear (Phase 3) - populated from EquipmentAssignment
    - messages (Phase 5) - placeholder
    - tasks (Phase 5) - placeholder
    - files (Phase 5) - placeholder

    RLS automatically filters by tenant.
    """
    from app.models import CrewAssignment, EquipmentAssignment
    from app.schemas.job import CrewAssignmentSummary, EquipmentAssignmentSummary

    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )

    # Query crew assignments
    crew_result = await db.execute(
        select(CrewAssignment).where(CrewAssignment.job_id == job_id)
    )
    crew_assignments = [
        CrewAssignmentSummary(
            id=ca.id,
            crew_id=ca.crew_id,
            role=ca.role,
            status=ca.status.value,
        )
        for ca in crew_result.scalars().all()
    ]

    # Query equipment assignments
    equipment_result = await db.execute(
        select(EquipmentAssignment).where(EquipmentAssignment.job_id == job_id)
    )
    equipment_assignments = [
        EquipmentAssignmentSummary(
            id=ea.id,
            equipment_id=ea.equipment_id,
            quantity_assigned=ea.quantity_assigned,
        )
        for ea in equipment_result.scalars().all()
    ]

    # Get coordination summary
    coordination = await build_coordination_summary(job.id, db)

    # Build response manually with assignment data
    return {
        "id": job.id,
        "title": job.title,
        "description": job.description,
        "venue": job.venue,
        "scheduled_start": job.scheduled_start,
        "scheduled_end": job.scheduled_end,
        "state": job.state,
        "created_at": job.created_at,
        "updated_at": job.updated_at,
        "assigned_crew": crew_assignments,
        "assigned_gear": equipment_assignments,
        "coordination": coordination,
    }


@router.patch("/{job_id}", response_model=JobResponse)
async def update_job(
    job_id: str,
    job_update: JobUpdate,
    current_user: User = Depends(require_admin),
    tenant_id: str = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """
    Update job fields (admin only).

    Excludes state field - state transitions happen via separate endpoint.
    Only updates fields provided in request (partial updates supported).
    RLS automatically filters by tenant.
    """
    from app.models import CrewAssignment, EquipmentAssignment
    from app.schemas.job import CrewAssignmentSummary, EquipmentAssignmentSummary

    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )

    # Update only provided fields, exclude state field
    update_data = job_update.model_dump(exclude_unset=True, exclude={"state"})
    for key, value in update_data.items():
        setattr(job, key, value)

    await db.commit()
    await db.refresh(job)

    # Query crew assignments
    crew_result = await db.execute(
        select(CrewAssignment).where(CrewAssignment.job_id == job_id)
    )
    crew_assignments = [
        CrewAssignmentSummary(
            id=ca.id,
            crew_id=ca.crew_id,
            role=ca.role,
            status=ca.status.value,
        )
        for ca in crew_result.scalars().all()
    ]

    # Query equipment assignments
    equipment_result = await db.execute(
        select(EquipmentAssignment).where(EquipmentAssignment.job_id == job_id)
    )
    equipment_assignments = [
        EquipmentAssignmentSummary(
            id=ea.id,
            equipment_id=ea.equipment_id,
            quantity_assigned=ea.quantity_assigned,
        )
        for ea in equipment_result.scalars().all()
    ]

    # Get coordination summary
    coordination = await build_coordination_summary(job.id, db)

    # Build response with assignment and coordination data
    return {
        "id": job.id,
        "title": job.title,
        "description": job.description,
        "venue": job.venue,
        "scheduled_start": job.scheduled_start,
        "scheduled_end": job.scheduled_end,
        "state": job.state,
        "created_at": job.created_at,
        "updated_at": job.updated_at,
        "assigned_crew": crew_assignments,
        "assigned_gear": equipment_assignments,
        "coordination": coordination,
    }


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_job(
    job_id: str,
    current_user: User = Depends(require_admin),
    tenant_id: str = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete job (admin only).

    Hard delete - job is permanently removed from database.
    RLS automatically filters by tenant.
    """
    from app.models import CrewAssignment, AssignmentState, CrewProfile

    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )

    # Email all assigned crew about cancellation BEFORE deleting
    assigned_crew_result = await db.execute(
        select(CrewAssignment).where(
            CrewAssignment.job_id == job_id,
            CrewAssignment.status == AssignmentState.CONFIRMED,
        )
    )
    assigned_crew = assigned_crew_result.scalars().all()
    for ca in assigned_crew:
        crew_user_result = await db.execute(
            select(User).join(CrewProfile, CrewProfile.user_id == User.id).where(
                CrewProfile.id == ca.crew_id
            )
        )
        crew_user = crew_user_result.scalar_one_or_none()
        if crew_user:
            try:
                send_job_update_email.delay(
                    email=crew_user.email,
                    job_title=job.title,
                    job_id=str(job.id),
            except Exception:
                pass
                event_type="cancelled",
            )

    await db.delete(job)
    await db.commit()


@router.post("/{job_id}/transition", response_model=JobResponse)
async def transition_job_state(
    job_id: str,
    transition: JobTransitionRequest,
    current_user: User = Depends(require_admin),
    tenant_id: str = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """
    Transition job to new state with validation (admin only).

    Validates that transition is allowed before updating state.
    State machine enforces:
    - INTAKE → [SIMMER, ACTIVE]
    - SIMMER → [ACTIVE, INTAKE] (can return to intake)
    - ACTIVE → [COMPLETE, SIMMER] (can pause to simmer)
    - COMPLETE → [] (terminal state)

    Returns 400 if transition is invalid.
    RLS automatically filters by tenant.
    """
    from app.models import CrewAssignment, EquipmentAssignment, AssignmentState, CrewProfile
    from app.schemas.job import CrewAssignmentSummary, EquipmentAssignmentSummary

    # Get job
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )

    # Validate transition
    if not can_transition(job.state, transition.new_state):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid transition: {job.state.value} -> {transition.new_state.value}",
        )

    # Capture old state before transition
    old_state = job.state

    # Update state
    job.state = transition.new_state
    await db.commit()
    await db.refresh(job)

    # Email all assigned crew about state change
    assigned_crew_result = await db.execute(
        select(CrewAssignment).where(
            CrewAssignment.job_id == job_id,
            CrewAssignment.status == AssignmentState.CONFIRMED,
        )
    )
    assigned_crew = assigned_crew_result.scalars().all()
    for ca in assigned_crew:
        crew_user_result = await db.execute(
            select(User).join(CrewProfile, CrewProfile.user_id == User.id).where(
                CrewProfile.id == ca.crew_id
            )
        )
        crew_user = crew_user_result.scalar_one_or_none()
        if crew_user:
            try:
                send_job_update_email.delay(
                    email=crew_user.email,
                    job_title=job.title,
                    job_id=str(job.id),
            except Exception:
                pass
                event_type="state_change",
                old_state=old_state.value,
                new_state=transition.new_state.value,
            )

    # Query crew assignments
    crew_result = await db.execute(
        select(CrewAssignment).where(CrewAssignment.job_id == job_id)
    )
    crew_assignments = [
        CrewAssignmentSummary(
            id=ca.id,
            crew_id=ca.crew_id,
            role=ca.role,
            status=ca.status.value,
        )
        for ca in crew_result.scalars().all()
    ]

    # Query equipment assignments
    equipment_result = await db.execute(
        select(EquipmentAssignment).where(EquipmentAssignment.job_id == job_id)
    )
    equipment_assignments = [
        EquipmentAssignmentSummary(
            id=ea.id,
            equipment_id=ea.equipment_id,
            quantity_assigned=ea.quantity_assigned,
        )
        for ea in equipment_result.scalars().all()
    ]

    # Get coordination summary
    coordination = await build_coordination_summary(job.id, db)

    # Build response with assignment and coordination data
    return {
        "id": job.id,
        "title": job.title,
        "description": job.description,
        "venue": job.venue,
        "scheduled_start": job.scheduled_start,
        "scheduled_end": job.scheduled_end,
        "state": job.state,
        "created_at": job.created_at,
        "updated_at": job.updated_at,
        "assigned_crew": crew_assignments,
        "assigned_gear": equipment_assignments,
        "coordination": coordination,
    }
