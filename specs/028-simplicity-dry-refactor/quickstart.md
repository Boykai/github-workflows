# Quickstart: Simplicity & DRY Refactoring Plan (5 Phases)

**Feature**: `028-simplicity-dry-refactor` | **Date**: 2026-03-07

---

## Prerequisites

- Python ≥3.12 (project targets 3.13) and Node.js 20+
- Repository cloned with backend and frontend set up
- Familiarity with project structure: `backend/src/` (FastAPI + Python), `frontend/src/` (React + TypeScript)
- Docker Compose available (for Phase 3 validation)

## Development Environment Setup

```bash
# Backend
cd backend
pip install -e ".[dev]"
ruff check src/          # Lint check
pyright src/             # Type check
pytest                   # Run tests

# Frontend
cd frontend
npm install
npm run lint             # ESLint
npm run type-check       # tsc --noEmit
npm run test             # Vitest
```

---

## Phase Execution Order

```
Phase 1: Backend Quick Wins (DRY consolidation)
    │   Steps 1.1–1.4 are parallel
    │
    ├──→ Phase 2: Service Decomposition (depends on Phase 1)
    │       │
    │       └──→ Phase 3: Initialization Consolidation (depends on Phase 2)
    │               │
    │               └──→ Phase 5: Test Cleanup (depends on Phases 1–3)
    │
    └──→ Phase 4: Frontend DRY Consolidation (parallel with Phases 2–3)
```

---

## Phase 1: Backend Quick Wins

### Step 1.1 — Unify Repository Resolution

```bash
# 1. Find all duplicate implementations
grep -rn "resolve_repository\|_get_repository_info\|get_repo" backend/src/api/

# 2. Update callers to use utils.resolve_repository()
# Edit: workflow.py, main.py, projects.py, tasks.py, chat.py, chores.py

# 3. Delete _get_repository_info from workflow.py

# 4. Verify
grep -rn "_get_repository_info" backend/
# Expected: 0 results
pytest
```

### Step 1.2 — Adopt Error Handling Helpers

```bash
# 1. Find endpoints with hand-rolled error handling
grep -rn "except.*Exception.*as.*e:" backend/src/api/ | head -20

# 2. Replace with handle_service_error() from logging_utils.py
# Edit: board.py, workflow.py, projects.py, auth.py

# 3. Verify
pytest
```

### Step 1.3 — Create Validation Helper

```bash
# 1. Add require_selected_project() to dependencies.py

# 2. Find inline guard clauses
grep -rn "selected_project_id" backend/src/api/

# 3. Replace with require_selected_project(session)

# 4. Verify
grep -rn "if not.*selected_project_id" backend/src/api/
# Expected: 0 results outside dependencies.py
pytest
```

### Step 1.4 — Generic Cache Wrapper

```bash
# 1. Add cached_fetch() to cache.py

# 2. Find verbose cache patterns
grep -rn "cache\.get\|cache\.set" backend/src/api/

# 3. Replace with cached_fetch()

# 4. Verify
pytest
```

---

## Phase 2: Service Decomposition

```bash
# Extract one module at a time. After each:
pytest
ruff check backend/src/
python -c "import src.services.github_projects"  # No circular imports

# Extraction order (follows dependency graph):
# 1. client.py (base — no dependencies)
# 2. fields.py (depends only on client)
# 3. projects.py, copilot.py, repository.py (depend only on client)
# 4. issues.py, board.py (depend on client + fields)
# 5. pull_requests.py (depends only on client)
# 6. Update __init__.py facade
# 7. Remove service.py

# Verify each module < 800 LOC:
wc -l backend/src/services/github_projects/*.py
```

---

## Phase 3: Initialization Consolidation

```bash
# 1. Ensure all services created in lifespan()
grep -n "app.state" backend/src/main.py

# 2. Remove module-level singletons
grep -rn "github_projects_service = " backend/src/

# 3. Update callers to use Depends()
grep -rn "from.*import github_projects_service" backend/src/api/

# 4. Verify
docker compose up -d
curl http://localhost:8000/api/v1/health  # Health check
# Test OAuth flow manually
docker compose down
pytest
```

---

## Phase 4: Frontend DRY Consolidation

### Step 4.1 — CRUD Hook Factory

```bash
# 1. Create hooks/useCrudResource.ts
# 2. Refactor useAgents.ts and useChores.ts
# 3. Verify
cd frontend && npm run test
```

### Step 4.2 — Settings Hook Consolidation

```bash
# 1. Refactor useSettings.ts to use generic pattern
# 2. Verify
npm run test
```

### Step 4.3 — Shared UI Components

```bash
# 1. Create PreviewCard.tsx, Modal.tsx, ErrorAlert.tsx
# 2. Refactor consuming components
# 3. Verify
npm run test
# Visual check in browser
```

### Step 4.4 — Query Key Registry

```bash
# 1. Create hooks/queryKeys.ts
# 2. Migrate keys from individual hook files
# 3. Verify
npm run test
```

### Step 4.5 — ChatInterface Split

```bash
# 1. Extract ChatMessageList.tsx and ChatInput.tsx
# 2. Update ChatInterface.tsx to compose them
# 3. Verify
npm run test
```

---

## Phase 5: Test Cleanup

```bash
# 1. Audit tests/helpers/mocks.py
# 2. Move unique factories to conftest.py
# 3. Replace inline patches in test_api_e2e.py
# 4. Delete tests/helpers/mocks.py
# 5. Verify
pytest
```

---

## Verification Checklist

```bash
# Backend
pytest                                              # All tests green
ruff check backend/src/                             # No lint issues
wc -l backend/src/services/github_projects/*.py     # All < 800 LOC
grep -rn "_get_repository_info" backend/            # 0 results
grep -rn "if not.*selected_project_id" backend/src/api/  # 0 results

# Frontend
cd frontend
npm run test                                        # All tests green
npm run lint                                        # No lint issues
npm run type-check                                  # No type errors

# Integration
docker compose up -d
curl http://localhost:8000/api/v1/health            # 200 OK
```
