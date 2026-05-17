---
phase: 08-ui-polish
plan: 08
subsystem: frontend-calendar
tags: [ui, calendar, week-view, gap-closure]
dependency_graph:
  requires: [08-06-calendar-month-view]
  provides: [calendar-week-view-with-hourly-grid]
  affects: [frontend/src/pages/Calendar.tsx, frontend/src/hooks/useCalendar.ts]
tech_stack:
  added: []
  patterns: [css-grid-timeline, absolute-event-positioning, responsive-mobile-fallback]
key_files:
  created: []
  modified:
    - frontend/src/hooks/useCalendar.ts
    - frontend/src/pages/Calendar.tsx
decisions:
  - useWeekCalendarEvents hook mirrors useCalendarEvents pattern with startOfWeek/endOfWeek
  - 8-column CSS Grid (time gutter + 7 days) with 3rem per hour for precise event positioning
  - Absolute positioning for events with top/height calculated from start time and duration
  - Desktop shows hourly grid, mobile shows day list for responsive UX
  - Today highlighting reuses isToday pattern from month view (accent border + background)
  - Event click reuses existing handleEventClick handler for consistency
metrics:
  duration_seconds: 84
  tasks_completed: 1
  files_modified: 2
  commits: 1
  completed_at: "2026-05-17T09:07:13Z"
---

# Phase 08 Plan 08: Calendar Week View Summary

**One-liner:** 7-day hourly timeline grid with absolute-positioned event blocks, week navigation, today highlighting, and responsive mobile fallback

## What Was Built

Implemented the calendar week view that previously showed a "coming soon" placeholder. The week view provides operational detail for daily scheduling by showing crew and equipment assignments broken down by day and hour.

### Components Delivered

1. **useWeekCalendarEvents Hook** (`frontend/src/hooks/useCalendar.ts`)
   - Added new hook alongside existing `useCalendarEvents`
   - Uses `startOfWeek` and `endOfWeek` from date-fns to calculate week range
   - Formats dates as yyyy-MM-dd and calls `api.calendar.events`
   - Query key: `['calendar-events-week', start, end]` for independent caching

2. **Week View Implementation** (`frontend/src/pages/Calendar.tsx`)
   - **Desktop Layout**: 8-column CSS Grid (time gutter + 7 day columns)
     - Time column shows 24 hourly labels (00:00 - 23:00) in monospace font
     - Each hour row is 3rem tall for precise event positioning
     - Grid lines via `border-b` and `border-r` on cells
     - Events positioned absolutely within day columns with `top` and `height` calculated from start time and duration
     - Events styled with job state colors (e.g., `backgroundColor: event.color + '33'`, `color: event.color`)
   
   - **Mobile Layout**: Stacked day cards
     - Each day shows as a card with header and event list
     - Events display title + time range (e.g., "9:00 AM - 11:00 AM")
     - Uses `md:hidden` / `hidden md:block` for clean breakpoints
   
   - **Week Navigation**: Previous/Next buttons using `subWeeks` and `addWeeks`
     - Week range displayed as "May 12 - May 18, 2026"
   
   - **Today Highlighting**: `isToday(day)` check adds `bg-accent/5` background and `border-accent` on header
   
   - **Event Interaction**: Click navigates to job detail via existing `handleEventClick` handler

### Technical Approach

**Event Positioning Logic:**
- `calculateEventPosition` function handles multi-day events by clamping to day boundaries
- Uses `max([eventStart, dayStart])` and `min([eventEnd, dayEnd])` to handle events spanning multiple days
- Converts hours/minutes to rem units: `startHour * 3 + (startMinute / 60) * 3`
- Duration calculated via `differenceInMinutes` and converted to rem: `(durationMinutes / 60) * 3`
- Minimum height of 1.5rem ensures short events remain visible

**Grid Layout:**
- `grid-cols-8` creates 8 equal columns
- Time gutter is first column, 7 day columns follow
- Each hour rendered as a row with `height: 3rem`
- Events rendered only once (on hour === 0) with absolute positioning to avoid duplication across hour rows

**Responsive Strategy:**
- Desktop (md+): Full hourly grid with absolute-positioned events
- Mobile (< md): Day list with events shown as colored blocks with time text
- Ensures usability on phones where grid would be too cramped

## Deviations from Plan

None - plan executed exactly as written.

## Key Decisions

1. **CSS Grid over external library**: Custom grid implementation using date-fns + CSS Grid is simpler and faster to ship than integrating FullCalendar or react-big-calendar for v1.

2. **Absolute positioning for events**: Positioning events absolutely within day columns allows overlapping events to stack naturally without complex layout calculations.

3. **3rem per hour**: Chosen for balance between vertical space and event legibility. Allows 1-hour events to have comfortable padding while keeping 24 hours visible with reasonable scroll.

4. **Clamped event rendering**: Events spanning multiple days are clamped to day boundaries (00:00-23:59) to avoid overflow. Each day column shows only the portion of the event that falls within that day.

5. **Mobile fallback to day list**: Hourly grid is unusable on small screens. Day list provides same information (events with times) in a mobile-optimized format.

## Files Changed

**Modified:**
- `frontend/src/hooks/useCalendar.ts` — Added `useWeekCalendarEvents` hook with week date range calculation
- `frontend/src/pages/Calendar.tsx` — Replaced "coming soon" placeholder with full week view implementation (201 lines added, 3 removed)

## Verification Results

**Build:** ✓ Passes in 359ms with no TypeScript errors

**Acceptance Criteria:**
- ✓ `useWeekCalendarEvents` hook exists and uses `startOfWeek/endOfWeek`
- ✓ Placeholder "Week view coming soon" removed
- ✓ Week navigation implemented with `handlePrevWeek/handleNextWeek`
- ✓ 8-column grid (`grid-cols-8`) for time + 7 days
- ✓ Today highlighting using `isToday` check
- ✓ Event click handling via `handleEventClick` (5 instances)

## Integration Points

**Consumes:**
- `api.calendar.events` — Fetches events for week date range
- `useCalendarEvents` pattern — Mirrors existing month view hook structure

**Provides:**
- Week view accessible via view toggle buttons in Calendar page
- Hourly detail for crew/equipment scheduling

**Affects:**
- Calendar page now has two functional views (month + week)
- View state managed via `view` state variable ('month' | 'week')

## What Comes Next

Week view implementation completes the calendar feature set for v1. Future enhancements could include:
- Drag-and-drop event rescheduling
- Day view (single day with 15-minute intervals)
- Event conflict visualization (overlapping events in same column)
- Week start customization (Sunday vs Monday)

## Notes

- Event colors come from backend `JOB_STATE_COLORS` mapping (intake=blue, simmer=yellow, active=green, complete=grey)
- Week start defaults to Sunday (date-fns default) — could be made configurable
- Loading state matches month view pattern ("Loading calendar...")
- Grid is scrollable vertically to fit 24 hours in viewport (max-height: 70vh)

## Self-Check: PASSED

**Files created:** None (only modifications)

**Files modified:**
- ✓ frontend/src/hooks/useCalendar.ts exists
- ✓ frontend/src/pages/Calendar.tsx exists

**Commits:**
- ✓ 0b652d3 exists: `feat(08-08): implement calendar week view with hourly grid`

All deliverables verified.
