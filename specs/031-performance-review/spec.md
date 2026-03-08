# Feature Specification: Performance Review

**Feature Branch**: `031-performance-review`  
**Created**: 2026-03-08  
**Status**: Draft  
**Input**: User description: "Perform a balanced first pass focused on measurable, low-risk performance gains across backend and frontend. Start by capturing baselines and instrumentation, then fix the highest-value issues already surfaced by the codebase: backend GitHub API churn around board refreshes and polling, and frontend board responsiveness issues caused by broad query invalidation, full-list rerenders, and hot event listeners. Defer broader architectural refactors like virtualization and large service decomposition unless the first pass fails to meet targets."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Baseline Measurement Before Any Optimization (Priority: P1)

As the development team, I need to capture current backend and frontend performance baselines before making any behavior changes so that every optimization can be proven with data rather than assumed, and regressions can be detected immediately.

**Why this priority**: Without baselines, there is no way to prove that optimizations work or detect regressions. This story blocks all other optimization work because the success criteria and regression guardrails depend on it.

**Independent Test**: Can be verified by executing a repeatable measurement protocol that records idle API call count over a fixed interval, board endpoint request cost, WebSocket/polling refresh counts, board render time, and component rerender hot spots for a representative project board.

**Acceptance Scenarios**:

1. **Given** the measurement protocol is defined and documented, **When** baseline measurements are captured on a representative board (50–200 cards), **Then** the following metrics are recorded: idle outbound GitHub API call count over 5 minutes, board endpoint average response time, board initial render time, single-card-update rerender count, and WebSocket/polling refresh frequency.
2. **Given** baseline metrics have been captured, **When** optimization changes are applied, **Then** the same measurement protocol is re-run and improvement percentages are documented with before/after comparisons.
3. **Given** existing tests cover cache, polling, WebSocket fallback, and board refresh behavior, **When** the baseline phase completes, **Then** a before/after checklist is produced that maps each test to the optimization area it guards.

---

### User Story 2 - Idle Board Viewing Without Excessive API Calls (Priority: P1)

As a user viewing a project board that has no active changes, the system should not make unnecessary GitHub API calls in the background. Repeated identical refreshes waste rate-limit budget and can degrade or block board interactions when the budget is exhausted.

**Why this priority**: Excessive idle API consumption is the highest-impact backend issue. It directly affects rate-limit headroom for all users and, unchecked, can block board interactions entirely.

**Independent Test**: Can be verified by opening a board with no pending changes and monitoring network activity over a 5-minute interval. The count of outbound GitHub API calls should remain below a defined threshold.

**Acceptance Scenarios**:

1. **Given** a user is viewing an open board with no data changes, **When** 5 minutes elapse without user interaction, **Then** the system makes no more than 2 GitHub API calls during that window (excluding the initial load).
2. **Given** a board is open and WebSocket change detection reports no changes, **When** the next subscription refresh cycle fires, **Then** no board data refresh is triggered.
3. **Given** a board is open and the WebSocket connection drops to fallback polling, **When** the polling cycle completes and detects no data changes, **Then** no expensive board data refresh is triggered.
4. **Given** the current backend state is audited against Spec 022 acceptance criteria, **When** any gaps are identified in WebSocket change detection, board cache TTL alignment, or sub-issue cache invalidation, **Then** those gaps are addressed before declaring the idle API reduction complete.

---

### User Story 3 - Coherent and Lightweight Board Refresh on Real-Time Updates (Priority: P1)

As a user collaborating on a board, when a teammate makes a change (moves a card, updates a status), I should see the update reflected quickly without triggering a full board reload or a cascade of redundant queries.

**Why this priority**: The refresh path directly determines the user's perception of real-time collaboration. If lightweight task updates trigger expensive full-board queries, users experience both unnecessary latency and wasted API budget.

**Independent Test**: Can be verified by making a single task change on one client and measuring update latency and network activity on a second client. Lightweight updates should not cause full board data re-fetches.

**Acceptance Scenarios**:

1. **Given** a user is viewing a board and a collaborator updates a task field via WebSocket, **When** the update arrives, **Then** only the affected task data is refreshed and the board data query is not fully invalidated.
2. **Given** a user is on fallback polling (WebSocket unavailable), **When** the polling cycle detects a lightweight task change, **Then** the system refreshes only the relevant task data without re-fetching the entire board.
3. **Given** the refresh paths (WebSocket updates, fallback polling, auto-refresh, manual refresh) are reviewed, **When** all four paths are tested, **Then** they follow a single coherent policy where only manual refresh triggers a full board data re-fetch.
4. **Given** a user explicitly clicks the manual refresh button, **When** the refresh executes, **Then** all caches (including sub-issue caches) are bypassed and a complete board data fetch occurs.

---

### User Story 4 - Sub-Issue Cache Reduces Redundant Fetches (Priority: P2)

As a user viewing a board with cards that have sub-issues, the system should reuse cached sub-issue data across automatic board refreshes instead of re-fetching sub-issues on every board load.

**Why this priority**: Sub-issue fetching multiplies the API call count per board refresh. Caching sub-issue data materially reduces per-refresh cost and is a high-value, low-risk optimization.

**Independent Test**: Can be verified by loading a board with sub-issues, observing the initial sub-issue API call count, then triggering an automatic refresh and confirming that warm sub-issue cache eliminates redundant calls.

**Acceptance Scenarios**:

1. **Given** a board is loaded with cards containing sub-issues, **When** an automatic (non-manual) board refresh occurs, **Then** sub-issue data is served from cache and no additional sub-issue API calls are made.
2. **Given** a user clicks the manual refresh button, **When** the board reloads, **Then** sub-issue caches are invalidated and fresh sub-issue data is fetched.
3. **Given** sub-issue cache entries exist, **When** the cache TTL expires, **Then** subsequent board refreshes fetch fresh sub-issue data.
4. **Given** sub-issue data is partially cached (some cached, some not), **When** a board refresh occurs, **Then** only the missing sub-issues are fetched, not all of them.

---

### User Story 5 - Responsive Board Interactions on Medium-to-Large Boards (Priority: P2)

As a user working with a board containing 50–200 cards, dragging cards, opening card details, and scrolling columns should feel responsive and smooth without visible lag or jank.

**Why this priority**: Frontend rendering cost is noticeable on medium-to-large boards and directly affects usability. While lower priority than fixing API churn (which can block functionality entirely), render responsiveness is a key quality-of-experience indicator.

**Independent Test**: Can be verified by profiling a board with 100+ cards: measure initial render time, drag-interaction frame rate, and column scroll smoothness, comparing before/after metrics.

**Acceptance Scenarios**:

1. **Given** a board with 100 cards across 5 columns is loaded, **When** the user drags a card between columns, **Then** the interaction completes without visible frame drops (target: ≥30 fps during drag).
2. **Given** a board with 100 cards is displayed, **When** a single card's status changes, **Then** only the affected card and its column re-render, not the entire board.
3. **Given** the user scrolls a column containing 40 cards, **When** scrolling at normal speed, **Then** the scroll interaction is smooth with no perceptible jank.
4. **Given** board page components perform sorting and aggregation for derived state, **When** the component re-renders without data changes, **Then** the derived-state computation is not repeated (results are stabilized across renders).

---

### User Story 6 - Chat and Popover Interactions Without Performance Degradation (Priority: P3)

As a user interacting with the chat popup (dragging, resizing) or agent popovers, these interactions should not cause noticeable lag due to excessive event listener activity.

**Why this priority**: While lower impact than board rendering, hot event listeners on drag and positioning logic can cause frame drops during common interactions. These are low-risk fixes with visible improvement.

**Independent Test**: Can be verified by profiling the chat drag interaction and popover open/reposition, measuring event handler invocations per second and frame rate during interaction.

**Acceptance Scenarios**:

1. **Given** the chat popup is visible, **When** the user drags it to a new position, **Then** the drag interaction maintains ≥30 fps with throttled position updates.
2. **Given** an agent popover is open, **When** the viewport is resized or scrolled, **Then** the popover repositions smoothly without triggering excessive re-renders of unrelated components.

---

### User Story 7 - Verification and Regression Coverage (Priority: P2)

As the development team, after optimization changes are applied, I need to verify improvements with automated tests and at least one manual network/profile pass to confirm the target improvements are real rather than inferred.

**Why this priority**: Verification closes the loop on the measurement-driven approach. Without it, optimizations may be incomplete, incorrectly applied, or regressed by future changes.

**Independent Test**: Can be verified by running the extended test suite (backend and frontend) and comparing automated and manual measurements against the Phase 1 baselines.

**Acceptance Scenarios**:

1. **Given** optimization changes are complete, **When** backend unit tests covering cache behavior, WebSocket change detection, fallback polling, and board refresh are executed, **Then** all tests pass and new tests cover the optimization-specific behaviors.
2. **Given** optimization changes are complete, **When** frontend tests covering real-time sync, board refresh hooks, and render behavior are executed, **Then** all tests pass and new tests cover the decoupled refresh paths and memoized components.
3. **Given** both automated test suites pass, **When** a manual network/profile pass is performed on a representative board, **Then** the results confirm that idle API activity, refresh behavior, and board interaction responsiveness meet the success criteria.

---

### Edge Cases

- What happens when the WebSocket connection is lost and re-established during an active board session? The system must not trigger a cascade of redundant board refreshes on reconnection.
- How does the system behave when the board cache TTL expires while the user is actively interacting with the board? Active interactions must not be interrupted by cache expiration-triggered refreshes.
- What happens when a manual refresh is triggered while an automatic refresh is already in progress? The manual refresh must take priority and the automatic refresh must be cancelled or deduplicated.
- How does the fallback polling path behave when the backend returns identical data to the previous poll? No board refresh should be triggered if the data has not changed.
- What happens when a board has zero cards? Optimizations must not introduce errors for empty board states.
- What happens when sub-issue data is partially cached (some sub-issues cached, others not)? The system must fetch only the missing sub-issues, not refetch all of them.
- What happens if the polling loop or subscription refresh fires while the previous cycle is still completing? The system must deduplicate or queue requests, not stack them.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST capture and record performance baselines (idle API call count, board endpoint cost, board render time, rerender counts, WebSocket/polling refresh frequency) before any optimization code changes are applied.
- **FR-002**: System MUST verify current backend implementation state against Spec 022 acceptance criteria (WebSocket change detection, board cache TTL alignment, sub-issue cache invalidation) before beginning optimization work, to target gaps rather than redo completed items.
- **FR-003**: System MUST NOT trigger board data refreshes when WebSocket change detection reports no changes to the board data.
- **FR-004**: System MUST NOT trigger full board data refreshes during fallback polling when no data changes are detected compared to the previous poll result.
- **FR-005**: System MUST decouple lightweight task updates (field changes received via WebSocket or polling) from the expensive full board data query, refreshing only the affected task data.
- **FR-006**: System MUST ensure manual refresh bypasses all caches (including sub-issue caches) and performs a complete board data fetch.
- **FR-007**: System MUST cache sub-issue data and serve it from cache on automatic (non-manual) board refreshes, reducing redundant sub-issue API calls.
- **FR-008**: System MUST invalidate sub-issue caches when the cache TTL expires or when a manual refresh is triggered.
- **FR-009**: System MUST ensure that only affected cards and their containing columns re-render when a single card's data changes, rather than re-rendering the entire board.
- **FR-010**: System MUST reduce repeated derived-data computation (sorting, aggregation) in board page components by stabilizing computation results across renders.
- **FR-011**: System MUST throttle or debounce event listeners for drag interactions (chat popup) and popover positioning to prevent per-pixel event handler execution.
- **FR-012**: System MUST ensure that WebSocket reconnection does not trigger a cascade of redundant board refreshes.
- **FR-013**: System MUST ensure that concurrent refresh requests (manual refresh during an in-progress automatic refresh) are deduplicated, with manual refresh taking priority.
- **FR-014**: System MUST ensure that the four refresh paths (WebSocket updates, fallback polling, auto-refresh timer, manual refresh) follow a single coherent policy.
- **FR-015**: System MUST maintain or extend existing test coverage for cache behavior, WebSocket change detection, fallback polling, and board refresh logic to serve as regression guardrails.
- **FR-016**: System MUST validate all optimization improvements with before/after measurements using the same repeatable measurement protocol.

### Key Entities

- **Board Data Cache**: Represents the cached state of a project board, including columns, cards, and metadata. Has a TTL (currently 300 seconds) and can be invalidated by manual refresh or data changes.
- **Sub-Issue Cache**: Represents cached sub-issue data associated with board cards. Has its own TTL and is invalidated on manual refresh or TTL expiry. Reduces per-refresh API call count.
- **Refresh Event**: Represents a trigger to update board data. Has a source (WebSocket update, fallback polling, auto-refresh timer, or manual user action) and a scope (lightweight task update vs. full board refresh).
- **Performance Baseline**: A recorded set of metrics captured before and after optimization changes, including idle API call count, board endpoint response time, board render time, component rerender counts, and refresh frequency.
- **Refresh Policy**: The coherent set of rules governing how each refresh source (WebSocket, polling, auto-refresh, manual) interacts with the board data query and cache layers.

## Scope

### In Scope (First Pass)

- Performance baseline capture and measurement protocol
- Verification of current backend state against Spec 022 acceptance criteria
- Backend idle API reduction (WebSocket subscription refresh logic, sub-issue caching, polling path cleanup)
- Frontend refresh-path decoupling (lightweight task updates vs. full board refresh)
- Low-risk frontend render optimization (memoization, prop stabilization, derived-data caching, event listener throttling)
- Regression test extension for affected areas
- Before/after measurement validation

### Out of Scope (Unless Metrics Justify)

- Board virtualization (deferred to a potential follow-on phase)
- Major service decomposition around GitHub project fetching/polling
- New frontend dependencies or libraries
- Larger architectural rewrites
- Bounded cache policy redesign beyond current TTL-based approach

## Dependencies

- **Spec 022 (API Rate Limit Protection)**: The current backend implementation is expected to partially or fully implement Spec 022 acceptance criteria. Phase 1 must confirm the current state before targeting remaining gaps.
- **Existing Test Suites**: The optimization relies on existing backend tests (cache, board, polling) and frontend tests (real-time sync, board refresh) as regression guardrails. These must be passing before optimization begins.

## Assumptions

- The current board endpoint already implements a 300-second cache TTL and clears sub-issue cache on manual refresh. Optimization work builds on this existing foundation rather than reimplementing it.
- WebSocket change detection is at least partially implemented per Spec 022. Phase 1 will confirm exactly what is implemented vs. what remains.
- The target board size for performance testing is 50–200 cards across 3–7 columns, representing a typical medium-to-large project board.
- Rate-limit budget improvements are measured against the idle scenario (board open with no active changes) as the primary indicator of waste reduction.
- Fallback polling is already present as a degraded-mode path when WebSocket connections fail. Optimization focuses on making this path cheaper, not replacing it.
- The existing test suites provide adequate coverage to serve as regression guardrails. Test extension is limited to areas directly affected by the optimization changes.
- Performance improvements target the standard web application experience; no mobile-specific optimizations are included.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Idle API call count for an open board with no changes is reduced by at least 50% compared to the pre-optimization baseline over a 5-minute observation window.
- **SC-002**: Board refresh triggered by a single-card WebSocket update completes in under 1 second as perceived by the user, without triggering a full board data re-fetch.
- **SC-003**: Sub-issue data is served from cache on automatic board refreshes, reducing sub-issue-related API calls by at least 80% compared to the no-cache baseline.
- **SC-004**: Board initial render time for a 100-card board is not degraded (stays within 10% of baseline) after optimization changes.
- **SC-005**: A single-card status change on a 100-card board causes no more than 3 component re-renders (the card, its column, and the board container), rather than re-rendering all cards.
- **SC-006**: Chat popup drag interaction and popover repositioning maintain at least 30 frames per second during continuous movement.
- **SC-007**: No existing tests in the backend or frontend test suites are broken by the optimization changes.
- **SC-008**: All optimization improvements are validated with before/after measurements using the same repeatable measurement protocol.
- **SC-009**: Fallback polling does not trigger full board data refreshes when the polled data is unchanged from the previous cycle.
- **SC-010**: Manual refresh continues to bypass all caches and return fully fresh data within the current expected response time (no regression).
- **SC-011**: The four refresh paths (WebSocket, fallback polling, auto-refresh, manual) follow a documented, coherent policy with no conflicting behaviors.
