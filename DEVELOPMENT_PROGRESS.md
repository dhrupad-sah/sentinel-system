# Autonomous GitHub Issue Resolution System - Development Progress

## Project Overview
An autonomous tool that picks GitHub issues, uses Claude Code CLI to work on them, and creates PRs automatically with human oversight.

## System Architecture

### Core Workflow (v1 - Event-Driven)
1. **Issue Discovery**: GitHub webhooks trigger instantly when labels are added/removed
2. **AI Analysis**: Claude Code CLI analyzes issue and proposes solution 
3. **Human Review Loop**: Human reviews/approves AI proposal via GitHub labels
4. **Implementation**: AI implements approved solution (triggered by webhook)
5. **Git Workflow**: Auto-commit, branch creation, PR submission, and issue closure

## Version Planning

### v0 - MVP (Completed ✅)
**Scope**: Simple single-threaded approach with scheduler-based polling
- ✅ Single chat session for all issues (process one issue at a time)
- ✅ Basic GitHub integration (issue fetching, commenting, labeling)
- ✅ Simple human approval workflow
- ✅ Basic git operations (commit, branch, push, PR)
- ✅ Configuration via settings file
- ✅ Scheduler-based issue polling
- ✅ Complete end-to-end workflow with automatic issue closure

**Key Decisions for v0**:
- ✅ Process issues sequentially (no parallel processing)
- ✅ Single Claude Code CLI chat session
- ✅ Wait for current issue completion before picking next
- ✅ Simple label-based approval system
- ✅ Polling-based issue detection

### v1 - Event-Driven Architecture (Current Target 🔄)
**Major Upgrade**: Replace polling with real-time webhooks
- **🔄 GitHub Webhooks Integration**: Real-time event-driven processing
  - Replace scheduler polling with instant webhook triggers
  - Process issues immediately when labels are added/removed
  - Webhook signature verification for security
  - Background task processing for async handling
- **🔄 System Cleanup**: Remove scheduler-related components
  - Remove SchedulerService and scheduler router
  - Keep manual trigger endpoints for testing/debugging
  - Streamline codebase and reduce complexity
- **🔄 Enhanced Performance**: Instant response times
  - No more 1-10 minute delays from polling
  - Immediate processing when `ai-ready` label added
  - Instant implementation when `ai-approved` label added
- **🔄 Production Readiness**: Improved reliability and efficiency
  - Reduced API calls (no unnecessary polling)
  - Better resource utilization
  - Webhook retry handling via GitHub's built-in mechanism

**Future v1 Enhancements**:
- [ ] **Separate Chat Threads**: Each issue gets its own isolated Claude Code chat session
- [ ] **Parallel Processing**: Handle multiple issues simultaneously
- [ ] **Enhanced Error Handling**: Robust fallback mechanisms
- [ ] **Metrics & Monitoring**: Track success rates, processing times

### v2 - Advanced Features
**Future Considerations**:
- [ ] **Automated Testing**: Run tests before creating PR
- [ ] **Multi-repo Support**: Handle issues across multiple repositories
- [ ] **Smart Issue Prioritization**: AI-driven issue selection
- [ ] **Integration with CI/CD**: Automated deployment pipeline
- [ ] **Advanced Human Review**: Web interface for proposal review

## Current Development Status

### Completed
- [x] **Docker & CI/CD Pipeline** ✅ (Latest Update)
  - [x] Created GitHub Actions workflow for automated builds
  - [x] Implemented automatic semantic versioning with tags (sentinel-v*)
  - [x] Set up GitHub Container Registry publishing (ghcr.io/dhrupadsah/sentinel-system)
  - [x] Created optimized Dockerfile with PDM support
  - [x] Added .dockerignore for efficient builds
  - [x] Configured workflow triggers for main branch and manual dispatch
- [x] **AI Integration Migration** ✅
  - [x] Migrated from Gemini CLI to Claude Code CLI
  - [x] Updated all service references and imports
  - [x] Updated configuration settings (CLAUDE_MODEL)
  - [x] Updated documentation and examples
  - [x] Verified Claude Code CLI integration working
- [x] Project architecture design
- [x] Development roadmap creation
- [x] PDM project setup with dependencies
- [x] FastAPI application structure
- [x] Configuration management (Pydantic Settings)
- [x] API router structure (health, github, scheduler)
- [x] GitHub service implementation
- [x] Health check endpoints
- [x] Environment configuration example
- [x] Comprehensive README documentation
- [x] Claude Code CLI service implementation (using authenticated CLI)
- [x] Issue processor service (complete workflow orchestration)
- [x] Git service implementation (branch management, commits, pushes)
- [x] Scheduler service implementation (automated processing)
- [x] Updated health checks with service integration

### In Progress - v1 Webhook Implementation
- [x] Testing and validation of complete workflow
- [x] Error handling improvements (git stashing, phase separation)
- [x] Fixed premature code implementation during analysis phase
- [x] Automatic issue closure after PR creation
- [x] **GitHub Webhooks Integration** ✅
  - [x] Create webhook endpoint with signature verification
  - [x] Implement label-based event filtering
  - [x] Add background task processing for async handling
  - [x] Handle `issues.labeled` and `issues.unlabeled` events
  - [x] Add webhook test endpoint for debugging
- [x] **System Cleanup** ✅
  - [x] Remove SchedulerService and related components
  - [x] Remove scheduler router and endpoints
  - [x] Update configuration to remove scheduler settings
  - [x] Clean up imports and dependencies
- [ ] **Documentation Updates** 🔄
  - [ ] Update README with webhook setup instructions
  - [ ] Add webhook configuration examples
  - [ ] Document GitHub webhook setup process

### Next Steps
1. ✅ ~~Set up project structure~~
2. ✅ ~~Implement GitHub API integration~~
3. ✅ ~~Complete Claude Code CLI integration service~~
4. ✅ ~~Create basic issue processing workflow~~
5. ✅ ~~Implement scheduler service~~
6. ✅ ~~Add git operations service~~
7. ✅ ~~Set up Docker containerization and CI/CD pipeline~~
8. 🔄 Testing and refinement
9. 🔄 Create environment file and configure settings
10. 🔄 Test complete end-to-end workflow
11. 🔄 Add monitoring and logging improvements
12. 🔄 Production deployment and testing

## Technical Decisions

### GitHub Integration (v1 - Webhook-Driven)
- **GitHub Webhooks**: Real-time event processing for instant responses
- **GitHub REST API**: For issue management, commenting, and labeling
- **Webhook Events**: Listen for `issues.labeled` and `issues.unlabeled` events
- **Security**: Webhook signature verification using GitHub secret
- **Labels for workflow state management**:
  - `ai-ready` - Issues ready for AI processing (triggers analysis)
  - `ai-proposal-pending` - AI has proposed solution, awaiting human review
  - `ai-approved` - Human has approved AI's proposal (triggers implementation)
  - `ai-working` - AI is currently implementing solution

### Event Processing Architecture
- **Async Processing**: Background tasks for webhook event handling
- **Quick Response**: Return 200 OK immediately to prevent GitHub retries
- **Idempotent Processing**: Handle duplicate webhooks gracefully
- **Error Handling**: Robust error recovery with GitHub's built-in retry mechanism

### AI Integration
- Claude Code CLI already configured in target repository
- No git cloning needed (works within existing repo)
- AI adds comments to issues for transparency
- Background task processing prevents blocking webhook responses

### Human Review Process
- AI posts proposal as GitHub issue comment
- Human reviews and either approves or requests changes via labels
- Webhook instantly triggers next phase when approval label added
- Iterative refinement until approval received

## Configuration Requirements
- Target repository settings
- GitHub API credentials
- Issue label configurations
- Claude Code CLI setup verification
- Scheduling parameters
- Docker deployment environment
- GitHub Container Registry access

## Risk Mitigation
- Human approval required before any code changes
- All AI actions logged as GitHub comments
- Git branch isolation for each issue
- Rollback capabilities

---

*Last Updated: December 2024*
*Version: v1 Implementation Phase - Webhook Integration* 