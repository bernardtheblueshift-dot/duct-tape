# Roadmap: Duct Tape

**Project:** Crew and resource management SaaS for event production companies
**Core Value:** When a job ignites, a production manager can instantly see who's available, what gear is free, and assign resources from one place
**Granularity:** Standard (5-8 phases)
**Mode:** Yolo (fast iteration, validation through shipping)

## Phases

- [x] **Phase 1: Foundation & Multi-Tenancy** - Database, auth, tenant isolation with RLS (completed 2026-05-15)
- [ ] **Phase 2: Job Management** - Create, edit, search jobs with lifecycle states
- [ ] **Phase 3: Resource Management** - Crew and equipment with conflict detection
- [ ] **Phase 4: Calendar & Scheduling** - Visual calendar with availability views
- [ ] **Phase 5: Coordination Layer (Messaging + Tasks + Files)** - Job-scoped collaboration tools
- [ ] **Phase 6: Notifications** - Email alerts for assignments and updates
- [ ] **Phase 7: Crew Portal** - Crew-facing views and booking confirmations
- [ ] **Phase 8: UI Polish** - Dark theme, mobile-responsive design

## Phase Details

### Phase 1: Foundation & Multi-Tenancy
**Goal**: Database and authentication infrastructure with tenant isolation that prevents data leaks and supports timezone-aware operations

**Depends on**: Nothing (first phase)

**Requirements**: AUTH-01, AUTH-02, AUTH-03, AUTH-04, AUTH-05, AUTH-06, AUTH-07

**Success Criteria** (what must be TRUE):
  1. User can sign up with email, receive verification email, and complete account activation
  2. User can log in and session persists across browser refresh without re-authentication
  3. User can reset forgotten password via email link
  4. Admin can invite crew members to their tenant workspace
  5. Database queries automatically filter by tenant_id and PostgreSQL RLS policies enforce isolation
  6. All datetime operations handle timezones correctly (stored as TIMESTAMPTZ, displayed in user's local timezone)
  7. Cross-tenant access attempts are blocked at database level (RLS verification)

**Plans**: 3 plans in 3 waves

Plans:
- [x] 01-01-PLAN.md — Database foundation with PostgreSQL RLS and timezone-aware models (Wave 1) ✓
- [x] 01-02-PLAN.md — Core authentication (register, login, verify, reset, RBAC) (Wave 2) ✓
- [ ] 01-03-PLAN.md — Invitation workflow and test suite (Wave 3)

---

### Phase 2: Job Management
**Goal**: Admin can create and manage jobs through their full lifecycle from intake to completion

**Depends on**: Phase 1

**Requirements**: JOBS-01, JOBS-02, JOBS-03, JOBS-04, JOBS-05, JOBS-06

**Success Criteria** (what must be TRUE):
  1. Admin can create job with title, date/time, venue, description and see it in job list
  2. Admin can edit existing job details and delete jobs no longer needed
  3. Admin can search jobs by text and filter by date range, status, or venue
  4. Jobs transition through lifecycle states (intake → simmer → active → complete) with state history
  5. Admin can manually trigger state transitions with reason tracking
  6. Job detail view shows job metadata and placeholder sections for crew/gear/messages/tasks/files

**Plans**: 3 plans in 2 waves

Plans:
- [ ] 02-01-PLAN.md — Job model and schemas with lifecycle state management (Wave 1)
- [ ] 02-02-PLAN.md — CRUD endpoints with search and filtering (Wave 2)
- [ ] 02-03-PLAN.md — State transition endpoint with validation (Wave 2)

---
