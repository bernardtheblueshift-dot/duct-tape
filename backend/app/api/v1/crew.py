"""Crew CRUD endpoints with search/filter and admin-only write operations"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from datetime import datetime, timezone
from typing import List
from uuid import UUID

from app.database import get_db
from app.dependencies import get_current_tenant
from app.core.permissions import require_admin, require_active
from app.models import CrewProfile, User, UserRole, CrewAssignment
from app.schemas.crew import CrewProfileCreate, CrewProfileUpdate, CrewProfileResponse

router = APIRouter(prefix="/api/v1/crew", tags=["crew"])


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
