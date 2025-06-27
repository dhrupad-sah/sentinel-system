"""
GitHub API endpoints for Sentinel System.

Handles GitHub issue management, labeling, and repository operations.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import httpx
from datetime import datetime

from ..config import settings
from ..services.github_service import GitHubService
from ..services.issue_processor import IssueProcessor

router = APIRouter()


class IssueResponse(BaseModel):
    """GitHub issue response model."""
    number: int
    title: str
    body: Optional[str]
    state: str
    labels: List[str]
    created_at: datetime
    updated_at: datetime
    html_url: str


class ProcessIssueRequest(BaseModel):
    """Request model for processing a specific issue."""
    issue_number: int
    force: bool = False


class ProcessIssueResponse(BaseModel):
    """Response model for issue processing."""
    success: bool
    message: str
    issue_number: int
    status: str


@router.get("/issues", response_model=List[IssueResponse])
async def get_issues(
    label: Optional[str] = None,
    state: str = "open",
    limit: int = 10
):
    """
    Get issues from the configured repository.
    
    Args:
        label: Filter by label (defaults to ai-ready label from config)
        state: Issue state (open, closed, all)
        limit: Maximum number of issues to return
    """
    try:
        github_service = GitHubService()
        filter_label = label or settings.GITHUB_ISSUE_LABEL
        
        issues = await github_service.get_issues(
            label=filter_label,
            state=state,
            limit=limit
        )
        
        return [
            IssueResponse(
                number=issue["number"],
                title=issue["title"],
                body=issue.get("body"),
                state=issue["state"],
                labels=[label["name"] for label in issue.get("labels", [])],
                created_at=datetime.fromisoformat(issue["created_at"].replace("Z", "+00:00")),
                updated_at=datetime.fromisoformat(issue["updated_at"].replace("Z", "+00:00")),
                html_url=issue["html_url"]
            )
            for issue in issues
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch issues: {str(e)}")


@router.get("/issues/{issue_number}", response_model=IssueResponse)
async def get_issue(issue_number: int):
    """Get a specific issue by number."""
    try:
        github_service = GitHubService()
        issue = await github_service.get_issue(issue_number)
        
        return IssueResponse(
            number=issue["number"],
            title=issue["title"],
            body=issue.get("body"),
            state=issue["state"],
            labels=[label["name"] for label in issue.get("labels", [])],
            created_at=datetime.fromisoformat(issue["created_at"].replace("Z", "+00:00")),
            updated_at=datetime.fromisoformat(issue["updated_at"].replace("Z", "+00:00")),
            html_url=issue["html_url"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch issue: {str(e)}")


@router.post("/issues/{issue_number}/process", response_model=ProcessIssueResponse)
async def process_issue(
    issue_number: int,
    background_tasks: BackgroundTasks,
    force: bool = False
):
    """
    Process a specific issue with AI.
    
    This endpoint triggers the AI processing workflow for a single issue.
    The processing happens in the background.
    """
    try:
        github_service = GitHubService()
        issue_processor = IssueProcessor()
        
        # Check if issue exists and is in correct state
        issue = await github_service.get_issue(issue_number)
        labels = [label["name"] for label in issue.get("labels", [])]
        
        # Check if issue is ready for processing
        if not force:
            if settings.GITHUB_ISSUE_LABEL not in labels:
                raise HTTPException(
                    status_code=400,
                    detail=f"Issue must have '{settings.GITHUB_ISSUE_LABEL}' label to be processed"
                )
            
            if settings.GITHUB_WORKING_LABEL in labels:
                raise HTTPException(
                    status_code=400,
                    detail="Issue is already being processed"
                )
        
        # Add background task to process the issue
        background_tasks.add_task(
            issue_processor.process_issue,
            issue_number
        )
        
        return ProcessIssueResponse(
            success=True,
            message="Issue processing started",
            issue_number=issue_number,
            status="processing"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start processing: {str(e)}")


@router.post("/issues/{issue_number}/approve")
async def approve_issue_proposal(issue_number: int):
    """
    Approve an AI proposal for an issue.
    
    Adds the approved label and removes the proposal-pending label.
    """
    try:
        github_service = GitHubService()
        
        # Remove proposal pending label and add approved label
        await github_service.remove_label(issue_number, settings.GITHUB_PROPOSAL_LABEL)
        await github_service.add_label(issue_number, settings.GITHUB_APPROVED_LABEL)
        
        return {
            "success": True,
            "message": "Issue proposal approved",
            "issue_number": issue_number
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to approve proposal: {str(e)}")


@router.post("/issues/{issue_number}/reject")
async def reject_issue_proposal(issue_number: int, feedback: Optional[str] = None):
    """
    Reject an AI proposal for an issue.
    
    Removes the proposal-pending label and optionally adds feedback comment.
    """
    try:
        github_service = GitHubService()
        
        # Remove proposal pending label
        await github_service.remove_label(issue_number, settings.GITHUB_PROPOSAL_LABEL)
        
        # Add feedback comment if provided
        if feedback:
            comment = f"🤖 **Sentinel System - Proposal Rejected**\n\n{feedback}\n\nPlease revise your proposal."
            await github_service.add_comment(issue_number, comment)
        
        return {
            "success": True,
            "message": "Issue proposal rejected",
            "issue_number": issue_number
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reject proposal: {str(e)}")


@router.get("/labels")
async def get_repository_labels():
    """Get all labels from the configured repository."""
    try:
        github_service = GitHubService()
        labels = await github_service.get_labels()
        
        return {
            "labels": [
                {
                    "name": label["name"],
                    "color": label["color"],
                    "description": label.get("description")
                }
                for label in labels
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch labels: {str(e)}")


@router.post("/issues/{issue_number}/close")
async def close_issue(issue_number: int, reason: str = "completed"):
    """
    Close a specific issue.
    
    Args:
        issue_number: Issue number to close
        reason: Reason for closing (completed, not_planned)
    """
    try:
        github_service = GitHubService()
        result = await github_service.close_issue(issue_number, reason)
        
        return {
            "success": True,
            "message": f"Issue #{issue_number} closed successfully",
            "issue_number": issue_number,
            "reason": reason,
            "state": result["state"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to close issue: {str(e)}")


@router.get("/status")
async def get_github_status():
    """Get GitHub service status and configuration."""
    return {
        "configured": bool(settings.GITHUB_TOKEN and settings.GITHUB_REPO),
        "repository": settings.GITHUB_REPO,
        "labels": {
            "ready": settings.GITHUB_ISSUE_LABEL,
            "proposal_pending": settings.GITHUB_PROPOSAL_LABEL,
            "approved": settings.GITHUB_APPROVED_LABEL,
            "working": settings.GITHUB_WORKING_LABEL
        }
    } 