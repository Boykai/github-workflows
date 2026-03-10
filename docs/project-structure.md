# Project Structure

```text
github-workflows/
├── .devcontainer/                # GitHub Codespaces / Dev Container config
│   ├── devcontainer.json         #   Python 3.13, Node 22, Docker-in-Docker
│   ├── docker-compose.devcontainer.yml
│   ├── post-create.sh            #   Installs deps, creates venv, Playwright
│   └── post-start.sh             #   Prints Codespaces callback URL
├── .env.example                  # Environment template (documented)
├── .github/
│   ├── agents/                   # Spec Kit custom Copilot agent definitions
│   │   ├── speckit.specify.agent.md
│   │   ├── speckit.plan.agent.md
│   │   ├── speckit.tasks.agent.md
│   │   ├── speckit.implement.agent.md
│   │   ├── speckit.clarify.agent.md
│   │   ├── speckit.analyze.agent.md
│   │   ├── speckit.checklist.agent.md
│   │   ├── speckit.constitution.agent.md
│   │   ├── speckit.taskstoissues.agent.md
│   │   └── copilot-instructions.md
│   ├── prompts/                  # GitHub Copilot prompt files
│   └── workflows/                # GitHub Actions workflows
├── .pre-commit-config.yaml       # Pre-commit framework config
├── docker-compose.yml            # 3 services: backend, frontend, signal-api
├── README.md
├── docs/                         # Documentation (this directory)
│
├── backend/
│   ├── Dockerfile                # Python 3.13-slim, non-root user, health check
│   ├── pyproject.toml            # Dependencies + dev tools (ruff, pyright, pytest)
│   ├── src/
│   │   ├── main.py               # FastAPI app factory, lifespan, CORS, exception handlers
│   │   ├── config.py             # pydantic-settings from .env
│   │   ├── constants.py          # Status names, agent mappings, labels, cache keys
│   │   ├── dependencies.py       # FastAPI DI helpers (app.state singletons)
│   │   ├── exceptions.py         # AppException hierarchy
│   │   ├── utils.py              # BoundedSet, CIDict, utcnow, resolve_repository
│   │   ├── api/                  # Route handlers
│   │   │   ├── auth.py           #   OAuth flow, sessions, dev-login
│   │   │   ├── board.py          #   Project board (Kanban columns + items)
│   │   │   ├── chat.py           #   Chat messages, proposals, #agent command
│   │   │   ├── chores.py        #   Chore CRUD, triggering, chat, evaluation
│   │   │   ├── cleanup.py        #   Stale resource cleanup
│   │   │   ├── health.py         #   Health check endpoint
│   │   │   ├── mcp.py            #   MCP configuration endpoints
│   │   │   ├── projects.py       #   Project selection, tasks, WebSocket, SSE
│   │   │   ├── settings.py       #   User, global, project settings
│   │   │   ├── signal.py         #   Signal connection, preferences, banners
│   │   │   ├── tasks.py          #   Task CRUD
│   │   │   ├── agents.py         #   Agent CRUD and configuration
│   │   │   ├── metadata.py       #   Repository metadata (labels, branches, milestones)
│   │   │   ├── webhooks.py       #   GitHub webhook handler
│   │   │   └── workflow.py       #   Workflow config, pipeline, polling control
│   │   ├── middleware/
│   │   │   └── request_id.py     #   RequestIDMiddleware for tracing
│   │   ├── migrations/           # SQL schema migrations (001–020, auto-run)
│   │   ├── models/               # Pydantic v2 data models
│   │   │   ├── agent.py          #   AgentSource, AgentAssignment, AvailableAgent
│   │   │   ├── agent_creator.py  #   CreationStep, AgentPreview, AgentCreationState
│   │   │   ├── board.py          #   Board columns, items, custom fields
│   │   │   ├── chat.py           #   ChatMessage, SenderType, ActionType
│   │   │   ├── chores.py         #   Chore models
│   │   │   ├── cleanup.py        #   Cleanup models
│   │   │   ├── mcp.py            #   MCP configuration models
│   │   │   ├── project.py        #   GitHubProject, StatusColumn
│   │   │   ├── agents.py         #   AgentConfig list/CRUD models
│   │   │   ├── recommendation.py #   AITaskProposal, IssueRecommendation, labels
│   │   │   ├── settings.py       #   User preferences, global/project settings
│   │   │   ├── signal.py         #   Signal connection, message, banner models
│   │   │   ├── task.py           #   Task / project item
│   │   │   ├── user.py           #   UserSession
│   │   │   └── workflow.py       #   WorkflowConfiguration, WorkflowTransition
│   │   ├── prompts/              # AI prompt templates
│   │   │   ├── issue_generation.py  # System/user prompts for issue creation
│   │   │   └── task_generation.py   # Task generation prompts
│   │   └── services/             # Business logic layer
│   │       ├── github_projects/
│   │       │   ├── __init__.py    #   GitHubClientFactory (pooled githubkit SDK clients)
│   │       │   ├── service.py    #   GitHubProjectsService (REST + GraphQL via githubkit)
│   │       │   └── graphql.py    #   GraphQL queries and mutations
│   │       ├── copilot_polling/
│   │       │   ├── state.py      #   Module-level mutable state
│   │       │   ├── helpers.py    #   Sub-issue lookup, tracking helpers
│   │       │   ├── polling_loop.py  # Start/stop/tick scheduling
│   │       │   ├── agent_output.py  # Agent output extraction and posting
│   │       │   ├── pipeline.py   #   Pipeline advancement and transitions
│   │       │   ├── recovery.py   #   Stalled issue recovery, cooldowns
│   │       │   └── completion.py #   PR completion detection
│   │       ├── workflow_orchestrator/
│   │       │   ├── models.py     #   WorkflowContext, PipelineState, WorkflowState
│   │       │   ├── config.py     #   Async config load/persist/defaults/dedup
│   │       │   ├── transitions.py  # Status transitions, branch tracking
│   │       │   └── orchestrator.py  # WorkflowOrchestrator class
│   │       ├── chores/
│   │       │   ├── chat.py       #   Chore chat flow
│   │       │   ├── counter.py    #   Counter tracking
│   │       │   ├── scheduler.py  #   Schedule management
│   │       │   ├── service.py    #   ChoresService
│   │       │   └── template_builder.py  # Template generation
│   │       ├── agents/
│   │       │   └── service.py    #   Agent configuration service
│   │       ├── agent_creator.py  #   #agent command: guided agent creation flow
│   │       ├── agent_tracking.py #   Agent pipeline tracking (issue body markdown)
│   │       ├── ai_agent.py       #   AI issue generation (via CompletionProvider)
│   │       ├── cache.py          #   In-memory TTL cache
│   │       ├── cleanup_service.py  # Stale resource cleanup service
│   │       ├── completion_providers.py  # Pluggable LLM: Copilot SDK / Azure OpenAI
│   │       ├── database.py       #   aiosqlite connection, WAL mode, migrations
│   │       ├── encryption.py     #   Fernet encryption for tokens at rest
│   │       ├── github_auth.py    #   OAuth token exchange
│   │       ├── github_commit_workflow.py  # Git commit workflow helpers
│   │       ├── mcp_store.py      #   MCP configuration persistence
│   │       ├── metadata_service.py  # Repository metadata caching service
│   │       ├── model_fetcher.py  #   AI model metadata fetching
│   │       ├── session_store.py  #   Session CRUD (async SQLite)
│   │       ├── settings_store.py #   Settings persistence (async SQLite)
│   │       ├── signal_bridge.py  #   Signal HTTP client, DB helpers, WS listener
│   │       ├── signal_chat.py    #   Inbound Signal message processing
│   │       ├── signal_delivery.py  # Outbound Signal formatting & retry
│   │       └── websocket.py      #   WebSocket connection manager
│   └── tests/
│       ├── conftest.py           # Shared test fixtures
│       ├── helpers/              # Test helper utilities
│       ├── unit/                 # 47 unit test files
│       ├── integration/          # Integration tests
│       └── test_api_e2e.py       # API end-to-end tests
│
├── frontend/
│   ├── Dockerfile                # Multi-stage: Node 22 build → nginx:alpine
│   ├── nginx.conf                # SPA + /api/ reverse proxy + security headers
│   ├── package.json              # Dependencies + scripts
│   ├── vite.config.ts            # Vite configuration
│   ├── vitest.config.ts          # Vitest configuration
│   ├── playwright.config.ts      # Playwright E2E configuration
│   ├── tsconfig.json             # TypeScript config
│   ├── eslint.config.js          # ESLint flat config
│   ├── src/
│   │   ├── App.tsx               # Root component (auth, routing, providers)
│   │   ├── main.tsx              # React entry point
│   │   ├── constants.ts          # Named timing/polling/cache constants
│   │   ├── types/index.ts        # TypeScript type definitions
│   │   ├── components/
│   │   │   ├── ThemeProvider.tsx  # Dark/light/system theme + cosmic transition overlay
│   │   │   ├── auth/             # LoginButton
│   │   │   ├── board/            # ProjectBoard, BoardColumn, IssueCard,
│   │   │   │                     # IssueDetailModal, agent config UI, cleanup UI
│   │   │   ├── chat/             # ChatInterface, ChatPopup, MessageBubble,
│   │   │   │                     # TaskPreview, StatusChangePreview,
│   │   │   │                     # IssueRecommendationPreview, CommandAutocomplete
│   │   │   ├── common/           # ErrorBoundary, CelestialCatalogHero,
│   │   │   │                     # CelestialLoader, ThemedAgentIcon, agentIcons
│   │   │   ├── agents/           # AgentsPanel, AgentCard, AgentAvatar,
│   │   │   │                     # AgentChatFlow, AddAgentModal, AgentInlineEditor
│   │   │   ├── chores/           # ChoresPanel, AddChoreModal, ChoreCard,
│   │   │   │                     # ChoreScheduleConfig, ChoreChatFlow
│   │   │   ├── pipeline/         # PipelineBoard, PipelineFlowGraph, AgentNode,
│   │   │   │                     # StageCard, ModelSelector, PipelineToolbar
│   │   │   ├── tools/            # ToolsPanel, ToolSelectorModal, ToolCard,
│   │   │   │                     # McpPresetsGallery, EditRepoMcpModal
│   │   │   ├── settings/         # AI, Display, Workflow, Notification preferences,
│   │   │   │                     # ProjectSettings, GlobalSettings, SignalConnection,
│   │   │   │                     # McpSettings, AdvancedSettings
│   │   │   └── ui/               # Shared UI primitives (button, input, card, tooltip)
│   │   ├── hooks/                # React hooks (see Architecture doc)
│   │   ├── pages/                # AgentsPage, AgentsPipelinePage, AppPage,
│   │   │                         # ChoresPage, LoginPage, NotFoundPage,
│   │   │                         # ProjectsPage, SettingsPage, ToolsPage
│   │   ├── services/api.ts       # Centralized HTTP/WS client
│   │   └── utils/                # generateId, formatTime
│   └── e2e/                      # Playwright E2E test specs
│
├── scripts/
│   ├── pre-commit                # Git hook: ruff, pyright, eslint, tsc, vitest, build
│   └── setup-hooks.sh            # Install git hooks
│
└── specs/                        # Feature specifications (Spec Kit output)
```
