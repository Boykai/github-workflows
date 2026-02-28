# Quickstart: Codebase Cleanup — Remove Dead Code, Backwards Compatibility & Stale Tests

**Feature**: `010-codebase-cleanup-refactor` | **Date**: 2026-02-28

## Prerequisites

- Python 3.11+ with pip
- Node.js 20+ with npm
- Git

## Setup

```bash
# Clone and checkout feature branch
git checkout 010-codebase-cleanup-refactor

# Backend setup
cd backend
pip install -e ".[dev]"

# Frontend setup
cd ../frontend
npm ci
```

## Verification Commands

These commands validate that the cleanup has not introduced regressions:

### Backend

```bash
cd backend

# Lint check (Ruff) — must pass with zero violations
ruff check src/ tests/
ruff format --check src/ tests/

# Type check (Pyright) — must pass with zero errors
pyright

# Run all tests — must pass with zero failures
pytest -v
```

### Frontend

```bash
cd frontend

# Lint check (ESLint) — must pass with zero violations
npm run lint

# Type check (TypeScript) — must pass with zero errors
npm run type-check

# Run all tests — must pass with zero failures
npm test

# Build — must succeed
npm run build
```

## Cleanup Verification Checklist

After each story is completed, verify:

### Story 1 — Backwards Compatibility Removal
```bash
# Verify no backwards compatibility shims remain
grep -rn "legacy\|backward\|compat\|deprecated" backend/src/ --include="*.py" | grep -v "test_\|\.pyc\|__pycache__"
# Review each match — document any intentional retentions
```

### Story 2 — Dead Code Elimination
```bash
# Backend: Check for unused imports
ruff check src/ --select F401

# Frontend: Check for unused type exports
# For each type in the removal list, verify zero imports:
grep -rn "IssueLabel\|PipelineStateInfo\|AgentNotification\|SignalConnectionStatus\|SignalNotificationMode\|SignalLinkStatus" frontend/src/ --include="*.ts" --include="*.tsx"

# Verify silent exception handlers are replaced with logging
grep -rn "except.*:$" backend/src/ --include="*.py" -A1 | grep "pass$"
```

### Story 3 — DRY Consolidation
```bash
# Verify cache pattern consolidated
grep -rn "cache.get\|cache.set" backend/src/api/ --include="*.py"
# Should show reduced occurrences after consolidation

# Verify useAgentConfig deduplication
grep -n "hasAgentOrderChanged\|isDirty\|isColumnDirty" frontend/src/hooks/useAgentConfig.ts
```

### Story 4 — Stale Test Removal
```bash
# Run full test suites to confirm no regressions
cd backend && pytest -v
cd ../frontend && npm test
```

### Story 5 — Best Practices
```bash
# Full lint pass
cd backend && ruff check src/ tests/ && ruff format --check src/ tests/
cd ../frontend && npm run lint && npm run type-check
```

## Delivery Order

Recommended execution order (per spec assumptions):

1. **Story 1** (P1): Remove backwards compatibility code → removes code that might be flagged as dead in Story 2
2. **Story 2** (P1): Eliminate dead code → produces the leanest codebase for consolidation
3. **Story 3** (P2): Consolidate duplicated logic → DRY patterns visible after dead code removal
4. **Story 4** (P2): Remove stale tests → tests for removed code are identified after Stories 1-2
5. **Story 5** (P3): Apply best practices → final polish on the cleaned codebase

Each story is delivered as an atomic commit where all tests pass.
