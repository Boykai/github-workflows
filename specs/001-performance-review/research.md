# Research: Performance Review

**Feature**: 001-performance-review
**Date**: 2026-03-15
**Status**: Complete — all NEEDS CLARIFICATION items resolved

## Research Tasks

### R-001: Current State of Spec 022 Rate-Limit Protection

**Context**: The spec references "Spec 022 (API Rate Limit Protection)" as prior work. Need to confirm what is implemented and what gaps remain.

**Decision**: Spec 022 acceptance criteria are substantially implemented in the current codebase. The `specs/022-api-rate-limit-protection/` directory does not exist in the repository (it may have been completed and archived, or its criteria were implemented without a formal spec directory). Evidence of implementation is spread across backend source and test files.

**Rationale**: Codebase audit confirms the following Spec 022-aligned behaviors are already in place:
- **Board cache TTL alignment**: `board.py` sets 300-second (5 min) TTL for board data, matching the frontend auto-refresh cycle in `useBoardRefresh.ts`.
- **Sub-issue cache invalidation on manual refresh**: `board.py` clears sub-issue caches before fetching when `refresh=True`. Test `test_manual_refresh_clears_sub_issue_caches` validates this.
- **Change detection via data hashing**: `compute_data_hash()` in `cache.py` produces SHA-256 hashes. Board data cache entries store `data_hash`. WebSocket subscription in `projects.py` uses `compute_data_hash()` to suppress unchanged refreshes.
- **Rate-limit-aware polling**: `polling_loop.py` implements pause thresholds, expensive-step skipping, adaptive idle backoff (up to 300s), and stale-cache cleanup. Extensively tested in `test_copilot_polling.py`.
- **Inflight request coalescing**: `service.py` deduplicates in-progress GraphQL requests (up to 256 cached).
- **Stale fallback on error**: `cached_fetch()` and board endpoint serve expired cache on GitHub API errors.

**Remaining gaps to address in this feature**:
1. WebSocket subscription sends initial tasks with `force_refresh=True` (bypasses cache); verify whether the 30-second periodic check truly suppresses unchanged data or still pushes to clients.
2. Fallback polling in `useRealTimeSync.ts` invalidates the tasks query every 30 seconds. While it does NOT invalidate board data, it still triggers refetches that may be unnecessary if data is unchanged.
3. Background polling (`polling_loop.py`) calls `clear_cycle_cache()` at the top of each iteration, which forces fresh fetches. This is correct for detection but may cause unnecessary API calls when nothing has changed — need to confirm the interaction with adaptive backoff.
4. `workflow.py` contains multiple calls to `resolve_repository()` that duplicate the shared utility pattern. While not directly a rate-limit issue, it adds unnecessary API calls.

**Alternatives considered**: Starting from scratch with a new rate-limit spec was rejected because the existing implementation is substantial and mostly correct. Building on it is lower risk.

---

### R-002: Backend Idle Board API Activity Sources

**Context**: Need to identify all sources of outbound API calls when a board is open and idle.

**Decision**: There are four distinct activity sources during idle board viewing, each with a different optimization path.

**Rationale**:
1. **WebSocket subscription periodic check** (`projects.py`): Every 30 seconds, fetches cached project tasks and compares data hash. If unchanged, no message is sent to the client. If the cache is cold (expired after 300s), this triggers a fresh API call. **Optimization**: Ensure the periodic check reuses warm cache without forcing refresh; only fetch from GitHub when the cache entry is expired.
2. **Frontend fallback polling** (`useRealTimeSync.ts`): When WebSocket is unavailable, polls every 30 seconds and invalidates the tasks query. Each invalidation triggers a backend fetch if the query is stale. **Optimization**: Add change-detection check to the polling fallback so it skips invalidation when data is unchanged (similar to WebSocket path).
3. **Frontend auto-refresh timer** (`useBoardRefresh.ts`): Fires every 5 minutes, invalidates the board data query. This is the intended refresh cycle and aligns with the 300s board cache TTL. **Optimization**: This is working as designed; no change needed unless baselines show it fires more often than expected.
4. **Background Copilot polling** (`polling_loop.py`): Runs every 60 seconds with adaptive backoff. Clears cycle cache per iteration, which forces fresh in-memory lookups. **Optimization**: Adaptive backoff already reduces frequency when idle. The cycle cache clear is necessary for correctness (detecting new PRs). No change recommended unless baselines show material cost.

**Alternatives considered**: Disabling all background activity was rejected because real-time sync and polling serve legitimate purposes. The optimization target is unnecessary calls within those flows, not the flows themselves.

---

### R-003: Frontend Query Invalidation and Rerender Scope

**Context**: Need to understand the current query invalidation strategy and its impact on rerenders.

**Decision**: The current invalidation strategy is already well-scoped. The primary optimization opportunities are in derived-data computation and component prop stability, not in query invalidation breadth.

**Rationale**:
- `useRealTimeSync.ts` only invalidates `['projects', projectId, 'tasks']` — it does NOT invalidate board data. This is correct behavior.
- `useBoardRefresh.ts` invalidates `['board', 'data', selectedProjectId]` on auto-refresh and forces a full fetch on manual refresh. This is also correct.
- `BoardColumn.tsx` and `IssueCard.tsx` are already wrapped in `memo()`. Sub-issue rows are also memoized.
- `ProjectsPage.tsx` uses `useMemo` for grid layout, hero stats, pipeline assignment, and stage map.
- **Remaining opportunities**:
  1. Derived-data computation in `ProjectsPage.tsx`: `reduce()` across columns for total items runs on every render. While `useMemo` covers several computations, verify all heavy aggregations are memoized.
  2. Component prop stability: Ensure that objects passed as props to memoized components are stable references (not recreated each render), or the `memo()` wrappers are ineffective.
  3. Event listener rationalization: `ChatPopup.tsx` and `AddAgentPopover.tsx` already use RAF throttling. The drag interaction in `@dnd-kit` may have separate overhead worth profiling.

**Alternatives considered**: Replacing TanStack React Query with a custom state management solution was rejected (too invasive, violates SC-009 no-new-dependencies constraint). Adding virtualization was explicitly deferred per spec scope boundaries.

---

### R-004: Refresh Policy Coherence Across All Sources

**Context**: Multiple refresh sources coexist (WebSocket, fallback polling, auto-refresh timer, manual refresh). Need to confirm they follow a single coherent policy (FR-010).

**Decision**: The current implementation has a mostly coherent refresh policy, but there are two integration seams that need tightening.

**Rationale**:
- **Manual refresh**: `useBoardRefresh.ts` cancels in-progress queries, calls backend with `refresh=true` (bypasses cache, clears sub-issue caches), writes result directly to query cache. This is the most authoritative path and correctly overrides all other refresh sources.
- **Auto-refresh timer**: `useBoardRefresh.ts` fires every 5 minutes and uses `invalidateQueries` (allows cache hits). The timer resets after manual refresh, preventing overlap. Page Visibility API pauses the timer when the tab is hidden.
- **WebSocket updates**: `useRealTimeSync.ts` handles `task_update`/`status_changed` by calling `onRefreshTriggered` (which resets the auto-refresh timer) and updates task data via `setQueryData`. Board data is NOT invalidated by WebSocket events.
- **Fallback polling**: `useRealTimeSync.ts` fallback polling invalidates tasks query every 30 seconds and calls `onRefreshTriggered`.

**Seam 1 — Fallback polling board interaction**: When polling fallback is active and the auto-refresh timer fires simultaneously, both can trigger activity. The 2-second debounce window in `requestBoardReload` handles most cases, but a concurrent poll + auto-refresh could theoretically produce two requests within the same window. **Fix**: Ensure the polling fallback path is aware of the auto-refresh timer and vice versa; the `onRefreshTriggered` callback already resets the auto-refresh timer, which mitigates this in practice.

**Seam 2 — WebSocket reconnection storm**: On reconnection, `initial_data` messages trigger invalidation with a 2-second debounce. If multiple tabs reconnect simultaneously (e.g., after laptop wake), each tab independently invalidates. **Fix**: Per-session scope already limits this; the debounce window is sufficient for single-tab use. Multi-tab deduplication is out of scope for the first pass.

**Alternatives considered**: Building a centralized refresh coordinator was rejected as premature abstraction (violates Principle V). The current hook-based approach with callbacks is simple and testable.

---

### R-005: Test Extension Strategy

**Context**: FR-014 requires maintaining or extending automated test coverage. Need to identify what to extend without introducing new frameworks.

**Decision**: Extend existing test suites with targeted assertions for the specific behaviors being optimized. No new test frameworks or dependencies.

**Rationale**:
- **Backend**: `test_cache.py` (264 lines), `test_api_board.py` (331 lines), and `test_copilot_polling.py` (9843 lines) provide comprehensive coverage. Extensions should add assertions for:
  - Warm cache reuse reducing call count (SC-002 validation)
  - Change detection suppressing unchanged refreshes (FR-004)
  - Polling idle backoff behavior (already well-tested; add specific idle-board scenario if missing)
- **Frontend**: `useRealTimeSync.test.tsx` (806 lines) and `useBoardRefresh.test.tsx` (584 lines) cover the critical paths. Extensions should add assertions for:
  - Polling fallback not triggering board data invalidation (already tested; confirm completeness)
  - Refresh deduplication across simultaneous triggers (FR-010)
  - Timer reset on WebSocket reconnection
- **Manual verification**: One network profiling pass (backend idle activity over 5 min) and one rendering profiling pass (board interaction rerender counts) to validate before-and-after improvements.

**Alternatives considered**: Adding Playwright end-to-end performance tests was rejected (too heavyweight, new infrastructure, first pass should validate with unit/integration tests + manual profiling).

---

### R-006: Performance Measurement Approach

**Context**: Baselines must be captured before code changes (FR-001, SC-001 through SC-006). Need to define a practical measurement approach.

**Decision**: Use a checklist-based measurement approach combining automated test output, manual network profiling, and manual rendering profiling. No new instrumentation infrastructure in the first pass.

**Rationale**:
- **Backend idle baseline**: Open a board, wait 5 minutes, count outbound GitHub API calls (via logging or network capture). The backend already logs API calls with `structlog`; grep logs for GraphQL/REST requests during the window.
- **Backend cache-hit baseline**: Run a board refresh with cold cache, then with warm cache. Compare outbound call counts. The `test_api_board.py` tests already validate cache-hit behavior; extend with call-count assertions.
- **Frontend load baseline**: Profile a board load with React DevTools Profiler; record time-to-interactive, render count, and component tree depth. Note rerender count per component.
- **Frontend interaction baseline**: Profile drag, click, and detail-open interactions. Record rerender counts and interaction latency. React DevTools Profiler's "Highlight updates" mode shows which components rerender.
- **Regression thresholds**: Define "no worse than baseline" as the regression threshold. Define target improvements per SC-001 through SC-006.

**Alternatives considered**: Adding permanent APM instrumentation (e.g., OpenTelemetry) was rejected for the first pass (new dependency, scope creep). Lightweight instrumentation is recommended as follow-on work if repeated performance tuning is needed.

## Summary of Resolved Unknowns

| Item | Resolution |
|------|-----------|
| Spec 022 implementation status | Substantially complete in current codebase; gaps identified for WebSocket periodic check, fallback polling invalidation, and workflow.py duplication |
| Idle activity sources | Four sources identified: WebSocket periodic check, frontend fallback polling, auto-refresh timer, background Copilot polling |
| Query invalidation scope | Already well-scoped; opportunities are in derived-data memoization and prop stability |
| Refresh policy coherence | Mostly coherent; two seams identified for tightening |
| Test extension strategy | Extend existing suites; no new frameworks |
| Performance measurement | Checklist-based with manual profiling; no new instrumentation infrastructure |
