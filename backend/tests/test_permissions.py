import pytest
import pytest_asyncio
from fastapi import HTTPException
from app.core.permissions import require_admin, require_active
from app.models import User, UserRole
from app.core.security import hash_password


@pytest.mark.asyncio
async def test_require_admin_allows_admin(test_admin_user):
    """Admin users pass require_admin check"""
    result = require_admin(test_admin_user)
    assert result == test_admin_user


@pytest.mark.asyncio
async def test_require_admin_blocks_crew(test_crew_user):
    """Crew users are blocked by require_admin"""
    with pytest.raises(HTTPException) as exc_info:
        require_admin(test_crew_user)
    assert exc_info.value.status_code == 403
    assert "Admin access required" in exc_info.value.detail


@pytest.mark.asyncio
async def test_require_active_allows_active_user(test_admin_user):
    """Active users pass require_active check"""
    result = require_active(test_admin_user)
    assert result == test_admin_user


@pytest.mark.asyncio
async def test_require_active_blocks_inactive_user(test_db, test_tenant):
    """Inactive users are blocked by require_active"""
    inactive_user = User(
        email="inactive@test.com",
        hashed_password=hash_password("password123"),
        tenant_id=test_tenant.id,
        role=UserRole.ADMIN,
        is_active=False,
    )
    test_db.add(inactive_user)
    await test_db.commit()

    with pytest.raises(HTTPException) as exc_info:
        require_active(inactive_user)
    assert exc_info.value.status_code == 403
