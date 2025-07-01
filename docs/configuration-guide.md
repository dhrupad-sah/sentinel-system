# Configuration Guide

Comprehensive guide for configuring the Sentinel System environment and deployment settings.

## Table of Contents

1. [Quick Setup](#quick-setup)
2. [Environment Variables](#environment-variables)
3. [GitHub Configuration](#github-configuration)
4. [Gemini CLI Setup](#gemini-cli-setup)
5. [Git Configuration](#git-configuration)
6. [Webhook Configuration](#webhook-configuration)
7. [Security Settings](#security-settings)
8. [Development vs Production](#development-vs-production)
9. [Configuration Validation](#configuration-validation)
10. [Troubleshooting](#troubleshooting)

---

## Quick Setup

### 1. Environment File Setup

```bash
# Copy the example environment file
cp env.example .env

# Edit the configuration
nano .env  # or your preferred editor
```

### 2. Minimum Required Configuration

For basic functionality, you need:

```bash
# Required: GitHub token with repo access
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxx

# Required: Target repository
GITHUB_REPO=owner/repository-name

# Optional but recommended: Webhook security
GITHUB_WEBHOOK_SECRET=your-random-secret-here
```

### 3. Verify Configuration

```bash
# Start the service
pdm run dev

# Check health endpoint
curl http://localhost:8000/health
```

---

## Environment Variables

### Core Application Settings

#### `DEBUG`
- **Type**: Boolean
- **Default**: `false`
- **Description**: Enables debug mode with verbose logging and API documentation
- **Example**: `DEBUG=true`

#### `ALLOWED_ORIGINS`
- **Type**: JSON array of strings
- **Default**: `["*"]`
- **Description**: CORS allowed origins for web access
- **Example**: `ALLOWED_ORIGINS=["http://localhost:3000", "https://myapp.com"]`

#### `LOG_LEVEL`
- **Type**: String
- **Default**: `INFO`
- **Options**: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`
- **Description**: Logging verbosity level
- **Example**: `LOG_LEVEL=DEBUG`

---

## GitHub Configuration

### Authentication

#### `GITHUB_TOKEN` (Required)
- **Type**: String
- **Description**: GitHub Personal Access Token with appropriate permissions
- **Required Permissions**:
  - `repo` (full repository access)
  - `workflow` (if using GitHub Actions)
- **Example**: `GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxx`

**How to create a GitHub token:**
1. Go to GitHub Settings → Developer settings → Personal access tokens
2. Click "Generate new token (classic)"
3. Select required scopes: `repo`, `workflow`
4. Copy the generated token

#### `GITHUB_REPO` (Required)
- **Type**: String
- **Format**: `owner/repository-name`
- **Description**: Target repository for issue processing
- **Example**: `GITHUB_REPO=octocat/Hello-World`

### Webhook Security

#### `GITHUB_WEBHOOK_SECRET`
- **Type**: String
- **Description**: Secret key for webhook signature verification
- **Security**: Use a strong, random secret (32+ characters)
- **Example**: `GITHUB_WEBHOOK_SECRET=your-random-secret-here`

**Generating a secure webhook secret:**
```bash
# Using openssl
openssl rand -hex 32

# Using Python
python -c "import secrets; print(secrets.token_hex(32))"
```

### Label Configuration

#### `GITHUB_ISSUE_LABEL`
- **Type**: String
- **Default**: `ai-ready`
- **Description**: Label that triggers AI processing
- **Example**: `GITHUB_ISSUE_LABEL=needs-ai-help`

#### `GITHUB_PROPOSAL_LABEL`
- **Type**: String
- **Default**: `ai-proposal-pending`
- **Description**: Label applied when AI proposal is pending review
- **Example**: `GITHUB_PROPOSAL_LABEL=awaiting-review`

#### `GITHUB_APPROVED_LABEL`
- **Type**: String
- **Default**: `ai-approved`
- **Description**: Label applied when proposal is approved for implementation
- **Example**: `GITHUB_APPROVED_LABEL=approved-for-implementation`

#### `GITHUB_WORKING_LABEL`
- **Type**: String
- **Default**: `ai-working`
- **Description**: Label applied during active processing
- **Example**: `GITHUB_WORKING_LABEL=processing-in-progress`

---

## Gemini CLI Setup

### Prerequisites

The Sentinel System uses Google's Gemini CLI for AI functionality. You need to:

1. **Install Gemini CLI**:
   ```bash
   # Follow Google's official installation guide
   curl -sSL https://sdk.cloud.google.com | bash
   gcloud components install gemini-cli
   ```

2. **Authenticate with Google**:
   ```bash
   gcloud auth login
   gcloud auth application-default login
   ```

3. **Verify Installation**:
   ```bash
   gemini --version
   gemini models list  # Should show available models
   ```

### Configuration

#### `GEMINI_MODEL`
- **Type**: String
- **Default**: `gemini-2.5-flash`
- **Description**: Gemini model to use for AI processing
- **Options**: `gemini-2.5-flash`, `gemini-pro`, etc.
- **Example**: `GEMINI_MODEL=gemini-pro`

**Note**: The system uses the authenticated Google account's default project and credentials. No API key is required in the environment file.

---

## Git Configuration

### User Configuration

Git requires user configuration for commits:

```bash
# Set globally (recommended)
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"

# Or set locally in the repository
git config user.name "Sentinel System"
git config user.email "sentinel@yourcompany.com"
```

### Branch and Commit Prefixes

#### `GIT_BRANCH_PREFIX`
- **Type**: String
- **Default**: `sentinel/issue-`
- **Description**: Prefix for automatically created branches
- **Example**: `GIT_BRANCH_PREFIX=feature/ai-`
- **Result**: Creates branches like `feature/ai-123`

#### `GIT_COMMIT_PREFIX`
- **Type**: String
- **Default**: `"feat: "`
- **Description**: Prefix for commit messages
- **Example**: `GIT_COMMIT_PREFIX="fix: "`
- **Result**: Commits like `fix: resolve issue #123 validation error`

---

## Webhook Configuration

### GitHub Webhook Setup

1. **Go to Repository Settings**:
   - Navigate to your GitHub repository
   - Go to Settings → Webhooks
   - Click "Add webhook"

2. **Configure Webhook**:
   ```
   Payload URL: https://your-domain.com/webhook/github
   Content type: application/json
   Secret: [your GITHUB_WEBHOOK_SECRET]
   ```

3. **Select Events**:
   - Individual events: `Issues`
   - Or use "Send me everything" for testing

4. **Verify Setup**:
   ```bash
   # Check webhook status
   curl http://localhost:8000/webhook/status
   ```

### Webhook Security

#### Signature Verification
- **Enabled by default** in production
- **Can be disabled** for development by setting `GITHUB_WEBHOOK_SECRET=""` (empty string)
- **Uses HMAC-SHA256** for secure payload verification

#### Payload Validation
- Content-Type validation
- Event type filtering (only `issues` events)
- Action filtering (`labeled`/`unlabeled` only)

---

## Security Settings

### Token Security

#### Best Practices:
1. **Use minimal permissions**: Only grant necessary repository access
2. **Rotate tokens regularly**: Replace tokens every 90 days
3. **Use organization tokens**: For team repositories
4. **Store securely**: Never commit tokens to repositories

#### Repository Permissions:
```
Required:
- Contents: Read (to analyze code)
- Issues: Write (to comment and label)
- Pull requests: Write (to create PRs)
- Metadata: Read (repository info)

Optional:
- Actions: Read (for workflow integration)
```

### Network Security

#### CORS Configuration:
```bash
# Production: Restrict to specific domains
ALLOWED_ORIGINS=["https://your-app.com", "https://api.your-app.com"]

# Development: Allow localhost
ALLOWED_ORIGINS=["http://localhost:3000", "http://localhost:8000"]

# Testing: Allow all (not recommended for production)
ALLOWED_ORIGINS=["*"]
```

#### Webhook Security:
- Always use HTTPS for webhook URLs
- Use strong, unique webhook secrets
- Monitor webhook delivery logs
- Implement rate limiting if needed

---

## Development vs Production

### Development Configuration

```bash
# .env.development
DEBUG=true
LOG_LEVEL=DEBUG
ALLOWED_ORIGINS=["http://localhost:3000", "http://localhost:8000"]
GITHUB_WEBHOOK_SECRET=""  # Disabled for local testing
```

### Production Configuration

```bash
# .env.production
DEBUG=false
LOG_LEVEL=INFO
ALLOWED_ORIGINS=["https://your-domain.com"]
GITHUB_WEBHOOK_SECRET=your-secure-secret-here
```

### Environment-Specific Settings

#### Development Features:
- API documentation available at `/docs`
- Verbose error messages
- Webhook signature verification disabled
- Test webhook endpoint available

#### Production Features:
- API documentation hidden
- Minimal error messages
- Webhook signature verification enforced
- Enhanced security logging

---

## Configuration Validation

### Health Check Validation

The system validates configuration on startup:

```bash
curl http://localhost:8000/health
```

**Validation Checks**:
- GitHub token validity and permissions
- Repository access
- Gemini CLI availability and authentication
- Git configuration completeness
- Webhook secret configuration

### Manual Validation

#### Test GitHub Access:
```bash
curl -H "Authorization: Bearer $GITHUB_TOKEN" \
     "https://api.github.com/repos/OWNER/REPO"
```

#### Test Gemini CLI:
```bash
gemini models list
```

#### Test Git Configuration:
```bash
git config --get user.name
git config --get user.email
```

---

## Troubleshooting

### Common Configuration Issues

#### GitHub Token Issues:
```bash
# Error: 401 Unauthorized
# Solution: Check token validity and permissions
curl -H "Authorization: Bearer $GITHUB_TOKEN" \
     "https://api.github.com/user"
```

#### Repository Access Issues:
```bash
# Error: 404 Not Found or 403 Forbidden
# Solution: Verify repository name and token permissions
curl -H "Authorization: Bearer $GITHUB_TOKEN" \
     "https://api.github.com/repos/OWNER/REPO"
```

#### Gemini CLI Issues:
```bash
# Error: Command not found
# Solution: Install and authenticate Gemini CLI
which gemini
gcloud auth list
```

#### Git Configuration Issues:
```bash
# Error: Git user not configured
# Solution: Set git user configuration
git config --global user.name "Your Name"
git config --global user.email "your@email.com"
```

#### Webhook Issues:
```bash
# Error: Invalid signature
# Solution: Verify webhook secret matches configuration
echo "Check webhook secret in GitHub settings"
```

### Configuration Testing

#### Test Full Configuration:
```bash
# Start service
pdm run dev

# Test health endpoint
curl http://localhost:8000/health

# Test GitHub integration
curl -H "Authorization: Bearer $GITHUB_TOKEN" \
     "http://localhost:8000/github/issues?limit=1"

# Test webhook (if configured)
curl -X POST "http://localhost:8000/webhook/test" \
     -H "Content-Type: application/json" \
     -d '{"action": "labeled", "issue": {"number": 1, "labels": [{"name": "ai-ready"}]}, "label": {"name": "ai-ready"}}'
```

### Environment Variable Debugging

```bash
# Check all environment variables
printenv | grep -E "(GITHUB|GEMINI|GIT|DEBUG)"

# Validate JSON arrays
python -c "import json, os; print(json.loads(os.getenv('ALLOWED_ORIGINS', '[]')))"
```

---

## Advanced Configuration

### Custom Label Workflows

You can customize the label workflow by creating custom labels:

```bash
# Create custom labels via GitHub API
curl -X POST "https://api.github.com/repos/OWNER/REPO/labels" \
     -H "Authorization: Bearer $GITHUB_TOKEN" \
     -d '{
       "name": "ai-ready",
       "color": "0075ca",
       "description": "Issue ready for AI processing"
     }'
```

### Multiple Environment Management

```bash
# Use different environment files
cp .env .env.development
cp .env .env.production

# Load specific environment
export $(cat .env.production | xargs)
pdm run start
```

### Configuration Monitoring

```bash
# Monitor configuration changes
watch -n 30 'curl -s http://localhost:8000/health | jq .configuration'
```

---

## Support

For configuration issues:
1. Check the [Troubleshooting Guide](troubleshooting-guide.md)
2. Verify all required environment variables are set
3. Test individual components (GitHub API, Gemini CLI, Git)
4. Check system logs for detailed error messages