# API Contracts: Board Refresh & Rate Limit

**Feature**: 014-board-refresh-ratelimit | **Date**: 2026-02-28

## Modified Endpoint: GET /api/v1/board/projects/{project_id}

**Change**: Add `rate_limit` field to response body.

### Request (unchanged)

```
GET /api/v1/board/projects/{project_id}?refresh={true|false}
Authorization: Bearer <session_token>
```

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| project_id | string (path) | Yes | GitHub Project V2 node ID |
| refresh | boolean (query) | No | Force refresh from GitHub API (default: false) |

### Response (modified)

**200 OK**
```json
{
  "project": {
    "project_id": "PVT_abc123",
    "name": "My Project",
    "owner_login": "octocat",
    "url": "https://github.com/users/octocat/projects/1",
    "short_description": "Project description",
    "status_field": { ... }
  },
  "columns": [ ... ],
  "total_item_count": 24,
  "rate_limit": {
    "limit": 5000,
    "remaining": 4850,
    "reset_at": 1740780000,
    "used": 150
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| rate_limit | RateLimitInfo \| null | GitHub API rate limit status; null if headers were not available |
| rate_limit.limit | integer | Maximum requests per hour |
| rate_limit.remaining | integer | Requests remaining in current window |
| rate_limit.reset_at | integer | Unix timestamp (seconds) when limit resets |
| rate_limit.used | integer | Requests consumed in current window |

**Error Responses** (existing, enhanced):

| Status | Condition | Body |
|--------|-----------|------|
| 404 | Project not found | `{"detail": "Project not found: PVT_xxx"}` |
| 502 | GitHub API error | `{"detail": "Failed to fetch board data from GitHub", "error": "..."}` |
| 429 | Rate limit exceeded | `{"detail": "GitHub API rate limit exceeded", "rate_limit": {"limit": 5000, "remaining": 0, "reset_at": 1740780000, "used": 5000}}` |

---

## Modified Endpoint: GET /api/v1/board/projects

**Change**: Add `rate_limit` field to response body.

### Response (modified)

**200 OK**
```json
{
  "projects": [ ... ],
  "rate_limit": {
    "limit": 5000,
    "remaining": 4900,
    "reset_at": 1740780000,
    "used": 100
  }
}
```

---

## Frontend API Client Contract

### boardApi (frontend/src/services/api.ts)

```typescript
export const boardApi = {
  /**
   * List available projects for board display.
   * Response now includes rate_limit field.
   */
  listProjects(refresh?: boolean): Promise<BoardProjectListResponse>;

  /**
   * Get board data for a specific project.
   * Response now includes rate_limit field.
   */
  getBoardData(projectId: string, refresh?: boolean): Promise<BoardDataResponse>;
};
```

---

## Frontend Hook Contract

### useBoardRefresh (frontend/src/hooks/useBoardRefresh.ts)

```typescript
interface UseBoardRefreshOptions {
  /** Currently selected project ID */
  projectId: string | null;
  /** TanStack QueryClient instance (from useQueryClient) */
  queryClient: QueryClient;
}

interface UseBoardRefreshReturn {
  /** Trigger a manual refresh */
  refresh: () => void;
  /** Whether a refresh is currently in progress */
  isRefreshing: boolean;
  /** Timestamp of last successful refresh */
  lastRefreshedAt: Date | null;
  /** Current error state */
  error: RefreshError | null;
  /** Rate limit information from last response */
  rateLimitInfo: RateLimitInfo | null;
  /** Whether rate limit is critically low (<10 remaining) */
  isRateLimitLow: boolean;
}

function useBoardRefresh(options: UseBoardRefreshOptions): UseBoardRefreshReturn;
```

**Behavioral Contract**:
1. Calling `refresh()` when `isRefreshing` is `true` is a no-op
2. `refresh()` resets the 5-minute auto-refresh timer
3. Auto-refresh pauses when `document.hidden` is `true`
4. Auto-refresh resumes (with immediate refresh if stale > 5min) when tab becomes visible
5. `error` is cleared on the next successful refresh
6. `rateLimitInfo` is updated on every successful response

---

## RefreshButton Component Contract

### RefreshButton (frontend/src/components/board/RefreshButton.tsx)

```typescript
interface RefreshButtonProps {
  /** Callback to trigger manual refresh */
  onRefresh: () => void;
  /** Whether a refresh is currently in progress */
  isRefreshing: boolean;
  /** Whether the button should be disabled */
  disabled?: boolean;
}
```

**UI Contract**:
- Renders an icon button with a refresh/reload icon
- Shows a tooltip on hover: "Auto-refreshes every 5 minutes"
- Displays a spinning animation when `isRefreshing` is `true`
- Disabled state when `disabled` is `true` or `isRefreshing` is `true`

---

## Internal Service Contract: Rate Limit Extraction

### GitHubProjectsService._graphql (backend)

**Change**: The `_graphql` and `_request_with_retry` methods should make rate limit headers accessible to callers.

```python
class RateLimitHeaders(TypedDict, total=False):
    limit: int
    remaining: int
    reset_at: int
    used: int

# _request_with_retry stores last rate limit headers on the service instance
# board.py extracts them after calling get_board_data()
```

The simplest approach: after `get_board_data()` completes, the `board.py` endpoint reads the rate limit headers from the last response and includes them in the `BoardDataResponse`.
