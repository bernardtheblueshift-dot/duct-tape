"""File upload, serve, and management endpoints for job attachments"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import FileResponse as FastAPIFileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from pathlib import Path

from app.database import get_db
from app.dependencies import get_current_tenant
from app.core.permissions import require_admin, require_active
from app.models.job import Job
from app.models.file import JobFile
from app.models.user import User
from app.schemas.file import FileResponse
from app.core.file_storage import save_upload, delete_file

# Router for job-scoped file operations (upload, list)
job_files_router = APIRouter(
    prefix="/api/v1/jobs/{job_id}/files",
    tags=["files"],
)

# Router for file-scoped operations (serve, delete by file ID)
files_router = APIRouter(
    prefix="/api/v1/files",
    tags=["files"],
)


@job_files_router.post("/", response_model=FileResponse, status_code=status.HTTP_201_CREATED)
async def upload_file(
    job_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(require_active),
    tenant_id: str = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload file to job (authenticated users).

    Validates MIME type server-side using python-magic (not trusting client headers).
    Enforces 100MB file size limit.
    Saves to uploads/{tenant_id}/{job_id}/ with UUID filename.

    Returns file metadata including uploader_id, original filename, size, and MIME type.
    """
    # Verify job exists
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )

    # Save file with validation
    try:
        storage_path, mime_type, file_size = await save_upload(
            str(tenant_id), str(job_id), file
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    # Create database record
    job_file = JobFile(
        job_id=job_id,
        uploader_id=current_user.id,
        original_filename=file.filename or "unnamed",
        storage_path=str(storage_path),
        mime_type=mime_type,
        file_size=file_size,
        tenant_id=tenant_id,
    )

    db.add(job_file)
    await db.commit()
    await db.refresh(job_file)

    return job_file


@job_files_router.get("/", response_model=List[FileResponse])
async def list_files(
    job_id: str,
    current_user: User = Depends(require_active),
    tenant_id: str = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """
    List all files for a job (authenticated users).

    Returns files ordered by upload time (most recent first).
    RLS automatically filters by tenant.
    """
    # Query files for this job
    query = (
        select(JobFile)
        .where(JobFile.job_id == job_id)
        .order_by(JobFile.created_at.desc())
    )

    result = await db.execute(query)
    files = result.scalars().all()

    return files


@files_router.get("/{file_id}", response_model=FileResponse)
async def get_file_metadata(
    file_id: str,
    current_user: User = Depends(require_active),
    tenant_id: str = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """
    Get file metadata by ID (authenticated users).

    Returns upload metadata including uploader, filename, size, MIME type, timestamps.
    RLS ensures tenant isolation - no cross-tenant file access.
    """
    result = await db.execute(select(JobFile).where(JobFile.id == file_id))
    file_record = result.scalar_one_or_none()

    if not file_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found",
        )

    return file_record


@files_router.get("/{file_id}/download")
async def serve_file(
    file_id: str,
    current_user: User = Depends(require_active),
    tenant_id: str = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """
    Serve/download file with correct Content-Type header (authenticated users).

    RLS ensures tenant isolation - no cross-tenant file access.
    Returns 404 if file record exists but file missing from disk.
    """
    # Get file record
    result = await db.execute(select(JobFile).where(JobFile.id == file_id))
    file_record = result.scalar_one_or_none()

    if not file_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found",
        )

    # Verify file exists on disk
    file_path = Path(file_record.storage_path)
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found on disk",
        )

    # Serve file with correct MIME type and original filename
    return FastAPIFileResponse(
        path=str(file_path),
        media_type=file_record.mime_type,
        filename=file_record.original_filename,
    )


@files_router.delete("/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_file_endpoint(
    file_id: str,
    current_user: User = Depends(require_admin),
    tenant_id: str = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete file from database and disk (admin only).

    Removes both DB record and physical file from storage.
    RLS ensures tenant isolation.
    """
    # Get file record
    result = await db.execute(select(JobFile).where(JobFile.id == file_id))
    file_record = result.scalar_one_or_none()

    if not file_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found",
        )

    # Delete from database first
    await db.delete(file_record)
    await db.commit()

    # Then delete from disk
    await delete_file(Path(file_record.storage_path))
