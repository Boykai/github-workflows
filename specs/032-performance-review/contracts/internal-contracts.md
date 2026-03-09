# Internal Contracts: Performance Review

**Feature**: 032-performance-review
**Date**: 2026-03-09

## Overview

This feature's performance optimization changes introduce no new API endpoints. All changes are internal behavioral modifications to existing endpoints, WebSocket handlers, cache strategies, rendering patterns, and event handlers. This document defines the behavioral contracts that must hold before and after optimization work.

## Contract 1: WebSocket Change Detection Contract

**Location**: `backend/src/api/projects.py` — WebSocket `/ws/projects/{project_id}/subscribe`
**Status**: Already implemented (Spec 022). Verified in this review.

### Behavior (verified current state):
- Every 30 seconds, fetches tasks and computes SHA-256 hash of serialized task list (`json.dumps(tasks_payload, sort_keys=True)`)
- Only sends `{"type": "refresh", ...}` if hash differs from `last_sent_hash`
- First cycle always sends (no previous hash to compare)
- Message format unchanged — no breaking changes to frontend contract

### Invariants:
- `initial_data` message on connection open: always sent (unchanged)
- `refresh` message: sent only when data has changed (hash comparison)
- `pong` response to `ping`: always sent (unchanged)
- Hash is per-connection, not shared across connections

### Success Criterion Alignment:
- SC-001: ≥50% reduction in idle API calls (WebSocket only sends when data changes)
- SC-009: Fallback polling does not trigger full board refreshes when data unchanged

## Contract 2: Frontend Query Invalidation Contract

**Location**: `frontend/src/hooks/useRealTimeSync.ts`
**Status**: Already implemented (Spec 022). Verified in this review.

### Behavior (verified current state):
- On `initial_data`, `refresh`, `task_update`, `task_created`, `status_changed` messages:
  - Invalidates `['projects', projectId, 'tasks']` ✅
  - Does NOT invalidate `['board', 'data', projectId]` ✅
- Board data refreshes on its own 5-minute `AUTO_REFRESH_INTERVAL_MS` schedule via `useBoardRefresh`
- `blocking_queue_updated` messages invalidate `['blocking-queue', projectId]` only

### Invariants:
- WebSocket messages never trigger board data re-fetch
- Manual refresh (user-initiated) still invalidates board data query key (separate code path in `useBoardRefresh`)
- Board data auto-refresh interval remains 5 minutes
- Reconnection debounce (2s) prevents cascading invalidation on WebSocket reconnect

### Success Criterion Alignment:
- SC-002: Single-card real-time update under 1 second without full board re-fetch
- SC-005: Single-card update causes ≤3 component re-renders

## Contract 3: Sub-Issue Cache Contract

**Location**: `backend/src/services/github_projects/service.py` — `get_sub_issues()`
**Status**: Already implemented (Spec 022). Verified in this review.

### Behavior (verified current state):
- Checks `InMemoryCache` for key `sub_issues:{owner}/{repo}#{issue_number}`
- On cache hit: returns cached value, no API call
- On cache miss: makes REST API call, caches result with 600s TTL, returns result
- Logs cache hit/miss events

### Cache Invalidation:
- TTL expiration: automatic after 600 seconds
- Manual refresh: board endpoint iterates all items and deletes per-issue sub-issue cache entries
- No cache invalidation on WebSocket messages or automatic refreshes

### Invariants:
- Automatic board refreshes always use cached sub-issue data when available
- Manual refresh always fetches fresh sub-issue data
- Partially cached sub-issues: only uncached entries are fetched (per-issue granularity)

### Success Criterion Alignment:
- SC-003: ≥80% reduction in sub-issue API calls via caching
- SC-010: Manual refresh bypasses all caches and returns fresh data

## Contract 4: Board Refresh Coordination Contract

**Location**: `frontend/src/hooks/useBoardRefresh.ts`
**Status**: Already implemented. Verified in this review.

### Refresh Policy:

| Trigger | Method | Cache Bypass | Timer Reset |
|---------|--------|-------------|-------------|
| Auto-refresh (5 min timer) | `invalidateQueries(['board', 'data', projectId])` | No (backend cache may hit) | No (timer continues) |
| Manual refresh (button click) | Direct `boardApi.getBoardData(projectId, true)` + `setQueryData` | Yes (`refresh=true`) | Yes (restarts 5-min timer) |

### Deduplication:
- `isRefreshingRef` boolean prevents concurrent refresh executions
- Multiple rapid `refresh()` calls result in only one actual API call
- Both `isRefreshingRef` (ref) and `isRefreshing` (state) are set/reset in try/finally

### Page Visibility:
- Tab hidden: auto-refresh timer paused
- Tab visible: check if data > 5 minutes old → immediate refresh if stale, then restart timer
- No refresh storms on rapid tab-switching (deduplication guards)

### Invariants:
- Manual refresh always bypasses backend cache (`refresh=true`)
- Manual refresh always resets auto-refresh timer
- Concurrent refresh calls are deduplicated
- Tab visibility changes do not create refresh storms

### Success Criterion Alignment:
- SC-006: Chat popup drag ≥30 fps (no interference from refresh)
- SC-010: Manual refresh returns fully fresh data

## Contract 5: Board Render Optimization Contract

**Location**: `frontend/src/components/board/BoardColumn.tsx`, `IssueCard.tsx`, `pages/ProjectsPage.tsx`
**Status**: Partially optimized. `BoardColumn` and `IssueCard` already use `React.memo`. Derived data memoization and callback stability are targets for this review.

### Current State:
- `BoardColumn` (Line 20): Wrapped in `React.memo` — shallow comparison on props
- `IssueCard` (Line 108): Wrapped in `React.memo` — shallow comparison on props
- `ProjectsPage`: Contains 20+ hooks; derived data (stats, sorting, aggregation) computed inline at render time

### Target State:
- Derived data in `ProjectsPage` wrapped in `useMemo` with appropriate dependencies
- Callbacks passed to `BoardColumn` and `IssueCard` stabilized via `useCallback` in parent
- Single-card update causes re-render of only: the affected `IssueCard`, its parent `BoardColumn`, and the board container — not all cards

### Invariants:
- `React.memo` on `BoardColumn` and `IssueCard` must not be removed
- `useMemo` must have correct dependency arrays (no stale data)
- `useCallback` must have correct dependency arrays (no stale closures)
- Board initial render time must not degrade (SC-004: within 10% of baseline)

### Success Criterion Alignment:
- SC-004: Board initial render time not degraded
- SC-005: Single-card update causes ≤3 component re-renders

## Contract 6: Event Listener Optimization Contract

**Location**: `frontend/src/components/chat/ChatPopup.tsx`, `frontend/src/components/board/AddAgentPopover.tsx`
**Status**: ChatPopup already optimized with RAF gating. AddAgentPopover needs RAF gating on scroll/resize.

### ChatPopup (verified current state):
- `onMouseMove`: `requestAnimationFrame` gating — `if (rafId) return` prevents multiple RAF callbacks
- `onMouseUp`: cancels pending RAF, persists size to localStorage
- Event listeners on `window`, cleaned up on unmount
- **No changes needed** — implementation is correct

### AddAgentPopover (target for optimization):
- Current: `scroll` and `resize` listeners call `updatePosition()` on every event without throttling
- Target: Add `requestAnimationFrame` gating (same pattern as ChatPopup) to prevent `getBoundingClientRect()` calls more than once per frame
- Cleanup: cancel pending RAF on unmount or `isOpen` change

### Invariants:
- ChatPopup drag maintains ≥30 fps during continuous drag movement
- AddAgentPopover repositions smoothly without triggering excessive layout recalculations
- All event listeners are cleaned up on unmount
- RAF callbacks are cancelled on cleanup

### Success Criterion Alignment:
- SC-006: Chat popup drag ≥30 fps
