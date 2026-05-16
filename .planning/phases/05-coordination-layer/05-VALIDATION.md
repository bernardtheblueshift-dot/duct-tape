---
phase: 5
slug: coordination-layer
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-05-16
---

# Phase 5 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x |
| **Config file** | `backend/pyproject.toml` |
| **Quick run command** | `cd backend && python3 -m pytest tests/ -x -q` |
| **Full suite command** | `cd backend && python3 -m pytest tests/ -v` |
| **Estimated runtime** | ~25 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd backend && python3 -m pytest tests/ -x -q`
- **After every plan wave:** Run `cd backend && python3 -m pytest tests/ -v`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 25 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| *Populated during planning* | | | | | | | |

---

## Wave 0 Requirements

- [ ] `tests/test_messages.py` — stubs for MSG-01 through MSG-04
- [ ] `tests/test_tasks.py` — stubs for TASK-01 through TASK-05
- [ ] `tests/test_files.py` — stubs for FILE-01 through FILE-04
- [ ] `tests/test_websocket.py` — stubs for WebSocket connection and message delivery

*Existing test infrastructure (conftest.py, fixtures) from Phase 1-4 covers framework setup.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| WebSocket real-time delivery in browser | MSG-04 | Needs actual browser WebSocket client | Open two browser tabs, send message in one, verify appears in other |
| File preview renders in browser | FILE-02 | Frontend rendering behavior | Upload image/PDF, verify preview displays correctly |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 25s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
