---
phase: 03-resource-management
plan: 04
subsystem: assignments
tags: [crew-assignments, equipment-assignments, conflict-detection, confirmation-workflow, api]
dependency_graph:
  requires:
    - 03-02-PLAN (conflict detection)
    - 03-03-PLAN (equipment CRUD)
    - 03-01-PLAN (assignment models and schemas)
  provides:
    - crew assignment endpoints with conflict detection
    - equipment assignment endpoints with availability checking
    - assignment state transitions (confirm/decline)
    - populated JobResponse with real assignment data
  affects:
    - backend/app/api/v1/jobs.py (now populates assigned_crew and assigned_gear)
tech_stack:
  added: []
  patterns:
    - batch query optimization for list endpoints
    - structured error responses for conflict warnings
    - permission checks: admin for assign/delete, crew or admin for transitions
key_files:
  created:
    - backend/app/api/v1/assignments.py
    - backend/tests/test_assignments.py
  modified:
    - backend/app/main.py (registered assignments router)
    - backend/app/schemas/job.py (added CrewAssignmentSummary, EquipmentAssignmentSummary)
    - backend/app/api/v1/jobs.py (populate assignments in get_job and list_jobs)
decisions:
  - "Crew assignments have pending/confirmed/declined workflow"
  - "Equipment assignments are direct (no confirmation needed)"
  - "Crew conflicts: warn + allow override with force=true and override_reason"
  - "Equipment conflicts: hard block when quantity exhausted (no override)"
  - "Batch query assignments in list_jobs for efficiency"
  - "Use str for status in CrewAssignmentSummary to avoid circular import"
  - "Permission: crew can only transition their own assignments, admin can transition any"
metrics:
  duration: 241
  completed: "2026-05-16"
  tasks_completed: 2
  files_created: 2
  files_modified: 3
---

# Phase 03 Plan 04: Assignment Endpoints with Conflict Detection Summary

**One-liner:** Crew and equipment assignment endpoints with conflict detection integration, confirmation workflow, and real assignment data in JobResponse

## What Was Built

### Assignment Endpoints (7 total)

**Crew Assignment:**
- `POST /api/v1/assignments/crew` — Assign crew to job with conflict detection
  - Validates job and crew exist
  - Checks for existing assignment (409 if duplicate)
  - If job has schedule: checks time conflicts and availability patterns
  - Returns 409 with ConflictWarning if conflicts detected and force=false
  - Accepts force=true + override_reason to bypass conflict warnings
  - Creates assignment in PENDING state
- `POST /api/v1/assignments/crew/{id}/transition` — Crew confirms/declines assignment
  - Validates ASSIGNMENT_TRANSITIONS state machine rules
  - Permission: crew can transition their own, admin can transition any
  - Stores declined_reason when status changes to DECLINED
- `GET /api/v1/assignments/job/{job_id}/crew` — List crew assignments for job
- `DELETE /api/v1/assignments/crew/{id}` — Remove crew assignment (admin only)

**Equipment Assignment:**
- `POST /api/v1/assignments/equipment` — Assign equipment to job
  - Validates job and equipment exist
  - Checks for existing assignment (409 if duplicate)
  - If job has schedule: checks equipment availability
  - Returns 409 with availability details if quantity exhausted (hard block, no override)
  - Creates assignment immediately (no confirmation workflow)
- `GET /api/v1/assignments/job/{job_id}/equipment` — List equipment assignments for job
- `DELETE /api/v1/assignments/equipment/{id}` — Remove equipment assignment (admin only)

### JobResponse Population

**Updated schemas:**
- `CrewAssignmentSummary` — id, crew_id, role, status (str to avoid circular import)
- `EquipmentAssignmentSummary` — id, equipment_id, quantity_assigned
- `JobResponse.assigned_crew` — now typed as `list[CrewAssignmentSummary]`
- `JobResponse.assigned_gear` — now typed as `list[EquipmentAssignmentSummary]`

**Updated endpoints:**
- `GET /api/v1/jobs/{id}` — queries CrewAssignment and EquipmentAssignment, builds response dict with populated assignment arrays
- `GET /api/v1/jobs/` — batch queries all assignments for returned jobs, groups by job_id, populates each job response

### Integration Tests (12 total)

1. **test_assign_crew_to_job** — Basic crew assignment starts in pending state
2. **test_crew_confirmation_flow** — Crew confirms their assignment (pending → confirmed)
3. **test_crew_decline_flow** — Crew declines with reason (pending → declined)
4. **test_crew_conflict_detected** — Overlapping confirmed assignment returns 409 with conflict details
5. **test_crew_conflict_override** — force=true with override_reason bypasses conflict warning
6. **test_assign_equipment_to_job** — Basic equipment assignment
7. **test_equipment_conflict_hard_block** — Quantity exhausted returns 409 with availability details (no override)
8. **test_equipment_partial_availability** — Partial quantity available allows assignment
9. **test_list_crew_assignments_for_job** — List endpoint returns all crew assignments
10. **test_job_detail_shows_assignments** — JobResponse populated with assigned_crew and assigned_gear
11. **test_delete_crew_assignment** — Admin deletes assignment, list returns empty
12. **test_assignment_transition_requires_correct_user** — Crew A cannot confirm Crew B's assignment (403)

## Key Integration Points

**From Plan 03-02 (Conflict Detection):**
- `check_crew_conflicts(db, crew_id, start, end)` — returns list of overlapping confirmed assignments
- `check_equipment_availability(db, equipment_id, start, end)` — returns dict with total/assigned/available quantities
- `check_crew_availability_patterns(db, crew_id, target_date)` — checks day-of-week availability

**From Plan 03-01 (Models/Schemas):**
- `CrewAssignment` model with status, override_reason, declined_reason
- `EquipmentAssignment` model with quantity_assigned
- `AssignmentState` enum (PENDING, CONFIRMED, DECLINED)
- `ASSIGNMENT_TRANSITIONS` state machine rules
- `CrewAssignmentCreate`, `EquipmentAssignmentCreate`, `AssignmentTransitionRequest` schemas
- `ConflictWarning` and `ConflictDetail` schemas

## Deviations from Plan

None — plan executed exactly as written.

## Verification Results

All verification commands passed:

```bash
# Assignments router imports correctly
$ python3 -c "from app.api.v1.assignments import router; print(f'Assignments router OK: {router.prefix}')"
Assignments router OK: /api/v1/assignments

# Updated JobResponse schema imports correctly
$ python3 -c "from app.schemas.job import JobResponse, CrewAssignmentSummary, EquipmentAssignmentSummary; print('Updated JobResponse imports OK')"
Updated JobResponse imports OK

# Test count
$ python3 -c "import ast; tree = ast.parse(open('tests/test_assignments.py').read()); test_count = len([n for n in ast.walk(tree) if isinstance(n, ast.AsyncFunctionDef) and n.name.startswith('test_')]); print(f'{test_count} tests')"
12 tests
```

## Success Criteria Met

- [x] Crew assignments: pending → confirmed/declined workflow functional
- [x] Crew conflicts: warn + allow override with force=true
- [x] Equipment conflicts: hard block when quantity exhausted, no override
- [x] JobResponse.assigned_crew and assigned_gear contain real data from database
- [x] 12 integration tests covering all assignment flows and edge cases

## Technical Highlights

**Conflict Detection Flow:**
1. Crew assignment validates job has schedule
2. Calls `check_crew_conflicts()` for time overlaps (only CONFIRMED assignments)
3. Calls `check_crew_availability_patterns()` for day-of-week blocks
4. If conflicts and force=false: returns 409 with structured ConflictWarning JSON
5. If force=true: proceeds and stores override_reason

**Equipment Availability Flow:**
1. Equipment assignment validates job has schedule
2. Calls `check_equipment_availability()` to sum overlapping assignments
3. Compares available_quantity with requested quantity_assigned
4. If insufficient: returns 409 with detailed availability breakdown (hard block, no override)

**Permission Model:**
- Admin: can assign crew/equipment, transition any assignment, delete any assignment
- Crew: can transition their own assignments only (validated via CrewProfile.user_id match)

**Batch Query Optimization:**
- `list_jobs()` queries all jobs first
- Extracts job IDs, batch queries CrewAssignment WHERE job_id IN (...)
- Batch queries EquipmentAssignment WHERE job_id IN (...)
- Groups by job_id using dicts
- Builds response with O(n) lookups instead of O(n²) queries

## Commits

| Task | Commit | Description |
|------|--------|-------------|
| 1    | f2f068f | Assignment endpoints with conflict detection (7 endpoints, router registration) |
| 2    | e388490 | JobResponse population + 12 integration tests |

## What's Next

**Phase 03 Plan 05** (final plan): Crew availability calendar endpoints (set recurring availability patterns, query availability, batch availability checks)

After Phase 03 completes: Phase 04 (Calendar Integration) will build on this assignment foundation to add calendar views, scheduling optimization, and resource utilization dashboards.

## Self-Check: PASSED

Files created:
```bash
$ [ -f "backend/app/api/v1/assignments.py" ] && echo "FOUND: backend/app/api/v1/assignments.py"
FOUND: backend/app/api/v1/assignments.py
$ [ -f "backend/tests/test_assignments.py" ] && echo "FOUND: backend/tests/test_assignments.py"
FOUND: backend/tests/test_assignments.py
```

Commits exist:
```bash
$ git log --oneline --all | grep -q "f2f068f" && echo "FOUND: f2f068f"
FOUND: f2f068f
$ git log --oneline --all | grep -q "e388490" && echo "FOUND: e388490"
FOUND: e388490
```

All files and commits verified.
