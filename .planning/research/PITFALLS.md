# Domain Pitfalls: Crew Management SaaS

**Domain:** Event production crew and resource scheduling
**Researched:** 2026-05-15
**Confidence:** MEDIUM (based on domain patterns, training data, and SaaS architecture principles)

---

## Critical Pitfalls

Mistakes that cause rewrites or major issues.

### Pitfall 1: Naive Multi-Tenancy (Shared Schema Without Proper Isolation)

**What goes wrong:** Using tenant_id columns with application-layer filtering leads to data leakage, slow queries as tenant data grows, and difficult-to-debug cross-tenant contamination.

**Why it happens:** Initial implementation seems simple ("just add tenant_id to every table"). Row-level security feels like premature optimization.

**Consequences:**
- Query performance degrades non-linearly as ANY tenant grows large (indexes scan all tenants)
- One tenant's 10K jobs slows down a tenant with 50 jobs
- Data leaks when developers forget WHERE tenant_id = filters (happens eventually)
- Difficult to offer tenant-specific performance tuning or data residency
- Hard to implement tenant-level backup/restore or migrations

**Prevention:**
- Use PostgreSQL schemas per tenant OR separate databases (schema-per-tenant recommended for <1000 tenants)
- Implement Row-Level Security (RLS) policies as defense-in-depth even if using schemas
- Set session variables for current tenant context, not application-layer filters
- Test queries with multi-million row datasets for one tenant while others have <100 rows

**Detection:**
- Query plans show sequential scans across all tenant data
- Adding indexes doesn't improve performance proportionally
- "Works fine in dev" but slow in production with realistic data volumes
- Security audits flag missing tenant_id filters

**Phase:** Must be decided in Phase 1 (Foundation). Cannot refactor later without full data migration.

---

### Pitfall 2: Optimistic Locking for Resource Conflicts (Double-Booking Hell)

**What goes wrong:** Using application-layer conflict detection without database-level locking allows double-booking of crew or equipment when two admins assign the same resource simultaneously.

**Why it happens:** Developers check availability, then insert booking records without atomic reservation. Race conditions seem unlikely in testing.

**Consequences:**
- Crew member gets double-booked for overlapping jobs
- Equipment shows as available but is actually allocated
- Conflicts discovered only when crew/gear doesn't show up
- Loss of trust in the system's core promise (conflict detection)
- Awkward conversations with clients about booking mistakes

**Prevention:**
- Use database transactions with SELECT FOR UPDATE when checking availability
- Implement pessimistic locking for booking operations
- Add unique constraints or exclusion constraints for time-based conflicts (PostgreSQL range types + exclusion constraints)
- Consider advisory locks for multi-step booking workflows
- Show real-time "someone else is booking this resource" warnings in UI

**Detection:**
- Users report "system said it was available but now shows booked"
- Database logs show concurrent INSERT/UPDATE on same resource
- No transaction isolation in booking code
- Conflict detection happens in Python, not SQL

**Phase:** Phase 2 (Resource Management). Must be correct from first implementation—retrofitting locks is error-prone.

---

### Pitfall 3: Timezone Naivety (The "Works Fine Locally" Disaster)

**What goes wrong:** Storing datetimes without timezone info, or assuming server/database timezone matches user timezone. Jobs scheduled for "9am" show at wrong times for distributed crews.

**Why it happens:** Single-location testing, UTC-only thinking, or assuming "we only operate in one timezone."

**Consequences:**
- Crew shows up at wrong time (or doesn't show up)
- Availability conflicts appear/disappear based on user location
- Month/week boundaries shift between users
- Reports and analytics show wrong dates
- Cannot expand to multi-location operations without data migration

**Prevention:**
- Store ALL datetimes as UTC with timezone in PostgreSQL (TIMESTAMPTZ)
- Store user/tenant timezone separately
- Display times in user's local timezone in UI
- Jobs should store both UTC time AND the intended display timezone ("9am Tokyo time")
- Test with users in UTC, UTC+10, UTC-8 simultaneously
- Use libraries that handle timezone transitions (DST, timezone database updates)

**Detection:**
- Times display wrong in browser
- Date filters return unexpected results
- Developers say "just use UTC" but UI shows UTC times to users
- Database has TIMESTAMP (not TIMESTAMPTZ) columns

**Phase:** Phase 1 (Foundation). Changing column types later requires data migration and downtime.

---

### Pitfall 4: File Upload Storage Without Tenant Isolation

**What goes wrong:** Storing uploaded files (briefs, photos, videos) in shared directories with predictable paths. File access controlled only by application logic.

**Why it happens:** Simple file storage (e.g., `/uploads/{job_id}/{filename}`) seems sufficient. Security by obscurity.

**Consequences:**
- Tenant A can access Tenant B's files by guessing URLs
- Deleted jobs leave orphaned files consuming storage
- No way to implement tenant-specific storage quotas
- Cannot offer tenant data export/deletion for GDPR/privacy compliance
- File permissions don't align with database permissions (e.g., crew can't access file but has job access)

**Prevention:**
- Use object storage with signed URLs (S3, MinIO, GCS)
- Generate UUIDs for file keys, not predictable names
- Implement pre-signed URL generation with short expiry
- Store file metadata in database with tenant_id, validate on every access
- Isolate files by tenant in storage structure (`/{tenant_id}/{job_id}/...`)
- Implement file lifecycle policies (auto-delete after job completion + N days)

**Detection:**
- Files stored in local filesystem or shared network storage
- URLs like `/uploads/job-123/brief.pdf` are directly accessible
- No authentication required to download files
- File access logs show cross-tenant requests succeeding

**Phase:** Phase 3 (File Sharing). Get it right from the start—retrofitting secure storage is painful.

---

### Pitfall 5: Real-Time Messaging as an Afterthought

**What goes wrong:** Implementing job messaging with polling, HTTP requests, or bolt-on solutions that don't scale or feel responsive.

**Why it happens:** WebSockets/SSE seem complex. "We'll add real-time later." REST-first mindset.

**Consequences:**
- Messages don't appear instantly (users refresh constantly)
- Polling creates database load and API traffic
- Poor mobile experience (battery drain, delayed notifications)
- Cannot implement presence indicators ("who's online")
- Threads feel disjointed compared to Slack/Discord
- Users abandon in-app messaging for external tools

**Prevention:**
- Plan WebSocket or SSE architecture from Phase 1
- Use battle-tested libraries (FastAPI supports WebSockets, use Redis for pub/sub)
- Implement connection management, reconnection, offline queue
- Store messages in database but push via WebSocket
- Consider managed solutions (Pusher, Ably) if budget allows
- Design message schema with threading, reactions, read receipts from start

**Detection:**
- UI polls `/api/messages` every N seconds
- Users complain messages don't appear immediately
- Database shows constant SELECT queries for message updates
- No WebSocket or SSE endpoints in API

**Phase:** Phase 4 (Messaging). Architecture decisions must be made early even if implementation comes later.

---

### Pitfall 6: Inadequate Crew Availability Modeling

**What goes wrong:** Modeling availability as simple boolean (available/unavailable) or day-level granularity. Cannot handle partial-day bookings, tentative holds, or multi-job days.

**Why it happens:** Simplistic data model ("crew has bookings, check for overlaps"). Underestimating complexity of real scheduling.

**Consequences:**
- Cannot book crew for half-day jobs
- No way to mark "tentative" bookings that might cancel
- Cannot handle crew working multiple jobs in one day (morning setup, evening teardown)
- Availability calendar shows entire day as blocked for 2-hour booking
- Admins resort to external tracking to handle edge cases

**Prevention:**
- Model bookings with start_time + end_time (not just dates)
- Support booking states: confirmed, tentative, pending, declined
- Allow overlapping bookings with warnings (some crew can handle multiple gigs)
- Implement buffer times (travel between jobs, setup/teardown)
- Support recurring availability patterns ("available every Monday")
- UI shows hour-level granularity, not just day blocks

**Detection:**
- Database has `booking_date DATE` instead of time ranges
- Users ask "how do I book someone for just the morning?"
- Availability queries use DATE comparison, not TIMESTAMP ranges
- No booking status beyond boolean

**Phase:** Phase 2 (Resource Management). Core data model must support from day one.

---

## Moderate Pitfalls

Painful but recoverable mistakes.

### Pitfall 7: No Audit Trail for Resource Changes

**What goes wrong:** Resource assignments, job updates, and crew changes happen without logging who changed what when.

**Why it happens:** Audit logging feels like overhead. "We trust our users."

**Consequences:**
- Cannot answer "who assigned this crew member?"
- Disputes about schedule changes have no evidence
- Cannot detect or investigate malicious changes
- Compliance issues if handling sensitive data
- No undo/rollback capability

**Prevention:**
- Add created_by, updated_by, created_at, updated_at to all key tables
- Consider event sourcing for critical entities (bookings, assignments)
- Log job state transitions to separate audit table
- Implement soft deletes (deleted_at) not hard deletes
- UI shows change history for jobs/bookings

**Detection:**
- Tables lack updated_at/updated_by columns
- No audit or history tables
- DELETE queries instead of UPDATE with deleted_at
- Users ask "who changed this?" with no way to answer

**Phase:** Phase 1 (Foundation) for schema, Phase 5+ for UI display.

---

### Pitfall 8: Ignoring Crew Notification Preferences

**What goes wrong:** Sending all notifications via one channel (email) without considering crew preferences or urgency.

**Why it happens:** Email seems universal. Notification systems are complex.

**Consequences:**
- Critical job confirmations lost in spam folders
- Crew misses schedule updates because they don't check email
- Notification fatigue leads to important alerts being ignored
- Cannot reach crew urgently (email has hours of delay)
- No way to confirm crew received critical information

**Prevention:**
- Support multiple channels: email, SMS, in-app, push (for future mobile)
- Let crew set notification preferences per event type
- Implement urgency levels (critical = SMS, info = email)
- Track notification delivery and read status
- Require explicit confirmation for critical bookings (not just "email sent")

**Detection:**
- Only email notifications exist
- No delivery tracking or read receipts
- Users complain about missed notifications
- No way to send urgent alerts

**Phase:** Phase 6+ (Notifications). Can be added later but should be architected early.

---

### Pitfall 9: Equipment Tracking Without State Management

**What goes wrong:** Treating equipment as simple boolean (available/booked) without tracking physical state, location, or maintenance.

**Why it happens:** Copying crew booking model for equipment without considering physical assets.

**Consequences:**
- Cannot track where equipment is currently located
- No maintenance scheduling or service history
- Gear booked but actually broken/in-repair
- Cannot handle rented gear that needs return-by dates
- Missing consumables tracking (batteries, cables, etc.)

**Prevention:**
- Equipment should have status: available, booked, in-use, in-transit, maintenance, retired
- Track current location (warehouse, job site, in-transit)
- Maintenance log with service dates and next service due
- Differentiate owned vs rented gear (rental periods, return dates)
- Track equipment condition and issues
- Support kits (multiple items booked as a unit)

**Detection:**
- Equipment table mirrors crew table structure
- No location or status fields
- No maintenance tracking
- Users ask "where is this gear now?"

**Phase:** Phase 2 (Resource Management). Plan for complexity from start.

---

### Pitfall 10: Calendar Performance Degradation

**What goes wrong:** Calendar views (month, week, day) become unusably slow as bookings accumulate.

**Why it happens:** Naive queries that fetch all bookings in range for all crew/equipment without optimization.

**Consequences:**
- Calendar takes 10+ seconds to load
- UI freezes during date range changes
- Database CPU spikes on calendar access
- Cannot add features like drag-and-drop rescheduling
- Users resort to external calendars

**Prevention:**
- Use database indexes on date ranges (BTREE on start_time, end_time)
- Implement pagination or virtualization for large crew lists
- Cache frequently-accessed calendar views (Redis)
- Use PostgreSQL range types and GiST indexes for overlap queries
- Fetch only visible date range + small buffer, not all bookings
- Consider materialized views for availability summaries

**Detection:**
- Calendar queries take >1 second
- EXPLAIN shows sequential scans on bookings table
- No indexes on date columns
- Calendar fetches all bookings then filters in JavaScript

**Phase:** Phase 2 (Resource Management) for query optimization, Phase 5+ for caching.

---

### Pitfall 11: Task Management Separate from Message Context

**What goes wrong:** Tasks exist as separate entities from job discussions, losing conversation context that led to task creation.

**Why it happens:** Modeling tasks like a traditional todo app instead of conversational workflow.

**Consequences:**
- "What did we decide about this task?" requires reading separate thread
- Cannot trace task origin or reasoning
- Crew receives task without context
- Re-asking questions already answered in messages
- Task list feels disconnected from actual work happening in threads

**Prevention:**
- Tasks can be created from messages (message → task link)
- Task view shows originating message/thread
- Task comments thread back to main job conversation
- UI allows inline task creation during discussions
- Tasks reference specific messages as context

**Detection:**
- Tasks table has no relation to messages table
- Users copy message text into task descriptions
- No way to see conversation that led to task

**Phase:** Phase 4 (Messaging) and Phase 5 (Tasks) must coordinate.

---

### Pitfall 12: Ignoring Job State Complexity

**What goes wrong:** Modeling job lifecycle as simple linear progression (intake → active → complete) without handling real-world complexity.

**Why it happens:** Requirements list "job lifecycle" but real workflows are messier.

**Consequences:**
- Cannot handle jobs that pause/resume (client delays)
- No way to represent tentative/potential jobs vs confirmed
- Cancelled jobs vs completed jobs not distinguished
- Cannot track jobs that split into multiple sub-jobs
- Job reactivation after completion not supported

**Prevention:**
- Job status: inquiry, quoted, tentative, confirmed, active, on-hold, cancelled, completed, archived
- Allow state transitions in both directions (reactivate completed jobs)
- Track status history with timestamps and reasons
- Support sub-jobs or phases within a job
- Model "simmer" state explicitly (from requirements: jobs can sit dormant)

**Detection:**
- Job status is enum with 3-4 values only
- No status transition history
- Users ask "how do I put a job on hold?"
- Cannot search for "cancelled last month"

**Phase:** Phase 1 (Foundation). Job state model is core schema.

---

## Minor Pitfalls

Annoyances that impact UX but don't break core functionality.

### Pitfall 13: Poor Search/Filter Performance

**What goes wrong:** Crew and job search uses LIKE '%term%' queries that don't scale.

**Why it happens:** Simple string matching seems sufficient initially.

**Consequences:**
- Search slows down as crew count grows
- Cannot search across multiple fields efficiently
- No fuzzy matching (typos fail to find results)
- Search doesn't rank results by relevance

**Prevention:**
- Use PostgreSQL full-text search (tsvector, tsquery)
- Create GIN indexes for text search
- Consider specialized search (Elasticsearch, Meilisearch) for large datasets
- Implement search ranking and relevance scoring
- Support filters + search combination efficiently

**Detection:**
- Search queries use ILIKE '%term%'
- No indexes on searched fields
- Search performance degrades with data growth

**Phase:** Phase 2+ for basic search, Phase 6+ for advanced.

---

### Pitfall 14: Rate/Cost Tracking Without History

**What goes wrong:** Crew rates and equipment rental costs stored as single current value, losing historical pricing.

**Why it happens:** Simple "crew.hourly_rate" field in profile.

**Consequences:**
- Cannot generate accurate historical job cost reports
- Changing crew rate retroactively affects old jobs
- Cannot track rate negotiations or changes over time
- Budget estimates don't match actual costs from booking date

**Prevention:**
- Store rates with effective_from dates in separate table
- Bookings capture rate at time of booking (snapshot)
- Support multiple rate types (standard, overtime, weekend)
- Track negotiated rates per job/client

**Detection:**
- Crew table has single `rate` column
- Old jobs show current rates, not booking-time rates
- No rate history or audit trail

**Phase:** Phase 2 (Resource Management) for data model.

---

### Pitfall 15: Email Thread Linking Without Deduplication

**What goes wrong:** Email threads attached to jobs without detecting duplicates or managing updates.

**Why it happens:** Simple "link email to job" feature without email processing logic.

**Consequences:**
- Same email thread linked multiple times
- Email replies create new threads instead of updating existing
- Cannot detect when email conversation continues
- Email metadata (subject, participants) becomes stale

**Prevention:**
- Use Message-ID header for deduplication
- Track email thread IDs (References, In-Reply-To headers)
- Update existing email thread records on new replies
- Show email as conversation tree, not flat list
- Consider webhooks from email provider for real-time updates

**Detection:**
- Email table has no message_id or thread_id columns
- Duplicate emails appear in job view
- Email threading doesn't work

**Phase:** Phase 3 (Email Integration). Can be rough initially but plan for improvement.

---

### Pitfall 16: No Crew Reliability Metrics Definition

**What goes wrong:** Requirements mention "reliability rating" but without clear definition or calculation method.

**Why it happens:** Vague requirement without implementation spec.

**Consequences:**
- Rating system implemented arbitrarily
- Admins don't know how to rate fairly
- Ratings become subjective and inconsistent
- Cannot use ratings for automated recommendations
- Legal/HR issues if ratings affect hiring without clear criteria

**Prevention:**
- Define specific metrics: on-time arrival, task completion, communication responsiveness
- Combine objective data (confirmed/showed up ratio) with subjective ratings
- Show rating breakdown (not just single score)
- Allow crew to view their ratings and improve
- Document rating criteria clearly

**Detection:**
- Rating is single number field with no definition
- No tracking of confirmations vs actual attendance
- Ratings entered manually without supporting data

**Phase:** Phase 2 (Crew Profiles) for basic rating, Phase 6+ for sophisticated metrics.

---

## Phase-Specific Warnings

| Phase Topic | Likely Pitfall | Mitigation |
|-------------|---------------|------------|
| Database schema design | Choosing shared-schema multi-tenancy | Research schema-per-tenant vs shared-schema tradeoffs early |
| Authentication | Rolling custom auth instead of proven libraries | Use FastAPI-Users or similar battle-tested library |
| Resource booking | Race conditions in conflict detection | Implement database-level locking from day one |
| File uploads | Storing files in application server filesystem | Plan object storage (S3, MinIO) from start |
| Calendar queries | N+1 queries for availability checks | Profile queries with realistic data volumes early |
| Message threading | Implementing custom threading logic | Study existing schemas (Slack export format, email threading) |
| Timezone handling | Adding timezone support after initial development | Make all datetime fields timezone-aware from start |
| Crew scheduling | Underestimating availability pattern complexity | Interview real production managers about edge cases |
| Job lifecycle | Oversimplifying state machine | Map all possible state transitions before schema freeze |
| API design | Exposing internal IDs in URLs | Use UUIDs or obfuscated IDs for multi-tenant isolation |

---

## Domain-Specific Anti-Patterns

### Anti-Pattern: "Admin Knows Best" Data Model

**What it is:** Designing only for admin workflows, treating crew as passive data subjects.

**Why it's bad:** Crew engagement requires crew agency. If crew can't update availability, confirm bookings, or communicate needs, they'll route around the system.

**Instead:** Design crew portal as first-class user experience, not afterthought.

---

### Anti-Pattern: Treating Equipment Like Crew

**What it is:** Using identical data model for crew and equipment scheduling.

**Why it's bad:** Equipment has physical location, maintenance needs, consumables, condition tracking—none applicable to crew. Crew have availability patterns, skills, preferences—none applicable to equipment.

**Instead:** Shared booking concept but separate resource models with resource-specific attributes.

---

### Anti-Pattern: Message Threads as Comment Logs

**What it is:** Implementing job messaging as simple comment list without threading, reactions, or notifications.

**Why it's bad:** Users expect Slack/Discord/Teams level functionality. Simple comment logs feel archaic and don't support real conversation flow.

**Instead:** Study how modern chat platforms handle threading, presence, read status, and structure messages accordingly.

---

### Anti-Pattern: Job Intake as Form Submission

**What it is:** Treating job intake as structured form that must be completed fully before job creation.

**Why it's bad:** Real jobs arrive as rough ideas, partial info, or urgent requests. Forcing complete forms creates friction and abandonment.

**Instead:** Allow rapid job creation with minimal info, progressive enrichment as details emerge. Match "ad-hoc intake" requirement.

---

### Anti-Pattern: Calendar as Read-Only View

**What it is:** Building calendar as reporting view without inline editing or drag-and-drop rescheduling.

**Why it's bad:** Production managers think spatially—they want to move bookings on calendar, not edit forms.

**Instead:** Interactive calendar with drag-drop, resize, quick-edit modals. Calendar is primary interface, not secondary view.

---

## Research Gaps & Validation Needs

### Needs Phase-Specific Research

1. **Real-time messaging patterns** — Specific WebSocket architecture for FastAPI + React. Should investigate libraries like `socketio`, `channels`, or managed services.

2. **Multi-tenant database strategy** — Need to benchmark schema-per-tenant vs shared-schema with RLS for expected tenant count and data volumes.

3. **Email integration approach** — IMAP parsing, OAuth flows, webhook providers (SendGrid, Postmark). Needs technical evaluation.

4. **Conflict detection algorithms** — PostgreSQL exclusion constraints vs application logic vs advisory locks. Performance testing required.

5. **File storage costs** — Object storage pricing models (S3, Backblaze B2, Cloudflare R2) for video/photo heavy usage patterns.

### Community Validation Needed

- Do production managers actually use reliability ratings, or are they vanity metrics?
- What's the acceptable latency for "real-time" messaging in this domain?
- How deep is equipment tracking really needed (vs simple available/booked)?
- Are crew notifications genuinely multi-channel, or is email sufficient initially?

---

## Confidence Assessment

**Overall confidence:** MEDIUM

**Reasoning:**
- **HIGH confidence** pitfalls: Multi-tenancy, timezone handling, file storage security, race conditions—these are general SaaS/scheduling system patterns with well-documented failures.
- **MEDIUM confidence** pitfalls: Crew availability complexity, equipment state management, job lifecycle—based on domain understanding but not verified with production managers.
- **LOW confidence** pitfalls: Specific crew reliability metrics, notification channel preferences—these need user research to validate importance.

**What would increase confidence:**
- Interviews with production managers about current pain points
- Examining existing crew management software (Show Division Crew, others) for patterns/anti-patterns
- Database performance benchmarks with realistic data volumes
- Access to real-world job/crew data to understand complexity

---

## Sources

**No external sources** — research based on:
- SaaS architecture patterns (multi-tenancy, authentication, file storage)
- Scheduling system design principles (conflict detection, timezone handling, calendar performance)
- Domain knowledge from project requirements (event production workflows)
- General database optimization and API design best practices

**Limitation:** Without web search access or Context7 for specific libraries (FastAPI, PostgreSQL patterns), recommendations are based on training data (knowledge cutoff January 2025). Some library-specific guidance may be outdated.

**Recommendation:** Validate specific technical choices (e.g., FastAPI WebSocket libraries, PostgreSQL RLS performance) during phase planning with current documentation.
