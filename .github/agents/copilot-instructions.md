# codeagentworkflows Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-01-30

## Active Technologies
- In-memory session storage (MVP), Redis for token caching (future) (001-github-project-chat)
- Python 3.11 + FastAPI, httpx, azure-ai-inference, pydantic (001-github-project-workflow)
- In-memory (MVP) with session-based caching (001-github-project-workflow)
- Python 3.11 + FastAPI, httpx, Pydantic 2.x, pydantic-settings (002-speckit-agent-assignment)
- In-memory (dicts/lists); GitHub Issue comments as durable source of truth (002-speckit-agent-assignment)
- Python 3.11 (backend), TypeScript ~5.4 (frontend) + FastAPI, React 18, TanStack React Query, plain CSS with custom properties (001-github-project-board)
- N/A (no persistent storage; data fetched from GitHub API) (001-github-project-board)
- Python 3.12 (backend), TypeScript ~5.4 (frontend) + FastAPI ≥0.109, Pydantic ≥2.5, httpx ≥0.26 (backend); React 18.3, @tanstack/react-query ^5.17, `@dnd-kit/core` + `@dnd-kit/sortable` (new, frontend) (004-agent-workflow-config-ui)
- In-memory dict (`_workflow_configs` in `workflow_orchestrator.py`); no database (004-agent-workflow-config-ui)
- Python 3.12 (Dockerfile), ≥3.11 (pyproject.toml); TypeScript ~5.4 (frontend) + FastAPI 0.109+, Pydantic 2.5+, pydantic-settings 2.1+, React 18.3, TanStack Query 5.17+ (006-sqlite-settings-storage)
- SQLite database file, Docker volume mount (new) (006-sqlite-settings-storage)
- Python ≥3.11 (backend), TypeScript ~5.4 (frontend) + FastAPI, Pydantic v2, httpx, aiosqlite, github-copilot-sdk, agent-framework-core (backend); React 18, @tanstack/react-query v5, socket.io-client, Vite 5 (frontend) (007-codebase-cleanup-refactor)
- SQLite via aiosqlite (settings/sessions); in-memory caches (InMemoryCache, module-level dicts/sets) (007-codebase-cleanup-refactor)
- Python ≥3.11 (Pyright targets 3.12), TypeScript ~5.4 (target ES2022) + FastAPI ≥0.109, React 18.3, TanStack Query 5.17, Pydantic 2.x, httpx, aiosqlite (008-test-coverage-bug-fixes)
- SQLite via aiosqlite (WAL mode, migration-managed schema) (008-test-coverage-bug-fixes)
- Python 3.11+ (backend, pyright targets 3.12), TypeScript ~5.4 (frontend) + FastAPI, Pydantic 2.x, httpx, aiosqlite (backend); React 18, TanStack Query v5, Vite 5, dnd-kit (frontend) (009-codebase-cleanup-refactor)
- SQLite via aiosqlite (async), plus synchronous `sqlite3` in workflow_orchestrator (to be migrated) (009-codebase-cleanup-refactor)
- TypeScript ~5.4, CSS3 + React 18.3, Vite (010-blue-background)

- Python 3.11+ (backend), TypeScript 5.x (frontend) (001-github-project-chat)

## Project Structure

```text
src/
tests/
```

## Commands

cd src [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] pytest [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] ruff check .

## Code Style

Python 3.11+ (backend), TypeScript 5.x (frontend): Follow standard conventions

## Recent Changes
- 010-blue-background: Added TypeScript ~5.4, CSS3 + React 18.3, Vite
- 009-codebase-cleanup-refactor: Added Python 3.11+ (backend, pyright targets 3.12), TypeScript ~5.4 (frontend) + FastAPI, Pydantic 2.x, httpx, aiosqlite (backend); React 18, TanStack Query v5, Vite 5, dnd-kit (frontend)
- 008-test-coverage-bug-fixes: Added Python ≥3.11 (Pyright targets 3.12), TypeScript ~5.4 (target ES2022) + FastAPI ≥0.109, React 18.3, TanStack Query 5.17, Pydantic 2.x, httpx, aiosqlite


<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
