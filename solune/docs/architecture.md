# Architecture

Solune is a three-service application — a React frontend, a FastAPI backend, and a Signal messaging sidecar — orchestrated by Docker Compose. The backend manages all GitHub API interactions, AI-powered issue generation, and the autonomous agent pipeline engine. This document describes how these pieces fit together.

## Overview

Solune is a full-stack web application with a React frontend, a FastAPI backend, and a Signal messaging sidecar. All three services are orchestrated with Docker Compose behind a shared bridge network.

```text
┌───────────────────────────┐     ┌──────────────────────────────────┐     ┌──────────────────┐
│        Frontend            │────▶│            Backend                │────▶│    GitHub API     │
│  React 19 + Vite 8          │◀────│            FastAPI                │◀────│  GraphQL + REST   │
│  TypeScript 5.9              │ WS  │                                  │     │                  │
│  TanStack Query v5          │     │  ┌──────────────────────────┐    │     │  ┌────────────┐  │
│  dnd-kit (drag-drop)        │     │  │ Workflow Orchestrator     │    │     │  │ Projects   │  │
│  ErrorBoundary              │     │  │ (4 sub-modules)          │    │     │  │ V2 API     │  │
└───────────────────────────┘     │  └──────────────────────────┘    │     │  └────────────┘  │
                                  │  ┌──────────────────────────┐    │     │  ┌────────────┐  │
                                  │  │ Copilot Polling Service   │    │     │  │ Copilot    │  │
                                  │  │ (7 sub-modules)          │    │     │  │ Assignment │  │
                                  │  └──────────────────────────┘    │     │  └────────────┘  │
                                  │  ┌──────────────────────────┐    │     └──────────────────┘
                                  │  │ GitHub Projects Service   │    │
                                  │  │ (2 sub-modules)          │    │     ┌──────────────────┐
                                  │  └──────────────────────────┘    │     │ signal-cli-rest- │
                                  │  ┌──────────────────────────┐    │ HTTP │ api (sidecar)    │
                                  │  │ Signal Bridge             │────│────▶│ Signal Relay     │
                                  │  │ + Delivery + WS Listener  │◀───│─WS──│                  │
                                  │  └──────────────────────────┘    │     └──────────────────┘
                                  │  ┌──────────────────────────┐    │
                                  │  │ AI Completion Providers   │    │
                                  │  │  ├ Copilot SDK (default)  │    │
                                  │  │  └ Azure OpenAI (optional)│    │
                                  │  └──────────────────────────┘    │
                                  │  ┌──────────────────────────┐    │
                                  │  │ SQLite (aiosqlite)        │    │
                                  │  │ WAL mode, auto-migrated   │    │
                                  │  │ data/settings.db          │    │
                                  │  └──────────────────────────┘    │
                                  │  ┌──────────────────────────┐    │
                                  │  │ FastAPI DI (dependencies) │    │
                                  │  │ app.state singletons      │    │
                                  │  └──────────────────────────┘    │
                                  └──────────────────────────────────┘
```

## Docker Compose Services

| Service | Container | Port | Purpose |
|---------|-----------|------|---------|
| `backend` | `solune-backend` | 8000 | FastAPI API server |
| `frontend` | `solune-frontend` | 5173 → 80 | nginx serving React SPA + reverse proxy to `/api/` |
| `signal-api` | `solune-signal-api` | 8080 (internal) | `bbernhard/signal-cli-rest-api` sidecar (json-rpc mode) |

Volumes: `solune-data` (SQLite DB), `signal-cli-config` (Signal protocol state).

## Frontend Architecture

The frontend is a single-page React application that provides the visual pipeline builder, Kanban board, chat interface, and settings UI. It communicates with the backend over REST and WebSocket connections, proxied through nginx.

- **Framework**: React 19 with TypeScript 5.9, built by Vite 8
- **State Management**: TanStack Query v5 for server state; local `useState` for UI state
- **Real-Time**: Native `WebSocket` connection for live board updates (with polling fallback)
- **Routing**: Hash-based view switching (`#board`, `#settings`, `#chat`)
- **Drag-and-Drop**: `@dnd-kit` for pipeline agent reordering within and across stages and execution groups
- **Styling**: Tailwind CSS 4 (CSS-first config) with dark/light/system theme support (`ThemeProvider`), celestial/cosmic CSS animation system (motion tokens, `@keyframes`, utility classes centralized in `index.css`), `prefers-reduced-motion` support
- **Error Handling**: Global `ErrorBoundary` (React class component + TanStack `QueryErrorResetBoundary`)

### Key Frontend Modules

| Directory | Contents |
|-----------|----------|
| `components/auth/` | `LoginButton` — GitHub OAuth login |
| `components/board/` | `ProjectBoard`, `BoardColumn`, `IssueCard`, `IssueDetailModal`, `ProjectIssueLaunchPanel`, agent config UI (`AgentPresetSelector`, `AgentConfigRow`, `AgentTile`, `AgentSaveBar`, `AddAgentPopover`) |
| `components/chat/` | `ChatInterface`, `ChatPopup`, `MessageBubble`, `TaskPreview`, `StatusChangePreview`, `IssueRecommendationPreview`, `CommandAutocomplete`, `SystemMessage`, `ChatToolbar`, `VoiceInputButton` |
| `components/settings/` | `AIPreferences`, `DisplayPreferences`, `WorkflowDefaults`, `NotificationPreferences`, `ProjectSettings`, `GlobalSettings`, `SignalConnection`, `McpSettings` |
| `components/common/` | `ErrorBoundary`, `CelestialCatalogHero` (reusable hero with celestial animations), `CelestialLoader` (orbital loading indicator), `ThemedAgentIcon`, `ProjectSelectionEmptyState`, `agentIcons` |
| `components/agents/` | `AgentsPanel`, `AgentCard`, `AgentAvatar`, `AgentChatFlow`, `AgentInlineEditor`, `AddAgentModal`, `AgentIconPickerModal`, `BulkModelUpdateDialog` |
| `components/pipeline/` | `PipelineBoard`, `PipelineFlowGraph`, `AgentNode`, `StageCard`, `ExecutionGroupCard`, `ModelSelector`, `PipelineModelDropdown`, `PipelineToolbar`, `SavedWorkflowsList`, `UnsavedChangesDialog` |
| `components/tools/` | `ToolsPanel`, `ToolSelectorModal`, `ToolCard`, `McpPresetsGallery`, `EditRepoMcpModal`, `UploadMcpModal`, `RepoConfigPanel`, `GitHubMcpConfigGenerator` |
| `hooks/` | `useAuth`, `useChat`, `useChatHistory`, `useProjects`, `useWorkflow`, `useRealTimeSync`, `useProjectBoard`, `useAppTheme`, `useAgentConfig`, `useAgents`, `useSettings`, `useSettingsForm`, `useBoardRefresh`, `useCommands`, `useCleanup`, `useChores`, `useMcpSettings`, `useMetadata`, `useSidebarState`, `useMediaQuery`, `usePipelineConfig`, `usePipelineBoardMutations`, `usePipelineModelOverride`, `usePipelineReducer`, `useTools`, `useNotifications`, `useVoiceInput` |
| `pages/` | `AgentsPage`, `AgentsPipelinePage`, `AppPage`, `ChoresPage`, `LoginPage`, `NotFoundPage`, `ProjectsPage`, `SettingsPage`, `ToolsPage` |
| `services/` | `api.ts` — centralized HTTP/WS client for all backend endpoints |

## Backend Architecture

The backend is the core of Solune — it handles authentication, GitHub API interactions, AI completion, pipeline orchestration, and database management. All endpoints are async, and background tasks run in managed task groups.

- **Framework**: FastAPI with async endpoints, Pydantic v2 models
- **Database**: SQLite via `aiosqlite` in WAL mode, auto-migrated at startup (SQL migration files `023` through `037`)
- **DI**: Singletons registered on `app.state` during lifespan; `dependencies.py` provides `Depends()` getters
- **Middleware**: `RequestIDMiddleware` for request tracing; CORS middleware; `CSPMiddleware` for Content Security Policy plus companion security headers (including HSTS); `CSRFMiddleware` for double-submit cookie CSRF protection; `RateLimitMiddleware` for request rate limiting
- **Async Task Safety**: `asyncio.TaskGroup` for background loops (automatic cancellation on shutdown); `TaskRegistry` singleton for fire-and-forget tasks (tracked, drained on shutdown)
- **Exceptions**: Custom `AppException` hierarchy → `AuthenticationError`, `AuthorizationError`, `NotFoundError`, `ValidationError`, `GitHubAPIError`, `RateLimitError`, `McpValidationError`, `McpLimitExceededError`, `DatabaseError`, `PersistenceError`

### Backend Module Layout

| Directory | Purpose |
|-----------|---------|
| `api/` | Route handlers: `auth`, `agents`, `board`, `chat`, `chores`, `cleanup`, `health`, `mcp`, `metadata`, `pipelines`, `projects`, `settings`, `signal`, `tasks`, `webhooks`, `workflow` |
| `models/` | Pydantic v2 models: `agent`, `agent_creator`, `agents`, `board`, `chat`, `chores`, `cleanup`, `mcp`, `pipeline`, `project`, `recommendation`, `settings`, `signal`, `task`, `user`, `workflow` |
| `services/` | Business logic (see below) |
| `services/github_projects/` | `GitHubProjectsService` + `graphql.py` + `GitHubClientFactory` — pooled `githubkit` SDK clients for GitHub API |
| `services/copilot_polling/` | Background polling loop: `state`, `helpers`, `polling_loop`, `agent_output`, `pipeline`, `recovery`, `completion` |
| `services/workflow_orchestrator/` | Pipeline orchestration: `models` (contexts/state), `config` (async load/persist), `transitions`, `orchestrator` |
| `services/chores/` | Chore templates, scheduler, counter, chat, template builder, service |
| `services/agents/` | Agent configuration CRUD service (SQLite + GitHub repo merge) + Agent MCP Sync (`agent_mcp_sync.py`) — keeps `mcp-servers` and `tools: ["*"]` in sync across all `.agent.md` files |
| `migrations/` | SQL migration files `023` through `037` |
| `prompts/` | AI prompt templates for issue and task generation |
| `middleware/` | `RequestIDMiddleware`, `CSPMiddleware` (Content Security Policy + HTTP security headers such as HSTS), `CSRFMiddleware` (double-submit cookie CSRF protection), `RateLimitMiddleware` (request rate limiting), `AdminGuardMiddleware` |
| `logging_utils.py` | `RequestIDFilter`, `SanitizingFormatter`, `StructuredJsonFormatter` for structured JSON logging |
| `config.py` | `pydantic-settings` configuration from `.env` |
| `constants.py` | Status names, agent mappings, labels, cache keys |
| `dependencies.py` | FastAPI DI helpers |
| `exceptions.py` | Custom exception classes (`AppException` hierarchy including `PersistenceError`) |
| `protocols.py` | `Protocol` types for service interfaces (`ModelProvider`, `CacheInvalidationPolicy`) |

### AI Completion Providers

The backend uses a pluggable `CompletionProvider` abstraction:

| Provider | Class | Default | Auth |
|----------|-------|---------|------|
| GitHub Copilot | `CopilotCompletionProvider` | Yes | User's GitHub OAuth token (per-request) |
| Azure OpenAI | `AzureOpenAICompletionProvider` | No | Static API key from env vars |

Set via `AI_PROVIDER` env var (`copilot` or `azure_openai`).

### Startup Lifecycle (`main.py`)

1. Install global asyncio exception handler for unhandled async errors
2. Initialize SQLite database + run pending migrations
3. Seed `global_settings` row
4. Load persisted pipeline state from SQLite into L1 caches
5. Register singleton services on `app.state`
6. Start Signal WebSocket listener for inbound messages
7. Auto-resume Copilot polling from the most recent session with a selected project
8. Run Agent MCP Sync in background via `TaskRegistry` (fire-and-forget)
9. Start background loops via `asyncio.TaskGroup` — session cleanup loop (exponential backoff on failures) + polling watchdog loop (auto-restart on crash)
10. On shutdown: drain `TaskRegistry` (30 s timeout) → stop Signal listener → stop polling → close database

### nginx Reverse Proxy

The frontend nginx config (`nginx.conf`):

- Proxies `/api/` to `backend:8000` with WebSocket upgrade support
- Serves static assets with 1-year cache (`/assets/`)
- SPA fallback: all non-file routes serve `index.html`
- Security headers: `X-Frame-Options`, `X-Content-Type-Options`, `X-XSS-Protection`
- Health endpoint: `/health` returns 200 OK

---

For the rationale behind key design decisions, see the [Architecture Decision Records](decisions/README.md).

## What's next?

- [Agent Pipeline](agent-pipeline.md) — How pipelines orchestrate agents through execution stages
- [Configuration](configuration.md) — Every environment variable and how to customize your deployment
- [Project Structure](project-structure.md) — The complete directory layout with file descriptions
