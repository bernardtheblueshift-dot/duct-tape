from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from app.config import settings
from app.api.v1 import auth, invitations, jobs, crew, equipment, assignments, calendar, ical, messages, websocket, tasks, files, notifications, portal

# Create FastAPI application
app = FastAPI(
    title="GT API",
    version="1.0.0",
    docs_url="/api/docs" if settings.DEBUG else None,
    redoc_url=None if not settings.DEBUG else "/api/redoc",
)

# Add rate limiter
limiter = Limiter(key_func=get_remote_address, default_limits=["200/minute"])
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Cookie"],
)

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request as StarletteRequest
from starlette.responses import Response as StarletteResponse


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: StarletteRequest, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        if not settings.DEBUG:
            response.headers["Content-Security-Policy"] = "default-src 'self'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src https://fonts.gstatic.com; connect-src 'self' wss: ws:; img-src 'self' data:; script-src 'self'"
        if request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response


app.add_middleware(SecurityHeadersMiddleware)

# Include routers
app.include_router(auth.router)
app.include_router(invitations.router)
app.include_router(jobs.router)
app.include_router(crew.router)
app.include_router(equipment.router)
app.include_router(assignments.router)
app.include_router(calendar.router)
app.include_router(ical.router)  # Admin token management
app.include_router(ical.feed_router)  # Public feed endpoint
app.include_router(messages.router)
app.include_router(websocket.router)
app.include_router(tasks.router)
app.include_router(files.job_files_router)  # Job-scoped file operations
app.include_router(files.files_router)  # File-scoped operations
app.include_router(notifications.router)
app.include_router(portal.router)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}
