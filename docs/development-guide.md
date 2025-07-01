# Development Guide

Complete guide for setting up a development environment and contributing to the Sentinel System.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Setup](#environment-setup)
3. [Project Structure](#project-structure)
4. [Development Workflow](#development-workflow)
5. [Code Standards](#code-standards)
6. [Testing](#testing)
7. [Debugging](#debugging)
8. [Contributing](#contributing)
9. [Release Process](#release-process)

---

## Prerequisites

### System Requirements

- **Python**: 3.10 or higher
- **PDM**: Python Dependency Management
- **Git**: For version control
- **Gemini CLI**: Google's AI CLI tool
- **curl**: For API testing (usually pre-installed)

### Development Tools (Recommended)

- **VS Code** with Python extension
- **GitHub CLI** (`gh`) for repository management
- **Postman** or **Insomnia** for API testing
- **Docker** (optional, for containerized development)

---

## Environment Setup

### 1. Clone and Setup

```bash
# Clone the repository
git clone https://github.com/your-org/sentinel-system.git
cd sentinel-system

# Install PDM if not already installed
curl -sSL https://raw.githubusercontent.com/pdm-project/pdm/main/install-pdm.py | python3 -

# Install dependencies
pdm install
```

### 2. Development Dependencies

```bash
# Install development dependencies
pdm install --group dev

# Verify installation
pdm list
```

### 3. Pre-commit Hooks (Optional)

```bash
# Install pre-commit hooks for code quality
pdm run pip install pre-commit
pre-commit install
```

### 4. Environment Configuration

```bash
# Copy and configure environment
cp env.example .env.development
nano .env.development  # Edit with your settings
```

**Development Environment Variables:**
```bash
# .env.development
DEBUG=true
LOG_LEVEL=DEBUG
ALLOWED_ORIGINS=["http://localhost:3000", "http://localhost:8000"]
GITHUB_TOKEN=your_development_token
GITHUB_REPO=your-username/test-repo
GITHUB_WEBHOOK_SECRET=""  # Disabled for local development
```

### 5. Gemini CLI Setup

```bash
# Install Google Cloud SDK
curl https://sdk.cloud.google.com | bash
exec -l $SHELL

# Install Gemini CLI
gcloud components install gemini-cli

# Authenticate
gcloud auth login
gcloud auth application-default login

# Verify setup
gemini --version
gemini models list
```

### 6. Git Configuration

```bash
# Configure git for development
git config user.name "Your Name"
git config user.email "your.email@example.com"

# Configure git hooks (optional)
git config core.hooksPath .githooks
```

---

## Project Structure

```
sentinel-system/
├── src/
│   └── sentinel_system/
│       ├── __init__.py
│       ├── main.py              # FastAPI application entry point
│       ├── config.py            # Configuration management
│       ├── routers/             # API route handlers
│       │   ├── __init__.py
│       │   ├── health.py        # Health check endpoints
│       │   ├── github.py        # GitHub API endpoints
│       │   └── webhook.py       # Webhook endpoints
│       └── services/            # Business logic layer
│           ├── __init__.py
│           ├── gemini_service.py    # AI processing service
│           ├── github_service.py   # GitHub API service
│           ├── git_service.py      # Git operations service
│           └── issue_processor.py  # Main workflow orchestrator
├── tests/                       # Test suite
├── docs/                        # Documentation
├── logs/                        # Application logs
├── pyproject.toml              # Project configuration
├── pdm.lock                    # Dependency lock file
├── env.example                 # Environment template
└── README.md                   # Project overview
```

### Key Components

#### **main.py**
- FastAPI application initialization
- Router registration
- Middleware configuration
- Startup/shutdown events

#### **config.py**
- Pydantic Settings for environment variables
- Configuration validation
- Logging setup

#### **Services Layer**
- **GeminiService**: AI processing and analysis
- **GitHubService**: GitHub API interactions
- **GitService**: Local git operations
- **IssueProcessor**: Workflow orchestration

#### **Routers Layer**
- **HealthRouter**: System monitoring endpoints
- **GitHubRouter**: Issue and repository management
- **WebhookRouter**: GitHub webhook processing

---

## Development Workflow

### 1. Start Development Server

```bash
# Load development environment
export $(cat .env.development | xargs)

# Start server with hot reloading
pdm run dev

# Server will be available at http://localhost:8000
```

### 2. API Documentation

Visit http://localhost:8000/docs for interactive API documentation (Swagger UI).

### 3. Health Check

```bash
# Test system health
curl http://localhost:8000/health

# Expected response indicates all services are configured correctly
```

### 4. Feature Development Process

#### A. Create Feature Branch
```bash
git checkout -b feature/your-feature-name
```

#### B. Implement Changes
- Follow code standards (see below)
- Add tests for new functionality
- Update documentation as needed

#### C. Test Changes
```bash
# Run tests
pdm run test

# Run linting
pdm run lint

# Run type checking
pdm run type-check

# Format code
pdm run format
```

#### D. Commit Changes
```bash
git add .
git commit -m "feat: add your feature description"
```

#### E. Create Pull Request
```bash
gh pr create --title "Add your feature" --body "Description of changes"
```

---

## Code Standards

### Python Code Style

The project uses **Black** for code formatting and **Ruff** for linting:

```bash
# Format code
pdm run format

# Check formatting
black --check src tests

# Lint code
pdm run lint

# Fix auto-fixable lint issues
ruff check src tests --fix
```

### Type Hints

All functions must include type hints:

```python
from typing import List, Optional, Dict, Any

async def process_issue(
    issue_number: int,
    background_tasks: BackgroundTasks
) -> Dict[str, Any]:
    """Process a GitHub issue with proper type hints."""
    ...
```

### Documentation Standards

#### Docstrings
Use Google-style docstrings:

```python
def analyze_issue(self, issue_data: Dict[str, Any]) -> str:
    """Analyze GitHub issue and generate proposal.
    
    Args:
        issue_data: GitHub issue data containing title, body, labels
        
    Returns:
        Markdown-formatted analysis and proposal
        
    Raises:
        GeminiError: If AI analysis fails
        ValidationError: If issue data is invalid
    """
    ...
```

#### API Documentation
Document all endpoints with proper examples:

```python
@router.post("/issues/{issue_number}/process")
async def process_issue(
    issue_number: int,
    background_tasks: BackgroundTasks
) -> Dict[str, Any]:
    """
    Process GitHub issue with AI analysis.
    
    - **issue_number**: GitHub issue number
    - **Returns**: Processing status and job details
    """
    ...
```

### Error Handling Standards

#### Service Layer Errors
```python
class ServiceError(Exception):
    """Base exception for service layer errors."""
    pass

class GitHubServiceError(ServiceError):
    """GitHub API related errors."""
    pass

# Usage
try:
    result = await github_service.get_issue(issue_number)
except GitHubServiceError as e:
    logger.error(f"Failed to fetch issue {issue_number}: {str(e)}")
    raise HTTPException(status_code=404, detail="Issue not found")
```

#### Logging Standards
```python
import logging

logger = logging.getLogger(__name__)

# Good logging practices
logger.info(f"Processing issue #{issue_number}")
logger.warning(f"Rate limit approaching: {remaining_requests} requests left")
logger.error(f"Failed to process issue #{issue_number}: {str(e)}")
logger.debug(f"Issue data: {issue_data}")  # Detailed debug info
```

---

## Testing

### Test Structure

```
tests/
├── __init__.py
├── conftest.py                 # Pytest configuration and fixtures
├── test_main.py               # Application startup tests
├── test_config.py             # Configuration tests
├── routers/
│   ├── test_health.py         # Health endpoint tests
│   ├── test_github.py         # GitHub API tests
│   └── test_webhook.py        # Webhook tests
└── services/
    ├── test_gemini_service.py # AI service tests
    ├── test_github_service.py # GitHub service tests
    ├── test_git_service.py    # Git service tests
    └── test_issue_processor.py # Workflow tests
```

### Running Tests

```bash
# Run all tests
pdm run test

# Run specific test file
pytest tests/test_github.py

# Run with coverage
pytest --cov=src tests/

# Run tests with verbose output
pytest -v tests/
```

### Writing Tests

#### Unit Tests
```python
import pytest
from unittest.mock import Mock, patch
from src.sentinel_system.services.github_service import GitHubService

@pytest.fixture
def github_service():
    """Create GitHub service instance for testing."""
    return GitHubService()

@patch('httpx.AsyncClient.get')
async def test_get_issue_success(mock_get, github_service):
    """Test successful issue retrieval."""
    # Mock response
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"number": 123, "title": "Test Issue"}
    mock_get.return_value = mock_response
    
    # Test
    result = await github_service.get_issue(123)
    
    # Assertions
    assert result["number"] == 123
    assert result["title"] == "Test Issue"
```

#### Integration Tests
```python
@pytest.mark.asyncio
async def test_webhook_processing_integration():
    """Test complete webhook processing flow."""
    webhook_data = {
        "action": "labeled",
        "issue": {"number": 123, "labels": [{"name": "ai-ready"}]},
        "label": {"name": "ai-ready"}
    }
    
    # Process webhook
    result = await process_webhook_event(webhook_data)
    
    # Verify processing was queued
    assert result["status"] == "queued"
```

### Test Fixtures

```python
# conftest.py
import pytest
from fastapi.testclient import TestClient
from src.sentinel_system.main import app

@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)

@pytest.fixture
def mock_github_token():
    """Mock GitHub token for testing."""
    return "ghp_test_token_123456"

@pytest.fixture
def sample_issue_data():
    """Sample issue data for testing."""
    return {
        "number": 123,
        "title": "Test Issue",
        "body": "This is a test issue",
        "labels": [{"name": "ai-ready"}]
    }
```

---

## Debugging

### Local Debugging

#### VS Code Configuration
Create `.vscode/launch.json`:

```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Debug Sentinel System",
            "type": "python",
            "request": "launch",
            "module": "uvicorn",
            "args": [
                "src.sentinel_system.main:app",
                "--host", "0.0.0.0",
                "--port", "8000",
                "--reload"
            ],
            "envFile": ".env.development",
            "console": "integratedTerminal"
        }
    ]
}
```

#### Debug Logging
```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Add debug breakpoints
import pdb; pdb.set_trace()
```

### Production Debugging

#### Log Analysis
```bash
# View application logs
tail -f logs/app.log

# Filter for errors
grep "ERROR" logs/app.log

# Search for specific issue
grep "issue.*123" logs/app.log
```

#### Health Monitoring
```bash
# Monitor system health
watch -n 30 'curl -s http://localhost:8000/health | jq'

# Check GitHub rate limits
curl -H "Authorization: Bearer $GITHUB_TOKEN" \
     "http://localhost:8000/github/status"
```

---

## Contributing

### Getting Started

1. **Fork the Repository**
   ```bash
   gh repo fork your-org/sentinel-system
   cd sentinel-system
   ```

2. **Set Up Development Environment**
   Follow the [Environment Setup](#environment-setup) section

3. **Find an Issue**
   - Check GitHub Issues for `good-first-issue` label
   - Join discussions on feature requests
   - Report bugs you discover during development

### Code Contribution Process

#### 1. Create Issue
- Describe the problem or feature
- Include reproduction steps for bugs
- Discuss approach before large changes

#### 2. Implement Solution
- Follow coding standards
- Add comprehensive tests
- Update documentation
- Keep commits atomic and well-described

#### 3. Submit Pull Request
```bash
# Create PR with good description
gh pr create --title "feat: add issue auto-labeling" \
             --body "Implements automatic labeling based on issue content analysis..."
```

#### 4. Code Review Process
- Address reviewer feedback promptly
- Keep discussion professional and constructive
- Update tests and documentation as requested

### Contribution Guidelines

#### What to Contribute
- **Bug fixes**: Always welcome
- **Documentation improvements**: Help other developers
- **Performance optimizations**: With benchmarks
- **New features**: Discuss first in issues
- **Security improvements**: Critical priority

#### What to Avoid
- **Breaking changes**: Without discussion
- **Code style changes**: Use automated formatters
- **Large refactors**: Break into smaller PRs
- **Untested code**: All code needs tests

---

## Release Process

### Version Management

The project follows [Semantic Versioning](https://semver.org/):
- **MAJOR**: Breaking changes
- **MINOR**: New features, backward compatible
- **PATCH**: Bug fixes, backward compatible

### Release Steps

#### 1. Prepare Release
```bash
# Update version in pyproject.toml
# Update CHANGELOG.md
# Run full test suite
pdm run test
pdm run lint
pdm run type-check
```

#### 2. Create Release Branch
```bash
git checkout -b release/v1.2.0
git commit -am "chore: prepare release v1.2.0"
git push origin release/v1.2.0
```

#### 3. Create Release PR
```bash
gh pr create --title "Release v1.2.0" \
             --body "Release notes and changelog updates"
```

#### 4. Tag Release
```bash
git tag v1.2.0
git push origin v1.2.0
```

#### 5. GitHub Release
```bash
gh release create v1.2.0 --title "v1.2.0" --notes-file CHANGELOG.md
```

### Deployment

#### Development Deployment
```bash
# Deploy to development environment
pdm run start
```

#### Production Deployment
```bash
# Build production package
pdm build

# Deploy with production settings
export $(cat .env.production | xargs)
pdm run start
```

---

## Development Tools

### Useful Scripts

Create a `scripts/` directory with helper scripts:

#### `scripts/dev-setup.sh`
```bash
#!/bin/bash
# Development environment setup script
cp env.example .env.development
pdm install --group dev
pre-commit install
echo "Development environment ready!"
```

#### `scripts/test-all.sh`
```bash
#!/bin/bash
# Run all quality checks
set -e

echo "Running tests..."
pdm run test

echo "Running linting..."
pdm run lint

echo "Running type checking..."
pdm run type-check

echo "Checking formatting..."
black --check src tests

echo "All checks passed!"
```

### IDE Configuration

#### VS Code Extensions
- Python (Microsoft)
- Pylance (Microsoft)
- Black Formatter
- Ruff
- GitLens
- GitHub Pull Requests

#### VS Code Settings
```json
{
    "python.defaultInterpreterPath": ".venv/bin/python",
    "python.linting.enabled": true,
    "python.linting.ruffEnabled": true,
    "python.formatting.provider": "black",
    "python.testing.pytestEnabled": true
}
```

---

## Support

### Getting Help

1. **Documentation**: Check this guide first
2. **GitHub Issues**: Search existing issues
3. **Discussions**: Use GitHub Discussions for questions
4. **Code Review**: Ask for help in pull requests

### Reporting Issues

When reporting bugs, include:
- Python version
- Operating system
- Complete error messages
- Steps to reproduce
- Expected vs actual behavior

### Contributing Documentation

Documentation contributions are highly valued:
- Fix typos and unclear explanations
- Add examples and use cases
- Improve setup instructions
- Translate documentation

---

## Next Steps

After setting up your development environment:

1. **Run the test suite** to ensure everything works
2. **Try the API endpoints** using the development server
3. **Read the codebase** to understand the architecture
4. **Pick a small issue** to make your first contribution
5. **Join the community** through GitHub Discussions

Happy coding! 🚀