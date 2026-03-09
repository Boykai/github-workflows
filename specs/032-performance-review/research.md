# Research: Performance Review

**Feature**: 032-performance-review
**Date**: 2026-03-09
**Status**: Complete — all unknowns resolved

## R1: Current Backend State Against Spec 022

**Decision**: Spec 022 optimizations are fully implemented. The current codebase already includes hash-based WebSocket change detection, sub-issue caching with 600s TTL, board data cache TTL of 300s (aligned with frontend 5-minute auto-refresh), and frontend query invalidation decoupling.

**Rationale**: Code inspection confirms:
- `backend/src/api/projects.py` (Lines 375–388): SHA-256 hash-based change detection in WebSocket handler. `last_sent_hash` compared each 30-second cycle; refresh message only sent when hash differs.
- `backend/src/services/github_projects/service.py` (Lines 4329–4382): `get_sub_issues()` checks `InMemoryCache` first with key `sub_issues:{owner}/{repo}#{issue_number}` and 600s TTL.
- `backend/src/api/board.py` (Line 359): Board data cache TTL is 300 seconds, aligned with frontend auto-refresh interval.
- `frontend/src/hooks/useRealTimeSync.ts` (Lines 64, 71, 83): WebSocket message handler only invalidates `['projects', projectId, 'tasks']`; board data query is not invalidated. Comments confirm intentional decoupling.
- `backend/src/api/board.py` (Lines 301–322): Manual refresh (`refresh=true`) bypasses cache and clears sub-issue caches.

**Alternatives considered**:
- Re-implementing Spec 022 changes: Rejected — already fully landed.
- Starting from scratch with new caching strategy: Rejected — existing infrastructure is sound and battle-tested.

**Implication**: Phase 2 backend work focuses on remaining gaps beyond Spec 022: polling loop behavior during idle, reconnection refresh storms, and verifying change detection completeness.

## R2: Idle API Consumption During Polling Fallback

**Decision**: The copilot polling loop (`polling_loop.py`) is already rate-limit-aware with adaptive backoff, but the fallback polling in `useRealTimeSync.ts` (30-second interval) still invalidates the tasks query unconditionally, which can trigger downstream API calls even when data is unchanged.

**Rationale**:
- `copilot_polling/polling_loop.py` (Lines 384–438): Adaptive polling with consecutive idle detection, interval doubling, and 8x max multiplier up to 300s. Rate-limit thresholds at 50 (pause), 200 (slow), 100 (skip expensive). This is well-designed and rate-limit safe.
- `useRealTimeSync.ts` (Lines 100–112): Fallback polling uses `setInterval` with `WS_FALLBACK_POLL_MS = 30,000ms` and calls `queryClient.invalidateQueries()` for tasks query key. This triggers a refetch regardless of whether data has changed.
- The tasks API endpoint itself is lightweight compared to board data, but unconditional invalidation every 30 seconds still generates unnecessary API calls during idle.

**Alternatives considered**:
- Adding client-side change detection to polling: Could compare task data hashes client-side, but adds complexity for minimal gain since backend already has WebSocket change detection.
- Increasing fallback poll interval: Simple but delays change detection when WebSocket is down.
- ETag-based conditional fetching: Server returns 304 Not Modified if data unchanged. More efficient but requires backend endpoint changes.

**Implementation detail**: The recommended approach is to verify that fallback polling invalidation does not cascade to board data (already confirmed in R1) and to ensure reconnection after WebSocket recovery stops the polling timer cleanly (already implemented — Line 151 calls `stopPolling()` on WebSocket open).

## R3: Frontend Reconnection Refresh Storm Prevention

**Decision**: The existing reconnection debounce (2-second window) in `useRealTimeSync.ts` adequately prevents refresh storms during WebSocket reconnection. The `initial_data` message handler skips invalidation if previous invalidation occurred within `RECONNECT_DEBOUNCE_MS = 2,000ms`.

**Rationale**:
- `useRealTimeSync.ts` (Lines 13–14, 59–63): Debounce window of 2 seconds using `lastInvalidationRef` timestamp comparison.
- On reconnection, only `initial_data` triggers invalidation, not additional refresh messages within the debounce window.
- `useBoardRefresh.ts` (Lines 67, 78, 105–106): Deduplication via `isRefreshingRef` prevents concurrent refresh executions. Multiple rapid `refresh()` calls result in only one actual execution.

**Alternatives considered**:
- Queue-based refresh batching: Over-engineering for the current use case.
- Longer debounce window: 2 seconds is appropriate given the 30-second refresh cycle.

## R4: Board Render Optimization Strategy

**Decision**: Use `useMemo` for derived data (sorting, aggregation, stats computation) in `ProjectsPage.tsx`, verify React.memo effectiveness on `BoardColumn` and `IssueCard` by ensuring parent callback stability via `useCallback`, and add throttling to the `AddAgentPopover` scroll/resize positioning listener.

**Rationale**:
- `ProjectsPage.tsx`: Contains 20+ hooks and performs render-time sorting/aggregation via `.reduce()` on columns. Wrapping derived data in `useMemo` prevents recomputation on unrelated state changes.
- `BoardColumn.tsx` (Line 20): Already uses `React.memo`. Effectiveness depends on parent props stability — callbacks from `ProjectsPage` must be wrapped in `useCallback`.
- `IssueCard.tsx` (Line 108): Already uses `React.memo`. Same callback stability dependency.
- `AddAgentPopover.tsx` (Lines 72–83): `scroll` and `resize` event listeners call `updatePosition()` on every event with no throttling. Adding `requestAnimationFrame` gating (same pattern as `ChatPopup.tsx`) prevents excessive layout recalculation.

**Alternatives considered**:
- React.memo with custom comparator: Rejected — shallow comparison is sufficient when parent callbacks are stable.
- Board virtualization (react-window/react-virtual): Explicitly out of scope for first pass per spec. Deferred to Phase 4 optional second-wave work.
- Component splitting of ProjectsPage: Beneficial but higher risk. Deferred.

## R5: Chat Popup Drag Performance

**Decision**: The existing `ChatPopup.tsx` drag implementation already uses `requestAnimationFrame` gating, which is the correct pattern. No changes needed.

**Rationale**:
- `ChatPopup.tsx` (Lines 97–113): `onMouseMove` handler checks `if (rafId) return` before scheduling a new `requestAnimationFrame`. This limits position updates to once per frame (~60 fps).
- `onMouseUp` handler (Lines 115–128) cancels pending RAF and persists size to localStorage.
- Event listeners are attached to `window` on mount and cleaned up on unmount (Lines 130–137).

**Alternatives considered**:
- `lodash.throttle`: Unnecessary — RAF gating is equivalent to ~16ms throttle at 60 fps, which is optimal.
- CSS transform for drag position: Would avoid layout thrashing but requires refactoring the resize logic. Out of scope.

## R6: AddAgentPopover Event Listener Optimization

**Decision**: Add `requestAnimationFrame` gating to the `updatePosition()` handler in `AddAgentPopover.tsx` to prevent excessive layout recalculation during rapid scroll/resize events.

**Rationale**:
- `AddAgentPopover.tsx` (Lines 72–83): `scroll` (capture phase, passive) and `resize` listeners call `updatePosition()` on every event. During rapid scrolling, this can trigger `getBoundingClientRect()` many times per frame, causing layout thrashing.
- The `ChatPopup.tsx` component already uses the correct RAF gating pattern (R5). Applying the same pattern to `AddAgentPopover.tsx` ensures consistency.

**Alternatives considered**:
- `lodash.throttle(updatePosition, 16)`: Equivalent to RAF but adds a dependency on throttle timing accuracy. RAF is more precise.
- CSS `position: sticky` or `position: fixed` with CSS transforms: Would eliminate JavaScript positioning entirely but requires restructuring the portal-based rendering approach.

## R7: Derived Data Memoization in ProjectsPage

**Decision**: Wrap derived-data computations (column stats, sorted/filtered lists, aggregated counts) in `useMemo` with appropriate dependency arrays to prevent recalculation on unrelated re-renders.

**Rationale**:
- `ProjectsPage.tsx`: Integrates 20+ hooks. Any state change in any hook triggers a re-render of the entire component, recomputing all inline derived data.
- `.reduce()` operations on board columns for stats calculation run on every render even when board data hasn't changed.
- `useMemo` with `[boardData]` as dependency ensures stats are only recalculated when board data actually changes.

**Alternatives considered**:
- Moving derived data into custom hooks: Adds indirection without solving the re-render problem.
- React.useDeferredValue: Applicable for large lists but the primary issue is unnecessary recomputation, not rendering priority.
- Splitting ProjectsPage into sub-components: Would isolate render scopes but is higher risk and more invasive. Deferred to second wave.

## R8: Test Extension Strategy

**Decision**: Extend existing test suites rather than creating new test files. Add targeted tests for changed behavior within the current test structure.

**Rationale**:
- Backend: `test_cache.py` (14 tests), `test_api_board.py` (13 tests), `test_copilot_polling.py` (227 tests) provide comprehensive existing coverage. New tests should follow existing patterns (pytest-asyncio, mock-based).
- Frontend: `useRealTimeSync.test.tsx` and `useBoardRefresh.test.tsx` have thorough coverage with fake timers and spy-based assertions. New tests extend these suites.
- Constitution Principle IV (Test Optionality): Tests are mandated by spec (FR-014) and should cover cache behavior, change detection, polling, and refresh logic changes.

**Alternatives considered**:
- Separate performance test suite: Over-engineering for the current scope. Manual profiling supplemented by unit tests is sufficient.
- E2E performance tests with Playwright: Useful for second wave but not necessary for the first pass where changes are surgical.
