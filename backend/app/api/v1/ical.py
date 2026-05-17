"""iCal feed and token management API endpoints"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from datetime import datetime, timezone
from uuid import UUID

from app.database import get_db
from app.dependencies import get_current_tenant
from app.core.permissions import require_admin
from app.models.ical_token import ICalToken
from app.models.crew_profile import CrewProfile
from app.models.assignment import CrewAssignment, AssignmentState
from app.models.job import Job
from app.schemas.calendar import ICalTokenCreate, ICalTokenResponse
from app.core.icalendar import build_ical_feed

# Public feed router (no prefix - mounted at /ical/)
feed_router = APIRouter(prefix="/ical", tags=["ical-feed"])

# Admin token management router (mounted at /api/v1/ical/)
router = APIRouter(prefix="/api/v1/ical", tags=["ical"])


@feed_router.get("/{token}.ics")
async def ical_feed(
    token: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Public iCal feed endpoint for calendar app subscriptions.

    No authentication required - token in URL provides access.
    Calendar apps (Google Calendar, Apple Calendar, Outlook) poll this URL.

    Args:
        token: URL-safe token string
        db: Database session

    Returns:
        iCal feed as text/calendar

    Raises:
        404: Invalid token
        410: Token expired
    """
    # Look up token
    token_result = await db.execute(
        select(ICalToken).where(ICalToken.token == token)
    )
    ical_token = token_result.scalar_one_or_none()

    if not ical_token:
        raise HTTPException(status_code=404, detail="Invalid feed token")

    if ical_token.expires_at and ical_token.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=410, detail="Feed token expired")

    # Update last accessed timestamp
    ical_token.last_accessed = datetime.now(timezone.utc)

    # Set tenant context for RLS
    await db.execute(text(f"SET LOCAL app.current_tenant_id = '{ical_token.tenant_id}'"))

    # Fetch confirmed assignments for this crew
    assignments_result = await db.execute(
        select(CrewAssignment).where(
            CrewAssignment.crew_id == ical_token.crew_id,
            CrewAssignment.status == AssignmentState.CONFIRMED,
        )
    )
    assignments = list(assignments_result.scalars().all())

    # Batch fetch jobs
    job_ids = [a.job_id for a in assignments]
    if job_ids:
        jobs_result = await db.execute(select(Job).where(Job.id.in_(job_ids)))
        jobs_dict = {j.id: j for j in jobs_result.scalars().all()}
    else:
        jobs_dict = {}

    # Generate iCal feed
    ical_data = build_ical_feed(assignments, jobs_dict)

    return Response(
        content=ical_data,
        media_type="text/calendar; charset=utf-8",
        headers={
            "Content-Disposition": 'attachment; filename="my-jobs.ics"',
            "Cache-Control": "no-cache, must-revalidate",
        },
    )


@router.post("/tokens", response_model=ICalTokenResponse, status_code=201)
async def create_ical_token(
    body: ICalTokenCreate,
    tenant_id: str = Depends(get_current_tenant),
    current_user=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Create iCal feed token for crew member.

    Admin-only endpoint. Creates non-expiring token for crew calendar subscription.

    Args:
        body: Request with crew_id
        tenant_id: Current tenant context
        current_user: Admin user
        db: Database session

    Returns:
        Token response with feed URL

    Raises:
        404: Crew not found
    """
    # Verify crew exists in tenant
    crew_result = await db.execute(
        select(CrewProfile).where(CrewProfile.id == body.crew_id)
    )
    crew = crew_result.scalar_one_or_none()

    if not crew:
        raise HTTPException(
            status_code=404,
            detail="Crew member not found",
        )

    # Create token
    token_obj = ICalToken.create_for_crew(
        crew_id=body.crew_id,
        tenant_id=UUID(tenant_id),
    )

    db.add(token_obj)
    await db.flush()
    await db.refresh(token_obj)

    # Build response with feed URL
    return ICalTokenResponse(
        id=token_obj.id,
        crew_id=token_obj.crew_id,
        token=token_obj.token,
        feed_url=f"/ical/{token_obj.token}.ics",
        created_at=token_obj.created_at,
    )


@router.get("/tokens/{crew_id}", response_model=list[ICalTokenResponse])
async def list_ical_tokens(
    crew_id: UUID,
    tenant_id: str = Depends(get_current_tenant),
    current_user=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    List all iCal tokens for crew member.

    Admin-only endpoint for token management.

    Args:
        crew_id: Crew profile ID
        tenant_id: Current tenant context
        current_user: Admin user
        db: Database session

    Returns:
        List of tokens for this crew
    """
    tokens_result = await db.execute(
        select(ICalToken).where(ICalToken.crew_id == crew_id)
    )
    tokens = tokens_result.scalars().all()

    return [
        ICalTokenResponse(
            id=t.id,
            crew_id=t.crew_id,
            token=t.token,
            feed_url=f"/ical/{t.token}.ics",
            created_at=t.created_at,
        )
        for t in tokens
    ]


@router.delete("/tokens/{token_id}", status_code=204)
async def delete_ical_token(
    token_id: UUID,
    tenant_id: str = Depends(get_current_tenant),
    current_user=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Revoke iCal token.

    Admin-only endpoint. Deletes token, making feed URL invalid.

    Args:
        token_id: Token ID to delete
        tenant_id: Current tenant context
        current_user: Admin user
        db: Database session

    Returns:
        204 No Content

    Raises:
        404: Token not found
    """
    token_result = await db.execute(
        select(ICalToken).where(ICalToken.id == token_id)
    )
    token = token_result.scalar_one_or_none()

    if not token:
        raise HTTPException(status_code=404, detail="Token not found")

    await db.delete(token)
    return Response(status_code=204)
