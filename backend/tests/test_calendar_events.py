"""Tests for calendar events endpoints"""

import pytest
from httpx import AsyncClient
from datetime import datetime, timezone
from sqlalchemy import text
from app.models import (
    Job,
    JobState,
    CrewAssignment,
    EquipmentAssignment,
    AssignmentState,
    Equipment,
    EquipmentCondition,
    CrewProfile,
)


@pytest.mark.asyncio
async def test_get_events_returns_jobs_in_range(
    async_client: AsyncClient,
    admin_token: str,
    test_db,
    test_tenant,
):
    """Calendar events endpoint returns only jobs within date range"""
    await test_db.execute(
        text(f"SET LOCAL app.current_tenant_id = '{test_tenant.id}'")
    )

    # Create 3 jobs: one in range, one before, one after
    job_in_range = Job(
        title="In Range Job",
        tenant_id=test_tenant.id,
        scheduled_start=datetime(2026, 6, 15, 9, 0, tzinfo=timezone.utc),
        scheduled_end=datetime(2026, 6, 15, 17, 0, tzinfo=timezone.utc),
        state=JobState.ACTIVE,
    )
    job_before = Job(
        title="Before Range Job",
        tenant_id=test_tenant.id,
        scheduled_start=datetime(2026, 5, 1, 9, 0, tzinfo=timezone.utc),
        scheduled_end=datetime(2026, 5, 1, 17, 0, tzinfo=timezone.utc),
        state=JobState.COMPLETE,
    )
    job_after = Job(
        title="After Range Job",
        tenant_id=test_tenant.id,
        scheduled_start=datetime(2026, 7, 1, 9, 0, tzinfo=timezone.utc),
        scheduled_end=datetime(2026, 7, 1, 17, 0, tzinfo=timezone.utc),
        state=JobState.INTAKE,
    )
    test_db.add_all([job_in_range, job_before, job_after])
    await test_db.flush()

    response = await async_client.get(
        "/api/v1/calendar/events?start=2026-06-01T00:00:00Z&end=2026-06-30T00:00:00Z",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 1
    assert len(data["events"]) == 1
    assert data["events"][0]["title"] == "In Range Job"
    assert data["events"][0]["event_type"] == "job"
    assert data["events"][0]["color"] == "#10B981"  # active state color
    assert data["events"][0]["status"] == "active"


@pytest.mark.asyncio
async def test_get_events_excludes_unscheduled_jobs(
    async_client: AsyncClient,
    admin_token: str,
    test_db,
    test_tenant,
):
    """Calendar events exclude jobs without scheduled times"""
    await test_db.execute(
        text(f"SET LOCAL app.current_tenant_id = '{test_tenant.id}'")
    )

    # Create job with no scheduled_start
    unscheduled_job = Job(
        title="Unscheduled Job",
        tenant_id=test_tenant.id,
        scheduled_start=None,
        scheduled_end=None,
        state=JobState.INTAKE,
    )
    test_db.add(unscheduled_job)
    await test_db.flush()

    response = await async_client.get(
        "/api/v1/calendar/events?start=2020-01-01T00:00:00Z&end=2027-12-31T00:00:00Z",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 0
    assert len(data["events"]) == 0


@pytest.mark.asyncio
async def test_get_events_includes_crew_assignments(
    async_client: AsyncClient,
    admin_token: str,
    test_db,
    test_tenant,
    test_crew_profile,
):
    """Calendar events include crew assignments with job details"""
    await test_db.execute(
        text(f"SET LOCAL app.current_tenant_id = '{test_tenant.id}'")
    )

    # Create job
    job = Job(
        title="Production Shoot",
        tenant_id=test_tenant.id,
        scheduled_start=datetime(2026, 6, 10, 9, 0, tzinfo=timezone.utc),
        scheduled_end=datetime(2026, 6, 10, 17, 0, tzinfo=timezone.utc),
        state=JobState.ACTIVE,
    )
    test_db.add(job)
    await test_db.flush()

    # Create crew assignment
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
        "/api/v1/calendar/events?start=2026-06-01T00:00:00Z&end=2026-06-30T00:00:00Z",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 2  # job + crew assignment

    # Find crew assignment event
    crew_event = next(e for e in data["events"] if e["event_type"] == "crew_assignment")
    assert crew_event["title"] == "Camera Operator - Production Shoot"
    assert crew_event["status"] == "confirmed"
    assert crew_event["resource_name"] == "crew@test.com"
    assert crew_event["role"] == "Camera Operator"
    assert crew_event["job_title"] == "Production Shoot"


@pytest.mark.asyncio
async def test_get_events_includes_equipment_assignments(
    async_client: AsyncClient,
    admin_token: str,
    test_db,
    test_tenant,
):
    """Calendar events include equipment assignments"""
    await test_db.execute(
        text(f"SET LOCAL app.current_tenant_id = '{test_tenant.id}'")
    )

    # Create job
    job = Job(
        title="Corporate Video",
        tenant_id=test_tenant.id,
        scheduled_start=datetime(2026, 6, 12, 9, 0, tzinfo=timezone.utc),
        scheduled_end=datetime(2026, 6, 12, 17, 0, tzinfo=timezone.utc),
        state=JobState.ACTIVE,
    )
    test_db.add(job)
    await test_db.flush()

    # Create equipment
    equipment = Equipment(
        name="Sony FX6",
        tenant_id=test_tenant.id,
        category="Camera",
        quantity=2,
        condition=EquipmentCondition.GOOD,
    )
    test_db.add(equipment)
    await test_db.flush()

    # Create equipment assignment
    assignment = EquipmentAssignment(
        equipment_id=equipment.id,
        job_id=job.id,
        tenant_id=test_tenant.id,
        quantity_assigned=1,
    )
    test_db.add(assignment)
    await test_db.flush()

    response = await async_client.get(
        "/api/v1/calendar/events?start=2026-06-01T00:00:00Z&end=2026-06-30T00:00:00Z",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 2  # job + equipment assignment

    # Find equipment assignment event
    equip_event = next(e for e in data["events"] if e["event_type"] == "equipment_assignment")
    assert equip_event["title"] == "Sony FX6 - Corporate Video"
    assert equip_event["status"] == "assigned"
    assert equip_event["resource_name"] == "Sony FX6"
    assert equip_event["job_title"] == "Corporate Video"


@pytest.mark.asyncio
async def test_get_events_date_range_too_large(
    async_client: AsyncClient,
    admin_token: str,
):
    """Calendar events reject date ranges exceeding 365 days"""
    response = await async_client.get(
        "/api/v1/calendar/events?start=2020-01-01T00:00:00Z&end=2026-01-01T00:00:00Z",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 400
    assert "Date range too large" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_events_requires_auth(async_client: AsyncClient):
    """Calendar events require authentication"""
    response = await async_client.get(
        "/api/v1/calendar/events?start=2026-06-01T00:00:00Z&end=2026-06-30T00:00:00Z",
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_crew_calendar(
    async_client: AsyncClient,
    admin_token: str,
    test_db,
    test_tenant,
    test_crew_profile,
    test_crew_user,
):
    """Crew calendar endpoint returns only that crew's assignments"""
    await test_db.execute(
        text(f"SET LOCAL app.current_tenant_id = '{test_tenant.id}'")
    )

    # Create another crew member
    from app.models import User, UserRole
    other_user = User(
        email="other@test.com",
        hashed_password="hashed",
        tenant_id=test_tenant.id,
        role=UserRole.CREW,
        is_active=True,
    )
    test_db.add(other_user)
    await test_db.flush()

    other_crew = CrewProfile(
        user_id=other_user.id,
        tenant_id=test_tenant.id,
        skills=["Audio"],
    )
    test_db.add(other_crew)
    await test_db.flush()

    # Create job
    job = Job(
        title="Multi-Crew Job",
        tenant_id=test_tenant.id,
        scheduled_start=datetime(2026, 6, 15, 9, 0, tzinfo=timezone.utc),
        scheduled_end=datetime(2026, 6, 15, 17, 0, tzinfo=timezone.utc),
        state=JobState.ACTIVE,
    )
    test_db.add(job)
    await test_db.flush()

    # Assign both crew members
    assignment1 = CrewAssignment(
        crew_id=test_crew_profile.id,
        job_id=job.id,
        tenant_id=test_tenant.id,
        role="Camera",
        status=AssignmentState.CONFIRMED,
    )
    assignment2 = CrewAssignment(
        crew_id=other_crew.id,
        job_id=job.id,
        tenant_id=test_tenant.id,
        role="Sound",
        status=AssignmentState.CONFIRMED,
    )
    test_db.add_all([assignment1, assignment2])
    await test_db.flush()

    # Get calendar for test_crew_profile only
    response = await async_client.get(
        f"/api/v1/calendar/crew/{test_crew_profile.id}?start=2026-06-01T00:00:00Z&end=2026-06-30T00:00:00Z",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 2  # job + this crew's assignment only

    # Should only have one crew_assignment event
    crew_events = [e for e in data["events"] if e["event_type"] == "crew_assignment"]
    assert len(crew_events) == 1
    assert crew_events[0]["role"] == "Camera"
    assert crew_events[0]["resource_name"] == "crew@test.com"


@pytest.mark.asyncio
async def test_get_equipment_calendar(
    async_client: AsyncClient,
    admin_token: str,
    test_db,
    test_tenant,
):
    """Equipment calendar endpoint returns only that equipment's assignments"""
    await test_db.execute(
        text(f"SET LOCAL app.current_tenant_id = '{test_tenant.id}'")
    )

    # Create two equipment items
    equipment1 = Equipment(
        name="Camera A",
        tenant_id=test_tenant.id,
        category="Camera",
        quantity=1,
    )
    equipment2 = Equipment(
        name="Camera B",
        tenant_id=test_tenant.id,
        category="Camera",
        quantity=1,
    )
    test_db.add_all([equipment1, equipment2])
    await test_db.flush()

    # Create job
    job = Job(
        title="Dual Camera Shoot",
        tenant_id=test_tenant.id,
        scheduled_start=datetime(2026, 6, 20, 9, 0, tzinfo=timezone.utc),
        scheduled_end=datetime(2026, 6, 20, 17, 0, tzinfo=timezone.utc),
        state=JobState.ACTIVE,
    )
    test_db.add(job)
    await test_db.flush()

    # Assign both equipment
    assignment1 = EquipmentAssignment(
        equipment_id=equipment1.id,
        job_id=job.id,
        tenant_id=test_tenant.id,
        quantity_assigned=1,
    )
    assignment2 = EquipmentAssignment(
        equipment_id=equipment2.id,
        job_id=job.id,
        tenant_id=test_tenant.id,
        quantity_assigned=1,
    )
    test_db.add_all([assignment1, assignment2])
    await test_db.flush()

    # Get calendar for equipment1 only
    response = await async_client.get(
        f"/api/v1/calendar/equipment/{equipment1.id}?start=2026-06-01T00:00:00Z&end=2026-06-30T00:00:00Z",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 2  # job + this equipment's assignment only

    # Should only have one equipment_assignment event
    equip_events = [e for e in data["events"] if e["event_type"] == "equipment_assignment"]
    assert len(equip_events) == 1
    assert equip_events[0]["resource_name"] == "Camera A"


@pytest.mark.asyncio
async def test_event_color_mapping(
    async_client: AsyncClient,
    admin_token: str,
    test_db,
    test_tenant,
):
    """Calendar events have correct colors for different job states"""
    await test_db.execute(
        text(f"SET LOCAL app.current_tenant_id = '{test_tenant.id}'")
    )

    # Create jobs in different states
    job_intake = Job(
        title="Intake Job",
        tenant_id=test_tenant.id,
        scheduled_start=datetime(2026, 6, 1, 9, 0, tzinfo=timezone.utc),
        scheduled_end=datetime(2026, 6, 1, 17, 0, tzinfo=timezone.utc),
        state=JobState.INTAKE,
    )
    job_simmer = Job(
        title="Simmer Job",
        tenant_id=test_tenant.id,
        scheduled_start=datetime(2026, 6, 5, 9, 0, tzinfo=timezone.utc),
        scheduled_end=datetime(2026, 6, 5, 17, 0, tzinfo=timezone.utc),
        state=JobState.SIMMER,
    )
    job_active = Job(
        title="Active Job",
        tenant_id=test_tenant.id,
        scheduled_start=datetime(2026, 6, 10, 9, 0, tzinfo=timezone.utc),
        scheduled_end=datetime(2026, 6, 10, 17, 0, tzinfo=timezone.utc),
        state=JobState.ACTIVE,
    )
    job_complete = Job(
        title="Complete Job",
        tenant_id=test_tenant.id,
        scheduled_start=datetime(2026, 6, 15, 9, 0, tzinfo=timezone.utc),
        scheduled_end=datetime(2026, 6, 15, 17, 0, tzinfo=timezone.utc),
        state=JobState.COMPLETE,
    )
    test_db.add_all([job_intake, job_simmer, job_active, job_complete])
    await test_db.flush()

    response = await async_client.get(
        "/api/v1/calendar/events?start=2026-06-01T00:00:00Z&end=2026-06-30T00:00:00Z",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 4

    # Check colors
    events_by_title = {e["title"]: e for e in data["events"]}
    assert events_by_title["Intake Job"]["color"] == "#3B82F6"  # blue
    assert events_by_title["Simmer Job"]["color"] == "#EAB308"  # yellow
    assert events_by_title["Active Job"]["color"] == "#10B981"  # green
    assert events_by_title["Complete Job"]["color"] == "#6B7280"  # grey


@pytest.mark.asyncio
async def test_batch_query_no_n_plus_1(
    async_client: AsyncClient,
    admin_token: str,
    test_db,
    test_tenant,
    test_crew_profile,
):
    """Calendar events use batch queries to avoid N+1 problem"""
    await test_db.execute(
        text(f"SET LOCAL app.current_tenant_id = '{test_tenant.id}'")
    )

    # Create 5 jobs with 2 crew assignments each
    for i in range(5):
        job = Job(
            title=f"Job {i+1}",
            tenant_id=test_tenant.id,
            scheduled_start=datetime(2026, 6, i+1, 9, 0, tzinfo=timezone.utc),
            scheduled_end=datetime(2026, 6, i+1, 17, 0, tzinfo=timezone.utc),
            state=JobState.ACTIVE,
        )
        test_db.add(job)
        await test_db.flush()

        # Add 2 crew assignments per job
        assignment1 = CrewAssignment(
            crew_id=test_crew_profile.id,
            job_id=job.id,
            tenant_id=test_tenant.id,
            role=f"Role A",
            status=AssignmentState.CONFIRMED,
        )
        test_db.add(assignment1)

    await test_db.flush()

    # This should succeed quickly without N+1 issue
    response = await async_client.get(
        "/api/v1/calendar/events?start=2026-06-01T00:00:00Z&end=2026-06-30T00:00:00Z",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    # Should have 5 jobs + 5 crew assignments = 10 events
    assert data["count"] == 10
