# Research: Performance Review

**Feature**: 001-performance-review  
**Date**: 2026-03-26  
**Status**: Complete — all NEEDS CLARIFICATION resolved

## R-001: Current Backend Cache Implementation State

**Task**: Verify whether board cache TTL alignment, data-hash change detection, and sub-issue cache invalidation are fully implemented or only partially landed.

**Decision**: All three mechanisms are fully implemented in the current codebase.

**Rationale**: Code inspection confirms:
- **Board cache TTL**: `InMemoryCache` in `cache.py` uses a default 300-second TTL. Board data is cached with this TTL in `board.py` via `cached_fetch()`. The frontend auto-refresh interval (5 min) aligns exactly with the backend TTL.
- **Data-hash change detection**: `CacheEntry` stores a `data_hash` field (SHA256 of JSON-serialized data). `cached_fetch()` compares hashes and only refreshes the TTL (not the value) when data is unchanged. The WebSocket subscription in `projects.py` uses hash comparison to suppress unchanged `refresh` messages.
- **Sub-issue cache invalidation**: `get_sub_issues_cache_key(owner, repo, issue_number)` produces keys like `sub_issues:owner/repo#123`. Manual refresh (`refresh=true`) triggers cache deletion for board data; sub-issue cache is cleared on manual refresh but reused during automatic refreshes.

**Alternatives considered**: Re-implementing cache from scratch — rejected because existing `InMemoryCache` with `cached_fetch()` pattern is well-tested and sufficient.

---

## R-002: WebSocket Change Detection Completeness

**Task**: Determine whether WebSocket subscription change detection is fully operational or has remaining gaps.

**Decision**: WebSocket change detection and the polling fallback path are both complete and aligned.

**Rationale**: 
- The WebSocket endpoint in `projects.py` computes data hashes and suppresses `refresh` messages when data is unchanged — this is complete.
- The frontend `useRealTimeSync.ts` correctly handles `refresh`, `task_update`, `task_created`, and `status_changed` messages, invalidating only `['projects', projectId, 'tasks']` — not the expensive board-level query.
- The fallback polling path (`WS_FALLBACK_POLL_MS = 30s`) in `useRealTimeSync.ts` already follows the same selective invalidation pattern by invalidating only `['projects', projectId, 'tasks']` when WebSocket is unavailable.

**Alternatives considered**: Removing polling fallback entirely — rejected because WebSocket connections are unreliable in some environments.

---

## R-003: Polling Loop Rate-Limit Behavior

**Task**: Confirm the polling loop's rate-limit-aware behavior and identify remaining unnecessary GitHub calls.

**Decision**: The polling loop (`polling_loop.py`) is already rate-limit-aware with threshold-based step skipping, but polling cycles can still trigger expensive board data refreshes indirectly.

**Rationale**:
- Polling thresholds are well-defined: pause at 50 remaining, slow at 200, skip expensive at 100.
- Exponential backoff and 15-min cap on rate-limit sleep prevent pathological waits.
- Polling steps check backlog, ready, in-progress, and review issues independently.
- **Remaining concern**: If any polling step triggers a state change that invalidates the board cache, the next board request will force a cold-cache fetch. This is correct behavior but should be validated against the idle-rate-limit goal.

**Alternatives considered**: Disabling polling during idle board viewing — rejected because polling serves purposes beyond board data (agent completion tracking, stalled recovery).

---

## R-004: Frontend Query Invalidation Pattern

**Task**: Research best practices for TanStack React Query selective invalidation and confirm the current invalidation strategy.

**Decision**: The current strategy is mostly correct but can be tightened.

**Rationale**:
- TanStack React Query (v5) supports `queryClient.invalidateQueries({ queryKey: [...] })` for targeted invalidation.
- Current WebSocket handlers invalidate `['projects', projectId, 'tasks']` — correctly scoped.
- Board data lives under `['board', 'data', projectId]` with its own 5-min auto-refresh timer — correctly decoupled.
- `useBoardRefresh` already suppresses auto-refresh when WebSocket is connected.
- **Best practice**: Use `staleTime` to prevent refetches within a window even if invalidation fires. Current `staleTime: 1 min` for board data and `staleTime: 15 min` for projects list are appropriate.
- **Improvement opportunity**: The debounced `requestBoardReload()` in `useBoardRefresh` uses a 2s window. This is adequate but should be validated against rapid WebSocket message bursts.

**Alternatives considered**: Using optimistic updates instead of invalidation — rejected for the first pass because it increases complexity and risk without proven need.

---

## R-005: Frontend Rendering Optimization Patterns

**Task**: Research low-risk React rendering optimization patterns for board components.

**Decision**: Use `React.memo`, `useMemo`, `useCallback`, and event listener throttling as the primary tools.

**Rationale**:
- **React.memo**: Wrap `IssueCard` and `BoardColumn` to skip rerenders when props haven't changed. `BoardColumn` already has some memoization but `IssueCard` likely does not.
- **useMemo**: Memoize derived data (sorting, grouping, aggregation) in `ProjectsPage.tsx` so it recomputes only when the underlying board data reference changes.
- **useCallback**: Stabilize callback props passed to card/column components to avoid breaking `React.memo` shallow comparison.
- **Event listener throttling**: Use `requestAnimationFrame` or a 16ms throttle for hot drag/resize listeners such as those in `ChatPopup.tsx`. `AddAgentPopover.tsx` relies on Radix Popover positioning and does not register custom positioning listeners that need throttling.
- **dnd-kit**: Already handles its own optimization; focus on the event handlers *around* dnd-kit, not inside it.

**Alternatives considered**:
- Board virtualization (react-window/react-virtuoso) — deferred to second-wave per spec constraint FR-017.
- React Compiler auto-memoization — not yet stable enough; manual memo is safer for this pass.

---

## R-006: Repository Resolution Duplication Check

**Task**: Confirm whether `workflow.py` duplicates repository resolution logic from `utils.py`.

**Decision**: No duplication exists. `resolve_repository()` is defined once in `utils.py` and imported in `workflow.py`.

**Rationale**:
- `workflow.py` line 42: `from src.utils import ... resolve_repository ...`
- The function implements a 4-step fallback (in-memory cache → GraphQL → REST → config → default) with token-scoped caching.
- All callers use the same import. No parallel implementation exists.

**Alternatives considered**: N/A — the concern was unfounded.

---

## R-007: Adaptive Polling in useProjectBoard

**Task**: Understand the adaptive polling mechanism and its interaction with other refresh paths.

**Decision**: Adaptive polling is well-implemented but adds a third refresh dimension alongside WebSocket and auto-refresh. The refresh policy contract must explicitly define the interaction.

**Rationale**:
- `useProjectBoard` uses `useAdaptivePolling()` to dynamically adjust `refetchInterval` based on detected change frequency.
- Board data query has `staleTime: 1 min` and a dynamic `refetchInterval`.
- This creates three concurrent refresh sources: (1) adaptive polling via `refetchInterval`, (2) auto-refresh timer via `useBoardRefresh`, (3) WebSocket invalidation via `useRealTimeSync`.
- **Key finding**: `useBoardRefresh` already suppresses its auto-refresh timer when WebSocket is connected. The adaptive polling in `useProjectBoard` is the remaining source of potential redundant fetches.
- **Recommendation**: The refresh policy contract should specify that adaptive polling defers to WebSocket when connected, similar to how auto-refresh already does.

**Alternatives considered**: Removing adaptive polling entirely — rejected because it provides value when WebSocket is disconnected and auto-refresh is the only other mechanism.

---

## R-008: Existing Test Coverage Assessment

**Task**: Assess existing test coverage for the areas being optimized.

**Decision**: Existing tests provide adequate regression coverage for backend cache and frontend refresh behavior. Gaps exist in change-detection-specific assertions and idle-refresh-prevention tests.

**Rationale**:
- **test_cache.py**: Covers CacheEntry lifecycle, TTL, stale retrieval, hash comparison, and `cached_fetch()` patterns. Strong baseline.
- **test_api_board.py**: Covers board list/get endpoints, error handling, rate limits, cache invalidation on status update. Needs: assertion that unchanged data doesn't trigger upstream API call.
- **test_copilot_polling.py**: Covers polling steps, rate-limit handling, stalled recovery. Needs: assertion that polling doesn't trigger board cache invalidation unnecessarily.
- **useRealTimeSync.test.tsx**: Covers WebSocket lifecycle, message types, reconnection, query invalidation, and polling fallback selective invalidation. Strong baseline.
- **useBoardRefresh.test.tsx**: Covers manual refresh, auto-refresh timer, visibility API, debounce, rate limit, WebSocket suppression. Strong baseline.

**Alternatives considered**: Building a new test framework — rejected per spec assumption (extend existing files only).
