# Data Model: Add Manual Refresh Button & Auto-Refresh to Project Board with GitHub API Rate Limit Optimization

**Feature**: 014-board-refresh-ratelimit | **Date**: 2026-02-28

## Entity: Refresh State (Frontend)

**Purpose**: Represents the current state of the refresh mechanism, managed by the `useBoardRefresh` hook.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| isRefreshing | boolean | Whether a refresh operation is currently in progress | Prevents concurrent refresh operations |
| lastRefreshedAt | Date \| null | Timestamp of the last successful refresh | Set on every successful refresh (manual or auto) |
| autoRefreshEnabled | boolean | Whether the auto-refresh timer is active | Paused when tab is hidden |
| nextRefreshAt | Date \| null | When the next auto-refresh will fire | Recomputed on every refresh and tab visibility change |
| error | RefreshError \| null | Current error state, if any | Cleared on next successful refresh |

**Validation Rules**:
- `isRefreshing` must be `false` before a new refresh can be initiated
- `lastRefreshedAt` must be updated atomically with the successful query resolution
- `nextRefreshAt` must be recalculated whenever a manual refresh completes or the auto-refresh fires
- When tab becomes hidden, `autoRefreshEnabled` must be set to `false`; when visible, set to `true`

**State Transitions**:
```
idle → [manual click OR timer fires] → refreshing → [success] → idle (timer reset)
idle → [manual click OR timer fires] → refreshing → [failure] → error (timer continues)
idle → [tab hidden] → paused → [tab visible + stale > 5min] → refreshing → idle
idle → [tab hidden] → paused → [tab visible + stale < 5min] → idle (timer resumes)
```

---

## Entity: Rate Limit Info (Shared Backend → Frontend)

**Purpose**: GitHub API rate limit status, extracted from response headers and forwarded to the frontend.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| limit | integer | Maximum requests allowed per hour | From `X-RateLimit-Limit` header |
| remaining | integer | Requests remaining in the current window | From `X-RateLimit-Remaining` header |
| reset_at | integer (Unix timestamp) | When the rate limit window resets | From `X-RateLimit-Reset` header |
| used | integer | Requests used in the current window | Computed: `limit - remaining` |

**Backend Model** (Pydantic, added to `backend/src/models/board.py`):
```python
class RateLimitInfo(BaseModel):
    limit: int = Field(description="Maximum requests per hour")
    remaining: int = Field(description="Remaining requests in current window")
    reset_at: int = Field(description="Unix timestamp when limit resets")
    used: int = Field(description="Requests used in current window")
```

**Frontend Type** (TypeScript, added to `frontend/src/types/index.ts`):
```typescript
interface RateLimitInfo {
  limit: number;
  remaining: number;
  reset_at: number;
  used: number;
}
```

**Validation Rules**:
- `remaining` must be ≥ 0
- `reset_at` must be a valid future Unix timestamp (seconds since epoch)
- `used` must equal `limit - remaining`
- When `remaining` < 10, trigger a preemptive low-quota warning (FR-016)

---

## Entity: Refresh Error (Frontend)

**Purpose**: Represents a failed refresh attempt with typed error categories.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| type | enum | Error category | `rate_limit` \| `network` \| `auth` \| `server` \| `unknown` |
| message | string | Human-readable error message | Non-empty |
| rateLimitInfo | RateLimitInfo \| null | Rate limit details if type is `rate_limit` | Required when type is `rate_limit` |
| retryAfter | Date \| null | When to retry | Computed from `rateLimitInfo.reset_at` for rate limit errors |

**Frontend Type** (TypeScript):
```typescript
type RefreshErrorType = 'rate_limit' | 'network' | 'auth' | 'server' | 'unknown';

interface RefreshError {
  type: RefreshErrorType;
  message: string;
  rateLimitInfo?: RateLimitInfo;
  retryAfter?: Date;
}
```

**Validation Rules**:
- `type: 'rate_limit'` requires `rateLimitInfo` to be present
- `message` must be a user-friendly string (no raw stack traces or API error details)
- `retryAfter` for rate limit errors is computed as `new Date(rateLimitInfo.reset_at * 1000)`

---

## Entity: Cache Entry with ETag (Backend)

**Purpose**: Extension of the existing `CacheEntry` in `backend/src/services/cache.py` to support ETag-based conditional requests.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| value | T | Cached response data | Existing field |
| expires_at | datetime | TTL-based expiration | Existing field |
| etag | string \| None | ETag from the last GitHub API response | Optional; stored from `ETag` response header |
| last_modified | string \| None | Last-Modified header value | Optional; stored from `Last-Modified` response header |

**Validation Rules**:
- `etag` and `last_modified` are optional — not all GitHub API responses include them
- When present, `etag` should be used in subsequent requests as `If-None-Match` header
- A 304 response with matching ETag should refresh the `expires_at` without replacing the `value`

---

## Entity: BoardDataResponse (Modified Backend Model)

**Purpose**: Existing response model for board data, extended with rate limit information.

| Field | Type | Description | Change |
|-------|------|-------------|--------|
| project | BoardProject | Project metadata | Existing |
| columns | list[BoardColumn] | Board columns with items | Existing |
| total_item_count | integer | Total items across all columns | Existing |
| rate_limit | RateLimitInfo \| None | GitHub API rate limit status | **NEW** — optional, populated from API response headers |

---

## Relationships

```
BoardDataResponse 1──0..1 RateLimitInfo  (response includes rate limit status)
RefreshState      1──0..1 RefreshError   (refresh may fail with typed error)
RefreshError      1──0..1 RateLimitInfo  (rate limit errors include details)
CacheEntry        1──0..1 ETag           (cached responses may have ETags)
```

## Constants

| Constant | Value | Location | Purpose |
|----------|-------|----------|---------|
| AUTO_REFRESH_INTERVAL_MS | 300_000 (5 min) | `frontend/src/constants.ts` | Auto-refresh timer interval |
| RATE_LIMIT_LOW_THRESHOLD | 10 | `frontend/src/constants.ts` | Remaining requests threshold for preemptive warning |
| BOARD_CACHE_TTL_SECONDS | 30 | `backend/src/api/board.py` | Existing backend cache TTL for board data |
