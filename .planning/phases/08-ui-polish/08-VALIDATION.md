---
phase: 8
slug: ui-polish
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-05-17
---

# Phase 8 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Vitest + React Testing Library |
| **Config file** | `frontend/vitest.config.ts` |
| **Quick run command** | `cd frontend && npx vitest run --reporter=verbose` |
| **Full suite command** | `cd frontend && npx vitest run --reporter=verbose` |
| **Estimated runtime** | ~10 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd frontend && npx vitest run`
- **After every plan wave:** Run full suite
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| *Populated during planning* | | | | | | | |

---

## Wave 0 Requirements

- [ ] Vite + React + TypeScript project bootstrapped
- [ ] Tailwind CSS + shadcn/ui configured with dark theme
- [ ] Vitest + React Testing Library configured

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Dark theme renders correctly in browser | UI-01 | Visual appearance | Open in browser, verify dark backgrounds, accent colors, typography |
| Mobile responsive layout on phone | UI-02 | Device-specific rendering | Open on mobile or Chrome DevTools mobile mode, verify sidebar collapse, grid stack |
| Dashboard data displays correctly | UI-03 | E2E with backend | Start backend + frontend, login as admin, verify dashboard shows real data |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
