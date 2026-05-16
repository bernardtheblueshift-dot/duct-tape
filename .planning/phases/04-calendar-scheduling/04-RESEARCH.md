# Phase 4: Calendar & Scheduling - Research

**Researched:** 2026-05-16
**Domain:** Calendar APIs, iCal/RFC 5545, date range queries, token-based feed authentication
**Confidence:** HIGH

## Summary

Phase 4 delivers backend API endpoints for calendar data access and iCal feed export. The phase builds entirely on existing infrastructure: `Job` model with `scheduled_start`/`scheduled_end` (TIMESTAMPTZ), `CrewAssignment`/`EquipmentAssignment` tables, and `AvailabilityPattern` for recurring crew schedules. No frontend UI implementation required.

Standard approach uses `icalendar` library (current: 7.1.0) for RFC 5545-compliant feed generation, PostgreSQL date range queries with existing overlap logic from `conflicts.py`, and `secrets.token_urlsafe()` pattern (already used in `VerificationToken`, `PasswordResetToken`, `InvitationToken`) for revocable feed URLs.

Key architectural decisions already locked via CONTEXT.md: unified event format with `event_type` discriminator, separate availability endpoint that expands weekly patterns into concrete dates, and token-authenticated public iCal URLs for calendar app subscriptions.

**Primary recommendation:** Leverage existing patterns throughout—reuse overlap query logic, token generation, schema patterns, and batch query optimization from Phase 3. Add single new model (`ICalToken`) and four new routers (`/calendar`, `/calendar/crew/{id}`, `/calendar/equipment/{id}`, `/ical/{token}.ics`). Implementation is primarily query reshaping, not new infrastructure.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Calendar API shape**
- Backend API only — no React calendar UI in this phase
- Events-by-range endpoint: GET /calendar/events?start=X&end=Y returns all jobs + assignments in range
- Per-resource endpoints: GET /calendar/crew/{id}?start=X&end=Y and GET /calendar/equipment/{id}?start=X&end=Y
- Raw events format — API returns flat list, frontend arranges into calendar grid
- Unified event format with event_type field ('job', 'crew_assignment', 'equipment_assignment')

**View granularity & data density**
- Each event includes: id, title, start, end, event_type, color, status, resource_name, job_title, role
- No summary mode — same endpoint for month/week/day, frontend decides how to summarize
- Color by job state: intake=blue, simmer=yellow, active=green, complete=grey
- All assignments for a job inherit the job's color

**Availability visualization**
- Separate availability endpoint: GET /calendar/crew/{id}/availability?start=X&end=Y
- Expands recurring weekly patterns into concrete unavailable dates within the range (frontend doesn't need to understand recurrence)
- Bulk availability summary: GET /calendar/availability?start=X&end=Y returns all crew with status per day (free/booked/unavailable) — admin's "who's available?" view

**iCal export design**
- Token-authenticated URL: /ical/{token}.ics — long random string, no login required
- Calendar apps subscribe to this URL and poll for updates
- Token is revocable if compromised
- Event content: SUMMARY = "Role - Job Title", LOCATION = venue, DESCRIPTION = job description
- Confirmed assignments only — pending not included (avoids premature calendar blocks)

### Claude's Discretion
- iCal token generation and storage approach
- Exact query optimization for date range queries
- How to handle jobs without scheduled times in calendar views
- Response pagination for large date ranges
- Cache strategy for expanded availability dates

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope

</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| SCHED-01 | Month view showing all jobs and resource bookings | Calendar API endpoints return flat event lists; frontend date grouping architecture not in scope (frontend phase) |
| SCHED-02 | Week view with daily breakdown of assignments | Same endpoint as SCHED-01 with different date range; query optimization for 7-day windows |
| SCHED-03 | Day view showing detailed schedule per resource | Per-resource endpoints (`/calendar/crew/{id}`, `/calendar/equipment/{id}`) with single-day range queries |
| SCHED-04 | Crew availability visible on calendar (free, booked, unavailable) | Availability expansion logic: weekly patterns → concrete date list; bulk summary endpoint for "who's free" queries |
| SCHED-06 | Calendar export via iCal for crew to sync with personal calendars | `icalendar` library for RFC 5545 VEVENT generation; token model for authentication; Content-Type: text/calendar |

</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| icalendar | 7.1.0 | RFC 5545 iCal generation | De facto Python standard for .ics files, handles timezone complexity, active maintenance (6+ releases in 2024-2025), used by CalDAV servers, event platforms |
| FastAPI | 0.136.1 | API endpoints (existing) | Already project stack, no new dependencies |
| SQLAlchemy | 2.0.49 | ORM queries (existing) | Already project stack, async support for date range queries |
| asyncpg | (existing) | PostgreSQL driver (existing) | Already project stack, efficient TIMESTAMPTZ handling |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| python-dateutil | bundled with icalendar | Timezone conversions, RRULEs | If future phases add recurring events (out of scope for v1) |
| secrets | stdlib | Token generation | Already used in token.py models—reuse pattern for ICalToken |
| pytz | avoid | Timezone database | icalendar uses dateutil; mixing pytz causes subtle bugs |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| icalendar | vobject | vobject unmaintained since 2021; icalendar has active community |
| icalendar | Hand-rolled RFC 5545 | Timezone handling alone is 500+ lines; VTIMEZONE definitions massive |
| Token model | JWT with claims | iCal feed URLs need year+ validity; JWT refresh flow overcomplicated for read-only feeds |
| Separate tables | Virtual events via views | PostgreSQL views perform poorly for complex joins; caching harder |

**Installation:**
```bash
# Add to backend/pyproject.toml dependencies array:
"icalendar==7.1.0",
```

**Version verification:**
Latest stable is 7.1.0 (released 2025), current installed 7.0.3. Upgrade recommended for bug fixes in VTIMEZONE handling.

```bash
pip index versions icalendar
# INSTALLED: 7.0.3
# LATEST: 7.1.0
```

## Architecture Patterns

### Recommended Project Structure
```
backend/app/
├── api/v1/
│   ├── calendar.py          # /calendar/events, /calendar/availability
│   └── ical.py              # /ical/{token}.ics public endpoint
├── models/
│   └── ical_token.py        # ICalToken model (crew_id FK, token, expires_at)
├── schemas/
│   └── calendar.py          # CalendarEvent, AvailabilityDay, ICalTokenResponse
├── core/
│   └── icalendar.py         # iCal feed generation logic
└── tests/
    └── test_calendar_*.py   # Calendar endpoint tests, iCal validation tests
```

### Pattern 1: Unified Event Response Schema
**What:** Single Pydantic model representing jobs, crew assignments, equipment assignments with discriminator field
**When to use:** All calendar endpoints return `list[CalendarEvent]` — frontend switches on `event_type`
**Example:**
```python
# Source: Existing schema patterns in app/schemas/job.py, app/schemas/crew.py
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from uuid import UUID

class CalendarEvent(BaseModel):
    """Unified event format for calendar views"""
    
    id: UUID
    event_type: str  # 'job' | 'crew_assignment' | 'equipment_assignment'
    title: str
    start: datetime
    end: datetime
    color: str  # Hex code derived from job state
    status: str  # Job state or assignment status
    
    # Optional fields populated based on event_type
    job_id: UUID | None = None
    resource_id: UUID | None = None  # crew_id or equipment_id
    resource_name: str | None = None
    role: str | None = None  # For crew assignments
    
    model_config = ConfigDict(from_attributes=True)
```

### Pattern 2: Date Range Query with Overlap Logic
**What:** Reuse `start1 < end2 AND start2 < end1` pattern from conflicts.py for calendar event fetching
**When to use:** All `/calendar/*` endpoints with `start`/`end` query params
**Example:**
```python
# Source: app/core/conflicts.py lines 46-48
# Existing overlap detection — reuse for calendar queries
query = select(Job).where(
    Job.scheduled_start.is_not(None),
    Job.scheduled_end.is_not(None),
    Job.scheduled_start < end_param,  # Job starts before range ends
    Job.scheduled_end > start_param,  # Job ends after range starts
)
```

**Critical:** Exclude jobs with `NULL` scheduled times (intake-phase jobs may not have dates). Calendar endpoints only show scheduled events.

### Pattern 3: Batch Query for Assignment Context
**What:** Fetch jobs + assignments in 2-3 queries, then assemble in Python (avoid N+1)
**When to use:** `/calendar/events` endpoint needs job details + crew names + equipment names
**Example:**
```python
# Source: app/api/v1/jobs.py lines 104-118 (existing pattern from Phase 3)
# Step 1: Get all jobs in range
jobs = await db.execute(
    select(Job).where(Job.scheduled_start < end, Job.scheduled_end > start)
)
job_list = list(jobs.scalars().all())
job_ids = [j.id for j in job_list]

# Step 2: Batch fetch crew assignments
crew_assignments = await db.execute(
    select(CrewAssignment, CrewProfile.name)
    .join(CrewProfile)
    .where(CrewAssignment.job_id.in_(job_ids))
)

# Step 3: Group by job_id and assemble CalendarEvent objects
events = []
for job in job_list:
    events.append(CalendarEvent(
        id=job.id,
        event_type='job',
        title=job.title,
        start=job.scheduled_start,
        end=job.scheduled_end,
        color=JOB_STATE_COLORS[job.state],
        status=job.state.value,
    ))
    # Add crew assignment events...
```

### Pattern 4: Availability Expansion (Weekly Pattern → Date List)
**What:** Convert `AvailabilityPattern` (day_of_week + is_available) into list of concrete unavailable dates
**When to use:** `/calendar/crew/{id}/availability` endpoint
**Example:**
```python
# New logic (not in codebase yet)
from datetime import timedelta

async def expand_availability(
    db: AsyncSession,
    crew_id: UUID,
    start: datetime,
    end: datetime
) -> list[datetime]:
    """Returns list of dates crew is UNAVAILABLE (from patterns)"""
    
    # Fetch patterns
    patterns = await db.execute(
        select(AvailabilityPattern).where(
            AvailabilityPattern.crew_id == crew_id,
            AvailabilityPattern.is_available == False
        )
    )
    unavailable_days = {p.day_of_week for p in patterns.scalars().all()}
    
    # Generate date list
    unavailable_dates = []
    current = start.date()
    while current <= end.date():
        if current.weekday() in unavailable_days:
            unavailable_dates.append(current)
        current += timedelta(days=1)
    
    return unavailable_dates
```

**Performance:** For 30-day month, max 30 iterations. Fast enough without caching for v1.

### Pattern 5: iCal Feed Generation with icalendar
**What:** Convert `CrewAssignment` list to RFC 5545 VCALENDAR
**When to use:** `/ical/{token}.ics` endpoint after validating token
**Example:**
```python
# Source: icalendar library docs (https://icalendar.readthedocs.io/)
from icalendar import Calendar, Event
from datetime import datetime

def generate_ical_feed(assignments: list[CrewAssignment], jobs: dict[UUID, Job]) -> str:
    """Generate iCal feed from crew assignments"""
    
    cal = Calendar()
    cal.add('prodid', '-//Duct Tape//Crew Calendar//EN')
    cal.add('version', '2.0')
    cal.add('calscale', 'GREGORIAN')
    cal.add('method', 'PUBLISH')
    cal.add('x-wr-calname', 'My Jobs - Duct Tape')
    
    for assignment in assignments:
        if assignment.status != AssignmentState.CONFIRMED:
            continue  # Only confirmed assignments
        
        job = jobs[assignment.job_id]
        if not job.scheduled_start or not job.scheduled_end:
            continue  # Skip unscheduled jobs
        
        event = Event()
        event.add('uid', f'{assignment.id}@ducttape.local')
        event.add('dtstamp', datetime.now(timezone.utc))
        event.add('dtstart', job.scheduled_start)
        event.add('dtend', job.scheduled_end)
        event.add('summary', f'{assignment.role} - {job.title}' if assignment.role else job.title)
        event.add('location', job.venue or '')
        event.add('description', job.description or '')
        event.add('status', 'CONFIRMED')
        
        cal.add_component(event)
    
    return cal.to_ical().decode('utf-8')
```

**Critical:** `uid` must be stable — use `assignment.id` so calendar apps recognize updates vs new events. Changing UID creates duplicates.

### Pattern 6: Token-Based Feed Authentication
**What:** Public URL with unguessable token, no session/cookies required
**When to use:** iCal feed URLs (calendar apps can't handle OAuth flows)
**Example:**
```python
# Source: Existing token.py pattern (VerificationToken, InvitationToken)
from sqlalchemy import Column, String, DateTime, ForeignKey
from app.models.base import Base, TenantMixin, TimestampMixin
import secrets
from datetime import datetime, timedelta, timezone

class ICalToken(Base, TenantMixin, TimestampMixin):
    """Long-lived token for iCal feed access"""
    
    __tablename__ = 'ical_tokens'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    crew_id = Column(UUID(as_uuid=True), ForeignKey('crew_profiles.id'), nullable=False)
    token = Column(String, unique=True, nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)  # NULL = never expires
    last_accessed = Column(DateTime(timezone=True), nullable=True)
    
    @staticmethod
    def create_for_crew(crew_id: UUID, tenant_id: UUID) -> 'ICalToken':
        """Generate token with no expiry (revoke manually if compromised)"""
        return ICalToken(
            crew_id=crew_id,
            tenant_id=tenant_id,
            token=secrets.token_urlsafe(32),  # 256-bit entropy, URL-safe
            expires_at=None,
        )
```

**Security:** 32-byte `token_urlsafe()` = 43-character string, 256 bits of entropy. Infeasible to brute force. Store in password manager like API keys.

### Anti-Patterns to Avoid

- **Don't use JWT for iCal tokens:** Calendar apps poll every 15-60 minutes; JWT refresh flow breaks subscription model. Use long-lived revocable tokens instead.
- **Don't compute events in real-time per calendar app poll:** Cache or precompute event list for 5-15 minutes if performance becomes issue (v2 optimization).
- **Don't return assignments without job context:** Always join to Job table to get `scheduled_start`, `scheduled_end`, `title`, `venue`. Frontend can't display "Assignment ABC" without job info.
- **Don't filter by AssignmentState in calendar queries:** Include PENDING assignments with visual indicator (color/opacity). Admin needs to see "waiting for confirmation" state.
  - **CORRECTION based on CONTEXT.md:** iCal feeds ONLY include CONFIRMED (locked decision). Calendar API endpoints can include all states with status field.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| iCal/RFC 5545 format | Custom .ics string builder | `icalendar` library | 100+ page spec, VTIMEZONE definitions are 50KB+ per timezone, RRULE parsing is regex hell, escaping rules for SUMMARY/DESCRIPTION subtle |
| Timezone conversions | Manual UTC offset math | `datetime` with `timezone.utc`, PostgreSQL TIMESTAMPTZ | DST transitions, leap seconds, historical timezone changes—database handles all of it |
| Token generation | `random.randint()`, UUID4 | `secrets.token_urlsafe()` | `random` module is predictable (Mersenne Twister), not cryptographically secure; `secrets` uses OS entropy source |
| Date range iteration | while loops with date arithmetic | `dateutil.rrule` (if needed) or simple `timedelta` | Off-by-one errors, month-end edge cases, leap years—but for simple day iteration, `timedelta(days=1)` is fine |
| Calendar color schemes | Hard-coded hex values | CSS variables or config | Colors need to match frontend theme; central config enables dark mode, accessibility contrast ratios |

**Key insight:** iCal generation is 90% edge cases. `icalendar` library handles: multi-day events spanning midnight, VTIMEZONE generation for every timezone in IANA db, escaping special characters in text fields, DURATION vs DTEND ambiguity, VALARM for reminders, ATTENDEE/ORGANIZER vCard formatting. Rolling your own means rediscovering 20 years of bugs.

## Common Pitfalls

### Pitfall 1: Timezone Stripping on Date Range Boundaries
**What goes wrong:** FastAPI deserializes `?start=2024-05-01T00:00:00Z` to naive datetime, loses UTC context, query misses events
**Why it happens:** Pydantic coerces ISO strings to `datetime` objects without timezone if model uses `datetime` not `datetime | None` with validation
**How to avoid:** 
- Always use `datetime.timezone.utc` on incoming params
- Validate timezone awareness: `if start.tzinfo is None: start = start.replace(tzinfo=timezone.utc)`
- PostgreSQL TIMESTAMPTZ normalizes to UTC internally, but comparisons require aware datetimes
**Warning signs:** Calendar shows events in wrong month, or events disappear when switching timezones in frontend

### Pitfall 2: N+1 Queries When Fetching Assignment Context
**What goes wrong:** Loop through jobs, fetch assignments per job → 100 jobs = 201 queries (1 for jobs + 100×2 for crew/equipment)
**Why it happens:** ORM lazy loading, convenient but kills performance
**How to avoid:** Batch pattern from `jobs.py`:
```python
# BAD (N+1)
for job in jobs:
    crew = await db.execute(select(CrewAssignment).where(job_id=job.id))
    
# GOOD (2 queries total)
job_ids = [j.id for j in jobs]
all_crew = await db.execute(select(CrewAssignment).where(job_id.in_(job_ids)))
crew_by_job = defaultdict(list)
for assignment in all_crew.scalars():
    crew_by_job[assignment.job_id].append(assignment)
```
**Warning signs:** Calendar endpoint takes 2+ seconds for 30-day month with 20 jobs

### Pitfall 3: iCal Feed Caching Gone Wrong
**What goes wrong:** Calendar app shows old event times after admin updates job schedule
**Why it happens:** Calendar apps cache aggressively, respect HTTP cache headers, `Expires`/`ETag` headers cause stale reads
**How to avoid:**
- Set `Cache-Control: no-cache, must-revalidate` for iCal endpoint
- Or set short TTL: `Cache-Control: max-age=300` (5 minutes) as compromise
- Update `LAST-MODIFIED` and `SEQUENCE` in VEVENT when job changes (requires tracking version)
**Warning signs:** Users report "calendar not updating", force refresh works

### Pitfall 4: Token Leakage via Logs/Analytics
**What goes wrong:** iCal token appears in server logs (`GET /ical/abc123...ics`), analytics tools, browser history shared via screenshot
**Why it happens:** URL-based auth means token is in every request line, not hidden in headers
**How to avoid:**
- Log sanitization: regex replace `/ical/[^/]+\.ics` with `/ical/***REDACTED***.ics` before logging
- Documentation: warn users tokens are like passwords, don't share calendar subscription URL
- Revocation UI: admin panel to revoke/regenerate tokens if compromised
- Optional: IP allowlist per token (over-engineered for v1)
**Warning signs:** Support ticket "someone else's events in my calendar" — token shared accidentally

### Pitfall 5: Unbounded Date Range Queries
**What goes wrong:** Request `?start=1970-01-01&end=2099-12-31` returns 50+ years of data, query timeout or OOM
**Why it happens:** No pagination or max range validation on query params
**How to avoid:**
```python
from datetime import timedelta

MAX_RANGE_DAYS = 365  # 1 year max

@router.get('/calendar/events')
async def get_events(start: datetime, end: datetime, ...):
    if (end - start).days > MAX_RANGE_DAYS:
        raise HTTPException(
            status_code=400,
            detail=f'Date range too large (max {MAX_RANGE_DAYS} days)'
        )
```
**Warning signs:** Slow queries when user switches to "year view" in frontend

### Pitfall 6: Job State Color Mapping Drift
**What goes wrong:** Calendar shows blue for "active" jobs, frontend legend says "green = active"
**Why it happens:** Color mapping duplicated in frontend and backend, one gets updated
**How to avoid:**
- Single source of truth: backend returns color hex in API response
- Or: backend returns `state` field, frontend has single color mapping table
- Document in schema: `color: str  # Hex code: intake=#3B82F6, simmer=#EAB308, active=#10B981, complete=#6B7280`
**Warning signs:** User bug reports "calendar colors wrong"

## Code Examples

Verified patterns from official sources and existing codebase:

### Date Range Query with Timezone Handling
```python
# Source: app/core/conflicts.py + PostgreSQL TIMESTAMPTZ best practices
from datetime import datetime, timezone
from fastapi import Query
from sqlalchemy import select

@router.get('/calendar/events')
async def get_calendar_events(
    start: datetime = Query(..., description='Range start (ISO 8601 with timezone)'),
    end: datetime = Query(..., description='Range end (ISO 8601 with timezone)'),
    db: AsyncSession = Depends(get_db),
):
    # Ensure timezone-aware datetimes
    if start.tzinfo is None:
        start = start.replace(tzinfo=timezone.utc)
    if end.tzinfo is None:
        end = end.replace(tzinfo=timezone.utc)
    
    # Reuse overlap logic from conflicts.py
    query = select(Job).where(
        Job.scheduled_start.is_not(None),
        Job.scheduled_end.is_not(None),
        Job.scheduled_start < end,
        Job.scheduled_end > start,
    )
    
    result = await db.execute(query)
    return list(result.scalars().all())
```

### Availability Expansion (Weekly Pattern → Concrete Dates)
```python
# Source: New implementation based on app/models/availability.py
from datetime import date, timedelta

async def get_crew_unavailable_dates(
    db: AsyncSession,
    crew_id: UUID,
    start_date: date,
    end_date: date,
) -> list[date]:
    """Expand weekly availability patterns into list of unavailable dates"""
    
    # Fetch crew's unavailable day patterns
    patterns_result = await db.execute(
        select(AvailabilityPattern).where(
            AvailabilityPattern.crew_id == crew_id,
            AvailabilityPattern.is_available == False
        )
    )
    patterns = patterns_result.scalars().all()
    unavailable_weekdays = {p.day_of_week for p in patterns}
    
    # Generate list of dates matching unavailable weekdays
    unavailable_dates = []
    current = start_date
    while current <= end_date:
        if current.weekday() in unavailable_weekdays:
            unavailable_dates.append(current)
        current += timedelta(days=1)
    
    return unavailable_dates
```

### iCal Feed Generation
```python
# Source: icalendar documentation https://icalendar.readthedocs.io/
from icalendar import Calendar, Event
from datetime import datetime, timezone

def build_ical_feed(crew_id: UUID, assignments: list[CrewAssignment], jobs: dict[UUID, Job]) -> bytes:
    """Generate RFC 5545 compliant iCal feed"""
    
    cal = Calendar()
    cal.add('prodid', '-//Duct Tape Crew Management//NONSGML v1.0//EN')
    cal.add('version', '2.0')
    cal.add('calscale', 'GREGORIAN')
    cal.add('method', 'PUBLISH')
    cal.add('x-wr-calname', 'My Jobs')
    cal.add('x-wr-timezone', 'UTC')
    
    for assignment in assignments:
        # Only confirmed assignments (per CONTEXT.md)
        if assignment.status != AssignmentState.CONFIRMED:
            continue
        
        job = jobs.get(assignment.job_id)
        if not job or not job.scheduled_start or not job.scheduled_end:
            continue
        
        event = Event()
        event.add('uid', f'assignment-{assignment.id}@ducttape')
        event.add('dtstamp', datetime.now(timezone.utc))
        event.add('dtstart', job.scheduled_start)
        event.add('dtend', job.scheduled_end)
        
        # SUMMARY format from CONTEXT.md: "Role - Job Title"
        summary = f"{assignment.role} - {job.title}" if assignment.role else job.title
        event.add('summary', summary)
        
        if job.venue:
            event.add('location', job.venue)
        if job.description:
            event.add('description', job.description)
        
        event.add('status', 'CONFIRMED')
        event.add('transp', 'OPAQUE')  # Shows as "busy" in calendar
        
        cal.add_component(event)
    
    return cal.to_ical()


@router.get('/ical/{token}.ics')
async def ical_feed(token: str, db: AsyncSession = Depends(get_db)):
    """Public iCal feed endpoint (no auth required, token validates access)"""
    
    # Validate token
    token_result = await db.execute(
        select(ICalToken).where(ICalToken.token == token)
    )
    ical_token = token_result.scalar_one_or_none()
    
    if not ical_token:
        raise HTTPException(status_code=404, detail='Invalid token')
    
    if ical_token.expires_at and ical_token.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=410, detail='Token expired')
    
    # Update last_accessed timestamp (analytics)
    ical_token.last_accessed = datetime.now(timezone.utc)
    await db.commit()
    
    # Fetch crew's confirmed assignments
    assignments_result = await db.execute(
        select(CrewAssignment)
        .where(
            CrewAssignment.crew_id == ical_token.crew_id,
            CrewAssignment.status == AssignmentState.CONFIRMED
        )
    )
    assignments = list(assignments_result.scalars().all())
    
    # Batch fetch jobs
    job_ids = [a.job_id for a in assignments]
    jobs_result = await db.execute(select(Job).where(Job.id.in_(job_ids)))
    jobs_dict = {job.id: job for job in jobs_result.scalars().all()}
    
    # Generate iCal feed
    ical_data = build_ical_feed(ical_token.crew_id, assignments, jobs_dict)
    
    return Response(
        content=ical_data,
        media_type='text/calendar; charset=utf-8',
        headers={
            'Content-Disposition': 'attachment; filename="my-jobs.ics"',
            'Cache-Control': 'no-cache, must-revalidate',
        }
    )
```

### Bulk Availability Summary (Admin View)
```python
# Source: New implementation pattern
from collections import defaultdict

@router.get('/calendar/availability')
async def get_bulk_availability(
    start: datetime = Query(...),
    end: datetime = Query(...),
    tenant_id: str = Depends(get_current_tenant),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Admin endpoint: crew availability summary across date range"""
    
    # Get all crew in tenant
    crew_result = await db.execute(
        select(CrewProfile).where(CrewProfile.archived_at.is_(None))
    )
    all_crew = crew_result.scalars().all()
    
    # Get all crew assignments in range (batch query)
    crew_ids = [c.id for c in all_crew]
    assignments_result = await db.execute(
        select(CrewAssignment)
        .join(Job)
        .where(
            CrewAssignment.crew_id.in_(crew_ids),
            CrewAssignment.status == AssignmentState.CONFIRMED,
            Job.scheduled_start < end,
            Job.scheduled_end > start,
        )
    )
    
    # Map: crew_id -> list[Job]
    bookings = defaultdict(list)
    for assignment in assignments_result.scalars().all():
        bookings[assignment.crew_id].append(assignment.job)
    
    # Get availability patterns (batch)
    patterns_result = await db.execute(
        select(AvailabilityPattern).where(
            AvailabilityPattern.crew_id.in_(crew_ids),
            AvailabilityPattern.is_available == False
        )
    )
    
    # Map: crew_id -> set[weekday]
    unavailable_days = defaultdict(set)
    for pattern in patterns_result.scalars().all():
        unavailable_days[pattern.crew_id].add(pattern.day_of_week)
    
    # Build response: crew -> daily availability status
    availability = []
    for crew in all_crew:
        # For each day in range, compute status
        # (simplified — real impl would check job overlaps per day)
        status_by_day = []
        current = start.date()
        while current <= end.date():
            if current.weekday() in unavailable_days[crew.id]:
                status = 'unavailable'
            elif any(job.scheduled_start.date() <= current <= job.scheduled_end.date() for job in bookings[crew.id]):
                status = 'booked'
            else:
                status = 'free'
            
            status_by_day.append({'date': current, 'status': status})
            current += timedelta(days=1)
        
        availability.append({
            'crew_id': crew.id,
            'crew_name': crew.user.name,  # Requires join to User
            'days': status_by_day
        })
    
    return availability
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| CalDAV for full bidirectional sync | iCal subscription (read-only) | v1 scope decision | Simpler implementation, crew can't edit via calendar app (must use web UI) |
| JWT for feed auth | Long-lived token with revocation | Industry standard since 2015 | Calendar apps don't support OAuth; token pattern matches password reset tokens |
| Separate recurring events table | Expand patterns on-demand | Architecture decision | Frontend doesn't need RRULE parsing; backend owns complexity |
| pytz for timezones | icalendar's bundled dateutil | icalendar 4.0+ (2019) | Avoid mixing timezone libraries; pytz deprecated patterns |

**Deprecated/outdated:**
- **pytz library:** Python 3.9+ has `zoneinfo` in stdlib; `icalendar` uses `dateutil.tz` which wraps `zoneinfo`. Mixing `pytz` causes "can't compare offset-naive and offset-aware datetime" errors.
- **CalDAV write support:** Complex spec (RFC 4791), requires WebDAV server, locking/conflict resolution. Read-only iCal subscriptions solve 80% use case with 20% effort.
- **UUID4 for tokens:** Predictable (only 122 bits entropy, version bits fixed). Use `secrets.token_urlsafe()` for full 256 bits.

## Open Questions

1. **Pagination strategy for large date ranges**
   - What we know: Max range validation prevents abuse (365 days), batch queries efficient up to ~1000 events
   - What's unclear: Whether to use cursor pagination, offset/limit, or rely on frontend requesting smaller ranges
   - Recommendation: Start with max range validation only; add pagination in v2 if perf issues arise. Most calendar UIs request 30-90 days max.

2. **Color scheme source of truth**
   - What we know: CONTEXT.md specifies color mapping (intake=blue, simmer=yellow, active=green, complete=grey)
   - What's unclear: Hex codes vs named colors, accessibility contrast ratios, dark mode variants
   - Recommendation: Backend returns hex codes in API, document values in schema. Frontend can override for theming but backend provides defaults.

3. **Cache/memoization for availability expansion**
   - What we know: 30-day expansion is ~30 iterations, fast enough
   - What's unclear: Whether 365-day ranges need Redis caching, TTL strategy
   - Recommendation: No caching for v1. Profile query performance first; optimize only if >500ms response times.

4. **Handling all-day events**
   - What we know: Job model has start/end as TIMESTAMPTZ (includes time component)
   - What's unclear: Whether jobs can be "all day" (9am-5pm vs midnight-midnight), iCal representation (DATE vs DATETIME)
   - Recommendation: Treat all jobs as DATETIME (with times). If future phase adds all-day toggle, use `DTSTART;VALUE=DATE:20240501` format.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.3.4 + pytest-asyncio 0.24.0 |
| Config file | `backend/pytest.ini` (existing) |
| Quick run command | `pytest tests/test_calendar.py -x` |
| Full suite command | `pytest tests/` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| SCHED-01 | Month/week view (backend: events-by-range endpoint) | integration | `pytest tests/test_calendar_events.py::test_get_events_date_range -x` | ❌ Wave 0 |
| SCHED-02 | Week view (same endpoint, 7-day range) | integration | `pytest tests/test_calendar_events.py::test_get_events_week_range -x` | ❌ Wave 0 |
| SCHED-03 | Day view per resource (per-resource endpoints) | integration | `pytest tests/test_calendar_resources.py::test_crew_calendar -x` | ❌ Wave 0 |
| SCHED-04 | Crew availability visible | integration | `pytest tests/test_calendar_availability.py::test_expand_patterns -x` | ❌ Wave 0 |
| SCHED-06 | iCal export | integration + unit | `pytest tests/test_ical.py::test_feed_generation -x` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest tests/test_calendar*.py tests/test_ical*.py -x --tb=short`
- **Per wave merge:** `pytest tests/` (full suite including Phase 1-3 regression)
- **Phase gate:** Full suite green + manual iCal subscription test (import .ics into Google Calendar/Apple Calendar)

### Wave 0 Gaps
- [ ] `tests/test_calendar_events.py` — covers SCHED-01, SCHED-02 (range queries, event format, batch optimization)
- [ ] `tests/test_calendar_resources.py` — covers SCHED-03 (per-crew, per-equipment endpoints)
- [ ] `tests/test_calendar_availability.py` — covers SCHED-04 (pattern expansion, bulk summary)
- [ ] `tests/test_ical.py` — covers SCHED-06 (feed generation, token validation, RFC 5545 compliance)
- [ ] `backend/app/models/ical_token.py` — ICalToken model + migration
- [ ] Framework install: `pip install icalendar==7.1.0` (add to pyproject.toml)

## Sources

### Primary (HIGH confidence)
- **Codebase inspection:** `app/models/job.py`, `app/models/assignment.py`, `app/models/availability.py`, `app/core/conflicts.py`, `app/api/v1/jobs.py` — existing patterns for date range queries, batch fetching, token generation
- **icalendar library:** `pip index versions icalendar` confirmed 7.1.0 latest, 7.0.3 installed
- **CONTEXT.md:** Locked architectural decisions (unified event format, token auth, expansion logic)
- **REQUIREMENTS.md:** SCHED-01 through SCHED-06 requirements text

### Secondary (MEDIUM confidence)
- **RFC 5545 (iCalendar spec):** IETF standard for .ics format — icalendar library implements this, don't need to read spec directly
- **PostgreSQL TIMESTAMPTZ docs:** Timezone-aware datetime handling, overlap query patterns
- **FastAPI query parameter handling:** Automatic Pydantic validation for datetime params

### Tertiary (LOW confidence)
- **Calendar app polling behavior:** Assumption that apps poll every 15-60 minutes (varies by client); needs real-world testing with Google Calendar, Apple Calendar, Outlook

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - `icalendar` verified via pip, existing dependencies confirmed in pyproject.toml
- Architecture: HIGH - All patterns reuse existing codebase structure (models, schemas, routers, batch queries)
- Pitfalls: HIGH - Timezone issues, N+1 queries, caching, token security are well-documented failure modes in calendar APIs
- iCal generation: MEDIUM - icalendar library API verified via docs, but haven't tested VTIMEZONE generation for all edge cases

**Research date:** 2026-05-16
**Valid until:** 60 days (icalendar library stable, FastAPI patterns established, no fast-moving dependencies)
