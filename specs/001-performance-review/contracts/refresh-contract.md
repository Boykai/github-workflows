# Refresh Contract: Performance Review

**Feature**: 001-performance-review  
**Date**: 2026-03-22  
**Status**: Complete

## Overview

This document defines the refresh contract governing how data flows from the GitHub API through the backend cache to the frontend UI. The contract specifies which refresh triggers affect which data queries, ensuring lightweight task updates stay decoupled from expensive board data queries.

## Refresh Sources

| # | Source | Trigger | Frequency | Scope |
|---|--------|---------|-----------|-------|
| R1 | WebSocket `task_update` | Backend detects task change | Event-driven | Tasks only |
| R2 | WebSocket `task_created` | Backend detects new task | Event-driven | Tasks only |
| R3 | WebSocket `status_changed` | Backend detects status change | Event-driven | Tasks only |
| R4 | WebSocket `refresh` | Backend subscription loop (30s) | Periodic (suppressed if hash unchanged) | Tasks only |
| R5 | WebSocket `initial_data` | Connection established | Once per connection (debounced 2s) | Tasks only |
| R6 | Fallback polling | WebSocket unavailable | `WS_FALLBACK_POLL_MS` interval | Tasks only |
| R7 | Auto-refresh timer | `useBoardRefresh` timer | 5-minute interval (suppressed when WS connected) | Board data |
| R8 | Manual refresh | User clicks refresh button | User-initiated | Board data (cache bypass) |

## Query Invalidation Matrix

| Refresh Source | `['projects', projectId, 'tasks']` | `['board', 'data', projectId]` | `['board', 'projects']` | Backend Cache Bypass |
|----------------|:---:|:---:|:---:|:---:|
| R1: WS task_update | ✅ Invalidate | ❌ No touch | ❌ No touch | ❌ No |
| R2: WS task_created | ✅ Invalidate | ❌ No touch | ❌ No touch | ❌ No |
| R3: WS status_changed | ✅ Invalidate | ❌ No touch | ❌ No touch | ❌ No |
| R4: WS refresh | ✅ Invalidate | ❌ No touch | ❌ No touch | ❌ No |
| R5: WS initial_data | ✅ Invalidate (debounced 2s) | ❌ No touch | ❌ No touch | ❌ No |
| R6: Fallback polling | ✅ Invalidate | ❌ No touch | ❌ No touch | ❌ No |
| R7: Auto-refresh | ❌ No touch | ✅ Invalidate | ❌ No touch | ❌ No (serves from cache if TTL valid) |
| R8: Manual refresh | ❌ No touch | ✅ Refetch | ❌ No touch | ✅ Yes (`refresh=true`, clears sub-issue caches) |

## Backend Cache Contract

### Board Data Cache (`board_data:{project_id}`)

```
TTL: 300 seconds (5 minutes)
Stale Fallback: Yes (on rate limit or error)
Hash Comparison: Yes (SHA-256 of columns data, excluding rate_limit)
Manual Refresh: Bypasses cache, clears sub-issue caches, fetches fresh data
Auto/WS Refresh: Serves from cache if TTL valid
```

### Sub-Issue Cache (`sub_issues:{owner}:{repo}:{issue_number}`)

```
TTL: 600 seconds (10 minutes)
Stale Fallback: No (returns empty list on error)
Manual Refresh: Cache entries deleted before board data fetch
Auto/WS Refresh: Reused from cache (no deletion)
```

### WebSocket Subscription Data (`project:items:{project_id}`)

```
TTL: 300 seconds (5 minutes)
Stale Fallback: Yes (up to 10 stale cycles, then force refresh)
Hash Comparison: Required (suppress refresh message when hash unchanged)
Message Sent: Only when data hash differs from last-sent hash
```

## Frontend Refresh Policy

### Timer Coordination

```
1. WebSocket connected → Auto-refresh timer PAUSED
2. WebSocket disconnected → Auto-refresh timer RESUMES
3. WebSocket triggers refresh → Auto-refresh timer RESET
4. Tab hidden → Auto-refresh timer PAUSED
5. Tab visible + data stale → Immediate refresh
6. Manual refresh → Cancels any pending debounced reload
```

### Debounce Rules

```
1. WebSocket reconnect initial_data: 2-second debounce window
2. Board reload requests: 2-second debounce window (BOARD_RELOAD_DEBOUNCE_MS)
3. Manual refresh: Always bypasses debounce
4. Multiple concurrent refreshes: Deduplicated (only one executes)
```

## Rate Limit Contract

```
1. Backend detects rate limit (429 or 403 + X-RateLimit-Remaining: 0)
2. Backend returns stale cached data (if available) with rate_limit info
3. Frontend extracts rate_limit from response, shows warning if remaining < threshold
4. Polling loop pauses when remaining ≤ RATE_LIMIT_PAUSE_THRESHOLD
5. Polling loop skips expensive operations when remaining ≤ RATE_LIMIT_SKIP_EXPENSIVE_THRESHOLD
```

## Verification Checklist

- [ ] WebSocket `refresh` messages suppressed when data hash unchanged (FR-003, SC-001)
- [ ] Board endpoint serves cached data within TTL without API calls (FR-004, SC-002)
- [ ] Sub-issue caches reused on non-manual refresh (FR-005)
- [ ] Manual refresh bypasses cache and clears sub-issues (FR-006, SC-009)
- [ ] Fallback polling invalidates tasks query only (FR-007, SC-008)
- [ ] WebSocket updates invalidate tasks query only (FR-008)
- [ ] Auto-refresh suppressed when WebSocket connected (FR-009)
- [ ] Board reload debounced within 2-second window
- [ ] Rate limit exhaustion returns stale data gracefully (FR-014)
- [ ] Tab visibility correctly pauses/resumes auto-refresh
