"""File storage utilities for job attachments"""

from pathlib import Path
import aiofiles
import uuid
from fastapi import UploadFile

try:
    import magic
    HAS_MAGIC = True
except ImportError:
    HAS_MAGIC = False

# Configuration
UPLOAD_DIR = Path("uploads")
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB

# Allowed MIME types for file uploads
ALLOWED_MIME_TYPES = {
    # Images
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/webp",
    # Documents
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",  # .docx
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",  # .xlsx
    # Video
    "video/mp4",
    "video/quicktime",
    # Text
    "text/plain",
}


def get_upload_path(tenant_id: str, job_id: str, file_id: str, extension: str) -> Path:
    """
    Generate storage path for uploaded file.

    Args:
        tenant_id: Tenant UUID
        job_id: Job UUID
        file_id: File UUID
        extension: File extension (including leading dot)

    Returns:
        Path object with structure: uploads/tenant_id/job_id/file_id.ext
    """
    return UPLOAD_DIR / tenant_id / job_id / f"{file_id}{extension}"


async def save_upload(
    tenant_id: str,
    job_id: str,
    file: UploadFile,
    max_size: int = MAX_FILE_SIZE,
) -> tuple[Path, str, int]:
    """
    Save uploaded file to disk with validation.

    Args:
        tenant_id: Tenant UUID
        job_id: Job UUID
        file: FastAPI UploadFile object
        max_size: Maximum file size in bytes

    Returns:
        Tuple of (storage_path, mime_type, file_size)

    Raises:
        ValueError: If file too large or MIME type not allowed
    """
    # Read file content
    content = await file.read()
    file_size = len(content)

    # Check file size
    if file_size > max_size:
        raise ValueError(f"File too large: {file_size} bytes (max {max_size})")

    # Detect MIME type (python-magic if available, otherwise trust upload header)
    if HAS_MAGIC:
        mime_type = magic.from_buffer(content, mime=True)
    else:
        mime_type = file.content_type or "application/octet-stream"

    # Validate MIME type
    if mime_type not in ALLOWED_MIME_TYPES:
        raise ValueError(f"MIME type not allowed: {mime_type}")

    # Generate UUID filename preserving original extension
    file_id = str(uuid.uuid4())
    original_filename = file.filename or "unnamed"
    extension = Path(original_filename).suffix  # e.g., ".pdf"

    # Build storage path
    storage_path = get_upload_path(tenant_id, job_id, file_id, extension)

    # Create directory if needed
    storage_path.parent.mkdir(parents=True, exist_ok=True)

    # Write file asynchronously
    async with aiofiles.open(storage_path, "wb") as f:
        await f.write(content)

    return storage_path, mime_type, file_size


async def delete_file(storage_path: Path) -> None:
    """
    Delete file from storage.

    Args:
        storage_path: Path to file on disk
    """
    if storage_path.exists():
        storage_path.unlink()
