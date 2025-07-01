# Sentinel System Deployment Guide

This guide shows you how to deploy the Sentinel System on any machine using Docker Compose.

## Prerequisites

- Docker and Docker Compose installed
- Claude Code CLI installed and authenticated (for AI functionality)
- GitHub Personal Access Token
- Git configured with your credentials

## Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/dhrupad-sah/sentinel-system.git
cd sentinel-system
```

### 2. Create Environment File
```bash
cp env.example .env
```

### 3. Configure Environment Variables
Edit `.env` file with your settings:

```bash
# Required Settings
GITHUB_TOKEN=your_github_token_here
GITHUB_REPO=owner/repository-name

# Optional Settings (defaults shown)
GITHUB_WEBHOOK_SECRET=your_webhook_secret
GITHUB_ISSUE_LABEL=sentinel-analyze
GITHUB_PROPOSAL_LABEL=proposal-pending
GITHUB_APPROVED_LABEL=approved
GITHUB_WORKING_LABEL=implementing
CLAUDE_MODEL=claude-sonnet-4-20250514
```

### 4. Run with Docker Compose

#### Option A: Build from Source (Development)
```bash
# Build and run
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

#### Option B: Use Pre-built Image (Production)
```bash
# Run with pre-built image
docker-compose -f docker-compose.prod.yml up -d

# View logs
docker-compose -f docker-compose.prod.yml logs -f

# Stop
docker-compose -f docker-compose.prod.yml down
```

## Deployment Options

### Development Deployment (`docker-compose.yml`)
- **Builds from source** - Uses local Dockerfile
- **Good for**: Development, testing, customization
- **Build time**: ~2-3 minutes
- **Image size**: Built locally

### Production Deployment (`docker-compose.prod.yml`)
- **Uses pre-built image** - From GitHub Container Registry
- **Good for**: Production, quick deployment
- **Start time**: ~30 seconds
- **Image size**: Optimized and cached

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GITHUB_TOKEN` | ✅ | - | GitHub Personal Access Token |
| `GITHUB_REPO` | ✅ | - | Target repository (owner/repo) |
| `GITHUB_WEBHOOK_SECRET` | ⚠️ | - | Webhook secret (recommended) |
| `GITHUB_ISSUE_LABEL` | ❌ | `sentinel-analyze` | Trigger label |
| `GITHUB_PROPOSAL_LABEL` | ❌ | `proposal-pending` | Proposal pending label |
| `GITHUB_APPROVED_LABEL` | ❌ | `approved` | Approval label |
| `GITHUB_WORKING_LABEL` | ❌ | `implementing` | Working label |
| `CLAUDE_MODEL` | ❌ | - | Claude model override |
| `DEBUG` | ❌ | `false` | Debug mode |
| `LOG_LEVEL` | ❌ | `INFO` | Logging level |

### GitHub Token Permissions
Your GitHub token needs these permissions:
- `repo` - Full repository access
- `write:packages` - For container registry (if building)

### Claude Code CLI Setup
The container assumes Claude Code CLI is available. For production deployments, you may need to:

1. **Mount Claude CLI from host**:
   ```yaml
   volumes:
     - /usr/local/bin/claude:/usr/local/bin/claude:ro
   ```

2. **Or use Claude API** instead of CLI (requires code changes)

## Networking

### Ports
- **8000**: Main application port (HTTP API)

### Health Checks
- **Endpoint**: `http://localhost:8000/health`
- **Interval**: 30 seconds
- **Timeout**: 10 seconds
- **Retries**: 3

## Data Persistence

### Logs
Logs are persisted in `./logs` directory:
```bash
# View application logs
tail -f logs/app.log

# View container logs
docker-compose logs -f sentinel-system
```

### Configuration
Environment configuration is mounted from `.env` file.

## Monitoring

### Health Check
```bash
# Check if service is healthy
curl http://localhost:8000/health

# Check detailed health status
curl http://localhost:8000/health | jq
```

### Service Status
```bash
# Check container status
docker-compose ps

# View resource usage
docker stats sentinel-system-sentinel-system-1
```

## Troubleshooting

### Common Issues

#### 1. Claude CLI Not Available
```bash
# Check if Claude CLI is accessible in container
docker-compose exec sentinel-system claude --help
```

#### 2. GitHub Authentication Issues
```bash
# Check GitHub token
curl -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/user
```

#### 3. Port Already in Use
```bash
# Use different port
docker-compose up -d -p 8001:8000
```

#### 4. Permission Issues
```bash
# Fix logs directory permissions
sudo chown -R $(id -u):$(id -g) logs/
```

### Logs and Debugging

```bash
# Application logs
docker-compose logs sentinel-system

# Follow logs in real-time
docker-compose logs -f sentinel-system

# Debug mode
echo "DEBUG=true" >> .env
docker-compose restart
```

## Production Considerations

### Security
- Use webhook secrets for GitHub webhooks
- Run behind reverse proxy (nginx/traefik)
- Use non-root user in container
- Limit container resources

### Scaling
- For multiple repositories, run separate instances
- Use load balancer for high availability
- Monitor resource usage and scale accordingly

### Backup
- Backup `.env` configuration
- Backup logs directory if needed
- Repository access tokens should be rotated regularly

## Updates

### Updating to Latest Version
```bash
# Pull latest image
docker-compose -f docker-compose.prod.yml pull

# Restart with new image
docker-compose -f docker-compose.prod.yml up -d

# Or rebuild from source
docker-compose build --no-cache
docker-compose up -d
```

## Support

- **GitHub Issues**: [Report issues](https://github.com/dhrupad-sah/sentinel-system/issues)
- **Documentation**: Check README.md for detailed configuration
- **Logs**: Always check application logs first for troubleshooting 