# Phase 7: Crew Portal - Context

**Gathered:** 2026-05-17
**Status:** Ready for planning

<domain>
## Phase Boundary

Crew-facing API endpoints — a dedicated /portal/ router providing crew-perspective views of existing data. Dashboard with upcoming and recent assignments, assignment-scoped job detail access, assignment confirmation/decline, and self-service profile/availability management. Backend API only, no React frontend.

</domain>

<decisions>
## Implementation Decisions

### Backend vs frontend scope
- Backend API only — no React portal UI in this phase
- Separate /api/v1/portal/ router for all crew-facing endpoints — clear separation from admin endpoints
- Most underlying logic already exists — this phase adds crew-perspective views and permission wrappers

### Dashboard data shape
- Dashboard endpoint returns: upcoming assignments (all future) + recently completed (last 7 days) + notification counts (unread messages, pending assignments)
- Assignments include job title, dates, venue, role, assignment status
- Separate sections in response: upcoming, recent, counts
- One call gives crew everything they need on login

### Job detail access
- GET /portal/jobs/{id} returns job details + files (briefs) only if crew is assigned to that job
- Assignment check enforced — crew can't browse all jobs, only their own
- Reuses existing Job query logic with assignment verification

### Assignment confirmation
- GET /portal/assignments lists crew's own assignments with status
- POST /portal/assignments/{id}/confirm and /decline wrappers around existing transition endpoint
- Crew can only act on their own assignments

### Crew self-service boundaries
- Crew can edit: phone, bio, availability patterns (contact + scheduling)
- Crew cannot edit: skills, hourly rate (admin-managed)
- GET /portal/profile returns own crew profile
- PATCH /portal/profile updates allowed fields only
- PUT /portal/availability wraps existing availability endpoint with own-profile enforcement
- Crew cannot see other crew members — portal is self-focused

### Claude's Discretion
- Dashboard response schema structure
- Assignment sorting (by date, by status priority)
- How to handle crew without a CrewProfile (edge case)
- Error messages for unauthorized access attempts (assigned-only enforcement)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

No external specs — requirements fully captured in decisions above and in `.planning/REQUIREMENTS.md` (PORT-01 through PORT-04).

### Existing codebase patterns
- `backend/app/api/v1/crew.py` — Existing crew endpoints (profile CRUD, availability, ratings) — portal wraps these with crew-only permissions
- `backend/app/api/v1/assignments.py` — Assignment transition endpoint (confirm/decline) — portal provides crew-scoped wrappers
- `backend/app/api/v1/jobs.py` — Job detail endpoint — portal adds assignment check
- `backend/app/api/v1/notifications.py` — Notification counts endpoint — reuse for dashboard counts
- `backend/app/models/assignment.py` — CrewAssignment with AssignmentState enum
- `backend/app/models/crew_profile.py` — CrewProfile linked 1:1 to User
- `backend/app/core/permissions.py` — require_admin, require_active guards
- `backend/app/dependencies.py` — get_current_user, get_current_tenant

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `get_current_user` dependency: Identifies crew member for portal queries
- `CrewAssignment` queries: Already filter by crew_id and status
- `require_active` guard: Ensures crew has verified email before portal access
- Availability set/get endpoints: Already enforce crew-can-only-set-own (Phase 3 decision)
- NotificationCounts endpoint: Reuse computation for dashboard counts

### Established Patterns
- Router registration in main.py
- Pydantic Create/Update/Response schemas
- RLS tenant isolation via SET LOCAL
- ILIKE search, batch query optimization

### Integration Points
- Portal router registered in main.py alongside existing routers
- Dashboard queries across Job + CrewAssignment + Message + MessageLastSeen tables
- Profile update endpoint must restrict fields (no skills/rate editing by crew)
- Job detail endpoint adds assignment existence check before returning data

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

*Phase: 07-crew-portal*
*Context gathered: 2026-05-17*
