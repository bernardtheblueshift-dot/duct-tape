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

**Plans**: TBD

---

### Phase 3: Resource Management
**Goal**: Admin can assign crew and equipment to jobs with automatic conflict prevention

**Depends on**: Phase 2

**Requirements**: CREW-01, CREW-02, CREW-03, CREW-04, CREW-05, CREW-06, CREW-07, CREW-08, CREW-09, EQUP-01, EQUP-02, EQUP-03, EQUP-04, SCHED-05

**Success Criteria** (what must be TRUE):
  1. Admin can create crew profiles with name, role, skills, rate, contact details and see them in directory
  2. Admin can edit crew profiles and archive crew no longer available
  3. Admin can search crew directory by name, filter by role/skill, and see availability status
  4. Crew can accept or decline job assignments via confirmation workflow
  5. Admin can rate crew reliability after job completion and view reliability history
  6. Crew profile displays past jobs worked and reliability trend
  7. Skills matrix view shows all crew members with their skill tags for gap analysis
  8. Crew can set recurring availability patterns (e.g., unavailable Sundays) that block those times
  9. Crew availability automatically updates when assigned to jobs (free → booked)
  10. Admin can add equipment to inventory with name, category, quantity, condition
  11. Admin can assign equipment to jobs and see assignment history
  12. System prevents double-booking equipment using database-level conflict detection
  13. Equipment status automatically updates when assigned (available → assigned)
  14. Assigning crew to overlapping job times triggers conflict error (database-level locking prevents race conditions)

**Plans**: TBD

---

### Phase 4: Calendar & Scheduling
**Goal**: Admin views resource allocation visually across time with interactive scheduling

**Depends on**: Phase 3

**Requirements**: SCHED-01, SCHED-02, SCHED-03, SCHED-04, SCHED-06

**Success Criteria** (what must be TRUE):
  1. Month view shows all jobs and resource bookings in calendar grid
  2. Week view displays daily breakdown with crew and equipment assignments
  3. Day view shows detailed hour-by-hour schedule for each resource
  4. Calendar displays crew availability states (free, booked, unavailable) with visual distinction
  5. Crew can export their personal schedule via iCal download for sync with personal calendar apps

**Plans**: TBD

---

### Phase 5: Coordination Layer (Messaging + Tasks + Files)
**Goal**: Users collaborate on jobs through threaded messaging, task assignment, and file sharing in real-time

**Depends on**: Phase 2

**Requirements**: MSG-01, MSG-02, MSG-03, MSG-04, TASK-01, TASK-02, TASK-03, TASK-04, TASK-05, FILE-01, FILE-02, FILE-03, FILE-04

**Success Criteria** (what must be TRUE):
  1. Users post threaded messages to job-scoped channels with Slack-like conversation flow
  2. Messages support basic text formatting (bold, italic, links, lists)
  3. Message history within a job is searchable by text and author
  4. Messages appear in real-time via WebSocket connection without browser refresh
  5. Admin creates tasks linked to jobs with assignee, deadline, and priority level
  6. Tasks have status workflow (todo → in progress → done) and display overdue warnings
  7. Crew can view tasks assigned to them and update task status
  8. Tasks can reference originating messages to preserve conversation context
  9. Users upload files to jobs (briefs, runsheets, photos, videos, documents)
  10. Images and PDFs show inline preview without downloading
  11. Files are organized per job with metadata (uploader, timestamp, size)
  12. File access is tenant-isolated using signed URLs (predictable paths blocked)

**Plans**: TBD

---

### Phase 6: Notifications
**Goal**: Users receive timely email alerts for job assignments and updates

**Depends on**: Phase 3

**Requirements**: NOTF-01, NOTF-02, NOTF-03

**Success Criteria** (what must be TRUE):
  1. Crew receives email when assigned to a job with job details and confirmation link
  2. All job participants receive email when job is updated or cancelled
  3. In-app notification badge shows count of unread messages and new assignments

**Plans**: TBD

---

### Phase 7: Crew Portal
**Goal**: Crew members access their schedule, confirm bookings, and view job details from dedicated portal

**Depends on**: Phase 4, Phase 5, Phase 6

**Requirements**: PORT-01, PORT-02, PORT-03, PORT-04

**Success Criteria** (what must be TRUE):
  1. Crew dashboard displays upcoming assignments in chronological order
  2. Crew can view job details and access briefs/files for their assignments
  3. Crew can confirm or decline assignments directly from portal (triggers notification to admin)
  4. Crew can update their own profile details and availability patterns

**Plans**: TBD

---

### Phase 8: UI Polish
**Goal**: Interface reflects event production aesthetic with mobile accessibility

**Depends on**: Phase 1

**Requirements**: UI-01, UI-02, UI-03

**Success Criteria** (what must be TRUE):
  1. Application uses dark theme with production industry visual aesthetic (not generic SaaS)
  2. All views are mobile-responsive and functional on phone browsers without native app
  3. Admin dashboard shows at-a-glance summary of upcoming jobs and resource utilization status

**Plans**: TBD

---

## Progress

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundation & Multi-Tenancy | 3/3 | Complete   | 2026-05-15 |
| 2. Job Management | 0/? | Not started | - |
| 3. Resource Management | 0/? | Not started | - |
| 4. Calendar & Scheduling | 0/? | Not started | - |
| 5. Coordination Layer | 0/? | Not started | - |
| 6. Notifications | 0/? | Not started | - |
| 7. Crew Portal | 0/? | Not started | - |
| 8. UI Polish | 0/? | Not started | - |

## Research Flags

**Phases requiring deeper research before planning:**

- **Phase 3 (Resource Management)**: Conflict detection algorithms (PostgreSQL exclusion constraints vs advisory locks), availability modeling (store free blocks vs derive from assignments). Performance critical.

- **Phase 5 (Coordination Layer)**: WebSocket scaling patterns (single server vs Redis pub/sub), connection management at scale, message retention policies, large file chunked uploads, virus scanning integration.

**Phases with standard patterns (skip research-phase):**

- Phase 1: Multi-tenant SaaS auth/RLS well-documented
- Phase 2: CRUD with state machines standard
- Phase 4: react-big-calendar well-documented
- Phase 6: Email notifications standard
- Phase 7: RBAC patterns standard
- Phase 8: UI frameworks standard

---

*Roadmap created: 2026-05-15*
*Last updated: 2026-05-16*
