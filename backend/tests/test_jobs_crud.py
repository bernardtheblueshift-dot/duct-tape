"""Tests for job CRUD endpoints"""

import pytest
from httpx import AsyncClient
from datetime import datetime, timedelta
from app.models.job import Job, JobState
from app.models.user import User, UserRole
from app.models.tenant import Tenant


@pytest.mark.asyncio
async def test_create_job_as_admin(async_client: AsyncClient, admin_token: str):
    """Admin can create job with valid data"""
    response = await async_client.post(
        "/api/v1/jobs",
        json={
            "title": "Corporate Event",
            "description": "Annual company meeting",
            "venue": "Grand Ballroom",
            "scheduled_start": "2026-06-01T09:00:00Z",
            "scheduled_end": "2026-06-01T17:00:00Z",
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Corporate Event"
    assert data["description"] == "Annual company meeting"
    assert data["venue"] == "Grand Ballroom"
    assert data["state"] == "intake"
    assert "id" in data
    assert "created_at" in data


@pytest.mark.asyncio
async def test_create_job_as_crew_forbidden(async_client: AsyncClient, crew_token: str):
    """Crew user cannot create jobs"""
    response = await async_client.post(
        "/api/v1/jobs",
        json={"title": "Test Job"},
        headers={"Authorization": f"Bearer {crew_token}"},
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_list_jobs_empty(async_client: AsyncClient, admin_token: str):
    """List jobs returns empty array when no jobs exist"""
    response = await async_client.get(
        "/api/v1/jobs",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_list_jobs_with_data(
    async_client: AsyncClient, admin_token: str, test_db
):
    """List jobs returns all jobs for tenant"""
    # Create test jobs directly in database
    from sqlalchemy import select
    from app.database import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        # Get tenant from admin token
        result = await db.execute(select(User).where(User.email == "admin@test.com"))
        admin_user = result.scalar_one()

        # Set RLS context
        from sqlalchemy import text

        await db.execute(
            text(f"SET LOCAL app.current_tenant_id = '{admin_user.tenant_id}'")
        )

        # Create jobs
        job1 = Job(
            title="Job 1",
            tenant_id=admin_user.tenant_id,
            scheduled_start=datetime(2026, 6, 1, 9, 0),
        )
        job2 = Job(
            title="Job 2",
            tenant_id=admin_user.tenant_id,
            scheduled_start=datetime(2026, 6, 2, 9, 0),
        )
        db.add(job1)
        db.add(job2)
        await db.commit()

    response = await async_client.get(
        "/api/v1/jobs",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    # Should be ordered by scheduled_start desc (most recent first)
    assert data[0]["title"] == "Job 2"
    assert data[1]["title"] == "Job 1"


@pytest.mark.asyncio
async def test_search_jobs_by_title(
    async_client: AsyncClient, admin_token: str, test_db
):
    """Search jobs by title using ILIKE"""
    from sqlalchemy import select, text
    from app.database import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.email == "admin@test.com"))
        admin_user = result.scalar_one()
        await db.execute(
            text(f"SET LOCAL app.current_tenant_id = '{admin_user.tenant_id}'")
        )

        job1 = Job(title="Corporate Event", tenant_id=admin_user.tenant_id)
        job2 = Job(title="Wedding Reception", tenant_id=admin_user.tenant_id)
        db.add_all([job1, job2])
        await db.commit()

    response = await async_client.get(
        "/api/v1/jobs?search=corporate",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "Corporate Event"


@pytest.mark.asyncio
async def test_filter_jobs_by_state(
    async_client: AsyncClient, admin_token: str, test_db
):
    """Filter jobs by state"""
    from sqlalchemy import select, text
    from app.database import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.email == "admin@test.com"))
        admin_user = result.scalar_one()
        await db.execute(
            text(f"SET LOCAL app.current_tenant_id = '{admin_user.tenant_id}'")
        )

        job1 = Job(title="Job 1", state=JobState.INTAKE, tenant_id=admin_user.tenant_id)
        job2 = Job(title="Job 2", state=JobState.ACTIVE, tenant_id=admin_user.tenant_id)
        db.add_all([job1, job2])
        await db.commit()

    response = await async_client.get(
        "/api/v1/jobs?state=active",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "Job 2"
    assert data[0]["state"] == "active"


@pytest.mark.asyncio
async def test_filter_jobs_by_date_range(
    async_client: AsyncClient, admin_token: str, test_db
):
    """Filter jobs by date range"""
    from sqlalchemy import select, text
    from app.database import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.email == "admin@test.com"))
        admin_user = result.scalar_one()
        await db.execute(
            text(f"SET LOCAL app.current_tenant_id = '{admin_user.tenant_id}'")
        )

        job1 = Job(
            title="Past Job",
            scheduled_start=datetime(2026, 5, 1),
            tenant_id=admin_user.tenant_id,
        )
        job2 = Job(
            title="Future Job",
            scheduled_start=datetime(2026, 7, 1),
            tenant_id=admin_user.tenant_id,
        )
        db.add_all([job1, job2])
        await db.commit()

    response = await async_client.get(
        "/api/v1/jobs?start_date=2026-06-01T00:00:00Z",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "Future Job"


@pytest.mark.asyncio
async def test_get_job_by_id(async_client: AsyncClient, admin_token: str, test_db):
    """Get single job by ID"""
    from sqlalchemy import select, text
    from app.database import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.email == "admin@test.com"))
        admin_user = result.scalar_one()
        await db.execute(
            text(f"SET LOCAL app.current_tenant_id = '{admin_user.tenant_id}'")
        )

        job = Job(title="Test Job", tenant_id=admin_user.tenant_id)
        db.add(job)
        await db.commit()
        await db.refresh(job)
        job_id = str(job.id)

    response = await async_client.get(
        f"/api/v1/jobs/{job_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == job_id
    assert data["title"] == "Test Job"
    # Check placeholder sections exist
    assert data["assigned_crew"] == []
    assert data["assigned_gear"] == []
    assert data["messages"] == []
    assert data["tasks"] == []
    assert data["files"] == []


@pytest.mark.asyncio
async def test_get_job_not_found(async_client: AsyncClient, admin_token: str):
    """Get non-existent job returns 404"""
    response = await async_client.get(
        "/api/v1/jobs/00000000-0000-0000-0000-000000000000",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_job_as_admin(
    async_client: AsyncClient, admin_token: str, test_db
):
    """Admin can update job fields"""
    from sqlalchemy import select, text
    from app.database import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.email == "admin@test.com"))
        admin_user = result.scalar_one()
        await db.execute(
            text(f"SET LOCAL app.current_tenant_id = '{admin_user.tenant_id}'")
        )

        job = Job(title="Original Title", tenant_id=admin_user.tenant_id)
        db.add(job)
        await db.commit()
        await db.refresh(job)
        job_id = str(job.id)

    response = await async_client.patch(
        f"/api/v1/jobs/{job_id}",
        json={
            "title": "Updated Title",
            "venue": "New Venue",
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Title"
    assert data["venue"] == "New Venue"


@pytest.mark.asyncio
async def test_delete_job_as_admin(
    async_client: AsyncClient, admin_token: str, test_db
):
    """Admin can delete jobs"""
    from sqlalchemy import select, text
    from app.database import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.email == "admin@test.com"))
        admin_user = result.scalar_one()
        await db.execute(
            text(f"SET LOCAL app.current_tenant_id = '{admin_user.tenant_id}'")
        )

        job = Job(title="Job to Delete", tenant_id=admin_user.tenant_id)
        db.add(job)
        await db.commit()
        await db.refresh(job)
        job_id = str(job.id)

    response = await async_client.delete(
        f"/api/v1/jobs/{job_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 204

    # Verify job is deleted
    response = await async_client.get(
        f"/api/v1/jobs/{job_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_tenant_isolation(async_client: AsyncClient, test_db):
    """Jobs are isolated by tenant via RLS"""
    from sqlalchemy import select, text
    from app.database import AsyncSessionLocal
    from app.core.security import create_access_token

    # Create two tenants with jobs
    async with AsyncSessionLocal() as db:
        tenant1 = Tenant(name="Tenant 1")
        tenant2 = Tenant(name="Tenant 2")
        db.add_all([tenant1, tenant2])
        await db.flush()

        user1 = User(
            email="user1@test.com",
            hashed_password="fake",
            tenant_id=tenant1.id,
            role=UserRole.ADMIN,
            is_active=True,
        )
        user2 = User(
            email="user2@test.com",
            hashed_password="fake",
            tenant_id=tenant2.id,
            role=UserRole.ADMIN,
            is_active=True,
        )
        db.add_all([user1, user2])
        await db.flush()

        # Create jobs for each tenant
        await db.execute(text(f"SET LOCAL app.current_tenant_id = '{tenant1.id}'"))
        job1 = Job(title="Tenant 1 Job", tenant_id=tenant1.id)
        db.add(job1)

        await db.execute(text(f"SET LOCAL app.current_tenant_id = '{tenant2.id}'"))
        job2 = Job(title="Tenant 2 Job", tenant_id=tenant2.id)
        db.add(job2)

        await db.commit()

        user1_id = str(user1.id)
        tenant1_id = str(tenant1.id)

    # Create token for tenant 1
    token1 = create_access_token(user1_id, tenant1_id, "admin")

    # Tenant 1 should only see their job
    response = await async_client.get(
        "/api/v1/jobs",
        headers={"Authorization": f"Bearer {token1}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "Tenant 1 Job"
