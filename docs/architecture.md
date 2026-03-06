# Architecture

## Overview

Agent Projects is a full-stack web application with a React frontend, a FastAPI backend, and a Signal messaging sidecar. All three services are orchestrated with Docker Compose behind a shared bridge network.

```
┌───────────────────────────┐     ┌──────────────────────────────────┐     ┌──────────────────┐
│        Frontend            │────▶│            Backend                │────▶│    GitHub API     │
│  React 18 + Vite 5         │◀────│            FastAPI                │◀────│  GraphQL + REST   │
│  TypeScript ~5.4            │ WS  │                                  │     │                  │
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
| `backend` | `ghchat-backend` | 8000 | FastAPI API server |
| `frontend` | `ghchat-frontend` | 5173 → 80 | nginx serving React SPA + reverse proxy to `/api/` |
| `signal-api` | `ghchat-signal-api` | 8080 (internal) | `bbernhard/signal-cli-rest-api` sidecar (json-rpc mode) |

Volumes: `ghchat-data` (SQLite DB), `signal-cli-config` (Signal protocol state).

## Frontend Architecture

- **Framework**: React 18 with TypeScript ~5.4, built by Vite 5
- **State Management**: TanStack Query v5 for server state; local `useState` for UI state
- **Real-Time**: `socket.io-client` WebSocket connection for live board updates
- **Routing**: Hash-based view switching (`#board`, `#settings`, `#chat`)
- **Drag-and-Drop**: `@dnd-kit` for agent configuration reordering
- **Styling**: Tailwind CSS with dark/light theme support (`ThemeProvider`)
- **Error Handling**: Global `ErrorBoundary` (React class component + TanStack `QueryErrorResetBoundary`)

### Key Frontend Modules

| Directory | Contents |
|-----------|----------|
| `components/auth/` | `LoginButton` — GitHub OAuth login |
| `components/board/` | `ProjectBoard`, `BoardColumn`, `IssueCard`, `IssueDetailModal`, agent config UI (`AgentPresetSelector`, `AgentConfigRow`, `AgentTile`, `AgentSaveBar`, `AddAgentPopover`) |
| `components/chat/` | `ChatInterface`, `ChatPopup`, `MessageBubble`, `TaskPreview`, `StatusChangePreview`, `IssueRecommendationPreview`, `CommandAutocomplete`, `SystemMessage` |
| `components/settings/` | `AIPreferences`, `DisplayPreferences`, `WorkflowDefaults`, `NotificationPreferences`, `ProjectSettings`, `GlobalSettings`, `SignalConnection`, `McpSettings` |
| `components/common/` | `ErrorBoundary` |
| `hooks/` | `useAuth`, `useChat`, `useProjects`, `useWorkflow`, `useRealTimeSync`, `useProjectBoard`, `useAppTheme`, `useAgentConfig`, `useSettings`, `useSettingsForm`, `useBoardRefresh`, `useCommands`, `useCleanup`, `useChores`, `useMcpSettings` |
| `pages/` | `ProjectBoardPage`, `SettingsPage` |
| `services/` | `api.ts` — centralized HTTP/WS client for all backend endpoints |

## Backend Architecture

- **Framework**: FastAPI with async endpoints, Pydantic v2 models
- **Database**: SQLite via `aiosqlite` in WAL mode, auto-migrated at startup (10 numbered SQL migrations)
- **DI**: Singletons registered on `app.state` during lifespan; `dependencies.py` provides `Depends()` getters
- **Middleware**: `RequestIDMiddleware` for request tracing; CORS middleware
- **Exceptions**: Custom `AppException` hierarchy → `AuthenticationError`, `AuthorizationError`, `NotFoundError`, `ValidationError`, `GitHubAPIError`, `RateLimitError`, `McpValidationError`, `McpLimitExceededError`

### Backend Module Layout

| Directory | Purpose |
|-----------|---------|
| `api/` | Route handlers: `auth`, `board`, `chat`, `chores`, `cleanup`, `health`, `mcp`, `projects`, `settings`, `signal`, `tasks`, `webhooks`, `workflow` |
| `models/` | Pydantic v2 models: `agent`, `agent_creator`, `agents`, `board`, `chat`, `chores`, `cleanup`, `mcp`, `project`, `recommendation`, `settings`, `signal`, `task`, `user`, `workflow` |
| `services/` | Business logic (see below) |
| `services/github_projects/` | `GitHubProjectsService` + `graphql.py` + `GitHubClientFactory` — pooled `githubkit` SDK clients for GitHub API |
| `services/copilot_polling/` | Background polling loop: `state`, `helpers`, `polling_loop`, `agent_output`, `pipeline`, `recovery`, `completion` |
| `services/workflow_orchestrator/` | Pipeline orchestration: `models` (contexts/state), `config` (async load/persist), `transitions`, `orchestrator` |
| `services/chores/` | Chore templates, scheduler, counter, chat, template builder, service |
| `migrations/` | SQL migration files `001` through `012` |
| `prompts/` | AI prompt templates for issue and task generation |
| `middleware/` | `RequestIDMiddleware` |
| `config.py` | `pydantic-settings` configuration from `.env` |
| `constants.py` | Status names, agent mappings, labels, cache keys |
| `dependencies.py` | FastAPI DI helpers |
| `exceptions.py` | Custom exception classes |

### AI Completion Providers

The backend uses a pluggable `CompletionProvider` abstraction:

| Provider | Class | Default | Auth |
|----------|-------|---------|------|
| GitHub Copilot | `CopilotCompletionProvider` | Yes | User's GitHub OAuth token (per-request) |
| Azure OpenAI | `AzureOpenAICompletionProvider` | No | Static API key from env vars |

Set via `AI_PROVIDER` env var (`copilot` or `azure_openai`).

### Startup Lifecycle (`main.py`)

1. Initialize SQLite database + run pending migrations
2. Seed `global_settings` row
3. Initialize chores service seed templates
4. Register singleton services on `app.state`
5. Start periodic session cleanup loop (exponential backoff on failures)
6. Start Signal WebSocket listener for inbound messages
7. Auto-resume Copilot polling from the most recent session with a selected project
8. On shutdown: stop Signal listener → cancel cleanup task → stop polling → close database

### nginx Reverse Proxy

The frontend nginx config (`nginx.conf`):
- Proxies `/api/` to `backend:8000` with WebSocket upgrade support
- Serves static assets with 1-year cache (`/assets/`)
- SPA fallback: all non-file routes serve `index.html`
- Security headers: `X-Frame-Options`, `X-Content-Type-Options`, `X-XSS-Protection`
- Health endpoint: `/health` returns 200 OK
