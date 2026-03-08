# GitHub Workflows Chat — Development Guidelines

Last updated: 2026-03-04

> **Important:** Always use search tools (e.g., Context7 MCP, Microsoft Docs MCP, or web search) to look up the most up-to-date documentation when working with any and all libraries, frameworks, and APIs. Never rely solely on training data — verify current syntax, options, and best practices from official sources before writing or modifying code.

# GitHub Workflows Chat — Development Guidelines

Last updated: 2026-03-06

> Always verify third-party library, framework, and API usage against current official documentation before making code changes. Use live docs or official references rather than relying on older syntax or assumptions.

## Current Stack

### Backend
- Runtime floor: Python `>=3.12` in `backend/pyproject.toml`
- Primary dev/runtime target: Python 3.13 (`ruff` target `py313`, `pyright` target `3.13`, Docker image `python:3.13-slim`)
- Framework: FastAPI `>=0.135.0`, Uvicorn `>=0.41.0`
- GitHub integration: `githubkit>=0.14.6`
- Validation/config: `pydantic>=2.12.0`, `pydantic-settings>=2.13.0`
- Storage: SQLite via `aiosqlite>=0.22.0`
- AI providers: `github-copilot-sdk>=0.1.30`, `openai>=2.26.0`, `azure-ai-inference>=1.0.0b9`
- Security/session crypto: `cryptography>=44.0.0`
- Messaging/retries: `tenacity>=9.1.0`, `websockets>=16.0`, `python-multipart>=0.0.22`, `pyyaml>=6.0.3`
- Lint/type/test: `ruff>=0.15.0`, `pyright>=1.1.408`, `pytest>=9.0.0`, `pytest-asyncio>=1.3.0`, `pytest-cov>=7.0.0`

### Frontend
- Runtime/build target: Node 22 for Docker and local bare-metal guidance
- Framework: React 19.2, React DOM 19.2
- Build tooling: Vite 7.3 with a single source of truth in `frontend/vite.config.ts`
- Language: TypeScript 5.9
- State/data fetching: `@tanstack/react-query` 5.90
- Styling: Tailwind CSS 4.2 via `@tailwindcss/vite`
- UI utilities: Radix Slot, class-variance-authority, clsx, tailwind-merge, lucide-react
- Drag and drop: `@dnd-kit/core` 6.3, `@dnd-kit/modifiers` 9.0, `@dnd-kit/sortable` 10.0, `@dnd-kit/utilities` 3.2
- Lint/test: ESLint 9.39, Prettier 3.8, Vitest 4.0, Playwright 1.58, `happy-dom` is the active Vitest environment

### Infrastructure
- `docker-compose.yml` defines 3 services:
  - `backend` on port 8000
  - `frontend` on port 5173, served by nginx on container port 80
  - `signal-api` (`bbernhard/signal-cli-rest-api`) on internal port 8080
- Backend health check: `http://localhost:8000/api/v1/health`
- Frontend health check: `http://localhost/health` inside the container

## Architecture Notes

- Auth is GitHub OAuth based and uses secure HTTP-only session cookies. There is no `python-jose`/JWT layer in the backend anymore.
- Real-time updates use native WebSocket support, with Server-Sent Events fallback in the projects API. Do not reintroduce `socket.io-client` patterns.
- Settings and session persistence are SQLite-backed. Migrations live under `backend/src/migrations/` and run on startup.
- Tailwind is already migrated to the v4 CSS-first model. Keep theme/config in `frontend/src/index.css`; `tailwind.config.js` and `postcss.config.js` are intentionally removed.
- GitHub project and agent pipeline logic lives primarily under `backend/src/services/github_projects/`, `backend/src/services/copilot_polling/`, and `backend/src/services/workflow_orchestrator/`.
- Repository resolution should use the shared `resolve_repository()` flow rather than reintroducing ad hoc owner/repo fallback logic.
- When using `AsyncGenerator` from `collections.abc`, include both type parameters for Python 3.12 compatibility, e.g. `AsyncGenerator[str, None]`.

## Repo Layout

```text
backend/
  src/
    api/                  FastAPI route handlers
    middleware/           request/response middleware
    migrations/           SQL schema migrations
    models/               Pydantic models
    prompts/              AI prompt templates
    services/             application/business logic
      chores/
      copilot_polling/
      github_projects/
      workflow_orchestrator/
  tests/
    unit/
    integration/
    helpers/

frontend/
  src/
    components/
    hooks/
    lib/
    pages/
    services/
    types/
    utils/
  e2e/
```

## Commands

```bash
# Backend
cd backend && source .venv/bin/activate
ruff check src/ tests/
ruff format src/ tests/
pyright src/
pytest tests/unit/ -q
pytest tests/ --cov=src

# Frontend
cd frontend
npm run lint
npm run type-check
npm run test
npm run build
npx playwright test
```

## Conventions

- Python formatting/linting is Ruff-driven with 100-character lines and `known-first-party = ["src"]`.
- TypeScript uses strict typing and the `@/` alias mapped to `frontend/src`.
- Keep commits in conventional-commit style: `feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`.
- Prefer focused fixes over broad refactors unless the task explicitly calls for architectural work.
- Do not reintroduce deleted compatibility files like `frontend/vite.config.js`, `frontend/tailwind.config.js`, or `frontend/postcss.config.js`.

## Validation Expectations

- Backend changes should normally be validated with Ruff, Pyright, and relevant pytest coverage.
- Frontend changes should normally be validated with ESLint, `tsc --noEmit`, Vitest, and Vite build.
- Pre-commit runs backend formatting/lint/type checks.
- Pre-push runs the full backend/frontend test gates; a known flaky failure can occur in `frontend/src/hooks/useAuth.test.tsx` under full parallel runs, so confirm isolated behavior before changing unrelated code.
- Python 3.12 (pyproject.toml targets ≥3.11, pyright configured for 3.12) + TypeScript ~5.8 + FastAPI ≥0.109.0, githubkit ≥0.14.0, httpx ≥0.26.0, pydantic ≥2.5.0, React 18.3, @tanstack/react-query 5.17, Vite 5.4 (023-codebase-review-refactor)

## Active Technologies
- TypeScript 5.9, React 19.2, Vite 7.3 + react-router-dom v7 (new), TanStack Query 5.90, Tailwind CSS v4 (via @tailwindcss/vite), @dnd-kit, lucide-react 0.577, Radix UI (025-solune-ui-redesign)
- localStorage (sidebar state, chat history, notification read timestamp, pre-auth redirect URL) (025-solune-ui-redesign)
- TypeScript ~5.9, React 19.2, Vite 7.3 + react-router-dom v7, TanStack Query 5.90, Tailwind CSS v4, lucide-react 0.577 (026-recent-interactions-filter)
- localStorage (sidebar state), in-memory (board data via TanStack Query cache) (026-recent-interactions-filter)
- TypeScript ~5.9, React 19.2, Vite 7.3 + TanStack Query 5.90, Tailwind CSS v4, lucide-react 0.577 (026-chat-help-optimistic-render)
- N/A (local React state only — no persistence for pending messages) (026-chat-help-optimistic-render)
- TypeScript ~5.9 (frontend), Python 3.13 (backend) + React 19.2, react-router-dom v7, TanStack Query v5.90, Tailwind CSS v4, lucide-react 0.577 (frontend); FastAPI 0.135, aiosqlite 0.22, Pydantic v2.12 (backend) (027-mcp-tools-page)
- SQLite with WAL mode (aiosqlite) — extending existing `mcp_configurations` table + new `agent_tool_associations` junction table (027-mcp-tools-page)
- Python 3.13 (backend), TypeScript 5.9 (frontend), Node 22 (build) + FastAPI, githubkit, pydantic 2.x, aiosqlite, React 19.2, TanStack Query, Vite 7.3 (027-performance-review)
- SQLite with WAL mode (aiosqlite) — sessions, settings; in-memory cache (backend/src/services/cache.py) (027-performance-review)
- TypeScript ~5.9 (frontend), Python 3.13 (backend) + React 19.2, TanStack Query v5.90, Tailwind CSS v4, lucide-react 0.577 (frontend); FastAPI >=0.135.0, aiosqlite >=0.22.0 (backend) (028-mcp-tools-fixes)
- N/A — no schema changes; existing SQLite tables unchanged (028-mcp-tools-fixes)
- TypeScript ~5.9 (frontend), Python 3.13 (backend) + React 19.2, TanStack Query v5.90, Tailwind CSS v4, lucide-react 0.577 (frontend); FastAPI 0.135, aiosqlite 0.22, Pydantic v2.12, python-multipart 0.0.22 (backend) (028-chat-ux-enhancements)
- SQLite with WAL mode (aiosqlite) — existing `chat_messages`, `chat_proposals`, `chat_recommendations` tables; localStorage for toggle preference persistence (028-chat-ux-enhancements)
- TypeScript ~5.9 (frontend), Python 3.13 (backend) + React 19.2, react-router-dom v7, TanStack Query v5.90, @dnd-kit (core + sortable), Tailwind CSS v4, lucide-react 0.577 (frontend); FastAPI 0.135, aiosqlite 0.22, Pydantic v2.12 (backend) (028-pipeline-mcp-config)
- SQLite with WAL mode (aiosqlite) — extending `pipeline_configs` table with preset flags and `PipelineAgentNode` with `tool_ids`; adding `assigned_pipeline_id` column to `project_settings` (028-pipeline-mcp-config)
- TypeScript ~5.9 (frontend), Python 3.13 (backend) + React 19.2, react-router-dom v7, TanStack Query v5.90, Tailwind CSS v4, lucide-react 0.577 (frontend); FastAPI 0.135, aiosqlite 0.22, Pydantic v2.12, githubkit (backend) (029-chores-page-enhancements)
- SQLite with WAL mode (aiosqlite) — extending `chores` table with `execution_count`, `ai_enhance_enabled`, `agent_pipeline_id`; leveraging existing `pipeline_configs` and `project_settings` tables (029-chores-page-enhancements)
- TypeScript ~5.9 (frontend), Python 3.13 (backend) + React 19.2, TanStack Query v5.90, Tailwind CSS v4, lucide-react 0.577 (frontend); FastAPI 0.135, aiosqlite 0.22, Pydantic v2.12 (backend) (029-agents-page-ux)
- SQLite with WAL mode (aiosqlite) — existing `agent_configs` table; Git-backed `.github/agents/*.agent.md` files on repo default branch (029-agents-page-ux)
- TypeScript ~5.9 (frontend), Python 3.13 (backend) + React 19.2, react-router-dom v7, TanStack Query v5.90, @dnd-kit (core@6.3 + sortable@10.0), Tailwind CSS v4, lucide-react 0.577 (frontend); FastAPI 0.135, aiosqlite 0.22, Pydantic v2.12 (backend) (029-pipeline-ux-fixes)
- SQLite with WAL mode (aiosqlite) — no schema changes needed (029-pipeline-ux-fixes)
- Python 3.13 (type-check target, backend runtime requires 3.12+), TypeScript 5.9, React 19.2, Node.js 20 + FastAPI, TanStack Query, @dnd-kit/core, Tailwind CSS v4, Vite 7.3 (029-board-hierarchy-filters)
- GitHub API (GraphQL + REST) with in-memory caching (backend), localStorage (frontend persistence) (029-board-hierarchy-filters)
- Python 3.13 (backend), TypeScript/Node.js 22 (frontend) + FastAPI (backend API), React (frontend UI), Pydantic (models) (029-fix-ai-enhance-disabled)
- In-memory dictionaries (`_proposals`, `_recommendations`) — lost on restart (029-fix-ai-enhance-disabled)
- Python 3.13 (backend) + FastAPI 0.135, aiosqlite 0.22, Pydantic v2.12 (backend) (030-pipeline-model-display)
- SQLite with WAL mode (aiosqlite) — existing schema, no changes needed (030-pipeline-model-display)

## Recent Changes
- 025-solune-ui-redesign: Added TypeScript 5.9, React 19.2, Vite 7.3 + react-router-dom v7 (new), TanStack Query 5.90, Tailwind CSS v4 (via @tailwindcss/vite), @dnd-kit, lucide-react 0.577, Radix UI
