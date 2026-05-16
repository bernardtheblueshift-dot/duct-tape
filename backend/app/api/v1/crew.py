"""Crew CRUD endpoints with search/filter and admin-only write operations"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, func, delete
from datetime import datetime, timezone
from typing import List
from uuid import UUID
from pydantic import BaseModel

from app.database import get_db
from app.dependencies import get_current_tenant
from app.core.permissions import require_admin, require_active
from app.models import CrewProfile, User, UserRole, CrewAssignment, Job
from app.models.rating import CrewRating
from app.models.availability import AvailabilityPattern
from app.schemas.crew import (
    CrewProfileCreate,
    CrewProfileUpdate,
    CrewProfileResponse,
    CrewRatingCreate,
    CrewRatingResponse,
    AvailabilityPatternCreate,
    AvailabilityPatternResponse,
    SkillsMatrixResponse,
    SkillsMatrixEntry,
)

router = APIRouter(prefix="/api/v1/crew", tags=["crew"])


# Inline schema for crew job history
class CrewJobHistoryEntry(BaseModel):
    """Single job entry in crew's work history"""

    job_id: UUID
    job_title: str
    role: str | None
    status: str
    scheduled_start: datetime | None
    scheduled_end: datetime | None


@router.post("/", response_model=CrewProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_crew_profile(
    profile_data: CrewProfileCreate,
    current_user: User = Depends(require_admin),
    tenant_id: str = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """
    Create crew profile (admin only).

    Validates:
    - User exists and has role=CREW
    - No existing CrewProfile for that user_id (returns 409 if duplicate)

    Profile is automatically associated with current tenant via RLS context.
    """
    # Validate user exists and has CREW role
    user_result = await db.execute(
        select(User).where(User.id == profile_data.user_id)
    )
    user = user_result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if user.role != UserRole.CREW:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must have CREW role",
        )

    # Check for existing crew profile
    existing_result = await db.execute(
        select(CrewProfile).where(CrewProfile.user_id == profile_data.user_id)
    )
    existing = existing_result.scalar_one_or_none()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Crew profile already exists for this user",
        )

    # Create crew profile
    profile = CrewProfile(
        **profile_data.model_dump(),
        tenant_id=tenant_id,
    )
    db.add(profile)
    await db.commit()
    await db.refresh(profile)
    return profile


@router.get("/", response_model=List[CrewProfileResponse])
async def list_crew(
    search: str | None = None,
    role: str | None = None,
    skills: list[str] | None = Query(None),
    include_archived: bool = False,
    current_user: User = Depends(require_active),
    tenant_id: str = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """
    List/search crew directory (authenticated users).

    Query parameters:
    - search: Case-insensitive search across email, bio, phone
    - role: Filter by functional role (e.g., "Camera Operator") from assignments
    - skills: Filter by skills (must have ALL specified skills)
    - include_archived: Include archived profiles (default: false)

    Results are automatically filtered by tenant via RLS.
    """
    query = select(CrewProfile)

    # Default: exclude archived profiles
    if not include_archived:
        query = query.where(CrewProfile.archived_at.is_(None))

    # Apply search filter
    if search:
        search_pattern = f"%{search}%"
        # Join with User to search email
        query = query.join(User, CrewProfile.user_id == User.id)
        query = query.where(
            or_(
                User.email.ilike(search_pattern),
                CrewProfile.bio.ilike(search_pattern),
                CrewProfile.phone.ilike(search_pattern),
            )
        )

    # Apply role filter - find crew who have been assigned this role
    if role:
        role_pattern = f"%{role}%"
        # Subquery for crew IDs with matching role assignments
        role_subquery = (
            select(CrewAssignment.crew_id)
            .where(CrewAssignment.role.ilike(role_pattern))
            .distinct()
        )
        query = query.where(CrewProfile.id.in_(role_subquery))

    # Apply skills filter - must have ALL specified skills
    if skills:
        for skill in skills:
            query = query.where(CrewProfile.skills.contains([skill]))

    result = await db.execute(query)
    crew = result.scalars().all()
    return crew


@router.get("/skills-matrix", response_model=SkillsMatrixResponse)
async def get_skills_matrix(
    current_user: User = Depends(require_active),
    tenant_id: str = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """
    Get skills matrix showing all crew capabilities across all skill tags.

    Returns matrix format with all unique skills and boolean mapping per crew member.
    Excludes archived crew profiles.
    RLS automatically filters by tenant.
    """
    # Get all unique skills across non-archived crew
    skills_query = select(func.unnest(CrewProfile.skills).distinct()).where(
        CrewProfile.archived_at.is_(None)
    )
    skills_result = await db.execute(skills_query)
    all_skills = sorted([skill for skill, in skills_result.all()])

    # Get all non-archived crew profiles with user email
    crew_query = (
        select(CrewProfile, User.email)
        .join(User, CrewProfile.user_id == User.id)
        .where(CrewProfile.archived_at.is_(None))
    )
    crew_result = await db.execute(crew_query)
    crew_data = crew_result.all()

    # Build matrix: for each crew, map each skill to True/False
    crew_entries = []
    for profile, email in crew_data:
        skill_map = {skill: skill in profile.skills for skill in all_skills}
        crew_entries.append(
            SkillsMatrixEntry(
                id=profile.id,
                email=email,
                skills=skill_map,
            )
        )

    return SkillsMatrixResponse(skills=all_skills, crew=crew_entries)


@router.get("/{crew_id}", response_model=CrewProfileResponse)
async def get_crew_profile(
    crew_id: UUID,
    current_user: User = Depends(require_active),
    tenant_id: str = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """
    Get crew profile by ID.

    RLS automatically filters by tenant.
    """
    result = await db.execute(select(CrewProfile).where(CrewProfile.id == crew_id))
    profile = result.scalar_one_or_none()

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Crew profile not found",
        )

    return profile


@router.patch("/{crew_id}", response_model=CrewProfileResponse)
async def update_crew_profile(
    crew_id: UUID,
    profile_update: CrewProfileUpdate,
    current_user: User = Depends(require_admin),
    tenant_id: str = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """
    Update crew profile fields (admin only).

    Only updates fields provided in request (partial updates supported).
    RLS automatically filters by tenant.
    """
    result = await db.execute(select(CrewProfile).where(CrewProfile.id == crew_id))
    profile = result.scalar_one_or_none()

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Crew profile not found",
        )

    # Update only provided fields
    update_data = profile_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(profile, key, value)

    await db.commit()
    await db.refresh(profile)
    return profile


@router.post("/{crew_id}/archive", response_model=CrewProfileResponse)
async def archive_crew_profile(
    crew_id: UUID,
    current_user: User = Depends(require_admin),
    tenant_id: str = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """
    Archive crew profile (admin only).

    Sets archived_at timestamp. Archived profiles are excluded from
    directory search by default.
    RLS automatically filters by tenant.
    """
    result = await db.execute(select(CrewProfile).where(CrewProfile.id == crew_id))
    profile = result.scalar_one_or_none()

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Crew profile not found",
        )

    profile.archived_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(profile)
    return profile


@router.post("/{crew_id}/unarchive", response_model=CrewProfileResponse)
async def unarchive_crew_profile(
    crew_id: UUID,
    current_user: User = Depends(require_admin),
    tenant_id: str = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """
    Restore archived crew profile (admin only).

    Clears archived_at timestamp, making profile visible in directory again.
    RLS automatically filters by tenant.
    """
    result = await db.execute(select(CrewProfile).where(CrewProfile.id == crew_id))
    profile = result.scalar_one_or_none()

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Crew profile not found",
        )

    profile.archived_at = None
    await db.commit()
    await db.refresh(profile)
    return profile


@router.post(
    "/{crew_id}/ratings", response_model=CrewRatingResponse, status_code=status.HTTP_201_CREATED
)
async def rate_crew(
    crew_id: UUID,
    job_id: UUID,
    rating_data: CrewRatingCreate,
    current_user: User = Depends(require_admin),
    tenant_id: str = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """
    Rate crew member for a completed job (admin only).

    Creates rating (1-5 stars) and updates cached rating_average on CrewProfile.
    Validates:
    - crew_id exists (404)
    - job_id exists (404)
    - No duplicate rating for this crew+job pair (409)

    RLS automatically filters by tenant.
    """
    # Validate crew exists
    crew_result = await db.execute(select(CrewProfile).where(CrewProfile.id == crew_id))
    crew = crew_result.scalar_one_or_none()
    if not crew:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Crew profile not found",
        )

    # Validate job exists
    job_result = await db.execute(select(Job).where(Job.id == job_id))
    job = job_result.scalar_one_or_none()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )

    # Check for existing rating (unique constraint)
    existing_query = select(CrewRating).where(
        CrewRating.crew_id == crew_id,
        CrewRating.job_id == job_id,
    )
    existing_result = await db.execute(existing_query)
    if existing_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Already rated for this job",
        )

    # Create rating
    rating = CrewRating(
        crew_id=crew_id,
        job_id=job_id,
        rated_by=current_user.id,
        tenant_id=tenant_id,
        **rating_data.model_dump(),
    )
    db.add(rating)
    await db.flush()

    # Recalculate cached average
    avg_query = select(func.avg(CrewRating.stars), func.count(CrewRating.id)).where(
        CrewRating.crew_id == crew_id
    )
    avg_result = await db.execute(avg_query)
    avg, count = avg_result.one()

    crew.rating_average = round(float(avg), 2)
    crew.rating_count = count

    await db.commit()
    await db.refresh(rating)
    return rating


@router.get("/{crew_id}/ratings", response_model=List[CrewRatingResponse])
async def list_ratings(
    crew_id: UUID,
    limit: int = 20,
    offset: int = 0,
    current_user: User = Depends(require_active),
    tenant_id: str = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """
    List ratings for a crew member.

    Returns ratings in reverse chronological order (newest first).
    Supports pagination via limit/offset.
    RLS automatically filters by tenant.
    """
    query = (
        select(CrewRating)
        .where(CrewRating.crew_id == crew_id)
        .order_by(CrewRating.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    result = await db.execute(query)
    ratings = result.scalars().all()
    return ratings


@router.get("/{crew_id}/history", response_model=List[CrewJobHistoryEntry])
async def get_crew_history(
    crew_id: UUID,
    current_user: User = Depends(require_active),
    tenant_id: str = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """
    Get crew member's job history.

    Returns all jobs this crew member has been assigned to,
    ordered by scheduled_start (most recent first).
    RLS automatically filters by tenant.
    """
    query = (
        select(
            Job.id.label("job_id"),
            Job.title.label("job_title"),
            CrewAssignment.role,
            CrewAssignment.status,
            Job.scheduled_start,
            Job.scheduled_end,
        )
        .join(Job, CrewAssignment.job_id == Job.id)
        .where(CrewAssignment.crew_id == crew_id)
        .order_by(Job.scheduled_start.desc())
    )
    result = await db.execute(query)
    history = []
    for row in result.all():
        history.append(
            CrewJobHistoryEntry(
                job_id=row.job_id,
                job_title=row.job_title,
                role=row.role,
                status=row.status.value,
                scheduled_start=row.scheduled_start,
                scheduled_end=row.scheduled_end,
            )
        )
    return history


@router.put("/{crew_id}/availability", response_model=List[AvailabilityPatternResponse])
async def set_availability(
    crew_id: UUID,
    patterns: List[AvailabilityPatternCreate],
    current_user: User = Depends(require_active),
    tenant_id: str = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """
    Set crew availability patterns (upsert).

    Crew can set their own availability.
    Admin can set any crew member's availability.

    Replaces all existing patterns with new ones (delete + insert).
    RLS automatically filters by tenant.
    """
    # Validate crew exists
    crew_result = await db.execute(select(CrewProfile).where(CrewProfile.id == crew_id))
    crew = crew_result.scalar_one_or_none()
    if not crew:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Crew profile not found",
        )

    # Permission check: crew can only set their own availability
    if current_user.role == UserRole.CREW and crew.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Crew can only set their own availability",
        )

    # Delete existing patterns (upsert pattern)
    await db.execute(delete(AvailabilityPattern).where(AvailabilityPattern.crew_id == crew_id))

    # Insert new patterns
    new_patterns = []
    for pattern_data in patterns:
        pattern = AvailabilityPattern(
            crew_id=crew_id,
            tenant_id=tenant_id,
            **pattern_data.model_dump(),
        )
        db.add(pattern)
        new_patterns.append(pattern)

    await db.commit()
    for pattern in new_patterns:
        await db.refresh(pattern)

    return new_patterns


@router.get("/{crew_id}/availability", response_model=List[AvailabilityPatternResponse])
async def get_availability(
    crew_id: UUID,
    current_user: User = Depends(require_active),
    tenant_id: str = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """
    Get crew availability patterns.

    Returns all weekly availability patterns, ordered by day of week.
    RLS automatically filters by tenant.
    """
    query = (
        select(AvailabilityPattern)
        .where(AvailabilityPattern.crew_id == crew_id)
        .order_by(AvailabilityPattern.day_of_week.asc())
    )
    result = await db.execute(query)
    patterns = result.scalars().all()
    return patterns
