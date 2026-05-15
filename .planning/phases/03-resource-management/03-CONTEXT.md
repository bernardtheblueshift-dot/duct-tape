# Phase 3: Resource Management - Context

**Gathered:** 2026-05-16
**Status:** Ready for planning

<domain>
## Phase Boundary

Crew profiles, equipment inventory, job assignments with confirmation workflow, and conflict detection that prevents double-booking. Admin manages crew and gear; crew can accept/decline assignments. Skills matrix and availability patterns round out the resource picture.

</domain>

<decisions>
## Implementation Decisions

### Crew-to-User relationship
- Crew profile is 1:1 with User account — every crew member must have a User (via invitation flow from Phase 1)
- Separate CrewProfile table with one-to-one FK to User — keeps auth concerns separate from crew data
- CrewProfile holds: skills, hourly rate, phone, bio, reliability stats
- Soft delete via `archived_at` timestamp on CrewProfile — archived crew hidden from search/assignment but historical data preserved
- Auto-create blank CrewProfile when a User with role=crew registers via invitation

### Assignment & confirmation flow
- Crew assignment: admin assigns directly, crew must confirm (pending → confirmed / declined)
- On decline: crew is unassigned, admin notified, decline history kept
- Equipment assignment: direct assign, no confirmation needed (gear doesn't have opinions)
- Assignment record includes a role/position field per job (e.g., "Camera Operator" on Job A, "Sound Tech" on Job B)

### Conflict detection behavior
- Crew conflicts: warn but allow admin override with reason — real production sometimes requires double-booking
- Time overlap: exact time range overlap (start1 < end2 AND start2 < end1) — jobs without scheduled times never conflict
- Equipment conflicts: hard block — physically can't be in two places, track available quantity per time slot
- Crew availability patterns also trigger conflict warnings (same warn-and-override flow as job overlap)
- All conflict checks happen at database level (decided in Phase 1 STATE.md)

### Skills & availability model
- Crew skills: free-text tags, tenant-scoped — admin creates skill vocabulary as needed
- Equipment categories: free-text, tenant-scoped — same pattern as crew skills for consistency
- Recurring availability: weekly day-of-week patterns (crew marks specific days as unavailable)
- Reliability ratings: 1-5 star rating per completed job, with optional notes — profile shows average + count

### Claude's Discretion
- Database indexing strategy for conflict detection queries
- Exact schema for the assignment/conflict warning response payloads
- How to handle equipment with quantity > 1 (individual tracking vs pool)
- Loading/error states for search and filter operations
- Pagination approach for crew directory and equipment inventory

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

No external specs — requirements are fully captured in decisions above and in `.planning/REQUIREMENTS.md` (CREW-01 through CREW-09, EQUP-01 through EQUP-04, SCHED-05).

### Existing codebase patterns
- `backend/app/models/base.py` — TenantMixin, TimestampMixin, Base class patterns (all new models MUST use these)
- `backend/app/models/job.py` — Enum-based state pattern, model structure reference
- `backend/app/models/user.py` — UserRole enum (admin/crew), User model that CrewProfile links to
- `backend/app/schemas/job.py` — JobResponse with `assigned_crew`/`assigned_gear` placeholders to populate
- `backend/app/core/permissions.py` — `require_admin`, `require_active` guards for endpoint protection
- `backend/app/core/state_machine.py` — State transition pattern (reference for assignment state machine)
- `backend/app/dependencies.py` — `get_current_user`, `get_current_tenant` auth dependencies
- `backend/app/api/v1/jobs.py` — CRUD + search endpoint patterns to replicate

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `TenantMixin` + `TimestampMixin`: All new models (CrewProfile, Equipment, Assignment) must use these
- `require_admin` / `require_active`: Permission guards for admin-only and auth-required endpoints
- `get_current_user` / `get_current_tenant`: Auth dependencies with RLS tenant context setting
- `JobState` enum + `state_machine.py`: Pattern for assignment status (pending/confirmed/declined)
- Job CRUD router pattern: Replicable for crew and equipment endpoints
- ILIKE search pattern from jobs: Reusable for crew directory search

### Established Patterns
- Alembic migrations created manually (Docker unavailable)
- Pydantic schemas: separate Create/Update/Response models per resource
- UUID primary keys on all models
- TIMESTAMPTZ for all datetime columns
- SET LOCAL for tenant context in every request

### Integration Points
- `JobResponse.assigned_crew` and `JobResponse.assigned_gear` placeholders need populating with real assignment data
- User registration flow (Phase 1) needs hook to auto-create CrewProfile for crew-role users
- Job state transitions may need awareness of assignments (e.g., can't complete a job with pending crew?)

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

*Phase: 03-resource-management*
*Context gathered: 2026-05-16*
