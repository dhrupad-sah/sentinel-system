# System Architecture Workflow

This document outlines the high-level workflow of the Sentinel System.

## Workflow Description

The Sentinel System is designed to monitor GitHub repositories for new issues and pull requests, process them, and potentially interact with a large language model (LLM) for automated responses or actions.

1.  **GitHub Webhook Event:** GitHub sends webhook events (e.g., `issues`, `pull_request`) to the Sentinel System's webhook endpoint.
2.  **Webhook Ingestion:** The `webhook` router receives and validates the incoming webhook payload.
3.  **Event Routing:** The validated event is routed to the appropriate service based on its type (e.g., `issue_processor` for issues, `git_service` for pull requests).
4.  **Issue Processing (for issues):**
    *   The `issue_processor` service analyzes the issue content.
    *   It may interact with the `gemini_service` (LLM) to generate a response, categorize the issue, or suggest actions.
    *   The `github_service` is used to post comments or update the issue status on GitHub.
5.  **Git Service (for pull requests):**
    *   The `git_service` handles pull request events, potentially fetching code, running checks, or interacting with the `gemini_service` for code review suggestions.
    *   The `github_service` is used to post comments or update pull request status on GitHub.
6.  **Gemini Service Interaction:** The `gemini_service` acts as an interface to the LLM, handling prompts, responses, and any necessary context management.
7.  **GitHub Service Interaction:** The `github_service` provides a centralized way to interact with the GitHub API (e.g., posting comments, updating labels, fetching repository details).

## System Architecture Diagram

```mermaid
graph TD
    A[GitHub Webhook Event] --> B(Webhook Ingestion);
    B --> C{Event Routing};
    C -- Issues --> D[Issue Processing];
    C -- Pull Requests --> E[Git Service];
    D --> F(Gemini Service Interaction);
    E --> F;
    D --> G(GitHub Service Interaction);
    E --> G;
    F --> H[LLM (e.g., Gemini)];
    G --> I[GitHub API];
    H --> D;
    H --> E;
    I --> D;
    I --> E;
```

**To view the diagram:**

This diagram is written in Mermaid syntax. You can view it by:
*   Using a Markdown editor with Mermaid support (e.g., VS Code with a Mermaid extension).
*   Pasting the code into an online Mermaid live editor (e.g., <https://mermaid.live/>).
*   Using a tool that renders Mermaid to an image (e.g., `mermaid-cli`).
