# Research: Performance Review — Balanced First Pass

**Feature Branch**: `028-performance-review`
**Date**: 2026-03-08
**Status**: Complete — all technical unknowns resolved

## Findings

### 1. Current Backend State vs. Spec 022 (FR-002)

- **Decision**: Spec 022 is substantially implemented. WebSocket change detection (SHA256 hash comparison), board cache TTL alignment (300s), and sub-issue cache invalidation on manual refresh are all present and working. Remaining gaps are limited to: (a) verifying fallback polling does not trigger expensive board refreshes, (b) verifying sub-issue cache warm reuse on automatic (non-manual) refreshes.
- **Rationale**: Code inspection of `backend/src/api/projects.py` confirms SHA256 hash comparison on each 30-second WebSocket cycle — refresh messages are only sent when data actually changes. `backend/src/api/board.py` confirms a 300-second cache TTL for board data (matching the frontend 5-minute auto-refresh interval) and proactively clears sub-issue caches before manual refresh fetch. `polling_loop.py` uses adaptive backoff (60→120→240→300s cap) with rate-limit pre-checks and filters out sub-issues upfront.
- **Alternatives considered**:
  - Full reimplementation of Spec 022 — rejected because inspection shows the majority of Spec 022 acceptance criteria are already met.
  - Skip verification entirely — rejected because the spec requires explicit confirmation before optimization work begins (FR-002).
- **Key evidence**:
  - `projects.py`: WebSocket subscription computes `hashlib.sha256()` of task data and only sends `refresh` type when hash differs from previous
  - `board.py`: Cache key `board_data:{project_id}` with TTL=300s; manual refresh (`refresh=true`) bypasses cache and clears sub-issue entries before fetching
  - `polling_loop.py`: Adaptive backoff with RATE_LIMIT_SKIP_EXPENSIVE_THRESHOLD and RATE_LIMIT_SLOW_THRESHOLD; sub-issues filtered out upfront
  - `service.py`: Sub-issue cache TTL=600s; BoundedDict(maxlen=256) for request deduplication; per-cycle cache cleared at start of each polling iteration

### 2. WebSocket Reconnection and Refresh Cascades (FR-013)

- **Decision**: The frontend `useRealTimeSync` hook already implements a 2-second reconnection debounce window to prevent query storms on rapid reconnects. On reconnection, only the tasks query is invalidated — the board data query is not touched. This behavior is correct and requires no further changes.
- **Rationale**: Code inspection of `useRealTimeSync.ts` confirms debounced reconnection invalidations (2-second window). The hook separates task invalidations (`['projects', projectId, 'tasks']`) from board data, and explicit comments document the intent not to invalidate board data during polling fallback or WebSocket reconnection. Exponential backoff with jitter (1s → 30s cap) is also present.
- **Alternatives considered**:
  - Additional server-side deduplication — rejected because the server already has hash-based change detection; the issue is client-side invalidation volume, which is already addressed
  - Suppress all invalidation on reconnection — rejected because the first reconnection should fetch current state
- **Implementation approach**: Verify and extend existing behavior. No code changes needed for reconnection handling. Ensure test coverage documents this contract.

### 3. Fallback Polling and Board Data Refresh (FR-004, FR-005)

- **Decision**: The fallback polling path in `useRealTimeSync.ts` correctly targets only the tasks query for invalidation, never the board data query. The board data query is exclusively refreshed by: (a) the 5-minute auto-refresh timer in `useBoardRefresh`, or (b) manual refresh triggered by the user.
- **Rationale**: Code inspection confirms the polling fallback invalidation scope is limited to `['projects', projectId, 'tasks']`. Comments in the code explicitly document this policy. The auto-refresh timer in `useBoardRefresh.ts` is reset by any data update (WebSocket or polling), maintaining a consistent 5-minute window from the last update regardless of refresh source.
- **Alternatives considered**:
  - Polling invalidates board data on change detection — rejected because board data is expensive and has its own 5-minute schedule
  - Disable auto-refresh during polling fallback — rejected because polling has lower fidelity than WebSocket and auto-refresh provides a safety net
- **Implementation approach**: Verify the existing behavior. Ensure the auto-refresh timer reset path is called consistently on polling updates (same as WebSocket updates). Document the contract in the refresh-contract artifact.

### 4. Frontend Component Memoization Status (FR-010)

- **Decision**: Both `BoardColumn` and `IssueCard` are already wrapped in `React.memo()`. The remaining optimization work is to stabilize function props (`onCardClick`, `getGroups`) in the parent `ProjectsPage` using `useCallback`, and to stabilize object props (`blockingIssueNumbers` as a Set) to prevent unnecessary re-renders of memoized children.
- **Rationale**: Code inspection confirms `BoardColumn` (line 6/20) and `IssueCard` (line 6/107) are both exported with `React.memo()`. However, `React.memo()` only prevents re-renders when props are referentially equal. If the parent (`ProjectsPage`) recreates callback functions on every render, the memo wrapper is ineffective. The key stabilization targets are: `handleCardClick`, `handleCloseModal`, and any function props passed to columns.
- **Alternatives considered**:
  - Deep comparison via custom `areEqual` function — rejected because it adds complexity and the data flow already uses immutable patterns (TanStack Query returns new references only when data changes)
  - Virtualization (react-window, react-virtuoso) — rejected for first pass per spec; deferred to Phase 4 if measurements show it's needed
- **Implementation approach**:
  - In `ProjectsPage`, wrap `handleCardClick` in `useCallback` to stabilize the reference
  - In `ProjectsPage`, wrap `handleCloseModal` in `useCallback`
  - In `ProjectsPage`, wrap `handleProjectSwitch` in `useCallback`
  - Verify `getGroups` and `blockingIssueNumbers` are already memoized (confirmed: both use `useMemo`)

### 5. Derived State Computation in ProjectsPage (FR-011)

- **Decision**: `ProjectsPage` already memoizes `blockingIssueNumbers` and `assignedStageMap` with `useMemo`. Remaining inline computations (`totalItems`, `projectsRateLimitError`, `boardRateLimitError`, `pipelineGridStyle`) are lightweight and do not warrant memoization. The primary optimization target is stabilizing event handler callbacks with `useCallback` (see Finding 4).
- **Rationale**: Code inspection shows `totalItems` is a simple `.length` access, and the rate-limit derivations are ternary chains with no computation. `pipelineGridStyle` creates a new object on each render but is passed to a `style` prop (React compares style objects shallowly, so this is low-impact). The material performance gains come from stabilizing callbacks that break `React.memo()` on child components, not from memoizing trivial inline expressions.
- **Alternatives considered**:
  - Memoize all inline expressions — rejected because the overhead of `useMemo` wrapper exceeds the cost of the trivial computations themselves
  - Move computation to a custom hook — rejected because the logic is page-specific and doesn't need to be shared
- **Implementation approach**: Focus `useCallback` on event handlers. Leave trivial inline derivations as-is.

### 6. Event Listener Throttling Assessment (FR-012)

- **Decision**: `ChatPopup` already uses `requestAnimationFrame` (RAF) gating for drag event listeners — no further throttling needed. `AddAgentPopover` repositioning listeners on scroll/resize lack debouncing and should be debounced or RAF-gated to prevent excessive repositioning calls during rapid scrolling.
- **Rationale**: `ChatPopup` drag handling (lines 85-126) stores a `rafId` and only processes position updates once per animation frame, which is the standard browser-native approach. This limits updates to ~60fps. `AddAgentPopover` (in `board/AddAgentPopover.tsx`) attaches scroll and resize listeners that call `updatePosition` directly without any throttling. During rapid scrolling, this can fire 100+ times per second.
- **Alternatives considered**:
  - lodash `throttle` — rejected to avoid adding a dependency for a single use case; RAF or a simple debounce is sufficient
  - CSS `will-change: transform` without JS changes — rejected because the issue is JS execution frequency, not GPU composition
- **Implementation approach**:
  - ChatPopup: No changes needed (already RAF-gated)
  - AddAgentPopover: Wrap `updatePosition` in `useCallback` with appropriate dependencies; consider adding RAF gating or `requestAnimationFrame`-based throttling to scroll/resize handlers

### 7. Sub-Issue Cache Warm Reuse on Automatic Refresh (FR-008)

- **Decision**: The `get_sub_issues` path in `service.py` already implements per-issue caching with a 600-second TTL. The cache is checked before making REST API calls, and only issues with expired or missing cache entries trigger new API calls. This behavior is correct for automatic refreshes.
- **Rationale**: Code inspection of `service.py` (lines 4325-4378) confirms the sub-issue fetch path uses the cache with 600s TTL. The manual refresh path in `board.py` clears sub-issue entries before fetching, ensuring manual refresh always gets fresh data. No gap exists in the sub-issue caching logic.
- **Alternatives considered**:
  - Batch sub-issue fetching via GraphQL — rejected for first pass because it requires changes to the GitHub API integration pattern
  - Increase sub-issue cache TTL — the 600s TTL (2x board TTL) already provides coverage across two automatic refresh cycles
- **Implementation approach**: No code changes needed. Verify cache hit/miss behavior during baseline measurement. Document the contract.

### 8. Manual Refresh Priority and Deduplication (FR-014)

- **Decision**: Verify that `useBoardRefresh.ts` cancels any in-progress automatic refresh when manual refresh is triggered using TanStack Query's `cancelQueries`. This ensures manual refresh takes priority and prevents duplicate requests.
- **Rationale**: The spec requires that concurrent refresh requests are deduplicated with manual refresh taking priority (FR-014). If an automatic refresh is in-flight when the user clicks manual refresh, both requests could complete and cause unnecessary state updates. TanStack Query's `cancelQueries` provides the standard mechanism.
- **Alternatives considered**:
  - AbortController on fetch — rejected because TanStack Query wraps fetch with AbortController internally; `cancelQueries` is the idiomatic approach
  - Ignore automatic refresh results if manual is pending — more complex than simply canceling the automatic request
- **Implementation approach**: Verify the manual refresh handler calls `queryClient.cancelQueries({ queryKey: ['board', 'data', projectId] })` before triggering the manual fetch with `refresh=true`. If not present, add it.

### 9. Baseline Measurement Protocol (FR-001, SC-008)

- **Decision**: Define a repeatable measurement protocol documented in `quickstart.md`. Backend: count outbound GitHub API calls over 5-minute idle window using backend logging. Frontend: use React DevTools Profiler + Chrome DevTools Performance tab for render counts and frame rates.
- **Rationale**: The spec mandates baseline measurements before any code changes (FR-001, User Story 1). The protocol must be repeatable so post-optimization measurements use the same methodology for valid before/after comparison.
- **Alternatives considered**:
  - Automated instrumentation (OpenTelemetry, Sentry Performance) — rejected for first pass because it adds infrastructure; manual measurement is sufficient for a single optimization cycle
  - Backend request counting middleware — possible addition but the existing logging already tracks cycle-level cache hits; extending this is simpler than new middleware
- **Measurement protocol**: See `quickstart.md` for the full protocol definition.
