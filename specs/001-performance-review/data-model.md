# Data Model: Performance Review

**Feature**: 001-performance-review
**Date**: 2026-03-15
**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

## Overview

This feature does not introduce new persistent entities or database schema changes. It optimizes the runtime behavior of existing entities and their interactions. The data model below documents the key entities as they exist today, their relationships, and the state transitions relevant to the performance optimizations.

## Key Entities

### 1. BoardDataCache

**Source**: `solune/backend/src/services/cache.py` → `InMemoryCache` + `CacheEntry[T]`
**Used by**: `solune/backend/src/api/board.py`

| Field | Type | Description |
|-------|------|-------------|
| key | `str` | Cache key (e.g., `board:data:{project_id}`) |
| value | `BoardDataResponse` | Cached board data (columns, items, sub-items) |
| expires_at | `float` | Unix timestamp when entry expires |
| data_hash | `str \| None` | SHA-256 hash of content for change detection (FR-004) |
| ttl | `int` | Time-to-live in seconds (300s for board data) |

**Validation Rules**:
- TTL must be positive integer
- `data_hash` is 64-character hex string when present
- Expired entries are still servable via `get_stale()` for degraded-mode fallback

**Relationships**:
- One board data cache entry per `(project_id)` combination
- References zero or more `SubIssueCache` entries (invalidated together on manual refresh)

---

### 2. SubIssueCache

**Source**: `solune/backend/src/services/cache.py` → `InMemoryCache`
**Used by**: `solune/backend/src/api/board.py`, `solune/backend/src/services/github_projects/service.py`

| Field | Type | Description |
|-------|------|-------------|
| key | `str` | Cache key (e.g., `sub_issues:{issue_id}`) |
| value | `list[SubIssue]` | Cached sub-issue data for a parent issue |
| expires_at | `float` | Unix timestamp when entry expires |
| ttl | `int` | Time-to-live in seconds (inherits default from config) |

**Validation Rules**:
- Cleared on manual refresh (`refresh=True`) before board data fetch
- Reused on non-manual refreshes to reduce outbound API calls (FR-005, SC-002)

**Relationships**:
- Many sub-issue cache entries per board data cache entry (one per parent issue with sub-issues)

---

### 3. RealTimeSyncState

**Source**: `solune/frontend/src/hooks/useRealTimeSync.ts`
**Runtime only** (React hook state, not persisted)

| Field | Type | Description |
|-------|------|-------------|
| status | `'disconnected' \| 'connecting' \| 'connected' \| 'polling'` | Current sync connection state |
| lastUpdate | `Date \| null` | Timestamp of last received update |
| projectId | `string \| null` | Active project for sync subscription |
| reconnectAttempts | `number` | Count of consecutive reconnection attempts |
| isPolling | `boolean` | Whether fallback polling is active |

**State Transitions**:

```
disconnected ──→ connecting ──→ connected
      ↑               │              │
      │               ↓              ↓ (connection lost)
      │           (error) ──→ polling ──→ connecting (retry)
      │                              │
      └──────────────────────────────┘ (unmount / projectId null)
```

**Validation Rules**:
- WebSocket reconnection uses exponential backoff: 1s → 2s → 4s → 8s → 16s (max)
- Rapid reconnection messages debounced within 2-second window
- Polling fallback interval: 30 seconds
- Only invalidates tasks query, NOT board data query (FR-008)

---

### 4. BoardRefreshState

**Source**: `solune/frontend/src/hooks/useBoardRefresh.ts`
**Runtime only** (React hook state, not persisted)

| Field | Type | Description |
|-------|------|-------------|
| isRefreshing | `boolean` | Whether a manual refresh is in progress |
| lastRefreshedAt | `Date \| null` | Timestamp of last successful refresh |
| refreshError | `Error \| null` | Last refresh error (may contain rate-limit info) |
| rateLimitInfo | `RateLimitInfo \| null` | Extracted rate-limit state from responses |
| isRateLimitLow | `boolean` | Whether remaining budget < threshold (10) |

**State Transitions**:

```
idle ──→ refreshing (manual) ──→ idle (success / error)
  │
  └──→ auto-refresh (timer fires) ──→ idle (invalidation completes)
  │
  └──→ board-reload-requested (external trigger) ──→ idle
```

**Validation Rules**:
- Manual refresh cancels in-progress queries before starting
- Concurrent manual refresh calls are deduplicated (only one executes)
- Auto-refresh timer resets after manual refresh
- Timer pauses when tab is hidden (Page Visibility API)
- Board reload requests are debounced within 2-second window
- Manual refresh always wins over pending debounced reload (FR-009)

---

### 5. RefreshPolicy

**Logical entity** — not a single code artifact but the emergent behavior across hooks.

| Source | Trigger | Action | Bypasses Cache | Invalidates Board Data |
|--------|---------|--------|----------------|----------------------|
| Manual refresh button | User click | Full fetch with `refresh=true` | Yes | Yes (direct write) |
| Auto-refresh timer | 5-min interval | `invalidateQueries` | No (allows cache hit) | Yes (if stale) |
| WebSocket task update | Server push | `setQueryData` on tasks | N/A (direct write) | No |
| WebSocket initial_data | Reconnection | Invalidate tasks query | No | No |
| Fallback polling | 30-sec interval | Invalidate tasks query | No | No |

**Invariants** (FR-010):
- At most one refresh source should trigger a board data fetch in any 2-second window
- Manual refresh always takes priority and cancels other pending operations
- WebSocket updates and fallback polling never directly invalidate board data
- Auto-refresh timer resets when any other refresh source triggers activity

---

### 6. PerformanceBaseline

**Logical entity** — documented measurements, not stored in code.

| Metric | Category | Measurement Method | Target (post-optimization) |
|--------|----------|-------------------|---------------------------|
| Idle outbound calls (5 min) | Backend | Log grep / network capture | ≥ 50% reduction (SC-001) |
| Board refresh call count (cold) | Backend | Test assertion / log count | Baseline reference |
| Board refresh call count (warm) | Backend | Test assertion / log count | ≥ 30% fewer than cold (SC-002) |
| Single-task update latency | Frontend | Profiler / manual timing | < 2 seconds (SC-003) |
| Fallback polling unnecessary refreshes | Frontend | Network tab observation | Zero (SC-004) |
| Board interaction latency (50+ tasks) | Frontend | React Profiler | Measurable improvement (SC-005) |
| Single-task rerender scope | Frontend | React Profiler highlights | Card + container only (SC-006) |

## Entity Relationship Diagram

```
┌─────────────────────┐       invalidates on        ┌──────────────────┐
│   BoardDataCache     │───── manual refresh ────────│  SubIssueCache   │
│ (300s TTL, data_hash)│                             │ (per parent issue)│
└──────────┬──────────┘                              └──────────────────┘
           │ serves data to
           ▼
┌─────────────────────────────────────────────────────────────────┐
│                        RefreshPolicy                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────────┐  ┌─────────────┐ │
│  │  Manual   │  │  Auto    │  │  WebSocket   │  │  Fallback   │ │
│  │  Refresh  │  │  Timer   │  │  Updates     │  │  Polling    │ │
│  │ (full)    │  │ (5 min)  │  │ (task-only)  │  │ (30s, tasks)│ │
│  └──────────┘  └──────────┘  └──────────────┘  └─────────────┘ │
└──────────────────────────┬──────────────────────────────────────┘
                           │ drives UI state
                           ▼
┌─────────────────────┐         ┌─────────────────────┐
│ BoardRefreshState    │         │ RealTimeSyncState    │
│ (refresh, rate-limit)│         │ (connection, polling)│
└──────────┬──────────┘         └──────────┬──────────┘
           │                               │
           └───────────┬───────────────────┘
                       ▼
              ┌─────────────────┐
              │ Board UI Render  │
              │ (memoized cols   │
              │  + cards)        │
              └─────────────────┘
```
