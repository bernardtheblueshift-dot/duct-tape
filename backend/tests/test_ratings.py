"""Tests for crew rating system"""

import pytest
from httpx import AsyncClient
from uuid import uuid4


@pytest.mark.asyncio
async def test_rate_crew(
    async_client: AsyncClient, admin_token, test_crew_profile, test_job
):
    """Admin can rate crew member for a job"""
    response = await async_client.post(
        f"/api/v1/crew/{test_crew_profile.id}/ratings",
        params={"job_id": str(test_job.id)},
        json={"stars": 4, "notes": "Great work"},
        cookies={"access_token": admin_token},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["stars"] == 4
    assert data["notes"] == "Great work"
    assert data["crew_id"] == str(test_crew_profile.id)
    assert data["job_id"] == str(test_job.id)


@pytest.mark.asyncio
async def test_rate_crew_updates_average(
    async_client: AsyncClient, admin_token, test_db, test_crew_profile, test_job, test_tenant
):
    """Rating updates cached rating_average on CrewProfile"""
    from app.models import Job, JobState
    from datetime import datetime, timezone

    # Create second job for second rating
    job2 = Job(
        title="Second Event",
        tenant_id=test_tenant.id,
        scheduled_start=datetime(2026, 6, 2, 9, 0, tzinfo=timezone.utc),
        scheduled_end=datetime(2026, 6, 2, 17, 0, tzinfo=timezone.utc),
        state=JobState.ACTIVE,
    )
    test_db.add(job2)
    await test_db.flush()

    # Rate crew 4 stars on first job
    await async_client.post(
        f"/api/v1/crew/{test_crew_profile.id}/ratings",
        params={"job_id": str(test_job.id)},
        json={"stars": 4},
        cookies={"access_token": admin_token},
    )

    # Rate crew 2 stars on second job
    await async_client.post(
        f"/api/v1/crew/{test_crew_profile.id}/ratings",
        params={"job_id": str(job2.id)},
        json={"stars": 2},
        cookies={"access_token": admin_token},
    )

    # Get crew profile and check cached average
    response = await async_client.get(
        f"/api/v1/crew/{test_crew_profile.id}",
        cookies={"access_token": admin_token},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["rating_average"] == 3.0  # (4 + 2) / 2
    assert data["rating_count"] == 2


@pytest.mark.asyncio
async def test_rate_crew_duplicate_rejected(
    async_client: AsyncClient, admin_token, test_crew_profile, test_job
):
    """Cannot rate same crew for same job twice"""
    # First rating
    await async_client.post(
        f"/api/v1/crew/{test_crew_profile.id}/ratings",
        params={"job_id": str(test_job.id)},
        json={"stars": 4},
        cookies={"access_token": admin_token},
    )

    # Duplicate rating
    response = await async_client.post(
        f"/api/v1/crew/{test_crew_profile.id}/ratings",
        params={"job_id": str(test_job.id)},
        json={"stars": 5},
        cookies={"access_token": admin_token},
    )

    assert response.status_code == 409
    assert "already rated" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_rate_crew_invalid_stars(
    async_client: AsyncClient, admin_token, test_crew_profile, test_job
):
    """Rating validation rejects stars outside 1-5 range"""
    # Stars too low
    response = await async_client.post(
        f"/api/v1/crew/{test_crew_profile.id}/ratings",
        params={"job_id": str(test_job.id)},
        json={"stars": 0},
        cookies={"access_token": admin_token},
    )
    assert response.status_code == 422

    # Stars too high
    response = await async_client.post(
        f"/api/v1/crew/{test_crew_profile.id}/ratings",
        params={"job_id": str(test_job.id)},
        json={"stars": 6},
        cookies={"access_token": admin_token},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_list_ratings(
    async_client: AsyncClient, admin_token, test_db, test_crew_profile, test_job, test_tenant
):
    """Can list all ratings for a crew member"""
    from app.models import Job, JobState
    from datetime import datetime, timezone

    # Create 2 more jobs
    job2 = Job(
        title="Event 2",
        tenant_id=test_tenant.id,
        scheduled_start=datetime(2026, 6, 2, 9, 0, tzinfo=timezone.utc),
        scheduled_end=datetime(2026, 6, 2, 17, 0, tzinfo=timezone.utc),
        state=JobState.ACTIVE,
    )
    job3 = Job(
        title="Event 3",
        tenant_id=test_tenant.id,
        scheduled_start=datetime(2026, 6, 3, 9, 0, tzinfo=timezone.utc),
        scheduled_end=datetime(2026, 6, 3, 17, 0, tzinfo=timezone.utc),
        state=JobState.ACTIVE,
    )
    test_db.add_all([job2, job3])
    await test_db.flush()

    # Create 3 ratings
    for job in [test_job, job2, job3]:
        await async_client.post(
            f"/api/v1/crew/{test_crew_profile.id}/ratings",
            params={"job_id": str(job.id)},
            json={"stars": 4},
            cookies={"access_token": admin_token},
        )

    # List ratings
    response = await async_client.get(
        f"/api/v1/crew/{test_crew_profile.id}/ratings",
        cookies={"access_token": admin_token},
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3


@pytest.mark.asyncio
async def test_crew_history(
    async_client: AsyncClient, admin_token, test_db, test_crew_profile, test_job, test_tenant
):
    """Crew job history shows assignments with job details"""
    from app.models import Job, JobState, CrewAssignment, AssignmentState
    from datetime import datetime, timezone

    # Create second job
    job2 = Job(
        title="Second Event",
        tenant_id=test_tenant.id,
        scheduled_start=datetime(2026, 6, 2, 9, 0, tzinfo=timezone.utc),
        scheduled_end=datetime(2026, 6, 2, 17, 0, tzinfo=timezone.utc),
        state=JobState.ACTIVE,
    )
    test_db.add(job2)
    await test_db.flush()

    # Create 2 assignments
    assignment1 = CrewAssignment(
        crew_id=test_crew_profile.id,
        job_id=test_job.id,
        tenant_id=test_tenant.id,
        role="Camera Operator",
        status=AssignmentState.CONFIRMED,
    )
    assignment2 = CrewAssignment(
        crew_id=test_crew_profile.id,
        job_id=job2.id,
        tenant_id=test_tenant.id,
        role="Sound Tech",
        status=AssignmentState.PENDING,
    )
    test_db.add_all([assignment1, assignment2])
    await test_db.flush()

    # Get history
    response = await async_client.get(
        f"/api/v1/crew/{test_crew_profile.id}/history",
        cookies={"access_token": admin_token},
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2

    # Check details
    history_entry = next(e for e in data if e["job_id"] == str(test_job.id))
    assert history_entry["job_title"] == "Test Event"
    assert history_entry["role"] == "Camera Operator"
    assert history_entry["status"] == "confirmed"


@pytest.mark.asyncio
async def test_rate_crew_requires_admin(
    async_client: AsyncClient, crew_token, test_crew_profile, test_job
):
    """Crew users cannot rate (admin only)"""
    response = await async_client.post(
        f"/api/v1/crew/{test_crew_profile.id}/ratings",
        params={"job_id": str(test_job.id)},
        json={"stars": 4},
        cookies={"access_token": crew_token},
    )

    assert response.status_code == 403
