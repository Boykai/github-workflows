# Quickstart: Bug Basher — Full Codebase Review & Fix

**Feature**: 001-bug-basher | **Date**: 2026-03-26 | **Phase**: 1 (Design & Contracts)

## Prerequisites

- Python 3.12+ installed
- Node.js 18+ and npm installed
- Repository cloned and on the feature branch

## Environment Setup

### Backend

```bash
cd solune/backend
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### Frontend

```bash
cd solune/frontend
npm ci
```

## Validation Commands

### Backend — Full CI Pipeline

```bash
cd solune/backend
source .venv/bin/activate

# 1. Lint
ruff check src tests

# 2. Format
ruff format --check src tests

# 3. Security scan
bandit -r src/ -ll -ii --skip B104,B608

# 4. Type check
pyright src

# 5. Tests with coverage
pytest --cov=src --cov-report=term-missing \
  --ignore=tests/property \
  --ignore=tests/fuzz \
  --ignore=tests/chaos \
  --ignore=tests/concurrency
```

### Frontend — Full CI Pipeline

```bash
cd solune/frontend

# 1. Lint
npm run lint

# 2. Type check
npm run type-check

# 3. Tests
npm run test

# 4. Build
npm run build
```

## Execution Phases

### Phase 1: Security Vulnerabilities (P1)

**Review targets** (in order):
1. `solune/backend/src/services/github_auth.py` — Authentication logic
2. `solune/backend/src/services/session_store.py` — Session management
3. `solune/backend/src/services/encryption.py` — Encryption handling
4. `solune/backend/src/middleware/admin_guard.py` — Admin access control
5. `solune/backend/src/middleware/csrf.py` — CSRF protection
6. `solune/backend/src/middleware/csp.py` — Content Security Policy
7. `solune/backend/src/middleware/rate_limit.py` — Rate limiting
8. `solune/backend/src/config.py` — Configuration and secrets
9. `solune/backend/src/api/auth.py` — Auth API routes
10. `solune/backend/src/api/webhooks.py` — Webhook handlers
11. All remaining API routes — Input validation via Pydantic
12. All frontend files — XSS, token handling, sensitive data exposure

**After fixes**: Run full backend + frontend validation.

### Phase 2: Runtime Errors (P2)

**Review targets**:
1. All service files (`solune/backend/src/services/`) — Exception handling patterns, `handle_service_error()` usage
2. Database operations (`database.py`, `chat_store.py`, `settings_store.py`, `session_store.py`) — Resource management
3. External API calls (`httpx`, `githubkit` usage) — Timeout handling, error propagation
4. Frontend hooks and services — Null checks, error boundaries, async error handling

**After fixes**: Run full backend + frontend validation.

### Phase 3: Logic Bugs (P3)

**Review targets**:
1. State machines and workflows (`workflow_orchestrator/`, `pipelines/`) — State transitions
2. API response construction — Correct return values and status codes
3. Data transformation logic (`models/`, `services/`) — Off-by-one, boundary conditions
4. Frontend state management (`context/`, `hooks/`) — State consistency

**After fixes**: Run full backend + frontend validation.

### Phase 4: Test Quality (P4)

**Review targets**:
1. All backend test files (`solune/backend/tests/`) — Mock isolation, assertion quality
2. All frontend test files (`solune/frontend/src/**/*.test.*`) — Mock leaks, assertion effectiveness
3. Cross-reference: service files without corresponding test files

**After fixes**: Run full backend + frontend validation.

### Phase 5: Code Quality (P5)

**Review targets**:
1. All source files — Dead code, unreachable branches
2. Service files — Duplicated logic, hardcoded values
3. Error handling — Silent failures, empty except blocks

**After fixes**: Run full backend + frontend validation.

## Output

After all phases, produce the summary table as specified in `contracts/process-contracts.md` (Contract 3).
