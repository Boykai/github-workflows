# Quickstart: Bug Basher — Full Codebase Review & Fix

**Feature**: `031-bug-basher` | **Date**: 2026-03-08

## Prerequisites

- Python >=3.12 installed
- Node.js (for frontend)
- Repository cloned and on the working branch

## Setup

### Backend

```bash
cd backend
pip install -e ".[dev]"
```

### Frontend

```bash
cd frontend
npm install
```

## Running Tests (Validation)

### Backend Tests

```bash
cd backend
python -m pytest tests/unit/ -v --tb=short
```

### Frontend Tests

```bash
cd frontend
npx vitest run
```

### Backend Linting

```bash
cd backend
ruff check src/ tests/
```

### Frontend Linting & Type Check

```bash
cd frontend
npx eslint src/
npx tsc --noEmit
```

## Bug Bash Workflow

### Step 1: Audit Files by Priority Category

Review files in this order:

1. **Security (P1)**: Focus on `backend/src/api/` (auth, input validation), `backend/src/config.py` (secrets), `backend/src/services/encryption.py`, `backend/src/main.py` (CORS, middleware)
2. **Runtime (P2)**: Focus on `backend/src/services/` (exception handling, resource management), `backend/src/main.py` (lifespan, startup/shutdown), `backend/src/services/database.py` (migrations, connections)
3. **Logic (P3)**: Focus on `backend/src/services/workflow_orchestrator/` (state transitions), `backend/src/services/github_projects/` (API calls), `backend/src/services/agents/` (method naming, preferences)
4. **Test Quality (P4)**: Focus on `backend/tests/unit/` (53 test files — mock leaks, tautological assertions), `frontend/src/**/*.test.*` (coverage gaps)
5. **Code Quality (P5)**: Dead imports, unreachable branches, silent failures across all files
6. **Ambiguous Flagging (P6)**: Record `TODO(bug-bash):` comments for issues requiring human trade-off decisions

### Step 2: For Each Bug Found

**If clear bug:**
```bash
# 1. Fix the bug in source code
# 2. Update affected tests
# 3. Add regression test
# 4. Run tests to verify
cd backend && python -m pytest tests/unit/ -v --tb=short
cd frontend && npx vitest run
# 5. Commit with descriptive message
```

**If ambiguous/trade-off:**
```python
# Add TODO comment at the relevant location:
# TODO(bug-bash): <description>. Options: (1) <option A>, (2) <option B>.
# Human decision needed: <rationale>.
```

### Step 3: Validate

```bash
# Run full backend test suite
cd backend && python -m pytest tests/unit/ -v --tb=short

# Run backend linting
cd backend && ruff check src/ tests/

# Run full frontend test suite
cd frontend && npx vitest run

# Run frontend type check
cd frontend && npx tsc --noEmit
```

### Step 4: Generate Summary Table

Create the output summary table following the format in `contracts/summary-table.md`.

## Known Issues (from Research)

| ID | Issue | Approach |
|----|-------|----------|
| R-001 | Migration numbering conflicts (013, 014, 015 duplicates) | Flag as TODO — requires deployment strategy |
| R-002 | Signal chat error message leakage (3 locations) | Verify existing TODOs from previous bug bash |
| R-003 | Temp file accumulation in chat upload | Fix with cleanup after file processing |
| R-004 | CORS allow_methods/allow_headers wildcards | Verify existing TODO from previous bug bash |

## Existing TODO(bug-bash) Comments

The following `TODO(bug-bash):` comments were added by the previous bug bash (030) and should be verified for accuracy during this review:

| File | Lines | Issue |
|------|-------|-------|
| `backend/src/services/signal_chat.py` | 175–179 | Raw exception sent for #agent command errors |
| `backend/src/services/signal_chat.py` | 538–541 | Truncated exception sent for CONFIRM errors |
| `backend/src/services/signal_chat.py` | 818–824 | Truncated exception sent for main pipeline errors |
| `backend/src/main.py` | 388–394 | CORS wildcard methods/headers |
| `backend/src/services/database.py` | 213–221 | Migration numbering duplicates |
