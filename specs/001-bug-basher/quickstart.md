# Quickstart: Bug Basher — Full Codebase Review & Fix

**Feature**: `001-bug-basher` | **Date**: 2026-03-15 | **Plan**: [plan.md](plan.md)

## Prerequisites

- Git repository cloned with full history
- Python 3.13+ with `uv` package manager
- Node.js 20+ with `npm`
- Access to all files in the repository

## Setup

### Backend Environment

```bash
cd solune/backend
uv sync --dev
```

### Frontend Environment

```bash
cd solune/frontend
npm ci
```

## Running Validation

### Backend Tests & Linting

```bash
cd solune/backend

# Run full test suite
python -m pytest tests/ -v

# Run with coverage
python -m pytest --cov=src --cov-report=term-missing

# Lint check
python -m ruff check src tests

# Format check
python -m ruff format --check src tests

# Type check
python -m pyright src
```

### Frontend Tests & Linting

```bash
cd solune/frontend

# Run unit tests
npm test

# Lint check
npm run lint

# Type check
npm run type-check

# Build verification
npm run build
```

## Bug Bash Workflow

### Step 1: Establish Baseline

Before making any changes, run the full validation suite to document the current state:

```bash
# Backend baseline
cd solune/backend
python -m pytest tests/ -v 2>&1 | tee /tmp/baseline-backend-tests.log
python -m ruff check src tests 2>&1 | tee /tmp/baseline-backend-lint.log

# Frontend baseline
cd solune/frontend
npm test 2>&1 | tee /tmp/baseline-frontend-tests.log
npm run lint 2>&1 | tee /tmp/baseline-frontend-lint.log
```

### Step 2: Audit by Priority

Work through the codebase in priority order:

1. **Security Vulnerabilities** (P1) — Audit all files for auth bypasses, injection risks, exposed secrets, insecure defaults, improper input validation
2. **Runtime Errors** (P2) — Audit for unhandled exceptions, race conditions, null references, missing imports, type errors, resource leaks
3. **Logic Bugs** (P3) — Audit for incorrect state transitions, wrong API calls, off-by-one errors, data inconsistencies
4. **Test Gaps** (P4) — Audit test suite for untested paths, mock leaks, vacuous assertions, missing edge cases
5. **Code Quality** (P5) — Audit for dead code, unreachable branches, duplicated logic, hardcoded values, silent failures

### Step 3: For Each Bug Found

**If the fix is clear:**
```bash
# 1. Fix the bug in source code
# 2. Update any affected existing tests
# 3. Add regression test
# 4. Validate
cd solune/backend && python -m pytest tests/ -v  # or cd solune/frontend && npm test
# 5. Commit with descriptive message
git commit -m "fix(<category>): <description>"
```

**If the fix is ambiguous:**
```python
# Add TODO comment at the relevant location:
# TODO(bug-bash): <description of issue, options, and rationale for deferral>
```

### Step 4: Final Validation

After all fixes are applied:

```bash
# Backend - all checks must pass
cd solune/backend
python -m pytest tests/ -v
python -m ruff check src tests
python -m ruff format --check src tests
python -m pyright src

# Frontend - all checks must pass
cd solune/frontend
npm test
npm run lint
npm run type-check
npm run build
```

### Step 5: Generate Summary

Create the summary table with all bugs found. See [contracts/bug-report-schema.md](contracts/bug-report-schema.md) for the exact format.

## Key Constraints

- **No new dependencies** — do not `pip install`, `npm install`, or add entries to `pyproject.toml`/`package.json`
- **No public API changes** — HTTP endpoints, CLI commands, exported interfaces must remain unchanged
- **No architecture changes** — file structure, module boundaries, and service patterns stay the same
- **Minimal, focused fixes** — one bug per commit, no drive-by refactors
- **Preserve code style** — follow existing patterns (ruff format for Python, Prettier for TypeScript)

## File Audit Order (Recommended)

Start with highest-risk files (services, middleware, auth) and work outward:

1. `solune/backend/src/services/` — Core business logic, database access, encryption
2. `solune/backend/src/middleware/` — Security middleware (admin_guard, CSP, rate limiting)
3. `solune/backend/src/api/` — API route handlers (input validation, error handling)
4. `solune/backend/src/config.py` — Configuration and secrets management
5. `solune/backend/src/main.py` — Application setup, CORS, middleware registration
6. `solune/backend/src/models/` — Pydantic models (validation rules)
7. `solune/backend/tests/` — Test quality review
8. `solune/frontend/src/services/` — API client code
9. `solune/frontend/src/hooks/` — Custom hooks (resource cleanup, error handling)
10. `solune/frontend/src/components/` — UI components (XSS, accessibility)
11. `solune/frontend/src/pages/` — Page components
12. `docker-compose.yml`, `Dockerfile`s — Infrastructure configuration
13. `solune/scripts/` — Development utility scripts
