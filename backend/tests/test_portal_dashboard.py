"""Tests for crew portal dashboard and job detail endpoints"""

import pytest
import pytest_asyncio
from datetime import datetime, timezone, timedelta
from uuid import UUID


@pytest_asyncio.fixture
async def crew_with_assignments(test_db, test_tenant, test_crew_user, test_crew_profile):
    """Crew user with a profile and multiple job assignments"""
    from app.models import Job, JobState, CrewAssignment, AssignmentState, JobFile

    # Future jobs (upcoming)
    upcoming_job1 = Job(
        title="Future Event 1",
        venue="Venue A",
        scheduled_start=datetime.now(timezone.utc) + timedelta(days=5),
        scheduled_end=datetime.now(timezone.utc) + timedelta(days=5, hours=8),
        state=JobState.ACTIVE,
        tenant_id=test_tenant.id,
    )
    upcoming_job2 = Job(
        title="Future Event 2",
        venue="Venue B",
        scheduled_start=datetime.now(timezone.utc) + timedelta(days=10),
        scheduled_end=datetime.now(timezone.utc) + timedelta(days=10, hours=8),
        state=JobState.SIMMER,
        tenant_id=test_tenant.id,
    )

    # Recent completed job (within last 7 days)
    recent_job = Job(
        title="Recent Completed Event",
        venue="Venue C",
        scheduled_start=datetime.now(timezone.utc) - timedelta(days=3),
        scheduled_end=datetime.now(timezone.utc) - timedelta(days=3, hours=-8),
        state=JobState.COMPLETE,
        tenant_id=test_tenant.id,
    )

    # Old completed job (beyond 7 days, should NOT appear in recent)
    old_job = Job(
        title="Old Completed Event",
        venue="Venue D",
        scheduled_start=datetime.now(timezone.utc) - timedelta(days=10),
        scheduled_end=datetime.now(timezone.utc) - timedelta(days=10, hours=-8),
        state=JobState.COMPLETE,
        tenant_id=test_tenant.id,
    )

    test_db.add_all([upcoming_job1, upcoming_job2, recent_job, old_job])
    await test_db.flush()

    # Create assignments
    assignment1 = CrewAssignment(
        crew_id=test_crew_profile.id,
        job_id=upcoming_job1.id,
        role="Camera Operator",
        status=AssignmentState.CONFIRMED,
        tenant_id=test_tenant.id,
    )
    assignment2 = CrewAssignment(
        crew_id=test_crew_profile.id,
        job_id=upcoming_job2.id,
        role="Sound Tech",
        status=AssignmentState.PENDING,
        tenant_id=test_tenant.id,
    )
    assignment3 = CrewAssignment(
        crew_id=test_crew_profile.id,
        job_id=recent_job.id,
        role="Lighting",
        status=AssignmentState.CONFIRMED,
        tenant_id=test_tenant.id,
    )
    # Declined assignment should not appear
    assignment4 = CrewAssignment(
        crew_id=test_crew_profile.id,
        job_id=old_job.id,
        role="Audio",
        status=AssignmentState.DECLINED,
        tenant_id=test_tenant.id,
    )

    test_db.add_all([assignment1, assignment2, assignment3, assignment4])
    await test_db.flush()

    # Add files to upcoming_job1 for job detail test
    file1 = JobFile(
        job_id=upcoming_job1.id,
        uploader_id=test_crew_user.id,
        original_filename="brief.pdf",
        storage_path="uploads/tenant/job/brief.pdf",
        mime_type="application/pdf",
        file_size=1024,
        tenant_id=test_tenant.id,
    )
    file2 = JobFile(
        job_id=upcoming_job1.id,
        uploader_id=test_crew_user.id,
        original_filename="schedule.xlsx",
        storage_path="uploads/tenant/job/schedule.xlsx",
        mime_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        file_size=2048,
        tenant_id=test_tenant.id,
    )
    test_db.add_all([file1, file2])
    await test_db.flush()

    return {
        "crew_user": test_crew_user,
        "crew_profile": test_crew_profile,
        "upcoming_job1": upcoming_job1,
        "upcoming_job2": upcoming_job2,
        "recent_job": recent_job,
        "old_job": old_job,
        "assignment1": assignment1,
        "assignment2": assignment2,
        "file1": file1,
        "file2": file2,
    }


@pytest.mark.asyncio
async def test_dashboard_returns_upcoming_and_recent_assignments(
    async_client, crew_token, crew_with_assignments, test_db
):
    """GET /api/v1/portal/dashboard returns upcoming and recent assignments"""
    from sqlalchemy import text

    # Set tenant context
    await test_db.execute(
        text(f"SET LOCAL app.current_tenant_id = '{crew_with_assignments['crew_user'].tenant_id}'")
    )

    response = await async_client.get(
        "/api/v1/portal/dashboard",
        headers={"Authorization": f"Bearer {crew_token}"},
    )

    assert response.status_code == 200
    data = response.json()

    # Should have upcoming and recent sections
    assert "upcoming" in data
    assert "recent" in data
    assert "counts" in data

    # Upcoming: 2 jobs (sorted by scheduled_start ASC)
    assert len(data["upcoming"]) == 2
    assert data["upcoming"][0]["job_title"] == "Future Event 1"
    assert data["upcoming"][0]["role"] == "Camera Operator"
    assert data["upcoming"][0]["status"] == "confirmed"
    assert data["upcoming"][1]["job_title"] == "Future Event 2"
    assert data["upcoming"][1]["role"] == "Sound Tech"
    assert data["upcoming"][1]["status"] == "pending"

    # Recent: 1 completed job (within last 7 days)
    assert len(data["recent"]) == 1
    assert data["recent"][0]["job_title"] == "Recent Completed Event"
    assert data["recent"][0]["role"] == "Lighting"


@pytest.mark.asyncio
async def test_dashboard_includes_notification_counts(
    async_client, crew_token, crew_with_assignments, test_db
):
    """GET /api/v1/portal/dashboard includes notification counts"""
    from sqlalchemy import text

    # Set tenant context
    await test_db.execute(
        text(f"SET LOCAL app.current_tenant_id = '{crew_with_assignments['crew_user'].tenant_id}'")
    )

    response = await async_client.get(
        "/api/v1/portal/dashboard",
        headers={"Authorization": f"Bearer {crew_token}"},
    )

    assert response.status_code == 200
    data = response.json()

    # Notification counts present
    assert "counts" in data
    assert "unread_messages" in data["counts"]
    assert "pending_assignments" in data["counts"]

    # Should have 1 pending assignment (Future Event 2)
    assert data["counts"]["pending_assignments"] == 1


@pytest.mark.asyncio
async def test_dashboard_returns_404_for_user_without_crew_profile(
    async_client, test_db, test_tenant
):
    """GET /api/v1/portal/dashboard returns 404 if user has no CrewProfile"""
    from app.models import User, UserRole
    from app.core.security import hash_password, create_access_token
    from sqlalchemy import text

    # Create user without crew profile
    user_no_profile = User(
        email="nocrewprofile@test.com",
        hashed_password=hash_password("password123"),
        tenant_id=test_tenant.id,
        role=UserRole.CREW,
        is_active=True,
    )
    test_db.add(user_no_profile)
    await test_db.flush()

    token = create_access_token(
        str(user_no_profile.id),
        str(user_no_profile.tenant_id),
        user_no_profile.role.value,
    )

    # Set tenant context
    await test_db.execute(
        text(f"SET LOCAL app.current_tenant_id = '{user_no_profile.tenant_id}'")
    )

    response = await async_client.get(
        "/api/v1/portal/dashboard",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404
    assert "Crew profile not found" in response.json()["detail"]


@pytest.mark.asyncio
async def test_job_detail_returns_full_job_for_assigned_crew(
    async_client, crew_token, crew_with_assignments, test_db
):
    """GET /api/v1/portal/jobs/{id} returns full job details for assigned crew"""
    from sqlalchemy import text

    # Set tenant context
    await test_db.execute(
        text(f"SET LOCAL app.current_tenant_id = '{crew_with_assignments['crew_user'].tenant_id}'")
    )

    job_id = crew_with_assignments["upcoming_job1"].id

    response = await async_client.get(
        f"/api/v1/portal/jobs/{job_id}",
        headers={"Authorization": f"Bearer {crew_token}"},
    )

    assert response.status_code == 200
    data = response.json()

    # Job fields
    assert data["id"] == str(job_id)
    assert data["title"] == "Future Event 1"
    assert data["venue"] == "Venue A"
    assert data["state"] == "active"

    # Crew-specific fields
    assert data["crew_role"] == "Camera Operator"
    assert data["assignment_status"] == "confirmed"

    # Files list
    assert "files" in data
    assert len(data["files"]) == 2
    assert data["files"][0]["original_filename"] in ["brief.pdf", "schedule.xlsx"]


@pytest.mark.asyncio
async def test_job_detail_returns_403_for_unassigned_job(
    async_client, crew_token, crew_with_assignments, test_db, test_tenant
):
    """GET /api/v1/portal/jobs/{id} returns 403 if crew is not assigned"""
    from app.models import Job, JobState
    from sqlalchemy import text

    # Create a job the crew is NOT assigned to
    unassigned_job = Job(
        title="Unassigned Event",
        venue="Venue X",
        scheduled_start=datetime.now(timezone.utc) + timedelta(days=15),
        state=JobState.ACTIVE,
        tenant_id=test_tenant.id,
    )
    test_db.add(unassigned_job)
    await test_db.flush()

    # Set tenant context
    await test_db.execute(
        text(f"SET LOCAL app.current_tenant_id = '{crew_with_assignments['crew_user'].tenant_id}'")
    )

    response = await async_client.get(
        f"/api/v1/portal/jobs/{unassigned_job.id}",
        headers={"Authorization": f"Bearer {crew_token}"},
    )

    assert response.status_code == 403
    assert "Not assigned to this job" in response.json()["detail"]


@pytest.mark.asyncio
async def test_job_detail_returns_404_for_nonexistent_job(
    async_client, crew_token, crew_with_assignments, test_db
):
    """GET /api/v1/portal/jobs/{id} returns 404 for nonexistent job"""
    from sqlalchemy import text
    from uuid import uuid4

    # Set tenant context
    await test_db.execute(
        text(f"SET LOCAL app.current_tenant_id = '{crew_with_assignments['crew_user'].tenant_id}'")
    )

    fake_job_id = uuid4()

    response = await async_client.get(
        f"/api/v1/portal/jobs/{fake_job_id}",
        headers={"Authorization": f"Bearer {crew_token}"},
    )

    assert response.status_code == 404
    assert "Job not found" in response.json()["detail"]


@pytest.mark.asyncio
async def test_dashboard_only_shows_current_crew_assignments(
    async_client, test_db, test_tenant, crew_with_assignments
):
    """Dashboard only shows assignments for the current user's crew profile"""
    from app.models import User, UserRole, CrewProfile, CrewAssignment, AssignmentState, Job, JobState
    from app.core.security import hash_password, create_access_token
    from sqlalchemy import text

    # Create a second crew user with their own assignment
    crew_user2 = User(
        email="crew2@test.com",
        hashed_password=hash_password("password123"),
        tenant_id=test_tenant.id,
        role=UserRole.CREW,
        is_active=True,
    )
    test_db.add(crew_user2)
    await test_db.flush()

    crew_profile2 = CrewProfile(
        user_id=crew_user2.id,
        tenant_id=test_tenant.id,
        skills=["Audio"],
    )
    test_db.add(crew_profile2)
    await test_db.flush()

    # Create a job for crew2
    job_for_crew2 = Job(
        title="Crew 2 Event",
        scheduled_start=datetime.now(timezone.utc) + timedelta(days=7),
        state=JobState.ACTIVE,
        tenant_id=test_tenant.id,
    )
    test_db.add(job_for_crew2)
    await test_db.flush()

    assignment_crew2 = CrewAssignment(
        crew_id=crew_profile2.id,
        job_id=job_for_crew2.id,
        status=AssignmentState.CONFIRMED,
        tenant_id=test_tenant.id,
    )
    test_db.add(assignment_crew2)
    await test_db.flush()

    # Get token for crew_user2
    token_crew2 = create_access_token(
        str(crew_user2.id),
        str(crew_user2.tenant_id),
        crew_user2.role.value,
    )

    # Set tenant context
    await test_db.execute(
        text(f"SET LOCAL app.current_tenant_id = '{crew_user2.tenant_id}'")
    )

    # Request dashboard as crew2
    response = await async_client.get(
        "/api/v1/portal/dashboard",
        headers={"Authorization": f"Bearer {token_crew2}"},
    )

    assert response.status_code == 200
    data = response.json()

    # Should only see crew2's job, not crew1's jobs
    assert len(data["upcoming"]) == 1
    assert data["upcoming"][0]["job_title"] == "Crew 2 Event"
