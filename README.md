# GT

Crew and resource management for event production companies.

When a job ignites, see who's available, what gear is free, and assign resources from one place — replacing spreadsheets, memory, and scattered messages.

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
| Email | Celery + SMTP |
| Auth | JWT (httpOnly cookies), RBAC (admin/crew) |

## Quick Start

### Prerequisites

- Python 3.12+
- Node.js 20+
- PostgreSQL 16
- Redis

### Database Setup

```bash
# Create database and user
psql -c "CREATE USER duct_tape_dev WITH PASSWORD 'duct_tape_dev';"
psql -c "CREATE DATABASE duct_tape OWNER duct_tape_dev;"
```

### Backend

```bash
cd backend
cp .env.example .env    # edit SECRET_KEY for production
pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload
```

Backend runs at http://localhost:8000. API docs at http://localhost:8000/api/docs.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at http://localhost:5173. Proxies API calls to backend automatically.

### Email (Development)

For local email testing, use [MailHog](https://github.com/mailhog/MailHog):

```bash
# macOS
brew install mailhog && mailhog
# View emails at http://localhost:8025
```

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
│   ├── alembic/             # Database migrations
│   └── tests/               # pytest integration tests
├── frontend/
│   ├── src/
│   │   ├── components/      # Layout + feature components
│   │   ├── hooks/           # React Query data hooks
│   │   ├── lib/             # API client, auth, WebSocket
│   │   ├── pages/           # Route pages
│   │   └── types/           # TypeScript API types
│   └── ...
└── .planning/               # GSD project management artifacts
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

## License

Private. Not open source.
