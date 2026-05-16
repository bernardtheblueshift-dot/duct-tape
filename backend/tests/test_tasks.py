"""Integration tests for task management endpoints"""

import pytest
from httpx import AsyncClient
from sqlalchemy import text


async def create_task(
    client: AsyncClient, job_id: str, token: str, title: str, **kwargs
):
    """Helper to create a task with default values"""
    data = {"title": title, **kwargs}
    response = await client.post(
        f"/api/v1/jobs/{job_id}/tasks",
        json=data,
        headers={"Authorization": f"Bearer {token}"},
    )
    return response


@pytest.mark.asyncio
async def test_admin_create_task(
    async_client: AsyncClient, admin_token: str, test_job
):
    """Admin can create a task with title and priority"""
    response = await create_task(
        async_client, str(test_job.id), admin_token, "Set up cameras", priority="high"
    )

    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["title"] == "Set up cameras"
    assert data["status"] == "todo"
    assert data["priority"] == "high"
    assert data["job_id"] == str(test_job.id)


@pytest.mark.asyncio
async def test_admin_create_task_with_assignee(
    async_client: AsyncClient, admin_token: str, test_job, test_crew_profile
):
    """Admin can create task with assignee"""
    response = await create_task(
        async_client,
        str(test_job.id),
        admin_token,
        "Check lighting",
        assignee_id=str(test_crew_profile.id),
    )

    assert response.status_code == 201
    data = response.json()
    assert data["assignee_id"] == str(test_crew_profile.id)


@pytest.mark.asyncio
async def test_crew_cannot_create_task(
    async_client: AsyncClient, crew_token: str, test_job
):
    """Crew cannot create tasks (403 Forbidden)"""
    response = await create_task(
        async_client, str(test_job.id), crew_token, "Some task"
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_list_tasks(
    async_client: AsyncClient, admin_token: str, test_job
):
    """List returns all tasks for a job"""
    # Create 3 tasks
    await create_task(async_client, str(test_job.id), admin_token, "Task 1")
    await create_task(async_client, str(test_job.id), admin_token, "Task 2")
    await create_task(async_client, str(test_job.id), admin_token, "Task 3")

    response = await async_client.get(
        f"/api/v1/jobs/{test_job.id}/tasks",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 3


@pytest.mark.asyncio
async def test_list_tasks_filter_by_status(
    async_client: AsyncClient, admin_token: str, test_job
):
    """List can filter by task status"""
    # Create tasks
    response1 = await create_task(
        async_client, str(test_job.id), admin_token, "Todo task"
    )
    task1_id = response1.json()["id"]

    response2 = await create_task(
        async_client, str(test_job.id), admin_token, "In progress task"
    )
    task2_id = response2.json()["id"]

    # Update second task to in_progress
    await async_client.post(
        f"/api/v1/jobs/{test_job.id}/tasks/{task2_id}/status",
        json={"status": "in_progress"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    # Filter by status=todo
    response = await async_client.get(
        f"/api/v1/jobs/{test_job.id}/tasks?status=todo",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert all(task["status"] == "todo" for task in data)


@pytest.mark.asyncio
async def test_list_tasks_filter_by_assignee(
    async_client: AsyncClient, admin_token: str, test_job, test_crew_profile, test_db, test_tenant
):
    """List can filter by assignee_id"""
    from app.models import CrewProfile

    # Create another crew profile
    await test_db.execute(
        text(f"SET LOCAL app.current_tenant_id = '{test_tenant.id}'")
    )

    other_crew = CrewProfile(
        user_id=None,  # Not linked to user for this test
        tenant_id=test_tenant.id,
        phone="+9876543210",
    )
    test_db.add(other_crew)
    await test_db.flush()

    # Create tasks with different assignees
    await create_task(
        async_client,
        str(test_job.id),
        admin_token,
        "Task for crew 1",
        assignee_id=str(test_crew_profile.id),
    )
    await create_task(
        async_client,
        str(test_job.id),
        admin_token,
        "Task for crew 2",
        assignee_id=str(other_crew.id),
    )

    # Filter by assignee
    response = await async_client.get(
        f"/api/v1/jobs/{test_job.id}/tasks?assignee_id={test_crew_profile.id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert all(task["assignee_id"] == str(test_crew_profile.id) for task in data)


@pytest.mark.asyncio
async def test_get_task(
    async_client: AsyncClient, admin_token: str, test_job
):
    """Get single task by ID"""
    create_response = await create_task(
        async_client, str(test_job.id), admin_token, "Get me"
    )
    task_id = create_response.json()["id"]

    response = await async_client.get(
        f"/api/v1/jobs/{test_job.id}/tasks/{task_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == task_id
    assert data["title"] == "Get me"


@pytest.mark.asyncio
async def test_get_task_not_found(
    async_client: AsyncClient, admin_token: str, test_job
):
    """Get returns 404 for non-existent task"""
    import uuid
    fake_id = str(uuid.uuid4())

    response = await async_client.get(
        f"/api/v1/jobs/{test_job.id}/tasks/{fake_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_admin_update_task(
    async_client: AsyncClient, admin_token: str, test_job
):
    """Admin can update task fields via PATCH"""
    create_response = await create_task(
        async_client, str(test_job.id), admin_token, "Original title"
    )
    task_id = create_response.json()["id"]

    response = await async_client.patch(
        f"/api/v1/jobs/{test_job.id}/tasks/{task_id}",
        json={"title": "Updated title"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated title"


@pytest.mark.asyncio
async def test_admin_update_task_status_via_transition(
    async_client: AsyncClient, admin_token: str, test_job
):
    """Admin can update task status via transition endpoint"""
    create_response = await create_task(
        async_client, str(test_job.id), admin_token, "Do this"
    )
    task_id = create_response.json()["id"]

    response = await async_client.post(
        f"/api/v1/jobs/{test_job.id}/tasks/{task_id}/status",
        json={"status": "in_progress"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "in_progress"


@pytest.mark.asyncio
async def test_crew_update_assigned_task_status(
    async_client: AsyncClient, admin_token: str, crew_token: str, test_job, test_crew_profile
):
    """Crew can update status of tasks assigned to them"""
    # Create task assigned to crew
    create_response = await create_task(
        async_client,
        str(test_job.id),
        admin_token,
        "Crew task",
        assignee_id=str(test_crew_profile.id),
    )
    task_id = create_response.json()["id"]

    # Crew updates status
    response = await async_client.post(
        f"/api/v1/jobs/{test_job.id}/tasks/{task_id}/status",
        json={"status": "in_progress"},
        headers={"Authorization": f"Bearer {crew_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "in_progress"


@pytest.mark.asyncio
async def test_crew_cannot_update_unassigned_task(
    async_client: AsyncClient, admin_token: str, crew_token: str, test_job
):
    """Crew cannot update tasks not assigned to them (403 Forbidden)"""
    # Create task without assignee
    create_response = await create_task(
        async_client, str(test_job.id), admin_token, "Unassigned task"
    )
    task_id = create_response.json()["id"]

    # Crew tries to update status
    response = await async_client.post(
        f"/api/v1/jobs/{test_job.id}/tasks/{task_id}/status",
        json={"status": "in_progress"},
        headers={"Authorization": f"Bearer {crew_token}"},
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_invalid_status_transition(
    async_client: AsyncClient, admin_token: str, test_job
):
    """Invalid state transitions return 400"""
    # Create task and move to done
    create_response = await create_task(
        async_client, str(test_job.id), admin_token, "Task"
    )
    task_id = create_response.json()["id"]

    await async_client.post(
        f"/api/v1/jobs/{test_job.id}/tasks/{task_id}/status",
        json={"status": "done"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    # Try invalid transition done -> todo
    response = await async_client.post(
        f"/api/v1/jobs/{test_job.id}/tasks/{task_id}/status",
        json={"status": "todo"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_task_message_link(
    async_client: AsyncClient, admin_token: str, test_job
):
    """Task can reference a message via message_id FK"""
    # Create a message first
    message_response = await async_client.post(
        f"/api/v1/jobs/{test_job.id}/messages",
        json={"content": "We need to set up cameras by 9am"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    message_id = message_response.json()["id"]

    # Create task linked to message
    response = await create_task(
        async_client,
        str(test_job.id),
        admin_token,
        "Set up cameras",
        message_id=message_id,
    )

    assert response.status_code == 201
    data = response.json()
    assert data["message_id"] == message_id


@pytest.mark.asyncio
async def test_admin_delete_task(
    async_client: AsyncClient, admin_token: str, test_job
):
    """Admin can delete task and it's removed from database"""
    create_response = await create_task(
        async_client, str(test_job.id), admin_token, "Delete me"
    )
    task_id = create_response.json()["id"]

    # Delete task
    delete_response = await async_client.delete(
        f"/api/v1/jobs/{test_job.id}/tasks/{task_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert delete_response.status_code == 204

    # Verify task is gone
    get_response = await async_client.get(
        f"/api/v1/jobs/{test_job.id}/tasks/{task_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert get_response.status_code == 404
