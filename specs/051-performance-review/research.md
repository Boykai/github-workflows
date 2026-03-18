# Research: Performance Review

**Feature**: `051-performance-review`
**Date**: 2026-03-18
**Status**: Complete

---

## Research Task 1: Current Backend Idle API Behavior

### Decision

The WebSocket subscription in `projects.py` already implements hash-based change detection (only sends `refresh` messages when task data actually differs) and uses a 30-second check interval governed by the cache layer. The idle behavior is substantially correct but has a gap: each 30-second check still calls `get_project_tasks()` which may trigger external API calls if the cached data has expired (300-second TTL). Additionally, after 10 consecutive stale returns, the code forces a fresh fetch regardless of whether data changed.

### Rationale

The existing implementation covers the most critical path — hash comparison prevents redundant WebSocket messages. However, the forced fresh-fetch after 10 stale cycles (stale revalidation) can generate unnecessary API calls during idle periods. The optimization should focus on ensuring the stale-revalidation counter resets only on actual data changes rather than on forced fetches, and that cache TTL alignment prevents gratuitous expiry during idle board sessions.

### Alternatives Considered

- **Disable stale revalidation entirely**: Rejected — the 10-cycle stale guard exists to prevent serving arbitrarily old data. A better approach is to reset the counter on verified-unchanged data (same hash) rather than removing it.
- **Increase cache TTL beyond 300s for idle detection**: Rejected — the 300-second TTL is aligned with frontend auto-refresh and Spec 022 targets. Changing it would create a mismatch.
- **Add server-side idle detection**: Rejected for first pass — the WebSocket handler would need to track user activity signals, adding complexity. The simpler approach is to reduce the cost of each idle check.

---

## Research Task 2: Spec 022 Implementation Status

### Decision

Spec 022 targets are substantially implemented. The board endpoint (`board.py`) sets a 300-second cache TTL, clears sub-issue caches on manual refresh, and uses hash-based change detection. The polling loop (`polling_loop.py`) implements adaptive backoff (up to 300s max interval), rate-limit pause/slow/skip thresholds, and per-cycle cache clearing. The main remaining gaps are:

1. **WebSocket subscription refresh logic**: Still calls `get_project_tasks()` on each 30-second cycle even when idle — should short-circuit on cache hit.
2. **Fallback polling board invalidation**: The frontend SSE/polling fallback in `useRealTimeSync.ts` invalidates the board data query during polling cycles, which can trigger expensive full board refreshes.
3. **Duplicate repository resolution**: `workflow.py` contains its own repository resolution path that duplicates `utils.py`'s `resolve_repository()`, adding avoidable API calls.

### Rationale

Starting from a mostly-implemented baseline means the optimization work focuses on gap-filling rather than greenfield implementation. Each identified gap has a clear fix with minimal blast radius.

### Alternatives Considered

- **Re-audit and reimplement Spec 022 from scratch**: Rejected — the implementation is mostly correct. A full reimplementation would be wasteful and risky.
- **Ignore Spec 022 gaps and focus only on frontend**: Rejected — the backend gaps (especially fallback polling invalidation) directly contribute to frontend performance problems.

---

## Research Task 3: Frontend Query Invalidation Patterns

### Decision

The frontend uses TanStack React Query with clearly separated query keys: `['board', 'projects']` for the project list and `['board', 'data', projectId]` for board data. The `useProjectBoard` hook correctly avoids `refetchInterval` to prevent polling storms. However, `useRealTimeSync` invalidates the tasks query on every WebSocket message type (initial_data, refresh, task_update, task_created, status_changed), which can cascade to board data re-renders.

The optimization should:
1. Make `useRealTimeSync` only invalidate the tasks query for task-level changes (status, assignee, label) — not trigger board data refetch.
2. Ensure `useBoardRefresh.requestBoardReload()` is the only path that triggers full board data invalidation (via manual refresh or stale auto-refresh).
3. Stabilize the query data shape to prevent unnecessary re-renders from React Query's structural sharing.

### Rationale

The current architecture already separates concerns correctly between hooks. The fix is about tightening the invalidation scope — a surgical change in `useRealTimeSync` — rather than restructuring the hook hierarchy.

### Alternatives Considered

- **Merge all board queries into a single query**: Rejected — separate queries for project list and board data allow independent staleness management and reduce unnecessary refetches.
- **Use WebSocket messages to directly update query cache**: Rejected for first pass — this is the ideal pattern but requires backend to send full task payloads in WebSocket messages, which is a larger change. The simpler first step is to stop invalidating board data on task-level updates.
- **Add React Query's `select` option for derived data**: Considered for Phase 3 render optimization — `select` can stabilize derived state without `useMemo`. Evaluate during implementation.

---

## Research Task 4: Frontend Render Optimization Best Practices for React 19

### Decision

Apply standard React performance patterns for the board components:

1. **`React.memo` for `BoardColumn` and `IssueCard`**: These are the highest-frequency re-render units. Memoization prevents re-renders when props haven't changed.
2. **`useMemo` for derived data in `ProjectsPage`**: Sorting, filtering, and aggregation should be memoized based on source data identity.
3. **`useCallback` for event handlers**: Stabilize `onCardClick` and similar handlers passed to memoized children.
4. **`requestAnimationFrame` throttling for drag/resize listeners**: The `ChatPopup` resize handler and any drag-related positioning should be throttled to once per animation frame.

### Rationale

React 19 does not fundamentally change the memoization story — `React.memo`, `useMemo`, and `useCallback` remain the standard tools. The React compiler (React Forget) is experimental and not recommended for production use yet. These patterns are well-understood, low-risk, and measurable.

### Alternatives Considered

- **React Compiler (Forget)**: Rejected — still experimental, would add a dependency, and the team should understand what's being memoized rather than relying on automatic optimization.
- **Board virtualization**: Deferred to Phase 4 — virtualization (react-window, react-virtuoso) is high-impact but high-risk for the first pass. The spec explicitly defers this unless baseline results show large boards still regress after lighter fixes.
- **CSS `content-visibility: auto`**: Considered as a no-code alternative to virtualization for off-screen columns. Worth testing during implementation but not a primary strategy.
- **Signals or external state management (Zustand, Jotai)**: Rejected — TanStack Query already provides the needed state management. Adding another state layer adds complexity without clear benefit.

---

## Research Task 5: Sub-Issue Cache Reuse Strategy

### Decision

The current sub-issue cache uses per-issue keys (`sub_issues:{owner}/{repo}#{issue_number}`) with standard TTL. On manual refresh, `board.py` iterates all board items and deletes their sub-issue cache entries before fetching. On non-manual refreshes (auto-refresh, real-time updates), the sub-issue cache should be reused.

The gap: the board data fetch path in `service.py` may still fetch sub-issues on every board data call regardless of whether sub-issue caches are warm. The optimization should:
1. Check sub-issue cache before making external API calls during board data construction.
2. Only clear sub-issue caches on manual refresh (already implemented in `board.py`).
3. Track cache hit rates via log-level instrumentation to validate improvement.

### Rationale

Sub-issue fetches are individually cheap but multiply quickly — a 50-task board with 2 sub-issues each generates 100 additional API calls without caching. Even partial cache reuse (e.g., 60% hit rate) significantly reduces API consumption.

### Alternatives Considered

- **Batch sub-issue fetches into a single GraphQL query**: Considered for Phase 4 — this is the optimal solution but requires GraphQL query restructuring. For the first pass, per-issue caching with reuse is simpler and already partially implemented.
- **Prefetch sub-issues on initial board load**: Rejected — this front-loads all API calls to the initial load, making first-load slower. The cache-on-access pattern is preferable for perceived performance.
- **Remove sub-issue display from board view**: Out of scope — sub-issues are a core feature.

---

## Research Task 6: Fallback Polling Safety

### Decision

The fallback polling path has two components:
1. **Backend SSE endpoint** (`projects.py` `/events`): Polls every 10 seconds with heartbeat, serves stale data on failures. This is already reasonably safe.
2. **Frontend polling fallback** (`useRealTimeSync.ts`): When WebSocket fails, falls back to periodic HTTP polling. The current implementation invalidates the tasks query on each poll cycle, which can trigger cascading board data refreshes.

The fix: make the frontend polling fallback only invalidate task data (not board data), and only when the polled data actually differs from the cached version. This mirrors the WebSocket handler's hash-based change detection but at the frontend layer.

### Rationale

The frontend polling fallback currently treats every poll cycle as a potential change, which is the root cause of "polling storms" — each poll invalidates queries, causing React Query to refetch, which triggers another render cycle. By adding a client-side change comparison (e.g., comparing task list hashes), the fallback becomes as efficient as the WebSocket path.

### Alternatives Considered

- **Remove fallback polling entirely**: Rejected — the fallback exists for reliability when WebSocket is unavailable. Removing it would degrade the user experience on unreliable networks.
- **Server-side ETag/If-None-Match**: Considered — the backend could return 304 Not Modified on unchanged data. This is a clean solution but requires coordinated backend+frontend changes. Evaluate for second pass.
- **Increase polling interval**: Partial solution — longer intervals reduce frequency but don't address the fundamental problem of unnecessary invalidation. Combining longer intervals with change detection is the optimal approach.

---

## Research Task 7: Duplicate Repository Resolution Consolidation

### Decision

`workflow.py` contains repository-resolution logic that duplicates the shared `resolve_repository()` in `utils.py`. The consolidation should replace the workflow-specific resolution with a call to the shared utility, which already implements the 3-step fallback chain (in-memory cache → GitHub API → workflow config DB → env settings) with token-hashed caching.

### Rationale

Duplicate resolution paths mean duplicate API calls, inconsistent caching, and maintenance burden. The shared utility already handles all fallback scenarios and caches results with a 300-second TTL. Consolidation eliminates redundant external calls at zero risk.

### Alternatives Considered

- **Keep both paths but share the cache**: Rejected — this reduces API calls but doesn't address the maintenance burden of duplicate code. Full consolidation is simpler.
- **Defer consolidation to a separate feature**: Rejected — the change is small (replace one function call with another) and directly contributes to the performance goal. It should be part of this feature.

---

## Research Task 8: Event Listener Throttling Patterns

### Decision

Use `requestAnimationFrame` (rAF) throttling for high-frequency event listeners:
1. **ChatPopup resize handler**: Already has some debouncing but can be improved with rAF gating.
2. **Drag positioning (dnd-kit)**: dnd-kit already uses rAF internally for drag animations. No additional throttling needed unless custom listeners are added.
3. **Popover positioning (Radix UI)**: Radix manages its own positioning updates via Floating UI. No custom throttling needed.

Pattern:
```typescript
const throttledHandler = useCallback(() => {
  if (rafId.current) return;
  rafId.current = requestAnimationFrame(() => {
    // handle event
    rafId.current = null;
  });
}, [deps]);
```

### Rationale

rAF throttling is the standard pattern for visual updates — it aligns handler execution with the browser's paint cycle (~60fps), preventing wasted work between frames. It's a no-dependency solution that works with any event type.

### Alternatives Considered

- **lodash.throttle**: Rejected — adds a dependency for a one-line utility. rAF is native and more semantically correct for visual updates.
- **CSS `will-change` hints**: Complementary but doesn't reduce JavaScript execution frequency. Worth adding as a micro-optimization alongside rAF throttling.
- **Passive event listeners**: Already used by dnd-kit for touch events. Ensure any custom mouse/touch listeners also use `{ passive: true }` where appropriate.
