# Data Model: Performance Review

**Feature Branch**: `056-performance-review`
**Date**: 2026-03-21
**Status**: Complete

## Overview

This feature does not introduce new data entities. It optimizes existing cache structures, refresh coordination state, and rendering data flow. This document captures the existing data structures being modified and the relationships between them.

## Entities

### 1. CacheEntry (existing — `solune/backend/src/services/cache.py`)

Represents a cached value with TTL and change-detection metadata.

| Field | Type | Description |
|-------|------|-------------|
| `value` | `Any` | The cached data (board data, project items, sub-issues) |
| `expires_at` | `float` | Unix timestamp when entry expires (now + TTL) |
| `etag` | `str | None` | HTTP ETag for conditional requests (optional) |
| `last_modified` | `str | None` | HTTP Last-Modified header (optional) |
| `data_hash` | `str | None` | SHA-256 hash of serialized value for change detection |

**Validation Rules**:
- TTL must be positive (default: 300 seconds)
- `data_hash` is computed via `compute_data_hash()` — SHA-256 of sorted JSON serialization
- Expired entries are still accessible via `get_stale()` for fallback scenarios

**State Transitions**:
- `FRESH` (within TTL) → `EXPIRED` (past TTL) → `EVICTED` (deleted or replaced)
- `refresh_ttl()` extends `expires_at` without replacing value (used when data hash unchanged)

---

### 2. Cache Keys (existing — `solune/backend/src/services/cache.py`)

Defines the namespace for all cached data relevant to board performance.

| Key Pattern | TTL | Used By | Description |
|-------------|-----|---------|-------------|
| `board_projects:{user_id}` | 300s | `board.py` | Filtered project list with status fields |
| `board_data:{project_id}` | 300s | `board.py` | Full board structure with columns and items |
| `projects:{user_id}` | 300s | `projects.py` | User's accessible projects |
| `project_items:{project_id}` | 300s | `projects.py` | All items for a project |
| `sub_issues:{owner}/{repo}#{issue_number}` | 300s | `service.py` (IssuesMixin) | Sub-issues for a specific issue |
| `resolve_repo:{token_hash}:{project_id}` | 300s | `utils.py` | Resolved (owner, repo) for a project |
| `repo_agents:{owner}/{repo}` | 300s | `cache.py` | Available agents for a repository |

**Optimization Targets**:
- Sub-issue cache: ensure reuse on non-manual board refreshes (FR-005)
- Board data cache: ensure hash-based TTL refresh when data unchanged (FR-003, FR-004)
- Repository resolution cache: already cached, no changes needed (R4 finding)

---

### 3. WebSocket Subscription State (existing — `solune/backend/src/api/projects.py`)

Per-connection state managed within `websocket_subscribe()`.

| Field | Type | Description |
|-------|------|-------------|
| `last_data_hash` | `str | None` | Hash of last data sent to client |
| `stale_revalidation_count` | `int` | Consecutive cycles served from stale cache |
| `connected` | `bool` | Whether WebSocket is still open |

**Refresh Cycle** (every 30 seconds):
1. Fetch items (cache-first)
2. Compute data hash
3. Compare with `last_data_hash`
4. If different → send refresh message, update hash
5. If same → refresh TTL only, increment stale counter
6. After 10 stale cycles → force fresh API call

---

### 4. Polling State (existing — `solune/backend/src/services/copilot_polling/polling_loop.py`)

Global polling state managing rate-limit-aware scheduling.

| Field | Type | Description |
|-------|------|-------------|
| `is_running` | `bool` | Whether polling loop is active |
| `_consecutive_idle_polls` | `int` | Counter for adaptive backoff |
| `poll_interval_seconds` | `int` | Base polling interval |
| `rate_limit_remaining` | `int | None` | Last known API quota remaining |
| `rate_limit_reset_at` | `datetime | None` | When quota resets |

**Rate-Limit Thresholds**:
- `RATE_LIMIT_PAUSE_THRESHOLD = 50` → Pause polling entirely
- `RATE_LIMIT_SLOW_THRESHOLD = 200` → Double poll interval
- `RATE_LIMIT_SKIP_EXPENSIVE_THRESHOLD = 100` → Skip expensive steps

**Adaptive Backoff**: `interval × 2^min(consecutive_idle, 3)`, capped at 300 seconds.

---

### 5. Frontend Query Cache (existing — TanStack Query)

Query keys and cache configuration for board-related data.

| Query Key | staleTime | Refresh Trigger | Description |
|-----------|-----------|-----------------|-------------|
| `['board', 'projects']` | `STALE_TIME_PROJECTS` | Manual only | Project list |
| `['board', 'data', projectId]` | `STALE_TIME_SHORT` | useBoardRefresh (5min timer), manual | Board columns and items |
| `['projects', projectId, 'tasks']` | Default | useRealTimeSync (WS/polling) | Project task list |

**Invalidation Policy** (optimization target — FR-008, FR-010):
- WebSocket `task_update`/`task_created`/`status_changed` → Invalidate tasks query only
- Polling fallback → Invalidate tasks query only (never board data)
- Manual refresh → Force-refresh board data (bypass server cache)
- Auto-refresh timer (5 min) → Invalidate board data query (may serve from TanStack cache)

---

### 6. Frontend Refresh State (existing — `useBoardRefresh.ts`)

State managed by the board refresh hook.

| Field | Type | Description |
|-------|------|-------------|
| `lastRefreshedAt` | `Date | null` | Timestamp of last successful refresh |
| `isRefreshing` | `boolean` | Whether a refresh is in progress |
| `isRateLimitLow` | `boolean` | Whether API quota is below warning threshold |
| `autoRefreshTimerId` | `number | null` | ID for the 5-minute interval timer |
| `debounceTimerId` | `number | null` | ID for the 2s reload debounce |

**Optimization Target**: Suppress auto-refresh when WebSocket connection is healthy (R5 finding).

## Relationships

```text
CacheEntry ──serves──> Board Data Query (frontend)
CacheEntry ──serves──> WebSocket Subscription (backend)
CacheEntry ──serves──> Polling Loop (backend)

WebSocket Subscription ──invalidates──> Tasks Query (frontend)
Polling Fallback ──invalidates──> Tasks Query (frontend)
Manual Refresh ──force-refreshes──> Board Data Query (frontend)
Auto-Refresh Timer ──invalidates──> Board Data Query (frontend)

Board Data Cache ──contains──> Sub-Issue Cache (per-item)
Manual Refresh ──clears──> Sub-Issue Cache (before fetch)
Non-Manual Refresh ──reuses──> Sub-Issue Cache (optimization target)
```

## No New Entities

This feature introduces no new database tables, API models, or frontend state stores. All changes optimize the behavior and coordination of existing structures documented above.
