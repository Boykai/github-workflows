# Quickstart: Performance Review

**Feature Branch**: `056-performance-review`
**Date**: 2026-03-21
**Status**: Complete

## Prerequisites

- Python 3.13+ with pip
- Node.js 18+ with npm
- Access to the `solune/` monorepo

## Setup

### Backend

```bash
cd solune/backend
pip install -e ".[dev]"
```

### Frontend

```bash
cd solune/frontend
npm ci
```

## Phase 1: Baseline Measurement

### Backend Baseline

1. **Run existing backend tests** (establishes "before" regression baseline):

```bash
cd solune/backend
python -m pytest tests/unit/test_cache.py tests/unit/test_api_board.py tests/unit/test_copilot_polling.py -x -q
```

2. **Run linting and type checks**:

```bash
cd solune/backend
ruff check src/
pyright src/
```

3. **Measure idle API activity** (manual step):
   - Start the backend server with logging enabled
   - Open a board and leave it idle for 5 minutes
   - Count upstream API calls in logs (look for `_graphql()` and `_rest()` calls)
   - Record: total calls, calls per minute, cache hit/miss ratio

### Frontend Baseline

1. **Run existing frontend tests** (establishes "before" regression baseline):

```bash
cd solune/frontend
npm test -- --run src/hooks/useRealTimeSync.test.tsx src/hooks/useBoardRefresh.test.tsx
```

2. **Run linting, type-checking, and build**:

```bash
cd solune/frontend
npm run lint
npm run type-check
npm run build
```

3. **Profile board rendering** (manual step):
   - Open a board with 5+ columns and 50+ tasks
   - Open React DevTools Profiler
   - Record a session: load board → scroll columns → drag a card → open a popover
   - Note: components with highest render count, event listener fire rates

## Phase 2: Backend Optimizations

### Key Files to Modify

| File | Optimization |
|------|-------------|
| `src/api/projects.py` | Remove redundant `list_user_projects()` in WebSocket refresh cycle |
| `src/api/board.py` | Ensure non-manual refresh reuses sub-issue cache |
| `src/services/copilot_polling/polling_loop.py` | Verify `get_project_items()` is cache-first in all paths |

### Verification

```bash
cd solune/backend
# Run targeted tests after each change
python -m pytest tests/unit/test_api_board.py -x -q
python -m pytest tests/unit/test_cache.py -x -q
python -m pytest tests/unit/test_copilot_polling.py -x -q
# Full lint + type check
ruff check src/
```

## Phase 3: Frontend Optimizations

### Key Files to Modify

| File | Optimization |
|------|-------------|
| `src/hooks/useRealTimeSync.ts` | Confirm tasks-only invalidation (already correct) |
| `src/hooks/useBoardRefresh.ts` | Suppress auto-refresh when WebSocket is healthy |
| `src/pages/ProjectsPage.tsx` | Memoize sync status labels, stabilize context values |
| `src/components/board/BoardColumn.tsx` | Stabilize `onCardClick` prop from parent |
| `src/components/board/IssueCard.tsx` | Memoize inline label parsing and body truncation |
| `src/components/agents/AddAgentPopover.tsx` | Memoize `filteredAgents`, add `useMemo` for `assignedSlugs` |

### Verification

```bash
cd solune/frontend
# Run targeted tests after each change
npm test -- --run src/hooks/useRealTimeSync.test.tsx
npm test -- --run src/hooks/useBoardRefresh.test.tsx
# Full suite
npm run lint
npm run type-check
npm test
npm run build
```

## Phase 4: Verification

### Automated Verification

```bash
# Backend full suite
cd solune/backend
ruff check src/
python -m pytest tests/unit/ -x -q

# Frontend full suite
cd solune/frontend
npm run lint
npm run type-check
npm test
npm run build
```

### Manual Verification Checklist

- [ ] Open a board → leave idle 5 min → count API calls → compare to baseline (SC-001: ≥50% reduction)
- [ ] Open a board with warm cache → refresh → verify sub-issue cache hits (SC-002)
- [ ] Disconnect WebSocket → verify polling does not trigger board data refresh (SC-003)
- [ ] Change a task status → verify only tasks query refetches, not board data (SC-004)
- [ ] Profile board interactions → compare rerender counts to baseline (SC-005)
- [ ] Run full test suites → all pass (SC-006)
- [ ] Manual e2e: WS updates arrive promptly, polling fallback safe, manual refresh works (SC-007)
- [ ] No visible regression in board functionality (SC-008)

## Key Decisions Reference

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Optimization approach | Balanced backend + frontend | Addresses both API churn and render cost |
| First-pass scope | Low-risk only | Avoids virtualization, decomposition, new dependencies |
| Baseline requirement | Mandatory before changes | Ensures improvements are proven, not assumed |
| Auto-refresh + WebSocket | Suppress timer when WS healthy | Prevents redundant 5-min refreshes during active connection |
| Board virtualization | Deferred | Only needed if large boards still lag after lighter fixes |
