---
phase: 08-ui-polish
plan: 05
subsystem: frontend-crew-equipment
tags: [ui, crew-management, equipment-management, react-query, responsive]
dependency_graph:
  requires:
    - 08-01-frontend-foundation
    - 08-04-jobs-list-detail
  provides:
    - crew-directory-ui
    - crew-detail-ui
    - equipment-inventory-ui
    - crew-hooks
    - equipment-hooks
  affects:
    - admin-workflow
    - resource-management
tech_stack:
  added: []
  patterns:
    - DataTable component reuse
    - React Query hooks pattern
    - Inline form editing
    - Mobile-first responsive cards
    - Type-safe API client usage
key_files:
  created:
    - frontend/src/hooks/useCrew.ts
    - frontend/src/hooks/useEquipment.ts
    - frontend/src/pages/Crew.tsx
    - frontend/src/pages/CrewDetail.tsx
    - frontend/src/pages/Equipment.tsx
  modified:
    - frontend/src/App.tsx
decisions:
  - title: Truncated user_id display for crew names
    rationale: V1 has no User name lookup; showing "Crew {short_id}" provides unique identifier without full UUID clutter
    alternatives: Show full email (requires backend join), show full UUID (too long)
    impact: Acceptable for v1, will need User.name field in future iteration
  - title: Inline condition dropdown in table
    rationale: Quick status updates without modal/form overhead; common admin action
    alternatives: Dedicated condition modal, row edit mode only
    impact: Faster workflow for frequent condition updates
  - title: Skills pills with "+N more" truncation
    rationale: Max 3 visible skills prevents table row expansion on desktop; full list available in detail view
    alternatives: Show all skills (wraps rows), tooltip hover (hidden context)
    impact: Cleaner table layout, acceptable UX trade-off
  - title: Archive toggle instead of separate view
    rationale: Admin sometimes needs to see archived crew; toggle simpler than route split
    alternatives: /crew/archived route, filter dropdown
    impact: Single-page UX, fewer routes to maintain
metrics:
  duration: 221s
  completed: 2026-05-17
---

# Phase 08 Plan 05: Crew and Equipment Pages Summary

**One-liner:** Crew directory with skills pills and ratings, crew detail with availability grid, equipment inventory with quick condition updates and inline CRUD

## What Was Built

Implemented crew and equipment resource management pages with responsive layouts and DataTable component reuse.

### Task 1: Crew Directory and Detail Pages

**Created:**
- `frontend/src/hooks/useCrew.ts` — React Query hooks for crew list, detail, ratings, availability, archive operations
- `frontend/src/pages/Crew.tsx` — Crew directory with search, skill filter, archive toggle, skills pills (max 3 visible + "N more"), ratings display, responsive DataTable
- `frontend/src/pages/CrewDetail.tsx` — Crew profile detail with user info, phone, bio, hourly rate, skills pills, ratings history with stars/notes/dates, 7-day availability grid (Mon-Sun with colored dots)

**Key Features:**
- Search bar with debounced text input
- Skill filter dropdown populated from unique crew skills
- Archive toggle (filter out archived by default)
- Skills displayed as pill badges (rounded-full bg-secondary, monospace font)
- Rating display: `{avg} ({count})` in monospace, or "—" if null
- Hourly rate: `$XX` in monospace, or "—" if null
- Mobile card layout: name bold, skills pills, rating + rate on bottom row
- Row click navigates to detail page
- Crew detail: profile card (bg-surface, border, p-6), ratings section with individual rating list, availability grid (7 columns, colored dots for available/unavailable)
- Archive/Unarchive button with confirmation

**Commit:** d249a8b

### Task 2: Equipment Inventory Page

**Created:**
- `frontend/src/hooks/useEquipment.ts` — React Query hooks for equipment list, create, update, delete, quick condition update
- `frontend/src/pages/Equipment.tsx` — Equipment inventory with search, category/condition filters, inline create form, edit/delete actions, quick condition dropdown

**Key Features:**
- Inline create form (toggled by "Add Equipment" button) with fields: name (required), category, quantity (default 1), condition dropdown, serial number, notes
- Search bar with debounced text input
- Category filter dropdown (populated from unique categories)
- Condition filter dropdown (All, Good, Fair, Poor, Maintenance)
- DataTable columns: Name, Category, Qty (monospace), Condition (colored badge dropdown), Serial (monospace text-muted), Actions (edit/delete icons)
- Condition badge colors:
  - good = `bg-job-active/20 text-job-active` (green)
  - fair = `bg-job-simmer/20 text-job-simmer` (yellow)
  - poor = `bg-destructive/20 text-destructive` (red)
  - maintenance = `bg-muted/20 text-muted` (grey)
- Quick condition update: click badge → dropdown select → instant update via `api.equipment.updateCondition()`
- Inline row edit: click edit icon → name field becomes input → save/cancel buttons
- Delete with confirmation dialog
- Mobile card layout: name bold, category below, condition badge + qty on right, serial at bottom (monospace text-xs)

**Commit:** c94fd57

### Router Integration

Updated `frontend/src/App.tsx`:
- Replaced `<StubPage title="Crew" />` with `<CrewPage />`
- Replaced `<StubPage title="Crew Detail" />` with `<CrewDetailPage />`
- Replaced `<StubPage title="Equipment" />` with `<EquipmentPage />`

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] TypeScript unused import errors**
- **Found during:** Task 2 build verification
- **Issue:** Unused type imports in useCrew.ts (CrewRatingCreate, AvailabilityPatternCreate), Crew.tsx (CrewProfileResponse), Equipment.tsx (EquipmentResponse)
- **Fix:** Removed unused imports
- **Files modified:** frontend/src/hooks/useCrew.ts, frontend/src/pages/Crew.tsx, frontend/src/pages/Equipment.tsx
- **Commit:** c94fd57 (included in Task 2)

**2. [Rule 1 - Bug] TypeScript null type error in category filter**
- **Found during:** Task 2 build verification
- **Issue:** `allCategories.map(c => <option value={c}>)` where `c` could be `null` but option value doesn't accept null
- **Fix:** Changed `.filter(Boolean)` to `.filter((c): c is string => c !== null)` type guard
- **Files modified:** frontend/src/pages/Equipment.tsx
- **Commit:** c94fd57 (included in Task 2)

## Verification

- [x] `npm run build` exits 0 (450ms)
- [x] TypeScript compilation passes with no errors
- [x] Crew page imports DataTable, useCrewList, skills pills, rating display, font-mono styling
- [x] CrewDetail page imports useCrew, useCrewRatings, useCrewAvailability, useParams, hourly_rate, skills, grid grid-cols-7 availability
- [x] Equipment page imports DataTable, useEquipmentList, useCreateEquipment, condition badges (good/fair/poor/maintenance), quantity in font-mono
- [x] App.tsx imports CrewPage, CrewDetailPage, EquipmentPage and wires routes correctly

## Self-Check: PASSED

**Created files exist:**
```bash
[x] frontend/src/hooks/useCrew.ts
[x] frontend/src/hooks/useEquipment.ts
[x] frontend/src/pages/Crew.tsx
[x] frontend/src/pages/CrewDetail.tsx
[x] frontend/src/pages/Equipment.tsx
```

**Commits exist:**
```bash
[x] d249a8b — feat(08-05): implement crew directory and detail pages
[x] c94fd57 — feat(08-05): implement equipment inventory page with CRUD
```

## Technical Notes

**DataTable Component Reuse:**
Successfully reused DataTable component from Plan 08-04. Pattern works well: columns config for desktop table, renderMobileCard for responsive layout. Hides columns marked `hideOnMobile` on mobile breakpoint.

**React Query Pattern:**
Consistent hook naming (`useCrewList`, `useCrew`, `useCrewRatings`, etc.) with queryKey arrays for automatic cache invalidation. Mutation hooks invalidate queries on success.

**Skills Pills Truncation:**
Displaying max 3 skills in table view with "+N more" indicator prevents row wrapping. Full skill list visible in detail view. Good UX balance for scannable tables.

**Condition Badge Dropdown:**
Unique pattern: badge itself is a styled `<select>` element. Allows instant condition updates without leaving table or opening modal. Color-coded with job state palette reuse (active=green, simmer=yellow, destructive=red, muted=grey).

**Inline Edit:**
Equipment row edit converts name cell to form with hidden fields for other properties. Simple pattern for quick name changes. Full edit would need modal or dedicated form.

**Availability Grid:**
7-column grid with day labels (Mon-Sun) and colored dots. Simple visual pattern for weekly availability. Data from `AvailabilityPatternResponse[]` where `day_of_week` is 0-6 index (Monday=0).

## Impact

**Admin workflow enhanced:**
- Crew directory provides searchable talent pool with skills and ratings at a glance
- Crew detail shows full profile, rating history, and availability for scheduling decisions
- Equipment inventory enables quick condition tracking and quantity management
- All three views use consistent DataTable + mobile card pattern for unified UX

**Resource management complete:**
Crew and equipment pages round out resource management UI. Combined with Jobs (Plan 08-04), admin now has full visibility into:
1. Jobs (what work is happening)
2. Crew (who can do it)
3. Equipment (what gear is available)

**Mobile responsive:**
Both pages switch to card layout on mobile. Crew cards show name, skills, rating + rate. Equipment cards show name, category, condition badge + qty, serial.

## Next Steps

Phase 08 Plan 06: Calendar view with job/crew/equipment events
Phase 08 Plan 07: Responsive polish and dark theme refinements

## Files Modified

- frontend/src/App.tsx — Added CrewPage, CrewDetailPage, EquipmentPage imports and routes
- frontend/src/hooks/useCrew.ts — Crew resource React Query hooks (7 hooks)
- frontend/src/hooks/useEquipment.ts — Equipment resource React Query hooks (6 hooks)
- frontend/src/pages/Crew.tsx — Crew directory with search/filter/DataTable
- frontend/src/pages/CrewDetail.tsx — Crew profile with ratings and availability grid
- frontend/src/pages/Equipment.tsx — Equipment inventory with CRUD and condition badges
