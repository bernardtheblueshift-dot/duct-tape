import pytest
import pytest_asyncio
from sqlalchemy import select, text
from app.models import User, Tenant, UserRole
from app.core.security import hash_password


@pytest.mark.asyncio
async def test_rls_prevents_cross_tenant_access(test_db):
    """Verify RLS policies prevent cross-tenant data access"""
    # Create two tenants with users
    tenant_a = Tenant(name="Tenant A", timezone="UTC")
    tenant_b = Tenant(name="Tenant B", timezone="UTC")
    test_db.add_all([tenant_a, tenant_b])
    await test_db.flush()

    user_a = User(
        email="usera@test.com",
        hashed_password=hash_password("password123"),
        tenant_id=tenant_a.id,
        role=UserRole.ADMIN,
        is_active=True,
    )
    user_b = User(
        email="userb@test.com",
        hashed_password=hash_password("password123"),
        tenant_id=tenant_b.id,
        role=UserRole.ADMIN,
        is_active=True,
    )
    test_db.add_all([user_a, user_b])
    await test_db.commit()

    # Set tenant context to Tenant A
    await test_db.execute(text(f"SET LOCAL app.current_tenant_id = '{tenant_a.id}'"))

    # Query users - should only return user_a
    result = await test_db.execute(select(User))
    users = result.scalars().all()

    assert len(users) == 1, f"Expected 1 user, got {len(users)}"
    assert users[0].email == "usera@test.com"

    # Change tenant context to Tenant B
    await test_db.execute(text(f"SET LOCAL app.current_tenant_id = '{tenant_b.id}'"))

    # Query users - should only return user_b
    result = await test_db.execute(select(User))
    users = result.scalars().all()

    assert len(users) == 1
    assert users[0].email == "userb@test.com"


@pytest.mark.asyncio
async def test_rls_blocks_access_without_tenant_context(test_db):
    """Verify RLS blocks access when tenant context not set"""
    tenant = Tenant(name="Test", timezone="UTC")
    test_db.add(tenant)
    await test_db.flush()

    user = User(
        email="test@test.com",
        hashed_password=hash_password("password123"),
        tenant_id=tenant.id,
        role=UserRole.ADMIN,
        is_active=True,
    )
    test_db.add(user)
    await test_db.commit()

    # Query without setting tenant context
    result = await test_db.execute(select(User))
    users = result.scalars().all()

    # RLS should block access (empty result)
    assert len(users) == 0, "RLS should block access without tenant context"
