"""Tests for assignment endpoints with conflict detection"""

import pytest
from httpx import AsyncClient
from datetime import datetime, timezone
from sqlalchemy import text


@pytest.mark.asyncio
async def test_assign_crew_to_job(
    async_client: AsyncClient, admin_token: str, test_db, test_crew_profile, test_job
):
    """Admin can assign crew to job and assignment starts in pending state"""
    response = await async_client.post(
        "/api/v1/assignments/crew",
        json={
            "crew_id": str(test_crew_profile.id),
            "job_id": str(test_job.id),
            "role": "Camera Operator",
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["crew_id"] == str(test_crew_profile.id)
    assert data["job_id"] == str(test_job.id)
    assert data["role"] == "Camera Operator"
    assert data["status"] == "pending"
    assert "id" in data


@pytest.mark.asyncio
async def test_crew_confirmation_flow(
    async_client: AsyncClient,
    admin_token: str,
    crew_token: str,
    test_db,
    test_crew_profile,
    test_job,
):
    """Crew can confirm their assignment"""
    # Admin assigns crew
    assign_response = await async_client.post(
        "/api/v1/assignments/crew",
        json={
            "crew_id": str(test_crew_profile.id),
            "job_id": str(test_job.id),
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert assign_response.status_code == 201
    assignment_id = assign_response.json()["id"]

    # Crew confirms assignment
    confirm_response = await async_client.post(
        f"/api/v1/assignments/crew/{assignment_id}/transition",
        json={"new_status": "confirmed"},
        headers={"Authorization": f"Bearer {crew_token}"},
    )

    assert confirm_response.status_code == 200
    data = confirm_response.json()
    assert data["status"] == "confirmed"


@pytest.mark.asyncio
async def test_crew_decline_flow(
    async_client: AsyncClient,
    admin_token: str,
    crew_token: str,
    test_db,
    test_crew_profile,
    test_job,
):
    """Crew can decline assignment with reason"""
    # Admin assigns crew
    assign_response = await async_client.post(
        "/api/v1/assignments/crew",
        json={
            "crew_id": str(test_crew_profile.id),
            "job_id": str(test_job.id),
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert assign_response.status_code == 201
    assignment_id = assign_response.json()["id"]

    # Crew declines with reason
    decline_response = await async_client.post(
        f"/api/v1/assignments/crew/{assignment_id}/transition",
        json={
            "new_status": "declined",
            "declined_reason": "Schedule conflict with another commitment",
        },
        headers={"Authorization": f"Bearer {crew_token}"},
    )

    assert decline_response.status_code == 200
    data = decline_response.json()
    assert data["status"] == "declined"
    assert data["declined_reason"] == "Schedule conflict with another commitment"


@pytest.mark.asyncio
async def test_crew_conflict_detected(
    async_client: AsyncClient, admin_token: str, test_db, test_tenant, test_crew_profile
):
    """Conflict detection warns when crew is double-booked"""
    from app.models import Job, JobState, CrewAssignment, AssignmentState

    await test_db.execute(
        text(f"SET LOCAL app.current_tenant_id = '{test_tenant.id}'")
    )

    # Create two overlapping jobs
    job1 = Job(
        title="Event 1",
        tenant_id=test_tenant.id,
        scheduled_start=datetime(2026, 6, 1, 9, 0, tzinfo=timezone.utc),
        scheduled_end=datetime(2026, 6, 1, 17, 0, tzinfo=timezone.utc),
        state=JobState.ACTIVE,
    )
    job2 = Job(
        title="Event 2",
        tenant_id=test_tenant.id,
        scheduled_start=datetime(2026, 6, 1, 14, 0, tzinfo=timezone.utc),
        scheduled_end=datetime(2026, 6, 1, 20, 0, tzinfo=timezone.utc),
        state=JobState.ACTIVE,
    )
    test_db.add(job1)
    test_db.add(job2)
    await test_db.commit()

    # Assign crew to first job
    assign1_response = await async_client.post(
        "/api/v1/assignments/crew",
        json={
            "crew_id": str(test_crew_profile.id),
            "job_id": str(job1.id),
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert assign1_response.status_code == 201
    assignment1_id = assign1_response.json()["id"]

    # Confirm first assignment to trigger conflict detection
    confirm_response = await async_client.post(
        f"/api/v1/assignments/crew/{assignment1_id}/transition",
        json={"new_status": "confirmed"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert confirm_response.status_code == 200

    # Try to assign to overlapping job without force - should return 409 with conflict details
    assign2_response = await async_client.post(
        "/api/v1/assignments/crew",
        json={
            "crew_id": str(test_crew_profile.id),
            "job_id": str(job2.id),
            "force": False,
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert assign2_response.status_code == 409
    error_detail = assign2_response.json()["detail"]
    assert error_detail["message"] == "Crew has scheduling conflicts"
    assert len(error_detail["conflicts"]) == 1
    assert error_detail["conflicts"][0]["job_id"] == str(job1.id)
    assert error_detail["conflicts"][0]["job_title"] == "Event 1"


@pytest.mark.asyncio
async def test_crew_conflict_override(
    async_client: AsyncClient, admin_token: str, test_db, test_tenant, test_crew_profile
):
    """Admin can force assign crew despite conflicts with override reason"""
    from app.models import Job, JobState

    await test_db.execute(
        text(f"SET LOCAL app.current_tenant_id = '{test_tenant.id}'")
    )

    # Create two overlapping jobs
    job1 = Job(
        title="Event 1",
        tenant_id=test_tenant.id,
        scheduled_start=datetime(2026, 6, 1, 9, 0, tzinfo=timezone.utc),
        scheduled_end=datetime(2026, 6, 1, 17, 0, tzinfo=timezone.utc),
        state=JobState.ACTIVE,
    )
    job2 = Job(
        title="Event 2",
        tenant_id=test_tenant.id,
        scheduled_start=datetime(2026, 6, 1, 14, 0, tzinfo=timezone.utc),
        scheduled_end=datetime(2026, 6, 1, 20, 0, tzinfo=timezone.utc),
        state=JobState.ACTIVE,
    )
    test_db.add(job1)
    test_db.add(job2)
    await test_db.commit()

    # Assign and confirm crew to first job
    assign1_response = await async_client.post(
        "/api/v1/assignments/crew",
        json={
            "crew_id": str(test_crew_profile.id),
            "job_id": str(job1.id),
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert assign1_response.status_code == 201
    assignment1_id = assign1_response.json()["id"]

    confirm_response = await async_client.post(
        f"/api/v1/assignments/crew/{assignment1_id}/transition",
        json={"new_status": "confirmed"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert confirm_response.status_code == 200

    # Force assign to overlapping job with override reason
    assign2_response = await async_client.post(
        "/api/v1/assignments/crew",
        json={
            "crew_id": str(test_crew_profile.id),
            "job_id": str(job2.id),
            "force": True,
            "override_reason": "Client specifically requested this crew member",
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert assign2_response.status_code == 201
    data = assign2_response.json()
    assert data["override_reason"] == "Client specifically requested this crew member"


@pytest.mark.asyncio
async def test_assign_equipment_to_job(
    async_client: AsyncClient, admin_token: str, test_db, test_tenant, test_job
):
    """Admin can assign equipment to job"""
    from app.models import Equipment

    await test_db.execute(
        text(f"SET LOCAL app.current_tenant_id = '{test_tenant.id}'")
    )

    # Create equipment
    equipment = Equipment(
        name="Camera A",
        category="camera",
        quantity=2,
        tenant_id=test_tenant.id,
    )
    test_db.add(equipment)
    await test_db.commit()

    response = await async_client.post(
        "/api/v1/assignments/equipment",
        json={
            "equipment_id": str(equipment.id),
            "job_id": str(test_job.id),
            "quantity_assigned": 1,
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["equipment_id"] == str(equipment.id)
    assert data["job_id"] == str(test_job.id)
    assert data["quantity_assigned"] == 1


@pytest.mark.asyncio
async def test_equipment_conflict_hard_block(
    async_client: AsyncClient, admin_token: str, test_db, test_tenant
):
    """Equipment assignment is blocked when quantity exhausted (no override)"""
    from app.models import Equipment, Job, JobState

    await test_db.execute(
        text(f"SET LOCAL app.current_tenant_id = '{test_tenant.id}'")
    )

    # Create equipment with quantity 2
    equipment = Equipment(
        name="Camera A",
        category="camera",
        quantity=2,
        tenant_id=test_tenant.id,
    )
    test_db.add(equipment)
    await test_db.flush()

    # Create two overlapping jobs
    job1 = Job(
        title="Event 1",
        tenant_id=test_tenant.id,
        scheduled_start=datetime(2026, 6, 1, 9, 0, tzinfo=timezone.utc),
        scheduled_end=datetime(2026, 6, 1, 17, 0, tzinfo=timezone.utc),
        state=JobState.ACTIVE,
    )
    job2 = Job(
        title="Event 2",
        tenant_id=test_tenant.id,
        scheduled_start=datetime(2026, 6, 1, 14, 0, tzinfo=timezone.utc),
        scheduled_end=datetime(2026, 6, 1, 20, 0, tzinfo=timezone.utc),
        state=JobState.ACTIVE,
    )
    test_db.add(job1)
    test_db.add(job2)
    await test_db.commit()

    # Assign 2 units to first job
    assign1_response = await async_client.post(
        "/api/v1/assignments/equipment",
        json={
            "equipment_id": str(equipment.id),
            "job_id": str(job1.id),
            "quantity_assigned": 2,
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert assign1_response.status_code == 201

    # Try to assign 1 to overlapping job - should fail with hard block
    assign2_response = await async_client.post(
        "/api/v1/assignments/equipment",
        json={
            "equipment_id": str(equipment.id),
            "job_id": str(job2.id),
            "quantity_assigned": 1,
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert assign2_response.status_code == 409
    error_detail = assign2_response.json()["detail"]
    assert error_detail["message"] == "Insufficient equipment available"
    assert error_detail["total_quantity"] == 2
    assert error_detail["assigned_quantity"] == 2
    assert error_detail["available_quantity"] == 0
    assert error_detail["requested"] == 1


@pytest.mark.asyncio
async def test_equipment_partial_availability(
    async_client: AsyncClient, admin_token: str, test_db, test_tenant
):
    """Equipment assignment succeeds when partial quantity available"""
    from app.models import Equipment, Job, JobState

    await test_db.execute(
        text(f"SET LOCAL app.current_tenant_id = '{test_tenant.id}'")
    )

    # Create equipment with quantity 5
    equipment = Equipment(
        name="LED Panel",
        category="lighting",
        quantity=5,
        tenant_id=test_tenant.id,
    )
    test_db.add(equipment)
    await test_db.flush()

    # Create two overlapping jobs
    job1 = Job(
        title="Event 1",
        tenant_id=test_tenant.id,
        scheduled_start=datetime(2026, 6, 1, 9, 0, tzinfo=timezone.utc),
        scheduled_end=datetime(2026, 6, 1, 17, 0, tzinfo=timezone.utc),
        state=JobState.ACTIVE,
    )
    job2 = Job(
        title="Event 2",
        tenant_id=test_tenant.id,
        scheduled_start=datetime(2026, 6, 1, 14, 0, tzinfo=timezone.utc),
        scheduled_end=datetime(2026, 6, 1, 20, 0, tzinfo=timezone.utc),
        state=JobState.ACTIVE,
    )
    test_db.add(job1)
    test_db.add(job2)
    await test_db.commit()

    # Assign 3 units to first job
    assign1_response = await async_client.post(
        "/api/v1/assignments/equipment",
        json={
            "equipment_id": str(equipment.id),
            "job_id": str(job1.id),
            "quantity_assigned": 3,
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert assign1_response.status_code == 201

    # Assign 2 units to overlapping job - should succeed (2 <= 5-3=2)
    assign2_response = await async_client.post(
        "/api/v1/assignments/equipment",
        json={
            "equipment_id": str(equipment.id),
            "job_id": str(job2.id),
            "quantity_assigned": 2,
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert assign2_response.status_code == 201
    data = assign2_response.json()
    assert data["quantity_assigned"] == 2


@pytest.mark.asyncio
async def test_list_crew_assignments_for_job(
    async_client: AsyncClient, admin_token: str, test_db, test_tenant, test_job
):
    """List crew assignments for a job returns all assignments"""
    from app.models import CrewProfile, User, UserRole

    await test_db.execute(
        text(f"SET LOCAL app.current_tenant_id = '{test_tenant.id}'")
    )

    # Create two crew profiles
    user1 = User(
        email="crew1@test.com",
        hashed_password="hash",
        tenant_id=test_tenant.id,
        role=UserRole.CREW,
        is_active=True,
    )
    user2 = User(
        email="crew2@test.com",
        hashed_password="hash",
        tenant_id=test_tenant.id,
        role=UserRole.CREW,
        is_active=True,
    )
    test_db.add(user1)
    test_db.add(user2)
    await test_db.flush()

    crew1 = CrewProfile(
        user_id=user1.id,
        tenant_id=test_tenant.id,
        phone="+1111111111",
    )
    crew2 = CrewProfile(
        user_id=user2.id,
        tenant_id=test_tenant.id,
        phone="+2222222222",
    )
    test_db.add(crew1)
    test_db.add(crew2)
    await test_db.commit()

    # Assign both crew to job
    await async_client.post(
        "/api/v1/assignments/crew",
        json={"crew_id": str(crew1.id), "job_id": str(test_job.id)},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    await async_client.post(
        "/api/v1/assignments/crew",
        json={"crew_id": str(crew2.id), "job_id": str(test_job.id)},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    # List assignments
    response = await async_client.get(
        f"/api/v1/assignments/job/{test_job.id}/crew",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


@pytest.mark.asyncio
async def test_job_detail_shows_assignments(
    async_client: AsyncClient, admin_token: str, test_db, test_tenant, test_crew_profile
):
    """Job detail endpoint populates assigned_crew and assigned_gear"""
    from app.models import Job, JobState, Equipment

    await test_db.execute(
        text(f"SET LOCAL app.current_tenant_id = '{test_tenant.id}'")
    )

    # Create job and equipment
    job = Job(
        title="Test Event",
        tenant_id=test_tenant.id,
        scheduled_start=datetime(2026, 6, 1, 9, 0, tzinfo=timezone.utc),
        scheduled_end=datetime(2026, 6, 1, 17, 0, tzinfo=timezone.utc),
        state=JobState.ACTIVE,
    )
    equipment = Equipment(
        name="Camera A",
        category="camera",
        quantity=2,
        tenant_id=test_tenant.id,
    )
    test_db.add(job)
    test_db.add(equipment)
    await test_db.commit()

    # Assign crew and equipment
    await async_client.post(
        "/api/v1/assignments/crew",
        json={"crew_id": str(test_crew_profile.id), "job_id": str(job.id)},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    await async_client.post(
        "/api/v1/assignments/equipment",
        json={"equipment_id": str(equipment.id), "job_id": str(job.id), "quantity_assigned": 1},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    # Get job detail
    response = await async_client.get(
        f"/api/v1/jobs/{job.id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["assigned_crew"]) == 1
    assert data["assigned_crew"][0]["crew_id"] == str(test_crew_profile.id)
    assert len(data["assigned_gear"]) == 1
    assert data["assigned_gear"][0]["equipment_id"] == str(equipment.id)
    assert data["assigned_gear"][0]["quantity_assigned"] == 1


@pytest.mark.asyncio
async def test_delete_crew_assignment(
    async_client: AsyncClient, admin_token: str, test_crew_profile, test_job
):
    """Admin can delete crew assignment"""
    # Create assignment
    assign_response = await async_client.post(
        "/api/v1/assignments/crew",
        json={"crew_id": str(test_crew_profile.id), "job_id": str(test_job.id)},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert assign_response.status_code == 201
    assignment_id = assign_response.json()["id"]

    # Delete assignment
    delete_response = await async_client.delete(
        f"/api/v1/assignments/crew/{assignment_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert delete_response.status_code == 204

    # Verify list is empty
    list_response = await async_client.get(
        f"/api/v1/assignments/job/{test_job.id}/crew",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert list_response.status_code == 200
    assert list_response.json() == []


@pytest.mark.asyncio
async def test_assignment_transition_requires_correct_user(
    async_client: AsyncClient, admin_token: str, test_db, test_tenant, test_job
):
    """Crew A cannot confirm Crew B's assignment"""
    from app.models import CrewProfile, User, UserRole
    from app.core.security import create_access_token

    await test_db.execute(
        text(f"SET LOCAL app.current_tenant_id = '{test_tenant.id}'")
    )

    # Create two crew users
    user_a = User(
        email="crew_a@test.com",
        hashed_password="hash",
        tenant_id=test_tenant.id,
        role=UserRole.CREW,
        is_active=True,
    )
    user_b = User(
        email="crew_b@test.com",
        hashed_password="hash",
        tenant_id=test_tenant.id,
        role=UserRole.CREW,
        is_active=True,
    )
    test_db.add(user_a)
    test_db.add(user_b)
    await test_db.flush()

    crew_a = CrewProfile(
        user_id=user_a.id,
        tenant_id=test_tenant.id,
        phone="+1111111111",
    )
    crew_b = CrewProfile(
        user_id=user_b.id,
        tenant_id=test_tenant.id,
        phone="+2222222222",
    )
    test_db.add(crew_a)
    test_db.add(crew_b)
    await test_db.commit()

    # Admin assigns crew B
    assign_response = await async_client.post(
        "/api/v1/assignments/crew",
        json={"crew_id": str(crew_b.id), "job_id": str(test_job.id)},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert assign_response.status_code == 201
    assignment_id = assign_response.json()["id"]

    # Crew A tries to confirm Crew B's assignment
    crew_a_token = create_access_token(
        str(user_a.id), str(test_tenant.id), UserRole.CREW.value
    )

    confirm_response = await async_client.post(
        f"/api/v1/assignments/crew/{assignment_id}/transition",
        json={"new_status": "confirmed"},
        headers={"Authorization": f"Bearer {crew_a_token}"},
    )

    assert confirm_response.status_code == 403
    assert "Cannot transition another crew member's assignment" in confirm_response.json()["detail"]
