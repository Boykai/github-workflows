# Data Model: Performance Review

**Feature Branch**: `027-performance-review`

## Entities

### 1. Board Data Cache (modified behavior)

The existing in-memory cache entry for board data. No schema change — behavioral change to ensure consistent TTL alignment and automatic-refresh warm-cache reuse.

**Current fields** (from `backend/src/services/cache.py`):
| Field | Type | Description |
|-------|------|-------------|
| key | str | Cache key: `board_data:{project_id}` |
| value | Any | Serialized board data (columns, cards, metadata) |
| expires_at | float | Unix timestamp of expiration (TTL=300s from set time) |
| etag | str \| None | GitHub ETag for conditional requests |
| last_modified | str \| None | GitHub Last-Modified for conditional requests |

**Behavioral changes**:
- Automatic (non-manual) board refreshes MUST check cache before fetching — serve cached data if TTL is valid
- Manual refresh (`refresh=true`) MUST bypass cache and clear sub-issue entries (already implemented)
- Cache TTL remains 300 seconds, aligned with the frontend 5-minute auto-refresh interval
- Stale fallback (`get_stale()`) continues to serve expired data on upstream errors

### 2. Sub-Issue Cache (modified behavior)

Individual sub-issue cache entries, keyed per parent issue. No schema change — behavioral change to ensure warm-cache reuse on automatic refreshes and proper invalidation on manual refresh.

**Current fields**:
| Field | Type | Description |
|-------|------|-------------|
| key | str | Cache key: `sub_issues:{issue_node_id}` or similar per-issue key |
| value | list[dict] | List of sub-issue data for the parent issue |
| expires_at | float | Unix timestamp of expiration (TTL=600s default) |

**Behavioral changes**:
- Automatic board refreshes MUST check sub-issue cache before making per-issue REST calls
- Only issues with expired or missing cache entries trigger new API calls
- Manual refresh clears all sub-issue cache entries for the project (already implemented in `board.py`)
- Cache TTL remains 600 seconds (2x board data TTL) — provides coverage across two automatic refresh cycles

**State transitions**:
```
COLD (no entry) → fetch from GitHub → WARM (cached, TTL active)
WARM → automatic refresh → WARM (served from cache, no API call)
WARM → TTL expires → COLD → fetch from GitHub → WARM
WARM → manual refresh → COLD (cleared) → fetch from GitHub → WARM
```

### 3. Refresh Event (new concept, no persistence)

Represents a trigger to update board data. Used to define the refresh contract between backend and frontend.

**Fields**:
| Field | Type | Description |
|-------|------|-------------|
| source | enum | `websocket_update`, `fallback_poll`, `auto_refresh`, `manual_refresh` |
| scope | enum | `task_only` (lightweight) or `full_board` (expensive) |
| target_query_keys | list[str[]] | TanStack Query keys to invalidate |
| bypass_cache | bool | Whether to skip backend cache |
| priority | int | 1=manual (highest), 2=auto, 3=websocket/poll (lowest) |

**Refresh policy matrix**:
| Source | Scope | Invalidates Tasks | Invalidates Board | Bypasses Cache | Clears Sub-Issues |
|--------|-------|-------------------|-------------------|----------------|-------------------|
| WebSocket update | task_only | ✅ | ❌ | ❌ | ❌ |
| Fallback poll | task_only | ✅ | ❌ | ❌ | ❌ |
| Auto-refresh (5 min) | full_board | ✅ | ✅ | ❌ | ❌ |
| Manual refresh | full_board | ✅ | ✅ | ✅ | ✅ |

### 4. Performance Baseline (new concept, documentation only)

A recorded set of metrics captured before and after optimization changes. Not persisted in the application — documented in measurement reports.

**Fields**:
| Metric | Unit | Measurement Method | Target |
|--------|------|--------------------|--------|
| idle_api_calls_5min | count | Backend logs over 5-minute idle window | ≤2 (excl. initial load) |
| board_refresh_api_calls | count | Backend logs per single board refresh | ≤3 with warm sub-issue cache |
| single_card_update_latency | ms | User-perceived time from WebSocket update to UI reflect | <1000ms |
| single_card_rerender_count | count | React DevTools Profiler component count | ≤3 (card + column + container) |
| board_initial_render_time | ms | React DevTools Profiler for 100-card board | Within 10% of baseline |
| drag_fps | frames/sec | Chrome DevTools Performance during card drag | ≥30 fps |
| sub_issue_cache_hit_rate | percent | Backend logs on automatic refresh | ≥80% |

### 5. WebSocket Subscription State (existing, behavioral clarification)

The existing WebSocket subscription in `projects.py` tracks per-connection state for change detection.

**Existing fields** (no change):
| Field | Type | Description |
|-------|------|-------------|
| project_id | str | Target project for the subscription |
| last_hash | str | SHA256 hash of last-sent task data |
| websocket | WebSocket | Active WebSocket connection |
| refresh_interval | int | Seconds between refresh checks (30s) |

**Behavioral clarification**:
- Refresh message sent ONLY when `current_hash != last_hash`
- On reconnection: single initial_data message sent, then resume hash-based detection
- Frontend MUST NOT cascade board invalidation on reconnection — only task query

### 6. Auto-Refresh Timer State (existing, behavioral clarification)

The existing auto-refresh timer in `useBoardRefresh.ts` coordinates the 5-minute board refresh cycle.

**Existing fields** (no change):
| Field | Type | Description |
|-------|------|-------------|
| intervalRef | React.MutableRefObject | Timer reference for 5-minute auto-refresh |
| isRefreshing | boolean | Whether a refresh is currently in progress |
| lastRefreshTime | number | Timestamp of last successful refresh |

**Behavioral clarification**:
- Timer resets on ANY data update (WebSocket, polling, manual) to maintain 5-minute window from last update
- Manual refresh cancels any in-progress automatic refresh via `queryClient.cancelQueries()`
- Timer pauses when tab is hidden (Page Visibility API) and resumes with freshness check
- Concurrent manual + automatic refresh: manual takes priority, automatic is cancelled

## Validation Rules

| Rule | Entity | Condition |
|------|--------|-----------|
| Board cache TTL must equal frontend auto-refresh interval | Board Data Cache | TTL = 300s = AUTO_REFRESH_INTERVAL_MS / 1000 |
| Sub-issue cache TTL must exceed board cache TTL | Sub-Issue Cache | Sub-issue TTL (600s) > Board TTL (300s) |
| Manual refresh must bypass all caches | Refresh Event | `source=manual_refresh` → `bypass_cache=true` AND `clears_sub_issues=true` |
| Task-only updates must not invalidate board query | Refresh Event | `scope=task_only` → `target_query_keys` excludes `['board', 'data', *]` |
| Reconnection must not cascade invalidations | WebSocket State | At most 1 task invalidation per reconnection cycle |
| Board re-renders bounded per card change | Performance Baseline | `single_card_rerender_count` ≤ 3 |
