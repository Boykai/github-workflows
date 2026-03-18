# Contract: Refresh Policy

**Feature**: `051-performance-review`
**Date**: 2026-03-18

---

## Overview

This contract defines the expected behavior of the board refresh system across all four refresh triggers. It serves as the single source of truth for how data flows from backend to frontend and when caches are used vs. bypassed.

## Refresh Triggers

### 1. Real-Time WebSocket Updates

**Backend** (`solune/backend/src/api/projects.py`):
- WebSocket handler checks for task changes every 30 seconds
- Uses `compute_data_hash()` to detect whether task data actually changed
- Only sends `refresh` message if hash differs from last sent
- Message types: `initial_data`, `refresh`, `task_update`, `task_created`, `status_changed`

**Frontend** (`solune/frontend/src/hooks/useRealTimeSync.ts`):
- On `initial_data`: invalidate tasks query
- On `refresh`: invalidate tasks query
- On `task_update`, `task_created`, `status_changed`: invalidate tasks query only
- **MUST NOT** invalidate board data query (`['board', 'data', projectId]`) on any WebSocket message
- Board data freshness is managed exclusively by `useBoardRefresh`

**Contract**:
```
GIVEN a WebSocket connection is active
WHEN a task-level message is received (task_update, task_created, status_changed)
THEN only the tasks query is invalidated
AND the board data query is NOT invalidated
AND the user's scroll position is preserved
AND any open popovers remain open
```

### 2. Fallback Polling

**Backend** (`solune/backend/src/api/projects.py` SSE endpoint):
- Polls every 10 seconds
- Sends heartbeat on each cycle
- Falls back to stale data on fetch failures

**Frontend** (`solune/frontend/src/hooks/useRealTimeSync.ts`):
- Activated when WebSocket connection fails
- **MUST** compare polled data against cached data before invalidating queries
- **MUST NOT** trigger board data refresh unless actual task changes are detected
- **MUST** maintain consistent polling intervals (no escalation)

**Contract**:
```
GIVEN fallback polling is active
WHEN a polling cycle finds no changes (same data hash)
THEN no query invalidation occurs
AND no network requests are triggered beyond the poll itself

GIVEN fallback polling is active
WHEN a polling cycle detects changed data
THEN only the tasks query is invalidated
AND the board data query is NOT invalidated
```

### 3. Auto-Refresh Timer

**Frontend** (`solune/frontend/src/hooks/useBoardRefresh.ts`):
- Fires at `AUTO_REFRESH_INTERVAL_MS` (typically 300,000ms = 5 minutes)
- Pauses when document is hidden (Page Visibility API)
- On visibility return, checks staleness before refreshing
- Uses `invalidateQueries` (background refetch, not immediate)

**Contract**:
```
GIVEN the auto-refresh timer fires
WHEN the board data is stale (older than AUTO_REFRESH_INTERVAL_MS)
THEN invalidateQueries is called for the board data query
AND the refresh happens in the background (not blocking UI)
AND cached sub-issue data is reused (cache NOT cleared)

GIVEN the user returns to a hidden tab
WHEN board data is stale
THEN an immediate background refresh is triggered
AND the auto-refresh timer is reset
```

### 4. Manual Refresh

**Frontend** (`solune/frontend/src/hooks/useBoardRefresh.ts`):
- Triggered by user clicking the refresh button
- Calls `boardApi.getBoardData` with `refresh=true`
- Cancels any pending auto-refresh or debounced reload

**Backend** (`solune/backend/src/api/board.py`):
- When `refresh=True`: clears all sub-issue cache entries for board items before fetching
- Forces fresh data from external API (bypasses board data cache)
- Returns fresh rate-limit info

**Contract**:
```
GIVEN the user triggers a manual refresh
WHEN the refresh request is sent with refresh=true
THEN all sub-issue caches for board items are cleared
AND board data is fetched fresh from external API (cache bypassed)
AND the board UI shows a loading indicator
AND on completion, all board data is replaced with fresh data
```

## Idle Board Behavior

**Contract**:
```
GIVEN a board is open with no user interaction and no data changes
WHEN five minutes elapse
THEN the system makes no more than 2 external API calls per minute on average

GIVEN a board is open and WebSocket is connected
WHEN the 30-second check interval fires and data is unchanged
THEN no external API call is made (served from cache)
AND no WebSocket message is sent to the client
```

## Deduplication

**Contract**:
```
GIVEN multiple refresh triggers fire within BOARD_RELOAD_DEBOUNCE_MS (2 seconds)
WHEN the debounce window has not elapsed since last reload
THEN only one refresh is executed
AND subsequent triggers within the window are deferred

GIVEN a manual refresh is in progress
WHEN an auto-refresh timer fires
THEN the auto-refresh is skipped
AND the timer is reset
```
