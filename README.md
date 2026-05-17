# GT

Crew and resource management for event production companies.

When a job ignites, see who's available, what gear is free, and assign resources from one place — replacing spreadsheets, memory, and scattered messages.

## Demo

Seed the database with realistic event production data and start exploring immediately.

### Prerequisites

- Python 3.12+
- Node.js 20+
- PostgreSQL 16
- Redis

### Setup (5 minutes)

```bash
# 1. Database
psql -c "CREATE USER duct_tape_dev WITH PASSWORD 'duct_tape_dev';"
psql -c "CREATE DATABASE duct_tape OWNER duct_tape_dev;"

# 2. Backend
cd backend
cp .env.example .env
pip install -e ".[dev]"
python3 seed.py          # Creates tables + demo data

# 3. Frontend (new terminal)
cd frontend
npm install
```

### Run

```bash
# Terminal 1 — Backend
cd backend && uvicorn app.main:app --reload

# Terminal 2 — Frontend
cd frontend && npm run dev
```

Open http://localhost:5173

### Demo Accounts

| Role | Email | Password | What you see |
|------|-------|----------|-------------|
| Admin | `admin@gt.dev` | `admin123` | Dashboard, all jobs, crew, equipment, calendar |
| Crew | `kenji@gt.dev` | `crew123` | Crew portal, assigned jobs only |
| Crew | `yuki@gt.dev` | `crew123` | Different assignments |
| Crew | `mari@gt.dev` | `crew123` | Has availability restrictions |

All crew passwords are `crew123`. Available: kenji, yuki, mari, takeshi, aya, ryo, hana.

### Demo Data

| What | Count | Details |
|------|-------|---------|
| Tenant | 1 | Blue Shift Productions |
| Jobs | 8 | 2 active, 2 simmering, 2 intake, 2 complete |
| Crew | 7 | Skills, rates, ratings, availability patterns |
| Equipment | 12 | Cameras, audio, lighting, video, rigging |
| Crew assignments | 18 | Mix of confirmed, pending, declined |
| Equipment assignments | 9 | Across active jobs |
| Messages | 10 | Threaded conversations on active jobs |
| Tasks | 9 | Various statuses and priorities |

### Things to Try

**As Admin (`admin@gt.dev`):**
- Dashboard shows upcoming jobs with state colors, crew availability, stat cards
- Click a job to see crew, equipment, messages, tasks, files tabs
- Create a new job, assign crew, transition states
- Browse crew directory — click a crew member for ratings and availability
- Check the calendar for month/week views
- Add equipment, change condition status

**As Crew (`kenji@gt.dev`):**
- Portal shows your upcoming assignments
- Confirm or decline pending assignments
- View job details and briefs for your gigs
- Update your phone, bio, and weekly availability

**Reseed anytime:**
```bash
cd backend && python3 seed.py
```

---

## Features

- **Job Management** — lifecycle states (intake → simmer → active → complete), search, filtering
- **Crew Profiles** — skills, rates, availability patterns, reliability ratings
- **Equipment Inventory** — quantity tracking, condition monitoring, conflict detection
- **Resource Assignment** — crew confirmation workflow, equipment hard-block, conflict warnings with override
- **Calendar** — month/week views, job state color coding, iCal subscription feeds
- **Messaging** — job-scoped threaded messages, real-time WebSocket delivery
- **Task Management** — assignees, priorities, deadlines, message linking
- **File Sharing** — upload/download with MIME validation, image/PDF preview
- **Notifications** — email on assignment/job changes, in-app badge counts
- **Crew Portal** — mobile-optimized dashboard, confirm/decline, self-service profile
- **Dark Theme** — industrial aesthetic, Inter + JetBrains Mono, bento grid dashboard

## Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI, Python 3.12+, SQLAlchemy 2, Alembic |
| Frontend | React 19, Vite, TypeScript, Tailwind CSS 4, shadcn/ui |
| Database | PostgreSQL 16 with Row-Level Security |
| Real-time | WebSockets (FastAPI native) |
| Email | Celery + SMTP (optional for dev) |
| Auth | JWT (httpOnly cookies), RBAC (admin/crew) |

## Architecture

```
gt/
├── backend/
│   ├── app/
│   │   ├── api/v1/          # REST endpoints (15 routers)
│   │   ├── core/            # Business logic (conflicts, state machines, file storage)
│   │   ├── models/          # SQLAlchemy models with RLS
│   │   ├── schemas/         # Pydantic request/response types
│   │   └── tasks/           # Celery email tasks
│   ├── seed.py              # Demo data generator
│   └── tests/               # pytest integration tests
├── frontend/
│   ├── src/
│   │   ├── components/      # Layout + feature components
│   │   ├── hooks/           # React Query data hooks
│   │   ├── lib/             # API client, auth, WebSocket
│   │   ├── pages/           # Route pages
│   │   └── types/           # TypeScript API types
│   └── ...
└── .planning/               # Project management artifacts
```

### Multi-Tenancy

Every model uses `TenantMixin` with PostgreSQL Row-Level Security. Tenant context is set per-request via `SET LOCAL app.current_tenant_id`, scoped to the transaction. Cross-tenant access is blocked at the database level.

### Auth Flow

1. `POST /api/v1/auth/login` sets httpOnly JWT cookie
2. All subsequent requests include cookie automatically
3. WebSocket auth uses `GET /api/v1/auth/ws-token` (cookies can't be sent over WS)
4. Roles: `admin` (full access) and `crew` (portal + assigned jobs only)

## API Overview

| Route | Purpose |
|-------|---------|
| `/api/v1/auth/*` | Register, login, verify email, reset password |
| `/api/v1/jobs/*` | Job CRUD, search, state transitions |
| `/api/v1/crew/*` | Crew profiles, ratings, availability, skills matrix |
| `/api/v1/equipment/*` | Equipment inventory, condition tracking |
| `/api/v1/assignments/*` | Crew/equipment assignment with conflict detection |
| `/api/v1/calendar/*` | Calendar events, availability, per-resource views |
| `/api/v1/jobs/{id}/messages/*` | Job-scoped messaging |
| `/api/v1/jobs/{id}/tasks/*` | Task management |
| `/api/v1/jobs/{id}/files/*` | File upload/management |
| `/api/v1/notifications/*` | Badge counts |
| `/api/v1/portal/*` | Crew-facing endpoints |
| `/api/v1/ical/*` | iCal token management |
| `/ical/{token}.ics` | Public iCal feed (no auth) |
| `/ws` | WebSocket (real-time messages) |
| `/api/docs` | Interactive API documentation (Swagger) |
