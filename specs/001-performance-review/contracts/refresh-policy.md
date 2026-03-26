# Refresh Policy Contract

**Feature**: 001-performance-review  
**Date**: 2026-03-26  
**Governs**: FR-008, FR-009, FR-010, FR-011

## Purpose

Define the single coherent refresh policy that all refresh sources (WebSocket, polling fallback, auto-refresh, manual refresh) must follow. This contract eliminates duplicated or conflicting refetch behavior and ensures lightweight task updates remain decoupled from the expensive board-level query.

## Definitions

| Term | Definition |
|------|-----------|
| **Task Query** | TanStack Query key `['projects', projectId, 'tasks']`. Lightweight; fetches task list from cache-first endpoint. |
| **Board Query** | TanStack Query key `['board', 'data', projectId]`. Expensive; fetches full board structure with columns, items, and pipeline state. |
| **Selective Invalidation** | Invalidating only the Task Query, not the Board Query, for lightweight changes. |
| **Full Invalidation** | Invalidating both Task Query and Board Query; used only for structural board changes or manual refresh. |
| **Debounce Window** | 2-second deduplication window (`BOARD_RELOAD_DEBOUNCE_MS`) for concurrent refresh triggers. |

## Refresh Source Behavior

### 1. WebSocket Messages

| Message Type | Action | Queries Affected | Cache Behavior |
|-------------|--------|------------------|----------------|
| `initial_data` | Selective invalidation (debounced 2s) | Task Query only | Respect server cache |
| `refresh` | Selective invalidation (debounced 2s) | Task Query only | Respect server cache |
| `task_update` | Selective invalidation | Task Query only | Respect server cache |
| `task_created` | Selective invalidation | Task Query only | Respect server cache |
| `status_changed` | Selective invalidation | Task Query only | Respect server cache |
| `auto_merge_completed` | Selective invalidation | Task Query only | Respect server cache |
| `auto_merge_failed` | No query invalidation | None | N/A (notification only) |
| `devops_triggered` | No query invalidation | None | N/A (notification only) |

**Rule**: WebSocket messages MUST NOT invalidate the Board Query. Board data refreshes on its own timer.

### 2. Polling Fallback (WebSocket unavailable)

| Condition | Action | Queries Affected | Cache Behavior |
|-----------|--------|------------------|----------------|
| Poll cycle, no changes detected | No invalidation | None | Respect server cache |
| Poll cycle, task-level changes | Selective invalidation | Task Query only | Respect server cache |
| Poll cycle, structural changes | Full invalidation (debounced) | Task + Board Queries | Respect server cache |

**Rule**: Polling fallback MUST use the same selective invalidation pattern as WebSocket. It MUST NOT trigger full board reloads on every cycle.

### 3. Auto-Refresh Timer

| Condition | Action | Queries Affected | Cache Behavior |
|-----------|--------|------------------|----------------|
| WebSocket connected | Timer suppressed (no action) | None | N/A |
| WebSocket disconnected, timer fires | Board reload (debounced) | Board Query | Respect server cache |
| Tab hidden → restored, data stale | Board reload (debounced) | Board Query | Respect server cache |

**Rule**: Auto-refresh MUST be suppressed when WebSocket is connected. When active, auto-refresh targets the Board Query (which already has a 5-minute `staleTime` alignment with the backend 300s TTL).

### 4. Manual Refresh (user-initiated)

| Condition | Action | Queries Affected | Cache Behavior |
|-----------|--------|------------------|----------------|
| User clicks refresh | Full invalidation (immediate) | Task + Board Queries | Bypass all caches (`refresh=true`) |

**Rule**: Manual refresh MUST bypass all caches (frontend `staleTime` and backend TTL). It MUST NOT be debounced or deduplicated. It always takes precedence over any concurrent refresh.

### 5. Adaptive Polling (useProjectBoard refetchInterval)

| Condition | Action | Queries Affected | Cache Behavior |
|-----------|--------|------------------|----------------|
| WebSocket connected | Polling deferred (interval extended or paused) | None | N/A |
| WebSocket disconnected | Adaptive interval active | Board Query | Respect server cache (`staleTime: 1 min`) |

**Rule**: Adaptive polling in `useProjectBoard` SHOULD defer to WebSocket when connected. The `staleTime: 1 min` on the board query prevents redundant fetches even if the interval fires frequently.

## Precedence Rules

1. **Manual refresh** always wins. If a manual refresh is in-flight, all other refresh triggers are ignored.
2. **Debounce window** (2 seconds) deduplicates all non-manual refresh triggers that arrive within the window.
3. **WebSocket suppresses auto-refresh**. When WebSocket is connected, the auto-refresh timer is paused.
4. **WebSocket suppresses adaptive polling**. When WebSocket is connected, adaptive polling should extend its interval or pause.
5. **Selective over full**: Default to selective invalidation (Task Query only) unless the refresh source explicitly requires full invalidation.

## Anti-Patterns (MUST NOT)

1. **Polling storm**: Polling fallback MUST NOT invalidate the Board Query on every 30-second cycle.
2. **Broadcast invalidation**: WebSocket task updates MUST NOT trigger `queryClient.invalidateQueries()` with a broad key that matches both Task and Board queries.
3. **Double refresh**: Auto-refresh and adaptive polling MUST NOT both fire independently when WebSocket is disconnected — one mechanism should be the primary, the other deferred.
4. **Stale loop**: If the backend returns unchanged data (same hash), the frontend MUST NOT treat it as "new data" and trigger downstream invalidations.
