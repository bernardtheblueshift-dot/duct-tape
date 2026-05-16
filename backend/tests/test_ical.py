"""Tests for iCal feed generation and token management"""

import pytest
from httpx import AsyncClient
from datetime import datetime, timezone, timedelta
from types import SimpleNamespace
from uuid import uuid4
from sqlalchemy import text
from icalendar import Calendar as ICalCalendar

from app.models import (
    Job,
    JobState,
    CrewAssignment,
    AssignmentState,
    ICalToken,
    CrewProfile,
)
from app.core.icalendar import build_ical_feed


# --- Unit tests for build_ical_feed ---


def test_build_ical_feed_empty():
    """Empty feed produces valid VCALENDAR with no events"""
    ical_data = build_ical_feed([], {})

    cal = ICalCalendar.from_ical(ical_data)
    assert cal.get('prodid') == '-//Duct Tape Crew Management//NONSGML v1.0//EN'
    assert cal.get('version') == '2.0'

    # No VEVENT components
    events = [c for c in cal.walk() if c.name == 'VEVENT']
    assert len(events) == 0


def test_build_ical_feed_confirmed_only():
    """Only CONFIRMED assignments appear in feed"""
    # Create mock assignments
    confirmed = SimpleNamespace(
        id=uuid4(),
        job_id=uuid4(),
        status=AssignmentState.CONFIRMED,
        role="Camera Operator",
    )
    pending = SimpleNamespace(
        id=uuid4(),
        job_id=uuid4(),
        status=AssignmentState.PENDING,
        role="Sound Tech",
    )

    # Create matching job
    job = SimpleNamespace(
        id=confirmed.job_id,
        title="Concert",
        scheduled_start=datetime(2026, 6, 1, 9, 0, tzinfo=timezone.utc),
        scheduled_end=datetime(2026, 6, 1, 17, 0, tzinfo=timezone.utc),
        venue="Main Stage",
        description="Summer concert",
    )

    jobs_dict = {confirmed.job_id: job}

    ical_data = build_ical_feed([confirmed, pending], jobs_dict)

    cal = ICalCalendar.from_ical(ical_data)
    events = [c for c in cal.walk() if c.name == 'VEVENT']

    # Only 1 event (confirmed), pending excluded
    assert len(events) == 1
    assert str(events[0].get('summary')) == "Camera Operator - Concert"


def test_build_ical_feed_summary_format():
    """SUMMARY format: 'Role - Job Title' when role exists"""
    assignment = SimpleNamespace(
        id=uuid4(),
        job_id=uuid4(),
        status=AssignmentState.CONFIRMED,
        role="Camera Operator",
    )

    job = SimpleNamespace(
        id=assignment.job_id,
        title="Concert",
        scheduled_start=datetime(2026, 6, 1, 9, 0, tzinfo=timezone.utc),
        scheduled_end=datetime(2026, 6, 1, 17, 0, tzinfo=timezone.utc),
        venue=None,
        description=None,
    )

    ical_data = build_ical_feed([assignment], {assignment.job_id: job})

    cal = ICalCalendar.from_ical(ical_data)
    events = [c for c in cal.walk() if c.name == 'VEVENT']

    assert len(events) == 1
    assert str(events[0].get('summary')) == "Camera Operator - Concert"


def test_build_ical_feed_summary_no_role():
    """SUMMARY without role: just Job Title"""
    assignment = SimpleNamespace(
        id=uuid4(),
        job_id=uuid4(),
        status=AssignmentState.CONFIRMED,
        role=None,  # No role
    )

    job = SimpleNamespace(
        id=assignment.job_id,
        title="Concert",
        scheduled_start=datetime(2026, 6, 1, 9, 0, tzinfo=timezone.utc),
        scheduled_end=datetime(2026, 6, 1, 17, 0, tzinfo=timezone.utc),
        venue=None,
        description=None,
    )

    ical_data = build_ical_feed([assignment], {assignment.job_id: job})

    cal = ICalCalendar.from_ical(ical_data)
    events = [c for c in cal.walk() if c.name == 'VEVENT']

    assert len(events) == 1
    assert str(events[0].get('summary')) == "Concert"


def test_build_ical_feed_skips_unscheduled():
    """Unscheduled jobs (no start/end) are excluded from feed"""
    assignment = SimpleNamespace(
        id=uuid4(),
        job_id=uuid4(),
        status=AssignmentState.CONFIRMED,
        role="Camera Operator",
    )

    # Job with no scheduled times
    job = SimpleNamespace(
        id=assignment.job_id,
        title="Concert",
        scheduled_start=None,
        scheduled_end=None,
        venue=None,
        description=None,
    )

    ical_data = build_ical_feed([assignment], {assignment.job_id: job})

    cal = ICalCalendar.from_ical(ical_data)
    events = [c for c in cal.walk() if c.name == 'VEVENT']

    # No events since job is unscheduled
    assert len(events) == 0


# --- Integration tests for API endpoints ---


@pytest.mark.asyncio
async def test_create_ical_token_admin(
    async_client: AsyncClient,
    admin_token: str,
    test_db,
    test_tenant,
    test_crew_profile,
):
    """Admin can create iCal token for crew member"""
    await test_db.execute(
        text(f"SET LOCAL app.current_tenant_id = '{test_tenant.id}'")
    )

    response = await async_client.post(
        "/api/v1/ical/tokens",
        json={"crew_id": str(test_crew_profile.id)},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 201
    data = response.json()

    assert "token" in data
    assert "feed_url" in data
    assert data["crew_id"] == str(test_crew_profile.id)
    assert data["feed_url"].startswith("/ical/")
    assert data["feed_url"].endswith(".ics")


@pytest.mark.asyncio
async def test_create_ical_token_crew_forbidden(
    async_client: AsyncClient,
    crew_token: str,
    test_db,
    test_tenant,
    test_crew_profile,
):
    """Crew cannot create tokens (admin-only)"""
    await test_db.execute(
        text(f"SET LOCAL app.current_tenant_id = '{test_tenant.id}'")
    )

    response = await async_client.post(
        "/api/v1/ical/tokens",
        json={"crew_id": str(test_crew_profile.id)},
        headers={"Authorization": f"Bearer {crew_token}"},
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_ical_feed_valid_token(
    async_client: AsyncClient,
    test_db,
    test_tenant,
    test_crew_profile,
    test_job,
):
    """Valid token returns iCal feed with confirmed assignments"""
    await test_db.execute(
        text(f"SET LOCAL app.current_tenant_id = '{test_tenant.id}'")
    )

    # Create token
    token = ICalToken.create_for_crew(
        crew_id=test_crew_profile.id,
        tenant_id=test_tenant.id,
    )
    test_db.add(token)

    # Create confirmed assignment
    assignment = CrewAssignment(
        crew_id=test_crew_profile.id,
        job_id=test_job.id,
        tenant_id=test_tenant.id,
        role="Camera Operator",
        status=AssignmentState.CONFIRMED,
    )
    test_db.add(assignment)
    await test_db.flush()

    # Fetch feed (no auth header required)
    response = await async_client.get(f"/ical/{token.token}.ics")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/calendar")

    # Parse and validate iCal
    cal = ICalCalendar.from_ical(response.content)
    events = [c for c in cal.walk() if c.name == 'VEVENT']

    assert len(events) >= 1
    assert str(events[0].get('summary')) == "Camera Operator - Test Event"


@pytest.mark.asyncio
async def test_ical_feed_invalid_token(async_client: AsyncClient):
    """Invalid token returns 404"""
    response = await async_client.get("/ical/nonexistent-token.ics")

    assert response.status_code == 404
    assert "Invalid feed token" in response.json()["detail"]


@pytest.mark.asyncio
async def test_ical_feed_expired_token(
    async_client: AsyncClient,
    test_db,
    test_tenant,
    test_crew_profile,
):
    """Expired token returns 410"""
    await test_db.execute(
        text(f"SET LOCAL app.current_tenant_id = '{test_tenant.id}'")
    )

    # Create token with past expiry
    token = ICalToken.create_for_crew(
        crew_id=test_crew_profile.id,
        tenant_id=test_tenant.id,
    )
    token.expires_at = datetime.now(timezone.utc) - timedelta(days=1)
    test_db.add(token)
    await test_db.flush()

    response = await async_client.get(f"/ical/{token.token}.ics")

    assert response.status_code == 410
    assert "expired" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_ical_feed_no_auth_required(
    async_client: AsyncClient,
    test_db,
    test_tenant,
    test_crew_profile,
):
    """Feed endpoint accessible without Authorization header"""
    await test_db.execute(
        text(f"SET LOCAL app.current_tenant_id = '{test_tenant.id}'")
    )

    token = ICalToken.create_for_crew(
        crew_id=test_crew_profile.id,
        tenant_id=test_tenant.id,
    )
    test_db.add(token)
    await test_db.flush()

    # No Authorization header
    response = await async_client.get(f"/ical/{token.token}.ics")

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_delete_ical_token(
    async_client: AsyncClient,
    admin_token: str,
    test_db,
    test_tenant,
    test_crew_profile,
):
    """Admin can revoke token, making feed URL invalid"""
    await test_db.execute(
        text(f"SET LOCAL app.current_tenant_id = '{test_tenant.id}'")
    )

    # Create token via API
    create_response = await async_client.post(
        "/api/v1/ical/tokens",
        json={"crew_id": str(test_crew_profile.id)},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert create_response.status_code == 201
    token_data = create_response.json()
    token_id = token_data["id"]
    token_str = token_data["token"]

    # Delete token
    delete_response = await async_client.delete(
        f"/api/v1/ical/tokens/{token_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert delete_response.status_code == 204

    # Feed should now return 404
    feed_response = await async_client.get(f"/ical/{token_str}.ics")
    assert feed_response.status_code == 404


@pytest.mark.asyncio
async def test_list_ical_tokens(
    async_client: AsyncClient,
    admin_token: str,
    test_db,
    test_tenant,
    test_crew_profile,
):
    """Admin can list all tokens for a crew member"""
    await test_db.execute(
        text(f"SET LOCAL app.current_tenant_id = '{test_tenant.id}'")
    )

    # Create 2 tokens for same crew
    token1 = ICalToken.create_for_crew(
        crew_id=test_crew_profile.id,
        tenant_id=test_tenant.id,
    )
    token2 = ICalToken.create_for_crew(
        crew_id=test_crew_profile.id,
        tenant_id=test_tenant.id,
    )
    test_db.add_all([token1, token2])
    await test_db.flush()

    response = await async_client.get(
        f"/api/v1/ical/tokens/{test_crew_profile.id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    data = response.json()

    assert len(data) == 2
    assert all("token" in item for item in data)
    assert all("feed_url" in item for item in data)


@pytest.mark.asyncio
async def test_ical_feed_content_headers(
    async_client: AsyncClient,
    test_db,
    test_tenant,
    test_crew_profile,
):
    """Feed returns correct content-type and cache-control headers"""
    await test_db.execute(
        text(f"SET LOCAL app.current_tenant_id = '{test_tenant.id}'")
    )

    token = ICalToken.create_for_crew(
        crew_id=test_crew_profile.id,
        tenant_id=test_tenant.id,
    )
    test_db.add(token)
    await test_db.flush()

    response = await async_client.get(f"/ical/{token.token}.ics")

    assert response.status_code == 200
    assert "text/calendar" in response.headers["content-type"]
    assert "no-cache" in response.headers["cache-control"]
