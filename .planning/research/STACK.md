# Technology Stack

**Project:** Duct Tape (Crew Management SaaS)
**Researched:** 2026-05-15
**Overall Confidence:** MEDIUM (limited to API version checks + training data due to web search unavailable)

## Executive Summary

Recommended stack builds on the pre-decided FastAPI + React + PostgreSQL foundation with battle-tested libraries for multi-tenancy, real-time messaging, file handling, and calendar UIs. This is a **conventional modern Python/React SaaS stack** — proven, well-documented, but not cutting-edge.

**Key architectural choices:**
- **Multi-tenancy:** PostgreSQL Row-Level Security (RLS) + SQLAlchemy tenant filtering
- **Real-time:** WebSockets via FastAPI native support + Redis pub/sub for multi-worker broadcast
- **Auth:** JWT tokens with httpOnly cookies, passlib for password hashing
- **File uploads:** Direct S3/R2 with pre-signed URLs (avoid proxying through API)
- **Frontend state:** Zustand (simpler than Redux, more flexible than Context)
- **Styling:** Tailwind CSS (rapid dark theme development)

## Recommended Stack

### Backend Core

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| **FastAPI** | 0.136.1 | API framework | Pre-decided. Async support, automatic OpenAPI docs, Pydantic integration, WebSocket support built-in. **Confidence: HIGH** (verified via GitHub API) |
| **Pydantic** | 2.13.4 | Data validation | FastAPI dependency. v2 is significantly faster than v1. Use for request/response schemas, config validation. **Confidence: HIGH** (verified via GitHub API) |
| **SQLAlchemy** | 2.0.49 | ORM | Industry standard for Python. v2.0 has modern async support, better type hints. Use async mode (`create_async_engine`). **Confidence: HIGH** (verified via GitHub API) |
| **Alembic** | 1.18.4 | Database migrations | SQLAlchemy's migration tool. Essential for multi-tenant schema evolution. **Confidence: HIGH** (verified via PyPI) |
| **Uvicorn** | 0.47.0 | ASGI server | High-performance async server for FastAPI. Use with `--workers` for production. **Confidence: HIGH** (verified via PyPI) |
| **PostgreSQL** | 16+ | Database | Pre-decided. Use v16+ for improved performance and native JSON handling. **Confidence: HIGH** (training data + project constraint) |

### Authentication & Security

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| **PyJWT** | 2.12.1 | JWT tokens | Token-based auth. Use with httpOnly cookies (not localStorage) to prevent XSS. Short-lived access tokens (15min) + refresh tokens. **Confidence: MEDIUM** (verified via PyPI, pattern is training data) |
| **Passlib** | 1.7.4 | Password hashing | Industry standard. Use `bcrypt` backend for password hashing. **Confidence: HIGH** (verified via PyPI) |
| **python-multipart** | 0.0.28 | Form/file parsing | Required for FastAPI file uploads and form data handling. **Confidence: HIGH** (verified via PyPI, FastAPI dependency) |

**Auth pattern (MEDIUM confidence, training data):**
```python
# JWT in httpOnly cookie (not localStorage)
# Access token: 15 min expiry
# Refresh token: 7 day expiry, rotate on use
# Store tenant_id in token claims for RLS filtering
```

### Multi-Tenancy

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| **PostgreSQL RLS** | Built-in | Row-level isolation | Native PostgreSQL feature. Set `app.current_tenant_id` session variable, use RLS policies to filter all queries automatically. Prevents accidental cross-tenant data leaks. **Confidence: MEDIUM** (training data pattern) |
| **SQLAlchemy tenant filter** | N/A (pattern) | Application-level safety net | Add `tenant_id` to all tables, use SQLAlchemy query filters as backup to RLS. Defense in depth. **Confidence: MEDIUM** (training data pattern) |

**Why RLS over schema-per-tenant:**
- Simpler migrations (one schema, not N)
- Better PostgreSQL connection pooling
- Easier to add cross-tenant admin features later
- Standard approach for SaaS with <10K tenants

**When NOT to use RLS:**
- Tenant count >10K (connection pool pressure)
- Tenants need custom schema modifications
- Regulatory compliance requires physical isolation

### Real-Time Messaging

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| **FastAPI WebSockets** | Built-in | WebSocket connections | Native FastAPI support. Use for job-specific message threads. **Confidence: HIGH** (FastAPI docs) |
| **Redis** | 7.4.0 (client) | Pub/sub + session store | Broadcast messages across multiple Uvicorn workers. Also use for storing active WebSocket connections (connection manager). Lightweight, fast. **Confidence: MEDIUM** (verified client version via PyPI, pattern is training data) |
| **Celery** | 5.6.3 | Background tasks | Async task queue for non-real-time operations (email notifications, file processing, report generation). Use Redis as broker. **Confidence: MEDIUM** (verified via PyPI, pattern is training data) |

**Architecture (MEDIUM confidence, training data):**
```
Client WebSocket → Uvicorn worker → Redis pub/sub → All workers → Subscribed clients
Use Redis pub/sub to broadcast messages across workers
Store active connections in Redis (connection manager pattern)
```

**Alternative considered:** Socket.io (rejected — adds unnecessary abstraction over native FastAPI WebSockets)

### File Uploads & Storage

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| **AWS S3 / Cloudflare R2** | N/A (service) | Object storage | Use pre-signed URLs for direct client→S3 uploads (avoid proxying files through FastAPI). R2 has S3-compatible API with zero egress fees. **Confidence: HIGH** (training data + R2 is cost-optimized alternative) |
| **boto3** | Latest | S3 client | AWS SDK for Python. Generate pre-signed POST URLs. **Confidence: HIGH** (standard AWS SDK) |

**Upload flow (HIGH confidence, standard pattern):**
```
1. Client requests upload URL from API
2. API generates pre-signed POST URL (1hr expiry)
3. Client uploads directly to S3/R2
4. Client notifies API of completion
5. API stores file metadata in PostgreSQL
```

**Why pre-signed URLs:**
- No FastAPI memory pressure from large files
- Faster uploads (client → CDN, not client → API → S3)
- Better scalability

### Frontend Core

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| **React** | 19.2.6 | UI framework | Pre-decided. Latest stable version with concurrent features. **Confidence: HIGH** (verified via GitHub API) |
| **Vite** | 8.0.2+ | Build tool | Faster than Create React App, better HMR, simpler config. Industry standard for new React projects in 2025. **Confidence: MEDIUM** (latest release tag unclear from API, training data pattern) |
| **TypeScript** | 5.7+ | Type safety | Essential for medium/large React apps. Catch errors at compile time, better IDE support. **Confidence: HIGH** (training data) |
| **React Router** | 7.15.1 | Client routing | Industry standard for React routing. v7 has improved data loading patterns. **Confidence: HIGH** (verified via npm) |

### Frontend State & Data

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| **TanStack Query** | v5 (latest) | Server state | Best-in-class for API caching, optimistic updates, background refetching. Replaces Redux for server data. Use `useQuery` for reads, `useMutation` for writes. **Confidence: HIGH** (verified latest release exists, training data pattern) |
| **Zustand** | 5.0.13 | Client state | Lightweight state manager for UI state (modals, forms, filters). Simpler than Redux, more flexible than React Context. **Confidence: HIGH** (verified via npm) |
| **WebSocket (native)** | Built-in | Real-time messaging | Use native browser WebSocket API, wrap in React hook. No need for Socket.io. **Confidence: HIGH** (training data) |

**Why NOT Redux:**
- TanStack Query handles server state better
- Zustand is simpler for UI state
- Less boilerplate, faster development

### Frontend UI Components

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| **Tailwind CSS** | 4.3.0 | Styling | Rapid dark theme development, utility-first. Good for production-focused dark UI aesthetic. **Confidence: HIGH** (verified via npm) |
| **Shadcn/ui** | N/A (copy pattern) | Component primitives | Unstyled, accessible React components you copy into your codebase (not installed as dependency). Built on Radix UI. Use for modals, dropdowns, popovers. **Confidence: MEDIUM** (training data pattern) |
| **Radix UI** | Latest | Headless primitives | Accessible component primitives. Shadcn/ui is built on this. **Confidence: MEDIUM** (training data) |
| **Lucide React** | Latest | Icons | Modern icon set, tree-shakeable. Cleaner than Font Awesome. **Confidence: MEDIUM** (training data) |

### Calendar & Scheduling UI

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| **react-big-calendar** | 1.19.4 | Calendar views | Most mature React calendar library. Supports month/week/day views, drag-drop, resource scheduling view. **Confidence: MEDIUM** (verified via npm, training data for features) |
| **date-fns** | Latest | Date utilities | Lightweight, tree-shakeable date library. Better bundle size than Moment.js. Works well with react-big-calendar. **Confidence: MEDIUM** (training data) |

**Alternative considered:**
- **FullCalendar** — More features but commercial license required for resource timeline view ($500+/dev)
- **TUI Calendar** — Less active maintenance, Korean origin (docs can be unclear)

**Why react-big-calendar:**
- Open source, MIT license
- Resource timeline view available
- Well-maintained, large community
- Good TypeScript support

### Data Tables

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| **TanStack Table** | 8.21.3 | Headless table | Best React table library. Headless (bring your own UI), supports sorting, filtering, pagination, row selection. Essential for crew/equipment lists. **Confidence: HIGH** (verified via npm) |

### Development & Testing

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| **pytest** | Latest | Backend testing | Python standard. Use with `pytest-asyncio` for async FastAPI tests. **Confidence: HIGH** (training data) |
| **httpx** | Latest | Test client | Async HTTP client for testing FastAPI endpoints. Better than requests for async. **Confidence: MEDIUM** (training data) |
| **Vitest** | Latest | Frontend testing | Vite-native test runner. Faster than Jest, same API. **Confidence: MEDIUM** (training data) |
| **Playwright** | Latest | E2E testing | Better than Cypress for multi-browser, faster, more reliable. **Confidence: MEDIUM** (training data) |

## Deployment Stack

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| **Docker** | Latest | Containerization | Package app + dependencies. Use multi-stage builds for smaller images. **Confidence: HIGH** (training data) |
| **Docker Compose** | Latest | Local orchestration | Run FastAPI + PostgreSQL + Redis locally. **Confidence: HIGH** (training data) |
| **Fly.io / Railway / Render** | N/A (platforms) | Hosting | Easy deploys, auto-scaling, managed PostgreSQL + Redis. Fly.io has best performance, Railway has simplest UI. **Confidence: MEDIUM** (training data) |
| **Caddy / Nginx** | Latest | Reverse proxy | Automatic HTTPS (Caddy) or manual config (Nginx). Caddy is simpler for SaaS. **Confidence: MEDIUM** (training data) |

**Why NOT Kubernetes:**
- Overkill for SaaS with <100 concurrent users
- Steeper learning curve
- Higher operational overhead

**When to consider Kubernetes:**
- Scale >1000 concurrent users
- Need fine-grained resource control
- Multi-region deployment

## Supporting Libraries

### Backend

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| **python-dotenv** | Latest | Env config | Load `.env` files in development. **Confidence: MEDIUM** |
| **email-validator** | Latest | Email validation | Pydantic email field validation. **Confidence: MEDIUM** |
| **phonenumbers** | Latest | Phone validation | Parse/validate crew phone numbers. **Confidence: MEDIUM** |
| **Pillow** | Latest | Image processing | Generate thumbnails for uploaded images. **Confidence: MEDIUM** |
| **python-slugify** | Latest | URL slugs | Generate slugs from job names. **Confidence: MEDIUM** |

### Frontend

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| **clsx** | Latest | Conditional classes | Merge Tailwind classes conditionally. **Confidence: MEDIUM** |
| **react-hook-form** | Latest | Form handling | Form state + validation. Integrates with Zod for schema validation. **Confidence: MEDIUM** |
| **zod** | Latest | Schema validation | TypeScript-first validation. Use for form schemas. **Confidence: MEDIUM** |
| **react-hot-toast** | Latest | Notifications | Simple toast notifications. Better UX than alerts. **Confidence: MEDIUM** |
| **react-dropzone** | Latest | File uploads | Drag-drop file upload UI. **Confidence: MEDIUM** |

## Anti-Patterns & Rejected Options

### Backend

| Rejected | Why Not | Use Instead |
|----------|---------|-------------|
| **Django** | Monolithic, slower async support, heavier. FastAPI is better for SaaS APIs. | FastAPI |
| **Flask** | Lacks async support, manual OpenAPI docs, older patterns. | FastAPI |
| **GraphQL** | Adds complexity, harder to cache, overkill for CRUD SaaS. REST is sufficient. | REST with FastAPI |
| **MongoDB** | Schema flexibility not needed, harder multi-tenancy, weaker consistency. | PostgreSQL |
| **ORMless (raw SQL)** | More work, error-prone tenant filtering, no migration tooling. | SQLAlchemy |

### Frontend

| Rejected | Why Not | Use Instead |
|----------|---------|-------------|
| **Vue / Svelte** | Smaller ecosystem, React pre-decided. | React |
| **Next.js** | SSR not needed for SaaS admin tool, adds complexity, harder WebSocket integration. | Vite + React Router |
| **Create React App** | Deprecated, slow builds, heavy config. | Vite |
| **Redux** | Verbose, unnecessary with TanStack Query. | TanStack Query + Zustand |
| **MUI / Ant Design** | Heavy bundle size, hard to customize for dark production aesthetic. | Tailwind + Shadcn/ui |
| **FullCalendar Pro** | $500+/dev license for resource timeline. | react-big-calendar (free) |

### Deployment

| Rejected | Why Not | Use Instead |
|----------|---------|-------------|
| **Heroku** | Expensive at scale, less control. | Fly.io / Railway |
| **AWS EC2 (bare)** | Manual scaling, more ops overhead. | Managed platforms (Fly.io, Railway) |
| **Vercel / Netlify** | Frontend-focused, awkward for FastAPI backends. | Fly.io (full-stack) |

## Installation Commands

### Backend

```bash
# Core
pip install fastapi[standard]==0.136.1 uvicorn[standard]==0.47.0
pip install sqlalchemy==2.0.49 alembic==1.18.4 asyncpg  # PostgreSQL async driver
pip install pydantic==2.13.4 pydantic-settings
pip install pyjwt==2.12.1 passlib==1.7.4 bcrypt
pip install python-multipart==0.0.28
pip install redis==7.4.0 celery==5.6.3

# File uploads
pip install boto3

# Supporting
pip install python-dotenv email-validator phonenumbers Pillow python-slugify

# Dev dependencies
pip install pytest pytest-asyncio httpx black ruff
```

### Frontend

```bash
# Create Vite project
npm create vite@latest frontend -- --template react-ts

# Core
npm install react@19.2.6 react-dom@19.2.6
npm install react-router-dom@7.15.1
npm install @tanstack/react-query
npm install zustand@5.0.13

# UI
npm install tailwindcss@4.3.0 postcss autoprefixer
npm install @radix-ui/react-* lucide-react  # Install specific Radix primitives as needed
npm install react-big-calendar@1.19.4 date-fns
npm install @tanstack/react-table@8.21.3

# Forms & validation
npm install react-hook-form zod
npm install clsx react-hot-toast react-dropzone

# Dev dependencies
npm install -D vitest @playwright/test
npm install -D @types/react @types/react-dom
```

## Database Setup

```sql
-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable Row-Level Security on all tenant tables
ALTER TABLE jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE crew_members ENABLE ROW LEVEL SECURITY;
ALTER TABLE equipment ENABLE ROW LEVEL SECURITY;
-- ... repeat for all tenant tables

-- RLS policy example (apply to all tenant tables)
CREATE POLICY tenant_isolation ON jobs
    USING (tenant_id::text = current_setting('app.current_tenant_id', TRUE));

-- Set tenant context in each request (FastAPI middleware)
-- Execute before each query: SET LOCAL app.current_tenant_id = '<tenant_uuid>';
```

## Architecture Notes

### Multi-Tenancy Pattern (MEDIUM confidence)

```python
# FastAPI dependency to set tenant context
async def get_current_tenant(token: str = Depends(oauth2_scheme)):
    tenant_id = decode_jwt(token)["tenant_id"]
    
    # Set PostgreSQL session variable for RLS
    await db.execute(text(f"SET LOCAL app.current_tenant_id = '{tenant_id}'"))
    
    return tenant_id

# Use in routes
@router.get("/jobs")
async def list_jobs(tenant_id: str = Depends(get_current_tenant)):
    # RLS automatically filters by tenant_id
    jobs = await db.execute(select(Job))
    return jobs.all()
```

### WebSocket Connection Manager (MEDIUM confidence)

```python
# Store connections in Redis
# Key: f"ws:{tenant_id}:{job_id}:{user_id}" → connection_id
# Use Redis pub/sub to broadcast messages across workers

class ConnectionManager:
    def __init__(self):
        self.redis = redis.Redis()
        
    async def connect(self, websocket: WebSocket, tenant_id: str, job_id: str, user_id: str):
        await websocket.accept()
        key = f"ws:{tenant_id}:{job_id}:{user_id}"
        self.redis.setex(key, 3600, connection_id)
        
    async def broadcast(self, tenant_id: str, job_id: str, message: dict):
        # Publish to Redis, all workers receive and send to their connected clients
        channel = f"messages:{tenant_id}:{job_id}"
        self.redis.publish(channel, json.dumps(message))
```

### File Upload Flow (HIGH confidence)

```python
# 1. Client requests pre-signed URL
@router.post("/files/upload-url")
async def get_upload_url(filename: str, content_type: str):
    s3_client = boto3.client('s3')
    key = f"{tenant_id}/{job_id}/{uuid4()}/{filename}"
    
    presigned_url = s3_client.generate_presigned_post(
        Bucket='duct-tape-files',
        Key=key,
        ExpiresIn=3600,
        Conditions=[
            ['content-length-range', 0, 100 * 1024 * 1024],  # 100MB max
            {'Content-Type': content_type}
        ]
    )
    
    return presigned_url

# 2. Client uploads directly to S3 using presigned URL

# 3. Client notifies API of completion
@router.post("/files")
async def create_file_record(file_key: str, filename: str, size: int):
    # Store metadata in PostgreSQL
    file_record = File(key=file_key, filename=filename, size=size, ...)
    db.add(file_record)
    await db.commit()
```

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| **Core stack (FastAPI, React, PostgreSQL)** | HIGH | Versions verified via API calls, well-established patterns |
| **Auth (JWT, httpOnly cookies)** | MEDIUM | Pattern from training data, standard but not verified against current best practices |
| **Multi-tenancy (RLS)** | MEDIUM | Training data pattern, widely used but implementation details may vary |
| **WebSockets + Redis** | MEDIUM | Standard pattern from training data, FastAPI WebSocket support is native |
| **File uploads (pre-signed URLs)** | HIGH | Well-documented AWS/S3 pattern, current as of training cutoff |
| **Frontend libraries (TanStack Query, Zustand)** | MEDIUM | Versions verified, patterns from training data |
| **Calendar (react-big-calendar)** | MEDIUM | Version verified, feature set from training data |
| **Deployment (Fly.io, Railway)** | MEDIUM | Training data, platforms active as of Jan 2025 |

**Overall:** This stack is conservative and proven. All components are well-documented and widely used as of early 2025. The main uncertainty is whether web search would have revealed better alternatives for calendar UI or deployment platforms.

## Sources

**Version verification:**
- FastAPI: GitHub API (tag 0.136.1)
- React: GitHub API (tag v19.2.6)
- SQLAlchemy: GitHub API (tag rel_2_0_49)
- Pydantic: GitHub API (tag v2.13.4)
- Alembic, Celery, Redis, PyJWT, Passlib, Uvicorn, python-multipart: PyPI API
- TanStack Table, react-big-calendar, Zustand, Tailwind CSS, React Router: npm registry API

**Patterns and architectural decisions:** Training data (January 2025 cutoff), unable to verify against current 2026 best practices due to web search unavailable.

## Research Gaps

**Unable to verify without web search:**
1. Current best practices for FastAPI multi-tenancy in 2026 (RLS vs other patterns)
2. Alternative calendar libraries released in 2025-2026
3. Emerging real-time messaging patterns (e.g., Server-Sent Events vs WebSockets for this use case)
4. Latest deployment platform comparisons (Fly.io vs Railway vs Render in 2026)
5. React 19-specific state management patterns (concurrent features impact)

**Recommendation:** Validate these areas with Context7 or official docs during implementation phases. The current stack is safe and proven, but may not be cutting-edge.
