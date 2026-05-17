---
phase: 07-crew-portal
plan: 02
subsystem: crew-portal
tags: [api, permissions, state-machine, self-service]
one_liner: Crew assignment confirm/decline with state machine validation, restricted profile editing (phone/bio only), and availability self-service
dependency_graph:
  requires: [07-01-portal-dashboard, 03-04-assignments]
  provides: [crew-action-endpoints, profile-self-service, availability-self-service]
  affects: [assignment-workflow, crew-autonomy]
tech_stack:
  added: []
  patterns:
    - ASSIGNMENT_TRANSITIONS state machine for confirm/decline validation
    - Ownership enforcement (crew can only act on own assignments)
    - Field restriction (PortalProfileUpdate excludes skills/hourly_rate)
    - Upsert pattern for availability (delete all + insert)
key_files:
  created: [backend/tests/test_portal_actions.py]
  modified:
    - backend/app/schemas/portal.py
    - backend/app/api/v1/portal.py
decisions:
  - title: Field-restricted profile update schema
    rationale: PortalProfileUpdate only exposes phone and bio; skills and hourly_rate are admin-only fields to preserve data integrity
  - title: State machine validation for assignment actions
    rationale: ASSIGNMENT_TRANSITIONS enforces valid transitions; prevents invalid operations like confirming already-declined assignments
  - title: Ownership checks on all action endpoints
    rationale: Crew can only confirm/decline their own assignments and edit their own profile; prevents unauthorized actions
  - title: Portal router already registered from 07-01
    rationale: Task 2 was already complete; no changes needed
metrics:
  duration: 276
  tasks_completed: 2
  tests_added: 12
  files_modified: 3
  completed_date: "2026-05-17"
---

# Phase 07 Plan 02: Crew Portal Actions Summary

## Objective

Add crew action endpoints to the portal — assignment confirmation/decline, self-service profile editing, and availability management. Register the portal router in main.py to make all portal endpoints live.

## What Was Built

**Assignment Actions**
- POST /api/v1/portal/assignments/{id}/confirm — Transition PENDING to CONFIRMED
- POST /api/v1/portal/assignments/{id}/decline — Transition PENDING/CONFIRMED to DECLINED with optional reason
- GET /api/v1/portal/assignments — List all assignments for current crew with job context
- State transitions validated using ASSIGNMENT_TRANSITIONS from assignment model
- Ownership enforced: crew can only act on their own assignments (403 for others)

**Profile Self-Service**
- GET /api/v1/portal/profile — View own crew profile
- PATCH /api/v1/portal/profile — Update phone and bio only
- PortalProfileUpdate schema restricts fields to phone/bio (silently ignores skills/hourly_rate)
- Admin-only fields preserved from unauthorized editing

**Availability Self-Service**
- PUT /api/v1/portal/availability — Set weekly availability patterns (upsert: delete all + insert)
- GET /api/v1/portal/availability — Get current availability patterns ordered by day_of_week
- Crew can only manage their own availability

**Router Registration**
- Portal router already registered in main.py from Plan 07-01
- All endpoints accessible at /api/v1/portal/* prefix
- Task 2 was a verification task; no changes needed

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] libmagic dependency missing in test environment**
- **Found during:** Test execution (RED phase)
- **Issue:** python-magic library requires libmagic system library; tests failed on import with "failed to find libmagic"
- **Fix:** Mocked magic module in conftest.py before app imports using sys.modules['magic'] = MagicMock()
- **Files modified:** backend/tests/conftest.py
- **Commit:** afdedf1 (part of RED commit)

**2. [Rule 1 - Bug] Test fixture missing for ownership check**
- **Found during:** Test execution (GREEN phase)
- **Issue:** test_confirm_another_crews_assignment_forbidden used crew_token without test_crew_profile fixture; user had no profile → 404 instead of 403
- **Fix:** Added test_crew_profile to test signature to ensure profile exists for token user
- **Files modified:** backend/tests/test_portal_actions.py
- **Commit:** bebd7b4 (part of GREEN commit)

**3. [Non-change] Task 2 already complete**
- Portal router registration was already done in Plan 07-01
- Verified all routes are accessible via Python import test
- No code changes needed; task was verification-only

## Tests

**Created:** backend/tests/test_portal_actions.py (12 test functions)

Test coverage:
- test_confirm_pending_assignment — Basic confirm flow
- test_confirm_already_confirmed_fails — State transition validation
- test_confirm_another_crews_assignment_forbidden — Ownership enforcement
- test_decline_pending_assignment_with_reason — Decline with optional reason
- test_decline_confirmed_assignment — Emergency cancellation flow
- test_get_own_profile — Profile retrieval
- test_get_profile_no_crew_profile_fails — 404 for users without profile
- test_update_profile_phone_and_bio — Field updates work
- test_update_profile_ignores_skills_and_rate — Field restriction enforced
- test_set_availability_patterns — Upsert availability
- test_get_availability_patterns — Retrieve patterns ordered by day
- test_get_assignments_list — List assignments with job context

All tests passing (12/12).

## Commits

| Hash    | Type | Message                                      |
| ------- | ---- | -------------------------------------------- |
| afdedf1 | test | Add failing tests for portal actions         |
| bebd7b4 | feat | Implement portal action endpoints            |

## Verification

- POST /api/v1/portal/assignments/{id}/confirm returns 200 for own PENDING assignment ✓
- POST /api/v1/portal/assignments/{id}/decline returns 200 with optional reason ✓
- POST /api/v1/portal/assignments/{id}/confirm returns 403 for another crew's assignment ✓
- GET /api/v1/portal/profile returns own profile data ✓
- PATCH /api/v1/portal/profile with {phone, bio, skills, hourly_rate} only updates phone and bio ✓
- PUT /api/v1/portal/availability replaces availability patterns ✓
- Portal router is registered in main.py ✓
- All tests pass: 12/12 ✓

## Key Implementation Details

**State Machine Validation**
```python
allowed_transitions = ASSIGNMENT_TRANSITIONS.get(assignment.status, [])
if AssignmentState.CONFIRMED not in allowed_transitions:
    raise HTTPException(status_code=400, detail=f"Invalid transition: {current} -> confirmed")
```

**Ownership Enforcement**
```python
if assignment.crew_id != crew_profile.id:
    raise HTTPException(status_code=403, detail="Cannot act on another crew member's assignment")
```

**Field Restriction**
```python
update_data = profile_update.model_dump(exclude_unset=True)
allowed_fields = {"phone", "bio"}
for key in allowed_fields:
    if key in update_data:
        setattr(crew_profile, key, update_data[key])
```

**Availability Upsert**
```python
# Delete existing patterns
await db.execute(delete(AvailabilityPattern).where(AvailabilityPattern.crew_id == crew_profile.id))
# Insert new patterns
for pattern_data in patterns:
    pattern = AvailabilityPattern(crew_id=crew_profile.id, tenant_id=tenant_id, **pattern_data.model_dump())
    db.add(pattern)
```

## Success Criteria

- [x] Crew can confirm and decline their own assignments with state machine validation
- [x] Crew can view and update their profile with field restrictions enforced (no skills/rate editing)
- [x] Crew can manage their own availability patterns
- [x] All action endpoints verify ownership (crew can only act on their own data)
- [x] Portal router is live in the application
- [x] All test cases pass (12/12)

## Next Steps

Phase 07 complete. Portal provides:
- Dashboard with upcoming/recent assignments + notification counts (07-01)
- Job detail view for assigned crew (07-01)
- Assignment confirm/decline actions (07-02)
- Profile self-service editing (07-02)
- Availability self-service management (07-02)

All crew portal requirements satisfied. Ready for Phase 08 (Polish and Production Readiness) or conclude v1 milestone.

## Self-Check: PASSED

**Files created:**
- [x] backend/tests/test_portal_actions.py exists (354 lines)

**Files modified:**
- [x] backend/app/schemas/portal.py contains PortalProfileUpdate class
- [x] backend/app/schemas/portal.py contains PortalDeclineRequest class
- [x] backend/app/schemas/portal.py contains PortalAssignmentDetail class
- [x] backend/app/api/v1/portal.py contains 8 new endpoints (assignments, confirm, decline, profile GET/PATCH, availability PUT/GET)
- [x] backend/tests/conftest.py contains magic module mock

**Commits:**
- [x] afdedf1 exists in git log (test commit)
- [x] bebd7b4 exists in git log (implementation commit)

**Endpoints verified:**
- [x] /api/v1/portal/assignments registered
- [x] /api/v1/portal/assignments/{id}/confirm registered
- [x] /api/v1/portal/assignments/{id}/decline registered
- [x] /api/v1/portal/profile registered (GET + PATCH)
- [x] /api/v1/portal/availability registered (GET + PUT)

All checks passed.
