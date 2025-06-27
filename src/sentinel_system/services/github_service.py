"""
GitHub API service for Sentinel System.

Handles all GitHub API operations including issues, labels, comments, and repository management.
"""

import httpx
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime

from ..config import settings

logger = logging.getLogger(__name__)


class GitHubService:
    """Service for interacting with GitHub API."""
    
    def __init__(self):
        self.base_url = "https://api.github.com"
        self.repo = settings.GITHUB_REPO
        self.headers = {
            "Authorization": f"token {settings.GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "Sentinel-System/0.1.0"
        }
    
    async def get_issues(
        self, 
        label: Optional[str] = None, 
        state: str = "open", 
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get issues from the repository.
        
        Args:
            label: Filter by label
            state: Issue state (open, closed, all)
            limit: Maximum number of issues to return
            
        Returns:
            List of issue dictionaries
        """
        try:
            params = {
                "state": state,
                "per_page": min(limit, 100),  # GitHub API limit
                "sort": "created",
                "direction": "desc"
            }
            
            if label:
                params["labels"] = label
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/repos/{self.repo}/issues",
                    headers=self.headers,
                    params=params
                )
                response.raise_for_status()
                
                issues = response.json()
                logger.info(f"Retrieved {len(issues)} issues from {self.repo}")
                return issues
                
        except httpx.HTTPStatusError as e:
            logger.error(f"GitHub API error: {e.response.status_code} - {e.response.text}")
            raise Exception(f"GitHub API error: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Error fetching issues: {str(e)}")
            raise
    
    async def get_issue(self, issue_number: int) -> Dict[str, Any]:
        """
        Get a specific issue by number.
        
        Args:
            issue_number: Issue number
            
        Returns:
            Issue dictionary
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/repos/{self.repo}/issues/{issue_number}",
                    headers=self.headers
                )
                response.raise_for_status()
                
                issue = response.json()
                logger.info(f"Retrieved issue #{issue_number} from {self.repo}")
                return issue
                
        except httpx.HTTPStatusError as e:
            logger.error(f"GitHub API error: {e.response.status_code} - {e.response.text}")
            raise Exception(f"GitHub API error: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Error fetching issue #{issue_number}: {str(e)}")
            raise
    
    async def add_comment(self, issue_number: int, comment: str) -> Dict[str, Any]:
        """
        Add a comment to an issue.
        
        Args:
            issue_number: Issue number
            comment: Comment text
            
        Returns:
            Comment dictionary
        """
        try:
            data = {"body": comment}
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/repos/{self.repo}/issues/{issue_number}/comments",
                    headers=self.headers,
                    json=data
                )
                response.raise_for_status()
                
                comment_data = response.json()
                logger.info(f"Added comment to issue #{issue_number}")
                return comment_data
                
        except httpx.HTTPStatusError as e:
            logger.error(f"GitHub API error: {e.response.status_code} - {e.response.text}")
            raise Exception(f"GitHub API error: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Error adding comment to issue #{issue_number}: {str(e)}")
            raise
    
    async def add_label(self, issue_number: int, label: str) -> None:
        """
        Add a label to an issue.
        
        Args:
            issue_number: Issue number
            label: Label name
        """
        try:
            data = {"labels": [label]}
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/repos/{self.repo}/issues/{issue_number}/labels",
                    headers=self.headers,
                    json=data
                )
                response.raise_for_status()
                
                logger.info(f"Added label '{label}' to issue #{issue_number}")
                
        except httpx.HTTPStatusError as e:
            logger.error(f"GitHub API error: {e.response.status_code} - {e.response.text}")
            raise Exception(f"GitHub API error: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Error adding label to issue #{issue_number}: {str(e)}")
            raise
    
    async def remove_label(self, issue_number: int, label: str) -> None:
        """
        Remove a label from an issue.
        
        Args:
            issue_number: Issue number
            label: Label name
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.delete(
                    f"{self.base_url}/repos/{self.repo}/issues/{issue_number}/labels/{label}",
                    headers=self.headers
                )
                # 404 is acceptable - label might not exist
                if response.status_code not in [200, 204, 404]:
                    response.raise_for_status()
                
                logger.info(f"Removed label '{label}' from issue #{issue_number}")
                
        except httpx.HTTPStatusError as e:
            if e.response.status_code != 404:  # Ignore 404 for non-existent labels
                logger.error(f"GitHub API error: {e.response.status_code} - {e.response.text}")
                raise Exception(f"GitHub API error: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Error removing label from issue #{issue_number}: {str(e)}")
            raise
    
    async def get_labels(self) -> List[Dict[str, Any]]:
        """
        Get all labels from the repository.
        
        Returns:
            List of label dictionaries
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/repos/{self.repo}/labels",
                    headers=self.headers
                )
                response.raise_for_status()
                
                labels = response.json()
                logger.info(f"Retrieved {len(labels)} labels from {self.repo}")
                return labels
                
        except httpx.HTTPStatusError as e:
            logger.error(f"GitHub API error: {e.response.status_code} - {e.response.text}")
            raise Exception(f"GitHub API error: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Error fetching labels: {str(e)}")
            raise
    
    async def create_pull_request(
        self,
        title: str,
        body: str,
        head: str,
        base: str = "main"
    ) -> Dict[str, Any]:
        """
        Create a pull request.
        
        Args:
            title: PR title
            body: PR description
            head: Source branch
            base: Target branch (default: main)
            
        Returns:
            Pull request dictionary
        """
        try:
            data = {
                "title": title,
                "body": body,
                "head": head,
                "base": base
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/repos/{self.repo}/pulls",
                    headers=self.headers,
                    json=data
                )
                response.raise_for_status()
                
                pr_data = response.json()
                logger.info(f"Created pull request: {pr_data['html_url']}")
                return pr_data
                
        except httpx.HTTPStatusError as e:
            logger.error(f"GitHub API error: {e.response.status_code} - {e.response.text}")
            raise Exception(f"GitHub API error: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Error creating pull request: {str(e)}")
            raise
    
    async def close_issue(self, issue_number: int, reason: str = "completed") -> Dict[str, Any]:
        """
        Close a GitHub issue.
        
        Args:
            issue_number: Issue number to close
            reason: Reason for closing (completed, not_planned)
            
        Returns:
            Updated issue data
        """
        try:
            data = {
                "state": "closed",
                "state_reason": reason
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.patch(
                    f"{self.base_url}/repos/{self.repo}/issues/{issue_number}",
                    headers=self.headers,
                    json=data
                )
                response.raise_for_status()
                
                issue_data = response.json()
                logger.info(f"Closed issue #{issue_number} with reason: {reason}")
                
                return issue_data
                
        except httpx.HTTPStatusError as e:
            logger.error(f"GitHub API error: {e.response.status_code} - {e.response.text}")
            raise Exception(f"GitHub API error: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Error closing issue #{issue_number}: {str(e)}")
            raise 