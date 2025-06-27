"""
Issue processor service for Sentinel System.

Orchestrates the entire workflow from issue analysis to implementation.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

from .github_service import GitHubService
from .gemini_service import GeminiService
from .git_service import GitService
from ..config import settings

logger = logging.getLogger(__name__)


class IssueProcessor:
    """Service for processing GitHub issues with AI assistance."""
    
    def __init__(self):
        self.github_service = GitHubService()
        self.gemini_service = GeminiService()
        self.git_service = GitService()
    
    async def process_issue(self, issue_number: int) -> Dict[str, Any]:
        """
        Process a GitHub issue through the complete workflow.
        
        Args:
            issue_number: The issue number to process
            
        Returns:
            Processing result dictionary
        """
        try:
            logger.info(f"Starting processing for issue #{issue_number}")
            
            # Get the issue details
            issue = await self.github_service.get_issue(issue_number)
            issue_title = issue["title"]
            issue_body = issue.get("body", "")
            labels = [label["name"] for label in issue.get("labels", [])]
            
            logger.info(f"Processing issue #{issue_number}: {issue_title}")
            
            # Check if issue is in correct state
            if settings.GITHUB_WORKING_LABEL in labels:
                logger.warning(f"Issue #{issue_number} is already being processed")
                return {"status": "already_processing", "message": "Issue is already being processed"}
            
            # Add working label
            await self.github_service.add_label(issue_number, settings.GITHUB_WORKING_LABEL)
            
            try:
                # Check if this is a proposal phase or implementation phase
                if settings.GITHUB_APPROVED_LABEL in labels:
                    # Implementation phase
                    result = await self._implement_approved_solution(issue_number, issue_title, issue_body)
                else:
                    # Analysis and proposal phase
                    result = await self._analyze_and_propose(issue_number, issue_title, issue_body)
                
                # Remove working label on success
                await self.github_service.remove_label(issue_number, settings.GITHUB_WORKING_LABEL)
                
                logger.info(f"Successfully processed issue #{issue_number}")
                return result
                
            except Exception as e:
                # Remove working label on error
                await self.github_service.remove_label(issue_number, settings.GITHUB_WORKING_LABEL)
                
                # Add error comment
                error_comment = f"🚨 **Sentinel System - Processing Error**\n\nAn error occurred while processing this issue:\n\n```\n{str(e)}\n```\n\nPlease check the system logs for more details."
                await self.github_service.add_comment(issue_number, error_comment)
                
                raise
            
        except Exception as e:
            logger.error(f"Error processing issue #{issue_number}: {str(e)}")
            raise
    
    async def _analyze_and_propose(self, issue_number: int, issue_title: str, issue_body: str) -> Dict[str, Any]:
        """
        Analyze issue and create proposal.
        
        Args:
            issue_number: Issue number
            issue_title: Issue title
            issue_body: Issue description
            
        Returns:
            Analysis result
        """
        try:
            logger.info(f"Analyzing issue #{issue_number}")
            
            # Get AI analysis and proposal
            proposal = await self.gemini_service.analyze_issue(issue_title, issue_body, issue_number)
            
            # Create proposal comment
            comment = f"""🤖 **Sentinel System - Issue Analysis & Proposal**

## My Understanding
I've analyzed issue #{issue_number} and here's my assessment:

{proposal}

---

**Next Steps:**
- 👍 If you approve this proposal, add the `{settings.GITHUB_APPROVED_LABEL}` label
- 👎 If you want changes, remove the `{settings.GITHUB_PROPOSAL_LABEL}` label and add feedback
- 🔄 I'll refine the proposal based on your feedback

*Generated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}*
"""
            
            # Add comment to issue
            await self.github_service.add_comment(issue_number, comment)
            
            # Add proposal pending label
            await self.github_service.add_label(issue_number, settings.GITHUB_PROPOSAL_LABEL)
            
            # Remove ready label since we've started processing
            await self.github_service.remove_label(issue_number, settings.GITHUB_ISSUE_LABEL)
            
            logger.info(f"Created proposal for issue #{issue_number}")
            
            return {
                "status": "proposal_created",
                "message": "AI proposal created and awaiting human review",
                "proposal": proposal
            }
            
        except Exception as e:
            logger.error(f"Error analyzing issue #{issue_number}: {str(e)}")
            raise
    
    async def _implement_approved_solution(self, issue_number: int, issue_title: str, issue_body: str) -> Dict[str, Any]:
        """
        Implement the approved solution.
        
        Args:
            issue_number: Issue number
            issue_title: Issue title
            issue_body: Issue description
            
        Returns:
            Implementation result
        """
        try:
            logger.info(f"Implementing approved solution for issue #{issue_number}")
            
            # Get the approved proposal from comments
            # For now, we'll use a placeholder - in a real implementation,
            # we'd parse the comments to find the approved proposal
            approved_proposal = "Approved proposal from previous analysis"
            
            # Create branch for this issue
            branch_name = f"{settings.GIT_BRANCH_PREFIX}{issue_number}"
            await self.git_service.create_branch(branch_name)
            
            # Get AI to implement the solution
            implementation = await self.gemini_service.implement_solution(
                issue_title, issue_body, approved_proposal, issue_number
            )
            
            # Check if there are any changes to commit
            has_changes = await self.git_service.has_changes()
            
            if has_changes:
                # Commit changes
                commit_message = f"{settings.GIT_COMMIT_PREFIX}resolve issue #{issue_number}: {issue_title}"
                await self.git_service.commit_changes(commit_message)
                
                # Push branch
                await self.git_service.push_branch(branch_name)
                
                # Create pull request
                pr_title = f"Fix issue #{issue_number}: {issue_title}"
                pr_body = f"""Resolves #{issue_number}

## Implementation Summary

{implementation}

## Changes Made
- Implemented solution as approved in issue #{issue_number}
- All changes are focused on resolving the specific issue

**Auto-generated by Sentinel System**
"""
                
                pr = await self.github_service.create_pull_request(
                    title=pr_title,
                    body=pr_body,
                    head=branch_name,
                    base="main"
                )
                
                # Add completion comment to issue
                completion_comment = f"""✅ **Sentinel System - Implementation Complete**

## Solution Implemented

{implementation}

## Pull Request Created
🔗 **Pull Request:** {pr['html_url']}

The solution has been implemented and is ready for review. The PR contains all necessary changes to resolve this issue.

*Completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}*
"""
                
                await self.github_service.add_comment(issue_number, completion_comment)
                
                # Remove labels
                await self.github_service.remove_label(issue_number, settings.GITHUB_APPROVED_LABEL)
                
                logger.info(f"Successfully implemented solution for issue #{issue_number}, PR: {pr['html_url']}")
                
                return {
                    "status": "implemented",
                    "message": "Solution implemented and PR created",
                    "pull_request_url": pr['html_url'],
                    "branch": branch_name
                }
            else:
                # No changes were made
                no_changes_comment = f"""ℹ️ **Sentinel System - No Changes Required**

After analyzing the issue and attempting implementation, no code changes were required. This might mean:

- The issue was already resolved
- The solution doesn't require code changes
- The issue needs clarification

{implementation}

*Completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}*
"""
                
                await self.github_service.add_comment(issue_number, no_changes_comment)
                await self.github_service.remove_label(issue_number, settings.GITHUB_APPROVED_LABEL)
                
                return {
                    "status": "no_changes",
                    "message": "No code changes were required",
                    "implementation": implementation
                }
            
        except Exception as e:
            logger.error(f"Error implementing solution for issue #{issue_number}: {str(e)}")
            raise
    
    async def refine_proposal(self, issue_number: int, feedback: str) -> Dict[str, Any]:
        """
        Refine a proposal based on human feedback.
        
        Args:
            issue_number: Issue number
            feedback: Human feedback on the proposal
            
        Returns:
            Refinement result
        """
        try:
            logger.info(f"Refining proposal for issue #{issue_number}")
            
            # Get issue details
            issue = await self.github_service.get_issue(issue_number)
            issue_title = issue["title"]
            issue_body = issue.get("body", "")
            
            # For now, use placeholder for previous proposal
            # In real implementation, we'd parse comments to get the previous proposal
            previous_proposal = "Previous proposal from earlier analysis"
            
            # Get refined proposal
            refined_proposal = await self.gemini_service.refine_proposal(
                issue_title, issue_body, previous_proposal, feedback, issue_number
            )
            
            # Create refined proposal comment
            comment = f"""🔄 **Sentinel System - Refined Proposal**

Based on your feedback, I've refined my proposal:

## Refined Solution

{refined_proposal}

---

**Next Steps:**
- 👍 If you approve this refined proposal, add the `{settings.GITHUB_APPROVED_LABEL}` label
- 👎 If you want further changes, provide additional feedback

*Refined at {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}*
"""
            
            # Add refined proposal comment
            await self.github_service.add_comment(issue_number, comment)
            
            # Re-add proposal pending label
            await self.github_service.add_label(issue_number, settings.GITHUB_PROPOSAL_LABEL)
            
            logger.info(f"Refined proposal for issue #{issue_number}")
            
            return {
                "status": "proposal_refined",
                "message": "Proposal refined based on feedback",
                "refined_proposal": refined_proposal
            }
            
        except Exception as e:
            logger.error(f"Error refining proposal for issue #{issue_number}: {str(e)}")
            raise 