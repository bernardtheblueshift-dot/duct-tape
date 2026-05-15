# Phase 1: Foundation & Multi-Tenancy - Research

**Researched:** 2026-05-15
**Domain:** Multi-tenant SaaS authentication and database architecture
**Confidence:** HIGH

## Summary

Phase 1 establishes the foundation for a multi-tenant crew management SaaS. This phase makes **three irreversible decisions** that cannot be changed later without full data migration: (1) PostgreSQL Row-Level Security for tenant isolation, (2) TIMESTAMPTZ for all datetime columns, and (3) JWT-based authentication with httpOnly cookies.

The research confirms that the pre-decided stack (FastAPI + PostgreSQL + React) is well-suited for this phase. FastAPI provides built-in async support, automatic OpenAPI documentation, and Pydantic integration for type-safe request/response handling. PostgreSQL's Row-Level Security is the industry-standard approach for multi-tenant isolation at this scale (<1000 tenants), providing defense-in-depth against data leaks.

**Primary recommendation:** Implement PostgreSQL RLS with SQLAlchemy session variable injection, use PyJWT with httpOnly cookies (15-minute access tokens + 7-day refresh tokens), store all datetimes as TIMESTAMPTZ, and structure the project using FastAPI's dependency injection for tenant context propagation.

**Critical timing:** All architectural decisions in this phase are permanent. RLS policies, timezone handling, and auth token structure cannot be refactored later without breaking existing deployments and requiring data migration.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| AUTH-01 | User can sign up with email and password | FastAPI-Users library provides registration endpoints; Passlib with bcrypt for password hashing; email-validator for validation |
| AUTH-02 | User receives email verification after signup | Token-based verification with UUID + expiry; Celery for async email sending; SMTP or transactional email service (Postmark/SendGrid) |
| AUTH-03 | User can log in and session persists across browser refresh | PyJWT for token generation; httpOnly cookies prevent XSS; refresh token rotation for security |
| AUTH-04 | User can reset password via email link | Time-limited reset tokens (1-hour expiry); secure token generation with secrets module; token stored hashed in database |
| AUTH-05 | Admin can invite crew members to their tenant | Invitation token model with tenant_id; pre-registration workflow; role assignment on acceptance |
| AUTH-06 | Each tenant's data is fully isolated (PostgreSQL RLS) | RLS policies enforce tenant_id filtering; SET LOCAL app.current_tenant_id for session context; defense-in-depth with SQLAlchemy filters |
| AUTH-07 | Role-based access control (admin vs crew permissions) | FastAPI dependencies for role checking; user.role enum (admin, crew); permission decorators for endpoint protection |

</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| FastAPI | 0.136.1 | API framework | Industry standard for Python async APIs; built-in OpenAPI docs, Pydantic integration, WebSocket support for future phases |
| SQLAlchemy | 2.0.49 | ORM | v2.0 has modern async support (`create_async_engine`), better type hints, required for complex queries and migrations |
| Alembic | 1.18.4 | Database migrations | SQLAlchemy's official migration tool; handles multi-tenant schema evolution, supports auto-generation from models |
| PostgreSQL | 16+ | Database | Pre-decided; v16+ required for improved RLS performance, native JSON handling, better indexing for tenant isolation |
| Pydantic | 2.13.4 | Data validation | FastAPI dependency; v2 is 10x faster than v1, provides request/response schemas with automatic validation |
| Uvicorn | 0.47.0 | ASGI server | High-performance async server for FastAPI; production-ready with `--workers` flag for multi-process deployment |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| PyJWT | 2.12.1 | JWT tokens | Access tokens (15min) + refresh tokens (7d); include tenant_id in claims for RLS context |
| Passlib | 1.7.4 | Password hashing | Use bcrypt backend; industry standard for secure password storage; configurable work factor |
| asyncpg | Latest | PostgreSQL driver | Required for SQLAlchemy async mode; faster than psycopg2 for async operations |
| python-multipart | 0.0.28 | Form parsing | Required for FastAPI file uploads and form data; needed for registration/login forms |
| email-validator | Latest | Email validation | Validates email format in Pydantic models; prevents invalid email addresses |
| python-dotenv | Latest | Environment config | Load `.env` files in development; keeps secrets out of code |
| Redis | 7.4.0 (client) | Session store + cache | Store refresh tokens (blacklist revoked tokens); cache user permissions; needed for Phase 5 WebSockets |
| Celery | 5.6.3 | Background tasks | Async email sending (verification, password reset, invitations); use Redis as broker |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| FastAPI | Django REST Framework | DRF is more batteries-included but slower, heavier, less modern async support |
| PyJWT | python-jose | jose has broader spec support but PyJWT is simpler and more widely used for basic JWT |
| Row-Level Security | Schema-per-tenant | Schema-per-tenant offers better isolation but adds migration complexity and connection pool pressure |
| httpOnly cookies | localStorage tokens | localStorage is easier for SPA but vulnerable to XSS attacks; cookies are more secure |

**Installation:**
```bash
# Core dependencies
pip install fastapi[standard]==0.136.1 uvicorn[standard]==0.47.0
pip install sqlalchemy==2.0.49 alembic==1.18.4 asyncpg
pip install pydantic==2.13.4 pydantic-settings
pip install pyjwt==2.12.1 passlib==1.7.4 bcrypt
pip install python-multipart==0.0.28 email-validator python-dotenv
pip install redis==7.4.0 celery==5.6.3

# Development
pip install pytest pytest-asyncio httpx black ruff
```

**Version verification:** Versions verified 2026-05-15 via GitHub API (FastAPI, SQLAlchemy, Pydantic) and PyPI API (remaining packages). All are current stable releases.

## Architecture Patterns

### Recommended Project Structure
```
duct-tape/
├── backend/
│   ├── alembic/              # Database migrations
│   │   ├── versions/         # Migration scripts
│   │   └── env.py            # Alembic configuration
│   ├── app/
│   │   ├── main.py           # FastAPI app initialization
│   │   ├── config.py         # Settings (Pydantic BaseSettings)
│   │   ├── database.py       # SQLAlchemy engine, session factory
│   │   ├── dependencies.py   # Shared FastAPI dependencies
│   │   ├── models/           # SQLAlchemy models
│   │   │   ├── base.py       # Base model with tenant_id, timestamps
│   │   │   ├── user.py       # User, Tenant models
│   │   │   └── token.py      # VerificationToken, ResetToken, InvitationToken
│   │   ├── schemas/          # Pydantic schemas (request/response)
│   │   │   ├── auth.py       # Login, Register, Token schemas
│   │   │   └── user.py       # User response schemas
│   │   ├── api/              # API routes
│   │   │   ├── v1/
│   │   │   │   ├── auth.py   # /auth/register, /auth/login, /auth/refresh
│   │   │   │   └── users.py  # /users (tenant-scoped CRUD)
│   │   ├── core/             # Core utilities
│   │   │   ├── security.py   # Password hashing, JWT creation/verification
│   │   │   ├── permissions.py # Role-based access control decorators
│   │   │   └── tenant.py     # Tenant context management
│   │   ├── tasks/            # Celery tasks
│   │   │   └── email.py      # send_verification_email, send_reset_email
│   │   └── tests/            # Pytest tests
│   ├── .env.example          # Environment variable template
│   ├── pyproject.toml        # Dependencies (Poetry or pip-tools)
│   └── alembic.ini           # Alembic configuration
├── frontend/                 # React app (Vite)
└── docker-compose.yml        # Local development (PostgreSQL + Redis)
```

### Pattern 1: PostgreSQL Row-Level Security with SQLAlchemy

**What:** Database-enforced tenant isolation using PostgreSQL RLS policies combined with SQLAlchemy session variables.

**When to use:** Multi-tenant SaaS with <10,000 tenants where tenant data must never leak.

**Example:**
```python
# backend/app/models/base.py
from sqlalchemy import Column, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase
import uuid

class Base(DeclarativeBase):
    pass

class TenantMixin:
    """Add to all tenant-scoped models"""
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

# backend/app/models/user.py
from sqlalchemy import Column, String, Boolean, Enum
from .base import Base, TenantMixin
import enum

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    CREW = "crew"

class User(Base, TenantMixin):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, nullable=False, unique=True)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=False)  # False until email verified
    role = Column(Enum(UserRole), nullable=False, default=UserRole.CREW)
    # tenant_id from TenantMixin

# Migration: Enable RLS and create policy
# alembic/versions/001_enable_rls.py
def upgrade():
    # Enable RLS on users table
    op.execute("ALTER TABLE users ENABLE ROW LEVEL SECURITY")
    
    # Create policy: only show rows where tenant_id matches session variable
    op.execute("""
        CREATE POLICY tenant_isolation ON users
        USING (tenant_id::text = current_setting('app.current_tenant_id', TRUE))
    """)
    
    # Allow superuser (migrations, backups) to bypass RLS
    op.execute("ALTER TABLE users FORCE ROW LEVEL SECURITY")

# backend/app/dependencies.py
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from .core.security import decode_access_token
from .database import get_db

async def get_current_tenant(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> str:
    """Extract tenant_id from JWT and set PostgreSQL session variable"""
    payload = decode_access_token(token)
    tenant_id = payload.get("tenant_id")
    
    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )
    
    # Set PostgreSQL session variable for RLS
    await db.execute(text(f"SET LOCAL app.current_tenant_id = '{tenant_id}'"))
    
    return tenant_id

# Usage in routes
@router.get("/users")
async def list_users(
    tenant_id: str = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db)
):
    # RLS automatically filters by tenant_id - no WHERE clause needed
    result = await db.execute(select(User))
    return result.scalars().all()
```

**Source:** PostgreSQL RLS documentation + SQLAlchemy async patterns (verified via training data)

### Pattern 2: JWT Authentication with httpOnly Cookies

**What:** Token-based authentication using short-lived access tokens and long-lived refresh tokens, stored in httpOnly cookies.

**When to use:** SPA (React) authentication where you need XSS protection and automatic token refresh.

**Example:**
```python
# backend/app/core/security.py
from datetime import datetime, timedelta
from typing import Optional
import jwt
from passlib.context import CryptContext
from app.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(user_id: str, tenant_id: str, role: str) -> str:
    """Create short-lived access token (15 minutes)"""
    expire = datetime.utcnow() + timedelta(minutes=15)
    payload = {
        "sub": user_id,
        "tenant_id": tenant_id,
        "role": role,
        "exp": expire,
        "type": "access"
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")

def create_refresh_token(user_id: str) -> str:
    """Create long-lived refresh token (7 days)"""
    expire = datetime.utcnow() + timedelta(days=7)
    payload = {
        "sub": user_id,
        "exp": expire,
        "type": "refresh"
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")

def decode_access_token(token: str) -> dict:
    """Verify and decode access token"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        if payload.get("type") != "access":
            raise jwt.InvalidTokenError("Invalid token type")
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# backend/app/api/v1/auth.py
from fastapi import APIRouter, Depends, HTTPException, Response, Cookie
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/login")
async def login(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    # Verify credentials
    user = await authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Email not verified")
    
    # Create tokens
    access_token = create_access_token(
        user_id=str(user.id),
        tenant_id=str(user.tenant_id),
        role=user.role
    )
    refresh_token = create_refresh_token(user_id=str(user.id))
    
    # Set httpOnly cookies (prevents XSS)
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=True,  # HTTPS only in production
        samesite="lax",
        max_age=15 * 60  # 15 minutes
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=7 * 24 * 60 * 60  # 7 days
    )
    
    return {"status": "success"}

@router.post("/refresh")
async def refresh_access_token(
    response: Response,
    refresh_token: str = Cookie(None),
    db: AsyncSession = Depends(get_db)
):
    """Refresh access token using refresh token"""
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Refresh token missing")
    
    # Verify refresh token
    payload = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=["HS256"])
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid token type")
    
    user_id = payload.get("sub")
    user = await db.get(User, user_id)
    
    # Create new access token
    new_access_token = create_access_token(
        user_id=str(user.id),
        tenant_id=str(user.tenant_id),
        role=user.role
    )
    
    response.set_cookie(
        key="access_token",
        value=new_access_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=15 * 60
    )
    
    return {"status": "success"}
```

**Source:** FastAPI Security documentation + OWASP authentication best practices

### Pattern 3: Email Verification Workflow

**What:** Token-based email verification with expiring tokens and resend capability.

**When to use:** User registration flows requiring email confirmation.

**Example:**
```python
# backend/app/models/token.py
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime, timedelta
import secrets

class VerificationToken(Base):
    __tablename__ = "verification_tokens"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    token = Column(String, unique=True, nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    
    @staticmethod
    def generate_token() -> str:
        """Generate secure random token"""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def create_for_user(user_id: str) -> "VerificationToken":
        """Create verification token with 24-hour expiry"""
        return VerificationToken(
            user_id=user_id,
            token=VerificationToken.generate_token(),
            expires_at=datetime.utcnow() + timedelta(hours=24)
        )

# backend/app/api/v1/auth.py
@router.post("/register")
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    # Check if email already exists
    existing = await db.execute(
        select(User).where(User.email == user_data.email)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create tenant and admin user
    tenant = Tenant(name=user_data.company_name)
    db.add(tenant)
    await db.flush()  # Get tenant.id
    
    user = User(
        email=user_data.email,
        hashed_password=hash_password(user_data.password),
        tenant_id=tenant.id,
        role=UserRole.ADMIN,
        is_active=False  # Activate after email verification
    )
    db.add(user)
    await db.flush()
    
    # Create verification token
    verification_token = VerificationToken.create_for_user(str(user.id))
    db.add(verification_token)
    await db.commit()
    
    # Send verification email (async task)
    send_verification_email.delay(
        email=user.email,
        token=verification_token.token
    )
    
    return {"status": "success", "message": "Verification email sent"}

@router.post("/verify-email")
async def verify_email(
    token: str,
    db: AsyncSession = Depends(get_db)
):
    # Find token
    result = await db.execute(
        select(VerificationToken).where(VerificationToken.token == token)
    )
    verification = result.scalar_one_or_none()
    
    if not verification:
        raise HTTPException(status_code=400, detail="Invalid verification token")
    
    if verification.expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Verification token expired")
    
    # Activate user
    user = await db.get(User, verification.user_id)
    user.is_active = True
    
    # Delete used token
    await db.delete(verification)
    await db.commit()
    
    return {"status": "success", "message": "Email verified"}

# backend/app/tasks/email.py
from celery import shared_task
from app.config import settings
import smtplib
from email.mime.text import MIMEText

@shared_task
def send_verification_email(email: str, token: str):
    """Send verification email via SMTP"""
    verification_url = f"{settings.FRONTEND_URL}/verify-email?token={token}"
    
    msg = MIMEText(f"""
        Welcome to Duct Tape!
        
        Click the link below to verify your email address:
        {verification_url}
        
        This link expires in 24 hours.
    """)
    msg["Subject"] = "Verify your email address"
    msg["From"] = settings.SMTP_FROM
    msg["To"] = email
    
    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
        server.starttls()
        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.send_message(msg)
```

**Source:** Common email verification patterns + Celery async task patterns

### Pattern 4: Timezone-Aware Datetime Handling

**What:** Store all datetimes as TIMESTAMPTZ in PostgreSQL, display in user's timezone.

**When to use:** Always, for any application with datetime fields.

**Example:**
```python
# backend/app/models/base.py
from sqlalchemy import Column, DateTime
from datetime import datetime

class TimestampMixin:
    """Add to all models requiring timestamps"""
    created_at = Column(
        DateTime(timezone=True),  # Uses TIMESTAMPTZ in PostgreSQL
        nullable=False,
        default=datetime.utcnow
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

# backend/app/models/user.py
from sqlalchemy import Column, String
from .base import Base, TenantMixin, TimestampMixin

class User(Base, TenantMixin, TimestampMixin):
    __tablename__ = "users"
    
    timezone = Column(String, nullable=False, default="UTC")  # User's preferred timezone
    # e.g., "America/New_York", "Asia/Tokyo"

# backend/app/schemas/user.py
from pydantic import BaseModel, ConfigDict
from datetime import datetime

class UserResponse(BaseModel):
    id: str
    email: str
    created_at: datetime  # Pydantic automatically serializes to ISO 8601 with timezone
    timezone: str
    
    model_config = ConfigDict(from_attributes=True)

# Frontend: Display in user's timezone
// frontend/src/utils/datetime.ts
import { formatInTimeZone } from 'date-fns-tz';

export function formatUserDateTime(
  isoString: string,
  userTimezone: string
): string {
  return formatInTimeZone(
    new Date(isoString),
    userTimezone,
    'PPpp'  // e.g., "Apr 29, 2026, 9:00 AM"
  );
}
```

**Source:** PostgreSQL TIMESTAMPTZ documentation + timezone handling best practices

### Anti-Patterns to Avoid

- **Storing JWT in localStorage:** Vulnerable to XSS attacks. Use httpOnly cookies instead.
- **Application-only tenant filtering:** Without RLS, one missed WHERE clause leaks data. Use defense-in-depth.
- **TIMESTAMP without timezone:** Causes incorrect datetime display for users in different timezones. Always use TIMESTAMPTZ.
- **Sequential integer IDs in multi-tenant:** Allows enumeration attacks. Use UUIDs for public-facing IDs.
- **Synchronous email sending:** Blocks HTTP requests. Use Celery for async background tasks.
- **Plaintext password reset tokens:** Security vulnerability. Hash tokens before storing in database.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Password hashing | Custom hash algorithm | Passlib with bcrypt | Well-tested, configurable work factor, handles salt automatically |
| JWT generation/verification | Manual base64 + signing | PyJWT | Handles algorithm selection, expiry checking, signature verification correctly |
| Email validation | Regex patterns | email-validator library | Handles edge cases (internationalized domains, quoted strings, comments) |
| Database migrations | Manual SQL scripts | Alembic | Tracks migration history, supports rollbacks, auto-generates from models |
| Async PostgreSQL | DIY connection pool | SQLAlchemy with asyncpg | Handles connection pooling, transaction management, query compilation |
| Security tokens | `random.randint()` or `uuid4()` | `secrets` module | Cryptographically secure random generation for tokens |

**Key insight:** Authentication and security have well-documented failure modes. Rolling custom solutions introduces vulnerabilities that experts have already solved. Use battle-tested libraries.

## Common Pitfalls

### Pitfall 1: RLS Session Variable Leakage Across Requests

**What goes wrong:** Setting `app.current_tenant_id` globally instead of per-request with `SET LOCAL` causes tenant context to leak between requests.

**Why it happens:** Using `SET` instead of `SET LOCAL`, or setting the variable outside a transaction.

**How to avoid:**
- Always use `SET LOCAL app.current_tenant_id = '...'` (scoped to transaction)
- Set the variable inside each transaction, not globally
- Use FastAPI dependencies to set context per-request
- Test with concurrent requests to different tenants

**Warning signs:**
- Cross-tenant data appearing in API responses
- RLS tests pass individually but fail when run concurrently
- `SET` used instead of `SET LOCAL` in code

**Phase 1 critical:** This must be correct from day one. Cross-tenant data leaks are catastrophic security failures.

### Pitfall 2: Refresh Token Not Rotated on Use

**What goes wrong:** Reusing the same refresh token indefinitely allows stolen tokens to remain valid forever.

**Why it happens:** Simple implementation that doesn't rotate refresh tokens on use.

**How to avoid:**
- Issue new refresh token on each `/auth/refresh` call
- Store refresh token family IDs to detect reuse (token theft)
- Invalidate all tokens in family if reuse detected
- Set absolute maximum lifetime (30 days) even with rotation

**Warning signs:**
- Same refresh token works for weeks/months
- No refresh token storage or tracking
- No reuse detection mechanism

**Phase 1 implementation:** Start with simple rotation; add reuse detection in Phase 2+.

### Pitfall 3: Email Verification Tokens Not Hashed in Database

**What goes wrong:** Storing plaintext verification tokens allows database compromise to enable account takeover.

**Why it happens:** Tokens seem less sensitive than passwords.

**How to avoid:**
- Hash verification tokens before storing (use `hashlib.sha256`)
- Generate token with `secrets.token_urlsafe()` (not UUID)
- Compare hashed version on verification
- Same applies to password reset tokens

**Warning signs:**
- `verification_tokens.token` column stores plaintext
- Tokens are predictable (sequential or UUID-based)
- No hashing function in token verification code

**Phase 1 decision:** Implement hashed tokens from start; retrofitting requires migration.

### Pitfall 4: Tenant Isolation Not Tested with Cross-Tenant Requests

**What goes wrong:** RLS policies look correct but don't actually prevent cross-tenant access in all scenarios.

**Why it happens:** Testing only happy paths with single tenant.

**How to avoid:**
- Write integration tests with multiple tenants
- Attempt to access Tenant B's data using Tenant A's credentials
- Test with missing `tenant_id` in session (should fail)
- Test with malformed `tenant_id` (SQL injection attempt)
- Verify RLS policies in database inspector

**Warning signs:**
- No multi-tenant tests in test suite
- Tests use single hardcoded tenant ID
- No negative tests (unauthorized access attempts)

**Phase 1 verification:** RLS test coverage is mandatory before production deployment.

### Pitfall 5: Missing Async Context in Database Sessions

**What goes wrong:** Using synchronous SQLAlchemy patterns with async FastAPI causes blocking or errors.

**Why it happens:** Copying synchronous SQLAlchemy examples.

**How to avoid:**
- Use `create_async_engine` not `create_engine`
- Use `AsyncSession` not `Session`
- Use `await db.execute()` not `db.execute()`
- Use `async with` for session context managers
- Import from `sqlalchemy.ext.asyncio`

**Warning signs:**
- Event loop errors in logs
- Blocking database calls
- `RuntimeError: Event loop is closed`
- Mixing sync and async SQLAlchemy imports

**Phase 1 foundation:** All database code must be async from start.

### Pitfall 6: CORS Configuration Too Permissive in Production

**What goes wrong:** Allowing `origins=["*"]` in production exposes API to cross-origin attacks.

**Why it happens:** Copying development CORS config to production.

**How to avoid:**
- Use environment-specific CORS origins
- Development: `http://localhost:5173` (Vite default)
- Production: Specific frontend domain only
- Never use `origins=["*"]` with `allow_credentials=True`
- Verify `Access-Control-Allow-Origin` headers in production

**Warning signs:**
- `origins=["*"]` in main.py
- Same CORS config for dev and prod
- Credentials allowed with wildcard origins

**Phase 1 setup:** Configure environment-specific CORS from start.

## Code Examples

Verified patterns from official sources:

### FastAPI Application Structure

```python
# backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api.v1 import auth, users

app = FastAPI(
    title="Duct Tape API",
    version="1.0.0",
    docs_url="/api/docs"
)

# CORS configuration (environment-specific)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,  # ["http://localhost:5173"] in dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
```

**Source:** FastAPI documentation - Application structure

### Database Session Management

```python
# backend/app/database.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.config import settings

# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True  # Verify connections before use
)

# Session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def get_db() -> AsyncSession:
    """FastAPI dependency for database sessions"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
```

**Source:** SQLAlchemy 2.0 async documentation

### Role-Based Permission Checking

```python
# backend/app/core/permissions.py
from fastapi import Depends, HTTPException, status
from app.dependencies import get_current_user
from app.models.user import User, UserRole

def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Require admin role for endpoint access"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user

def require_active(current_user: User = Depends(get_current_user)) -> User:
    """Require active (email-verified) user"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email verification required"
        )
    return current_user

# Usage in routes
@router.post("/users/invite")
async def invite_crew_member(
    invite_data: InviteCreate,
    current_user: User = Depends(require_admin),  # Admin-only endpoint
    db: AsyncSession = Depends(get_db)
):
    # Only admins can invite crew members
    pass
```

**Source:** FastAPI dependencies documentation

### Invitation Workflow

```python
# backend/app/models/token.py
class InvitationToken(Base, TenantMixin):
    __tablename__ = "invitation_tokens"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.CREW)
    token = Column(String, unique=True, nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    invited_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    # tenant_id from TenantMixin - invitee joins this tenant

# backend/app/api/v1/auth.py
@router.post("/invite")
async def invite_crew(
    email: str,
    role: UserRole,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Admin invites crew member to their tenant"""
    # Check if user already exists in this tenant
    existing = await db.execute(
        select(User).where(
            User.email == email,
            User.tenant_id == current_user.tenant_id
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="User already in tenant")
    
    # Create invitation token
    invitation = InvitationToken(
        email=email,
        role=role,
        tenant_id=current_user.tenant_id,
        token=secrets.token_urlsafe(32),
        expires_at=datetime.utcnow() + timedelta(days=7),
        invited_by=current_user.id
    )
    db.add(invitation)
    await db.commit()
    
    # Send invitation email
    send_invitation_email.delay(
        email=email,
        token=invitation.token,
        inviter_name=current_user.name,
        tenant_name=current_user.tenant.name
    )
    
    return {"status": "success", "message": "Invitation sent"}

@router.post("/accept-invitation")
async def accept_invitation(
    token: str,
    password: str,
    db: AsyncSession = Depends(get_db)
):
    """Accept invitation and create crew account"""
    # Find invitation
    result = await db.execute(
        select(InvitationToken).where(InvitationToken.token == token)
    )
    invitation = result.scalar_one_or_none()
    
    if not invitation:
        raise HTTPException(status_code=400, detail="Invalid invitation")
    
    if invitation.expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Invitation expired")
    
    # Create user in invited tenant
    user = User(
        email=invitation.email,
        hashed_password=hash_password(password),
        tenant_id=invitation.tenant_id,
        role=invitation.role,
        is_active=True  # No email verification needed for invitations
    )
    db.add(user)
    
    # Delete used invitation
    await db.delete(invitation)
    await db.commit()
    
    return {"status": "success", "message": "Account created"}
```

**Source:** Multi-tenant invitation pattern from SaaS best practices

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.3.4 + pytest-asyncio 0.24.0 |
| Config file | backend/pyproject.toml (test configuration) |
| Quick run command | `pytest tests/test_auth.py -v -x` |
| Full suite command | `pytest tests/ -v --cov=app --cov-report=term-missing` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| AUTH-01 | User signup with email/password validation | unit | `pytest tests/test_auth.py::test_register_user -x` | ❌ Wave 0 |
| AUTH-02 | Email verification token creation and validation | unit | `pytest tests/test_auth.py::test_email_verification -x` | ❌ Wave 0 |
| AUTH-03 | Login creates tokens, session persists (cookie validation) | integration | `pytest tests/test_auth.py::test_login_session -x` | ❌ Wave 0 |
| AUTH-04 | Password reset token flow | integration | `pytest tests/test_auth.py::test_password_reset -x` | ❌ Wave 0 |
| AUTH-05 | Admin invitation workflow | integration | `pytest tests/test_auth.py::test_invitation_flow -x` | ❌ Wave 0 |
| AUTH-06 | RLS prevents cross-tenant data access | integration | `pytest tests/test_tenant_isolation.py::test_rls_isolation -x` | ❌ Wave 0 |
| AUTH-07 | Role-based endpoint access control | unit | `pytest tests/test_permissions.py::test_role_permissions -x` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest tests/ -v -x --lf` (run last-failed first, stop on first failure)
- **Per wave merge:** `pytest tests/ -v --cov=app --cov-report=term-missing` (full suite with coverage)
- **Phase gate:** Full suite green + manual RLS verification in database before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `backend/tests/test_auth.py` — covers AUTH-01 through AUTH-05
- [ ] `backend/tests/test_tenant_isolation.py` — covers AUTH-06 (RLS verification with multi-tenant data)
- [ ] `backend/tests/test_permissions.py` — covers AUTH-07 (role-based access)
- [ ] `backend/tests/conftest.py` — shared fixtures (test database, async client, test tenants/users)
- [ ] Framework install: `pip install pytest pytest-asyncio httpx pytest-cov` — if none detected
- [ ] `backend/pytest.ini` or `pyproject.toml` with `[tool.pytest.ini_options]` — test configuration

**Critical:** AUTH-06 (RLS isolation) requires integration tests that create multiple tenants, attempt cross-tenant access with valid credentials, and verify database-level blocking. Cannot be unit-tested; must use real database with RLS enabled.

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Django for async APIs | FastAPI | ~2019 | Better async support, automatic OpenAPI, faster development |
| Synchronous SQLAlchemy | Async SQLAlchemy 2.0 | 2023 | Native async/await, better performance with async frameworks |
| localStorage for JWT | httpOnly cookies | 2020+ | XSS protection, automatic CSRF handling with SameSite |
| Schema-per-tenant (default) | RLS for <10K tenants | 2018+ | Simpler migrations, better connection pooling, easier cross-tenant features |
| Pydantic v1 | Pydantic v2 | 2023 | 10x performance improvement, better type inference |
| Manual CORS handling | FastAPI CORS middleware | Initial release | Standardized, secure defaults |

**Deprecated/outdated:**
- **Flask-JWT:** Use PyJWT directly with FastAPI dependencies (simpler, more control)
- **Flask-SQLAlchemy:** SQLAlchemy 2.0 works natively with FastAPI async
- **Bcrypt without Passlib:** Passlib provides unified interface, easier to upgrade hash algorithms
- **Schema-per-tenant for small SaaS:** RLS is now preferred for <10K tenants (simpler operations)

## Open Questions

1. **Email service provider selection**
   - What we know: Need transactional email for verification/reset/invitations; Celery for async sending
   - What's unclear: SMTP (self-hosted) vs Postmark vs SendGrid vs AWS SES for cost/reliability tradeoff
   - Recommendation: Start with SMTP (development), add Postmark in production (99%+ deliverability, simple API)

2. **Refresh token storage strategy**
   - What we know: Refresh tokens need blacklist capability for revocation; Redis fast but volatile
   - What's unclear: Redis-only vs PostgreSQL vs hybrid (Redis cache + PostgreSQL persistence)
   - Recommendation: PostgreSQL for persistence (simpler, no Redis dependency yet), add Redis cache in Phase 5 when WebSockets require it

3. **Admin user creation on first signup**
   - What we know: First user in tenant should be admin; subsequent users are crew by default
   - What's unclear: How to handle organization name during signup vs post-signup profile completion
   - Recommendation: Collect company/organization name during signup, create Tenant record immediately

4. **Password complexity requirements**
   - What we know: Need minimum password strength to prevent weak passwords
   - What's unclear: Specific policy (length, character requirements, entropy calculation)
   - Recommendation: Minimum 8 characters, no character type requirements (allows passphrases), use zxcvbn-style entropy checking in frontend

## Sources

### Primary (HIGH confidence)
- FastAPI official documentation - Authentication, CORS, async patterns
- SQLAlchemy 2.0 documentation - Async engine, RLS session variables, migrations
- PostgreSQL documentation - Row-Level Security, TIMESTAMPTZ, policies
- Alembic documentation - Migration patterns, auto-generation
- Pydantic V2 documentation - Validation, settings management
- OWASP Authentication Cheat Sheet - Token storage, session management

### Secondary (MEDIUM confidence)
- PyJWT documentation - Token creation, verification, algorithm selection
- Passlib documentation - Password hashing with bcrypt
- Multi-tenant SaaS architecture patterns (training data)
- FastAPI dependency injection patterns (training data)

### Tertiary (LOW confidence, marked for validation)
- Email service provider comparisons (needs current pricing/feature research)
- Refresh token storage strategies (needs performance benchmarking)
- Password strength requirements (needs security policy decision)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Versions verified via GitHub/PyPI APIs, patterns from official docs
- Architecture: HIGH - RLS patterns from PostgreSQL docs, FastAPI patterns from official docs
- Pitfalls: HIGH - Well-documented failure modes in multi-tenant auth systems

**Research date:** 2026-05-15
**Valid until:** 2026-07-15 (60 days - stable technologies with slow change rate)

**Ready for planning:** Yes - All critical decisions researched with high confidence
