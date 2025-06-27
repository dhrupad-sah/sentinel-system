"""
Git service for Sentinel System.

Handles all git operations including branch creation, commits, and pushes.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
import os
from pathlib import Path

logger = logging.getLogger(__name__)


class GitService:
    """Service for handling git operations."""
    
    def __init__(self, repo_path: Optional[str] = None):
        """
        Initialize Git service.
        
        Args:
            repo_path: Path to git repository (defaults to current directory)
        """
        self.repo_path = repo_path or os.getcwd()
        
    async def _run_git_command(self, *args: str) -> str:
        """
        Run a git command asynchronously.
        
        Args:
            *args: Git command arguments
            
        Returns:
            Command output
        """
        try:
            cmd = ["git"] + list(args)
            logger.debug(f"Running git command: {' '.join(cmd)}")
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.repo_path
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                error_msg = stderr.decode('utf-8') if stderr else "Unknown git error"
                logger.error(f"Git command failed: {error_msg}")
                raise Exception(f"Git command failed: {error_msg}")
            
            output = stdout.decode('utf-8').strip()
            logger.debug(f"Git command output: {output}")
            return output
            
        except Exception as e:
            logger.error(f"Error running git command: {str(e)}")
            raise
    
    async def get_current_branch(self) -> str:
        """
        Get the current branch name.
        
        Returns:
            Current branch name
        """
        try:
            output = await self._run_git_command("branch", "--show-current")
            return output.strip()
        except Exception as e:
            logger.error(f"Error getting current branch: {str(e)}")
            raise
    
    async def create_branch(self, branch_name: str, from_branch: str = "main") -> None:
        """
        Create and checkout a new branch.
        
        Args:
            branch_name: Name of the new branch
            from_branch: Base branch to create from (default: main)
        """
        try:
            logger.info(f"Creating branch '{branch_name}' from '{from_branch}'")
            
            # Check if there are uncommitted changes
            if await self.has_changes():
                logger.warning("Uncommitted changes detected, stashing them")
                await self._run_git_command("stash", "push", "-m", f"Auto-stash before creating branch {branch_name}")
            
            # Ensure we're on the base branch and it's up to date
            await self._run_git_command("checkout", from_branch)
            await self._run_git_command("pull", "origin", from_branch)
            
            # Create and checkout new branch
            await self._run_git_command("checkout", "-b", branch_name)
            
            logger.info(f"Successfully created and checked out branch '{branch_name}'")
            
        except Exception as e:
            logger.error(f"Error creating branch '{branch_name}': {str(e)}")
            raise
    
    async def has_changes(self) -> bool:
        """
        Check if there are any uncommitted changes.
        
        Returns:
            True if there are changes, False otherwise
        """
        try:
            # Check for staged changes
            staged_output = await self._run_git_command("diff", "--cached", "--name-only")
            
            # Check for unstaged changes
            unstaged_output = await self._run_git_command("diff", "--name-only")
            
            # Check for untracked files
            untracked_output = await self._run_git_command("ls-files", "--others", "--exclude-standard")
            
            has_changes = bool(staged_output or unstaged_output or untracked_output)
            logger.debug(f"Repository has changes: {has_changes}")
            
            return has_changes
            
        except Exception as e:
            logger.error(f"Error checking for changes: {str(e)}")
            raise
    
    async def add_all_changes(self) -> None:
        """Add all changes to staging area."""
        try:
            await self._run_git_command("add", ".")
            logger.info("Added all changes to staging area")
        except Exception as e:
            logger.error(f"Error adding changes: {str(e)}")
            raise
    
    async def commit_changes(self, message: str) -> str:
        """
        Commit staged changes.
        
        Args:
            message: Commit message
            
        Returns:
            Commit hash
        """
        try:
            logger.info(f"Committing changes with message: {message}")
            
            # Add all changes first
            await self.add_all_changes()
            
            # Commit changes
            await self._run_git_command("commit", "-m", message)
            
            # Get commit hash
            commit_hash = await self._run_git_command("rev-parse", "HEAD")
            
            logger.info(f"Successfully committed changes: {commit_hash}")
            return commit_hash
            
        except Exception as e:
            logger.error(f"Error committing changes: {str(e)}")
            raise
    
    async def push_branch(self, branch_name: str, remote: str = "origin") -> None:
        """
        Push branch to remote repository.
        
        Args:
            branch_name: Name of the branch to push
            remote: Remote name (default: origin)
        """
        try:
            logger.info(f"Pushing branch '{branch_name}' to '{remote}'")
            
            # Push branch with upstream tracking
            await self._run_git_command("push", "-u", remote, branch_name)
            
            logger.info(f"Successfully pushed branch '{branch_name}' to '{remote}'")
            
        except Exception as e:
            logger.error(f"Error pushing branch '{branch_name}': {str(e)}")
            raise
    
    async def get_changed_files(self) -> List[str]:
        """
        Get list of changed files.
        
        Returns:
            List of changed file paths
        """
        try:
            # Get staged files
            staged_files = await self._run_git_command("diff", "--cached", "--name-only")
            
            # Get unstaged files
            unstaged_files = await self._run_git_command("diff", "--name-only")
            
            # Get untracked files
            untracked_files = await self._run_git_command("ls-files", "--others", "--exclude-standard")
            
            all_files = []
            if staged_files:
                all_files.extend(staged_files.split('\n'))
            if unstaged_files:
                all_files.extend(unstaged_files.split('\n'))
            if untracked_files:
                all_files.extend(untracked_files.split('\n'))
            
            # Remove duplicates and empty strings
            changed_files = list(set(f for f in all_files if f))
            
            logger.debug(f"Changed files: {changed_files}")
            return changed_files
            
        except Exception as e:
            logger.error(f"Error getting changed files: {str(e)}")
            raise
    
    async def get_branch_status(self) -> Dict[str, Any]:
        """
        Get detailed status of the current branch.
        
        Returns:
            Status dictionary with branch information
        """
        try:
            current_branch = await self.get_current_branch()
            has_changes = await self.has_changes()
            changed_files = await self.get_changed_files()
            
            # Get last commit info
            try:
                last_commit = await self._run_git_command("log", "-1", "--pretty=format:%H|%an|%ad|%s", "--date=iso")
                commit_parts = last_commit.split('|', 3)
                last_commit_info = {
                    "hash": commit_parts[0] if len(commit_parts) > 0 else "",
                    "author": commit_parts[1] if len(commit_parts) > 1 else "",
                    "date": commit_parts[2] if len(commit_parts) > 2 else "",
                    "message": commit_parts[3] if len(commit_parts) > 3 else ""
                }
            except Exception:
                last_commit_info = None
            
            status = {
                "current_branch": current_branch,
                "has_changes": has_changes,
                "changed_files": changed_files,
                "changed_files_count": len(changed_files),
                "last_commit": last_commit_info,
                "repo_path": self.repo_path
            }
            
            logger.debug(f"Branch status: {status}")
            return status
            
        except Exception as e:
            logger.error(f"Error getting branch status: {str(e)}")
            raise
    
    async def cleanup_branch(self, branch_name: str, remote: str = "origin") -> None:
        """
        Clean up a branch (checkout main and delete the branch).
        
        Args:
            branch_name: Name of the branch to clean up
            remote: Remote name (default: origin)
        """
        try:
            logger.info(f"Cleaning up branch '{branch_name}'")
            
            # Checkout main branch
            await self._run_git_command("checkout", "main")
            
            # Delete local branch
            await self._run_git_command("branch", "-D", branch_name)
            
            # Delete remote branch (ignore errors if it doesn't exist)
            try:
                await self._run_git_command("push", remote, "--delete", branch_name)
            except Exception as e:
                logger.warning(f"Could not delete remote branch '{branch_name}': {str(e)}")
            
            logger.info(f"Successfully cleaned up branch '{branch_name}'")
            
        except Exception as e:
            logger.error(f"Error cleaning up branch '{branch_name}': {str(e)}")
            raise
    
    async def check_git_config(self) -> Dict[str, Any]:
        """
        Check git configuration.
        
        Returns:
            Git configuration status
        """
        try:
            config = {}
            
            # Check user name
            try:
                config["user_name"] = await self._run_git_command("config", "user.name")
            except Exception:
                config["user_name"] = None
            
            # Check user email
            try:
                config["user_email"] = await self._run_git_command("config", "user.email")
            except Exception:
                config["user_email"] = None
            
            # Check remote origin
            try:
                config["remote_origin"] = await self._run_git_command("config", "remote.origin.url")
            except Exception:
                config["remote_origin"] = None
            
            config["configured"] = bool(config["user_name"] and config["user_email"])
            
            logger.debug(f"Git configuration: {config}")
            return config
            
        except Exception as e:
            logger.error(f"Error checking git config: {str(e)}")
            raise 