"""Task state transition validation logic"""

from app.models.task import TaskStatus

# Define allowed state transitions
# Each state maps to a list of valid next states
TASK_TRANSITIONS = {
    TaskStatus.TODO: [TaskStatus.IN_PROGRESS, TaskStatus.DONE],
    TaskStatus.IN_PROGRESS: [TaskStatus.TODO, TaskStatus.DONE],
    TaskStatus.DONE: [TaskStatus.IN_PROGRESS],  # Can reopen
}


def can_transition(from_status: TaskStatus, to_status: TaskStatus) -> bool:
    """
    Check if state transition is allowed.

    Args:
        from_status: Current task status
        to_status: Desired new status

    Returns:
        True if transition is valid, False otherwise
    """
    allowed = TASK_TRANSITIONS.get(from_status, [])
    return to_status in allowed


def validate_transition(from_status: TaskStatus, to_status: TaskStatus) -> None:
    """
    Validate state transition and raise exception if invalid.

    Args:
        from_status: Current task status
        to_status: Desired new status

    Raises:
        ValueError: If transition is not allowed
    """
    if not can_transition(from_status, to_status):
        raise ValueError(
            f"Invalid transition: {from_status.value} -> {to_status.value}"
        )
