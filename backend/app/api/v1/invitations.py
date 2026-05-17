from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone
from uuid import UUID

from app.database import get_db
from app.dependencies import get_current_user, get_current_tenant
from app.core.permissions import require_admin
from app.core.security import hash_password
from app.models import User, Tenant, InvitationToken, UserRole
from app.schemas.auth import InviteRequest, AcceptInvitationRequest, MessageResponse
from app.tasks.email import send_invitation_email

router = APIRouter(prefix="/api/v1/invitations", tags=["invitations"])


@router.post("/", response_model=MessageResponse)
async def create_invitation(
    request: InviteRequest,
    current_user: User = Depends(require_admin),
    tenant_id: str = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """
    Create invitation for new user to join tenant (admin only).

    Args:
        request: Email and role for invitee
        current_user: Current admin user (from require_admin dependency)
        tenant_id: Tenant context (from get_current_tenant dependency)
        db: Database session

    Returns:
        Success message

    Raises:
        HTTPException: 400 if user already exists in tenant
    """
    # Check if user already exists in tenant
    result = await db.execute(
        select(User).where(
            User.email == request.email, User.tenant_id == UUID(tenant_id)
        )
    )
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already exists in tenant",
        )

    # Create invitation token
    invitation = InvitationToken.create(
        email=request.email,
        tenant_id=UUID(tenant_id),
        invited_by=current_user.id,
        role=UserRole[request.role.upper()],
    )

    db.add(invitation)
    await db.flush()

    # Get tenant name for email
    result = await db.execute(select(Tenant).where(Tenant.id == UUID(tenant_id)))
    tenant = result.scalar_one()

    # Send invitation email asynchronously
    try:
        send_invitation_email.delay(
            request.email, invitation.token, current_user.email, tenant.name
        )
    except Exception:
        pass

    await db.commit()

    return MessageResponse(message="Invitation sent")


@router.post("/accept", response_model=MessageResponse)
async def accept_invitation(
    request: AcceptInvitationRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Accept invitation and create account in invited tenant.

    Args:
        request: Invitation token and password for new account
        db: Database session

    Returns:
        Success message

    Raises:
        HTTPException: 400 if token invalid, expired, or account exists
    """
    # Query invitation token
    result = await db.execute(
        select(InvitationToken).where(InvitationToken.token == request.token)
    )
    invitation = result.scalar_one_or_none()

    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid invitation",
        )

    # Check expiration
    if invitation.expires_at < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invitation expired",
        )

    # Check if user already exists
    result = await db.execute(
        select(User).where(
            User.email == invitation.email, User.tenant_id == invitation.tenant_id
        )
    )
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account already exists",
        )

    # Create user with is_active=True (no email verification needed for invitations)
    new_user = User(
        email=invitation.email,
        hashed_password=hash_password(request.password),
        tenant_id=invitation.tenant_id,
        role=invitation.role,
        is_active=True,
    )

    db.add(new_user)

    # Delete invitation token
    await db.delete(invitation)

    await db.commit()

    return MessageResponse(message="Account created successfully")
