"""
Sentinel System - Autonomous GitHub Issue Resolution System

Main FastAPI application entry point.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .routers import github, scheduler, health

app = FastAPI(
    title="Sentinel System",
    description="Autonomous GitHub issue resolution system using Gemini CLI",
    version="0.1.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(github.router, prefix="/github", tags=["github"])
app.include_router(scheduler.router, prefix="/scheduler", tags=["scheduler"])


@app.get("/")
async def root():
    """Root endpoint with basic system information."""
    return {
        "name": "Sentinel System",
        "version": "0.1.0",
        "description": "Autonomous GitHub issue resolution system",
        "status": "running",
        "docs": "/docs" if settings.DEBUG else "disabled",
    }


@app.on_event("startup")
async def startup_event():
    """Application startup event."""
    print("🚀 Sentinel System starting up...")
    print(f"📊 Debug mode: {settings.DEBUG}")
    print(f"🎯 Target repository: {settings.GITHUB_REPO}")


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event."""
    print("🛑 Sentinel System shutting down...") 