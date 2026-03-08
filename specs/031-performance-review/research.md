# Research: Performance Review

**Feature Branch**: `031-performance-review`
**Date**: 2026-03-08
**Status**: Complete — all NEEDS CLARIFICATION resolved; Spec 022 audit confirmed

## Spec 022 Audit Results

> Audit performed 2026-03-08 by code inspection of the running codebase.

| Spec 022 Item | Status | Evidence |
|----------------|--------|----------|
| WebSocket SHA256 change detection | ✅ Complete | `projects.py:375-388` — hash comparison on each 30s cycle |
| Board cache TTL alignment (300s) | ✅ Complete | `board.py:359` — `cache.set(cache_key, board_data, ttl_seconds=300)` |
| Sub-issue cache invalidation on manual refresh | ✅ Complete | `board.py:313-322` — pre-clears sub-issue entries |
| Sub-issue cache with 600s TTL | ✅ Complete | `service.py:4366` — `cache.set(cache_key, sub_issues, ttl_seconds=600)` |
| Adaptive polling backoff | ✅ Complete | `polling_loop.py:52-86` — multi-threshold system |
| Rate-limit pre-checks in polling | ✅ Complete | `polling_loop.py:170,197-208` — skip expensive ops when budget low |
| Fallback polling only invalidates tasks | ✅ Complete | `useRealTimeSync.ts:100-101` — tasks only, board commented |
| Reconnection debounce (2s window) | ✅ Complete | `useRealTimeSync.ts:14,56-60` — `RECONNECT_DEBOUNCE_MS = 2000` |
| Manual refresh cancels in-flight queries | ✅ Complete | `useBoardRefresh.ts:84` — `cancelQueries` before manual fetch |
| No refetchInterval in board query | ✅ Complete | `useProjectBoard.ts:63-65` — deliberately removed |
| BoardColumn React.memo | ✅ Complete | `BoardColumn.tsx:20` — `memo(function BoardColumn ...)` |
| IssueCard React.memo | ✅ Complete | `IssueCard.tsx:107` — `memo(function IssueCard ...)` |
| ChatPopup rAF gating | ✅ Complete | `ChatPopup.tsx:86-101` — `requestAnimationFrame` pattern |
| AddAgentPopover useCallback | ✅ Complete | `AddAgentPopover.tsx:51` — `useCallback` on `updatePosition` |
| Callbacks in ProjectsPage | ✅ Complete | `ProjectsPage.tsx:103-108` — `useCallback` wrappers |
| onRefreshTriggered → resetTimer | ✅ Complete | `ProjectsPage.tsx:62-64` — wired via hook options |

**Remaining gap found**: `pipelineGridStyle` and `totalItems` in `ProjectsPage.tsx` not memoized — fixed by wrapping in `useMemo`.

## Findings

### 1. Current Backend State vs. Spec 022 (FR-002)

- **Decision**: Spec 022 is substantially implemented. WebSocket change detection (SHA256 hash comparison), board cache TTL alignment (300s), and sub-issue cache invalidation on manual refresh are all present. Remaining gaps are limited to: (a) fallback polling still potentially triggering board data refreshes, (b) sub-issue cache could benefit from tighter warm-cache reuse on automatic refreshes, and (c) reconnection handling could produce cascaded invalidations.
- **Rationale**: Code inspection of `backend/src/api/projects.py` confirms SHA256 hash comparison on each 30-second WebSocket cycle — refresh messages are only sent when data actually changes. `backend/src/api/board.py` confirms a 300-second cache TTL for board data (matching the frontend 5-minute auto-refresh interval) and pre-clears sub-issue caches on manual refresh. The polling loop in `polling_loop.py` uses adaptive backoff (60→120→240→300s cap after idle cycles) and rate-limit pre-checks. The remaining work is incremental tightening, not reimplementation.
- **Alternatives considered**:
  - Full reimplementation of Spec 022 — rejected because inspection shows the majority of Spec 022 acceptance criteria are already met.
  - Skip verification entirely — rejected because the spec requires explicit confirmation before optimization work begins (FR-002).
- **Key evidence**:
  - `projects.py`: WebSocket subscription computes `hashlib.sha256()` of task data and only sends `refresh` type when hash differs from previous
  - `board.py`: Cache key `board_data:{project_id}` with TTL=300s; manual refresh (`refresh=true`) bypasses cache and clears sub-issue entries
  - `polling_loop.py`: Adaptive backoff; rate-limit pre-checks at 100/500/150 remaining thresholds; sub-issues filtered out upfront

### 2. WebSocket Reconnection and Refresh Cascades (FR-012)

- **Decision**: Add a reconnection guard in the frontend `useRealTimeSync` hook. On WebSocket reconnection, perform a single tasks query invalidation. Do not invalidate the board data query, which follows its own 5-minute schedule. Prevent multiple rapid reconnections from stacking invalidations by debouncing the reconnection handler.
- **Rationale**: The current reconnection flow in `useRealTimeSync.ts` uses exponential backoff with jitter (1s → 30s cap), which is good for connection timing. However, each successful reconnection currently triggers a query invalidation cycle. If the WebSocket drops and reconnects multiple times in quick succession (e.g., network instability), this can create a cascade of invalidations.
- **Alternatives considered**:
  - Suppress all invalidation on reconnection — rejected because the first reconnection should fetch current state
  - Add server-side deduplication — rejected because the server already has hash-based change detection; the issue is client-side invalidation volume
- **Implementation approach**: Debounce reconnection invalidation to at most once per reconnection cycle. The `useRealTimeSync` hook already separates task queries from board queries, so the decouple is a matter of ensuring reconnection only targets `['projects', projectId, 'tasks']`.

### 3. Fallback Polling and Board Data Refresh (FR-004, FR-009)

- **Decision**: Ensure the fallback polling path in `useRealTimeSync.ts` only invalidates the tasks query, never the board data query. The board data query is exclusively refreshed by: (a) the 5-minute auto-refresh timer in `useBoardRefresh`, or (b) manual refresh triggered by the user.
- **Rationale**: The current fallback polling path targets `['projects', projectId, 'tasks']` for invalidation, which is correct. However, the interaction between fallback polling, auto-refresh, and manual refresh must be explicitly documented and tested to prevent future regression. The board auto-refresh timer in `useBoardRefresh.ts` is reset by WebSocket refreshes; if polling fallback does not reset the timer, the auto-refresh could fire shortly after a polling update, creating unnecessary work.
- **Alternatives considered**:
  - Polling invalidates board data when changes detected — rejected because board data is expensive (~23 API calls) and has its own schedule
  - Disable auto-refresh during polling fallback — rejected because polling has lower fidelity than WebSocket and auto-refresh provides a safety net
- **Implementation approach**: Verify the fallback polling path only targets task queries. Ensure the auto-refresh timer reset is called on polling updates (same as WebSocket updates) to maintain the 5-minute window from the last data update regardless of source.

### 4. Frontend Component Memoization Strategy (FR-009)

- **Decision**: Verify `BoardColumn` and `IssueCard` already use `React.memo()`. If not, apply it. Stabilize callback props (`onCardClick`) in the parent component using `useCallback`. Do not add custom deep comparators — shallow comparison is sufficient given the data flow.
- **Rationale**: Code inspection shows `BoardColumn` is exported via `export const BoardColumn = memo(function...)` and `IssueCard` is wrapped in `React.memo()`. However, if parent callback props are not stabilized with `useCallback`, the memo wrappers have no effect because new function references are created on every parent render. For a 100-card board across 5 columns, unstable callbacks cause 100+ unnecessary re-renders on a single-card status change.
- **Alternatives considered**:
  - Deep comparison via custom `areEqual` function — rejected because it adds complexity and the data flow already uses immutable patterns (TanStack Query returns new references only when data changes)
  - Virtualization (react-window, react-virtuoso) — rejected for first pass per spec; deferred to Phase 4 if measurements show it's needed
  - `shouldComponentUpdate` in class components — rejected because the codebase uses functional components
- **Implementation approach**:
  - Verify `BoardColumn` and `IssueCard` memo wrappers are present
  - In `ProjectsPage`, wrap `handleCardClick` and `handleProjectSwitch` in `useCallback` to stabilize the references
  - No custom comparators needed — shallow comparison is sufficient

### 5. Derived State Computation in ProjectsPage (FR-010)

- **Decision**: Wrap inline sorting, progress calculation, and rate-limit state derivation in `useMemo` hooks with appropriate dependency arrays. Stabilize event handlers with `useCallback`.
- **Rationale**: Code inspection of `ProjectsPage.tsx` shows `O(n log n)` sorting computed inline on every render, progress calculation from scratch on every render, and a multi-level rate-limit fallback chain computed inline. For a board with 100+ items, this represents measurable wasted computation per render cycle. `useMemo` ensures these values are only recomputed when their inputs change.
- **Alternatives considered**:
  - Move computation to a custom hook — rejected because the logic is page-specific and doesn't need to be shared
  - Move sorting to the server — rejected because sorting preferences are client-side and change frequently
  - Use a state management library (Zustand, Jotai) — rejected as over-engineering for this case; `useMemo` is sufficient
- **Implementation approach**:
  - `const sortedBoardData = useMemo(() => [...].sort(...), [boardData, sortField, sortDirection])`
  - `const progress = useMemo(() => computeProgress(boardData), [boardData])`
  - `const rateLimitInfo = useMemo(() => deriveRateLimitState(...), [dependencies])`
  - `const handleCardClick = useCallback((card) => ..., [dependencies])`
  - `const handleProjectSwitch = useCallback((projectId) => ..., [dependencies])`

### 6. Event Listener Throttling for ChatPopup and AddAgentPopover (FR-011)

- **Decision**: Throttle `mousemove` events in ChatPopup drag handling using `requestAnimationFrame` (rAF) gating. Memoize `updatePosition` callback in AddAgentPopover using `useCallback` to prevent re-registration on every render.
- **Rationale**: ChatPopup attaches `mousemove` listeners during drag that fire on every pixel of mouse movement. While cleanup is correct (listeners removed on mouseup), during active drag this can cause 60+ event handler invocations per second without rAF gating. AddAgentPopover recreates `updatePosition` on every render, causing scroll and resize listeners to be removed and re-added unnecessarily.
- **Alternatives considered**:
  - lodash `throttle` — rejected to avoid adding a dependency for a single use case; rAF is the standard browser-native approach for visual updates
  - CSS `will-change: transform` without JS changes — rejected because the issue is JS execution frequency, not GPU composition
  - Pointer Events API instead of Mouse Events — noted as a future improvement for mobile support, but not required for this performance pass
- **Implementation approach**:
  - ChatPopup: Add rAF gating to the `mousemove` handler during resize drag — only process position updates once per animation frame
  - AddAgentPopover: Wrap `updatePosition` in `useCallback` with appropriate dependencies so the callback reference is stable across renders

### 7. Sub-Issue Cache Warm Reuse on Automatic Refresh (FR-007)

- **Decision**: Ensure the board data fetch path in `github_projects/service.py` checks the sub-issue cache before making individual REST calls, and only fetches sub-issues with expired or missing cache entries. The existing cache infrastructure in `cache.py` supports per-key TTL checks.
- **Rationale**: The board endpoint currently clears all sub-issue caches on manual refresh (confirmed in `board.py`), but automatic refreshes should reuse warm sub-issue cache entries. The service layer (`service.py`) fetches sub-issues per-issue; adding a cache-check gate before each fetch eliminates redundant API calls when the cache is warm.
- **Alternatives considered**:
  - Batch sub-issue fetching via GraphQL — rejected for first pass because it requires changes to the GitHub API integration pattern
  - Increase sub-issue cache TTL to match board TTL — considered but the 600s sub-issue TTL (2x the board TTL) already provides good coverage; the issue is ensuring the cache is checked, not the TTL duration
- **Implementation approach**: Verify the `get_sub_issues` path in `service.py` checks `cache.get()` before making REST calls. If cache miss, fetch and `cache.set()` with the configured sub-issue TTL. The manual refresh path in `board.py` already clears sub-issue cache entries, so manual refresh correctly bypasses the cache.

### 8. Manual Refresh Priority and Deduplication (FR-006, FR-013)

- **Decision**: Ensure `useBoardRefresh.ts` cancels any in-progress automatic refresh when a manual refresh is triggered, and that manual refresh takes priority. Use TanStack Query's `cancelQueries` before initiating the manual fetch.
- **Rationale**: The spec requires that concurrent refresh requests are deduplicated with manual refresh taking priority (FR-013). If an automatic refresh is in-flight when the user clicks manual refresh, both requests could complete and cause unnecessary state updates. TanStack Query's `cancelQueries` provides the standard mechanism for this.
- **Alternatives considered**:
  - AbortController on fetch — rejected because TanStack Query already wraps fetch with AbortController internally; `cancelQueries` is the idiomatic approach
  - Ignore automatic refresh results if manual is pending — possible but more complex than simply canceling the automatic request
- **Implementation approach**: In the manual refresh handler in `useBoardRefresh.ts`, call `queryClient.cancelQueries({ queryKey: ['board', 'data', projectId] })` before triggering the manual fetch with `refresh=true`.

### 9. Baseline Measurement Protocol (FR-001, SC-008)

- **Decision**: Define a repeatable measurement protocol documented in quickstart.md. Backend: count outbound GitHub API calls over 5-minute idle window using backend logging. Frontend: use React DevTools Profiler + Chrome DevTools Performance tab for render counts and frame rates.
- **Rationale**: The spec mandates baseline measurements before any code changes (FR-001, Story 1). The protocol must be repeatable so post-optimization measurements use the same methodology (SC-008).
- **Alternatives considered**:
  - Automated instrumentation (OpenTelemetry, Sentry Performance) — rejected for first pass because it adds infrastructure; manual measurement is sufficient for a single optimization cycle
  - Backend request counting middleware — possible addition but the existing logging in polling_loop.py already tracks cycle-level cache hits; extending this is simpler than new middleware
- **Measurement protocol**:
  1. Backend idle: Open a board, wait 5 minutes, count outbound GitHub API calls from backend logs
  2. Backend per-refresh: Trigger a single board refresh, count outbound API calls from backend logs
  3. Frontend render: Use React DevTools Profiler to count component renders during a single-card status change on a 100-card board
  4. Frontend frame rate: Use Chrome DevTools Performance tab during card drag on a 100-card board
  5. Frontend network: Use Chrome DevTools Network tab to count board data requests during fallback polling and auto-refresh cycles

### 10. Refresh Path Coherence (FR-014)

- **Decision**: Document and enforce a single coherent refresh policy across all four refresh sources (WebSocket, fallback polling, auto-refresh, manual refresh). The policy matrix is captured in the refresh contract.
- **Rationale**: The spec requires all four refresh paths to follow a single coherent policy (FR-014, SC-011). Without explicit documentation and enforcement, the paths can drift independently and recreate the polling storm behavior that Spec 022 addressed.
- **Alternatives considered**:
  - Single refresh manager component — rejected as over-engineering; the existing hook-based separation (`useRealTimeSync` for WebSocket/polling, `useBoardRefresh` for auto/manual) is architecturally clean
  - Server-driven refresh policy — rejected because refresh scoping is a frontend concern tied to query key management
- **Implementation approach**: Define the refresh policy matrix in the refresh contract. Each refresh source maps to specific query invalidation targets and cache bypass rules. Test coverage must validate that each source follows its assigned policy.
