# Quickstart: Codebase Cleanup — Reduce Technical Debt

**Feature**: `018-code-cleanup` | **Date**: 2026-03-05

## Overview

A systematic codebase cleanup across the full repository (backend, frontend, scripts, specs) to reduce technical debt and improve maintainability. All changes are internal-only — no public API contracts, data model schemas, or user-facing behavior changes.

## Prerequisites

- Repository cloned and on the `018-code-cleanup` branch
- Python ≥3.11 with backend dependencies installed (`pip install -e ".[dev]"` from `backend/`)
- Node.js 20+ with frontend dependencies installed (`npm install` from `frontend/`)
- Docker and Docker Compose (for integration validation)

## Cleanup Execution Order

The cleanup follows the priority order from the spec. Each category can be executed independently, but the recommended order minimizes conflicts:

### Phase 1: Detection & Analysis (Read-Only)

1. **Run all CI checks to establish baseline**:
   ```bash
   # Backend
   cd backend
   ruff check src/ tests/
   ruff format --check src/ tests/
   pyright src/
   pytest --tb=short

   # Frontend
   cd frontend
   npx eslint src/
   npx tsc --noEmit
   npx vitest run
   npm run build
   ```

2. **Run dead code detection tools**:
   ```bash
   # Backend — unused imports, variables
   cd backend
   ruff check --select F401,F811,F841 src/

   # Frontend — unused exports, types
   cd frontend
   npx tsc --noUnusedLocals --noUnusedParameters --noEmit 2>&1 | head -50
   ```

3. **Grep for cleanup targets**:
   ```bash
   # Backwards-compatibility patterns
   grep -rn "legacy\|compat\|old_format\|deprecated\|shim\|polyfill" backend/src/ frontend/src/

   # Stale TODO/FIXME comments
   grep -rn "TODO\|FIXME\|HACK" backend/src/ frontend/src/

   # Commented-out code (Python)
   grep -rn "^[[:space:]]*#.*def \|^[[:space:]]*#.*class \|^[[:space:]]*#.*import " backend/src/

   # Commented-out code (TypeScript)
   grep -rn "^[[:space:]]*//.*function \|^[[:space:]]*//.*const \|^[[:space:]]*//.*import " frontend/src/
   ```

### Phase 2: Remove Dead Code & Shims (P1)

1. Remove confirmed backwards-compatibility shims (verify each individually)
2. Remove unused imports, variables, and type definitions
3. Remove commented-out code blocks
4. Remove unused functions, methods, and components
5. **Validate**: Run full CI checks after each removal

### Phase 3: Consolidate Duplicated Logic (P2)

1. Extract shared `TokenClientCache` from completion_providers.py and model_fetcher.py
2. Evaluate and possibly extract shared `GenericChatFlow` component
3. Evaluate and possibly extract shared CRUD hooks factory
4. Consolidate chat response models if field alignment is confirmed
5. **Validate**: Run full CI checks after each consolidation

### Phase 4: Delete Stale Tests (P2)

1. Identify tests targeting deleted or refactored functionality
2. Identify tests with excessive mocking that don't test real behavior
3. Remove identified stale tests
4. Remove test artifacts
5. **Validate**: Run full test suite, verify coverage doesn't drop for active code

### Phase 5: General Hygiene (P3)

1. Remove unused npm dependencies (`socket.io-client`, `jsdom`)
2. ~~Remove unused environment variables (`SESSION_EXPIRE_HOURS`)~~ — Corrected: `SESSION_EXPIRE_HOURS` IS actively used by `config.py` → `session_store.py`. Do NOT remove.
3. Review and remove stale TODO/FIXME comments (only those referencing completed work)
4. **Validate**: Run full CI checks and verify `npm install`/`pip install` still work

## Validation Checklist

After all changes, verify:

- [ ] `ruff check src/ tests/` passes (backend)
- [ ] `ruff format --check src/ tests/` passes (backend)
- [ ] `pyright src/` passes (backend)
- [ ] `pytest` passes with no new failures (backend)
- [ ] `npx eslint src/` passes (frontend)
- [ ] `npx tsc --noEmit` passes (frontend)
- [ ] `npx vitest run` passes with no new failures (frontend)
- [ ] `npm run build` succeeds (frontend)
- [ ] `docker compose build` succeeds
- [ ] No public API routes changed
- [ ] Every removal documented with rationale in PR description

## Key Files

### Backend (Python)
- `backend/src/api/*.py` — API route handlers (inspect for dead routes)
- `backend/src/models/*.py` — Pydantic models (inspect for duplicates)
- `backend/src/services/*.py` — Business logic (inspect for duplication)
- `backend/src/services/encryption.py` — Legacy token shim candidate
- `backend/src/services/completion_providers.py` — Token cache duplication
- `backend/src/services/model_fetcher.py` — Token cache duplication
- `backend/tests/helpers/factories.py` — Shared test factories
- `backend/tests/helpers/mocks.py` — Shared test mocks
- `backend/pyproject.toml` — Dependency manifest

### Frontend (TypeScript)
- `frontend/src/components/agents/AgentChatFlow.tsx` — Chat flow duplication
- `frontend/src/components/chores/ChoreChatFlow.tsx` — Chat flow duplication
- `frontend/src/hooks/useAgents.ts` — CRUD hook duplication
- `frontend/src/hooks/useChores.ts` — CRUD hook duplication
- `frontend/src/services/api.ts` — API client
- `frontend/package.json` — Dependency manifest

### Configuration
- `.env.example` — Environment variable reference
- `docker-compose.yml` — Service definitions

## Commit Convention

- `refactor:` — For code consolidation (merging duplicates into shared implementations)
- `chore:` — For dead code removal, test cleanup, and dependency removal
