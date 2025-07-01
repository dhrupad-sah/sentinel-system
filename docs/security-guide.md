# Security Guide

Comprehensive security documentation for the Sentinel System, covering best practices, authentication, and defensive security measures.

## Table of Contents

1. [Security Overview](#security-overview)
2. [Authentication & Authorization](#authentication--authorization)
3. [Webhook Security](#webhook-security)
4. [GitHub Token Security](#github-token-security)
5. [Network Security](#network-security)
6. [Data Protection](#data-protection)
7. [Input Validation](#input-validation)
8. [Process Isolation](#process-isolation)
9. [Audit & Monitoring](#audit--monitoring)
10. [Security Checklist](#security-checklist)
11. [Incident Response](#incident-response)

---

## Security Overview

The Sentinel System implements multiple layers of defense to ensure secure operation:

### Defense in Depth
- **Authentication**: GitHub token validation
- **Authorization**: Repository permission checks
- **Input Validation**: Comprehensive payload verification
- **Process Isolation**: Sandboxed AI and Git operations
- **Audit Trail**: Comprehensive logging and monitoring
- **Human-in-the-Loop**: Manual approval for all code changes

### Security Principles
- **Principle of Least Privilege**: Minimal required permissions
- **Fail Secure**: Safe defaults and graceful degradation
- **Defense Against Malicious Input**: Robust input validation
- **Transparency**: Comprehensive audit trails
- **Isolation**: Separate processing contexts

---

## Authentication & Authorization

### GitHub Token Authentication

#### Token Requirements
```yaml
Required Scopes:
  - repo: Full repository access
    - repo:status: Access to commit statuses
    - repo_deployment: Access to deployment statuses
    - public_repo: Public repository access
    - repo:invite: Repository invitations
  - workflow: GitHub Actions workflow access (optional)

Repository Permissions:
  - Contents: Read (code analysis)
  - Issues: Write (comments, labels)
  - Pull Requests: Write (create PRs)
  - Metadata: Read (repository info)
```

#### Token Validation
```python
# Automatic token validation on startup
async def validate_github_token(token: str) -> bool:
    """Validate GitHub token and check permissions."""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = await client.get("https://api.github.com/user", headers=headers)
        
        if response.status_code != 200:
            return False
            
        # Check repository access
        repo_response = await client.get(
            f"https://api.github.com/repos/{settings.GITHUB_REPO}",
            headers=headers
        )
        return repo_response.status_code == 200
        
    except Exception:
        return False
```

### API Endpoint Protection

#### Token-Based Authentication
```python
# All protected endpoints require valid GitHub token
@router.get("/github/issues")
async def list_issues(
    authorization: str = Header(..., alias="Authorization")
) -> Dict[str, Any]:
    """List issues - requires valid GitHub token."""
    token = extract_bearer_token(authorization)
    if not await validate_token(token):
        raise HTTPException(401, "Invalid or expired GitHub token")
```

#### Authorization Headers
```bash
# Correct format
Authorization: Bearer ghp_xxxxxxxxxxxxxxxxxxxx

# Common mistakes to avoid
Authorization: ghp_xxxxxxxxxxxxxxxxxxxx  # Missing "Bearer"
Authorization: token ghp_xxxxxxxxxxxxxxxxxxxx  # Wrong prefix
```

---

## Webhook Security

### Signature Verification

#### HMAC-SHA256 Verification
```python
import hashlib
import hmac
from typing import Optional

def verify_webhook_signature(
    payload: bytes, 
    signature: str, 
    secret: str
) -> bool:
    """Verify GitHub webhook signature using HMAC-SHA256."""
    if not secret:
        # Development mode - signature verification disabled
        return True
        
    if not signature.startswith('sha256='):
        return False
        
    expected_signature = hmac.new(
        secret.encode('utf-8'),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    received_signature = signature[7:]  # Remove 'sha256=' prefix
    
    # Use constant-time comparison to prevent timing attacks
    return hmac.compare_digest(expected_signature, received_signature)
```

#### Webhook Configuration Security
```yaml
# GitHub Webhook Settings
Payload URL: https://your-domain.com/webhook/github
Content Type: application/json
Secret: [32+ character random string]
SSL Verification: Enabled
Events: Issues only (minimize attack surface)
```

#### Secret Generation
```bash
# Generate secure webhook secret
openssl rand -hex 32

# Alternative using Python
python -c "import secrets; print(secrets.token_hex(32))"

# Alternative using Node.js
node -e "console.log(require('crypto').randomBytes(32).toString('hex'))"
```

### Webhook Payload Validation

#### Event Filtering
```python
@router.post("/webhook/github")
async def github_webhook(
    request: Request,
    x_github_event: str = Header(..., alias="X-GitHub-Event"),
    x_github_delivery: str = Header(..., alias="X-GitHub-Delivery"),
    x_hub_signature_256: Optional[str] = Header(None, alias="X-Hub-Signature-256")
):
    """Process GitHub webhook with comprehensive validation."""
    
    # 1. Event type validation
    if x_github_event not in SUPPORTED_EVENTS:
        raise HTTPException(400, f"Unsupported event type: {x_github_event}")
    
    # 2. Payload signature verification
    payload = await request.body()
    if not verify_webhook_signature(payload, x_hub_signature_256, settings.GITHUB_WEBHOOK_SECRET):
        raise HTTPException(400, "Invalid webhook signature")
    
    # 3. Payload parsing and validation
    try:
        webhook_data = await request.json()
    except ValueError:
        raise HTTPException(400, "Invalid JSON payload")
    
    # 4. Repository validation
    if webhook_data.get("repository", {}).get("full_name") != settings.GITHUB_REPO:
        raise HTTPException(400, "Repository mismatch")
```

---

## GitHub Token Security

### Token Best Practices

#### Creation Guidelines
- **Use Fine-grained Personal Access Tokens** when available
- **Set expiration dates** (max 1 year, recommended 90 days)
- **Use organization-owned tokens** for team repositories
- **Document token purpose** in GitHub settings

#### Storage Security
```yaml
Production:
  - Use environment variables
  - Store in secure secret management systems
  - Never commit to repositories
  - Use encrypted storage for backups

Development:
  - Use separate tokens from production
  - Store in .env files (excluded from git)
  - Use shorter expiration periods
  - Rotate frequently
```

#### Token Rotation
```bash
#!/bin/bash
# Token rotation script
echo "Creating new GitHub token..."
gh auth refresh --scopes repo,workflow

echo "Testing new token..."
curl -H "Authorization: Bearer $(gh auth token)" \
     "https://api.github.com/user"

echo "Update environment variables with new token"
echo "Revoke old token from GitHub settings"
```

### Permission Auditing
```python
async def audit_token_permissions(token: str) -> Dict[str, Any]:
    """Audit GitHub token permissions and access."""
    headers = {"Authorization": f"Bearer {token}"}
    
    # Check user info
    user_response = await client.get("https://api.github.com/user", headers=headers)
    user_data = user_response.json()
    
    # Check repository access
    repo_response = await client.get(
        f"https://api.github.com/repos/{settings.GITHUB_REPO}",
        headers=headers
    )
    repo_data = repo_response.json()
    
    # Check rate limits
    rate_limit_response = await client.get(
        "https://api.github.com/rate_limit",
        headers=headers
    )
    rate_limit_data = rate_limit_response.json()
    
    return {
        "user": user_data.get("login"),
        "repository_access": repo_response.status_code == 200,
        "permissions": repo_data.get("permissions", {}),
        "rate_limit": rate_limit_data
    }
```

---

## Network Security

### HTTPS Configuration

#### Production Deployment
```yaml
# nginx configuration for HTTPS termination
server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    ssl_certificate /path/to/certificate.crt;
    ssl_certificate_key /path/to/private.key;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### CORS Configuration

#### Secure CORS Settings
```python
# Production CORS configuration
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://your-frontend.com",
        "https://api.your-domain.com"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
    expose_headers=["X-Total-Count"],
    max_age=3600
)
```

#### Development CORS Settings
```python
# Development CORS configuration (more permissive)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)
```

### Rate Limiting

#### GitHub API Rate Limiting
```python
class GitHubRateLimiter:
    """Handle GitHub API rate limiting."""
    
    def __init__(self):
        self.remaining_requests = 5000
        self.reset_time = None
        
    async def check_rate_limit(self, response: httpx.Response):
        """Check and update rate limit status."""
        self.remaining_requests = int(response.headers.get('X-RateLimit-Remaining', 0))
        self.reset_time = response.headers.get('X-RateLimit-Reset')
        
        if self.remaining_requests < 100:
            logger.warning(f"GitHub API rate limit low: {self.remaining_requests} remaining")
            
        if self.remaining_requests == 0:
            reset_timestamp = int(self.reset_time)
            sleep_time = reset_timestamp - time.time()
            logger.error(f"GitHub API rate limit exceeded. Reset in {sleep_time} seconds")
            raise RateLimitExceeded(f"Rate limit reset at {self.reset_time}")
```

---

## Data Protection

### Sensitive Data Handling

#### Data Classification
```yaml
Public Data:
  - Repository names
  - Issue titles and numbers
  - Public issue content
  - Public user profiles

Sensitive Data:
  - GitHub tokens
  - Webhook secrets
  - Private repository content
  - User email addresses
  - Internal system configurations

Confidential Data:
  - Authentication credentials
  - Private code analysis results
  - Internal error details
  - System architecture details
```

#### Data Sanitization
```python
def sanitize_for_logs(data: Dict[str, Any]) -> Dict[str, Any]:
    """Remove sensitive information from log data."""
    sensitive_keys = {
        'token', 'password', 'secret', 'key', 'authorization',
        'x-hub-signature', 'x-hub-signature-256'
    }
    
    sanitized = {}
    for key, value in data.items():
        if key.lower() in sensitive_keys:
            sanitized[key] = "[REDACTED]"
        elif isinstance(value, dict):
            sanitized[key] = sanitize_for_logs(value)
        else:
            sanitized[key] = value
            
    return sanitized

# Usage in logging
logger.info(f"Processing webhook: {sanitize_for_logs(webhook_data)}")
```

### Encryption at Rest

#### Log File Protection
```bash
# Set secure permissions on log files
chmod 600 logs/app.log
chown app:app logs/app.log

# Encrypt sensitive log data
gpg --symmetric --cipher-algo AES256 logs/app.log
```

#### Configuration File Security
```bash
# Secure environment files
chmod 600 .env .env.production
chown app:app .env .env.production

# Use encrypted configuration for production
ansible-vault encrypt .env.production
```

---

## Input Validation

### Webhook Payload Validation

#### Comprehensive Validation
```python
from pydantic import BaseModel, validator
from typing import List, Optional

class GitHubWebhookPayload(BaseModel):
    """Validated GitHub webhook payload."""
    action: str
    repository: Dict[str, Any]
    issue: Optional[Dict[str, Any]] = None
    pull_request: Optional[Dict[str, Any]] = None
    
    @validator('action')
    def validate_action(cls, v):
        allowed_actions = {'labeled', 'unlabeled', 'opened', 'closed'}
        if v not in allowed_actions:
            raise ValueError(f"Action '{v}' not allowed")
        return v
    
    @validator('repository')
    def validate_repository(cls, v):
        full_name = v.get('full_name')
        if not full_name or full_name != settings.GITHUB_REPO:
            raise ValueError("Repository mismatch")
        return v

# Usage
@router.post("/webhook/github")
async def github_webhook(payload: GitHubWebhookPayload):
    """Process validated webhook payload."""
    ...
```

### API Input Validation

#### Parameter Validation
```python
from pydantic import BaseModel, Field, validator
from typing import Optional

class IssueProcessRequest(BaseModel):
    """Request to process an issue."""
    feedback: Optional[str] = Field(None, max_length=2000)
    priority: Optional[str] = Field('normal', regex='^(low|normal|high|urgent)$')
    
    @validator('feedback')
    def validate_feedback(cls, v):
        if v and len(v.strip()) < 10:
            raise ValueError("Feedback must be at least 10 characters")
        return v

class IssueQuery(BaseModel):
    """Query parameters for listing issues."""
    state: str = Field('open', regex='^(open|closed|all)$')
    labels: Optional[str] = Field(None, max_length=500)
    limit: int = Field(10, ge=1, le=100)
    
    @validator('labels')
    def validate_labels(cls, v):
        if v:
            labels = v.split(',')
            if len(labels) > 10:
                raise ValueError("Too many labels (max 10)")
            for label in labels:
                if len(label.strip()) > 50:
                    raise ValueError("Label name too long (max 50 chars)")
        return v
```

### Command Injection Prevention

#### Safe Subprocess Execution
```python
import subprocess
import shlex
from typing import List

class SecureCommandExecutor:
    """Execute system commands securely."""
    
    ALLOWED_COMMANDS = {
        'git': [
            'status', 'add', 'commit', 'push', 'checkout', 
            'branch', 'log', 'diff', 'clone'
        ],
        'gemini': ['analyze', 'generate', 'help']
    }
    
    def execute_command(self, command: List[str], cwd: str = None) -> str:
        """Execute command with security checks."""
        if not command:
            raise ValueError("Empty command")
            
        program = command[0]
        if program not in self.ALLOWED_COMMANDS:
            raise ValueError(f"Command '{program}' not allowed")
            
        # Validate subcommands
        if len(command) > 1:
            subcommand = command[1]
            if subcommand not in self.ALLOWED_COMMANDS[program]:
                raise ValueError(f"Subcommand '{subcommand}' not allowed for '{program}'")
        
        # Execute with timeout and secure environment
        try:
            result = subprocess.run(
                command,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=30,  # Prevent hanging
                env={'PATH': '/usr/bin:/bin'},  # Minimal environment
                check=True
            )
            return result.stdout
        except subprocess.CalledProcessError as e:
            logger.error(f"Command failed: {' '.join(command)}, Error: {e.stderr}")
            raise CommandExecutionError(f"Command failed: {e.stderr}")
```

---

## Process Isolation

### Background Task Security

#### Isolated Processing
```python
import asyncio
from concurrent.futures import ThreadPoolExecutor
import multiprocessing

class SecureTaskProcessor:
    """Process tasks in isolated environments."""
    
    def __init__(self):
        # Create process pool for CPU-intensive tasks
        self.process_pool = multiprocessing.Pool(processes=2)
        # Create thread pool for I/O tasks
        self.thread_pool = ThreadPoolExecutor(max_workers=4)
    
    async def process_issue_safely(self, issue_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process issue in isolated environment."""
        try:
            # Run AI processing in separate process
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                self.process_pool,
                self._analyze_issue_isolated,
                issue_data
            )
            return result
        except Exception as e:
            logger.error(f"Isolated processing failed: {str(e)}")
            raise ProcessingError("Issue processing failed")
    
    def _analyze_issue_isolated(self, issue_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze issue in isolated process."""
        # This runs in a separate process with limited access
        # No access to main application state or network
        return {"analysis": "Safe analysis result"}
```

### File System Security

#### Restricted File Access
```python
import os
import tempfile
from pathlib import Path

class SecureFileManager:
    """Manage file operations with security restrictions."""
    
    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir).resolve()
        self.allowed_extensions = {'.py', '.js', '.ts', '.md', '.json', '.yaml', '.yml'}
    
    def validate_path(self, file_path: str) -> Path:
        """Validate file path is within allowed directory."""
        path = Path(file_path).resolve()
        
        # Prevent directory traversal
        if not str(path).startswith(str(self.base_dir)):
            raise SecurityError(f"Access denied: {file_path}")
        
        # Check file extension
        if path.suffix not in self.allowed_extensions:
            raise SecurityError(f"File type not allowed: {path.suffix}")
        
        return path
    
    def create_temp_workspace(self) -> str:
        """Create isolated temporary workspace."""
        temp_dir = tempfile.mkdtemp(prefix="sentinel_")
        os.chmod(temp_dir, 0o700)  # Owner-only access
        return temp_dir
```

---

## Audit & Monitoring

### Security Logging

#### Comprehensive Security Events
```python
import logging
from datetime import datetime
from typing import Dict, Any

class SecurityLogger:
    """Log security-relevant events."""
    
    def __init__(self):
        self.logger = logging.getLogger("security")
        self.logger.setLevel(logging.INFO)
        
        # Create security-specific handler
        handler = logging.FileHandler("logs/security.log")
        handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        self.logger.addHandler(handler)
    
    def log_authentication_event(self, event: str, details: Dict[str, Any]):
        """Log authentication events."""
        self.logger.info(f"AUTH_EVENT: {event}", extra={
            "event_type": "authentication",
            "timestamp": datetime.utcnow().isoformat(),
            "details": sanitize_for_logs(details)
        })
    
    def log_webhook_event(self, event: str, payload_hash: str, source_ip: str):
        """Log webhook events."""
        self.logger.info(f"WEBHOOK_EVENT: {event}", extra={
            "event_type": "webhook",
            "payload_hash": payload_hash,
            "source_ip": source_ip,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    def log_security_violation(self, violation: str, details: Dict[str, Any]):
        """Log security violations."""
        self.logger.warning(f"SECURITY_VIOLATION: {violation}", extra={
            "event_type": "security_violation",
            "severity": "high",
            "details": sanitize_for_logs(details),
            "timestamp": datetime.utcnow().isoformat()
        })

# Usage throughout the application
security_logger = SecurityLogger()

# In webhook handler
@router.post("/webhook/github")
async def github_webhook(request: Request):
    payload = await request.body()
    payload_hash = hashlib.sha256(payload).hexdigest()
    source_ip = request.client.host
    
    security_logger.log_webhook_event(
        "webhook_received",
        payload_hash,
        source_ip
    )
```

### Monitoring and Alerting

#### Health Check Security
```python
@router.get("/health")
async def health_check():
    """Comprehensive security-aware health check."""
    health_data = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": {}
    }
    
    # Security-focused checks
    try:
        # Check GitHub token validity
        token_valid = await validate_github_token(settings.GITHUB_TOKEN)
        health_data["checks"]["github_token"] = "valid" if token_valid else "invalid"
        
        # Check webhook secret configuration
        webhook_secure = bool(settings.GITHUB_WEBHOOK_SECRET)
        health_data["checks"]["webhook_security"] = "enabled" if webhook_secure else "disabled"
        
        # Check SSL/TLS configuration
        ssl_enabled = request.url.scheme == "https"
        health_data["checks"]["ssl_enabled"] = ssl_enabled
        
        # Check file permissions
        log_perms = oct(os.stat("logs/app.log").st_mode)[-3:]
        health_data["checks"]["log_permissions"] = log_perms
        
    except Exception as e:
        logger.error(f"Health check error: {str(e)}")
        health_data["status"] = "unhealthy"
        health_data["error"] = "Security check failed"
    
    return health_data
```

### Security Metrics

#### Key Security Metrics
```python
from prometheus_client import Counter, Histogram, Gauge

# Security metrics
webhook_signatures_verified = Counter(
    'webhook_signatures_verified_total',
    'Number of webhook signatures verified',
    ['status']
)

authentication_attempts = Counter(
    'authentication_attempts_total',
    'Number of authentication attempts',
    ['status', 'method']
)

security_violations = Counter(
    'security_violations_total',
    'Number of security violations detected',
    ['type', 'severity']
)

# Usage
def verify_webhook_signature(payload: bytes, signature: str, secret: str) -> bool:
    is_valid = _verify_signature_impl(payload, signature, secret)
    webhook_signatures_verified.labels(
        status='valid' if is_valid else 'invalid'
    ).inc()
    return is_valid
```

---

## Security Checklist

### Pre-Deployment Security Checklist

#### Infrastructure Security
- [ ] HTTPS enabled with valid SSL certificate
- [ ] Webhook signature verification enabled
- [ ] Strong webhook secrets configured (32+ characters)
- [ ] CORS properly configured for production domains
- [ ] Rate limiting configured
- [ ] Log file permissions set correctly (600)
- [ ] Environment file permissions set correctly (600)

#### Authentication & Authorization
- [ ] GitHub tokens have minimal required permissions
- [ ] Tokens have expiration dates set
- [ ] Token rotation schedule established
- [ ] API endpoints properly protected
- [ ] Authorization headers validated
- [ ] Repository access permissions verified

#### Input Validation
- [ ] All webhook payloads validated
- [ ] API parameters sanitized
- [ ] File paths validated against directory traversal
- [ ] Command injection prevention implemented
- [ ] Request size limits configured

#### Monitoring & Logging
- [ ] Security logging enabled
- [ ] Log retention policy defined
- [ ] Monitoring alerts configured
- [ ] Health check includes security status
- [ ] Audit trail for all operations
- [ ] Error handling doesn't leak sensitive information

#### Code Security
- [ ] Dependencies scanned for vulnerabilities
- [ ] Secrets not hardcoded in source
- [ ] Sensitive data sanitized in logs
- [ ] Process isolation implemented
- [ ] Temporary files cleaned up
- [ ] Error messages don't expose internals

### Production Security Configuration

```bash
#!/bin/bash
# Production security setup script

echo "Setting up production security..."

# Set secure file permissions
chmod 600 .env.production
chmod 600 logs/app.log
chmod 755 src/

# Create security log directory
mkdir -p logs/security
chmod 700 logs/security

# Generate webhook secret if not exists
if [ -z "$GITHUB_WEBHOOK_SECRET" ]; then
    echo "GITHUB_WEBHOOK_SECRET=$(openssl rand -hex 32)" >> .env.production
fi

# Validate configuration
python -c "
import os
from src.sentinel_system.config import settings

# Validate critical security settings
assert settings.GITHUB_WEBHOOK_SECRET, 'Webhook secret required'
assert len(settings.GITHUB_WEBHOOK_SECRET) >= 32, 'Webhook secret too short'
assert settings.GITHUB_TOKEN.startswith('ghp_'), 'Invalid GitHub token format'
assert not settings.DEBUG, 'Debug mode disabled in production'

print('Security configuration validated!')
"

echo "Production security setup complete!"
```

---

## Incident Response

### Security Incident Response Plan

#### 1. Detection and Analysis
```yaml
Immediate Actions:
  - Identify the nature and scope of the incident
  - Preserve evidence and logs
  - Assess potential data exposure
  - Document initial findings

Detection Sources:
  - Security monitoring alerts
  - Error logs and exceptions
  - GitHub audit logs
  - User reports
  - Webhook delivery failures
```

#### 2. Containment and Mitigation
```bash
#!/bin/bash
# Emergency security response script

echo "SECURITY INCIDENT RESPONSE"
echo "=========================="

# 1. Stop the service
sudo systemctl stop sentinel-system

# 2. Rotate GitHub tokens
echo "Rotating GitHub tokens..."
gh auth refresh --scopes repo,workflow

# 3. Generate new webhook secret
NEW_SECRET=$(openssl rand -hex 32)
echo "GITHUB_WEBHOOK_SECRET=$NEW_SECRET" >> .env.emergency

# 4. Backup current logs for analysis
cp -r logs/ logs-backup-$(date +%Y%m%d-%H%M%S)/

# 5. Clear temporary files
rm -rf /tmp/sentinel_*

echo "Emergency containment complete!"
echo "1. Update GitHub webhook secret to: $NEW_SECRET"
echo "2. Review logs in logs-backup-* directory"
echo "3. Restart service after validation"
```

#### 3. Investigation
```python
# Security incident analysis tools

def analyze_security_logs(start_time: datetime, end_time: datetime):
    """Analyze security logs for incident investigation."""
    suspicious_events = []
    
    with open("logs/security.log", "r") as log_file:
        for line in log_file:
            try:
                log_data = json.loads(line)
                timestamp = datetime.fromisoformat(log_data["timestamp"])
                
                if start_time <= timestamp <= end_time:
                    # Look for security violations
                    if log_data.get("event_type") == "security_violation":
                        suspicious_events.append(log_data)
                    
                    # Look for failed authentications
                    if "AUTH_EVENT" in log_data.get("message", ""):
                        if "failed" in log_data["message"].lower():
                            suspicious_events.append(log_data)
                    
                    # Look for unusual webhook activity
                    if "WEBHOOK_EVENT" in log_data.get("message", ""):
                        if log_data.get("source_ip") not in KNOWN_GITHUB_IPS:
                            suspicious_events.append(log_data)
                            
            except (json.JSONDecodeError, KeyError):
                continue
    
    return suspicious_events

def check_github_audit_log():
    """Check GitHub audit log for suspicious activity."""
    # Use GitHub API to fetch audit log
    headers = {"Authorization": f"Bearer {settings.GITHUB_TOKEN}"}
    response = requests.get(
        f"https://api.github.com/repos/{settings.GITHUB_REPO}/events",
        headers=headers
    )
    
    events = response.json()
    suspicious_activity = []
    
    for event in events:
        # Look for unexpected pushes, deletions, or permission changes
        if event["type"] in ["PushEvent", "DeleteEvent", "MemberEvent"]:
            suspicious_activity.append(event)
    
    return suspicious_activity
```

#### 4. Recovery and Lessons Learned
```yaml
Recovery Steps:
  1. Patch vulnerabilities
  2. Update configurations
  3. Rotate all credentials
  4. Restart services
  5. Verify system integrity
  6. Resume normal operations

Post-Incident:
  1. Document incident details
  2. Update security procedures
  3. Enhance monitoring
  4. Conduct team training
  5. Review and test response plan
```

### Emergency Contacts and Procedures

```yaml
Emergency Contacts:
  - Security Team: security@company.com
  - DevOps Team: devops@company.com
  - GitHub Support: support@github.com

Escalation Matrix:
  - Level 1: Development Team (0-2 hours)
  - Level 2: Security Team (2-4 hours)
  - Level 3: Management (4+ hours)

Communication Channels:
  - Slack: #security-incidents
  - Email: security-team@company.com
  - Phone: Emergency contact list
```

---

## Conclusion

Security is a continuous process. Regularly review and update these security measures based on:

- **Threat landscape changes**
- **New vulnerabilities discovered**
- **Feature additions or changes**
- **Incident lessons learned**
- **Industry best practices**

### Regular Security Tasks

```yaml
Daily:
  - Monitor security logs
  - Check health endpoints
  - Review authentication failures

Weekly:
  - Audit token permissions
  - Review webhook deliveries
  - Update dependency vulnerabilities

Monthly:
  - Rotate credentials
  - Security configuration review
  - Penetration testing
  - Security awareness training

Quarterly:
  - Full security audit
  - Incident response drill
  - Security policy updates
  - Third-party security assessments
```

Remember: **Security is everyone's responsibility**. Stay vigilant, keep systems updated, and always follow the principle of least privilege.