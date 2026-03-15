# Quick Start: Performance Review

**Feature**: 001-performance-review
**Date**: 2026-03-15

## Prerequisites

- Python ≥ 3.12 with pip
- Node.js (for frontend, version per `solune/frontend/.nvmrc` or package.json engines)
- Docker (optional, for running the full stack)
- Access to a GitHub account with a Projects V2 board containing 50–100 tasks across 4–8 columns (for manual verification)

## Project Setup

### Backend

```bash
cd solune/backend

# Install dependencies
pip install -e ".[dev]"

# Run linter
python -m ruff check src/

# Run type checker
python -m pyright src/

# Run all tests
python -m pytest tests/ -v

# Run targeted tests (performance-relevant)
python -m pytest tests/unit/test_cache.py tests/unit/test_api_board.py tests/unit/test_copilot_polling.py -v
```

### Frontend

```bash
cd solune/frontend

# Install dependencies
npm install

# Run linter
npm run lint

# Run type checker
npm run type-check

# Run all tests
npx vitest run

# Run targeted tests (performance-relevant)
npx vitest run src/hooks/useRealTimeSync.test.tsx src/hooks/useBoardRefresh.test.tsx

# Build
npm run build
```

### Full Stack (Docker)

```bash
# From repository root
docker compose up
```

## Development Workflow

### Phase 1: Baseline Capture

Before making any code changes:

1. **Backend idle baseline**:
   ```bash
   # Start the backend, open a board in the browser, and monitor logs
   cd solune/backend
   # Grep for outbound API calls over 5 minutes
   # Count GraphQL/REST requests to GitHub API
   ```

2. **Frontend load baseline**:
   - Open Chrome DevTools → Performance tab
   - Load a board with 50+ tasks
   - Record: time to interactive, render count, network requests

3. **Frontend interaction baseline**:
   - Open React DevTools → Profiler
   - Enable "Highlight updates when components render"
   - Perform: drag card, click card, open task detail
   - Record: rerender count per interaction, interaction latency

4. **Document baselines** in the measurement checklist (part of implementation tasks)

### Phase 2: Backend Optimization

Key files to modify:

| File | Focus Area |
|------|-----------|
| `solune/backend/src/api/projects.py` | WebSocket periodic check — ensure warm cache reuse, suppress unchanged pushes |
| `solune/backend/src/api/board.py` | Verify sub-issue cache reuse on non-manual refresh |
| `solune/backend/src/api/workflow.py` | Consolidate duplicate `resolve_repository()` calls |
| `solune/backend/src/services/cache.py` | No changes expected — already well-implemented |
| `solune/backend/src/services/copilot_polling/polling_loop.py` | No changes expected — adaptive backoff already in place |

### Phase 3: Frontend Optimization

Key files to modify:

| File | Focus Area |
|------|-----------|
| `solune/frontend/src/hooks/useRealTimeSync.ts` | Ensure fallback polling does not over-invalidate |
| `solune/frontend/src/hooks/useBoardRefresh.ts` | Verify refresh policy coherence; no changes expected |
| `solune/frontend/src/pages/ProjectsPage.tsx` | Audit `useMemo` coverage for all derived computations |
| `solune/frontend/src/components/board/BoardColumn.tsx` | Verify `memo()` effectiveness (stable props) |
| `solune/frontend/src/components/board/IssueCard.tsx` | Verify `memo()` effectiveness (stable props) |

### Phase 4: Test Extension

Key test files to extend:

| File | New Assertions |
|------|---------------|
| `solune/backend/tests/unit/test_cache.py` | Warm cache reuse reducing call count |
| `solune/backend/tests/unit/test_api_board.py` | Sub-issue cache reuse on non-manual refresh |
| `solune/backend/tests/unit/test_copilot_polling.py` | Idle-board scenario (minimal changes expected) |
| `solune/frontend/src/hooks/useRealTimeSync.test.tsx` | Verify polling does not over-invalidate |
| `solune/frontend/src/hooks/useBoardRefresh.test.tsx` | Refresh deduplication across simultaneous triggers |

## Verification Checklist

After all changes are complete:

- [ ] All existing backend tests pass: `cd solune/backend && python -m pytest tests/ -v`
- [ ] All existing frontend tests pass: `cd solune/frontend && npx vitest run`
- [ ] Backend linter clean: `cd solune/backend && python -m ruff check src/`
- [ ] Backend type check clean: `cd solune/backend && python -m pyright src/`
- [ ] Frontend linter clean: `cd solune/frontend && npm run lint`
- [ ] Frontend type check clean: `cd solune/frontend && npm run type-check`
- [ ] Frontend build succeeds: `cd solune/frontend && npm run build`
- [ ] Manual: idle board produces ≥ 50% fewer outbound calls (SC-001)
- [ ] Manual: warm cache reduces call count by ≥ 30% (SC-002)
- [ ] Manual: single-task update reflected < 2s without full reload (SC-003)
- [ ] Manual: fallback polling produces zero unnecessary full refreshes (SC-004)
- [ ] Manual: board interactions show measurable improvement on 50+ tasks (SC-005)
- [ ] Manual: single-task update rerenders only affected card + container (SC-006)
- [ ] No new external dependencies introduced (SC-009)

## Key Architecture Notes

- **Cache layer**: `InMemoryCache` in `services/cache.py` with `CacheEntry[T]` supporting TTL, stale fallback, and data hashing
- **Change detection**: SHA-256 content hash via `compute_data_hash()` — deterministic, key-order-independent, excludes rate-limit metadata
- **Inflight coalescing**: `github_projects/service.py` deduplicates concurrent identical GraphQL requests
- **Adaptive backoff**: `polling_loop.py` exponentially backs off idle polling up to 300s max interval
- **Component memoization**: `BoardColumn` and `IssueCard` are wrapped in `React.memo()`; `SubIssueRow` is also memoized
- **Query scoping**: WebSocket and polling only touch task queries; board data has its own query key and refresh cycle
- **Refresh deduplication**: `useBoardRefresh` debounces reload requests within 2-second windows; manual refresh cancels pending reloads
