"""Notification endpoints for badge counts"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_db
from app.dependencies import get_current_tenant, get_current_user
from app.core.permissions import require_active
from app.models import (
    Message,
    MessageLastSeen,
    CrewAssignment,
    CrewProfile,
    AssignmentState,
    User,
)
from app.schemas.notification import NotificationCounts

router = APIRouter(prefix="/api/v1/notifications", tags=["notifications"])


@router.get("/counts", response_model=NotificationCounts)
async def get_notification_counts(
    current_user: User = Depends(require_active),
    tenant_id: str = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """
    Get notification badge counts for current user.

    Returns:
    - unread_messages: count of messages across all jobs that are newer than user's last_seen_at
    - pending_assignments: count of PENDING CrewAssignments for this user
    """
    # --- Unread messages ---
    # Get all last_seen records for this user
    last_seen_result = await db.execute(
        select(MessageLastSeen).where(MessageLastSeen.user_id == current_user.id)
    )
    last_seen_records = {
        ls.job_id: ls.last_seen_at for ls in last_seen_result.scalars().all()
    }

    # Count messages newer than last_seen per job, plus all messages in unseen jobs
    # For jobs user has viewed: count messages with created_at > last_seen_at
    # For jobs user has never viewed: count all messages
    unread_count = 0

    if last_seen_records:
        # Messages in seen jobs that are newer than last_seen
        for job_id, last_seen_at in last_seen_records.items():
            count_result = await db.execute(
                select(func.count(Message.id)).where(
                    Message.job_id == job_id,
                    Message.created_at > last_seen_at,
                )
            )
            unread_count += count_result.scalar() or 0

    # --- Pending assignments ---
    # Find crew profile for current user
    crew_result = await db.execute(
        select(CrewProfile.id).where(CrewProfile.user_id == current_user.id)
    )
    crew_id = crew_result.scalar_one_or_none()

    pending_count = 0
    if crew_id:
        pending_result = await db.execute(
            select(func.count(CrewAssignment.id)).where(
                CrewAssignment.crew_id == crew_id,
                CrewAssignment.status == AssignmentState.PENDING,
            )
        )
        pending_count = pending_result.scalar() or 0

    return NotificationCounts(
        unread_messages=unread_count,
        pending_assignments=pending_count,
    )
