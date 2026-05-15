import pytest
import pytest_asyncio
from unittest.mock import patch
from sqlalchemy import select
from app.models import User, InvitationToken, UserRole


@pytest.mark.asyncio
async def test_admin_creates_invitation_token_in_database(
    async_client, admin_token, test_db
):
    """Admin POST /invitations creates InvitationToken in database"""
    response = await async_client.post(
        "/api/v1/invitations/",
        json={"email": "newcrew@test.com", "role": "crew"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    assert "Invitation sent" in response.json()["message"]

    # Verify token created in database
    result = await test_db.execute(
        select(InvitationToken).where(InvitationToken.email == "newcrew@test.com")
    )
    invitation = result.scalar_one()
    assert invitation.role == UserRole.CREW
    assert invitation.token is not None


@pytest.mark.asyncio
async def test_crew_cannot_create_invitation_returns_403(async_client, crew_token):
    """Crew POST /invitations returns 403 Forbidden"""
    response = await async_client.post(
        "/api/v1/invitations/",
        json={"email": "another@test.com", "role": "crew"},
        headers={"Authorization": f"Bearer {crew_token}"},
    )
    assert response.status_code == 403
    assert "Admin access required" in response.json()["detail"]


@pytest.mark.asyncio
async def test_invitation_sends_email_via_celery(
    async_client, admin_token, test_tenant, test_admin_user
):
    """POST /invitations sends email via Celery task"""
    # Mock the Celery task
    with patch("app.api.v1.invitations.send_invitation_email") as mock_task:
        response = await async_client.post(
            "/api/v1/invitations/",
            json={"email": "invited@test.com", "role": "crew"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200

        # Verify email task was called
        mock_task.delay.assert_called_once()
        args = mock_task.delay.call_args[0]
        assert args[0] == "invited@test.com"  # email
        assert args[2] == test_admin_user.email  # inviter_name
        assert args[3] == test_tenant.name  # tenant_name


@pytest.mark.asyncio
async def test_accept_invitation_creates_active_user(
    async_client, test_db, test_admin_user, test_tenant
):
    """POST /accept-invitation with valid token creates User with is_active=True"""
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
    assert "Account created successfully" in response.json()["message"]

    # Verify user created with is_active=True
    result = await test_db.execute(select(User).where(User.email == "invited@test.com"))
    user = result.scalar_one()
    assert user.is_active is True
    assert user.role == UserRole.CREW
    assert user.tenant_id == test_tenant.id


@pytest.mark.asyncio
async def test_accept_invitation_expired_token_returns_400(
    async_client, test_db, test_admin_user, test_tenant
):
    """POST /accept-invitation with expired token returns 400"""
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
    """POST /accept-invitation creates user in invitation's tenant"""
    from app.models import Tenant

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
