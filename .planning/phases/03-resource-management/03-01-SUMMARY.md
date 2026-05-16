---
phase: 03-resource-management
plan: 01
subsystem: resource-management-models
tags: [models, schemas, migration, crew, equipment, assignment]
dependency_graph:
  requires: [phase-01-foundation, phase-02-jobs]
  provides: [crew-profile-model, equipment-model, assignment-models, rating-model, availability-model]
  affects: [phase-03-remaining-plans, phase-04-calendar, phase-05-coordination]
tech_stack:
  added: [sqlalchemy-array, numeric-columns, postgresql-enums]
  patterns: [tenant-mixin, timestamp-mixin, soft-delete, state-machine]
key_files:
  created:
    - backend/app/models/crew_profile.py
    - backend/app/models/equipment.py
    - backend/app/models/assignment.py
    - backend/app/models/availability.py
    - backend/app/models/rating.py
    - backend/app/schemas/crew.py
    - backend/app/schemas/equipment.py
    - backend/app/schemas/assignment.py
    - backend/alembic/versions/004_resource_management_tables.py
  modified:
    - backend/app/models/__init__.py
decisions:
  - id: crew-user-relationship
    summary: "CrewProfile 1:1 with User via unique FK"
    rationale: "Separates auth concerns from crew data, preserves Phase 1 User model"
  - id: soft-delete-pattern
    summary: "archived_at timestamp for crew soft delete"
    rationale: "Preserves historical assignment data while hiding from active search"
  - id: skills-as-array
    summary: "PostgreSQL ARRAY(String) for skills tags"
    rationale: "Flexible tenant-scoped vocabulary, no separate skills table needed"
  - id: assignment-state-machine
    summary: "pending/confirmed/declined with ASSIGNMENT_TRANSITIONS dict"
    rationale: "Follows state_machine.py pattern from Phase 2"
  - id: equipment-quantity-pool
    summary: "Single quantity column, pool-based tracking"
    rationale: "Simpler than individual item tracking, sufficient for v1"
  - id: rating-cache-columns
    summary: "rating_average and rating_count on CrewProfile"
    rationale: "Avoid aggregate query on every profile load, update via trigger or app logic"
metrics:
  duration_seconds: 187
  completed_at: "2026-05-16T00:12:45Z"
---

# Phase 03 Plan 01: Resource Management Models Summary

**One-liner:** Database layer for crew profiles, equipment inventory, and job assignments with conflict detection foundation

## What Was Built

Created the complete data layer for Phase 3 resource management: 5 model files, 3 schema files, and 1 comprehensive migration covering all resource types (crew, equipment, assignments, availability, ratings).

### Models Created

**CrewProfile** (`crew_profile.py`):
- One-to-one with User via unique FK to users.id
- Skills stored as PostgreSQL TEXT[] for flexible tenant-scoped tags
- Soft delete via `archived_at` timestamp preserves historical data
- Cached rating statistics (`rating_average`, `rating_count`) avoid expensive aggregates
- Decimal fields for currency (`hourly_rate`)

**Equipment** (`equipment.py`):
- EquipmentCondition enum (good/fair/poor/maintenance)
- Quantity-based pool tracking (no individual item tracking in v1)
- Free-text category field (tenant-scoped vocabulary)
- Optional serial_number for per-unit tracking when needed

**Assignments** (`assignment.py`):
- AssignmentState enum (pending/confirmed/declined) with ASSIGNMENT_TRANSITIONS dict
- CrewAssignment: includes role field per job, status workflow, override/declined reason tracking
- EquipmentAssignment: quantity_assigned supports partial allocation from pool
- Unique constraints prevent duplicate assignments (uq_crew_job, uq_equipment_job)

**AvailabilityPattern** (`availability.py`):
- Recurring weekly patterns (day_of_week 0-6)
- Boolean is_available flag
- Unique constraint per crew per day (uq_crew_day)

**CrewRating** (`rating.py`):
- 1-5 stars per crew per job
- rated_by FK tracks which admin rated
- Unique constraint (uq_crew_job_rating) enforces one rating per crew per job
- Optional notes field for qualitative feedback

### Schemas Created

**crew.py:**
- CrewProfileCreate/Update/Response with validation (hourly_rate ge=0)
- AvailabilityPatternCreate/Response with day_of_week validation (0-6)
- CrewRatingCreate/Response with stars validation (1-5)
- SkillsMatrixResponse for cross-crew capability view

**equipment.py:**
- EquipmentCreate/Update/Response with EquipmentCondition enum
- Validation: name 1-200 chars, quantity ge=1

**assignment.py:**
- CrewAssignmentCreate/Response with force flag and override_reason
- EquipmentAssignmentCreate/Response with quantity_assigned validation
- AssignmentTransitionRequest for state machine operations
- ConflictWarning and ConflictDetail for conflict detection warnings

### Migration Created

**004_resource_management_tables.py:**
- Creates 6 tables with proper TIMESTAMPTZ columns
- Two enums: equipmentcondition, assignmentstate
- Foreign keys: user_id→users.id, crew_id→crew_profiles.id, job_id→jobs.id, equipment_id→equipment.id
- Unique constraints enforce business rules (no duplicate assignments, one rating per crew per job)
- Indexes on tenant_id, foreign keys, and query-heavy columns (category, status)
- Clean downgrade path drops everything in reverse order

## Deviations from Plan

None - plan executed exactly as written. All models follow established TenantMixin/TimestampMixin patterns, schemas follow Create/Update/Response convention, and migration uses enum pattern from Phase 2.

## Verification Results

All automated checks passed:
- All models importable: `from app.models import CrewProfile, Equipment, CrewAssignment, EquipmentAssignment, AssignmentState, AvailabilityPattern, CrewRating`
- All schemas importable: `from app.schemas.crew import CrewProfileCreate, CrewProfileResponse; from app.schemas.equipment import EquipmentCreate; from app.schemas.assignment import ConflictWarning`
- Migration structure verified: revision=004, down_revision=003, 6 tables, 4 unique constraints

## Integration Points

**Phase 1 (Foundation):**
- CrewProfile.user_id FK to User model
- All models use TenantMixin and TimestampMixin from base.py
- CrewRating.rated_by FK to User for admin tracking

**Phase 2 (Jobs):**
- Both assignment models FK to Job
- JobResponse.assigned_crew and assigned_gear placeholders ready to populate in Plan 03-04

**Phase 3 remaining plans:**
- Plan 03-02: Crew CRUD endpoints consume CrewProfile model/schemas
- Plan 03-03: Equipment CRUD endpoints consume Equipment model/schemas
- Plan 03-04: Assignment endpoints consume assignment models/schemas, implement conflict detection
- Plan 03-05: Rating and availability endpoints consume CrewRating/AvailabilityPattern

## Next Steps

1. Plan 03-02: Implement crew CRUD endpoints with search and archive
2. Plan 03-03: Implement equipment CRUD endpoints with status tracking
3. Plan 03-04: Build assignment endpoints with conflict detection logic and JobResponse wiring
4. Plan 03-05: Add rating submission, availability pattern management, and skills matrix view

All subsequent Phase 3 work depends on these models and schemas being in place. No blocking issues encountered.

## Task Completion Summary

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Create all resource models | 0613fb1 | crew_profile.py, equipment.py, assignment.py, availability.py, rating.py, models/__init__.py |
| 2 | Create Pydantic schemas | 4a21b8b | crew.py, equipment.py, assignment.py (schemas) |
| 3 | Create Alembic migration | ef9e954 | 004_resource_management_tables.py |

**Total duration:** 187 seconds (3m 7s)
**Total commits:** 3
**Total files created:** 9
**Total files modified:** 1

## Self-Check: PASSED

Verified all claims:
- ✓ All model files exist and contain expected classes
- ✓ All schema files exist and contain expected patterns
- ✓ Migration file exists with correct revision metadata
- ✓ All commits exist in git history
- ✓ All imports succeed without errors
