"""Unit tests for task state transition validation logic"""

import pytest
from app.models.task import TaskStatus
from app.core.task_state import TASK_TRANSITIONS, can_transition, validate_transition


def test_todo_to_in_progress():
    """Test that transition from todo to in_progress is allowed"""
    assert can_transition(TaskStatus.TODO, TaskStatus.IN_PROGRESS) is True


def test_todo_to_done():
    """Test that transition from todo to done is allowed"""
    assert can_transition(TaskStatus.TODO, TaskStatus.DONE) is True


def test_in_progress_to_done():
    """Test that transition from in_progress to done is allowed"""
    assert can_transition(TaskStatus.IN_PROGRESS, TaskStatus.DONE) is True


def test_in_progress_to_todo():
    """Test that backward transition from in_progress to todo is allowed"""
    assert can_transition(TaskStatus.IN_PROGRESS, TaskStatus.TODO) is True


def test_done_to_in_progress():
    """Test that reopen transition from done to in_progress is allowed"""
    assert can_transition(TaskStatus.DONE, TaskStatus.IN_PROGRESS) is True


def test_done_to_todo():
    """Test that direct transition from done to todo is blocked"""
    assert can_transition(TaskStatus.DONE, TaskStatus.TODO) is False


def test_validate_transition_raises():
    """Test that validate_transition raises ValueError for invalid transitions"""
    with pytest.raises(ValueError, match="Invalid transition: done -> todo"):
        validate_transition(TaskStatus.DONE, TaskStatus.TODO)


def test_validate_transition_valid():
    """Test that validate_transition does not raise for valid transitions"""
    # Should not raise
    validate_transition(TaskStatus.TODO, TaskStatus.IN_PROGRESS)
    validate_transition(TaskStatus.TODO, TaskStatus.DONE)
    validate_transition(TaskStatus.IN_PROGRESS, TaskStatus.TODO)
    validate_transition(TaskStatus.IN_PROGRESS, TaskStatus.DONE)
    validate_transition(TaskStatus.DONE, TaskStatus.IN_PROGRESS)
