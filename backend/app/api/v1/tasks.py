"""Task management endpoints with admin-only creation and state transition validation"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, case
from typing import List
from uuid import UUID

from app.database import get_db
from app.dependencies import get_current_tenant
from app.core.permissions import require_admin, require_active
from app.core.task_state import can_transition
from app.models import Job, Task, TaskStatus, TaskPriority, CrewProfile, Message, User
from app.models.user import UserRole
from app.schemas.task import TaskCreate, TaskUpdate, TaskStatusUpdate, TaskResponse

router = APIRouter(prefix="/api/v1/jobs/{job_id}/tasks", tags=["tasks"])


@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    job_id: UUID,
    task_data: TaskCreate,
    current_user: User = Depends(require_admin),
    tenant_id: str = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """
    Create new task linked to job (admin only).

    Validates job exists, assignee exists if provided, and message exists if provided.
    Task defaults to TODO status and MEDIUM priority.
    """
    # Verify job exists
    job_result = await db.execute(select(Job).where(Job.id == job_id))
    job = job_result.scalar_one_or_none()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )

    # Verify assignee exists if provided
    if task_data.assignee_id:
        assignee_result = await db.execute(
            select(CrewProfile).where(CrewProfile.id == task_data.assignee_id)
        )
        assignee = assignee_result.scalar_one_or_none()

        if not assignee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assignee not found",
            )

    # Verify message exists in same job if provided
    if task_data.message_id:
        message_result = await db.execute(
            select(Message).where(
                Message.id == task_data.message_id,
                Message.job_id == job_id,
            )
        )
        message = message_result.scalar_one_or_none()

        if not message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found",
            )

    # Create task
    task = Task(
        **task_data.model_dump(),
        job_id=job_id,
        tenant_id=tenant_id,
    )

    db.add(task)
    await db.commit()
    await db.refresh(task)
    return task


@router.get("/", response_model=List[TaskResponse])
async def list_tasks(
    job_id: UUID,
    status: TaskStatus | None = None,
    assignee_id: UUID | None = None,
    current_user: User = Depends(require_active),
    tenant_id: str = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """
    List tasks for a job with optional filtering.

    Query parameters:
    - status: Filter by task status (todo/in_progress/done)
    - assignee_id: Filter by assigned crew member

    Results ordered by priority (urgent > high > medium > low) then created_at ascending.
    Both admin and crew can view tasks.
    """
    # Build query
    query = select(Task).where(Task.job_id == job_id)

    # Apply status filter
    if status:
        query = query.where(Task.status == status)

    # Apply assignee filter
    if assignee_id:
        query = query.where(Task.assignee_id == assignee_id)

    # Order by priority then created_at
    # Priority ordering: URGENT=4, HIGH=3, MEDIUM=2, LOW=1
    priority_order = case(
        (Task.priority == TaskPriority.URGENT, 4),
        (Task.priority == TaskPriority.HIGH, 3),
        (Task.priority == TaskPriority.MEDIUM, 2),
        (Task.priority == TaskPriority.LOW, 1),
        else_=0,
    )
    query = query.order_by(priority_order.desc(), Task.created_at.asc())

    result = await db.execute(query)
    tasks = result.scalars().all()
    return list(tasks)


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    job_id: UUID,
    task_id: UUID,
    current_user: User = Depends(require_active),
    tenant_id: str = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """
    Get task by ID.

    Both admin and crew can view tasks.
    """
    result = await db.execute(
        select(Task).where(Task.id == task_id, Task.job_id == job_id)
    )
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    return task


@router.patch("/{task_id}", response_model=TaskResponse)
async def update_task(
    job_id: UUID,
    task_id: UUID,
    task_update: TaskUpdate,
    current_user: User = Depends(require_admin),
    tenant_id: str = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """
    Update task fields (admin only).

    Excludes status field - use dedicated status transition endpoint.
    Only updates fields provided in request (partial updates supported).
    """
    # Find task
    result = await db.execute(
        select(Task).where(Task.id == task_id, Task.job_id == job_id)
    )
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    # Verify assignee exists if being updated
    update_data = task_update.model_dump(exclude_unset=True)
    if "assignee_id" in update_data and update_data["assignee_id"] is not None:
        assignee_result = await db.execute(
            select(CrewProfile).where(CrewProfile.id == update_data["assignee_id"])
        )
        assignee = assignee_result.scalar_one_or_none()

        if not assignee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assignee not found",
            )

    # Apply updates
    for key, value in update_data.items():
        setattr(task, key, value)

    await db.commit()
    await db.refresh(task)
    return task


@router.post("/{task_id}/status", response_model=TaskResponse)
async def update_task_status(
    job_id: UUID,
    task_id: UUID,
    status_update: TaskStatusUpdate,
    current_user: User = Depends(require_active),
    tenant_id: str = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """
    Update task status with state machine validation (admin or assigned crew).

    Admin can update any task status.
    Crew can only update status of tasks assigned to them.
    Validates transition is allowed by task state machine.
    """
    # Find task
    result = await db.execute(
        select(Task).where(Task.id == task_id, Task.job_id == job_id)
    )
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    # Check permission: admin OR assigned crew
    if current_user.role != UserRole.ADMIN:
        # Get crew profile for current user
        crew_result = await db.execute(
            select(CrewProfile).where(CrewProfile.user_id == current_user.id)
        )
        crew = crew_result.scalar_one_or_none()

        # Check if crew is assigned to this task
        if not crew or task.assignee_id != crew.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this task",
            )

    # Validate transition
    if not can_transition(task.status, status_update.status):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid transition: {task.status.value} -> {status_update.status.value}",
        )

    # Update status
    task.status = status_update.status
    await db.commit()
    await db.refresh(task)
    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    job_id: UUID,
    task_id: UUID,
    current_user: User = Depends(require_admin),
    tenant_id: str = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete task (admin only).

    Hard delete - task is permanently removed from database.
    """
    result = await db.execute(
        select(Task).where(Task.id == task_id, Task.job_id == job_id)
    )
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    await db.delete(task)
    await db.commit()
