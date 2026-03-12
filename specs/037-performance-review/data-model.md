# Data Model: Performance Review

**Feature**: 037-performance-review  
**Date**: 2026-03-12  
**Status**: Complete

## Overview

This feature does not introduce new persistent data entities. It optimizes existing data flow and caching behaviors across backend and frontend. The entities below describe the runtime data structures and state machines that are the targets of optimization.

## Entities

### 1. BoardDataCache

**Description**: Server-side in-memory cache entry holding the full board dataset for a project.

| Field | Type | Description |
|-------|------|-------------|
| key | string | `"board_data:{project_id}"` |
| value | dict | Full board data (columns, items, metadata) |
| expires_at | datetime | UTC timestamp = created_at + TTL |
| ttl_seconds | int | 300 (5 minutes, aligned with frontend auto-refresh) |
| etag | string \| None | Optional HTTP ETag for conditional requests |

**Validation Rules**:
- TTL must be ≥ 60 seconds and ≤ 3600 seconds
- Value must be a valid board data structure (columns array with items)
- Cache key must include a non-empty project_id

**Relationships**:
- Contains references to SubIssueCache entries (one per board item with sub-issues)
- Referenced by BoardRefreshPolicy for invalidation decisions

---

### 2. SubIssueCache

**Description**: Server-side in-memory cache entry for sub-issue data associated with a single board item.

| Field | Type | Description |
|-------|------|-------------|
| key | string | `"sub_issues:{owner}/{repo}#{issue_number}"` |
| value | list[dict] | Array of sub-issue objects |
| expires_at | datetime | UTC timestamp = created_at + TTL |
| ttl_seconds | int | 300 (default, same as board data) |

**Validation Rules**:
- Owner and repo must be non-empty strings
- Issue number must be a positive integer
- Value must be a list (may be empty for items with no sub-issues)

**Relationships**:
- Referenced by BoardDataCache during board data construction
- Cleared by manual refresh path before re-fetching

---

### 3. DataChangeHash

**Description**: SHA-256 hash of serialized board/task data used for change detection in WebSocket and polling paths.

| Field | Type | Description |
|-------|------|-------------|
| hash_value | string | 64-character hex SHA-256 digest |
| data_source | enum | `"websocket"` \| `"polling"` \| `"auto_refresh"` |
| computed_at | datetime | UTC timestamp of computation |

**Validation Rules**:
- Hash must be computed with `sort_keys=True` JSON serialization for determinism
- Hash comparison must be case-insensitive (hex lowercase)

**Relationships**:
- Compared against previous hash to determine if refresh/send is needed
- Produced by `compute_data_hash()` in `backend/src/services/cache.py`

---

### 4. RefreshPolicy (Frontend)

**Description**: The unified set of rules governing when and how board data is refreshed, implemented across `useRealTimeSync`, `useBoardRefresh`, and `useProjectBoard` hooks.

| Field | Type | Description |
|-------|------|-------------|
| source | enum | `"websocket"` \| `"polling_fallback"` \| `"auto_refresh"` \| `"manual_refresh"` |
| action | enum | `"invalidate_tasks"` \| `"invalidate_board"` \| `"set_query_data"` \| `"skip"` |
| debounce_window_ms | int | 2000 (board reload debounce) |
| auto_refresh_interval_ms | int | 300000 (5 minutes) |
| polling_interval_ms | int | 30000 (30 seconds, fallback only) |

**State Transitions** (see below)

**Relationships**:
- Consumes DataChangeHash for skip decisions
- Drives TanStack Query cache operations (`invalidateQueries`, `setQueryData`, `cancelQueries`)

---

### 5. WebSocketConnection (Frontend)

**Description**: Runtime state of the real-time sync WebSocket connection managed by `useRealTimeSync`.

| Field | Type | Description |
|-------|------|-------------|
| status | enum | `"disconnected"` \| `"connecting"` \| `"connected"` \| `"polling"` |
| reconnect_delay_ms | int | Exponential backoff: base 1000, max 30000, with jitter |
| connection_timeout_ms | int | 5000 |
| last_update | Date \| null | Timestamp of last received update |
| consecutive_failures | int | Counter for backoff calculation |

**Validation Rules**:
- Reconnect delay must not exceed 30000ms
- Connection timeout must be ≥ 1000ms
- Fallback to polling activates after connection_timeout_ms without successful open

**Relationships**:
- Drives RefreshPolicy source selection (websocket vs polling_fallback)
- Provides status to UI for connection indicator display

---

### 6. PerformanceBaseline

**Description**: Recorded measurements captured before optimization work, used as reference for validation. Not persisted in production; captured in test artifacts and documentation.

| Field | Type | Description |
|-------|------|-------------|
| measurement_type | enum | `"idle_api_calls"` \| `"board_load_time"` \| `"render_count"` \| `"interaction_latency"` \| `"cache_hit_rate"` |
| value | float | Measured numeric value |
| unit | string | `"calls/5min"` \| `"ms"` \| `"count"` \| `"percent"` |
| captured_at | datetime | When the measurement was taken |
| board_size | int | Number of tasks on the measured board |
| context | string | Description of measurement conditions |

**Validation Rules**:
- Value must be ≥ 0
- Board size must be ≥ 0
- Context must describe the measurement environment (e.g., "idle board, 50 tasks, 5 columns")

---

## State Transitions

### Refresh Policy State Machine

```
                    ┌─────────────────────────────────────┐
                    │         BOARD DATA STATE             │
                    │                                       │
                    │  ┌─────────┐      ┌──────────────┐  │
                    │  │  FRESH  │─────▶│   STALE      │  │
                    │  │ (< 60s) │ time │ (60s-300s)   │  │
                    │  └────┬────┘      └──────┬───────┘  │
                    │       │                   │          │
                    │       │ ws_task_update     │ auto_refresh │
                    │       ▼                   ▼          │
                    │  ┌─────────────┐  ┌──────────────┐  │
                    │  │ PATCH ONLY  │  │  BACKGROUND  │  │
                    │  │ (setQuery)  │  │  REFETCH     │  │
                    │  └─────────────┘  └──────────────┘  │
                    │                                       │
                    │  ┌──────────────────────────────────┐│
                    │  │ MANUAL REFRESH                    ││
                    │  │ → cancel in-flight                ││
                    │  │ → bypass all caches               ││
                    │  │ → clear sub-issue caches          ││
                    │  │ → full reload + reset timer       ││
                    │  └──────────────────────────────────┘│
                    └─────────────────────────────────────┘
```

### Refresh Source → Action Mapping

| Source | Data Changed? | Action | Query Operation |
|--------|--------------|--------|-----------------|
| WebSocket task_update | Yes | Patch affected task | `setQueryData` on tasks query |
| WebSocket task_update | No (hash match) | Skip | None |
| Polling fallback | Yes (hash differs) | Invalidate tasks | `invalidateQueries` on tasks |
| Polling fallback | No (hash match) | Skip | None |
| Auto-refresh timer | Always | Background refetch | `invalidateQueries` on board |
| Manual refresh | Always | Full reload | `cancelQueries` → API call → `setQueryData` |
| Tab visibility (hidden→visible) | Stale check | Conditional refetch | `invalidateQueries` if stale |

### WebSocket Connection State Machine

```
  DISCONNECTED ──────▶ CONNECTING ──────▶ CONNECTED
       ▲                    │                  │
       │                    │ timeout/error     │ close/error
       │                    ▼                  ▼
       │               POLLING ◀──────────────┘
       │                    │
       │                    │ ws_retry (backoff)
       └────────────────────┘
```

## Entity Relationship Diagram

```
  ┌─────────────────┐       ┌──────────────────┐
  │ BoardDataCache  │──────▶│  SubIssueCache   │
  │ (server)        │ 1:N   │  (server)        │
  └────────┬────────┘       └──────────────────┘
           │
           │ produces
           ▼
  ┌─────────────────┐       ┌──────────────────┐
  │ DataChangeHash  │◀──────│  RefreshPolicy   │
  │ (server+client) │ uses  │  (client)        │
  └─────────────────┘       └────────┬─────────┘
                                     │
                                     │ driven by
                                     ▼
                            ┌──────────────────┐
                            │ WebSocketConnection│
                            │  (client)         │
                            └──────────────────┘
```
