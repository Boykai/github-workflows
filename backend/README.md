# Agent Projects — Backend

FastAPI backend that powers Agent Projects and the **Spec Kit agent pipeline**. This service manages GitHub OAuth, issue/project CRUD via the GitHub GraphQL & REST APIs, AI-powered issue generation (GitHub Copilot SDK by default, Azure OpenAI optional), real-time WebSocket updates, **sub-issue-per-agent workflow** with automatic lifecycle management, **SQLite-backed workflow config persistence**, and the background polling service that orchestrates custom Copilot agents with hierarchical PR branching.

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
├── constants.py               # Status names, agent mappings, display names, cache key helpers
├── exceptions.py              # Custom exception classes
│
├── api/                       # Route handlers
│   ├── auth.py                # OAuth flow, sessions, dev-login
│   ├── board.py               # Project board (Kanban columns + items)
│   ├── chat.py                # Chat messages, proposals, confirm/reject, auto-start polling
│   ├── projects.py            # List/select projects, tasks, WebSocket, SSE
│   ├── tasks.py               # Create/update tasks (GitHub Issues + project items)
│   ├── workflow.py            # Workflow config, pipeline state, polling control, agent discovery, auto-start polling
│   └── webhooks.py            # GitHub webhook (PR ready_for_review)
│
├── models/                    # Pydantic v2 data models
│   ├── board.py               # Board columns, items, custom fields, linked PRs
│   ├── chat.py                # ChatMessage, IssueRecommendation, WorkflowConfig, AgentMapping, display names…
│   ├── project.py             # Project, StatusColumn
│   ├── task.py                # Task / project item
│   └── user.py                # User, session
│
├── migrations/                # Numbered SQL migration scripts (auto-run at startup)
│   ├── 001_initial_schema.sql # Sessions, preferences, project settings, global settings
│   └── 002_add_workflow_config_column.sql  # Full workflow config JSON persistence
│
├── services/                  # Business logic
│   ├── ai_agent.py            # AI issue generation via pluggable CompletionProvider
│   ├── agent_tracking.py      # Agent pipeline tracking (issue body markdown table)
│   ├── cache.py               # In-memory TTL cache (for GitHub API responses)
│   ├── completion_providers.py # Pluggable LLM providers (Copilot SDK / Azure OpenAI)
│   ├── copilot_polling.py     # Background polling loop + agent output posting + sub-issue management
│   ├── github_auth.py         # OAuth token exchange
│   ├── github_projects.py     # GitHub GraphQL + REST client (projects, issues, PRs, Copilot assignment, sub-issues)
│   ├── websocket.py           # WebSocket connection manager, broadcast
│   └── workflow_orchestrator.py  # Pipeline state machine, agent assignment, SQLite config persistence
│
└── prompts/                   # Prompt templates for AI completion providers
    ├── issue_generation.py    # System/user prompts for issue creation (concise JSON output)
    └── task_generation.py     # Legacy task generation prompts
```

## Key Services

### Copilot Polling Service (`copilot_polling.py`)

A background `asyncio.Task` that runs every `COPILOT_POLLING_INTERVAL` seconds (default 60). **Auto-starts** when a user confirms a proposal (chat) or recommendation (workflow) — no manual start required. Each cycle:

1. **Step 0 — Post Agent Outputs**: For each issue with an active pipeline, check if the current agent's work is done on the agent's **sub-issue** (or parent if no sub-issue mapping exists). If so:
   - **Merge child PR first** into the main branch (before posting Done!)
   - Wait 2 seconds for GitHub to process the merge
   - Extract `.md` files from the PR branch and post them as **comments on the sub-issue**
   - Post a `<agent>: Done!` marker on the **sub-issue**
   - **Close the sub-issue** as completed (`state=closed, state_reason=completed`), verified via GitHub API
   - Update the tracking table in the **parent issue** body (mark agent as ✅ Done)
   - Also captures the first PR's branch as the "main branch" for the issue
   - (Only applies to `speckit.specify`, `speckit.plan`, `speckit.tasks` — not `speckit.implement`.)
2. **Step 1 — Check Backlog**: Look for `speckit.specify: Done!` on Backlog issues (checking sub-issues) → transition to Ready and assign `speckit.plan` (branching from the main branch).
3. **Step 2 — Check Ready**: Look for `speckit.plan: Done!` / `speckit.tasks: Done!` → advance the internal pipeline or transition to In Progress and assign `speckit.implement`.
4. **Step 3 — Check In Progress**: For issues with active `speckit.implement` pipeline, detect child PR completion via timeline events (`copilot_work_finished`, `review_requested`) or when PR is no longer a draft. When detected:
   - Merge `speckit.implement` child PR into main branch
   - Delete child branch
   - Convert the **main PR** (first PR for the issue) from draft to ready for review
   - Transition status to "In Review"
   - Request Copilot code review on the main PR
   - If Copilot moves an issue to "In Progress" before the pipeline expects it, the service **accepts the status change** and updates the pipeline state — it does NOT restore the old status (which would re-trigger the agent).
5. **Step 4 — Check In Review**: Ensure Copilot code review has been requested on In Review PRs.
6. **Step 5 — Self-Healing Recovery**: Detect stalled agent pipelines across all non-completed issues. If an issue has an active agent in its tracking table but no corresponding pending assignment or recent progress, the system re-assigns the agent. A per-issue cooldown (5 minutes) prevents rapid re-assignment. On restart, workflow configuration is auto-bootstrapped from SQLite if missing, and sub-issue mappings are reconstructed from `[agent-name]` title prefixes.

**Sub-Issue Targeting**: For each agent, the polling service uses `_get_sub_issue_number()` to find the agent's dedicated sub-issue and `_check_agent_done_on_sub_or_parent()` to check for completion markers on the sub-issue first, falling back to the parent. Comments and Done! markers are always posted on the correct sub-issue.

**Pipeline Reconstruction**: On server restart, `_reconstruct_full_pipeline_state()` rebuilds pipeline state from the tracking table embedded in each issue body, and sub-issue number mappings are reconstructed from sub-issues whose titles start with `[agent-name]`.

**Double-Assignment Prevention**: The polling service tracks `_pending_agent_assignments` to avoid race conditions where concurrent polling loops could re-assign the same agent before Copilot has started working. The pending flag is set BEFORE the API call and cleared on failure. A per-issue recovery cooldown (5 minutes) prevents rapid re-assignment.

### Agent Tracking Service (`agent_tracking.py`)

Provides durable pipeline state via markdown tables embedded in GitHub Issue bodies:

- **Tracking Table Format**: Each issue body includes a `## 🤖 Agent Pipeline` section with a table showing all agents and their states (⏳ Pending, 🔄 Active, ✅ Done)
- `build_agent_pipeline_steps()` — Generates the ordered list of agents from workflow configuration, using **case-insensitive status matching** to handle mismatches between config and project board column names
- `render_tracking_markdown()` — Renders the tracking table as markdown
- `parse_tracking_from_body()` — Parses existing tracking table from issue body
- `mark_agent_active()` / `mark_agent_done()` — Update agent states in the tracking table
- `determine_next_action()` — Reads tracking table + last comment to decide what action to take next

This tracking survives server restarts and provides visibility into pipeline progress directly on GitHub.

### Workflow Orchestrator (`workflow_orchestrator.py`)

Manages per-issue pipeline state, hierarchical PR branching, **sub-issue creation**, and **SQLite-backed workflow config persistence**:

- **SQLite Workflow Config Persistence**: Workflow configuration (agent mappings, status order) is persisted to SQLite via `_persist_workflow_config_to_db()` and loaded on startup via `_load_workflow_config_from_db()`. Uses sync `sqlite3` module (not aiosqlite) for reliability. An in-memory dict cache (`_cached_workflow_configs`) provides fast reads; writes go to both cache and DB.
- **Case-Insensitive Lookups**: The `_ci_get()` helper performs case-insensitive dictionary key lookups throughout the orchestrator, preventing mismatches between config status names and GitHub project board column names (e.g., "in progress" vs "In Progress").
- **Sub-Issue Creation**: `create_all_sub_issues()` creates one sub-issue per agent in the pipeline upfront when a workflow is confirmed. Each sub-issue title is prefixed with `[agent-name]` for later reconstruction. Sub-issue numbers are stored in `_sub_issue_numbers[parent_issue_number][agent_name]`.
- **Main Branch Tracking**: `_issue_main_branches` dict maps issue numbers to their main PR branch info (`MainBranchInfo: {branch, pr_number, head_sha}`). The first PR created for an issue establishes the main branch via `set_issue_main_branch()`. All subsequent agents use `get_issue_main_branch()` to determine their `base_ref` — the main branch **name** is passed as `base_ref` so Copilot creates a child branch from it. The `head_sha` is tracked for audit purposes.
- **Pipeline State Tracking**: `_pipeline_states` dict tracks active agent pipelines per issue, including which agents have completed and which is currently active. This prevents premature status transitions (e.g., waiting for `speckit.implement` to complete before transitioning to "In Review").
- **Status Order**: `get_status_order(config)` returns all 4 statuses (`Backlog → Ready → In Progress → In Review`) including `copilot-review` for the In Review column.
- **Retry-with-Backoff**: Agent assignments retry up to 3 times with exponential backoff (3s → 6s → 12s) to handle transient GitHub API errors, especially after PR merges.
- **Early Pending Flags**: Pending agent assignments are set BEFORE the GitHub API call and cleared only on failure. This prevents race conditions in `execute_full_workflow` where a poll could overlap with the initial assignment.
- `assign_agent_for_status(issue, status)` — Finds the correct agent(s) for a status column using `_ci_get()`, checks for cached main branch or discovers it from existing PRs, and calls `assign_copilot_to_issue()` with the main branch name as `base_ref`.
- `handle_ready_status()` — Handles the Ready column's sequential pipeline (`speckit.plan` → `speckit.tasks`).
- `_advance_pipeline()` / `_transition_after_pipeline_complete()` — Move to the next agent or next status when an agent finishes. Sub-issues are closed as completed when their agent finishes.
- `_check_child_pr_completion()` — For `speckit.implement`, checks if a child PR targeting the main branch exists and shows completion signals.
- `_reconstruct_pipeline_state()` — Rebuilds pipeline state from issue comments on server restart.
- `_update_agent_tracking_state()` — Updates the tracking table in the issue body when agents are assigned or complete.

### Completion Providers (`completion_providers.py`)

Pluggable AI completion layer used by `ai_agent.py` for issue generation:

- **`CompletionProvider`** — Abstract base class defining `async complete(system_prompt, user_prompt, github_token) -> str`
- **`CopilotCompletionProvider`** (default) — Uses `github-copilot-sdk` (`CopilotClient`, `SessionConfig`, `MessageOptions`). Caches clients per GitHub token hash. Creates a session with `system_message={"mode": "replace", "content": ...}`, sends the prompt, gathers `ASSISTANT_MESSAGE` events, and joins them. 120s timeout.
- **`AzureOpenAICompletionProvider`** (optional) — Uses `openai` SDK (or `azure-ai-inference` fallback). Static API key from env vars. `API_VERSION = "2024-02-15-preview"`.
- **`create_completion_provider()`** — Factory that reads `settings.ai_provider` and returns the appropriate provider instance.

### GitHub Projects Service (`github_projects.py`)

All GitHub API interactions. Uses **Claude Opus 4.6** as the default model for Copilot agents.

- **GraphQL**: `list_projects`, `get_project_details`, `get_project_items`, `update_item_status`, `assign_copilot_to_issue` (GraphQL-first with REST fallback, model: `claude-opus-4.6`), `merge_pull_request` (squash merge child PRs into main branch), `mark_pr_ready_for_review`, `request_copilot_review`
- **REST**: `create_issue`, `add_issue_to_project`, `create_issue_comment`, `update_issue_body`, `get_pr_changed_files`, `get_file_content_from_ref`, `update_pr`, `request_review`, `delete_branch` (clean up child branches after merge), `close_issue` (close sub-issues as completed)
- **Sub-Issues**: `create_sub_issue()` — Creates a sub-issue linked to a parent issue, `list_sub_issues()` — Lists all sub-issues for a parent (used for mapping reconstruction)
- `find_existing_pr_for_issue()` — Scans open PRs to discover the first/main PR for an issue
- `get_pull_request()` — Returns PR details including `head_ref` and `base_ref` (used to verify child PRs target the main branch)
- `format_issue_context_as_prompt()` — Builds the prompt sent to Copilot with issue context, agent instructions, output file mappings, and existing PR branch info

## Database & Migrations

The backend uses **SQLite** (WAL mode) for durable storage. The database is created automatically at startup at the path specified by `DATABASE_PATH` (default: `./data/ghchat.db`).

### Migration System

Numbered SQL migration files in `src/migrations/` are executed in order at startup. Each migration runs inside a transaction and is tracked in a `schema_migrations` table so it only executes once.

| Migration | Purpose |
|---|---|
| `001_initial_schema.sql` | Creates `sessions`, `user_preferences`, `project_settings`, `global_settings` tables |
| `002_add_workflow_config_column.sql` | Adds `workflow_config TEXT` column to `project_settings` for full JSON config persistence |

### Workflow Config Storage

Workflow configurations are serialized as JSON and stored in the `project_settings.workflow_config` column. On startup, configs are loaded from the DB into an in-memory cache. All writes go to both cache and DB for consistency. The sync `sqlite3` module is used (not `aiosqlite`) for reliability — DB operations are simple key-value reads/writes that complete quickly.

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
