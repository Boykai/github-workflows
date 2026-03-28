# Solune — Backend

FastAPI backend that powers Solune and its **customizable Agent Pipelines**. This service manages GitHub OAuth, issue/project CRUD via the GitHub GraphQL & REST APIs, AI-powered issue generation (GitHub Copilot SDK by default, Azure OpenAI optional), real-time WebSocket updates, **sub-issue-per-agent workflow** with automatic lifecycle management, **SQLite-backed workflow config persistence**, and the background polling service that orchestrates custom GitHub agents with hierarchical PR branching, all integrated with **GitHub Projects** for real-time tracking.

## Setup

```bash
uv sync --extra dev
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

- Swagger UI: <http://localhost:8000/api/docs>
- ReDoc: <http://localhost:8000/api/redoc>

## Architecture

The backend follows a layered architecture: **API routes → Services → Models**, with three large service modules decomposed into focused sub-module packages. A `dependencies.py` module provides FastAPI DI helpers backed by `app.state` singletons registered in the lifespan handler.

```text
src/
├── main.py                    # FastAPI app factory, lifespan (DB init, DI registration, TaskGroup)
├── config.py                  # Pydantic Settings from env / .env
├── constants.py               # Status names, agent mappings, display names, cache key helpers
├── dependencies.py            # FastAPI DI helpers (app.state → Depends())
├── exceptions.py              # Custom exception classes (AppException tree + PersistenceError)
├── protocols.py               # Protocol types for service interfaces (ModelProvider, CacheInvalidationPolicy)
├── utils.py                   # Shared helpers: utcnow(), resolve_repository()
│
├── api/                       # Route handlers (8 modules)
│   ├── auth.py                # OAuth flow, consolidated session dependency
│   ├── board.py               # Project board (Kanban columns + items)
│   ├── chat.py                # Chat messages, proposals, confirm/reject, auto-start polling
│   ├── projects.py            # List/select projects, tasks, WebSocket, SSE
│   ├── settings.py            # User preferences, global settings, project settings
│   ├── tasks.py               # Create/update tasks (GitHub Issues + project items)
│   ├── workflow.py            # Workflow config, pipeline state, polling control, agent discovery
│   └── webhooks.py            # GitHub webhook (PR ready_for_review)
│
├── models/                    # Pydantic v2 data models (7 focused modules)
│   ├── agent.py               # AgentSource, AgentAssignment, AvailableAgent
│   ├── board.py               # Board columns, items, custom fields, linked PRs
│   ├── chat.py                # ChatMessage, SenderType, ActionType (+ backward-compat re-exports)
│   ├── project.py             # GitHubProject, StatusColumn
│   ├── recommendation.py     # AITaskProposal, IssueRecommendation, labels, priorities
│   ├── settings.py            # User preferences, global settings, project settings
│   ├── task.py                # Task / project item
│   ├── user.py                # UserSession
│   └── workflow.py            # WorkflowConfiguration, WorkflowTransition, TriggeredBy
│
├── migrations/                # Numbered SQL migration scripts (auto-run at startup)
│   ├── 001_initial_schema.sql
│   ├── …
│   └── 026_performance_indexes.sql
│
├── middleware/                 # HTTP middleware stack
│   ├── request_id.py          #   Request-ID tracing
│   ├── csp.py                 #   Content Security Policy headers
│   ├── csrf.py                #   Double-submit cookie CSRF protection
│   ├── rate_limit.py          #   Per-user/IP rate limiting
│   └── admin_guard.py         #   Admin-only endpoint protection
│
├── services/                  # Business logic layer
│   ├── github_projects/       # GitHub API package (decomposed from monolithic file)
│   │   ├── __init__.py        #   GitHubClientFactory (pooled githubkit SDK clients) + re-exports
│   │   ├── service.py         #   Main service class, REST and GraphQL via githubkit SDK
│   │   └── graphql.py         #   GraphQL query/mutation strings
│   │
│   ├── copilot_polling/       # Background polling package (decomposed, 7 sub-modules)
│   │   ├── __init__.py        #   Re-exports all public names + ensure_polling_started()
│   │   ├── state.py           #   Module-level mutable state (polling flags, caches, cooldowns)
│   │   ├── helpers.py         #   Sub-issue lookup, tracking state helpers
│   │   ├── polling_loop.py    #   Start/stop/tick scheduling
│   │   ├── agent_output.py    #   Agent output extraction and posting to sub-issues
│   │   ├── pipeline.py        #   Pipeline advancement, status transitions
│   │   ├── recovery.py        #   Stalled issue recovery with cooldowns
│   │   └── completion.py      #   PR completion detection (main + child PRs)
│   │
│   ├── workflow_orchestrator/  # Pipeline orchestration package (decomposed, 4 sub-modules)
│   │   ├── __init__.py        #   Re-exports all public names
│   │   ├── models.py          #   WorkflowContext, PipelineState, WorkflowState (leaf dep)
│   │   ├── config.py          #   Async config load/persist/defaults, transition audit log
│   │   ├── transitions.py     #   Pipeline state, branch tracking, sub-issue maps
│   │   └── orchestrator.py    #   WorkflowOrchestrator class, assign_agent_for_status()
│   │
│   ├── ai_agent.py            # AI issue generation via pluggable CompletionProvider
│   ├── agent_tracking.py      # Durable agent pipeline tracking (issue body markdown table)
│   ├── cache.py               # In-memory TTL cache (for GitHub API responses)
│   ├── completion_providers.py # Pluggable LLM providers (Copilot SDK / Azure OpenAI)
│   ├── database.py            # aiosqlite connection, WAL mode, schema migrations
│   ├── github_auth.py         # OAuth token exchange
│   ├── session_store.py       # Session CRUD (async SQLite)
│   ├── settings_store.py      # Settings persistence (async SQLite)
│   ├── task_registry.py       # Centralized fire-and-forget asyncio.Task tracking + drain
│   └── websocket.py           # WebSocket connection manager, broadcast
│
└── prompts/                   # Prompt templates for AI completion providers
    ├── issue_generation.py    # System/user prompts for issue creation (concise JSON output)
    └── task_generation.py     # Task generation prompts
```

## Key Services

### Task Registry (`services/task_registry.py`)

Centralized registry for fire-and-forget `asyncio` tasks. Every `asyncio.create_task()` call that is not directly awaited should go through the module-level `task_registry` singleton instead. The registry:

- **Tracks** all pending tasks so none are silently garbage-collected.
- **Logs** failures at WARNING level with the task name and exception.
- **`drain(timeout=30.0)`** — graceful shutdown: awaits pending tasks, cancels stragglers.
- **`cancel_all()`** — forceful shutdown: cancels every non-done task.

### Copilot Polling Service (`services/copilot_polling/`)

Decomposed into 7 focused sub-modules. A background `asyncio.Task` that runs every `COPILOT_POLLING_INTERVAL` seconds (default 60). **Auto-starts** when a user confirms a proposal (chat) or recommendation (workflow) — no manual start required. Each cycle:

1. **Step 0 — Post Agent Outputs**: For each issue with an active pipeline, check if the current agent's work is done on the agent's **sub-issue** (or parent if no sub-issue mapping exists). If so:
   - **Merge child PR first** into the main branch (before posting Done!)
   - Wait 2 seconds for GitHub to process the merge
   - Extract `.md` files from the PR branch and post them as **comments on the sub-issue**
   - Post a `<agent>: Done!` marker on the **sub-issue**
   - **Close the sub-issue** as completed (`state=closed, state_reason=completed`), verified via GitHub API
   - Update the tracking table in the **parent issue** body (mark agent as ✅ Done)
   - Also captures the first PR's branch as the "main branch" for the issue
   - (Only applies to agents whose work produces `.md` output files — not the final implementation agent.)
2. **Step 1 — Check Backlog**: Look for first-stage agent `Done!` markers on Backlog issues (checking sub-issues) → transition to Ready and assign next agent(s) (branching from the main branch).
3. **Step 2 — Check Ready**: Look for middle-stage agent `Done!` markers → advance the internal pipeline or transition to In Progress and assign the implementation agent.
4. **Step 3 — Check In Progress**: For issues with an active implementation agent, detect child PR completion via timeline events (`copilot_work_finished`, `review_requested`) or when PR is no longer a draft. When detected:
   - Merge implementation agent's child PR into main branch
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

**Sub-Modules**: `state.py` (mutable state, flags, caches), `helpers.py` (sub-issue lookup, tracking helpers), `polling_loop.py` (start/stop/tick scheduling), `agent_output.py` (extraction and posting to sub-issues), `pipeline.py` (advancement, status transitions), `recovery.py` (stalled issue recovery with cooldowns), `completion.py` (PR completion detection for main + child PRs).

### Agent Tracking Service (`agent_tracking.py`)

Provides durable pipeline state via markdown tables embedded in GitHub Issue bodies:

- **Tracking Table Format**: Each issue body includes a `## 🤖 Agent Pipeline` section with a table showing all agents and their states (⏳ Pending, 🔄 Active, ✅ Done)
- `build_agent_pipeline_steps()` — Generates the ordered list of agents from workflow configuration, using **case-insensitive status matching** to handle mismatches between config and project board column names
- `render_tracking_markdown()` — Renders the tracking table as markdown
- `parse_tracking_from_body()` — Parses existing tracking table from issue body
- `mark_agent_active()` / `mark_agent_done()` — Update agent states in the tracking table
- `determine_next_action()` — Reads tracking table + last comment to decide what action to take next

This tracking survives server restarts and provides visibility into pipeline progress directly on GitHub.

### Workflow Orchestrator (`services/workflow_orchestrator/`)

Decomposed into 4 focused sub-modules managing per-issue pipeline state, hierarchical PR branching, **sub-issue creation**, and **async SQLite-backed workflow config persistence**:

#### `models.py` — Data Models (leaf dependency, no service imports)

- **`WorkflowContext`** — Immutable context for pipeline operations (issue, config, service refs)
- **`PipelineState`** — Tracks active agent pipelines per issue (completed agents, current agent)
- **`WorkflowState`** — Top-level state container (pipeline states, main branches, sub-issue maps)
- **`MainBranchInfo`** — Branch name, PR number, head SHA for hierarchical branching
- **`_ci_get()`** — Case-insensitive dictionary key lookup, prevents mismatches between config status names and GitHub project board column names

#### `config.py` — Async Configuration Persistence

- **Async aiosqlite** for config load/persist (migrated from sync sqlite3)
- `load_workflow_config_from_db()` / `persist_workflow_config_to_db()` — Read/write workflow JSON to `project_settings.workflow_config`
- `get_default_workflow_config()` — Builds default config from available Copilot agents
- `log_transition()` — Audit trail for pipeline state transitions
- In-memory dict cache for fast reads; writes go to both cache and DB

#### `transitions.py` — Pipeline State Management

- `advance_pipeline()` / `transition_after_pipeline_complete()` — Move to the next agent or next status when an agent finishes
- `set_issue_main_branch()` / `get_issue_main_branch()` — Main branch tracking for hierarchical PR branching
- `update_sub_issue_map()` / `get_sub_issue_number()` — Sub-issue number mappings per parent issue per agent
- `reconstruct_pipeline_state()` — Rebuilds pipeline state from issue comments on server restart

#### `orchestrator.py` — WorkflowOrchestrator Class

- `assign_agent_for_status(issue, status)` — Finds the correct agent(s) for a status column, manages branch refs
- `handle_ready_status()` — Handles the Ready column’s sequential or parallel pipeline (executing agents within the current execution group)
- `create_all_sub_issues()` — Creates one sub-issue per agent upfront when a workflow is confirmed
- `_check_child_pr_completion()` — For the implementation agent, checks child PR targeting the main branch
- **Retry-with-Backoff**: Agent assignments retry up to 3 times with exponential backoff (3s → 6s → 12s)
- **Early Pending Flags**: Set BEFORE the GitHub API call and cleared only on failure to prevent race conditions
- Singleton factory via `get_workflow_orchestrator()`

### Session Store (`session_store.py`)

Manages session lifecycle in SQLite:

- `create_session()` — Creates a new session row with encrypted token data
- `get_session()` — Retrieves a session by ID, returns `None` if expired
- `delete_session()` — Removes a session (logout)
- `cleanup_expired_sessions()` — Periodic cleanup of expired sessions (runs every `SESSION_CLEANUP_INTERVAL` seconds, default 3600)

### Settings Store (`settings_store.py`)

Manages user preferences, global settings, and per-project settings in SQLite:

- `get_effective_user_settings()` / `upsert_user_preferences()` — CRUD for user preferences (AI, display, workflow defaults, notifications)
- `get_global_settings()` / `update_global_settings()` — CRUD for global settings
- `get_effective_project_settings()` / `upsert_project_settings()` — CRUD for project-specific settings
- `flatten_user_preferences_update()` / `flatten_global_settings_update()` — Flatten nested update models for SQL upserts

### Database Service (`database.py`)

SQLite database lifecycle management:

- `get_db()` — Singleton aiosqlite connection factory
- `init_database()` — Creates database file, enables WAL mode, runs migrations
- `close_database()` — Graceful shutdown
- `run_migrations()` — Executes numbered SQL migration files in order, tracked by `schema_version` table

### Completion Providers (`completion_providers.py`)

Pluggable AI completion layer used by `ai_agent.py` for issue generation:

- **`CompletionProvider`** — Abstract base class defining `async complete(system_prompt, user_prompt, github_token) -> str`
- **`CopilotCompletionProvider`** (default) — Uses `github-copilot-sdk` (`CopilotClient`, `SessionConfig`, `MessageOptions`). Caches clients per GitHub token hash. Creates a session with `system_message={"mode": "replace", "content": ...}`, sends the prompt, gathers `ASSISTANT_MESSAGE` events, and joins them. 120s timeout.
- **`AzureOpenAICompletionProvider`** (optional) — Uses `openai` SDK (or `azure-ai-inference` fallback). Static API key from env vars. `API_VERSION = "2024-02-15-preview"`.
- **`create_completion_provider()`** — Factory that reads `settings.ai_provider` and returns the appropriate provider instance.

### GitHub Projects Service (`services/github_projects/`)

Decomposed into 2 sub-modules handling all GitHub API interactions. Uses **Claude Opus 4.6** as the default model for Copilot agents.

#### `service.py` — GitHubProjectsService class

- Pooled `githubkit` SDK clients via `GitHubClientFactory` with built-in retry, throttling, and HTTP cache
- `_rest()` / `_rest_response()` — SDK-routed REST helpers with automatic auth and rate-limit tracking
- `_graphql()` — GraphQL request routing through SDK client
- **GraphQL**: `list_projects`, `get_project_details`, `get_project_items`, `update_item_status`, `assign_copilot_to_issue` (GraphQL-first with REST fallback, model: `claude-opus-4.6`), `merge_pull_request` (squash merge child PRs), `mark_pr_ready_for_review`, `request_copilot_review`
- **REST**: `create_issue`, `add_issue_to_project`, `create_issue_comment`, `update_issue_body`, `get_pr_changed_files`, `get_file_content_from_ref`, `update_pr`, `request_review`, `delete_branch`, `close_issue`
- **Sub-Issues**: `create_sub_issue()`, `list_sub_issues()` (for mapping reconstruction)
- `find_existing_pr_for_issue()`, `get_pull_request()`, `format_issue_context_as_prompt()`

#### `graphql.py` — GraphQL query/mutation strings

- All GraphQL operations extracted as named constants for readability and reuse

## Database & Migrations

The backend uses **aiosqlite** (SQLite in WAL mode) for fully async durable storage. The database is created automatically at startup at the path specified by `DATABASE_PATH` (default: `/app/data/settings.db`). All database access uses `async`/`await` — no blocking I/O on the event loop. Chat persistence uses `BEGIN IMMEDIATE` transactions via `chat_store.transaction()` to prevent inconsistent state during multi-step writes.

### Migration System

Numbered SQL migration files in `src/migrations/` are executed in order at startup. Each migration runs inside a transaction and is tracked in a `schema_migrations` table so it only executes once.

| Migration | Purpose |
|---|---|
| `001_initial_schema.sql` | Creates `sessions`, `user_preferences`, `project_settings`, `global_settings` tables |
| `002_add_workflow_config_column.sql` | Adds `workflow_config TEXT` column to `project_settings` for full JSON config persistence |
| … | _(see `src/migrations/` for the full list)_ |
| `026_performance_indexes.sql` | Adds indexes on `admin_github_user_id`, `selected_project_id`, and chat session columns |

### Workflow Config Storage

Workflow configurations are serialized as JSON and stored in the `project_settings.workflow_config` column. On startup, configs are loaded from the DB into an in-memory cache. All writes go to both cache and DB for consistency. Uses async aiosqlite for all operations.

## Testing

```bash
pytest tests/ -v                          # All tests
pytest tests/unit/ -v                     # Unit tests only
pytest tests/integration/ -v              # Integration tests
pytest tests/test_api_e2e.py -v           # API E2E tests
pytest tests/ -v --tb=short -q            # Quick summary
```

The test suite covers:

- **Unit**: Each service in isolation (AI agent, cache, completion providers, config, database, GitHub auth/projects, models, prompts, session store, settings store, polling, webhooks, WebSocket, workflow orchestrator, all API routes)
- **Integration**: Custom agent assignment flow
- **E2E**: Full API endpoint testing

Total: **1,450+ tests** across 50 test files (47 unit + 1 integration + 1 E2E + 1 conftest).

## Environment

All configuration is loaded from the root `.env` file (one directory up). See the root [README.md](../README.md#environment-variables-reference) for the full list of environment variables.
