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
| Cache TTL & stale fallback | `backend/tests/unit/test_cache.py` | — | — |
| Board endpoint behavior | `backend/tests/unit/test_api_board.py` | — | — |
| Projects & WebSocket | `backend/tests/unit/test_api_projects.py` | — | — |
| Polling & rate-limit logic | `backend/tests/unit/test_copilot_polling.py` | — | — |

### Frontend Guardrails

| Suite | File | Before (pass/total) | After (pass/total) |
|-------|------|---------------------|--------------------|
| WebSocket + fallback polling | `frontend/src/hooks/useRealTimeSync.test.tsx` | — | — |
| Auto-refresh & manual refresh | `frontend/src/hooks/useBoardRefresh.test.tsx` | — | — |
| Board query ownership | `frontend/src/hooks/useProjectBoard.test.tsx` | — | — |
| Board interaction render | `frontend/src/pages/ProjectsPage.test.tsx` | — | — |

## Baseline Capture: Before State

**Captured**: 2026-03-11

### Backend Test Results

- `test_cache.py`: 304 passed (full backend unit suite)
- `test_api_board.py`: included in above
- `test_copilot_polling.py`: included in above

### Frontend Test Results

- `useRealTimeSync.test.tsx`: 34 passed
- `useBoardRefresh.test.tsx`: 17 passed

### Observed Behavior (Before)

- **WebSocket `refresh` messages**: Sent unconditionally every 30 seconds regardless of data changes.
- **Fallback polling**: Invalidates tasks query only (lightweight). Auto-refresh runs independently.
- **Board auto-refresh**: 5-minute interval; no coordination with fallback polling or WebSocket refresh.
- **Manual refresh**: Bypasses cache (`refresh=true`), clears sub-issue caches.
- **Board components**: `BoardColumn` and `IssueCard` are `React.memo`-wrapped.
- **ChatPopup resize**: RAF-throttled `mousemove` handler; listeners only active during drag.
- **AddAgentPopover**: RAF-throttled scroll/resize repositioning.

### Gaps Identified

1. WebSocket subscription broadcasts `refresh` even when task data is unchanged (hash check exists on tasks but not on board structure).
2. No debounce between auto-refresh and WebSocket `refresh` arriving concurrently.
3. Auto-refresh timer does not coordinate with fallback polling state.
4. Callback props in `ProjectsPage` may defeat `React.memo` on child components if not stabilized with `useCallback`.

## Success-Criteria Rubric

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
