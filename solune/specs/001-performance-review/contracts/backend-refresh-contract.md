# Backend Refresh Contract

**Feature**: 001-performance-review
**Date**: 2026-03-15
**Scope**: Defines the expected behavior of backend board-data endpoints and caching layers with respect to refresh semantics, cache reuse, and outbound API call minimization.

## Contract Parties

- **Producer**: Backend API endpoints (`board.py`, `projects.py`) and services (`cache.py`, `github_projects/service.py`, `copilot_polling/polling_loop.py`)
- **Consumer**: Frontend hooks (`useProjectBoard.ts`, `useBoardRefresh.ts`, `useRealTimeSync.ts`)

## Endpoint Contracts

### GET /api/v1/board/projects/{project_id}

**Purpose**: Retrieve board data (columns, items, sub-items) for display.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `refresh` | query bool | `false` | When `true`, bypasses cache reads, clears sub-issue caches, fetches fresh data from GitHub, and repopulates cache. When `false`, serves from cache if warm. |

**Response**: `BoardDataResponse` with `columns`, `items`, `rate_limit`, and `data_hash`.

**Cache Behavior**:

| Scenario | Cache Read | Cache Write | Sub-Issue Cache | Outbound API Calls |
|----------|-----------|-------------|-----------------|-------------------|
| `refresh=false`, cache warm | ✅ Serve from cache | No write | Reused (FR-005) | Zero |
| `refresh=false`, cache expired | Skip | ✅ Write with 300s TTL | Reused if warm | Minimum needed |
| `refresh=true` (manual) | Skip | ✅ Write with 300s TTL | ❌ Cleared first | Full fetch (FR-009) |
| GitHub API error, cache warm | ✅ Serve stale | No write | Serve stale | Zero (fallback) |
| GitHub API error, cache cold | ❌ Error | No write | N/A | Failed attempt |
| Rate limit exhausted | ✅ Serve stale if available | No write | Serve stale | Zero + 429 status |

**Data Hash Contract**:
- Every successful cache write includes a `data_hash` (SHA-256, 64-char hex)
- Hash is computed from board content, excluding `rate_limit` metadata
- Consumers MAY compare `data_hash` to detect unchanged data (FR-004)
- Identical content always produces identical hash (deterministic, key-order-independent)

### WebSocket /api/v1/projects/{project_id}/subscribe

**Purpose**: Real-time push of project task changes.

**Subscription Lifecycle**:
1. Client connects → server sends `initial_data` message with current tasks (fetched with `force_refresh=True`)
2. Server runs periodic check every 30 seconds:
   - Fetches tasks (prefers cache when warm)
   - Computes `data_hash` and compares with last sent hash
   - If unchanged: no message sent (FR-003, FR-004)
   - If changed: sends `refresh` message with updated data
3. Client disconnect → cleanup subscription

**Message Types**:

| Type | Payload | Trigger |
|------|---------|---------|
| `initial_data` | Full task list | Connection established |
| `refresh` | Full task list | Data hash changed |
| `task_update` | Single task delta | Individual task change detected |
| `task_created` | New task data | New task added |
| `status_changed` | Task + new status | Task status transition |

**Idle Behavior Contract** (FR-003):
- When no external data changes occur, the 30-second periodic check MUST NOT produce outbound GitHub API calls if the board cache is warm (within 300s TTL)
- When the board cache expires (> 300s), the periodic check MAY make one outbound API call to refresh the cache, then suppress further calls until the cache expires again

## Caching Layer Contract

### InMemoryCache Guarantees

| Guarantee | Description |
|-----------|-------------|
| TTL enforcement | Entries expire after their configured TTL; `get()` returns `None` for expired entries |
| Stale access | `get_stale()` returns expired entries for fallback scenarios |
| Data hash tracking | Optional `data_hash` field stored alongside value for change detection |
| Thread safety | Basic; concurrent `clear_expired()` tolerates missing keys |
| No persistence | Cache is in-memory only; lost on process restart |

### Cache Key Conventions

| Key Pattern | TTL | Description |
|-------------|-----|-------------|
| `board:data:{project_id}` | 300s | Full board data with columns and items |
| `sub_issues:{issue_id}` | config default | Sub-issue data for a parent issue |
| `user:projects:{user_id}` | config default | User's accessible projects |
| `project:items:{project_id}` | config default | Project items/tasks |

## Background Polling Contract

### Copilot Polling Loop (`polling_loop.py`)

**Interaction with Board Cache**:
- Polling loop clears its own `cycle_cache` (transient per-iteration cache) at the start of each iteration
- Polling loop does NOT directly read or write the board data cache
- Polling loop triggers are independent of board refresh; they detect PR completions and pipeline transitions
- Rate-limit budget checks in polling loop protect the shared GitHub API budget used by board endpoints

**Rate-Limit Budget Rules**:

| Remaining Budget | Polling Behavior |
|-----------------|-----------------|
| > SKIP_EXPENSIVE_THRESHOLD (100) | Normal operation |
| ≤ SKIP_EXPENSIVE_THRESHOLD (100) | Skip expensive steps (Step 0, Step 5) |
| ≤ SLOW_THRESHOLD | Double polling interval |
| ≤ PAUSE_THRESHOLD (20) | Pause polling entirely until reset |
| Stale data (remaining=0, reset in past) | Clear stale data, resume |

## Regression Test Assertions

These assertions MUST be maintained by any future changes to the endpoints above:

1. **Cache hit on second request**: `GET /board/projects/{id}` with `refresh=false` — second call within 300s MUST NOT trigger outbound API calls
2. **Manual refresh clears sub-issue cache**: `GET /board/projects/{id}?refresh=true` MUST clear sub-issue cache entries before fetching
3. **Data hash stored on cache write**: Board data cache entries MUST include a 64-char SHA-256 `data_hash`
4. **Data hash excludes rate-limit**: Same board content with different rate-limit headers MUST produce the same `data_hash`
5. **Stale fallback on error**: GitHub API error with warm cache MUST serve stale data rather than propagating error
6. **Rate-limit detection**: Remaining=0 MUST return 429 status with `retry_after` information
