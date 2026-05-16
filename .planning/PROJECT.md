# Duct Tape

## What This Is

A SaaS crew and resource management platform for event production companies. Duct Tape gives production managers a single place to manage the full lifecycle of jobs — from ad-hoc intake through resourcing (crew + equipment), coordination (messaging, files, tasks), and delivery. Crew members log in to see their schedule, confirm bookings, and access briefs.

## Core Value

When a job ignites, a production manager can instantly see who's available, what gear is free, and assign resources — replacing the current workflow of cross-referencing spreadsheets, memory, and scattered text/email threads.

## Requirements

### Validated

- [x] Multi-tenant SaaS with proper auth (admin + crew roles) — Validated in Phase 1: Foundation & Multi-Tenancy
- [x] Job management with full lifecycle (intake → simmer → active → complete) — Validated in Phase 2: Job Management
- [x] Crew profiles (skills, rates, availability, past jobs, reliability rating, contact details) — Validated in Phase 3: Resource Management
- [x] Equipment tracking (owned inventory) — Validated in Phase 3: Resource Management
- [x] Resource allocation — assign crew and gear to jobs with conflict detection — Validated in Phase 3: Resource Management

### Active

- [ ] Ad-hoc job intake from multiple sources (email, text, meetings)
- [ ] Deep crew bench support (15-30+ freelancers per tenant)
- [ ] Equipment tracking (hired/rented gear — rental management deferred to v2)
- [ ] Availability calendar — day and month views showing crew/gear bookings
- [ ] Threaded messaging tied to jobs (Slack-like secure messaging)
- [ ] Task assignment with deadlines, priority levels, and expected delivery times
- [ ] File sharing — briefs, runsheets, photos, videos, documents
- [ ] Email chain linking — attach/reference email threads to jobs
- [ ] Crew-facing portal — view schedule, confirm bookings, access job briefs
- [ ] Dark theme, event production focused UI

### Out of Scope

- Mobile native app — web-first, responsive design handles mobile
- Video calling/conferencing — use existing tools (Zoom, etc.)
- Accounting/invoicing — integrate with existing tools later
- Public-facing client portal — internal crew tool only for v1

## Context

- Inspired by Show Division Crew (shift scheduling app for production companies) but significantly expanded
- Current workflow: jobs arrive ad-hoc, tracked across spreadsheets + memory + text messages + email
- Pain point: resourcing staff and equipment when jobs go live — no single source of truth
- Jobs have unpredictable lifecycles — can sit dormant for weeks then suddenly require immediate action
- When a job "ignites," both messages and tasks snowball together, making it hard to separate decisions from action items
- Equipment is a mix of owned gear (needs availability tracking) and hired gear (needs rental management)
- Crew members are mostly freelancers — need to track their skills, rates, and reliability across jobs

## Constraints

- **Stack**: FastAPI (Python) backend + React frontend + PostgreSQL
- **Deployment**: Cloud-hosted (VPS or managed platform) — must be accessible remotely
- **Scale**: Multi-tenant from day one — designed as a product, not a personal tool
- **Auth**: Proper authentication with role-based access (admin vs crew)
- **Design**: Dark theme, production-industry aesthetic — not generic SaaS

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| FastAPI + React + PostgreSQL | Matches builder's expertise, proven stack for SaaS | — Pending |
| Multi-tenant SaaS from day one | Product ambition, not just a personal tool | — Pending |
| Admin + crew login (not full collaboration) | Admin controls resourcing, crew confirms/views | — Pending |
| Full loop for v1 (not MVP slice) | Won't get daily use unless jobs + crew + gear + messaging + files all work together | — Pending |
| Cloud-deployed | Multiple users need remote access | — Pending |

---
*Last updated: 2026-05-16 after Phase 3 completion*
