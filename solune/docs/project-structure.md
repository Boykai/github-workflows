# Project Structure

Understanding the directory layout helps you navigate the codebase quickly, find the right file to edit, and understand how the pieces fit together. This document maps every directory and file with a brief description of its purpose.

```text
solune/
├── .devcontainer/                # GitHub Codespaces / Dev Container config
│   ├── devcontainer.json         #   Python 3.13, Node 25, Docker-in-Docker
│   ├── docker-compose.devcontainer.yml
│   ├── post-create.sh            #   Installs deps, creates venv, Playwright
│   └── post-start.sh             #   Prints Codespaces callback URL
├── .env.example                  # Environment template (documented)
├── .github/
│   ├── agents/                   # Custom Copilot agent definitions + MCP config
│   │   ├── archivist.agent.md
│   │   ├── designer.agent.md
│   │   ├── judge.agent.md
│   │   ├── linter.agent.md
│   │   ├── quality-assurance.agent.md
│   │   ├── tester.agent.md
│   │   ├── speckit.analyze.agent.md
│   │   ├── speckit.checklist.agent.md
│   │   ├── speckit.clarify.agent.md
│   │   ├── speckit.constitution.agent.md
│   │   ├── speckit.implement.agent.md
│   │   ├── speckit.plan.agent.md
│   │   ├── speckit.specify.agent.md
│   │   ├── speckit.tasks.agent.md
│   │   ├── speckit.taskstoissues.agent.md
│   │   ├── mcp.json              #   Built-in MCP server definitions (Context7, CodeGraphContext)
│   │   └── copilot-instructions.md
│   ├── prompts/                  # GitHub Copilot prompt files
│   └── workflows/                # GitHub Actions workflows
├── .pre-commit-config.yaml       # Pre-commit framework config
├── docker-compose.yml            # 3 services: backend, frontend, signal-api
├── README.md
├── docs/                         # Documentation (this directory)
│
├── backend/
│   ├── Dockerfile                # Python 3.14-slim, non-root user, health check
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
│   │   │   ├── pipelines.py      #   Pipeline CRUD + launch from imported issue
│   │   │   ├── projects.py       #   Project selection, tasks, WebSocket, SSE
│   │   │   ├── settings.py       #   User, global, project settings
│   │   │   ├── signal.py         #   Signal connection, preferences, banners
│   │   │   ├── tasks.py          #   Task CRUD
│   │   │   ├── agents.py         #   Agent CRUD and configuration
│   │   │   ├── metadata.py       #   Repository metadata (labels, branches, milestones)
│   │   │   ├── tools.py          #   MCP tool CRUD and configuration
│   │   │   ├── webhooks.py       #   GitHub webhook handler
│   │   │   └── workflow.py       #   Workflow config, pipeline, polling control
│   │   ├── middleware/
│   │   │   ├── admin_guard.py    #   AdminGuardMiddleware for @admin/@adminlock file protection
│   │   │   ├── csp.py            #   CSPMiddleware — Content Security Policy + HTTP security headers
│   │   │   ├── csrf.py           #   CSRFMiddleware — double-submit cookie CSRF protection
│   │   │   ├── rate_limit.py     #   RateLimitMiddleware — per-user request rate limiting
│   │   │   └── request_id.py     #   RequestIDMiddleware for request tracing
│   │   ├── migrations/           # SQL schema migrations (16 SQL files, 023–037, auto-run)
│   │   ├── models/               # Pydantic v2 data models
│   │   │   ├── agent.py          #   AgentSource, AgentAssignment, AvailableAgent
│   │   │   ├── agent_creator.py  #   CreationStep, AgentPreview, AgentCreationState
│   │   │   ├── board.py          #   Board columns, items, custom fields
│   │   │   ├── chat.py           #   ChatMessage, SenderType, ActionType
│   │   │   ├── chores.py         #   Chore models
│   │   │   ├── cleanup.py        #   Cleanup models
│   │   │   ├── mcp.py            #   MCP configuration models
│   │   │   ├── pipeline.py       #   PipelineConfig, ExecutionGroup, PipelineIssueLaunchRequest, assignments
│   │   │   ├── project.py        #   GitHubProject, StatusColumn
│   │   │   ├── agents.py         #   AgentConfig list/CRUD models
│   │   │   ├── recommendation.py #   AITaskProposal, IssueRecommendation, labels
│   │   │   ├── settings.py       #   User preferences, global/project settings
│   │   │   ├── signal.py         #   Signal connection, message, banner models
│   │   │   ├── task.py           #   Task / project item
│   │   │   ├── tools.py          #   MCP tool models
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
│   │       │   ├── service.py    #   Agent configuration CRUD (SQLite + GitHub repo merge)
│   │       │   └── agent_mcp_sync.py  # MCP sync: enforces tools: ["*"] + mcp-servers on all agent files
│   │       ├── pipelines/
│   │       │   └── service.py    #   PipelineService CRUD and normalization
│   │       ├── tools/
│   │       │   ├── presets.py    #   Built-in MCP tool presets
│   │       │   └── service.py    #   ToolsService CRUD
│   │       ├── agent_creator.py  #   #agent command: guided agent creation flow
│   │       ├── agent_tracking.py #   Agent pipeline tracking (issue body markdown)
│   │       ├── ai_agent.py       #   AI issue generation (via CompletionProvider)
│   │       ├── cache.py          #   In-memory TTL cache
│   │       ├── chat_store.py     #   Chat message persistence (async SQLite)
│   │       ├── cleanup_service.py  # Stale resource cleanup service
│   │       ├── completion_providers.py  # Pluggable LLM: Copilot SDK / Azure OpenAI
│   │       ├── database.py       #   aiosqlite connection, WAL mode, migrations
│   │       ├── encryption.py     #   Fernet encryption for tokens at rest
│   │       ├── github_auth.py    #   OAuth token exchange
│   │       ├── github_commit_workflow.py  # Git commit workflow helpers
│   │       ├── mcp_store.py      #   MCP configuration persistence
│   │       ├── metadata_service.py  # Repository metadata caching service
│   │       ├── model_fetcher.py  #   AI model metadata fetching
│   │       ├── pipeline_state_store.py  # Pipeline execution state persistence
│   │       ├── session_store.py  #   Session CRUD (async SQLite)
│   │       ├── settings_store.py #   Settings persistence (async SQLite)
│   │       ├── signal_bridge.py  #   Signal HTTP client, DB helpers, WS listener
│   │       ├── signal_chat.py    #   Inbound Signal message processing
│   │       ├── signal_delivery.py  # Outbound Signal formatting & retry
│   │       └── websocket.py      #   WebSocket connection manager
│   └── tests/
│       ├── conftest.py           # Shared test fixtures
│       ├── helpers/              # Test helper utilities
│       ├── unit/                 # 59 unit test files
│       ├── integration/          # Integration tests
│       └── test_api_e2e.py       # API end-to-end tests
│
├── frontend/
│   ├── Dockerfile                # Multi-stage: Node 25 build → nginx:1.29-alpine
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
│   │   ├── context/               # React context providers
│   │   │   └── RateLimitContext.tsx  # Rate limit status context
│   │   ├── data/                  # Static data and presets
│   │   │   └── preset-pipelines.ts  # Built-in pipeline preset definitions
│   │   ├── components/
│   │   │   ├── ThemeProvider.tsx  # Dark/light/system theme + cosmic transition overlay
│   │   │   ├── auth/             # LoginButton
│   │   │   ├── board/            # ProjectBoard, BoardColumn, IssueCard,
│   │   │   │                     # IssueDetailModal, ProjectIssueLaunchPanel,
│   │   │   │                     # agent config UI, cleanup UI
│   │   │   ├── chat/             # ChatInterface, ChatPopup, MessageBubble,
│   │   │   │                     # TaskPreview, StatusChangePreview,
│   │   │   │                     # IssueRecommendationPreview, CommandAutocomplete,
│   │   │   │                     # ChatToolbar, VoiceInputButton
│   │   │   ├── common/           # ErrorBoundary, CelestialCatalogHero,
│   │   │   │                     # CelestialLoader, ThemedAgentIcon, agentIcons
│   │   │   ├── agents/           # AgentsPanel, AgentCard, AgentAvatar,
│   │   │   │                     # AgentChatFlow, AddAgentModal, AgentInlineEditor
│   │   │   ├── chores/           # ChoresPanel, ChoresToolbar, ChoresGrid,
│   │   │   │                     # ChoresSaveAllBar, ChoresSpotlight,
│   │   │   │                     # AddChoreModal, ChoreCard,
│   │   │   │                     # ChoreScheduleConfig, ChoreChatFlow,
│   │   │   │                     # ChoreInlineEditor, ConfirmChoreModal,
│   │   │   │                     # FeaturedRitualsPanel, PipelineSelector
│   │   │   ├── pipeline/         # PipelineBoard, PipelineFlowGraph, AgentNode,
│   │   │   │                     # StageCard, ExecutionGroupCard, ModelSelector,
│   │   │   │                     # PipelineToolbar
│   │   │   ├── tools/            # ToolsPanel, ToolSelectorModal, ToolCard,
│   │   │   │                     # McpPresetsGallery, EditRepoMcpModal,
│   │   │   │                     # UploadMcpModal, RepoConfigPanel,
│   │   │   │                     # GitHubMcpConfigGenerator
│   │   │   ├── settings/         # AI, Display, Workflow, Notification preferences,
│   │   │   │                     # ProjectSettings, GlobalSettings, SignalConnection,
│   │   │   │                     # McpSettings, AdvancedSettings
│   │   │   └── ui/               # Shared UI primitives (button, input, card, tooltip)
│   │   ├── hooks/                # React hooks (see Architecture doc)
│   │   ├── lib/                 # Shared utilities and helpers
│   │   │   ├── utils.ts         #   cn() class-name helper
│   │   │   ├── buildGitHubMcpConfig.ts  # GitHub.com MCP config generator
│   │   │   ├── pipelineMigration.ts  # Legacy-to-group pipeline format migration
│   │   │   └── commands/        #   Chat command registry + handlers
│   │   ├── pages/                # ActivityPage, AgentsPage, AgentsPipelinePage,
│   │   │                         # AppPage, AppsPage, ChoresPage, HelpPage,
│   │   │                         # LoginPage, NotFoundPage, ProjectsPage,
│   │   │                         # SettingsPage, ToolsPage
│   │   ├── layout/               # App shell layout components
│   │   │                         # AppLayout, AuthGate, TopBar, Sidebar,
│   │   │                         # Breadcrumb, ProjectSelector, NotificationBell,
│   │   │                         # RateLimitBar
│   │   ├── services/api.ts       # Centralized HTTP/WS client
│   │   ├── test/                  # Shared test utilities, factories, and setup
│   │   └── utils/                # generateId, formatTime
│   └── e2e/                      # Playwright E2E test specs
│
├── scripts/
│   ├── pre-commit                # Git hook: ruff, pyright, eslint, tsc, vitest, build
│   └── setup-hooks.sh            # Install git hooks
│
└── specs/                        # Feature specifications (Spec Kit output)
```

---

## What's Next?

- [Explore the architecture](architecture.md) — how the services connect
- [Set up your environment](setup.md) — get running locally or in Codespaces
- [Create custom agents](custom-agents-best-practices.md) — build your own AI agents
