# Quickstart: Codebase Cleanup & Refactor

**Feature**: `007-codebase-cleanup-refactor` | **Date**: 2026-02-19

## Prerequisites

- Python ≥3.11 with virtual environment (`backend/.venv`)
- Node.js with npm (frontend)
- Docker + Docker Compose (for full-stack testing)

## Development Setup

```bash
# 1. Switch to the feature branch
git checkout 007-codebase-cleanup-refactor

# 2. Backend: activate venv and install dependencies
cd backend
source .venv/bin/activate
pip install -e ".[dev]"

# 3. Frontend: install dependencies
cd ../frontend
npm install
```

## Running Tests (Regression Baseline)

Before making any changes, run the full test suite to establish the baseline:

```bash
# Backend tests
cd backend
pytest tests/ -v

# Frontend tests
cd ../frontend
npm test
```

**All existing tests must pass after every refactoring step (SC-007).**

## Verification Workflow

After each refactoring task, verify:

### 1. Import Resolution
```bash
# Backend: check that all imports resolve
cd backend
python -c "from src.services.github_projects import github_projects_service; print('OK')"
python -c "from src.services.copilot_polling import start_polling, stop_polling; print('OK')"
```

### 2. Full Test Suite
```bash
# Backend
cd backend && pytest tests/ -v

# Frontend
cd ../frontend && npm test
```

### 3. Application Start
```bash
# Via Docker Compose (full stack)
docker compose up --build

# Or backend only
cd backend && uvicorn src.main:app --reload
```

### 4. Lint and Type Check
```bash
# Backend
cd backend
ruff check src/
ruff format --check src/
pyright src/

# Frontend
cd ../frontend
npm run lint
npm run type-check
```

## Key Implementation Order

The refactoring must proceed in dependency order to avoid intermediate breakage:

1. **Shared utilities first** (`services/shared/`) — No existing code depends on these yet
2. **Constants consolidation** — Update `constants.py` and create `constants.ts`
3. **`github_projects` split** — Many modules depend on it; re-export facade ensures compatibility
4. **`copilot_polling` split** — Depends on `github_projects`; split after it
5. **Error handling standardization** — Cross-cutting; do after module splits to avoid conflicts
6. **Frontend changes** — API client, sessionStorage, error boundary, WS/polling unification
7. **New tests** — Written against the refactored code

## Common Pitfalls

- **Circular imports**: When splitting into sub-modules, watch for import cycles. Use late imports or restructure dependencies if needed.
- **Module-level state**: `copilot_polling` has 8 mutable module-level variables. These must stay in `state.py` and be imported by other sub-modules — not duplicated.
- **Re-export completeness**: The `__init__.py` facades must re-export everything that external code imports. Run `grep -r "from.*github_projects import" backend/src/` to find all import sites.
- **Test imports**: Test files may import internal functions. Update these imports to point to new sub-module locations (tests don't need to go through the facade).
