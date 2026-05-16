"""Tests for crew CRUD endpoints"""

import pytest
from httpx import AsyncClient
from uuid import uuid4


@pytest.mark.asyncio
async def test_create_crew_profile(
    async_client: AsyncClient, admin_token, test_crew_user, test_tenant
):
    """Admin can create crew profile linked to existing crew user"""
    response = await async_client.post(
        "/api/v1/crew/",
        json={
            "user_id": str(test_crew_user.id),
            "phone": "+1234567890",
            "bio": "Camera operator with 5 years experience",
            "hourly_rate": 75.00,
            "skills": ["Camera", "Lighting", "Audio"],
        },
        cookies={"access_token": admin_token},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["user_id"] == str(test_crew_user.id)
    assert data["phone"] == "+1234567890"
    assert data["hourly_rate"] == 75.00
    assert "Camera" in data["skills"]
    assert data["archived_at"] is None


@pytest.mark.asyncio
async def test_create_crew_profile_duplicate_user(
    async_client: AsyncClient, admin_token, test_crew_profile
):
    """Cannot create duplicate crew profile for same user"""
    response = await async_client.post(
        "/api/v1/crew/",
        json={
            "user_id": str(test_crew_profile.user_id),
            "phone": "+9999999999",
        },
        cookies={"access_token": admin_token},
    )

    assert response.status_code == 409
    assert "already exists" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_create_crew_profile_invalid_user(
    async_client: AsyncClient, admin_token
):
    """Cannot create crew profile for non-existent user"""
    fake_uuid = str(uuid4())
    response = await async_client.post(
        "/api/v1/crew/",
        json={
            "user_id": fake_uuid,
            "phone": "+1234567890",
        },
        cookies={"access_token": admin_token},
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_crew_profile_non_crew_user(
    async_client: AsyncClient, admin_token, test_admin_user
):
    """Cannot create crew profile for user without CREW role"""
    response = await async_client.post(
        "/api/v1/crew/",
        json={
            "user_id": str(test_admin_user.id),
            "phone": "+1234567890",
        },
        cookies={"access_token": admin_token},
    )

    assert response.status_code == 400
    assert "crew role" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_list_crew(
    async_client: AsyncClient, admin_token, test_crew_profile
):
    """Can list crew profiles"""
    response = await async_client.get(
        "/api/v1/crew/",
        cookies={"access_token": admin_token},
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert any(p["id"] == str(test_crew_profile.id) for p in data)


@pytest.mark.asyncio
async def test_search_crew_by_email(
    async_client: AsyncClient, admin_token, test_crew_profile, test_crew_user
):
    """Can search crew by email"""
    response = await async_client.get(
        "/api/v1/crew/",
        params={"search": "crew"},
        cookies={"access_token": admin_token},
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    # Should match test_crew_user email "crew@test.com"


@pytest.mark.asyncio
async def test_filter_crew_by_role(
    async_client: AsyncClient, admin_token, test_db, test_crew_profile, test_job
):
    """Can filter crew by functional role from assignments"""
    from app.models import CrewAssignment, AssignmentState

    # Create assignment with role
    assignment = CrewAssignment(
        crew_id=test_crew_profile.id,
        job_id=test_job.id,
        tenant_id=test_job.tenant_id,
        role="Camera Operator",
        status=AssignmentState.CONFIRMED,
    )
    test_db.add(assignment)
    await test_db.flush()

    # Search for crew with "Camera" role
    response = await async_client.get(
        "/api/v1/crew/",
        params={"role": "Camera"},
        cookies={"access_token": admin_token},
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert any(p["id"] == str(test_crew_profile.id) for p in data)


@pytest.mark.asyncio
async def test_filter_crew_by_skills(
    async_client: AsyncClient, admin_token, test_crew_profile
):
    """Can filter crew by skills - must have ALL specified skills"""
    # test_crew_profile has skills: ["Camera", "Lighting"]
    response = await async_client.get(
        "/api/v1/crew/",
        params={"skills": ["Camera", "Lighting"]},
        cookies={"access_token": admin_token},
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert any(p["id"] == str(test_crew_profile.id) for p in data)


@pytest.mark.asyncio
async def test_filter_crew_by_skills_no_match(
    async_client: AsyncClient, admin_token, test_crew_profile
):
    """Crew without required skill should not appear in results"""
    # test_crew_profile has skills: ["Camera", "Lighting"]
    # Search for "Audio" skill
    response = await async_client.get(
        "/api/v1/crew/",
        params={"skills": ["Audio"]},
        cookies={"access_token": admin_token},
    )

    assert response.status_code == 200
    data = response.json()
    # Should not include test_crew_profile
    assert not any(p["id"] == str(test_crew_profile.id) for p in data)


@pytest.mark.asyncio
async def test_archive_crew_profile(
    async_client: AsyncClient, admin_token, test_crew_profile
):
    """Admin can archive crew profile"""
    response = await async_client.post(
        f"/api/v1/crew/{test_crew_profile.id}/archive",
        cookies={"access_token": admin_token},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["archived_at"] is not None


@pytest.mark.asyncio
async def test_archived_crew_hidden_from_search(
    async_client: AsyncClient, admin_token, test_crew_profile
):
    """Archived crew profiles are excluded from default search"""
    # Archive the profile
    await async_client.post(
        f"/api/v1/crew/{test_crew_profile.id}/archive",
        cookies={"access_token": admin_token},
    )

    # List crew (default excludes archived)
    response = await async_client.get(
        "/api/v1/crew/",
        cookies={"access_token": admin_token},
    )

    assert response.status_code == 200
    data = response.json()
    # Should not include archived profile
    assert not any(p["id"] == str(test_crew_profile.id) for p in data)


@pytest.mark.asyncio
async def test_archived_crew_shown_with_flag(
    async_client: AsyncClient, admin_token, test_crew_profile
):
    """Archived crew profiles appear when include_archived=true"""
    # Archive the profile
    await async_client.post(
        f"/api/v1/crew/{test_crew_profile.id}/archive",
        cookies={"access_token": admin_token},
    )

    # List crew with include_archived flag
    response = await async_client.get(
        "/api/v1/crew/",
        params={"include_archived": "true"},
        cookies={"access_token": admin_token},
    )

    assert response.status_code == 200
    data = response.json()
    # Should include archived profile
    assert any(p["id"] == str(test_crew_profile.id) for p in data)


@pytest.mark.asyncio
async def test_unarchive_crew_profile(
    async_client: AsyncClient, admin_token, test_crew_profile
):
    """Admin can restore archived crew profile"""
    # Archive first
    await async_client.post(
        f"/api/v1/crew/{test_crew_profile.id}/archive",
        cookies={"access_token": admin_token},
    )

    # Unarchive
    response = await async_client.post(
        f"/api/v1/crew/{test_crew_profile.id}/unarchive",
        cookies={"access_token": admin_token},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["archived_at"] is None


@pytest.mark.asyncio
async def test_update_crew_profile(
    async_client: AsyncClient, admin_token, test_crew_profile
):
    """Admin can update crew profile fields"""
    response = await async_client.patch(
        f"/api/v1/crew/{test_crew_profile.id}",
        json={
            "hourly_rate": 100.00,
            "skills": ["Camera", "Lighting", "Grip"],
        },
        cookies={"access_token": admin_token},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["hourly_rate"] == 100.00
    assert "Grip" in data["skills"]


@pytest.mark.asyncio
async def test_get_crew_profile(
    async_client: AsyncClient, admin_token, test_crew_profile
):
    """Can retrieve single crew profile"""
    response = await async_client.get(
        f"/api/v1/crew/{test_crew_profile.id}",
        cookies={"access_token": admin_token},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(test_crew_profile.id)
    assert data["phone"] == test_crew_profile.phone


@pytest.mark.asyncio
async def test_get_crew_profile_not_found(
    async_client: AsyncClient, admin_token
):
    """Returns 404 for non-existent crew profile"""
    fake_uuid = str(uuid4())
    response = await async_client.get(
        f"/api/v1/crew/{fake_uuid}",
        cookies={"access_token": admin_token},
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_crew_crud_requires_admin(
    async_client: AsyncClient, crew_token, test_crew_user
):
    """Crew users cannot create/update profiles (admin only)"""
    # Try to create profile with crew token
    response = await async_client.post(
        "/api/v1/crew/",
        json={
            "user_id": str(test_crew_user.id),
            "phone": "+1234567890",
        },
        cookies={"access_token": crew_token},
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_crew_can_list_directory(
    async_client: AsyncClient, crew_token, test_crew_profile
):
    """Crew users can view directory (read-only access)"""
    response = await async_client.get(
        "/api/v1/crew/",
        cookies={"access_token": crew_token},
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
