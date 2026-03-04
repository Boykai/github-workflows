# Quickstart: Bug Basher — Full Codebase Review & Fix

**Feature**: `018-bug-basher` | **Date**: 2026-03-04

## Overview

The Bug Basher is a systematic code review process that audits every file in the repository across five bug categories (security, runtime, logic, test quality, code quality) in priority order. Confirmed bugs are fixed with minimal changes and validated by regression tests. Ambiguous issues are flagged for human review.

## Prerequisites

- Repository cloned locally with write access to the working branch
- Python ≥3.11 with backend dev dependencies installed (`pip install -e ".[dev]"` in `backend/`)
- Node.js with frontend dependencies installed (`npm install` in `frontend/`)
- Familiarity with existing code conventions (see repository memories and `logging_utils.py` patterns)

## Quick Walkthrough

### Phase 1: Security Vulnerabilities (P1)

**Audit scope**:
1. Scan all `backend/src/api/*.py` files for missing authentication/authorization checks
2. Scan all `except` blocks for `str(e)` leaking into API responses
3. Check `.env.example` and config files for exposed secrets or insecure defaults
4. Audit SQL query construction in `backend/src/services/` for injection risks
5. Check frontend components rendering user input for XSS vulnerabilities

**Fix pattern**:
```python
# BEFORE (security bug — raw exception in response)
except Exception as e:
    return JSONResponse(status_code=500, content={"error": str(e)})

# AFTER (fix — static message, log details server-side)
except Exception:
    logger.error("Operation failed", exc_info=True)
    return JSONResponse(status_code=500, content={"error": "Internal server error"})
```

### Phase 2: Runtime Errors (P2)

**Audit scope**:
1. Find `assert` statements in production code paths (`backend/src/`)
2. Check for unhandled exceptions in async code
3. Verify resource cleanup (file handles, DB connections) uses context managers
4. Check for missing imports and type errors

**Fix pattern**:
```python
# BEFORE (runtime bug — assert stripped by python -O)
assert user_id is not None

# AFTER (fix — proper validation)
if user_id is None:
    raise ValueError("user_id is required")
```

### Phase 3: Logic Bugs (P3)

**Audit scope**:
1. Review state transitions in service layer
2. Check return values and control flow in all functions
3. Look for off-by-one errors in loops and slicing
4. Verify API call arguments match expected signatures

### Phase 4: Test Gaps & Quality (P4)

**Audit scope**:
1. Check all test files for proper mock cleanup (`mockRestore()` in `afterEach`)
2. Look for assertions that always pass (e.g., `assert True`, `expect(true).toBe(true)`)
3. Verify mock objects don't leak into production code paths
4. Identify critical code paths with no test coverage

### Phase 5: Code Quality (P5)

**Audit scope**:
1. Find dead code and unreachable branches
2. Look for duplicated logic that should be shared
3. Check for hardcoded values that should be configurable
4. Find silent `except: pass` blocks

## Validation Commands

### Backend

```bash
# Run tests file-by-file (recommended — avoids hanging)
cd backend
timeout 30 python -m pytest tests/unit/test_health.py -q

# Lint and format check
ruff check src tests
ruff format --check src tests

# Type checking
pyright
```

### Frontend

```bash
# Run all tests
cd frontend
npx vitest run

# Type checking
npx tsc --noEmit

# Lint
npx eslint .
```

## Output Format

The final summary table follows this exact format:

| # | File | Line(s) | Category | Description | Status |
|---|------|---------|----------|-------------|--------|
| 1 | `path/to/file.py` | 42-45 | Security | Description of bug | ✅ Fixed |
| 2 | `path/to/file.py` | 100 | Logic | Description of ambiguity | ⚠️ Flagged (TODO) |

## Key Files for Review

### Backend — Highest Priority
- `backend/src/api/*.py` — All API endpoint handlers
- `backend/src/services/**/*.py` — All service layer logic
- `backend/src/logging_utils.py` — Error handling utilities (reference patterns)
- `backend/src/config.py` — Configuration and secrets handling
- `backend/src/utils.py` — Shared utilities
- `backend/src/main.py` — Application lifecycle

### Frontend — Medium Priority
- `frontend/src/hooks/*.ts` — React hooks (state management bugs)
- `frontend/src/services/api.ts` — API client (error handling)
- `frontend/src/components/**/*.tsx` — UI components (logic, XSS)
- `frontend/src/components/**/*.test.tsx` — Test files (mock leaks)

### Configuration — Check Once
- `.env.example` — Exposed secrets
- `docker-compose.yml` — Insecure defaults
- `backend/pyproject.toml` — Dependency versions
- `frontend/package.json` — Dependency versions
