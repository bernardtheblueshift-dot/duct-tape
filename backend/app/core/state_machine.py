"""Job state transition validation logic"""

from app.models.job import JobState

# Define allowed state transitions
# Each state maps to a list of valid next states
ALLOWED_TRANSITIONS = {
    JobState.INTAKE: [JobState.SIMMER, JobState.ACTIVE],
    JobState.SIMMER: [JobState.ACTIVE, JobState.INTAKE],  # Can return to intake
    JobState.ACTIVE: [JobState.COMPLETE, JobState.SIMMER],  # Can pause to simmer
    JobState.COMPLETE: [],  # Terminal state - no outbound transitions
}


def can_transition(from_state: JobState, to_state: JobState) -> bool:
    """
    Check if state transition is allowed.

    Args:
        from_state: Current job state
        to_state: Desired new state

    Returns:
        True if transition is valid, False otherwise
    """
    allowed = ALLOWED_TRANSITIONS.get(from_state, [])
    return to_state in allowed


def validate_transition(from_state: JobState, to_state: JobState) -> None:
    """
    Validate state transition and raise exception if invalid.

    Args:
        from_state: Current job state
        to_state: Desired new state

    Raises:
        ValueError: If transition is not allowed
    """
    if not can_transition(from_state, to_state):
        raise ValueError(f"Invalid transition: {from_state.value} -> {to_state.value}")
