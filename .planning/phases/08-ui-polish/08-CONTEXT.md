# Phase 8: UI Polish - Context

**Gathered:** 2026-05-17
**Status:** Ready for planning

<domain>
## Phase Boundary

Full React frontend SPA — dark theme with event production aesthetic, mobile-responsive design, admin dashboard with at-a-glance job/resource overview, and all major views (jobs, crew, equipment, calendar, messages, tasks, files, crew portal). This is v1's only frontend phase — must be usable end-to-end.

</domain>

<decisions>
## Implementation Decisions

### Frontend scope & stack
- Full React SPA with routing — all backend APIs consumed, complete user experience
- Vite + React Router — fast dev server, SPA routing, no SSR needed (authenticated dashboard app)
- Tailwind CSS + shadcn/ui — utility CSS with copy-paste accessible components, fully customizable, dark theme built-in
- Frontend lives in `frontend/` directory alongside `backend/`

### Dark theme & visual identity
- Technical/industrial dark theme — deep charcoal backgrounds (#0a0a0a to #1a1a1a), not gaming/neon
- Accent colors from established job state mapping: intake=blue, simmer=yellow, active=green, complete=grey
- Typography: Inter for body/UI text, JetBrains Mono for data values, counts, timestamps, IDs
- Monospace accents give backstage tech console feel
- Dark only for v1 — no light theme toggle, no system preference detection
- Subtle borders, no heavy shadows — clean industrial aesthetic

### Admin dashboard layout
- Bento grid layout — asymmetric card grid, micheledu-inspired data-viz storytelling
- Large card: upcoming jobs (next 7 days) with state color coding
- Medium card: crew availability today (who's free/booked/unavailable)
- Stat cards: active job count, pending assignments, unread messages, equipment utilization
- Top navbar: GT logo + user menu + notification badge
- Collapsible sidebar: Dashboard, Jobs, Crew, Equipment, Calendar, Messages navigation
- Sidebar collapses to icons on mobile

### Mobile responsive approach
- Responsive breakpoints via Tailwind — same React app, not separate mobile views
- Sidebar → hamburger menu on mobile
- Bento grid → single column stack on mobile
- Tables → card layout on mobile
- Crew portal views prioritized for mobile (crew check schedule on phones)
- Admin dashboard secondary on mobile (admins use desktop)

### Claude's Discretion
- Exact Tailwind color palette values (beyond job state colors)
- shadcn/ui component customization details
- Calendar view implementation (FullCalendar vs custom)
- WebSocket reconnection UI patterns
- Loading skeleton designs
- Error/empty state visual patterns
- Form validation UX patterns
- File upload progress UI

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

No external specs — requirements fully captured in decisions above and in `.planning/REQUIREMENTS.md` (UI-01, UI-02, UI-03).

### Design preferences
- `~/.claude/skills/frontend-design/design-references/micheledu-patterns.md` — Preferred design patterns (bento grids, monospace accents, dashed hover borders, asymmetric masonry)

### Backend API reference (all endpoints to consume)
- `backend/app/main.py` — All registered routers and endpoint prefixes
- `backend/app/api/v1/jobs.py` — Job CRUD + search + state transitions
- `backend/app/api/v1/crew.py` — Crew CRUD + search + ratings + availability + skills matrix
- `backend/app/api/v1/equipment.py` — Equipment CRUD + condition tracking
- `backend/app/api/v1/assignments.py` — Crew/equipment assignment + conflict detection
- `backend/app/api/v1/calendar.py` — Calendar events + per-resource views + availability
- `backend/app/api/v1/messages.py` — Job-scoped messaging
- `backend/app/api/v1/websocket.py` — Real-time WebSocket delivery
- `backend/app/api/v1/tasks.py` — Task CRUD + state transitions
- `backend/app/api/v1/files.py` — File upload/serve/delete
- `backend/app/api/v1/notifications.py` — Badge counts
- `backend/app/api/v1/portal.py` — Crew portal (dashboard, job detail, confirm/decline, profile)
- `backend/app/api/v1/ical.py` — iCal token management
- `backend/app/api/v1/auth.py` — Login/register/verify/reset

### Schema reference
- `backend/app/schemas/` — All Pydantic response schemas (defines API contracts for frontend)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- No existing frontend code — this phase creates the entire frontend from scratch
- Backend API is complete with 15+ routers providing all data
- shadcn/ui provides ready-made dark theme components

### Established Patterns
- All backend endpoints follow RESTful conventions with consistent response schemas
- JWT auth via httpOnly cookies (set by backend, frontend just calls /api/v1/auth/login)
- WebSocket at /ws?token={jwt} for real-time messages
- File serving at /api/v1/files/{id}/download

### Integration Points
- Frontend at `frontend/` connects to backend at localhost:8000 (dev) or same-origin (prod)
- CORS already configured in backend main.py
- Auth flow: POST /auth/login → httpOnly cookie set → subsequent requests auto-include cookie
- WebSocket needs JWT token extracted from auth state for connection

</code_context>

<specifics>
## Specific Ideas

- Dashboard should feel like a "backstage tech console" — functional, data-dense, professional
- micheledu-inspired: "dashboard as interface", show-don't-tell, asymmetric card layouts
- Dashed hover borders on interactive elements
- Monospace for all numeric data (counts, dates, times, IDs)

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 08-ui-polish*
*Context gathered: 2026-05-17*
