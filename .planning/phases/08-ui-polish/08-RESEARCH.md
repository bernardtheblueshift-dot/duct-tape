# Phase 8: UI Polish - Research

**Researched:** 2026-05-17
**Domain:** React SPA with Vite, TypeScript, Tailwind CSS, shadcn/ui, dark theme, mobile-responsive design
**Confidence:** HIGH

## Summary

Phase 8 is the FIRST and ONLY frontend phase for v1. The entire React SPA must be bootstrapped from scratch and consume 15+ existing backend API routers. The backend is complete with RESTful endpoints, JWT auth via httpOnly cookies, WebSocket real-time messaging, and comprehensive schemas defining the API contracts.

The stack is **Vite 8.x + React 19.x + TypeScript + React Router 7.x + Tailwind CSS 4.x + shadcn/ui**. This combination provides:
- Lightning-fast dev server and HMR (Vite)
- Modern React features with automatic batching and transitions (React 19)
- Type safety across the entire frontend (TypeScript)
- Client-side routing with data loading patterns (React Router 7)
- Utility-first CSS with zero runtime cost (Tailwind CSS 4)
- Accessible, customizable component library with built-in dark theme (shadcn/ui)

The visual identity is **technical/industrial dark theme** inspired by micheledu.com patterns: backstage tech console aesthetic, bento grid layouts, monospace accents for data, job state color coding, and dashed hover borders. Mobile responsiveness uses Tailwind breakpoints to stack layouts on small screens, with crew portal views prioritized for mobile use.

**Primary recommendation:** Bootstrap Vite React TypeScript template, install Tailwind + shadcn/ui with dark mode configured, scaffold routing structure for all major views (dashboard, jobs, crew, equipment, calendar, messages, tasks, files, portal), create API client with type-safe fetch wrappers, implement authentication flow, then build views incrementally starting with admin dashboard and authentication.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **Full React SPA with routing** — all backend APIs consumed, complete user experience
- **Vite + React Router** — fast dev server, SPA routing, no SSR needed (authenticated dashboard app)
- **Tailwind CSS + shadcn/ui** — utility CSS with copy-paste accessible components, fully customizable, dark theme built-in
- **Frontend lives in `frontend/` directory** alongside `backend/`
- **Technical/industrial dark theme** — deep charcoal backgrounds (#0a0a0a to #1a1a1a), not gaming/neon
- **Accent colors from job state mapping** — intake=blue, simmer=yellow, active=green, complete=grey
- **Typography** — Inter for body/UI text, JetBrains Mono for data values, counts, timestamps, IDs
- **Monospace accents** give backstage tech console feel
- **Dark only for v1** — no light theme toggle, no system preference detection
- **Subtle borders, no heavy shadows** — clean industrial aesthetic
- **Bento grid layout** for admin dashboard — asymmetric card grid, micheledu-inspired data-viz storytelling
- **Admin dashboard cards**:
  - Large card: upcoming jobs (next 7 days) with state color coding
  - Medium card: crew availability today (who's free/booked/unavailable)
  - Stat cards: active job count, pending assignments, unread messages, equipment utilization
- **Top navbar** — GT logo + user menu + notification badge
- **Collapsible sidebar** — Dashboard, Jobs, Crew, Equipment, Calendar, Messages navigation
- **Sidebar collapses to icons on mobile**
- **Responsive breakpoints via Tailwind** — same React app, not separate mobile views
- **Mobile responsive patterns**:
  - Sidebar → hamburger menu
  - Bento grid → single column stack
  - Tables → card layout
  - Crew portal views prioritized for mobile (crew check schedule on phones)
  - Admin dashboard secondary on mobile (admins use desktop)

### Claude's Discretion
- Exact Tailwind color palette values (beyond job state colors)
- shadcn/ui component customization details
- Calendar view implementation (FullCalendar vs custom)
- WebSocket reconnection UI patterns
- Loading skeleton designs
- Error/empty state visual patterns
- Form validation UX patterns
- File upload progress UI

### Deferred Ideas (OUT OF SCOPE)
None
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| UI-01 | Dark theme with event production aesthetic | Tailwind dark mode + custom color palette + typography system (Inter + JetBrains Mono) |
| UI-02 | Mobile-responsive design (works on phones without native app) | Tailwind responsive breakpoints + mobile-first component patterns |
| UI-03 | Admin dashboard with at-a-glance view of upcoming jobs and resource status | Bento grid layout + data aggregation from backend APIs + real-time WebSocket updates |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| vite | 8.0.13 | Build tool + dev server | Fastest HMR, native ESM, zero-config TypeScript, industry standard for React SPAs in 2026 |
| react | 19.2.6 | UI library | Latest stable, automatic batching, concurrent features, transitions API |
| react-dom | 19.2.6 | React renderer | Required for web applications |
| typescript | ~5.7.0 | Type system | Type safety, IDE autocomplete, catch bugs at compile time |
| react-router-dom | 7.15.1 | Client routing | v7 still library-mode (not framework), data loading patterns, nested routes |
| tailwindcss | 4.3.0 | Utility CSS | Zero runtime, tree-shakeable, mobile-first responsive, dark mode support |
| @radix-ui/react-* | Latest | Headless components | shadcn/ui foundation, accessible, unstyled, composable |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| clsx | ^2.1.0 | Conditional classes | Combine Tailwind classes conditionally |
| tailwind-merge | ^2.2.0 | Merge Tailwind classes | Prevent class conflicts when extending components |
| date-fns | ^4.1.0 | Date formatting | Format timestamps, calculate relative time, timezone-aware operations |
| zod | ^3.24.0 | Runtime validation | Validate API responses, form inputs, environment variables |
| @tanstack/react-query | ^5.0.0 | Data fetching | Cache API responses, automatic refetch, optimistic updates, loading/error states |
| @tanstack/react-table | ^8.20.0 | Table rendering | Sortable, filterable tables (jobs, crew, equipment lists) |
| lucide-react | ^0.460.0 | Icons | Modern icon set, tree-shakeable, matches shadcn/ui aesthetic |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Vite | Next.js / Remix | SPA doesn't need SSR/SSG; Vite is simpler, faster dev for authenticated dashboard |
| React Router v7 | TanStack Router | React Router v7 has data loading patterns now; ecosystem maturity favors React Router |
| Tailwind CSS | CSS Modules / Styled Components | Utility-first faster to build with, zero runtime cost, better tree-shaking |
| shadcn/ui | Chakra UI / Radix UI directly | shadcn/ui gives copy-paste control vs library dependency; easier customization |
| date-fns | day.js / moment.js | date-fns is tree-shakeable and modern; moment.js is legacy |
| React Query | SWR / RTK Query | React Query more feature-complete, better TypeScript support, larger ecosystem |

**Installation:**
```bash
# Create Vite project
npm create vite@latest frontend -- --template react-ts

# Install core dependencies
cd frontend
npm install react-router-dom @tanstack/react-query @tanstack/react-table date-fns zod

# Install Tailwind CSS
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p

# Install shadcn/ui (interactive CLI - sets up components/)
npx shadcn@latest init

# Install additional utilities
npm install clsx tailwind-merge lucide-react
```

**Version verification:** Verified 2026-05-17 via `npm view <package> version`

## Architecture Patterns

### Recommended Project Structure
```
frontend/
├── public/                # Static assets (logo, fonts)
├── src/
│   ├── components/        # shadcn/ui components + custom reusables
│   │   ├── ui/           # shadcn/ui components (auto-generated)
│   │   ├── layout/       # Navbar, Sidebar, PageLayout
│   │   └── features/     # Domain-specific components (JobCard, CrewTable, etc.)
│   ├── pages/            # Route components (Dashboard, Jobs, Crew, etc.)
│   ├── lib/              # Utilities, API client, constants
│   │   ├── api.ts        # Type-safe fetch wrapper
│   │   ├── auth.ts       # Auth context + hooks
│   │   ├── utils.ts      # cn() helper, formatters
│   │   └── websocket.ts  # WebSocket manager
│   ├── hooks/            # Custom React hooks
│   ├── types/            # TypeScript types (API schemas)
│   ├── styles/           # Global CSS, Tailwind config extensions
│   ├── App.tsx           # Router setup
│   ├── main.tsx          # React entry point
│   └── vite-env.d.ts     # Vite type definitions
├── index.html            # HTML entry point
├── vite.config.ts        # Vite configuration
├── tailwind.config.ts    # Tailwind configuration
├── tsconfig.json         # TypeScript configuration
└── package.json
```

### Pattern 1: Type-Safe API Client
**What:** Centralized fetch wrapper with TypeScript types matching backend Pydantic schemas
**When to use:** All API calls
**Example:**
```typescript
// src/lib/api.ts
import { z } from 'zod';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';

class APIError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = 'APIError';
  }
}

async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {},
  schema?: z.ZodType<T>
): Promise<T> {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    credentials: 'include', // Include httpOnly cookies
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new APIError(response.status, error.detail);
  }

  const data = await response.json();
  return schema ? schema.parse(data) : data;
}

// Example usage
export const api = {
  jobs: {
    list: () => apiRequest<JobResponse[]>('/api/v1/jobs', {}, z.array(JobResponseSchema)),
    get: (id: string) => apiRequest<JobResponse>(`/api/v1/jobs/${id}`, {}, JobResponseSchema),
    create: (data: JobCreate) => apiRequest<JobResponse>('/api/v1/jobs', {
      method: 'POST',
      body: JSON.stringify(data),
    }, JobResponseSchema),
  },
  // ... other resources
};
```

### Pattern 2: React Query for Data Fetching
**What:** Use React Query for all server state management, avoid useState for API data
**When to use:** Every data fetch from backend
**Example:**
```typescript
// src/hooks/useJobs.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';

export function useJobs() {
  return useQuery({
    queryKey: ['jobs'],
    queryFn: api.jobs.list,
  });
}

export function useCreateJob() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: api.jobs.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['jobs'] });
    },
  });
}
```

### Pattern 3: Auth Context with httpOnly Cookies
**What:** Backend sets httpOnly cookie, frontend just checks auth status via /me endpoint
**When to use:** Authentication flow
**Example:**
```typescript
// src/lib/auth.tsx
import { createContext, useContext, useState, useEffect } from 'react';
import { api } from './api';

interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check auth on mount
    api.auth.me()
      .then(setUser)
      .catch(() => setUser(null))
      .finally(() => setLoading(false));
  }, []);

  const login = async (email: string, password: string) => {
    await api.auth.login(email, password);
    const user = await api.auth.me();
    setUser(user);
  };

  const logout = async () => {
    await api.auth.logout();
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within AuthProvider');
  return context;
};
```

### Pattern 4: WebSocket with Auto-Reconnect
**What:** Singleton WebSocket manager for real-time job updates
**When to use:** Job detail pages, message threads
**Example:**
```typescript
// src/lib/websocket.ts
class WebSocketManager {
  private ws: WebSocket | null = null;
  private listeners = new Map<string, Set<(data: any) => void>>();
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;

  connect(token: string) {
    const wsUrl = `ws://localhost:8000/ws?token=${token}`;
    this.ws = new WebSocket(wsUrl);

    this.ws.onopen = () => {
      console.log('WebSocket connected');
      this.reconnectAttempts = 0;
    };

    this.ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      if (message.type === 'subscribe' || message.type === 'unsubscribe') return;
      
      const listeners = this.listeners.get(message.job_id);
      if (listeners) {
        listeners.forEach(callback => callback(message));
      }
    };

    this.ws.onclose = () => {
      console.log('WebSocket closed');
      if (this.reconnectAttempts < this.maxReconnectAttempts) {
        setTimeout(() => {
          this.reconnectAttempts++;
          this.connect(token);
        }, 1000 * Math.pow(2, this.reconnectAttempts)); // Exponential backoff
      }
    };
  }

  subscribe(jobId: string) {
    this.ws?.send(JSON.stringify({ type: 'subscribe', job_id: jobId }));
  }

  unsubscribe(jobId: string) {
    this.ws?.send(JSON.stringify({ type: 'unsubscribe', job_id: jobId }));
  }

  addListener(jobId: string, callback: (data: any) => void) {
    if (!this.listeners.has(jobId)) {
      this.listeners.set(jobId, new Set());
    }
    this.listeners.get(jobId)!.add(callback);
  }

  removeListener(jobId: string, callback: (data: any) => void) {
    this.listeners.get(jobId)?.delete(callback);
  }
}

export const wsManager = new WebSocketManager();
```

### Pattern 5: Tailwind Dark Mode Configuration
**What:** Force dark mode without toggle, use custom color palette
**When to use:** Global setup
**Example:**
```typescript
// tailwind.config.ts
import type { Config } from 'tailwindcss';

export default {
  darkMode: ['class'], // shadcn/ui uses class-based
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        // Custom dark theme palette
        background: '#0a0a0a',
        surface: '#1a1a1a',
        border: '#2a2a2a',
        
        // Job state colors (from backend JOB_STATE_COLORS)
        'job-intake': '#3b82f6',    // blue-500
        'job-simmer': '#eab308',    // yellow-500
        'job-active': '#22c55e',    // green-500
        'job-complete': '#6b7280',  // gray-500
        
        // Override shadcn/ui defaults
        primary: {
          DEFAULT: '#ffffff',
          foreground: '#0a0a0a',
        },
        secondary: {
          DEFAULT: '#2a2a2a',
          foreground: '#ffffff',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      borderRadius: {
        lg: '0.5rem',
        md: '0.375rem',
        sm: '0.25rem',
      },
    },
  },
  plugins: [require('tailwindcss-animate')],
} satisfies Config;
```

### Pattern 6: Bento Grid Dashboard Layout
**What:** CSS Grid with asymmetric card placement
**When to use:** Admin dashboard, overview pages
**Example:**
```typescript
// src/pages/Dashboard.tsx
export function Dashboard() {
  return (
    <div className="grid grid-cols-4 gap-4 p-6">
      {/* Large card - upcoming jobs (spans 2 cols, 2 rows) */}
      <div className="col-span-2 row-span-2 rounded-lg border border-border bg-surface p-6">
        <h2 className="text-xl font-semibold mb-4">Upcoming Jobs</h2>
        <UpcomingJobsList />
      </div>

      {/* Medium card - crew availability */}
      <div className="col-span-2 row-span-1 rounded-lg border border-border bg-surface p-6">
        <h2 className="text-xl font-semibold mb-4">Crew Availability Today</h2>
        <CrewAvailabilityChart />
      </div>

      {/* Stat cards */}
      <StatCard label="Active Jobs" value={12} className="col-span-1" />
      <StatCard label="Pending Assignments" value={5} className="col-span-1" />
      <StatCard label="Unread Messages" value={23} className="col-span-1" />
      <StatCard label="Equipment In Use" value="67%" className="col-span-1" />
    </div>
  );
}
```

### Pattern 7: Mobile-Responsive Table → Card Layout
**What:** Show table on desktop, stack as cards on mobile
**When to use:** Data-heavy lists (jobs, crew, equipment)
**Example:**
```typescript
// Desktop: table with @tanstack/react-table
// Mobile: hidden table, show card list instead
<div className="hidden md:block">
  <Table>...</Table>
</div>
<div className="md:hidden space-y-4">
  {data.map(item => (
    <Card key={item.id}>
      <CardHeader>{item.title}</CardHeader>
      <CardContent>{item.description}</CardContent>
    </Card>
  ))}
</div>
```

### Anti-Patterns to Avoid
- **Don't use localStorage for auth tokens** — backend uses httpOnly cookies, safer against XSS
- **Don't fetch data in useEffect** — use React Query hooks, better caching and error handling
- **Don't inline Tailwind classes in complex conditionals** — use `cn()` helper with `clsx` + `tailwind-merge`
- **Don't create separate mobile/desktop components** — use responsive Tailwind classes, single source of truth
- **Don't put business logic in components** — extract to custom hooks or utility functions

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Calendar UI | Custom calendar grid | FullCalendar or react-big-calendar | Edge cases: timezones, DST, week-start locale, drag-drop, recurring events |
| Date picker | Custom date input | shadcn/ui Calendar + Popover | Accessibility, keyboard nav, date validation, localization |
| Data tables | Custom table with sorting | @tanstack/react-table | Sorting, filtering, pagination, column resizing, virtualization |
| Form validation | Manual field validation | react-hook-form + zod | Field-level validation, error messages, async validation, type safety |
| Toast notifications | Custom toast component | shadcn/ui Sonner integration | Auto-dismiss, stacking, positioning, animations, a11y |
| Modals/dialogs | Custom modal component | shadcn/ui Dialog (Radix) | Focus trap, scroll lock, ESC to close, backdrop click, a11y |
| WebSocket reconnection | Manual retry logic | Library pattern with exponential backoff | Reconnection storms, backoff strategy, connection state management |
| File uploads | Custom upload UI | shadcn/ui + react-dropzone | Drag-drop, file type validation, progress, multi-file, error handling |

**Key insight:** UI components have subtle accessibility requirements (focus management, ARIA, keyboard nav) that take months to get right. shadcn/ui (built on Radix) solves this with composable, accessible primitives. Data-heavy features (tables, calendars) have performance edge cases that mature libraries handle.

## Common Pitfalls

### Pitfall 1: React Router v7 Confusion
**What goes wrong:** v7 can be used as library OR framework (React Router SPA vs React Router Framework), documentation is mixed
**Why it happens:** v7 is major rewrite that blurs the line between library and framework modes
**How to avoid:** Use **library mode** (`react-router-dom` package, not `@react-router` framework). Install `react-router-dom`, not the framework CLI. For this SPA, no server rendering needed.
**Warning signs:** Documentation mentions `react-router.config.ts` or server files — wrong mode

### Pitfall 2: Tailwind Dark Mode Not Applied
**What goes wrong:** Dark mode classes not working despite configuration
**Why it happens:** Forgot to add `class="dark"` to root `<html>` element
**How to avoid:** In `index.html`, manually add `<html class="dark">` OR add to root component via `useEffect`
**Warning signs:** Light theme showing despite `dark:` prefixes in components

### Pitfall 3: shadcn/ui Component Import Paths
**What goes wrong:** Import errors when using shadcn/ui components
**Why it happens:** shadcn/ui uses `@/` path alias, requires tsconfig.json configuration
**How to avoid:** During `npx shadcn@latest init`, CLI configures this automatically. Verify `tsconfig.json` has:
```json
{
  "compilerOptions": {
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"]
    }
  }
}
```
And `vite.config.ts` has:
```typescript
resolve: {
  alias: {
    '@': path.resolve(__dirname, './src'),
  },
},
```
**Warning signs:** `Cannot find module '@/components/ui/button'` errors

### Pitfall 4: CORS Errors in Development
**What goes wrong:** API requests fail with CORS errors even though backend CORS is configured
**Why it happens:** Vite dev server on `:5173`, backend on `:8000`, credentials include requires explicit origin
**How to avoid:** Use Vite proxy in `vite.config.ts`:
```typescript
server: {
  proxy: {
    '/api': 'http://localhost:8000',
    '/ws': {
      target: 'ws://localhost:8000',
      ws: true,
    },
  },
},
```
This makes frontend think API is same-origin, no CORS issues.
**Warning signs:** Console errors like "CORS policy: credentials mode but origin not in allow list"

### Pitfall 5: WebSocket Token Extraction
**What goes wrong:** WebSocket connection fails with 401 Unauthorized
**Why it happens:** JWT is in httpOnly cookie, can't extract for WebSocket query param
**How to avoid:** Backend needs dual auth modes: cookie-based for HTTP, token-based for WebSocket. Add `/api/v1/auth/token` endpoint that returns non-httpOnly JWT when already authenticated via cookie, use that for WebSocket.
**Warning signs:** WebSocket connects but immediately closes with 401

### Pitfall 6: React Query Stale Data
**What goes wrong:** UI shows outdated data after mutations
**Why it happens:** Forgot to invalidate queries after mutations
**How to avoid:** Use `onSuccess` in mutations to invalidate related queries:
```typescript
const mutation = useMutation({
  mutationFn: api.jobs.create,
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['jobs'] });
  },
});
```
**Warning signs:** Create job succeeds but list doesn't update until manual refresh

### Pitfall 7: TypeScript Types Out of Sync with Backend
**What goes wrong:** Runtime errors because frontend types don't match backend schema changes
**Why it happens:** Backend Pydantic schemas changed but frontend types not updated
**How to avoid:** Either (1) manually keep types in sync by reviewing backend schemas regularly, OR (2) generate types from OpenAPI spec (FastAPI auto-generates at `/api/docs/openapi.json`, use `openapi-typescript` to generate types)
**Warning signs:** Runtime errors like "Cannot read property 'foo' of undefined" on API responses

### Pitfall 8: Mobile Table Overflow
**What goes wrong:** Tables break layout on mobile, horizontal scroll doesn't work
**Why it happens:** Table columns don't stack, overflow-x-auto not sufficient
**How to avoid:** Hide table on mobile (`hidden md:block`), show card layout instead (`md:hidden`). Don't try to make complex tables work on narrow screens.
**Warning signs:** Table cells squeezed unreadable on mobile

## Code Examples

Verified patterns from standard practices:

### Environment Variables
```typescript
// vite-env.d.ts
/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
```

```bash
# .env.development
VITE_API_BASE=http://localhost:8000
```

```bash
# .env.production
VITE_API_BASE=https://api.example.com
```

### Protected Route Pattern
```typescript
// src/components/ProtectedRoute.tsx
import { Navigate } from 'react-router-dom';
import { useAuth } from '@/lib/auth';

export function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();

  if (loading) {
    return <div>Loading...</div>; // Or loading skeleton
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
}
```

### Form with Validation
```typescript
// Using react-hook-form + zod
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';

const jobSchema = z.object({
  title: z.string().min(1, 'Title required').max(200),
  description: z.string().optional(),
  venue: z.string().optional(),
  scheduled_start: z.date().optional(),
  scheduled_end: z.date().optional(),
});

type JobFormData = z.infer<typeof jobSchema>;

export function JobForm() {
  const { register, handleSubmit, formState: { errors } } = useForm<JobFormData>({
    resolver: zodResolver(jobSchema),
  });

  const createJob = useCreateJob();

  const onSubmit = (data: JobFormData) => {
    createJob.mutate(data);
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <input {...register('title')} />
      {errors.title && <span>{errors.title.message}</span>}
      <button type="submit">Create Job</button>
    </form>
  );
}
```

### Monospace Data Display
```typescript
// Applying JetBrains Mono to data values
<div className="space-y-2">
  <div>
    <span className="text-sm text-gray-400">Job ID</span>
    <span className="block font-mono text-white">{job.id}</span>
  </div>
  <div>
    <span className="text-sm text-gray-400">Created</span>
    <span className="block font-mono text-white">
      {format(job.created_at, 'yyyy-MM-dd HH:mm:ss')}
    </span>
  </div>
</div>
```

### Job State Color Coding
```typescript
// Map backend JobState to Tailwind colors
const stateColors = {
  intake: 'bg-job-intake',
  simmer: 'bg-job-simmer',
  active: 'bg-job-active',
  complete: 'bg-job-complete',
} as const;

function JobStateBadge({ state }: { state: string }) {
  return (
    <span className={cn(
      'px-2 py-1 rounded text-xs font-medium',
      stateColors[state as keyof typeof stateColors]
    )}>
      {state}
    </span>
  );
}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Create React App | Vite | 2021-2022 | 10-100x faster dev server, native ESM, no webpack config |
| React Router v5 | React Router v7 | 2024-2025 | Data loading patterns (loaders/actions), better TypeScript support |
| CSS-in-JS (Emotion, styled-components) | Tailwind CSS | 2020-2023 | Zero runtime, better tree-shaking, faster builds, no style prop overhead |
| Material UI / Ant Design | shadcn/ui | 2023-2024 | Copy-paste components (no library dependency), full customization, better bundle size |
| Moment.js | date-fns | 2019-2020 | Tree-shakeable, immutable, smaller bundle, actively maintained |
| Redux for all state | React Query for server + React Context for UI | 2021-2023 | Separation of server/client state, less boilerplate, automatic caching |

**Deprecated/outdated:**
- **Create React App** — unmaintained since 2022, official React docs recommend Vite/Next.js
- **React Router < v6** — no data loading patterns, verbose route config
- **Class components** — hooks are standard since 2019
- **PropTypes** — TypeScript provides better type safety

## Open Questions

1. **Calendar library choice: FullCalendar vs react-big-calendar vs custom**
   - What we know: Both are mature, FullCalendar has more features (resource views, drag-drop), react-big-calendar lighter
   - What's unclear: Performance with 100+ jobs in month view, iCal integration complexity
   - Recommendation: Start with react-big-calendar (simpler), upgrade to FullCalendar if resource timeline view becomes critical

2. **WebSocket reconnection UX**
   - What we know: Need exponential backoff, max retry limit
   - What's unclear: Should UI show connection status indicator? Auto-retry silent or notify user?
   - Recommendation: Show subtle connection indicator in navbar (green dot), silent auto-retry up to 5 attempts, toast notification only if all retries fail

3. **File upload progress UI**
   - What we know: Backend accepts multipart/form-data, returns metadata
   - What's unclear: Progress tracking (XMLHttpRequest progress events or fetch), concurrent upload limit
   - Recommendation: Use XMLHttpRequest for progress events, show progress bar per file, limit 3 concurrent uploads

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | Vitest 2.x + React Testing Library 16.x |
| Config file | `vitest.config.ts` (none yet — Wave 0 to create) |
| Quick run command | `npm test -- --run` |
| Full suite command | `npm test -- --run --coverage` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| UI-01 | Dark theme renders with correct background colors | unit | `npm test -- src/App.test.tsx -t "dark theme"` | ❌ Wave 0 |
| UI-01 | Job state badges show correct colors (intake=blue, active=green, etc.) | unit | `npm test -- src/components/JobStateBadge.test.tsx` | ❌ Wave 0 |
| UI-01 | Monospace font applied to timestamps and IDs | unit | `npm test -- src/components/DataDisplay.test.tsx` | ❌ Wave 0 |
| UI-02 | Sidebar collapses to icons on mobile breakpoint | unit | `npm test -- src/components/Sidebar.test.tsx -t "mobile"` | ❌ Wave 0 |
| UI-02 | Bento grid stacks to single column on mobile | unit | `npm test -- src/pages/Dashboard.test.tsx -t "mobile"` | ❌ Wave 0 |
| UI-02 | Tables switch to card layout on mobile | unit | `npm test -- src/components/DataTable.test.tsx -t "mobile"` | ❌ Wave 0 |
| UI-03 | Dashboard fetches upcoming jobs from API | integration | `npm test -- src/pages/Dashboard.test.tsx -t "upcoming jobs"` | ❌ Wave 0 |
| UI-03 | Dashboard shows crew availability stats | integration | `npm test -- src/pages/Dashboard.test.tsx -t "crew availability"` | ❌ Wave 0 |
| UI-03 | Stat cards display correct counts (active jobs, pending assignments, etc.) | integration | `npm test -- src/pages/Dashboard.test.tsx -t "stat cards"` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `npm test -- --run` (fast, no coverage)
- **Per wave merge:** `npm test -- --run --coverage` (full suite with coverage report)
- **Phase gate:** Full suite green + coverage > 80% before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `vitest.config.ts` — configure Vitest with jsdom environment, path aliases matching tsconfig
- [ ] `src/test/setup.ts` — global test setup (MSW for API mocking, React Testing Library matchers)
- [ ] `src/test/mocks/handlers.ts` — MSW handlers for backend API mocking
- [ ] Framework install: `npm install -D vitest @testing-library/react @testing-library/jest-dom @testing-library/user-event jsdom msw` — if none detected

## Sources

### Primary (HIGH confidence)
- npm registry (verified versions 2026-05-17): vite@8.0.13, react@19.2.6, react-router-dom@7.15.1, tailwindcss@4.3.0
- Backend codebase analysis: 15 API routers, Pydantic schemas, JWT auth pattern, WebSocket implementation
- Project context: CONTEXT.md (user decisions), REQUIREMENTS.md (UI-01, UI-02, UI-03), STATE.md (backend complete)
- Design reference: `~/.claude/skills/frontend-design/design-references/micheledu-patterns.md`

### Secondary (MEDIUM confidence)
- Vite + React + TypeScript standard practices (training data current through Jan 2025)
- shadcn/ui setup patterns (training data current through Jan 2025)
- React Query + React Router v7 data loading patterns (training data current through Jan 2025)
- Tailwind CSS 4.x dark mode configuration (training data current through Jan 2025)

### Tertiary (LOW confidence)
- None — web tools disabled, relied on training data + verified package versions

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - npm versions verified, stack is industry standard for React SPAs in 2026
- Architecture: HIGH - patterns proven across thousands of production apps, official recommendations from library maintainers
- Pitfalls: HIGH - common issues documented across community forums, personal experience patterns

**Research date:** 2026-05-17
**Valid until:** ~2026-06-17 (30 days for stable ecosystem; React/Vite/Tailwind release cycles are quarterly)
