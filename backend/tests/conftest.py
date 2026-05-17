import pytest
import pytest_asyncio
from unittest.mock import patch, MagicMock
import sys

sys.modules['magic'] = MagicMock()

from httpx import AsyncClient, ASGITransport
from sqlalchemy import text, event
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.models.base import Base
from app.models import User, Tenant, UserRole
from app.main import app
from app.database import get_db
from app.config import settings
from app.core.security import hash_password, create_access_token


TEST_DATABASE_URL = settings.DATABASE_URL.replace("/duct_tape", "/duct_tape_test")

engine = create_async_engine(TEST_DATABASE_URL, echo=False)


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def test_db():
    connection = await engine.connect()
    transaction = await connection.begin()
    session = AsyncSession(bind=connection, expire_on_commit=False)

    # Disable the outer commit in get_db since we control the transaction
    await connection.begin_nested()

    @event.listens_for(session.sync_session, "after_transaction_end")
    def restart_savepoint(session_inner, transaction_inner):
        if transaction_inner.nested and not transaction_inner._parent.nested:
            session_inner.begin_nested()

    yield session

    await session.close()
    await transaction.rollback()
    await connection.close()


@pytest_asyncio.fixture(scope="function")
async def async_client(test_db):
    async def override_get_db():
        yield test_db

    app.dependency_overrides[get_db] = override_get_db

    with patch("app.api.v1.auth.send_verification_email") as mock_verify, \
         patch("app.api.v1.auth.send_password_reset_email") as mock_reset, \
         patch("app.api.v1.invitations.send_invitation_email") as mock_invite:
        mock_verify.delay = lambda *a, **k: None
        mock_reset.delay = lambda *a, **k: None
        mock_invite.delay = lambda *a, **k: None

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
            follow_redirects=True,
        ) as client:
            yield client

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_tenant(test_db):
    tenant = Tenant(name="Test Company", timezone="UTC")
    test_db.add(tenant)
    await test_db.flush()
    return tenant


@pytest_asyncio.fixture
async def test_admin_user(test_db, test_tenant):
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
    return create_access_token(
        str(test_admin_user.id),
        str(test_admin_user.tenant_id),
        test_admin_user.role.value,
    )


@pytest_asyncio.fixture
async def crew_token(test_crew_user):
    return create_access_token(
        str(test_crew_user.id),
        str(test_crew_user.tenant_id),
        test_crew_user.role.value,
    )


@pytest_asyncio.fixture
async def test_crew_profile(test_db, test_crew_user, test_tenant):
    from app.models import CrewProfile
    profile = CrewProfile(
        user_id=test_crew_user.id,
        tenant_id=test_tenant.id,
        phone="+1234567890",
        bio="Experienced camera operator",
        hourly_rate=50.00,
        skills=["Camera", "Lighting"],
    )
    test_db.add(profile)
    await test_db.flush()
    return profile


@pytest_asyncio.fixture
async def test_job(test_db, test_tenant):
    from app.models import Job, JobState
    from datetime import datetime, timezone
    job = Job(
        title="Test Event",
        tenant_id=test_tenant.id,
        scheduled_start=datetime(2026, 6, 1, 9, 0, tzinfo=timezone.utc),
        scheduled_end=datetime(2026, 6, 1, 17, 0, tzinfo=timezone.utc),
        state=JobState.ACTIVE,
    )
    test_db.add(job)
    await test_db.flush()
    return job
