"""Tests for job state transition validation logic"""

import pytest
from app.models.job import JobState
from app.core.state_machine import (
    ALLOWED_TRANSITIONS,
    can_transition,
    validate_transition,
)


def test_intake_to_simmer_allowed():
    """Test that transition from intake to simmer is allowed"""
    assert can_transition(JobState.INTAKE, JobState.SIMMER) is True


def test_intake_to_active_allowed():
    """Test that transition from intake to active is allowed"""
    assert can_transition(JobState.INTAKE, JobState.ACTIVE) is True


def test_simmer_to_active_allowed():
    """Test that transition from simmer to active is allowed"""
    assert can_transition(JobState.SIMMER, JobState.ACTIVE) is True


def test_simmer_to_intake_allowed():
    """Test that backward transition from simmer to intake is allowed"""
    assert can_transition(JobState.SIMMER, JobState.INTAKE) is True


def test_active_to_complete_allowed():
    """Test that transition from active to complete is allowed"""
    assert can_transition(JobState.ACTIVE, JobState.COMPLETE) is True


def test_active_to_simmer_allowed():
    """Test that backward transition from active to simmer is allowed"""
    assert can_transition(JobState.ACTIVE, JobState.SIMMER) is True


def test_complete_is_terminal():
    """Test that complete state has no outbound transitions"""
    assert ALLOWED_TRANSITIONS[JobState.COMPLETE] == []
    assert can_transition(JobState.COMPLETE, JobState.INTAKE) is False
    assert can_transition(JobState.COMPLETE, JobState.SIMMER) is False
    assert can_transition(JobState.COMPLETE, JobState.ACTIVE) is False


def test_intake_to_complete_blocked():
    """Test that skipping states (intake -> complete) is blocked"""
    assert can_transition(JobState.INTAKE, JobState.COMPLETE) is False


def test_validate_transition_raises_on_invalid():
    """Test that validate_transition raises ValueError for invalid transitions"""
    with pytest.raises(ValueError, match="Invalid transition: intake -> complete"):
        validate_transition(JobState.INTAKE, JobState.COMPLETE)


def test_validate_transition_succeeds_on_valid():
    """Test that validate_transition does not raise for valid transitions"""
    # Should not raise
    validate_transition(JobState.INTAKE, JobState.SIMMER)
    validate_transition(JobState.INTAKE, JobState.ACTIVE)
    validate_transition(JobState.SIMMER, JobState.ACTIVE)
    validate_transition(JobState.ACTIVE, JobState.COMPLETE)
