# Second-Wave Performance Plan

**Date**: 2026-03-21
**Status**: Reference — no action needed unless first-pass metrics fall short

## Context

This document captures recommendations for deeper structural changes if the
first-pass low-risk optimisations do not meet the performance targets defined
in Spec 022 and the performance-review spec (specs/056).

The first pass targeted:
- ≥50% reduction in idle upstream API calls (SC-001)
- Measurable reduction in board component rerenders (SC-005)
- Polling fallback never triggers full board refresh when data unchanged (SC-003)
- All refresh sources follow a single coherent policy (SC-004)

## Trigger Criteria

Pursue second-wave work **only** when post-first-pass measurements show:

| Condition | Threshold | Recommended Action |
|-----------|-----------|-------------------|
| Idle API calls still excessive | <50% reduction vs baseline | Service consolidation (§1) |
| Large boards still lag | >200ms interaction latency on 50+ item boards | Board virtualisation (§2) |
| Cache hit rate low | <80% for sub-issue cache on warm boards | Bounded cache policies (§3) |
| Regression detection gap | Performance regressions discovered late | Instrumentation (§4) |

## §1 — GitHub Projects Service Consolidation

**Problem**: Board data, project items, and sub-issue fetching are spread
across `board.py`, `service.py`, and `issues.py` with overlapping cache
paths.

**Recommendation**:
- Unify board data fetching into a single `BoardDataService` that owns the
  cache lifecycle from GraphQL query through sub-issue enrichment.
- Consolidate `get_project_items()` and `get_board_data()` reuse paths so
  that polling and WebSocket share one cache entry instead of maintaining
  separate caches.
- Estimated scope: ~3 files changed, ~200 lines refactored.

## §2 — Board Virtualisation

**Problem**: Rendering 50+ cards in a single column forces the browser to
layout and paint all DOM nodes, causing jank during scroll and drag.

**Recommendation**:
- Add `react-window` or `@tanstack/react-virtual` for column item lists.
- Keep the existing `BoardColumn` / `IssueCard` components; wrap the
  card list in a virtualised container.
- Ensure drag-and-drop (`@dnd-kit`) interop — both libraries support
  virtualised lists with adapters.
- Estimated scope: 1 new dependency, 2 component files changed.

## §3 — Bounded Cache Policies

**Problem**: `InMemoryCache` grows unboundedly — long-running servers with
many projects accumulate stale entries until `clear_expired()` runs.

**Recommendation**:
- Add a `max_size` parameter to `InMemoryCache` (LRU eviction using
  `collections.OrderedDict`).
- Set reasonable bounds: ~500 entries for project items, ~2000 for
  sub-issues.
- Add cache size metrics to logging.
- Estimated scope: 1 file changed, ~40 lines.

## §4 — Lightweight Instrumentation

**Problem**: Performance regressions are invisible until user complaints or
manual profiling.

**Recommended additions** (low-cost, no new dependencies):

### Backend
- **Board refresh cost**: Log wall-clock time for `get_board_data()` calls
  with project_id and item count.
- **Sub-issue cache hit rate**: Log hit/miss ratio per board refresh
  (already have cache.get/set logging at DEBUG level — aggregate to INFO).
- **Refresh-source attribution**: Tag each cache read/write with the
  caller (WebSocket cycle, polling, manual refresh, auto-refresh) so
  logs show which path is generating load.

### Frontend
- **Render timing**: Add a `useEffect` in `ProjectBoard` that logs
  `performance.now()` delta on mount and re-render in development mode.
- **Query invalidation audit**: In development mode, subscribe to
  TanStack Query's `onQueryUpdated` event to log unexpected board-data
  invalidations.

All instrumentation should be behind a feature flag or `NODE_ENV`/log-level
check so it adds zero cost in production unless explicitly enabled.

## Dependencies

No new runtime dependencies in any of the above recommendations except §2
(virtualisation), which would add one library (~10 KB gzipped).
