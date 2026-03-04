# Quickstart: Bug Basher — Full Codebase Review & Fix

**Feature**: 001-bug-basher | **Date**: 2026-03-04

## Prerequisites

- Python ≥3.11 with pip
- Node.js ≥18 with npm
- Git (repository checked out on a feature branch)

## Setup

```bash
# Navigate to repository root
cd /path/to/github-workflows

# Install backend dependencies
cd backend
pip install -e ".[dev]"

# Install frontend dependencies
cd ../frontend
npm install
```

## Validation Commands

### Backend

```bash
cd backend

# Lint and format check
ruff check src tests
ruff format --check src tests

# Type check
pyright

# Run all unit tests (individually to prevent hanging)
for f in tests/unit/test_*.py; do
  timeout 30 python -m pytest "$f" -q
done

# Run a single test file
timeout 30 python -m pytest tests/unit/test_api_auth.py -q

# Run integration tests
timeout 30 python -m pytest tests/integration/ -q
```

### Frontend

```bash
cd frontend

# Lint
npx eslint .

# Type check
npx tsc --noEmit

# Run all tests
npx vitest run

# Run a specific test file
npx vitest run src/components/auth/LoginButton.test.tsx
```

## Bug Bash Execution Order

Execute the audit in this order, completing each category before moving to the next:

### Phase 1: Security Vulnerabilities (P1)
1. Audit `backend/src/api/` — auth endpoints, input validation
2. Audit `backend/src/services/github_auth.py` — OAuth flow, token handling
3. Audit `backend/src/services/encryption.py` — key management, crypto
4. Audit `backend/src/config.py` — secrets, defaults
5. Audit `backend/src/dependencies.py` — auth dependency injection
6. Audit `frontend/src/services/` — token storage, API calls
7. Audit `frontend/src/hooks/useAuth.ts` — auth state management
8. Run full test suite after all P1 fixes

### Phase 2: Runtime Errors (P2)
1. Audit `backend/src/services/` — exception handling, resource management
2. Audit `backend/src/api/` — error responses, null safety
3. Audit `backend/src/services/copilot_polling/` — async errors, race conditions
4. Audit `frontend/src/hooks/` — state management, async operations
5. Audit `frontend/src/components/` — error boundaries, null rendering
6. Run full test suite after all P2 fixes

### Phase 3: Logic Bugs (P3)
1. Audit `backend/src/services/workflow_orchestrator/` — state transitions
2. Audit `backend/src/services/` — business logic, data consistency
3. Audit `backend/src/api/` — request handling logic, pagination
4. Audit `frontend/src/hooks/` — data fetching logic, mutations
5. Audit `frontend/src/components/` — UI logic, event handlers
6. Run full test suite after all P3 fixes

### Phase 4: Test Quality (P4)
1. Audit `backend/tests/unit/` — mock quality, assertion strength
2. Audit `backend/tests/helpers/` — factory and mock correctness
3. Audit `frontend/src/**/*.test.*` — component test quality
4. Run full test suite after all P4 fixes

### Phase 5: Code Quality (P5)
1. Audit `backend/src/` — dead code, duplication, hardcoded values
2. Audit `frontend/src/` — dead code, duplication, hardcoded values
3. Run full test suite and lint after all P5 fixes

## Output

After completing all phases, produce the summary table:

```markdown
| # | File | Line(s) | Category | Description | Status |
|---|------|---------|----------|-------------|--------|
| 1 | `path/to/file.py` | 42-45 | Security | Description | ✅ Fixed |
| 2 | `path/to/file.ts` | 100 | Logic | Description | ⚠️ Flagged (TODO) |
```

## Constraints Reminder

- ❌ No architecture or public API changes
- ❌ No new dependencies
- ❌ No drive-by refactors
- ✅ Minimal, focused fixes only
- ✅ At least one regression test per fix
- ✅ All tests and lint must pass before committing
