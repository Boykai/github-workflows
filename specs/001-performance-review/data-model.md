# Data Model: Performance Review

**Feature Branch**: `001-performance-review`  
**Date**: 2026-03-21  
**Status**: Complete

## Overview

This feature modifies behavior of existing entities rather than introducing new data models. The entities below describe the existing structures relevant to performance optimization, their fields, relationships, validation rules, and state transitions affected by this work.

---

## Entity: Board Data Cache

**Purpose**: Server-side cached representation of board column and card data, keyed per project, with a configurable TTL. Used for auto-refresh responses and as a fallback during rate limiting.

### Fields

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| `cache_key` | `string` | `"board_data:{project_id}"` | Required; must match pattern `board_data:\w+` |
| `value` | `BoardDataResponse` | Full board data including columns and items | Required; must be valid Pydantic model |
| `expires_at` | `datetime` | Expiration timestamp (UTC) | Required; must be in the future at creation |
| `data_hash` | `string` | SHA-256 hash of board data (excluding rate-limit info) | Required on set; 64-char hex string |
| `etag` | `string \| None` | Optional HTTP ETag for conditional requests | Optional |
| `last_modified` | `string \| None` | Optional HTTP Last-Modified header value | Optional |

### Relationships

- **Contains** → `BoardColumn[]` → each contains `BoardItem[]`
- **References** → `SubIssueCache` (per board item with sub-issues)
- **Consumed by** → Board API endpoint (`GET /board/projects/{project_id}`)
- **Invalidated by** → Manual refresh (`refresh=True`) bypasses this cache entirely

### State Transitions

```
[Empty] → set(data, ttl=300s, hash) → [Warm]
[Warm] → get() within TTL → [Warm] (returns value)
[Warm] → TTL expires → [Expired]
[Expired] → get() → None; get_stale() → value
[Expired] → set(new_data, new_hash) → [Warm]
[Warm] → refresh_ttl() → [Warm] (extends expiration, preserves hash)
[Warm] → delete() → [Empty]
[Any] → manual refresh → [Empty] (board + sub-issue caches cleared)
```

---

## Entity: Sub-Issue Cache

**Purpose**: Separate cache layer for sub-issue data associated with board cards, with its own TTL. Cleared on manual refresh but preserved during auto-refresh to reduce API calls.

### Fields

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| `cache_key` | `string` | `"sub_issues:{owner}/{repo}#{issue_number}"` | Required; must match pattern |
| `value` | `list[SubIssue]` | List of child issues for a parent issue | Required |
| `expires_at` | `datetime` | Expiration timestamp (UTC) | Required |
| `ttl_seconds` | `int` | 600 (10 minutes) | Fixed; 2x board cache TTL |

### Relationships

- **Belongs to** → `BoardItem` (one sub-issue cache per board item with children)
- **Invalidated by** → Manual refresh only (not auto-refresh)
- **Populated by** → `get_sub_issues()` REST API call to GitHub

### State Transitions

```
[Empty] → get_sub_issues() → [Warm] (ttl=600s)
[Warm] → board auto-refresh → [Warm] (preserved, FR-007)
[Warm] → manual refresh → [Empty] (proactively deleted, FR-008)
[Warm] → TTL expires → [Expired]
[Expired] → next board fetch → [Warm] (re-fetched from GitHub)
```

---

## Entity: Content Hash

**Purpose**: SHA-256 hash of data payload used for change detection. Compared across refresh cycles to determine whether data has actually changed before notifying clients.

### Fields

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| `hash_value` | `string` | 64-character hex SHA-256 string | Required; computed via `compute_data_hash()` |
| `source_data` | `Any` | JSON-serializable data (sorted keys, `default=str`) | Must be deterministic |

### Usage Points

| Context | What Is Hashed | Excludes | Purpose |
|---------|---------------|----------|---------|
| WebSocket `send_tasks()` | Task list payload | N/A | Suppress refresh message when tasks unchanged |
| Board endpoint | `BoardDataResponse.model_dump()` | `rate_limit` field | Detect board data changes across cache cycles |

---

## Entity: Refresh Source

**Purpose**: Origin of a board refresh request. Each source follows different cache-bypass rules.

### Values and Rules

| Source | Cache Bypass | Sub-Issue Cache | Board Query Invalidated | Trigger |
|--------|-------------|-----------------|------------------------|---------|
| `manual` | Yes (board + sub-issue) | Cleared | Yes (direct fetch) | User clicks refresh button |
| `auto-timer` | No (uses cache if warm) | Preserved | Yes (via `invalidateQueries`) | 5-minute interval |
| `websocket` | No | Preserved | No (task query only) | WebSocket message |
| `fallback-polling` | No | Preserved | No (task query only) | 30-second fallback interval |

### Frontend Query Key Mapping

| Query Key | Invalidated By |
|-----------|---------------|
| `['board', 'data', projectId]` | Manual refresh, auto-timer |
| `['projects', projectId, 'tasks']` | WebSocket messages, fallback polling |
| `['board', 'projects']` | Manual project list refresh only |

---

## Entity: Rate Limit Budget

**Purpose**: Remaining GitHub API quota available for the current rate-limit window. Used to gate expensive operations and trigger fallback behavior.

### Fields

| Field | Type | Description | Source |
|-------|------|-------------|--------|
| `limit` | `int` | Total quota for the rate-limit window | `X-RateLimit-Limit` header |
| `remaining` | `int` | Remaining calls in the current window | `X-RateLimit-Remaining` header |
| `reset_at` | `int` | Unix timestamp when the window resets | `X-RateLimit-Reset` header |
| `used` | `int` | Calls consumed (`limit - remaining`) | Computed |

### Thresholds (Polling Loop)

| Threshold | Value | Action |
|-----------|-------|--------|
| `RATE_LIMIT_PAUSE_THRESHOLD` | 50 | Sleep until reset window; abort cycle |
| `RATE_LIMIT_SKIP_EXPENSIVE_THRESHOLD` | 100 | Skip expensive steps (agent outputs, stalled recovery) |
| `RATE_LIMIT_SLOW_THRESHOLD` | 200 | Double polling interval |

### Storage

- **Request-scoped**: `_request_rate_limit` contextvar (thread-safe, per-request)
- **Instance fallback**: `GitHubProjectsService._last_rate_limit` (for background tasks)
- **Client-side**: `RateLimitInfo` in board response, tracked by `useBoardRefresh`

---

## Relationships Diagram

```
┌─────────────────────────────────────────────────────────┐
│                    Board Data Flow                        │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  [Frontend]                                              │
│    ProjectsPage                                          │
│      ├── useProjectBoard ──→ ['board','data',pid]        │
│      │     └── query (stale: 1min, no refetchInterval)   │
│      ├── useRealTimeSync ──→ ['projects',pid,'tasks']    │
│      │     ├── WebSocket messages → invalidate tasks     │
│      │     └── Fallback polling → invalidate tasks       │
│      └── useBoardRefresh                                 │
│            ├── Auto-refresh (5min) → invalidate board    │
│            └── Manual refresh → direct fetch + cache set │
│                                                          │
│  [Backend]                                               │
│    Board API                                             │
│      ├── Cache lookup (board_data:{pid}, TTL=300s)       │
│      ├── Hash comparison (change detection)              │
│      └── Sub-issue cache (sub_issues:o/r#n, TTL=600s)   │
│    WebSocket                                             │
│      ├── Periodic task fetch (30s)                       │
│      ├── Hash comparison → suppress if unchanged         │
│      └── Stale fallback (10-cycle limit)                 │
│    Polling Loop                                          │
│      ├── Rate-limit gating (3 thresholds)                │
│      ├── Sub-issue filtering                             │
│      └── Dynamic interval adjustment                     │
│                                                          │
└─────────────────────────────────────────────────────────┘
```
