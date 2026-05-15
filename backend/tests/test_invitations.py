import pytest
import pytest_asyncio
from sqlalchemy import select
from app.models import User, Tenant, InvitationToken, UserRole


@pytest.mark.asyncio
async def test_admin_can_create_invitation(async_client, admin_token, test_tenant):
    """Admin can POST /api/v1/invitations to create invitation"""
    response = await async_client.post(
        "/api/v1/invitations/",
        json={"email": "newcrew@test.com", "role": "crew"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    assert "Invitation sent" in response.json()["message"]


@pytest.mark.asyncio
async def test_crew_cannot_create_invitation(async_client, crew_token):
    """Crew user receives 403 when creating invitation"""
    response = await async_client.post(
        "/api/v1/invitations/",
        json={"email": "another@test.com", "role": "crew"},
        headers={"Authorization": f"Bearer {crew_token}"},
    )
    assert response.status_code == 403
    assert "Admin access required" in response.json()["detail"]


@pytest.mark.asyncio
async def test_accept_invitation_creates_user(
    async_client, test_db, test_admin_user, test_tenant
):
    """Accepting invitation creates user with is_active=True"""
    # Create invitation
    invitation = InvitationToken.create(
        email="invited@test.com",
        tenant_id=test_tenant.id,
        invited_by=test_admin_user.id,
        role=UserRole.CREW,
    )
    test_db.add(invitation)
    await test_db.commit()

    # Accept invitation
    response = await async_client.post(
        "/api/v1/invitations/accept",
        json={"token": invitation.token, "password": "password123"},
    )
    assert response.status_code == 200

    # Verify user created
    result = await test_db.execute(select(User).where(User.email == "invited@test.com"))
    user = result.scalar_one()
    assert user.is_active is True  # No email verification needed
    assert user.role == UserRole.CREW
    assert user.tenant_id == test_tenant.id


@pytest.mark.asyncio
async def test_accept_invitation_expired_token_fails(
    async_client, test_db, test_admin_user, test_tenant
):
    """Accepting expired invitation returns 400"""
    from datetime import datetime, timedelta, timezone

    # Create expired invitation
    invitation = InvitationToken(
        email="expired@test.com",
        tenant_id=test_tenant.id,
        invited_by=test_admin_user.id,
        role=UserRole.CREW,
        token="expired_token_123",
        expires_at=datetime.now(timezone.utc) - timedelta(days=1),  # Already expired
    )
    test_db.add(invitation)
    await test_db.commit()

    # Try to accept expired invitation
    response = await async_client.post(
        "/api/v1/invitations/accept",
        json={"token": "expired_token_123", "password": "password123"},
    )
    assert response.status_code == 400
    assert "expired" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_accept_invitation_creates_user_in_correct_tenant(
    async_client, test_db, test_admin_user
):
    """User is created in invitation's tenant, not admin's tenant"""
    # Create second tenant
    tenant_b = Tenant(name="Tenant B", timezone="UTC")
    test_db.add(tenant_b)
    await test_db.flush()

    # Create invitation for Tenant B
    invitation = InvitationToken.create(
        email="tenantb@test.com",
        tenant_id=tenant_b.id,
        invited_by=test_admin_user.id,
        role=UserRole.CREW,
    )
    test_db.add(invitation)
    await test_db.commit()

    # Accept invitation
    response = await async_client.post(
        "/api/v1/invitations/accept",
        json={"token": invitation.token, "password": "password123"},
    )
    assert response.status_code == 200

    # Verify user created in Tenant B
    result = await test_db.execute(select(User).where(User.email == "tenantb@test.com"))
    user = result.scalar_one()
    assert user.tenant_id == tenant_b.id


@pytest.mark.asyncio
async def test_create_invitation_existing_user_fails(
    async_client, admin_token, test_db, test_tenant, test_crew_user
):
    """Cannot create invitation for user already in tenant"""
    response = await async_client.post(
        "/api/v1/invitations/",
        json={"email": "crew@test.com", "role": "crew"},  # crew user already exists
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"].lower()
