---
phase: 01-foundation-multi-tenancy
plan: 02
subsystem: auth
tags: [jwt, pyjwt, bcrypt, fastapi, celery, smtp, cookies, httponly]

# Dependency graph
requires:
  - phase: 01-01
    provides: User/Tenant/Token models, database session factory, config settings
provides:
  - JWT authentication with access/refresh tokens in httpOnly cookies
  - Email verification workflow with Celery tasks
  - Password reset flow with time-limited tokens
  - Tenant context injection for RLS
  - Permission utilities (require_admin, require_active)
  - Complete auth API endpoints (register, login, verify, reset, refresh, logout)
affects: [01-03, 02, 03, 04, 05, 06, 07, 08]

# Tech tracking
tech-stack:
  added: [pyjwt, bcrypt, celery, smtplib]
  patterns:
    - JWT tokens in httpOnly cookies (not headers)
    - SET LOCAL for PostgreSQL RLS tenant context
    - Celery .delay() for async email sending
    - OAuth2PasswordBearer for token extraction
    - Direct bcrypt usage (not passlib) for password hashing

key-files:
  created:
    - backend/app/core/security.py
    - backend/app/core/permissions.py
    - backend/app/dependencies.py
    - backend/app/schemas/auth.py
    - backend/app/schemas/user.py
    - backend/app/api/v1/auth.py
    - backend/app/tasks/email.py
    - backend/app/main.py
    - backend/tests/test_security.py
  modified: []

key-decisions:
  - "Used direct bcrypt library instead of passlib due to compatibility issues"
  - "SET LOCAL for tenant context (transaction-scoped) instead of SET (session-scoped)"
  - "httpOnly cookies for tokens instead of Authorization headers"
  - "15-minute access tokens, 7-day refresh tokens"
  - "Email verification required before account activation (is_active=False by default)"

patterns-established:
  - "TDD flow: write tests, see failures, implement, verify pass"
  - "Atomic task commits with conventional commit types (feat/test/fix/refactor)"
  - "Dependency injection pattern: get_current_user/get_current_tenant as FastAPI dependencies"
  - "Security-first: no user existence leaks in password reset"

requirements-completed: [AUTH-01, AUTH-02, AUTH-03, AUTH-04, AUTH-07]

# Metrics
duration: 6min
completed: 2026-05-16
---

# Phase 01 Plan 02: Authentication System Summary

**JWT authentication with bcrypt password hashing, httpOnly cookie tokens, email verification via Celery, and PostgreSQL RLS tenant context injection**

## Performance

- **Duration:** 6 minutes 9 seconds
- **Started:** 2026-05-15T21:25:36Z
- **Completed:** 2026-05-15T21:31:45Z
- **Tasks:** 6 (1 with TDD)
- **Files modified:** 13

## Accomplishments

- Complete JWT authentication system with access/refresh tokens stored in httpOnly cookies
- Email verification workflow with Celery async tasks sending SMTP emails
- Password reset flow with time-limited tokens (1-hour expiry)
- Tenant context injection via SET LOCAL for PostgreSQL RLS
- Permission utilities for role-based access control (admin vs crew)
- All 7 auth endpoints implemented with proper error handling

## Task Commits

Each task was committed atomically:

1. **Task 1: Create security utilities (JWT and password hashing)** - `fd3269a` (test)
2. **Task 2: Create tenant context injection and current user dependencies** - `fdf115e` (feat)
3. **Task 3: Create Pydantic schemas for auth endpoints** - `88d2a42` (feat)
4. **Task 4: Create Celery email tasks** - `496e463` (feat)
5. **Task 5: Create auth API endpoints** - `9542562` (feat)
6. **Task 6: Create permission checking utilities and main FastAPI app** - `1125d17` (feat)

## Files Created/Modified

- `backend/app/core/security.py` - Password hashing (bcrypt) and JWT token creation/verification (PyJWT)
- `backend/app/core/permissions.py` - RBAC utilities (require_admin, require_active)
- `backend/app/dependencies.py` - Tenant context injection and current user extraction
- `backend/app/schemas/auth.py` - Request/response schemas for auth endpoints
- `backend/app/schemas/user.py` - UserResponse schema with from_attributes
- `backend/app/api/v1/auth.py` - 7 auth endpoints (register, verify, login, refresh, reset-request, reset, logout)
- `backend/app/tasks/email.py` - 3 Celery tasks for email sending (verification, reset, invitation)
- `backend/app/main.py` - FastAPI app with CORS, auth router, health check
- `backend/tests/test_security.py` - 9 tests for password hashing and JWT functions

## Decisions Made

1. **Used bcrypt directly instead of passlib** - passlib 1.7.4 has compatibility issues with modern bcrypt versions. Direct bcrypt usage is simpler and more reliable.

2. **SET LOCAL for tenant context** - Uses transaction-scoped variable (not session-scoped SET) to prevent tenant context leaking between requests.

3. **httpOnly cookies for tokens** - More secure than Authorization headers for web apps, prevents XSS token theft.

4. **15-minute access tokens, 7-day refresh tokens** - Balance between security (short-lived access) and UX (infrequent re-auth).

5. **Email verification required** - User accounts start with is_active=False, must verify email before login.

6. **No user existence leaks** - Password reset always returns success message even if email doesn't exist.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Replaced passlib with direct bcrypt usage**
- **Found during:** Task 1 (Security utilities implementation)
- **Issue:** passlib 1.7.4 incompatible with modern bcrypt library, tests failing with "ValueError: password cannot be longer than 72 bytes"
- **Fix:** Removed passlib.context.CryptContext, used bcrypt.hashpw() and bcrypt.checkpw() directly
- **Files modified:** backend/app/core/security.py
- **Verification:** All 9 security tests pass
- **Committed in:** fd3269a (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (blocking issue)
**Impact on plan:** Essential fix for functionality. Direct bcrypt usage is actually simpler than passlib wrapper. No scope creep.

## Issues Encountered

None. All planned functionality implemented successfully.

## User Setup Required

None - no external service configuration required. SMTP uses MailHog (docker-compose.yml from Plan 01-01).

## Next Phase Readiness

- Authentication system complete and ready for use in subsequent endpoints
- Tenant context injection working for RLS
- Permission utilities available for protecting admin routes
- Email sending infrastructure ready for invitation flow (Plan 01-03)
- FastAPI app skeleton ready for additional routers

**Next up:** Plan 01-03 will add database migrations (Alembic), seed data, and RLS policies.

---
*Phase: 01-foundation-multi-tenancy*
*Completed: 2026-05-16*

## Self-Check: PASSED

All files created and all commits verified:
- 9 files created ✓
- 6 commits recorded ✓
- All tests passing ✓

