---
phase: 08-ui-polish
plan: 02
subsystem: frontend-auth-shell
tags: [authentication, routing, layout, navigation, ui]
dependency_graph:
  requires:
    - 08-01-frontend-foundation
  provides:
    - auth-context
    - login-flow
    - protected-routing
    - app-shell-layout
  affects:
    - all-future-frontend-plans
tech_stack:
  added:
    - react-router-dom: client-side routing
    - react-query: notification count polling
    - lucide-react: icon library
  patterns:
    - context-provider-auth
    - protected-route-wrapper
    - websocket-singleton-manager
    - navbar-sidebar-layout
key_files:
  created:
    - frontend/src/lib/auth.tsx
    - frontend/src/lib/websocket.ts
    - frontend/src/components/ProtectedRoute.tsx
    - frontend/src/pages/Login.tsx
    - frontend/src/pages/Register.tsx
    - frontend/src/components/layout/Navbar.tsx
    - frontend/src/components/layout/Sidebar.tsx
    - frontend/src/components/layout/AppLayout.tsx
  modified:
    - frontend/src/App.tsx
decisions:
  - choice: AuthProvider calls api.auth.me() on mount
    rationale: Frontend needs initial user state from httpOnly cookie
  - choice: WebSocket manager uses singleton pattern
    rationale: Single connection per app, multiple components can subscribe to job updates
  - choice: Navbar polls notification counts every 30s with React Query
    rationale: Real-time badge updates without full WebSocket complexity for counts
  - choice: Sidebar shows admin-only items conditionally based on user.role
    rationale: Crew users only see Dashboard (portal), admin sees all 5 sections
  - choice: Collapse sidebar to icon-only mode with toggle button
    rationale: Desktop space optimization, mobile uses overlay (future)
metrics:
  duration_seconds: 133
  tasks_completed: 2
  files_created: 8
  files_modified: 1
  commits: 2
  completed_date: "2026-05-17"
---

# Phase 08 Plan 02: App Shell with Auth & Layout Summary

**One-liner:** Login/register flow with JWT cookies, protected routing, fixed navbar with notification badge, collapsible sidebar navigation (5 items), and full app layout shell.

## What Was Built

Complete authentication UI and application shell. Users can register (with email verification message), log in (email + password), and see the main app layout with navbar and sidebar. All future views render inside this shell.

### Task 1: Auth Context & Login/Register Pages
- **Auth context (`frontend/src/lib/auth.tsx`)**: Manages user state via `api.auth.me()` call on mount, provides `login/logout/refreshUser` to components, persists auth via httpOnly cookies
- **WebSocket manager (`frontend/src/lib/websocket.ts`)**: Singleton class for WebSocket connections, handles reconnect with exponential backoff, job-based subscriptions with message routing
- **Protected route (`frontend/src/components/ProtectedRoute.tsx`)**: Redirects unauthenticated users to `/login`, shows loading state during auth check, optional `requiredRole` prop for role-based access
- **Login page (`frontend/src/pages/Login.tsx`)**: Dark-themed card with email/password inputs, error display in red border box, "Sign In" button, link to register, navigates to `/` on success
- **Register page (`frontend/src/pages/Register.tsx`)**: Company name + email + password fields, shows success message ("Check your email") after registration, link back to login

**Commit:** 391db7d

### Task 2: App Shell Layout & Router
- **Navbar (`frontend/src/components/layout/Navbar.tsx`)**: Fixed top bar (h-14), GT logo with dashed left border accent, notification bell icon with red badge (unread_messages + pending_assignments), user email in mono font, "Sign Out" button
- **Sidebar (`frontend/src/components/layout/Sidebar.tsx`)**: 5 navigation items (Dashboard, Jobs, Crew, Equipment, Calendar) with lucide-react icons, admin-only visibility for 4 items (crew sees only Dashboard), collapse toggle at bottom (icon-only mode w-16, expanded w-56), active state with left accent border
- **AppLayout (`frontend/src/components/layout/AppLayout.tsx`)**: Main wrapper with fixed navbar + sidebar + main content area, responsive margin (ml-16 collapsed, ml-56 expanded, ml-0 mobile), `<Outlet>` for route content
- **Router config (`frontend/src/App.tsx`)**: BrowserRouter with QueryClientProvider and AuthProvider wrappers, public routes (/login, /register), protected routes nested under AppLayout (/, /jobs, /jobs/:jobId, /crew, /crew/:crewId, /equipment, /calendar), stub pages show "Coming soon" for unimplemented views

**Commit:** f06ef06

## Deviations from Plan

None - plan executed exactly as written.

## Key Decisions

| Decision | Rationale |
|----------|-----------|
| AuthProvider calls api.auth.me() on mount | Frontend needs initial user state from httpOnly cookie |
| WebSocket manager uses singleton pattern | Single connection per app, multiple components can subscribe to job updates |
| Navbar polls notification counts every 30s with React Query | Real-time badge updates without full WebSocket complexity for counts |
| Sidebar shows admin-only items conditionally based on user.role | Crew users only see Dashboard (portal), admin sees all 5 sections |
| Collapse sidebar to icon-only mode with toggle button | Desktop space optimization, mobile uses overlay (future) |

## Testing Notes

- TypeScript type check: PASSED (`npx tsc --noEmit`)
- Build: PASSED (`npm run build` - 313.73 kB JS bundle, 17.80 kB CSS)
- All routes configured with stub pages inside protected shell
- Dark theme consistent across login/register/layout components

## Integration Points

**Consumes:**
- `frontend/src/lib/api.ts`: All auth methods (login, register, logout, me, wsToken)
- `frontend/src/types/api.ts`: User, LoginRequest, RegisterRequest, NotificationCounts types
- `backend/app/api/v1/auth.py`: /login, /register, /logout, /me, /ws-token endpoints

**Provides:**
- `useAuth()` hook: Available to all components inside AuthProvider
- `wsManager` singleton: Global WebSocket connection manager
- `ProtectedRoute` component: Wraps any route requiring authentication
- Router structure: All future plans add pages as `<Route>` children of AppLayout

**Next plans:**
- 08-03: Dashboard view (renders inside AppLayout at `/`)
- 08-04: Jobs list + detail (renders at `/jobs` and `/jobs/:jobId`)
- 08-05+: Crew, Equipment, Calendar views follow same pattern

## Self-Check

PASSED - All files created and commits verified:

```bash
✓ frontend/src/lib/auth.tsx exists
✓ frontend/src/lib/websocket.ts exists
✓ frontend/src/components/ProtectedRoute.tsx exists
✓ frontend/src/pages/Login.tsx exists
✓ frontend/src/pages/Register.tsx exists
✓ frontend/src/components/layout/Navbar.tsx exists
✓ frontend/src/components/layout/Sidebar.tsx exists
✓ frontend/src/components/layout/AppLayout.tsx exists
✓ frontend/src/App.tsx modified
✓ Commit 391db7d exists (Task 1)
✓ Commit f06ef06 exists (Task 2)
```
