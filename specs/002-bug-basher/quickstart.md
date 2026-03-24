# Quickstart: Bug Basher — Full Codebase Review & Fix

**Feature**: 002-bug-basher
**Date**: 2026-03-24

## Overview

This guide covers the step-by-step process for conducting the bug bash code review across the entire Solune platform codebase. The review is organized in five phases matching the bug category priorities.

## Prerequisites

- Python 3.12+ with `uv` package manager (backend)
- Node.js 18+ and npm (frontend)
- Repository cloned with `solune/backend` and `solune/frontend` accessible
- Existing test suite passing before starting (baseline verification)

## Baseline Verification

Before starting the review, verify the codebase is in a known-good state:

```bash
# Backend — install deps and run tests
cd solune/backend
uv sync --dev
uv run pytest tests/ -x --timeout=30

# Backend — run linting
uv run ruff check src/ tests/
uv run ruff format --check src/ tests/

# Frontend — install deps and run tests
cd ../frontend
npm ci
npm run lint
npm run type-check
npm run test
```

Document any pre-existing failures — these are not the responsibility of the bug bash.

## Phase 1 — Security Vulnerability Audit (P1)

### Step 1: Run automated security tools

```bash
cd solune/backend

# Static security analysis
uv run bandit -r src/ -ll -ii

# Dependency vulnerability audit
uv run pip-audit

cd ../frontend

# Dependency vulnerability audit
npm audit --audit-level=high
```

### Step 2: Manual security review

Review the following critical paths manually:

1. **Authentication**: `src/api/auth.py`, `src/services/github_auth.py`
   - OAuth state parameter validation
   - Redirect URI validation
   - Token storage and expiration
   - Session management

2. **Authorization**: `src/middleware/admin_guard.py`, `src/middleware/csrf.py`
   - CSRF token generation and validation
   - Admin guard bypass scenarios
   - Rate limiting effectiveness

3. **Secrets management**: `src/config.py`, `src/services/encryption.py`
   - No hardcoded secrets in source
   - Encryption key management
   - Environment variable handling

4. **Input validation**: All `src/api/*.py` route handlers
   - Path parameter validation
   - Request body validation via Pydantic models
   - SQL injection prevention (parameterized queries)

5. **Frontend security**: React components
   - XSS prevention in markdown rendering
   - URL validation in links
   - No `dangerouslySetInnerHTML` with unsanitized content

### Step 3: Fix and test

For each security issue found:

```bash
# Fix the bug, then add regression test, then verify
cd solune/backend
uv run pytest tests/ -x --timeout=30
uv run ruff check src/ tests/
uv run bandit -r src/ -ll -ii
```

## Phase 2 — Runtime Error and Logic Bug Resolution (P2)

### Step 1: Audit exception handling

```bash
# Find bare except clauses
cd solune/backend
grep -rn "except:" src/ --include="*.py"

# Find broad exception catches
grep -rn "except Exception" src/ --include="*.py"

# Find potential None/null reference issues
grep -rn "\.get(" src/ --include="*.py" | head -50
```

### Step 2: Audit resource management

Review all database and file operations for proper cleanup:

- `src/services/database.py` — connection lifecycle
- All `async with` patterns for aiosqlite
- WebSocket cleanup in `src/services/websocket.py`
- File handle management in `src/services/template_files.py`

### Step 3: Audit state transitions

Review state machines and control flow:

- `src/services/workflow_orchestrator/` — workflow state transitions
- `src/services/copilot_polling/` — polling state management
- `src/services/pipelines/` — pipeline execution flow

### Step 4: Fix and test

```bash
cd solune/backend
uv run pytest tests/ -x --timeout=30
uv run ruff check src/ tests/
```

## Phase 3 — Test Quality Improvement (P3)

### Step 1: Detect mock leaks

```bash
cd solune/backend

# Find MagicMock without spec parameter
grep -rn "MagicMock()" tests/ --include="*.py"

# Find mocks used as file paths
grep -rn "mock.*path\|mock.*file\|mock.*db" tests/ --include="*.py"
```

### Step 2: Find dead assertions

```bash
# Find assertions on constants (always true)
grep -rn "assert True\|assert 1\|assert \"" tests/ --include="*.py"

# Find assertions that check type instead of value
grep -rn "assert isinstance" tests/ --include="*.py"
```

### Step 3: Run coverage analysis

```bash
cd solune/backend
uv run pytest tests/unit/ --cov=src --cov-report=term-missing --timeout=30

# Identify files with low coverage
# Focus on files modified in Phases 1-2
```

### Step 4: Fix and verify

```bash
cd solune/backend
uv run pytest tests/ -x --timeout=30
```

## Phase 4 — Code Quality Cleanup (P4)

### Step 1: Run linting tools

```bash
cd solune/backend

# Full lint check
uv run ruff check src/ tests/

# Type checking
uv run pyright src/

cd ../frontend

# ESLint
npm run lint

# TypeScript type check
npm run type-check
```

### Step 2: Find dead code

```bash
cd solune/backend

# Find unused imports (ruff handles this with F401)
uv run ruff check src/ --select F401

# Find unreachable code
uv run ruff check src/ --select F811,F841
```

### Step 3: Find silent failures

```bash
cd solune/backend

# Find bare except: pass patterns
grep -rn "except.*:" src/ -A1 --include="*.py" | grep -B1 "pass$"

# Find empty exception handlers
grep -rn "except.*:" src/ -A1 --include="*.py" | grep -B1 "^\s*$"
```

### Step 4: Fix and verify

```bash
cd solune/backend
uv run ruff check src/ tests/
uv run pytest tests/ -x --timeout=30

cd ../frontend
npm run lint
npm run test
```

## Phase 5 — Summary Report

### Step 1: Compile findings

Create a summary table in the required format:

```markdown
| # | File | Line(s) | Category | Description | Status |
|---|------|---------|----------|-------------|--------|
| 1 | `path/to/file.py` | 42-45 | Security | Description | ✅ Fixed |
| 2 | `path/to/file.py` | 100 | Logic | Description | ⚠️ Flagged (TODO) |
```

### Step 2: Final validation

```bash
# Full backend test suite
cd solune/backend
uv run pytest tests/ --timeout=30

# Full backend lint suite
uv run ruff check src/ tests/
uv run ruff format --check src/ tests/
uv run pyright src/
uv run bandit -r src/ -ll -ii

# Full frontend test suite
cd ../frontend
npm run lint
npm run type-check
npm run test
```

### Step 3: Verify constraints

- [ ] No architecture changes
- [ ] No public API surface changes
- [ ] No new dependencies added
- [ ] Existing code style preserved
- [ ] Each fix is minimal and focused
- [ ] Files with no bugs not mentioned in summary

## Full Verification Checklist

1. ✅ All security tools pass clean (`bandit`, `pip-audit`, `npm audit`)
2. ✅ No secrets or tokens in source code
3. ✅ All regression tests pass
4. ✅ Full `pytest` suite passes
5. ✅ Full `vitest` suite passes
6. ✅ `ruff check` and `ruff format --check` pass
7. ✅ `pyright` passes
8. ✅ `eslint` passes
9. ✅ `tsc --noEmit` passes
10. ✅ Summary report includes all findings
11. ✅ Each ✅ Fixed item has a regression test
12. ✅ Each ⚠️ Flagged item has a `TODO(bug-bash)` comment in source
