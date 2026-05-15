"""Job CRUD endpoints with admin-only write operations and RLS tenant isolation"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from datetime import datetime
from typing import List

from app.database import get_db
from app.dependencies import get_current_tenant
from app.core.permissions import require_admin
from app.models.job import Job, JobState
from app.schemas.job import JobCreate, JobUpdate, JobResponse, JobTransitionRequest
from app.models.user import User
from app.core.state_machine import can_transition

router = APIRouter(prefix="/api/v1/jobs", tags=["jobs"])


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
    RLS automatically filters by tenant.
    """
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
    jobs = result.scalars().all()
    return jobs


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: str,
    tenant_id: str = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """
    Get job by ID with placeholder sections for future features.

    Returns job with empty placeholder sections for:
    - assigned_crew (Phase 3)
    - assigned_gear (Phase 3)
    - messages (Phase 5)
    - tasks (Phase 5)
    - files (Phase 5)

    RLS automatically filters by tenant.
    """
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )

    return job


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
    return job


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
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
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

    # Update state
    job.state = transition.new_state
    await db.commit()
    await db.refresh(job)
    return job
