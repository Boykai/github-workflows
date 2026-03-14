# Quickstart: Codebase Improvement Plan — Modern Best Practices Overhaul

**Feature**: `035-best-practices-overhaul` | **Date**: 2026-03-11 | **Plan**: [plan.md](plan.md)

## Overview

This guide helps developers implement the 7-phase codebase overhaul. Each phase is independently verifiable. Phase 1 must be completed first; Phases 2–5 can be done in parallel; Phases 6–7 are independent.

## Prerequisites

- Python 3.13+ with `uv` package manager
- Node.js 20+ with npm
- Git
- Docker (for container restart testing in Phase 1)

## Setup

```bash
# Clone and checkout the feature branch
git checkout 035-best-practices-overhaul

# Backend setup
cd backend
uv sync --extra dev

# Frontend setup
cd ../frontend
npm install
```

## Phase Execution Order

```text
Phase 1: Data Integrity ──────────────────┐
                                          ▼
              ┌──── Phase 2: Complexity ──────┐
              ├──── Phase 3: DRY/Errors ──────┤
              ├──── Phase 4: DI Modern. ──────┤
              └──── Phase 5: Security ────────┘
                                          │
              ┌──── Phase 6: Observability ───┤
              └──── Phase 7: Dev Experience ──┘
```

## Phase 1: Data Integrity & Reliability

### Step 1.1: Create Pipeline State Store

1. Create migration `backend/src/migrations/021_pipeline_state.sql` (see [pipeline-state-store contract](contracts/pipeline-state-store.md))
2. Create `backend/src/services/pipeline_state_store.py` following `session_store.py` pattern
3. Add `asyncio.Lock` in `transitions.py` for all BoundedDict mutations
4. Replace direct BoundedDict access in `transitions.py` public functions with write-through calls

### Step 1.2: Wire Chat Persistence

1. Create `backend/src/services/chat_store.py` (see [chat-persistence contract](contracts/chat-persistence.md))
2. In `backend/src/api/chat.py`, replace in-memory dicts with `chat_store.py` calls
3. The migration `012_chat_persistence.sql` already runs automatically

### Step 1.3: Add Async-Safe Locking

1. Add `_state_lock = asyncio.Lock()` in `transitions.py`
2. Wrap all mutation functions with `async with _state_lock:`
3. Add `_ws_lock = asyncio.Lock()` in `websocket.py`
4. Wrap `ConnectionManager.connect()` and `disconnect()` with lock

### Verify Phase 1

```bash
cd backend
uv run --extra dev pytest tests/unit/ -x
uv run --extra dev ruff check src/
uv run --extra dev pyright src/
```

## Phase 2: Cyclomatic Complexity Reduction

### Backend

1. **`post_agent_outputs_from_pr`** (agent_output.py): Extract into `_scan_pipeline_issues()`, `_extract_pr_outputs()`, `_route_output_to_destination()`, `_advance_pipeline_state()`
2. **`assign_agent_for_status`** (orchestrator.py): Extract `_resolve_agent_config()`, `_determine_base_ref()`, `_resolve_sub_issue()`
3. **`recover_stalled_issues`** (recovery.py): Extract `_recover_single_issue()`, `_validate_copilot_assignment()`, `_validate_wip_pr()`

### Frontend

4. **`usePipelineConfig`**: Return grouped objects `{ crud, validation, state, assignment, model, board }`
5. **`useAgentConfig`**: Extract `useAgentDnd`, return grouped objects

### Verify Phase 2

```bash
# Backend
cd backend
uv run --extra dev pytest tests/unit/ -x
uv run --extra dev ruff check src/

# Frontend
cd ../frontend
npm run test
npm run type-check
npm run lint
```

## Phase 3: DRY & Error Handling Consolidation

### Step 3.1: Repository Resolution DI

1. Create FastAPI dependency `get_repository()` in `dependencies.py`
2. Replace all 25+ `resolve_repository()` + try/except patterns with `Depends(get_repository)`

### Step 3.2: Adopt Error Infrastructure

1. Apply `@handle_github_errors` decorator to endpoint functions
2. Replace bare `except Exception` with specific types (see [error-handling contract](contracts/error-handling.md))

### Step 3.3: Pydantic Input Models

1. Create `backend/src/models/api_inputs.py` with typed models
2. Replace `dict` parameters in settings and webhook endpoints

### Verify Phase 3

```bash
cd backend
# Should return 0 results:
grep -r "except Exception" src/api/ --include="*.py" | grep -v "noqa"
uv run --extra dev pytest tests/unit/ -x
```

## Phase 4: Dependency Injection Modernization

1. Create `backend/src/interfaces.py` with Protocol definitions
2. Move singleton creation into `lifespan()` in `main.py`
3. Create `Depends()` functions for all services in `dependencies.py`
4. Remove module-level `github_projects_service = GitHubProjectsService()`
5. Remove lazy import hacks in `dependencies.py`

### Verify Phase 4

```bash
cd backend
# Should return 0 module-level service instantiations:
grep -r "= GitHubProjectsService()" src/ --include="*.py"
grep -r "_ai_agent_service_instance" src/ --include="*.py"
uv run --extra dev pytest tests/unit/ -x
```

## Phase 5: Security Hardening

1. Update CORS `allow_headers` in `main.py` (see [security contract](contracts/security-middleware.md))
2. Create `backend/src/middleware/csp.py` and register in `main.py`
3. Add `ADMIN_GITHUB_USER_ID` to config and update `require_admin()` in `dependencies.py`
4. Verify all session queries include `session_id` filter

### Verify Phase 5

```bash
cd backend
# Check CORS:
grep -A5 "allow_headers" src/main.py
# Check CSP:
grep -r "Content-Security-Policy" src/ --include="*.py"
uv run --extra dev pytest tests/unit/ -x
```

## Phase 6: Observability & Testing

1. Audit all `except` blocks — ensure `logger.error(exc_info=True)` in every handler
2. Verify `window.onerror` and `unhandledrejection` handlers in `frontend/src/main.tsx` (already present)
3. Create integration tests in `backend/tests/integration/`
4. Tighten test assertions (specific status codes)
5. Add `htmlcov/`, `coverage/`, `e2e-report/`, `test-results/` to `.gitignore`

### Verify Phase 6

```bash
cd backend
uv run --extra dev pytest tests/ -x --cov=src
cd ../frontend
npm run test -- --coverage
```

## Phase 7: Developer Experience

1. Restructure `usePipelineConfig` return value (if not done in Phase 2)
2. Verify all retry logic uses `tenacity` (backend) or TanStack Query `retry` (frontend)

### Verify Phase 7

```bash
cd frontend
npm run test
npm run type-check
```

## Full Verification

After all phases:

```bash
# Backend
cd backend
uv run --extra dev pytest tests/unit/ -x
uv run --extra dev ruff check src/
uv run --extra dev pyright src/

# Frontend
cd ../frontend
npm run test
npm run type-check
npm run lint
```

## Key Files Created/Modified

| Phase | New Files | Modified Files |
|-------|-----------|----------------|
| 1 | `pipeline_state_store.py`, `chat_store.py`, `021_pipeline_state.sql` | `transitions.py`, `chat.py`, `websocket.py`, `main.py` |
| 2 | — | `agent_output.py`, `orchestrator.py`, `recovery.py`, `usePipelineConfig.ts`, `useAgentConfig.ts` |
| 3 | `models/api_inputs.py` | `dependencies.py`, all `api/*.py` files |
| 4 | `interfaces.py` | `main.py`, `dependencies.py`, `ai_agent.py`, `service.py` |
| 5 | `middleware/csp.py` | `main.py`, `dependencies.py`, `config.py` |
| 6 | `tests/integration/test_pipeline_lifecycle.py` | `.gitignore`, various test files |
| 7 | `usePipelineCrud.ts`, `useAgentDnd.ts` | `usePipelineConfig.ts`, `useAgentConfig.ts` |
