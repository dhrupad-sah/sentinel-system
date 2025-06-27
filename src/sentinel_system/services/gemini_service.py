"""
Gemini CLI service for Sentinel System.

Handles interaction with Gemini CLI using the authenticated Google account.
"""

import subprocess
import asyncio
import logging
from typing import Optional, Dict, Any
import json
import tempfile
import os

from ..config import settings

logger = logging.getLogger(__name__)


class GeminiService:
    """Service for interacting with Gemini CLI."""
    
    def __init__(self):
        self.model = getattr(settings, 'GEMINI_MODEL', None)
    
    async def chat(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """
        Send a chat prompt to Gemini CLI.
        
        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt for context
            
        Returns:
            Gemini's response text
        """
        try:
            # Combine system prompt and user prompt if system prompt is provided
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"System: {system_prompt}\n\nUser: {prompt}"
            
            # Build the command
            cmd = ["gemini", "--prompt", full_prompt, "-y"]
            
            # Add model if specified
            if self.model:
                cmd.extend(["--model", self.model])
            
            logger.info(f"Executing Gemini CLI command: {' '.join(cmd[:3])}...")  # Don't log full prompt for privacy
            
            # Execute the command asynchronously
            # For analysis phase, run in current directory
            # For implementation phase, this should run in the target repository
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=os.getcwd()
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                error_msg = stderr.decode('utf-8') if stderr else "Unknown error"
                logger.error(f"Gemini CLI command failed with return code {process.returncode}: {error_msg}")
                raise Exception(f"Gemini CLI error: {error_msg}")
            
            response = stdout.decode('utf-8').strip()
            logger.info(f"Gemini CLI response received ({len(response)} characters)")
            return response
            
        except Exception as e:
            logger.error(f"Error executing Gemini CLI: {str(e)}")
            raise
    
    async def analyze_issue(self, issue_title: str, issue_body: str, issue_number: int) -> str:
        """
        Without changing any code, analyze a GitHub issue and propose a solution.
        
        Args:
            issue_title: The issue title
            issue_body: The issue description
            issue_number: The issue number
            
        Returns:
            AI analysis and proposed solution
        """
        system_prompt = """WITHOUT CHANGING OR TOUCHING ANY CODE, you are an AI assistant helping to analyze GitHub issues and propose solutions.

IMPORTANT: This is the ANALYSIS phase only. DO NOT make any code changes or modifications to files.

Your task is to:
1. Analyze and understand the issue
2. Propose a clear solution approach
3. Outline implementation steps
4. Identify potential considerations or risks

Please provide:
- Your understanding of what the issue is asking for
- A detailed solution proposal (but don't implement it yet)
- Step-by-step implementation plan
- Files that would need to be modified
- Any potential risks or considerations

Do NOT make any code changes during this analysis phase. You will implement the solution only after human approval."""

        user_prompt = f"""Please analyze this GitHub issue and propose a solution:

**Issue #{issue_number}: {issue_title}**

**Description:**
{issue_body or 'No description provided'}

Please provide your analysis and proposed solution."""

        try:
            response = await self.chat(user_prompt, system_prompt)
            return response
        except Exception as e:
            logger.error(f"Error analyzing issue #{issue_number}: {str(e)}")
            raise
    
    async def implement_solution(self, issue_title: str, issue_body: str, approved_proposal: str, issue_number: int) -> str:
        """
        Implement the approved solution for an issue.
        
        Args:
            issue_title: The issue title
            issue_body: The issue description  
            approved_proposal: The human-approved proposal
            issue_number: The issue number
            
        Returns:
            Implementation details and summary
        """
        system_prompt = """You are an AI assistant implementing approved solutions for GitHub issues.
You have access to the codebase and can make changes to fix the issue.

Your task is to:
1. Implement the approved solution
2. Make necessary code changes
3. Ensure the changes are working
4. Provide a summary of what was implemented

Be thorough and make sure your implementation addresses the issue completely.
Only make changes that are necessary to fix the issue."""

        user_prompt = f"""Please implement the approved solution for this GitHub issue:

**Issue #{issue_number}: {issue_title}**

**Original Description:**
{issue_body or 'No description provided'}

**Approved Proposal:**
{approved_proposal}

Please implement the solution and provide a summary of the changes made."""

        try:
            response = await self.chat(user_prompt, system_prompt)
            return response
        except Exception as e:
            logger.error(f"Error implementing solution for issue #{issue_number}: {str(e)}")
            raise
    
    async def refine_proposal(self, issue_title: str, issue_body: str, previous_proposal: str, feedback: str, issue_number: int) -> str:
        """
        Refine a proposal based on human feedback.
        
        Args:
            issue_title: The issue title
            issue_body: The issue description
            previous_proposal: The previous proposal that was rejected
            feedback: Human feedback on the proposal
            issue_number: The issue number
            
        Returns:
            Refined proposal based on feedback
        """
        system_prompt = """You are an AI assistant refining solution proposals for GitHub issues based on human feedback.

Your task is to:
1. Understand the feedback provided
2. Address the concerns raised
3. Provide an improved, refined proposal
4. Ensure the new proposal addresses both the original issue and the feedback

Be responsive to the feedback and make meaningful improvements."""

        user_prompt = f"""Please refine your proposal for this GitHub issue based on the feedback:

**Issue #{issue_number}: {issue_title}**

**Original Description:**
{issue_body or 'No description provided'}

**Previous Proposal:**
{previous_proposal}

**Human Feedback:**
{feedback}

Please provide a refined proposal that addresses the feedback."""

        try:
            response = await self.chat(user_prompt, system_prompt)
            return response
        except Exception as e:
            logger.error(f"Error refining proposal for issue #{issue_number}: {str(e)}")
            raise
    
    async def check_availability(self) -> Dict[str, Any]:
        """
        Check if Gemini CLI is available and working.
        
        Returns:
            Status dictionary with availability information
        """
        try:
            # Try a simple test command
            process = await asyncio.create_subprocess_exec(
                "gemini", "--version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                version = stdout.decode('utf-8').strip()
                return {
                    "available": True,
                    "version": version,
                    "authenticated": True,  # If version works, likely authenticated
                    "model": self.model
                }
            else:
                error = stderr.decode('utf-8') if stderr else "Unknown error"
                return {
                    "available": False,
                    "error": error,
                    "model": self.model
                }
                
        except FileNotFoundError:
            return {
                "available": False,
                "error": "Gemini CLI not found in PATH",
                "model": self.model
            }
        except Exception as e:
            return {
                "available": False,
                "error": str(e),
                "model": self.model
            } 