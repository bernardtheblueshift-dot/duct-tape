"""Tests for file upload, serve, and management endpoints"""

import pytest
from unittest.mock import patch, AsyncMock
from pathlib import Path
from httpx import AsyncClient
from app.models.user import User, UserRole
from app.models.tenant import Tenant
from app.core.security import create_access_token


# Helper function to reduce boilerplate
async def upload_file(
    client: AsyncClient,
    job_id: str,
    token: str,
    filename: str = "test.jpg",
    content: bytes = b"fake image content",
    content_type: str = "image/jpeg",
):
    """Helper to upload a file to a job"""
    response = await client.post(
        f"/api/v1/jobs/{job_id}/files/",
        files={"file": (filename, content, content_type)},
        headers={"Authorization": f"Bearer {token}"},
    )
    return response


@pytest.mark.asyncio
async def test_upload_file(async_client: AsyncClient, admin_token: str, test_job):
    """Admin can upload file with valid MIME type"""
    # Mock save_upload to avoid filesystem operations
    mock_path = Path("/tmp/test.jpg")
    with patch("app.api.v1.files.save_upload") as mock_save:
        mock_save.return_value = (mock_path, "image/jpeg", 1024)

        response = await upload_file(async_client, str(test_job.id), admin_token)

        assert response.status_code == 201
        data = response.json()
        assert data["original_filename"] == "test.jpg"
        assert data["mime_type"] == "image/jpeg"
        assert data["file_size"] == 1024
        assert data["job_id"] == str(test_job.id)
        assert "id" in data
        assert "uploader_id" in data
        assert "created_at" in data


@pytest.mark.asyncio
async def test_upload_file_as_crew(async_client: AsyncClient, crew_token: str, test_job):
    """Crew can upload files (require_active allows crew)"""
    mock_path = Path("/tmp/test.jpg")
    with patch("app.api.v1.files.save_upload") as mock_save:
        mock_save.return_value = (mock_path, "image/jpeg", 2048)

        response = await upload_file(async_client, str(test_job.id), crew_token)

        assert response.status_code == 201
        data = response.json()
        assert data["original_filename"] == "test.jpg"


@pytest.mark.asyncio
async def test_upload_file_invalid_mime(async_client: AsyncClient, admin_token: str, test_job):
    """Upload rejects invalid MIME type with 400"""
    with patch("app.api.v1.files.save_upload") as mock_save:
        mock_save.side_effect = ValueError("MIME type not allowed: application/x-executable")

        response = await upload_file(
            async_client,
            str(test_job.id),
            admin_token,
            filename="bad.exe",
            content_type="application/x-executable",
        )

        assert response.status_code == 400
        assert "MIME type not allowed" in response.json()["detail"]


@pytest.mark.asyncio
async def test_upload_file_too_large(async_client: AsyncClient, admin_token: str, test_job):
    """Upload rejects files exceeding 100MB limit with 400"""
    with patch("app.api.v1.files.save_upload") as mock_save:
        mock_save.side_effect = ValueError("File too large: 104857601 bytes (max 104857600)")

        response = await upload_file(async_client, str(test_job.id), admin_token)

        assert response.status_code == 400
        assert "File too large" in response.json()["detail"]


@pytest.mark.asyncio
async def test_upload_file_nonexistent_job(async_client: AsyncClient, admin_token: str):
    """Upload to nonexistent job returns 404"""
    from uuid import uuid4

    mock_path = Path("/tmp/test.jpg")
    with patch("app.api.v1.files.save_upload") as mock_save:
        mock_save.return_value = (mock_path, "image/jpeg", 1024)

        response = await upload_file(async_client, str(uuid4()), admin_token)

        assert response.status_code == 404
        assert "Job not found" in response.json()["detail"]


@pytest.mark.asyncio
async def test_list_files(async_client: AsyncClient, admin_token: str, test_job):
    """List files returns all files for job ordered by created_at desc"""
    mock_path = Path("/tmp/test.jpg")
    with patch("app.api.v1.files.save_upload") as mock_save:
        mock_save.return_value = (mock_path, "image/jpeg", 1024)

        # Upload 3 files
        await upload_file(async_client, str(test_job.id), admin_token, filename="file1.jpg")
        await upload_file(async_client, str(test_job.id), admin_token, filename="file2.pdf")
        mock_save.return_value = (mock_path, "video/mp4", 2048)
        await upload_file(
            async_client, str(test_job.id), admin_token, filename="file3.mp4", content_type="video/mp4"
        )

        # List files
        response = await async_client.get(
            f"/api/v1/jobs/{test_job.id}/files/",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        files = response.json()
        assert len(files) >= 3
        # Verify ordered by created_at desc (most recent first)
        assert files[0]["original_filename"] == "file3.mp4"
        assert files[1]["original_filename"] == "file2.pdf"
        assert files[2]["original_filename"] == "file1.jpg"


@pytest.mark.asyncio
async def test_get_file_metadata(async_client: AsyncClient, admin_token: str, test_job):
    """Get file metadata returns full file record"""
    mock_path = Path("/tmp/test.jpg")
    with patch("app.api.v1.files.save_upload") as mock_save:
        mock_save.return_value = (mock_path, "image/jpeg", 1024)

        # Upload file
        upload_response = await upload_file(async_client, str(test_job.id), admin_token)
        file_id = upload_response.json()["id"]

        # Get metadata
        response = await async_client.get(
            f"/api/v1/files/{file_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == file_id
        assert data["original_filename"] == "test.jpg"
        assert data["mime_type"] == "image/jpeg"
        assert data["file_size"] == 1024


@pytest.mark.asyncio
async def test_get_file_not_found(async_client: AsyncClient, admin_token: str):
    """Get metadata for nonexistent file returns 404"""
    from uuid import uuid4

    response = await async_client.get(
        f"/api/v1/files/{uuid4()}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 404
    assert "File not found" in response.json()["detail"]


@pytest.mark.asyncio
async def test_serve_file_with_mime(async_client: AsyncClient, admin_token: str, test_job, tmp_path):
    """Serve file returns file with correct Content-Type header"""
    # Create a real temp file for this test
    temp_file = tmp_path / "test.jpg"
    temp_file.write_bytes(b"fake image content")

    mock_path = Path(str(temp_file))
    with patch("app.api.v1.files.save_upload") as mock_save:
        mock_save.return_value = (mock_path, "image/jpeg", 18)

        # Upload file
        upload_response = await upload_file(async_client, str(test_job.id), admin_token)
        file_id = upload_response.json()["id"]

        # Serve/download file
        response = await async_client.get(
            f"/api/v1/files/{file_id}/download",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "image/jpeg"
        assert response.content == b"fake image content"


@pytest.mark.asyncio
async def test_serve_file_missing_from_disk(async_client: AsyncClient, admin_token: str, test_job):
    """Serve file returns 404 if DB record exists but file missing from disk"""
    mock_path = Path("/tmp/nonexistent.jpg")
    with patch("app.api.v1.files.save_upload") as mock_save:
        mock_save.return_value = (mock_path, "image/jpeg", 1024)

        # Upload file (creates DB record)
        upload_response = await upload_file(async_client, str(test_job.id), admin_token)
        file_id = upload_response.json()["id"]

        # Try to serve (file doesn't exist on disk)
        response = await async_client.get(
            f"/api/v1/files/{file_id}/download",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 404
        assert "File not found on disk" in response.json()["detail"]


@pytest.mark.asyncio
async def test_admin_delete_file(async_client: AsyncClient, admin_token: str, test_job):
    """Admin can delete file, removing DB record and disk file"""
    mock_path = Path("/tmp/test.jpg")
    with patch("app.api.v1.files.save_upload") as mock_save, \
         patch("app.api.v1.files.delete_file") as mock_delete:
        mock_save.return_value = (mock_path, "image/jpeg", 1024)

        # Upload file
        upload_response = await upload_file(async_client, str(test_job.id), admin_token)
        file_id = upload_response.json()["id"]

        # Delete file
        delete_response = await async_client.delete(
            f"/api/v1/files/{file_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert delete_response.status_code == 204

        # Verify file no longer accessible
        get_response = await async_client.get(
            f"/api/v1/files/{file_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert get_response.status_code == 404

        # Verify delete_file was called
        mock_delete.assert_called_once()


@pytest.mark.asyncio
async def test_crew_cannot_delete_file(async_client: AsyncClient, admin_token: str, crew_token: str, test_job):
    """Crew cannot delete files (admin only)"""
    mock_path = Path("/tmp/test.jpg")
    with patch("app.api.v1.files.save_upload") as mock_save:
        mock_save.return_value = (mock_path, "image/jpeg", 1024)

        # Upload file as admin
        upload_response = await upload_file(async_client, str(test_job.id), admin_token)
        file_id = upload_response.json()["id"]

        # Try to delete as crew
        response = await async_client.delete(
            f"/api/v1/files/{file_id}",
            headers={"Authorization": f"Bearer {crew_token}"},
        )

        assert response.status_code == 403
        assert "Admin access required" in response.json()["detail"]


@pytest.mark.asyncio
async def test_file_metadata(async_client: AsyncClient, admin_token: str, test_job, test_admin_user):
    """File response contains all required metadata fields"""
    mock_path = Path("/tmp/test.jpg")
    with patch("app.api.v1.files.save_upload") as mock_save:
        mock_save.return_value = (mock_path, "image/jpeg", 1024)

        # Upload file
        response = await upload_file(async_client, str(test_job.id), admin_token)

        assert response.status_code == 201
        data = response.json()

        # Verify all metadata fields present
        assert "id" in data
        assert data["job_id"] == str(test_job.id)
        assert data["uploader_id"] == str(test_admin_user.id)
        assert data["original_filename"] == "test.jpg"
        assert data["mime_type"] == "image/jpeg"
        assert data["file_size"] == 1024
        assert "created_at" in data
        assert "updated_at" in data


@pytest.mark.asyncio
async def test_file_tenant_isolation(
    async_client: AsyncClient,
    admin_token: str,
    test_job,
    test_db,
):
    """Files from one tenant cannot be accessed by another tenant"""
    from app.models import Tenant, User, UserRole
    from app.core.security import hash_password

    # Create second tenant and user
    tenant2 = Tenant(name="Other Company", timezone="UTC")
    test_db.add(tenant2)
    await test_db.flush()

    user2 = User(
        email="admin2@test.com",
        hashed_password=hash_password("password123"),
        tenant_id=tenant2.id,
        role=UserRole.ADMIN,
        is_active=True,
    )
    test_db.add(user2)
    await test_db.flush()

    # Create token for second tenant
    token2 = create_access_token(
        str(user2.id),
        str(tenant2.id),
        user2.role.value,
    )

    # Upload file as tenant 1
    mock_path = Path("/tmp/test.jpg")
    with patch("app.api.v1.files.save_upload") as mock_save:
        mock_save.return_value = (mock_path, "image/jpeg", 1024)

        upload_response = await upload_file(async_client, str(test_job.id), admin_token)
        file_id = upload_response.json()["id"]

        # Try to access file as tenant 2
        response = await async_client.get(
            f"/api/v1/files/{file_id}",
            headers={"Authorization": f"Bearer {token2}"},
        )

        # RLS should block access - file not found for this tenant
        assert response.status_code == 404
