"""
Configuration settings for Sentinel System.

Uses Pydantic Settings for environment-based configuration.
"""

from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application settings
    DEBUG: bool = Field(default=True, description="Enable debug mode")
    ALLOWED_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        description="CORS allowed origins"
    )
    
    # GitHub settings
    GITHUB_TOKEN: str = Field(description="GitHub API token")
    GITHUB_REPO: str = Field(description="Target GitHub repository (owner/repo)")
    GITHUB_WEBHOOK_SECRET: str = Field(
        default="",
        description="GitHub webhook secret for signature verification (optional)"
    )
    GITHUB_ISSUE_LABEL: str = Field(
        default="ai-ready", 
        description="Label to identify issues ready for AI processing"
    )
    GITHUB_PROPOSAL_LABEL: str = Field(
        default="ai-proposal-pending",
        description="Label for issues with AI proposals pending human review"
    )
    GITHUB_APPROVED_LABEL: str = Field(
        default="ai-approved",
        description="Label for issues approved by humans"
    )
    GITHUB_WORKING_LABEL: str = Field(
        default="ai-working",
        description="Label for issues currently being worked on by AI"
    )
    
    # Claude Code CLI settings (uses authenticated Claude account)
    CLAUDE_MODEL: str = Field(
        default="",
        description="Claude model to use (optional, CLI uses default if not specified)"
    )
    
    # Webhook settings (scheduler removed in v1)
    # Real-time processing via GitHub webhooks
    
    # Git settings
    GIT_BRANCH_PREFIX: str = Field(
        default="sentinel/issue-",
        description="Prefix for auto-created branches"
    )
    GIT_COMMIT_PREFIX: str = Field(
        default="feat: ",
        description="Prefix for commit messages"
    )
    
    LOG_LEVEL: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
    )
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Global settings instance
settings = Settings()

import logging
import os

def configure_logging():
    """Configures logging for the application."""
    log_level = os.environ.get("LOG_LEVEL", settings.LOG_LEVEL).upper()
    numeric_log_level = getattr(logging, log_level, logging.INFO)

    # Ensure the logs directory exists
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)

    # Configure root logger
    logging.basicConfig(
        level=numeric_log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),  # Console output
            logging.FileHandler(os.path.join(log_dir, "app.log"))  # File output
        ]
    )

    # Set log level for specific loggers if needed
    logging.getLogger("uvicorn").setLevel(numeric_log_level)
    logging.getLogger("uvicorn.access").setLevel(numeric_log_level)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)

    logging.info(f"Logging configured with level: {log_level}") 