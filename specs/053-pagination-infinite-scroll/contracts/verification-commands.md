# Contracts: Verification Commands

**Feature Branch**: `053-pagination-infinite-scroll`
**Date**: 2026-03-20

## Verification Command Reference

This document provides the complete set of commands to verify each phase of the
Pagination & Infinite Scroll feature. All commands are run from the repository root
(the directory containing `solune/`).

### Phase A: Backend Pagination Foundation

```bash
# Unit tests for pagination utility
cd solune/backend && \
  .venv/bin/python -m pytest tests/unit/test_pagination.py -v --tb=short

# Type-check pagination models
cd solune/backend && \
  .venv/bin/pyright src/models/pagination.py src/services/pagination.py
```

### Phase B: Backend Endpoint Migration

```bash
# Test individual endpoint with pagination params
# Agents endpoint
curl -s "http://localhost:8000/api/v1/agents/{project_id}?limit=5" | python -m json.tool

# Verify backward compatibility (no pagination params returns full list)
curl -s "http://localhost:8000/api/v1/agents/{project_id}" | python -m json.tool

# Board endpoint with per-column pagination
curl -s 'http://localhost:8000/api/v1/board/data/{project_id}?column_limit=10' | python -m json.tool

# Run backend tests (expect all pass)
cd solune/backend && \
  .venv/bin/python -m pytest tests/ -q --tb=short

# Backend lint (expect zero violations)
cd solune/backend && \
  .venv/bin/ruff check src/

# Backend type-check (expect zero errors)
cd solune/backend && \
  .venv/bin/pyright src/
```

### Phase C: Frontend Shared Infrastructure

```bash
# Frontend type-check (expect zero errors)
cd solune/frontend && \
  npx tsc --noEmit

# Frontend lint (expect zero violations)
cd solune/frontend && \
  npx eslint src/hooks/useInfiniteList.ts src/components/common/InfiniteScrollContainer.tsx

# Run frontend tests
cd solune/frontend && \
  npx vitest run --reporter=verbose
```

### Phase D: Frontend Page Migration

```bash
# Type-check all modified files
cd solune/frontend && \
  npx tsc --noEmit

# Lint all modified hooks and pages
cd solune/frontend && \
  npx eslint \
    src/hooks/useAgents.ts \
    src/hooks/useTools.ts \
    src/hooks/useChores.ts \
    src/hooks/useApps.ts \
    src/hooks/useProjectBoard.ts \
    src/pages/AgentsPage.tsx \
    src/pages/ToolsPage.tsx \
    src/pages/ChoresPage.tsx \
    src/pages/AppsPage.tsx

# Run all frontend tests
cd solune/frontend && \
  npx vitest run
```

### Phase E: Edge Cases and Polish

```bash
# Full frontend test suite (includes edge case tests)
cd solune/frontend && \
  npx vitest run --reporter=verbose

# Full backend test suite
cd solune/backend && \
  .venv/bin/python -m pytest tests/ -q --tb=short
```

### Phase F: Final Verification

```bash
# Complete backend verification
cd solune/backend && \
  .venv/bin/ruff check src/ && \
  .venv/bin/pyright src/ && \
  .venv/bin/python -m pytest tests/ --cov=src --cov-report=term-missing

# Complete frontend verification
cd solune/frontend && \
  npx eslint . --max-warnings=0 && \
  npx tsc --noEmit && \
  npx vitest run

# Performance verification (manual)
# 1. Seed database with 200+ items per list type
# 2. Navigate to each list view
# 3. Measure initial load time (target: < 2s)
# 4. Scroll through all pages, measure per-page load (target: < 1s)
# 5. Verify zero duplicated/skipped items
# 6. Verify drag-and-drop works on paginated board columns
```

## Quick Reference

| Phase | Gate | Command | Expected |
|-------|------|---------|----------|
| A | Pagination unit tests | `pytest tests/unit/test_pagination.py` | All pass |
| B | Backend lint | `ruff check src/` | 0 violations |
| B | Backend types | `pyright src/` | 0 errors |
| B | Backend tests | `pytest tests/ -q` | All pass |
| C | Frontend types | `npx tsc --noEmit` | 0 errors |
| C | Frontend lint | `npx eslint .` | 0 violations |
| D | Frontend tests | `npx vitest run` | All pass |
| F | Initial load time | Manual measurement | < 2s for 200+ items |
| F | Per-page load time | Manual measurement | < 1s |
| F | Zero duplicates | Scroll through full list | 0 duplicated/skipped |
