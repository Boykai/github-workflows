# Data Model: Performance Review

**Feature**: 001-performance-review  
**Date**: 2026-03-22  
**Status**: Complete

## Overview

This feature does not introduce new persistent entities or data models. It optimizes the behavior of existing data flows — cache entries, WebSocket messages, query keys, and render cycles. This document describes the existing data entities relevant to the performance work and the behavioral contracts that the optimization must preserve.

## Existing Entities (No Schema Changes)

### 1. CacheEntry\<T\>

**Location**: `solune/backend/src/services/cache.py`

| Field | Type | Description |
|-------|------|-------------|
| `value` | `T` | Cached data payload |
| `expires_at` | `float` | Unix timestamp when entry expires |
| `etag` | `str \| None` | HTTP ETag for conditional requests |
| `last_modified` | `str \| None` | HTTP Last-Modified for conditional requests |
| `data_hash` | `str \| None` | SHA-256 hash of serialized data for change detection |

**Validation Rules**: `expires_at` must be a future timestamp at time of creation. `data_hash` is a 64-character hex string when present.

**State Transitions**: `fresh` → `stale` (when `time.time() > expires_at`) → `evicted` (when cleared or replaced)

**Optimization Relevance**: The `data_hash` field is the key mechanism for WebSocket change detection. When a new fetch produces a hash matching the cached hash, only the TTL is refreshed (no data re-storage, no message sent).

---

### 2. Board Data Response

**Location**: `solune/backend/src/api/board.py` (constructed inline)

| Field | Type | Description |
|-------|------|-------------|
| `columns` | `list[BoardColumn]` | Board columns with items |
| `rate_limit` | `RateLimitInfo \| None` | Current GitHub rate limit status |

**Board Column**:

| Field | Type | Description |
|-------|------|-------------|
| `name` | `str` | Column/status name |
| `items` | `list[BoardItem]` | Cards in this column |

**Board Item**:

| Field | Type | Description |
|-------|------|-------------|
| `item_id` | `str` | GitHub project item ID |
| `title` | `str` | Issue/PR title |
| `status` | `str` | Current status/column |
| `labels` | `list[str]` | Issue labels |
| `assignees` | `list[Assignee]` | Assigned users |
| `sub_issues` | `list[SubIssue]` | Nested sub-issues (cached separately at 600s TTL) |

**Optimization Relevance**: Content hash is computed over columns data (excluding `rate_limit`) for change detection. Sub-issues are cached independently to avoid refetching on every board request.

---

### 3. WebSocket Message Types

**Location**: `solune/backend/src/api/projects.py` → `solune/frontend/src/hooks/useRealTimeSync.ts`

| Message Type | Direction | Payload | Frontend Action |
|-------------|-----------|---------|-----------------|
| `initial_data` | Server → Client | Full task list | Invalidate tasks query (debounced 2s) |
| `refresh` | Server → Client | Updated task list | Invalidate tasks query |
| `task_update` | Server → Client | Updated task data | Invalidate tasks query |
| `task_created` | Server → Client | New task data | Invalidate tasks query |
| `status_changed` | Server → Client | Status change data | Invalidate tasks query |

**Optimization Relevance**: The `refresh` message is the target for hash-based suppression. When the server-side data hash is unchanged from the last sent message, the `refresh` message should be suppressed entirely (FR-003).

---

### 4. Frontend Query Keys

**Location**: Various hooks in `solune/frontend/src/hooks/`

| Query Key | Hook Owner | Stale Time | Refresh Trigger |
|-----------|-----------|------------|-----------------|
| `['board', 'projects']` | `useProjectBoard` | `STALE_TIME_PROJECTS` | Manual project list refresh |
| `['board', 'data', projectId]` | `useProjectBoard` | `STALE_TIME_SHORT` | Auto-refresh (5 min) or manual refresh |
| `['projects', projectId, 'tasks']` | External | N/A | WebSocket, polling, and real-time sync |

**Optimization Relevance**: The critical contract is that WebSocket/polling messages invalidate ONLY `['projects', projectId, 'tasks']` and never `['board', 'data', projectId]`. Board data refreshes exclusively via its own timer or manual user action.

---

### 5. Cache Keys (Backend)

**Location**: `solune/backend/src/constants.py` and inline in API handlers

| Cache Key Pattern | TTL | Used By |
|-------------------|-----|---------|
| `board_data:{project_id}` | 300s | Board endpoint |
| `sub_issues:{owner}:{repo}:{issue_number}` | 600s | Sub-issue fetches |
| `projects:user:{token_hash}` | 300s | Project list |
| `project:items:{project_id}` | 300s | WebSocket subscription loop |

**Optimization Relevance**: These TTLs are constants that should not change in the first pass. The optimization focuses on cache hit rates (reusing data within TTL) and cache bypass behavior (only on manual refresh).

## Relationships

```text
┌─────────────────┐     serves cached     ┌──────────────────┐
│  InMemoryCache   │◄────────────────────── │  Board Endpoint  │
│  (CacheEntry<T>) │                        │  (board.py)      │
└────────┬────────┘                        └────────┬─────────┘
         │                                          │
         │ hash comparison                          │ fetches
         ▼                                          ▼
┌─────────────────┐                        ┌──────────────────┐
│  WS Subscription │──── sends refresh ───►│  Frontend Query  │
│  Loop            │     (if hash changed) │  Client          │
│  (projects.py)   │                        │  (React Query)   │
└─────────────────┘                        └────────┬─────────┘
                                                    │
                                           invalidates tasks only
                                                    │
                                                    ▼
                                           ┌──────────────────┐
                                           │  Board Components │
                                           │  (memoized)       │
                                           └──────────────────┘
```

## State Transitions

### Board Data Lifecycle

```text
[No Data] ──► [Fresh Cache] ──► [Stale Cache] ──► [Evicted]
    │              │                  │                │
    │              │                  │                │
    ▼              ▼                  ▼                ▼
  First load    Serve from cache   Stale fallback   Force fetch
  (API call)    (no API call)      (on error/rate   (manual refresh
                                    limit)           clears + refetch)
```

### WebSocket Refresh Decision

```text
[Timer fires (30s)] ──► [Fetch/cache board data] ──► [Compute hash]
                                                          │
                                              ┌───────────┴───────────┐
                                              ▼                       ▼
                                        Hash unchanged           Hash changed
                                              │                       │
                                              ▼                       ▼
                                        Skip message             Send refresh
                                        (TTL refresh only)       message to client
```

## No New Models Required

This feature operates entirely on existing data structures. The optimization work modifies:
1. **Behavioral logic** (when to send messages, when to invalidate queries)
2. **Cache usage patterns** (reuse more, bypass less)
3. **Render efficiency** (memoize derivations, stabilize references)

No database migrations, new tables, new API response shapes, or new type definitions are required.
