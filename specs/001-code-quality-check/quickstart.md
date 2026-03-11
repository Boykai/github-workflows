# Quickstart: Code Quality Check

**Feature**: 001-code-quality-check | **Date**: 2026-03-11

## Prerequisites

- Python 3.12+ with `uv` package manager
- Node.js 20+ with npm
- Git

## Repository Setup

```bash
# Clone and navigate
cd /path/to/github-workflows

# Backend setup
cd backend
uv sync --extra dev

# Frontend setup
cd ../frontend
npm install
```

## Validation Commands

### Backend

```bash
cd backend

# Lint (Ruff)
uv run --extra dev ruff check src/

# Type check (Pyright)
uv run --extra dev pyright src/

# Unit tests
uv run --extra dev pytest tests/unit/ -x

# Specific test file
uv run --extra dev pytest tests/unit/test_specific.py -x -v
```

### Frontend

```bash
cd frontend

# Lint (ESLint)
npm run lint

# Type check (TypeScript)
npm run type-check

# Unit tests (Vitest + happy-dom)
npm run test

# Specific test file
npx vitest run src/hooks/__tests__/useBoardControls.test.tsx

# Build
npm run build
```

### Documentation

```bash
# Markdown lint
npx -y markdownlint-cli@0.48.0 docs/**/*.md --config .markdownlint.json

# Link check
npx -y markdown-link-check@3.14.2 docs/**/*.md --config .markdown-link-check.json --quiet
```

## Implementation Order

### Phase 1: Critical — Fix Silent Failures & Security (P0)

**Start here.** These changes fix active bugs and security issues.

1. **Exception handling audit** (`backend/src/`)
   - Audit all `except Exception:` blocks (38 remaining across 15 files)
   - Bind exceptions with `as e` and add logging
   - Narrow to specific exception types where possible
   - Skip `logging_utils.py` resilience guards (4 intentional bare blocks)

2. **Signal chat exception leaks** (`backend/src/services/signal_chat.py`)
   - Line ~103: Replace `error_detail=str(e)[:500]` with generic message
   - Line ~329: Replace `result["error"] = str(e)[:200]` with generic message
   - Log full exception details internally

### Phase 2: DRY — Consolidate Patterns (P1)

**Shared helpers already exist.** Verify full adoption and fill gaps.

1. **Verify helper adoption** — Confirm `resolve_repository()`, `cached_fetch()`, `require_selected_project()`, `handle_service_error()` are used at all applicable call sites
2. **Create external error sanitizer** — Add helper for Signal/external error responses (since `safe_error_response()` doesn't exist)

### Phase 3: Break Apart Frontend God Files (P2)

1. **Split `api.ts`** (1,136 LOC → 14 modules)
   - Extract `api/client.ts` with `request<T>()`, `ApiError`, auth listener
   - Create domain modules: auth, projects, chat, board, settings, workflow, signal, agents, pipelines, tools, chores, cleanup
   - Create `api/index.ts` re-exports
   - Update all import sites

2. **Split `useBoardControls.ts`** (375 LOC → 4 hooks)
   - Extract `useBoardFilters`, `useBoardSort`, `useBoardGroups`
   - Keep `useBoardControls` as composition wrapper

### Phase 4: Type Safety (P2)

1. **Backend return types** — Add explicit return type annotations to public functions
2. **Frontend unsafe casts** — Replace 4 production `as unknown as` casts with proper types

### Phase 5: Technical Debt (P3)

1. **Singleton migration** — Move `_orchestrator_instance` and `_ai_agent_service_instance` to FastAPI DI
2. **Migration uniqueness** — Add test verifying no duplicate migration prefixes
3. **Chat persistence** — Verify/complete in-memory → SQLite migration for chat stores
4. **TODO resolution** — Convert `api/projects.py:109` to GitHub issue; others resolved by above work

### Phase 6: Performance & Observability (P3)

1. **Memoization** — Add `useMemo` / `React.memo` to expensive page computations
2. **AbortController** — Propagate `AbortSignal` from TanStack Query through API modules
3. **Bounded stores** — Add size limits to `_signal_pending` and other in-memory collections
4. **Bundle analysis** — Add `rollup-plugin-visualizer` to Vite config

### Phase 7: Testing Gaps (P4, Ongoing)

1. **Backend exception tests** — After Phase 1 narrowing, test specific exception types
2. **Frontend component tests** — Add render + a11y tests for pages and modals
3. **Accessibility assertions** — Add `aria-live` to chat regions, expand `jest-axe` coverage

## Key Files Reference

| Purpose | File |
|---------|------|
| Shared error handling | `backend/src/logging_utils.py` |
| Shared utilities | `backend/src/utils.py` |
| DI helpers | `backend/src/dependencies.py` |
| Frontend API client | `frontend/src/services/api.ts` |
| Frontend class helper | `frontend/src/lib/utils.ts` |
| Board controls hook | `frontend/src/hooks/useBoardControls.ts` |
| Signal chat service | `backend/src/services/signal_chat.py` |
| Migration directory | `backend/src/migrations/` |
| Feature spec | `specs/001-code-quality-check/spec.md` |

## PR Strategy

Each phase should be a separate PR (or group of PRs) to keep reviews manageable:

- **PR 1**: Phase 1 — Exception handling + security fixes
- **PR 2**: Phase 2 — DRY verification + external error helper
- **PR 3**: Phase 3 — Frontend API split + hook decomposition
- **PR 4**: Phase 4 — Type safety improvements
- **PR 5**: Phase 5 — Technical debt (singletons, migrations, chat persistence)
- **PR 6**: Phase 6 — Performance and observability
- **PR 7+**: Phase 7 — Testing gaps (ongoing)

Each PR MUST leave the changed scope in a passing, releasable state (FR-027).
