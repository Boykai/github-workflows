# Research: Performance Review

**Feature Branch**: `034-performance-review`
**Date**: 2026-03-11
**Purpose**: Resolve all NEEDS CLARIFICATION items and document technology decisions

## Research Tasks

### RT-1: Current Spec 022 Implementation State

**Context**: The spec requires verifying Spec 022 implementation before optimizing. Need to confirm what is already in place vs. what has gaps.

**Findings**:

- **WebSocket change detection**: ✅ Implemented. `projects.py` uses SHA256 hash comparison on task payloads before sending WebSocket updates. Periodic refresh runs every 30 seconds; only sends data if hash differs from previous.
- **Board cache TTL alignment**: ✅ Implemented. `board.py` uses `cache_key = "board_data:{project_id}"` with `cache.set(key, data, ttl=300)` (5-minute TTL). Metadata cache uses 3600s (1-hour) TTL.
- **Sub-issue cache invalidation on manual refresh**: ✅ Implemented. `board.py` manual refresh path explicitly clears all `SUB_ISSUES:*` cache entries before fetching, preventing stale data within the same refresh cycle.
- **Stale fallback on rate limit**: ✅ Implemented. `board.py` uses `cache.get_stale()` to serve expired data when the GitHub API is rate-limited.
- **Rate-limit-aware polling**: ✅ Implemented. `polling_loop.py` defines thresholds: pause at ≤ 50 remaining, skip expensive operations at ≤ 100 remaining, proceed cautiously at ≤ 200 remaining.

**Gaps identified**:

1. **Fallback polling still invalidates board data**: `useRealTimeSync.ts` polling fallback path may still invalidate task queries broadly rather than using a lightweight change check. Need to verify the exact invalidation scope during polling fallback.
2. **No lightweight polling check**: Fallback polling currently triggers task query invalidation on each poll interval without first checking whether data has actually changed. A lightweight change-detection step (e.g., ETag or hash comparison) before full invalidation would reduce unnecessary work.
3. **Duplicate repository resolution**: `workflow.py` implements its own repository resolution logic instead of reusing `utils.py:resolve_repository()`. This creates a DRY violation and potential inconsistency but is a minor API consumption concern.

**Decision**: Spec 022 is substantially complete. Optimization work targets the 3 identified gaps plus measurable performance improvements beyond the original spec scope.
**Rationale**: Starting from a nearly complete baseline means the work can focus on measurable gains rather than fundamental implementation.
**Alternatives considered**: Full Spec 022 re-implementation was rejected since most items are already in place.

---

### RT-2: Backend Cache Architecture and Optimization Opportunities

**Context**: Need to understand cache topology and identify where warm caches can reduce API calls.

**Findings**:

- **Cache service** (`cache.py`): In-memory TTL cache with `get()`, `set()`, `get_stale()`, `refresh_ttl()`, `delete()`, `clear_expired()`. Uses `BoundedSet` (FIFO, maxlen configurable) and `BoundedDict` (FIFO, maxlen configurable) to prevent unbounded memory growth.
- **Cache key patterns**:
  - `PROJECTS:{user_id}` — user project list (3600s TTL)
  - `PROJECT_ITEMS:{project_id}` — project items (300s TTL)
  - `board_data:{project_id}` — full board data (300s TTL)
  - `SUB_ISSUES:{owner}/{repo}#{issue_number}` — sub-issue data (300s TTL)
- **GraphQL in-flight coalescing** (`service.py`): `BoundedDict(maxlen=256)` deduplicates identical in-progress GraphQL queries. Context-aware with request-scoped contextvar + instance-level fallback.
- **Cycle cache** (`service.py`): Cleared at start of each polling cycle to prevent stale data accumulation within a single cycle.

**Optimization opportunities**:

1. **Warm sub-issue cache reuse**: When board data is refreshed (non-manual), sub-issue caches should be checked before making new API calls. Current implementation already caches sub-issues, but measurement will confirm the actual hit rate and API call reduction.
2. **Selective cache invalidation**: Instead of clearing all sub-issue caches on manual refresh, consider invalidating only sub-issues for tasks that have changed (requires change detection at the sub-issue level).
3. **Cache hit rate instrumentation**: Adding lightweight logging around cache hits/misses would provide visibility into cache effectiveness without runtime cost.

**Decision**: Leverage existing cache infrastructure; focus on measuring warm cache effectiveness and ensuring sub-issue caches are properly reused during non-manual refreshes.
**Rationale**: The cache architecture is well-designed; the opportunity is in ensuring it is used optimally rather than adding new caching layers.
**Alternatives considered**: Redis-based distributed cache was rejected (overkill for single-instance deployment; adds a dependency).

---

### RT-3: Frontend Refresh Policy and Query Invalidation Strategy

**Context**: Need to understand how WebSocket, polling, auto-refresh, and manual refresh interact with React Query.

**Findings**:

- **useRealTimeSync** (227 lines):
  - WebSocket messages (`task_update`, `task_created`, `refresh`) invalidate only task queries, NOT board data queries. This is already well-decoupled.
  - `initial_data` messages invalidate tasks + debounce (2s window).
  - Fallback polling (30s interval) uses `queryClient.invalidateQueries` — need to verify exact scope.
  - WebSocket connection: 10s timeout, exponential backoff reconnect (base 1s, max 30s, jitter).

- **useBoardRefresh** (212 lines):
  - Auto-refresh: 5-minute interval, non-forced (allows backend cache).
  - Manual refresh: `forceRefresh=true`, cancels existing refresh, bypasses backend cache.
  - Page Visibility API: pauses auto-refresh when tab hidden, force-refreshes when visible if stale > 5 min.
  - Deduplication: prevents concurrent refresh operations.

- **useProjectBoard** (106 lines):
  - Projects list: `staleTime = 15 minutes`.
  - Board data: `staleTime = 60 seconds`, only enabled when `projectId` is selected.
  - No internal polling — relies on useRealTimeSync for invalidation signals.

**Gaps identified**:

1. **Polling fallback invalidation scope**: During polling fallback, the invalidation may still be broader than necessary. Need to confirm it only targets task queries, not board data.
2. **Auto-refresh and polling interaction**: When both auto-refresh and polling are active, they could create competing invalidation patterns. The current 5-minute auto-refresh interval should naturally be superseded by 30s polling, but the interaction should be explicit.

**Decision**: The frontend refresh policy is already well-structured. The optimization targets are: (a) ensuring polling fallback scope is narrow, (b) making the auto-refresh/polling interaction explicit, and (c) decoupling any remaining broad invalidation paths.
**Rationale**: The existing architecture handles the hard problems (WebSocket/polling fallback, page visibility). Remaining work is refinement, not redesign.
**Alternatives considered**: Replacing React Query with a custom state management solution was rejected (unnecessary complexity for the gains).

---

### RT-4: Frontend Rendering Performance Patterns

**Context**: Need to understand which components are already optimized and where the remaining low-risk gains are.

**Findings**:

- **Already optimized**:
  - `BoardColumn.tsx`: Wrapped in `React.memo()`. Prevents rerender when sibling columns update.
  - `IssueCard.tsx`: Wrapped in `React.memo()`. Prevents rerender when sibling cards update.
  - `ChatPopup.tsx`: Drag/resize listeners are gated to `requestAnimationFrame` and only registered during active drag operations. Listeners removed on mouseup.

- **Optimization targets**:
  - `ProjectsPage.tsx` (~32.9 KB):
    - `transformedBoardData`, `assignedPipeline`, `assignedStageMap` use `useMemo` ✅.
    - `pipelineGridStyle` is created on every render — not memoized ⚠️.
    - Some event listeners re-registered on every modal toggle via `useEffect` dependencies ⚠️.
    - Inline object creation in `useEffect` dependency arrays ⚠️.

- **AddAgentPopover.tsx**: File not found at the expected path. May have been renamed or removed. Not a blocker — ChatPopup is already optimized.

**Decision**: Focus rendering optimization on `ProjectsPage.tsx` derived state and listener patterns. Board components are already memo-wrapped. No new memoization libraries needed.
**Rationale**: The highest-impact rendering targets are in the page component that orchestrates the board, not in the board components themselves (which are already optimized).
**Alternatives considered**: Adding `react-window` or `react-virtuoso` for board virtualization was considered but explicitly deferred per spec scope boundaries.

---

### RT-5: TanStack React Query 5 Best Practices for Selective Invalidation

**Context**: Need to ensure query invalidation patterns follow TanStack Query 5 best practices.

**Findings**:

- **Query key structure**: TanStack Query 5 supports hierarchical query keys for selective invalidation. The codebase should use structured keys like `['board', projectId]`, `['tasks', projectId]`, `['projects']` to enable precise invalidation.
- **`invalidateQueries` vs `setQueryData`**: For lightweight task updates, `setQueryData` (optimistic update) is more efficient than `invalidateQueries` (triggers refetch). However, `invalidateQueries` is simpler and the current approach.
- **`staleTime` vs `gcTime`**: Board data with `staleTime: 60s` means React Query will serve cached data for 60s before considering it stale. This aligns with the 5-minute auto-refresh interval.
- **Selective invalidation**: `queryClient.invalidateQueries({ queryKey: ['tasks'], exact: false })` invalidates all task queries without touching board queries. This is the pattern already in use.

**Decision**: Continue using `invalidateQueries` with selective query keys for the first pass. `setQueryData` for optimistic updates is a potential second-pass improvement if measurement shows invalidation-triggered refetches are still too expensive.
**Rationale**: The current invalidation approach is correct and well-scoped. Moving to optimistic updates would add complexity without proven need.
**Alternatives considered**: Switching to optimistic updates with `setQueryData` — deferred to second pass if needed.

---

### RT-6: Backend Rate Limit and Polling Best Practices

**Context**: Need to understand best practices for rate-limit-aware API consumption.

**Findings**:

- **Current implementation**: `polling_loop.py` already implements a sophisticated rate-limit-aware strategy with multiple thresholds (50, 100, 200 remaining). This is a good pattern.
- **Exponential backoff**: Used in WebSocket reconnection on the frontend. The backend polling loop uses a max interval cap (300s) but not true exponential backoff.
- **ETag/If-None-Match**: GitHub API supports conditional requests. Using `If-None-Match` with ETags would allow the server to return `304 Not Modified` without counting against the rate limit (for REST endpoints). This is not currently implemented but could be a valuable optimization.
- **GraphQL rate limits**: GitHub GraphQL API has separate rate limits (node counts). The existing in-flight coalescing in `service.py` helps, but GraphQL queries should be monitored separately.

**Decision**: Focus on measuring the current rate-limit-aware polling effectiveness. ETag-based conditional requests are a potential second-pass improvement if measurement shows REST calls are still excessive.
**Rationale**: The current rate-limit handling is comprehensive. Adding ETag support would require changes across the cache and API layers and is better suited for a targeted follow-up if needed.
**Alternatives considered**: Implementing ETag support for all GitHub REST calls — deferred due to cross-cutting complexity.

---

## Research Summary

| Item | Status | Key Finding |
|------|--------|-------------|
| Spec 022 state | ✅ Resolved | Substantially complete; 3 minor gaps identified |
| Cache architecture | ✅ Resolved | Well-designed; focus on measurement and warm cache utilization |
| Frontend refresh policy | ✅ Resolved | Well-structured; refine polling fallback scope and auto-refresh interaction |
| Rendering performance | ✅ Resolved | Board components optimized; ProjectsPage has measurable targets |
| React Query patterns | ✅ Resolved | Current patterns follow best practices; selective invalidation in place |
| Rate limit / polling | ✅ Resolved | Comprehensive handling in place; ETag support deferred to second pass |

**All NEEDS CLARIFICATION items resolved.** Proceeding to Phase 1 design.

---

## Implementation Audit (Spec 034 First Pass)

**Date**: 2026-03-11 | **Status**: Complete

### Spec 022 Audit Confirmation

All five Spec 022 targets confirmed fully implemented:

| Target | Status | Evidence |
|--------|--------|----------|
| WebSocket SHA256 change detection | ✅ | `projects.py` lines 375-388 — hash comparison before send |
| Board cache TTL 300s | ✅ | `board.py` line 364 — `ttl_seconds=300` |
| Sub-issue cache invalidation on manual refresh | ✅ | `board.py` lines 318-327 — clears all `SUB_ISSUES:*` entries |
| Stale fallback on rate limit | ✅ | `board.py` stale fallback via `cache.get_stale()` |
| Rate-limit-aware polling | ✅ | `polling_loop.py` — pause/skip/slow thresholds |

### Gap Fixes Applied

1. **Sub-issue cache TTL alignment**: Fixed 600s → 300s in `issues.py` to match board data TTL (contract violation).
2. **Centralized query keys**: Extracted `boardProjectsKey`, `boardDataKey`, `projectTasksKey` from inline strings to prevent drift.
3. **Repository resolution caching**: Added `BoundedDict(maxlen=128)` memoization for `resolve_repository()` to avoid repeated GraphQL lookups.
4. **pipelineGridStyle memoization**: Wrapped with `useMemo` to prevent object recreation on every render.

### Items Already Implemented (No Code Changes Needed)

- Polling fallback invalidation already targets task queries only (not board data).
- Auto-refresh already uses `invalidateQueries` (non-forced, backend cache allowed).
- WebSocket messages already skip unchanged data via SHA256 hash.
- BoardColumn and IssueCard already wrapped in `React.memo`.
- ChatPopup drag listeners already gated to `requestAnimationFrame`.
- `workflow.py` already uses the canonical `resolve_repository` from `utils.py`.

### Deferred to Second Pass

- Board virtualization (react-window / react-virtuoso)
- ETag-based conditional requests to GitHub REST API
- Deeper service decomposition of GitHub project fetching pipeline
- Request budget instrumentation and render timing dashboards
