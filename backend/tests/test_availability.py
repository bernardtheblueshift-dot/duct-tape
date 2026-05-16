"""Tests for crew availability patterns"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_set_weekly_pattern(
    async_client: AsyncClient, admin_token, test_crew_profile
):
    """Admin can set crew weekly availability pattern"""
    response = await async_client.put(
        f"/api/v1/crew/{test_crew_profile.id}/availability",
        json=[
            {"day_of_week": 0, "is_available": False},  # Monday unavailable
            {"day_of_week": 6, "is_available": False},  # Sunday unavailable
        ],
        cookies={"access_token": admin_token},
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert any(p["day_of_week"] == 0 and not p["is_available"] for p in data)
    assert any(p["day_of_week"] == 6 and not p["is_available"] for p in data)


@pytest.mark.asyncio
async def test_get_availability(
    async_client: AsyncClient, admin_token, test_crew_profile
):
    """Can retrieve crew availability patterns"""
    # Set patterns first
    await async_client.put(
        f"/api/v1/crew/{test_crew_profile.id}/availability",
        json=[
            {"day_of_week": 0, "is_available": False},
            {"day_of_week": 3, "is_available": True},
        ],
        cookies={"access_token": admin_token},
    )

    # Get patterns
    response = await async_client.get(
        f"/api/v1/crew/{test_crew_profile.id}/availability",
        cookies={"access_token": admin_token},
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    # Should be ordered by day_of_week
    assert data[0]["day_of_week"] < data[1]["day_of_week"]


@pytest.mark.asyncio
async def test_availability_upsert_replaces(
    async_client: AsyncClient, admin_token, test_crew_profile
):
    """Setting availability replaces old patterns (upsert)"""
    # Set 3 patterns
    await async_client.put(
        f"/api/v1/crew/{test_crew_profile.id}/availability",
        json=[
            {"day_of_week": 0, "is_available": False},
            {"day_of_week": 1, "is_available": False},
            {"day_of_week": 2, "is_available": False},
        ],
        cookies={"access_token": admin_token},
    )

    # Replace with only 2 patterns
    await async_client.put(
        f"/api/v1/crew/{test_crew_profile.id}/availability",
        json=[
            {"day_of_week": 5, "is_available": True},
            {"day_of_week": 6, "is_available": True},
        ],
        cookies={"access_token": admin_token},
    )

    # Get patterns - should only have 2 new ones
    response = await async_client.get(
        f"/api/v1/crew/{test_crew_profile.id}/availability",
        cookies={"access_token": admin_token},
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert all(p["day_of_week"] in [5, 6] for p in data)


@pytest.mark.asyncio
async def test_crew_sets_own_availability(
    async_client: AsyncClient, crew_token, test_crew_profile
):
    """Crew can set their own availability"""
    response = await async_client.put(
        f"/api/v1/crew/{test_crew_profile.id}/availability",
        json=[{"day_of_week": 0, "is_available": False}],
        cookies={"access_token": crew_token},
    )

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_crew_cannot_set_others_availability(
    async_client: AsyncClient, crew_token, test_db, test_tenant
):
    """Crew cannot set another crew member's availability"""
    from app.models import User, UserRole, CrewProfile
    from app.core.security import hash_password

    # Create second crew user and profile
    crew2_user = User(
        email="crew2@test.com",
        hashed_password=hash_password("password123"),
        tenant_id=test_tenant.id,
        role=UserRole.CREW,
        is_active=True,
    )
    test_db.add(crew2_user)
    await test_db.flush()

    crew2_profile = CrewProfile(
        user_id=crew2_user.id,
        tenant_id=test_tenant.id,
        phone="+9999999999",
        skills=["Audio"],
    )
    test_db.add(crew2_profile)
    await test_db.flush()

    # Try to set crew2's availability using crew1's token
    response = await async_client.put(
        f"/api/v1/crew/{crew2_profile.id}/availability",
        json=[{"day_of_week": 0, "is_available": False}],
        cookies={"access_token": crew_token},
    )

    assert response.status_code == 403
    assert "own availability" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_invalid_day_of_week(
    async_client: AsyncClient, admin_token, test_crew_profile
):
    """Day of week validation rejects values outside 0-6"""
    response = await async_client.put(
        f"/api/v1/crew/{test_crew_profile.id}/availability",
        json=[{"day_of_week": 7, "is_available": False}],
        cookies={"access_token": admin_token},
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_computed_availability(
    async_client: AsyncClient, admin_token, test_crew_profile
):
    """Set Sunday unavailable and verify it appears in GET"""
    # Set Sunday (6) as unavailable
    await async_client.put(
        f"/api/v1/crew/{test_crew_profile.id}/availability",
        json=[{"day_of_week": 6, "is_available": False}],
        cookies={"access_token": admin_token},
    )

    # Get availability
    response = await async_client.get(
        f"/api/v1/crew/{test_crew_profile.id}/availability",
        cookies={"access_token": admin_token},
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["day_of_week"] == 6
    assert data[0]["is_available"] is False
