"""Crew portal endpoints for dashboard and job details"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from datetime import datetime, timezone, timedelta
from uuid import UUID

from app.database import get_db
from app.dependencies import get_current_tenant
from app.core.permissions import require_active
from app.models import (
    User,
    CrewProfile,
    CrewAssignment,
    Job,
    JobFile,
    Message,
    MessageLastSeen,
    AssignmentState,
)
from app.schemas.portal import (
    PortalDashboardResponse,
    PortalAssignmentItem,
    PortalJobDetailResponse,
    PortalFileItem,
)
from app.schemas.notification import NotificationCounts

router = APIRouter(prefix="/api/v1/portal", tags=["portal"])


@router.get("/dashboard", response_model=PortalDashboardResponse)
async def get_dashboard(
    current_user: User = Depends(require_active),
    tenant_id: str = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """
    Get crew dashboard with upcoming/recent assignments and notification counts.

    Returns:
    - upcoming: Future assignments sorted by scheduled_start ASC
    - recent: Completed assignments from last 7 days sorted by scheduled_start DESC
    - counts: Notification badge counts (unread messages, pending assignments)

    Raises:
    - 404: If current user has no CrewProfile
    """
    # Look up CrewProfile for current user
    crew_result = await db.execute(
        select(CrewProfile).where(CrewProfile.user_id == current_user.id)
    )
    crew_profile = crew_result.scalar_one_or_none()

    if not crew_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Crew profile not found",
        )

    now = datetime.now(timezone.utc)
    seven_days_ago = now - timedelta(days=7)

    # Query upcoming assignments: future jobs OR jobs with no scheduled_start, exclude DECLINED
    upcoming_query = (
        select(
            CrewAssignment.id.label("assignment_id"),
            Job.id.label("job_id"),
            Job.title.label("job_title"),
            Job.venue.label("job_venue"),
            Job.scheduled_start,
            Job.scheduled_end,
            CrewAssignment.role,
            CrewAssignment.status,
        )
        .join(Job, CrewAssignment.job_id == Job.id)
        .where(
            CrewAssignment.crew_id == crew_profile.id,
            CrewAssignment.status != AssignmentState.DECLINED,
            or_(Job.scheduled_start >= now, Job.scheduled_start.is_(None)),
        )
        .order_by(Job.scheduled_start.asc().nulls_last())
    )
    upcoming_result = await db.execute(upcoming_query)
    upcoming_assignments = [
        PortalAssignmentItem(
            assignment_id=row.assignment_id,
            job_id=row.job_id,
            job_title=row.job_title,
            job_venue=row.job_venue,
            scheduled_start=row.scheduled_start,
            scheduled_end=row.scheduled_end,
            role=row.role,
            status=row.status.value,
        )
        for row in upcoming_result.all()
    ]

    # Query recent assignments: completed jobs from last 7 days
    recent_query = (
        select(
            CrewAssignment.id.label("assignment_id"),
            Job.id.label("job_id"),
            Job.title.label("job_title"),
            Job.venue.label("job_venue"),
            Job.scheduled_start,
            Job.scheduled_end,
            CrewAssignment.role,
            CrewAssignment.status,
        )
        .join(Job, CrewAssignment.job_id == Job.id)
        .where(
            CrewAssignment.crew_id == crew_profile.id,
            Job.state == "complete",
            Job.scheduled_start >= seven_days_ago,
        )
        .order_by(Job.scheduled_start.desc())
    )
    recent_result = await db.execute(recent_query)
    recent_assignments = [
        PortalAssignmentItem(
            assignment_id=row.assignment_id,
            job_id=row.job_id,
            job_title=row.job_title,
            job_venue=row.job_venue,
            scheduled_start=row.scheduled_start,
            scheduled_end=row.scheduled_end,
            role=row.role,
            status=row.status.value,
        )
        for row in recent_result.all()
    ]

    # Compute notification counts (inline from notifications.py logic)

    # --- Unread messages ---
    # Get all last_seen records for this user
    last_seen_result = await db.execute(
        select(MessageLastSeen).where(MessageLastSeen.user_id == current_user.id)
    )
    last_seen_records = {
        ls.job_id: ls.last_seen_at for ls in last_seen_result.scalars().all()
    }

    # Count messages newer than last_seen per job
    unread_count = 0
    if last_seen_records:
        for job_id, last_seen_at in last_seen_records.items():
            count_result = await db.execute(
                select(func.count(Message.id)).where(
                    Message.job_id == job_id,
                    Message.created_at > last_seen_at,
                )
            )
            unread_count += count_result.scalar() or 0

    # --- Pending assignments ---
    pending_result = await db.execute(
        select(func.count(CrewAssignment.id)).where(
            CrewAssignment.crew_id == crew_profile.id,
            CrewAssignment.status == AssignmentState.PENDING,
        )
    )
    pending_count = pending_result.scalar() or 0

    notification_counts = NotificationCounts(
        unread_messages=unread_count,
        pending_assignments=pending_count,
    )

    return PortalDashboardResponse(
        upcoming=upcoming_assignments,
        recent=recent_assignments,
        counts=notification_counts,
    )


@router.get("/jobs/{job_id}", response_model=PortalJobDetailResponse)
async def get_job_detail(
    job_id: UUID,
    current_user: User = Depends(require_active),
    tenant_id: str = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """
    Get job details for assigned crew member.

    Returns full job details including files, but only if crew member is assigned to this job.

    Raises:
    - 404: If CrewProfile not found or Job not found
    - 403: If crew member is not assigned to this job
    """
    # Look up CrewProfile for current user
    crew_result = await db.execute(
        select(CrewProfile).where(CrewProfile.user_id == current_user.id)
    )
    crew_profile = crew_result.scalar_one_or_none()

    if not crew_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Crew profile not found",
        )

    # Look up Job
    job_result = await db.execute(select(Job).where(Job.id == job_id))
    job = job_result.scalar_one_or_none()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )

    # Look up CrewAssignment to verify crew is assigned to this job
    assignment_result = await db.execute(
        select(CrewAssignment).where(
            CrewAssignment.crew_id == crew_profile.id,
            CrewAssignment.job_id == job_id,
        )
    )
    assignment = assignment_result.scalar_one_or_none()

    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not assigned to this job",
        )

    # Query JobFile records for this job
    files_result = await db.execute(
        select(JobFile)
        .where(JobFile.job_id == job_id)
        .order_by(JobFile.created_at.desc())
    )
    files = [
        PortalFileItem(
            id=file.id,
            original_filename=file.original_filename,
            mime_type=file.mime_type,
            file_size=file.file_size,
            uploaded_at=file.created_at,
        )
        for file in files_result.scalars().all()
    ]

    return PortalJobDetailResponse(
        id=job.id,
        title=job.title,
        description=job.description,
        venue=job.venue,
        scheduled_start=job.scheduled_start,
        scheduled_end=job.scheduled_end,
        state=job.state.value,
        crew_role=assignment.role,
        assignment_status=assignment.status.value,
        files=files,
    )
