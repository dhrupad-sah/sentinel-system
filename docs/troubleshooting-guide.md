# Troubleshooting Guide

Comprehensive troubleshooting guide for common issues and problems with the Sentinel System.

## Table of Contents

1. [Quick Diagnostics](#quick-diagnostics)
2. [Configuration Issues](#configuration-issues)
3. [Authentication Problems](#authentication-problems)
4. [Claude CLI Issues](#claude-cli-issues)
5. [Webhook Problems](#webhook-problems)
6. [API Errors](#api-errors)
7. [Git Operations Issues](#git-operations-issues)
8. [Performance Issues](#performance-issues)
9. [Logging and Monitoring](#logging-and-monitoring)
10. [Common Error Messages](#common-error-messages)
11. [FAQ](#faq)

---

## Quick Diagnostics

### System Health Check

First, always check the system health endpoint:

```bash
curl http://localhost:8000/health
```

**Expected Healthy Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00Z",
  "dependencies": {
    "github_token": "valid",
    "claude_cli": "available",
    "git_config": "configured",
    "repository_access": "accessible"
  }
}
```

### Quick Diagnostic Commands

```bash
# Check if the service is running
curl -f http://localhost:8000/health/live || echo "Service not responding"

# Check GitHub token
curl -H "Authorization: Bearer $GITHUB_TOKEN" https://api.github.com/user

# Check Claude CLI
claude --help

# Check git configuration
git config --get user.name
git config --get user.email

# Check logs for errors
tail -50 logs/app.log | grep -i error
```

---

## Configuration Issues

### Environment Variables Not Loading

**Problem**: Configuration values not being read correctly.

**Symptoms**:
- Health check shows missing configuration
- Service fails to start
- Default values being used instead of configured ones

**Solutions**:

1. **Check environment file location**:
   ```bash
   ls -la .env*
   # Should show .env file with correct permissions
   ```

2. **Verify environment file format**:
   ```bash
   cat .env
   # Check for:
   # - No spaces around equals signs
   # - Quoted values for complex strings
   # - No trailing whitespace
   ```

3. **Test environment loading**:
   ```bash
   # Load environment manually
   export $(cat .env | xargs)
   echo $GITHUB_TOKEN  # Should show your token
   ```

4. **Check for common syntax errors**:
   ```bash
   # Bad format examples:
   GITHUB_TOKEN = ghp_xxxx  # Extra spaces
   GITHUB_REPO="owner/repo  # Missing closing quote
   DEBUG="true"  # Should be true without quotes for boolean
   
   # Correct format:
   GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxx
   GITHUB_REPO=owner/repo
   DEBUG=true
   ```

### JSON Array Configuration Issues

**Problem**: CORS origins or other JSON array configs not parsing.

**Error**: `json.decoder.JSONDecodeError: Expecting value`

**Solutions**:

1. **Check JSON format**:
   ```bash
   # Correct format
   ALLOWED_ORIGINS=["http://localhost:3000", "https://myapp.com"]
   
   # Test parsing
   python -c "import json, os; print(json.loads(os.getenv('ALLOWED_ORIGINS', '[]')))"
   ```

2. **Use single quotes for JSON strings**:
   ```bash
   # Avoid shell interpretation issues
   ALLOWED_ORIGINS='["http://localhost:3000", "https://myapp.com"]'
   ```

---

## Authentication Problems

### GitHub Token Issues

#### Invalid or Expired Token

**Error**: `401 Unauthorized` when accessing GitHub API

**Diagnosis**:
```bash
# Test token directly
curl -H "Authorization: Bearer $GITHUB_TOKEN" https://api.github.com/user

# Check token scopes
curl -H "Authorization: Bearer $GITHUB_TOKEN" -I https://api.github.com/user | grep -i scope
```

**Solutions**:

1. **Generate new token**:
   - Go to GitHub Settings → Developer settings → Personal access tokens
   - Generate new token with `repo` and `workflow` scopes
   - Update `.env` file

2. **Check token format**:
   ```bash
   # GitHub personal access tokens start with ghp_
   echo $GITHUB_TOKEN | grep "^ghp_" || echo "Invalid token format"
   ```

#### Repository Access Issues

**Error**: `404 Not Found` or `403 Forbidden` for repository operations

**Diagnosis**:
```bash
# Test repository access
curl -H "Authorization: Bearer $GITHUB_TOKEN" \
     "https://api.github.com/repos/$GITHUB_REPO"

# Check repository permissions
curl -H "Authorization: Bearer $GITHUB_TOKEN" \
     "https://api.github.com/repos/$GITHUB_REPO" | jq .permissions
```

**Solutions**:

1. **Verify repository name format**:
   ```bash
   # Correct format: owner/repository-name
   GITHUB_REPO=octocat/Hello-World
   ```

2. **Check token permissions**:
   - Token must have `repo` scope for private repositories
   - Token must have `public_repo` scope for public repositories
   - User must have write access to the repository

3. **Verify repository exists**:
   ```bash
   # Check if repository exists and is accessible
   curl -H "Authorization: Bearer $GITHUB_TOKEN" \
        "https://api.github.com/repos/$GITHUB_REPO" \
        | jq '.full_name, .permissions'
   ```

---

## Claude CLI Issues

### Claude CLI Not Found

**Error**: `FileNotFoundError: [Errno 2] No such file or directory: 'claude'`

**Solutions**:

1. **Install Claude CLI**:
   ```bash
   # Check current installation
   which claude
   
   # If not found, install Claude CLI
   # Follow the official installation guide from Anthropic
   ```

2. **Check PATH**:
   ```bash
   echo $PATH
   # Make sure Claude CLI installation directory is in PATH
   
   # Add to PATH if needed
   export PATH="$PATH:/path/to/claude/cli"
   ```

3. **Verify installation**:
   ```bash
   claude --help
   # Should show Claude CLI help information
   ```

### Claude CLI Authentication Issues

**Error**: Authentication failures when calling Claude CLI

**Diagnosis**:
```bash
# Test Claude CLI directly
claude --help

# Check for authentication errors in logs
grep -i "auth" logs/app.log
```

**Solutions**:

1. **Authenticate Claude CLI**:
   ```bash
   # Follow Claude CLI authentication process
   claude auth login
   ```

2. **Check authentication status**:
   ```bash
   # Most Claude CLI implementations have a status command
   claude auth status
   ```

3. **Re-authenticate if needed**:
   ```bash
   claude auth logout
   claude auth login
   ```

### Claude CLI Command Failures

**Error**: Claude CLI commands returning non-zero exit codes

**Diagnosis**:
```bash
# Check logs for detailed error messages
grep -A 5 -B 5 "Claude.*CLI.*error" logs/app.log

# Test Claude CLI manually
claude -p "Hello, Claude!" --dangerously-skip-permissions
```

**Solutions**:

1. **Check command syntax**:
   - Ensure prompts are properly formatted
   - Verify all required parameters are provided
   - Check for special characters that need escaping

2. **Review Claude CLI documentation**:
   - Ensure using correct command-line options
   - Check for version-specific syntax changes

3. **Test with simple prompts**:
   ```bash
   # Test with minimal prompt
   claude -p "What is 2+2?" --dangerously-skip-permissions
   ```

---

## Webhook Problems

### Webhook Not Receiving Events

**Problem**: GitHub webhooks not triggering system actions

**Diagnosis**:

1. **Check webhook configuration in GitHub**:
   - Go to Repository Settings → Webhooks
   - Verify URL is correct: `https://your-domain.com/webhook/github`
   - Check "Recent Deliveries" for delivery attempts

2. **Check webhook status endpoint**:
   ```bash
   curl http://localhost:8000/webhook/status
   ```

3. **Check logs for webhook events**:
   ```bash
   grep -i webhook logs/app.log
   ```

**Solutions**:

1. **Verify webhook URL**:
   - Must be publicly accessible
   - Should use HTTPS in production
   - Check firewall and network configuration

2. **Test webhook locally with ngrok**:
   ```bash
   # Install ngrok for local testing
   ngrok http 8000
   
   # Use the ngrok URL for webhook
   # https://abcd1234.ngrok.io/webhook/github
   ```

3. **Check webhook secret configuration**:
   ```bash
   # Ensure webhook secret matches
   echo $GITHUB_WEBHOOK_SECRET
   # Should match the secret configured in GitHub webhook settings
   ```

### Webhook Signature Verification Failures

**Error**: `400 Bad Request - Invalid webhook signature`

**Diagnosis**:
```bash
# Check webhook secret configuration
echo "Webhook secret configured: ${GITHUB_WEBHOOK_SECRET:+yes}"

# Check webhook logs
grep -i "signature" logs/app.log
```

**Solutions**:

1. **Verify webhook secret**:
   ```bash
   # Generate new webhook secret
   openssl rand -hex 32
   
   # Update both GitHub webhook and environment file
   ```

2. **Disable signature verification for testing**:
   ```bash
   # Temporarily disable for local testing
   GITHUB_WEBHOOK_SECRET=""
   ```

3. **Check GitHub webhook delivery logs**:
   - Look for signature verification errors
   - Verify payload is being sent correctly

### Webhook Events Not Processing

**Problem**: Webhooks received but not triggering issue processing

**Diagnosis**:
```bash
# Check for webhook processing logs
grep -i "webhook.*process" logs/app.log

# Check for issue label matching
grep -i "label.*ai-ready" logs/app.log
```

**Solutions**:

1. **Verify event filtering**:
   - Only `issues` events with `labeled` actions are processed
   - Label must match `GITHUB_ISSUE_LABEL` setting

2. **Check label configuration**:
   ```bash
   echo "Trigger label: $GITHUB_ISSUE_LABEL"
   # Default: ai-ready
   ```

3. **Test webhook manually**:
   ```bash
   curl -X POST "http://localhost:8000/webhook/test" \
        -H "Content-Type: application/json" \
        -d '{
          "action": "labeled",
          "issue": {"number": 123, "labels": [{"name": "ai-ready"}]},
          "label": {"name": "ai-ready"}
        }'
   ```

---

## API Errors

### 500 Internal Server Error

**Problem**: API endpoints returning internal server errors

**Diagnosis**:
```bash
# Check application logs for stack traces
grep -A 10 "ERROR" logs/app.log | tail -20

# Check specific endpoint
curl -v http://localhost:8000/github/issues
```

**Solutions**:

1. **Check configuration**:
   ```bash
   # Verify all required environment variables
   curl http://localhost:8000/health
   ```

2. **Review error logs**:
   ```bash
   # Look for specific error messages
   tail -50 logs/app.log | grep -i error
   ```

3. **Restart service**:
   ```bash
   # Sometimes helps with temporary issues
   pdm run dev  # For development
   # or
   sudo systemctl restart sentinel-system  # For production
   ```

### 401 Authentication Required

**Problem**: API requests failing with authentication errors

**Diagnosis**:
```bash
# Test with token
curl -H "Authorization: Bearer $GITHUB_TOKEN" \
     http://localhost:8000/github/issues

# Test token validity
curl -H "Authorization: Bearer $GITHUB_TOKEN" \
     https://api.github.com/user
```

**Solutions**:

1. **Check authorization header format**:
   ```bash
   # Correct format
   Authorization: Bearer ghp_xxxxxxxxxxxxxxxxxxxx
   
   # Common mistakes
   Authorization: ghp_xxxxxxxxxxxxxxxxxxxx  # Missing "Bearer "
   Authorization: token ghp_xxxxxxxxxxxxxxxxxxxx  # Wrong prefix
   ```

2. **Verify token is active**:
   - Check GitHub token settings
   - Ensure token hasn't expired
   - Verify token has required scopes

### 429 Rate Limit Exceeded

**Problem**: Too many requests to GitHub API

**Diagnosis**:
```bash
# Check GitHub rate limit status
curl -H "Authorization: Bearer $GITHUB_TOKEN" \
     "http://localhost:8000/github/status" | jq .rate_limit

# Check logs for rate limit warnings
grep -i "rate limit" logs/app.log
```

**Solutions**:

1. **Wait for rate limit reset**:
   ```bash
   # Check when rate limit resets
   curl -H "Authorization: Bearer $GITHUB_TOKEN" \
        -I https://api.github.com/user | grep -i rate
   ```

2. **Reduce API calls**:
   - Implement caching
   - Batch operations
   - Use webhooks instead of polling

3. **Use GitHub Apps** (for higher rate limits):
   - Consider migrating to GitHub App authentication
   - Higher rate limits than personal access tokens

---

## Git Operations Issues

### Git Configuration Missing

**Error**: `Git user.name not configured` or similar git configuration errors

**Diagnosis**:
```bash
# Check git configuration
git config --get user.name
git config --get user.email

# Check global vs local configuration
git config --global --get user.name
git config --local --get user.name
```

**Solutions**:

1. **Configure git globally**:
   ```bash
   git config --global user.name "Your Name"
   git config --global user.email "your.email@example.com"
   ```

2. **Configure git locally for the repository**:
   ```bash
   cd /path/to/sentinel-system
   git config user.name "Sentinel System"
   git config user.email "sentinel@yourcompany.com"
   ```

3. **Verify configuration**:
   ```bash
   git config --list | grep user
   ```

### Git Branch Creation Failures

**Problem**: Unable to create or switch branches

**Diagnosis**:
```bash
# Check git status
git status

# Check existing branches
git branch -a

# Check for uncommitted changes
git diff --name-only
```

**Solutions**:

1. **Clean working directory**:
   ```bash
   # Stash uncommitted changes
   git stash
   
   # Or commit changes
   git add .
   git commit -m "Temporary commit"
   ```

2. **Check branch naming**:
   ```bash
   # Verify branch prefix configuration
   echo $GIT_BRANCH_PREFIX
   # Default: sentinel/issue-
   ```

3. **Manual branch creation test**:
   ```bash
   # Test branch creation manually
   git checkout -b test-branch
   git checkout main
   git branch -d test-branch
   ```

### Git Push Failures

**Problem**: Unable to push changes to remote repository

**Diagnosis**:
```bash
# Check remote configuration
git remote -v

# Check authentication
ssh -T git@github.com  # For SSH
# or test HTTPS authentication
```

**Solutions**:

1. **Check remote URL**:
   ```bash
   # Should match your repository
   git remote get-url origin
   
   # Update if needed
   git remote set-url origin https://github.com/user/repo.git
   ```

2. **Authentication issues**:
   ```bash
   # For HTTPS, ensure token has push permissions
   # For SSH, ensure SSH key is configured
   ssh-add -l
   ```

3. **Check branch permissions**:
   - Verify push permissions to repository
   - Check if branch protection rules apply
   - Ensure not pushing to protected branches

---

## Performance Issues

### Slow API Response Times

**Problem**: API endpoints taking too long to respond

**Diagnosis**:
```bash
# Test endpoint response times
time curl http://localhost:8000/health
time curl -H "Authorization: Bearer $GITHUB_TOKEN" \
     http://localhost:8000/github/issues

# Check logs for slow operations
grep -i "slow\|timeout" logs/app.log
```

**Solutions**:

1. **Check GitHub API response times**:
   ```bash
   # Test GitHub API directly
   time curl -H "Authorization: Bearer $GITHUB_TOKEN" \
        https://api.github.com/repos/$GITHUB_REPO/issues
   ```

2. **Monitor Claude CLI performance**:
   ```bash
   # Check Claude CLI response times
   time claude -p "Simple test" --dangerously-skip-permissions
   ```

3. **Check system resources**:
   ```bash
   # Monitor CPU and memory usage
   top
   # or
   htop
   
   # Check disk space
   df -h
   ```

### Memory Usage Issues

**Problem**: High memory consumption or out-of-memory errors

**Diagnosis**:
```bash
# Check memory usage
free -h

# Monitor process memory usage
ps aux | grep python | grep sentinel

# Check for memory leaks in logs
grep -i "memory\|oom" logs/app.log
```

**Solutions**:

1. **Restart service**:
   ```bash
   # Temporary fix for memory leaks
   sudo systemctl restart sentinel-system
   ```

2. **Monitor memory usage over time**:
   ```bash
   # Use monitoring tools
   watch -n 5 'ps aux | grep sentinel | grep -v grep'
   ```

3. **Check for large log files**:
   ```bash
   # Check log file sizes
   ls -lh logs/
   
   # Rotate logs if needed
   logrotate /etc/logrotate.d/sentinel-system
   ```

---

## Logging and Monitoring

### Log File Issues

#### Log Files Not Being Created

**Problem**: No log files in the `logs/` directory

**Diagnosis**:
```bash
# Check logs directory exists
ls -la logs/

# Check permissions
ls -ld logs/

# Check logging configuration
grep -i log src/sentinel_system/config.py
```

**Solutions**:

1. **Create logs directory**:
   ```bash
   mkdir -p logs
   chmod 755 logs
   ```

2. **Check file permissions**:
   ```bash
   # Ensure application can write to logs directory
   touch logs/test.log
   rm logs/test.log
   ```

3. **Verify logging configuration**:
   ```python
   # In Python console
   import logging
   logging.basicConfig(level=logging.INFO)
   logger = logging.getLogger("test")
   logger.info("Test message")
   ```

#### Log Files Too Large

**Problem**: Log files consuming too much disk space

**Solutions**:

1. **Implement log rotation**:
   ```bash
   # Create logrotate configuration
   sudo tee /etc/logrotate.d/sentinel-system << EOF
   /path/to/sentinel-system/logs/*.log {
       daily
       rotate 7
       compress
       delaycompress
       missingok
       notifempty
   }
   EOF
   ```

2. **Clean old logs**:
   ```bash
   # Remove logs older than 7 days
   find logs/ -name "*.log" -mtime +7 -delete
   ```

3. **Adjust log level**:
   ```bash
   # Change from DEBUG to INFO in production
   LOG_LEVEL=INFO
   ```

### Monitoring Service Health

#### Service Not Responding

**Problem**: Health check endpoints not responding

**Diagnosis**:
```bash
# Check if service is running
ps aux | grep python | grep sentinel

# Check if port is open
netstat -tlnp | grep :8000

# Check for service errors
journalctl -u sentinel-system --no-pager -n 50
```

**Solutions**:

1. **Restart service**:
   ```bash
   # Development
   pdm run dev
   
   # Production
   sudo systemctl restart sentinel-system
   ```

2. **Check service configuration**:
   ```bash
   # Verify systemd service file
   sudo systemctl cat sentinel-system
   
   # Check service status
   sudo systemctl status sentinel-system
   ```

3. **Test manual startup**:
   ```bash
   # Run manually to see errors
   cd /path/to/sentinel-system
   pdm run start
   ```

---

## Common Error Messages

### "GitHub token is invalid or expired"

**Cause**: GitHub token authentication failure

**Fix**:
1. Generate new GitHub token
2. Update `.env` file
3. Restart service

### "Gemini CLI not found or not authenticated"

**Cause**: Claude CLI not installed or not authenticated

**Fix**:
1. Install Claude CLI
2. Authenticate: `claude auth login`
3. Test: `claude --help`

### "Repository access denied"

**Cause**: Insufficient permissions for target repository

**Fix**:
1. Check token has `repo` scope
2. Verify repository name is correct
3. Ensure user has write access to repository

### "Invalid webhook signature"

**Cause**: Webhook signature verification failure

**Fix**:
1. Check webhook secret matches GitHub configuration
2. Verify webhook secret is at least 32 characters
3. Regenerate webhook secret if needed

### "Issue processing already in progress"

**Cause**: Issue has `ai-working` label indicating active processing

**Fix**:
1. Wait for processing to complete
2. Check logs for processing status
3. Manually remove `ai-working` label if stuck

### "Git user not configured"

**Cause**: Git user name/email not set

**Fix**:
```bash
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

---

## FAQ

### Q: How do I reset the system to a clean state?

**A**: Follow these steps:

```bash
# 1. Stop the service
sudo systemctl stop sentinel-system

# 2. Clear any stuck processing states
# Remove ai-working labels from issues manually in GitHub

# 3. Clear temporary files
rm -rf /tmp/sentinel_*

# 4. Restart service
sudo systemctl start sentinel-system

# 5. Check health
curl http://localhost:8000/health
```

### Q: How do I enable debug logging?

**A**: Set debug configuration:

```bash
# In .env file
DEBUG=true
LOG_LEVEL=DEBUG

# Restart service
pdm run dev
```

### Q: How do I test the system without GitHub webhooks?

**A**: Use the test endpoints:

```bash
# Test webhook processing
curl -X POST "http://localhost:8000/webhook/test" \
     -H "Content-Type: application/json" \
     -d '{
       "action": "labeled",
       "issue": {"number": 123, "labels": [{"name": "ai-ready"}]},
       "label": {"name": "ai-ready"}
     }'

# Test issue processing directly
curl -X POST "http://localhost:8000/github/issues/123/process" \
     -H "Authorization: Bearer $GITHUB_TOKEN"
```

### Q: How do I change the trigger label?

**A**: Update the configuration:

```bash
# In .env file
GITHUB_ISSUE_LABEL=custom-ai-label

# Restart service
sudo systemctl restart sentinel-system
```

### Q: How do I backup the system configuration?

**A**: Backup these files:

```bash
# Create backup directory
mkdir -p backups/$(date +%Y%m%d)

# Backup configuration
cp .env backups/$(date +%Y%m%d)/
cp -r logs/ backups/$(date +%Y%m%d)/logs/

# Backup database if using one
# cp database.db backups/$(date +%Y%m%d)/

# Create archive
tar -czf backups/sentinel-backup-$(date +%Y%m%d).tar.gz backups/$(date +%Y%m%d)/
```

### Q: How do I migrate to a different repository?

**A**: Update repository configuration:

```bash
# 1. Update .env file
GITHUB_REPO=new-owner/new-repository

# 2. Verify token has access to new repository
curl -H "Authorization: Bearer $GITHUB_TOKEN" \
     "https://api.github.com/repos/new-owner/new-repository"

# 3. Update webhook URL in new repository
# 4. Test configuration
curl http://localhost:8000/health

# 5. Restart service
sudo systemctl restart sentinel-system
```

### Q: How do I monitor system performance?

**A**: Use these monitoring approaches:

```bash
# 1. Health check monitoring
watch -n 30 'curl -s http://localhost:8000/health | jq .status'

# 2. Log monitoring
tail -f logs/app.log | grep -E "(ERROR|WARNING)"

# 3. Resource monitoring
watch -n 5 'ps aux | grep python | grep sentinel'

# 4. GitHub API rate limit monitoring
curl -H "Authorization: Bearer $GITHUB_TOKEN" \
     "http://localhost:8000/github/status" | jq .rate_limit
```

---

## Getting Additional Help

If this troubleshooting guide doesn't resolve your issue:

1. **Check GitHub Issues**: Search for similar problems in the project repository
2. **Enable Debug Logging**: Set `DEBUG=true` and `LOG_LEVEL=DEBUG` for detailed logs
3. **Collect System Information**:
   ```bash
   # System info
   uname -a
   python --version
   pdm --version
   
   # Service info
   curl http://localhost:8000/health
   
   # Recent logs
   tail -100 logs/app.log
   ```

4. **Create Issue Report**: Include all relevant information when reporting issues
5. **Join Community**: Participate in project discussions and forums

Remember: When reporting issues, always include:
- System information
- Complete error messages
- Steps to reproduce
- Configuration (with secrets redacted)
- Relevant log entries