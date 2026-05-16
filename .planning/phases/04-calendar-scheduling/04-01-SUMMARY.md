---
phase: 04-calendar-scheduling
plan: 01
subsystem: calendar-api
tags: [calendar, events, ical-token, date-range-queries]
dependency_graph:
  requires: [phase-03-resource-management]
  provides: [calendar-events-api, ical-token-model]
  affects: [frontend-calendar-views]
tech_stack:
  added: [icalendar==7.1.0]
  patterns: [batch-queries, overlap-filtering, unified-event-format]
key_files:
  created:
    - backend/app/schemas/calendar.py
    - backend/app/models/ical_token.py
    - backend/app/api/v1/calendar.py
    - backend/alembic/versions/005_calendar_ical_token.py
    - backend/tests/test_calendar_events.py
  modified:
    - backend/app/models/__init__.py
    - backend/pyproject.toml
    - backend/app/main.py
decisions:
  - "CalendarEvent unified format with event_type field for jobs, crew assignments, equipment assignments"
  - "JOB_STATE_COLORS mapping: intake=blue, simmer=yellow, active=green, complete=grey"
  - "Batch query pattern to avoid N+1: join assignments with jobs in single query"
  - "Overlap filtering: Job.scheduled_start < end AND Job.scheduled_end > start"
  - "Max date range validation: 365 days, returns 400 if exceeded"
  - "ICalToken model with non-expiring tokens (expires_at=NULL), revocable via deletion"
  - "Migration 005 creates ical_tokens table with RLS tenant isolation"
metrics:
  duration: 282s
  tasks_completed: 3
  files_created: 5
  files_modified: 3
  commits: 3
  tests_added: 10
  completed_at: "2026-05-16T01:34:47Z"
---

# Phase 04 Plan 01: Calendar Events API Summary

**One-liner:** Calendar events API with batch-optimized date range queries, unified event format, and ICalToken model for iCal feeds

## What Was Built

Created three REST endpoints that return jobs and resource assignments in a unified CalendarEvent format:

1. **GET /api/v1/calendar/events** — Returns all jobs + assignments within date range
2. **GET /api/v1/calendar/crew/{id}** — Returns crew-specific events (assignments + parent jobs)
3. **GET /api/v1/calendar/equipment/{id}** — Returns equipment-specific events (assignments + parent jobs)

All endpoints:
- Filter by date range (start/end query params)
- Exclude unscheduled jobs (scheduled_start/end must be non-null)
- Use overlap logic: `Job.scheduled_start < end AND Job.scheduled_end > start`
- Return 400 if date range exceeds 365 days
- Apply timezone-aware datetime handling (convert naive datetimes to UTC)
- Use batch queries to avoid N+1 (single query per resource type)

**Schema layer:**
- `CalendarEvent` — Unified event format with event_type ('job', 'crew_assignment', 'equipment_assignment'), color, status, resource details
- `JOB_STATE_COLORS` — Dict mapping job states to hex colors
- `AvailabilityDay` and `CrewAvailabilitySummary` — Schemas for availability expansion (used in Plan 02)
- `ICalTokenCreate` and `ICalTokenResponse` — Schemas for iCal feed token management (used in Plan 03)

**Model layer:**
- `ICalToken` — Token model for iCal feed authentication following token.py pattern (secrets.token_urlsafe(32), non-expiring by default)
- Migration 005 creates ical_tokens table with RLS tenant isolation

**Dependency:**
- Added `icalendar==7.1.0` to pyproject.toml for Plan 03 iCal feed generation

## Testing

Created 10 integration tests in `test_calendar_events.py`:

1. `test_get_events_returns_jobs_in_range` — Verifies only jobs within date range returned
2. `test_get_events_excludes_unscheduled_jobs` — Jobs without scheduled_start/end excluded
3. `test_get_events_includes_crew_assignments` — Crew assignment events with role, resource_name, job_title
4. `test_get_events_includes_equipment_assignments` — Equipment assignment events with resource details
5. `test_get_events_date_range_too_large` — Returns 400 for ranges > 365 days
6. `test_get_events_requires_auth` — Returns 401 without auth token
7. `test_get_crew_calendar` — Crew endpoint returns only that crew's assignments + parent jobs
8. `test_get_equipment_calendar` — Equipment endpoint returns only that equipment's assignments + parent jobs
9. `test_event_color_mapping` — Verifies color mapping for all four job states
10. `test_batch_query_no_n_plus_1` — Verifies batch query performance with 5 jobs + 5 assignments

All tests use conftest fixtures (test_db, async_client, admin_token, test_tenant, test_crew_profile, test_job).

## Deviations from Plan

None — plan executed exactly as written.

## Requirements Satisfied

- **SCHED-01:** Calendar events endpoint returns jobs and assignments in date range ✓
- **SCHED-02:** Per-resource calendar endpoints (crew/{id}, equipment/{id}) ✓
- **SCHED-03:** CalendarEvent schema with all required fields (id, title, start, end, event_type, color, status) ✓

## Technical Insights

**Batch query optimization:**

The `/events` endpoint uses a 3-step batch pattern to avoid N+1:

1. Query all jobs in range → extract job_ids
2. Single query for all crew assignments + user emails where job_id IN (job_ids)
3. Single query for all equipment assignments + equipment names where job_id IN (job_ids)

This scales to O(n) instead of O(n²) as job count grows.

**Overlap filtering:**

Used the same overlap logic from `conflicts.py`: `start1 < end2 AND end2 > start1`. This catches all overlaps including:
- Partial overlaps (job starts before range, ends during)
- Full containment (job fully within range)
- Spanning (job starts before range, ends after)

Touching boundaries (job1 ends 12pm, job2 starts 12pm) do NOT conflict.

**Per-resource endpoints:**

The crew/{id} and equipment/{id} endpoints return BOTH:
- Assignment events for that specific resource
- Parent job events (to provide context on the calendar)

This prevents the frontend from needing to make a second API call to get job details.

**Timezone handling:**

All datetime query params are converted to timezone-aware if naive: `start.replace(tzinfo=timezone.utc)`. This ensures consistent overlap filtering regardless of how the frontend sends datetimes.

## Next Steps

**Plan 04-02:** Crew availability expansion + bulk admin summary endpoints
- Expand `AvailabilityPattern` weekly patterns into concrete unavailable dates within range
- Bulk availability summary for "who's available?" admin view

**Plan 04-03:** iCal feed generation + token management endpoints
- Generate .ics files from CalendarEvent data using `icalendar` library
- Create/revoke ICalToken for crew members
- Public /ical/{token}.ics endpoint (no auth required, token-authenticated)

## Self-Check: PASSED

All files created:
- backend/app/schemas/calendar.py ✓
- backend/app/models/ical_token.py ✓
- backend/app/api/v1/calendar.py ✓
- backend/alembic/versions/005_calendar_ical_token.py ✓
- backend/tests/test_calendar_events.py ✓

All commits verified:
- 967a882 (Task 1: schemas, model, migration) ✓
- 7444f78 (Task 2: API endpoints) ✓
- 2994713 (Task 3: integration tests) ✓
