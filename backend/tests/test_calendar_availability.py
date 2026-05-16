"""Tests for crew availability endpoints"""

import pytest
from httpx import AsyncClient
from datetime import datetime, timezone
from sqlalchemy import text
from app.models import (
    Job,
    JobState,
    CrewAssignment,
    AssignmentState,
    AvailabilityPattern,
    CrewProfile,
    User,
    UserRole,
)
from app.core.security import hash_password


@pytest.mark.asyncio
async def test_crew_availability_free_days(
    async_client: AsyncClient,
    admin_token: str,
    test_db,
    test_tenant,
    test_crew_profile,
):
    """Crew with no patterns or assignments shows all free days"""
    await test_db.execute(
        text(f"SET LOCAL app.current_tenant_id = '{test_tenant.id}'")
    )

    response = await async_client.get(
        f"/api/v1/calendar/crew/{test_crew_profile.id}/availability?start=2026-06-01T00:00:00Z&end=2026-06-07T00:00:00Z",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 7
    assert all(day["status"] == "free" for day in data)
    assert data[0]["date"] == "2026-06-01"
    assert data[6]["date"] == "2026-06-07"


@pytest.mark.asyncio
async def test_crew_availability_unavailable_from_pattern(
    async_client: AsyncClient,
    admin_token: str,
    test_db,
    test_tenant,
    test_crew_profile,
):
    """Availability pattern marks days as unavailable"""
    await test_db.execute(
        text(f"SET LOCAL app.current_tenant_id = '{test_tenant.id}'")
    )

    # Create unavailable pattern for Sunday (weekday=6)
    pattern = AvailabilityPattern(
        crew_id=test_crew_profile.id,
        tenant_id=test_tenant.id,
        day_of_week=6,
        is_available=False,
    )
    test_db.add(pattern)
    await test_db.flush()

    # 2026-06-01 is Sunday
    response = await async_client.get(
        f"/api/v1/calendar/crew/{test_crew_profile.id}/availability?start=2026-06-01T00:00:00Z&end=2026-06-07T00:00:00Z",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 7
    # Sunday (2026-06-01) should be unavailable
    assert data[0]["date"] == "2026-06-01"
    assert data[0]["status"] == "unavailable"
    # Other days should be free
    assert all(day["status"] == "free" for day in data[1:])


@pytest.mark.asyncio
async def test_crew_availability_booked_from_assignment(
    async_client: AsyncClient,
    admin_token: str,
    test_db,
    test_tenant,
    test_crew_profile,
):
    """CONFIRMED assignments mark days as booked"""
    await test_db.execute(
        text(f"SET LOCAL app.current_tenant_id = '{test_tenant.id}'")
    )

    # Create job spanning 2026-06-03 to 2026-06-04
    job = Job(
        title="Test Job",
        tenant_id=test_tenant.id,
        scheduled_start=datetime(2026, 6, 3, 9, 0, tzinfo=timezone.utc),
        scheduled_end=datetime(2026, 6, 4, 17, 0, tzinfo=timezone.utc),
        state=JobState.ACTIVE,
    )
    test_db.add(job)
    await test_db.flush()

    # Create CONFIRMED assignment
    assignment = CrewAssignment(
        crew_id=test_crew_profile.id,
        job_id=job.id,
        tenant_id=test_tenant.id,
        role="Camera Operator",
        status=AssignmentState.CONFIRMED,
    )
    test_db.add(assignment)
    await test_db.flush()

    response = await async_client.get(
        f"/api/v1/calendar/crew/{test_crew_profile.id}/availability?start=2026-06-01T00:00:00Z&end=2026-06-07T00:00:00Z",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 7
    # June 3 and 4 should be booked
    assert data[2]["date"] == "2026-06-03"
    assert data[2]["status"] == "booked"
    assert data[3]["date"] == "2026-06-04"
    assert data[3]["status"] == "booked"
    # Other days should be free
    assert data[0]["status"] == "free"
    assert data[1]["status"] == "free"
    assert data[4]["status"] == "free"


@pytest.mark.asyncio
async def test_crew_availability_pending_not_booked(
    async_client: AsyncClient,
    admin_token: str,
    test_db,
    test_tenant,
    test_crew_profile,
):
    """PENDING assignments do not mark days as booked"""
    await test_db.execute(
        text(f"SET LOCAL app.current_tenant_id = '{test_tenant.id}'")
    )

    # Create job
    job = Job(
        title="Test Job",
        tenant_id=test_tenant.id,
        scheduled_start=datetime(2026, 6, 3, 9, 0, tzinfo=timezone.utc),
        scheduled_end=datetime(2026, 6, 4, 17, 0, tzinfo=timezone.utc),
        state=JobState.ACTIVE,
    )
    test_db.add(job)
    await test_db.flush()

    # Create PENDING assignment (default status)
    assignment = CrewAssignment(
        crew_id=test_crew_profile.id,
        job_id=job.id,
        tenant_id=test_tenant.id,
        role="Camera Operator",
        status=AssignmentState.PENDING,
    )
    test_db.add(assignment)
    await test_db.flush()

    response = await async_client.get(
        f"/api/v1/calendar/crew/{test_crew_profile.id}/availability?start=2026-06-01T00:00:00Z&end=2026-06-07T00:00:00Z",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 7
    # All days should be free (PENDING does not count as booked)
    assert all(day["status"] == "free" for day in data)


@pytest.mark.asyncio
async def test_crew_availability_combined_statuses(
    async_client: AsyncClient,
    admin_token: str,
    test_db,
    test_tenant,
    test_crew_profile,
):
    """Combined unavailable pattern + confirmed assignment shows correct priority"""
    await test_db.execute(
        text(f"SET LOCAL app.current_tenant_id = '{test_tenant.id}'")
    )

    # Create unavailable pattern for Sunday (weekday=6)
    pattern = AvailabilityPattern(
        crew_id=test_crew_profile.id,
        tenant_id=test_tenant.id,
        day_of_week=6,
        is_available=False,
    )
    test_db.add(pattern)

    # Create job on Wed-Thu (2026-06-04 to 2026-06-05)
    job = Job(
        title="Test Job",
        tenant_id=test_tenant.id,
        scheduled_start=datetime(2026, 6, 4, 9, 0, tzinfo=timezone.utc),
        scheduled_end=datetime(2026, 6, 5, 17, 0, tzinfo=timezone.utc),
        state=JobState.ACTIVE,
    )
    test_db.add(job)
    await test_db.flush()

    assignment = CrewAssignment(
        crew_id=test_crew_profile.id,
        job_id=job.id,
        tenant_id=test_tenant.id,
        status=AssignmentState.CONFIRMED,
    )
    test_db.add(assignment)
    await test_db.flush()

    response = await async_client.get(
        f"/api/v1/calendar/crew/{test_crew_profile.id}/availability?start=2026-06-01T00:00:00Z&end=2026-06-07T00:00:00Z",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 7
    # Sunday (2026-06-01) should be unavailable
    assert data[0]["date"] == "2026-06-01"
    assert data[0]["status"] == "unavailable"
    # Wed-Thu should be booked
    assert data[3]["date"] == "2026-06-04"
    assert data[3]["status"] == "booked"
    assert data[4]["date"] == "2026-06-05"
    assert data[4]["status"] == "booked"
    # Other days should be free
    assert data[1]["status"] == "free"
    assert data[2]["status"] == "free"
    assert data[5]["status"] == "free"
    assert data[6]["status"] == "free"


@pytest.mark.asyncio
async def test_bulk_availability_admin_only(
    async_client: AsyncClient,
    crew_token: str,
    admin_token: str,
    test_db,
    test_tenant,
):
    """Bulk availability endpoint requires admin role"""
    await test_db.execute(
        text(f"SET LOCAL app.current_tenant_id = '{test_tenant.id}'")
    )

    # Try with crew token (non-admin)
    response = await async_client.get(
        "/api/v1/calendar/availability?start=2026-06-01T00:00:00Z&end=2026-06-07T00:00:00Z",
        headers={"Authorization": f"Bearer {crew_token}"},
    )
    assert response.status_code == 403

    # Try with admin token
    response = await async_client.get(
        "/api/v1/calendar/availability?start=2026-06-01T00:00:00Z&end=2026-06-07T00:00:00Z",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_bulk_availability_returns_all_crew(
    async_client: AsyncClient,
    admin_token: str,
    test_db,
    test_tenant,
    test_crew_profile,
):
    """Bulk availability returns all active crew members"""
    await test_db.execute(
        text(f"SET LOCAL app.current_tenant_id = '{test_tenant.id}'")
    )

    # Create second crew member
    user2 = User(
        email="crew2@test.com",
        hashed_password=hash_password("password123"),
        tenant_id=test_tenant.id,
        role=UserRole.CREW,
        is_active=True,
    )
    test_db.add(user2)
    await test_db.flush()

    profile2 = CrewProfile(
        user_id=user2.id,
        tenant_id=test_tenant.id,
    )
    test_db.add(profile2)
    await test_db.flush()

    response = await async_client.get(
        "/api/v1/calendar/availability?start=2026-06-01T00:00:00Z&end=2026-06-07T00:00:00Z",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    # Check both crew members returned with correct fields
    crew_ids = {str(c["crew_id"]) for c in data}
    assert str(test_crew_profile.id) in crew_ids
    assert str(profile2.id) in crew_ids
    # Each should have crew_name and days
    for crew in data:
        assert "crew_name" in crew
        assert "days" in crew
        assert len(crew["days"]) == 7


@pytest.mark.asyncio
async def test_bulk_availability_excludes_archived(
    async_client: AsyncClient,
    admin_token: str,
    test_db,
    test_tenant,
    test_crew_profile,
):
    """Bulk availability excludes archived crew members"""
    await test_db.execute(
        text(f"SET LOCAL app.current_tenant_id = '{test_tenant.id}'")
    )

    # Create second crew member and archive them
    user2 = User(
        email="archived@test.com",
        hashed_password=hash_password("password123"),
        tenant_id=test_tenant.id,
        role=UserRole.CREW,
        is_active=True,
    )
    test_db.add(user2)
    await test_db.flush()

    profile2 = CrewProfile(
        user_id=user2.id,
        tenant_id=test_tenant.id,
        archived_at=datetime(2026, 5, 1, 0, 0, tzinfo=timezone.utc),
    )
    test_db.add(profile2)
    await test_db.flush()

    response = await async_client.get(
        "/api/v1/calendar/availability?start=2026-06-01T00:00:00Z&end=2026-06-07T00:00:00Z",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    # Should only have 1 crew member (not the archived one)
    assert len(data) == 1
    assert str(data[0]["crew_id"]) == str(test_crew_profile.id)


@pytest.mark.asyncio
async def test_availability_date_range_validation(
    async_client: AsyncClient,
    admin_token: str,
    test_db,
    test_tenant,
):
    """Availability endpoints reject date ranges > 365 days"""
    await test_db.execute(
        text(f"SET LOCAL app.current_tenant_id = '{test_tenant.id}'")
    )

    # Try range > 365 days
    response = await async_client.get(
        "/api/v1/calendar/availability?start=2026-01-01T00:00:00Z&end=2027-12-31T00:00:00Z",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 400
    assert "too large" in response.json()["detail"].lower()
