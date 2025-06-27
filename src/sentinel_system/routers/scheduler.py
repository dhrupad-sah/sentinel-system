"""
Scheduler endpoints for Sentinel System.

Manages the automated issue processing scheduler.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
import asyncio

from ..config import settings
from ..services.scheduler_service import SchedulerService

router = APIRouter()


class SchedulerStatus(BaseModel):
    """Scheduler status response model."""
    enabled: bool
    running: bool
    interval_minutes: int
    last_run: Optional[datetime]
    next_run: Optional[datetime]
    total_runs: int
    issues_processed: int


class SchedulerConfig(BaseModel):
    """Scheduler configuration model."""
    enabled: bool
    interval_minutes: int


@router.get("/status", response_model=SchedulerStatus)
async def get_scheduler_status():
    """Get current scheduler status and statistics."""
    try:
        scheduler_service = SchedulerService()
        status = await scheduler_service.get_status()
        
        return SchedulerStatus(
            enabled=status["enabled"],
            running=status["running"],
            interval_minutes=status["interval_minutes"],
            last_run=status.get("last_run"),
            next_run=status.get("next_run"),
            total_runs=status.get("total_runs", 0),
            issues_processed=status.get("issues_processed", 0)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get scheduler status: {str(e)}")


@router.post("/start")
async def start_scheduler():
    """Start the automated issue processing scheduler."""
    try:
        scheduler_service = SchedulerService()
        result = await scheduler_service.start()
        
        return {
            "success": True,
            "message": "Scheduler started successfully",
            "interval_minutes": settings.SCHEDULER_INTERVAL_MINUTES
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start scheduler: {str(e)}")


@router.post("/stop")
async def stop_scheduler():
    """Stop the automated issue processing scheduler."""
    try:
        scheduler_service = SchedulerService()
        result = await scheduler_service.stop()
        
        return {
            "success": True,
            "message": "Scheduler stopped successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to stop scheduler: {str(e)}")


@router.post("/run-now")
async def run_scheduler_now():
    """Trigger an immediate scheduler run (manual execution)."""
    try:
        scheduler_service = SchedulerService()
        result = await scheduler_service.run_now()
        
        return {
            "success": True,
            "message": "Scheduler run triggered",
            "issues_found": result.get("issues_found", 0),
            "issues_processed": result.get("issues_processed", 0)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to run scheduler: {str(e)}")


@router.put("/config")
async def update_scheduler_config(config: SchedulerConfig):
    """Update scheduler configuration."""
    try:
        scheduler_service = SchedulerService()
        result = await scheduler_service.update_config(
            enabled=config.enabled,
            interval_minutes=config.interval_minutes
        )
        
        return {
            "success": True,
            "message": "Scheduler configuration updated",
            "config": {
                "enabled": config.enabled,
                "interval_minutes": config.interval_minutes
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update scheduler config: {str(e)}")


@router.get("/logs")
async def get_scheduler_logs(limit: int = 50):
    """Get recent scheduler execution logs."""
    try:
        scheduler_service = SchedulerService()
        logs = await scheduler_service.get_logs(limit=limit)
        
        return {
            "logs": logs,
            "total": len(logs)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get scheduler logs: {str(e)}")


@router.delete("/logs")
async def clear_scheduler_logs():
    """Clear scheduler execution logs."""
    try:
        scheduler_service = SchedulerService()
        await scheduler_service.clear_logs()
        
        return {
            "success": True,
            "message": "Scheduler logs cleared"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear scheduler logs: {str(e)}") 