# Feature Landscape

**Domain:** Crew Management & Resource Scheduling SaaS for Event Production
**Researched:** 2026-05-15

## Table Stakes

Features users expect. Missing = product feels incomplete.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| **Crew scheduling/calendar** | Core use case — assign people to jobs with date/time | Medium | Month/week/day views, drag-drop, conflict detection |
| **Crew profiles** | Need to store skills, rates, contact info, availability | Low | Name, role, skills, rate, email, phone, notes field |
| **Job/event management** | Central organizing unit for all resources | Medium | CRUD + lifecycle states (pending/confirmed/complete) |
| **Availability tracking** | Must know who's free before assigning | Medium | Calendar-based, manual entry + auto-sync from bookings |
| **Conflict detection** | Prevent double-booking crew or equipment | Medium | Real-time validation when assigning resources |
| **Equipment inventory** | Track owned gear availability | Low-Medium | Item name, category, quantity, status (available/out/maintenance) |
| **Contact list/directory** | Quick access to crew phone/email | Low | Searchable, filterable by role/skill |
| **Basic notifications** | Alert crew about new assignments | Low | Email notifications minimum, SMS bonus |
| **Assignment confirmation** | Crew must be able to accept/decline bookings | Medium | Status workflow: pending → confirmed/declined |
| **Mobile-responsive UI** | Crew check schedules on phones constantly | Medium | Progressive web app approach, not native required |
| **Role-based access** | Admin vs crew permissions | Medium | Admin: full CRUD, Crew: view own schedule + confirm |
| **Search/filter** | Find crew by skill, availability, past jobs | Low-Medium | Text search + faceted filters |
| **Date range views** | See bookings across time spans | Low | Standard calendar library feature |
| **Export to calendar** | Crew sync to Google/Apple calendar | Low-Medium | iCal/CalDAV export or calendar API integration |

## Differentiators

Features that set product apart. Not expected, but valued.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| **Job lifecycle states** | Handle jobs that "simmer" before going active | Low-Medium | Intake → simmer → active → complete workflow |
| **Ad-hoc intake capture** | Turn email/text into job records quickly | Medium-High | Email forwarding, parse/extract, manual cleanup |
| **Threaded messaging per job** | Replace scattered text/email with organized comms | Medium | Slack-like interface, job-scoped, searchable history |
| **Task management** | Separate actionable items from discussion | Medium | Assignee, deadline, priority, status, links to job |
| **File sharing per job** | Centralize briefs, runsheets, contracts, photos | Low-Medium | Upload, organize by job, version history optional |
| **Email chain linking** | Attach existing email threads to jobs | Medium | Forward-to-archive or manual link with context |
| **Crew reliability ratings** | Track past performance for better resourcing | Low-Medium | Admin-only ratings, show in crew profile |
| **Equipment rental tracking** | Manage hired gear separately from owned | Medium | Rental source, dates, cost, return tracking |
| **Skills matrix** | Visual map of crew capabilities vs job needs | Medium | Tag-based, shows coverage gaps |
| **Gear conflict detection** | Prevent over-allocating equipment | Medium | Same logic as crew conflicts, inventory-aware |
| **Bulk assignment** | Assign multiple crew to job at once | Low | Multi-select + assign action |
| **Recurring jobs/templates** | Clone common job types quickly | Low-Medium | Save as template, copy with resources |
| **Availability patterns** | Crew set regular unavailable days | Low | "Not available Sundays" overrides |
| **Deep crew bench** | Handle 30+ freelancers efficiently | Medium | Optimized UI for large rosters, not pagination hell |
| **Job brief builder** | Structured brief creation (not just freeform doc) | Medium | Template fields: location, times, roles, contacts, notes |
| **Integrated timeline view** | See all jobs + crew + gear on single timeline | High | Gantt-like view, filterable by resource type |
| **Custom fields** | Tenant-specific data (certifications, T-shirt size, etc.) | Medium | Admin defines fields, shows in crew profiles |

## Anti-Features

Features to explicitly NOT build.

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| **Native mobile app** | Increases complexity 3x, web-responsive sufficient | Progressive web app with mobile-first design |
| **Built-in video calling** | Zoom/Teams already solve this, integration overhead high | Deep-link to external meeting tools |
| **Full accounting/invoicing** | Scope creep into finance, low differentiation | Export data, integrate with Xero/QuickBooks later |
| **Timesheets/payroll** | Regulatory complexity, not core value prop | Track hours worked, export for external payroll |
| **Public client portal** | V1 is internal crew tool, client-facing adds auth complexity | Admin shares read-only links if needed |
| **Advanced reporting/BI** | Overkill for early customers, slows core dev | Basic CSV exports, integrate with Metabase/Tableau later |
| **Real-time collaboration** | Operational sync (Google Docs-style) complex, low ROI | Async messaging + file sharing sufficient |
| **Equipment maintenance logs** | Niche feature, distracts from scheduling focus | Notes field in equipment record |
| **Automated crew matching** | ML-based "suggest best crew" premature optimization | Manual assignment with search/filter tools |
| **GPS tracking** | Feels invasive, not requested by industry | Trust-based confirmation system |
| **Social features** | Not a social network, creeps into collaboration platform | Keep messaging job-scoped and professional |

## Feature Dependencies

```
Crew Profiles → Crew Scheduling (need profiles to assign)
Job Management → Everything (jobs are the organizing unit)
Availability Tracking → Conflict Detection (conflicts based on availability)
File Sharing → Job Brief Builder (briefs are files attached to jobs)
Task Management → Threaded Messaging (tasks reference discussions)
Equipment Inventory → Gear Conflict Detection (need inventory to track)
Role-based Access → Assignment Confirmation (crew can only confirm own bookings)
Ad-hoc Intake → Job Lifecycle States (intake creates jobs in "intake" state)
```

## MVP Recommendation

Prioritize this sequence to achieve a complete loop:

### Phase 1: Core Data Model
1. **Job management** — CRUD + lifecycle states (intake/simmer/active/complete)
2. **Crew profiles** — Name, role, skills, rate, contact, availability
3. **Equipment inventory** — Owned gear tracking (name, category, quantity, status)

### Phase 2: Scheduling Engine
4. **Crew scheduling** — Assign crew to jobs with calendar view
5. **Conflict detection** — Prevent double-booking crew and gear
6. **Availability tracking** — Calendar-based crew availability
7. **Gear assignment** — Allocate equipment to jobs

### Phase 3: Coordination Layer
8. **Threaded messaging** — Job-scoped discussion threads
9. **Task management** — Assign tasks with deadlines and priorities
10. **File sharing** — Upload/organize files per job
11. **Assignment confirmation** — Crew accept/decline workflow

### Phase 4: Intake & Polish
12. **Ad-hoc intake capture** — Email/text → job conversion
13. **Job brief builder** — Structured brief templates
14. **Email chain linking** — Archive related email threads

Defer:
- **Equipment rental tracking** — Start with owned gear only, add hired gear once scheduling proven
- **Crew reliability ratings** — Need historical data first
- **Skills matrix visualization** — Nice-to-have once roster grows
- **Recurring job templates** — Optimize after manual workflows established
- **Advanced timeline view** — Calendar views sufficient for v1

## Rationale

**Why this ordering:**
- Phases 1-2 create the "single source of truth" for who/what is available — solves the core pain point
- Phase 3 adds coordination tools so daily usage sticks (messaging + tasks + files together)
- Phase 4 addresses intake friction (the other major pain point)
- Without messaging + tasks together, users will continue using external tools and the platform becomes just a calendar

**Table stakes vs differentiators:**
- **Table stakes** = features every crew scheduling tool has (calendar, profiles, conflicts)
- **Differentiators** = Duct Tape's unique value (job lifecycle, threaded messaging, task separation, ad-hoc intake)

**Anti-features reasoning:**
- Avoid rebuilding commodity tools (video calling, accounting, real-time collab)
- Avoid premature optimization (ML matching, advanced BI)
- Avoid scope creep into adjacent domains (timesheets, maintenance logs, social features)

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Table stakes | **MEDIUM** | Based on training data for crew scheduling tools (Show Division, StudioBinder, CrewCall patterns) — could not verify with current product websites |
| Differentiators | **MEDIUM** | Derived from PROJECT.md pain points + industry patterns — some features extrapolated from stated needs |
| Anti-features | **HIGH** | Based on project constraints (no mobile native, no accounting) + common SaaS over-scoping pitfalls |
| Dependencies | **HIGH** | Logical dependencies clear from feature relationships |
| MVP sequencing | **MEDIUM-HIGH** | Aligned with "full loop for v1" decision in PROJECT.md — messaging + tasks + files together critical |

## Gaps to Address

**Could not verify via external research:**
- Current feature sets of Show Division Crew, CrewCall, StudioBinder, Assemble, Current RMS (internet mode disabled)
- Industry-standard terminology for job states (intake/simmer/active vs other naming)
- Prevalence of rental tracking vs owned-only equipment in competitor products
- Mobile app expectations (PWA vs native) in event production industry

**Recommend validating:**
- Feature prioritization with actual production managers (user interviews)
- Whether "threaded messaging" is valued or if email/text remains preferred
- Rental gear tracking importance (might be table stakes, not differentiator)
- Custom fields requirement (could be table stakes for some tenants)

**Phase-specific research needs:**
- Phase 4 (Ad-hoc Intake): Email parsing libraries, forwarding workflows, security implications
- Phase 3 (Messaging): Real-time vs polling architecture, notification delivery guarantees
- Phase 2 (Scheduling): Calendar sync protocols (CalDAV/iCal), timezone handling patterns

## Sources

**Unable to access (internet mode disabled):**
- Show Division Crew official website/documentation
- CrewCall product pages
- StudioBinder crew management features
- Assemble.live platform details
- Current RMS equipment rental features

**Research conducted using:**
- Training data (up to January 2025) on crew scheduling and resource management SaaS patterns
- Project context from `/Users/operator/projects/duct-tape/.planning/PROJECT.md`
- Milestone context describing reference products and domain

**Confidence caveat:**
All feature categorizations based on training data patterns and logical inference from stated project requirements. External verification blocked by Meta internet restrictions. Recommend treating as hypothesis to validate with industry research when possible.
