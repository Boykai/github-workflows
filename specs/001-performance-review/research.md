# Research: Performance Review

**Feature**: 001-performance-review  
**Date**: 2026-03-22  
**Status**: Complete

## Research Task 1: Current Backend Cache Architecture

**Question**: How does the existing in-memory cache work, and what are the TTLs, stale fallback patterns, and hash comparison mechanisms already in place?

**Decision**: The existing `InMemoryCache` in `solune/backend/src/services/cache.py` is mature and sufficient. No new cache infrastructure is needed.

**Rationale**: The cache already provides TTL-based expiration (default 300s), stale fallback on errors (including rate limit), data hash comparison via `compute_data_hash()` (SHA-256 of JSON-serialized data), and the `cached_fetch()` async helper that combines all these patterns. The board endpoint already uses a 300-second TTL (`board_data:{project_id}` cache key), and sub-issues use a 600-second TTL. The hash comparison pattern refreshes TTL without re-storing data when the hash is unchanged, which is exactly the mechanism needed for WebSocket change detection.

**Alternatives Considered**:
- Redis or external cache: Rejected — adds infrastructure complexity for a single-process deployment. The in-memory cache is appropriate for the current scale.
- Separate cache implementation for board data: Rejected — the existing `InMemoryCache` class handles all needed patterns.

---

## Research Task 2: WebSocket Subscription Refresh Loop and Change Detection

**Question**: Does the WebSocket subscription loop in `projects.py` already implement hash-based change detection to suppress redundant refresh messages?

**Decision**: The subscription loop uses a stale-revalidation counter pattern but does not yet use hash-based change detection for suppressing refresh messages. The `data_hash_fn` pattern exists in `cached_fetch()` but is not wired into the subscription loop's send-tasks flow.

**Rationale**: The current loop (in `projects.py`) checks cache freshness and uses a stale counter (force-refresh after 10 stale cycles), but it sends refresh messages on every cycle regardless of whether data has changed. The board endpoint already computes content hashes (excluding `rate_limit`), so the infrastructure exists. The gap is in the subscription loop: it needs to compare the current data hash against the last-sent hash and skip the message if unchanged.

**Alternatives Considered**:
- ETag-based comparison with GitHub API: Available via `cached_fetch` but requires additional upstream integration and doesn't help with the WebSocket send decision (which operates on cached data, not raw API responses).
- Timestamp-based comparison: Rejected — unreliable when data is fetched from cache (cache hit timestamps don't reflect data freshness).

---

## Research Task 3: Sub-Issue Cache Behavior on Board Refresh

**Question**: Are sub-issue caches properly cleared on manual refresh and reused on non-manual refresh? What's the current implementation status?

**Decision**: Sub-issue cache handling is already implemented correctly. Manual refresh clears sub-issue caches before fetching; non-manual refresh reuses cached sub-issues with a 600-second TTL.

**Rationale**: In `board.py`, manual refresh (`refresh=True`) explicitly deletes all sub-issue cache entries for the board's items before fetching new data (lines 389-399). In `github_projects/service.py` (IssuesMixin), `get_sub_issues()` checks cache first and only makes a REST API call on cache miss. The 600-second sub-issue TTL is intentionally longer than the board TTL (300s), so sub-issue data survives across multiple non-manual board refreshes. This behavior aligns with Spec 022 targets and the spec's FR-005/FR-006.

**Alternatives Considered**:
- Shared sub-issue cache across users: Rejected — cache keys include token-scoped identifiers, preventing cross-user data exposure.
- Batch sub-issue fetching: Not available in the GitHub API (no bulk sub-issues endpoint exists).

---

## Research Task 4: Fallback Polling Impact on Board Data

**Question**: Does fallback polling (when WebSocket is unavailable) trigger expensive board data refetches, or is it limited to task-level queries?

**Decision**: The frontend fallback polling currently invalidates only the tasks query (`['projects', projectId, 'tasks']`), which is the correct behavior. However, this must be verified and preserved as optimization work proceeds.

**Rationale**: In `useRealTimeSync.ts`, the polling fallback path calls `queryClient.invalidateQueries({ queryKey: ['projects', projectId, 'tasks'] })` — the same invalidation as WebSocket message handling. The board data query (`['board', 'data', projectId]`) refreshes on its own 5-minute schedule via `useBoardRefresh`. This separation is already correct per FR-007 and FR-008. The key risk is that future changes could inadvertently broaden the invalidation scope.

**Alternatives Considered**:
- Polling that also invalidates board data: Rejected — this recreates the polling storm problem. Board data should only refresh on its own timer or manual refresh.
- No polling fallback at all: Rejected — some environments block WebSocket; polling is necessary for resilience.

---

## Research Task 5: Frontend Memoization and Re-render Patterns

**Question**: What is the current state of memoization in board components, and where are the remaining gaps?

**Decision**: Core board components (`BoardColumn`, `IssueCard`) are already wrapped in `React.memo()` with internal `useMemo` for expensive derivations. The remaining gaps are in page-level derived data stability and event listener throttling.

**Rationale**: 
- `BoardColumn.tsx`: Wrapped in `memo()`, uses `useDroppable()` from dnd-kit. Card rendering delegates grouping to parent via `getGroups()` callback.
- `IssueCard.tsx`: Wrapped in `memo()`, uses `useMemo` for labels, pipeline/agent parsing, and body snippet (T023).
- `ProjectsPage.tsx`: Already memoizes `heroStats`, `assignedPipelineName`, `rateLimitState`, and `syncStatusLabel` via `useMemo`. Sorting/grouping is delegated to `useBoardControls.transformedData` (not computed in render).
- `ChatPopup.tsx`: Resize mousemove is RAF-gated (T026). Size persistence uses ref-based callbacks.
- `AddAgentModal.tsx`: Modal-based, not popover. No hot positioning listeners found.

The key remaining optimization targets are:
1. Ensuring callback references passed to memoized children are stable (via `useCallback`)
2. Verifying that `getGroups` callback reference is stable across renders
3. Confirming that `useBoardControls` transform output is referentially stable when underlying data hasn't changed

**Alternatives Considered**:
- Board virtualization (react-window/react-virtuoso): Explicitly deferred per spec scope boundaries — only considered if first-pass metrics fail.
- Rewriting components as class components for `shouldComponentUpdate`: Rejected — `React.memo` with hooks is the modern equivalent and already in use.

---

## Research Task 6: Polling Loop Rate Limit Budget and Board Interaction

**Question**: How does the copilot polling loop interact with board data, and can it consume rate limit budget that affects board responsiveness?

**Decision**: The polling loop operates independently of board data queries but shares the same GitHub API rate limit budget. Rate limit budget checking is already implemented with configurable thresholds.

**Rationale**: The polling loop in `polling_loop.py` monitors GitHub issues through workflow states (checking backlog, ready, in-progress, in-review issues). It uses `_check_rate_limit_budget()` and `_pause_if_rate_limited()` to respect rate limits, with configurable thresholds (`RATE_LIMIT_PAUSE_THRESHOLD`, `RATE_LIMIT_SLOW_THRESHOLD`, `RATE_LIMIT_SKIP_EXPENSIVE_THRESHOLD`). It does not directly fetch board data, but it shares the same GitHub token and rate limit pool. The polling loop already pauses when rate limits are low and skips expensive operations when budget is tight.

**Alternatives Considered**:
- Separate rate limit pools for polling vs board: Not possible — GitHub rate limits are per-token, not per-feature.
- Disabling polling during board viewing: Rejected — polling serves a different purpose (workflow automation) and already respects rate limits.

---

## Research Task 7: Repository Resolution Duplication

**Question**: Is there duplicated repository resolution logic between `utils.py` and `workflow.py` that causes unnecessary API calls?

**Decision**: `workflow.py` already uses the shared `resolve_repository()` function from `utils.py`. There is no duplication to fix.

**Rationale**: The `resolve_repository()` function in `utils.py` provides a 4-step fallback chain (in-memory cache → GraphQL → REST → DB workflow config → env defaults) with token-scoped cache keys. `workflow.py` imports and calls this shared function for issue creation. The cache TTL is 300 seconds, preventing repeated resolution calls within a session. No duplicate implementation was found.

**Alternatives Considered**:
- Consolidating into a service class: Rejected — the current utility function pattern is simple and DRY. No need for additional abstraction.

---

## Research Task 8: Spec 022 Implementation Status

**Question**: What is the current implementation status of Spec 022 (API Rate Limit Protection) and which pieces are still missing?

**Decision**: Spec 022 does not exist as a formal spec document in the `solune/specs/` directory. However, the rate-limit protection features referenced in the issue are substantially implemented in the codebase.

**Rationale**: The codebase contains evidence of implemented rate-limit protection:
- **Board cache TTL alignment**: Board endpoint uses 300s TTL, aligned with frontend auto-refresh (✅ implemented)
- **Sub-issue cache invalidation on manual refresh**: Board endpoint clears sub-issue caches when `refresh=True` (✅ implemented)
- **Rate limit detection and stale fallback**: Board, projects, and polling endpoints detect 429/403 and serve stale data (✅ implemented)
- **WebSocket change detection**: The `data_hash_fn` pattern exists in `cached_fetch()` and the board endpoint computes content hashes, but the WebSocket subscription loop does not yet use hash comparison to suppress unchanged refresh messages (⚠️ partially implemented)
- **Inflight request coalescing**: GraphQL deduplication via `_inflight_graphql` bounded dict (✅ implemented)

The primary gap is in the WebSocket subscription loop's lack of hash-based change detection for suppressing refresh messages.

**Alternatives Considered**:
- Treating Spec 022 as fully implemented and skipping verification: Rejected — the WebSocket hash comparison gap is a real issue that affects idle API consumption (SC-001, SC-007).

---

## Research Task 9: Auto-Refresh and WebSocket Interaction

**Question**: How do auto-refresh and WebSocket updates interact? Can they create redundant refresh cycles?

**Decision**: The current implementation already suppresses auto-refresh when WebSocket is connected. This is correct behavior and must be preserved.

**Rationale**: In `useBoardRefresh.ts`, auto-refresh is suppressed when `isWebSocketConnected=true` (per T017). When WebSocket triggers a task update, the `onRefreshTriggered` callback resets the auto-refresh timer, preventing the timer from firing during the WebSocket-driven window. When WebSocket disconnects and polling takes over, auto-refresh resumes on its 5-minute schedule. The `requestBoardReload()` function provides debounced board reload with a 2-second window, and manual refresh always cancels pending debounced reloads.

**Alternatives Considered**:
- Removing auto-refresh entirely when WebSocket is available: Rejected — auto-refresh serves as a safety net for ensuring data freshness even when WebSocket messages might be lost.

---

## Summary of Resolved Unknowns

| Unknown | Resolution | Impact on Plan |
|---------|-----------|---------------|
| Cache architecture maturity | Fully mature; no new infrastructure needed | Simplifies backend work — focus on wiring existing patterns |
| WebSocket hash comparison | Not yet in subscription loop; gap confirmed | Key Phase 2 backend task — wire `compute_data_hash` into send-tasks |
| Sub-issue cache correctness | Already correct (clear on manual, reuse otherwise) | Verify in Phase 1 baseline; no code changes expected |
| Fallback polling scope | Already correct (tasks-only invalidation) | Verify in Phase 1 baseline; add regression test |
| Board component memoization | Already implemented (`React.memo` + `useMemo`) | Phase 3 focus: callback stability and transform output stability |
| Polling loop rate limit | Already budget-aware with configurable thresholds | No changes needed; verify in baseline |
| Repository resolution duplication | No duplication found; shared utility used | No changes needed |
| Spec 022 status | Substantially implemented; WebSocket hash gap remains | Confirm in Phase 1; address hash gap in Phase 2 |
| Auto-refresh/WebSocket interaction | Already correctly suppressed when WS connected | Preserve behavior; add regression test |
