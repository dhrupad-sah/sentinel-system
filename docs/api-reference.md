# API Reference

Complete API documentation for the Sentinel System with detailed request/response examples.


## Authentication

Most endpoints require GitHub token authentication via the `Authorization` header:

```
Authorization: Bearer YOUR_GITHUB_TOKEN
```

## Response Format

All API responses follow this structure:

```json
{
  "status": "success|error",
  "message": "Human readable message",
  "data": { /* Response data */ },
  "error": { /* Error details (if applicable) */ }
}
```

---

## Health & Monitoring

### `GET /health`

Comprehensive system health check including all dependencies.

**Response 200:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00Z",
  "dependencies": {
    "github_token": "valid",
    "gemini_cli": "available",
    "git_config": "configured",
    "repository_access": "accessible"
  },
  "configuration": {
    "github_repo": "owner/repo",
    "gemini_model": "gemini-2.5-flash",
    "scheduler_enabled": false
  }
}
```

**Response 503 (Unhealthy):**
```json
{
  "status": "unhealthy",
  "timestamp": "2024-01-01T00:00:00Z",
  "dependencies": {
    "github_token": "invalid",
    "gemini_cli": "unavailable",
    "git_config": "missing",
    "repository_access": "forbidden"
  },
  "errors": [
    "GitHub token is invalid or expired",
    "Gemini CLI not found or not authenticated",
    "Git user.name not configured"
  ]
}
```

### `GET /health/ready`

Kubernetes readiness probe - minimal health check.

**Response 200:**
```json
{
  "status": "ready",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

### `GET /health/live`

Kubernetes liveness probe - service availability check.

**Response 200:**
```json
{
  "status": "alive",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

---

## GitHub Operations

### `GET /github/issues`

List repository issues with optional filtering.

**Query Parameters:**
- `state` (optional): `open`, `closed`, `all` (default: `open`)
- `labels` (optional): Comma-separated list of labels to filter by
- `limit` (optional): Maximum number of issues to return (default: 10, max: 100)

**Headers:**
```
Authorization: Bearer YOUR_GITHUB_TOKEN
```

**Example Request:**
```bash
curl -X GET "http://localhost:8000/github/issues?state=open&labels=ai-ready,bug&limit=5" \
     -H "Authorization: Bearer ghp_xxxxxxxxxxxxxxxxxxxx"
```

**Response 200:**
```json
{
  "status": "success",
  "data": {
    "issues": [
      {
        "number": 123,
        "title": "Fix login validation error",
        "body": "Users are experiencing validation errors...",
        "state": "open",
        "labels": [
          {"name": "ai-ready", "color": "0075ca"},
          {"name": "bug", "color": "d73a4a"}
        ],
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z",
        "html_url": "https://github.com/owner/repo/issues/123"
      }
    ],
    "total_count": 1,
    "filters": {
      "state": "open",
      "labels": ["ai-ready", "bug"],
      "limit": 5
    }
  }
}
```

### `GET /github/issues/{issue_number}`

Get detailed information about a specific issue.

**Path Parameters:**
- `issue_number`: GitHub issue number

**Headers:**
```
Authorization: Bearer YOUR_GITHUB_TOKEN
```

**Example Request:**
```bash
curl -X GET "http://localhost:8000/github/issues/123" \
     -H "Authorization: Bearer ghp_xxxxxxxxxxxxxxxxxxxx"
```

**Response 200:**
```json
{
  "status": "success",
  "data": {
    "issue": {
      "number": 123,
      "title": "Fix login validation error",
      "body": "## Problem\nUsers are experiencing validation errors when trying to log in...",
      "state": "open",
      "labels": [
        {"name": "ai-ready", "color": "0075ca"},
        {"name": "bug", "color": "d73a4a"}
      ],
      "assignees": [],
      "milestone": null,
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z",
      "html_url": "https://github.com/owner/repo/issues/123",
      "user": {
        "login": "username",
        "html_url": "https://github.com/username"
      }
    },
    "processing_status": {
      "can_process": true,
      "current_state": "ready_for_analysis",
      "blocking_labels": [],
      "next_action": "process"
    }
  }
}
```

**Response 404:**
```json
{
  "status": "error",
  "message": "Issue not found",
  "error": {
    "code": "ISSUE_NOT_FOUND",
    "details": "Issue #999 does not exist in the repository"
  }
}
```

### `POST /github/issues/{issue_number}/process`

Trigger AI analysis and proposal generation for an issue.

**Path Parameters:**
- `issue_number`: GitHub issue number

**Headers:**
```
Authorization: Bearer YOUR_GITHUB_TOKEN
```

**Example Request:**
```bash
curl -X POST "http://localhost:8000/github/issues/123/process" \
     -H "Authorization: Bearer ghp_xxxxxxxxxxxxxxxxxxxx"
```

**Response 202 (Processing Started):**
```json
{
  "status": "success",
  "message": "Issue processing started",
  "data": {
    "issue_number": 123,
    "processing_id": "proc_abc123def456",
    "status": "analysis_started",
    "estimated_completion": "2-5 minutes",
    "next_steps": [
      "AI will analyze the issue and related code",
      "A proposal comment will be posted to the issue",
      "Human review and approval will be required"
    ]
  }
}
```

**Response 409 (Already Processing):**
```json
{
  "status": "error",
  "message": "Issue is already being processed",
  "error": {
    "code": "ALREADY_PROCESSING",
    "details": "Issue #123 has the 'ai-working' label"
  }
}
```

**Response 400 (Cannot Process):**
```json
{
  "status": "error",
  "message": "Issue cannot be processed",
  "error": {
    "code": "INVALID_STATE",
    "details": "Issue must have 'ai-ready' label to be processed",
    "current_labels": ["bug", "enhancement"]
  }
}
```

### `POST /github/issues/{issue_number}/approve`

Approve an AI proposal and trigger implementation.

**Path Parameters:**
- `issue_number`: GitHub issue number

**Request Body (optional):**
```json
{
  "feedback": "Looks good, please implement the proposed solution",
  "modifications": "Please also add error logging to the validation function"
}
```

**Headers:**
```
Authorization: Bearer YOUR_GITHUB_TOKEN
Content-Type: application/json
```

**Example Request:**
```bash
curl -X POST "http://localhost:8000/github/issues/123/approve" \
     -H "Authorization: Bearer ghp_xxxxxxxxxxxxxxxxxxxx" \
     -H "Content-Type: application/json" \
     -d '{
       "feedback": "Approved! Please implement the solution.",
       "modifications": "Also add unit tests for the new validation logic"
     }'
```

**Response 202 (Implementation Started):**
```json
{
  "status": "success",
  "message": "Implementation started",
  "data": {
    "issue_number": 123,
    "approval_id": "appr_xyz789abc123",
    "status": "implementation_started",
    "branch_name": "sentinel/issue-123",
    "estimated_completion": "5-10 minutes",
    "next_steps": [
      "AI will implement the approved solution",
      "Changes will be committed to a new branch",
      "A pull request will be created for review"
    ]
  }
}
```

### `POST /github/issues/{issue_number}/reject`

Reject an AI proposal with optional feedback.

**Path Parameters:**
- `issue_number`: GitHub issue number

**Request Body:**
```json
{
  "feedback": "The proposed solution doesn't address the root cause",
  "reason": "INCORRECT_APPROACH"
}
```

**Headers:**
```
Authorization: Bearer YOUR_GITHUB_TOKEN
Content-Type: application/json
```

**Example Request:**
```bash
curl -X POST "http://localhost:8000/github/issues/123/reject" \
     -H "Authorization: Bearer ghp_xxxxxxxxxxxxxxxxxxxx" \
     -H "Content-Type: application/json" \
     -d '{
       "feedback": "This approach won\'t work because...",
       "reason": "SECURITY_CONCERNS"
     }'
```

**Response 200:**
```json
{
  "status": "success",
  "message": "Proposal rejected",
  "data": {
    "issue_number": 123,
    "rejection_id": "rej_def456ghi789",
    "feedback_posted": true,
    "labels_updated": true,
    "next_steps": [
      "Issue labels have been updated to reflect rejection",
      "AI can reanalyze with your feedback if 'ai-ready' label is re-added"
    ]
  }
}
```

### `GET /github/labels`

List all available labels in the repository.

**Headers:**
```
Authorization: Bearer YOUR_GITHUB_TOKEN
```

**Example Request:**
```bash
curl -X GET "http://localhost:8000/github/labels" \
     -H "Authorization: Bearer ghp_xxxxxxxxxxxxxxxxxxxx"
```

**Response 200:**
```json
{
  "status": "success",
  "data": {
    "labels": [
      {
        "name": "ai-ready",
        "color": "0075ca",
        "description": "Issue ready for AI processing"
      },
      {
        "name": "ai-proposal-pending",
        "color": "fbca04",
        "description": "AI proposal awaiting human review"
      },
      {
        "name": "ai-approved",
        "color": "0e8a16",
        "description": "AI proposal approved for implementation"
      },
      {
        "name": "ai-working",
        "color": "d876e3",
        "description": "AI currently processing this issue"
      },
      {
        "name": "bug",
        "color": "d73a4a",
        "description": "Something isn't working"
      }
    ],
    "system_labels": {
      "trigger": "ai-ready",
      "proposal_pending": "ai-proposal-pending",
      "approved": "ai-approved",
      "working": "ai-working"
    }
  }
}
```

### `GET /github/status`

Get GitHub service status and configuration.

**Headers:**
```
Authorization: Bearer YOUR_GITHUB_TOKEN
```

**Response 200:**
```json
{
  "status": "success",
  "data": {
    "service_status": "operational",
    "configuration": {
      "repository": "owner/repo",
      "api_version": "2022-11-28",
      "rate_limit": {
        "remaining": 4999,
        "reset_time": "2024-01-01T01:00:00Z"
      }
    },
    "permissions": {
      "issues": "write",
      "pull_requests": "write",
      "contents": "write"
    }
  }
}
```

---

## Webhook Operations

### `POST /webhook/github`

GitHub webhook endpoint for receiving repository events.

**Headers:**
```
X-GitHub-Event: issues
X-GitHub-Delivery: 12345678-1234-1234-1234-123456789012
X-Hub-Signature-256: sha256=abcdef123456...
Content-Type: application/json
```

**Request Body (Issues Labeled Event):**
```json
{
  "action": "labeled",
  "issue": {
    "number": 123,
    "title": "Fix login validation error",
    "body": "Users are experiencing validation errors...",
    "labels": [
      {"name": "ai-ready"},
      {"name": "bug"}
    ]
  },
  "label": {
    "name": "ai-ready"
  },
  "repository": {
    "full_name": "owner/repo"
  }
}
```

**Example Request:**
```bash
curl -X POST "http://localhost:8000/webhook/github" \
     -H "X-GitHub-Event: issues" \
     -H "X-GitHub-Delivery: 12345678-1234-1234-1234-123456789012" \
     -H "X-Hub-Signature-256: sha256=your-signature-here" \
     -H "Content-Type: application/json" \
     -d @webhook-payload.json
```

**Response 200:**
```json
{
  "status": "success",
  "message": "Webhook processed successfully",
  "data": {
    "event_type": "issues",
    "action": "labeled",
    "issue_number": 123,
    "processing_queued": true,
    "delivery_id": "12345678-1234-1234-1234-123456789012"
  }
}
```

**Response 400 (Invalid Signature):**
```json
{
  "status": "error",
  "message": "Invalid webhook signature",
  "error": {
    "code": "INVALID_SIGNATURE",
    "details": "Webhook signature verification failed"
  }
}
```

### `GET /webhook/status`

Get webhook service status and configuration.

**Response 200:**
```json
{
  "status": "success",
  "data": {
    "service_status": "operational",
    "configuration": {
      "signature_verification": true,
      "supported_events": ["issues"],
      "supported_actions": ["labeled", "unlabeled"]
    },
    "statistics": {
      "webhooks_received": 1247,
      "webhooks_processed": 1245,
      "last_webhook": "2024-01-01T00:00:00Z"
    }
  }
}
```

### `POST /webhook/test`

Test webhook processing without GitHub signature verification (development only).

**Request Body:**
```json
{
  "action": "labeled",
  "issue": {
    "number": 123,
    "title": "Test Issue",
    "labels": [{"name": "ai-ready"}]
  },
  "label": {"name": "ai-ready"}
}
```

**Response 200:**
```json
{
  "status": "success",
  "message": "Test webhook processed",
  "data": {
    "processed": true,
    "queued_for_processing": true
  }
}
```

---

## Error Codes Reference

| Code | Description | HTTP Status |
|------|-------------|-------------|
| `GITHUB_TOKEN_INVALID` | GitHub token is invalid or expired | 401 |
| `GITHUB_TOKEN_MISSING` | Authorization header missing | 401 |
| `ISSUE_NOT_FOUND` | Requested issue does not exist | 404 |
| `REPOSITORY_ACCESS_DENIED` | Insufficient permissions for repository | 403 |
| `INVALID_STATE` | Issue is in wrong state for operation | 400 |
| `ALREADY_PROCESSING` | Issue is currently being processed | 409 |
| `RATE_LIMIT_EXCEEDED` | GitHub API rate limit exceeded | 429 |
| `INVALID_SIGNATURE` | Webhook signature verification failed | 400 |
| `UNSUPPORTED_EVENT` | Webhook event type not supported | 400 |
| `GEMINI_UNAVAILABLE` | Gemini CLI not available or authenticated | 503 |
| `GIT_CONFIG_MISSING` | Git configuration incomplete | 503 |
| `INTERNAL_ERROR` | Unexpected server error | 500 |

---

## Rate Limits

- **GitHub API**: Follows GitHub's rate limiting (5,000 requests/hour for authenticated requests)
- **Webhook Processing**: No rate limiting (background processing)
- **Manual API Calls**: No additional rate limiting beyond GitHub's limits

---

## Webhook Event Types

Currently supported GitHub webhook events:

### Issues Events
- **`labeled`**: Triggers processing when `ai-ready` label is added
- **`unlabeled`**: Stops processing when trigger labels are removed

### Event Filtering
- Only `issues` events are processed
- Only `labeled`/`unlabeled` actions trigger workflows
- Repository must match configured `GITHUB_REPO`

---

## Authentication Examples

### Using Personal Access Token
```bash
# Set your token as environment variable
export GITHUB_TOKEN="ghp_xxxxxxxxxxxxxxxxxxxx"

# Use in API calls
curl -H "Authorization: Bearer $GITHUB_TOKEN" \
     "http://localhost:8000/github/issues"
```

### Using GitHub CLI Token
```bash
# Use GitHub CLI token
export GITHUB_TOKEN=$(gh auth token)

# Verify token
curl -H "Authorization: Bearer $GITHUB_TOKEN" \
     "http://localhost:8000/health"
```