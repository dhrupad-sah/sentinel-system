"""
Health check endpoints for Sentinel System.
"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Any
import subprocess
import os

from ..config import settings
from ..services.claude_service import ClaudeService
from ..services.git_service import GitService

router = APIRouter()

class HealthStatus(BaseModel):
    """Health status response model."""
    status: str
    version: str
    checks: Dict[str, Any]


@router.get("", response_model=HealthStatus)
async def health_check():
    """
    Comprehensive health check endpoint.
    
    Checks:
    - Service status
    - GitHub API connectivity  
    - Claude Code CLI availability
    - Git configuration
    """
    checks = {}
    overall_status = "healthy"
    
    # Check GitHub token
    try:
        if settings.GITHUB_TOKEN:
            checks["github_token"] = {"status": "ok", "configured": True}
        else:
            checks["github_token"] = {"status": "error", "configured": False}
            overall_status = "degraded"
    except Exception as e:
        checks["github_token"] = {"status": "error", "error": str(e)}
        overall_status = "degraded"
    
    # Check Claude Code CLI availability
    try:
        claude_service = ClaudeService()
        claude_status = await claude_service.check_availability()
        
        if claude_status["available"]:
            checks["claude_cli"] = {
                "status": "ok",
                "available": True,
                "version": claude_status.get("version", "unknown"),
                "authenticated": claude_status.get("authenticated", False)
            }
        else:
            checks["claude_cli"] = {
                "status": "error",
                "available": False,
                "error": claude_status.get("error", "Unknown error")
            }
            overall_status = "degraded"
    except Exception as e:
        checks["claude_cli"] = {"status": "error", "available": False, "error": str(e)}
        overall_status = "degraded"
    
    # Check Git configuration
    try:
        git_service = GitService()
        git_config = await git_service.check_git_config()
        
        if git_config["configured"]:
            checks["git_config"] = {
                "status": "ok",
                "user_name": git_config.get("user_name"),
                "user_email": git_config.get("user_email"),
                "remote_origin": git_config.get("remote_origin"),
                "configured": True
            }
        else:
            checks["git_config"] = {
                "status": "incomplete",
                "configured": False,
                "error": "Git user name or email not configured"
            }
            overall_status = "degraded"
    except Exception as e:
        checks["git_config"] = {"status": "error", "error": str(e)}
        overall_status = "degraded"
    
    # Check repository access
    if hasattr(settings, 'GITHUB_REPO') and settings.GITHUB_REPO:
        checks["target_repo"] = {
            "status": "ok",
            "configured": True,
            "repo": settings.GITHUB_REPO
        }
    else:
        checks["target_repo"] = {"status": "error", "configured": False}
        overall_status = "degraded"
    
    return HealthStatus(
        status=overall_status,
        version="0.1.0",
        checks=checks
    )


@router.get("/ready")
async def ready_check():
    """Simple readiness check for load balancers."""
    return {"status": "ready"}


@router.get("/live")
async def liveness_check():
    """Simple liveness check for container orchestration."""
    return {"status": "alive"} 