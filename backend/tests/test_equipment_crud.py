"""Tests for equipment CRUD endpoints"""

import pytest
from httpx import AsyncClient
from app.models.equipment import Equipment, EquipmentCondition
from app.models.user import User, UserRole
from app.models.tenant import Tenant
from app.core.security import create_access_token


@pytest.mark.asyncio
async def test_create_equipment(async_client: AsyncClient, admin_token: str):
    """Admin can create equipment with valid data"""
    response = await async_client.post(
        "/api/v1/equipment/",
        json={
            "name": "Sony A7IV",
            "category": "Camera",
            "quantity": 3,
            "condition": "good",
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Sony A7IV"
    assert data["category"] == "Camera"
    assert data["quantity"] == 3
    assert data["condition"] == "good"
    assert "id" in data
    assert "created_at" in data


@pytest.mark.asyncio
async def test_create_equipment_minimal(async_client: AsyncClient, admin_token: str):
    """Admin can create equipment with only name (all optional fields omitted)"""
    response = await async_client.post(
        "/api/v1/equipment/",
        json={"name": "XLR Cable"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "XLR Cable"
    assert data["quantity"] == 1  # Default
    assert data["condition"] == "good"  # Default


@pytest.mark.asyncio
async def test_list_equipment(
    async_client: AsyncClient, admin_token: str, test_db, test_tenant
):
    """List equipment returns all items for tenant"""
    from sqlalchemy import text

    await test_db.execute(
        text(f"SET LOCAL app.current_tenant_id = '{test_tenant.id}'")
    )

    # Create equipment using test_db fixture session
    eq1 = Equipment(
        name="Camera 1", category="Camera", tenant_id=test_tenant.id
    )
    eq2 = Equipment(
        name="Mic 1", category="Audio", tenant_id=test_tenant.id
    )
    test_db.add_all([eq1, eq2])
    await test_db.commit()

    response = await async_client.get(
        "/api/v1/equipment/",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    # Should be ordered by name ascending
    assert data[0]["name"] == "Camera 1"
    assert data[1]["name"] == "Mic 1"


@pytest.mark.asyncio
async def test_search_equipment_by_name(
    async_client: AsyncClient, admin_token: str, test_db, test_tenant
):
    """Search equipment by name using ILIKE"""
    from sqlalchemy import text

    await test_db.execute(
        text(f"SET LOCAL app.current_tenant_id = '{test_tenant.id}'")
    )

    eq1 = Equipment(name="Sony A7IV", tenant_id=test_tenant.id)
    eq2 = Equipment(name="Sennheiser MKH416", tenant_id=test_tenant.id)
    test_db.add_all([eq1, eq2])
    await test_db.commit()

    response = await async_client.get(
        "/api/v1/equipment/?search=Sony",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Sony A7IV"


@pytest.mark.asyncio
async def test_filter_equipment_by_category(
    async_client: AsyncClient, admin_token: str, test_db, test_tenant
):
    """Filter equipment by category"""
    from sqlalchemy import text

    await test_db.execute(
        text(f"SET LOCAL app.current_tenant_id = '{test_tenant.id}'")
    )

    eq1 = Equipment(name="Sony A7IV", category="Camera", tenant_id=test_tenant.id)
    eq2 = Equipment(name="Sennheiser MKH416", category="Microphone", tenant_id=test_tenant.id)
    test_db.add_all([eq1, eq2])
    await test_db.commit()

    response = await async_client.get(
        "/api/v1/equipment/?category=Camera",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Sony A7IV"


@pytest.mark.asyncio
async def test_filter_equipment_by_condition(
    async_client: AsyncClient, admin_token: str, test_db, test_tenant
):
    """Filter equipment by condition"""
    from sqlalchemy import text

    await test_db.execute(
        text(f"SET LOCAL app.current_tenant_id = '{test_tenant.id}'")
    )

    eq1 = Equipment(
        name="Camera Good",
        condition=EquipmentCondition.GOOD,
        tenant_id=test_tenant.id,
    )
    eq2 = Equipment(
        name="Camera Maintenance",
        condition=EquipmentCondition.MAINTENANCE,
        tenant_id=test_tenant.id,
    )
    test_db.add_all([eq1, eq2])
    await test_db.commit()

    response = await async_client.get(
        "/api/v1/equipment/?condition=maintenance",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Camera Maintenance"


@pytest.mark.asyncio
async def test_get_equipment_by_id(
    async_client: AsyncClient, admin_token: str, test_db, test_tenant
):
    """Get single equipment item by ID"""
    from sqlalchemy import text

    await test_db.execute(
        text(f"SET LOCAL app.current_tenant_id = '{test_tenant.id}'")
    )

    equipment = Equipment(name="Test Equipment", tenant_id=test_tenant.id)
    test_db.add(equipment)
    await test_db.commit()
    await test_db.refresh(equipment)
    equipment_id = str(equipment.id)

    response = await async_client.get(
        f"/api/v1/equipment/{equipment_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == equipment_id
    assert data["name"] == "Test Equipment"


@pytest.mark.asyncio
async def test_update_equipment(
    async_client: AsyncClient, admin_token: str, test_db, test_tenant
):
    """Admin can update equipment fields"""
    from sqlalchemy import text

    await test_db.execute(
        text(f"SET LOCAL app.current_tenant_id = '{test_tenant.id}'")
    )

    equipment = Equipment(
        name="Original Name", quantity=1, tenant_id=test_tenant.id
    )
    test_db.add(equipment)
    await test_db.commit()
    await test_db.refresh(equipment)
    equipment_id = str(equipment.id)

    response = await async_client.patch(
        f"/api/v1/equipment/{equipment_id}",
        json={"quantity": 5},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["quantity"] == 5
    assert data["name"] == "Original Name"  # Unchanged


@pytest.mark.asyncio
async def test_update_equipment_condition(
    async_client: AsyncClient, admin_token: str, test_db, test_tenant
):
    """Admin can update equipment condition via dedicated endpoint"""
    from sqlalchemy import text

    await test_db.execute(
        text(f"SET LOCAL app.current_tenant_id = '{test_tenant.id}'")
    )

    equipment = Equipment(
        name="Camera",
        condition=EquipmentCondition.GOOD,
        tenant_id=test_tenant.id,
    )
    test_db.add(equipment)
    await test_db.commit()
    await test_db.refresh(equipment)
    equipment_id = str(equipment.id)

    response = await async_client.patch(
        f"/api/v1/equipment/{equipment_id}/condition",
        json={"condition": "maintenance"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["condition"] == "maintenance"


@pytest.mark.asyncio
async def test_equipment_crud_requires_admin(
    async_client: AsyncClient, crew_token: str
):
    """Crew user cannot create equipment"""
    response = await async_client.post(
        "/api/v1/equipment/",
        json={"name": "Test Equipment"},
        headers={"Authorization": f"Bearer {crew_token}"},
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_equipment_status_tracking(
    async_client: AsyncClient, admin_token: str, test_db, test_tenant
):
    """Equipment condition persists across updates and retrieval (EQUP-04)"""
    from sqlalchemy import text

    await test_db.execute(
        text(f"SET LOCAL app.current_tenant_id = '{test_tenant.id}'")
    )

    # Create equipment with GOOD condition
    equipment = Equipment(
        name="Camera",
        condition=EquipmentCondition.GOOD,
        tenant_id=test_tenant.id,
    )
    test_db.add(equipment)
    await test_db.commit()
    await test_db.refresh(equipment)
    equipment_id = str(equipment.id)

    # Update to MAINTENANCE
    response = await async_client.patch(
        f"/api/v1/equipment/{equipment_id}/condition",
        json={"condition": "maintenance"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200

    # Verify condition persisted
    response = await async_client.get(
        f"/api/v1/equipment/{equipment_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["condition"] == "maintenance"


@pytest.mark.asyncio
async def test_delete_equipment_blocks_if_assigned(
    async_client: AsyncClient, admin_token: str, test_db, test_tenant, test_job
):
    """Delete equipment fails if active assignments exist"""
    from sqlalchemy import text
    from app.models.assignment import EquipmentAssignment

    await test_db.execute(
        text(f"SET LOCAL app.current_tenant_id = '{test_tenant.id}'")
    )

    # Create equipment
    equipment = Equipment(name="Camera", tenant_id=test_tenant.id)
    test_db.add(equipment)
    await test_db.commit()
    await test_db.refresh(equipment)
    equipment_id = str(equipment.id)

    # Create assignment
    assignment = EquipmentAssignment(
        equipment_id=equipment.id,
        job_id=test_job.id,
        tenant_id=test_tenant.id,
        quantity_assigned=1,
    )
    test_db.add(assignment)
    await test_db.commit()

    # Try to delete - should fail
    response = await async_client.delete(
        f"/api/v1/equipment/{equipment_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 409
    assert "active assignments" in response.json()["detail"]


@pytest.mark.asyncio
async def test_delete_equipment_succeeds_if_no_assignments(
    async_client: AsyncClient, admin_token: str, test_db, test_tenant
):
    """Delete equipment succeeds when no assignments exist"""
    from sqlalchemy import text

    await test_db.execute(
        text(f"SET LOCAL app.current_tenant_id = '{test_tenant.id}'")
    )

    equipment = Equipment(name="Camera", tenant_id=test_tenant.id)
    test_db.add(equipment)
    await test_db.commit()
    await test_db.refresh(equipment)
    equipment_id = str(equipment.id)

    response = await async_client.delete(
        f"/api/v1/equipment/{equipment_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 204

    # Verify deleted
    response = await async_client.get(
        f"/api/v1/equipment/{equipment_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 404
