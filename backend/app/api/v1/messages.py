"""Message endpoints for job-scoped threaded messaging with WebSocket broadcast"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from uuid import UUID

from app.database import get_db
from app.dependencies import get_current_tenant, get_current_user
from app.core.permissions import require_active
from app.models import Message, Job, JobFile, User, MessageLastSeen
from app.schemas.message import MessageCreate, MessageResponse
from app.core.websocket_manager import manager
from datetime import datetime, timezone

router = APIRouter(prefix="/api/v1/jobs/{job_id}/messages", tags=["messages"])


@router.post("/", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def create_message(
    job_id: UUID,
    message_data: MessageCreate,
    current_user: User = Depends(require_active),
    tenant_id: str = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """
    Create message in job conversation (admin and crew can post).

    Validates job exists, optional parent message exists, and file IDs are valid.
    Broadcasts new message to WebSocket subscribers.
    """
    # Verify job exists
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )

    # Verify parent message exists if reply_to_id is set
    if message_data.reply_to_id:
        parent_result = await db.execute(
            select(Message).where(
                Message.id == message_data.reply_to_id,
                Message.job_id == job_id,
            )
        )
        parent_message = parent_result.scalar_one_or_none()
        if not parent_message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parent message not found",
            )

    # Validate file IDs if provided
    file_objects = []
    if message_data.file_ids:
        file_result = await db.execute(
            select(JobFile).where(
                JobFile.id.in_(message_data.file_ids),
                JobFile.job_id == job_id,
            )
        )
        file_objects = list(file_result.scalars().all())
        if len(file_objects) != len(message_data.file_ids):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file IDs",
            )

    # Create message
    message = Message(
        job_id=job_id,
        user_id=current_user.id,
        content=message_data.content,
        reply_to_id=message_data.reply_to_id,
        tenant_id=tenant_id,
    )

    # Attach files if provided
    if file_objects:
        message.files = file_objects

    db.add(message)
    await db.commit()
    await db.refresh(message)

    # Broadcast to WebSocket subscribers
    await manager.broadcast_to_job(
        str(job_id),
        {
            "type": "message",
            "data": MessageResponse.model_validate(message).model_dump(mode="json"),
        },
    )

    return message


@router.get("/", response_model=List[MessageResponse])
async def list_messages(
    job_id: UUID,
    search: str | None = None,
    limit: int = Query(default=100, le=500, ge=1),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(require_active),
    tenant_id: str = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """
    List messages for a job with optional search.

    Both admin and crew can read messages.
    Results ordered oldest first (chat-style).
    Updates last-seen timestamp for this user+job.

    Query parameters:
    - limit: Max results (1-500, default 100)
    - offset: Skip N results (default 0)
    """
    query = select(Message).where(Message.job_id == job_id)

    # Apply search filter if provided
    if search:
        query = query.where(Message.content.ilike(f"%{search}%"))

    # Order by created_at ascending (oldest first, chat-style)
    query = query.order_by(Message.created_at.asc())

    # Apply pagination
    query = query.limit(limit).offset(offset)

    result = await db.execute(query)
    messages = result.scalars().all()

    # Update last-seen timestamp for this user+job
    existing_last_seen = await db.execute(
        select(MessageLastSeen).where(
            MessageLastSeen.user_id == current_user.id,
            MessageLastSeen.job_id == job_id,
        )
    )
    last_seen = existing_last_seen.scalar_one_or_none()

    now = datetime.now(timezone.utc)
    if last_seen:
        last_seen.last_seen_at = now
    else:
        last_seen = MessageLastSeen(
            user_id=current_user.id,
            job_id=job_id,
            last_seen_at=now,
            tenant_id=tenant_id,
        )
        db.add(last_seen)
    await db.commit()

    return messages


@router.get("/{message_id}", response_model=MessageResponse)
async def get_message(
    job_id: UUID,
    message_id: UUID,
    tenant_id: str = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """
    Get a single message by ID.

    Verifies message belongs to the specified job.
    """
    result = await db.execute(
        select(Message).where(
            Message.id == message_id,
            Message.job_id == job_id,
        )
    )
    message = result.scalar_one_or_none()

    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found",
        )

    return message
