# Phase 3: Resource Management - Research

**Researched:** 2026-05-16
**Domain:** Resource booking, conflict detection, crew/equipment management, assignment workflows
**Confidence:** MEDIUM (Training data from Jan 2025, web research unavailable, patterns derived from existing codebase)

## Summary

Phase 3 implements crew profiles, equipment inventory, job assignments with confirmation workflow, and conflict detection for double-booking prevention. The phase builds on established patterns from Phase 1 (auth, RLS, state machines) and Phase 2 (CRUD, search, filtering).

**Key technical challenges:**
1. **Time overlap detection** - PostgreSQL range queries to find conflicting assignments
2. **Quantity-based resource pools** - Equipment with quantity > 1 requires available count tracking
3. **Assignment state machine** - Three-state flow: pending → confirmed/declined with crew acceptance workflow
4. **Recurring availability patterns** - Day-of-week patterns stored as bitmask or JSON array
5. **Conflict warning vs blocking** - Crew conflicts warn-with-override, equipment conflicts hard-block

**Primary recommendation:** Follow established patterns from Phase 1/2. Use PostgreSQL range overlap queries for conflict detection, ARRAY columns for skills/tags (tenant-scoped with autocomplete), and enum-based state machine for assignment confirmation. Database-level conflict checks prevent race conditions.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Crew-to-User relationship:**
- Crew profile is 1:1 with User account — every crew member must have a User (via invitation flow from Phase 1)
- Separate CrewProfile table with one-to-one FK to User — keeps auth concerns separate from crew data
- CrewProfile holds: skills, hourly rate, phone, bio, reliability stats
- Soft delete via `archived_at` timestamp on CrewProfile — archived crew hidden from search/assignment but historical data preserved
- Auto-create blank CrewProfile when a User with role=crew registers via invitation

**Assignment & confirmation flow:**
- Crew assignment: admin assigns directly, crew must confirm (pending → confirmed / declined)
- On decline: crew is unassigned, admin notified, decline history kept
- Equipment assignment: direct assign, no confirmation needed (gear doesn't have opinions)
- Assignment record includes a role/position field per job (e.g., "Camera Operator" on Job A, "Sound Tech" on Job B)

**Conflict detection behavior:**
- Crew conflicts: warn but allow admin override with reason — real production sometimes requires double-booking
- Time overlap: exact time range overlap (start1 < end2 AND start2 < end1) — jobs without scheduled times never conflict
- Equipment conflicts: hard block — physically can't be in two places, track available quantity per time slot
- Crew availability patterns also trigger conflict warnings (same warn-and-override flow as job overlap)
- All conflict checks happen at database level (decided in Phase 1 STATE.md)

**Skills & availability model:**
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

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope

</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| CREW-01 | Admin can create crew profiles (name, role, skills, rate, contact details) | CrewProfile model with 1:1 User FK, ARRAY column for skills, standard CRUD endpoints |
| CREW-02 | Admin can edit and archive crew profiles | Soft delete via archived_at timestamp, exclude from search WHERE archived_at IS NULL |
| CREW-03 | Searchable crew directory filterable by role, skill, availability | ILIKE search pattern from jobs.py, skills ANY(array), availability joins to assignments |
| CREW-04 | Crew can accept or decline job assignments (confirmation workflow) | AssignmentState enum (pending/confirmed/declined), state machine pattern from Phase 2 |
| CREW-05 | Admin can rate crew reliability after each job | Rating table with FK to CrewProfile + Job, 1-5 stars + notes |
| CREW-06 | Crew profile shows reliability history and past jobs | Aggregate query for average rating, count, join assignments for job history |
| CREW-07 | Skills matrix view showing crew capabilities across skill tags | Pivot query: all skills × all crew, mark intersections, or denormalized JSON response |
| CREW-08 | Crew can set recurring availability patterns (e.g., "unavailable Sundays") | AvailabilityPattern table: day_of_week (0-6), is_available boolean, per crew |
| CREW-09 | Crew availability auto-updates when assigned to jobs | Computed availability: check assignments + patterns, not stored state |
| EQUP-01 | Admin can add equipment to inventory (name, category, quantity, condition) | Equipment model with quantity integer, condition enum, tenant-scoped |
| EQUP-02 | Admin can assign equipment to jobs | EquipmentAssignment table: equipment_id, job_id, quantity_assigned, TIMESTAMPTZ range |
| EQUP-03 | Equipment conflict detection prevents double-booking gear | Query: SUM(quantity_assigned) WHERE time overlaps < equipment.quantity for pool |
| EQUP-04 | Equipment status tracking (available, assigned, maintenance) | Computed status from assignments + maintenance flag on Equipment table |
| SCHED-05 | Conflict detection prevents double-booking crew across overlapping jobs | Query: crew assignments WHERE (start1 < end2 AND start2 < end1), return warnings |

</phase_requirements>

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| SQLAlchemy | 2.0.49 | ORM + async queries | Already in use, async support, relationship handling |
| FastAPI | 0.136.1 | API endpoints | Already in use, dependency injection for permissions |
| Pydantic | 2.13.4 | Schema validation | Already in use, strict validation for assignment state |
| PostgreSQL | 14+ (TIMESTAMPTZ) | Database with RLS | Already in use, ARRAY columns for tags, range queries for overlap |
| pytest | 9.0.2 | Testing framework | Already in use, async support via pytest-asyncio |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Alembic | 1.18.4 | Database migrations | Already in use, manual migration creation pattern |
| pytest-asyncio | 0.24.0+ | Async test fixtures | Already in use, required for async endpoint tests |

### Alternatives Considered

None — all dependencies already established in Phase 1/2. No new libraries required for Phase 3.

**Installation:**
```bash
# All dependencies already installed from Phase 1/2
# No additional packages needed
```

**Version verification:** All versions confirmed from existing `backend/pyproject.toml` (read 2026-05-16).

## Architecture Patterns

### Recommended Project Structure

```
backend/app/
├── models/
│   ├── crew_profile.py        # CrewProfile with 1:1 User FK
│   ├── equipment.py            # Equipment inventory
│   ├── assignment.py           # CrewAssignment + EquipmentAssignment
│   ├── availability.py         # AvailabilityPattern (day-of-week)
│   └── rating.py               # CrewRating (post-job feedback)
├── schemas/
│   ├── crew.py                 # CrewProfileCreate/Update/Response
│   ├── equipment.py            # EquipmentCreate/Update/Response
│   └── assignment.py           # AssignmentCreate/Response + ConflictWarning
├── api/v1/
│   ├── crew.py                 # CRUD + search + skills matrix
│   ├── equipment.py            # CRUD + inventory status
│   └── assignments.py          # Assign crew/gear + conflict detection
└── core/
    └── conflicts.py            # Time overlap detection logic
```

### Pattern 1: Time Overlap Detection (Conflict Detection)

**What:** Database-level query to find overlapping time ranges
**When to use:** Before creating crew or equipment assignments
**Example:**

```python
# backend/app/core/conflicts.py
from sqlalchemy import select, and_
from datetime import datetime

async def check_crew_conflicts(
    db: AsyncSession,
    crew_id: UUID,
    start: datetime,
    end: datetime,
    exclude_assignment_id: UUID | None = None
) -> list[Assignment]:
    """
    Find crew assignments that overlap with given time range.
    
    Overlap condition: start1 < end2 AND start2 < end1
    """
    query = select(Assignment).join(Job).where(
        and_(
            Assignment.crew_id == crew_id,
            Assignment.status == AssignmentState.CONFIRMED,
            Job.scheduled_start < end,  # Job starts before range ends
            Job.scheduled_end > start,   # Job ends after range starts
        )
    )
    
    if exclude_assignment_id:
        query = query.where(Assignment.id != exclude_assignment_id)
    
    result = await db.execute(query)
    return result.scalars().all()
```

**Confidence:** HIGH (Standard SQL range overlap pattern, verified in codebase review)

### Pattern 2: Assignment State Machine

**What:** Three-state confirmation workflow for crew assignments
**When to use:** Crew assignment endpoints (create, confirm, decline)
**Example:**

```python
# backend/app/models/assignment.py
from enum import Enum

class AssignmentState(str, Enum):
    PENDING = "pending"      # Admin assigned, crew hasn't responded
    CONFIRMED = "confirmed"  # Crew accepted
    DECLINED = "declined"    # Crew rejected

# State transitions (following state_machine.py pattern from Phase 2)
ALLOWED_TRANSITIONS = {
    AssignmentState.PENDING: [AssignmentState.CONFIRMED, AssignmentState.DECLINED],
    AssignmentState.CONFIRMED: [AssignmentState.DECLINED],  # Can cancel after confirming
    AssignmentState.DECLINED: [],  # Terminal
}
```

**Confidence:** HIGH (Established pattern from Phase 2 state_machine.py)

### Pattern 3: Skills as PostgreSQL ARRAY

**What:** Store skills as TEXT[] column with tenant-scoped vocabulary
**When to use:** CrewProfile model, Equipment categories
**Example:**

```python
# backend/app/models/crew_profile.py
from sqlalchemy import Column, ARRAY, String
from sqlalchemy.dialects.postgresql import ARRAY as PG_ARRAY

class CrewProfile(Base, TenantMixin, TimestampMixin):
    __tablename__ = "crew_profiles"
    
    skills = Column(PG_ARRAY(String), nullable=False, default=list)
    # Search: WHERE 'Camera' = ANY(skills)
    # Filter: WHERE skills && ARRAY['Camera', 'Sound']  (overlap)
```

**Confidence:** MEDIUM (PostgreSQL ARRAY standard, but project hasn't used arrays yet)

### Pattern 4: Equipment Quantity Pool Tracking

**What:** Track available quantity per time slot by summing active assignments
**When to use:** Equipment conflict detection for items with quantity > 1
**Example:**

```python
# backend/app/core/conflicts.py
async def check_equipment_availability(
    db: AsyncSession,
    equipment_id: UUID,
    start: datetime,
    end: datetime,
    quantity_needed: int
) -> tuple[bool, int]:
    """
    Check if enough equipment is available in time range.
    
    Returns: (is_available, quantity_available)
    """
    # Get total quantity
    equipment = await db.get(Equipment, equipment_id)
    
    # Sum assigned quantity in overlapping time range
    query = select(func.sum(EquipmentAssignment.quantity_assigned)).join(Job).where(
        and_(
            EquipmentAssignment.equipment_id == equipment_id,
            Job.scheduled_start < end,
            Job.scheduled_end > start,
        )
    )
    result = await db.execute(query)
    assigned = result.scalar() or 0
    
    available = equipment.quantity - assigned
    return available >= quantity_needed, available
```

**Confidence:** MEDIUM (Standard approach, but aggregation query adds complexity)

### Pattern 5: Recurring Availability (Day-of-Week)

**What:** Store weekly patterns as separate rows (one per day-of-week)
**When to use:** Crew availability settings
**Example:**

```python
# backend/app/models/availability.py
class AvailabilityPattern(Base, TenantMixin, TimestampMixin):
    __tablename__ = "availability_patterns"
    
    crew_id = Column(UUID(as_uuid=True), ForeignKey("crew_profiles.id"), nullable=False)
    day_of_week = Column(Integer, nullable=False)  # 0=Monday, 6=Sunday
    is_available = Column(Boolean, nullable=False, default=True)
    
    # Unique constraint: one row per crew per day
    __table_args__ = (
        UniqueConstraint('crew_id', 'day_of_week', name='uq_crew_day'),
    )
```

**Confidence:** HIGH (Straightforward relational pattern)

### Anti-Patterns to Avoid

- **Storing computed availability state** — Don't add `is_available` boolean to CrewProfile; compute from assignments + patterns on each query to avoid stale data
- **Application-level conflict checking** — Race conditions if two requests check availability simultaneously; use database constraints or transactions
- **Cascading deletes on assignments** — User locked decisions require keeping decline history; use soft delete or status field
- **Normalizing skill vocabulary prematurely** — Free-text tags are faster to build; can migrate to Skill table later if autocomplete performance degrades

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Time overlap detection | Custom date comparison logic | PostgreSQL range queries: `start1 < end2 AND start2 < end1` | Off-by-one errors, timezone bugs, tested pattern |
| State machine validation | If/else chains | Enum + ALLOWED_TRANSITIONS dict (see state_machine.py) | Already established in Phase 2, maintainable |
| Pagination | Manual LIMIT/OFFSET | FastAPI query params + SQLAlchemy slice | Consistent with Phase 2 patterns |
| Skills autocomplete | Custom search | PostgreSQL `SELECT DISTINCT unnest(skills)` + ILIKE filter | Native array functions, fast for < 10K rows |

**Key insight:** Conflict detection is deceptively complex — timezone handling, boundary conditions (start == end), null scheduled times, and race conditions all cause bugs. Database-level checks with proper indexing prevent most issues.

## Common Pitfalls

### Pitfall 1: Time Overlap Boundary Conditions

**What goes wrong:** Off-by-one errors when checking if time ranges overlap (e.g., Job A ends at 5:00 PM, Job B starts at 5:00 PM — is that a conflict?)

**Why it happens:** Confusion between inclusive/exclusive boundaries and different overlap formulas

**How to avoid:** Use strict inequality for overlap: `start1 < end2 AND start2 < end1`. This treats boundaries as exclusive (touching ranges don't conflict).

**Warning signs:** Test failures on edge cases, production double-bookings where jobs share exact boundary times

**Confidence:** HIGH (Standard SQL pattern, well-documented)

### Pitfall 2: Race Conditions in Conflict Detection

**What goes wrong:** Two requests check availability simultaneously, both see no conflict, both create assignments → double-booking

**Why it happens:** Check-then-act pattern without transaction isolation or locking

**How to avoid:** 
1. Run conflict check and assignment creation in same transaction
2. Use `SELECT ... FOR UPDATE` on related records
3. Or add database constraint (PostgreSQL EXCLUDE constraint with ranges)

**Warning signs:** Intermittent test failures, production double-bookings that shouldn't be possible

**Confidence:** MEDIUM (Database locking patterns vary by workload; EXCLUDE constraint is PostgreSQL-specific and complex to implement)

### Pitfall 3: Null Scheduled Times Breaking Queries

**What goes wrong:** Jobs without scheduled times (start/end are NULL) appear to conflict with everything or nothing depending on query

**Why it happens:** SQL three-valued logic: `NULL < X` is NULL (not true or false)

**How to avoid:** Explicitly filter out null times: `WHERE Job.scheduled_start IS NOT NULL AND Job.scheduled_end IS NOT NULL` in conflict queries

**Warning signs:** "Unscheduled job conflicts with everything" or "Unscheduled jobs never conflict" bugs

**Confidence:** HIGH (SQL NULL handling is well-defined)

### Pitfall 4: Timezone Confusion

**What goes wrong:** Jobs scheduled in different timezones appear to conflict when they don't (or vice versa)

**Why it happens:** Mixing timezone-aware and timezone-naive datetimes

**How to avoid:** 
- Already solved in Phase 1: all datetime columns use `TIMESTAMPTZ`
- All Python datetimes must include timezone (use `datetime.now(timezone.utc)`)
- Pydantic schemas enforce timezone-aware datetimes

**Warning signs:** Conflict detection works locally but fails in production (different server timezone)

**Confidence:** HIGH (Already established in Phase 1, pattern to follow)

### Pitfall 5: Equipment Quantity Tracking Edge Cases

**What goes wrong:** Equipment shows as "available" when all units are assigned, or "unavailable" when units are free

**Why it happens:** 
- Not accounting for partial assignments (3 cameras, 2 assigned → 1 available)
- Not filtering by time range when summing assigned quantity

**How to avoid:**
- Always sum quantity_assigned WHERE time overlaps target range
- Compare available = total_quantity - assigned_sum, not assigned_count

**Warning signs:** "Out of stock" errors when equipment should be available, silent over-booking

**Confidence:** MEDIUM (Aggregation queries are complex, easy to miss edge cases)

### Pitfall 6: Skills Array Search Performance

**What goes wrong:** Slow crew directory search when filtering by skills as dataset grows

**Why it happens:** ARRAY column searches don't use standard B-tree indexes efficiently

**How to avoid:**
- For early versions: ARRAY search is fine for < 10K rows
- If slow: add GIN index on skills column: `CREATE INDEX idx_crew_skills ON crew_profiles USING GIN(skills)`
- If still slow: migrate to normalized Skill table with junction table

**Warning signs:** Search endpoint timeouts, database CPU spikes on skill filters

**Confidence:** MEDIUM (GIN indexes are PostgreSQL-specific, migration path depends on scale)

## Code Examples

Verified patterns from existing codebase and established SQL standards.

### Crew Assignment with Conflict Detection

```python
# backend/app/api/v1/assignments.py
from fastapi import APIRouter, Depends, HTTPException, status
from app.core.conflicts import check_crew_conflicts

@router.post("/crew-assignments", response_model=AssignmentResponse)
async def assign_crew_to_job(
    assignment_data: CrewAssignmentCreate,
    current_user: User = Depends(require_admin),
    tenant_id: str = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """
    Assign crew to job with conflict detection.
    
    Returns 409 with conflict details if crew is double-booked.
    Admin can override by passing force=true.
    """
    # Get job to check scheduled times
    job = await db.get(Job, assignment_data.job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    
    # Skip conflict check if job has no scheduled times
    if job.scheduled_start and job.scheduled_end:
        conflicts = await check_crew_conflicts(
            db,
            assignment_data.crew_id,
            job.scheduled_start,
            job.scheduled_end,
        )
        
        if conflicts and not assignment_data.force:
            # Return 409 with conflict details
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "message": "Crew is already assigned to overlapping jobs",
                    "conflicts": [
                        {
                            "job_id": str(c.job_id),
                            "job_title": c.job.title,
                            "start": c.job.scheduled_start,
                            "end": c.job.scheduled_end,
                        }
                        for c in conflicts
                    ],
                },
            )
    
    # Create assignment in PENDING state
    assignment = CrewAssignment(
        job_id=assignment_data.job_id,
        crew_id=assignment_data.crew_id,
        role=assignment_data.role,  # e.g., "Camera Operator"
        status=AssignmentState.PENDING,
        override_reason=assignment_data.override_reason if assignment_data.force else None,
        tenant_id=tenant_id,
    )
    
    db.add(assignment)
    await db.commit()
    await db.refresh(assignment)
    return assignment
```

### Skills Matrix Query

```python
# backend/app/api/v1/crew.py
@router.get("/skills-matrix", response_model=SkillsMatrixResponse)
async def get_skills_matrix(
    tenant_id: str = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """
    Return all crew with their skills in matrix format.
    
    Response structure:
    {
      "skills": ["Camera", "Sound", "Lighting"],
      "crew": [
        {
          "id": "...",
          "name": "Alice",
          "skills": {"Camera": true, "Sound": false, "Lighting": true}
        }
      ]
    }
    """
    # Get all unique skills across all crew (tenant-scoped by RLS)
    query = select(func.unnest(CrewProfile.skills)).distinct()
    result = await db.execute(query)
    all_skills = sorted([s[0] for s in result.all()])
    
    # Get all crew with their skills
    crew_query = select(CrewProfile).where(CrewProfile.archived_at.is_(None))
    crew_result = await db.execute(crew_query)
    crew_list = crew_result.scalars().all()
    
    # Build matrix
    crew_matrix = [
        {
            "id": str(crew.id),
            "name": crew.user.name,  # Assuming User has name field
            "skills": {skill: skill in crew.skills for skill in all_skills}
        }
        for crew in crew_list
    ]
    
    return {"skills": all_skills, "crew": crew_matrix}
```

### Equipment Availability Check

```python
# backend/app/core/conflicts.py
from sqlalchemy import func

async def get_equipment_availability(
    db: AsyncSession,
    equipment_id: UUID,
    start: datetime,
    end: datetime,
) -> dict:
    """
    Calculate available equipment quantity in time range.
    
    Returns:
    {
      "total_quantity": 5,
      "assigned_quantity": 3,
      "available_quantity": 2,
      "assignments": [...]  # List of overlapping assignments
    }
    """
    # Get equipment
    equipment = await db.get(Equipment, equipment_id)
    if not equipment:
        raise ValueError("Equipment not found")
    
    # Find overlapping assignments
    query = select(EquipmentAssignment).join(Job).where(
        and_(
            EquipmentAssignment.equipment_id == equipment_id,
            Job.scheduled_start.is_not(None),
            Job.scheduled_end.is_not(None),
            Job.scheduled_start < end,
            Job.scheduled_end > start,
        )
    )
    result = await db.execute(query)
    overlapping = result.scalars().all()
    
    # Sum assigned quantity
    assigned_sum = sum(a.quantity_assigned for a in overlapping)
    
    return {
        "total_quantity": equipment.quantity,
        "assigned_quantity": assigned_sum,
        "available_quantity": equipment.quantity - assigned_sum,
        "assignments": overlapping,
    }
```

### Crew Directory Search with Filters

```python
# backend/app/api/v1/crew.py
from sqlalchemy import or_, and_

@router.get("/", response_model=list[CrewProfileResponse])
async def list_crew(
    search: str | None = None,
    skills: list[str] | None = None,
    available_on: datetime | None = None,
    tenant_id: str = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """
    List crew with search and filters.
    
    Query parameters:
    - search: Search name, bio, phone (case-insensitive)
    - skills: Filter by skills (crew must have ALL listed skills)
    - available_on: Filter to crew available at specific datetime
    
    Excludes archived crew (archived_at IS NULL).
    """
    query = select(CrewProfile).where(CrewProfile.archived_at.is_(None))
    
    # Search filter
    if search:
        pattern = f"%{search}%"
        query = query.join(User).where(
            or_(
                User.name.ilike(pattern),
                CrewProfile.bio.ilike(pattern),
                CrewProfile.phone.ilike(pattern),
            )
        )
    
    # Skills filter (crew must have ALL skills in list)
    if skills:
        for skill in skills:
            query = query.where(CrewProfile.skills.contains([skill]))
    
    # Availability filter (no overlapping confirmed assignments)
    if available_on:
        # Subquery: crew IDs with conflicting assignments
        conflict_subquery = select(CrewAssignment.crew_id).join(Job).where(
            and_(
                CrewAssignment.status == AssignmentState.CONFIRMED,
                Job.scheduled_start <= available_on,
                Job.scheduled_end >= available_on,
            )
        )
        query = query.where(CrewProfile.id.not_in(conflict_subquery))
    
    result = await db.execute(query)
    return result.scalars().all()
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Manual conflict checking in app code | Database-level range queries | N/A (best practice) | Prevents race conditions, enforces at data layer |
| Normalized skills table | PostgreSQL ARRAY column | ~2020 with JSONB/ARRAY support | Faster prototyping, simpler queries, migrate later if needed |
| Separate availability table rows | Bitmask or JSON column | N/A (both valid) | Row-per-day is more queryable, bitmask is more compact |
| Equipment individual serial tracking | Quantity pools | Depends on use case | Pools simpler for fungible gear, serial tracking for unique items |

**Deprecated/outdated:**
- `passlib` for password hashing: Phase 1 already migrated to direct `bcrypt` usage (passlib 1.7.4 incompatible with modern bcrypt)
- PostgreSQL `tsrange` columns: Could be used for time ranges but adds complexity; explicit start/end columns are clearer

## Open Questions

1. **Equipment individual vs pool tracking**
   - What we know: User decision allows Claude's discretion
   - What's unclear: If some equipment needs serial numbers (e.g., cameras with different firmware) while others are pools (e.g., cables)
   - Recommendation: Start with quantity pools (simpler), add optional `serial_number` text column for future per-unit tracking

2. **Conflict warning response format**
   - What we know: 409 status code for conflicts, admin can override
   - What's unclear: Should frontend show all conflicts or just first N? Should API paginate conflict list?
   - Recommendation: Return all conflicts (unlikely to be > 20 for single crew member), no pagination needed

3. **Skills autocomplete performance threshold**
   - What we know: Free-text tags, tenant-scoped
   - What's unclear: At what scale does ARRAY search become too slow?
   - Recommendation: GIN index supports 10K+ crew easily; migrate to normalized table only if > 50K crew or autocomplete latency > 200ms

4. **Assignment history retention**
   - What we know: Decline history must be kept
   - What's unclear: How long? Should old assignments be archived?
   - Recommendation: Keep all assignment history indefinitely (disk is cheap), add `archived_at` only if UI performance degrades

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 + pytest-asyncio 0.24.0 |
| Config file | `backend/pytest.ini` (already exists) |
| Quick run command | `pytest tests/test_crew*.py tests/test_equipment*.py tests/test_assignments*.py -x` |
| Full suite command | `pytest tests/ -v` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| CREW-01 | Admin creates crew profile | integration | `pytest tests/test_crew_crud.py::test_create_crew_profile -x` | ❌ Wave 0 |
| CREW-02 | Admin archives crew profile | integration | `pytest tests/test_crew_crud.py::test_archive_crew_profile -x` | ❌ Wave 0 |
| CREW-03 | Search crew by skills/availability | integration | `pytest tests/test_crew_search.py::test_filter_by_skills -x` | ❌ Wave 0 |
| CREW-04 | Crew confirms/declines assignment | integration | `pytest tests/test_assignments.py::test_crew_confirmation_flow -x` | ❌ Wave 0 |
| CREW-05 | Admin rates crew post-job | integration | `pytest tests/test_ratings.py::test_rate_crew -x` | ❌ Wave 0 |
| CREW-06 | Profile shows rating history | integration | `pytest tests/test_crew_crud.py::test_crew_profile_with_ratings -x` | ❌ Wave 0 |
| CREW-07 | Skills matrix view | integration | `pytest tests/test_crew_matrix.py::test_skills_matrix -x` | ❌ Wave 0 |
| CREW-08 | Set recurring availability | integration | `pytest tests/test_availability.py::test_set_weekly_pattern -x` | ❌ Wave 0 |
| CREW-09 | Availability updates on assignment | integration | `pytest tests/test_availability.py::test_computed_availability -x` | ❌ Wave 0 |
| EQUP-01 | Admin adds equipment | integration | `pytest tests/test_equipment_crud.py::test_create_equipment -x` | ❌ Wave 0 |
| EQUP-02 | Admin assigns equipment to job | integration | `pytest tests/test_assignments.py::test_assign_equipment -x` | ❌ Wave 0 |
| EQUP-03 | Equipment conflict detection | unit + integration | `pytest tests/test_conflicts.py::test_equipment_quantity_pool -x` | ❌ Wave 0 |
| EQUP-04 | Equipment status tracking | integration | `pytest tests/test_equipment_crud.py::test_equipment_status -x` | ❌ Wave 0 |
| SCHED-05 | Crew conflict detection | unit + integration | `pytest tests/test_conflicts.py::test_crew_time_overlap -x` | ❌ Wave 0 |

### Sampling Rate

- **Per task commit:** `pytest tests/test_conflicts.py -x` (conflict detection is critical path)
- **Per wave merge:** `pytest tests/test_crew*.py tests/test_equipment*.py tests/test_assignments*.py -v`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `tests/test_crew_crud.py` — covers CREW-01, CREW-02, CREW-06
- [ ] `tests/test_crew_search.py` — covers CREW-03 (search/filter)
- [ ] `tests/test_assignments.py` — covers CREW-04, EQUP-02 (assignment workflows)
- [ ] `tests/test_ratings.py` — covers CREW-05 (rating system)
- [ ] `tests/test_crew_matrix.py` — covers CREW-07 (skills matrix)
- [ ] `tests/test_availability.py` — covers CREW-08, CREW-09 (recurring patterns)
- [ ] `tests/test_equipment_crud.py` — covers EQUP-01, EQUP-04
- [ ] `tests/test_conflicts.py` — covers EQUP-03, SCHED-05 (conflict detection core)
- [ ] Fixtures in `tests/conftest.py` — add `test_crew_profile`, `test_equipment`, `test_assignment` fixtures

Framework already installed and configured (pytest.ini exists from Phase 1).

## Sources

### Primary (HIGH confidence)

- Existing codebase: `backend/app/models/base.py` (TenantMixin, TimestampMixin patterns)
- Existing codebase: `backend/app/models/job.py` (JobState enum pattern)
- Existing codebase: `backend/app/core/state_machine.py` (State transition validation pattern)
- Existing codebase: `backend/app/api/v1/jobs.py` (CRUD + search endpoint patterns)
- Existing codebase: `backend/app/core/permissions.py` (require_admin, require_active patterns)
- Existing codebase: `backend/tests/conftest.py` (Test fixture patterns)
- Existing codebase: `backend/pyproject.toml` (Dependency versions verified 2026-05-16)

### Secondary (MEDIUM confidence)

- Training data (Jan 2025): PostgreSQL time overlap queries (`start1 < end2 AND start2 < end1`)
- Training data (Jan 2025): PostgreSQL ARRAY column usage for tags
- Training data (Jan 2025): SQLAlchemy 2.0 async patterns
- Training data (Jan 2025): FastAPI dependency injection patterns

### Tertiary (LOW confidence)

- Training data (Jan 2025): GIN index performance characteristics for ARRAY columns
- Training data (Jan 2025): PostgreSQL EXCLUDE constraints for time ranges (complex to implement, not recommended without verification)

**Note:** Web research and Context7 were unavailable during research (2026-05-16). All findings based on existing codebase patterns (HIGH confidence) and training data from Jan 2025 (MEDIUM confidence). Conflict detection patterns and ARRAY usage are standard PostgreSQL features but should be verified with official docs if implementation details are unclear.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - all dependencies already in use, versions verified from pyproject.toml
- Architecture: HIGH - following established patterns from Phase 1/2
- Conflict detection: MEDIUM - standard SQL patterns but web research unavailable to verify edge cases
- Equipment quantity pools: MEDIUM - aggregation logic is complex, should test edge cases thoroughly
- Skills ARRAY performance: LOW - GIN index guidance from training data, not verified with recent benchmarks

**Research date:** 2026-05-16
**Valid until:** 2026-06-16 (30 days - stable domain, standard patterns unlikely to change)

**Limitations:** Web search and Context7 unavailable; relied on training data (Jan 2025) and codebase analysis. Recommend verifying PostgreSQL conflict detection edge cases and ARRAY performance characteristics with official docs during implementation if issues arise.
