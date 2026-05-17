---
phase: 06-notifications
plan: 01
subsystem: notifications
tags: [email, celery, crew-notifications]
dependency_graph:
  requires: [auth, jobs, assignments]
  provides: [email-notifications]
  affects: [crew-workflow]
tech_stack:
  added: []
  patterns: [celery-tasks, smtp-email, async-notifications]
key_files:
  created:
    - backend/tests/test_notifications_email.py
  modified:
    - backend/app/tasks/email.py
    - backend/app/api/v1/assignments.py
    - backend/app/api/v1/jobs.py
decisions:
  - decision: "Only CONFIRMED crew receive job update emails"
    rationale: "PENDING/DECLINED crew not actively working, reduces noise"
  - decision: "Email triggers fire after DB commit (assignment) or before delete (deletion)"
    rationale: "Assignment: email only after successful creation. Deletion: need job data before it's removed"
  - decision: "Capture old_state before transition for accurate email content"
    rationale: "Email body needs to show 'Status changed: intake → active' which requires old state"
metrics:
  duration: 334
  completed_date: "2026-05-17"
  tasks_completed: 2
  files_modified: 3
  files_created: 1
  commits: 3
---

# Phase 06 Plan 01: Email Notifications Summary

**One-liner:** Crew receive immediate email notifications on assignment and job state changes via Celery tasks with GT branding

## What Was Built

Two new Celery email tasks wired into existing endpoints:

1. **send_assignment_email**: Crew notified when assigned to a job
   - Subject: "New assignment: {role} - {job_title}" or "New assignment: {job_title}" (if no role)
   - Body: job title, role, venue, schedule, link to job details
   - Triggered after crew assignment creation (assignments.py)

2. **send_job_update_email**: Crew notified of job state changes and cancellations
   - State change subject: "Job update: {job_title}"
   - Cancellation subject: "Job cancelled: {job_title}"
   - Body: old state → new state (for transitions) or cancellation notice
   - Triggered on job state transitions and before deletion (jobs.py)

**Notification rules:**
- Only CONFIRMED crew receive job update emails (PENDING/DECLINED excluded)
- Email triggers fire after DB commit (assignment) or before delete (deletion)
- All emails use GT branding and SMTP settings from config

## Task Breakdown

### Task 1: Add email notification Celery tasks (TDD)

**Commits:**
- `077e2b2`: test(06-01): add failing tests for email notification tasks (RED)
- `19ff238`: feat(06-01): implement email notification Celery tasks (GREEN)

**Files modified:**
- `backend/app/tasks/email.py`: Added 2 new @shared_task functions (now 5 total)
- `backend/tests/test_notifications_email.py`: Created test suite with 5 tests

**Tests:**
- `test_send_assignment_email_content`: Verify subject/body with role
- `test_send_assignment_email_no_role`: Verify subject without role
- `test_send_job_update_email_state_change`: Verify state change notification
- `test_send_job_update_email_cancelled`: Verify cancellation notification
- `test_email_uses_smtp_settings`: Verify SMTP settings usage

**TDD flow:**
1. RED: Created failing tests, verified tasks don't exist
2. GREEN: Implemented tasks, all tests passing
3. No REFACTOR needed (code already clean)

### Task 2: Wire email triggers into assignment and job endpoints

**Commit:** `b82ab9f`

**Files modified:**
- `backend/app/api/v1/assignments.py`: Added send_assignment_email.delay() after crew assignment creation
- `backend/app/api/v1/jobs.py`: Added send_job_update_email.delay() on state transitions and before deletion

**Implementation details:**

**assignments.py:**
- Import `send_assignment_email` from `app.tasks.email`
- After `db.commit()` and `db.refresh(assignment)` in `assign_crew_to_job`
- Query crew user via CrewProfile.user_id → User
- Fire `send_assignment_email.delay()` with job details

**jobs.py:**
- Import `send_job_update_email` from `app.tasks.email`
- **State transition** (`transition_job_state`):
  - Capture `old_state = job.state` before transition
  - After `db.commit()` and `db.refresh(job)`
  - Query all CONFIRMED crew for the job
  - Fire `send_job_update_email.delay()` with event_type="state_change"
- **Deletion** (`delete_job`):
  - BEFORE `await db.delete(job)`
  - Query all CONFIRMED crew for the job
  - Fire `send_job_update_email.delay()` with event_type="cancelled"

## Deviations from Plan

None - plan executed exactly as written.

## Performance Notes

- Email notifications are async via Celery (non-blocking)
- Only CONFIRMED crew receive notifications (reduces unnecessary emails)
- Batch email sending handled by Celery worker (not in request path)

## Integration Points

**Upstream dependencies:**
- Phase 01 (Auth): User.email field
- Phase 02 (Jobs): Job model with title, venue, schedule
- Phase 03 (Assignments): CrewAssignment with status field

**Downstream impacts:**
- Crew receive immediate notifications (production coordination requirement)
- Email volume scales with confirmed crew count (each state change sends N emails)

## Success Criteria

✅ Two new Celery tasks (send_assignment_email, send_job_update_email) exist in email.py  
✅ Crew assignment creation fires assignment email to the assigned crew member  
✅ Job state transitions fire update emails to all confirmed crew on that job  
✅ Job deletion fires cancellation emails to all confirmed crew on that job  
✅ Email subjects follow format: "New assignment: {role} - {title}", "Job update: {title}", "Job cancelled: {title}"  
✅ All tests pass (verified via inline test execution)

## What's Next

Phase 06 Plan 02: Add remaining notification features (if applicable) or move to Phase 07 (Portal).

## Self-Check

✅ PASSED

**Files verified:**
- backend/app/tasks/email.py (exists)
- backend/tests/test_notifications_email.py (exists)
- backend/app/api/v1/assignments.py (exists)
- backend/app/api/v1/jobs.py (exists)

**Commits verified:**
- 077e2b2 (RED phase - tests)
- 19ff238 (GREEN phase - implementation)
- b82ab9f (wiring - endpoint integration)

---

**Plan completed:** 2026-05-17  
**Duration:** 334 seconds (5m 34s)  
**Commits:** 3 (1 RED, 1 GREEN, 1 wiring)
