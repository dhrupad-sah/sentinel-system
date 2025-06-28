"""
FastAPI routers for Sentinel System.
"""

# Import all routers to make them available
from . import health, github, webhook

__all__ = ["health", "github", "webhook"] 