# Phase 4: Calendar & Scheduling - Context

**Gathered:** 2026-05-16
**Status:** Ready for planning

<domain>
## Phase Boundary

Backend API endpoints for calendar data: events by date range, per-resource views, bulk crew availability, and iCal export feeds. No React frontend — this phase delivers the data layer that a future calendar UI will consume. Month/week/day granularity is handled by the frontend querying the same events endpoint with different date ranges.

</domain>

<decisions>
## Implementation Decisions

### Calendar API shape
- Backend API only — no React calendar UI in this phase
- Events-by-range endpoint: GET /calendar/events?start=X&end=Y returns all jobs + assignments in range
- Per-resource endpoints: GET /calendar/crew/{id}?start=X&end=Y and GET /calendar/equipment/{id}?start=X&end=Y
- Raw events format — API returns flat list, frontend arranges into calendar grid
- Unified event format with event_type field ('job', 'crew_assignment', 'equipment_assignment')

### View granularity & data density
- Each event includes: id, title, start, end, event_type, color, status, resource_name, job_title, role
- No summary mode — same endpoint for month/week/day, frontend decides how to summarize
- Color by job state: intake=blue, simmer=yellow, active=green, complete=grey
- All assignments for a job inherit the job's color

### Availability visualization
- Separate availability endpoint: GET /calendar/crew/{id}/availability?start=X&end=Y
- Expands recurring weekly patterns into concrete unavailable dates within the range (frontend doesn't need to understand recurrence)
- Bulk availability summary: GET /calendar/availability?start=X&end=Y returns all crew with status per day (free/booked/unavailable) — admin's "who's available?" view

### iCal export design
- Token-authenticated URL: /ical/{token}.ics — long random string, no login required
- Calendar apps subscribe to this URL and poll for updates
- Token is revocable if compromised
- Event content: SUMMARY = "Role - Job Title", LOCATION = venue, DESCRIPTION = job description
- Confirmed assignments only — pending not included (avoids premature calendar blocks)

### Claude's Discretion
- iCal token generation and storage approach
- Exact query optimization for date range queries
- How to handle jobs without scheduled times in calendar views
- Response pagination for large date ranges
- Cache strategy for expanded availability dates

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

No external specs — requirements fully captured in decisions above and in `.planning/REQUIREMENTS.md` (SCHED-01 through SCHED-04, SCHED-06).

### Existing codebase patterns
- `backend/app/models/job.py` — Job model with scheduled_start/scheduled_end (TIMESTAMPTZ) and JobState enum
- `backend/app/models/assignment.py` — CrewAssignment and EquipmentAssignment with AssignmentState enum, job FK
- `backend/app/models/availability.py` — AvailabilityPattern with day_of_week (0=Monday, 6=Sunday) and is_available
- `backend/app/models/crew_profile.py` — CrewProfile with user FK, skills, rating fields
- `backend/app/models/equipment.py` — Equipment with quantity, category, condition
- `backend/app/core/conflicts.py` — Time overlap detection logic (reuse for calendar range queries)
- `backend/app/schemas/job.py` — JobResponse with assigned_crew/assigned_gear lists
- `backend/app/api/v1/jobs.py` — CRUD + search endpoint patterns
- `backend/app/api/v1/crew.py` — Crew CRUD + availability endpoints (GET /{crew_id}/availability)
- `backend/app/dependencies.py` — get_current_user, get_current_tenant auth dependencies

### Prior phase context
- `.planning/phases/03-resource-management/03-CONTEXT.md` — Conflict detection decisions, assignment workflow, availability patterns

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `conflicts.py` time overlap queries: Same SQL pattern (start < end AND end > start) needed for calendar range queries
- `AvailabilityPattern` model: Already stores day_of_week + is_available — just needs expansion logic
- `AssignmentState` enum: Calendar events can derive status from assignment state
- `JobState` enum: Maps directly to color scheme (intake=blue, simmer=yellow, active=green, complete=grey)
- Auth dependencies: `get_current_user` / `get_current_tenant` for all protected endpoints

### Established Patterns
- Pydantic response schemas with `model_config = ConfigDict(from_attributes=True)`
- Router registration in `main.py` with prefix and tags
- UUID primary keys, TIMESTAMPTZ datetimes
- ILIKE search, query parameters for filtering

### Integration Points
- Calendar events query joins across Job + CrewAssignment + EquipmentAssignment tables
- Availability expansion reads AvailabilityPattern and generates date list
- iCal feed needs a new token model (or column on User/CrewProfile) for URL authentication
- Bulk availability summary queries all CrewProfiles + their assignments + patterns for a date range

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

*Phase: 04-calendar-scheduling*
*Context gathered: 2026-05-16*
