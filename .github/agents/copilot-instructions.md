# Solune — Development Guidelines

Last updated: 2026-03-18

> Prefer official documentation sources and repo-discovery tools when working with frameworks, libraries, or external APIs. Treat tool availability as situational rather than mandatory.

## Current Stack

### Backend

- **Runtime floor:** Python `>=3.12` (`solune/backend/pyproject.toml`); primary dev/runtime target is Python 3.13 (`ruff` target `py313`, `pyright` `pythonVersion = "3.13"`); Docker image is `python:3.14-slim`; CI uses Python 3.12
- **Framework:** FastAPI `>=0.135.0`, Uvicorn `>=0.42.0`
- **GitHub integration:** `githubkit>=0.14.6`, `httpx>=0.28.0`
- **Validation / config:** `pydantic>=2.12.0`, `pydantic-settings>=2.13.0`
- **Storage:** SQLite via `aiosqlite>=0.22.0` (WAL mode, single persistent connection, migrations run on startup)
- **AI providers:** `github-copilot-sdk>=0.1.30` (default), `openai>=2.26.0`, `azure-ai-inference>=1.0.0b9` (optional fallbacks)
- **Security / crypto:** `cryptography>=46.0.5` (Fernet token-at-rest encryption)
- **Rate limiting:** `slowapi>=0.1.9`
- **Utilities:** `tenacity>=9.1.0`, `websockets>=16.0`, `python-multipart>=0.0.22`, `pyyaml>=6.0.3`
- **Code graph analysis:** `codegraphcontext>=0.2.9` (MCP server + CLI)
- **Dev tools:** `ruff>=0.15.0`, `pyright>=1.1.408`, `pytest>=9.0.0`, `pytest-asyncio>=1.3.0`, `pytest-cov>=7.0.0`

### Frontend

- **Node / build:** Node 25 for Docker; CI currently uses Node 20. Vite 8 config lives in `solune/frontend/vite.config.ts`.
- **Framework:** React 19.2, react-router-dom v7
- **Language:** TypeScript ~5.9 (strict mode, `@/` alias → `frontend/src`)
- **State / data fetching:** `@tanstack/react-query` 5.91
- **Styling:** Tailwind CSS 4.2 via `@tailwindcss/vite` (CSS-first v4 model; config lives in `frontend/src/index.css`)
- **UI primitives:** `@radix-ui/react-slot`, `@radix-ui/react-tooltip`, `class-variance-authority`, `clsx`, `tailwind-merge`, `lucide-react 0.577`, `@tailwindcss/typography`
- **Drag-and-drop:** `@dnd-kit/core` 6.3, `@dnd-kit/modifiers` 9.0, `@dnd-kit/sortable` 10.0, `@dnd-kit/utilities` 3.2
- **Forms:** `react-hook-form` 7.71, `@hookform/resolvers` 5.2, `zod` 4.3
- **Markdown:** `react-markdown` 10.1, `remark-gfm` 4.0
- **Dev tools:** ESLint 10.0, Prettier 3.8, Vitest 4.0 (`happy-dom` environment), Playwright 1.58
- **Linting:** `eslint-plugin-react-hooks` 7.0, `eslint-plugin-security` 4.0, `eslint-plugin-jsx-a11y` 6.10, `typescript-eslint` 8.56
- **Testing:** `@testing-library/react` 16.3, `@testing-library/user-event` 14.6, `jest-axe` 10.0, `@fast-check/vitest` 0.3

### Infrastructure

`docker-compose.yml` defines three services:

| Service | Container | Host port | Container port | Notes |
|---|---|---|---|---|
| `backend` | `solune-backend` | 8000 | 8000 | FastAPI / Uvicorn |
| `frontend` | `solune-frontend` | 5173 | 8080 | nginx static server |
| `signal-api` | `solune-signal-api` | internal only | 8080 | `bbernhard/signal-cli-rest-api` |

- Backend health: `GET http://localhost:8000/api/v1/health`
- Frontend health: `GET http://localhost:8080/health` (inside container); `http://localhost:5173` from host
- Data volume: `solune-data` mounted at `/var/lib/solune/data` (SQLite database)
- Signal config volume: `signal-cli-config` at `/home/.local/share/signal-cli`
- All three services share the `solune-network` bridge network

## Architecture Notes

- **Auth:** GitHub OAuth with secure HTTP-only session cookies. No JWT / `python-jose` layer.
- **Real-time:** Native WebSocket (`ConnectionManager` in `solune/backend/src/services/websocket.py`) with SSE fallback in the projects API.
- **Storage:** SQLite via `aiosqlite` in WAL mode. Migrations (`001`–`032`, with the consolidated schema at `023`) run automatically on startup from `solune/backend/src/migrations/`.
- **Tailwind v4:** CSS-first config lives in `solune/frontend/src/index.css`. Do not add `tailwind.config.js` or `postcss.config.js` unless the build model changes.
- **Repository resolution:** Use the shared `resolve_repository()` helper in `solune/backend/src/utils.py`. Avoid ad-hoc owner/repo fallback logic.
- **AI providers:** `completion_providers.py` abstracts GitHub Copilot SDK (default, user OAuth token) and Azure OpenAI (static keys, optional). Selected via `AI_PROVIDER` env var.
- **Agent pipelines:** Configured in SQLite (`pipeline_configs`) and executed by `solune/backend/src/services/copilot_polling/` + `solune/backend/src/services/workflow_orchestrator/`.
- **Pipeline state:** `solune/backend/src/services/pipeline_state_store.py` persists pipeline execution state across restarts.
- **Chores:** `solune/backend/src/services/chores/` manages scheduled recurring tasks.
- **Signal messaging:** `solune/backend/src/services/signal_bridge.py`, `signal_chat.py`, and `signal_delivery.py` integrate with the Signal sidecar.
- **MCP tools:** `solune/backend/src/services/mcp_store.py` + `api/mcp.py` manage MCP server configurations and agent tool associations. `solune/backend/src/services/tools/presets.py` defines the preset catalog; `solune/backend/src/services/tools/service.py` handles per-project CRUD and repo sync.
- **MCP presets flow:** User selects preset on Tools page → draft form → saves as user tool in DB → agent dispatch calls `_resolve_agent_tool_selection()` → `generate_config_files()` writes `mcp-servers:` into `.github/agents/{slug}.agent.md` YAML frontmatter → GitHub reads agent file on assignment.
- **Remote MCP config:** `.github/agents/mcp.json` defines MCP servers available to remote GitHub Custom Agents (e.g., Context7 HTTP endpoint, Azure MCP, Bicep MCP). This file is co-located with agent definitions and read by GitHub.com during coding agent sessions.
- **Encryption:** Fernet (`cryptography` package) used for token-at-rest encryption when `ENCRYPTION_KEY` is set.
- **`AsyncGenerator` typing:** Always include both type parameters for Python 3.12 compatibility: `AsyncGenerator[str, None]`.

## Repo Layout

```text
solune/
  backend/
    src/
    api/              FastAPI route handlers
                      (agents, apps, auth, board, chat, chores, cleanup, health,
                       mcp, metadata, onboarding, pipelines, projects, settings,
                       signal, tasks, tools, webhook_models, webhooks, workflow)
    middleware/       Request middleware (request_id context var)
    migrations/       SQL schema migrations (001–032, run on startup)
    models/           Pydantic request/response models
    prompts/          AI prompt templates (issue_generation, task_generation, transcript_analysis)
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
      components/     UI components by domain
      hooks/          React hooks
      layout/         Shell components
      lib/            Shared utilities
      pages/          Route-level pages
      services/       HTTP client (`api.ts`)
      types/          Shared TypeScript types
      utils/          Pure utility helpers
    e2e/              Playwright end-to-end tests
```

## Commands

```bash
# Backend
cd solune/backend && source .venv/bin/activate
ruff check src/ tests/          # lint
ruff format src/ tests/         # format (or --check)
pyright src/                    # type-check
pytest tests/unit/ -q           # fast unit tests
pytest tests/ --cov=src         # full suite with coverage

# Frontend
cd solune/frontend
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
- Tailwind v4 uses the CSS-first setup in `solune/frontend/src/index.css`; do not add `tailwind.config.js` or `postcss.config.js` unless the build model changes.
- Agent `.agent.md` files live in `.github/agents/`; corresponding `.prompt.md` shortcuts live in `.github/prompts/`.
- `.github/agents/mcp.json` declares MCP servers for remote GitHub Custom Agents (currently Context7, Azure MCP, CodeGraphContext, and Bicep MCP). Do not confuse with `.vscode/mcp.json` (local IDE MCP servers).

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
- **CI** (`.github/workflows/ci.yml`): backend uses Python 3.12; frontend uses Node 20. Docker images use Python 3.14 and Node 25. Keep local-vs-CI runtime differences in mind when debugging build or lint mismatches.
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
| `architect` | Generates Azure IaC (Bicep), `azd` scaffolds, architecture diagrams, and deploy buttons. Always runs for new apps. |
| `archivist` | Updates documentation and README to match code changes |
| `designer` | Creates or refines design assets scoped to changes |
| `judge` | Triages PR review comments and applies justified changes |
| `linter` | Runs linting, tests, CI steps, and resolves errors |
| `quality-assurance` | Scoped quality improvements and defect fixes |
| `tester` | Adds tests for changed behavior and improves testability |

### MCP Configuration
- `.github/agents/mcp.json` — Declares MCP servers available to remote GitHub Custom Agents (Context7 for documentation lookup, Azure MCP for resource schema lookups and Well-Architected Framework guidance, Bicep MCP for Bicep best practices, resource type schemas, and Azure Verified Modules metadata, and CodeGraphContext for codebase analysis).

### Agent Degradation Rules

When tools, context, or commands are unavailable, agents should degrade gracefully rather than fail silently or hallucinate:

- **MCP server fails to start**: Proceed without MCP-dependent context. Use file reads and search as fallback. Note the unavailability in output.
- **PR diff or branch info unavailable**: Fall back to local mode. Use `git diff` or `git log` to reconstruct the change set. If that also fails, ask the user to specify the scope.
- **Terminal commands fail repeatedly** (lint, test, build): Report the exact error output. Attempt the most common fix (missing dependencies → install, wrong directory → cd to correct path). After 2 failed retries, report the failure and continue with other phases rather than blocking entirely.
- **GitHub API unavailable**: If the agent cannot fetch PR metadata, review comments, or repo contents, switch to local file analysis and note the limitation.

### Agent Input Convention

All agent `.agent.md` files include a `$ARGUMENTS` block in their markdown body:

````markdown
## User Input

```text
$ARGUMENTS
```
````

`$ARGUMENTS` is replaced at invocation time with the user's input message. Agents must check this block before proceeding — it may scope the work to specific files, PRs, features, or constraints. New agents should include this block following the same pattern.

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

- Prefer Context7 when you need up-to-date library documentation and examples.
- Consider Code Graph Context for relationship-heavy codebase exploration when simple file/search reads are not enough.

## Active Technologies
- Python 3.13 (backend runtime target, 3.12 CI, 3.14 Docker), TypeScript ~5.9 (frontend) + FastAPI >=0.135, React 19.2, Vite 8, TanStack Query 5.91, Tailwind CSS 4.2, @dnd-kit (drag-and-drop), Pydantic 2.12, aiosqlite, cryptography 46, githubkit >=0.14.6, Radix UI
- SQLite via aiosqlite (persistent module-level connection, `init_database()` / `get_db()`), SQL-based migrations (001–032) in `backend/src/migrations/`
- ESLint 10, eslint-plugin-react-hooks 7, eslint-plugin-security 4, Vitest 4.0, Playwright 1.58
- Docker images: python:3.14-slim (backend), node:25-alpine + nginx:1.29-alpine (frontend)
- TypeScript ~5.9.0, React 19.2.0 + TanStack React Query ^5.91.0, React Router DOM ^7.13.1, React Hook Form ^7.71.2, Radix UI (primitives), Tailwind CSS ^4.2.0, Zod ^4.3.6, Vite ^8.0.0 (052-ui-audit)
- N/A (frontend-only; backend uses SQLite via aiosqlite — not modified by this feature) (052-ui-audit)
- Python 3.12, TypeScript (ES2022) + FastAPI 0.135+, Pydantic 2.12+, aiosqlite, githubkit, React 18, TanStack Query, Vite (049-fix-repo-type-routing)
- SQLite (WAL mode, aiosqlite) — `apps` table with `repo_type`, `external_repo_url`, `github_project_id`, `github_project_url` columns (049-fix-repo-type-routing)
- Python 3.12+ (backend), TypeScript 5.x (frontend) + FastAPI 0.135+, React 18+, Pydantic 2.12+, Vitest, Playwright (050-fix-bugs-test-coverage)
- SQLite via aiosqlite (existing — no changes in this feature) (050-fix-bugs-test-coverage)
- TypeScript 5.x / React 19 / Vite, TanStack Query v5, @dnd-kit/core ^6.3.1, @dnd-kit/sortable ^10.0.0, react-markdown ^10.1.0, remark-gfm ^4.0.1, sonner (NEW — toast library), Radix UI primitives, lucide-react, class-variance-authority, zod (050-frontend-ux-improvements)
- N/A (all state via TanStack Query against Python/FastAPI backend) (050-frontend-ux-improvements)
- TypeScript ~5.9.0 (frontend only — no backend changes) + React ^19.2.0, TanStack React Query ^5.91.0, Tailwind CSS ^4.2.0, @dnd-kit/core ^6.3.1, Sonner ^2.0.7, Vite ^8.0.0, Radix UI (popover, tooltip), Lucide React ^0.577.0, Zod ^4.3.6, react-hook-form ^7.71.2 (051-solune-ux-improvements)
- N/A (frontend-only changes; existing API endpoints remain unchanged) (051-solune-ux-improvements)
- Python ≥3.12 (backend, pyright targets 3.13), TypeScript ~5.9.0 (frontend) + FastAPI ≥0.135 (backend), React 19.2 (frontend), Pydantic ≥2.12 (backend), Vite 8 (frontend), TanStack Query v5.91 (frontend), Tailwind CSS 4.2 (frontend), @dnd-kit (frontend drag-drop) (052-fix-bugs-test-coverage)
- SQLite via aiosqlite ≥0.22 (existing — no changes in this feature) (052-fix-bugs-test-coverage)
- TypeScript 5.9 (frontend only) + React 19, React Router v7, TanStack Query v5, Tailwind CSS 4, Lucide React, Radix UI (053-global-command-palette)
- N/A (client-side search against already-loaded or cached entity data) (053-global-command-palette)
- Python 3.12+/3.13 (backend), TypeScript 5.9 (frontend) + FastAPI 0.135+, React 19, Pydantic 2.12+, Vite 8, TanStack Query v5, Tailwind CSS 4, @dnd-kit/core (board drag-and-drop) (053-pagination-infinite-scroll)
- SQLite via aiosqlite (existing — no schema changes required) (053-pagination-infinite-scroll)
- TypeScript ~5.9.0, React ^19.2.0 + @tanstack/react-query ^5.91.0 (mutations, query cache), sonner ^2.0.7 (toast notifications), React hooks (useState, useRef, useCallback, useEffect) (054-undoable-delete)
- N/A — client-side only; leverages TanStack Query cache for optimistic state (054-undoable-delete)
- Python 3.13 (backend), TypeScript 5.x (frontend) + FastAPI + Pydantic (backend API/models), aiosqlite (async SQLite), React 18 + TanStack Query v5 (frontend state), React Router v6 (routing), Lucide React (icons), Tailwind CSS (styling) (054-activity-audit-trail)
- SQLite via aiosqlite — direct SQL queries, no ORM. Pydantic models for serialization. Numbered SQL migration files (current highest: 032). (054-activity-audit-trail)
- Python 3.13 (backend), TypeScript 5.x + React 19.2 (frontend) + FastAPI (backend), TanStack Query v5.91 + React 19 (frontend), Sonner v2 (toasts) (054-optimistic-ui-updates)
- SQLite with aiosqlite (backend local state), GitHub Projects GraphQL API (board data source) (054-optimistic-ui-updates)
- TypeScript 5.x + React 19.2 + React Router v7 (useLocation, Link), TanStack Query v5.91 (existing), Lucide React (ChevronRight icon) (055-breadcrumb-deep-routes)
- N/A (no persistence — breadcrumb state is ephemeral React context) (055-breadcrumb-deep-routes)
- Python 3.13 (backend) + FastAPI (API framework), httpx (HTTP client), githubkit (GitHub API), aiosqlite (async SQLite) (055-fix-copilot-review-completion)
- SQLite with aiosqlite (durable state), in-memory `BoundedDict` (fast access) (055-fix-copilot-review-completion)
- TypeScript 5.x (strict mode) + TanStack React Query v5, React 18+, Sonner (toast notifications) (001-optimistic-updates-mutations)
- N/A (client-side cache only — TanStack Query `QueryClient`) (001-optimistic-updates-mutations)
- Python 3.13 (backend), TypeScript 5.x (frontend) + FastAPI, Starlette WebSockets, httpx (backend); React 19.2, TanStack Query v5, Radix UI, dnd-kit (frontend) (056-performance-review)
- SQLite (backend persistence), In-memory cache with TTL (runtime caching) (056-performance-review)

## Recent Changes
- Dependabot upgrades: ESLint 9→10, Vite 7→8, react-hooks 5→7, security 3→4, @vitejs/plugin-react 5→6, Docker images (python 3.14, node 25, nginx 1.29), GitHub Actions (checkout v6, setup-python v6, upload-artifact v7, setup-node v6)
- Frontend lint compliance: 28 react-hooks v7 errors fixed (render-time state adjustments, purity fixes, memoization preservation)
- Backend bug fixes: coroutine leak in transitions, dict mutation in completion polling, URL-encoding in label manager, exception handling in agent output, sys.executable in lint test
