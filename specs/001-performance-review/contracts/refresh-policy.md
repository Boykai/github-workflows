# API Contracts: Performance Review

**Feature Branch**: `001-performance-review`  
**Date**: 2026-03-21

## Overview

This feature does not introduce new API endpoints. It modifies the behavior and contracts of existing endpoints. The contracts below document the expected behavior after optimization, focusing on cache semantics, refresh policies, and query invalidation rules.

---

## Contract 1: Board Data Endpoint

**Endpoint**: `GET /api/v1/board/projects/{project_id}`

### Request

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| `project_id` | `string` | Path | Yes | GitHub project ID |
| `refresh` | `boolean` | Query | No | When `true`, bypasses all caches (default: `false`) |

### Response (`BoardDataResponse`)

| Field | Type | Description |
|-------|------|-------------|
| `columns` | `BoardColumn[]` | Board columns with items |
| `rate_limit` | `RateLimitInfo \| null` | Current rate-limit budget |

### Cache Behavior Contract

| Scenario | `refresh` | Board Cache | Sub-Issue Caches | Response Source |
|----------|-----------|-------------|-------------------|-----------------|
| Auto-refresh / initial load | `false` | Checked (TTL=300s) | Preserved | Cache if warm; GitHub if expired |
| Manual refresh | `true` | Bypassed | Proactively cleared | Always GitHub |
| Rate-limited | `false` | Stale fallback | Preserved | Stale cache with rate-limit warning |

### Change Detection

- Board data hash is computed via `compute_data_hash()` excluding the `rate_limit` field.
- Hash is stored in `CacheEntry.data_hash` on each successful fetch.
- Consumers can compare hashes to detect whether data has actually changed.

---

## Contract 2: WebSocket Subscription

**Endpoint**: `WS /api/v1/projects/{project_id}/subscribe`

### Connection Flow

1. Client connects with session cookie.
2. Server validates session and project access.
3. Server sends `initial_data` message with full task list.
4. Server periodically checks for task changes (30-second interval).
5. Server sends `refresh` message only when task data hash changes.

### Message Types

| Type | Payload | Client Action |
|------|---------|---------------|
| `initial_data` | `{ tasks: Task[] }` | Invalidate `['projects', pid, 'tasks']` (debounced 2s) |
| `refresh` | `{ tasks: Task[] }` | Invalidate `['projects', pid, 'tasks']` |
| `task_update` | `{ task: Task }` | Invalidate `['projects', pid, 'tasks']` |
| `task_created` | `{ task: Task }` | Invalidate `['projects', pid, 'tasks']` |
| `status_changed` | `{ task: Task }` | Invalidate `['projects', pid, 'tasks']` |

### Change Detection Contract

- Server computes `compute_data_hash(tasks_payload)` on each periodic check.
- If hash matches the previously stored hash, the server does NOT send a `refresh` message (FR-005).
- If hash differs, the server sends a `refresh` message with the new task data.
- The `refresh_ttl()` method extends cache expiration without replacing the entry when data is unchanged.

### Client Invalidation Rules (FR-011, FR-012, FR-013)

| Message Source | Invalidates Tasks Query | Invalidates Board Query |
|----------------|------------------------|------------------------|
| WebSocket `task_update` | ✅ Yes | ❌ No |
| WebSocket `task_created` | ✅ Yes | ❌ No |
| WebSocket `status_changed` | ✅ Yes | ❌ No |
| WebSocket `refresh` | ✅ Yes | ❌ No |
| Fallback polling | ✅ Yes | ❌ No |
| Auto-refresh timer | ❌ No | ✅ Yes |
| Manual refresh | ❌ No | ✅ Yes (direct fetch) |

---

## Contract 3: Frontend Refresh Policy

### Query Ownership

| Query Key | Owner Hook | Refresh Trigger |
|-----------|-----------|-----------------|
| `['board', 'data', projectId]` | `useProjectBoard` | `useBoardRefresh` (auto/manual) |
| `['projects', projectId, 'tasks']` | (tasks query) | `useRealTimeSync` (WS/polling) |
| `['board', 'projects']` | `useProjectBoard` | Manual only (stale: 15min) |

### Refresh Timer Rules

| Condition | Auto-Refresh Timer | Manual Refresh |
|-----------|--------------------|----------------|
| WebSocket connected | ❌ Suppressed | ✅ Always available |
| WebSocket disconnected | ✅ Active (5-minute interval) | ✅ Always available |
| Tab hidden | ⏸️ Paused | ✅ Available on return |
| Tab visible + stale (>5min) | 🔄 Immediate refresh | ✅ Available |
| Rate-limit exhausted | ⏸️ Serves stale data | ✅ Attempts (may fail with warning) |

### Manual Refresh Priority (FR-014)

1. Cancel all in-flight board queries (`cancelQueries`).
2. Cancel any pending debounced reload.
3. Fetch fresh data with `refresh=true` (bypasses backend cache).
4. Write result directly to query cache (`setQueryData`).
5. Reset auto-refresh timer.

### Board Reload Debounce

- 2-second window (`BOARD_RELOAD_DEBOUNCE_MS`).
- Defers execution if a reload occurred within the last 2 seconds.
- Manual refresh bypasses debounce entirely.

---

## Contract 4: Rate Limit Budget Communication

### Backend → Frontend

The `rate_limit` field in `BoardDataResponse` communicates the current quota state:

```typescript
interface RateLimitInfo {
  limit: number;      // Total quota for the window
  remaining: number;  // Remaining calls
  reset_at: number;   // Unix timestamp for window reset
  used: number;       // Calls consumed
}
```

### Frontend Behavior by Quota Level

| Remaining | Frontend Behavior |
|-----------|-------------------|
| > 10 | Normal operation |
| ≤ 10 | `isRateLimitLow = true`; show low-quota warning |
| 0 (429 response) | Show rate-limit error with retry time; preserve cached data |

### Backend Polling Behavior by Quota Level

| Remaining | Polling Loop Behavior |
|-----------|----------------------|
| > 200 | Normal interval |
| ≤ 200 | Double polling interval |
| ≤ 100 | Skip expensive steps (agent outputs, stalled recovery) |
| ≤ 50 | Pause until rate-limit window resets |
