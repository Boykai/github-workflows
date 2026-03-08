# Refresh Contract: Performance Review

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
**Cache bypass**: Backend uses `force_refresh=True` for the initial fetch only

### 3. Fallback Polling

**Trigger**: WebSocket connection failed; polling timer fires
**Frontend handler**: `useRealTimeSync.ts` → polling interval callback
**Behavior**:

```text
Frontend (on polling interval):
  queryClient.invalidateQueries({ queryKey: ['projects', projectId, 'tasks'] })
  # Do NOT invalidate: ['board', 'data', projectId]
  useBoardRefresh.resetTimer()  // Reset 5-min auto-refresh window
```

**Query invalidation scope**: Tasks ONLY
**Cache bypass**: None (standard TanStack Query refetch)
**Key constraint**: Fallback polling MUST NOT trigger full board data refreshes. Board data follows its own 5-minute auto-refresh schedule independently.

### 4. Auto-Refresh (5-Minute Timer)

**Trigger**: 5 minutes elapsed since last data update (any source)
**Frontend handler**: `useBoardRefresh.ts` → interval callback
**Behavior**:

```text
Frontend (on 5-min timer):
  queryClient.invalidateQueries({ queryKey: ['board', 'data', projectId] })
  # Board data refetch occurs through standard TanStack Query mechanics
  # Backend serves from cache if TTL is valid, fetches fresh if expired
```

**Query invalidation scope**: Board data (which transitively includes task data)
**Cache bypass**: None (backend cache checked first; only fetches if expired)

### 5. Manual Refresh (User Action)

**Trigger**: User clicks the refresh button
**Frontend handler**: `useBoardRefresh.ts` → manual refresh handler
**Behavior**:

```text
Frontend (on manual refresh):
  queryClient.cancelQueries({ queryKey: ['board', 'data', projectId] })  // Cancel in-flight auto
  fetch(`/api/v1/board/${projectId}/data?refresh=true`)
  # Backend: skip cache, clear sub-issue caches, fetch fresh from GitHub
  queryClient.setQueryData(['board', 'data', projectId], freshData)
  useBoardRefresh.resetTimer()  // Reset 5-min window
```

**Query invalidation scope**: Full board data (complete replacement)
**Cache bypass**: YES — `refresh=true` bypasses backend cache AND clears sub-issue caches

## Refresh Policy Summary

| Source | Tasks Invalidated | Board Invalidated | Backend Cache Bypassed | Sub-Issue Cache Cleared | Timer Reset |
|--------|:-:|:-:|:-:|:-:|:-:|
| WebSocket update | ✅ | ❌ | ❌ | ❌ | ✅ |
| WebSocket initial/reconnect | ✅ | ❌ | ✅ (force_refresh) | ❌ | ✅ |
| Fallback polling | ✅ | ❌ | ❌ | ❌ | ✅ |
| Auto-refresh (5 min) | ✅ | ✅ | ❌ | ❌ | ✅ |
| Manual refresh | ✅ | ✅ | ✅ | ✅ | ✅ |

## Invariants

1. **Board data isolation**: Only auto-refresh and manual refresh may invalidate the board data query. WebSocket updates and fallback polling MUST NOT.
2. **Timer reset on all updates**: Every data update (regardless of source) resets the 5-minute auto-refresh timer to prevent stale-data accumulation.
3. **Manual priority**: Manual refresh cancels any in-flight automatic refresh. If both complete, manual data wins (it's fresher).
4. **Reconnection debounce**: Multiple rapid WebSocket reconnections produce at most one task query invalidation per 2-second window.
5. **Idle silence**: When no data changes, WebSocket sends no messages and no query invalidations occur. The only scheduled activity is the 5-minute auto-refresh timer.
