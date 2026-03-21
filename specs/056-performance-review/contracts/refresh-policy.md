# Refresh Policy Contract: Performance Review

**Feature Branch**: `056-performance-review`
**Date**: 2026-03-21
**Status**: Complete

## Overview

This document defines the unified refresh policy governing how board data is updated across all refresh sources. The policy ensures that lightweight task updates do not trigger expensive full board reloads, and that all refresh paths follow a single coherent strategy.

## Refresh Sources

### 1. WebSocket Real-Time Updates

**Trigger**: Server pushes `task_update`, `task_created`, `status_changed`, or `refresh` message.

**Behavior**:
- Invalidate the tasks query (`['projects', projectId, 'tasks']`) only.
- Do NOT invalidate or refetch the board data query.
- Debounce `initial_data` messages within a 2-second window to prevent reconnection storms.

**Backend Contract**:
- WebSocket subscription sends refresh messages only when `compute_data_hash()` detects a data change.
- Unchanged data triggers `cache.refresh_ttl()` instead of a new cache write.
- Maximum one upstream API call per 30-second refresh cycle (cache-first).

### 2. Polling Fallback

**Trigger**: WebSocket connection fails; polling activates as fallback.

**Behavior**:
- Invalidate the tasks query (`['projects', projectId, 'tasks']`) only.
- NEVER invalidate board data during polling fallback (FR-006, SC-003).
- Polling interval follows existing adaptive schedule.

**Backend Contract**:
- `get_project_items()` checks cache before making upstream calls.
- Polling loop respects rate-limit thresholds (PAUSE at ≤50, SLOW at ≤200, SKIP_EXPENSIVE at ≤100).

### 3. Auto-Refresh Timer

**Trigger**: 5-minute interval timer fires (managed by `useBoardRefresh`).

**Behavior**:
- Invalidate the board data query (`['board', 'data', projectId]`).
- Uses `invalidateQueries` (TanStack Query decides if refetch is needed based on `staleTime`).
- Does NOT bypass server-side cache (`forceRefresh=false`).

**Optimization** (new): Suppress auto-refresh timer when WebSocket connection is healthy and actively delivering updates. Resume timer when WebSocket disconnects.

### 4. Manual Refresh

**Trigger**: User clicks the refresh button.

**Behavior**:
- Cancel all in-progress board data queries.
- Cancel any pending debounced reload.
- Force-refresh board data: call `getBoardData(projectId, true)` which bypasses server cache.
- Server clears sub-issue caches before fetching fresh data.
- Reset the auto-refresh timer after completion.

**Backend Contract**:
- `refresh=True` parameter causes `board.py` to skip cache reads and delete sub-issue caches.
- Fresh data is written to cache with new TTL and data hash.

### 5. Page Visibility Resume

**Trigger**: User returns to the tab (Page Visibility API `visibilitychange` event).

**Behavior**:
- Check if data is stale (last refresh > staleTime).
- If stale: trigger an auto-refresh (same as #3, not a manual refresh).
- Resume the auto-refresh timer.

## Priority Rules

When multiple refresh sources fire simultaneously:

1. **Manual refresh always wins**: Cancels pending auto-refresh and debounced reloads.
2. **Debounced reload deduplication**: Rapid `requestBoardReload()` calls coalesced within 2-second window.
3. **Auto-refresh is advisory**: TanStack Query may serve from cache if data is within `staleTime`.
4. **Reconnection coalescing**: Multiple WebSocket reconnections within 2 seconds produce only one `initial_data` invalidation.

## Data Flow Diagram

```text
┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│  WebSocket Msg   │    │  Polling Cycle   │    │  Manual Refresh  │
│  (task_update,   │    │  (fallback only) │    │  (user action)   │
│   status_changed)│    │                  │    │                  │
└────────┬─────────┘    └────────┬─────────┘    └────────┬─────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌────────────────────────────────────────────────────────────────────┐
│                    Refresh Policy Router                          │
│                                                                    │
│  WS/Polling → invalidate tasks query ONLY                         │
│  Manual     → cancel queries + force-refresh board data           │
│  Auto-timer → invalidate board data (cache-aware)                 │
└────────────────────────────────────────────────────────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│  Tasks Query     │    │  Tasks Query     │    │  Board Data      │
│  (lightweight)   │    │  (lightweight)   │    │  (full reload)   │
└──────────────────┘    └──────────────────┘    └──────────────────┘
```

## Verification Criteria

| Scenario | Expected Behavior | How to Verify |
|----------|-------------------|---------------|
| WS task update arrives | Tasks query invalidated, board data untouched | Network tab shows no board data request |
| Polling fallback detects change | Tasks query invalidated, board data untouched | Network tab shows no board data request |
| 5-min auto-refresh fires | Board data query invalidated (cache-aware) | Network tab shows conditional request |
| User clicks refresh | Board data force-refreshed, sub-issue caches cleared | Network tab shows full board request with `refresh=true` |
| WS reconnects rapidly | Single `initial_data` invalidation (2s debounce) | Console shows debounce message |
| Tab becomes visible after 10 min | Auto-refresh triggered (not manual) | Network tab shows regular (not forced) request |
| Manual refresh during auto-refresh | Auto-refresh cancelled, manual takes precedence | Only one board data request completes |
