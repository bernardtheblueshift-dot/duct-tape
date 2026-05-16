---
phase: 05-coordination-layer
plan: 05
subsystem: coordination
tags: [api, schemas, batch-queries, enrichment]
dependency_graph:
  requires: [05-01, 05-02, 05-03, 05-04]
  provides: [job-coordination-summary]
  affects: [job-api, frontend-job-detail]
tech_stack:
  added: []
  patterns: [batch-queries, summary-objects, O(1)-per-resource-type]
key_files:
  created: []
  modified:
    - backend/app/schemas/job.py
    - backend/app/api/v1/jobs.py
decisions:
  - Use typed summary objects (MessageSummary, TaskSummary, FileSummary) instead of raw lists
  - Batch queries in list view for O(1) performance per resource type, not O(n)
  - Skip recent_messages and recent_files in list view for performance
  - Overdue count calculated as deadline < now AND status != DONE
  - Use str for status/priority in summaries to avoid circular imports
metrics:
  duration_seconds: 184
  tasks_completed: 2
  files_modified: 2
  commits: 2
  deviations: 0
  completed_date: "2026-05-16"
---

# Phase 05 Plan 05: Job Coordination Summary Summary

**One-liner:** Replaced placeholder messages/tasks/files lists with typed CoordinationSummary containing message counts, task status breakdown, overdue tasks, and file counts using batch queries for O(1) performance.

## What Was Built

Wired coordination data (messages, tasks, files) into JobResponse by replacing Phase 2 placeholder empty lists with real summary counts and recent items. When a user views a job detail, they see: message count + 3 most recent messages, task counts by status (todo/in_progress/done) + overdue count, file count + 3 most recent files. List endpoint uses batch queries to avoid N+1 queries.

### Task 1: Update JobResponse schema with coordination summary types

Created four new summary schemas in `backend/app/schemas/job.py`:

- **MessageSummary** - id, user_id, content, created_at
- **TaskSummary** - id, title, status (str), priority (str), assignee_id, deadline
- **FileSummary** - id, original_filename, mime_type, file_size, created_at
- **CoordinationSummary** - message_count, recent_messages, task_total, task_todo, task_in_progress, task_done, task_overdue, file_count, recent_files

Replaced the three placeholder fields in JobResponse:
```python
# OLD:
messages: list = []
tasks: list = []
files: list = []

# NEW:
coordination: CoordinationSummary = CoordinationSummary()
```

**Commit:** a3891d3

### Task 2: Update jobs.py with coordination data enrichment using batch queries

Added two helper functions to `backend/app/api/v1/jobs.py`:

**build_coordination_summary(job_id, db)** - For detail view
- Message count: `func.count(Message.id)` where job_id matches
- Recent 3 messages: ordered by created_at desc, limit 3
- Task counts by status: `group_by(Task.status)`
- Overdue count: `Task.deadline < datetime.now(timezone.utc) AND Task.status != TaskStatus.DONE`
- File count: `func.count(JobFile.id)`
- Recent 3 files: ordered by created_at desc, limit 3

**batch_coordination_summaries(job_ids, db)** - For list view
- Message counts per job: `group_by(Message.job_id)` where job_id in list
- Task counts per job per status: `group_by(Task.job_id, Task.status)`
- Overdue counts per job: `group_by(Task.job_id)` with deadline filter
- File counts per job: `group_by(JobFile.job_id)`
- Skip recent items (empty lists) to avoid expensive queries for N jobs

Updated 4 endpoints to return enriched coordination data:
1. **GET /api/v1/jobs/{id}** - Full enrichment with recent items
2. **GET /api/v1/jobs** - Batch counts only, no recent items
3. **PATCH /api/v1/jobs/{id}** - Full enrichment with recent items
4. **POST /api/v1/jobs/{id}/transition** - Full enrichment with recent items

All placeholder `"messages": []`, `"tasks": []`, `"files": []` removed and replaced with `"coordination": coordination`.

**Commit:** caaa206

## Deviations from Plan

None - plan executed exactly as written.

## Verification Results

All verifications passed:

1. Schema validation: JobResponse with CoordinationSummary validates correctly
2. Module imports: `build_coordination_summary` and `batch_coordination_summaries` functions load without error
3. Placeholder removal: No `"messages": []`, `"tasks": []`, or `"files": []` found in jobs.py
4. Overall verification: CoordinationSummary works with all fields, old placeholders removed from JobResponse

## Technical Notes

### Performance Pattern

List view uses **batch queries** to avoid N+1 problem:
- 1 query for message counts across all jobs
- 1 query for task counts across all jobs
- 1 query for overdue counts across all jobs
- 1 query for file counts across all jobs

Total: **O(1) queries per resource type**, not O(n) per job. This scales well as job count grows.

Detail view uses **direct queries** for single job with recent items included (acceptable for single-job fetch).

### Overdue Task Logic

Overdue count uses two conditions:
```python
Task.deadline < datetime.now(timezone.utc) AND Task.status != TaskStatus.DONE
```

This ensures:
- Only tasks with deadlines are counted (NULL deadlines excluded)
- Completed tasks don't count as overdue even if deadline passed
- Uses timezone-aware datetime for correct deadline comparison

### String Types for Status/Priority

TaskSummary uses `status: str` and `priority: str` instead of TaskStatus/TaskPriority enums. This follows the same pattern as CrewAssignmentSummary (using str for status) to avoid circular imports between schema modules. The actual enum values are converted to strings when building summaries.

## Impact

- **Frontend:** Job detail and list views can now display coordination summary without additional API calls
- **Performance:** List endpoint remains O(1) per resource type regardless of job count
- **Phase 5 completion:** All coordination layer plans (05-01 through 05-05) now complete

## Next Steps

Phase 05 (Coordination Layer) is now complete with all 5 plans shipped:
- 05-01: Task state transitions and file upload models
- 05-02: Message API with WebSocket support
- 05-03: Task API with status transitions
- 05-04: File upload and management API
- 05-05: Job coordination summary (this plan)

Ready to proceed to Phase 06 or begin testing/integration.

## Self-Check: PASSED

**Created files:** None (all modifications)

**Modified files:**
- backend/app/schemas/job.py: FOUND
- backend/app/api/v1/jobs.py: FOUND

**Commits:**
- a3891d3: FOUND
- caaa206: FOUND

All claims verified.
