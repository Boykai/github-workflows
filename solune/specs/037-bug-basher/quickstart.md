# Quickstart: Bug Basher — Full Codebase Review & Fix

**Feature**: 037-bug-basher | **Date**: 2026-03-12

## Overview

This feature performs a comprehensive bug bash code review across the entire codebase — both Python backend and TypeScript frontend. The review identifies bugs across five priority categories (security, runtime, logic, test quality, code quality), applies minimal fixes with regression tests, and produces a summary table of all findings.

## Prerequisites

### Backend Environment

```bash
cd backend
pip install -e ".[dev]"

# Verify existing tests pass
python -m pytest tests/unit/ -v
# Expected: ~1736 tests pass

# Verify linting passes
python -m ruff check src/
```

### Frontend Environment

```bash
cd frontend
npm install

# Verify existing tests pass
npx vitest run
# Expected: ~644 tests pass

# Verify type checking passes
npm run type-check

# Verify linting passes
npm run lint
```

## Execution Workflow

### Step 1: Establish Baseline

Before making any changes, run the full test suite and linting to document pre-existing state:

```bash
# Backend baseline
cd backend
python -m pytest tests/unit/ -v --tb=short 2>&1 | tail -5
python -m ruff check src/ 2>&1 | tail -5

# Frontend baseline
cd frontend
npx vitest run 2>&1 | tail -5
npm run type-check 2>&1 | tail -5
npm run lint 2>&1 | tail -5
```

Document any pre-existing failures — these are not part of the bug bash scope.

### Step 2: Security Review (P1)

Review all files for security vulnerabilities in this order:

1. **Secrets scan**: Search for hardcoded API keys, tokens, passwords in source code
   ```bash
   # Backend
   grep -rn "password\|secret\|token\|api_key\|apikey" backend/src/ --include="*.py" | grep -v "test" | grep -v "__pycache__"
   
   # Frontend
   grep -rn "password\|secret\|token\|api_key\|apikey" frontend/src/ --include="*.ts" --include="*.tsx" | grep -v "test" | grep -v "node_modules"
   ```

2. **Input validation**: Review API endpoints for unvalidated user input
3. **Auth checks**: Review middleware and route guards for bypass risks
4. **Insecure defaults**: Check configuration files for debug/dev settings in production paths

### Step 3: Runtime Error Review (P2)

1. **Unhandled exceptions**: Search for `async` functions without try/except
2. **Null references**: Check for attribute access without null guards
3. **Resource leaks**: Verify file handles and DB connections are properly closed
4. **Missing imports**: Run the application and check for ImportError

### Step 4: Logic Bug Review (P3)

1. **State transitions**: Review `workflow_orchestrator/` state machine logic
2. **Boundary conditions**: Check loop bounds and off-by-one patterns
3. **Return values**: Verify functions return expected types and values
4. **API integration**: Check GitHub API call parameters and response handling

### Step 5: Test Quality Review (P4)

1. **Weak assertions**: Find `assert True`, `assert mock_obj`, or assertions that always pass
2. **Mock leaks**: Search for `MagicMock` objects used as production values
3. **Missing coverage**: Identify critical paths without test coverage
4. **Test isolation**: Check for shared mutable state between tests

### Step 6: Code Quality Review (P5)

1. **Dead code**: Find functions/classes never referenced
2. **Duplication**: Identify copy-pasted logic blocks
3. **Silent failures**: Find empty `except` blocks or swallowed errors
4. **Hardcoded values**: Find values that should be configurable

### Step 7: Validate All Fixes

```bash
# Backend validation
cd backend
python -m pytest tests/unit/ -v
python -m ruff check src/

# Frontend validation
cd frontend
npx vitest run
npm run type-check
npm run lint
```

All tests must pass. All linting must pass without new violations.

### Step 8: Generate Summary Table

Compile all findings into the summary table format:

```markdown
| # | File | Line(s) | Category | Description | Status |
|---|------|---------|----------|-------------|--------|
```

## Key Rules

- **No architecture changes** (FR-009)
- **No new dependencies** (FR-010)
- **Preserve existing code style** (FR-011)
- **Minimal, focused fixes only** (FR-012)
- **One regression test per fix minimum** (FR-003)
- **`TODO(bug-bash)` for ambiguous issues** (FR-005)
- **Full test suite must pass after all fixes** (FR-006)

## Architecture Reference

```text
┌─────────────────────────────────────────────────────┐
│                   Bug Bash Workflow                  │
│                                                     │
│  ┌──────────┐   ┌───────────┐   ┌──────────────┐  │
│  │ Baseline │──▶│  Review   │──▶│   Fix/Flag   │  │
│  │  Check   │   │ (P1→P5)  │   │  Per Bug     │  │
│  └──────────┘   └───────────┘   └──────┬───────┘  │
│                                         │          │
│                      ┌──────────────────┼────────┐ │
│                      ▼                  ▼        │ │
│              ┌──────────────┐   ┌────────────┐   │ │
│              │ ✅ Fixed     │   │ ⚠️ Flagged │   │ │
│              │ + Regression │   │ + TODO     │   │ │
│              │   Test       │   │   Comment  │   │ │
│              └──────┬───────┘   └─────┬──────┘   │ │
│                     │                 │          │ │
│                     └────────┬────────┘          │ │
│                              ▼                   │ │
│                     ┌──────────────┐             │ │
│                     │  Validate    │             │ │
│                     │  (pytest +   │             │ │
│                     │   vitest +   │             │ │
│                     │   lint)      │             │ │
│                     └──────┬───────┘             │ │
│                            ▼                     │ │
│                     ┌──────────────┐             │ │
│                     │  Summary     │             │ │
│                     │  Table       │             │ │
│                     └──────────────┘             │ │
└─────────────────────────────────────────────────────┘
```
