# Spec 022 Acceptance Criteria Audit

**Feature**: 001-performance-review
**Date**: 2026-03-15
**Status**: Complete

## Audit Results

| # | Criterion | Status | Evidence | Remaining Work |
|---|-----------|--------|----------|----------------|
| 1 | Board cache TTL alignment (300s) | ✅ Fully Implemented | `board.py:365` — `cache.set(cache_key, board_data, ttl_seconds=300, data_hash=board_hash)` aligns with frontend 5-min auto-refresh in `useBoardRefresh.ts` | None |
| 2 | Sub-issue cache invalidation on manual refresh | ✅ Fully Implemented | `board.py:315-324` — iterates cached board columns, deletes sub-issue cache entries when `refresh=True`. Validated by `test_manual_refresh_clears_sub_issue_caches` | None |
| 3 | Change detection via data hashing | ✅ Fully Implemented | `cache.py:compute_data_hash()` produces SHA-256. `board.py:364` stores hash. `projects.py:363-374` compares hash in WebSocket periodic check | None |
| 4 | Rate-limit-aware polling | ✅ Fully Implemented | `polling_loop.py` — pause at ≤50, skip expensive at ≤200, slow at ≤500. Adaptive idle backoff up to 300s. Stale cleanup. Extensively tested in `test_copilot_polling.py` | None |
| 5 | Inflight request coalescing | ✅ Fully Implemented | `service.py` — `_inflight_graphql: BoundedDict[str, asyncio.Task]` (maxlen=256). Hashes query+variables+headers for dedup. Self-cleans on completion | None |
| 6 | Stale fallback on error | ✅ Fully Implemented | `cache.py:get_stale()` returns expired entries. `board.py` and `projects.py` serve stale data on GitHub API errors | None |

## Summary

**Overall Status**: All 6 Spec 022 acceptance criteria are fully implemented.

**Remaining Gaps** (identified in research, not Spec 022 gaps but optimization opportunities):

1. **WebSocket periodic check cache usage** — The 30-second periodic check in `projects.py` calls `send_tasks(force_refresh=False)` which correctly checks cache first. However, if the cache TTL (300s) has expired, it still makes a fresh API call. This is correct behavior but could be optimized to serve stale data during idle periods and only refresh when explicitly requested.

2. **Fallback polling invalidation scope** — `useRealTimeSync.ts` fallback polling only invalidates tasks query (confirmed correct). No board data invalidation occurs during polling. This is working as designed.

3. **Duplicate repository resolution** — `workflow.py` has multiple `resolve_repository()` calls. While each call may hit cache, consolidating repeated calls within the same request handler would reduce unnecessary work.

4. **Polling loop cycle cache clear** — `polling_loop.py` clears cycle cache at each iteration start. This is correct for change detection but could be optimized to only clear when the interval has fully elapsed.

## Conclusion

No Spec 022 criteria need to be re-implemented. The optimization work focuses on:
- Reducing unnecessary API calls during idle periods (SC-001)
- Improving sub-issue cache reuse on non-manual refreshes (SC-002)
- Verifying and tightening refresh policy coherence (SC-003, SC-004)
- Low-risk render optimizations (SC-005, SC-006)
