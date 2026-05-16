---
phase: 05-coordination-layer
plan: 01
subsystem: coordination-foundation
tags: [models, schemas, migration, core-utilities, websocket, file-storage]
dependency_graph:
  requires: [phase-01-auth, phase-02-jobs, phase-03-resources]
  provides: [message-model, task-model, jobfile-model, task-state-machine, file-storage, websocket-manager]
  affects: [phase-05-plans-02-04]
tech_stack:
  added: [aiofiles, python-magic]
  patterns: [association-table, websocket-singleton, state-machine, tenant-isolated-storage]
key_files:
  created:
    - backend/app/models/message.py
    - backend/app/models/task.py
    - backend/app/models/file.py
    - backend/app/models/message_file.py
    - backend/app/schemas/message.py
    - backend/app/schemas/task.py
    - backend/app/schemas/file.py
    - backend/app/core/task_state.py
    - backend/app/core/file_storage.py
    - backend/app/core/websocket_manager.py
    - backend/alembic/versions/006_coordination_layer_tables.py
  modified:
    - backend/app/models/__init__.py
    - backend/pyproject.toml
decisions:
  - id: task-state-transitions
    choice: Bidirectional transitions (TODO <-> IN_PROGRESS <-> DONE)
    rationale: Tasks can be reopened (DONE -> IN_PROGRESS) and paused (IN_PROGRESS -> TODO) for workflow flexibility
  - id: message-content-format
    choice: Markdown text stored as TEXT column
    rationale: Simple storage, frontend handles rendering; no HTML sanitization needed
  - id: file-association-pattern
    choice: Many-to-many via message_files association table
    rationale: Files can be attached to multiple messages (e.g., re-shared in thread)
  - id: mime-type-validation
    choice: python-magic for detection + whitelist
    rationale: Client-provided MIME type unreliable; python-magic reads file magic bytes
  - id: websocket-singleton
    choice: Global ConnectionManager instance
    rationale: Single source of truth for all WebSocket connections and subscriptions
metrics:
  duration_seconds: 194
  tasks_completed: 3
  files_created: 13
  commits: 3
  completed_at: "2026-05-16"
---

# Phase 05 Plan 01: Coordination Layer Foundation Summary

**One-liner:** Created Message/Task/JobFile models, Pydantic schemas, task state machine, file storage with MIME validation, and WebSocket manager singleton for real-time job updates

## What Was Built

### Models (4 new)
- **Message**: Job conversation with reply threading (reply_to_id), markdown content, many-to-many file attachments
- **Task**: Assignable work items with status (TODO/IN_PROGRESS/DONE), priority (LOW/MEDIUM/HIGH/URGENT), deadline, optional link to origin message
- **JobFile**: Upload metadata (original_filename, storage_path, mime_type, file_size), tenant-isolated storage
- **message_files**: Association table for Message <-> JobFile many-to-many relationship

### Schemas (3 modules)
- **message.py**: MessageCreate (with file_ids list), MessageResponse, MessageSearchParams
- **task.py**: TaskCreate, TaskUpdate, TaskStatusUpdate, TaskResponse (imports TaskStatus/TaskPriority enums)
- **file.py**: FileResponse (no Create schema - multipart upload uses UploadFile)

### Core Utilities (3 modules)
- **task_state.py**: TASK_TRANSITIONS dict, can_transition, validate_transition (follows state_machine.py pattern)
- **file_storage.py**: save_upload with python-magic MIME detection, 100MB limit, tenant_id/job_id directory structure, ALLOWED_MIME_TYPES whitelist
- **websocket_manager.py**: ConnectionManager singleton with subscribe/unsubscribe/broadcast_to_job methods

### Migration
- **006_coordination_layer_tables.py**: Creates messages, tasks, job_files, message_files tables with RLS policies, taskstatus/taskpriority enums, indexes on job_id

### Dependencies
- Added aiofiles>=0.24.0 (async file I/O)
- Added python-magic>=0.4.27 (MIME type detection from file content)

## Deviations from Plan

None - plan executed exactly as written.

## Technical Decisions

### Task State Transitions
**Decision:** Bidirectional transitions between all states (TODO <-> IN_PROGRESS <-> DONE)
**Rationale:** Real-world workflow requires flexibility - tasks can be paused (IN_PROGRESS -> TODO) or reopened (DONE -> IN_PROGRESS). Linear flow too restrictive.
**Pattern:** Follows existing state_machine.py structure with TASK_TRANSITIONS dict and validate_transition function.

### File Storage Architecture
**Decision:** Tenant-isolated directory structure (uploads/tenant_id/job_id/file_id.ext)
**Rationale:** Physical separation prevents cross-tenant access even if RLS fails. Directory structure mirrors data model hierarchy.
**MIME Validation:** python-magic reads file magic bytes instead of trusting client-provided Content-Type (security).

### WebSocket Manager Singleton
**Decision:** Global `manager` instance instead of dependency injection
**Rationale:** Single source of truth for connections prevents split-brain. Simpler than passing manager through every endpoint.
**Subscription Model:** User subscribes to job_id, broadcasts filtered by subscription set.

### Message Content Format
**Decision:** Markdown stored as TEXT, no server-side rendering
**Rationale:** Simple storage, frontend controls rendering. Avoids HTML sanitization complexity. Can upgrade to rich text later if needed.

## Key Implementation Details

### Association Table Pattern
Used SQLAlchemy Table() construct (not mapped class) for message_files, following best practice for pure many-to-many with no additional columns.

### Enum Integration
TaskStatus and TaskPriority imported directly into task.py schema module to avoid circular imports. Migration creates PostgreSQL ENUMs with matching string values.

### ForeignKey Chain
Task.message_id -> Message.id enables "task created from message" workflow. Message.reply_to_id -> Message.id enables threaded conversations.

## Testing Notes

All models and schemas import successfully. Migration file created following existing pattern (no Docker, manual migration).

**Ready for PostgreSQL testing:** Once database available, run migration 006 to create tables and verify RLS policies.

## Files Changed

**Created (13):**
- backend/app/models/message.py (28 lines)
- backend/app/models/task.py (54 lines)
- backend/app/models/file.py (27 lines)
- backend/app/models/message_file.py (20 lines)
- backend/app/schemas/message.py (33 lines)
- backend/app/schemas/task.py (56 lines)
- backend/app/schemas/file.py (21 lines)
- backend/app/core/task_state.py (43 lines)
- backend/app/core/file_storage.py (121 lines)
- backend/app/core/websocket_manager.py (96 lines)
- backend/alembic/versions/006_coordination_layer_tables.py (246 lines)

**Modified (2):**
- backend/app/models/__init__.py (+4 imports, +4 __all__ entries)
- backend/pyproject.toml (+2 dependencies)

## Commits

1. **7a7a4d3** - feat(05-01): create coordination layer models and migration
2. **41844f5** - feat(05-01): create Pydantic schemas for coordination layer
3. **bab9d20** - feat(05-01): create core utilities and add dependencies

## Next Steps

**Immediate:** Execute Plan 05-02 (Messages API) to build POST/GET/PATCH/DELETE endpoints on Message model
**Then:** Plan 05-03 (Tasks API) and Plan 05-04 (Files API)
**Foundation Complete:** All data structures ready for API implementation

## Self-Check: PASSED

**Models exist:**
- backend/app/models/message.py: FOUND
- backend/app/models/task.py: FOUND
- backend/app/models/file.py: FOUND
- backend/app/models/message_file.py: FOUND

**Schemas exist:**
- backend/app/schemas/message.py: FOUND
- backend/app/schemas/task.py: FOUND
- backend/app/schemas/file.py: FOUND

**Core utilities exist:**
- backend/app/core/task_state.py: FOUND
- backend/app/core/file_storage.py: FOUND
- backend/app/core/websocket_manager.py: FOUND

**Migration exists:**
- backend/alembic/versions/006_coordination_layer_tables.py: FOUND

**Commits exist:**
- 7a7a4d3: FOUND
- 41844f5: FOUND
- bab9d20: FOUND

**All imports succeed:** ✓

All planned artifacts created and committed. Plan complete.
