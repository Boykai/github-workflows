# Refresh Contract: Board Data Refresh Policy

**Feature**: 037-performance-review  
**Date**: 2026-03-12  
**Version**: 1.0

## Purpose

Defines the single coherent refresh policy governing all board data update paths. All refresh sources (WebSocket, polling fallback, auto-refresh timer, manual refresh) must follow this contract to prevent duplicate refreshes, polling storms, and unnecessary backend load.

## Refresh Sources

### 1. WebSocket Real-Time Updates

**Trigger**: Server pushes a message via the WebSocket subscription channel.

**Contract**:
- Message types: `initial_data`, `refresh`, `task_update`, `task_created`, `status_changed`
- For `task_update`, `task_created`, `status_changed`: invalidate **only** the tasks query (`['projects', projectId, 'tasks']`). Do NOT invalidate the board data query.
- For `initial_data` and `refresh`: invalidate the tasks query. Board data manages its own refresh schedule.
- Debounce: Multiple WebSocket messages within 2 seconds are coalesced into a single invalidation.
- If the WebSocket message payload hash matches the current cached data hash, skip invalidation entirely.

**Backend behavior**:
- Server computes `compute_data_hash()` on each 30-second cycle.
- Server sends data to client **only** when hash differs from the previous cycle.
- Server uses cached data for periodic checks (does not bypass cache unless initial connection).

### 2. Polling Fallback

**Trigger**: WebSocket connection fails; polling activates at 30-second intervals.

**Contract**:
- Invalidate **only** the tasks query (`['projects', projectId, 'tasks']`). Do NOT invalidate the board data query.
- Before invalidating, compare the response data hash against the last known hash. If unchanged, skip invalidation.
- Polling must NOT trigger a full board data refresh under any circumstances (board data has its own 5-minute auto-refresh).
- Polling transitions back to WebSocket when reconnection succeeds.

### 3. Auto-Refresh Timer

**Trigger**: 5-minute (300,000ms) interval timer managed by `useBoardRefresh`.

**Contract**:
- Uses `invalidateQueries` on the board data query (`['board', 'data', projectId]`), allowing TanStack Query to background-refetch.
- Timer resets on manual refresh, project change, or page visibility resume.
- Timer pauses when the browser tab is hidden (Page Visibility API).
- Timer resumes on tab-visible; if data is stale (last refresh older than auto-refresh interval), triggers immediate refetch.
- Auto-refresh allows backend caches (does not set `refresh=true` on API call).

### 4. Manual Refresh

**Trigger**: User clicks the refresh button.

**Contract**:
- Cancel any in-flight board data requests (`cancelQueries`).
- Call `boardApi.getBoardData(projectId, forceRefresh=true)` — this sets `refresh=true` on the API call.
- Backend clears sub-issue caches for all board items before re-fetching.
- Backend bypasses board data cache and fetches fresh data from GitHub.
- Write result directly to TanStack Query cache (`setQueryData`), avoiding a redundant background refetch.
- Reset the auto-refresh timer.
- Manual refresh always wins over debounce — it bypasses the 2-second debounce window.

## Deduplication Rules

| Concurrent Events | Resolution |
|-------------------|------------|
| WebSocket + Auto-refresh within 2s | Debounce coalesces; one refetch executes |
| Polling + Auto-refresh within 2s | Debounce coalesces; one refetch executes |
| Manual refresh during auto-refresh | Manual wins; cancel auto-refresh in-flight |
| Manual refresh during WebSocket update | Manual wins; manual refresh bypasses debounce |
| Multiple WebSocket messages < 2s | Coalesced into single invalidation |
| Tab hidden → visible + auto-refresh due | Single refetch on visibility resume |

## Error Handling

| Error Type | Refresh Behavior |
|------------|-----------------|
| Rate limit (429) | Serve stale cached data; display rate limit warning; do not retry until reset_at |
| Auth error (401/403) | Display auth error; do not retry automatically |
| Server error (5xx) | Serve stale cached data if available; retry on next scheduled refresh |
| Network error | Serve stale cached data; fallback to polling if WebSocket; retry on next interval |

## Query Key Structure

```
['board', 'projects']                    → Projects list (stale time: 15 min)
['board', 'data', projectId]             → Board data (stale time: 60s, auto-refresh: 5 min)
['projects', projectId, 'tasks']         → Task list (invalidated by WS/polling)
```

## Non-Goals

- This contract does NOT define how individual task patches are applied (that is an implementation detail of the WebSocket message handler).
- This contract does NOT define backend-to-backend communication patterns (e.g., GitHub webhook handling).
- This contract does NOT define cache eviction policies beyond TTL-based expiration.
