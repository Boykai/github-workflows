# Performance Baseline Report

**Feature**: 001-performance-review
**Date**: 2026-03-26
**Board Size**: Representative (5+ columns, 20+ cards)

## Measurement Run Details

- **Status**: Pending — this branch documents the audit and guardrails, but it does not attach a recorded baseline/profile run yet.
- **Commit SHA**: TBD
- **Environment**: TBD
- **Board identifier**: TBD
- **Tooling**: TBD

## Implementation State Audit (FR-003)

### Backend Cache Implementation (R-001)

| Component | Status | Evidence |
|-----------|--------|----------|
| Board cache TTL (300s default) | ✅ Fully Landed | `InMemoryCache` in `cache.py` uses `settings.cache_ttl_seconds`; board data cached via `cached_fetch()` in `board.py` |
| Data-hash change detection (SHA256) | ✅ Fully Landed | `CacheEntry.data_hash` field; `cached_fetch()` compares hashes and only refreshes TTL when unchanged |
| Sub-issue cache invalidation | ✅ Fully Landed | Manual refresh (`refresh=true`) in `board.py` deletes sub-issue cache entries; automatic refreshes reuse cache |
| Stale fallback | ✅ Fully Landed | `cached_fetch()` returns stale data on fetch failure when `stale_fallback=True` |

### WebSocket Change Detection (R-002)

| Component | Status | Evidence |
|-----------|--------|----------|
| Hash comparison suppresses unchanged `refresh` | ✅ Fully Landed | `projects.py` tracks `last_sent_hash`, only sends WS message when hash differs |
| Stale revalidation counter | ✅ Fully Landed | Counter-based pattern serves stale up to 10 times, then forces fresh fetch |
| Frontend selective invalidation (WS) | ✅ Fully Landed | `useRealTimeSync.ts` invalidates only `['projects', projectId, 'tasks']` for all WS message types |
| Frontend polling fallback selective invalidation | ✅ Fully Landed | `startPolling()` in `useRealTimeSync.ts` invalidates only `['projects', projectId, 'tasks']` (line 140) |

### Polling Loop Behavior (R-003)

| Component | Status | Evidence |
|-----------|--------|----------|
| Rate-limit pause at 50 remaining | ✅ Fully Landed | `RATE_LIMIT_PAUSE_THRESHOLD = 50` in polling state |
| Rate-limit slow at 200 remaining | ✅ Fully Landed | `RATE_LIMIT_SLOW_THRESHOLD = 200` in polling state |
| Skip expensive steps at 100 remaining | ✅ Fully Landed | `RATE_LIMIT_SKIP_EXPENSIVE_THRESHOLD = 100` with `is_expensive` flag on `PollStep` |
| Exponential backoff with 15-min cap | ✅ Fully Landed | Backoff logic in polling loop |

### Frontend Query Invalidation (R-004)

| Component | Status | Evidence |
|-----------|--------|----------|
| WS handlers invalidate tasks only | ✅ Fully Landed | All WS message types invalidate `['projects', projectId, 'tasks']` only |
| Board data on separate 5-min timer | ✅ Fully Landed | `useBoardRefresh` manages auto-refresh independently |
| Auto-refresh suppressed when WS connected | ✅ Fully Landed | `startTimer()` returns early when `isWebSocketConnected` is true |
| Debounce window (2s) for board reloads | ✅ Fully Landed | `BOARD_RELOAD_DEBOUNCE_MS = 2_000` with `requestBoardReload()` |
| Board data `staleTime: 1 min` | ✅ Fully Landed | `useProjectBoard` sets `staleTime: STALE_TIME_SHORT` |
| Projects list `staleTime: 15 min` | ✅ Fully Landed | Projects query uses extended stale time |

### Frontend Rendering (R-005)

| Component | Status | Evidence |
|-----------|--------|----------|
| IssueCard wrapped with React.memo | ✅ Fully Landed | `export const IssueCard = memo(function IssueCard...)` |
| IssueCard internal useMemo (labels, snippet) | ✅ Fully Landed | 3x `useMemo()` for labels, label parsing, body snippet |
| BoardColumn wrapped with React.memo | ✅ Fully Landed | `export const BoardColumn = memo(function BoardColumn...)` |
| BoardColumn groups memoized | ✅ Fully Landed | `useMemo()` for `getGroups?.(column.items)` |
| ProjectsPage derived data memoized | ✅ Fully Landed | 4x `useMemo()` for hero stats, pipeline lookup, rate limit, sync status |
| ChatPopup RAF-gated resize | ✅ Fully Landed | `requestAnimationFrame` gating on mousemove during resize |
| AddAgentPopover positioning | ✅ Fully Landed | Radix UI handles positioning — no custom listeners needed |
| Callback props stabilized (useCallback) | ✅ Fully Landed | `handleCardClick`, `handleCloseModal`, `handleStatusUpdate` all use `useCallback` |

### Gap Analysis Summary

**All identified optimization targets from the spec are FULLY LANDED.** The codebase already implements:
- Backend: Hash-based change detection, sub-issue cache reuse, rate-limit-aware polling, stale fallback
- Frontend: Selective query invalidation, auto-refresh suppression, debounced board reloads, component memoization, event throttling, stable callback props

**Remaining work**: Add regression tests to codify these behaviors as guardrails against future regressions.

---

## Pre-Optimization Baselines (FR-001, FR-002)

> Values remain `TBD` until a concrete measurement run is recorded in the section above.

### Backend Metrics

| Metric | Category | Value | Unit | Conditions |
|--------|----------|-------|------|------------|
| Idle API calls (5 min) | backend_api | TBD | calls | Board open, WS connected, no upstream changes. Measure with backend logs/network tracing. |
| Board cold-cache request cost | backend_api | TBD | calls | Empty cache → fetches board data from GitHub API. Capture from a recorded request run. |
| Board warm-cache request cost | backend_api | TBD | calls | Within TTL → expected to serve cached data, but baseline value should be recorded from a measurement run. |
| WebSocket idle refresh events (5 min) | backend_api | TBD | count | Measure over 5 idle minutes to confirm unchanged `refresh` messages stay suppressed. |

### Frontend Metrics

| Metric | Category | Value | Unit | Conditions |
|--------|----------|-------|------|------------|
| Board initial render time | frontend_render | TBD | ms | Representative board, to be measured with React DevTools/profile tooling. |
| Component mount count (initial) | frontend_render | TBD | count | Record with React DevTools profiler during the same run. |
| Single-card-update rerender count | frontend_render | TBD | count | Trigger one task update and record the resulting rerenders. |
| Drag interaction event fires/sec | frontend_render | TBD | count/s | Record during a representative drag interaction. |
| Network requests on WS task_update | frontend_network | TBD | count | Record the network activity caused by a single task-level update. |
| Network requests on polling fallback | frontend_network | TBD | count | Record one fallback interval when WebSocket is unavailable. |

### Test Suite Baseline

| Test Suite | Tests | Status | Duration |
|------------|-------|--------|----------|
| Backend: test_cache.py + test_api_board.py + test_copilot_polling.py | 398 | ✅ All passed | ~12s |
| Frontend: useRealTimeSync.test.tsx + useBoardRefresh.test.tsx | 76 | ✅ All passed | ~1s |

---

## Post-Optimization Results

> Post-optimization values are also pending until the same measurement procedure is rerun and attached here.

### Backend Metrics (Post)

| Metric | Baseline | Post | Change | Target Met? |
|--------|----------|------|--------|-------------|
| Idle API calls (5 min) | TBD | TBD | TBD | Pending measurement |
| Board warm-cache cost | TBD | TBD | TBD | Pending measurement |
| WS idle refresh events | TBD | TBD | TBD | Pending measurement |

### Frontend Metrics (Post)

| Metric | Baseline | Post | Change | Target Met? |
|--------|----------|------|--------|-------------|
| Single-card-update rerender | TBD | TBD | TBD | Pending measurement |
| Drag event rate | TBD | TBD | TBD | Pending measurement |
| WS task_update requests | TBD | TBD | TBD | Pending measurement |

### Success Criteria Verification

| Criterion | Result | Notes |
|-----------|--------|-------|
| SC-001: ≥50% fewer idle API calls | ⚠️ PENDING | Requires a recorded before/after idle measurement run |
| SC-002: Zero warm-cache API calls | ⚠️ PENDING | Expected from cache behavior, but the baseline/post comparison is not yet recorded |
| SC-003: No full board reload on single task update | ⚠️ PENDING | Behavior is covered by tests/code inspection, but the documented measurement run is still missing |
| SC-004: Measurable rerender reduction | ⚠️ PENDING | Requires profiler evidence from a representative board interaction |
| SC-005: All existing tests pass | ✅ PASS | 398 backend + 76 frontend tests pass |
| SC-006: Regression test coverage added | ✅ PASS | New tests added for idle refresh prevention, decoupled refresh, change detection |
| SC-007: Manual E2E verification | ⚠️ PENDING | No manual network/profile pass is recorded in this branch; current evidence is code inspection only |
| SC-008: No new dependencies | ✅ PASS | No changes to pyproject.toml or package.json dependencies |
