# Quickstart: Bug Basher — Full Codebase Review & Fix

**Feature**: `030-bug-basher` | **Date**: 2026-03-08

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
python -m pytest tests/unit/ -v
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

1. **Security** (P1): Focus on `backend/src/api/` (auth, input validation), `backend/src/config.py` (secrets), `backend/src/services/encryption.py`
2. **Runtime + Logic** (P2): Focus on `backend/src/services/` (exception handling, resource management), `backend/src/main.py` (lifespan, middleware), `backend/src/services/database.py` (migrations), `backend/src/services/agents/service.py` (method calls), and business logic across services
3. **Test Quality** (P3): Focus on `backend/tests/unit/` (mock leaks, assertion quality), `frontend/src/**/*.test.*` (coverage gaps)
4. **Code Quality** (P4): Focus on dead imports, unreachable branches, silent failures across all files
5. **Ambiguous Flagging** (P5): Record `TODO(bug-bash):` comments for issues that require a human trade-off decision instead of an immediate code change

### Step 2: For Each Bug Found

**If clear bug:**
```bash
# 1. Fix the bug in source code
# 2. Update affected tests
# 3. Add regression test
# 4. Run tests to verify
cd backend && python -m pytest tests/unit/ -v
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
cd backend && python -m pytest tests/unit/ -v

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
| R-002 | Signal chat error message leakage | Already flagged — verify existing TODOs |
| R-003 | Temp file accumulation in chat upload | Fix with cleanup |
| R-004 | CORS allow_methods/allow_headers wildcards | Flag as TODO |
