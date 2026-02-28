# Research: Add Manual Refresh Button & Auto-Refresh to Project Board with GitHub API Rate Limit Optimization

**Feature**: 014-board-refresh-ratelimit | **Date**: 2026-02-28

## Research Task 1: Current Board Data Refresh Architecture

### Decision
The project board currently fetches data via two TanStack Query hooks: `useProjectBoard` (fetches board data and project list) and `useRealTimeSync` (WebSocket with polling fallback that invalidates TanStack Query caches). There is **no manual refresh button** and **no explicit auto-refresh timer**. The `useRealTimeSync` polling fallback fires every 5 seconds (`WS_FALLBACK_POLL_MS`) which is too aggressive for API conservation. The refresh button and 5-minute auto-refresh timer should be added as a new `useBoardRefresh` hook that coordinates with the existing infrastructure.

### Rationale
Analysis of the current codebase reveals:
- `frontend/src/hooks/useProjectBoard.ts`: Uses TanStack `useQuery` with `staleTime: STALE_TIME_SHORT` (10s). No `refetchInterval` — the comment explicitly states "useRealTimeSync handles periodic refresh."
- `frontend/src/hooks/useRealTimeSync.ts`: WebSocket connects to `/api/v1/projects/{id}/subscribe`. On WS failure, falls back to polling every 5s (`WS_FALLBACK_POLL_MS`). Invalidates `['board', 'data', projectId]` query key on messages.
- `frontend/src/services/api.ts`: `boardApi.getBoardData()` accepts a `refresh` parameter but the hook never uses it (always fetches without `?refresh=true`).
- `backend/src/api/board.py`: Server-side cache with 30s TTL on board data. The `?refresh=true` query parameter bypasses the cache.

### Alternatives Considered
- Adding `refetchInterval` to the existing `useQuery` in `useProjectBoard` — rejected because it would conflict with `useRealTimeSync` polling (the comment explicitly warns about "duplicate polling storms that freeze the UI")
- Modifying `useRealTimeSync` to handle the 5-minute timer — rejected because it conflates WebSocket lifecycle management with user-facing refresh logic; better to create a separate `useBoardRefresh` hook

---

## Research Task 2: Page Visibility API for Auto-Refresh Pause

### Decision
Use the standard `document.visibilitychange` event and `document.hidden` property to pause auto-refresh when the tab is hidden. Resume with an immediate refresh if data is older than 5 minutes when the tab regains focus. The existing `useRealTimeSync` does NOT currently implement visibility-based pausing.

### Rationale
- The Page Visibility API is supported in all modern browsers (Chrome 33+, Firefox 18+, Safari 7+, Edge 12+).
- `document.hidden` returns `true` when the tab is not visible; `document.visibilitychange` fires on state change.
- The 5-minute auto-refresh `setInterval` should be cleared when the tab is hidden and a new one started when the tab becomes visible.
- If the elapsed time since the last refresh exceeds 5 minutes when the tab becomes visible, trigger an immediate refresh before starting a new timer.
- The `useRealTimeSync` hook's WebSocket connection should remain open regardless of tab visibility (WebSocket messages are lightweight and the connection is shared).

### Alternatives Considered
- Using `window.blur`/`focus` events — rejected because they fire for iframes and overlapping windows, not just tab visibility
- Pausing the WebSocket connection when the tab is hidden — rejected because reconnection is expensive and the WebSocket only receives small push messages

---

## Research Task 3: GitHub API Rate Limit Headers and ETag Support

### Decision
Leverage GitHub API response headers (`X-RateLimit-Remaining`, `X-RateLimit-Reset`, `ETag`) to implement smart caching and rate limit awareness. GitHub GraphQL API returns rate limit headers on every response. Store ETags per resource and use `If-None-Match` on subsequent requests. For GraphQL, GitHub supports conditional requests but the behavior differs from REST — the `_graphql` method in `service.py` should extract and return rate limit headers.

### Rationale
- GitHub REST API returns: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset` (Unix timestamp), `X-RateLimit-Used`, `X-RateLimit-Resource`, and `ETag`.
- GitHub GraphQL API also returns rate limit headers. For GraphQL, rate limits are tracked differently (point-based) but the headers are still present.
- The existing `_request_with_retry` method in `service.py` already handles 429 status codes with exponential backoff (MAX_RETRIES=3) but does NOT extract or forward rate limit headers to the caller.
- The backend `board.py` endpoints should pass rate limit info in the response body (or custom response headers) so the frontend can display warnings.
- ETag support: Store the `ETag` from the last successful response in the backend cache alongside the response data. On subsequent requests, send `If-None-Match: <etag>` — if the data hasn't changed, GitHub returns 304 with zero body, which does not count against the rate limit.

### Alternatives Considered
- Client-side (frontend) ETag caching — rejected because the backend is the one making GitHub API calls; ETag logic belongs in the backend service layer
- Moving entirely to GraphQL `rateLimit` query field — considered supplementary; the response headers are more reliable and universally available

---

## Research Task 4: Request Deduplication Strategy

### Decision
Use TanStack Query's built-in request deduplication on the frontend (same query key = single in-flight request) combined with the backend's existing `InMemoryCache` (30s TTL for board data) for server-side deduplication. Add a mutex/lock flag in `useBoardRefresh` to prevent concurrent manual refresh triggers.

### Rationale
- TanStack Query already deduplicates: if multiple components mount with the same query key, only one fetch fires. When `invalidateQueries` is called, TanStack waits for the in-flight request rather than issuing a duplicate.
- The `useBoardRefresh` hook should maintain an `isRefreshing` flag that prevents multiple concurrent refresh operations.
- Backend `InMemoryCache` with 30s TTL already prevents duplicate API calls within the TTL window.
- For rapid manual clicks (SC-006: 5 clicks in 1 second → at most 1 API call): the `isRefreshing` guard in the hook plus TanStack Query's deduplication handles this automatically.

### Alternatives Considered
- Adding a debounce to the refresh button click — provides additional safety but TanStack Query's deduplication already covers this; a simple `isRefreshing` guard is simpler and sufficient
- Backend request-level deduplication with a lock per project ID — over-engineered; the 30s cache TTL already provides this

---

## Research Task 5: Rate Limit Error Display UX Pattern

### Decision
Display a non-intrusive amber/yellow warning banner below the board header (same position as the existing error banner) when a rate limit error occurs. Include the reset time as a human-readable countdown (e.g., "Rate limit reached. Resets in 12 minutes."). Automatically dismiss the warning when the next refresh succeeds. For non-rate-limit errors, display a red error banner with a retry button (matching the existing pattern in `ProjectBoardPage.tsx`).

### Rationale
- The existing `ProjectBoardPage.tsx` already has an error banner pattern for `boardError` (lines 159-172) with a red destructive style and a "Retry" button. The rate limit warning should follow the same layout but with a yellow/amber style to differentiate severity.
- The `X-RateLimit-Reset` header provides a Unix timestamp; the frontend should compute the human-readable time remaining and update it periodically.
- The warning should be dismissible but also auto-dismiss when a successful refresh occurs (FR-010).
- When remaining rate limit is critically low (<10 requests per FR-016), show a preemptive warning before exhaustion.

### Alternatives Considered
- Toast notifications — rejected because they auto-dismiss and the user may miss them; a persistent banner is more appropriate for an ongoing rate limit condition
- Modal dialog — rejected because it blocks the user from interacting with potentially-stale-but-still-useful board data

---

## Research Task 6: Batching GitHub API Requests via GraphQL

### Decision
The board data fetch already uses a single GraphQL query (`BOARD_GET_PROJECT_ITEMS_QUERY`) that retrieves all project items, status fields, assignees, linked PRs, and sub-issues in one request with pagination. This is already well-optimized. The `list_board_projects` endpoint uses a separate GraphQL query (`BOARD_LIST_PROJECTS_QUERY`). No additional batching is needed — the current architecture already minimizes API calls to 1-2 GraphQL requests per refresh cycle.

### Rationale
- `BOARD_GET_PROJECT_ITEMS_QUERY` in `graphql.py` fetches: project metadata, status field options, all items with their content (issues/PRs), assignees, custom fields (priority, size, estimate), linked PRs, and sub-issues — all in a single paginated query.
- The only scenario requiring multiple requests is pagination (`hasNextPage` + `endCursor`), which is inherent to the data size.
- The project list fetch (`BOARD_LIST_PROJECTS_QUERY`) is called separately but is cached with a longer TTL (`STALE_TIME_LONG` = 5 minutes) and changes infrequently.
- Combining the project list and board data queries into a single GraphQL query is possible but adds complexity for minimal gain (the project list rarely changes).

### Alternatives Considered
- Combining `list_board_projects` and `get_board_data` into a single GraphQL query — rejected because the project list is fetched once and cached, while board data is refreshed every 5 minutes; merging them would force unnecessary re-fetching of the project list
- REST API batching — not applicable; GitHub REST doesn't support batching; GraphQL is already the optimal approach

---

## Research Task 7: Integration with Existing useRealTimeSync Hook

### Decision
The `useBoardRefresh` hook should work alongside `useRealTimeSync`, not replace it. `useRealTimeSync` handles real-time push updates via WebSocket (instant updates when issues change). `useBoardRefresh` handles the 5-minute periodic refresh and manual refresh button. Both invalidate the same TanStack Query key (`['board', 'data', projectId]`), so TanStack Query's deduplication prevents conflicts.

### Rationale
- `useRealTimeSync` provides instant updates for individual changes (task_update, task_created, status_changed). These are high-priority, low-latency updates.
- The 5-minute auto-refresh provides a full data sync as a safety net — in case a WebSocket message is missed or the connection is interrupted.
- Both mechanisms call `queryClient.invalidateQueries({ queryKey: ['board', 'data', projectId] })`, which triggers TanStack Query to refetch. If both fire simultaneously, TanStack Query ensures only one actual fetch occurs.
- The `useBoardRefresh` hook should reset its 5-minute timer whenever a WebSocket-triggered refresh occurs (to prevent a redundant auto-refresh shortly after a real-time update).

### Alternatives Considered
- Replacing `useRealTimeSync` polling with the 5-minute timer — rejected because `useRealTimeSync` provides real-time updates via WebSocket which are essential for the live board experience; the 5-minute timer is a supplementary safety net
- Having `useRealTimeSync` own the 5-minute timer — rejected because it conflates real-time event handling with scheduled polling; separation of concerns is cleaner

---

## Research Task 8: Backend Rate Limit Response Forwarding

### Decision
Add optional `rate_limit` field to `BoardDataResponse` containing `remaining`, `reset_at`, and `limit` values extracted from GitHub API response headers. The backend `board.py` endpoint should pass these through from the `_request_with_retry` / `_graphql` method responses.

### Rationale
- The frontend needs rate limit information to display warnings (FR-009, FR-016).
- The backend already receives rate limit headers from GitHub but currently discards them.
- Adding a `rate_limit` field to the response model is the cleanest approach — it doesn't require custom response headers and works with the existing JSON serialization.
- The `_request_with_retry` method should extract `X-RateLimit-Remaining`, `X-RateLimit-Reset`, and `X-RateLimit-Limit` from the last response and make them available to callers.
- When a 403/429 rate limit error occurs, the error response should also include rate limit reset information.

### Alternatives Considered
- Custom HTTP response headers from the backend — rejected because TanStack Query's `useQuery` doesn't easily expose response headers; embedding in the JSON body is more ergonomic for the frontend
- Separate `/api/v1/rate-limit` endpoint — over-engineered; the rate limit info is most useful when attached to the data response it relates to
