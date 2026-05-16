---
phase: 05-coordination-layer
plan: 03
subsystem: coordination
tags: [tasks, state-machine, permissions, api]

dependency_graph:
  requires:
    - phase: 05
      plan: 01
      artifacts: [Task model, TaskStatus enum, task_state.py]
    - phase: 02
      plan: 01
      artifacts: [Job model]
    - phase: 03
      plan: 01
      artifacts: [CrewProfile model]
  provides:
    - artifact: tasks REST API
      endpoints: [POST create, GET list, GET single, PATCH update, POST status, DELETE]
      consumers: [frontend, mobile]
    - artifact: task state machine
      validators: [can_transition, validate_transition]
      consumers: [tasks API, frontend]
  affects:
    - file: backend/app/main.py
      change: registered tasks router

tech_stack:
  added:
    - sqlalchemy case() for priority ordering
  patterns:
    - bidirectional state transitions
    - dual permission model (admin-only create, crew can update status)
    - message linking via FK validation

key_files:
  created:
    - backend/app/api/v1/tasks.py: 6 endpoints (create, list, get, update, status, delete)
    - backend/tests/test_task_state.py: 8 unit tests for state machine
    - backend/tests/test_tasks.py: 15 integration tests for API
  modified:
    - backend/app/main.py: registered tasks router

decisions:
  - choice: Admin-only task creation, crew can update status
    rationale: Tasks originate from admin planning workflow; crew need autonomy to update progress
    alternatives: [crew can create tasks, fully locked to admin]
  - choice: Priority ordering via case() expression
    rationale: TaskPriority enum has no inherent order; manual mapping needed for urgent > high > medium > low
    alternatives: [custom SQL, separate priority_order column]
  - choice: Dedicated status transition endpoint
    rationale: Enables validation via state machine, matches job state pattern
    alternatives: [status field in PATCH, automatic transitions]

metrics:
  duration: 151
  tasks_completed: 2
  tasks_planned: 2
  files_created: 3
  files_modified: 1
  tests_added: 23
  commits: 2
  deviations: 0
  completion_date: 2026-05-16
---

# Phase 05 Plan 03: Task Management API Summary

**One-liner:** Task CRUD API with admin-only creation, crew status updates, and bidirectional state machine (todo/in_progress/done)

## What Got Built

### Tasks REST API (backend/app/api/v1/tasks.py)
- **POST /api/v1/jobs/{job_id}/tasks** — Create task (admin only)
  - Validates job exists
  - Validates assignee (CrewProfile) exists if provided
  - Validates message exists in same job if message_id provided
  - Defaults to TODO status, MEDIUM priority
- **GET /api/v1/jobs/{job_id}/tasks** — List tasks with filtering
  - Filter by status (todo/in_progress/done)
  - Filter by assignee_id
  - Ordered by priority (urgent > high > medium > low) then created_at ascending
  - Uses SQLAlchemy case() for enum-to-int priority mapping
- **GET /api/v1/jobs/{job_id}/tasks/{task_id}** — Get single task
- **PATCH /api/v1/jobs/{job_id}/tasks/{task_id}** — Update task fields (admin only)
  - Partial updates via exclude_unset=True
  - Validates assignee exists if being updated
- **POST /api/v1/jobs/{job_id}/tasks/{task_id}/status** — Update status (admin OR assigned crew)
  - Permission check: admin can update any, crew can only update tasks assigned to them
  - Queries CrewProfile by user_id to match task.assignee_id
  - Validates transition via can_transition() before applying
- **DELETE /api/v1/jobs/{job_id}/tasks/{task_id}** — Delete task (admin only)

### State Machine (already implemented in 05-01)
- TASK_TRANSITIONS dict in app/core/task_state.py
- TODO → [IN_PROGRESS, DONE]
- IN_PROGRESS → [TODO, DONE] (bidirectional)
- DONE → [IN_PROGRESS] (reopen allowed)
- DONE → TODO blocked (invalid transition)

### Test Coverage
- **test_task_state.py** — 8 unit tests for state machine
  - All valid transitions tested
  - Invalid transition (done → todo) raises ValueError
  - validate_transition() raises on invalid, passes on valid
- **test_tasks.py** — 15 integration tests
  - test_admin_create_task (201, title + priority)
  - test_admin_create_task_with_assignee (assignee_id FK)
  - test_crew_cannot_create_task (403)
  - test_list_tasks (≥3 tasks returned)
  - test_list_tasks_filter_by_status (only todo tasks)
  - test_list_tasks_filter_by_assignee (assignee_id filter)
  - test_get_task (200, matches ID)
  - test_get_task_not_found (404)
  - test_admin_update_task (PATCH title change)
  - test_admin_update_task_status_via_transition (POST status)
  - test_crew_update_assigned_task_status (crew can update own)
  - test_crew_cannot_update_unassigned_task (403)
  - test_invalid_status_transition (400 for done → todo)
  - test_task_message_link (message_id FK validation)
  - test_admin_delete_task (204, then 404 on GET)

## How It Works

### Permission Model
- **Admin-only creation** — Tasks originate from admin planning workflow
- **Admin-only field updates** — Only admin can change title, description, assignee, priority, deadline
- **Crew can update status** — Crew need autonomy to mark progress on assigned tasks
  - Permission check: `current_user.role == ADMIN` OR `task.assignee_id == crew_profile.id`
  - Queries CrewProfile by `user_id == current_user.id` to match against `task.assignee_id`

### Priority Ordering
SQLAlchemy case() expression maps TaskPriority enum to integers for sorting:
```python
priority_order = case(
    (Task.priority == TaskPriority.URGENT, 4),
    (Task.priority == TaskPriority.HIGH, 3),
    (Task.priority == TaskPriority.MEDIUM, 2),
    (Task.priority == TaskPriority.LOW, 1),
    else_=0,
)
query.order_by(priority_order.desc(), Task.created_at.asc())
```

### Message Linking
Tasks can optionally reference a Message via `message_id` FK:
- Validates message exists in the same job: `Message.id == message_id AND Message.job_id == job_id`
- Returns 404 "Message not found" if invalid
- Enables "create task from message" workflow in frontend

### State Transitions
- Dedicated `/status` endpoint separates status updates from field updates
- Validates via `can_transition(task.status, new_status)` before applying
- Returns 400 with clear error message if transition invalid
- Matches job state transition pattern from Phase 2

## Requirements Coverage

- **TASK-01** — Admin can create task with title, assignee, priority, deadline ✓
- **TASK-02** — Admin can update task fields ✓
- **TASK-03** — Both admin and crew can update status via transition endpoint ✓
  - Admin can update any task
  - Crew can only update tasks assigned to them
- **TASK-04** — Crew cannot create tasks (403) ✓
- **TASK-05** — Task can reference message via message_id FK ✓

## Deviations from Plan

None - plan executed exactly as written.

## Known Issues / Tech Debt

None.

## Next Steps

Phase 5 Plan 04 will implement file upload and attachment linking to jobs/messages/tasks.

## Self-Check: PASSED

Created files exist:
- backend/app/api/v1/tasks.py ✓
- backend/tests/test_task_state.py ✓
- backend/tests/test_tasks.py ✓

Modified files exist:
- backend/app/main.py ✓

Commits exist:
- 4aab944 (Task 1: tasks REST API) ✓
- ad05f23 (Task 2: tests) ✓

Router loads successfully:
- `python3 -c "from app.api.v1.tasks import router"` exits 0 ✓
- 6 routes registered ✓

State machine verified:
- `can_transition(TODO, IN_PROGRESS)` returns True ✓
- `can_transition(DONE, IN_PROGRESS)` returns True (reopen) ✓
- `can_transition(DONE, TODO)` returns False (blocked) ✓
