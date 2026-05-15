# Architecture Patterns for Crew Management SaaS

**Domain:** Crew/Resource Management SaaS
**Stack:** FastAPI + React + PostgreSQL
**Researched:** 2026-05-15

**Confidence:** MEDIUM — Based on training data analysis of workforce management systems, multi-tenant SaaS patterns, and FastAPI best practices. Unable to verify with current documentation due to environment constraints.

## Recommended Architecture

### High-Level Structure

```
┌─────────────────────────────────────────────────────────────┐
│                     React Frontend (SPA)                     │
│  ┌──────────┬──────────┬──────────┬──────────┬───────────┐ │
│  │ Job View │ Calendar │ Crew Mgmt│ Messages │ Tasks     │ │
│  └──────────┴──────────┴──────────┴──────────┴───────────┘ │
└────────────────────────┬────────────────────────────────────┘
                         │ REST API + WebSocket
┌────────────────────────┴────────────────────────────────────┐
│                    FastAPI Backend                          │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              API Gateway Layer                        │  │
│  │  (Auth, Tenant Resolution, Request Routing)           │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌─────────────────┐  ┌─────────────────┐  ┌────────────┐ │
│  │ Job Management  │  │ Resource Mgmt   │  │ Messaging  │ │
│  │   Service       │  │   Service       │  │  Service   │ │
│  └────────┬────────┘  └────────┬────────┘  └─────┬──────┘ │
│           │                    │                   │        │
│  ┌────────┴────────────────────┴───────────────────┴─────┐ │
│  │            Domain Models & Business Logic             │ │
│  └────────┬──────────────────────────────────────────────┘ │
│           │                                                 │
│  ┌────────┴────────────────────────────────────────────┐  │
│  │        Data Access Layer (SQLAlchemy ORM)           │  │
│  └────────┬────────────────────────────────────────────┘  │
└───────────┼─────────────────────────────────────────────────┘
            │
┌───────────┴─────────────────────────────────────────────────┐
│                    PostgreSQL Database                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Tenants    │  │    Jobs      │  │   Resources  │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  Assignments │  │  Messages    │  │    Files     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│              External Services (Loosely Coupled)             │
│  ┌────────────┐  ┌────────────┐  ┌─────────────────────┐   │
│  │ S3/Object  │  │   Email    │  │   Background Jobs   │   │
│  │  Storage   │  │  Service   │  │   (Celery/Redis)    │   │
│  └────────────┘  └────────────┘  └─────────────────────┘   │
└──────────────────────────────────────────────────────────────┘
```

## Component Boundaries

### 1. API Gateway Layer
**Responsibility:** Request entry point, cross-cutting concerns
**Communicates With:** All service layers

**Functions:**
- Authentication/authorization (JWT validation)
- Tenant context resolution from token
- Request logging and monitoring
- Rate limiting per tenant
- CORS handling
- API versioning

**Critical for:** Multi-tenancy enforcement — every request must resolve to a tenant context

### 2. Job Management Service
**Responsibility:** Job lifecycle orchestration
**Communicates With:** Resource Management (for allocation), Messaging (for notifications), File Service (for attachments)

**Functions:**
- Job CRUD operations (create, read, update, delete)
- State transitions (intake → simmer → active → complete)
- Job search and filtering
- Timeline/history tracking
- Email chain attachment

**Domain Models:**
- Job (id, tenant_id, name, status, dates, description)
- JobStatusHistory (state change log)
- JobEmailChain (linked email references)

### 3. Resource Management Service
**Responsibility:** Crew and equipment allocation
**Communicates With:** Job Management (for assignments), Calendar Service (for availability)

**Functions:**
- Crew profile management (skills, rates, availability, reliability)
- Equipment inventory tracking (owned + rented)
- Resource allocation to jobs
- Conflict detection (double-booking prevention)
- Availability calculation
- Utilization reporting

**Domain Models:**
- CrewMember (id, tenant_id, name, skills, rate, contact)
- Equipment (id, tenant_id, name, type, owner/rental status)
- ResourceAssignment (links jobs ↔ crew/equipment)
- Availability (calendar blocks per resource)

### 4. Messaging Service
**Responsibility:** Real-time communication tied to jobs
**Communicates With:** Job Management (context), WebSocket Gateway (delivery)

**Functions:**
- Threaded messaging (Slack-style)
- Message persistence
- Read receipts / online status
- Notification dispatch
- Message search

**Domain Models:**
- MessageThread (id, job_id, tenant_id)
- Message (id, thread_id, author_id, content, timestamp)
- MessageRead (tracking who read what)

**Tech Note:** WebSocket connection pool in FastAPI for real-time delivery

### 5. Task Management Service
**Responsibility:** Actionable work items within jobs
**Communicates With:** Job Management (context), Messaging (notifications)

**Functions:**
- Task CRUD with assignments
- Priority levels and deadlines
- Expected delivery time tracking
- Task status transitions (todo → in-progress → done)
- Dependency tracking (task A blocks task B)
- Overdue notifications

**Domain Models:**
- Task (id, job_id, assignee_id, title, priority, deadline, status)
- TaskDependency (task_id, blocks_task_id)

### 6. File Service
**Responsibility:** Document/media storage and access
**Communicates With:** Object Storage (S3), Job Management (context)

**Functions:**
- File upload/download
- Metadata storage (filename, type, size, uploader, timestamp)
- Access control (tenant isolation, job-based permissions)
- Version tracking (optional for briefs/runsheets)
- Thumbnail generation for images

**Domain Models:**
- File (id, job_id, tenant_id, storage_key, metadata)

**Storage Strategy:** 
- PostgreSQL for metadata
- S3/object storage for blobs
- Path structure: `{tenant_id}/{job_id}/{file_id}-{filename}`

### 7. Calendar Service
**Responsibility:** Temporal views of resource allocation
**Communicates With:** Resource Management (data source)

**Functions:**
- Day/week/month views of crew schedules
- Equipment availability calendar
- Job timeline visualization
- Drag-and-drop rescheduling (triggers allocation updates)

**Tech Note:** Heavy read layer, minimal write logic (delegates to Resource Management)

### 8. Authentication Service
**Responsibility:** User identity and access control
**Communicates With:** API Gateway (token validation)

**Functions:**
- User login/logout
- JWT token issuance and refresh
- Password hashing (bcrypt/Argon2)
- Role-based access control (admin vs crew)
- Tenant membership verification

**Domain Models:**
- User (id, tenant_id, email, password_hash, role)
- RefreshToken (session management)

## Data Flow Patterns

### Pattern 1: Job Resource Allocation
```
User Action: Admin assigns crew member to job

1. Frontend → POST /jobs/{job_id}/assignments
2. API Gateway → Authenticate, resolve tenant
3. Resource Management Service:
   - Check crew member availability (conflict detection)
   - Create ResourceAssignment record
   - Update resource availability cache
4. Job Management Service:
   - Update job status if needed
5. Messaging Service:
   - Notify assigned crew member
6. Calendar Service:
   - Invalidate cache for affected date range
7. Response → Frontend updates UI
```

### Pattern 2: Real-Time Messaging
```
User Action: Admin sends message in job thread

1. Frontend → WebSocket send message
2. WebSocket Gateway → Validate connection, resolve tenant
3. Messaging Service:
   - Persist message to DB
   - Determine thread participants
4. WebSocket Gateway:
   - Broadcast to connected participants (same tenant, same job)
5. Messaging Service:
   - Queue notifications for offline users
6. Frontend → All connected clients receive message
```

### Pattern 3: Job Ignition (State Change)
```
User Action: Admin transitions job from simmer → active

1. Frontend → PATCH /jobs/{job_id} with status: active
2. Job Management Service:
   - Validate state transition allowed
   - Update job status
   - Create JobStatusHistory entry
   - Trigger side effects:
     a. Messaging: Create default thread
     b. Tasks: Generate checklist from template
     c. Notifications: Alert assigned crew
3. Response → Frontend refreshes job view
```

### Pattern 4: Availability Check (Read-Heavy)
```
User Action: Admin opens crew allocation screen

1. Frontend → GET /resources/availability?date_from=X&date_to=Y
2. API Gateway → Authenticate, resolve tenant
3. Resource Management Service:
   - Check cache (Redis) for date range
   - If miss: Query ResourceAssignment table filtered by tenant + dates
   - Build availability matrix (crew × dates)
   - Cache result (TTL: 5 minutes)
4. Response → Frontend renders calendar heatmap
```

## Multi-Tenancy Strategy

### Recommended: Row-Level Security (RLS) with SQLAlchemy Filters

**Why Row-Level Over Schema-Per-Tenant:**
- Simpler deployment (single DB connection pool)
- Easier backups and migrations
- Better resource utilization for small tenants
- PostgreSQL RLS policies provide defense-in-depth
- SQLAlchemy can enforce at ORM level + DB level

**Implementation:**

#### 1. Database Layer (PostgreSQL RLS)
```sql
-- Enable RLS on all tenant-isolated tables
ALTER TABLE jobs ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation ON jobs
  USING (tenant_id = current_setting('app.current_tenant')::uuid);

-- Set tenant context per request
SET app.current_tenant = '<tenant_uuid>';
```

#### 2. ORM Layer (SQLAlchemy)
```python
# Base model with tenant filtering
class TenantScopedModel(Base):
    __abstract__ = True
    tenant_id = Column(UUID, nullable=False, index=True)
    
    @declared_attr
    def __table_args__(cls):
        return (Index(f'ix_{cls.__tablename__}_tenant', 'tenant_id'),)

# Session factory with tenant context
def get_db_session(tenant_id: UUID):
    session = SessionLocal()
    session.execute(text(f"SET app.current_tenant = '{tenant_id}'"))
    return session

# Query filter automatically applied
class JobRepository:
    def __init__(self, db: Session, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id
    
    def get_all(self):
        # tenant_id filter automatic via RLS + base query filter
        return self.db.query(Job).filter(Job.tenant_id == self.tenant_id).all()
```

#### 3. API Layer (FastAPI Dependency)
```python
async def get_current_tenant(token: str = Depends(oauth2_scheme)) -> UUID:
    payload = jwt.decode(token, SECRET_KEY)
    return payload['tenant_id']

@app.get("/jobs")
async def list_jobs(
    tenant_id: UUID = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    # tenant_id automatically enforced
    repo = JobRepository(db, tenant_id)
    return repo.get_all()
```

**Defense Layers:**
1. JWT token contains `tenant_id` claim
2. API dependency extracts and validates tenant
3. SQLAlchemy queries include `tenant_id` filter
4. PostgreSQL RLS provides final enforcement

**Critical Tables with Tenant Isolation:**
- tenants (no RLS, global)
- users (tenant_id indexed)
- jobs, crew_members, equipment (tenant_id indexed)
- resource_assignments, messages, tasks, files (tenant_id indexed)

**Global/Shared Tables (No Tenant Isolation):**
- System configuration
- Audit logs (tenant_id as dimension, not filter)

### Alternative: Schema-Per-Tenant (When to Consider)
**Use when:**
- Tenants require data sovereignty (separate backups)
- Compliance mandates physical separation
- Tenants have vastly different scale (10-user vs 10,000-user)

**Tradeoffs:**
- More complex migrations (N schemas to update)
- Connection pool per schema or dynamic routing
- Higher operational overhead

**For Duct Tape:** Row-level security recommended unless customer contracts require schema isolation.

## Suggested Build Order

### Phase 1: Foundation (Core Infrastructure)
**Why First:** All features depend on these primitives

1. **Database schema setup** — Tenant model, migration framework (Alembic)
2. **Multi-tenancy middleware** — Tenant resolution from JWT
3. **Authentication service** — User login, JWT issuance, role checks
4. **API gateway skeleton** — FastAPI app structure, CORS, logging

**Validation:** Can create tenant, register admin user, log in, receive JWT

### Phase 2: Job Management (Primary Entity)
**Why Second:** Jobs are the central organizing concept

1. **Job CRUD** — Create, read, update, delete with tenant isolation
2. **Job state machine** — Status transitions (intake → simmer → active → complete)
3. **Job listing/search** — Filters by status, date, search term
4. **Frontend job views** — List, detail, create/edit forms

**Validation:** Can manage full job lifecycle via UI

### Phase 3: Resource Management (Crew + Equipment)
**Why Third:** Jobs need resources to be useful

1. **Crew profile management** — CRUD for crew members with skills/rates
2. **Equipment inventory** — CRUD for owned + rental gear
3. **Resource assignment** — Link crew/equipment to jobs
4. **Conflict detection** — Prevent double-booking
5. **Frontend resource views** — Crew list, equipment list, assignment UI

**Validation:** Can assign crew and gear to jobs, detect conflicts

### Phase 4: Calendar & Availability
**Why Fourth:** Builds on resource assignments

1. **Availability calculation engine** — Given assignments, compute free/busy
2. **Calendar day view** — Single-day schedule per resource
3. **Calendar month view** — Heatmap of utilization
4. **Drag-and-drop rescheduling** — Update assignments via UI

**Validation:** Can visualize resource allocation and reschedule

### Phase 5: Messaging & Real-Time
**Why Fifth:** Requires WebSocket infrastructure

1. **WebSocket gateway setup** — FastAPI WebSocket endpoint with tenant auth
2. **Message persistence** — Thread and message models
3. **Real-time broadcast** — Send to connected clients in same tenant/job
4. **Message history** — Load past messages on thread open
5. **Frontend chat UI** — Slack-like threaded messaging

**Validation:** Can send/receive messages in real-time tied to jobs

### Phase 6: Task Management
**Why Sixth:** Tasks integrate with jobs and messaging

1. **Task CRUD** — Create tasks tied to jobs
2. **Task assignment** — Assign to crew members
3. **Status tracking** — Todo → In Progress → Done
4. **Deadline alerts** — Notify on overdue tasks
5. **Frontend task views** — Checklist, Kanban, or table view

**Validation:** Can create, assign, track tasks to completion

### Phase 7: File Storage
**Why Seventh:** Requires external service integration (S3)

1. **Object storage setup** — S3 bucket or compatible service
2. **File upload endpoint** — Multipart upload with tenant/job context
3. **File download/access** — Signed URLs or direct serve
4. **Metadata storage** — Track files in PostgreSQL
5. **Frontend file UI** — Upload dropzone, file list, download/delete

**Validation:** Can upload briefs/documents to jobs and retrieve

### Phase 8: Email Integration
**Why Eighth:** Nice-to-have, not critical path

1. **Email ingestion** — Webhook or IMAP polling to capture threads
2. **Email-to-job linking** — Attach email references to jobs
3. **Outbound email** — Send notifications via transactional email service
4. **Frontend email view** — Display linked email chains

**Validation:** Can link email threads to jobs and view history

### Phase 9: Crew Portal
**Why Last:** Requires all other features to be useful

1. **Crew-specific views** — My schedule, my jobs, my tasks
2. **Booking confirmation** — Accept/decline assignments
3. **Job brief access** — Read-only view of job details and files
4. **Simplified navigation** — Crew-focused UI (not admin tools)

**Validation:** Crew member can log in, see schedule, confirm bookings

## Cross-Cutting Concerns

### Caching Strategy
**Where to Cache:**
- **Availability calculations** — Redis cache, 5-minute TTL, invalidate on assignment change
- **Crew skill lookups** — In-memory cache, refresh on profile update
- **Job counts by status** — Redis cache, 1-minute TTL

**Don't Cache:**
- Messages (real-time requirement)
- Task status (state changes frequent)
- Job details (consistency critical)

### Background Jobs
**Use Cases:**
- File processing (thumbnail generation, virus scanning)
- Email sending (notifications, digests)
- Report generation (utilization reports, crew stats)
- Data cleanup (old message pruning, archived job compression)

**Tech:** Celery + Redis or FastAPI Background Tasks for lightweight jobs

### Monitoring & Observability
**Key Metrics:**
- API response times per endpoint
- WebSocket connection count per tenant
- Database query performance (slow query log)
- Cache hit/miss rates
- Background job queue depth

**Logging:**
- Structured JSON logs (tenant_id, user_id, request_id on every entry)
- Separate log streams: API access, application errors, security events

### Security Considerations
**Tenant Isolation:**
- Defense-in-depth: JWT validation + ORM filter + RLS policy
- Test tenant leakage in integration tests (attempt cross-tenant access)

**Data Privacy:**
- Hash passwords with Argon2 (bcrypt minimum)
- Encrypt sensitive fields at rest (crew contact details, rates)
- HTTPS only for API (enforce in production)

**Access Control:**
- Admin role: full CRUD on all resources in tenant
- Crew role: read-only on jobs, read/write on own assignments/tasks
- Middleware checks role before allowing write operations

## Scalability Patterns

### At 100 Users (5-10 Tenants)
**Architecture:** Monolith (single FastAPI app)
**Database:** Single PostgreSQL instance (16GB RAM)
**Caching:** Redis (2GB)
**File Storage:** S3 standard
**Hosting:** Single VPS or managed platform (Railway, Render)

### At 1,000 Users (50-100 Tenants)
**Architecture:** Monolith with read replicas
**Database:** Primary + 1 read replica (route reads to replica)
**Caching:** Redis cluster (8GB)
**File Storage:** S3 with CDN (CloudFront)
**Hosting:** Load-balanced app servers (2+ instances)

### At 10,000 Users (500+ Tenants)
**Architecture:** Service split (Job/Resource/Messaging as separate apps)
**Database:** Primary + 2 read replicas, consider sharding by tenant_id
**Caching:** Redis cluster with persistence
**File Storage:** S3 with CDN + edge caching
**Hosting:** Kubernetes or managed container platform
**Async:** Dedicated background job workers (Celery)

### Optimization Triggers
**Split messaging service when:** WebSocket connection count > 10K
**Add read replicas when:** DB read latency > 100ms p95
**Shard database when:** Single-tenant exceeds 50% of DB capacity
**Add CDN when:** File download bandwidth > 1TB/month

## Anti-Patterns to Avoid

### Anti-Pattern 1: Tenant ID in URL Path
**What:** `/api/tenants/{tenant_id}/jobs`
**Why bad:** 
- Exposes tenant IDs to users (security risk)
- Easy to accidentally leak data (user changes URL)
- Breaks if tenant ID changes

**Instead:** Extract tenant from JWT, never from URL
```python
# Good
@app.get("/jobs")
async def list_jobs(tenant_id: UUID = Depends(get_current_tenant)):
    ...

# Bad
@app.get("/tenants/{tenant_id}/jobs")
async def list_jobs(tenant_id: UUID):
    ...
```

### Anti-Pattern 2: Lazy-Loaded Relationships Without Tenant Filter
**What:** SQLAlchemy relationship loads related objects without tenant check
**Why bad:** ORM can fetch cross-tenant data if relationship not filtered
**Instead:** Always define relationship with `primaryjoin` including tenant_id

```python
# Good
class Job(TenantScopedModel):
    assignments = relationship(
        "ResourceAssignment",
        primaryjoin="and_(Job.id == ResourceAssignment.job_id, "
                   "Job.tenant_id == ResourceAssignment.tenant_id)"
    )

# Bad
class Job(TenantScopedModel):
    assignments = relationship("ResourceAssignment", back_populates="job")
```

### Anti-Pattern 3: Storing File Blobs in PostgreSQL
**What:** Large files (briefs, videos) in BYTEA columns
**Why bad:**
- Bloats database (expensive, slow backups)
- Poor streaming performance
- Replication overhead

**Instead:** Store in S3, reference by key in PostgreSQL

### Anti-Pattern 4: Synchronous Email Sending in Request Path
**What:** Sending notification emails during API request
**Why bad:**
- Blocks response (slow)
- Fails if email service down (user sees error)

**Instead:** Queue email jobs, send asynchronously

```python
# Good
@app.post("/jobs/{job_id}/assignments")
async def create_assignment(...):
    assignment = create_resource_assignment(...)
    email_queue.enqueue(send_assignment_notification, assignment.id)
    return assignment

# Bad
@app.post("/jobs/{job_id}/assignments")
async def create_assignment(...):
    assignment = create_resource_assignment(...)
    send_email(assignment.crew.email, "You've been assigned...")  # blocks!
    return assignment
```

### Anti-Pattern 5: God Models (Job Knows Everything)
**What:** Job model has methods for resource allocation, messaging, task creation
**Why bad:**
- Violates single responsibility
- Hard to test
- Tight coupling

**Instead:** Service layer orchestrates, models are data containers

```python
# Good
class JobService:
    def assign_resource(self, job_id, resource_id):
        job = self.job_repo.get(job_id)
        resource = self.resource_repo.get(resource_id)
        if self.availability_service.is_available(resource, job.dates):
            return self.assignment_repo.create(job, resource)

# Bad
class Job:
    def assign_resource(self, resource_id):
        # Job model does DB queries, business logic, etc.
        ...
```

### Anti-Pattern 6: WebSocket Authentication via Query Params
**What:** `/ws?token=xyz` (token in URL)
**Why bad:**
- Logged in server access logs (security risk)
- Cached by proxies/CDNs

**Instead:** Send token in first WebSocket message after connection

```python
# Good
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    auth_msg = await websocket.receive_json()
    tenant_id = verify_token(auth_msg['token'])
    # ... proceed

# Bad
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str):
    tenant_id = verify_token(token)  # token exposed in URL
```

## Technology-Specific Recommendations

### FastAPI Best Practices
1. **Dependency injection for tenant context** — Use `Depends()` for tenant_id extraction
2. **Pydantic models for request/response** — Type safety and automatic validation
3. **APIRouter for service modules** — Separate routers for jobs, resources, messaging
4. **Background tasks for side effects** — Use `BackgroundTasks` for lightweight jobs
5. **Lifespan events for startup/shutdown** — Database connection pool setup/teardown

### PostgreSQL Schema Design
1. **UUID primary keys** — Avoid sequential IDs (harder to guess, better for merges)
2. **Composite indexes** — `(tenant_id, created_at)` for common queries
3. **Partial indexes** — Index only active jobs: `WHERE status != 'complete'`
4. **JSONB for flexible attributes** — Crew skills, equipment specs (query with GIN index)
5. **Timestamp columns** — `created_at`, `updated_at` on all tables (track changes)

### React Frontend Architecture
1. **Context for tenant/user** — Global state via React Context
2. **React Query for API calls** — Caching, refetching, optimistic updates
3. **Component library** — Shadcn/ui or Mantine for dark theme support
4. **WebSocket hook** — Shared `useWebSocket()` for messaging
5. **Route-based code splitting** — Lazy load views to reduce bundle size

## Build Order Dependencies

```
Phase 1 (Foundation)
    ↓
Phase 2 (Job Management) ← All other features depend on jobs
    ↓
Phase 3 (Resource Management) ← Assignments need jobs + resources
    ↓
Phase 4 (Calendar) ← Visualizes assignments
    ↓
Phase 5 (Messaging) ← Independent, can parallel with Phase 6
    ↓
Phase 6 (Tasks) ← Independent, can parallel with Phase 5
    ↓
Phase 7 (Files) ← Needs jobs, can parallel with 5/6
    ↓
Phase 8 (Email) ← Needs jobs, nice-to-have
    ↓
Phase 9 (Crew Portal) ← Needs all features to be useful
```

**Critical Path:** 1 → 2 → 3 → 4 (delivers core value: job + resource scheduling)

**Parallel Tracks After Phase 4:**
- Track A: Messaging (Phase 5)
- Track B: Tasks (Phase 6)
- Track C: Files (Phase 7)

These can be built concurrently if multiple developers available.

## Open Questions for Phase-Specific Research

### Phase 3: Resource Management
- **Conflict detection algorithm:** Naive (O(n) scan) vs indexed (PostgreSQL exclusion constraint)?
- **Availability model:** Store free blocks or derive from assignments?

### Phase 5: Messaging
- **WebSocket scaling:** Single server vs Redis pub/sub for multi-instance?
- **Message retention:** How long to keep messages? Auto-archive or manual?

### Phase 7: File Storage
- **Large file uploads:** Chunked upload for files > 100MB?
- **Virus scanning:** Integrate ClamAV or cloud service (VirusTotal)?

### Phase 9: Crew Portal
- **Mobile app:** PWA sufficient or need native?
- **Offline support:** Service workers for crew on-site without internet?

## Success Metrics

**Architecture is successful if:**
- Tenant isolation tested and verified (zero data leaks)
- API response times < 200ms p95 (excluding file uploads)
- WebSocket messages delivered < 100ms p95
- Database queries use indexes (no sequential scans on large tables)
- New features can be added without modifying > 3 existing files
- Service boundaries clear (no circular dependencies)

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Multi-tenancy | HIGH | Row-level security is standard pattern, well-documented |
| Service boundaries | MEDIUM | Based on domain-driven design principles, not verified with real crew mgmt systems |
| Build order | MEDIUM | Logical dependency analysis, not validated with actual build |
| Scalability thresholds | LOW | Numbers are estimates, need production data to validate |
| PostgreSQL patterns | HIGH | Standard practices from training data |
| FastAPI patterns | MEDIUM | Unable to verify with current Context7 docs |

**Research Gaps:**
- Real-world crew management system case studies (architecture deep dives unavailable)
- Production scale benchmarks for FastAPI + PostgreSQL multi-tenant setups
- Specific conflict detection algorithms used in scheduling systems

**Sources:**
- Architecture patterns: Training data (SaaS multi-tenancy, workforce management systems)
- FastAPI patterns: Training data (unable to verify with official docs)
- PostgreSQL RLS: Training data (standard technique as of PostgreSQL 9.5+)
