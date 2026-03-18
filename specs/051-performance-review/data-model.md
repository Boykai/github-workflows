# Data Model: Performance Review

**Feature**: `051-performance-review`
**Date**: 2026-03-18

---

## Entities

### Performance Baseline

A structured record of performance metrics captured before and after optimization work. Used to prove improvements and detect regressions.

**File**: `specs/051-performance-review/checklists/baseline.md` (tracked as a markdown checklist, not runtime data)

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `capture_date` | string | ISO 8601 timestamp of measurement | Must be valid ISO 8601 |
| `idle_api_calls_per_minute` | number | External API calls during 5-minute idle board session, averaged per minute | ≥0, target ≤2 |
| `board_load_tti_ms` | number | Time-to-interactive for board load with warm caches (ms) | ≥0, target 30% reduction |
| `board_load_tti_cold_ms` | number | Time-to-interactive for board load with cold caches (ms) | ≥0, informational |
| `sub_issue_fetch_count` | number | External sub-issue fetch calls during a non-manual board refresh | ≥0, target 40% reduction |
| `board_render_cycle_count` | number | React render cycles during board load (React Profiler) | ≥0, target reduction |
| `network_request_count` | number | Network requests during board load (DevTools) | ≥0, target reduction |
| `drag_fps` | number | Frame rate during card drag on 50+ card board | ≥0, target ≥30 |
| `polling_calls_per_interval` | number | External calls per polling interval during fallback mode | ≥0, target ≤1 |

**Validation Rules**:
- All numeric values must be non-negative
- `capture_date` must be a valid ISO 8601 timestamp
- Baseline must be captured before any optimization code changes

**State Transitions**: N/A (static measurement, no runtime state)

---

### Refresh Policy

Defines the rules governing when and how board data is refreshed. This is not a new data structure but a formalized contract for existing behavior across four refresh triggers.

**Triggers and Expected Behavior**:

| Trigger | Source | Invalidates Board Query | Bypasses Cache | Refreshes Sub-Issues |
|---------|--------|------------------------|----------------|---------------------|
| Real-time task update | WebSocket `task_update`, `status_changed` | No (tasks query only) | No | No |
| Real-time initial data | WebSocket `initial_data` | Yes (tasks query) | No | No |
| Fallback polling | HTTP poll cycle with change detection | Only if data changed | No | No |
| Auto-refresh timer | `useBoardRefresh` interval | Yes (background refetch) | No | No |
| Manual refresh | User button click | Yes (immediate) | Yes | Yes (clears cache) |

**Validation Rules**:
- Exactly one trigger type should be active for any given refresh action
- Manual refresh is the only trigger that clears sub-issue caches
- Fallback polling must not trigger board data refresh unless polled data differs from cached data
- Auto-refresh and real-time updates must never bypass the in-memory cache

---

### Cache Entry (Existing — Updated Behavior)

The `InMemoryCache` and `CacheEntry` classes in `solune/backend/src/services/cache.py` remain structurally unchanged. The performance review modifies behavior at the call site, not the cache implementation.

**Existing Fields** (no changes):

| Field | Type | Description |
|-------|------|-------------|
| `value` | T (generic) | Cached data |
| `expires_at` | float | Unix timestamp when entry becomes stale |
| `etag` | str \| None | Optional HTTP ETag for conditional requests |
| `last_modified` | str \| None | Optional Last-Modified header value |
| `data_hash` | str \| None | SHA-256 hash for change detection |

**Behavioral Changes**:
1. Sub-issue cache entries are reused during non-manual board refreshes (already partially implemented — verify and complete)
2. Board data cache entries use hash-based comparison to suppress duplicate WebSocket refresh messages (already implemented — verify)
3. Stale revalidation counter in WebSocket handler resets on verified-unchanged data (new behavior)

---

### WebSocket Message Types (Existing — Tightened Semantics)

The WebSocket subscription in `projects.py` sends messages to connected clients. The performance review tightens which message types trigger which frontend actions.

| Message Type | Backend Sends When | Frontend Action (Current) | Frontend Action (Optimized) |
|-------------|-------------------|--------------------------|----------------------------|
| `initial_data` | Client first connects | Invalidate tasks query | Invalidate tasks query (unchanged) |
| `refresh` | Task data hash differs from last sent | Invalidate tasks query | Invalidate tasks query (unchanged) |
| `task_update` | Individual task changed | Invalidate tasks query | Invalidate tasks query only, not board data |
| `task_created` | New task detected | Invalidate tasks query | Invalidate tasks query only, not board data |
| `status_changed` | Task status changed | Invalidate tasks query | Invalidate tasks query only, not board data |
| `ping` | Keep-alive interval | Pong response | Pong response (unchanged) |

**Key Change**: Task-level messages (`task_update`, `task_created`, `status_changed`) must not cascade to board data query invalidation. Board data is refreshed independently by `useBoardRefresh` on its own schedule.

---

## Relationships

```text
Performance Baseline ──measures──> Board (project board data)
Performance Baseline ──measures──> Cache (sub-issue cache hit rate)
Performance Baseline ──measures──> Polling Loop (idle API call rate)

Refresh Policy ──governs──> useRealTimeSync (WebSocket/polling path)
Refresh Policy ──governs──> useBoardRefresh (auto/manual refresh path)
Refresh Policy ──governs──> useProjectBoard (query ownership)

Cache Entry ──stores──> Board Data (board_data:{project_id})
Cache Entry ──stores──> Sub-Issue Data (sub_issues:{owner}/{repo}#{issue_number})
Cache Entry ──stores──> Project Items (project_items:{project_id})

WebSocket Message ──triggers──> React Query Invalidation (scoped by message type)
```
