# Research: Performance Review

**Feature**: 001-performance-review
**Date**: 2026-03-11
**Status**: Complete — all unknowns resolved

## Research Tasks

### RT-001: Current Backend Cache and Refresh State

**Context**: Verify what cache TTLs, refresh mechanics, and change-detection logic are already implemented in the backend before proposing changes.

**Findings**:

- **Board cache TTL** is set to 300 seconds (5 minutes) via `config.cache_ttl_seconds` in `backend/src/services/cache.py`. This is already aligned with the auto-refresh interval on the frontend.
- **Metadata cache TTL** (labels, branches, milestones, collaborators) is 3600 seconds (1 hour) via `config.metadata_cache_ttl_seconds`.
- **Sub-issue cache** is populated during board data fetches in `backend/src/services/github_projects/service.py` and cleared on manual refresh (`refresh=true` parameter bypasses cache).
- **Stale cache fallback** exists: when GitHub API is rate-limited or unavailable, `cache.get_stale()` returns expired entries to avoid service disruption.
- **Rate-limit detection** catches `PrimaryRateLimitExceeded`, HTTP 429, and 403 with `X-RateLimit-Remaining: 0`.

**Decision**: The 300-second TTL and sub-issue cache invalidation on manual refresh are implemented. Focus remaining work on WebSocket change detection and suppressing unchanged-state refreshes in the subscription flow.

**Alternatives Considered**: Reducing the TTL below 300s was considered but rejected because a shorter TTL increases GitHub API pressure without proportional user-facing benefit; the 5-minute TTL is already conservative.

---

### RT-002: WebSocket Subscription and Change Detection

**Context**: Determine whether WebSocket subscriptions in `projects.py` already implement change detection (skip refresh when data is unchanged) or still broadcast unconditional refreshes.

**Findings**:

- The WebSocket endpoint at `/api/v1/projects/{projectId}/subscribe` sends `initial_data` on connection and `refresh` / `task_update` / `status_changed` / `task_created` / `blocking_queue_updated` messages during the subscription.
- The `initial_data` message is debounced with a 2-second delay on the frontend (`useRealTimeSync.ts`) to prevent connection storms.
- Task-level messages (`task_update`, `task_created`, `status_changed`) invalidate the `['projects', projectId, 'tasks']` query only — they do not force a full board reload.
- The `refresh` message type triggers a broader invalidation; this is the path most likely to cause unnecessary full board reloads when the board data itself has not changed.

**Decision**: The WebSocket subscription already provides granular message types and the frontend already distinguishes task-level updates from board-level refreshes. The gap is in the `refresh` message type: the backend should suppress `refresh` broadcasts when the underlying board data hash/version has not actually changed, and the frontend `refresh` handler should distinguish board-structure changes from data-unchanged pings.

**Alternatives Considered**: Adding a versioned ETag or data hash to board responses was considered as a heavier approach; the simpler path is to compare the board data checksum server-side before broadcasting a `refresh` message.

---

### RT-003: Fallback Polling Behavior

**Context**: Determine whether fallback polling (when WebSocket is unavailable) can trigger expensive board refreshes.

**Findings**:

- `useRealTimeSync.ts` falls back to polling at 30-second intervals (`WS_FALLBACK_POLL_MS`) when the WebSocket connection fails.
- In fallback mode, the poll invalidates the tasks query (`['projects', projectId, 'tasks']`), which is lightweight.
- The `useBoardRefresh.ts` auto-refresh runs independently at 5-minute intervals and does not distinguish between WebSocket-connected and fallback-polling modes.
- There is no current mechanism where a fallback poll directly forces a full board data refetch. However, if the auto-refresh timer fires concurrently with a fallback poll, the combined invalidation volume could be higher than necessary.

**Decision**: Fallback polling is already lightweight (tasks-only invalidation). The auto-refresh timer should be paused or extended when fallback polling is active, so both paths don't fire simultaneously. No changes to the 30-second fallback interval itself.

**Alternatives Considered**: Disabling auto-refresh entirely during fallback polling was considered but rejected because it could leave board data stale indefinitely if the WebSocket never reconnects.

---

### RT-004: Frontend Refresh Contract Coherence

**Context**: Determine whether the four refresh sources (WebSocket, fallback polling, auto-refresh, manual refresh) follow one coherent policy.

**Findings**:

- **WebSocket messages**: Task-level updates invalidate tasks query only. Board-level `refresh` messages may trigger broader invalidation.
- **Fallback polling**: Invalidates tasks query at 30-second intervals.
- **Auto-refresh**: Triggers a full board data refetch every 5 minutes via `useBoardRefresh.ts`, gated by page visibility.
- **Manual refresh**: Calls `refresh=true` on the backend, bypassing all caches for a full fresh load.

The policies are already partially separated: task freshness comes from WebSocket/polling, and full board freshness comes from auto-refresh. The gap is that the `refresh` WebSocket message could trigger a board-level reload that overlaps with auto-refresh, and there's no explicit deduplication between auto-refresh firing and a WebSocket `refresh` arriving around the same time.

**Decision**: Formalize the refresh contract:

1. **Lightweight updates** (task-level): WebSocket `task_*` messages and fallback polling → invalidate tasks query only.
2. **Full board reload**: Auto-refresh timer, manual refresh, or WebSocket `refresh` when board-structure change is confirmed → refetch board data.
3. **Deduplication**: Debounce board reloads so that concurrent auto-refresh + WebSocket `refresh` within a short window result in a single refetch.

**Alternatives Considered**: Unifying all refresh paths into a single queue was considered but rejected as over-engineering for this first pass; debouncing at the board-refetch level is simpler and sufficient.

---

### RT-005: Frontend Rendering State and Memoization

**Context**: Assess current memoization in board components and identify remaining render hot spots.

**Findings**:

- `BoardColumn.tsx` is wrapped in `React.memo` — prevents re-renders when other columns update.
- `IssueCard.tsx` is wrapped in `React.memo` — prevents re-renders for unaffected cards.
- `ProjectsPage.tsx` uses `useMemo` for `blockingIssueNumbers`, `assignedPipeline`, `assignedStageMap`, and other derived state.
- Potential remaining hot spots:
  - `ChatPopup.tsx` drag listener fires on every mouse move during drag — throttling would reduce handler frequency.
  - `AddAgentPopover.tsx` positioning listener fires frequently during repositioning — throttling is appropriate.
  - Inline function creation in render paths (e.g., `SubIssueRow`, `SubIssueStateIcon` inside `IssueCard.tsx`) — these are stateless helpers and unlikely to be a significant cost, but can be extracted if profiling confirms.
  - Callback props passed to memoized children that are recreated on each parent render may defeat memo — `useCallback` stabilization is a low-risk improvement.

**Decision**: The major board components are already memoized. Focus remaining render optimization on: (a) throttling hot event listeners in `ChatPopup.tsx` and `AddAgentPopover.tsx`, (b) stabilizing callback props with `useCallback` where it preserves existing memos, and (c) profiling to confirm the actual hot spots match expectations before applying further changes.

**Alternatives Considered**: Virtualization of board columns/cards was considered but explicitly deferred per spec scope boundaries. Adding `React.Profiler` instrumentation was considered for baseline capture and may be used during verification but is not a shipped code change.

---

### RT-006: Repository Resolution Duplication

**Context**: Determine whether `workflow.py` duplicates the canonical repo-resolution logic in `utils.py`.

**Findings**:

- `backend/src/utils.py` contains `cached_fetch()` and shared repository-resolution helpers that are the canonical path.
- `backend/src/api/workflow.py` contains a separate repository-resolution path that may not reuse the shared helpers.
- FR-007 requires that any repo-resolution or polling logic touched by this first pass reuse the canonical shared logic.

**Decision**: If any backend change in this first pass touches `workflow.py` or its repo-resolution path, consolidate to use `utils.py` shared helpers. If `workflow.py` is not in the change path, defer consolidation to a separate cleanup pass to minimize scope.

**Alternatives Considered**: Proactively consolidating all duplicate resolution paths was considered but rejected as out of scope for a performance-focused first pass unless the duplicate path directly contributes to measured waste.

---

### RT-007: Existing Test Coverage for Regression Guardrails

**Context**: Assess whether existing tests can serve as before/after regression guardrails.

**Findings**:

- `backend/tests/unit/test_cache.py` — covers cache TTL behavior and stale fallback. Suitable as-is for regression.
- `backend/tests/unit/test_api_board.py` — covers board endpoint behavior and cache semantics. Suitable as-is.
- `backend/tests/unit/test_copilot_polling.py` — covers polling behavior and rate-limit-aware logic. Suitable as-is.
- `frontend/src/hooks/useRealTimeSync.test.tsx` — covers WebSocket connection, fallback polling, and query invalidation. Suitable as-is; may need extension for deduplication behavior.
- `frontend/src/hooks/useBoardRefresh.test.tsx` — covers auto-refresh timer, manual refresh, and deduplication. Suitable as-is; may need extension for fallback-mode coordination.

**Decision**: Existing tests are reliable enough to serve as regression guardrails. Extensions will be scoped to new behaviors added by this pass: WebSocket `refresh` change-detection suppression, auto-refresh/fallback coordination, and board-reload debouncing.

**Alternatives Considered**: Creating an entirely new test suite was considered but rejected as unnecessary when existing tests already cover the core paths and only incremental extensions are needed.

## Summary of Decisions

| # | Decision | Rationale |
|---|----------|-----------|
| 1 | Keep 300s board cache TTL | Already aligned with auto-refresh; reducing it increases API pressure without proportional benefit. |
| 2 | Add server-side change detection for WebSocket `refresh` | Prevents unchanged-state board refreshes from consuming request budget and triggering unnecessary frontend reloads. |
| 3 | Pause/extend auto-refresh during fallback polling | Prevents concurrent auto-refresh + fallback poll from doubling invalidation volume. |
| 4 | Formalize three-tier refresh contract | Lightweight task updates, full board reloads, and manual refresh each have clear rules; debounce prevents overlap. |
| 5 | Throttle hot event listeners | Low-risk responsiveness improvement for drag and positioning handlers without changing visible behavior. |
| 6 | Stabilize callback props with useCallback | Preserves existing `React.memo` effectiveness on `BoardColumn` and `IssueCard`. |
| 7 | Defer virtualization and service decomposition | Explicitly out of scope per spec; only revisit if first-pass metrics fail targets. |
| 8 | Extend existing tests incrementally | Existing coverage is reliable; only add tests for new behaviors introduced by this pass. |
| 9 | Consolidate repo-resolution only if touched | DRY improvement is in scope only when the duplicate path is in the change path for this pass. |
