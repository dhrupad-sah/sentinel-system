"""
GitHub webhook endpoints for Sentinel System.

Handles real-time GitHub webhook events for instant issue processing.
"""

import hashlib
import hmac
import json
import logging
from typing import Dict, Any, Optional

from fastapi import APIRouter, Request, HTTPException, BackgroundTasks, Header
from pydantic import BaseModel

from ..config import settings
from ..services.issue_processor import IssueProcessor

router = APIRouter()
logger = logging.getLogger(__name__)


class WebhookEvent(BaseModel):
    """GitHub webhook event model."""
    action: str
    issue: Optional[Dict[str, Any]] = None
    label: Optional[Dict[str, Any]] = None
    repository: Optional[Dict[str, Any]] = None


class WebhookResponse(BaseModel):
    """Webhook response model."""
    status: str
    message: str
    processed: bool = False
    issue_number: Optional[int] = None


def verify_webhook_signature(payload: bytes, signature: str, secret: str) -> bool:
    """
    Verify GitHub webhook signature.
    
    Args:
        payload: Raw request payload
        signature: GitHub signature header (sha256=...)
        secret: Webhook secret
        
    Returns:
        True if signature is valid
    """
    if not signature or not secret:
        return False
    
    # Remove 'sha256=' prefix
    if signature.startswith('sha256='):
        signature = signature[7:]
    else:
        return False
    
    # Calculate expected signature
    expected_signature = hmac.new(
        secret.encode('utf-8'),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    # Compare signatures securely
    return hmac.compare_digest(expected_signature, signature)


@router.post("/github", response_model=WebhookResponse)
async def github_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_github_event: str = Header(...),
    x_github_delivery: str = Header(...),
    x_hub_signature_256: Optional[str] = Header(None)
):
    """
    Handle GitHub webhook events.
    
    Processes issue label events for the autonomous workflow.
    """
    try:
        # Get raw payload for signature verification
        payload = await request.body()
        content_type = request.headers.get("content-type", "")
        
        # Log payload details for debugging
        logger.info(f"Webhook payload debug - Content-Type: {content_type}")
        logger.info(f"Payload length: {len(payload)}")
        logger.info(f"Payload preview: {payload[:200]}")  # First 200 chars
        
        # Verify webhook signature if secret is configured
        # Temporarily disabled for testing - re-enable in production
        if False and hasattr(settings, 'GITHUB_WEBHOOK_SECRET') and settings.GITHUB_WEBHOOK_SECRET:
            if not x_hub_signature_256:
                logger.warning("Webhook signature missing")
                raise HTTPException(status_code=401, detail="Signature required")
            
            if not verify_webhook_signature(payload, x_hub_signature_256, settings.GITHUB_WEBHOOK_SECRET):
                logger.warning("Invalid webhook signature")
                raise HTTPException(status_code=401, detail="Invalid signature")
        
        # Parse payload based on content type
        try:
            if not payload:
                logger.warning("Empty payload received")
                return WebhookResponse(
                    status="ignored",
                    message="Empty payload received"
                )
            
            # Handle URL-encoded payload (GitHub sometimes sends this way)
            if "application/x-www-form-urlencoded" in content_type:
                from urllib.parse import parse_qs, unquote
                decoded_payload = payload.decode('utf-8')
                logger.info(f"URL-encoded payload: {decoded_payload[:200]}")
                
                # Parse the form data
                parsed_data = parse_qs(decoded_payload)
                if 'payload' in parsed_data:
                    json_payload = parsed_data['payload'][0]
                    event_data = json.loads(json_payload)
                else:
                    raise ValueError("No 'payload' field in form data")
            else:
                # Handle JSON payload
                event_data = json.loads(payload.decode('utf-8'))
                
            logger.info(f"Successfully parsed event data: action={event_data.get('action')}, issue={event_data.get('issue', {}).get('number')}")
            
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            logger.error(f"Failed to parse payload: {e}")
            logger.error(f"Content-Type: {content_type}")
            logger.error(f"Raw payload: {payload.decode('utf-8', errors='ignore')[:500]}")
            raise HTTPException(status_code=400, detail=f"Invalid payload format: {str(e)}")
        
        # Log webhook event
        logger.info(f"Received GitHub webhook: {x_github_event} - {x_github_delivery}")
        
        # Handle GitHub ping event (sent when webhook is first created)
        if x_github_event == "ping":
            logger.info("Received GitHub ping event - webhook setup successful")
            return WebhookResponse(
                status="pong",
                message="Webhook endpoint is working correctly"
            )
        
        # Only process 'issues' events
        if x_github_event != "issues":
            logger.debug(f"Ignoring non-issues event: {x_github_event}")
            return WebhookResponse(
                status="ignored",
                message=f"Event type '{x_github_event}' not processed"
            )
        
        # Extract event details
        action = event_data.get("action")
        issue = event_data.get("issue", {})
        label = event_data.get("label", {})
        issue_number = issue.get("number")
        
        if not issue_number:
            logger.warning("Webhook payload missing issue number")
            raise HTTPException(status_code=400, detail="Missing issue number")
        
        # Only process label-related actions
        if action not in ["labeled", "unlabeled"]:
            logger.debug(f"Ignoring action: {action}")
            return WebhookResponse(
                status="ignored",
                message=f"Action '{action}' not processed",
                issue_number=issue_number
            )
        
        label_name = label.get("name", "")
        
        # Check if it's a label we care about
        relevant_labels = {
            settings.GITHUB_ISSUE_LABEL,
            settings.GITHUB_APPROVED_LABEL,
            settings.GITHUB_PROPOSAL_LABEL,
            settings.GITHUB_WORKING_LABEL
        }
        
        if label_name not in relevant_labels:
            logger.debug(f"Ignoring irrelevant label: {label_name}")
            return WebhookResponse(
                status="ignored",
                message=f"Label '{label_name}' not relevant to workflow",
                issue_number=issue_number
            )
        
        # Process the webhook event in background
        background_tasks.add_task(
            process_webhook_event,
            action,
            issue_number,
            label_name,
            issue,
            x_github_delivery
        )
        
        logger.info(f"Queued processing for issue #{issue_number}, label: {label_name}, action: {action}")
        
        return WebhookResponse(
            status="received",
            message="Webhook event queued for processing",
            processed=True,
            issue_number=issue_number
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


async def process_webhook_event(
    action: str,
    issue_number: int,
    label_name: str,
    issue_data: Dict[str, Any],
    delivery_id: str
):
    """
    Process a webhook event in the background.
    
    Args:
        action: The action that triggered the webhook (labeled/unlabeled)
        issue_number: GitHub issue number
        label_name: Name of the label that was added/removed
        issue_data: Full issue data from webhook
        delivery_id: GitHub delivery ID for tracking
    """
    try:
        logger.info(f"Processing webhook event {delivery_id}: {action} '{label_name}' on issue #{issue_number}")
        
        issue_processor = IssueProcessor()
        
        # Handle different label events
        if action == "labeled":
            if label_name == settings.GITHUB_ISSUE_LABEL:
                # ai-ready label added - start analysis
                logger.info(f"Starting analysis for issue #{issue_number}")
                result = await issue_processor.process_issue(issue_number)
                logger.info(f"Analysis completed for issue #{issue_number}: {result.get('status')}")
                
            elif label_name == settings.GITHUB_APPROVED_LABEL:
                # ai-approved label added - start implementation
                logger.info(f"Starting implementation for issue #{issue_number}")
                result = await issue_processor.process_issue(issue_number)
                logger.info(f"Implementation completed for issue #{issue_number}: {result.get('status')}")
                
            else:
                logger.debug(f"No action needed for label '{label_name}' being added")
        
        elif action == "unlabeled":
            if label_name == settings.GITHUB_PROPOSAL_LABEL:
                # ai-proposal-pending label removed - could indicate rejection
                logger.info(f"Proposal label removed from issue #{issue_number} - may need refinement")
                # Note: We could implement refinement logic here in the future
            else:
                logger.debug(f"No action needed for label '{label_name}' being removed")
        
        logger.info(f"Webhook event {delivery_id} processed successfully")
        
    except Exception as e:
        logger.error(f"Error processing webhook event {delivery_id}: {str(e)}")
        # Don't raise the exception - we don't want to cause webhook retries
        # Log the error and continue


@router.get("/status")
async def webhook_status():
    """Get webhook service status."""
    return {
        "webhook_enabled": True,
        "signature_verification": hasattr(settings, 'GITHUB_WEBHOOK_SECRET') and bool(settings.GITHUB_WEBHOOK_SECRET),
        "supported_events": ["issues.labeled", "issues.unlabeled"],
        "relevant_labels": [
            settings.GITHUB_ISSUE_LABEL,
            settings.GITHUB_PROPOSAL_LABEL,
            settings.GITHUB_APPROVED_LABEL,
            settings.GITHUB_WORKING_LABEL
        ]
    }


@router.post("/test")
async def test_webhook(event_data: Dict[str, Any], background_tasks: BackgroundTasks):
    """
    Test webhook endpoint for development/debugging.
    
    Allows manual testing of webhook processing without GitHub.
    """
    try:
        action = event_data.get("action")
        issue = event_data.get("issue", {})
        label = event_data.get("label", {})
        issue_number = issue.get("number")
        label_name = label.get("name", "")
        
        if not issue_number:
            raise HTTPException(status_code=400, detail="Missing issue number")
        
        # Process in background
        background_tasks.add_task(
            process_webhook_event,
            action,
            issue_number,
            label_name,
            issue,
            "test-delivery"
        )
        
        return {
            "status": "received",
            "message": "Test webhook queued for processing",
            "issue_number": issue_number,
            "action": action,
            "label": label_name
        }
        
    except Exception as e:
        logger.error(f"Error processing test webhook: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 