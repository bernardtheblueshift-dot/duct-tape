"""Tests for notification counts endpoint and last-seen tracking"""

import pytest
import pytest_asyncio
from datetime import datetime, timezone, timedelta
from unittest.mock import patch


@pytest_asyncio.fixture
async def test_message(test_db, test_job, test_admin_user):
    """Create a test message"""
    from app.models import Message
    message = Message(
        job_id=test_job.id,
        user_id=test_admin_user.id,
        content="Test message",
        tenant_id=test_job.tenant_id,
    )
    test_db.add(message)
    await test_db.flush()
    return message


@pytest_asyncio.fixture
async def test_crew_assignment(test_db, test_job, test_crew_profile):
    """Create a PENDING crew assignment"""
    from app.models import CrewAssignment, AssignmentState
    assignment = CrewAssignment(
        job_id=test_job.id,
        crew_id=test_crew_profile.id,
        role="Camera Operator",
        status=AssignmentState.PENDING,
        tenant_id=test_job.tenant_id,
    )
    test_db.add(assignment)
    await test_db.flush()
    return assignment


@pytest.mark.asyncio
async def test_notification_counts_no_data(async_client, admin_token, test_db, test_tenant):
    """GET /notifications/counts returns zeros for user with no messages or assignments"""
    # Set tenant context
    from sqlalchemy import text
    await test_db.execute(text(f"SET LOCAL app.current_tenant_id = '{test_tenant.id}'"))

    response = await async_client.get(
        "/api/v1/notifications/counts",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["unread_messages"] == 0
    assert data["pending_assignments"] == 0


@pytest.mark.asyncio
async def test_notification_counts_pending_assignments(
    async_client,
    crew_token,
    test_db,
    test_tenant,
    test_crew_assignment,
):
    """User with PENDING crew assignments gets correct pending_assignments count"""
    # Set tenant context
    from sqlalchemy import text
    await test_db.execute(text(f"SET LOCAL app.current_tenant_id = '{test_tenant.id}'"))

    response = await async_client.get(
        "/api/v1/notifications/counts",
        headers={"Authorization": f"Bearer {crew_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["pending_assignments"] == 1
    assert data["unread_messages"] == 0


@pytest.mark.asyncio
async def test_notification_counts_unread_messages(
    async_client,
    admin_token,
    test_db,
    test_tenant,
    test_admin_user,
    test_job,
):
    """User who has viewed messages then new messages arrive gets correct unread_messages count"""
    from app.models import Message, MessageLastSeen
    from sqlalchemy import text

    # Set tenant context
    await test_db.execute(text(f"SET LOCAL app.current_tenant_id = '{test_tenant.id}'"))

    # Create old message
    old_time = datetime.now(timezone.utc) - timedelta(hours=2)
    old_message = Message(
        job_id=test_job.id,
        user_id=test_admin_user.id,
        content="Old message",
        tenant_id=test_tenant.id,
        created_at=old_time,
    )
    test_db.add(old_message)
    await test_db.flush()

    # User viewed messages 1 hour ago
    last_seen_time = datetime.now(timezone.utc) - timedelta(hours=1)
    last_seen = MessageLastSeen(
        user_id=test_admin_user.id,
        job_id=test_job.id,
        last_seen_at=last_seen_time,
        tenant_id=test_tenant.id,
    )
    test_db.add(last_seen)
    await test_db.flush()

    # Create new message after last_seen
    new_message = Message(
        job_id=test_job.id,
        user_id=test_admin_user.id,
        content="New message",
        tenant_id=test_tenant.id,
    )
    test_db.add(new_message)
    await test_db.flush()
    await test_db.commit()

    response = await async_client.get(
        "/api/v1/notifications/counts",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["unread_messages"] == 1  # Only the new message


@pytest.mark.asyncio
async def test_list_messages_updates_last_seen(
    async_client,
    admin_token,
    test_db,
    test_tenant,
    test_admin_user,
    test_job,
    test_message,
):
    """After calling GET /jobs/{id}/messages, the MessageLastSeen record is created/updated"""
    from app.models import MessageLastSeen
    from sqlalchemy import select, text

    # Set tenant context
    await test_db.execute(text(f"SET LOCAL app.current_tenant_id = '{test_tenant.id}'"))

    # Verify no last_seen record exists
    result = await test_db.execute(
        select(MessageLastSeen).where(
            MessageLastSeen.user_id == test_admin_user.id,
            MessageLastSeen.job_id == test_job.id,
        )
    )
    assert result.scalar_one_or_none() is None

    # Call list_messages
    before_call = datetime.now(timezone.utc)
    response = await async_client.get(
        f"/api/v1/jobs/{test_job.id}/messages",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    after_call = datetime.now(timezone.utc)

    assert response.status_code == 200

    # Verify last_seen record was created
    await test_db.commit()  # Ensure changes are visible
    result = await test_db.execute(
        select(MessageLastSeen).where(
            MessageLastSeen.user_id == test_admin_user.id,
            MessageLastSeen.job_id == test_job.id,
        )
    )
    last_seen = result.scalar_one_or_none()
    assert last_seen is not None
    assert before_call <= last_seen.last_seen_at <= after_call


@pytest.mark.asyncio
async def test_admin_sees_zero_pending(async_client, admin_token, test_db, test_tenant):
    """Admin user (no crew profile) gets pending_assignments=0"""
    # Set tenant context
    from sqlalchemy import text
    await test_db.execute(text(f"SET LOCAL app.current_tenant_id = '{test_tenant.id}'"))

    response = await async_client.get(
        "/api/v1/notifications/counts",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["pending_assignments"] == 0
