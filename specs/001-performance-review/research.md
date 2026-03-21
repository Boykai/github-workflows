# Research: Performance Review

**Feature Branch**: `001-performance-review`  
**Date**: 2026-03-21  
**Status**: Complete

## Research Summary

All technical unknowns from the Technical Context section have been resolved through codebase exploration. No external research or third-party tooling decisions were required because the feature targets optimization of existing code rather than introducing new capabilities.

---

## Research Task 1: Current Backend Cache and Change-Detection State

**Context**: Verify whether WebSocket change detection, board cache TTL alignment, and sub-issue cache invalidation are fully implemented or only partially landed.

**Decision**: The backend has all three mechanisms fully implemented.

**Rationale**:
- **WebSocket change detection** (FR-004): `projects.py` computes `compute_data_hash()` on each periodic task fetch and compares against the stored `CacheEntry.data_hash`. When hashes match, it calls `cache.refresh_ttl()` without sending a refresh message downstream. This is fully implemented and tested.
- **Board cache TTL alignment** (FR-009): `board.py` sets board data cache with `ttl_seconds=300` (5 minutes), matching the frontend `AUTO_REFRESH_INTERVAL_MS` of 5 minutes. Alignment is correct.
- **Sub-issue cache invalidation** (FR-008): `board.py` proactively iterates all board items on manual refresh (`refresh=True`) and deletes their sub-issue cache entries via `cache.delete(get_sub_issues_cache_key(...))`. Sub-issue cache uses a 600-second TTL, double the board cache TTL. This is fully implemented.

**Alternatives Considered**: N/A — these are existing implementations to verify, not choices to make.

---

## Research Task 2: WebSocket Stale-Revalidation Behavior

**Context**: The WebSocket `send_tasks()` loop uses a stale-revalidation counter that forces a fresh GitHub API fetch after 10 consecutive stale cache returns (~50 minutes with 30-second intervals). Determine whether this is a performance concern.

**Decision**: The stale-revalidation forced fetch is acceptable and does not need modification in the first pass.

**Rationale**:
- At 30-second intervals, 10 stale cycles = 5 minutes, not 50 minutes. After the cache TTL expires (300s), the next fetch will either get fresh data (resetting the counter) or confirm unchanged data via hash comparison.
- The forced fetch at 10 cycles is a safety net against stale-data loops where the cache expires but the revalidation keeps serving stale results without ever checking GitHub.
- The hash comparison at the fetch boundary still prevents downstream notification spam for unchanged data.
- Removing this would risk never detecting upstream changes if the cache layer has a bug.

**Alternatives Considered**:
- Removing the forced fetch entirely: Rejected because it removes the safety net against infinite stale loops.
- Increasing the threshold from 10 to 20: Possible but low-value; the forced fetch is already cheap if data is unchanged (single GraphQL query, hash compare, no downstream action).

---

## Research Task 3: Frontend Refresh Path Decoupling State

**Context**: Determine whether the frontend currently invalidates board data queries during WebSocket fallback polling, and whether task-level updates are properly decoupled from board data refreshes.

**Decision**: The frontend refresh path is already well-decoupled. Minimal changes may be needed.

**Rationale**:
- `useRealTimeSync.ts` invalidates only `['projects', projectId, 'tasks']` on WebSocket messages (`task_update`, `task_created`, `status_changed`, `refresh`). It does NOT invalidate `['board', 'data', projectId]`.
- The fallback polling path (`WS_FALLBACK_POLL_MS = 30000`) also only invalidates the tasks query, not board data.
- `useBoardRefresh.ts` manages board data refresh independently via a 5-minute auto-refresh timer that is suppressed when WebSocket is connected.
- `useProjectBoard.ts` has no `refetchInterval` — it relies entirely on `useRealTimeSync` and `useBoardRefresh` for refresh orchestration.
- The `requestBoardReload()` function in `useBoardRefresh` includes a 2-second debounce to prevent concurrent reload triggers.

**Existing Concerns**:
- The `onRefreshTriggered` callback in `useRealTimeSync` resets the board auto-refresh timer when WebSocket messages arrive. This is correct behavior (WebSocket activity proves connectivity, so defer auto-refresh).
- Manual refresh (`refresh=true`) correctly cancels in-flight queries and bypasses cache.

**Alternatives Considered**: N/A — the current architecture is well-designed. The plan should verify it via tests rather than restructure it.

---

## Research Task 4: Frontend Render Memoization State

**Context**: Assess current memoization coverage for board components and identify specific gaps.

**Decision**: Core board components are already memoized. Optimization should focus on verifying effectiveness and addressing specific gaps.

**Rationale**:
- `BoardColumn` is wrapped in `React.memo()` — prevents re-renders when parent state changes but column data is unchanged.
- `IssueCard` is wrapped in `React.memo()` — prevents re-renders for unrelated card changes.
- `SubIssueRow` is wrapped in `React.memo()`.
- `ProjectsPage` uses `useMemo` for derived state: `heroStats`, `rateLimitState`, `syncStatusLabel`, `syncStatusToneClass`, `assignedPipelineName`.
- `IssueCard` internally memoizes: labels, pipeline config, body snippet, assigned slugs.
- `ChatPopup` uses `requestAnimationFrame` gating for resize drag.

**Gaps Identified**:
- No virtualization for board columns (all cards rendered) — explicitly out of scope for first pass.
- Sub-issue expansion renders all sub-issues without virtualization — acceptable for typical counts.
- `useBoardControls` hook transforms board data (filter/sort/group) — verify this is memoized.
- Event listener callbacks (drag handlers, popover positioning) may recreate on each render if not stabilized with `useCallback`.

**Alternatives Considered**:
- Introducing `react-window` or `@tanstack/virtual` for board virtualization: Explicitly deferred to Phase 4 (optional second-wave) per spec assumptions.
- Aggressive `useCallback` wrapping: Only where profiling confirms benefit, per spec FR-015 ("where re-render profiling confirms a measurable benefit").

---

## Research Task 5: Backend Polling and Rate-Limit Budget Interaction

**Context**: Understand how the polling loop interacts with rate limits and whether it can trigger unnecessary board refreshes.

**Decision**: The polling loop is well-instrumented for rate limits but operates independently from the board endpoint. No cross-contamination risk.

**Rationale**:
- The polling loop in `polling_loop.py` uses three rate-limit thresholds: pause at 50, slow at 200, skip expensive at 100.
- It filters out sub-issues before processing (`is_sub_issue()` filter), avoiding redundant API calls for agent-created child issues.
- The polling loop does NOT call the board endpoint; it directly queries project items via `get_project_items()` and processes them through pipeline steps (PR status, agent outputs, stalled recovery).
- Rate-limit budget is shared across all API calls via `_request_rate_limit` contextvar and `_last_rate_limit` instance fallback.
- Dynamic interval doubling at budget ≤ 200 reduces polling frequency when quota is constrained.

**Concern**: The polling loop fetches all project items each cycle via `get_project_items()`. If the board endpoint also fetches project items within the same rate-limit window, both paths compete for the same GitHub API quota.

**Mitigation**: Both paths use the same cache layer (`cache.get/set` with `get_project_items_cache_key`), so warm cache from one path benefits the other.

**Alternatives Considered**: N/A — the current architecture is sound. The plan should verify cache sharing and measure actual quota consumption.

---

## Research Task 6: Repository Resolution Duplication

**Context**: Determine whether `workflow.py` duplicates repository resolution logic from `utils.py` and whether this adds inconsistency or avoidable API work.

**Decision**: There is no duplication. All callers use the shared `resolve_repository()` function from `utils.py`.

**Rationale**:
- `workflow.py` calls `resolve_repository(session.access_token, project_id)` in 7 locations. Each call goes through the same 3-step fallback (cache → project items → workflow config → default) defined in `utils.py`.
- The 300-second per-token-hash cache ensures that repeated calls within a 5-minute window skip API costs.
- Other callers (agents, chat, chores, tools) all use the same function.
- No inline repository resolution logic exists in `workflow.py` — all paths are centralized.

**Alternatives Considered**:
- Middleware-based resolution (resolve once per request): Possible future optimization but not needed now — cache hit rate makes individual calls effectively free after the first one.

---

## Research Task 7: Test Coverage Gaps

**Context**: Identify which spec requirements have existing test coverage and which need new tests.

**Decision**: Good existing coverage for backend cache and polling. Frontend hooks are well-tested. Specific gaps exist for hash-based change detection in WebSocket flows and event listener throttling.

**Rationale**:

### Existing Coverage

| Area | Test File | Coverage |
|------|-----------|----------|
| Cache TTL and operations | `test_cache.py` | ✅ Get/set, TTL, expiration, hash storage, stale fallback |
| Board cache bypass on refresh | `test_api_board.py` | ✅ Refresh parameter, cache reuse |
| Polling rate-limit thresholds | `test_copilot_polling.py` | ✅ Pause, slow, skip expensive, stale clearing |
| WebSocket connection lifecycle | `useRealTimeSync.test.tsx` | ✅ Connect, disconnect, fallback, message handling, debounce |
| Board refresh timer and dedup | `useBoardRefresh.test.tsx` | ✅ Timer suppression, manual priority, debounce, visibility |

### Gaps (FR-021 Requirements)

| Missing Test | Requirement | Test Target |
|-------------|-------------|-------------|
| WebSocket hash-based refresh suppression | FR-004, FR-005 | `test_api_projects.py` or `test_cache.py` |
| Fallback polling doesn't trigger board refresh | FR-006, FR-013 | `useRealTimeSync.test.tsx` |
| Sub-issue cache preservation during auto-refresh | FR-007 | `test_api_board.py` |
| Event listener throttling behavior | FR-017, SC-009 | New component tests |
| Derived data memoization effectiveness | FR-018 | Profile-based verification, not unit test |

**Alternatives Considered**: N/A — gap analysis is descriptive, not prescriptive.
