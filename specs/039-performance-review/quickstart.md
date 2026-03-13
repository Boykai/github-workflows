# Quickstart: Performance Review Implementation

**Feature**: 039-performance-review
**Date**: 2026-03-13

## Prerequisites

- Python ≥3.12 (backend)
- Node.js 22+ (frontend)
- Git

## Repository Setup

```bash
cd /path/to/github-workflows

# Backend
cd backend
pip install -e ".[dev]"

# Frontend
cd ../frontend
npm install
```

## Key Files to Modify

### Backend (Python/FastAPI)

| File | Purpose | What to Change |
|------|---------|---------------|
| `backend/src/api/board.py` | Board data endpoint | Add sub-issue cache reuse in non-manual refresh path |
| `backend/src/api/projects.py` | WebSocket subscription | Verify change detection, review periodic refresh behavior |
| `backend/src/services/copilot_polling/polling_loop.py` | Background polling | Verify rate-limit-aware skip logic for expensive steps |
| `backend/src/services/github_projects/service.py` | GitHub API client | Verify inflight coalescing and cycle cache behavior |
| `backend/src/services/cache.py` | Cache infrastructure | No structural changes expected; verify TTL alignment |

### Frontend (TypeScript/React)

| File | Purpose | What to Change |
|------|---------|---------------|
| `frontend/src/hooks/useRealTimeSync.ts` | WebSocket + polling | Add hash-based change detection before polling invalidation |
| `frontend/src/hooks/useBoardRefresh.ts` | Refresh orchestration | Verify debounce and deduplication rules |
| `frontend/src/hooks/useProjectBoard.ts` | Board data query | Verify stale times and no redundant refetch triggers |
| `frontend/src/pages/ProjectsPage.tsx` | Board page | Stabilize callback props with `useCallback` |
| `frontend/src/components/board/BoardColumn.tsx` | Column component | Already memoized; verify props stability |
| `frontend/src/components/board/IssueCard.tsx` | Card component | Already memoized; verify props stability |

### Test Files

| File | What to Extend |
|------|---------------|
| `backend/tests/unit/test_cache.py` | Sub-issue cache reuse assertions |
| `backend/tests/unit/test_api_board.py` | Board refresh with warm sub-issue cache |
| `backend/tests/unit/test_copilot_polling.py` | Polling idle behavior assertions |
| `frontend/src/hooks/useRealTimeSync.test.tsx` | Polling fallback change detection |
| `frontend/src/hooks/useBoardRefresh.test.tsx` | Deduplication and debounce behavior |

## Running Tests

```bash
# Backend tests (targeted)
cd backend
python -m pytest tests/unit/test_cache.py tests/unit/test_api_board.py tests/unit/test_copilot_polling.py -v

# Backend lint
python -m ruff check src/

# Frontend tests (targeted)
cd frontend
npx vitest run src/hooks/useRealTimeSync.test.tsx src/hooks/useBoardRefresh.test.tsx

# Frontend type check + lint
npm run type-check
npm run lint

# Full test suites (verification)
cd backend && python -m pytest tests/unit/ -v
cd frontend && npx vitest run
```

## Implementation Order

1. **Phase 1 — Baseline** (no code changes)
   - Run backend tests to confirm current behavior
   - Run frontend tests to confirm current behavior
   - Document baseline measurements in test artifacts

2. **Phase 2a — Backend fixes**
   - Sub-issue cache reuse in `board.py` non-manual refresh
   - Verify WebSocket change detection in `projects.py`
   - Verify polling loop idle behavior

3. **Phase 2b — Frontend refresh-path fixes** (parallel with 2a)
   - Add change detection to polling fallback in `useRealTimeSync.ts`
   - Verify refresh deduplication in `useBoardRefresh.ts`

4. **Phase 3a — Frontend render optimization**
   - Stabilize callback props in `ProjectsPage.tsx`
   - Verify memo effectiveness on `BoardColumn` and `IssueCard`
   - Profile and optimize derived state computation

5. **Phase 3b — Regression tests**
   - Extend backend tests for sub-issue cache reuse
   - Extend frontend tests for polling change detection
   - Run full test suites for regression check

## Contracts Reference

- [Refresh Policy](contracts/refresh-policy.md) — When and how board data refreshes
- [Cache Behavior](contracts/cache-behavior.md) — Backend caching rules and TTLs
- [Render Behavior](contracts/render-behavior.md) — Component rendering expectations

## Success Criteria Quick Reference

| Metric | Target |
|--------|--------|
| Idle API calls (5 min) | ≥50% reduction from baseline |
| Warm cache refresh calls | ≥30% fewer than cold cache |
| Single-task update latency | <2 seconds, no full board reload |
| Fallback polling false refreshes | Zero when data unchanged |
| Single-task rerender scope | Affected card + container only |
