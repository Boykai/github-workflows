# Research: Performance Review

**Feature**: 032-performance-review
**Date**: 2026-03-09
**Purpose**: Resolve all technical unknowns and document research decisions before design

## Research Area 1: Current Spec 022 Implementation State

**Question**: Which Spec 022 (API Rate Limit Protection) items are fully implemented vs partially landed?

**Findings**:

1. **WebSocket change detection (FR-001, FR-002)**: The `useRealTimeSync` hook processes WebSocket messages (`task_update`, `task_created`, `status_changed`, `refresh`, `initial_data`) and debounces `initial_data` to max once per 2-second cycle. The backend projects API sends subscription messages. However, the spec calls for hash-based change detection on the server side to prevent sending refresh messages when data hasn't changed — this needs verification in the current `projects.py` implementation.

2. **Board cache TTL alignment (FR-007)**: The board data cache TTL is set to 300 seconds in the backend, which aligns with the frontend's 5-minute auto-refresh interval in `useBoardRefresh`. **Status: Implemented.**

3. **Sub-issue cache (FR-005, FR-006)**: `get_sub_issues()` in `service.py` checks cache first (key: `sub_issues:{owner}/{repo}#{issue_number}`) with a 600-second TTL. On cache miss, it makes a REST call and caches the result. **Status: Implemented.**

4. **Sub-issue cache invalidation on manual refresh (FR-008, FR-009)**: The board endpoint accepts a `refresh=true` parameter that bypasses caches. Manual refresh in `useBoardRefresh` calls `boardApi.getBoardData(projectId, true)`. **Status: Implemented for manual refresh; automatic refresh uses cached sub-issues.**

5. **Frontend query decoupling (FR-003, FR-004)**: `useRealTimeSync` invalidates queries on WebSocket messages. The current implementation invalidates the tasks query. Manual refresh invalidates board data. **Status: Partially implemented — the fallback polling path may still invalidate board data.**

**Decision**: Spec 022 core cache and TTL items are implemented. Remaining gaps are: (a) server-side hash-based change detection for WebSocket subscriptions, (b) fallback polling still invalidating board data query, and (c) ensuring reconciliation path also benefits from sub-issue cache.

---

## Research Area 2: Backend Idle API Consumption Patterns

**Question**: What causes excessive API calls when a board is idle?

**Findings**:

1. **Polling loop**: The copilot polling loop (`polling_loop.py`) runs a 5-step cycle with adaptive backoff. It already has rate-limit-aware behavior (pause, skip-expensive, slow-down thresholds) and activity-based adaptive polling (exponential backoff on consecutive idle polls, max 300s interval). This is not the primary source of board-related idle API consumption.

2. **WebSocket subscription refresh**: The projects API WebSocket subscription flow sends messages to connected clients. If the server sends `refresh` or `initial_data` messages without change detection, each message triggers frontend query invalidation, which triggers a board data fetch, which triggers N sub-issue API calls. This cascade is the primary idle consumption source.

3. **Board data endpoint cost**: Each board data request fetches project items via GraphQL, then makes per-issue REST calls for sub-issues (unless cached). With warm sub-issue caches, the cost drops from ~23 calls to ~3 calls (GraphQL pagination + metadata). The reconciliation path (`_reconcile_board_items`) also fetches sub-issues for reconciled items.

4. **Fallback polling**: When WebSocket is unavailable, `useRealTimeSync` falls back to interval-based polling which invalidates queries on each tick, potentially triggering full board refreshes.

**Decision**: The primary optimization targets are: (1) server-side change detection to prevent unnecessary WebSocket messages, (2) ensuring fallback polling only triggers lightweight checks, and (3) maximizing sub-issue cache hit rate during automatic refreshes.

---

## Research Area 3: Frontend Refresh Architecture Coherence

**Question**: How do the four refresh channels (WebSocket, fallback polling, auto-refresh, manual refresh) interact, and where do they conflict?

**Findings**:

1. **WebSocket path** (`useRealTimeSync`): Invalidates tasks query on message receipt. Debounces `initial_data` to max once per 2s. Does not directly trigger board data refresh. **Well-behaved.**

2. **Fallback polling** (`useRealTimeSync`): Fires on interval when WebSocket is unavailable. Currently applies the same invalidation logic as WebSocket messages. If it invalidates the board data query, it triggers expensive refreshes on every poll tick. **Needs review — should match WebSocket behavior and only invalidate tasks.**

3. **Auto-refresh** (`useBoardRefresh`): 5-minute interval using `invalidateQueries()` (not force-refresh). Pauses when tab is hidden, resumes on visibility with immediate refresh if stale. Uses TanStack Query cache — serves cached data if still within `staleTime`. **Well-behaved.**

4. **Manual refresh** (`useBoardRefresh`): Calls `boardApi.getBoardData(projectId, true)` with `refresh=true` to bypass backend cache. Has deduplication — concurrent calls share the same promise. Cancels in-progress auto-refresh. **Well-behaved.**

5. **Conflict zone**: If fallback polling invalidates both tasks AND board data, and the auto-refresh timer fires concurrently, two board data refreshes could execute simultaneously. The deduplication in `useBoardRefresh` only covers manual refresh calls, not query invalidation from other sources.

**Decision**: The refresh policy should be: (a) WebSocket and fallback polling only invalidate the tasks query, never board data; (b) auto-refresh uses TanStack Query's stale-while-revalidate with backend cache; (c) manual refresh is the only path that bypasses all caches; (d) add query-level deduplication via TanStack Query's built-in request dedup (already present via query keys).

---

## Research Area 4: Frontend Rendering Hot Spots

**Question**: Where are the highest-impact rendering optimizations in the board and chat surfaces?

**Findings**:

1. **BoardColumn.tsx**: Already wrapped in `React.memo()`. Renders either grouped or flat list of `IssueCard` components. The column itself won't rerender unless its props change. **Current: Optimized at component boundary.**

2. **IssueCard.tsx**: Already wrapped in `React.memo()`. Has local state for sub-issue expansion. Contains validation logic (URL, color sanitization) that runs on every render but is lightweight. **Current: Optimized at component boundary.** Potential improvement: ensure callback props (onClick, etc.) are stable references.

3. **ProjectsPage.tsx**: Uses `useMemo` for `blockingIssueNumbers` (Set creation), `assignedPipeline` (find), and `assignedStageMap` (Map creation). Uses `useCallback` for click handlers. Rate limit state cascades through multiple sources. **Current: Reasonably optimized.** Potential improvement: memoize the `getGroups` function passed to columns if it creates new references on each render.

4. **ChatPopup.tsx**: Drag resize already uses `requestAnimationFrame` gating to prevent per-pixel handler execution. Uses ref-based state for non-render tracking. **Current: Already optimized.**

5. **AddAgentPopover.tsx**: Scroll and resize listeners fire `updatePosition()` on every event when the popover is open. `updatePosition` reads DOM layout (getBoundingClientRect) which forces layout calculation. **Optimization opportunity**: Throttle scroll/resize handlers or use RAF gating.

**Decision**: The highest-impact frontend rendering optimizations are: (1) stabilize callback props passed to memoized board components to prevent unnecessary child rerenders, (2) memoize the `getGroups` function in ProjectsPage if it creates new closures per render, (3) throttle AddAgentPopover scroll/resize listeners with RAF gating. BoardColumn and IssueCard are already memoized — the focus should be on ensuring their parent provides stable props.

---

## Research Area 5: Backend Repository Resolution Deduplication

**Question**: Is there duplicated repository resolution logic, and can it be consolidated?

**Findings**:

1. **Shared utility** (`utils.py`): `resolve_repository(access_token, project_id)` implements a 3-step fallback: (a) project items via GraphQL, (b) workflow configuration, (c) default repository from settings. This is the canonical path.

2. **Workflow endpoint** (`workflow.py`): Uses `resolve_repository()` from utils — already delegates to the shared function. Also has duplicate request detection via SHA256 hashing with a 5-minute bounded dict.

3. **Service layer** (`service.py`): Board data fetching extracts repository info from project items inline during GraphQL response parsing. This is not a separate resolution call — it's part of the board data response parsing.

**Decision**: Repository resolution is already consolidated in `utils.py` and used by `workflow.py`. The service layer extracts repository info from GraphQL responses inline (not a separate call). No further deduplication is needed for FR-007 — the existing shared path is already in use.

---

## Research Area 6: Existing Test Coverage and Extension Points

**Question**: What test coverage exists and where should it be extended for regression guardrails?

**Findings**:

1. **Backend cache tests** (`test_cache.py`): Covers CacheEntry TTL, InMemoryCache get/set/delete, expiration handling, concurrent removal tolerance. **Extension point**: Add tests for sub-issue cache key generation and warm-cache board refresh call count.

2. **Backend board tests** (`test_api_board.py`): Covers GET projects, GET board data, cache bypass on refresh=true, error handling, rate limit errors. **Extension point**: Add tests verifying that automatic refresh serves cached sub-issues.

3. **Backend polling tests** (`test_copilot_polling.py`): Extensive coverage (7,800+ lines) of polling loop, rate-limit-aware behavior, activity detection, adaptive backoff. **Extension point**: Minimal — already well covered.

4. **Frontend sync tests** (`useRealTimeSync.test.tsx`): Covers WebSocket connection, fallback to polling, message handling, cleanup. **Extension point**: Add test verifying that fallback polling does NOT invalidate board data query.

5. **Frontend refresh tests** (`useBoardRefresh.test.tsx`): Covers manual refresh with cache bypass, deduplication, auto-refresh timer, page visibility API, rate limit tracking. **Extension point**: Add test verifying that auto-refresh does not bypass backend cache.

**Decision**: Existing test suites provide solid regression guardrails. Extensions should be targeted: (1) backend — warm-cache board refresh behavior, (2) frontend — fallback polling invalidation scope, (3) frontend — refresh channel isolation. No fundamental test restructuring needed.

---

## Research Area 7: Spec 027 Prior Performance Review

**Question**: What was covered in the prior performance review (Spec 027) and how does Spec 032 differ?

**Findings**:

Spec 027 exists with a full artifact set (spec.md, plan.md, tasks.md, data-model.md, research.md, quickstart.md, contracts/). Spec 032 builds on the same performance domain but focuses specifically on:

1. **Baseline-first approach**: Spec 032 mandates quantitative baselines before any code changes (FR-001, FR-002).
2. **Spec 022 integration**: Spec 032 explicitly references and extends Spec 022's cache and refresh work.
3. **Phased delivery**: Spec 032 defines clear phase gates (baseline → backend fixes → frontend fixes → render optimization → verification).
4. **Deferred scope**: Spec 032 explicitly excludes virtualization and service decomposition unless measurements require them.

**Decision**: Spec 032 is a focused continuation of prior performance work with stricter measurement requirements and phase discipline. It does not duplicate Spec 027 — it targets remaining gaps identified since that work was planned.

---

## Consolidated Decisions Summary

| Area | Decision | Rationale | Alternatives Considered |
|------|----------|-----------|------------------------|
| Spec 022 state | Core cache/TTL items implemented; gaps in server-side change detection and fallback polling scope | Avoids redoing completed work; focuses effort on remaining value | Full reimplementation (rejected: wasteful) |
| Idle API reduction | Server-side hash change detection + fallback polling scope fix | Addresses root cause of cascade; 022 target of <100 calls/hour | Client-side dedup only (rejected: doesn't prevent server-side waste) |
| Refresh policy | Single coherent policy: WS/polling → tasks only; auto-refresh → cached; manual → bypass all | Prevents channel conflicts; matches existing architecture | Per-channel independent logic (rejected: conflict-prone) |
| Render optimization | Stabilize props, memoize getGroups, throttle popover listeners | Low-risk using existing patterns (React.memo, useMemo, RAF) | Virtualization (deferred: high-risk for first pass) |
| Repo resolution | No changes needed — already consolidated in utils.py | Shared function already in use by workflow.py | Inline resolution (current service.py pattern is fine for GraphQL response parsing) |
| Test extensions | Targeted additions to existing suites | Regression guardrails without restructuring | Full rewrite (rejected: scope creep) |
