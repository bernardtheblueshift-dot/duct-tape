"""Tests for conflict detection logic"""

import pytest
from datetime import datetime, timezone
from uuid import uuid4
from app.core.conflicts import (
    check_crew_conflicts,
    check_equipment_availability,
    check_crew_availability_patterns,
)
from app.models import (
    CrewProfile,
    Job,
    JobState,
    CrewAssignment,
    AssignmentState,
    Equipment,
    EquipmentAssignment,
    EquipmentCondition,
    AvailabilityPattern,
)


@pytest.mark.asyncio
async def test_no_overlap_when_times_are_separate(test_db, test_tenant, test_crew_user):
    """Two jobs with separate time slots should not conflict"""
    # Create crew profile
    crew = CrewProfile(
        user_id=test_crew_user.id,
        tenant_id=test_tenant.id,
        phone="+1234567890",
        skills=["Camera"],
    )
    test_db.add(crew)
    await test_db.flush()

    # Create job 1: 9am-12pm
    job1 = Job(
        title="Morning Event",
        tenant_id=test_tenant.id,
        scheduled_start=datetime(2026, 6, 1, 9, 0, tzinfo=timezone.utc),
        scheduled_end=datetime(2026, 6, 1, 12, 0, tzinfo=timezone.utc),
        state=JobState.ACTIVE,
    )
    test_db.add(job1)
    await test_db.flush()

    # Create confirmed assignment for job 1
    assignment1 = CrewAssignment(
        crew_id=crew.id,
        job_id=job1.id,
        tenant_id=test_tenant.id,
        status=AssignmentState.CONFIRMED,
    )
    test_db.add(assignment1)
    await test_db.flush()

    # Check for conflicts with job 2: 2pm-5pm
    conflicts = await check_crew_conflicts(
        test_db,
        crew.id,
        datetime(2026, 6, 1, 14, 0, tzinfo=timezone.utc),
        datetime(2026, 6, 1, 17, 0, tzinfo=timezone.utc),
    )

    assert len(conflicts) == 0


@pytest.mark.asyncio
async def test_overlap_detected(test_db, test_tenant, test_crew_user):
    """Two jobs with overlapping times should conflict"""
    # Create crew profile
    crew = CrewProfile(
        user_id=test_crew_user.id,
        tenant_id=test_tenant.id,
        phone="+1234567890",
        skills=["Camera"],
    )
    test_db.add(crew)
    await test_db.flush()

    # Create job 1: 9am-2pm
    job1 = Job(
        title="Morning Event",
        tenant_id=test_tenant.id,
        scheduled_start=datetime(2026, 6, 1, 9, 0, tzinfo=timezone.utc),
        scheduled_end=datetime(2026, 6, 1, 14, 0, tzinfo=timezone.utc),
        state=JobState.ACTIVE,
    )
    test_db.add(job1)
    await test_db.flush()

    # Create confirmed assignment for job 1
    assignment1 = CrewAssignment(
        crew_id=crew.id,
        job_id=job1.id,
        tenant_id=test_tenant.id,
        status=AssignmentState.CONFIRMED,
    )
    test_db.add(assignment1)
    await test_db.flush()

    # Check for conflicts with job 2: 1pm-5pm (overlaps with job 1)
    conflicts = await check_crew_conflicts(
        test_db,
        crew.id,
        datetime(2026, 6, 1, 13, 0, tzinfo=timezone.utc),
        datetime(2026, 6, 1, 17, 0, tzinfo=timezone.utc),
    )

    assert len(conflicts) == 1
    assert conflicts[0].id == assignment1.id


@pytest.mark.asyncio
async def test_touching_boundaries_no_conflict(test_db, test_tenant, test_crew_user):
    """Job A ends at 12pm, Job B starts at 12pm should not conflict"""
    # Create crew profile
    crew = CrewProfile(
        user_id=test_crew_user.id,
        tenant_id=test_tenant.id,
        phone="+1234567890",
        skills=["Camera"],
    )
    test_db.add(crew)
    await test_db.flush()

    # Create job 1: 9am-12pm
    job1 = Job(
        title="Morning Event",
        tenant_id=test_tenant.id,
        scheduled_start=datetime(2026, 6, 1, 9, 0, tzinfo=timezone.utc),
        scheduled_end=datetime(2026, 6, 1, 12, 0, tzinfo=timezone.utc),
        state=JobState.ACTIVE,
    )
    test_db.add(job1)
    await test_db.flush()

    # Create confirmed assignment for job 1
    assignment1 = CrewAssignment(
        crew_id=crew.id,
        job_id=job1.id,
        tenant_id=test_tenant.id,
        status=AssignmentState.CONFIRMED,
    )
    test_db.add(assignment1)
    await test_db.flush()

    # Check for conflicts with job 2: 12pm-5pm (touching boundary)
    conflicts = await check_crew_conflicts(
        test_db,
        crew.id,
        datetime(2026, 6, 1, 12, 0, tzinfo=timezone.utc),
        datetime(2026, 6, 1, 17, 0, tzinfo=timezone.utc),
    )

    assert len(conflicts) == 0


@pytest.mark.asyncio
async def test_null_times_excluded(test_db, test_tenant, test_crew_user):
    """Jobs without scheduled_start/end should never produce conflicts"""
    # Create crew profile
    crew = CrewProfile(
        user_id=test_crew_user.id,
        tenant_id=test_tenant.id,
        phone="+1234567890",
        skills=["Camera"],
    )
    test_db.add(crew)
    await test_db.flush()

    # Create job without scheduled times
    job1 = Job(
        title="TBD Event",
        tenant_id=test_tenant.id,
        scheduled_start=None,
        scheduled_end=None,
        state=JobState.INTAKE,
    )
    test_db.add(job1)
    await test_db.flush()

    # Create confirmed assignment for job 1
    assignment1 = CrewAssignment(
        crew_id=crew.id,
        job_id=job1.id,
        tenant_id=test_tenant.id,
        status=AssignmentState.CONFIRMED,
    )
    test_db.add(assignment1)
    await test_db.flush()

    # Check for conflicts with a scheduled time range
    conflicts = await check_crew_conflicts(
        test_db,
        crew.id,
        datetime(2026, 6, 1, 9, 0, tzinfo=timezone.utc),
        datetime(2026, 6, 1, 17, 0, tzinfo=timezone.utc),
    )

    assert len(conflicts) == 0


@pytest.mark.asyncio
async def test_only_confirmed_assignments_conflict(test_db, test_tenant, test_crew_user):
    """Pending and declined assignments should not trigger conflicts"""
    # Create crew profile
    crew = CrewProfile(
        user_id=test_crew_user.id,
        tenant_id=test_tenant.id,
        phone="+1234567890",
        skills=["Camera"],
    )
    test_db.add(crew)
    await test_db.flush()

    # Create job 1
    job1 = Job(
        title="Event 1",
        tenant_id=test_tenant.id,
        scheduled_start=datetime(2026, 6, 1, 9, 0, tzinfo=timezone.utc),
        scheduled_end=datetime(2026, 6, 1, 14, 0, tzinfo=timezone.utc),
        state=JobState.ACTIVE,
    )
    test_db.add(job1)
    await test_db.flush()

    # Create PENDING assignment
    assignment1 = CrewAssignment(
        crew_id=crew.id,
        job_id=job1.id,
        tenant_id=test_tenant.id,
        status=AssignmentState.PENDING,
    )
    test_db.add(assignment1)
    await test_db.flush()

    # Check for conflicts - pending should not count
    conflicts = await check_crew_conflicts(
        test_db,
        crew.id,
        datetime(2026, 6, 1, 13, 0, tzinfo=timezone.utc),
        datetime(2026, 6, 1, 17, 0, tzinfo=timezone.utc),
    )

    assert len(conflicts) == 0


@pytest.mark.asyncio
async def test_equipment_pool_available(test_db, test_tenant):
    """5 cameras, 3 assigned in time range, should return available=2"""
    # Create equipment pool
    equipment = Equipment(
        name="Canon C300",
        category="Camera",
        quantity=5,
        condition=EquipmentCondition.GOOD,
        tenant_id=test_tenant.id,
    )
    test_db.add(equipment)
    await test_db.flush()

    # Create job 1
    job1 = Job(
        title="Event 1",
        tenant_id=test_tenant.id,
        scheduled_start=datetime(2026, 6, 1, 9, 0, tzinfo=timezone.utc),
        scheduled_end=datetime(2026, 6, 1, 14, 0, tzinfo=timezone.utc),
        state=JobState.ACTIVE,
    )
    test_db.add(job1)
    await test_db.flush()

    # Assign 3 cameras to job 1
    eq_assignment = EquipmentAssignment(
        equipment_id=equipment.id,
        job_id=job1.id,
        tenant_id=test_tenant.id,
        quantity_assigned=3,
    )
    test_db.add(eq_assignment)
    await test_db.flush()

    # Check availability during overlapping time
    result = await check_equipment_availability(
        test_db,
        equipment.id,
        datetime(2026, 6, 1, 10, 0, tzinfo=timezone.utc),
        datetime(2026, 6, 1, 13, 0, tzinfo=timezone.utc),
    )

    assert result["total_quantity"] == 5
    assert result["assigned_quantity"] == 3
    assert result["available_quantity"] == 2


@pytest.mark.asyncio
async def test_equipment_pool_exhausted(test_db, test_tenant):
    """5 cameras, 5 assigned in overlapping range, should return available=0"""
    # Create equipment pool
    equipment = Equipment(
        name="Canon C300",
        category="Camera",
        quantity=5,
        condition=EquipmentCondition.GOOD,
        tenant_id=test_tenant.id,
    )
    test_db.add(equipment)
    await test_db.flush()

    # Create job 1
    job1 = Job(
        title="Event 1",
        tenant_id=test_tenant.id,
        scheduled_start=datetime(2026, 6, 1, 9, 0, tzinfo=timezone.utc),
        scheduled_end=datetime(2026, 6, 1, 14, 0, tzinfo=timezone.utc),
        state=JobState.ACTIVE,
    )
    test_db.add(job1)
    await test_db.flush()

    # Assign all 5 cameras to job 1
    eq_assignment = EquipmentAssignment(
        equipment_id=equipment.id,
        job_id=job1.id,
        tenant_id=test_tenant.id,
        quantity_assigned=5,
    )
    test_db.add(eq_assignment)
    await test_db.flush()

    # Check availability during overlapping time
    result = await check_equipment_availability(
        test_db,
        equipment.id,
        datetime(2026, 6, 1, 10, 0, tzinfo=timezone.utc),
        datetime(2026, 6, 1, 13, 0, tzinfo=timezone.utc),
    )

    assert result["total_quantity"] == 5
    assert result["assigned_quantity"] == 5
    assert result["available_quantity"] == 0


@pytest.mark.asyncio
async def test_equipment_no_overlap_available(test_db, test_tenant):
    """5 cameras, 3 assigned outside range, should return available=5"""
    # Create equipment pool
    equipment = Equipment(
        name="Canon C300",
        category="Camera",
        quantity=5,
        condition=EquipmentCondition.GOOD,
        tenant_id=test_tenant.id,
    )
    test_db.add(equipment)
    await test_db.flush()

    # Create job 1: 9am-12pm
    job1 = Job(
        title="Morning Event",
        tenant_id=test_tenant.id,
        scheduled_start=datetime(2026, 6, 1, 9, 0, tzinfo=timezone.utc),
        scheduled_end=datetime(2026, 6, 1, 12, 0, tzinfo=timezone.utc),
        state=JobState.ACTIVE,
    )
    test_db.add(job1)
    await test_db.flush()

    # Assign 3 cameras to job 1
    eq_assignment = EquipmentAssignment(
        equipment_id=equipment.id,
        job_id=job1.id,
        tenant_id=test_tenant.id,
        quantity_assigned=3,
    )
    test_db.add(eq_assignment)
    await test_db.flush()

    # Check availability for 2pm-5pm (no overlap)
    result = await check_equipment_availability(
        test_db,
        equipment.id,
        datetime(2026, 6, 1, 14, 0, tzinfo=timezone.utc),
        datetime(2026, 6, 1, 17, 0, tzinfo=timezone.utc),
    )

    assert result["total_quantity"] == 5
    assert result["assigned_quantity"] == 0
    assert result["available_quantity"] == 5


@pytest.mark.asyncio
async def test_crew_availability_pattern_unavailable(test_db, test_tenant, test_crew_user):
    """Crew marked unavailable on Sunday should return False"""
    # Create crew profile
    crew = CrewProfile(
        user_id=test_crew_user.id,
        tenant_id=test_tenant.id,
        phone="+1234567890",
        skills=["Camera"],
    )
    test_db.add(crew)
    await test_db.flush()

    # Create availability pattern: unavailable on Sunday (day 6)
    pattern = AvailabilityPattern(
        crew_id=crew.id,
        tenant_id=test_tenant.id,
        day_of_week=6,
        is_available=False,
    )
    test_db.add(pattern)
    await test_db.flush()

    # Check availability for Sunday June 1, 2026
    target_date = datetime(2026, 6, 1, 9, 0, tzinfo=timezone.utc)  # Sunday
    available = await check_crew_availability_patterns(test_db, crew.id, target_date)

    assert available is False


@pytest.mark.asyncio
async def test_crew_availability_pattern_available(test_db, test_tenant, test_crew_user):
    """Crew with no blocking pattern should return True"""
    # Create crew profile
    crew = CrewProfile(
        user_id=test_crew_user.id,
        tenant_id=test_tenant.id,
        phone="+1234567890",
        skills=["Camera"],
    )
    test_db.add(crew)
    await test_db.flush()

    # No availability patterns set - should be available
    target_date = datetime(2026, 6, 2, 9, 0, tzinfo=timezone.utc)  # Monday
    available = await check_crew_availability_patterns(test_db, crew.id, target_date)

    assert available is True
