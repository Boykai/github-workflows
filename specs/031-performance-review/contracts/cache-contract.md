# Cache Contract: Performance Review

This document defines the target caching behavior for board data and sub-issues after the performance optimization changes.

## Cache Layers

### Layer 1: Backend In-Memory Cache (`backend/src/services/cache.py`)

The primary caching layer for board data and sub-issues. All cache operations are synchronous in-memory lookups.

#### Board Data Cache

```text
Key pattern:    board_data:{project_id}
TTL:            300 seconds (5 minutes)
Value:          Serialized board data (columns, cards, metadata)
Invalidation:   Manual refresh (refresh=true) OR TTL expiry

Lookup flow:
  GET /api/v1/board/{project_id}/data?refresh=false
    → cache.get("board_data:{project_id}")
    → if HIT and not expired: return cached value (0 API calls)
    → if MISS or expired: fetch from GitHub, cache.set(), return fresh value

  GET /api/v1/board/{project_id}/data?refresh=true
    → skip cache.get()
    → clear sub-issue caches for project (see below)
    → fetch from GitHub (full cost)
    → cache.set("board_data:{project_id}", fresh_data, ttl=300)
    → return fresh value
```

#### Sub-Issue Cache

```text
Key pattern:    sub_issues:{owner}/{repo}#{issue_number}
TTL:            600 seconds (10 minutes)
Value:          List of sub-issue data for the parent issue
Invalidation:   Manual refresh (clears all project sub-issue entries) OR TTL expiry

Lookup flow (within board data fetch):
  For each issue with sub-issues:
    → cache.get("sub_issues:{owner}/{repo}#{issue_number}")
    → if HIT and not expired: use cached sub-issues (0 API calls for this issue)
    → if MISS or expired: fetch from GitHub REST API, cache.set(), use fresh data

Manual refresh clear (in board.py):
  For each issue in board data:
    → cache.delete("sub_issues:{owner}/{repo}#{issue_number}")
  Result: next fetch for each issue will be a cache miss → fresh data
```

### Layer 2: TanStack Query Cache (Frontend)

Client-side cache managed by TanStack Query. Separate from backend cache.

#### Board Data Query

```text
Query key:      ['board', 'data', projectId]
Stale time:     Default (0 — always stale, refetch on window focus or invalidation)
GC time:        Default (5 minutes after last observer unmounts)
Refetch:        No refetchInterval — controlled by useBoardRefresh auto-refresh timer

Invalidation triggers:
  - Auto-refresh timer (5 min) → queryClient.invalidateQueries()
  - Manual refresh → queryClient.cancelQueries() + direct setQueryData()
  - NOT triggered by WebSocket updates or fallback polling
```

#### Tasks Query

```text
Query key:      ['projects', projectId, 'tasks']
Stale time:     Default
GC time:        Default
Refetch:        No refetchInterval — controlled by useRealTimeSync

Invalidation triggers:
  - WebSocket "refresh" message → queryClient.invalidateQueries()
  - WebSocket "initial_data" message → queryClient.invalidateQueries()
  - Fallback polling interval → queryClient.invalidateQueries()
  - Auto-refresh timer → transitively via board data refetch
  - Manual refresh → transitively via board data refetch
```

## Cache Interaction Diagram

```text
User Action / Event
        │
        ├── WebSocket update ──→ Invalidate tasks query ONLY
        │                         (board data untouched)
        │
        ├── Fallback poll ─────→ Invalidate tasks query ONLY
        │                         (board data untouched)
        │
        ├── Auto-refresh ──────→ Invalidate board data query
        │                         │
        │                         └─→ Backend: check board cache (300s TTL)
        │                              ├── HIT: return cached (0 API calls)
        │                              └── MISS: fetch fresh, check sub-issue cache per issue
        │                                   ├── Sub-issue HIT: use cached (0 API calls)
        │                                   └── Sub-issue MISS: fetch fresh (1 API call/issue)
        │
        └── Manual refresh ────→ Cancel in-flight queries
                                  │
                                  └─→ Backend: skip board cache, clear sub-issue caches
                                       └─→ Fetch fresh board + fresh sub-issues (full cost)
```

## TTL Alignment

| Cache | TTL | Rationale |
|-------|-----|-----------|
| Board data (backend) | 300s | Matches frontend 5-minute auto-refresh interval |
| Sub-issue data (backend) | 600s | 2× board TTL — survives two auto-refresh cycles without refetch |
| Board data (TanStack) | staleTime=0 | Always considered stale; refetch controlled by timer/manual |
| Tasks (TanStack) | staleTime=0 | Always considered stale; refetch controlled by WebSocket/polling |

## Invariants

1. **Sub-issue cache survives automatic refreshes**: Automatic board refreshes MUST check sub-issue cache before fetching. Only expired or missing entries trigger API calls.
2. **Manual refresh clears all caches**: Manual refresh (`refresh=true`) MUST bypass board cache AND clear all sub-issue cache entries for the project.
3. **Cache TTL alignment**: Board data backend TTL (300s) MUST equal the frontend auto-refresh interval (5 minutes / 300,000ms).
4. **Stale fallback on error**: If an upstream fetch fails, the backend MUST serve stale cached data rather than returning an error (use `cache.get_stale()`).
5. **No cache pollution**: Polling and WebSocket paths do NOT write to or invalidate the board data cache. Only the board endpoint manages its own cache.
