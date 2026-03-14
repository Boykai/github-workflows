# Solune — Development Guidelines

Last updated: 2026-03-11

> **Important:** Always use search tools (e.g., Context7 MCP, Microsoft Docs MCP, or web search) to look up the most up-to-date documentation when working with any and all libraries, frameworks, and APIs. Never rely solely on training data — verify current syntax, options, and best practices from official sources before writing or modifying code.

## Current Stack

### Backend

- **Runtime floor:** Python `>=3.12` (`backend/pyproject.toml`); primary dev/runtime target is Python 3.13 (`ruff` target `py313`, `pyright` `pythonVersion = "3.13"`, Docker image `python:3.13-slim`)
- **Framework:** FastAPI `>=0.135.0`, Uvicorn `>=0.41.0`
- **GitHub integration:** `githubkit>=0.14.6`, `httpx>=0.28.0`
- **Validation / config:** `pydantic>=2.12.0`, `pydantic-settings>=2.13.0`
- **Storage:** SQLite via `aiosqlite>=0.22.0` (WAL mode, single persistent connection, migrations run on startup)
- **AI providers:** `github-copilot-sdk>=0.1.30` (default), `openai>=2.26.0`, `azure-ai-inference>=1.0.0b9` (optional fallbacks)
- **Security / crypto:** `cryptography>=44.0.0` (Fernet token-at-rest encryption)
- **Rate limiting:** `slowapi>=0.1.9`
- **Utilities:** `tenacity>=9.1.0`, `websockets>=16.0`, `python-multipart>=0.0.22`, `pyyaml>=6.0.3`
- **Code graph analysis:** `codegraphcontext>=0.2.9` (MCP server + CLI)
- **Dev tools:** `ruff>=0.15.0`, `pyright>=1.1.408`, `pytest>=9.0.0`, `pytest-asyncio>=1.3.0`, `pytest-cov>=7.0.0`

### Frontend

- **Node / build:** Node 22 for local dev and Docker; Vite 7.3 (`frontend/vite.config.ts` is the single source of truth)
- **Framework:** React 19.2, react-router-dom v7
- **Language:** TypeScript ~5.9 (strict mode, `@/` alias → `frontend/src`)
- **State / data fetching:** `@tanstack/react-query` 5.90
- **Styling:** Tailwind CSS 4.2 via `@tailwindcss/vite` (CSS-first v4 model; config lives in `frontend/src/index.css`)
- **UI primitives:** `@radix-ui/react-slot`, `@radix-ui/react-tooltip`, `class-variance-authority`, `clsx`, `tailwind-merge`, `lucide-react 0.577`, `@tailwindcss/typography`
- **Drag-and-drop:** `@dnd-kit/core` 6.3, `@dnd-kit/modifiers` 9.0, `@dnd-kit/sortable` 10.0, `@dnd-kit/utilities` 3.2
- **Forms:** `react-hook-form` 7.71, `@hookform/resolvers` 5.2, `zod` 4.3
- **Markdown:** `react-markdown` 10.1, `remark-gfm` 4.0
- **Dev tools:** ESLint 9.39, Prettier 3.8, Vitest 4.0 (`happy-dom` environment), Playwright 1.58
- **Testing:** `@testing-library/react` 16.3, `@testing-library/user-event` 14.6, `jest-axe` 10.0

### Infrastructure

`docker-compose.yml` defines three services:

| Service | Container | Host port | Container port | Notes |
|---|---|---|---|---|
| `backend` | `ghchat-backend` | 8000 | 8000 | FastAPI / Uvicorn |
| `frontend` | `ghchat-frontend` | 5173 | 8080 | nginx static server |
| `signal-api` | `ghchat-signal-api` | internal only | 8080 | `bbernhard/signal-cli-rest-api` |

- Backend health: `GET http://localhost:8000/api/v1/health`
- Frontend health: `GET http://localhost:8080/health` (inside container); `http://localhost:5173` from host
- Data volume: `ghchat-data` mounted at `/var/lib/ghchat/data` (SQLite database)
- Signal config volume: `signal-cli-config` at `/home/.local/share/signal-cli`
- All three services share the `ghchat-network` bridge network

## Architecture Notes

- **Auth:** GitHub OAuth with secure HTTP-only session cookies. No JWT / `python-jose` layer.
- **Real-time:** Native WebSocket (`ConnectionManager` in `services/websocket.py`), with SSE fallback in the projects API. Do not reintroduce `socket.io-client`.
- **Storage:** SQLite via `aiosqlite` in WAL mode. Migrations (`001`–`020`) run automatically on startup from `backend/src/migrations/`. Key tables: `user_sessions`, `project_settings`, `agent_configs`, `pipeline_configs`, `mcp_configurations`, `agent_tool_associations`, `chat_messages`, `chat_proposals`, `chat_recommendations`, `chores`, `blocking_queue`.
- **Tailwind v4:** CSS-first config lives entirely in `frontend/src/index.css`. `tailwind.config.js` and `postcss.config.js` are intentionally absent — do not recreate them.
- **Repository resolution:** Use the shared `resolve_repository()` helper (`src/utils.py`) everywhere. Do not introduce ad-hoc owner/repo fallback logic.
- **AI providers:** `completion_providers.py` abstracts GitHub Copilot SDK (default, user OAuth token) and Azure OpenAI (static keys, optional). Selected via `AI_PROVIDER` env var.
- **Agent pipelines:** Configured in SQLite (`pipeline_configs`) and executed by `services/copilot_polling/` + `services/workflow_orchestrator/`. Copilot polling auto-restarts on container restart using the most-recent persisted session (or `GITHUB_WEBHOOK_TOKEN` fallback).
- **Blocking queue:** `services/blocking_queue.py` implements serial issue activation with per-repo `asyncio.Lock` to prevent double-activation race conditions.
- **Chores:** `services/chores/` manages scheduled recurring tasks (scheduler, counter, chat, template builder).
- **Signal messaging:** `signal_bridge.py` / `signal_chat.py` / `signal_delivery.py` integrate with the Signal sidecar for inbound/outbound AI chat over Signal.
- **MCP tools:** `services/mcp_store.py` + `api/mcp.py` manage MCP server configurations and agent tool associations. `services/tools/presets.py` provides a static catalog of built-in MCP presets (GitHub, Azure, Sentry, Cloudflare, Azure DevOps, Context7, Code Graph Context) served via `GET /api/v1/tools/presets`. `services/tools/service.py` handles per-project tool CRUD and repo MCP config sync.
- **MCP presets flow:** User selects preset on Tools page → draft form → saves as user tool in DB → agent dispatch calls `_resolve_agent_tool_selection()` → `generate_config_files()` writes `mcp-servers:` into `.github/agents/{slug}.agent.md` YAML frontmatter → GitHub reads agent file on assignment.
- **Remote MCP config:** `.github/agents/mcp.json` defines MCP servers available to remote GitHub Custom Agents (e.g., Context7 HTTP endpoint). This file is co-located with agent definitions and read by GitHub.com during coding agent sessions.
- **Encryption:** Fernet (`cryptography` package) used for token-at-rest encryption when `ENCRYPTION_KEY` is set.
- **`AsyncGenerator` typing:** Always include both type parameters for Python 3.12 compatibility: `AsyncGenerator[str, None]`.

## Repo Layout

```text
backend/
  src/
    api/              FastAPI route handlers
                      (agents, auth, board, chat, chores, cleanup, health,
                       mcp, metadata, pipelines, projects, settings, signal,
                       tasks, tools, webhooks, workflow)
    middleware/       Request middleware (request_id context var)
    migrations/       SQL schema migrations (001–020, run on startup)
    models/           Pydantic request/response models
    prompts/          AI prompt templates (issue_generation, task_generation)
    services/         Business logic
      agents/         Agent config CRUD
      chores/         Scheduled chores (scheduler, counter, chat, template)
      copilot_polling/ Copilot PR polling loop and agent output parsing
      tools/          MCP tool service (presets catalog, per-project CRUD, repo sync)
      github_projects/ GitHub Projects v2 GraphQL + REST
      housekeeping/   Session/DB cleanup
      pipelines/      Pipeline config service
      workflow_orchestrator/ Issue workflow state machine
  tests/
    unit/
    integration/
    helpers/

frontend/
  src/
    components/       UI components by domain
                      (agents, auth, board, chat, chores, common,
                       pipeline, settings, tools, ui)
    hooks/            React hooks (useAuth, useChat, usePipelineConfig,
                      useBlockingQueue, useProjects, useChores, etc.)
    layout/           Shell components (AppLayout, AuthGate)
    lib/              Shared utilities (cn, etc.)
    pages/            Route-level pages
                      (AppPage, AgentsPage, AgentsPipelinePage, ChoresPage,
                       LoginPage, NotFoundPage, ProjectsPage, SettingsPage, ToolsPage)
    services/         HTTP client (api.ts)
    types/            Shared TypeScript types
    utils/            Pure utility helpers
  e2e/                Playwright end-to-end tests
```

## Commands

```bash
# Backend
cd backend && source .venv/bin/activate
ruff check src/ tests/          # lint
ruff format src/ tests/         # format (or --check)
pyright src/                    # type-check
pytest tests/unit/ -q           # fast unit tests
pytest tests/ --cov=src         # full suite with coverage

# Frontend
cd frontend
npm run lint                    # ESLint
npm run type-check              # tsc --noEmit
npm run test                    # Vitest (run once)
npm run build                   # production build
npx playwright test             # E2E
```

## Conventions

- Python: Ruff-driven, 100-character line limit, `known-first-party = ["src"]`.
- TypeScript: strict mode, `@/` path alias maps to `frontend/src`.
- Commits: conventional-commit style — `feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`.
- Prefer focused, minimal fixes over broad refactors unless the task explicitly calls for architectural work.
- Do **not** recreate deleted compatibility files: `frontend/vite.config.js`, `frontend/tailwind.config.js`, `frontend/postcss.config.js`.
- Agent `.agent.md` files live in `.github/agents/`; corresponding `.prompt.md` shortcuts live in `.github/prompts/`.
- `.github/agents/mcp.json` declares MCP servers for remote GitHub Custom Agents (currently Context7). Do not confuse with `.vscode/mcp.json` (local IDE MCP servers).

## CHANGELOG

**All agents must update `CHANGELOG.md`** (repo root) when implementing changes that affect user-facing behavior, APIs, configuration, or infrastructure.

### When to update
- Adding new features, pages, components, or API endpoints
- Fixing bugs or correcting behavior
- Removing or deprecating existing functionality
- Changing configuration, environment variables, or infrastructure
- Security fixes or dependency updates with user impact

### When NOT to update
- Internal refactors with no user-visible effect
- Test-only changes
- Documentation-only changes (unless they reflect a product change)
- Spec/plan/task file creation (spec work is not a shipped change)

### Format
Follow [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) conventions. Add entries under the `[Unreleased]` section using these categories:
- **Added** — new features or capabilities
- **Changed** — modifications to existing behavior
- **Deprecated** — features marked for future removal
- **Removed** — features that have been deleted
- **Fixed** — bug fixes
- **Security** — vulnerability or security-related changes

Each entry should be a single concise line describing the change from a user's perspective. Example:
```markdown
### Added
- Pipeline Analytics dashboard on the Agents Pipelines page showing agent frequency and model distribution
```

## Validation Expectations

- **Backend changes:** validate with `ruff check`, `ruff format --check`, `pyright`, and relevant `pytest` coverage.
- **Frontend changes:** validate with `npm run lint`, `npm run type-check`, `npm run test`, and `npm run build`.
- **Pre-commit hook** (`scripts/pre-commit`): runs ruff format (auto-fix) + ruff lint (auto-fix) + pyright on staged Python files; ESLint (auto-fix) on staged frontend files.
- **Pre-push hook** (`scripts/setup-hooks.sh`): full backend + frontend test gates.
- **CI** (`.github/workflows/ci.yml`): backend uses Python 3.12; frontend uses Node 20. Three jobs: `backend`, `frontend`, `docs` (markdownlint + link-check).
- A known flaky failure can occur in `frontend/src/hooks/useAuth.test.tsx` under full parallel runs — confirm isolated behavior before changing unrelated code.

## Frontend Pattern Notes
- Celestial theme animations and gradients are implemented via shared utility classes in `frontend/src/index.css` (for example, orbiting particles, glow effects, and parallax layers). Reuse these utilities instead of defining component-local `@keyframes` or duplicating animation logic.

## Custom Agents

All agents live in `.github/agents/`. The repository includes both **Spec Kit pipeline agents** and **utility agents**:

### Spec Kit Pipeline Agents
| Agent | Purpose |
|-------|---------|
| `speckit.specify` | Feature specification from issue description |
| `speckit.plan` | Implementation plan with research and data model |
| `speckit.tasks` | Actionable task list from spec + plan |
| `speckit.implement` | Code implementation from tasks |
| `speckit.clarify` | Identify underspecified areas in a spec |
| `speckit.analyze` | Cross-artifact consistency analysis |
| `speckit.checklist` | Custom checklist generation |
| `speckit.constitution` | Project constitution management |
| `speckit.taskstoissues` | Convert tasks to GitHub issues |

### Utility Agents
| Agent | Purpose |
|-------|---------|
| `archivist` | Updates documentation and README to match code changes |
| `designer` | Creates or refines design assets scoped to changes |
| `judge` | Triages PR review comments and applies justified changes |
| `linter` | Runs linting, tests, CI steps, and resolves errors |
| `quality-assurance` | Scoped quality improvements and defect fixes |
| `tester` | Adds tests for changed behavior and improves testability |

### MCP Configuration
- `.github/agents/mcp.json` — Declares MCP servers available to remote GitHub Custom Agents (currently Context7 for documentation lookup).

## MCP Presets

The Tools page exposes a **Preset Library** of built-in MCP server configurations. Presets are defined statically in `backend/src/services/tools/presets.py` and served via `GET /api/v1/tools/presets`.

| Preset | Type | Category | Description |
|--------|------|----------|-------------|
| GitHub MCP Server | HTTP | GitHub | Read-only GitHub MCP server |
| GitHub MCP Server (Full Access) | HTTP | GitHub | Full-access GitHub MCP server |
| Azure MCP | Local | Cloud | Azure-aware coding workflows |
| Sentry MCP | Local | Monitoring | Issue details and summaries |
| Cloudflare MCP | SSE | Cloud | Cloudflare docs and platform access |
| Azure DevOps MCP | Local | Cloud | Azure DevOps work items |
| Context7 | HTTP | Documentation | Up-to-date library docs and code examples |
| Code Graph Context | Local | Code Analysis | Code indexing, call chains, dead code detection |

## MCP Tool Usage Requirements

- **Always use Context7 MCP for library documentation.** Before writing or modifying code that uses any library, framework, or API, look up the current documentation via Context7. Never rely solely on training data for syntax, options, or best practices.
- **Always use Code Graph Context MCP when exploring the codebase.** Before making changes, use Code Graph Context to understand call chains, code relationships, and dependency graphs. This prevents unintended side effects and ensures changes are consistent with the existing architecture.

## Active Technologies
- Python 3.12+ backend with FastAPI ≥0.135 and websockets 16 (001-performance-review)
- SQLite via aiosqlite (session/settings); in-memory TTL cache (`backend/src/services/cache.py`) (001-performance-review)
- Python ≥3.12 (backend), TypeScript (frontend) + FastAPI ≥0.135.0, Pydantic ≥2.12.0, githubkit ≥0.14.6, httpx ≥0.28.0 (backend); React, TanStack Query (frontend) (034-label-pipeline-state)
- aiosqlite (pipeline configs, agent tracking); GitHub Issues API (labels as state markers) (034-label-pipeline-state)
- Python 3.13 (backend), TypeScript / ES2022 (frontend) + FastAPI 0.135+, Pydantic 2.12+, aiosqlite, githubkit, React 19, TanStack Query v5, Vite 7.3, Tailwind v4, Zod v4 (035-best-practices-overhaul)
- SQLite via aiosqlite (async), with write-through in-memory `BoundedDict` cache (035-best-practices-overhaul)
- Python 3.12+ (backend), TypeScript 5.9 (frontend) + FastAPI, aiosqlite, httpx, PyYAML (backend); React 19.2, TanStack React Query 5.90 (frontend) (036-agent-mcp-sync)
- aiosqlite (`mcp_configurations` table) + GitHub repository files (agent `.agent.md` files, `mcp.json`) (036-agent-mcp-sync)
- TypeScript 5.x with React 19.2, TanStack React Query 5.90, Tailwind CSS v4 (via `@tailwindcss/vite`), Radix UI (Slot, Tooltip), Lucide React icons, class-variance-authority, tailwind-merge, react-router-dom 7.13, react-markdown 10.1, @dnd-kit (drag-and-drop), Vite 7.3 (frontend: 001-performance-review, 034-projects-page-audit)
- Python ≥3.12 (backend), TypeScript (frontend) + FastAPI ≥0.135.0, Pydantic ≥2.12.0, githubkit ≥0.14.6, httpx ≥0.28.0 (backend); React, TanStack Query (frontend) (034-label-pipeline-state)
- aiosqlite (pipeline configs, agent tracking); GitHub Issues API (labels as state markers) (034-label-pipeline-state)
- Python ≥3.12 (backend), TypeScript (frontend) + FastAPI ≥0.135.0, Pydantic ≥2.12.0, githubkit ≥0.14.6, httpx ≥0.28.0 (backend); React 19, TanStack Query, Vitest (frontend) (035-remove-blocking-feature)
- aiosqlite (blocking_queue table, blocking columns on pipeline_configs/chores/project_settings) (035-remove-blocking-feature)
- TypeScript ~5.9.0 (frontend), Python ≥3.12 (backend) + React 19.2, @dnd-kit/core 6.3 + @dnd-kit/sortable 10.0, Tailwind CSS 4.2, Radix UI, TanStack React Query 5.90, FastAPI ≥0.135, Pydantic v2, aiosqlite (037-pipeline-builder-ux)
- SQLite via aiosqlite with JSON-serialised pipeline stages (existing pattern) (037-pipeline-builder-ux)
- Python 3.12+ (backend), TypeScript 5.9 / React 19.2 (frontend) + FastAPI, aiosqlite, githubkit, httpx, websockets (backend); TanStack React Query v5.90, @dnd-kit v6.3, Vite 7.3 (frontend) (037-performance-review)
- SQLite via aiosqlite (session/settings); InMemoryCache for board/sub-issue/project data (037-performance-review)
- Python 3.13 (backend, floor ≥3.12), TypeScript 5.9 (frontend) + FastAPI, aiosqlite, httpx, slowapi (backend); React 19.2, TanStack React Query 5.90 (frontend); nginx (reverse proxy) (037-security-review)
- aiosqlite (SQLite with application-level encryption via `encryption.py`) (037-security-review)
- Python ≥3.12 (target 3.13) for backend; TypeScript 5.x for frontend + FastAPI, aiosqlite, httpx, PyYAML (backend); React 19.2, TanStack React Query 5.90, Vitest 4.0 (frontend) (037-bug-basher)
- aiosqlite (SQLite) with custom migration runner; GitHub API for repository file operations (037-bug-basher)
- TypeScript 5.x, React 19.2.0, Node.js + Tailwind CSS v4.2.0 (with `@tailwindcss/vite`), Radix UI (tooltip, slot), Class Variance Authority (CVA), clsx, tailwind-merge, lucide-react icons (037-theme-contrast-audit)
- N/A (frontend-only audit; no persistence changes) (037-theme-contrast-audit)
- Python 3.13 (backend, floor ≥3.12), TypeScript 5.9 (frontend) + FastAPI, aiosqlite, httpx, Pydantic (backend); React 19.2, TanStack React Query 5.90 (frontend) (037-chat-attachment-github-issue)
- aiosqlite (chat_proposals, chat_recommendations tables) + GitHub Issues (final attachment destination) (037-chat-attachment-github-issue)
- Python 3.12+ (backend), TypeScript 5.9 / React 19.2 (frontend) + FastAPI, aiosqlite, githubkit, httpx, websockets (backend); TanStack React Query v5.90, @dnd-kit v6.3, Vite 7.3, Vitest 4.0 (frontend) (039-dead-code-cleanup)
- SQLite via aiosqlite (session/settings); InMemoryCache for board/sub-issue/project data; in-memory dicts for chat messages/proposals/recommendations (MVP, migration 012 tables ready) (039-dead-code-cleanup)
- Python ≥3.12 (backend only — no frontend changes required) + FastAPI ≥0.135, Pydantic v2, aiosqlite, asyncio (039-group-pipeline-execution)
- SQLite via aiosqlite with JSON-serialized pipeline stages (existing pattern); `WorkflowConfiguration` persisted per-project; `PipelineState` is in-memory only (reconstructed from issue tracking table) (039-group-pipeline-execution)
- Python 3.12+ (backend), TypeScript 5.9 (frontend) + FastAPI 0.135+, React 19.2, Vite 7.3, TanStack Query v5, Pydantic v2, aiosqlite (041-solune-rebrand-app-builder)
- SQLite with aiosqlite (async, WAL mode) — existing `settings.db` at `/var/lib/ghchat/data/settings.db` (will become `/var/lib/solune/data/settings.db`) (041-solune-rebrand-app-builder)

## Recent Changes
- 001-performance-review: Added Python 3.12+ (backend), TypeScript 5.9 / React 19 (frontend) + FastAPI ≥0.135, TanStack React Query 5.90, @dnd-kit, Vite 7.3, websockets 16
