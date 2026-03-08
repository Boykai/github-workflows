# Refresh Contract: Performance Review — Balanced First Pass

This document defines the target refresh behavior between backend and frontend after the performance optimization changes. It serves as the single source of truth for how different refresh sources interact.

## Refresh Sources and Behavior

### 1. WebSocket Task Update

**Trigger**: Backend detects data change via SHA256 hash comparison on 30-second cycle
**Frontend handler**: `useRealTimeSync.ts` → `onMessage` callback
**Behavior**:

```text
Backend:
  current_hash = sha256(serialize(tasks))
  if current_hash != last_sent_hash:
    send({ type: "refresh", data: tasks })
    last_sent_hash = current_hash
  else:
    # No message sent — idle connection produces zero traffic

Frontend (on "refresh" message):
  queryClient.invalidateQueries({ queryKey: ['projects', projectId, 'tasks'] })
  # Do NOT invalidate: ['board', 'data', projectId]
  useBoardRefresh.resetTimer()  // Reset 5-min auto-refresh window
```

**Query invalidation scope**: Tasks ONLY
**Cache bypass**: None (tasks use standard TanStack Query stale/refetch)

### 2. WebSocket Initial Data (Connection/Reconnection)

**Trigger**: New WebSocket connection established or reconnection after drop
**Frontend handler**: `useRealTimeSync.ts` → `onMessage` callback for `initial_data` type
**Behavior**:

```text
Backend:
  tasks = await get_project_tasks(project_id, force_refresh=True)
  send({ type: "initial_data", data: tasks })
  last_sent_hash = sha256(serialize(tasks))

Frontend (on "initial_data" message):
  queryClient.invalidateQueries({ queryKey: ['projects', projectId, 'tasks'] })
  # Do NOT invalidate: ['board', 'data', projectId]
  useBoardRefresh.resetTimer()
  # Debounce: ignore additional initial_data within 2 seconds (reconnection guard)
```

**Query invalidation scope**: Tasks ONLY (debounced on rapid reconnections)
**Cache bypass**: Backend force-refreshes task cache; frontend does not bypass board cache

### 3. Fallback Polling (WebSocket Unavailable)

**Trigger**: WebSocket connection failed; polling at `WS_FALLBACK_POLL_MS` interval (30s)
**Frontend handler**: `useRealTimeSync.ts` → polling callback
**Behavior**:

```text
Frontend (on poll response):
  queryClient.invalidateQueries({ queryKey: ['projects', projectId, 'tasks'] })
  # Do NOT invalidate: ['board', 'data', projectId]
  useBoardRefresh.resetTimer()  // Same as WebSocket — maintain 5-min window
```

**Query invalidation scope**: Tasks ONLY
**Cache bypass**: None (polling uses standard cached backend responses)

### 4. Auto-Refresh (5-Minute Timer)

**Trigger**: `AUTO_REFRESH_INTERVAL_MS` (300,000ms = 5 minutes) elapsed since last refresh from any source
**Frontend handler**: `useBoardRefresh.ts` → timer callback
**Behavior**:

```text
Frontend (on timer fire):
  queryClient.invalidateQueries({ queryKey: ['board', 'data', projectId] })
  queryClient.invalidateQueries({ queryKey: ['projects', projectId, 'tasks'] })
  # Standard invalidation — TanStack Query refetches if stale
  # Backend serves from 300s cache if warm → no GitHub API calls
```

**Query invalidation scope**: Tasks AND Board Data
**Cache bypass**: None (backend serves cached data if TTL valid)
**Timer behavior**:
- Resets on WebSocket update, polling update, or manual refresh
- Pauses when browser tab is hidden (Page Visibility API)
- Resumes with freshness check when tab becomes visible

### 5. Manual Refresh (User Action)

**Trigger**: User clicks the refresh button
**Frontend handler**: `useBoardRefresh.ts` → manual refresh callback
**Behavior**:

```text
Frontend (on manual refresh):
  # Cancel any in-progress automatic refresh
  queryClient.cancelQueries({ queryKey: ['board', 'data', projectId] })

  # Fetch with cache bypass
  const freshData = await fetchBoardData(projectId, { refresh: true })
  queryClient.setQueryData(['board', 'data', projectId], freshData)

  # Also invalidate tasks
  queryClient.invalidateQueries({ queryKey: ['projects', projectId, 'tasks'] })

  # Reset auto-refresh timer
  startTimer()
```

**Query invalidation scope**: Tasks AND Board Data (board via direct fetch + setQueryData)
**Cache bypass**: YES — `refresh=true` query parameter bypasses backend board cache AND clears sub-issue caches
**Priority**: Highest — cancels any concurrent automatic refresh

## Summary Matrix

| Source | Tasks Invalidated | Board Invalidated | Backend Cache Bypass | Sub-Issue Cache Clear | Timer Reset |
|--------|:-:|:-:|:-:|:-:|:-:|
| WebSocket update | ✅ | ❌ | ❌ | ❌ | ✅ |
| WebSocket initial/reconnect | ✅ | ❌ | Task only | ❌ | ✅ |
| Fallback polling | ✅ | ❌ | ❌ | ❌ | ✅ |
| Auto-refresh (5 min) | ✅ | ✅ | ❌ | ❌ | ✅ |
| Manual refresh | ✅ | ✅ | ✅ | ✅ | ✅ |

## Deduplication Rules

1. **Manual beats automatic**: If manual refresh is triggered while automatic refresh is in-flight, the automatic refresh is cancelled via `queryClient.cancelQueries()`.
2. **Reconnection debounce**: Multiple WebSocket reconnections within 2 seconds produce at most one task invalidation (implemented in `useRealTimeSync.ts`).
3. **Timer reset on any update**: Any successful data update (from any source) resets the 5-minute auto-refresh timer, preventing redundant scheduled refreshes shortly after a data update.
4. **Stale-time gating**: TanStack Query's `staleTime` prevents re-fetching data that was just fetched, even if `invalidateQueries` is called.
