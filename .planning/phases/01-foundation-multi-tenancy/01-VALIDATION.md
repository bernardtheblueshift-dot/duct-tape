---
phase: 1
slug: foundation-multi-tenancy
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-05-15
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x (backend), vitest (frontend) |
| **Config file** | `backend/pyproject.toml` / `frontend/vitest.config.ts` |
| **Quick run command** | `cd backend && python -m pytest tests/ -x -q` |
| **Full suite command** | `cd backend && python -m pytest tests/ -v --tb=short` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd backend && python -m pytest tests/ -x -q`
- **After every plan wave:** Run `cd backend && python -m pytest tests/ -v --tb=short`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 1-01-01 | 01 | 1 | AUTH-06 | unit | `pytest tests/test_models.py` | ❌ W0 | ⬜ pending |
| 1-01-02 | 01 | 1 | AUTH-06 | unit | `pytest tests/test_rls.py` | ❌ W0 | ⬜ pending |
| 1-02-01 | 02 | 1 | AUTH-01 | integration | `pytest tests/test_auth.py::test_signup` | ❌ W0 | ⬜ pending |
| 1-02-02 | 02 | 1 | AUTH-02 | integration | `pytest tests/test_auth.py::test_email_verification` | ❌ W0 | ⬜ pending |
| 1-02-03 | 02 | 1 | AUTH-03 | integration | `pytest tests/test_auth.py::test_login_session` | ❌ W0 | ⬜ pending |
| 1-02-04 | 02 | 1 | AUTH-04 | integration | `pytest tests/test_auth.py::test_password_reset` | ❌ W0 | ⬜ pending |
| 1-02-05 | 02 | 1 | AUTH-07 | unit | `pytest tests/test_auth.py::test_rbac` | ❌ W0 | ⬜ pending |
| 1-03-01 | 03 | 2 | AUTH-05 | integration | `pytest tests/test_invitations.py` | ❌ W0 | ⬜ pending |
| 1-03-02 | 03 | 2 | AUTH-06 | integration | `pytest tests/test_rls.py::test_cross_tenant` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending / ✅ green / ❌ red / ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `backend/tests/conftest.py` — shared fixtures (test DB, tenant factory, auth helpers)
- [ ] `backend/tests/test_models.py` — stubs for database model tests
- [ ] `backend/tests/test_auth.py` — stubs for auth endpoint tests
- [ ] `backend/tests/test_rls.py` — stubs for RLS isolation tests
- [ ] `backend/tests/test_invitations.py` — stubs for invitation tests
- [ ] pytest + httpx + factory-boy installed in dev dependencies

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Email delivery | AUTH-02, AUTH-04, AUTH-05 | Requires real SMTP or mailbox check | Send verification/reset/invite emails, check inbox |
| Browser session persistence | AUTH-03 | Requires browser with cookies | Log in, close tab, reopen — verify still logged in |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
