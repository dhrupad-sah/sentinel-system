"""
Scheduler service for Sentinel System.

Manages automated issue processing with configurable intervals.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import json
from pathlib import Path

from .github_service import GitHubService
from .issue_processor import IssueProcessor
from ..config import settings

logger = logging.getLogger(__name__)


class SchedulerService:
    """Service for managing automated issue processing."""
    
    def __init__(self):
        self.github_service = GitHubService()
        self.issue_processor = IssueProcessor()
        self.is_running = False
        self.task: Optional[asyncio.Task] = None
        self.stats = {
            "total_runs": 0,
            "issues_processed": 0,
            "last_run": None,
            "next_run": None,
            "enabled": settings.SCHEDULER_ENABLED,
            "interval_minutes": settings.SCHEDULER_INTERVAL_MINUTES
        }
        self.logs: List[Dict[str, Any]] = []
        self.max_logs = 100  # Keep last 100 log entries
    
    async def start(self) -> Dict[str, Any]:
        """
        Start the scheduler.
        
        Returns:
            Start result
        """
        try:
            if self.is_running:
                logger.warning("Scheduler is already running")
                return {"success": False, "message": "Scheduler is already running"}
            
            logger.info("Starting scheduler")
            self.is_running = True
            self.stats["enabled"] = True
            
            # Start the scheduler task
            self.task = asyncio.create_task(self._scheduler_loop())
            
            # Update next run time
            self.stats["next_run"] = datetime.now() + timedelta(minutes=self.stats["interval_minutes"])
            
            self._add_log("info", "Scheduler started", {"interval_minutes": self.stats["interval_minutes"]})
            
            return {"success": True, "message": "Scheduler started successfully"}
            
        except Exception as e:
            logger.error(f"Error starting scheduler: {str(e)}")
            self.is_running = False
            self.stats["enabled"] = False
            raise
    
    async def stop(self) -> Dict[str, Any]:
        """
        Stop the scheduler.
        
        Returns:
            Stop result
        """
        try:
            if not self.is_running:
                logger.warning("Scheduler is not running")
                return {"success": False, "message": "Scheduler is not running"}
            
            logger.info("Stopping scheduler")
            self.is_running = False
            self.stats["enabled"] = False
            self.stats["next_run"] = None
            
            # Cancel the scheduler task
            if self.task and not self.task.done():
                self.task.cancel()
                try:
                    await self.task
                except asyncio.CancelledError:
                    pass
            
            self._add_log("info", "Scheduler stopped")
            
            return {"success": True, "message": "Scheduler stopped successfully"}
            
        except Exception as e:
            logger.error(f"Error stopping scheduler: {str(e)}")
            raise
    
    async def run_now(self) -> Dict[str, Any]:
        """
        Trigger an immediate scheduler run.
        
        Returns:
            Run result
        """
        try:
            logger.info("Running scheduler manually")
            result = await self._process_ready_issues()
            
            self._add_log("info", "Manual scheduler run completed", {
                "issues_found": result.get("issues_found", 0),
                "issues_processed": result.get("issues_processed", 0)
            })
            
            return result
            
        except Exception as e:
            logger.error(f"Error running scheduler manually: {str(e)}")
            self._add_log("error", f"Manual scheduler run failed: {str(e)}")
            raise
    
    async def update_config(self, enabled: bool, interval_minutes: int) -> Dict[str, Any]:
        """
        Update scheduler configuration.
        
        Args:
            enabled: Whether scheduler should be enabled
            interval_minutes: Interval between runs in minutes
            
        Returns:
            Update result
        """
        try:
            logger.info(f"Updating scheduler config: enabled={enabled}, interval={interval_minutes}")
            
            old_enabled = self.stats["enabled"]
            old_interval = self.stats["interval_minutes"]
            
            self.stats["interval_minutes"] = interval_minutes
            
            # If enabling and not currently running, start it
            if enabled and not self.is_running:
                await self.start()
            # If disabling and currently running, stop it
            elif not enabled and self.is_running:
                await self.stop()
            # If running and interval changed, restart with new interval
            elif self.is_running and interval_minutes != old_interval:
                await self.stop()
                await self.start()
            
            self._add_log("info", "Scheduler configuration updated", {
                "old_enabled": old_enabled,
                "new_enabled": enabled,
                "old_interval": old_interval,
                "new_interval": interval_minutes
            })
            
            return {"success": True, "message": "Configuration updated successfully"}
            
        except Exception as e:
            logger.error(f"Error updating scheduler config: {str(e)}")
            raise
    
    async def get_status(self) -> Dict[str, Any]:
        """
        Get current scheduler status.
        
        Returns:
            Status dictionary
        """
        return {
            "enabled": self.stats["enabled"],
            "running": self.is_running,
            "interval_minutes": self.stats["interval_minutes"],
            "last_run": self.stats["last_run"],
            "next_run": self.stats["next_run"],
            "total_runs": self.stats["total_runs"],
            "issues_processed": self.stats["issues_processed"]
        }
    
    async def get_logs(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get recent scheduler logs.
        
        Args:
            limit: Maximum number of logs to return
            
        Returns:
            List of log entries
        """
        return self.logs[-limit:] if limit > 0 else self.logs
    
    async def clear_logs(self) -> None:
        """Clear scheduler logs."""
        self.logs.clear()
        logger.info("Scheduler logs cleared")
    
    async def _scheduler_loop(self) -> None:
        """Main scheduler loop."""
        try:
            while self.is_running:
                try:
                    # Wait for the interval
                    await asyncio.sleep(self.stats["interval_minutes"] * 60)
                    
                    if not self.is_running:
                        break
                    
                    # Process ready issues
                    result = await self._process_ready_issues()
                    
                    # Update next run time
                    self.stats["next_run"] = datetime.now() + timedelta(minutes=self.stats["interval_minutes"])
                    
                    self._add_log("info", "Scheduled run completed", {
                        "issues_found": result.get("issues_found", 0),
                        "issues_processed": result.get("issues_processed", 0)
                    })
                    
                except asyncio.CancelledError:
                    logger.info("Scheduler loop cancelled")
                    break
                except Exception as e:
                    logger.error(f"Error in scheduler loop: {str(e)}")
                    self._add_log("error", f"Scheduler loop error: {str(e)}")
                    # Continue running even if there's an error
                    
        except Exception as e:
            logger.error(f"Fatal error in scheduler loop: {str(e)}")
            self.is_running = False
            self.stats["enabled"] = False
    
    async def _process_ready_issues(self) -> Dict[str, Any]:
        """
        Process all ready issues.
        
        Returns:
            Processing result
        """
        try:
            start_time = datetime.now()
            self.stats["last_run"] = start_time
            self.stats["total_runs"] += 1
            
            logger.info("Processing ready issues")
            
            # Get issues with the ready label
            issues = await self.github_service.get_issues(
                label=settings.GITHUB_ISSUE_LABEL,
                state="open",
                limit=50  # Process up to 50 issues per run
            )
            
            # Also get approved issues that need implementation
            approved_issues = await self.github_service.get_issues(
                label=settings.GITHUB_APPROVED_LABEL,
                state="open",
                limit=50
            )
            
            all_issues = issues + approved_issues
            issues_found = len(all_issues)
            issues_processed = 0
            processing_errors = []
            
            logger.info(f"Found {issues_found} issues to process")
            
            # Process each issue
            for issue in all_issues:
                try:
                    issue_number = issue["number"]
                    labels = [label["name"] for label in issue.get("labels", [])]
                    
                    # Skip if already being processed
                    if settings.GITHUB_WORKING_LABEL in labels:
                        logger.debug(f"Skipping issue #{issue_number} - already being processed")
                        continue
                    
                    logger.info(f"Processing issue #{issue_number}: {issue['title']}")
                    
                    # Process the issue
                    result = await self.issue_processor.process_issue(issue_number)
                    
                    if result.get("status") != "already_processing":
                        issues_processed += 1
                    
                    logger.info(f"Successfully processed issue #{issue_number}")
                    
                except Exception as e:
                    error_msg = f"Error processing issue #{issue.get('number', 'unknown')}: {str(e)}"
                    logger.error(error_msg)
                    processing_errors.append(error_msg)
                    continue
            
            # Update stats
            self.stats["issues_processed"] += issues_processed
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            result = {
                "issues_found": issues_found,
                "issues_processed": issues_processed,
                "processing_errors": processing_errors,
                "duration_seconds": duration,
                "start_time": start_time,
                "end_time": end_time
            }
            
            logger.info(f"Processed {issues_processed}/{issues_found} issues in {duration:.2f} seconds")
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing ready issues: {str(e)}")
            raise
    
    def _add_log(self, level: str, message: str, data: Optional[Dict[str, Any]] = None) -> None:
        """
        Add a log entry.
        
        Args:
            level: Log level (info, warning, error)
            message: Log message
            data: Additional data
        """
        log_entry = {
            "timestamp": datetime.now(),
            "level": level,
            "message": message,
            "data": data or {}
        }
        
        self.logs.append(log_entry)
        
        # Keep only the last max_logs entries
        if len(self.logs) > self.max_logs:
            self.logs = self.logs[-self.max_logs:]
        
        # Also log to standard logger
        log_func = getattr(logger, level, logger.info)
        log_func(f"Scheduler: {message} {data or ''}") 