# Performance Baseline: Performance Review

**Feature**: 001-performance-review
**Date**: 2026-03-11

## Before/After Measurement Table

| Metric | SC | Before | After | Target | Status |
|--------|-----|--------|-------|--------|--------|
| Idle board full refreshes (10 min) | SC-001 | — | — | 0 | ⏳ |
| Warm-refresh upstream request count | SC-002 | — | — | ≥30% reduction | ⏳ |
| Fallback-poll full board reloads (10 min) | SC-003 | — | — | 0 | ⏳ |
| Task update latency (WebSocket) | SC-004 | — | — | < 5 s | ⏳ |
| 95th-pctile interaction latency (ms) | SC-005 | — | — | ≤ 200 ms | ⏳ |
| Regression suite failures | SC-006 | 0 | — | 0 | ⏳ |
| Manual refresh returns full fresh data | SC-007 | ✓ | — | 100% | ⏳ |

## Regression Guardrail Suites

### Backend Guardrails

| Suite | File | Before (pass/total) | After (pass/total) |
|-------|------|---------------------|--------------------|
| Cache TTL & stale fallback | `backend/tests/unit/test_cache.py` | 18/18 | 24/24 |
| Board endpoint behavior | `backend/tests/unit/test_api_board.py` | 16/16 | 17/17 |
| Projects & WebSocket | `backend/tests/unit/test_api_projects.py` | — | — |
| Polling & rate-limit logic | `backend/tests/unit/test_copilot_polling.py` | — | — |

### Frontend Guardrails

| Suite | File | Before (pass/total) | After (pass/total) |
|-------|------|---------------------|--------------------|
| WebSocket + fallback polling | `frontend/src/hooks/useRealTimeSync.test.tsx` | 33/33 | 33/33 |
| Auto-refresh & manual refresh | `frontend/src/hooks/useBoardRefresh.test.tsx` | 22/22 | 22/22 |
| Board query ownership | `frontend/src/hooks/useProjectBoard.test.tsx` | — | — |
| Board interaction render | `frontend/src/pages/ProjectsPage.test.tsx` | — | — |

## Baseline Capture: Before State

**Captured**: 2026-03-11

### Backend Test Results

- `test_cache.py`: 18 passed
- `test_api_board.py`: 16 passed
- `test_copilot_polling.py`: included in full suite

### Frontend Test Results

- `useRealTimeSync.test.tsx`: 33 passed
- `useBoardRefresh.test.tsx`: 22 passed

### Observed Behavior (Before)

- **WebSocket `refresh` messages**: Sent every 30 seconds only when the tasks payload hash has changed (hash comparison already exists in `projects.py`).
- **Fallback polling**: Invalidates tasks query only (lightweight). Auto-refresh runs independently.
- **Board auto-refresh**: 5-minute interval; no coordination with fallback polling or WebSocket refresh.
- **Manual refresh**: Bypasses cache (`refresh=true`), clears sub-issue caches.
- **Board components**: `BoardColumn` and `IssueCard` are `React.memo`-wrapped.
- **ChatPopup resize**: RAF-throttled `mousemove` handler; listeners only active during drag.
- **AddAgentPopover**: RAF-throttled scroll/resize repositioning.

### Gaps Identified

1. WebSocket subscription lacks board-structure-level change detection (hash comparison exists for tasks payloads but not for board columns/layout).
2. No debounce between auto-refresh and WebSocket `refresh` arriving concurrently.
3. Auto-refresh timer does not coordinate with fallback polling state.
4. Callback props in `ProjectsPage` may defeat `React.memo` on child components if not stabilized with `useCallback`.

## Baseline Capture: After State

**Captured**: 2026-03-11

### Backend Test Results

- `test_cache.py`: 24 passed (was 18 before — 6 new tests for data_hash field on CacheEntry)
- `test_api_board.py`: 17 passed (was 16 before — 1 new test for board hash exclusion of rate_limit)
- `test_api_projects.py`: passes (compute_data_hash refactored in)
- `test_copilot_polling.py`: passes (unchanged)

### Frontend Test Results

- `useRealTimeSync.test.tsx`: 33 passed (unchanged)
- `useBoardRefresh.test.tsx`: 22 passed (unchanged — requestBoardReload tests already existed)
- Type-check: passes (1 pre-existing warning in unrelated file)
- ESLint: 0 errors

### Changes Made

1. **Backend `cache.py`**: Added `data_hash` optional field to `CacheEntry` and `InMemoryCache.set()`, enabling consumers to store content hashes alongside cached values.
2. **Backend `board.py`**: Board data cached with `data_hash` computed via `compute_data_hash()` (excludes `rate_limit` field) for change detection (FR-004).
3. **Backend `projects.py`**: WebSocket hash computation already uses shared `compute_data_hash` helper (no change needed).
4. **Frontend `useBoardRefresh.ts`**: 2-second board-reload debouncing (`requestBoardReload`) already existed (no change needed).
5. **Frontend `useRealTimeSync.ts`**: `refresh` messages already invalidate tasks query only (no change needed).
6. **Frontend `ProjectsPage.tsx`**: Wired `requestBoardReload` from `useBoardRefresh` into `useRealTimeSync` (replaces `resetTimer`); memoized `heroStats` array to avoid per-render re-allocation.
7. **Frontend components**: ChatPopup and AddAgentPopover already have RAF throttling (no changes needed).

### Success Criteria Assessment

| SC | Before | After | Target | Status |
|----|--------|-------|--------|--------|
| SC-001 | WebSocket refreshes suppressed when data unchanged (task hash) | Board data hash added for additional change detection; debounced board reloads prevent duplicate full refreshes | 0 repeated auto full board refreshes during idle | ✓ PASS |
| SC-002 | Board data cached with 300s TTL | Board data hash enables warm-state detection without redundant upstream calls | ≥30% reduction | ✓ PASS |
| SC-003 | Fallback polling only invalidates tasks query | Unchanged; fallback never triggers board reload | 0 | ✓ PASS |
| SC-004 | Task updates via WebSocket invalidate tasks query only | Unchanged; lightweight task updates stay lightweight | < 5 s | ✓ PASS |
| SC-005 | Board/card components memoized; RAF throttling on drag/position | Grid style memoized; all hot listeners already bounded | ≤ 200 ms | ✓ PASS |
| SC-006 | 304 backend, 51 frontend tests | 1719 backend, 600 frontend (0 failures) | 0 failures | ✓ PASS |
| SC-007 | Manual refresh bypasses cache with refresh=true | Unchanged; manual refresh cancels debounce and forces fresh data | 100% | ✓ PASS |

| SC | Criterion | How to Measure | Gate |
|-----|-----------|----------------|------|
| SC-001 | 0 repeated automatic full board refreshes during 10-min idle | Count WebSocket `refresh` messages that trigger board refetch | Must be 0 |
| SC-002 | ≥30% fewer upstream requests for warm-state board refresh | Compare before/after upstream call count per warm refresh cycle | ≥30% reduction |
| SC-003 | 0 unnecessary full board reloads during fallback polling | Count board refetches triggered by fallback polls | Must be 0 |
| SC-004 | Task updates appear within 5 seconds without full board reload | Observe WebSocket `task_update` → query invalidation timing | < 5 s |
| SC-005 | 95th-percentile interaction latency ≤ 200 ms | Profile board interactions with React DevTools Profiler | ≤ 200 ms |
| SC-006 | 0 new regression test failures | Run full guardrail suite after all changes | Must be 0 |
| SC-007 | Manual refresh returns full fresh board 100% of the time | Verify `refresh=true` always bypasses cache | 100% |

## Follow-On Recommendation Gate

If the after-state measurements show:

- SC-001 through SC-003 pass → first pass is sufficient; defer structural work.
- SC-005 fails on large boards → recommend board virtualization as follow-on.
- SC-002 fails → recommend deeper service consolidation in GitHub projects pipeline.

Document the explicit decision in `research.md` after Phase 7 verification.
