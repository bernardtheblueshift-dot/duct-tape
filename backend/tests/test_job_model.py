"""Tests for Job model and JobState enum"""

import pytest
from datetime import datetime, timezone
from sqlalchemy import select
from app.models.job import Job, JobState
import uuid


@pytest.mark.asyncio
async def test_job_creation_defaults_to_intake_state(test_db, test_tenant):
    """Test that new jobs default to INTAKE state"""
    job = Job(
        title="Test Event",
        tenant_id=test_tenant.id,
    )
    test_db.add(job)
    await test_db.commit()
    await test_db.refresh(job)

    assert job.state == JobState.INTAKE
    assert job.id is not None
    assert isinstance(job.id, uuid.UUID)


@pytest.mark.asyncio
async def test_job_has_tenant_and_timestamp_fields(test_db, test_tenant):
    """Test that Job inherits TenantMixin and TimestampMixin fields"""
    job = Job(
        title="Test Event",
        description="A test event description",
        venue="Test Venue",
        tenant_id=test_tenant.id,
    )
    test_db.add(job)
    await test_db.commit()
    await test_db.refresh(job)

    # TenantMixin
    assert job.tenant_id == test_tenant.id
    assert isinstance(job.tenant_id, uuid.UUID)

    # TimestampMixin
    assert job.created_at is not None
    assert job.updated_at is not None
    assert isinstance(job.created_at, datetime)
    assert isinstance(job.updated_at, datetime)

    # Verify timezone awareness
    assert job.created_at.tzinfo is not None
    assert job.updated_at.tzinfo is not None


@pytest.mark.asyncio
async def test_job_scheduled_times_are_timezone_aware(test_db, test_tenant):
    """Test that scheduled_start and scheduled_end are timezone-aware"""
    scheduled_start = datetime(2026, 6, 1, 10, 0, 0, tzinfo=timezone.utc)
    scheduled_end = datetime(2026, 6, 1, 18, 0, 0, tzinfo=timezone.utc)

    job = Job(
        title="Event with Schedule",
        scheduled_start=scheduled_start,
        scheduled_end=scheduled_end,
        tenant_id=test_tenant.id,
    )
    test_db.add(job)
    await test_db.commit()
    await test_db.refresh(job)

    assert job.scheduled_start == scheduled_start
    assert job.scheduled_end == scheduled_end
    assert job.scheduled_start.tzinfo is not None
    assert job.scheduled_end.tzinfo is not None


@pytest.mark.asyncio
async def test_job_all_states_exist(test_db, test_tenant):
    """Test that all JobState enum values work"""
    states = [JobState.INTAKE, JobState.SIMMER, JobState.ACTIVE, JobState.COMPLETE]

    for state in states:
        job = Job(
            title=f"Job in {state.value} state",
            state=state,
            tenant_id=test_tenant.id,
        )
        test_db.add(job)
        await test_db.commit()
        await test_db.refresh(job)

        assert job.state == state

        # Clear session for next iteration
        await test_db.rollback()
