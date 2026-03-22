# Quickstart: Performance Review

**Feature**: 001-performance-review  
**Date**: 2026-03-22  
**Status**: Complete

## Prerequisites

- Python ≥3.12 (backend)
- Node.js ≥20 (frontend)
- GitHub personal access token with project/repo scope

## Setup

### Backend

```bash
cd solune/backend
pip install -e ".[dev]"
```

### Frontend

```bash
cd solune/frontend
npm install
```

## Phase 1: Capture Baselines

### Backend Baseline

1. **Run existing tests** to establish before-state:

```bash
cd solune/backend
pytest tests/unit/test_cache.py tests/unit/test_api_board.py tests/unit/test_copilot_polling.py -v --timeout=60
```

2. **Run linting and type checks**:

```bash
cd solune/backend
ruff check src tests
pyright src
```

3. **Measure idle API activity** (manual): Open a board in the app, leave it idle for 5 minutes, and count outbound GitHub API calls using the backend logs or network inspector.

### Frontend Baseline

1. **Run existing tests**:

```bash
cd solune/frontend
npm run test -- --run src/hooks/useRealTimeSync.test.tsx src/hooks/useBoardRefresh.test.tsx
```

2. **Run linting and type checks**:

```bash
cd solune/frontend
npm run lint
npm run type-check
```

3. **Profile board rendering** (manual): Open browser DevTools Performance tab, load a board with 50+ cards, and record:
   - Component render counts during load
   - Component render counts during a single task update
   - Frame rate during drag and scroll interactions

## Phase 2: Implementation

### Backend Changes

**Target files** (in priority order):

1. `solune/backend/src/api/projects.py` — Wire hash-based change detection into WebSocket subscription loop
2. `solune/backend/src/api/board.py` — Verify cache behavior, confirm sub-issue cache reuse
3. `solune/backend/src/services/copilot_polling/polling_loop.py` — Verify rate limit budget behavior

**Key pattern**: Use `compute_data_hash()` from `solune/backend/src/services/cache.py` to compare current data hash against last-sent hash in the WebSocket subscription loop. Skip sending `refresh` messages when hashes match.

### Frontend Changes

**Target files** (in priority order):

1. `solune/frontend/src/hooks/useRealTimeSync.ts` — Verify tasks-only invalidation is preserved
2. `solune/frontend/src/hooks/useBoardRefresh.ts` — Verify auto-refresh suppression when WS connected
3. `solune/frontend/src/pages/ProjectsPage.tsx` — Stabilize callback references for memoized children
4. `solune/frontend/src/components/board/BoardColumn.tsx` — Verify memo effectiveness
5. `solune/frontend/src/components/board/IssueCard.tsx` — Verify memo effectiveness

**Key pattern**: Ensure all callbacks passed to `React.memo`-wrapped children are wrapped in `useCallback` with stable dependency arrays.

## Phase 3: Verification

### Backend Verification

```bash
cd solune/backend
pytest tests/unit/test_cache.py tests/unit/test_api_board.py tests/unit/test_copilot_polling.py -v --timeout=60
ruff check src tests
pyright src
```

### Frontend Verification

```bash
cd solune/frontend
npm run test -- --run src/hooks/useRealTimeSync.test.tsx src/hooks/useBoardRefresh.test.tsx
npm run lint
npm run type-check
npm run build
```

### Manual Verification

1. Open a board with 50+ cards
2. Verify WebSocket connection establishes (check sync status indicator)
3. Leave board idle for 5 minutes — verify zero unnecessary API calls in backend logs
4. Trigger a task update — verify it appears within 5 seconds without full board reload
5. Click manual refresh — verify fresh data loads with cache bypass
6. Disconnect WebSocket (e.g., network throttle) — verify fallback polling activates
7. Profile drag and scroll — verify >30 FPS on 50+ card board

## Success Criteria Quick Reference

| Metric | Target | How to Measure |
|--------|--------|---------------|
| Idle API calls (5 min) | Zero unnecessary | Backend logs / network monitor |
| Cached board response | <500ms | Frontend DevTools network tab |
| Task update latency | <5s without full reload | Observe UI after WebSocket message |
| Board FPS (50+ cards) | >30 FPS | Chrome DevTools Performance tab |
| Re-render reduction | ≥30% fewer | React DevTools Profiler before/after |
| Idle API call reduction | ≥50% | Compare baseline counts |
| Test regressions | Zero | Run full test suite |
