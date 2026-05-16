"""Tests for crew skills matrix"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_skills_matrix(
    async_client: AsyncClient, admin_token, test_db, test_crew_profile, test_tenant
):
    """Skills matrix returns crew x skills boolean mapping"""
    from app.models import User, UserRole, CrewProfile
    from app.core.security import hash_password

    # Create second crew member with different skills
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
        skills=["Camera", "Lighting"],  # Camera overlaps with test_crew_profile
    )
    test_db.add(crew2_profile)
    await test_db.flush()

    # Note: test_crew_profile has skills ["Camera", "Lighting"] from conftest

    # Get skills matrix
    response = await async_client.get(
        "/api/v1/crew/skills-matrix",
        cookies={"access_token": admin_token},
    )

    assert response.status_code == 200
    data = response.json()

    # Should have all unique skills sorted
    assert set(data["skills"]) == {"Camera", "Lighting"}
    assert data["skills"] == sorted(data["skills"])

    # Should have 2 crew entries
    assert len(data["crew"]) == 2

    # Check crew1 skills mapping
    crew1_entry = next(e for e in data["crew"] if e["id"] == str(test_crew_profile.id))
    assert crew1_entry["email"] == "crew@test.com"
    assert crew1_entry["skills"]["Camera"] is True
    assert crew1_entry["skills"]["Lighting"] is True

    # Check crew2 skills mapping
    crew2_entry = next(e for e in data["crew"] if e["id"] == str(crew2_profile.id))
    assert crew2_entry["email"] == "crew2@test.com"
    assert crew2_entry["skills"]["Camera"] is True
    assert crew2_entry["skills"]["Lighting"] is True


@pytest.mark.asyncio
async def test_skills_matrix_excludes_archived(
    async_client: AsyncClient, admin_token, test_crew_profile
):
    """Archived crew members don't appear in skills matrix"""
    # Archive the crew profile
    await async_client.post(
        f"/api/v1/crew/{test_crew_profile.id}/archive",
        cookies={"access_token": admin_token},
    )

    # Get skills matrix
    response = await async_client.get(
        "/api/v1/crew/skills-matrix",
        cookies={"access_token": admin_token},
    )

    assert response.status_code == 200
    data = response.json()

    # Should not include archived profile
    assert not any(e["id"] == str(test_crew_profile.id) for e in data["crew"])


@pytest.mark.asyncio
async def test_skills_matrix_empty(async_client: AsyncClient, admin_token):
    """Skills matrix works with no crew profiles"""
    response = await async_client.get(
        "/api/v1/crew/skills-matrix",
        cookies={"access_token": admin_token},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["skills"] == []
    assert data["crew"] == []
