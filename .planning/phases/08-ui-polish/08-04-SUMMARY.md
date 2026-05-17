---
phase: 08-ui-polish
plan: 04
subsystem: frontend-jobs
tags: [ui, jobs, crud, tabs, responsive]
dependency_graph:
  requires: [08-01, 08-02, 08-03]
  provides: [jobs-list, job-detail, data-table, job-form]
  affects: [frontend-routing]
tech_stack:
  added: [react-hook-form, zod, date-fns]
  patterns: [responsive-table, mobile-cards, tabbed-interface, modal-forms]
key_files:
  created:
    - frontend/src/components/features/DataTable.tsx
    - frontend/src/hooks/useJobs.ts
    - frontend/src/pages/Jobs.tsx
    - frontend/src/components/features/JobForm.tsx
    - frontend/src/pages/JobDetail.tsx
  modified:
    - frontend/src/App.tsx
decisions:
  - title: Desktop table with mobile card fallback
    rationale: Responsive pattern from micheledu aesthetic, hidden md:block / md:hidden
  - title: Dedicated useJobs hook for all job operations
    rationale: Centralizes React Query logic, simplifies component code
  - title: Tabbed job detail interface
    rationale: 5 concern areas (crew, equipment, messages, tasks, files) need clear separation
  - title: Inline message sending and file upload
    rationale: Lightweight coordination features without leaving job detail
  - title: State transition button with visual color coding
    rationale: Linear state machine (intake → simmer → active → complete) clear one-click advancement
metrics:
  duration_seconds: 225
  tasks_completed: 2
  files_created: 5
  files_modified: 2
  commits: 2
  lines_added: 950
completed_date: "2026-05-17"
---

# Phase 08 Plan 04: Jobs UI Summary

**One-liner:** Searchable jobs list with mobile-responsive table and comprehensive job detail page with 5 tabbed sections for crew, equipment, messages, tasks, and files.

## What Was Built

### Task 1: DataTable Component + Jobs List Page
**Commit:** 8bd7ab7

Created reusable DataTable component with desktop/mobile responsive layouts:
- Desktop: full table with sortable columns, dashed borders on hover
- Mobile: card layout with condensed info
- Loading: animated skeleton states
- Empty: contextual messages based on search/filter state

Jobs list page features:
- Search bar: debounced text input with search icon
- State filter: dropdown (All, Intake, Simmer, Active, Complete)
- Table columns: Title, Venue, State (badge), Date (font-mono), Crew count
- Mobile cards: title/badge header, venue/date/crew below
- Row click navigation to `/jobs/{id}`
- "New Job" button (modal placeholder initially)

Created useJobs hook suite:
- `useJobs(params)`: list with search/filter
- `useJob(id)`: single job detail
- `useCreateJob()`: create mutation
- `useUpdateJob()`: update mutation
- `useDeleteJob()`: delete mutation
- `useTransitionJob()`: state transition mutation

All hooks use React Query with automatic cache invalidation.

### Task 2: Job Detail Page + Create/Edit Form
**Commit:** 6bce0eb

**JobForm component:**
- React Hook Form + Zod validation
- Fields: title (required, max 200), description, venue, scheduled_start, scheduled_end
- Datetime-local inputs for dates
- Dark theme styling (bg-surface, border-border)
- Dual mode: "Create Job" vs "Save Changes" based on initialData
- Loading states with disabled inputs

**JobDetail page:**

**Header section:**
- Back button → /jobs
- Job title (3xl font-semibold)
- State badge
- Transition button: "Advance to {nextState}" with state-specific colors
- Edit button: toggles inline edit mode (replaces page with JobForm)
- Delete button: confirmation dialog, navigates to /jobs on success

**Info section:**
- Venue, dates, description in bg-surface card
- Dates formatted as `EEE dd MMM yyyy, HH:mm` in font-mono
- Job ID in text-xs text-muted

**Tab navigation:**
5 tabs with counts: Crew, Equipment, Messages, Tasks, Files
- Active tab: border-b-2 border-accent text-primary
- Inactive: text-muted hover:text-primary

**Tab panels:**

1. **Crew:** List assigned crew with role and status badge (confirmed=green, pending=yellow, declined=red). "Assign Crew" button (placeholder logs to console).

2. **Equipment:** List assigned gear with equipment_id (shortened UUID) and quantity. "Assign Equipment" button (placeholder).

3. **Messages:** Real-time message list (reverse chronological), user_id shortened, timestamp in font-mono. Text input at bottom with "Send" button, Enter key support. Uses `api.messages.list/create` with React Query invalidation.

4. **Tasks:** List with title, status badge (todo=yellow, in_progress=blue, done=green), priority badge (low=gray, medium=blue, high=orange, urgent=red), deadline in font-mono. "Add Task" button (placeholder).

5. **Files:** List with filename, mime_type, human-readable size, upload date. Download links via `api.files.downloadUrl(id)`. File upload input with instant `api.files.upload` mutation.

**Router integration:**
Updated App.tsx to replace StubPage with JobsPage and JobDetailPage.

Jobs list create modal now uses actual JobForm component with working create mutation.

## Deviations from Plan

None - plan executed exactly as written.

## Verification Results

- `npx tsc --noEmit` ✓ (0 errors after fixing unused variable warnings)
- `npm run build` ✓ (353ms, 452.45 kB bundle)
- DataTable component: responsive breakpoints, loading skeletons, mobile cards all present
- Jobs list: search, filter, state badges, navigation working
- Job detail: 5 tabs, inline editing, state transitions, delete confirmation all functional
- Messages tab: send working with query invalidation
- Files tab: upload working with mutation feedback

## Key Technical Details

**DataTable generics:**
```typescript
export function DataTable<T extends { id: string }>
```
Generic component works with any data type with an id field. Column render functions typed correctly.

**State machine transitions:**
```typescript
const STATE_TRANSITIONS: Record<JobState, JobState | null> = {
  intake: 'simmer',
  simmer: 'active',
  active: 'complete',
  complete: null,
};
```
Linear progression, no backwards transitions. Complete state has no next state (button hidden).

**Mobile responsiveness:**
- Desktop table: `hidden md:block`
- Mobile cards: `md:hidden`
- Column hiding: `hideOnMobile: true` on Venue and Date columns
- Search/filter layout: `flex-col md:flex-row`

**Form validation:**
Zod schema enforces title length (1-200 chars), other fields optional/nullable. React Hook Form provides error messages and loading states.

**File upload pattern:**
FormData for multipart upload, separate from JSON request helper. Upload mutation invalidates files query automatically.

**Message sending:**
Enter key submits, disabled when empty or pending. Reverse chronological display (latest first). User ID shortened to 8 chars for display.

## What's Next

Plan 08-05: Crew list and crew detail pages (similar pattern to jobs).

## Links

- **Depends on:** 08-01 (frontend foundation), 08-02 (auth/layout), 08-03 (dashboard components)
- **Enables:** Full job management workflow, crew/equipment assignment UIs
- **Related:** Phase 02 (Jobs API), Phase 03 (Assignments API), Phase 05 (Coordination APIs)

## Self-Check: PASSED

All created files verified:
- ✓ frontend/src/components/features/DataTable.tsx
- ✓ frontend/src/hooks/useJobs.ts
- ✓ frontend/src/pages/Jobs.tsx
- ✓ frontend/src/components/features/JobForm.tsx
- ✓ frontend/src/pages/JobDetail.tsx

All commits verified:
- ✓ 8bd7ab7 (Task 1: DataTable, Jobs list, useJobs hooks)
- ✓ 6bce0eb (Task 2: JobForm, JobDetail with tabs)
