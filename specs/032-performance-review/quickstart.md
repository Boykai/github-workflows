# Quickstart: Performance Review

**Feature**: 032-performance-review
**Branch**: `032-performance-review`

## What This Feature Does

Performs a balanced first pass of measurable, low-risk performance gains across backend and frontend:

1. **Baseline measurement** — Captures current performance baselines (idle API calls, board render time, rerender counts, drag fps) before any optimization changes
2. **Backend verification** — Confirms Spec 022 implementations are fully landed (WebSocket change detection, sub-issue caching, board TTL alignment, query invalidation decoupling)
3. **Backend gap fixes** — Addresses any remaining idle API churn in polling, WebSocket reconnection, or repository resolution paths
4. **Frontend render optimization** — Stabilizes derived data with `useMemo`, ensures callback stability with `useCallback`, adds RAF throttling to unthrottled event listeners
5. **Regression coverage** — Extends existing tests to cover changed behavior and serve as regression guardrails

## Files Changed

### Backend (verification and targeted fixes)

| File | Change |
|------|--------|
| `backend/src/api/projects.py` | Verify WebSocket hash-based change detection (Spec 022) |
| `backend/src/api/board.py` | Verify board cache TTL (300s) and manual refresh cache bypass (Spec 022) |
| `backend/src/services/github_projects/service.py` | Verify sub-issue caching with 600s TTL (Spec 022) |
| `backend/src/services/copilot_polling/polling_loop.py` | Verify rate-limit-aware adaptive polling |
| `backend/src/services/cache.py` | Verify cache key helpers and TTL management |

### Frontend (render optimization)

| File | Change |
|------|--------|
| `frontend/src/pages/ProjectsPage.tsx` | Wrap derived data in `useMemo`, stabilize callbacks with `useCallback` |
| `frontend/src/components/board/AddAgentPopover.tsx` | Add RAF gating to scroll/resize positioning listeners |
| `frontend/src/hooks/useRealTimeSync.ts` | Verify query invalidation decoupling (Spec 022) |
| `frontend/src/hooks/useBoardRefresh.ts` | Verify refresh deduplication and visibility API integration |

### Tests (regression coverage)

| File | Change |
|------|--------|
| `backend/tests/unit/test_cache.py` | Extend with sub-issue cache behavior tests if needed |
| `backend/tests/unit/test_api_board.py` | Extend with board cache TTL verification if needed |
| `frontend/src/hooks/useRealTimeSync.test.tsx` | Extend with reconnection debounce and fallback polling tests if needed |
| `frontend/src/hooks/useBoardRefresh.test.tsx` | Extend with visibility API and deduplication edge case tests if needed |

## Verification Steps

### Phase 1: Baseline Measurement

```bash
# 1. Start the application
docker compose up

# 2. Backend baseline: idle API activity
# Open a project board, wait 5 minutes idle
# Count outbound API calls in backend logs
# Expected: <20 calls in 5 minutes (Spec 022 target)

# 3. Frontend baseline: render profiling
# Open React DevTools Profiler in browser
# Load a board with 50+ cards
# Record initial render time and component count
# Trigger a single-card update and count re-renders
```

### Phase 2: Run Existing Tests

```bash
# Backend tests
cd backend && python -m pytest tests/unit/test_cache.py tests/unit/test_api_board.py tests/unit/test_copilot_polling.py -v

# Frontend tests
cd frontend && npm test -- --run src/hooks/useRealTimeSync.test.tsx src/hooks/useBoardRefresh.test.tsx
```

All tests should pass without modification.

### Phase 3: Apply Optimizations and Re-test

```bash
# After applying frontend render optimizations:
cd frontend && npm run type-check && npm run lint && npm test

# After applying any backend fixes:
cd backend && python -m pytest tests/ -v
```

### Phase 4: Post-Optimization Measurement

```bash
# Repeat the baseline measurements from Phase 1
# Compare before/after results:
# - Idle API call count: target ≥50% reduction (SC-001)
# - Single-card rerender count: target ≤3 (SC-005)
# - Board initial render time: must not degrade >10% (SC-004)
# - Chat drag fps: target ≥30 fps (SC-006)
```

### Phase 5: Manual End-to-End Verification

1. **WebSocket updates**: Make a task change on one client → verify update appears on second client quickly without full board reload
2. **Fallback polling**: Disconnect WebSocket (e.g., kill server WebSocket temporarily) → verify polling starts, no excessive API calls
3. **Manual refresh**: Click refresh button → verify all data is fresh, sub-issue caches are cleared
4. **Board interactions**: On a board with 100+ cards, drag a card → verify smooth interaction (≥30 fps)
5. **Chat popup drag**: Drag the chat popup → verify smooth movement without jank

## Rollback

All changes are independent and can be reverted individually:

### Frontend
- `ProjectsPage.tsx`: Remove `useMemo`/`useCallback` wrappers — restores inline computation
- `AddAgentPopover.tsx`: Remove RAF gating — restores direct `updatePosition()` calls on every scroll/resize event

### Backend
- No backend code changes expected in the first pass (Spec 022 already implemented). If any gap fixes are applied, each is a localized edit that can be reverted independently.

### Tests
- Extended tests can be removed without affecting existing test coverage

## Out of Scope (Deferred to Second Wave)

The following are explicitly deferred unless Phase 1 baselines show they are necessary:
- Board virtualization (react-window, react-virtual, TanStack Virtual)
- Major service decomposition in backend GitHub projects service
- New frontend dependencies
- Deeper polling pipeline restructuring
- Request budget instrumentation and render timing telemetry
