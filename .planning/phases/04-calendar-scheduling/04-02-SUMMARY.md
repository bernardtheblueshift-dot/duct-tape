---
phase: 04-calendar-scheduling
plan: 02
subsystem: calendar
tags: [availability, crew-scheduling, batch-queries, admin-tools]
completed_date: "2026-05-16"

dependency_graph:
  requires:
    - 04-01-calendar-events
  provides:
    - crew-availability-expansion
    - bulk-admin-availability
  affects:
    - frontend-crew-scheduling

tech_stack:
  added: []
  patterns:
    - "Batch query optimization with .in_() for N+1 prevention"
    - "Weekly pattern expansion into concrete date lists"
    - "Three-tier status priority: unavailable > booked > free"

key_files:
  created:
    - backend/tests/test_calendar_availability.py
  modified:
    - backend/app/api/v1/calendar.py

decisions:
  - title: "Batch queries for bulk availability"
    rationale: "Single query per resource type prevents N+1 as crew count scales"
    alternatives: ["Per-crew queries", "DataLoader pattern"]
    tradeoffs: "More complex query logic, but O(n) vs O(n²) performance"

  - title: "Only CONFIRMED assignments count as booked"
    rationale: "PENDING/DECLINED should not block availability"
    alternatives: ["Include PENDING as tentative status"]
    tradeoffs: "Clearer availability picture, but crew may get double-assigned if pending becomes confirmed"

  - title: "Status priority: unavailable > booked > free"
    rationale: "Unavailable patterns override bookings (crew can't work those days anyway)"
    alternatives: ["Booked overrides unavailable", "Separate unavailable+booked status"]
    tradeoffs: "Simpler logic, matches real-world constraints"

metrics:
  duration_seconds: 219
  tasks_completed: 2
  files_created: 1
  files_modified: 1
  commits: 2
  tests_added: 9
---

# Phase 04 Plan 02: Crew Availability Expansion Summary

**One-liner:** Crew availability endpoints with batch-optimized queries expand weekly patterns into concrete date lists for "who's available?" views

## What Was Built

Two REST endpoints added to the calendar router:

1. **GET /api/v1/calendar/crew/{crew_id}/availability** (active users)
   - Per-crew availability across date range
   - Returns list of AvailabilityDay with status: free/booked/unavailable
   - Weekly patterns expanded into concrete dates
   - Only CONFIRMED assignments count as booked

2. **GET /api/v1/calendar/availability** (admin-only)
   - Bulk crew availability summary
   - All active (non-archived) crew included
   - Batch queries to avoid N+1 performance issues
   - Returns CrewAvailabilitySummary with crew_id, crew_name, days array

**Status Priority Logic:**
- unavailable (AvailabilityPattern where is_available=False)
- booked (CONFIRMED CrewAssignment overlapping date)
- free (default)

**Performance optimization:** Both endpoints use batch queries with `.in_()` to fetch all patterns/assignments upfront, then iterate in memory. O(n) instead of O(n²) as crew count scales.

## Test Coverage

9 integration tests in `backend/tests/test_calendar_availability.py`:

- test_crew_availability_free_days — No patterns/assignments = all free
- test_crew_availability_unavailable_from_pattern — Weekday pattern marks unavailable
- test_crew_availability_booked_from_assignment — CONFIRMED assignment marks booked
- test_crew_availability_pending_not_booked — PENDING assignments excluded
- test_crew_availability_combined_statuses — Pattern + assignment priority
- test_bulk_availability_admin_only — 403 for non-admin
- test_bulk_availability_returns_all_crew — Multi-crew summary
- test_bulk_availability_excludes_archived — Archived crew filtered
- test_availability_date_range_validation — 400 for >365 day range

## Implementation Details

**Batch Query Pattern (bulk endpoint):**
1. Fetch all active crew (one query)
2. Fetch all unavailable patterns for all crew (one query with .in_())
3. Fetch all confirmed assignments for all crew (one query with .in_())
4. Build maps: crew_id → unavailable_weekdays, crew_id → booking_ranges
5. Iterate dates for each crew member in memory

**Date Expansion Logic:**
```python
while current <= end_date:
    if current.weekday() in unavailable_weekdays:
        status = "unavailable"
    elif any(job_start.date() <= current <= job_end.date() for job_start, job_end in booked_ranges):
        status = "booked"
    else:
        status = "free"
    days.append(AvailabilityDay(date=current, status=status))
    current += timedelta(days=1)
```

**Why weekly patterns are expanded server-side:** Frontend doesn't need to understand recurrence rules. Server returns concrete date list, simplifying UI logic.

## Deviations from Plan

None — plan executed exactly as written.

## Verification Results

**Automated checks passed:**
- ✓ Routes registered: `/calendar/crew/{crew_id}/availability`, `/calendar/availability`
- ✓ 9 test functions present (>= 7 required)
- ✓ Code contains all required patterns (AvailabilityPattern.is_available == False, AssignmentState.CONFIRMED, CrewProfile.archived_at.is_(None), defaultdict, require_admin, require_active)

**Manual verification:**
- Calendar router now has 5 endpoint functions (3 from Plan 01 + 2 from this plan)
- No N+1 queries in bulk endpoint (uses batch .in_() queries)
- Unavailable days come from AvailabilityPattern where is_available=False
- Booked days come from CONFIRMED CrewAssignment only (PENDING excluded)
- Archived crew excluded from bulk summary

## Frontend Integration Notes

**Per-crew availability** (`/calendar/crew/{id}/availability`):
- Use for crew self-service calendar overlay
- Shows crew member which days they're booked, unavailable, or free
- Combine with job calendar events for full schedule view

**Bulk availability** (`/calendar/availability`):
- Use for admin "who's available?" tool
- Grid view: crew members as rows, dates as columns
- Color-code cells: green (free), red (unavailable), grey (booked)
- Filter by date range + optionally by skills/role (future enhancement)

**Date range picker:** Max 365 days enforced by API. Show validation error if user selects larger range.

## Performance Characteristics

**Per-crew endpoint:**
- 2 queries regardless of date range (patterns + assignments)
- O(days) iteration to build response
- Fast for typical 7-30 day ranges

**Bulk endpoint:**
- 3 queries regardless of crew count (crew list + patterns + assignments)
- O(crew_count × days) iteration in memory
- Efficient up to ~100 crew × 30 days (3000 iterations)
- For larger orgs, consider adding pagination or crew filters

## What's Next

Phase 04 Plan 03: iCal feed generation + token management
- Generate RFC5545-compliant .ics feeds from CalendarEvent data
- Token-based authentication for calendar subscriptions
- CRUD endpoints for ICalToken management

## Commits

- 58e5546: feat(04-02): add crew availability endpoints
- c04a0bc: test(04-02): add availability endpoint integration tests

## Self-Check: PASSED

**Created files exist:**
- ✓ backend/tests/test_calendar_availability.py

**Commits exist:**
- ✓ 58e5546 (Task 1: availability endpoints)
- ✓ c04a0bc (Task 2: integration tests)

**Code verification:**
- ✓ AvailabilityPattern.is_available == False in query
- ✓ AssignmentState.CONFIRMED for booking filter
- ✓ CrewProfile.archived_at.is_(None) for active crew
- ✓ defaultdict(set) and defaultdict(list) for batch grouping
- ✓ require_admin on bulk endpoint
- ✓ require_active on per-crew endpoint
- ✓ AvailabilityDay and CrewAvailabilitySummary schemas used
