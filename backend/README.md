# GitHub Projects Chat — Backend

FastAPI backend that powers the GitHub Projects Chat Interface and the **Spec Kit agent pipeline**. This service manages GitHub OAuth, issue/project CRUD via the GitHub GraphQL & REST APIs, AI-powered issue generation (Azure OpenAI), real-time WebSocket updates, and the background polling service that orchestrates custom Copilot agents with hierarchical PR branching.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

## Run

```bash
# From the backend/ directory
uvicorn src.main:app --reload --port 8000

# Or from the repo root with Docker
docker compose up --build -d
```

## API Documentation

When `DEBUG=true`:

- Swagger UI: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc

## Architecture

```
src/
├── main.py                    # FastAPI app, lifecycle (startup → polling), CORS, routers
├── config.py                  # Pydantic Settings from env / .env
├── constants.py               # GitHub API URLs, status constants
├── exceptions.py              # Custom exception classes
│
├── api/                       # Route handlers
│   ├── auth.py                # OAuth flow, sessions, dev-login
│   ├── chat.py                # Chat messages, proposals, confirm/reject
│   ├── projects.py            # List/select projects, tasks, WebSocket, SSE
│   ├── tasks.py               # Create/update tasks (GitHub Issues + project items)
│   ├── workflow.py            # Workflow config, pipeline state, polling control
│   └── webhooks.py            # GitHub webhook (PR ready_for_review)
│
├── models/                    # Pydantic v2 data models
│   ├── chat.py                # ChatMessage, IssueRecommendation, WorkflowConfig, AgentMapping…
│   ├── project.py             # Project, StatusColumn
│   ├── task.py                # Task / project item
│   └── user.py                # User, session
│
├── services/                  # Business logic
│   ├── ai_agent.py            # Azure OpenAI — issue generation from natural language
│   ├── cache.py               # In-memory TTL cache (for GitHub API responses)
│   ├── copilot_polling.py     # Background polling loop + agent output posting
│   ├── github_auth.py         # OAuth token exchange
│   ├── github_projects.py     # GitHub GraphQL + REST client (projects, issues, PRs, Copilot assignment)
│   ├── websocket.py           # WebSocket connection manager, broadcast
│   └── workflow_orchestrator.py  # Pipeline state machine, agent assignment, status transitions
│
└── prompts/                   # Prompt templates for Azure OpenAI
    ├── issue_generation.py    # System/user prompts for issue creation
    └── task_generation.py     # Legacy task generation prompts
```

## Key Services

### Copilot Polling Service (`copilot_polling.py`)

A background `asyncio.Task` that runs every `COPILOT_POLLING_INTERVAL` seconds (default 60). Each cycle:

1. **Step 0 — Post Agent Outputs**: For each issue with an active pipeline, check if the current agent's PR work is done. If so, extract `.md` files from the PR branch and post them as issue comments, then post a `<agent>: Done!` marker. Also captures the first PR's branch as the "main branch" for the issue.
2. **Step 1 — Check Backlog**: Look for `speckit.specify: Done!` on Backlog issues → transition to Ready and assign `speckit.plan` (branching from the main branch).
3. **Step 2 — Check Ready**: Look for `speckit.plan: Done!` / `speckit.tasks: Done!` → merge child PR into main branch, delete child branch, advance the internal pipeline or transition to In Progress and assign `speckit.implement`. Before assigning `speckit.implement`, discovers and caches the main branch from linked PRs if not already cached.
4. **Step 3 — Check In Progress**: Detect Copilot PR completion via timeline events (`copilot_work_finished`, `review_requested`) → merge `speckit.implement` child PR into main branch, delete child branch, convert main draft PR to ready, transition to In Review.
5. **Step 4 — Check In Review**: Ensure Copilot code review has been requested on the PR.

### Workflow Orchestrator (`workflow_orchestrator.py`)

Manages per-issue pipeline state and hierarchical PR branching:

- **Main Branch Tracking**: `_issue_main_branches` dict maps issue numbers to their main PR branch info (`{branch, pr_number}`). The first PR created for an issue establishes the main branch via `set_issue_main_branch()`. All subsequent agents use `get_issue_main_branch()` to determine their `base_ref`.
- `assign_agent_for_status(issue, status)` — Finds the correct agent(s) for a status column, checks for cached main branch or discovers it from existing PRs, and calls `assign_copilot_to_issue()` with the main branch as `base_ref`.
- `handle_ready_status()` — Handles the Ready column's sequential pipeline (`speckit.plan` → `speckit.tasks`).
- `_advance_pipeline()` / `_transition_after_pipeline_complete()` — Move to the next agent or next status when an agent finishes. Merges child PRs and deletes child branches on agent completion.
- `_reconstruct_pipeline_state()` — Rebuilds pipeline state from issue comments on server restart.

### GitHub Projects Service (`github_projects.py`)

All GitHub API interactions:

- **GraphQL**: `list_projects`, `get_project_details`, `get_project_items`, `update_item_status`, `assign_copilot_to_issue` (GraphQL-first with REST fallback), `merge_pull_request` (squash merge child PRs into main branch), `mark_pr_ready_for_review`, `request_copilot_review`
- **REST**: `create_issue`, `add_issue_to_project`, `create_issue_comment`, `get_pr_changed_files`, `get_file_content_from_ref`, `update_pr`, `request_review`, `delete_branch` (clean up child branches after merge)
- `find_existing_pr_for_issue()` — Scans open PRs to discover the first/main PR for an issue
- `get_pull_request()` — Returns PR details including `head_ref` and `base_ref` (used to verify child PRs target the main branch)
- `format_issue_context_as_prompt()` — Builds the prompt sent to Copilot with issue context, agent instructions, output file mappings, and existing PR branch info

## Testing

```bash
pytest tests/ -v                          # All tests
pytest tests/unit/ -v                     # Unit tests only
pytest tests/integration/ -v              # Integration tests
pytest tests/test_api_e2e.py -v           # API E2E tests
pytest tests/ -v --tb=short -q            # Quick summary
```

The test suite covers:
- **Unit**: Each service in isolation (AI agent, cache, polling, GitHub auth/projects, webhooks, workflow orchestrator, models)
- **Integration**: Custom agent assignment flow
- **E2E**: Full API endpoint testing

## Environment

All configuration is loaded from the root `.env` file (one directory up). See the root [README.md](../README.md#environment-variables-reference) for the full list of environment variables.
