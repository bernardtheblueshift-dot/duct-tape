"""Tests for job state transition endpoint"""

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.job import Job, JobState
from app.models.user import User
import uuid


@pytest_asyncio.fixture
async def intake_job(test_db: AsyncSession, test_tenant) -> Job:
    """Create job in intake state"""
    job = Job(
        id=uuid.uuid4(),
        title="Test Job",
        description="Test description",
        state=JobState.INTAKE,
        tenant_id=test_tenant.id,
    )
    test_db.add(job)
    await test_db.flush()
    return job


@pytest_asyncio.fixture
async def simmer_job(test_db: AsyncSession, test_tenant) -> Job:
    """Create job in simmer state"""
    job = Job(
        id=uuid.uuid4(),
        title="Simmer Job",
        state=JobState.SIMMER,
        tenant_id=test_tenant.id,
    )
    test_db.add(job)
    await test_db.flush()
    return job


@pytest_asyncio.fixture
async def active_job(test_db: AsyncSession, test_tenant) -> Job:
    """Create job in active state"""
    job = Job(
        id=uuid.uuid4(),
        title="Active Job",
        state=JobState.ACTIVE,
        tenant_id=test_tenant.id,
    )
    test_db.add(job)
    await test_db.flush()
    return job


@pytest_asyncio.fixture
async def complete_job(test_db: AsyncSession, test_tenant) -> Job:
    """Create job in complete state"""
    job = Job(
        id=uuid.uuid4(),
        title="Complete Job",
        state=JobState.COMPLETE,
        tenant_id=test_tenant.id,
    )
    test_db.add(job)
    await test_db.flush()
    return job


@pytest.mark.asyncio
async def test_transition_intake_to_simmer(
    async_client: AsyncClient, intake_job: Job, test_admin_user: User, admin_token: str
):
    """Test valid transition from intake to simmer"""
    response = await async_client.post(
        f"/api/v1/jobs/{intake_job.id}/transition",
        json={"new_state": "simmer"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["state"] == "simmer"
    assert data["id"] == str(intake_job.id)


@pytest.mark.asyncio
async def test_transition_intake_to_active(
    async_client: AsyncClient, intake_job: Job, test_admin_user: User, admin_token: str
):
    """Test valid transition from intake to active"""
    response = await async_client.post(
        f"/api/v1/jobs/{intake_job.id}/transition",
        json={"new_state": "active"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["state"] == "active"


@pytest.mark.asyncio
async def test_transition_simmer_to_active(
    async_client: AsyncClient, simmer_job: Job, test_admin_user: User, admin_token: str
):
    """Test valid transition from simmer to active"""
    response = await async_client.post(
        f"/api/v1/jobs/{simmer_job.id}/transition",
        json={"new_state": "active"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["state"] == "active"


@pytest.mark.asyncio
async def test_transition_simmer_to_intake(
    async_client: AsyncClient, simmer_job: Job, test_admin_user: User, admin_token: str
):
    """Test backward transition from simmer to intake"""
    response = await async_client.post(
        f"/api/v1/jobs/{simmer_job.id}/transition",
        json={"new_state": "intake"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["state"] == "intake"


@pytest.mark.asyncio
async def test_transition_active_to_complete(
    async_client: AsyncClient, active_job: Job, test_admin_user: User, admin_token: str
):
    """Test valid transition from active to complete"""
    response = await async_client.post(
        f"/api/v1/jobs/{active_job.id}/transition",
        json={"new_state": "complete"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["state"] == "complete"


@pytest.mark.asyncio
async def test_transition_active_to_simmer(
    async_client: AsyncClient, active_job: Job, test_admin_user: User, admin_token: str
):
    """Test backward transition from active to simmer"""
    response = await async_client.post(
        f"/api/v1/jobs/{active_job.id}/transition",
        json={"new_state": "simmer"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["state"] == "simmer"


@pytest.mark.asyncio
async def test_transition_invalid_blocked(
    async_client: AsyncClient, intake_job: Job, test_admin_user: User, admin_token: str
):
    """Test invalid transition (intake to complete) is blocked"""
    response = await async_client.post(
        f"/api/v1/jobs/{intake_job.id}/transition",
        json={"new_state": "complete"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 400
    assert "Invalid transition" in response.json()["detail"]


@pytest.mark.asyncio
async def test_transition_from_complete_blocked(
    async_client: AsyncClient,
    complete_job: Job,
    test_admin_user: User,
    admin_token: str,
):
    """Test that complete state is terminal (no transitions allowed)"""
    response = await async_client.post(
        f"/api/v1/jobs/{complete_job.id}/transition",
        json={"new_state": "intake"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 400
    assert "Invalid transition" in response.json()["detail"]


@pytest.mark.asyncio
async def test_transition_as_crew_forbidden(
    async_client: AsyncClient, intake_job: Job, test_crew_user: User, crew_token: str
):
    """Test that crew users cannot transition jobs (admin-only)"""
    response = await async_client.post(
        f"/api/v1/jobs/{intake_job.id}/transition",
        json={"new_state": "simmer"},
        headers={"Authorization": f"Bearer {crew_token}"},
    )
    assert response.status_code == 403
    assert "Admin access required" in response.json()["detail"]


@pytest.mark.asyncio
async def test_transition_nonexistent_job_404(
    async_client: AsyncClient, test_admin_user: User, admin_token: str
):
    """Test that transitioning nonexistent job returns 404"""
    fake_id = uuid.uuid4()
    response = await async_client.post(
        f"/api/v1/jobs/{fake_id}/transition",
        json={"new_state": "simmer"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 404
    assert "Job not found" in response.json()["detail"]


@pytest.mark.asyncio
async def test_transition_updates_updated_at_timestamp(
    async_client: AsyncClient,
    intake_job: Job,
    test_admin_user: User,
    admin_token: str,
    test_db: AsyncSession,
):
    """Test that transitioning updates the updated_at timestamp"""
    original_updated_at = intake_job.updated_at

    response = await async_client.post(
        f"/api/v1/jobs/{intake_job.id}/transition",
        json={"new_state": "simmer"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()

    # Refresh job from database
    await test_db.refresh(intake_job)
    assert intake_job.updated_at > original_updated_at
