import pytest
import pytest_asyncio
from sqlalchemy import select
from app.models import User, Tenant, VerificationToken, PasswordResetToken, UserRole, RefreshToken
from app.core.security import hash_password


@pytest.mark.asyncio
async def test_register_creates_user_and_tenant(async_client, test_db):
    """POST /auth/register creates user and tenant"""
    response = await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": "newuser@test.com",
            "password": "password123",
            "company_name": "New Co",
        },
    )
    assert response.status_code == 200
    assert "Verification email sent" in response.json()["message"]

    # Verify user created in database
    result = await test_db.execute(select(User).where(User.email == "newuser@test.com"))
    user = result.scalar_one()
    assert user.is_active is False
    assert user.role == UserRole.ADMIN

    # Verify tenant created
    result = await test_db.execute(select(Tenant).where(Tenant.id == user.tenant_id))
    tenant = result.scalar_one()
    assert tenant.name == "New Co"


@pytest.mark.asyncio
async def test_register_duplicate_email_fails(async_client, test_admin_user):
    """POST /auth/register with duplicate email returns 400"""
    response = await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": "admin@test.com",
            "password": "password123",
            "company_name": "Dup Co",
        },
    )
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_verify_email_activates_user(async_client, test_db):
    """POST /auth/verify-email with valid token activates user"""
    # Create inactive user with verification token
    tenant = Tenant(name="Test", timezone="UTC")
    test_db.add(tenant)
    await test_db.flush()

    user = User(
        email="verify@test.com",
        hashed_password=hash_password("password123"),
        tenant_id=tenant.id,
        role=UserRole.ADMIN,
        is_active=False,
    )
    test_db.add(user)
    await test_db.flush()

    token = VerificationToken.create_for_user(user.id)
    test_db.add(token)
    await test_db.commit()

    # Verify email
    response = await async_client.post(
        "/api/v1/auth/verify-email", json={"token": token.token}
    )
    assert response.status_code == 200

    # Check user activated
    await test_db.refresh(user)
    assert user.is_active is True


@pytest.mark.asyncio
async def test_verify_email_expired_token_fails(async_client, test_db):
    """POST /auth/verify-email with expired token returns 400"""
    from datetime import datetime, timedelta, timezone

    tenant = Tenant(name="Test", timezone="UTC")
    test_db.add(tenant)
    await test_db.flush()

    user = User(
        email="verify@test.com",
        hashed_password=hash_password("password123"),
        tenant_id=tenant.id,
        role=UserRole.ADMIN,
        is_active=False,
    )
    test_db.add(user)
    await test_db.flush()

    # Create expired token
    token = VerificationToken(
        user_id=user.id,
        token="expired_token_123",
        expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
    )
    test_db.add(token)
    await test_db.commit()

    # Try to verify with expired token
    response = await async_client.post(
        "/api/v1/auth/verify-email", json={"token": "expired_token_123"}
    )
    assert response.status_code == 400
    assert "expired" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_login_returns_cookies(async_client, test_admin_user):
    """POST /auth/login with valid credentials returns cookies"""
    response = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "admin@test.com", "password": "password123"},
    )
    assert response.status_code == 200
    cookies = response.cookies
    assert "access_token" in cookies
    assert "refresh_token" in cookies


@pytest.mark.asyncio
async def test_login_wrong_password_fails(async_client, test_admin_user):
    """POST /auth/login with wrong password returns 401"""
    response = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "admin@test.com", "password": "wrongpassword"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_unverified_email_fails(async_client, test_db, test_tenant):
    """POST /auth/login with unverified email returns 403"""
    # Create inactive user
    user = User(
        email="inactive@test.com",
        hashed_password=hash_password("password123"),
        tenant_id=test_tenant.id,
        role=UserRole.ADMIN,
        is_active=False,
    )
    test_db.add(user)
    await test_db.commit()

    response = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "inactive@test.com", "password": "password123"},
    )
    assert response.status_code == 403
    assert "not verified" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_refresh_with_valid_token_returns_new_access_token(
    async_client, test_admin_user, test_db
):
    """POST /auth/refresh with valid refresh token returns new access token"""
    # Create server-side refresh token
    refresh_obj, raw_token = RefreshToken.create_for_user(test_admin_user.id)
    test_db.add(refresh_obj)
    await test_db.flush()

    # Refresh access token
    response = await async_client.post(
        "/api/v1/auth/refresh", cookies={"refresh_token": raw_token}
    )
    assert response.status_code == 200
    assert "access_token" in response.cookies
    assert "refresh_token" in response.cookies


@pytest.mark.asyncio
async def test_password_reset_flow(async_client, test_db, test_admin_user):
    """Complete password reset flow: request -> reset -> login"""
    # Request reset
    response = await async_client.post(
        "/api/v1/auth/reset-password-request", json={"email": "admin@test.com"}
    )
    assert response.status_code == 200

    # Get reset token from database
    result = await test_db.execute(
        select(PasswordResetToken).where(
            PasswordResetToken.user_id == test_admin_user.id
        )
    )
    reset_token = result.scalar_one()

    # Reset password
    response = await async_client.post(
        "/api/v1/auth/reset-password",
        json={"token": reset_token.token, "new_password": "newpassword123"},
    )
    assert response.status_code == 200

    # Verify can login with new password
    response = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "admin@test.com", "password": "newpassword123"},
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_password_reset_request_always_succeeds(async_client):
    """POST /auth/reset-password-request always returns success (no user leak)"""
    # Request reset for non-existent user
    response = await async_client.post(
        "/api/v1/auth/reset-password-request", json={"email": "nonexistent@test.com"}
    )
    assert response.status_code == 200
    assert "sent if account exists" in response.json()["message"].lower()


@pytest.mark.asyncio
async def test_logout_clears_cookies(async_client):
    """POST /auth/logout clears auth cookies"""
    response = await async_client.post("/api/v1/auth/logout")
    assert response.status_code == 200

    # Check cookies are cleared (max_age=0) via Set-Cookie headers
    set_cookie_headers = response.headers.get_list("set-cookie")
    cookie_names = [h.split("=")[0] for h in set_cookie_headers]
    assert "access_token" in cookie_names
    assert "refresh_token" in cookie_names
    # Verify max-age=0 (deletion)
    for header in set_cookie_headers:
        assert "Max-Age=0" in header or '=""' in header
