# Feature Specification: Performance Review

**Feature Branch**: `001-performance-review`  
**Created**: 2026-03-22  
**Status**: Draft  
**Input**: User description: "Perform a balanced first pass focused on measurable, low-risk performance gains across backend and frontend. Start by capturing baselines and instrumentation, then fix the highest-value issues already surfaced by the codebase: backend GitHub API churn around board refreshes and polling, and frontend board responsiveness issues caused by broad query invalidation, full-list rerenders, and hot event listeners. Defer broader architectural refactors like virtualization and large service decomposition unless the first pass fails to meet targets."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Baseline Performance Measurement (Priority: P1)

As a developer maintaining the application, I need documented performance baselines for both backend API consumption and frontend rendering so that every subsequent optimization can be validated against real numbers rather than assumptions.

**Why this priority**: Without baselines, no optimization can be proven effective. This story blocks all other work because success criteria and regression guardrails depend on measured before/after comparisons. Skipping baselines risks wasting effort on changes that produce no measurable improvement or introducing regressions that go undetected.

**Independent Test**: Can be fully tested by running the baseline capture procedure on an open board and recording idle API call counts, board endpoint response times, WebSocket/polling refresh frequency, and frontend render profile data. Delivers a measurement checklist that gates all subsequent optimization work.

**Acceptance Scenarios**:

1. **Given** a user has a board open and idle (no manual interactions) for 5 minutes, **When** backend network activity is monitored, **Then** the number of outbound GitHub API calls and their endpoints are recorded as the backend idle baseline.
2. **Given** a user opens a board with a representative number of items (50+ cards across 5+ columns), **When** the board loads and renders, **Then** the total load time, number of API calls, and frontend component render counts are recorded as the board-load baseline.
3. **Given** existing automated tests for cache behavior, polling logic, WebSocket fallback, and board refresh, **When** each test is run and its pass/fail result recorded, **Then** a before/after checklist is established for regression detection.
4. **Given** a board is open and receiving WebSocket or polling updates, **When** a task update arrives, **Then** the number of queries invalidated and components re-rendered are recorded as the refresh-path baseline.

---

### User Story 2 - Reduced Backend API Consumption During Idle Board Viewing (Priority: P1)

As a user viewing a project board without making changes, I expect the application to remain responsive and not consume excessive GitHub API rate limit budget in the background, so that my rate limit quota is preserved for intentional actions.

**Why this priority**: Excessive idle API consumption is the highest-value backend issue. It directly depletes shared GitHub rate limit budget and can cause degraded service for the user and other concurrent sessions. Fixing this delivers immediate, measurable value.

**Independent Test**: Can be fully tested by opening a board, leaving it idle for a measured interval, and confirming that no repeated unchanged refresh calls are emitted. The WebSocket subscription loop should detect unchanged data via hash comparison and skip sending refresh messages.

**Acceptance Scenarios**:

1. **Given** a board is open and idle with no data changes on GitHub, **When** the WebSocket subscription refresh loop runs for 5 minutes, **Then** zero refresh messages are sent to the client because the data hash is unchanged.
2. **Given** the board endpoint caches data with a 300-second TTL, **When** the WebSocket loop checks for updates within that TTL window, **Then** the cached response is returned without a new outbound GitHub API call.
3. **Given** fallback polling is active (WebSocket unavailable), **When** the polling interval fires, **Then** it does not trigger a full board data refetch; it only refreshes task-level data consistent with the lightweight refresh contract.
4. **Given** a warm sub-issue cache exists for board items, **When** the board endpoint is called without manual refresh, **Then** cached sub-issue data is reused and no additional GitHub API calls are made for sub-issues.

---

### User Story 3 - Clean Refresh-Path Separation Between Lightweight and Full Refreshes (Priority: P2)

As a user interacting with the board, I expect lightweight real-time task updates (status changes, new tasks, task edits) to appear quickly without triggering a slow full board data reload, while manual refresh still performs a complete data refresh when I explicitly request it.

**Why this priority**: The refresh path is the bridge between backend and frontend performance. If lightweight updates trigger expensive board queries, both API consumption and UI responsiveness suffer. Establishing a clear contract here enables all other optimizations to work correctly.

**Independent Test**: Can be fully tested by triggering a WebSocket task update message and verifying that only the tasks query is invalidated (not the board data query), then triggering a manual refresh and confirming the full board query fires with cache bypass.

**Acceptance Scenarios**:

1. **Given** a WebSocket connection is active, **When** a `task_update`, `task_created`, or `status_changed` message arrives, **Then** only the tasks query (`['projects', projectId, 'tasks']`) is invalidated; the board data query (`['board', 'data', projectId]`) is not touched.
2. **Given** WebSocket is unavailable and fallback polling is active, **When** the polling interval fires, **Then** only the tasks query is invalidated; the board data query continues on its own 5-minute auto-refresh schedule.
3. **Given** a user clicks the manual refresh button, **When** the refresh request is sent, **Then** the backend is called with `refresh=true`, sub-issue caches are cleared, and fresh board data is fetched bypassing the cache.
4. **Given** the auto-refresh timer fires (5-minute interval), **When** the board data is refetched, **Then** the backend serves from cache if the TTL has not expired, avoiding an unnecessary GitHub API call.

---

### User Story 4 - Improved Frontend Board Rendering Performance (Priority: P2)

As a user scrolling, dragging, or interacting with a board containing many cards, I expect the interface to feel responsive without noticeable lag, jank, or delays when hovering, dragging, or scrolling.

**Why this priority**: Even with backend optimizations, frontend rendering bottlenecks can make the board feel slow. Low-risk render optimizations (reducing derived-data recomputation, stabilizing props, throttling hot event listeners) provide noticeable UX improvements without introducing new dependencies or architectural complexity.

**Independent Test**: Can be fully tested by profiling board interactions (drag, scroll, hover) on a board with 50+ cards using browser developer tools and confirming that unnecessary re-renders, expensive recomputations, and unthrottled event listeners are eliminated.

**Acceptance Scenarios**:

1. **Given** a board with 50+ cards is displayed, **When** the user scrolls through columns, **Then** only visible or near-visible cards re-render; cards outside the interaction area do not trigger unnecessary render cycles.
2. **Given** a user drags a card between columns, **When** the drag is in progress, **Then** drag positioning listeners fire at a throttled rate and do not cause frame drops or layout thrashing.
3. **Given** a board page component computes derived data (sorting, aggregation), **When** the underlying data has not changed, **Then** the derived computation is not re-executed on every render cycle.
4. **Given** popover or tooltip positioning listeners are active (chat popup, agent popover), **When** no user interaction is occurring, **Then** the listeners do not fire continuously or are throttled to prevent idle CPU usage.

---

### User Story 5 - Regression Test Coverage for Performance-Sensitive Paths (Priority: P3)

As a developer making future changes, I need automated tests covering the performance-sensitive code paths (cache behavior, WebSocket change detection, fallback polling, refresh invalidation) so that regressions are caught before they reach production.

**Why this priority**: Optimizations without regression coverage are fragile. Extending existing test suites to cover the specific behaviors being optimized ensures the gains are preserved over time. This story depends on stories 2–4 being implemented first.

**Independent Test**: Can be fully tested by running the extended test suites and confirming that all new test cases pass, covering idle refresh suppression, cache hit/miss behavior, refresh-path separation, and render optimization guards.

**Acceptance Scenarios**:

1. **Given** the backend cache tests, **When** a board endpoint is called within the TTL window without manual refresh, **Then** the test verifies cached data is returned without an outbound API call.
2. **Given** the WebSocket subscription tests, **When** the data hash is unchanged between refresh cycles, **Then** the test verifies no refresh message is sent to the client.
3. **Given** the frontend real-time sync tests, **When** a `refresh` message arrives via WebSocket, **Then** the test verifies only the tasks query is invalidated and the board data query is not.
4. **Given** the fallback polling tests, **When** polling fires, **Then** the test verifies it does not trigger an expensive board data refetch.

---

### User Story 6 - Optional Second-Wave Optimization Plan (Priority: P3)

As a product owner, if the first-pass optimizations do not meet performance targets, I need a documented follow-on plan identifying the next set of structural changes (board virtualization, service decomposition, bounded cache policies) so that the team can proceed without another full analysis phase.

**Why this priority**: This is explicitly deferred work. It is included only as a planning artifact produced if Phase 1–3 results are insufficient. No code changes are required unless measurements prove the need.

**Independent Test**: Can be fully tested by reviewing the follow-on plan document (if produced) and confirming it identifies specific structural changes, estimated effort, and the measurement thresholds that triggered its creation.

**Acceptance Scenarios**:

1. **Given** Phase 1–3 optimizations are complete and baselines re-measured, **When** backend idle API calls still exceed the target reduction, **Then** a follow-on plan is documented recommending deeper service consolidation in the GitHub projects service and polling pipeline.
2. **Given** Phase 1–3 optimizations are complete and baselines re-measured, **When** large boards (100+ cards) still exhibit noticeable UI lag, **Then** a follow-on plan is documented recommending board virtualization as the next step.

---

### Edge Cases

- What happens when the WebSocket connection drops and reconnects rapidly? The system must debounce reconnection-triggered invalidations (current 2-second debounce window) to prevent a burst of redundant queries.
- How does the system handle a GitHub API rate limit being fully exhausted (0 remaining) during a refresh cycle? The backend must detect rate limit exhaustion and return stale cached data with appropriate rate limit information rather than failing the request.
- What happens when a board has zero items? Cache and refresh logic must handle empty boards gracefully without triggering unnecessary refetches or errors.
- How does the system behave when multiple users view the same board simultaneously? Each user session maintains its own WebSocket subscription and cache context; shared server-side caches should not cause cross-session interference.
- What happens when the stale revalidation counter reaches its limit (10) during an extended period of unchanged data? The system forces a fresh fetch to confirm data freshness, then resets the counter.
- How does tab visibility affect auto-refresh? When a tab becomes hidden, auto-refresh timers are paused. When the tab becomes visible again, if the data is older than the auto-refresh interval, an immediate refresh is triggered.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST capture and record backend performance baselines (idle API call count, board endpoint response cost, WebSocket refresh frequency) before any optimization changes are applied.
- **FR-002**: System MUST capture and record frontend performance baselines (board load time, component render counts, query invalidation patterns) before any optimization changes are applied.
- **FR-003**: The WebSocket subscription refresh loop MUST skip sending refresh messages to the client when the computed data hash is unchanged from the last sent message.
- **FR-004**: The board endpoint MUST serve cached data when called within the cache TTL window (300 seconds) without a manual refresh flag, avoiding new outbound GitHub API calls.
- **FR-005**: Sub-issue cache data MUST be reused for non-manual-refresh board requests when a warm cache exists, eliminating redundant GitHub API calls for sub-issue data.
- **FR-006**: Manual refresh (user-initiated) MUST bypass backend caches, clear sub-issue caches, and fetch fresh data from GitHub.
- **FR-007**: Fallback polling (when WebSocket is unavailable) MUST invalidate only the tasks query and MUST NOT trigger full board data refetches.
- **FR-008**: WebSocket real-time update messages (`task_update`, `task_created`, `status_changed`) MUST invalidate only the tasks query, not the board data query.
- **FR-009**: Auto-refresh timer MUST be suppressed when a healthy WebSocket connection is active, preventing duplicate refresh paths.
- **FR-010**: Frontend page-level derived data (sorting, aggregation, grouping) MUST be memoized so that recomputation only occurs when the underlying data changes.
- **FR-011**: Hot event listeners (drag positioning, popover positioning) MUST be throttled or debounced to prevent frame drops and idle CPU consumption.
- **FR-012**: Existing backend test suites (cache, board, polling, WebSocket) MUST be extended to cover the specific behaviors modified by this optimization work.
- **FR-013**: Existing frontend test suites (real-time sync, board refresh) MUST be extended to verify refresh-path separation and invalidation correctness.
- **FR-014**: The system MUST handle GitHub API rate limit exhaustion gracefully by serving stale cached data with rate limit information rather than returning errors.
- **FR-015**: If first-pass optimization targets are not met, a documented follow-on plan MUST be produced identifying structural changes and their estimated scope.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Idle board viewing (no user interaction, no data changes) produces zero unnecessary outbound API calls to GitHub over a 5-minute observation window, compared to the pre-optimization baseline.
- **SC-002**: Board data endpoint response time for cached (non-manual-refresh) requests is under 500 milliseconds, as measured from the frontend's perspective.
- **SC-003**: A lightweight task update (via WebSocket or polling) reflects in the UI within 5 seconds without triggering a full board data reload.
- **SC-004**: Board interactions (scrolling, dragging, hovering) on a board with 50+ cards maintain a frame rate above 30 FPS with no perceptible jank, as measured by browser performance profiling.
- **SC-005**: The number of component re-renders during a single task update event is reduced by at least 30% compared to the pre-optimization baseline.
- **SC-006**: All existing automated tests continue to pass after optimization changes, with zero test regressions.
- **SC-007**: Backend idle API call count (GitHub API calls made while a board is open and idle) is reduced by at least 50% compared to the pre-optimization baseline.
- **SC-008**: Fallback polling (when WebSocket is unavailable) does not increase the board data query execution count beyond the 5-minute auto-refresh schedule.
- **SC-009**: Manual refresh completes a full data reload (bypassing all caches) and the user sees updated data within 10 seconds of clicking refresh.
- **SC-010**: New or extended regression tests cover at least the following paths: cache TTL behavior, WebSocket change detection (hash comparison), fallback polling query scope, refresh-path separation (tasks-only vs full board), and event listener throttling.

## Assumptions

- The current backend board cache TTL of 300 seconds (5 minutes) is appropriate and does not need adjustment for this first pass.
- The current WebSocket check interval of 30 seconds in the projects API subscription loop is acceptable and does not need tuning.
- The stale revalidation limit of 10 in the projects API is a reasonable threshold for forcing fresh data fetches.
- Existing memoization on BoardColumn and IssueCard components (both wrapped in React.memo) is correctly implemented and does not need replacement, only supplementation with prop stabilization and derived-data memoization where missing.
- The 2-second debounce window for WebSocket reconnection invalidations is sufficient to prevent query storms.
- A board with 50+ cards across 5+ columns is representative of a "typical large board" for baseline measurement purposes.
- Board virtualization, major service decomposition, and new dependency additions are explicitly out of scope for this first pass unless measurement results prove they are necessary.
- The frontend already separates tasks query invalidation from board data query invalidation in the real-time sync hook; this behavior must be preserved and verified, not redesigned.

## Scope Boundaries

### In Scope

- Performance baseline capture (backend and frontend)
- Verification of existing rate-limit-protection implementations
- Backend: WebSocket change detection, sub-issue caching, polling guard rails, redundant API call elimination
- Frontend: Refresh-path separation enforcement, derived-data memoization, event listener throttling
- Regression test extension for modified code paths
- Follow-on plan document (only if targets are not met)

### Out of Scope (First Pass)

- Board virtualization (deferred to second wave if needed)
- Major service decomposition of GitHub project fetching/polling
- New frontend or backend dependency additions
- Changes to cache TTL values or WebSocket check intervals
- Architectural rewrites of the polling or real-time sync systems
- Performance optimizations for non-board surfaces (unless trivially co-located)
