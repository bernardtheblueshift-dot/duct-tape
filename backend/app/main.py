from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api.v1 import auth, invitations

# Create FastAPI application
app = FastAPI(
    title="Duct Tape API",
    version="1.0.0",
    docs_url="/api/docs",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(invitations.router)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}
