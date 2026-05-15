# Phase 2: Job Management - Research

**Researched:** 2026-05-16
**Domain:** FastAPI CRUD operations, state machine patterns, PostgreSQL search/filtering
**Confidence:** MEDIUM-HIGH

## Summary

Phase 2 implements job lifecycle management with CRUD operations, state transitions, and search/filtering capabilities. This research identifies standard patterns for FastAPI async CRUD, state machine implementation approaches, and PostgreSQL full-text search vs simple filtering tradeoffs.

**Primary recommendation:** Build job CRUD using established Phase 1 patterns (async SQLAlchemy + Pydantic schemas + RLS). Implement state transitions as an ENUM column with validation logic rather than a full state machine library. Use PostgreSQL `ts_vector` for search only if search performance becomes a bottleneck - start with simple ILIKE queries for rapid development.

**Key insight:** The job state machine (intake → simmer → active → complete) is simple enough (4 states, linear progression with occasional backwards transitions) that a state machine library would add complexity without benefit. Python Enums + validation functions provide sufficient control with better debuggability.

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| JOBS-01 | Admin can create jobs with title, date/time, venue, description | Standard FastAPI POST endpoint + Pydantic validation + async SQLAlchemy insert |
| JOBS-02 | Admin can edit and delete jobs | Standard PUT/PATCH and DELETE endpoints with RLS ensuring tenant isolation |
| JOBS-03 | Admin can search and filter jobs by date, status, venue | SQLAlchemy `.where()` filters + optional PostgreSQL full-text search for text fields |
| JOBS-04 | Jobs follow lifecycle states: intake → simmer → active → complete | Python Enum + state transition validation function |
| JOBS-05 | Admin can transition jobs between lifecycle states | POST /jobs/{id}/transition endpoint with state validation |
| JOBS-06 | Job detail view shows all assigned crew, gear, messages, tasks, files | JSON response with placeholder sections (empty lists/nulls) for future phase relationships |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| FastAPI | 0.136.1 | API framework | Already in Phase 1, async-native, OpenAPI auto-docs |
| SQLAlchemy | 2.0.49 | ORM + query builder | Already in Phase 1, 2.0 async patterns mature |
| Pydantic | 2.13.4 | Request/response validation | Already in Phase 1, integrates with FastAPI |
| asyncpg | latest | PostgreSQL async driver | Already in Phase 1, high performance |
| Alembic | 1.18.4 | Database migrations | Already in Phase 1, standard for SQLAlchemy |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| python-dateutil | 2.9+ | Date parsing/manipulation | If advanced date filtering needed (e.g., "next 30 days") |
| transitions | 0.9+ | State machine framework | Only if state logic grows beyond 4 states (NOT recommended for Phase 2) |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Enum + validation | transitions library | Enum is simpler for 4-state linear flow; transitions adds complexity for minimal benefit |
| ILIKE filtering | PostgreSQL ts_vector | ts_vector faster for large datasets (10K+ rows) but adds migration complexity; premature optimization |
| Manual pagination | fastapi-pagination | Manual control simpler for now; library useful if pagination becomes repetitive across many endpoints |

**Installation:**
```bash
# No new dependencies required for Phase 2
# All core libraries already installed in Phase 1
```

**Version verification:**
Phase 1 already locked these versions in `backend/pyproject.toml`. No changes needed.

## Architecture Patterns

### Recommended Project Structure
```
backend/app/
├── models/
│   └── job.py              # Job model with JobState enum
├── schemas/
│   └── job.py              # JobCreate, JobUpdate, JobResponse, JobFilter schemas
├── api/v1/
│   └── jobs.py             # CRUD + state transition endpoints
├── core/
│   └── state_machine.py    # State transition validation logic (if needed)
└── tests/
    └── test_jobs.py        # Job CRUD + state transition tests
```

### Pattern 1: Async CRUD with RLS
**What:** FastAPI endpoints using async SQLAlchemy queries with automatic tenant filtering via RLS

**When to use:** All tenant-scoped resources (jobs, crew, equipment, etc.)

**Example:**
```python
# backend/app/api/v1/jobs.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.dependencies import get_current_tenant
from app.core.permissions import require_admin
from app.models.job import Job
from app.schemas.job import JobCreate, JobResponse
from app.models.user import User

router = APIRouter(prefix="/api/v1/jobs", tags=["jobs"])

@router.post("/", response_model=JobResponse)
async def create_job(
    job_data: JobCreate,
    current_user: User = Depends(require_admin),
    tenant_id: str = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """Create new job (admin only)"""
    job = Job(
        **job_data.model_dump(),
        tenant_id=tenant_id,
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)
    return job

@router.get("/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: str,
    tenant_id: str = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """Get job by ID (RLS auto-filters by tenant)"""
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job
```

**Why this pattern:** Matches Phase 1 auth endpoints pattern. RLS handles tenant isolation automatically - no manual tenant_id filtering needed in queries.

### Pattern 2: State Transition Validation
**What:** Enum-based state management with explicit transition validation function

**When to use:** Simple state machines (< 10 states, mostly linear flow)

**Example:**
```python
# backend/app/models/job.py
from sqlalchemy import Column, String, Enum, DateTime
from sqlalchemy.dialects.postgresql import UUID
import enum
import uuid
from app.models.base import Base, TenantMixin, TimestampMixin

class JobState(str, enum.Enum):
    INTAKE = "intake"
    SIMMER = "simmer"
    ACTIVE = "active"
    COMPLETE = "complete"

class Job(Base, TenantMixin, TimestampMixin):
    __tablename__ = "jobs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    venue = Column(String, nullable=True)
    scheduled_start = Column(DateTime(timezone=True), nullable=True)
    scheduled_end = Column(DateTime(timezone=True), nullable=True)
    state = Column(Enum(JobState), nullable=False, default=JobState.INTAKE)
    # tenant_id from TenantMixin
    # created_at, updated_at from TimestampMixin

# backend/app/core/state_machine.py (optional - can inline in endpoint)
from app.models.job import JobState

# Allowed state transitions
ALLOWED_TRANSITIONS = {
    JobState.INTAKE: [JobState.SIMMER, JobState.ACTIVE],
    JobState.SIMMER: [JobState.ACTIVE, JobState.INTAKE],  # Can return to intake
    JobState.ACTIVE: [JobState.COMPLETE, JobState.SIMMER],  # Can pause to simmer
    JobState.COMPLETE: [],  # Terminal state
}

def can_transition(from_state: JobState, to_state: JobState) -> bool:
    """Validate state transition is allowed"""
    return to_state in ALLOWED_TRANSITIONS.get(from_state, [])

def validate_transition(from_state: JobState, to_state: JobState) -> None:
    """Raise exception if transition invalid"""
    if not can_transition(from_state, to_state):
        raise ValueError(f"Invalid transition: {from_state} -> {to_state}")
```

**Why this pattern:** Explicit and debuggable. State machine libraries (like `transitions`) are overkill for 4-state systems. This approach keeps all transition logic in one place without library overhead.

### Pattern 3: Search and Filtering
**What:** SQLAlchemy dynamic query building with optional filters

**When to use:** List endpoints with search/filter parameters

**Example:**
```python
# backend/app/schemas/job.py
from pydantic import BaseModel
from datetime import datetime
from app.models.job import JobState

class JobFilter(BaseModel):
    """Query parameters for job filtering"""
    search: str | None = None  # Search title/description/venue
    state: JobState | None = None
    venue: str | None = None
    start_date: datetime | None = None  # Jobs starting after this date
    end_date: datetime | None = None  # Jobs starting before this date

# backend/app/api/v1/jobs.py
from sqlalchemy import or_
from app.schemas.job import JobFilter

@router.get("/", response_model=list[JobResponse])
async def list_jobs(
    filters: JobFilter = Depends(),
    tenant_id: str = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """List jobs with optional filtering"""
    query = select(Job)
    
    # Apply filters dynamically
    if filters.search:
        search_pattern = f"%{filters.search}%"
        query = query.where(
            or_(
                Job.title.ilike(search_pattern),
                Job.description.ilike(search_pattern),
                Job.venue.ilike(search_pattern),
            )
        )
    
    if filters.state:
        query = query.where(Job.state == filters.state)
    
    if filters.venue:
        query = query.where(Job.venue.ilike(f"%{filters.venue}%"))
    
    if filters.start_date:
        query = query.where(Job.scheduled_start >= filters.start_date)
    
    if filters.end_date:
        query = query.where(Job.scheduled_start <= filters.end_date)
    
    # Order by scheduled_start descending (most recent first)
    query = query.order_by(Job.scheduled_start.desc())
    
    result = await db.execute(query)
    jobs = result.scalars().all()
    return jobs
```

**Why this pattern:** Pydantic `Depends()` auto-parses query parameters. ILIKE is case-insensitive and sufficient for < 10K rows. PostgreSQL RLS still applies automatically.

### Pattern 4: TIMESTAMPTZ Consistency
**What:** All datetime columns use DateTime(timezone=True) and store UTC

**When to use:** Every datetime field across all models

**Example:**
```python
from sqlalchemy import DateTime
from datetime import datetime

class Job(Base):
    scheduled_start = Column(DateTime(timezone=True), nullable=True)
    scheduled_end = Column(DateTime(timezone=True), nullable=True)
    # created_at, updated_at from TimestampMixin already use DateTime(timezone=True)

# In endpoint, accept datetime as ISO8601 string
from pydantic import BaseModel
from datetime import datetime

class JobCreate(BaseModel):
    title: str
    scheduled_start: datetime | None = None  # Pydantic auto-parses ISO8601
```

**Why this pattern:** Established in Phase 1 (REQUIREMENTS.md line 62, 01-01-SUMMARY.md). PostgreSQL TIMESTAMPTZ stores UTC, displays in client timezone. Pydantic handles ISO8601 parsing automatically.

### Pattern 5: Job Detail with Placeholder Sections
**What:** Response schema includes empty fields for future phase relationships

**When to use:** JOBS-06 requirement - show full job view with future features

**Example:**
```python
# backend/app/schemas/job.py
from pydantic import BaseModel
from datetime import datetime
from app.models.job import JobState

class JobResponse(BaseModel):
    id: str
    title: str
    description: str | None
    venue: str | None
    scheduled_start: datetime | None
    scheduled_end: datetime | None
    state: JobState
    created_at: datetime
    updated_at: datetime
    
    # Placeholder sections for future phases
    assigned_crew: list = []  # Phase 3: Resource Management
    assigned_gear: list = []  # Phase 3: Resource Management
    messages: list = []       # Phase 5: Coordination Layer
    tasks: list = []          # Phase 5: Coordination Layer
    files: list = []          # Phase 5: Coordination Layer
    
    class Config:
        from_attributes = True

# In endpoint, return job with placeholders
@router.get("/{job_id}", response_model=JobResponse)
async def get_job(job_id: str, ...):
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Job model doesn't have these fields yet, but Pydantic schema defaults them to []
    return job
```

**Why this pattern:** UI can render placeholder sections now ("No crew assigned yet"), avoiding breaking changes when Phase 3/5 add relationships. Frontend code doesn't need refactoring when crew/gear/messages are added.

### Anti-Patterns to Avoid

- **Mixing sync and async code**: Never call synchronous ORM methods in async endpoints (use `await db.execute()` not `db.query()`)
- **Manual tenant filtering**: Don't add `.where(Job.tenant_id == tenant_id)` - RLS handles this automatically
- **Forgetting SET LOCAL**: `get_current_tenant` dependency MUST be called to set RLS context (already handled by Phase 1 pattern)
- **State machine library for simple flows**: `transitions` library adds 100+ lines of config for a 4-state linear machine
- **Premature full-text search optimization**: Don't add ts_vector indexes until proven slow (> 500ms queries on realistic data)

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Password hashing | Custom hash function | bcrypt (already in Phase 1) | Timing attacks, salt management, bcrypt cost factor |
| JWT tokens | Custom signing | PyJWT (already in Phase 1) | Signature verification, expiration, key rotation |
| Input validation | Manual type checks | Pydantic schemas | Type coercion, nested validation, auto-docs |
| Database migrations | Manual SQL scripts | Alembic (already in Phase 1) | Reversibility, version tracking, team sync |
| Async database queries | Raw SQL with asyncpg | SQLAlchemy 2.0 async | Type safety, query composition, ORM relationships |

**Key insight:** Phase 1 already established these patterns. Phase 2 is CRUD operations - no new complex problems requiring custom solutions.

## Common Pitfalls

### Pitfall 1: Forgetting Tenant Context for Protected Routes
**What goes wrong:** Job queries return 0 results or violate RLS policies

**Why it happens:** Endpoint has `Depends(get_db)` but not `Depends(get_current_tenant)`, so PostgreSQL RLS blocks all queries (no tenant context set)

**How to avoid:** Every job endpoint must include `tenant_id: str = Depends(get_current_tenant)` in dependencies (even if tenant_id not used in function body - it sets the RLS context via SET LOCAL)

**Warning signs:** 
- Tests fail with "no rows found" but data exists
- PostgreSQL logs show "app.current_tenant_id not set"
- Queries work in Alembic migrations but fail in API endpoints

**Prevention:**
```python
# WRONG - missing tenant context
@router.get("/")
async def list_jobs(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Job))  # RLS blocks this!
    return result.scalars().all()

# CORRECT - tenant context set
@router.get("/")
async def list_jobs(
    tenant_id: str = Depends(get_current_tenant),  # Sets RLS context
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Job))  # RLS auto-filters by tenant
    return result.scalars().all()
```

### Pitfall 2: Invalid State Transitions Without Validation
**What goes wrong:** Jobs transition from COMPLETE back to INTAKE, breaking business logic

**Why it happens:** No validation function, just direct `job.state = new_state` in endpoint

**How to avoid:** Create dedicated transition endpoint that calls `validate_transition()` before updating state

**Warning signs:**
- Jobs stuck in impossible states
- State history shows invalid transitions
- Users report "can't complete job that's already complete"

**Prevention:**
```python
# WRONG - no validation
@router.patch("/{job_id}")
async def update_job(job_id: str, update: JobUpdate, ...):
    job.state = update.state  # Allows COMPLETE -> INTAKE!
    await db.commit()

# CORRECT - separate transition endpoint with validation
@router.post("/{job_id}/transition")
async def transition_job(
    job_id: str,
    new_state: JobState,
    tenant_id: str = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Validate transition
    if not can_transition(job.state, new_state):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid transition: {job.state} -> {new_state}"
        )
    
    job.state = new_state
    await db.commit()
    return {"message": f"Job transitioned to {new_state}"}
```

### Pitfall 3: N+1 Query Problem with Relationships
**What goes wrong:** Loading 100 jobs triggers 100 separate queries to load crew/gear

**Why it happens:** SQLAlchemy lazy-loads relationships by default

**How to avoid:** Not a problem in Phase 2 (no relationships yet). When Phase 3 adds crew/gear, use `selectinload()` or `joinedload()` for eager loading.

**Warning signs:**
- API slow despite small dataset
- Database logs show thousands of individual SELECT queries
- Pagination helps but doesn't solve root cause

**Future prevention (Phase 3+):**
```python
from sqlalchemy.orm import selectinload

# When Phase 3 adds crew relationship
query = select(Job).options(selectinload(Job.assigned_crew))
```

### Pitfall 4: Missing Index on State Column
**What goes wrong:** Filtering by state (`WHERE state = 'active'`) causes full table scans

**Why it happens:** SQLAlchemy creates enum columns without indexes by default

**How to avoid:** Add index in Alembic migration when creating jobs table

**Warning signs:**
- Queries slow down as jobs table grows
- `EXPLAIN ANALYZE` shows "Seq Scan" instead of "Index Scan"
- Filtering by state noticeably slower than filtering by ID

**Prevention:**
```python
# In Alembic migration
def upgrade():
    op.create_table(
        'jobs',
        # ... columns ...
        sa.Column('state', sa.Enum('intake', 'simmer', 'active', 'complete', name='jobstate'), nullable=False),
    )
    # Add index on state for filtering
    op.create_index('ix_jobs_state', 'jobs', ['state'])
    op.create_index('ix_jobs_scheduled_start', 'jobs', ['scheduled_start'])  # For date filtering
```

### Pitfall 5: Timezone Naive Datetime Comparisons
**What goes wrong:** Date filters return incorrect results (jobs missing or duplicated)

**Why it happens:** Frontend sends timezone-naive datetime, backend compares against TIMESTAMPTZ

**How to avoid:** Pydantic auto-parses ISO8601 strings with timezone info. Always send datetimes as ISO8601 from frontend.

**Warning signs:**
- "Jobs starting today" shows yesterday's jobs
- Date filters off by several hours
- Works in one timezone but breaks for users in different timezones

**Prevention:**
```python
# Frontend sends ISO8601 with timezone
fetch('/api/v1/jobs?start_date=2026-05-16T00:00:00Z')  # CORRECT

# Pydantic automatically parses to timezone-aware datetime
class JobFilter(BaseModel):
    start_date: datetime | None = None  # Parsed as timezone-aware
```

## Code Examples

### Complete Job CRUD Endpoint Skeleton
```python
# backend/app/api/v1/jobs.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from app.database import get_db
from app.dependencies import get_current_tenant
from app.core.permissions import require_admin
from app.models.job import Job, JobState
from app.schemas.job import JobCreate, JobUpdate, JobResponse, JobFilter
from app.models.user import User
from typing import Annotated

router = APIRouter(prefix="/api/v1/jobs", tags=["jobs"])

@router.post("/", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def create_job(
    job_data: JobCreate,
    current_user: User = Depends(require_admin),
    tenant_id: str = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """Create new job (admin only)"""
    job = Job(**job_data.model_dump(), tenant_id=tenant_id)
    db.add(job)
    await db.commit()
    await db.refresh(job)
    return job

@router.get("/", response_model=list[JobResponse])
async def list_jobs(
    search: str | None = None,
    state: JobState | None = None,
    venue: str | None = None,
    tenant_id: str = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """List jobs with optional filtering"""
    query = select(Job)
    
    if search:
        pattern = f"%{search}%"
        query = query.where(
            or_(Job.title.ilike(pattern), Job.description.ilike(pattern), Job.venue.ilike(pattern))
        )
    if state:
        query = query.where(Job.state == state)
    if venue:
        query = query.where(Job.venue.ilike(f"%{venue}%"))
    
    query = query.order_by(Job.scheduled_start.desc())
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: str,
    tenant_id: str = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """Get job by ID with placeholder sections for future features"""
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@router.patch("/{job_id}", response_model=JobResponse)
async def update_job(
    job_id: str,
    job_update: JobUpdate,
    current_user: User = Depends(require_admin),
    tenant_id: str = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """Update job (admin only, excludes state transitions)"""
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Update fields (exclude state - use transition endpoint)
    update_data = job_update.model_dump(exclude_unset=True, exclude={"state"})
    for key, value in update_data.items():
        setattr(job, key, value)
    
    await db.commit()
    await db.refresh(job)
    return job

@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_job(
    job_id: str,
    current_user: User = Depends(require_admin),
    tenant_id: str = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """Delete job (admin only)"""
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    await db.delete(job)
    await db.commit()

@router.post("/{job_id}/transition", response_model=JobResponse)
async def transition_job_state(
    job_id: str,
    new_state: JobState,
    current_user: User = Depends(require_admin),
    tenant_id: str = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """Transition job to new state with validation (admin only)"""
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Validate transition (can inline or use separate function)
    allowed_transitions = {
        JobState.INTAKE: [JobState.SIMMER, JobState.ACTIVE],
        JobState.SIMMER: [JobState.ACTIVE, JobState.INTAKE],
        JobState.ACTIVE: [JobState.COMPLETE, JobState.SIMMER],
        JobState.COMPLETE: [],
    }
    
    if new_state not in allowed_transitions.get(job.state, []):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid transition: {job.state.value} -> {new_state.value}"
        )
    
    job.state = new_state
    await db.commit()
    await db.refresh(job)
    return job
```

### Pydantic Schemas
```python
# backend/app/schemas/job.py
from pydantic import BaseModel, Field
from datetime import datetime
from app.models.job import JobState

class JobCreate(BaseModel):
    """Request schema for creating job"""
    title: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    venue: str | None = None
    scheduled_start: datetime | None = None
    scheduled_end: datetime | None = None

class JobUpdate(BaseModel):
    """Request schema for updating job (all fields optional)"""
    title: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = None
    venue: str | None = None
    scheduled_start: datetime | None = None
    scheduled_end: datetime | None = None

class JobResponse(BaseModel):
    """Response schema with all job fields + placeholders"""
    id: str
    title: str
    description: str | None
    venue: str | None
    scheduled_start: datetime | None
    scheduled_end: datetime | None
    state: JobState
    created_at: datetime
    updated_at: datetime
    
    # Placeholder sections for future phases
    assigned_crew: list = []
    assigned_gear: list = []
    messages: list = []
    tasks: list = []
    files: list = []
    
    class Config:
        from_attributes = True  # Allows returning SQLAlchemy models directly
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Sync SQLAlchemy (session.query()) | Async SQLAlchemy 2.0 (await db.execute(select())) | SQLAlchemy 2.0 release (2023) | Breaking change - all ORM code must be rewritten for async |
| Passlib for password hashing | Direct bcrypt usage | Phase 1 (compatibility issues) | Simpler, fewer dependencies |
| Authorization headers for JWT | httpOnly cookies | Phase 1 decision | More secure against XSS, requires CORS config |
| DateTime without timezone | DateTime(timezone=True) | Phase 1 decision | All new datetime columns MUST use TIMESTAMPTZ |

**Deprecated/outdated:**
- **SQLAlchemy 1.x `session.query()` API**: Use `await db.execute(select())` instead (2.0+ async pattern)
- **Pydantic 1.x `orm_mode = True`**: Now `from_attributes = True` in Pydantic 2.x Config
- **FastAPI `Body(...)` for JSON**: Pydantic models as type hints auto-parse (cleaner syntax)

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.3.4+ with pytest-asyncio 0.24.0+ |
| Config file | `backend/pytest.ini` (already exists from Phase 1) |
| Quick run command | `cd backend && python3 -m pytest tests/test_jobs.py -x` |
| Full suite command | `cd backend && python3 -m pytest tests/ -v` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| JOBS-01 | Admin creates job with title/date/venue/description | unit | `pytest tests/test_jobs.py::test_create_job -x` | ❌ Wave 0 |
| JOBS-01 | Crew user cannot create job (403) | unit | `pytest tests/test_jobs.py::test_create_job_crew_forbidden -x` | ❌ Wave 0 |
| JOBS-02 | Admin edits job fields | unit | `pytest tests/test_jobs.py::test_update_job -x` | ❌ Wave 0 |
| JOBS-02 | Admin deletes job | unit | `pytest tests/test_jobs.py::test_delete_job -x` | ❌ Wave 0 |
| JOBS-03 | Search jobs by text (title/description/venue) | unit | `pytest tests/test_jobs.py::test_search_jobs -x` | ❌ Wave 0 |
| JOBS-03 | Filter jobs by state | unit | `pytest tests/test_jobs.py::test_filter_by_state -x` | ❌ Wave 0 |
| JOBS-03 | Filter jobs by date range | unit | `pytest tests/test_jobs.py::test_filter_by_date -x` | ❌ Wave 0 |
| JOBS-04 | Job created with default INTAKE state | unit | `pytest tests/test_jobs.py::test_default_state -x` | ❌ Wave 0 |
| JOBS-05 | Valid state transition (intake -> simmer) | unit | `pytest tests/test_jobs.py::test_valid_transition -x` | ❌ Wave 0 |
| JOBS-05 | Invalid state transition rejected (complete -> intake) | unit | `pytest tests/test_jobs.py::test_invalid_transition -x` | ❌ Wave 0 |
| JOBS-06 | Job detail returns placeholder sections (empty lists) | unit | `pytest tests/test_jobs.py::test_job_detail_placeholders -x` | ❌ Wave 0 |
| RLS | Cross-tenant job access blocked | integration | `pytest tests/test_jobs.py::test_tenant_isolation -x` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `cd backend && python3 -m pytest tests/test_jobs.py -x` (fast fail on first error)
- **Per wave merge:** `cd backend && python3 -m pytest tests/test_jobs.py -v` (full job tests)
- **Phase gate:** `cd backend && python3 -m pytest tests/ -v` (all tests including auth from Phase 1)

### Wave 0 Gaps
- [ ] `backend/tests/test_jobs.py` — covers all JOBS-01 through JOBS-06 requirements
- [ ] `backend/tests/fixtures/job_fixtures.py` (optional) — shared job creation fixtures if needed

*(Framework and conftest.py already exist from Phase 1, no new setup needed)*

## Open Questions

1. **State transition history tracking**
   - What we know: Requirements specify state transitions (JOBS-05), but don't mention history
   - What's unclear: Should we track who/when each transition happened?
   - Recommendation: Start without history (simple enum column). If users request audit trail, add separate `job_state_history` table in future phase. Frontend can show current state only for Phase 2.

2. **Scheduled start/end vs actual start/end**
   - What we know: JOBS-01 specifies date/time fields
   - What's unclear: Do we need separate "actual start/actual end" fields for when job really happened?
   - Recommendation: Phase 2 only needs `scheduled_start` and `scheduled_end`. Add `actual_start`/`actual_end` if users report needing to track variance (likely Phase 6+ reporting feature).

3. **Soft delete vs hard delete**
   - What we know: JOBS-02 says "admin can delete jobs"
   - What's unclear: Should deleted jobs be soft-deleted (is_deleted flag) or hard-deleted (removed from database)?
   - Recommendation: Start with hard delete (simpler). If users request "undelete" or audit trail, add soft delete in future phase. PostgreSQL RLS handles tenant isolation either way.

## Sources

### Primary (HIGH confidence)
- Phase 1 codebase patterns: `/Users/operator/projects/duct-tape/backend/app/` (auth endpoints, models, dependencies)
- SQLAlchemy 2.0 documentation: https://docs.sqlalchemy.org/en/20/ (async patterns, filtering)
- FastAPI documentation: https://fastapi.tiangolo.com/ (dependency injection, Pydantic integration)
- Pydantic v2 documentation: https://docs.pydantic.dev/2.0/ (schema validation, Config changes)

### Secondary (MEDIUM confidence)
- PostgreSQL documentation: https://www.postgresql.org/docs/current/textsearch.html (full-text search vs ILIKE)
- Python Enum documentation: https://docs.python.org/3/library/enum.html (state machine alternative)

### Tertiary (LOW confidence)
- State machine library comparisons: Based on training data (not verified against current 2026 versions)
- Performance estimates: ILIKE performance assumes < 10K rows based on general PostgreSQL knowledge, not benchmarked

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All libraries already locked in Phase 1, no new dependencies
- Architecture: HIGH - Direct extension of Phase 1 CRUD patterns
- State machine approach: MEDIUM - Enum pattern is standard, but ALLOWED_TRANSITIONS dict is project-specific design choice
- Search/filter: MEDIUM - ILIKE vs ts_vector tradeoff is well-documented, but "10K rows threshold" is estimate not measurement
- Pitfalls: HIGH - RLS tenant context and state validation are concrete failure modes from similar projects

**Research date:** 2026-05-16
**Valid until:** ~30 days (stable stack, FastAPI/SQLAlchemy patterns mature)
