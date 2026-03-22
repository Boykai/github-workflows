# Quickstart: Bug Basher — Full Codebase Review & Fix

**Feature**: 001-bug-basher
**Date**: 2026-03-22

## Overview

This guide walks through the complete bug-bash workflow: environment setup, category-by-category audit execution, fix validation, and summary generation. The process audits all ~550 source files across five priority-ordered bug categories.

## Prerequisites

- Python 3.13+ with pip (backend)
- Node.js 18+ with npm (frontend)
- Repository cloned with `solune/backend` and `solune/frontend` accessible
- Git for version control (commits per fix)

## Environment Setup

### Backend

```bash
cd solune/backend
pip install -e ".[dev]"

# Verify all existing tests pass before starting
pytest --timeout=60

# Verify lint and type checks pass
ruff check src tests
pyright src
bandit -r src/
```

### Frontend

```bash
cd solune/frontend
npm install

# Verify all existing tests pass before starting
npm run test
npm run lint
npm run type-check
npm run build
```

## Phase 1 — Security Vulnerability Audit (P1)

### Step 1: Run automated security scanning

```bash
# Backend: Run Bandit security linter
cd solune/backend
bandit -r src/ -f json -o /tmp/bandit-report.json
bandit -r src/  # Human-readable output

# Frontend: ESLint security plugin (already configured)
cd solune/frontend
npm run lint 2>&1 | grep -i "security"
```

### Step 2: Manual audit — Authentication & Authorization

Review all files in these directories for auth bypass risks:
- `solune/backend/src/middleware/` — request middleware, CORS, auth
- `solune/backend/src/api/` — route handlers with auth decorators
- `solune/backend/src/dependencies.py` — FastAPI dependency injection for auth

**Check for**: Missing auth checks on endpoints, permissive CORS, token validation bypasses.

### Step 3: Manual audit — Input Validation & Injection

Review all API route handlers for injection risks:
- SQL injection via raw queries (check aiosqlite usage)
- Command injection via `subprocess`, `os.system`, `eval()`
- Path traversal via unsanitized file paths

```bash
# Find potential injection points
cd solune/backend
grep -rn "execute\|executemany\|os\.system\|subprocess\|eval(" src/
```

### Step 4: Scan for exposed secrets

```bash
# Check for hardcoded secrets, tokens, passwords
grep -rn "password\|secret\|token\|api_key\|apikey" solune/ --include="*.py" --include="*.ts" --include="*.tsx" -i | grep -v "test" | grep -v "node_modules" | grep -v ".git"
```

### Step 5: Fix and test

For each security issue found:
1. Fix the vulnerability in the source code
2. Add a regression test that would catch the vulnerability if reintroduced
3. Verify: `pytest --timeout=60 && ruff check src tests`
4. Commit: `git commit -m "fix(security): {what} — {why} — {how}"`

## Phase 2 — Runtime Error Elimination (P1)

### Step 1: Type checking

```bash
# Backend type errors
cd solune/backend
pyright src  # Review all errors and warnings

# Frontend type errors
cd solune/frontend
npm run type-check  # tsc --noEmit
```

### Step 2: Exception handling audit

```bash
# Find bare except clauses (Python)
cd solune/backend
grep -rn "except:" src/ | grep -v "except Exception"

# Find empty catch blocks (TypeScript)
cd solune/frontend
grep -rn "catch.*{" src/ -A 1 | grep -B 1 "}"
```

### Step 3: Resource management audit

```bash
# Find file handle usage without context managers
cd solune/backend
grep -rn "open(" src/ | grep -v "with "

# Find DB connections that may leak
grep -rn "aiosqlite\|connect(" src/ | grep -v "async with"
```

### Step 4: Fix and test

For each runtime error found:
1. Fix with proper error handling / resource management
2. Add regression test
3. Verify: `pytest --timeout=60`
4. Commit: `git commit -m "fix(runtime): {what} — {why} — {how}"`

## Phase 3 — Logic Bug Resolution (P2)

### Step 1: State machine & workflow audit

Review `solune/backend/src/services/workflow_orchestrator/` for:
- Invalid state transitions
- Missing transition guards
- Incorrect state persistence

### Step 2: Boundary condition check

```bash
# Find loop/index patterns
cd solune/backend
grep -rn "range(\|for.*in\|\[.*:\|\.index(" src/
```

### Step 3: Fix and test

For each logic bug:
1. Fix the logic error
2. Add regression test covering the boundary/edge case
3. Verify: `pytest --timeout=60`
4. Commit: `git commit -m "fix(logic): {what} — {why} — {how}"`

## Phase 4 — Test Quality Improvement (P2)

### Step 1: Audit mock usage

```bash
# Find MagicMock usage that might leak into production paths
cd solune/backend
grep -rn "MagicMock\|patch\|mock" tests/ | grep -v "import" | head -50

# Find mocks used as database paths or file paths
grep -rn "MagicMock" tests/ -A 3 | grep -i "path\|file\|db\|database"
```

### Step 2: Find tautological assertions

```bash
# Assertions that always pass
grep -rn "assert True\|assertEqual.*==.*==\|assert 1" tests/

# Tests with no assertions
grep -L "assert\|expect(" tests/unit/test_*.py
```

### Step 3: Check coverage gaps

```bash
# Backend coverage report
cd solune/backend
pytest --cov=src --cov-report=term-missing --timeout=60 | grep "MISS"

# Frontend coverage report
cd solune/frontend
npm run test:coverage
```

### Step 4: Fix and test

For each test quality issue:
1. Fix the test (remove mock leak, replace tautological assertion, add coverage)
2. Verify the fixed test actually catches regressions
3. Commit: `git commit -m "fix(test-quality): {what} — {why} — {how}"`

## Phase 5 — Code Quality Cleanup (P3)

### Step 1: Dead code detection

```bash
# Unused imports (Python)
cd solune/backend
ruff check src --select F401

# Unused variables (Python)
ruff check src --select F841

# Frontend lint
cd solune/frontend
npm run lint
```

### Step 2: Silent failure detection

```bash
# Find silent exception handling
cd solune/backend
grep -rn "except.*:\s*$" src/ -A 1 | grep "pass"
grep -rn "except.*:" src/ -A 2 | grep -v "log\|raise\|return\|print"
```

### Step 3: Fix and test

For each code quality issue:
1. Remove dead code or add proper error handling
2. Verify existing tests still pass
3. Commit: `git commit -m "fix(quality): {what} — {why} — {how}"`

## Phase 6 — Final Validation

### Full validation pipeline

```bash
# Backend
cd solune/backend
pytest --timeout=60
ruff check src tests
pyright src
bandit -r src/

# Frontend
cd solune/frontend
npm run test
npm run lint
npm run type-check
npm run build
```

### Generate summary table

After all fixes pass validation, compile the summary table:

```markdown
| # | File | Line(s) | Category | Description | Status |
|---|------|---------|----------|-------------|--------|
| 1 | `path/to/file.py` | 42-45 | Security | Description of bug | ✅ Fixed |
| 2 | `path/to/file.py` | 100 | Logic | Description of ambiguity | ⚠️ Flagged (TODO) |
```

### Verify TODO(bug-bash) comments

```bash
# List all flagged items
grep -rn "TODO(bug-bash)" solune/
```

## Full Verification Checklist

1. ✅ `pytest --timeout=60` — all backend tests pass (including new regression tests)
2. ✅ `ruff check src tests` — no lint errors
3. ✅ `pyright src` — no type errors
4. ✅ `bandit -r src/` — no security issues
5. ✅ `npm run test` — all frontend tests pass
6. ✅ `npm run lint` — no ESLint errors
7. ✅ `npm run type-check` — no TypeScript errors
8. ✅ `npm run build` — successful build
9. ✅ Summary table includes every finding with correct status
10. ✅ Every `TODO(bug-bash)` comment includes description, options, and rationale
11. ✅ No changes to public API surface or architecture
12. ✅ No new dependencies added
13. ✅ Each commit message explains what, why, and how
