# Phase 5: Coordination Layer (Messaging + Tasks + Files) - Context

**Gathered:** 2026-05-16
**Status:** Ready for planning

<domain>
## Phase Boundary

Job-scoped collaboration tools that ship together: threaded messaging with real-time WebSocket delivery, task management with assignees and deadlines, and file sharing with tenant-isolated local storage. All three features are scoped to individual jobs. Messages, tasks, and files can cross-reference each other.

</domain>

<decisions>
## Implementation Decisions

### Messaging model & WebSockets
- Flat message list with optional reply_to_id (parent message reference) — not nested threads
- Messages stored as markdown text, frontend renders formatting
- Single multiplexed WebSocket connection per user — client subscribes to job IDs, server routes messages to matching subscriptions
- JWT token in WebSocket connection query param for authentication
- ILIKE search on message content within a job (same pattern as jobs/crew search)
- WebSocket delivers messages only (not task or file events) for v1

### Task workflow & permissions
- Admin creates tasks and sets assignees — crew cannot create tasks
- Both admin and assigned crew can update task status
- State machine: todo → in_progress → done, with backward transitions allowed (done→in_progress to reopen, in_progress→todo to deprioritize)
- Follows existing state_machine.py pattern from Phase 2
- Optional message_id FK on task — links task to the message that prompted it (one-to-one)
- Deadline is informational TIMESTAMPTZ field — no auto-escalation, no background jobs
- Priority levels: low, medium, high, urgent (enum)

### File storage & upload
- Local filesystem storage, organized by tenant_id/job_id/ directory structure
- 100MB per file upload limit
- Backend serves files via authenticated endpoint — frontend handles preview rendering (img tags, pdf.js)
- No server-side thumbnail generation for v1
- Hard delete — removes both DB record and file on disk
- Upload metadata tracked: uploader (user_id), upload timestamp, original filename, file size, MIME type

### Cross-feature integration
- Messages can reference files via optional file_ids (many-to-many — a message can attach multiple files)
- Tasks reference messages via optional message_id FK (one-to-one)
- JobResponse shows summary counts + recent items: message_count, unread_count, latest 3 messages; task counts by status, overdue count; file_count, latest 3 files
- Full lists of messages/tasks/files via separate per-job endpoints

### Claude's Discretion
- WebSocket connection management (heartbeat, reconnection strategy)
- File MIME type validation (allowed types list)
- Message pagination strategy (cursor vs offset)
- Task sorting/filtering options on the list endpoint
- File directory structure details (date subdirectories, UUID filenames)
- How to handle file_ids validation when attaching files to messages

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

No external specs — requirements fully captured in decisions above and in `.planning/REQUIREMENTS.md` (MSG-01 through MSG-04, TASK-01 through TASK-05, FILE-01 through FILE-04).

### Existing codebase patterns
- `backend/app/models/base.py` — TenantMixin, TimestampMixin, Base class patterns
- `backend/app/models/job.py` — Job model with JobState enum, scheduled_start/end
- `backend/app/models/assignment.py` — AssignmentState enum and ASSIGNMENT_TRANSITIONS pattern (reference for task state machine)
- `backend/app/core/state_machine.py` — State transition validation pattern (reuse for task status)
- `backend/app/core/permissions.py` — require_admin, require_active guards
- `backend/app/dependencies.py` — get_current_user, get_current_tenant auth dependencies
- `backend/app/schemas/job.py` — JobResponse with placeholder messages/tasks/files lists to replace
- `backend/app/api/v1/jobs.py` — CRUD + search patterns, batch query optimization
- `backend/app/main.py` — Router registration pattern

### Prior phase context
- `.planning/phases/03-resource-management/03-CONTEXT.md` — Assignment confirmation workflow, state machine pattern

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `TenantMixin` + `TimestampMixin`: All new models must use these
- `require_admin` / `require_active`: Permission guards for endpoint protection
- `state_machine.py` pattern: Reuse ALLOWED_TRANSITIONS dict + can_transition/validate_transition for task status
- `AssignmentState` enum pattern: Reference for TaskStatus enum
- ILIKE search pattern from jobs/crew: Reuse for message search
- Job CRUD router pattern: Replicable for messages, tasks, files
- Batch query optimization from calendar.py: Reuse for JobResponse summary data

### Established Patterns
- Pydantic Create/Update/Response schemas per resource
- UUID primary keys, TIMESTAMPTZ datetimes
- Router registration in main.py with prefix and tags
- Alembic manual migration creation

### Integration Points
- JobResponse.messages, .tasks, .files placeholders → replace with summary counts + recent items
- Task.message_id FK → references Message model
- Message file attachments → many-to-many link (message_file_attachments table or ARRAY)
- WebSocket endpoint needs its own router or mount point (not a standard REST router)
- File serving endpoint needs to bypass RLS for authenticated direct file access

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

*Phase: 05-coordination-layer*
*Context gathered: 2026-05-16*
