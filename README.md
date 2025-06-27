# Sentinel System

Autonomous GitHub issue resolution system using Gemini CLI and FastAPI.

## Overview

Sentinel System is an autonomous tool that:
- 🔍 Monitors GitHub repositories for issues with specific labels
- 🤖 Uses Gemini CLI to analyze and propose solutions
- 👥 Facilitates human review and approval process
- ⚡ Automatically implements approved solutions
- 🚀 Creates pull requests with the implemented changes

## Features

- **Automated Issue Detection**: Monitors GitHub repos for labeled issues
- **AI-Powered Analysis**: Uses Gemini CLI for intelligent issue analysis
- **Human-in-the-Loop**: Requires human approval before implementation
- **FastAPI Web Service**: RESTful API for monitoring and control
- **Comprehensive Health Checks**: System status and dependency monitoring
- **Flexible Configuration**: Environment-based configuration management

## Quick Start

### Prerequisites

- Python 3.10+
- PDM (Python Dependency Management)
- Gemini CLI installed and configured
- GitHub repository with appropriate permissions
- Git configured locally

### Installation

1. **Clone and setup**:
   ```bash
   git clone <repository-url>
   cd sentinel-system
   pdm install
   ```

2. **Configure environment**:
   ```bash
   cp env.example .env
   # Edit .env with your configuration
   ```

3. **Required environment variables**:
   - `GITHUB_TOKEN`: GitHub personal access token
   - `GITHUB_REPO`: Target repository (owner/repo)
   - `GEMINI_API_KEY`: Gemini API key
   - See `env.example` for all options

4. **Start the service**:
   ```bash
   pdm run dev
   ```

5. **Access the API**:
   - Web UI: http://localhost:8000/docs
   - Health check: http://localhost:8000/health

## API Endpoints

### Health & Status
- `GET /health` - Comprehensive system health check
- `GET /health/ready` - Readiness probe
- `GET /health/live` - Liveness probe

### GitHub Operations
- `GET /github/issues` - List issues with filtering
- `GET /github/issues/{issue_number}` - Get specific issue
- `POST /github/issues/{issue_number}/process` - Process issue with AI
- `POST /github/issues/{issue_number}/approve` - Approve AI proposal
- `POST /github/issues/{issue_number}/reject` - Reject AI proposal

### Scheduler Management
- `GET /scheduler/status` - Get scheduler status
- `POST /scheduler/start` - Start automated processing
- `POST /scheduler/stop` - Stop automated processing
- `POST /scheduler/run-now` - Trigger immediate run

## Workflow

1. **Issue Detection**: System monitors for issues with `ai-ready` label
2. **AI Analysis**: Gemini CLI analyzes issue and posts proposal comment
3. **Human Review**: Human reviews proposal and adds approval/rejection labels
4. **Implementation**: AI implements approved solution
5. **PR Creation**: System creates pull request with changes

## Configuration

Key configuration options in `.env`:

```bash
# GitHub Settings
GITHUB_TOKEN=your_token
GITHUB_REPO=owner/repo
GITHUB_ISSUE_LABEL=ai-ready

# Gemini Settings  
GEMINI_API_KEY=your_key
GEMINI_MODEL=gemini-2.5-flash

# Scheduler Settings
SCHEDULER_INTERVAL_MINUTES=10
SCHEDULER_ENABLED=false
```

## Development

### Project Structure
```
src/sentinel_system/
├── main.py              # FastAPI application
├── config.py            # Configuration management
├── routers/             # API route handlers
│   ├── health.py        # Health check endpoints
│   ├── github.py        # GitHub API endpoints
│   └── scheduler.py     # Scheduler endpoints
└── services/            # Business logic layer
    ├── github_service.py    # GitHub API service
    ├── issue_processor.py   # Issue processing logic
    └── scheduler_service.py # Scheduler management
```

### Development Commands
```bash
# Start development server
pdm run dev

# Run tests
pdm run test

# Format code
pdm run format

# Lint code
pdm run lint

# Type checking
pdm run type-check
```

## Deployment

### Docker (Coming Soon)
```bash
docker build -t sentinel-system .
docker run -p 8000:8000 --env-file .env sentinel-system
```

### Manual Deployment
1. Install dependencies: `pdm install --prod`
2. Set environment variables
3. Run: `pdm run start`

## Monitoring

The system provides comprehensive monitoring through:
- Health check endpoints
- Structured logging
- Scheduler execution logs
- GitHub API interaction tracking

## Security

- All GitHub operations require valid token
- Human approval required for all code changes
- Git operations isolated to separate branches
- Configurable CORS settings

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Support

For issues and questions:
- Check the health endpoint: `/health`
- Review logs for error details
- Ensure all dependencies are properly configured

---

**Version**: 0.1.0 (v0 - MVP)  
**Status**: Development  
**Next**: See [DEVELOPMENT_PROGRESS.md](DEVELOPMENT_PROGRESS.md) for roadmap
