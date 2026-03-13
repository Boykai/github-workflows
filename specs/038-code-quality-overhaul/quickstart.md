# Quickstart: 038 Code Quality Overhaul

## Prerequisites

- Python ≥ 3.12
- Node.js ≥ 18
- Docker & Docker Compose
- Git on branch `038-code-quality-overhaul`

## Setup

```bash
# 1. Switch to the feature branch
git checkout 038-code-quality-overhaul

# 2. Install backend dependencies
cd backend && pip install -e ".[dev]" && cd ..

# 3. Install frontend dependencies
cd frontend && npm install && cd ..

# 4. Start services (database, signal-api)
docker compose up -d
```

## Development Workflow

### Error Handling Consolidation (FR-001 → FR-003)

Replace inline `try/except` in an API file with `handle_service_error()`:

```python
# Before (inline):
try:
    result = await github_service.get_issues(owner, repo)
except Exception as e:
    logger.error(f"Failed: {e}")
    raise HTTPException(status_code=500, detail=str(e))

# After (consolidated):
from logging_utils import handle_service_error

try:
    result = await github_service.get_issues(owner, repo)
except Exception as e:
    handle_service_error(e, "get_issues", owner=owner, repo=repo)
```

**Files to update** (13 remaining): check `grep -rL "handle_service_error" backend/src/api/ --include="*.py"` to find unconverted files.

### DRY Consolidation (FR-004 → FR-006)

1. Remove `_resolve_repository()` duplicate from `api/chat.py`
2. Import `from utils import resolve_repository` instead
3. Replace bare `cached_fetch()` reimplementations with `from utils import cached_fetch`

### Chat Module Decomposition (FR-007 → FR-009)

```bash
# Create the package structure
mkdir -p backend/src/api/chat
touch backend/src/api/chat/__init__.py

# Move functions into focused submodules
# See contracts/chat-module.md for the endpoint distribution
```

### Type Generation (FR-010 → FR-012)

```bash
# Install the type generator
cd frontend && npm install -D openapi-typescript && cd ..

# Generate types (backend must be running)
docker compose up backend -d
npx openapi-typescript http://localhost:8000/openapi.json \
  --output frontend/src/types/generated.ts

# Generate constants
python scripts/generate-constants.py \
  --input backend/src/constants.py \
  --output frontend/src/constants/generated.ts
```

### Frontend Hook Decomposition (FR-013)

Split `usePipelineConfig.ts` (193 lines, 5 concerns) into:

1. `usePipelineOrchestration.ts` — loading/save orchestration
2. `usePipelineCrud.ts` — TanStack Query mutations for CRUD
3. `usePipelineDirtyState.ts` — unsaved change tracking

### Chat Persistence Wiring (FR-008)

Wire the existing `services/chat_store.py` (currently dead code):

```python
# In api/chat/messaging.py:
from services.chat_store import save_message, get_messages

# Phase A: Write-through (add saves alongside in-memory dict)
await save_message(session_id, "user", content)
response = await ai_agent.process(content)
await save_message(session_id, "assistant", response)
```

## Running Tests

```bash
# Backend tests
cd backend && pytest -x -v

# Backend tests with coverage
cd backend && pytest --cov=src --cov-report=html

# Frontend tests
cd frontend && npm run test

# Frontend tests with coverage
cd frontend && npm run test:coverage

# E2E tests
cd frontend && npm run test:e2e
```

### Adding New Tests

- **Page tests** go in `frontend/src/pages/__tests__/`
- **Hook tests** go in `frontend/src/hooks/__tests__/`
- **Backend API tests** go in `backend/tests/` mirroring `src/api/` structure
- **Integration tests** for chat persistence: `backend/tests/test_chat_persistence.py`

## Verification Checklist

After each change set, verify:

- [ ] `cd backend && pytest -x` — all tests pass
- [ ] `cd backend && ruff check src/` — no lint errors  
- [ ] `cd backend && pyright src/` — no type errors
- [ ] `cd frontend && npm run lint` — no lint errors
- [ ] `cd frontend && npm test` — all tests pass
- [ ] `cd frontend && npx tsc --noEmit` — no type errors
- [ ] `docker compose build` — images build successfully

## Key Files Reference

| File | Purpose |
|------|---------|
| `backend/src/logging_utils.py` | `handle_service_error()`, `StructuredJsonFormatter`, `handle_github_errors()` |
| `backend/src/utils.py` | `resolve_repository()`, `cached_fetch()`, `utcnow()` |
| `backend/src/exceptions.py` | 11 `AppException` subclasses |
| `backend/src/services/chat_store.py` | Chat persistence (currently unwired) |
| `backend/src/dependencies.py` | `require_selected_project()`, `get_github_service()` |
| `frontend/src/hooks/usePipelineConfig.ts` | Target for decomposition |
| `frontend/src/types/index.ts` | Manually maintained types (to supplement with generated) |
