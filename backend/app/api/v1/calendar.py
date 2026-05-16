"""Calendar API endpoints for jobs and resource bookings"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone
from uuid import UUID

from app.database import get_db
from app.dependencies import get_current_tenant
from app.core.permissions import require_active
from app.models import (
    Job,
    JobState,
    CrewAssignment,
    EquipmentAssignment,
    CrewProfile,
    Equipment,
    User,
)
from app.schemas.calendar import (
    CalendarEvent,
    CalendarEventsResponse,
    JOB_STATE_COLORS,
)

router = APIRouter(prefix="/api/v1/calendar", tags=["calendar"])


@router.get("/events", response_model=CalendarEventsResponse)
async def get_calendar_events(
    start: datetime,
    end: datetime,
    current_user: User = Depends(require_active),
    tenant_id: str = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """
    Get all calendar events (jobs and assignments) within date range.

    Query parameters:
    - start: Start of date range (required)
    - end: End of date range (required)

    Returns unified CalendarEvent list for jobs, crew assignments, and equipment assignments.
    Jobs without scheduled times are excluded.
    Date ranges exceeding 365 days return 400 error.
    RLS automatically filters by tenant.
    """
    # Ensure timezone-aware datetimes
    if start.tzinfo is None:
        start = start.replace(tzinfo=timezone.utc)
    if end.tzinfo is None:
        end = end.replace(tzinfo=timezone.utc)

    # Validate max date range
    if (end - start).days > 365:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Date range too large (max 365 days)",
        )

    # Step 1: Query jobs in range
    jobs_result = await db.execute(
        select(Job).where(
            Job.scheduled_start.is_not(None),
            Job.scheduled_end.is_not(None),
            Job.scheduled_start < end,
            Job.scheduled_end > start,
        )
    )
    jobs = list(jobs_result.scalars().all())
    job_ids = [j.id for j in jobs]

    events = []

    # Add job events
    for job in jobs:
        events.append(
            CalendarEvent(
                id=job.id,
                event_type="job",
                title=job.title,
                start=job.scheduled_start,
                end=job.scheduled_end,
                color=JOB_STATE_COLORS[job.state.value],
                status=job.state.value,
            )
        )

    # If no jobs, return early
    if not job_ids:
        return CalendarEventsResponse(events=events, count=len(events))

    # Step 2: Batch fetch crew assignments + crew names
    crew_result = await db.execute(
        select(CrewAssignment, User.email, Job.title, Job.state, Job.scheduled_start, Job.scheduled_end)
        .join(CrewProfile, CrewAssignment.crew_id == CrewProfile.id)
        .join(User, CrewProfile.user_id == User.id)
        .join(Job, CrewAssignment.job_id == Job.id)
        .where(CrewAssignment.job_id.in_(job_ids))
    )

    for ca, email, job_title, job_state, job_start, job_end in crew_result.all():
        events.append(
            CalendarEvent(
                id=ca.id,
                event_type="crew_assignment",
                title=f"{ca.role} - {job_title}" if ca.role else job_title,
                start=job_start,
                end=job_end,
                color=JOB_STATE_COLORS[job_state.value],
                status=ca.status.value,
                job_id=ca.job_id,
                resource_id=ca.crew_id,
                resource_name=email,
                job_title=job_title,
                role=ca.role,
            )
        )

    # Step 3: Batch fetch equipment assignments + equipment names
    equip_result = await db.execute(
        select(EquipmentAssignment, Equipment.name, Job.title, Job.state, Job.scheduled_start, Job.scheduled_end)
        .join(Equipment, EquipmentAssignment.equipment_id == Equipment.id)
        .join(Job, EquipmentAssignment.job_id == Job.id)
        .where(EquipmentAssignment.job_id.in_(job_ids))
    )

    for ea, equipment_name, job_title, job_state, job_start, job_end in equip_result.all():
        events.append(
            CalendarEvent(
                id=ea.id,
                event_type="equipment_assignment",
                title=f"{equipment_name} - {job_title}",
                start=job_start,
                end=job_end,
                color=JOB_STATE_COLORS[job_state.value],
                status="assigned",  # Equipment assignments don't have status enum
                job_id=ea.job_id,
                resource_id=ea.equipment_id,
                resource_name=equipment_name,
                job_title=job_title,
            )
        )

    return CalendarEventsResponse(events=events, count=len(events))


@router.get("/crew/{crew_id}", response_model=CalendarEventsResponse)
async def get_crew_calendar(
    crew_id: UUID,
    start: datetime,
    end: datetime,
    current_user: User = Depends(require_active),
    tenant_id: str = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """
    Get calendar events for specific crew member.

    Path parameters:
    - crew_id: UUID of crew member

    Query parameters:
    - start: Start of date range (required)
    - end: End of date range (required)

    Returns CalendarEvent list containing:
    - Job events for jobs this crew is assigned to
    - Crew assignment events for this crew member

    Date ranges exceeding 365 days return 400 error.
    RLS automatically filters by tenant.
    """
    # Ensure timezone-aware datetimes
    if start.tzinfo is None:
        start = start.replace(tzinfo=timezone.utc)
    if end.tzinfo is None:
        end = end.replace(tzinfo=timezone.utc)

    # Validate max date range
    if (end - start).days > 365:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Date range too large (max 365 days)",
        )

    # Query crew assignments for this crew member in range
    crew_result = await db.execute(
        select(CrewAssignment, User.email, Job.title, Job.state, Job.scheduled_start, Job.scheduled_end, Job.id)
        .join(CrewProfile, CrewAssignment.crew_id == CrewProfile.id)
        .join(User, CrewProfile.user_id == User.id)
        .join(Job, CrewAssignment.job_id == Job.id)
        .where(
            CrewAssignment.crew_id == crew_id,
            Job.scheduled_start.is_not(None),
            Job.scheduled_end.is_not(None),
            Job.scheduled_start < end,
            Job.scheduled_end > start,
        )
    )

    events = []
    job_ids_seen = set()

    for ca, email, job_title, job_state, job_start, job_end, job_id in crew_result.all():
        # Add crew assignment event
        events.append(
            CalendarEvent(
                id=ca.id,
                event_type="crew_assignment",
                title=f"{ca.role} - {job_title}" if ca.role else job_title,
                start=job_start,
                end=job_end,
                color=JOB_STATE_COLORS[job_state.value],
                status=ca.status.value,
                job_id=ca.job_id,
                resource_id=ca.crew_id,
                resource_name=email,
                job_title=job_title,
                role=ca.role,
            )
        )

        # Add parent job event (once per job)
        if job_id not in job_ids_seen:
            job_ids_seen.add(job_id)
            events.append(
                CalendarEvent(
                    id=job_id,
                    event_type="job",
                    title=job_title,
                    start=job_start,
                    end=job_end,
                    color=JOB_STATE_COLORS[job_state.value],
                    status=job_state.value,
                )
            )

    return CalendarEventsResponse(events=events, count=len(events))


@router.get("/equipment/{equipment_id}", response_model=CalendarEventsResponse)
async def get_equipment_calendar(
    equipment_id: UUID,
    start: datetime,
    end: datetime,
    current_user: User = Depends(require_active),
    tenant_id: str = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """
    Get calendar events for specific equipment item.

    Path parameters:
    - equipment_id: UUID of equipment

    Query parameters:
    - start: Start of date range (required)
    - end: End of date range (required)

    Returns CalendarEvent list containing:
    - Job events for jobs this equipment is assigned to
    - Equipment assignment events for this equipment

    Date ranges exceeding 365 days return 400 error.
    RLS automatically filters by tenant.
    """
    # Ensure timezone-aware datetimes
    if start.tzinfo is None:
        start = start.replace(tzinfo=timezone.utc)
    if end.tzinfo is None:
        end = end.replace(tzinfo=timezone.utc)

    # Validate max date range
    if (end - start).days > 365:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Date range too large (max 365 days)",
        )

    # Query equipment assignments for this equipment in range
    equip_result = await db.execute(
        select(EquipmentAssignment, Equipment.name, Job.title, Job.state, Job.scheduled_start, Job.scheduled_end, Job.id)
        .join(Equipment, EquipmentAssignment.equipment_id == Equipment.id)
        .join(Job, EquipmentAssignment.job_id == Job.id)
        .where(
            EquipmentAssignment.equipment_id == equipment_id,
            Job.scheduled_start.is_not(None),
            Job.scheduled_end.is_not(None),
            Job.scheduled_start < end,
            Job.scheduled_end > start,
        )
    )

    events = []
    job_ids_seen = set()

    for ea, equipment_name, job_title, job_state, job_start, job_end, job_id in equip_result.all():
        # Add equipment assignment event
        events.append(
            CalendarEvent(
                id=ea.id,
                event_type="equipment_assignment",
                title=f"{equipment_name} - {job_title}",
                start=job_start,
                end=job_end,
                color=JOB_STATE_COLORS[job_state.value],
                status="assigned",
                job_id=ea.job_id,
                resource_id=ea.equipment_id,
                resource_name=equipment_name,
                job_title=job_title,
            )
        )

        # Add parent job event (once per job)
        if job_id not in job_ids_seen:
            job_ids_seen.add(job_id)
            events.append(
                CalendarEvent(
                    id=job_id,
                    event_type="job",
                    title=job_title,
                    start=job_start,
                    end=job_end,
                    color=JOB_STATE_COLORS[job_state.value],
                    status=job_state.value,
                )
            )

    return CalendarEventsResponse(events=events, count=len(events))
