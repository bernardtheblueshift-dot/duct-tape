"""Calendar API endpoints for jobs and resource bookings"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone, timedelta, date as date_type
from uuid import UUID
from collections import defaultdict

from app.database import get_db
from app.dependencies import get_current_tenant
from app.core.permissions import require_active, require_admin
from app.models import (
    Job,
    JobState,
    CrewAssignment,
    EquipmentAssignment,
    CrewProfile,
    Equipment,
    User,
    AvailabilityPattern,
    AssignmentState,
)
from app.schemas.calendar import (
    CalendarEvent,
    CalendarEventsResponse,
    JOB_STATE_COLORS,
    AvailabilityDay,
    CrewAvailabilitySummary,
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


@router.get("/crew/{crew_id}/availability", response_model=list[AvailabilityDay])
async def get_crew_availability(
    crew_id: UUID,
    start: datetime,
    end: datetime,
    current_user: User = Depends(require_active),
    tenant_id: str = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """
    Get crew member availability across date range.

    Path parameters:
    - crew_id: UUID of crew member

    Query parameters:
    - start: Start of date range (required)
    - end: End of date range (required)

    Returns per-day status list:
    - status='free': Available and not assigned
    - status='booked': Has CONFIRMED assignment on this day
    - status='unavailable': Recurring pattern has is_available=False

    Weekly patterns are expanded into concrete date list.
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

    # Fetch unavailable weekdays for this crew
    patterns_result = await db.execute(
        select(AvailabilityPattern).where(
            AvailabilityPattern.crew_id == crew_id,
            AvailabilityPattern.is_available == False,
        )
    )
    unavailable_weekdays = {p.day_of_week for p in patterns_result.scalars().all()}

    # Fetch CONFIRMED crew assignments in range (batch with Job join)
    assignments_result = await db.execute(
        select(Job.scheduled_start, Job.scheduled_end)
        .select_from(CrewAssignment)
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
    booked_ranges = [(row.scheduled_start, row.scheduled_end) for row in assignments_result.all()]

    # Build per-day status list
    days: list[AvailabilityDay] = []
    current = start.date() if isinstance(start, datetime) else start
    end_date = end.date() if isinstance(end, datetime) else end

    while current <= end_date:
        if current.weekday() in unavailable_weekdays:
            status = "unavailable"
        elif any(
            job_start.date() <= current <= job_end.date()
            for job_start, job_end in booked_ranges
        ):
            status = "booked"
        else:
            status = "free"
        days.append(AvailabilityDay(date=current, status=status))
        current += timedelta(days=1)

    return days


@router.get("/availability", response_model=list[CrewAvailabilitySummary])
async def get_bulk_availability(
    start: datetime,
    end: datetime,
    current_user: User = Depends(require_admin),
    tenant_id: str = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """
    Get all crew availability summary (admin-only).

    Query parameters:
    - start: Start of date range (required)
    - end: End of date range (required)

    Returns list of crew members with per-day availability status.
    Only active (non-archived) crew included.
    Uses batch queries to avoid N+1 performance issues.

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

    # Get all active crew (not archived)
    crew_result = await db.execute(
        select(CrewProfile, User.email)
        .join(User, CrewProfile.user_id == User.id)
        .where(CrewProfile.archived_at.is_(None))
    )
    all_crew = crew_result.all()  # list of (CrewProfile, email) tuples
    crew_ids = [c.id for c, _ in all_crew]

    if not crew_ids:
        return []

    # Batch fetch ALL unavailable patterns for all crew
    patterns_result = await db.execute(
        select(AvailabilityPattern).where(
            AvailabilityPattern.crew_id.in_(crew_ids),
            AvailabilityPattern.is_available == False,
        )
    )
    # Build map: crew_id -> set of unavailable weekdays
    unavailable_map: dict[UUID, set[int]] = defaultdict(set)
    for pattern in patterns_result.scalars().all():
        unavailable_map[pattern.crew_id].add(pattern.day_of_week)

    # Batch fetch ALL confirmed assignments in range
    assignments_result = await db.execute(
        select(CrewAssignment.crew_id, Job.scheduled_start, Job.scheduled_end)
        .select_from(CrewAssignment)
        .join(Job, CrewAssignment.job_id == Job.id)
        .where(
            CrewAssignment.crew_id.in_(crew_ids),
            CrewAssignment.status == AssignmentState.CONFIRMED,
            Job.scheduled_start.is_not(None),
            Job.scheduled_end.is_not(None),
            Job.scheduled_start < end,
            Job.scheduled_end > start,
        )
    )
    # Build map: crew_id -> list of (start, end) tuples
    bookings_map: dict[UUID, list[tuple]] = defaultdict(list)
    for row in assignments_result.all():
        bookings_map[row.crew_id].append((row.scheduled_start, row.scheduled_end))

    # Build summary for each crew member
    summaries: list[CrewAvailabilitySummary] = []
    for crew_profile, email in all_crew:
        days = []
        current = start.date() if isinstance(start, datetime) else start
        end_date = end.date() if isinstance(end, datetime) else end

        while current <= end_date:
            if current.weekday() in unavailable_map[crew_profile.id]:
                status = "unavailable"
            elif any(s.date() <= current <= e.date() for s, e in bookings_map[crew_profile.id]):
                status = "booked"
            else:
                status = "free"
            days.append(AvailabilityDay(date=current, status=status))
            current += timedelta(days=1)

        summaries.append(
            CrewAvailabilitySummary(
                crew_id=crew_profile.id,
                crew_name=email,
                days=days,
            )
        )

    return summaries
