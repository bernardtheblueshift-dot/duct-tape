---
phase: 08-ui-polish
plan: 03
subsystem: frontend-dashboard
tags:
  - ui
  - dashboard
  - bento-grid
  - dark-theme
  - responsive
dependency_graph:
  requires:
    - 08-01-frontend-foundation
    - 08-02-app-shell
  provides:
    - admin-dashboard-view
    - dashboard-components
    - bento-grid-pattern
  affects:
    - router-index-route
key_files:
  created:
    - frontend/src/components/features/StatCard.tsx
    - frontend/src/components/features/JobStateBadge.tsx
    - frontend/src/components/features/UpcomingJobsList.tsx
    - frontend/src/components/features/CrewAvailabilityCard.tsx
    - frontend/src/hooks/useDashboard.ts
    - frontend/src/pages/Dashboard.tsx
  modified:
    - frontend/src/App.tsx
decisions:
  - key: Bento grid responsive breakpoints
    decision: "4-col on lg, 2-col on md, 1-col on mobile with asymmetric card spanning (2x2 large, 2x1 medium)"
    rationale: "Micheledu pattern from design references; mobile-first responsive stacking"
  - key: Dashboard data aggregation hook
    decision: "Single useDashboard hook aggregates all dashboard queries (jobs, availability, notifications, equipment)"
    rationale: "Centralized data fetching logic simplifies component code, enables derived stats calculation"
  - key: 7-day upcoming jobs filter
    decision: "Filter jobs to next 7 days, exclude complete state, max 10 displayed"
    rationale: "Focused near-term view for production managers, avoids overwhelming with full backlog"
  - key: Equipment utilization metric
    decision: "Calculate as (total assigned quantity / total inventory quantity) * 100"
    rationale: "Simple resource utilization indicator, no individual item tracking needed for v1"
metrics:
  duration: 140s
  tasks_completed: 2
  files_created: 6
  files_modified: 1
  commits: 2
  completed_at: "2026-05-17"
tech_stack:
  added:
    - lucide-react icons (Briefcase, UserCheck, Mail, Wrench)
    - date-fns format/isAfter/isBefore/addDays
  patterns:
    - React Query for dashboard data aggregation
    - Custom hooks for data composition
    - Bento grid CSS Grid layout
    - Monospace font for all numeric values
    - Job state color coding via CSS variables
---

# Phase 08 Plan 03: Admin Dashboard Summary

**One-liner**: Admin dashboard with bento grid layout showing upcoming jobs (7-day, state-colored), crew availability (stacked bar), and 4 metric cards

## What Was Built

### Reusable Dashboard Components (Task 1)

**StatCard** (`frontend/src/components/features/StatCard.tsx`):
- Reusable metric card with label, monospace value, icon, optional trend
- Dark theme styling with border-border, bg-surface
- Hover state transitions on icon and border

**JobStateBadge** (`frontend/src/components/features/JobStateBadge.tsx`):
- Color-coded badge for job states using CSS variables
- intake=blue (#3b82f6), simmer=yellow (#eab308), active=green (#22c55e), complete=grey (#6b7280)
- 20% opacity background, full opacity text, monospace uppercase label

**UpcomingJobsList** (`frontend/src/components/features/UpcomingJobsList.tsx`):
- Filters jobs to next 7 days, excludes complete state, max 10 displayed
- Each row: state badge, truncated title (40 chars), venue, date/time, crew count
- Dashed bottom borders (micheledu pattern)
- Click-to-navigate to job detail
- Sorts by scheduled_start ascending
- Empty state: "No upcoming jobs"

**CrewAvailabilityCard** (`frontend/src/components/features/CrewAvailabilityCard.tsx`):
- Aggregates today's crew availability from bulk query
- Displays free/booked/unavailable counts in monospace with state colors
- Horizontal stacked bar visualization (green/blue/grey segments)
- Lists first 5 crew with status dot indicators
- Loading skeleton while data fetching

### Dashboard Page with Bento Grid (Task 2)

**useDashboard hook** (`frontend/src/hooks/useDashboard.ts`):
- Aggregates 4 React Query calls: jobs, crew availability, notifications, equipment
- Calculates derived stats: activeJobCount, equipmentUtilization
- 30-second refetch interval for notification counts
- Returns unified loading state

**DashboardPage** (`frontend/src/pages/Dashboard.tsx`):
- CSS Grid layout: `grid-cols-1 md:grid-cols-2 lg:grid-cols-4`
- Large card (lg:col-span-2 lg:row-span-2): Upcoming Jobs list
- Medium card (lg:col-span-2): Crew Availability with stacked bar
- 4 stat cards: Active Jobs, Pending Assignments, Unread Messages, Equipment In Use
- Page header with monospace comment syntax: `// overview`
- All numeric values in JetBrains Mono font

**Router integration** (`frontend/src/App.tsx`):
- Index route now renders DashboardPage instead of StubPage
- Maintains protected route wrapper

## Architecture Decisions

### Bento Grid Responsive Pattern

**Decision**: Asymmetric grid with 4 columns on large screens, 2 on medium, 1 on mobile.

**Why**: Micheledu-inspired design pattern from `.claude/skills/frontend-design/design-references/micheledu-patterns.md`. Creates visual hierarchy with large upcoming jobs card (2x2 span) and medium availability card (2x1 span).

**Trade-off**: More complex CSS Grid span rules vs simpler uniform grid, but delivers the "dashboard as interface" aesthetic from design references.

### Single Data Hook for Dashboard

**Decision**: useDashboard hook encapsulates all queries and derived calculations.

**Why**: Components stay presentational, data logic centralized, easier to test and mock.

**Trade-off**: Hook is tightly coupled to dashboard needs vs more granular hooks per widget. Acceptable for v1 dashboard, can extract if other pages need same queries.

### 7-Day Upcoming Jobs Window

**Decision**: Filter to jobs with scheduled_start in next 7 days, exclude complete state.

**Why**: Production managers need near-term focus, not full backlog. 7 days balances advance planning with manageable list length.

**Trade-off**: Longer-term jobs invisible from dashboard vs overwhelming list. Accepted because Jobs list page will show full backlog.

### Equipment Utilization Calculation

**Decision**: `(assigned quantity / total quantity) * 100` across all equipment.

**Why**: Simple single-number resource utilization metric. No per-item tracking needed for v1.

**Trade-off**: Aggregate percentage vs per-category breakdown. Simpler metric sufficient for high-level dashboard, detailed equipment page will show category view.

## Deviations from Plan

**Auto-fixed Issues**: None

## Requirements Satisfied

- **UI-01** (Dark Theme): All components use dark theme CSS variables (#0a0a0a background, #1a1a1a surface, job state colors)
- **UI-03** (Admin Dashboard): Dashboard page with bento grid layout, upcoming jobs, crew availability, metric cards

## Testing Notes

**Manual verification needed**:
1. Start backend and frontend dev servers
2. Login as admin user
3. Verify dashboard renders bento grid layout
4. Check upcoming jobs list shows next 7 days (create test jobs if needed)
5. Verify crew availability bar chart displays correctly
6. Check stat cards show correct counts
7. Test mobile responsive layout (single column stack)
8. Verify job state badge colors match CSS variables
9. Click job row to navigate to detail page

**Known limitations**:
- No skeleton loading states for stat cards (only crew availability card)
- Equipment utilization shows 0% if no equipment in database
- Upcoming jobs list empty if no jobs scheduled in next 7 days

## What Changed

### Task 1: Dashboard Components
- Created StatCard.tsx (reusable metric card)
- Created JobStateBadge.tsx (color-coded state badge)
- Created UpcomingJobsList.tsx (7-day job list with filters)
- Created CrewAvailabilityCard.tsx (today's availability + bar chart)
- Commit: 9be2add

### Task 2: Dashboard Page
- Created useDashboard.ts hook (4 queries + derived stats)
- Created Dashboard.tsx page (bento grid layout)
- Updated App.tsx router (index route now renders DashboardPage)
- Fixed unused variable in UpcomingJobsList.tsx
- Commit: 301b465

## Self-Check

Verifying created files exist:

```bash
[ -f "/Users/operator/projects/duct-tape/frontend/src/components/features/StatCard.tsx" ] && echo "FOUND: StatCard.tsx" || echo "MISSING: StatCard.tsx"
[ -f "/Users/operator/projects/duct-tape/frontend/src/components/features/JobStateBadge.tsx" ] && echo "FOUND: JobStateBadge.tsx" || echo "MISSING: JobStateBadge.tsx"
[ -f "/Users/operator/projects/duct-tape/frontend/src/components/features/UpcomingJobsList.tsx" ] && echo "FOUND: UpcomingJobsList.tsx" || echo "MISSING: UpcomingJobsList.tsx"
[ -f "/Users/operator/projects/duct-tape/frontend/src/components/features/CrewAvailabilityCard.tsx" ] && echo "FOUND: CrewAvailabilityCard.tsx" || echo "MISSING: CrewAvailabilityCard.tsx"
[ -f "/Users/operator/projects/duct-tape/frontend/src/hooks/useDashboard.ts" ] && echo "FOUND: useDashboard.ts" || echo "MISSING: useDashboard.ts"
[ -f "/Users/operator/projects/duct-tape/frontend/src/pages/Dashboard.tsx" ] && echo "FOUND: Dashboard.tsx" || echo "MISSING: Dashboard.tsx"
```

Verifying commits exist:

```bash
git log --oneline --all | grep -q "9be2add" && echo "FOUND: 9be2add" || echo "MISSING: 9be2add"
git log --oneline --all | grep -q "301b465" && echo "FOUND: 301b465" || echo "MISSING: 301b465"
```

## Self-Check: PASSED

All files created and commits exist.
