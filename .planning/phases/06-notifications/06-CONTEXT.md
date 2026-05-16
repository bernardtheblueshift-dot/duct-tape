# Phase 6: Notifications - Context

**Gathered:** 2026-05-17
**Status:** Ready for planning

<domain>
## Phase Boundary

Email notifications for crew assignment and job state changes, plus in-app notification badge counts for unread messages and pending assignments. Email uses existing Celery + SMTP infrastructure. In-app counts are computed on-the-fly, no separate Notification table.

</domain>

<decisions>
## Implementation Decisions

### Email trigger points
- Assignment email: fire from POST /assignments/crew endpoint after creating the assignment (inline Celery task call, same pattern as verification email)
- Job update email: triggered on state transitions and job deletion only — NOT on every field edit (avoids email fatigue)
- Email to all assigned crew when job state changes (intake→active, active→complete, etc.) or job is deleted
- Use existing Celery task pattern from tasks/email.py — add new task functions alongside send_verification_email

### In-app notification model
- Computed counts endpoint: GET /notifications/counts returns {unread_messages: N, pending_assignments: M}
- No separate Notification table — counts derived from existing data:
  - unread_messages: count messages newer than last_seen_at per user-job pair
  - pending_assignments: count CrewAssignments with status=PENDING for current user
- Last-seen tracking: new table (user_id, job_id, last_seen_at) — updated when user views messages
- Frontend polls via REST every 30-60 seconds (no WebSocket extension for v1)

### Email content & delivery
- Plain text format (same as existing verification/invitation emails)
- Assignment email content: job title, scheduled dates, venue, assigned role, link to app
- Subject format: "New assignment: {role} - {job_title}"
- Job state change email: job title, old state → new state, link to app
- Per-event delivery, immediately via Celery (no batching/digests — production events are time-sensitive)

### Claude's Discretion
- Email template structure (how to organize plain text body)
- MessageLastSeen model name and exact column types
- Error handling for SMTP failures (retry strategy)
- Whether to skip email if crew has no email (shouldn't happen with current User model)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

No external specs — requirements fully captured in decisions above and in `.planning/REQUIREMENTS.md` (NOTF-01, NOTF-02, NOTF-03).

### Existing codebase patterns
- `backend/app/tasks/email.py` — Existing Celery email tasks (send_verification_email, send_password_reset_email, send_invitation_email) — NEW tasks follow this exact pattern
- `backend/app/config.py` — SMTP settings (SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, SMTP_FROM, FRONTEND_URL)
- `backend/app/api/v1/assignments.py` — Assignment creation endpoint (add email trigger here)
- `backend/app/api/v1/jobs.py` — Job state transition endpoint (add email trigger here)
- `backend/app/models/assignment.py` — CrewAssignment with status enum (PENDING for badge count)
- `backend/app/models/message.py` — Message model with created_at (for unread calculation)
- `backend/app/dependencies.py` — get_current_user, get_current_tenant

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `tasks/email.py` Celery task pattern: MIMEText + smtplib, settings-driven SMTP config
- `config.py` SMTP settings: already configured for verification/invitation emails
- `AssignmentState.PENDING` enum: use for pending assignment badge count
- `get_current_user` dependency: identify which user to compute counts for

### Established Patterns
- Celery @shared_task decorator for async email sending
- Plain text MIMEText format
- Settings-based SMTP configuration
- TenantMixin/TimestampMixin on all models

### Integration Points
- `assignments.py` endpoint: add Celery task call after creating crew assignment
- `jobs.py` state transition endpoint: add Celery task call after successful transition, querying all assigned crew
- New notifications router: GET /notifications/counts for badge data
- New MessageLastSeen model: tracks per-user-per-job last viewed timestamp
- messages.py: update last_seen_at when user GETs messages for a job

</code_context>

<specifics>
## Specific Ideas

No specific requirements — open to standard approaches

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 06-notifications*
*Context gathered: 2026-05-17*
