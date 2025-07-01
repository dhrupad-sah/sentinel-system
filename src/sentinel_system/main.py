"""
Sentinel System - Autonomous GitHub Issue Resolution System

Main FastAPI application entry point.
"""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings, configure_logging
from .routers import github, health, webhook

# Configure logging as early as possible
configure_logging()
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Sentinel System",
    description="Autonomous GitHub issue resolution system using Claude Code CLI",
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
app.include_router(webhook.router, prefix="/webhook", tags=["webhook"])


@app.get("/")
async def root():
    """Root endpoint with basic system information."""
    logger.info("Root endpoint accessed.")
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
    logger.info("🚀 Sentinel System starting up...")
    logger.info(f"📊 Debug mode: {settings.DEBUG}")
    logger.info(f"🎯 Target repository: {settings.GITHUB_REPO}")


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event."""
    logger.info("🛑 Sentinel System shutting down...") 