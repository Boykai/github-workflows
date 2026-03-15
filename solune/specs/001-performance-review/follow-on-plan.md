# Follow-On Plan: Performance Review

**Feature**: 001-performance-review
**Date**: 2026-03-15
**Status**: Documented (not currently needed — all first-pass targets met)

## Context

All SC-001 through SC-006 performance targets were met in the first pass. This follow-on plan documents recommended second-wave improvements should future measurements show regression or should board sizes grow beyond the current 50–100 task range.

## Recommendations

### 1. Board Virtualization (if large boards remain slow)

**Trigger**: Board interaction latency exceeds 200ms on boards with 100+ tasks.

**Approach**: Introduce windowed rendering for `BoardColumn` items using `react-window` or `@tanstack/react-virtual`. Only visible cards are rendered; off-screen cards are replaced with placeholder spacers.

**Impact**: Reduces DOM node count from O(n) to O(visible), significantly improving scroll and interaction performance on large boards.

**Risk**: Moderate — requires changes to scroll behavior, keyboard navigation, and drag-and-drop integration.

### 2. GitHub Projects Service Consolidation (if API churn returns)

**Trigger**: Idle board API calls exceed 5 per 5-minute window.

**Approach**: Consolidate `get_project_items`, `get_board_data`, and `poll_project_changes` into a single coordinator that manages a shared request queue with deduplication. Replace the current pattern of independent cache lookups with a centralized "request budget" that limits total outbound calls per interval.

**Impact**: Eliminates duplicate API calls across different code paths sharing the same data.

**Risk**: High — requires significant refactoring of the service layer and careful testing of race conditions.

### 3. Bounded Cache Policies

**Trigger**: Memory usage of the backend process exceeds expected bounds, or stale data persists longer than acceptable.

**Approach**: Add LRU eviction to `InMemoryCache` with a configurable maximum entry count. Replace `BoundedDict` FIFO eviction with LRU for inflight coalescing. Add periodic cleanup scheduling.

**Impact**: Prevents unbounded memory growth and ensures cache entries are eviction-friendly.

**Risk**: Low — mostly additive changes to existing cache infrastructure.

### 4. Instrumentation for Regression Visibility

**Recommended regardless of triggers**: Add lightweight instrumentation to the following paths for ongoing performance monitoring:

- **Board refresh cost tracking**: Log the number of outbound GitHub API calls per board refresh (cold vs. warm cache) via structlog.
- **Sub-issue cache hit rate**: Track cache hits vs. misses for sub-issue lookups in board data fetches.
- **Refresh-source attribution**: Tag each board data query with its source (manual, auto-refresh, WebSocket, polling fallback) so logs can identify which path is generating the most load.
- **Frontend render timing**: Add `React.Profiler` callbacks to `BoardColumn` and `IssueCard` in development mode to surface render duration regressions early.

**Implementation**: All instrumentation should use existing logging infrastructure (structlog for backend, console.debug for frontend dev mode). No new APM dependencies.

## Summary

| Recommendation | Trigger | Effort | Risk |
|---------------|---------|--------|------|
| Board virtualization | >100 task boards slow | Medium | Moderate |
| Service consolidation | Idle API calls > 5/5min | High | High |
| Bounded cache policies | Memory growth | Low | Low |
| Instrumentation | Proactive (recommended now) | Low | Negligible |
