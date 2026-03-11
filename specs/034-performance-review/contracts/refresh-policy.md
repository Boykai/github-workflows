# Contract: Unified Refresh Policy

**Feature**: 034-performance-review
**Date**: 2026-03-11
**Traces to**: FR-007, FR-008, FR-009, SC-003, SC-004

## Refresh Sources and Behavior

All data refresh operations follow a single coherent policy. Each refresh source maps to a defined scope and cache behavior:

| Source | Scope | Force (bypass cache) | Triggers Full Board Reload | Debounce Window |
|--------|-------|---------------------|---------------------------|-----------------|
| WebSocket `task_update` | task_only | No | No | 2s (initial_data only) |
| WebSocket `task_created` | task_only | No | No | 2s (initial_data only) |
| WebSocket `refresh` | task_only | No | No | None |
| WebSocket `initial_data` | task_only | No | No | 2s |
| Fallback polling (30s) | task_only | No | No | None |
| Auto-refresh (5 min) | board_data (non-forced) | No | Yes (non-forced, backend cache allowed) | None |
| Manual refresh (user) | full_board | Yes | Yes | None (dedup only) |

### Invariants

1. **No accidental full board reload from WebSocket/polling**: Only `manual` refresh and `auto-refresh` trigger a board data reload. WebSocket and polling MUST NOT invalidate the board data query.
2. **WebSocket/polling task-only invalidation**: WebSocket and polling events invalidate task-level queries (`['tasks', projectId]`) without touching board-level queries (`['board', projectId]`).
3. **Auto-refresh uses non-forced board invalidation**: Auto-refresh invalidates the board data query via `invalidateQueries` (non-forced), allowing the backend cache to serve fresh data without bypassing it. This is distinct from manual refresh which bypasses all caches.
4. **Manual refresh supremacy**: When a manual refresh is in progress, auto-refresh and polling events are either deduplicated or deferred until the manual refresh completes.
5. **No polling storm**: The transition from WebSocket to polling fallback MUST NOT trigger a burst of full board refreshes. Polling uses the same lightweight task-only invalidation as WebSocket.

## WebSocket → Polling Fallback Contract

```text
WebSocket connected:
  - Receives messages: task_update, task_created, refresh, initial_data
  - Each message invalidates task queries only
  - No board data invalidation

WebSocket disconnects:
  - Status transitions to 'polling'
  - Fallback polling starts at 30s interval
  - Each poll interval invalidates task queries only (same scope as WebSocket)
  - Reconnection attempts use exponential backoff (1s base, 30s max, jitter)

WebSocket reconnects:
  - Status transitions to 'connected'
  - Polling stops
  - No burst refresh on reconnection
```

### Measurement Contract (SC-004)

- **Metric**: `full_board_refreshes_during_idle_polling`
- **Observation window**: 5 minutes of fallback polling, no data changes
- **Target**: Zero full board data refreshes triggered by polling

## Auto-Refresh Contract

- **Interval**: 300,000ms (5 minutes)
- **Scope**: board_data (non-forced, backend cache allowed)
- **Page visibility**: Pauses when tab is hidden; force-refreshes when tab becomes visible if data is stale > 5 minutes
- **Interaction with manual refresh**: Timer resets after any manual refresh

## Deduplication Contract

- Concurrent refresh events from different sources are merged.
- Only one refresh operation executes at a time per scope.
- The highest-priority source wins: `manual` > `auto_refresh` > `polling` > `websocket`.
- Deduplicated events are logged for observability.

## First-Pass Verification Notes

- **Centralized query keys**: `boardDataKey`, `projectTasksKey`, `boardProjectsKey` exported from `useProjectBoard.ts` and used by `useRealTimeSync.ts` and `useBoardRefresh.ts` to prevent drift.
- **Polling fallback scope**: Confirmed task-only (`projectTasksKey`) — no board data invalidation from polling.
- **Auto-refresh scope**: Uses `boardDataKey` with `invalidateQueries` (non-forced, backend cache allowed). This is intentionally broader than task-only because the 5-minute auto-refresh is meant to keep board layout data reasonably fresh, while still respecting the backend's 300s cache TTL.
- **Manual refresh scope**: Uses `boardDataKey` with `cancelQueries` + `getBoardData(projectId, true)` + `setQueryData` (forced, bypasses all caches).
- **WebSocket/polling storm prevention**: WebSocket starts first; polling only activates on WS failure/close/timeout.
