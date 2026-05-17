"""Tests for crew portal action endpoints"""

import pytest
from uuid import uuid4
from datetime import datetime, timezone


@pytest.mark.asyncio
async def test_confirm_pending_assignment(async_client, crew_token, test_crew_profile, test_job, test_db):
    """Crew member can confirm their own PENDING assignment"""
    from app.models import CrewAssignment, AssignmentState

    # Create PENDING assignment
    assignment = CrewAssignment(
        crew_id=test_crew_profile.id,
        job_id=test_job.id,
        role="Camera Operator",
        status=AssignmentState.PENDING,
        tenant_id=test_crew_profile.tenant_id,
    )
    test_db.add(assignment)
    await test_db.commit()
    await test_db.refresh(assignment)

    response = await async_client.post(
        f"/api/v1/portal/assignments/{assignment.id}/confirm",
        headers={"Authorization": f"Bearer {crew_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "confirmed"
    assert data["id"] == str(assignment.id)


@pytest.mark.asyncio
async def test_confirm_already_confirmed_fails(async_client, crew_token, test_crew_profile, test_job, test_db):
    """Cannot confirm an already CONFIRMED assignment"""
    from app.models import CrewAssignment, AssignmentState

    assignment = CrewAssignment(
        crew_id=test_crew_profile.id,
        job_id=test_job.id,
        status=AssignmentState.CONFIRMED,
        tenant_id=test_crew_profile.tenant_id,
    )
    test_db.add(assignment)
    await test_db.commit()
    await test_db.refresh(assignment)

    response = await async_client.post(
        f"/api/v1/portal/assignments/{assignment.id}/confirm",
        headers={"Authorization": f"Bearer {crew_token}"},
    )

    assert response.status_code == 400
    assert "Invalid transition" in response.json()["detail"]


@pytest.mark.asyncio
async def test_confirm_another_crews_assignment_forbidden(async_client, crew_token, test_job, test_db, test_tenant):
    """Crew member cannot confirm another crew member's assignment"""
    from app.models import CrewProfile, User, CrewAssignment, AssignmentState, UserRole
    from app.core.security import hash_password

    # Create another crew user
    other_user = User(
        email="othercrew@test.com",
        hashed_password=hash_password("password123"),
        tenant_id=test_tenant.id,
        role=UserRole.CREW,
        is_active=True,
    )
    test_db.add(other_user)
    await test_db.flush()

    other_profile = CrewProfile(
        user_id=other_user.id,
        tenant_id=test_tenant.id,
    )
    test_db.add(other_profile)
    await test_db.flush()

    assignment = CrewAssignment(
        crew_id=other_profile.id,
        job_id=test_job.id,
        status=AssignmentState.PENDING,
        tenant_id=test_tenant.id,
    )
    test_db.add(assignment)
    await test_db.commit()
    await test_db.refresh(assignment)

    response = await async_client.post(
        f"/api/v1/portal/assignments/{assignment.id}/confirm",
        headers={"Authorization": f"Bearer {crew_token}"},
    )

    assert response.status_code == 403
    assert "Cannot act on another crew member's assignment" in response.json()["detail"]


@pytest.mark.asyncio
async def test_decline_pending_assignment_with_reason(async_client, crew_token, test_crew_profile, test_job, test_db):
    """Crew member can decline PENDING assignment with optional reason"""
    from app.models import CrewAssignment, AssignmentState

    assignment = CrewAssignment(
        crew_id=test_crew_profile.id,
        job_id=test_job.id,
        status=AssignmentState.PENDING,
        tenant_id=test_crew_profile.tenant_id,
    )
    test_db.add(assignment)
    await test_db.commit()
    await test_db.refresh(assignment)

    response = await async_client.post(
        f"/api/v1/portal/assignments/{assignment.id}/decline",
        headers={"Authorization": f"Bearer {crew_token}"},
        json={"declined_reason": "Schedule conflict"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "declined"
    assert data["declined_reason"] == "Schedule conflict"


@pytest.mark.asyncio
async def test_decline_confirmed_assignment(async_client, crew_token, test_crew_profile, test_job, test_db):
    """Crew member can decline CONFIRMED assignment (emergency cancellation)"""
    from app.models import CrewAssignment, AssignmentState

    assignment = CrewAssignment(
        crew_id=test_crew_profile.id,
        job_id=test_job.id,
        status=AssignmentState.CONFIRMED,
        tenant_id=test_crew_profile.tenant_id,
    )
    test_db.add(assignment)
    await test_db.commit()
    await test_db.refresh(assignment)

    response = await async_client.post(
        f"/api/v1/portal/assignments/{assignment.id}/decline",
        headers={"Authorization": f"Bearer {crew_token}"},
        json={},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "declined"


@pytest.mark.asyncio
async def test_get_own_profile(async_client, crew_token, test_crew_profile):
    """Crew member can view their own profile"""
    response = await async_client.get(
        "/api/v1/portal/profile",
        headers={"Authorization": f"Bearer {crew_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(test_crew_profile.id)
    assert data["phone"] == test_crew_profile.phone
    assert data["bio"] == test_crew_profile.bio


@pytest.mark.asyncio
async def test_get_profile_no_crew_profile_fails(async_client, test_db, test_tenant):
    """User without CrewProfile gets 404"""
    from app.models import User, UserRole
    from app.core.security import hash_password, create_access_token

    user_without_profile = User(
        email="nocrew@test.com",
        hashed_password=hash_password("password123"),
        tenant_id=test_tenant.id,
        role=UserRole.CREW,
        is_active=True,
    )
    test_db.add(user_without_profile)
    await test_db.commit()

    token = create_access_token(
        str(user_without_profile.id),
        str(user_without_profile.tenant_id),
        user_without_profile.role.value,
    )

    response = await async_client.get(
        "/api/v1/portal/profile",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404
    assert "Crew profile not found" in response.json()["detail"]


@pytest.mark.asyncio
async def test_update_profile_phone_and_bio(async_client, crew_token, test_crew_profile, test_db):
    """Crew member can update phone and bio fields"""
    response = await async_client.patch(
        "/api/v1/portal/profile",
        headers={"Authorization": f"Bearer {crew_token}"},
        json={
            "phone": "+9999999999",
            "bio": "Updated bio text",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["phone"] == "+9999999999"
    assert data["bio"] == "Updated bio text"


@pytest.mark.asyncio
async def test_update_profile_ignores_skills_and_rate(async_client, crew_token, test_crew_profile, test_db):
    """Profile update silently ignores skills and hourly_rate"""
    original_skills = test_crew_profile.skills.copy()
    original_rate = test_crew_profile.hourly_rate

    response = await async_client.patch(
        "/api/v1/portal/profile",
        headers={"Authorization": f"Bearer {crew_token}"},
        json={
            "phone": "+1111111111",
            "bio": "New bio",
            "skills": ["Hacking", "Exploits"],  # Should be ignored
            "hourly_rate": 999.99,  # Should be ignored
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["phone"] == "+1111111111"
    assert data["bio"] == "New bio"
    assert data["skills"] == original_skills  # Unchanged
    assert data["hourly_rate"] == original_rate  # Unchanged


@pytest.mark.asyncio
async def test_set_availability_patterns(async_client, crew_token, test_crew_profile):
    """Crew member can set their own availability patterns"""
    patterns = [
        {"day_of_week": 0, "is_available": True},
        {"day_of_week": 1, "is_available": True},
        {"day_of_week": 5, "is_available": False},
        {"day_of_week": 6, "is_available": False},
    ]

    response = await async_client.put(
        "/api/v1/portal/availability",
        headers={"Authorization": f"Bearer {crew_token}"},
        json=patterns,
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 4
    assert data[0]["day_of_week"] == 0
    assert data[0]["is_available"] is True


@pytest.mark.asyncio
async def test_get_availability_patterns(async_client, crew_token, test_crew_profile, test_db):
    """Crew member can get their own availability patterns"""
    from app.models import AvailabilityPattern

    # Create some patterns
    pattern1 = AvailabilityPattern(
        crew_id=test_crew_profile.id,
        tenant_id=test_crew_profile.tenant_id,
        day_of_week=0,
        is_available=True,
    )
    pattern2 = AvailabilityPattern(
        crew_id=test_crew_profile.id,
        tenant_id=test_crew_profile.tenant_id,
        day_of_week=6,
        is_available=False,
    )
    test_db.add_all([pattern1, pattern2])
    await test_db.commit()

    response = await async_client.get(
        "/api/v1/portal/availability",
        headers={"Authorization": f"Bearer {crew_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["day_of_week"] == 0
    assert data[1]["day_of_week"] == 6


@pytest.mark.asyncio
async def test_get_assignments_list(async_client, crew_token, test_crew_profile, test_db, test_tenant):
    """Crew member can list their own assignments"""
    from app.models import Job, JobState, CrewAssignment, AssignmentState

    job1 = Job(
        title="Job 1",
        tenant_id=test_tenant.id,
        scheduled_start=datetime(2026, 6, 1, 9, 0, tzinfo=timezone.utc),
        state=JobState.ACTIVE,
    )
    job2 = Job(
        title="Job 2",
        tenant_id=test_tenant.id,
        scheduled_start=datetime(2026, 6, 5, 9, 0, tzinfo=timezone.utc),
        state=JobState.ACTIVE,
    )
    test_db.add_all([job1, job2])
    await test_db.flush()

    assignment1 = CrewAssignment(
        crew_id=test_crew_profile.id,
        job_id=job1.id,
        role="Sound Tech",
        status=AssignmentState.CONFIRMED,
        tenant_id=test_tenant.id,
    )
    assignment2 = CrewAssignment(
        crew_id=test_crew_profile.id,
        job_id=job2.id,
        role="Camera Operator",
        status=AssignmentState.PENDING,
        tenant_id=test_tenant.id,
    )
    test_db.add_all([assignment1, assignment2])
    await test_db.commit()

    response = await async_client.get(
        "/api/v1/portal/assignments",
        headers={"Authorization": f"Bearer {crew_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["job_title"] == "Job 1"
    assert data[0]["role"] == "Sound Tech"
    assert data[1]["job_title"] == "Job 2"
