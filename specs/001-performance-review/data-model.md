# Data Model: Performance Review

**Feature**: 001-performance-review
**Date**: 2026-03-11

## Overview

This feature is a performance optimization pass, not a new data-persistence feature. There are no new database tables, columns, or migrations. The entities below are logical/runtime concepts that drive the implementation plan and refresh contract.

## Entities

### Performance Baseline

A point-in-time snapshot of measured system behavior, captured before optimization and repeated afterward for comparison.

| Field | Type | Description |
|-------|------|-------------|
| `capture_id` | string | Unique identifier for the baseline capture session |
| `captured_at` | ISO 8601 timestamp | When the baseline was recorded |
| `phase` | enum: `before` \| `after` | Whether this is a pre-change or post-change capture |
| `idle_board_refreshes_10min` | integer | Count of automatic full board refreshes during a 10-minute idle observation |
| `warm_refresh_upstream_requests` | integer | Count of upstream GitHub API calls for a repeated board refresh against warm cache |
| `fallback_poll_board_reloads_10min` | integer | Count of full board reloads triggered by fallback polling during a 10-minute observation |
| `p95_interaction_ms` | float | 95th-percentile interaction latency (ms) for in-scope board/chat interactions |
| `regression_suite_failures` | integer | Count of failing checks in the regression suite after changes |

**Validation Rules**:

- `idle_board_refreshes_10min` must be 0 in the `after` phase (SC-001).
- `warm_refresh_upstream_requests` must be ≥30% lower in `after` vs `before` (SC-002).
- `fallback_poll_board_reloads_10min` must be 0 in the `after` phase (SC-003).
- `p95_interaction_ms` must be ≤200 in the `after` phase (SC-005).
- `regression_suite_failures` must be 0 in the `after` phase (SC-006).

---

### Refresh Event

A runtime event representing any attempt to refresh board-related data, classified by source and outcome.

| Field | Type | Description |
|-------|------|-------------|
| `source` | enum: `websocket_task` \| `websocket_refresh` \| `fallback_poll` \| `auto_refresh` \| `manual_refresh` | Origin of the refresh event |
| `scope` | enum: `task_only` \| `full_board` | Whether the refresh targets task data or full board data |
| `deduplicated` | boolean | Whether this refresh was suppressed because another refresh of the same scope was in flight |
| `timestamp` | ISO 8601 timestamp | When the event occurred |

**State Transitions**:

```text
[websocket_task]       → scope: task_only     → invalidate tasks query
[websocket_refresh]    → scope: full_board*   → refetch board data (only if board data changed)
[fallback_poll]        → scope: task_only     → invalidate tasks query
[auto_refresh]         → scope: full_board    → refetch board data (debounced with websocket_refresh)
[manual_refresh]       → scope: full_board    → refetch board data (bypass cache, always executes)
```

*`websocket_refresh` is promoted to `full_board` only when server-side change detection confirms the board data actually changed. If unchanged, the event is suppressed.

---

### Board Cache Entry

An in-memory cached representation of board data in the backend TTL cache.

| Field | Type | Description |
|-------|------|-------------|
| `cache_key` | string | Composite key identifying the board + user context |
| `data` | object | Cached board response payload |
| `ttl_seconds` | integer | Time-to-live (default: 300) |
| `created_at` | float | Monotonic timestamp when entry was stored |
| `data_hash` | string | Hash of the board data payload, used for change detection |

**Validation Rules**:

- `data_hash` is computed on cache write and compared on WebSocket subscription refresh to suppress unchanged broadcasts.
- Entries expire after `ttl_seconds` and are eligible for stale fallback if the upstream is unavailable.

---

### Warm State

A derived concept: the board and its sub-issue data are both present in the backend cache and have not expired.

| Field | Type | Description |
|-------|------|-------------|
| `board_cached` | boolean | Whether the board data cache entry exists and is not expired |
| `sub_issues_cached` | boolean | Whether sub-issue data for the board's items is cached |
| `is_warm` | boolean | `board_cached AND sub_issues_cached` |

**Validation Rules**:

- When `is_warm` is true, a repeated board refresh must reuse cached data and avoid redundant upstream calls (FR-005).
- Manual refresh (`refresh=true`) bypasses warm state and forces a full upstream fetch (FR-008).

## Relationships

```text
Performance Baseline ──captures──▶ Refresh Event (aggregated counts)
Refresh Event ──targets──▶ Board Cache Entry (via cache_key)
Board Cache Entry ──determines──▶ Warm State (derived from cache presence + TTL)
Refresh Event ──governed by──▶ Refresh Contract (see contracts/refresh-contract.md)
```

## Notes

- No database schema changes are required. All entities above are runtime/observational.
- The `data_hash` field on Board Cache Entry is the key new concept enabling server-side change detection for WebSocket refresh suppression.
- The Performance Baseline entity is a measurement artifact (captured in documentation or test output), not a persisted data structure.
