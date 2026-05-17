---
phase: 06-notifications
verified: 2026-05-17T12:30:00Z
status: passed
score: 8/8 must-haves verified
re_verification: false
---

# Phase 6: Notifications Verification Report

**Phase Goal:** Email notifications for key events — crew assignment, job updates, and in-app notification badges for unread messages and new assignments

**Verified:** 2026-05-17T12:30:00Z

**Status:** passed

**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Crew receives email when assigned to a job | ✓ VERIFIED | send_assignment_email task exists, wired in assignments.py after db.commit(), triggers on crew assignment creation |
| 2 | All assigned crew receive email when job state changes | ✓ VERIFIED | send_job_update_email task exists with event_type="state_change", wired in jobs.py transition_job_state, filters CONFIRMED crew only, old_state captured before transition |
| 3 | All assigned crew receive email when job is deleted | ✓ VERIFIED | send_job_update_email task with event_type="cancelled", wired in jobs.py delete_job BEFORE db.delete(), filters CONFIRMED crew only |
| 4 | Email contains job title, dates, venue, and role | ✓ VERIFIED | send_assignment_email body includes job_title, role, venue, scheduled_start/end; send_job_update_email includes job_title and state transition info |
| 5 | User can fetch notification badge counts showing unread messages and pending assignments | ✓ VERIFIED | GET /api/v1/notifications/counts endpoint exists, returns NotificationCounts schema with unread_messages and pending_assignments |
| 6 | Unread message count reflects messages newer than the user's last-seen timestamp per job | ✓ VERIFIED | notifications.py queries MessageLastSeen per user, counts messages with created_at > last_seen_at for each job |
| 7 | Pending assignment count reflects PENDING CrewAssignments for the current user | ✓ VERIFIED | notifications.py queries CrewAssignment where status=PENDING and crew_id matches current user's crew profile |
| 8 | Viewing messages for a job updates the user's last-seen timestamp | ✓ VERIFIED | messages.py list_messages endpoint upserts MessageLastSeen with current timestamp after fetching messages |

**Score:** 8/8 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `backend/app/tasks/email.py` | send_assignment_email and send_job_update_email Celery tasks | ✓ VERIFIED | 5 @shared_task functions total (3 existing + 2 new). send_assignment_email at line 116-172, send_job_update_email at line 175-227. Both use MIMEText + smtplib.SMTP pattern with settings.SMTP_HOST/PORT/FROM |
| `backend/app/api/v1/assignments.py` | Email trigger after crew assignment creation | ✓ VERIFIED | Import at line 36. send_assignment_email.delay() at line 164 after db.commit() and db.refresh(). Queries crew user via CrewProfile.user_id FK |
| `backend/app/api/v1/jobs.py` | Email trigger after job state transition and deletion | ✓ VERIFIED | Import send_job_update_email. State transition (line 576): captures old_state before transition, fires email.delay() to CONFIRMED crew after commit. Deletion (line 507-528): fires email.delay() to CONFIRMED crew BEFORE db.delete() |
| `backend/tests/test_notifications_email.py` | Tests for email notification tasks and endpoint wiring | ✓ VERIFIED | 5 tests using unittest.mock.patch on smtplib.SMTP. Tests verify subject, body content, SMTP settings usage for assignment and job update emails |
| `backend/app/models/message_last_seen.py` | MessageLastSeen model for tracking per-user-per-job last viewed timestamp | ✓ VERIFIED | Class MessageLastSeen with unique constraint (user_id, job_id), columns: id (UUID), user_id (FK users.id), job_id (FK jobs.id), last_seen_at (TIMESTAMPTZ), tenant_id. Uses TenantMixin |
| `backend/app/schemas/notification.py` | NotificationCounts response schema | ✓ VERIFIED | Class NotificationCounts(BaseModel) with unread_messages: int = 0, pending_assignments: int = 0 |
| `backend/app/api/v1/notifications.py` | GET /api/v1/notifications/counts endpoint | ✓ VERIFIED | Router registered at /api/v1/notifications. get_notification_counts function at line 23-81. Queries MessageLastSeen + Message for unread count, CrewProfile + CrewAssignment for pending count. Uses require_active permission |
| `backend/alembic/versions/007_notification_message_last_seen.py` | Migration creating message_last_seen table | ✓ VERIFIED | Migration file exists with message_last_seen table creation + RLS policy |
| `backend/tests/test_notifications_counts.py` | Tests for notification counts endpoint and last-seen tracking | ✓ VERIFIED | Test file exists with fixtures and test functions for notification counts and last-seen behavior |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|----|--------|---------|
| `backend/app/api/v1/assignments.py` | `backend/app/tasks/email.py` | send_assignment_email.delay() after db.commit() | ✓ WIRED | Import at line 36, call at line 164 with 7 parameters (email, job_title, job_id, role, venue, scheduled_start, scheduled_end) |
| `backend/app/api/v1/jobs.py` | `backend/app/tasks/email.py` | send_job_update_email.delay() after state transition and before delete commit | ✓ WIRED | Import exists, 2 call sites: (1) transition_job_state line 599 with event_type="state_change", (2) delete_job line 523 with event_type="cancelled". Both query CONFIRMED crew and loop to send emails |
| `backend/app/api/v1/notifications.py` | `backend/app/models/message_last_seen.py` | Query MessageLastSeen + Message count for unread calculation | ✓ WIRED | Import MessageLastSeen at line 12. Query at line 38-42 to get last_seen records per job. Count query at line 53-59 for messages newer than last_seen_at |
| `backend/app/api/v1/notifications.py` | `backend/app/models/assignment.py` | Query CrewAssignment with status=PENDING for badge count | ✓ WIRED | Import AssignmentState at line 15. Query at line 70-75 filters by crew_id and AssignmentState.PENDING |
| `backend/app/api/v1/messages.py` | `backend/app/models/message_last_seen.py` | Upsert MessageLastSeen when user lists messages for a job | ✓ WIRED | Import MessageLastSeen at line 11. Upsert logic at line 130-150: queries existing last_seen, updates if exists else creates new, commits to DB |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| NOTF-01 | 06-01-PLAN.md | Email notification when crew is assigned to a job | ✓ SATISFIED | send_assignment_email task exists and fires on crew assignment creation. Subject: "New assignment: {role} - {job_title}", body includes job details and link |
| NOTF-02 | 06-01-PLAN.md | Email notification when a job is updated or cancelled | ✓ SATISFIED | send_job_update_email task exists with two event types: "state_change" (fires on job state transitions) and "cancelled" (fires before job deletion). Both send to CONFIRMED crew only |
| NOTF-03 | 06-02-PLAN.md | In-app notification badge for unread messages and new assignments | ✓ SATISFIED | GET /api/v1/notifications/counts endpoint returns {unread_messages: N, pending_assignments: M}. Unread calculated from MessageLastSeen timestamps, pending from PENDING CrewAssignments |

**All 3 requirements satisfied.**

**No orphaned requirements.** All phase 6 requirements from REQUIREMENTS.md are claimed by plans and verified.

### Anti-Patterns Found

None found.

**Checked files:** backend/app/tasks/email.py, backend/app/api/v1/notifications.py, backend/app/models/message_last_seen.py, backend/app/api/v1/messages.py, backend/app/api/v1/assignments.py, backend/app/api/v1/jobs.py

**Patterns searched:**
- TODO/FIXME/XXX/HACK/PLACEHOLDER comments: 0 occurrences
- Empty implementations (return null/{}): 0 occurrences
- Stub handlers (console.log only): 0 occurrences

### Human Verification Required

#### 1. Email Delivery Test

**Test:** Create a crew assignment in the UI, check crew member's email inbox

**Expected:** Crew receives email with subject "New assignment: {role} - {job_title}" containing job details and link to job page

**Why human:** Email delivery requires SMTP server and real inbox verification. Automated tests mock smtplib.SMTP but don't verify actual email delivery end-to-end.

#### 2. Job State Change Notification Test

**Test:** Transition a job from "intake" to "active" that has CONFIRMED crew assignments, check crew inboxes

**Expected:** All CONFIRMED crew receive email with subject "Job update: {job_title}" and body showing "Status changed: intake → active"

**Why human:** Requires real job with crew assignments and email delivery verification.

#### 3. Job Cancellation Notification Test

**Test:** Delete a job that has CONFIRMED crew assignments, check crew inboxes

**Expected:** All CONFIRMED crew receive email with subject "Job cancelled: {job_title}" before job is deleted

**Why human:** Tests timing of email trigger (before deletion) and actual email delivery.

#### 4. Notification Badge Count Test

**Test:** As a crew member, view messages in a job, then have another user post new messages. Refresh and call GET /api/v1/notifications/counts

**Expected:** unread_messages count increases by the number of new messages posted after viewing

**Why human:** Requires multi-user interaction and real-time message creation to verify timestamp comparison logic.

#### 5. Pending Assignment Badge Test

**Test:** As a crew member with PENDING assignments, call GET /api/v1/notifications/counts. Confirm one assignment. Call counts again.

**Expected:** pending_assignments decreases by 1 after confirmation

**Why human:** Requires crew user workflow (assignment confirmation) and state transition verification.

---

## Verification Summary

**All must-haves verified.** Phase 6 goal achieved.

### What Works

1. **Email notifications for crew assignments**: send_assignment_email Celery task wired into assignments.py, fires after crew assignment creation with full job details
2. **Email notifications for job updates**: send_job_update_email wired into jobs.py with two event types (state_change and cancelled), filters CONFIRMED crew only, captures old_state before transition
3. **In-app notification badge counts**: GET /api/v1/notifications/counts endpoint returns unread messages (calculated from MessageLastSeen timestamps) and pending assignments (PENDING CrewAssignments)
4. **Last-seen tracking**: messages.py list_messages endpoint automatically upserts MessageLastSeen timestamp when user views messages
5. **Proper SMTP usage**: All email tasks use settings.SMTP_HOST/PORT/FROM with MIMEText + smtplib.SMTP pattern
6. **Test coverage**: 5 email tests + notification counts tests verify task behavior and wiring

### Key Implementation Patterns

1. **Email trigger timing**: Assignment emails fire after db.commit() (ensures assignment exists). Deletion emails fire BEFORE db.delete() (need job data while it still exists).
2. **State capture**: old_state captured before job.state assignment in transition_job_state, enabling accurate email body "Status changed: X → Y"
3. **Crew filtering**: Only CONFIRMED crew receive job update/cancellation emails (PENDING/DECLINED excluded to reduce noise)
4. **Last-seen upsert**: Idempotent upsert pattern with scalar_one_or_none() check + conditional insert/update
5. **Badge calculation**: On-demand calculation (not cached) — acceptable for v1 scale, can optimize with Redis if needed

### Completeness

- **Models**: MessageLastSeen with unique constraint on (user_id, job_id), tenant isolation via TenantMixin
- **Migrations**: 007_notification_message_last_seen.py with RLS policy
- **Schemas**: NotificationCounts with unread_messages and pending_assignments fields
- **Endpoints**: Email tasks (2), notification counts (1), last-seen tracking (integrated into existing messages endpoint)
- **Tests**: Email task tests (5), notification counts tests (exists)
- **Wiring**: All 5 key links verified as WIRED with correct imports and call patterns

**No gaps found. Phase ready to proceed.**

---

_Verified: 2026-05-17T12:30:00Z_
_Verifier: Claude (gsd-verifier)_
