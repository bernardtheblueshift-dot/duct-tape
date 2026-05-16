"""Tests for message CRUD and search endpoints"""

import pytest
from httpx import AsyncClient
from uuid import uuid4
from app.models import Message


async def create_message(
    client: AsyncClient,
    job_id: str,
    token: str,
    content: str,
    reply_to_id: str | None = None,
    file_ids: list[str] | None = None,
):
    """Helper to create a message"""
    payload = {"content": content}
    if reply_to_id:
        payload["reply_to_id"] = reply_to_id
    if file_ids:
        payload["file_ids"] = file_ids

    response = await client.post(
        f"/api/v1/jobs/{job_id}/messages/",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    return response


@pytest.mark.asyncio
async def test_create_message(async_client: AsyncClient, admin_token: str, test_job):
    """Admin can create message with valid content"""
    response = await create_message(
        async_client, str(test_job.id), admin_token, "Hello team"
    )

    assert response.status_code == 201
    data = response.json()
    assert data["content"] == "Hello team"
    assert data["job_id"] == str(test_job.id)
    assert data["reply_to_id"] is None
    assert "id" in data
    assert "created_at" in data


@pytest.mark.asyncio
async def test_create_message_as_crew(async_client: AsyncClient, crew_token: str, test_job):
    """Crew can post messages"""
    response = await create_message(
        async_client, str(test_job.id), crew_token, "Crew message"
    )

    assert response.status_code == 201
    data = response.json()
    assert data["content"] == "Crew message"


@pytest.mark.asyncio
async def test_create_message_with_reply(async_client: AsyncClient, admin_token: str, test_job):
    """Can create message as reply to existing message"""
    # Create first message
    first_response = await create_message(
        async_client, str(test_job.id), admin_token, "Original message"
    )
    first_id = first_response.json()["id"]

    # Create reply
    reply_response = await create_message(
        async_client, str(test_job.id), admin_token, "Reply message", reply_to_id=first_id
    )

    assert reply_response.status_code == 201
    data = reply_response.json()
    assert data["content"] == "Reply message"
    assert data["reply_to_id"] == first_id


@pytest.mark.asyncio
async def test_create_message_invalid_reply(async_client: AsyncClient, admin_token: str, test_job):
    """Creating message with invalid reply_to_id returns 404"""
    random_id = str(uuid4())
    response = await create_message(
        async_client, str(test_job.id), admin_token, "Reply message", reply_to_id=random_id
    )

    assert response.status_code == 404
    assert "Parent message not found" in response.json()["detail"]


@pytest.mark.asyncio
async def test_create_message_empty_content(async_client: AsyncClient, admin_token: str, test_job):
    """Creating message with empty content returns 422"""
    response = await async_client.post(
        f"/api/v1/jobs/{test_job.id}/messages/",
        json={"content": ""},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_list_messages(
    async_client: AsyncClient, admin_token: str, test_job, test_db, test_tenant
):
    """List messages returns all messages ordered by created_at ascending"""
    from sqlalchemy import text
    import asyncio

    # Set RLS context
    await test_db.execute(
        text(f"SET LOCAL app.current_tenant_id = '{test_tenant.id}'")
    )

    # Create 3 messages with small delays to ensure different timestamps
    msg1 = Message(
        job_id=test_job.id,
        user_id=uuid4(),
        content="First message",
        tenant_id=test_tenant.id,
    )
    test_db.add(msg1)
    await test_db.flush()
    await asyncio.sleep(0.01)

    msg2 = Message(
        job_id=test_job.id,
        user_id=uuid4(),
        content="Second message",
        tenant_id=test_tenant.id,
    )
    test_db.add(msg2)
    await test_db.flush()
    await asyncio.sleep(0.01)

    msg3 = Message(
        job_id=test_job.id,
        user_id=uuid4(),
        content="Third message",
        tenant_id=test_tenant.id,
    )
    test_db.add(msg3)
    await test_db.flush()

    # List messages
    response = await async_client.get(
        f"/api/v1/jobs/{test_job.id}/messages/",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    # Verify oldest first ordering
    assert data[0]["content"] == "First message"
    assert data[1]["content"] == "Second message"
    assert data[2]["content"] == "Third message"


@pytest.mark.asyncio
async def test_search_messages(
    async_client: AsyncClient, admin_token: str, test_job, test_db, test_tenant
):
    """Search messages filters by content using ILIKE"""
    from sqlalchemy import text

    # Set RLS context
    await test_db.execute(
        text(f"SET LOCAL app.current_tenant_id = '{test_tenant.id}'")
    )

    # Create messages with different content
    msg1 = Message(
        job_id=test_job.id,
        user_id=uuid4(),
        content="Camera setup complete",
        tenant_id=test_tenant.id,
    )
    msg2 = Message(
        job_id=test_job.id,
        user_id=uuid4(),
        content="Audio check needed",
        tenant_id=test_tenant.id,
    )
    msg3 = Message(
        job_id=test_job.id,
        user_id=uuid4(),
        content="Camera angle adjusted",
        tenant_id=test_tenant.id,
    )
    test_db.add_all([msg1, msg2, msg3])
    await test_db.flush()

    # Search for "camera"
    response = await async_client.get(
        f"/api/v1/jobs/{test_job.id}/messages/?search=camera",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    contents = [m["content"] for m in data]
    assert "Camera setup complete" in contents
    assert "Camera angle adjusted" in contents
    assert "Audio check needed" not in contents


@pytest.mark.asyncio
async def test_search_messages_case_insensitive(
    async_client: AsyncClient, admin_token: str, test_job, test_db, test_tenant
):
    """Search is case-insensitive (ILIKE)"""
    from sqlalchemy import text

    # Set RLS context
    await test_db.execute(
        text(f"SET LOCAL app.current_tenant_id = '{test_tenant.id}'")
    )

    # Create message with lowercase content
    msg = Message(
        job_id=test_job.id,
        user_id=uuid4(),
        content="lighting setup complete",
        tenant_id=test_tenant.id,
    )
    test_db.add(msg)
    await test_db.flush()

    # Search with uppercase
    response = await async_client.get(
        f"/api/v1/jobs/{test_job.id}/messages/?search=LIGHTING",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["content"] == "lighting setup complete"


@pytest.mark.asyncio
async def test_get_message(async_client: AsyncClient, admin_token: str, test_job, test_db, test_tenant):
    """Get single message by ID"""
    from sqlalchemy import text

    # Set RLS context
    await test_db.execute(
        text(f"SET LOCAL app.current_tenant_id = '{test_tenant.id}'")
    )

    # Create message
    msg = Message(
        job_id=test_job.id,
        user_id=uuid4(),
        content="Test message",
        tenant_id=test_tenant.id,
    )
    test_db.add(msg)
    await test_db.flush()

    # Get message
    response = await async_client.get(
        f"/api/v1/jobs/{test_job.id}/messages/{msg.id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["content"] == "Test message"
    assert data["id"] == str(msg.id)


@pytest.mark.asyncio
async def test_get_message_not_found(async_client: AsyncClient, admin_token: str, test_job):
    """Get message with invalid ID returns 404"""
    random_id = str(uuid4())
    response = await async_client.get(
        f"/api/v1/jobs/{test_job.id}/messages/{random_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_message_markdown_content(async_client: AsyncClient, admin_token: str, test_job):
    """Messages store markdown content as-is without server-side rendering"""
    markdown_content = "**bold** and *italic* text with [link](https://example.com)"
    response = await create_message(
        async_client, str(test_job.id), admin_token, markdown_content
    )

    assert response.status_code == 201
    data = response.json()
    # Content should be stored exactly as provided (no HTML rendering)
    assert data["content"] == markdown_content
    assert "**bold**" in data["content"]
    assert "<strong>" not in data["content"]
