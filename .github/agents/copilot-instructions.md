# GitHub Workflows Chat — Development Guidelines

Last updated: 2026-03-01

## Tech Stack

### Backend (Python)
- **Runtime**: Python ≥3.11 (Docker image: 3.12-slim)
- **Framework**: FastAPI ≥0.109, Uvicorn ≥0.27
- **Data validation**: Pydantic ≥2.5, pydantic-settings ≥2.1
- **HTTP client**: httpx ≥0.26
- **Database**: SQLite via aiosqlite ≥0.20 (WAL mode, migration-managed schema, file-backed at `/app/data/settings.db`)
- **AI / Agents**: github-copilot-sdk ≥0.1, agent-framework-core ≥1.0.0a1, openai ≥1.0, azure-ai-inference ≥1.0.0b1
- **Auth**: python-jose[cryptography] ≥3.3 (JWT)
- **Utilities**: tenacity ≥8.2 (retries), websockets ≥12.0, python-multipart ≥0.0.6, pyyaml ≥6.0.1
- **Linting**: ruff ≥0.9 (target py311, line-length 100)
- **Type checking**: pyright ≥1.1.400 (targets Python 3.12, basic mode)
- **Testing**: pytest ≥7.4, pytest-asyncio ≥0.23 (auto mode), pytest-cov ≥4.1

### Frontend (TypeScript)
- **Runtime**: Node 20 (Docker: node:20-alpine build → nginx:alpine production)
- **Language**: TypeScript ~5.4 (target ES2022)
- **Framework**: React ^18.3, React DOM ^18.3
- **Build**: Vite ^5.4
- **Server state**: @tanstack/react-query ^5.17
- **Styling**: Tailwind CSS ^3.4, Shadcn UI (Radix UI primitives), class-variance-authority, clsx, tailwind-merge, lucide-react (icons)
- **Drag & drop**: @dnd-kit/core ^6.3, @dnd-kit/sortable ^10.0, @dnd-kit/modifiers ^9.0
- **Real-time**: socket.io-client ^4.7
- **Linting**: ESLint ^9 (flat config, typescript-eslint, react-hooks), Prettier ^3.2
- **Testing**: Vitest ^4.0 (happy-dom), @testing-library/react ^16.3, Playwright ^1.58 (E2E, Chromium)

### Infrastructure
- **Containers**: Docker Compose — 3 services on `ghchat-network` bridge
  - `backend` (port 8000) — FastAPI app, `ghchat-data` volume for SQLite
  - `frontend` (port 5173 → nginx :80) — static SPA
  - `signal-api` (port 8080 internal) — `bbernhard/signal-cli-rest-api:latest`, JSON-RPC mode
- **CI**: GitHub Actions — backend (ruff, pyright, pytest) + frontend (eslint, tsc, vitest, vite build) + Docker image build verification
- **CI actions**: pinned to SHA with explicit `permissions: contents: read`

## Project Structure

```
backend/
  src/
    api/              # FastAPI route handlers
    middleware/        # Request/response middleware
    migrations/       # SQL migration files (001–007)
    models/           # Pydantic models (board, chat, settings, task, user, agent_creator, etc.)
    prompts/          # AI prompt templates
    services/         # Business logic
      copilot_polling/ # Background polling loop for Copilot agent pipeline
      github_projects/ # GitHub GraphQL API client
      workflow_orchestrator/ # Agent pipeline config, state, transitions
      agent_creator.py # #agent command: guided custom agent creation flow
  tests/
    unit/             # pytest unit tests
    integration/      # pytest integration tests
    helpers/          # Shared factories and mocks

frontend/
  src/
    components/       # React components (auth, board, chat, common, settings, ui)
    hooks/            # Custom React hooks (useAuth, useChat, useProjectBoard, useWorkflow, etc.)
    lib/              # Shared utilities
    pages/            # Route pages
    services/         # API client functions
    types/            # TypeScript type definitions
    utils/            # Helper functions
  e2e/                # Playwright E2E tests
```

## Commands

```bash
# Backend
cd backend && source .venv/bin/activate
ruff check src/ tests/          # lint
ruff format src/ tests/         # format
pyright src/                    # type check
pytest tests/unit/ -q           # unit tests
pytest tests/ --cov=src         # all tests with coverage

# Frontend
cd frontend
npm run lint                    # eslint
npm run type-check              # tsc --noEmit
npm test                        # vitest
npm run build                   # production build
npx playwright test             # E2E tests
```

## Code Style

- **Python**: Follow ruff defaults — double quotes, 100 char lines, isort with `known-first-party = ["src"]`
- **TypeScript**: Strict mode, ESNext modules, path alias `@/` → `src/`
- **Tests**: Arrange-Act-Assert pattern. Backend factories in `tests/helpers/factories.py`, mocks in `tests/helpers/mocks.py`. Frontend test setup in `src/test/setup.ts`
- **Commits**: Conventional commits (`feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`)

## Key Architecture Notes

- Database migrations run automatically on startup (sequential SQL files in `src/migrations/`)
- SQLite uses WAL mode, busy_timeout=5000ms, foreign_keys=ON
- Copilot polling loop runs as a background task, scanning project board items every N seconds
- Sub-issues use title convention `[agent-name] Parent Title` and are filtered from the polling loop
- Agent pipeline state tracks per-issue progress through configurable status→agent mappings
- Session auth uses secure HTTP-only cookies set via a shared helper

## Active Technologies
- Python 3.12 (backend), TypeScript 5.4 / Node 20 (frontend) + FastAPI, Pydantic 2.5+, aiosqlite 0.20+ (backend); React 18, Vite 5, TanStack Query v5, Shadcn/ui (frontend) (014-housekeeping-triggers)
- SQLite (aiosqlite, WAL mode) — extends existing `settings.db` with new tables for housekeeping tasks, templates, and trigger history (014-housekeeping-triggers)
- Python 3.12 (backend), TypeScript 5.4 / Node 20 (frontend) + FastAPI 0.109+, aiosqlite 0.20+, Pydantic Settings (backend); React 18, Vite 5, TanStack Query v5, Radix UI, Socket.io-client (frontend) (016-codebase-bug-bash)
- SQLite via aiosqlite (async, no ORM), migrations in `backend/src/migrations/` (001–009) (016-codebase-bug-bash)

## Recent Changes
- 014-housekeeping-triggers: Added Python 3.12 (backend), TypeScript 5.4 / Node 20 (frontend) + FastAPI, Pydantic 2.5+, aiosqlite 0.20+ (backend); React 18, Vite 5, TanStack Query v5, Shadcn/ui (frontend)
- Python 3.11 (backend), TypeScript/React (frontend) + FastAPI, aiosqlite, Pydantic v2 (backend); React 18, Vite, TanStack Query, @dnd-kit, shadcn/ui tokens (frontend) (014-human-agent-pipeline)
- SQLite (WAL mode) via aiosqlite — no new tables required (reuses existing pipeline state and sub-issue tracking) (014-human-agent-pipeline)

## Recent Changes
- 016-codebase-bug-bash: Added Python 3.12 (backend), TypeScript 5.4 / Node 20 (frontend) + FastAPI 0.109+, aiosqlite 0.20+, Pydantic Settings (backend); React 18, Vite 5, TanStack Query v5, Radix UI, Socket.io-client (frontend)
- 014-human-agent-pipeline: Added Python 3.11 (backend), TypeScript/React (frontend) + FastAPI, aiosqlite, Pydantic v2 (backend); React 18, Vite, TanStack Query, @dnd-kit, shadcn/ui tokens (frontend)
- Python 3.12 (backend), TypeScript 5.4 / Node 20 (frontend) + FastAPI, React 18, Vite 5, TanStack Query v5, httpx (backend HTTP client) (014-board-refresh-ratelimit)

## Recent Changes
- 016-codebase-bug-bash: Added Python 3.12 (backend), TypeScript 5.4 / Node 20 (frontend) + FastAPI 0.109+, aiosqlite 0.20+, Pydantic Settings (backend); React 18, Vite 5, TanStack Query v5, Radix UI, Socket.io-client (frontend)

## Recent Changes
- 016-codebase-bug-bash: Added Python 3.12 (backend), TypeScript 5.4 / Node 20 (frontend) + FastAPI 0.109+, aiosqlite 0.20+, Pydantic Settings (backend); React 18, Vite 5, TanStack Query v5, Radix UI, Socket.io-client (frontend)

