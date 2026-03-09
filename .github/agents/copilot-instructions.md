# GitHub Workflows Chat — Development Guidelines

Last updated: 2026-03-08

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
- **Dev tools:** `ruff>=0.15.0`, `pyright>=1.1.408`, `pytest>=9.0.0`, `pytest-asyncio>=1.3.0`, `pytest-cov>=7.0.0`

### Frontend

- **Node / build:** Node 22 for local dev and Docker; Vite 7.3 (`frontend/vite.config.ts` is the single source of truth)
- **Framework:** React 19.2, react-router-dom v7
- **Language:** TypeScript ~5.9 (strict mode, `@/` alias → `frontend/src`)
- **State / data fetching:** `@tanstack/react-query` 5.90
- **Styling:** Tailwind CSS 4.2 via `@tailwindcss/vite` (CSS-first v4 model; config lives in `frontend/src/index.css`)
- **UI primitives:** `@radix-ui/react-slot`, `@radix-ui/react-tooltip`, `class-variance-authority`, `clsx`, `tailwind-merge`, `lucide-react 0.577`, `@tailwindcss/typography`
- **Drag-and-drop:** `@dnd-kit/core` 6.3, `@dnd-kit/modifiers` 9.0, `@dnd-kit/sortable` 10.0, `@dnd-kit/utilities` 3.2
- **Markdown:** `react-markdown` 10.1, `remark-gfm` 4.0
- **Dev tools:** ESLint 9.39, Prettier 3.8, Vitest 4.0 (`happy-dom` environment), Playwright 1.58

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
- **Storage:** SQLite via `aiosqlite` in WAL mode. Migrations (`001`–`017`) run automatically on startup from `backend/src/migrations/`. Key tables: `user_sessions`, `project_settings`, `agent_configs`, `pipeline_configs`, `mcp_configurations`, `agent_tool_associations`, `chat_messages`, `chat_proposals`, `chat_recommendations`, `chores`, `blocking_queue`.
- **Tailwind v4:** CSS-first config lives entirely in `frontend/src/index.css`. `tailwind.config.js` and `postcss.config.js` are intentionally absent — do not recreate them.
- **Repository resolution:** Use the shared `resolve_repository()` helper (`src/utils.py`) everywhere. Do not introduce ad-hoc owner/repo fallback logic.
- **AI providers:** `completion_providers.py` abstracts GitHub Copilot SDK (default, user OAuth token) and Azure OpenAI (static keys, optional). Selected via `AI_PROVIDER` env var.
- **Agent pipelines:** Configured in SQLite (`pipeline_configs`) and executed by `services/copilot_polling/` + `services/workflow_orchestrator/`. Copilot polling auto-restarts on container restart using the most-recent persisted session (or `GITHUB_WEBHOOK_TOKEN` fallback).
- **Blocking queue:** `services/blocking_queue.py` implements serial issue activation with per-repo `asyncio.Lock` to prevent double-activation race conditions.
- **Chores:** `services/chores/` manages scheduled recurring tasks (scheduler, counter, chat, template builder).
- **Signal messaging:** `signal_bridge.py` / `signal_chat.py` / `signal_delivery.py` integrate with the Signal sidecar for inbound/outbound AI chat over Signal.
- **MCP tools:** `services/mcp_store.py` + `api/mcp.py` manage MCP server configurations and agent tool associations.
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
    migrations/       SQL schema migrations (001–017, run on startup)
    models/           Pydantic request/response models
    prompts/          AI prompt templates (issue_generation, task_generation)
    services/         Business logic
      agents/         Agent config CRUD
      chores/         Scheduled chores (scheduler, counter, chat, template)
      copilot_polling/ Copilot PR polling loop and agent output parsing
      github_projects/ GitHub Projects v2 GraphQL + REST
      housekeeping/   Session/DB cleanup
      pipelines/      Pipeline config service
      tools/          MCP tool service
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
                       ProjectsPage, SettingsPage, ToolsPage)
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

## Validation Expectations

- **Backend changes:** validate with `ruff check`, `ruff format --check`, `pyright`, and relevant `pytest` coverage.
- **Frontend changes:** validate with `npm run lint`, `npm run type-check`, `npm run test`, and `npm run build`.
- **Pre-commit hook** (`scripts/pre-commit`): runs ruff format (auto-fix) + ruff lint (auto-fix) + pyright on staged Python files; ESLint (auto-fix) on staged frontend files.
- **Pre-push hook** (`scripts/setup-hooks.sh`): full backend + frontend test gates.
- **CI** (`.github/workflows/ci.yml`): backend uses Python 3.12; frontend uses Node 20. Three jobs: `backend`, `frontend`, `docs` (markdownlint + link-check).
- A known flaky failure can occur in `frontend/src/hooks/useAuth.test.tsx` under full parallel runs — confirm isolated behavior before changing unrelated code.

## Active Technologies
- TypeScript ~5.9 (frontend), Python 3.11+ (backend) + React 19.2, react-router-dom 7.13, @tanstack/react-query 5.90, Tailwind CSS v4, FastAPI, aiosqlite, Pydantic (031-profile-page)
- SQLite via aiosqlite — new `user_profiles` table for display name, bio, custom avatar path (031-profile-page)

## Recent Changes
- 031-profile-page: Added TypeScript ~5.9 (frontend), Python 3.11+ (backend) + React 19.2, react-router-dom 7.13, @tanstack/react-query 5.90, Tailwind CSS v4, FastAPI, aiosqlite, Pydantic
