# Frontend Refresh Policy Contract

**Feature**: 001-performance-review
**Date**: 2026-03-15
**Scope**: Defines the expected behavior of frontend refresh sources, their interactions, and the unified policy governing when board data is fetched or updated.

## Contract Parties

- **Producer**: Frontend hooks (`useRealTimeSync.ts`, `useBoardRefresh.ts`, `useProjectBoard.ts`)
- **Consumer**: Board UI components (`ProjectsPage.tsx`, `BoardColumn.tsx`, `IssueCard.tsx`)

## Refresh Source Hierarchy

The frontend has four refresh sources. They follow a strict priority hierarchy to prevent conflicting or redundant activity (FR-010):

| Priority | Source | Trigger | Board Data Action | Tasks Query Action |
|----------|--------|---------|-------------------|--------------------|
| 1 (highest) | Manual refresh | User click | Full fetch (`refresh=true`), cancel in-progress queries | N/A (board data includes tasks) |
| 2 | Auto-refresh timer | 5-minute interval | `invalidateQueries` (allows cache hit) | N/A |
| 3 | WebSocket update | Server push | No action (FR-008) | `setQueryData` (direct write) |
| 4 (lowest) | Fallback polling | 30-second interval | No action | `invalidateQueries` (refetch if stale) |

## Interaction Rules

### Rule 1: Manual Refresh Overrides Everything

When a manual refresh is initiated:
1. Cancel all in-progress board data queries
2. Cancel any pending debounced board reload
3. Call backend with `refresh=true` (bypasses cache, clears sub-issue caches)
4. Write result directly to TanStack Query cache via `setQueryData`
5. Reset the auto-refresh timer (extends the countdown by full 5 minutes)
6. Update `lastRefreshedAt` timestamp

**Test assertion**: Calling `refresh()` while a debounced reload is pending MUST cancel the pending reload and execute the manual refresh instead.

### Rule 2: Auto-Refresh Timer Management

- Timer fires every 5 minutes (300,000 ms)
- Timer is PAUSED when the browser tab is hidden (Page Visibility API)
- Timer RESUMES when the tab becomes visible; if the elapsed hidden time exceeds the auto-refresh interval, an immediate refresh is triggered
- Timer RESETS when:
  - Manual refresh completes (extends countdown)
  - `onRefreshTriggered` callback is called (by WebSocket events or polling)
  - `resetTimer()` is called explicitly by external code
- Timer STOPS when `projectId` becomes null (no active project)

**Test assertion**: After a manual refresh, the auto-refresh timer MUST NOT fire for at least the full interval duration.

### Rule 3: Board Reload Debouncing

External triggers (from hooks like `useRealTimeSync`) can request a board reload via `requestBoardReload()`:
- First call within a 2-second window executes immediately
- Subsequent calls within the same window are deferred until the window expires
- Manual refresh (`refresh()`) cancels any pending debounced reload
- At most one board reload executes per 2-second window

**Test assertion**: Three rapid `requestBoardReload()` calls within 2 seconds MUST result in at most two backend calls (one immediate, one deferred).

### Rule 4: WebSocket Updates Are Lightweight

When a WebSocket message arrives:
- `task_update`, `task_created`, `status_changed`: Update the tasks query cache directly via `setQueryData`. Do NOT invalidate or refetch board data (FR-008).
- `initial_data` (reconnection): Invalidate the tasks query only (not board data). Debounce rapid reconnection messages within a 2-second window.
- All WebSocket messages call `onRefreshTriggered` to reset the auto-refresh timer.

**Test assertion**: A `task_update` WebSocket message MUST NOT cause `invalidateQueries(['board', 'data', ...])` to be called.

### Rule 5: Fallback Polling Is Scoped

When the WebSocket connection is unavailable:
- Polling activates at 30-second intervals
- Polling invalidates only the tasks query `['projects', projectId, 'tasks']`
- Polling does NOT invalidate or directly fetch board data (FR-006)
- Polling calls `onRefreshTriggered` to reset the auto-refresh timer
- Polling STOPS immediately when WebSocket connects successfully

**Test assertion**: During fallback polling, `invalidateQueries` MUST only be called with the tasks query key, never with the board data query key.

### Rule 6: Transition Safety

When the system transitions between WebSocket and fallback polling:
- No duplicate refreshes during the transition (FR-010)
- No temporary spike in outbound calls
- Connection state changes are clean: WebSocket close → polling start, or polling stop → WebSocket open
- Reconnection attempts use exponential backoff: 1s → 2s → 4s → 8s → 16s (max)

**Test assertion**: Transitioning from WebSocket to polling MUST NOT produce more than one tasks query invalidation within the first 30 seconds.

## Component Rendering Contract

### Board Component Rerender Boundaries (FR-011, SC-006)

| Event | Expected Rerenders | NOT Expected to Rerender |
|-------|--------------------|--------------------------|
| Single task status change | The affected `IssueCard` + its `BoardColumn` | Other `BoardColumn` instances, other `IssueCard` instances |
| Task dragged between columns | Source `BoardColumn` + target `BoardColumn` + dragged `IssueCard` | Unaffected columns and cards |
| Popover opened | The popover component | Board columns, cards, page-level components |
| Auto-refresh (data unchanged) | None (cache hit, no state change) | Any board component |
| Manual refresh | All `BoardColumn` instances (new data) | Only after data arrives, not during loading |

### Derived Data Computation (FR-012)

| Computation | Frequency | Implementation |
|-------------|-----------|----------------|
| Grid template columns | Per column count change | `useMemo` with `[columns.length]` dependency |
| Hero stats (total items, project name) | Per board data change | `useMemo` with `[boardData]` dependency |
| Assigned pipeline lookup | Per pipeline data change | `useMemo` with `[savedPipelines, assignedPipelineId]` dependency |
| Stage assignment map | Per pipeline change | `useMemo` with `[assignedPipeline]` dependency |
| Board filtering/sorting/grouping | Per data or control change | `useBoardControls` hook with localStorage persistence |

**Test assertion**: Total item count aggregation MUST run only when board data changes, not on every render cycle.

### Event Listener Throttling (FR-013)

| Listener | Throttle Method | Maximum Frequency |
|----------|----------------|-------------------|
| Chat resize drag (`ChatPopup.tsx`) | `requestAnimationFrame` gate | ~60 Hz (frame rate) |
| Popover positioning (`AddAgentPopover.tsx`) | `requestAnimationFrame` gate | ~60 Hz (frame rate) |
| Board drag interaction (`@dnd-kit`) | Library-managed | Library default |

**Test assertion**: Window-level `mousemove` listeners during drag MUST be gated by RAF to prevent per-pixel handler execution.

## Query Key Registry

All TanStack Query keys used by the board feature, for reference:

| Query Key | Owner Hook | Stale Time | Refetch Behavior |
|-----------|-----------|------------|------------------|
| `['board', 'projects']` | `useProjectBoard` | `STALE_TIME_PROJECTS` | On mount, on invalidation |
| `['board', 'data', projectId]` | `useProjectBoard` | `STALE_TIME_SHORT` | On invalidation only (no refetchInterval) |
| `['projects', projectId, 'tasks']` | `useRealTimeSync` (consumer) | Default | On invalidation, on WebSocket setQueryData |

## Regression Test Assertions Summary

These assertions MUST be maintained by any future changes:

1. WebSocket task updates do not invalidate board data query
2. Fallback polling invalidates tasks query only, not board data
3. Manual refresh cancels in-progress queries and bypasses cache
4. Auto-refresh timer resets after manual refresh
5. Concurrent manual refresh calls are deduplicated
6. Board reload requests are debounced within 2-second window
7. Polling stops when WebSocket connects
8. Tab visibility pauses and resumes auto-refresh timer
9. Memoized components (`BoardColumn`, `IssueCard`) only rerender on prop changes
10. Derived data computations use `useMemo` with correct dependencies
