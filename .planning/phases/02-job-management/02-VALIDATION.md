---
phase: 2
slug: job-management
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-05-16
---

# Phase 2 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x |
| **Config file** | `backend/pytest.ini` |
| **Quick run command** | `cd backend && python -m pytest tests/test_jobs_crud.py tests/test_job_transitions.py -x -q` |
| **Full suite command** | `cd backend && python -m pytest tests/ -v --tb=short` |
| **Estimated runtime** | ~10 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd backend && python -m pytest tests/ -x -q`
- **After every plan wave:** Run `cd backend && python -m pytest tests/ -v --tb=short`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 2-01-01 | 01 | 1 | JOBS-04 | unit | `pytest tests/test_job_transitions.py -k test_job_state_enum` | ❌ W0 | ⬜ pending |
| 2-01-02 | 01 | 1 | JOBS-06 | unit | `python -c "from app.schemas.job import JobResponse"` | ❌ W0 | ⬜ pending |
| 2-01-03 | 01 | 1 | JOBS-01 | unit | `alembic upgrade head` | ❌ | ⬜ pending |
| 2-02-01 | 02 | 2 | JOBS-01,02,03 | integration | `pytest tests/test_jobs_crud.py -v` | ❌ W0 | ⬜ pending |
| 2-02-02 | 02 | 2 | JOBS-01 | integration | `python -c "from app.main import app"` | ❌ | ⬜ pending |
| 2-03-01 | 03 | 2 | JOBS-05 | unit | `pytest tests/test_job_transitions.py -k test_state_machine` | ❌ W0 | ⬜ pending |
| 2-03-02 | 03 | 2 | JOBS-05 | integration | `pytest tests/test_job_transitions.py -v` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending / ✅ green / ❌ red / ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `backend/tests/test_jobs_crud.py` — stubs for CRUD endpoint tests
- [ ] `backend/tests/test_job_transitions.py` — stubs for state transition tests
- [ ] Existing `backend/tests/conftest.py` covers fixtures (from Phase 1)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Job list UI placeholder sections | JOBS-06 | Visual verification of placeholder sections | GET /api/v1/jobs/{id} — verify response includes empty crew/gear/messages/tasks/files arrays |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
