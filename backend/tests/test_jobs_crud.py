"""Tests for job CRUD endpoints"""

import pytest
from httpx import AsyncClient
from datetime import datetime, timedelta, timezone
from app.models.job import Job, JobState
from app.models.user import User, UserRole
from app.models.tenant import Tenant
from app.core.security import create_access_token


@pytest.mark.asyncio
async def test_create_job_as_admin(async_client: AsyncClient, admin_token: str):
    """Admin can create job with valid data"""
    response = await async_client.post(
        "/api/v1/jobs/",
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
        "/api/v1/jobs/",
        json={"title": "Test Job"},
        headers={"Authorization": f"Bearer {crew_token}"},
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_list_jobs_empty(async_client: AsyncClient, admin_token: str):
    """List jobs returns empty array when no jobs exist"""
    response = await async_client.get(
        "/api/v1/jobs/",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_list_jobs_with_data(
    async_client: AsyncClient, admin_token: str, test_db, test_admin_user
):
    """List jobs returns all jobs for tenant"""
    from sqlalchemy import text

    # Set RLS context
    await test_db.execute(
        text(f"SET LOCAL app.current_tenant_id = '{test_admin_user.tenant_id}'")
    )

    # Create jobs using test_db fixture session
    job1 = Job(
        title="Job 1",
        tenant_id=test_admin_user.tenant_id,
        scheduled_start=datetime(2026, 6, 1, 9, 0, tzinfo=timezone.utc),
    )
    job2 = Job(
        title="Job 2",
        tenant_id=test_admin_user.tenant_id,
        scheduled_start=datetime(2026, 6, 2, 9, 0, tzinfo=timezone.utc),
    )
    test_db.add(job1)
    test_db.add(job2)
    await test_db.commit()

    response = await async_client.get(
        "/api/v1/jobs/",
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
    async_client: AsyncClient, admin_token: str, test_db, test_admin_user
):
    """Search jobs by title using ILIKE"""
    from sqlalchemy import text

    await test_db.execute(
        text(f"SET LOCAL app.current_tenant_id = '{test_admin_user.tenant_id}'")
    )

    job1 = Job(title="Corporate Event", tenant_id=test_admin_user.tenant_id)
    job2 = Job(title="Wedding Reception", tenant_id=test_admin_user.tenant_id)
    test_db.add_all([job1, job2])
    await test_db.commit()

    response = await async_client.get(
        "/api/v1/jobs/?search=corporate",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "Corporate Event"


@pytest.mark.asyncio
async def test_filter_jobs_by_state(
    async_client: AsyncClient, admin_token: str, test_db, test_admin_user
):
    """Filter jobs by state"""
    from sqlalchemy import text

    await test_db.execute(
        text(f"SET LOCAL app.current_tenant_id = '{test_admin_user.tenant_id}'")
    )

    job1 = Job(title="Job 1", state=JobState.INTAKE, tenant_id=test_admin_user.tenant_id)
    job2 = Job(title="Job 2", state=JobState.ACTIVE, tenant_id=test_admin_user.tenant_id)
    test_db.add_all([job1, job2])
    await test_db.commit()

    response = await async_client.get(
        "/api/v1/jobs/?state=active",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "Job 2"
    assert data[0]["state"] == "active"


@pytest.mark.asyncio
async def test_filter_jobs_by_date_range(
    async_client: AsyncClient, admin_token: str, test_db, test_admin_user
):
    """Filter jobs by date range"""
    from sqlalchemy import text

    await test_db.execute(
        text(f"SET LOCAL app.current_tenant_id = '{test_admin_user.tenant_id}'")
    )

    job1 = Job(
        title="Past Job",
        scheduled_start=datetime(2026, 5, 1, tzinfo=timezone.utc),
        tenant_id=test_admin_user.tenant_id,
    )
    job2 = Job(
        title="Future Job",
        scheduled_start=datetime(2026, 7, 1, tzinfo=timezone.utc),
        tenant_id=test_admin_user.tenant_id,
    )
    test_db.add_all([job1, job2])
    await test_db.commit()

    response = await async_client.get(
        "/api/v1/jobs/?start_date=2026-06-01T00:00:00Z",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "Future Job"


@pytest.mark.asyncio
async def test_get_job_by_id(
    async_client: AsyncClient, admin_token: str, test_db, test_admin_user
):
    """Get single job by ID"""
    from sqlalchemy import text

    await test_db.execute(
        text(f"SET LOCAL app.current_tenant_id = '{test_admin_user.tenant_id}'")
    )

    job = Job(title="Test Job", tenant_id=test_admin_user.tenant_id)
    test_db.add(job)
    await test_db.commit()
    await test_db.refresh(job)
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
    async_client: AsyncClient, admin_token: str, test_db, test_admin_user
):
    """Admin can update job fields"""
    from sqlalchemy import text

    await test_db.execute(
        text(f"SET LOCAL app.current_tenant_id = '{test_admin_user.tenant_id}'")
    )

    job = Job(title="Original Title", tenant_id=test_admin_user.tenant_id)
    test_db.add(job)
    await test_db.commit()
    await test_db.refresh(job)
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
    async_client: AsyncClient, admin_token: str, test_db, test_admin_user
):
    """Admin can delete jobs"""
    from sqlalchemy import text

    await test_db.execute(
        text(f"SET LOCAL app.current_tenant_id = '{test_admin_user.tenant_id}'")
    )

    job = Job(title="Job to Delete", tenant_id=test_admin_user.tenant_id)
    test_db.add(job)
    await test_db.commit()
    await test_db.refresh(job)
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
    from sqlalchemy import text

    # Create two tenants with jobs
    tenant1 = Tenant(name="Tenant 1")
    tenant2 = Tenant(name="Tenant 2")
    test_db.add_all([tenant1, tenant2])
    await test_db.flush()

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
    test_db.add_all([user1, user2])
    await test_db.flush()

    # Create jobs for each tenant
    job1 = Job(title="Tenant 1 Job", tenant_id=tenant1.id)
    job2 = Job(title="Tenant 2 Job", tenant_id=tenant2.id)
    test_db.add_all([job1, job2])
    await test_db.commit()

    user1_id = str(user1.id)
    tenant1_id = str(tenant1.id)

    # Enable RLS on jobs table AFTER data is inserted
    await test_db.execute(text("ALTER TABLE jobs ENABLE ROW LEVEL SECURITY"))
    await test_db.execute(text(
        "CREATE POLICY tenant_isolation ON jobs "
        "USING (tenant_id::text = current_setting('app.current_tenant_id', TRUE))"
    ))
    await test_db.execute(text("ALTER TABLE jobs FORCE ROW LEVEL SECURITY"))

    # Create token for tenant 1
    token1 = create_access_token(user1_id, tenant1_id, "admin")

    # Tenant 1 should only see their job
    response = await async_client.get(
        "/api/v1/jobs/",
        headers={"Authorization": f"Bearer {token1}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "Tenant 1 Job"
