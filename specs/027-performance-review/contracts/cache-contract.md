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
Key pattern:    sub_issues:{issue_node_id}
TTL:            600 seconds (10 minutes)
Value:          List of sub-issue data for the parent issue
Invalidation:   Manual refresh (clears all project sub-issue entries) OR TTL expiry

Lookup flow (within board data fetch):
  For each issue with sub-issues:
    → cache.get("sub_issues:{issue_node_id}")
    → if HIT and not expired: use cached sub-issues (0 API calls for this issue)
    → if MISS or expired: fetch from GitHub REST API, cache.set(), use fresh data

Manual refresh clear (in board.py):
  For each issue in board data:
    → cache.delete("sub_issues:{issue_node_id}")
  Result: next fetch for each issue will be a cache miss → fresh data
```

### Layer 2: TanStack Query Client Cache (Frontend)

The frontend caching layer managed by TanStack Query. Controls when React components re-fetch data.

#### Board Data Query

```text
Query key:      ['board', 'data', projectId]
Stale time:     STALE_TIME_SHORT (configured per hook)
Refetch:        Only on invalidation (no refetchInterval)
Invalidation:   Auto-refresh timer (5 min) OR manual refresh
                NOT invalidated by WebSocket updates or fallback polling

Cache behavior:
  - invalidateQueries triggers refetch only if data is stale
  - cancelQueries aborts in-flight requests (used by manual refresh)
  - setQueryData directly updates cache (used by manual refresh response)
```

#### Tasks Query

```text
Query key:      ['projects', projectId, 'tasks']
Stale time:     STALE_TIME_PROJECTS (configured per hook)
Refetch:        On invalidation from any refresh source
Invalidation:   WebSocket, polling, auto-refresh, OR manual refresh

Cache behavior:
  - Lightweight query — low API cost per refetch
  - Invalidated by all refresh sources (see refresh-contract.md)
  - Stale-time gating prevents redundant refetches
```

## TTL Alignment

```text
Frontend auto-refresh interval:  300,000 ms (5 minutes)
Backend board data cache TTL:    300 seconds (5 minutes)
Backend sub-issue cache TTL:     600 seconds (10 minutes)

Timeline for a single board viewing session:

  t=0s     Initial load: board data fetched, sub-issues fetched, both cached
  t=30s    WebSocket cycle: hash unchanged → no message → no invalidation
  t=60s    WebSocket cycle: hash unchanged → no message → no invalidation
  ...
  t=300s   Auto-refresh fires:
           → Backend board cache expired → fresh fetch from GitHub
           → Backend sub-issue cache still warm (TTL=600s) → served from cache
           → Net cost: ~3 API calls (board data only, no sub-issue calls)
  ...
  t=600s   Auto-refresh fires:
           → Backend board cache expired → fresh fetch from GitHub
           → Backend sub-issue cache expired → fresh fetch for each issue
           → Net cost: ~3 + N API calls (board + sub-issues)

  Manual refresh at any time:
           → All caches bypassed → full fresh fetch
           → Net cost: ~3 + N API calls (board + all sub-issues)
```

## Cache Cost Analysis

### Before Optimization (estimated from Spec 022 analysis)

```text
Per board refresh:       ~23 API calls (board + N sub-issues + M repo reconciliation)
Idle 5-min window:       ~500+ API calls (WebSocket-triggered cascading refreshes)
Per hour (idle):         ~1,000+ API calls
```

### After Optimization (target)

```text
Per board refresh:
  - Warm sub-issue cache:  ~3 API calls (board data only)
  - Cold sub-issue cache:  ~3 + N API calls (board + per-issue sub-issues)

Idle 5-min window:       ≤2 API calls (WebSocket heartbeat only, no board refresh)
Per hour (idle):         ~70-100 API calls (12 auto-refresh cycles × ~3-8 calls each)
```

### Cache Hit Rate Targets

| Cache | Target Hit Rate | Measurement |
|-------|:-:|---|
| Board data (automatic refresh) | ≥90% | Fraction of auto-refresh cycles served from warm cache |
| Sub-issue (automatic refresh) | ≥80% | Fraction of per-issue lookups served from cache |
| Sub-issue (manual refresh) | 0% | Manual refresh always clears sub-issue cache |

## Error Handling

| Scenario | Behavior |
|----------|----------|
| GitHub API error on cache miss | Use `cache.get_stale()` to serve expired data if available; return error only if no stale data |
| GitHub rate limit hit | Return 429 with Retry-After header; do not cache error responses |
| Cache corruption (unexpected value type) | Delete corrupted entry; fetch fresh data; log warning |
| Cache full (bounded dict capacity) | FIFO eviction of oldest entries (existing `BoundedDict` behavior) |
