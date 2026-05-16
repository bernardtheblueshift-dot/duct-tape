# Requirements: Duct Tape

**Defined:** 2026-05-15
**Core Value:** When a job ignites, a production manager can instantly see who's available, what gear is free, and assign resources from one place.

## v1 Requirements

Requirements for initial release. Each maps to roadmap phases.

### Authentication & Multi-tenancy

- [x] **AUTH-01**: User can sign up with email and password
- [x] **AUTH-02**: User receives email verification after signup
- [x] **AUTH-03**: User can log in and session persists across browser refresh
- [x] **AUTH-04**: User can reset password via email link
- [x] **AUTH-05**: Admin can invite crew members to their tenant
- [x] **AUTH-06**: Each tenant's data is fully isolated (PostgreSQL RLS)
- [x] **AUTH-07**: Role-based access control (admin vs crew permissions)

### Job Management

- [x] **JOBS-01**: Admin can create jobs with title, date/time, venue, description
- [x] **JOBS-02**: Admin can edit and delete jobs
- [x] **JOBS-03**: Admin can search and filter jobs by date, status, venue
- [x] **JOBS-04**: Jobs follow lifecycle states: intake → simmer → active → complete
- [x] **JOBS-05**: Admin can transition jobs between lifecycle states
- [x] **JOBS-06**: Job detail view shows all assigned crew, gear, messages, tasks, and files

### Crew Management

- [x] **CREW-01**: Admin can create crew profiles (name, role, skills, rate, contact details)
- [x] **CREW-02**: Admin can edit and archive crew profiles
- [x] **CREW-03**: Searchable crew directory filterable by role, skill, availability
- [x] **CREW-04**: Crew can accept or decline job assignments (confirmation workflow)
- [x] **CREW-05**: Admin can rate crew reliability after each job
- [x] **CREW-06**: Crew profile shows reliability history and past jobs
- [x] **CREW-07**: Skills matrix view showing crew capabilities across skill tags
- [x] **CREW-08**: Crew can set recurring availability patterns (e.g., "unavailable Sundays")
- [x] **CREW-09**: Crew availability auto-updates when assigned to jobs

### Equipment

- [x] **EQUP-01**: Admin can add equipment to inventory (name, category, quantity, condition)
- [x] **EQUP-02**: Admin can assign equipment to jobs
- [x] **EQUP-03**: Equipment conflict detection prevents double-booking gear
- [x] **EQUP-04**: Equipment status tracking (available, assigned, maintenance)

### Calendar & Scheduling

- [x] **SCHED-01**: Month view showing all jobs and resource bookings
- [x] **SCHED-02**: Week view with daily breakdown of assignments
- [x] **SCHED-03**: Day view showing detailed schedule per resource
- [x] **SCHED-04**: Crew availability visible on calendar (free, booked, unavailable)
- [x] **SCHED-05**: Conflict detection prevents double-booking crew across overlapping jobs
- [x] **SCHED-06**: Calendar export via iCal for crew to sync with personal calendars

### Messaging

- [ ] **MSG-01**: Threaded messaging per job (Slack-like channels scoped to each job)
- [ ] **MSG-02**: Messages support text with basic formatting
- [ ] **MSG-03**: Message history is searchable within a job
- [ ] **MSG-04**: Real-time message delivery via WebSockets

### Task Management

- [ ] **TASK-01**: Admin can create tasks linked to a job
- [ ] **TASK-02**: Tasks have assignee, deadline, priority (low/medium/high/urgent), and status
- [ ] **TASK-03**: Task status workflow: todo → in progress → done
- [ ] **TASK-04**: Crew can view and update tasks assigned to them
- [ ] **TASK-05**: Tasks can reference messages for context

### File Sharing

- [ ] **FILE-01**: Users can upload files to a job (briefs, runsheets, photos, videos, docs)
- [ ] **FILE-02**: File preview for images and PDFs
- [ ] **FILE-03**: Files are organized per job with upload metadata (who, when, size)
- [ ] **FILE-04**: Secure file storage with tenant isolation

### Notifications

- [ ] **NOTF-01**: Email notification when crew is assigned to a job
- [ ] **NOTF-02**: Email notification when a job is updated or cancelled
- [ ] **NOTF-03**: In-app notification badge for unread messages and new assignments

### Crew Portal

- [ ] **PORT-01**: Crew member dashboard showing upcoming assignments
- [ ] **PORT-02**: Crew can view job details and briefs for their assignments
- [ ] **PORT-03**: Crew can confirm or decline assignments from their portal
- [ ] **PORT-04**: Crew can update their own profile and availability

### UI & Design

- [ ] **UI-01**: Dark theme with event production aesthetic
- [ ] **UI-02**: Mobile-responsive design (works on phones without native app)
- [ ] **UI-03**: Admin dashboard with at-a-glance view of upcoming jobs and resource status

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Job Enhancements

- **JOBS-V2-01**: Ad-hoc intake capture (email forwarding → auto-create job)
- **JOBS-V2-02**: Job brief builder with structured templates
- **JOBS-V2-03**: Email chain linking (attach email threads to jobs)
- **JOBS-V2-04**: Recurring job templates (clone common job setups)

### Equipment Enhancements

- **EQUP-V2-01**: Equipment rental tracking (hired gear: source, dates, cost, returns)
- **EQUP-V2-02**: Custom fields per tenant (certifications, T-shirt sizes, etc.)

### Scheduling Enhancements

- **SCHED-V2-01**: Integrated Gantt-like timeline view (all jobs + crew + gear)
- **SCHED-V2-02**: Bulk crew assignment (multi-select and assign)
- **SCHED-V2-03**: Calendar sync via CalDAV (bidirectional)

### Auth Enhancements

- **AUTH-V2-01**: OAuth login (Google)
- **AUTH-V2-02**: Magic link login (passwordless)

### Notifications Enhancements

- **NOTF-V2-01**: SMS notifications
- **NOTF-V2-02**: Configurable notification preferences per user

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Native mobile app | Web-responsive sufficient; 3x complexity increase |
| Built-in video calling | Zoom/Teams already solve this |
| Accounting/invoicing | Not core value; integrate with Xero/QuickBooks later |
| Timesheets/payroll | Regulatory complexity, not core to scheduling |
| Public client portal | v1 is internal crew tool only |
| Advanced reporting/BI | Overkill early; export CSV, integrate Metabase later |
| Real-time collaborative editing | Async messaging sufficient; Google Docs-level sync too complex |
| Equipment maintenance logs | Notes field sufficient; full maintenance is a different product |
| Automated crew matching (ML) | Premature optimization; manual assignment with good search/filter |
| GPS/location tracking | Invasive; trust-based confirmation system instead |
| Social features | Not a social network; keep messaging job-scoped and professional |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| AUTH-01 | Phase 1 | Complete |
| AUTH-02 | Phase 1 | Complete |
| AUTH-03 | Phase 1 | Complete |
| AUTH-04 | Phase 1 | Complete |
| AUTH-05 | Phase 1 | Complete |
| AUTH-06 | Phase 1 | Complete |
| AUTH-07 | Phase 1 | Complete |
| JOBS-01 | Phase 2 | Complete |
| JOBS-02 | Phase 2 | Complete |
| JOBS-03 | Phase 2 | Complete |
| JOBS-04 | Phase 2 | Complete |
| JOBS-05 | Phase 2 | Complete |
| JOBS-06 | Phase 2 | Complete |
| CREW-01 | Phase 3 | Complete |
| CREW-02 | Phase 3 | Complete |
| CREW-03 | Phase 3 | Complete |
| CREW-04 | Phase 3 | Complete |
| CREW-05 | Phase 3 | Complete |
| CREW-06 | Phase 3 | Complete |
| CREW-07 | Phase 3 | Complete |
| CREW-08 | Phase 3 | Complete |
| CREW-09 | Phase 3 | Complete |
| EQUP-01 | Phase 3 | Complete |
| EQUP-02 | Phase 3 | Complete |
| EQUP-03 | Phase 3 | Complete |
| EQUP-04 | Phase 3 | Complete |
| SCHED-01 | Phase 4 | Complete |
| SCHED-02 | Phase 4 | Complete |
| SCHED-03 | Phase 4 | Complete |
| SCHED-04 | Phase 4 | Complete |
| SCHED-05 | Phase 3 | Complete |
| SCHED-06 | Phase 4 | Complete |
| MSG-01 | Phase 5 | Pending |
| MSG-02 | Phase 5 | Pending |
| MSG-03 | Phase 5 | Pending |
| MSG-04 | Phase 5 | Pending |
| TASK-01 | Phase 5 | Pending |
| TASK-02 | Phase 5 | Pending |
| TASK-03 | Phase 5 | Pending |
| TASK-04 | Phase 5 | Pending |
| TASK-05 | Phase 5 | Pending |
| FILE-01 | Phase 5 | Pending |
| FILE-02 | Phase 5 | Pending |
| FILE-03 | Phase 5 | Pending |
| FILE-04 | Phase 5 | Pending |
| NOTF-01 | Phase 6 | Pending |
| NOTF-02 | Phase 6 | Pending |
| NOTF-03 | Phase 6 | Pending |
| PORT-01 | Phase 7 | Pending |
| PORT-02 | Phase 7 | Pending |
| PORT-03 | Phase 7 | Pending |
| PORT-04 | Phase 7 | Pending |
| UI-01 | Phase 8 | Pending |
| UI-02 | Phase 8 | Pending |
| UI-03 | Phase 8 | Pending |

**Coverage:**
- v1 requirements: 43 total
- Mapped to phases: 43
- Unmapped: 0 ✓

---
*Requirements defined: 2026-05-15*
*Last updated: 2026-05-15 after roadmap creation*
