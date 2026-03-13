# Research: Performance Review

**Feature**: 039-performance-review
**Date**: 2026-03-13
**Status**: Complete

## Research Tasks

### R1: Current Spec 022 Implementation Status

**Decision**: Spec 022 (API Rate Limit Protection) acceptance criteria are substantially implemented in the current codebase.

**Rationale**: Code inspection reveals the following Spec 022 aligned behaviors are already in place:
- Board data cache TTL is 300 seconds (5 minutes), aligned with frontend auto-refresh interval (`backend/src/api/board.py`)
- Sub-issue cache is cleared on manual refresh before fetching new board data (`backend/src/api/board.py`, manual refresh path)
- WebSocket subscription uses `compute_data_hash()` for change detection — only sends updates when data actually changes (`backend/src/api/projects.py`, `websocket_subscribe`)
- Polling loop implements rate-limit-aware backoff with thresholds at 100 (pause), 200 (slow), and adaptive idle backoff up to 300s (`backend/src/services/copilot_polling/polling_loop.py`)
- Stale cache fallback serves cached data when GitHub API returns rate limit or server errors (`backend/src/api/board.py`, `backend/src/api/projects.py`)

**Remaining gaps to address**:
- Fallback polling in `useRealTimeSync.ts` invalidates only task queries (not board data), but the interaction between WebSocket message types and board query invalidation needs verification under all message paths
- The polling loop's `clear_cycle_cache()` at start of each cycle prevents cross-cycle staleness but may cause unnecessary re-fetches within a cycle if data hasn't changed
- Sub-issue cache reuse during non-manual refreshes is not explicitly verified — warm caches may not always be consulted

**Alternatives considered**: Full re-implementation of Spec 022 was rejected; incremental gap-filling on top of existing implementation is the correct approach.

---

### R2: TanStack React Query Invalidation Best Practices

**Decision**: Use granular query key invalidation with `setQueryData` for lightweight updates; reserve `invalidateQueries` for full refreshes only.

**Rationale**: TanStack React Query v5 (used at ^5.90.0) provides several invalidation strategies:
- `invalidateQueries` marks queries as stale and triggers background refetch — appropriate for auto-refresh and manual refresh
- `setQueryData` directly updates cache without refetch — appropriate for WebSocket-delivered task updates
- `cancelQueries` stops in-flight requests — appropriate before manual refresh to prevent race conditions
- Query key structure `['board', 'data', projectId]` and `['projects', projectId, 'tasks']` already provide good granularity

The current codebase correctly uses `invalidateQueries` for task queries on WebSocket messages and direct cache writes for manual refresh results. The key improvement is ensuring fallback polling also uses change-detection before invalidation rather than unconditional invalidation.

**Alternatives considered**: Moving to a normalized cache (like Apollo Client) was rejected as overengineering for the current architecture. The existing query key separation is sufficient.

---

### R3: React Memoization Effectiveness for Board Components

**Decision**: `BoardColumn` and `IssueCard` are already wrapped in `React.memo()`. Additional memoization should target derived data in parent components and stabilize callback props.

**Rationale**: Code inspection reveals:
- `BoardColumn` uses `React.memo()` — prevents rerender when props unchanged
- `IssueCard` uses `React.memo()` — prevents rerender when card data unchanged
- `SubIssueRow` uses `React.memo()` — prevents rerender when sub-issue data unchanged
- `ProjectsPage` uses `useMemo` for `pipelineGridStyle`, `assignedPipeline`, `assignedStageMap`, and `heroStats`
- `ProjectsPage` uses `useCallback` for `handleCardClick`, `handleCloseModal`, and `handlePipelineSelection`

Remaining opportunities:
- Verify that all callback props passed to memoized components are stable references (wrapped in `useCallback`) to prevent memo invalidation
- Profile whether derived data computations are actually expensive or just protective
- Check if the mapping of columns to `BoardColumn` components creates new arrays/objects on each render that defeat `memo()`

**Alternatives considered**: Introducing `useDeferredValue` or `useTransition` was considered but deferred as these add complexity; standard memoization is the safer first-pass approach.

---

### R4: Event Listener Throttling Patterns

**Decision**: Use `requestAnimationFrame` gating for high-frequency DOM event handlers; existing patterns in the codebase already follow this approach.

**Rationale**: The codebase already implements good patterns:
- `ChatPopup.tsx` registers mousemove/mouseup listeners only during active resize and uses `requestAnimationFrame()` for position updates
- `AddAgentPopover.tsx` (at `frontend/src/components/board/AddAgentPopover.tsx`) uses passive scroll listeners and repositions via `requestAnimationFrame()`

Remaining improvements:
- Verify all drag-related handlers in board interactions (via @dnd-kit) are properly throttled
- Check if window resize handlers in layout components fire at unrestricted frequency
- Ensure scroll handlers on board columns use passive listeners

**Alternatives considered**: Using a throttle utility (e.g., lodash.throttle) was considered but rejected to avoid adding dependencies; `requestAnimationFrame` is the native browser primitive and already used in the codebase.

---

### R5: Backend WebSocket Subscription Refresh Semantics

**Decision**: The current 30-second periodic refresh within the WebSocket subscription is the primary source of unnecessary backend activity on idle boards and should be the first optimization target.

**Rationale**: In `backend/src/api/projects.py`, the `websocket_subscribe` endpoint:
- Runs a loop with `refresh_interval = 30` seconds
- Each iteration fetches project tasks (using cache for periodic refreshes, bypass for initial)
- Computes data hash and compares against previous hash
- Only sends data to client when hash differs

While hash-based change detection prevents unnecessary client updates, each 30-second cycle still:
1. Reads from cache (cheap) or fetches from GitHub (expensive if cache expired)
2. Serializes and hashes the data (CPU cost per cycle)
3. Runs continuously even when the board tab is hidden or user is inactive

Optimization opportunities:
- Leverage Page Visibility API signals from the frontend to pause/reduce WebSocket polling when tab is hidden
- Consider server-side idle detection — if no changes detected for N consecutive cycles, increase the interval
- Ensure cache reads within WebSocket loop don't accidentally trigger cache expiration side effects

**Alternatives considered**: Replacing the polling-within-WebSocket pattern with GitHub webhooks was rejected as out of scope; the current architecture is a pull model and that's acceptable for the first pass.

---

### R6: Sub-Issue Cache Reuse During Board Refreshes

**Decision**: Sub-issue caches should be consulted during all board data fetches (not just manual refresh paths) to reduce outbound call volume.

**Rationale**: Current behavior in `backend/src/api/board.py`:
- Manual refresh explicitly clears sub-issue caches before re-fetching (correct — ensures fresh data)
- Non-manual board data fetches rely on the board data cache TTL (300s) but when the board cache expires, sub-issue data is re-fetched even if sub-issue caches are still warm

The optimization path:
1. During board data construction, check sub-issue cache for each item before making an outbound call
2. Only fetch sub-issues that are not in cache or have expired
3. This reduces the "thundering herd" effect when a board cache expires — sub-issue data (which changes less frequently) can be served from its own cache

**Alternatives considered**: Batching all sub-issue fetches into a single GraphQL query was considered but rejected because the GitHub GraphQL API doesn't support arbitrary batching of sub-issue queries. Individual cache checks are the pragmatic approach.

---

### R7: Fallback Polling Refresh Behavior

**Decision**: Frontend fallback polling should use lightweight change-detection (e.g., ETag or hash comparison) before triggering query invalidation.

**Rationale**: In `useRealTimeSync.ts`, the fallback polling path:
- Activates when WebSocket fails (timeout, error, or close)
- Polls at 30-second intervals (`WS_FALLBACK_POLL_MS`)
- Currently invalidates only `['projects', projectId, 'tasks']` queries — NOT board data
- This is already an improvement over previous behavior (documented in code comments about "polling storms")

Remaining improvement:
- Verify that task query invalidation during polling doesn't cascade into board data refetch through dependent query relationships
- Consider adding a server-side endpoint that returns only a change indicator (hash/timestamp) to avoid full task data fetch on each poll cycle
- Ensure debounce window (2s) in `useBoardRefresh` correctly coalesces polling-triggered and WebSocket-triggered refreshes

**Alternatives considered**: Server-Sent Events (SSE) as a more reliable fallback than polling was considered, and the codebase already has an SSE endpoint (`sse_subscribe`). The SSE path could be promoted as the primary fallback, but this is a larger change and should be deferred to the second pass.

---

### R8: Regression Test Strategy for Performance Changes

**Decision**: Extend existing test suites rather than creating new test infrastructure. Focus on behavioral assertions that prevent regression of the specific optimizations.

**Rationale**: The existing test infrastructure covers the critical paths:
- `test_cache.py`: TTL, expiration, stale fallback, hash computation
- `test_api_board.py`: Board caching, manual refresh, sub-issue invalidation, rate limit handling
- `test_copilot_polling.py`: Polling steps, rate limit pausing, cycle cache
- `useRealTimeSync.test.tsx`: WebSocket lifecycle, polling fallback, debounce
- `useBoardRefresh.test.tsx`: Manual refresh, auto-refresh timer, visibility API

New test assertions needed:
- Backend: Verify that warm sub-issue caches are consulted during non-manual board refreshes
- Backend: Verify that WebSocket change detection skips send when hash unchanged (may already exist)
- Frontend: Verify that fallback polling invalidation does not cascade to board data query
- Frontend: Verify that a single-task update rerenders only the affected card (component test)

**Alternatives considered**: Adding performance benchmarks (e.g., Lighthouse CI, k6) was considered but deferred; behavioral assertions are sufficient for the first pass and don't require new tooling.
