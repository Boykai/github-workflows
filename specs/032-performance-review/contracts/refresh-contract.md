# Refresh Contract: Performance Review

**Feature**: 032-performance-review
**Date**: 2026-03-09
**Source**: [spec.md](../spec.md) FR-008 through FR-013, [research.md](../research.md) Areas 3-4

## Overview

Defines the refresh behavior contracts for the frontend refresh system. These contracts ensure that the four refresh channels (WebSocket, fallback polling, auto-refresh, manual refresh) operate under a single coherent policy without duplication, conflict, or unnecessary expensive operations.

## Contract 1: Refresh Channel Policy

**Location**: `frontend/src/hooks/useRealTimeSync.ts`, `frontend/src/hooks/useBoardRefresh.ts`, `frontend/src/hooks/useProjectBoard.ts`

### Single Coherent Policy

All refresh channels MUST follow this decision matrix:

| Channel | Trigger | Invalidation Target | Cache Bypass | Board Data Refetch |
|---------|---------|---------------------|--------------|-------------------|
| WebSocket message | Server push | Tasks query only | No | No (tasks only) |
| Fallback polling | Interval timer (WS unavailable) | Tasks query only | No | No (tasks only) |
| Auto-refresh | 5-minute timer | Board data query (via `invalidateQueries`) | No (uses backend cache) | Only if stale |
| Manual refresh | User button click | Board data + tasks queries | Yes (`refresh=true`) | Yes (forced) |

### Invariants

1. **WebSocket and fallback polling MUST NOT invalidate the board data query** (FR-008). They MUST only invalidate the tasks query to apply lightweight task-level updates.
2. **Auto-refresh MUST use TanStack Query's `invalidateQueries`** which respects `staleTime` and serves cached data when appropriate. It MUST NOT call the API with `refresh=true`.
3. **Manual refresh is the ONLY channel that bypasses all caches** (backend `refresh=true` parameter). It MUST invalidate both board data and tasks queries.
4. **Deduplication**: Multiple near-simultaneous refresh triggers MUST result in at most one board data refresh operation (FR-010, SC-005).

---

## Contract 2: Refresh Deduplication

**Location**: `frontend/src/hooks/useBoardRefresh.ts`

### Invariants

1. Concurrent manual refresh calls MUST share the same promise (existing behavior).
2. TanStack Query MUST deduplicate concurrent requests for the same query key (built-in behavior).
3. Manual refresh MUST cancel any in-progress auto-refresh before executing (existing behavior).
4. If a WebSocket message arrives during a manual refresh, the task query invalidation MUST be queued and applied after the refresh completes.

### Timing Contract

| Scenario | Expected Behavior |
|----------|-------------------|
| Manual + Manual (concurrent) | 1 API call total (promise sharing) |
| Manual + Auto-refresh (overlapping) | Auto-refresh cancelled, 1 manual API call |
| WebSocket + Poll (concurrent, WS available) | Poll suppressed (WS takes precedence) |
| WebSocket + Auto-refresh (concurrent) | Both execute independently: WS updates tasks, auto-refresh checks board staleness |
| 3+ triggers within 1 second | At most 1 board data refresh (SC-005) |

---

## Contract 3: Task Update Decoupling

**Location**: `frontend/src/hooks/useRealTimeSync.ts`

### Invariants

1. A lightweight task update (status change, assignee change, title change) arriving via any channel MUST NOT trigger a full board data query refresh (FR-008).
2. Task updates MUST be applied by invalidating the tasks-specific query key, allowing TanStack Query to refetch only the tasks data.
3. The board layout (columns, ordering, metadata) MUST remain stable during task-only updates — only the affected card's data changes.

### Message Type → Action Mapping

| WebSocket Message Type | Frontend Action | Board Data Query |
|----------------------|-----------------|------------------|
| `task_update` | Invalidate tasks query | Not invalidated |
| `task_created` | Invalidate tasks query | Not invalidated |
| `status_changed` | Invalidate tasks query | Not invalidated |
| `refresh` | Invalidate tasks query | Not invalidated |
| `initial_data` | Invalidate tasks query (debounced) | Not invalidated |
| `blocking_queue_updated` | Invalidate blocking-queue query | Not invalidated |

---

## Contract 4: Render Optimization

**Location**: `frontend/src/components/board/`, `frontend/src/pages/ProjectsPage.tsx`, `frontend/src/components/agents/AddAgentPopover.tsx`

### Invariants

1. **Callback stability**: All callback props passed to `React.memo()` components (BoardColumn, IssueCard) MUST be stable references (wrapped in `useCallback`) to prevent unnecessary child rerenders (FR-011).
2. **Derived state memoization**: Derived state (sorting, aggregation, grouping) MUST only recompute when input data changes (FR-012). Use `useMemo` with correct dependency arrays.
3. **Event listener throttling**: High-frequency event listeners (scroll, resize for popover positioning) MUST be throttled using `requestAnimationFrame` or equivalent (FR-013). They MUST NOT execute on every pixel/frame.

### Component Rerender Contract

| Event | Components That SHOULD Rerender | Components That MUST NOT Rerender |
|-------|-------------------------------|----------------------------------|
| Single card data change | Affected IssueCard, parent BoardColumn | Other BoardColumns, other IssueCards, ProjectsPage |
| Task status change via WS | Affected IssueCard | All BoardColumns (if column assignment unchanged) |
| Manual board refresh | All components (full data reload) | N/A (full refresh expected) |
| Popover scroll/resize | Popover portal only | Board components, other page elements |

---

## Contract 5: Page Visibility Integration

**Location**: `frontend/src/hooks/useBoardRefresh.ts`

### Invariants (existing, preserved)

1. Auto-refresh timer MUST pause when the browser tab is hidden.
2. On tab becoming visible, if data is older than the auto-refresh interval (5 minutes), an immediate refresh MUST fire.
3. On tab becoming visible, if data is fresh, the timer MUST resume from its last state.
4. Fallback polling (in `useRealTimeSync`) SHOULD also respect page visibility to avoid polling when the tab is backgrounded.
