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
| Auto-refresh (5 min) | task_only | No | No | None |
| Manual refresh (user) | full_board | Yes | Yes | None (dedup only) |

### Invariants

1. **No accidental full board reload**: Only `manual` refresh triggers a full board data reload. WebSocket, polling, and auto-refresh MUST NOT invalidate the board data query.
2. **Task-only invalidation**: WebSocket and polling events invalidate task-level queries (`['tasks', projectId]`) without touching board-level queries (`['board', projectId]`).
3. **Manual refresh supremacy**: When a manual refresh is in progress, auto-refresh and polling events are either deduplicated or deferred until the manual refresh completes.
4. **No polling storm**: The transition from WebSocket to polling fallback MUST NOT trigger a burst of full board refreshes. Polling uses the same lightweight task-only invalidation as WebSocket.

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
- **Scope**: task_only (non-forced)
- **Page visibility**: Pauses when tab is hidden; force-refreshes when tab becomes visible if data is stale > 5 minutes
- **Interaction with manual refresh**: Timer resets after any manual refresh

## Deduplication Contract

- Concurrent refresh events from different sources are merged.
- Only one refresh operation executes at a time per scope.
- The highest-priority source wins: `manual` > `auto_refresh` > `polling` > `websocket`.
- Deduplicated events are logged for observability.
