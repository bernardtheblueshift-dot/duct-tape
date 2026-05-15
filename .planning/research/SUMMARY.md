# Project Research Summary

**Project:** Duct Tape (Crew Management SaaS)
**Domain:** Event Production Resource Scheduling
**Researched:** 2026-05-15
**Confidence:** MEDIUM

## Executive Summary

Duct Tape is a crew and resource scheduling SaaS for event production teams—a domain where jobs arrive unpredictably, require rapid coordination, and success depends on preventing double-booking while maintaining conversational context. Research across stack, features, architecture, and pitfalls reveals a clear path: build a **conventional FastAPI + React + PostgreSQL SaaS** with multi-tenant row-level security, real-time WebSocket messaging, and calendar-first UX.

The recommended approach prioritizes three critical decisions early: (1) PostgreSQL Row-Level Security for tenant isolation (prevents data leaks and scales to 1000+ tenants), (2) time-range booking models with database-level conflict detection (prevents double-booking race conditions), and (3) WebSocket infrastructure from Phase 1 even if messaging comes later (retrofitting real-time is painful). The stack is intentionally conventional—proven libraries, well-documented patterns, no cutting-edge tech—because the differentiation comes from domain-specific workflow design (job lifecycle states, threaded messaging tied to tasks, ad-hoc intake capture), not technology innovation.

Key risks center on multi-tenancy implementation complexity and real-time messaging architecture. Both must be correct from day one: tenant isolation cannot be retrofitted without data migration, and WebSocket connection management at scale requires planning even if initial implementation is simple. The research identifies 16 specific pitfalls (6 critical, 6 moderate, 4 minor) with phase-specific prevention strategies.

## Key Findings

### Recommended Stack

A **battle-tested modern Python/React SaaS stack** built on FastAPI 0.136.1, React 19.2.6, and PostgreSQL 16+. This is not cutting-edge—it's deliberately conservative, prioritizing proven patterns over novelty.

**Core technologies:**
- **FastAPI + Pydantic + SQLAlchemy 2.0:** Async-first API framework with automatic OpenAPI docs, modern ORM with strong type hints, and native WebSocket support. Industry standard for Python SaaS.
- **PostgreSQL 16+ with Row-Level Security (RLS):** Multi-tenant data isolation via database policies plus SQLAlchemy filtering (defense-in-depth). Simpler than schema-per-tenant, scales to 1000s of tenants.
- **React 19 + Vite + TypeScript + TanStack Query:** Modern build tooling (faster than CRA), type safety, and server state management that replaces Redux. Zustand for lightweight UI state.
- **Redis + Celery:** Pub/sub for multi-worker WebSocket broadcast, background job queue for emails/file processing. Lightweight and fast.
- **S3/Cloudflare R2 with pre-signed URLs:** Direct client→object storage uploads (avoid proxying files through API). R2 has zero egress fees.
- **Tailwind CSS + Shadcn/ui + react-big-calendar:** Rapid dark theme development, accessible headless components, MIT-licensed calendar with resource timeline views (no $500 FullCalendar Pro license).

**Key architectural choices:**
- JWT tokens in httpOnly cookies (not localStorage) for XSS protection
- Pre-signed POST URLs for file uploads (no API memory pressure)
- WebSocket native (no Socket.io abstraction layer)
- Deployment to managed platforms (Fly.io/Railway) not Kubernetes (overkill for <1000 users)

**Rejected alternatives:** Django (monolithic), GraphQL (overkill), Next.js (SSR not needed, awkward WebSockets), Redux (verbose), FullCalendar Pro (expensive), schema-per-tenant (operational overhead).

**Confidence:** MEDIUM-HIGH. Versions verified via GitHub/PyPI/npm APIs. Patterns from training data (January 2025), unable to verify with 2026 best practices due to environment constraints.

### Expected Features

Research identified **clear tiers** for feature prioritization based on crew scheduling domain patterns:

**Must have (table stakes):**
- Crew scheduling with calendar views (month/week/day, drag-drop)
- Crew profiles with skills, rates, contact info, availability
- Job/event management with lifecycle states (intake/simmer/active/complete)
- Equipment inventory tracking (owned gear: name, category, quantity, status)
- Conflict detection (prevent double-booking crew and equipment)
- Assignment confirmation workflow (pending → confirmed/declined)
- Role-based access (admin full CRUD, crew view own schedule + confirm)
- Search/filter crew by skill, availability, past jobs
- Mobile-responsive UI (PWA approach, not native app)
- Basic notifications (email minimum, SMS bonus)

**Should have (differentiators):**
- **Threaded messaging per job** (Slack-like, job-scoped, searchable)—replaces scattered texts/emails
- **Task management separate from discussion** (assignee, deadline, priority, status)—extract actionables from threads
- **Ad-hoc intake capture** (email forwarding, parse/extract, manual cleanup)—turn rough ideas into job records
- **File sharing per job** (briefs, runsheets, contracts, photos)—centralize documents
- **Job lifecycle "simmer" state** (jobs that sit dormant before activation)—matches real workflow
- **Email chain linking** (attach existing email threads to jobs)—preserve context
- Crew reliability ratings (admin-only, show in profiles)
- Equipment rental tracking (hired gear separately from owned)
- Skills matrix visualization (tag-based, show coverage gaps)
- Bulk assignment and recurring job templates

**Defer to v2+:**
- Native mobile apps (PWA sufficient initially)
- Built-in video calling (Zoom/Teams already solve this)
- Accounting/invoicing (scope creep, integrate with Xero/QuickBooks later)
- Timesheets/payroll (regulatory complexity)
- Public client portal (v1 is internal crew tool)
- Advanced BI/reporting (CSV exports + external BI tools)
- Automated crew matching via ML (premature optimization)
- GPS tracking (feels invasive)

**Critical insight:** Features 8-11 (threaded messaging + tasks + files + intake) must ship together or users will continue using external tools. Calendar alone is not sticky.

**Confidence:** MEDIUM. Based on training data for crew scheduling tools (Show Division, StudioBinder, CrewCall patterns). Unable to verify with current product websites. Phase sequencing aligned with "full loop for v1" requirement.

### Architecture Approach

A **monolithic FastAPI app with service-layer boundaries** (not microservices) using PostgreSQL Row-Level Security for multi-tenancy. Optimize for developer velocity and operational simplicity at 100-1000 users, plan for service extraction at 10K+ users.

**Major components:**

1. **API Gateway Layer** — Auth/tenant resolution from JWT, CORS, rate limiting. Sets PostgreSQL session variable `app.current_tenant_id` for RLS enforcement.

2. **Job Management Service** — Job CRUD, state transitions (intake → simmer → active → complete), search/filtering, timeline tracking. Central organizing concept—all features reference jobs.

3. **Resource Management Service** — Crew profiles + equipment inventory, resource allocation to jobs, conflict detection with database-level locking (SELECT FOR UPDATE), availability calculation with caching.

4. **Messaging Service** — Threaded messaging (Slack-style), WebSocket gateway for real-time delivery, Redis pub/sub for multi-worker broadcast, message persistence with read receipts.

5. **Task Management Service** — Task CRUD with assignments, priority/deadline tracking, dependency management, status transitions. Tasks link to originating messages for context.

6. **File Service** — S3/R2 object storage with pre-signed URLs, metadata in PostgreSQL, thumbnail generation, version tracking for briefs/runsheets.

7. **Calendar Service** — Read-heavy layer for day/week/month views, drag-drop rescheduling (delegates to Resource Management), availability heatmaps with Redis caching.

8. **Authentication Service** — JWT issuance/refresh, password hashing (bcrypt/Argon2), role-based access control (admin vs crew), tenant membership verification.

**Data flow pattern:** Frontend → API Gateway (auth + tenant resolution) → Service Layer (business logic) → Data Access Layer (SQLAlchemy ORM) → PostgreSQL (RLS enforcement).

**Multi-tenancy strategy:** Row-Level Security with defense-in-depth (JWT tenant_id claim → FastAPI dependency → SQLAlchemy filter → PostgreSQL RLS policy). All tenant-scoped tables have `tenant_id` indexed and RLS enabled. Chosen over schema-per-tenant for simpler migrations, better connection pooling, and easier cross-tenant admin features.

**Scalability plan:** Monolith + read replicas at 1K users, service split + sharding at 10K users. Don't prematurely optimize.

**Confidence:** MEDIUM. Based on domain-driven design principles and SaaS multi-tenancy patterns from training data. Not verified with real crew management system architectures.

### Critical Pitfalls

Top 6 pitfalls that cause rewrites or major issues:

1. **Naive Multi-Tenancy (Shared Schema Without RLS)** — Application-layer `tenant_id` filtering leads to data leaks, slow queries as any tenant grows large, and security audit failures. **Prevention:** Implement PostgreSQL RLS policies from Phase 1. Defense-in-depth: JWT tenant extraction + ORM filters + RLS. **Must decide in Phase 1—cannot refactor later without full data migration.**

2. **Optimistic Locking for Conflicts (Double-Booking Hell)** — Checking availability then inserting bookings without database-level locking allows race conditions. Two admins assign same crew simultaneously. **Prevention:** Use `SELECT FOR UPDATE` in transactions, PostgreSQL exclusion constraints for time-based conflicts, pessimistic locking for booking operations. **Must be correct in Phase 2 (Resource Management)—retrofitting locks is error-prone.**

3. **Timezone Naivety (Works Fine Locally Disaster)** — Storing datetimes without timezone info. Jobs scheduled for "9am" show at wrong times for distributed crews. **Prevention:** All datetime columns are `TIMESTAMPTZ` (not `TIMESTAMP`), store user/tenant timezone separately, display in user's local timezone, test with UTC/UTC+10/UTC-8 simultaneously. **Must decide in Phase 1—changing column types later requires data migration.**

4. **File Upload Storage Without Tenant Isolation** — Predictable file paths (`/uploads/{job_id}/{filename}`) with application-only access control. Tenant A can access Tenant B's files by guessing URLs. **Prevention:** Object storage (S3/R2) with signed URLs, UUID file keys (not predictable names), metadata in database with `tenant_id`, short-expiry pre-signed URLs. **Must be correct in Phase 3 (Files)—retrofitting secure storage is painful.**

5. **Real-Time Messaging as an Afterthought** — Implementing messaging with polling or bolt-on HTTP creates poor UX (users refresh constantly), database load, battery drain on mobile, no presence indicators. **Prevention:** Plan WebSocket/SSE architecture in Phase 1 even if implementation comes later. Use Redis pub/sub for multi-worker broadcast. **Architecture decisions must be made early even if messaging ships in Phase 5.**

6. **Inadequate Availability Modeling** — Simple boolean (available/unavailable) or day-level granularity. Cannot handle partial-day bookings, tentative holds, or multi-job days. **Prevention:** Model bookings with `start_time` + `end_time` (not just dates), support booking states (confirmed/tentative/pending/declined), allow overlapping with warnings, hour-level UI granularity. **Core data model must support from Phase 2 (Resource Management).**

**Confidence:** HIGH for pitfalls 1-5 (general SaaS/scheduling patterns, well-documented failures). MEDIUM for pitfall 6 (domain-specific, not verified with production managers).

## Implications for Roadmap

Based on research, suggested **9-phase structure** organized around three critical milestones: (1) data foundation with tenant isolation, (2) core scheduling loop with conflict prevention, (3) coordination layer for daily stickiness.

### Phase 1: Foundation & Multi-Tenancy
**Rationale:** All features depend on tenant isolation, auth, and database schema. **Pitfall 1 (multi-tenancy)** and **Pitfall 3 (timezones)** must be prevented here—cannot be fixed later without migration.

**Delivers:**
- Database schema with Alembic migrations
- PostgreSQL RLS policies on all tenant-scoped tables
- JWT authentication with httpOnly cookies
- Tenant resolution middleware (extracts `tenant_id` from token, sets `app.current_tenant_id`)
- FastAPI app structure with logging, CORS, error handling

**Validation:** Can create tenant, register admin user, log in, receive JWT. RLS policies tested with cross-tenant access attempts.

**Research flag:** Standard multi-tenant SaaS patterns. Skip research-phase.

**Key decisions:**
- Row-Level Security vs schema-per-tenant (choose RLS for <1000 tenants)
- TIMESTAMPTZ for all datetime columns
- UUID primary keys (not sequential IDs)

---

### Phase 2: Job Management (Central Entity)
**Rationale:** Jobs are the organizing concept for all resources, messages, tasks, and files. Everything else references jobs.

**Delivers:**
- Job CRUD with tenant isolation
- Job state machine (intake → simmer → active → on-hold → cancelled → completed → archived)
- Status transition history (who changed, when, why)
- Job listing with search/filters (status, date range, text)
- Frontend job views (list, detail, create/edit forms)

**Addresses features:** Job/event management (table stakes), job lifecycle states (differentiator).

**Avoids pitfall:** **Pitfall 12 (ignoring job state complexity)**—implement full state machine from start, not simple 3-state enum.

**Research flag:** Standard patterns. Skip research-phase.

**Tech from stack:** FastAPI + Pydantic (request/response schemas), SQLAlchemy (ORM), React + TanStack Query (frontend state).

---

### Phase 3: Resource Management (Crew + Equipment)
**Rationale:** Jobs need resources to be useful. Core scheduling value delivered here. **Critical phase for Pitfall 2 (double-booking) and Pitfall 6 (availability modeling).**

**Delivers:**
- Crew profile management (name, role, skills, rate, contact, availability patterns)
- Equipment inventory (owned gear: name, category, quantity, status)
- Resource assignment (link crew/equipment to jobs with time ranges)
- Conflict detection with database-level locking (`SELECT FOR UPDATE`)
- Availability calculation engine
- Frontend resource views (crew list, equipment list, assignment UI)

**Addresses features:** Crew profiles, equipment inventory, conflict detection, availability tracking (all table stakes).

**Avoids pitfalls:**
- **Pitfall 2 (double-booking):** Pessimistic locking in transactions
- **Pitfall 6 (availability modeling):** `start_time`/`end_time` (not just dates), booking states (confirmed/tentative/pending)
- **Pitfall 14 (rate tracking):** Capture rate at booking time (snapshot), support effective-from dates

**Research flag:** **NEEDS RESEARCH.** Conflict detection algorithms (exclusion constraints vs advisory locks vs application logic), availability model (store free blocks vs derive from assignments). Performance critical.

**Tech from stack:** PostgreSQL range types + GiST indexes for overlap queries, Redis for availability caching.

---

### Phase 4: Calendar & Scheduling UI
**Rationale:** Builds on resource assignments. Calendar is primary interface for production managers (spatial thinkers).

**Delivers:**
- Calendar day/week/month views (react-big-calendar)
- Resource utilization heatmap
- Drag-and-drop rescheduling (updates assignments)
- Availability visualization (who's free when)
- Interactive booking (not just read-only reports)

**Addresses features:** Crew scheduling calendar (table stakes), date range views (table stakes).

**Avoids pitfall:** **Pitfall 10 (calendar performance degradation)**—database indexes on date ranges, pagination/virtualization, Redis caching for frequently-accessed views, fetch only visible range.

**Research flag:** Standard patterns. Skip research-phase.

**Tech from stack:** react-big-calendar + date-fns (calendar UI), PostgreSQL BTREE indexes on `start_time`/`end_time`, Redis (cache).

**Anti-pattern:** Don't build calendar as read-only view. Drag-drop and inline editing are essential.

---

### Phase 5: Messaging & Real-Time
**Rationale:** Requires WebSocket infrastructure. **Critical for Pitfall 5 (messaging as afterthought)—architecture must be correct from start even if features come later.** Delivers first part of "coordination layer" that makes daily usage sticky.

**Delivers:**
- WebSocket gateway with tenant/job authentication
- Threaded messaging (Slack-style, job-scoped)
- Message persistence with thread/message models
- Real-time broadcast via Redis pub/sub (multi-worker support)
- Message history and search
- Read receipts and presence indicators
- Frontend chat UI (Slack-like component)

**Addresses features:** Threaded messaging per job (differentiator—core to product stickiness).

**Avoids pitfall:** **Pitfall 5 (real-time as afterthought)**—WebSocket connection manager with Redis backing, not polling.

**Research flag:** **NEEDS RESEARCH.** WebSocket scaling patterns (single server vs Redis pub/sub), message retention policies, connection management at scale. FastAPI WebSocket docs may be insufficient.

**Tech from stack:** FastAPI WebSockets (native), Redis pub/sub (broadcast across workers), PostgreSQL (message persistence).

**Anti-pattern:** Don't implement as comment log. Need threading, reactions, notifications.

---

### Phase 6: Task Management
**Rationale:** Integrates with jobs and messaging. Can be built in parallel with Phase 5 (independent). Completes "coordination layer."

**Delivers:**
- Task CRUD with assignments
- Priority levels and deadlines
- Status tracking (todo → in-progress → done)
- Task dependencies (task A blocks task B)
- Overdue notifications
- Frontend task views (checklist, Kanban, or table)
- Link tasks to originating messages (preserve conversation context)

**Addresses features:** Task management (differentiator—separates actionables from discussion).

**Avoids pitfall:** **Pitfall 11 (tasks separate from message context)**—tasks must reference messages, show originating thread.

**Research flag:** Standard patterns. Skip research-phase.

**Tech from stack:** PostgreSQL (task models), TanStack Query (optimistic updates).

**Implementation note:** Tasks created from messages (message → task link), task comments thread back to main conversation.

---

### Phase 7: File Storage & Sharing
**Rationale:** Needs external service integration (S3/R2). Can be built in parallel with Phases 5-6 (independent). Completes "coordination layer."

**Delivers:**
- Object storage setup (S3 or Cloudflare R2)
- Pre-signed URL generation for uploads/downloads
- File metadata storage in PostgreSQL
- Tenant/job-based access control
- Thumbnail generation for images
- Frontend file UI (drag-drop upload, file list, download/delete)
- File versioning for briefs/runsheets (optional)

**Addresses features:** File sharing per job (differentiator).

**Avoids pitfall:** **Pitfall 4 (file storage without tenant isolation)**—UUID file keys, signed URLs, metadata validation with `tenant_id`.

**Research flag:** **NEEDS RESEARCH.** Large file chunked uploads (>100MB), virus scanning (ClamAV vs cloud service), R2 vs S3 pricing for video/photo heavy usage.

**Tech from stack:** boto3 (S3 SDK), Cloudflare R2 (S3-compatible, zero egress), Pillow (thumbnails).

**Anti-pattern:** Don't store file blobs in PostgreSQL. Metadata only.

---

### Phase 8: Ad-Hoc Intake & Email Integration
**Rationale:** Addresses intake friction (second major pain point after scheduling). Nice-to-have, not critical path.

**Delivers:**
- Email forwarding webhook or IMAP polling
- Email parsing and metadata extraction
- Email-to-job linking (attach threads to jobs)
- Manual cleanup UI for extracted data
- Outbound transactional email (notifications via Celery queue)
- Frontend email view (display linked threads)

**Addresses features:** Ad-hoc intake capture (differentiator), email chain linking (differentiator), basic notifications (table stakes).

**Avoids pitfall:** **Pitfall 15 (email deduplication)**—use Message-ID header, track thread IDs (References/In-Reply-To), update existing threads on replies.

**Research flag:** **NEEDS RESEARCH.** Email parsing libraries, OAuth flows for IMAP, webhook providers (SendGrid/Postmark), deliverability best practices.

**Tech from stack:** Celery (async email sending), Redis (queue broker).

**Anti-pattern:** Don't send email synchronously in request path (blocks responses).

---

### Phase 9: Crew Portal
**Rationale:** Requires all other features to be useful. Crew-facing views built on top of admin features.

**Delivers:**
- Crew-specific views (my schedule, my jobs, my tasks)
- Booking confirmation workflow (accept/decline assignments)
- Job brief access (read-only job details and files)
- Simplified navigation (crew-focused UI, not admin tools)
- Calendar export (iCal/CalDAV or Google Calendar API)

**Addresses features:** Assignment confirmation (table stakes), export to calendar (table stakes), mobile-responsive UI (table stakes).

**Research flag:** **NEEDS RESEARCH.** PWA vs native mobile app decision, offline support via service workers, calendar sync protocols (CalDAV/iCal).

**Tech from stack:** React (same codebase, different routes), TailwindCSS (responsive design).

**Anti-pattern:** Don't treat crew as passive data subjects. Crew portal is first-class UX, not afterthought.

---

### Phase Ordering Rationale

**Critical path (delivers core value):**
- Phase 1 → 2 → 3 → 4 = Foundation + job scheduling with conflict prevention
- This is the "single source of truth" for who/what is available—solves primary pain point

**Parallel tracks after Phase 4:**
- **Track A:** Phase 5 (Messaging) — WebSocket infrastructure, independent
- **Track B:** Phase 6 (Tasks) — Independent, can parallel with messaging
- **Track C:** Phase 7 (Files) — Object storage, independent

If multiple developers available, Phases 5-7 can be concurrent (no dependencies).

**Why coordination layer (5+6+7) must ship together:**
- Messaging alone = users still use external tools
- Tasks alone = feels like generic todo app
- Files alone = just Dropbox
- **Together** = sticky daily workflow (discuss → extract tasks → attach files)

**Why intake comes later (Phase 8):**
- Intake is valuable but not required for core loop
- Email integration adds operational complexity (deliverability, spam)
- Users can manually create jobs initially

**Why crew portal is last (Phase 9):**
- Needs all features to be useful (schedule, tasks, files, messages)
- Admin features must stabilize first
- Can launch with admin-only tool, add crew access later

**How this avoids pitfalls:**
- Phase 1 decisions (RLS, timezones) prevent **Pitfalls 1+3** (cannot be fixed later)
- Phase 3 locking prevents **Pitfall 2** (double-booking)
- Phase 5 architecture prevents **Pitfall 5** (real-time as afterthought)
- Phase 7 S3 setup prevents **Pitfall 4** (file storage insecurity)

---

### Research Flags

**Phases needing deeper research during planning:**

- **Phase 3 (Resource Management):** Conflict detection algorithms (PostgreSQL exclusion constraints vs advisory locks vs application logic), availability model (store free blocks vs derive from assignments). Performance critical, multiple approaches exist.

- **Phase 5 (Messaging):** WebSocket scaling (single server vs Redis pub/sub for multi-instance), connection management patterns, message retention policies. FastAPI WebSocket docs may be insufficient for production scale.

- **Phase 7 (File Storage):** Large file chunked uploads (>100MB), virus scanning integration (ClamAV vs cloud service), cost comparison (S3 vs Backblaze B2 vs Cloudflare R2 for video/photo heavy usage).

- **Phase 8 (Email Integration):** Email parsing libraries, OAuth flows for IMAP access, webhook providers (SendGrid/Postmark/Mailgun), deliverability best practices, spam prevention.

- **Phase 9 (Crew Portal):** PWA vs native mobile app decision (what do crew actually need?), offline support requirements, calendar sync protocols (CalDAV/iCal vs Google Calendar API).

**Phases with standard patterns (skip research-phase):**

- **Phase 1 (Foundation):** Multi-tenant SaaS auth/RLS is well-documented.
- **Phase 2 (Job Management):** CRUD with state machines is standard.
- **Phase 4 (Calendar UI):** react-big-calendar is well-documented.
- **Phase 6 (Task Management):** Standard task model patterns.

---

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | **MEDIUM-HIGH** | Core library versions verified via GitHub/PyPI/npm APIs. Patterns from training data (January 2025). Unable to verify with 2026 best practices due to environment constraints. Conservative choices reduce risk. |
| Features | **MEDIUM** | Based on training data for crew scheduling tools (Show Division, StudioBinder, CrewCall patterns). Unable to verify with current product websites. MVP sequencing aligned with "full loop for v1" requirement from PROJECT.md. |
| Architecture | **MEDIUM** | Service boundaries based on domain-driven design principles. Multi-tenancy (RLS) is standard pattern. Not verified with real crew management system architectures. Build order dependencies logical but not validated. |
| Pitfalls | **MEDIUM-HIGH** | HIGH confidence for general SaaS pitfalls (multi-tenancy, timezones, file storage, race conditions)—well-documented failure modes. MEDIUM confidence for domain-specific pitfalls (availability modeling, equipment state)—not verified with production managers. |

**Overall confidence:** MEDIUM

### Gaps to Address

**Unable to verify without external access:**

1. **Current best practices for FastAPI multi-tenancy in 2026** — RLS pattern is from 2023-2024 training data. May be newer approaches or library support (e.g., FastAPI-Users multi-tenancy plugins).

2. **Competitor feature sets** — Could not access Show Division Crew, CrewCall, StudioBinder, Assemble, Current RMS websites. Feature categorization (table stakes vs differentiators) based on inference from training data.

3. **Alternative calendar libraries released 2025-2026** — react-big-calendar chosen from training data. May be newer options with better resource timeline views or performance.

4. **Emerging real-time patterns** — WebSocket vs Server-Sent Events (SSE) vs managed services (Pusher/Ably) for this use case. Pattern from training data may not reflect 2026 consensus.

5. **React 19-specific state management patterns** — Concurrent features and transitions may change best practices for TanStack Query + Zustand combination.

**How to handle gaps during planning:**

- **Phase 1 (Foundation):** Use Context7 to verify current FastAPI multi-tenancy patterns, PostgreSQL RLS best practices. Critical decision point.
- **Phase 3 (Resource Management):** Research conflict detection algorithms with Context7 (PostgreSQL docs, scheduling system case studies). Performance implications need validation.
- **Phase 4 (Calendar):** Evaluate react-big-calendar alternatives (FullCalendar, TUI Calendar) with current docs before committing.
- **Phase 5 (Messaging):** Deep research on FastAPI WebSocket production patterns, Redis pub/sub scaling, connection management libraries.
- **Phase 8 (Email):** Research email parsing libraries (Python email package, mailparser), OAuth flows, webhook providers.

**Validation needs with users:**

- Feature prioritization with production managers (user interviews)—is messaging valued or do they prefer external tools?
- Rental gear tracking importance—table stakes or differentiator?
- Custom fields requirement—some tenants may need this in Phase 2
- Crew reliability metrics definition—what actually matters?

**Research method limitations:**

All research conducted via training data analysis (knowledge cutoff January 2025) and API version checks. No web search access, no Context7 library access, no competitor product analysis. Recommendations are conservative and proven but may not reflect cutting-edge 2026 approaches.

## Sources

### Primary (HIGH confidence)

**Version verification (API calls):**
- FastAPI: GitHub API (tag 0.136.1)
- React: GitHub API (tag v19.2.6)
- SQLAlchemy: GitHub API (tag rel_2_0_49)
- Pydantic: GitHub API (tag v2.13.4)
- Alembic, Celery, Redis, PyJWT, Passlib, Uvicorn, python-multipart: PyPI API
- TanStack Table, react-big-calendar, Zustand, Tailwind CSS, React Router: npm registry API

### Secondary (MEDIUM confidence)

**Architectural patterns (training data):**
- Multi-tenant SaaS design patterns (row-level security, schema-per-tenant tradeoffs)
- FastAPI async patterns, dependency injection, WebSocket support
- PostgreSQL RLS policies, range types, exclusion constraints
- Scheduling system domain models (bookings, conflicts, availability)
- React state management (TanStack Query + Zustand patterns)
- Object storage patterns (pre-signed URLs, S3/R2 usage)

**Domain knowledge (training data + PROJECT.md):**
- Event production crew management workflows
- Resource scheduling conflict detection
- Job lifecycle patterns for service businesses
- Real-time messaging requirements for coordination tools

### Tertiary (LOW confidence, needs validation)

**Scalability thresholds:**
- 100 users = monolith, 1K users = read replicas, 10K users = service split
- Based on general SaaS patterns, not production data for this specific stack/domain

**Feature categorization:**
- Table stakes vs differentiators vs anti-features
- Inferred from training data on crew scheduling tools (Show Division, StudioBinder, CrewCall)
- Unable to verify with current product websites

**Unable to access (environment constraints):**
- Show Division Crew official website/documentation
- CrewCall, StudioBinder, Assemble, Current RMS product pages
- 2026 FastAPI/PostgreSQL/React best practice articles
- Crew management SaaS case studies or architecture deep dives
- Production benchmarks for FastAPI + PostgreSQL multi-tenant setups

---

**Research completed:** 2026-05-15  
**Ready for roadmap:** Yes

**Next step:** Use this summary as context for roadmap creation. Phase suggestions provide starting structure. Research flags identify which phases need `/gsd:research-phase` before detailed planning.
