import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.models.base import Base
from app.models import User, Tenant, UserRole
from app.main import app
from app.database import get_db
from app.config import settings
from app.core.security import hash_password, create_access_token
import uuid


# Create test database engine
TEST_DATABASE_URL = settings.DATABASE_URL.replace("/duct_tape", "/duct_tape_test")
test_engine = create_async_engine(TEST_DATABASE_URL, echo=False, pool_pre_ping=True)

# Session factory for tests
TestSessionLocal = async_sessionmaker(
    test_engine, class_=AsyncSession, expire_on_commit=False
)


@pytest_asyncio.fixture(scope="function")
async def test_db():
    """
    Create a fresh database for each test.
    Creates all tables, yields session, then drops all tables.
    """
    # Create all tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Yield session
    async with TestSessionLocal() as session:
        yield session

    # Drop all tables after test
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def async_client(test_db):
    """
    AsyncClient with test database dependency override.
    """

    async def override_get_db():
        yield test_db

    # Override dependency
    app.dependency_overrides[get_db] = override_get_db

    # Create client
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client

    # Restore original dependency
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_tenant(test_db):
    """Create a test tenant"""
    tenant = Tenant(name="Test Company", timezone="UTC")
    test_db.add(tenant)
    await test_db.flush()
    return tenant


@pytest_asyncio.fixture
async def test_admin_user(test_db, test_tenant):
    """Create a test admin user"""
    user = User(
        email="admin@test.com",
        hashed_password=hash_password("password123"),
        tenant_id=test_tenant.id,
        role=UserRole.ADMIN,
        is_active=True,
    )
    test_db.add(user)
    await test_db.flush()
    return user


@pytest_asyncio.fixture
async def test_crew_user(test_db, test_tenant):
    """Create a test crew user"""
    user = User(
        email="crew@test.com",
        hashed_password=hash_password("password123"),
        tenant_id=test_tenant.id,
        role=UserRole.CREW,
        is_active=True,
    )
    test_db.add(user)
    await test_db.flush()
    return user


@pytest_asyncio.fixture
async def admin_token(test_admin_user):
    """Generate JWT access token for admin user"""
    return create_access_token(
        str(test_admin_user.id),
        str(test_admin_user.tenant_id),
        test_admin_user.role.value,
    )


@pytest_asyncio.fixture
async def crew_token(test_crew_user):
    """Generate JWT access token for crew user"""
    return create_access_token(
        str(test_crew_user.id),
        str(test_crew_user.tenant_id),
        test_crew_user.role.value,
    )
