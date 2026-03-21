# Research: Performance Review

**Feature Branch**: `056-performance-review`
**Date**: 2026-03-21
**Status**: Complete

## Research Tasks

### R1: Current Backend Cache and Change-Detection State

**Context**: The spec references existing cache TTL alignment and sub-issue cache invalidation. Need to confirm what is already implemented vs. what remains.

**Decision**: The backend cache infrastructure is mature and well-implemented.

**Findings**:
- `InMemoryCache` in `cache.py` supports TTL (default 300s), stale fallback, data-hash tracking, and TTL refresh without value replacement.
- `compute_data_hash()` computes SHA-256 of sorted JSON for change detection — used in both `board.py` and `projects.py` WebSocket flows.
- Board data cache (`board_data:{project_id}`) uses 300s TTL aligned with the frontend 5-minute auto-refresh interval.
- Sub-issue cache (`sub_issues:{owner}/{repo}#{issue_number}`) is invalidated on manual refresh in `board.py` (lines 390–399).
- WebSocket subscription in `projects.py` uses `compute_data_hash()` to suppress unchanged refresh messages (only sends if hash differs).
- Stale fallback pattern (`cache.get_stale()`) is implemented for both board data and project items.
- `cached_fetch()` helper in `cache.py` provides a cache-aside pattern with forced refresh and stale fallback support.

**Alternatives Considered**: N/A — this was a confirmation audit, not a design decision.

---

### R2: WebSocket Subscription Refresh Behavior

**Context**: Need to understand whether idle board viewing still emits repeated refreshes when data is unchanged.

**Decision**: WebSocket subscription already implements change detection, but has a stale-revalidation cycle that may cause unnecessary upstream calls.

**Findings**:
- `websocket_subscribe()` in `projects.py` runs a periodic refresh every 30 seconds.
- Each cycle calls `get_project_items()` which checks cache first (300s TTL).
- Change detection compares data hashes before sending refresh messages to clients.
- A stale-revalidation counter (`stale_revalidation_count`) forces a fresh API call after 10 consecutive stale-served cycles — this is an intentional safety mechanism but may cause periodic unnecessary calls.
- On initial WebSocket connection, `force_refresh=True` bypasses cache — this is correct for initial sync.
- The subscription validates project access by calling `list_user_projects()` before each refresh — this is potentially redundant when the session is already authenticated.

**Rationale**: The 10-cycle stale revalidation is a reasonable safety mechanism. The redundant `list_user_projects()` call per refresh cycle is the primary optimization target.

**Alternatives Considered**:
- Remove stale revalidation entirely → Rejected: could serve indefinitely stale data if cache TTL is misaligned.
- Increase stale revalidation threshold → Possible second-pass optimization if first-pass metrics still show excess calls.

---

### R3: Polling Loop and Rate-Limit-Aware Scheduling

**Context**: Need to understand whether the polling hot path triggers expensive board refreshes unintentionally.

**Decision**: The polling loop is well-instrumented with rate-limit awareness but has potential for unnecessary work in sub-issue resolution.

**Findings**:
- `polling_loop.py` implements adaptive polling with three rate-limit thresholds: PAUSE (≤50), SLOW (≤200), SKIP_EXPENSIVE (≤100).
- Per-cycle cache (`clear_cycle_cache()`) ensures no stale data from previous cycles.
- Sub-issue filtering (`is_sub_issue()`) prevents wasting API quota on agent sub-issues.
- Adaptive backoff doubles interval on consecutive idle polls (up to 3x, capped at 300s).
- The loop fetches all project items once per cycle (`get_project_items()`) — this is the main API cost per cycle.
- Scoped app pipeline polling (lines 495–550) monitors only parent issues and their sub-issues, reducing scope.
- Error recovery clears stale rate-limit data to prevent infinite sleep loops.

**Rationale**: The polling loop itself is well-optimized. The primary optimization opportunity is ensuring `get_project_items()` uses cached data when available and does not trigger full board data refreshes.

**Alternatives Considered**:
- Separate polling for changed-only items → Rejected for first pass: requires GraphQL query changes and may complicate the existing pipeline state machine.
- WebSocket-only without polling fallback → Rejected: polling fallback is a required reliability mechanism.

---

### R4: Repository Resolution Duplication

**Context**: `resolve_repository()` in `utils.py` is called from multiple API endpoints. Need to assess consolidation value.

**Decision**: The duplication is real but low-cost due to caching. Consolidation is a low-risk improvement.

**Findings**:
- `resolve_repository()` implements a 3-step fallback: in-memory cache (300s TTL) → GitHub GraphQL → workflow config → app settings.
- Called from: `projects.py` (line 282), `workflow.py` (lines 203, 427), and other files.
- Each call site uses the same function — the duplication is in call sites, not logic.
- The cache key includes a token hash to prevent cross-user cache reads.
- Since the cache TTL is 300s and resolution is per-project, the redundancy cost is low (cache hits in most cases).

**Rationale**: No immediate consolidation needed — the cache already prevents duplicate upstream calls. If metrics show resolution as a hot path, a middleware-level cache or request-scoped resolution could be added.

**Alternatives Considered**:
- Middleware-level resolution → Deferred: adds complexity without proven benefit.
- Request-scoped contextvar for resolved repo → Possible future optimization if resolution shows up in profiling.

---

### R5: Frontend Query Invalidation Patterns

**Context**: Need to understand whether lightweight task updates trigger full board data reloads.

**Decision**: The current invalidation is well-scoped for tasks but the refresh coordination between hooks needs tightening.

**Findings**:
- `useRealTimeSync.ts` invalidates only `['projects', projectId, 'tasks']` on WebSocket messages — does NOT invalidate board data. This is correct.
- `useBoardRefresh.ts` manages manual refresh (force bypass), auto-refresh (5-minute interval), and page visibility.
- Manual refresh calls `getBoardData(projectId, true)` which bypasses server cache.
- Auto-refresh uses `invalidateQueries` which may serve from TanStack Query cache if data is within `staleTime`.
- `requestBoardReload()` is debounced at 2s to prevent rapid reload storms.
- Manual refresh cancels pending debounced reloads — correct priority ordering.
- Polling fallback in `useRealTimeSync.ts` only invalidates tasks, not board data — aligned with SC-004/FR-006.

**Rationale**: The invalidation scope is already correct (tasks vs. board data separation). The main optimization opportunity is ensuring that the 5-minute auto-refresh does not conflict with active WebSocket connections, and that reconnection storms are properly coalesced.

**Alternatives Considered**:
- Granular per-task invalidation → Deferred: TanStack Query v5 supports it but requires restructuring query keys.
- Suppress auto-refresh when WebSocket is active → Good first-pass optimization: reduces unnecessary backend calls when real-time channel is healthy.

---

### R6: Frontend Render Optimization Patterns

**Context**: Need to assess which components are memoized and where prop instability causes unnecessary rerenders.

**Decision**: Component-level memoization exists but prop stability is inconsistent. Low-risk improvements available.

**Findings**:
- `BoardColumn.tsx`: Wrapped in `React.memo` ✅. Receives `onCardClick` callback — if parent doesn't memoize this, all columns rerender on any parent state change.
- `IssueCard.tsx`: Wrapped in `React.memo` ✅. Label parsing and body truncation computed inline each render. `onClick` and `availableAgents` props need upstream stabilization.
- `ProjectsPage.tsx`: `heroStats` memoized with `useMemo` ✅. Sync status labels and rate limit checks computed inline ❌. `RateLimitContext` updated every render even if values unchanged.
- `ChatPopup.tsx`: RAF-gated drag listener ✅. `onResizeStart` depends on `size` state — recreated on every resize.
- `AddAgentPopover.tsx`: Uses Radix Popover for positioning ✅. Filter input has no debounce. `filteredAgents` array computed inline without `useMemo`.

**Rationale**: The React.memo wrappers are correct but ineffective when upstream props are unstable. The highest-value fixes are: (1) memoize callback props in parents, (2) memoize derived data that doesn't change between renders, (3) debounce filter input in AddAgentPopover.

**Alternatives Considered**:
- Board virtualization (react-window/react-virtuoso) → Explicitly deferred unless baseline shows large boards still lag after lighter fixes.
- Global state management (Zustand/Jotai) → Rejected: adds dependency and complexity for marginal gain over TanStack Query cache.

---

### R7: Existing Test Coverage Gaps

**Context**: Need to understand what test coverage exists and what needs to be extended for verification.

**Decision**: Coverage is strong for individual behaviors but lacks integration-level tests for coordinated refresh behavior.

**Findings**:
- **test_cache.py** (~17 test classes): Comprehensive cache TTL, expiration, stale fallback, hash change detection. Gap: no concurrent access or memory limit tests.
- **test_api_board.py** (28 tests): Board endpoint, caching, change detection, error handling, sub-issue cache. Gap: no concurrent request deduplication or cascading invalidation tests.
- **test_copilot_polling.py** (~302 tests): Extensive polling orchestration, state management, recovery. Gap: no end-to-end polling cycle cost measurement.
- **useRealTimeSync.test.tsx** (41 tests): WebSocket lifecycle, message handling, debouncing, polling fallback scope. Gap: no batching or interaction with useBoardRefresh.
- **useBoardRefresh.test.tsx** (27 tests): Manual/auto-refresh, deduplication, page visibility, rate limit. Gap: no coordinated refresh with useRealTimeSync or adaptive interval tests.

**Rationale**: The existing test infrastructure is well-designed and provides reliable regression coverage. New tests should extend existing patterns rather than introducing new test frameworks.

**Alternatives Considered**:
- E2E performance tests with Playwright → Deferred: high setup cost, manual profiling sufficient for first pass.
- Load testing with Locust → Deferred: single-user performance focus in first pass.

---

### R8: Best Practices for React Performance Optimization

**Context**: Need to confirm best practices for the render optimization targets.

**Decision**: Follow established React 18 patterns: stabilize props, memoize expensive computations, avoid new dependencies.

**Findings**:
- **React.memo effectiveness**: Only prevents rerenders when all props have stable references. Adding `React.memo` without stabilizing props is ineffective.
- **useCallback for event handlers**: Wrap callbacks passed as props in `useCallback` with correct dependency arrays. This prevents child components from rerendering when the parent renders.
- **useMemo for derived data**: Use for expensive computations (sorting, filtering, aggregation) that depend on stable inputs. Avoid for trivial computations where the overhead exceeds the computation cost.
- **Throttle/debounce for event listeners**: Use `requestAnimationFrame` for visual updates (drag, scroll), `debounce` for input filtering, `throttle` for periodic updates. The codebase already uses RAF in ChatPopup — extend this pattern.
- **Context value stability**: Wrap context provider values in `useMemo` to prevent consumers from rerendering when the provider renders. The `RateLimitContext` update in ProjectsPage is a candidate.

**Rationale**: These are standard React 18 patterns that align with the codebase's existing approaches (React.memo already used, RAF already used in ChatPopup).

**Alternatives Considered**:
- React Compiler (React 19) for automatic memoization → Not applicable: codebase uses React 18.
- useSyncExternalStore for cache → Overkill: TanStack Query already manages cache subscriptions.
