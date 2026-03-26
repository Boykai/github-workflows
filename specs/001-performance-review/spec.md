# Feature Specification: Performance Review

**Feature Branch**: `001-performance-review`  
**Created**: 2026-03-26  
**Status**: Draft  
**Input**: User description: "Perform a balanced first pass focused on measurable, low-risk performance gains across backend and frontend. Start by capturing baselines and instrumentation, then fix the highest-value issues already surfaced by the codebase: backend GitHub API churn around board refreshes and polling, and frontend board responsiveness issues caused by broad query invalidation, full-list rerenders, and hot event listeners. Defer broader architectural refactors like virtualization and large service decomposition unless the first pass fails to meet targets."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Establish Performance Baselines Before Optimization (Priority: P1)

As a developer preparing to optimize the application, I need to capture current backend and frontend performance baselines so that every subsequent optimization can be measured against a known starting point and regressions are immediately visible.

**Why this priority**: Without baselines, no optimization can be proven effective. This is a hard dependency for all other work — every success criterion and regression guardrail depends on having before-and-after data. Starting here prevents wasted effort on changes that don't actually improve anything.

**Independent Test**: Can be fully tested by running a board in idle state for a fixed interval, recording backend request counts, frontend render counts, and network activity, then comparing those numbers against a documented checklist. Delivers a measurement framework reusable for all subsequent phases.

**Acceptance Scenarios**:

1. **Given** a board is open and idle (no user interaction) for 5 minutes, **When** baseline measurement is captured, **Then** the total number of backend requests to external services, the number of board query invalidations, and the count of frontend component rerenders are recorded and documented.
2. **Given** a user triggers a manual board refresh, **When** the request completes, **Then** the end-to-end time from click to fully updated board is recorded as the baseline manual-refresh cost.
3. **Given** the baseline measurement framework exists, **When** any code change is made in a subsequent phase, **Then** the same measurements can be rerun to produce a before-and-after comparison.
4. **Given** a board is open with an active WebSocket connection, **When** no data changes occur on the server for 5 minutes, **Then** the number of redundant refresh requests sent by the backend is recorded.

---

### User Story 2 - Reduce Idle Backend API Consumption (Priority: P1)

As a user viewing a board without making changes, I expect the application to not consume unnecessary resources in the background — specifically, the backend should not repeatedly call external services when board data has not changed.

**Why this priority**: Excessive idle API consumption directly wastes external rate-limit budget, increases costs, slows response times for all users, and risks rate-limit exhaustion. This is the highest-value backend fix because it addresses wasted work on every open board session.

**Independent Test**: Can be tested by opening a board, leaving it idle for a measured interval, and verifying that the number of external service calls stays below the defined idle-rate-limit target. Delivers immediate rate-limit budget savings.

**Acceptance Scenarios**:

1. **Given** a board is open and idle with a WebSocket connection, **When** no data changes occur for 5 minutes, **Then** the backend sends zero redundant refresh requests to external services for unchanged data.
2. **Given** a board is open and the WebSocket connection drops to fallback polling, **When** no data changes occur, **Then** fallback polling does not trigger expensive board-data refreshes and stays within the idle-rate-limit budget.
3. **Given** board data has been fetched and cached, **When** a subsequent request arrives for the same board within the cache validity window, **Then** the cached response is returned without calling external services.
4. **Given** sub-issue data has been fetched and cached for a board, **When** the board is refreshed automatically (not manually), **Then** warm sub-issue caches are reused and the total external service call count is materially reduced compared to a cold-cache refresh.

---

### User Story 3 - Decouple Lightweight Task Updates from Expensive Board Refreshes (Priority: P2)

As a user collaborating on a board, I want real-time task status updates to appear quickly without triggering a full board data reload, so that the board feels responsive and I am not waiting for expensive queries on every small change.

**Why this priority**: The current refresh paths couple lightweight task updates with the expensive board-data query, causing unnecessary delays and network traffic. Decoupling these paths is the highest-value frontend fix because it eliminates the most common source of perceived lag during normal collaboration.

**Independent Test**: Can be tested by sending a WebSocket task-update event and verifying that the board reflects the change without triggering a full board-data query invalidation. Delivers faster perceived updates during collaboration.

**Acceptance Scenarios**:

1. **Given** a board is open and connected via WebSocket, **When** a task status change event arrives, **Then** the affected task is updated in place without invalidating or refetching the entire board-data query.
2. **Given** a board is in fallback polling mode, **When** a polling cycle detects a task-level change, **Then** only the affected task data is updated — the full board-data query is not invalidated.
3. **Given** a user clicks the manual refresh button, **When** the refresh executes, **Then** a full board-data query is triggered, bypassing caches as intended, and sub-issue caches are cleared.
4. **Given** WebSocket, fallback polling, auto-refresh, and manual refresh all exist, **When** any two or more fire concurrently, **Then** a single coherent refresh policy prevents duplicate or conflicting board-data fetches.

---

### User Story 4 - Improve Board Rendering Performance for Normal-Sized Boards (Priority: P2)

As a user interacting with a board (dragging cards, opening popovers, scrolling columns), I want the interface to remain smooth and responsive without noticeable lag, so that my workflow is not interrupted by rendering delays.

**Why this priority**: Even after fixing the refresh paths, unnecessary rerenders, unstable props, and hot event listeners can cause jank during board interactions. These are low-risk rendering fixes that collectively improve the feel of the application without introducing new dependencies or architectural changes.

**Independent Test**: Can be tested by profiling board interactions (drag, scroll, popover open) on a representative board and verifying that rerender counts and interaction responsiveness meet defined thresholds. Delivers smoother user experience during normal board use.

**Acceptance Scenarios**:

1. **Given** a board with multiple columns and cards is displayed, **When** the user drags a card between columns, **Then** only the affected columns and cards rerender — unrelated columns and cards do not rerender.
2. **Given** a board page is loaded, **When** the initial render completes, **Then** expensive derived-data computations (sorting, aggregation) are not repeated on every render cycle.
3. **Given** a popover or drag interaction is active, **When** the user moves the mouse, **Then** positioning and drag event listeners fire at a throttled rate that does not cause visible frame drops.
4. **Given** a board with 50+ cards across multiple columns, **When** a single task update arrives, **Then** fewer than 10% of total card components rerender.

---

### User Story 5 - Extend Regression Test Coverage for Performance-Critical Paths (Priority: P3)

As a developer maintaining the application after performance optimizations, I need automated regression tests that guard the optimized paths so that future changes do not silently reintroduce the performance problems that were fixed.

**Why this priority**: Optimizations without regression coverage tend to degrade over time. This story ensures the improvements from Stories 1–4 are durable and measurable in CI, but it does not block the delivery of user-facing value.

**Independent Test**: Can be tested by running the extended test suite and verifying that all new performance-related assertions pass. Delivers long-term confidence that optimizations remain in place.

**Acceptance Scenarios**:

1. **Given** the backend cache behavior has been optimized, **When** the backend test suite runs, **Then** tests verify that cache TTLs are respected, stale-while-revalidate works correctly, and sub-issue caches are reused during automatic refreshes.
2. **Given** the WebSocket change-detection logic has been updated, **When** the backend test suite runs, **Then** tests verify that unchanged data does not trigger downstream refresh actions.
3. **Given** the frontend refresh paths have been decoupled, **When** the frontend test suite runs, **Then** tests verify that task-level WebSocket events do not trigger full board-data query invalidation.
4. **Given** the fallback polling path has been updated, **When** the frontend test suite runs, **Then** tests verify that polling does not trigger expensive board refreshes and that polling-to-WebSocket transitions are seamless.

---

### User Story 6 - Conditional Follow-On Plan for Larger Optimizations (Priority: P3)

As a product owner, if the first-pass optimizations do not meet the defined performance targets, I want a documented follow-on plan for more structural changes so that the team can proceed without another discovery phase.

**Why this priority**: This story is explicitly deferred unless Phase 1–3 measurements prove it necessary. It ensures readiness without premature investment in large refactors like virtualization or service decomposition.

**Independent Test**: Can be tested by reviewing the documented follow-on plan and verifying it covers the identified second-wave topics (virtualization, service decomposition, bounded caches, instrumentation). Delivers decision-ready documentation.

**Acceptance Scenarios**:

1. **Given** the first-pass optimizations have been completed and measured, **When** any success criterion is not met, **Then** a follow-on plan document exists that identifies the next recommended structural change for that specific area.
2. **Given** all first-pass success criteria are met, **When** the performance review concludes, **Then** the follow-on plan is filed as reference material but no further implementation is scheduled.

---

### Edge Cases

- What happens when the WebSocket connection drops and reconnects during an active drag operation? The board state must remain consistent, and any missed updates must be reconciled on reconnection without triggering a disruptive full-page reload.
- What happens when the board cache expires exactly while a manual refresh is in flight? The system must not produce duplicate or conflicting fetches; the manual refresh should take precedence.
- What happens when fallback polling and a restored WebSocket connection overlap briefly? The system must deduplicate updates and avoid a polling storm during the transition period.
- What happens when a board has zero cards or zero columns? Baselines and optimizations must handle empty-state boards gracefully without errors or wasted fetch cycles.
- What happens when external service rate limits are exhausted? The system should degrade gracefully by serving cached data and deferring non-critical refreshes rather than failing or retrying aggressively.
- What happens when multiple users view the same board simultaneously? Backend caching must serve shared cached data correctly without cross-user data leakage and without multiplying external service calls per viewer.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST capture and document backend and frontend performance baselines before any optimization code changes are made, including idle API call counts, board-refresh end-to-end times, frontend rerender counts, and network activity profiles.
- **FR-002**: System MUST ensure that an idle board with an active WebSocket connection produces zero redundant external service calls when board data has not changed.
- **FR-003**: System MUST ensure that WebSocket change-detection logic prevents downstream refresh actions when received data is identical to the cached state.
- **FR-004**: System MUST ensure that board-data cache TTLs are respected and that automatic refreshes reuse cached data within the validity window rather than calling external services.
- **FR-005**: System MUST ensure that warm sub-issue caches are reused during automatic board refreshes, materially reducing the total external service call count compared to cold-cache refreshes.
- **FR-006**: System MUST ensure that fallback polling does not trigger expensive full board-data refreshes when no data changes are detected.
- **FR-007**: System MUST decouple lightweight task-update events (via WebSocket or polling) from the expensive board-data query, so that task-level changes update in place without triggering a full board reload.
- **FR-008**: System MUST preserve manual refresh as a full cache-bypassing operation that clears sub-issue caches and fetches fresh data from external services.
- **FR-009**: System MUST enforce a single coherent refresh policy across WebSocket, fallback polling, auto-refresh, and manual refresh to prevent duplicate or conflicting board-data fetches.
- **FR-010**: System MUST reduce unnecessary frontend component rerenders by stabilizing props, memoizing heavy card and column components where effective, and avoiding repeated derived-data computations on each render cycle.
- **FR-011**: System MUST throttle or rationalize hot event listeners (drag handlers, popover positioning) so that they do not cause visible frame drops during board interactions.
- **FR-012**: System MUST extend backend automated test coverage to verify cache TTL behavior, stale-while-revalidate semantics, sub-issue cache reuse, WebSocket change detection, and fallback polling safety.
- **FR-013**: System MUST extend frontend automated test coverage to verify that task-level events do not trigger full board-data query invalidation, that fallback polling does not cause expensive refreshes, and that refresh-path deduplication works correctly.
- **FR-014**: System MUST consolidate duplicate repository-resolution logic into a single shared path to eliminate inconsistency and unnecessary work.
- **FR-015**: System MUST produce a documented follow-on plan if any first-pass success criterion is not met, covering virtualization, service decomposition, bounded caches, and instrumentation as next steps.

### Key Entities

- **Board Data Cache**: Represents the cached state of a project board including columns, card positions, and metadata. Key attributes: cache key, TTL, staleness indicator, last-fetched timestamp, board identifier.
- **Sub-Issue Cache**: Represents cached sub-issue data associated with board cards. Key attributes: parent issue identifier, cached sub-issue list, TTL, invalidation trigger (manual refresh vs. automatic).
- **Refresh Event**: Represents a request to update board data. Key attributes: source (WebSocket, fallback polling, auto-refresh, manual refresh), scope (full board vs. task-level), timestamp, deduplication identifier.
- **Performance Baseline**: Represents a recorded snapshot of system performance metrics. Key attributes: measurement type (idle API calls, refresh cost, rerender count, network requests), measured value, measurement interval, timestamp.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: An idle board (no user interaction, no data changes) produces at least 50% fewer external service calls over a 5-minute window compared to the documented baseline.
- **SC-002**: A single task-status update via WebSocket is reflected on the board within 2 seconds without triggering a full board-data reload.
- **SC-003**: Board interactions (card drag, popover open, column scroll) maintain at least 30 frames per second on a board with 50+ cards, with no visible jank during normal use.
- **SC-004**: Fallback polling, when active, does not increase external service call volume by more than 20% compared to an idle board with an active WebSocket connection.
- **SC-005**: Manual board refresh completes a full cache-bypassing reload within 5 seconds for a board with up to 100 cards.
- **SC-006**: Warm sub-issue caches reduce the external service call count for an automatic board refresh by at least 30% compared to a cold-cache refresh of the same board.
- **SC-007**: After a task-level update arrives, fewer than 10% of total card components on the board rerender.
- **SC-008**: All new and extended regression tests pass in CI, covering cache behavior, WebSocket change detection, fallback polling safety, and refresh-path deduplication.
- **SC-009**: No existing automated tests are broken by the performance optimizations — the full backend and frontend test suites pass without regressions.

## Assumptions

- The current board endpoint already implements a 300-second cache TTL and clears sub-issue cache on manual refresh. Optimizations should target remaining gaps rather than reimplementing existing behavior.
- WebSocket change detection, board cache TTL alignment, and sub-issue cache invalidation may be partially implemented. Phase 1 baselines will confirm the current state before optimization work begins.
- "Normal-sized board" for rendering optimization purposes is defined as up to 100 cards across up to 10 columns. Boards significantly larger than this are out of scope for the first pass.
- The idle-rate-limit target is defined as a significant reduction (at least 50%) from the measured baseline, not an absolute number, since the baseline is not yet known.
- Board virtualization, major service decomposition, new external dependency additions, and large architectural rewrites are explicitly excluded from the first pass unless baseline measurements prove they are necessary.
- Existing test infrastructure (backend pytest, frontend Vitest, linting via Ruff/ESLint) is sufficient for regression coverage without adding new testing frameworks.
- External service rate limits are a shared constraint — optimizations must reduce consumption, not merely redistribute it across different code paths.

## Dependencies

- Phase 1 (baselines) blocks all optimization work in Phases 2 and 3.
- Phase 2 backend API fixes and Phase 2 frontend refresh-path fixes can proceed in parallel once Phase 1 baselines are captured and the desired refresh contract is confirmed.
- Phase 3 frontend render optimizations depend on the refresh-path fixes from Phase 2 being stable.
- Phase 3 verification depends on Phases 2 and 3 code changes being complete.
- Phase 4 (follow-on plan) is only triggered if first-pass measurements do not meet success criteria.

## Out of Scope

- Board virtualization for large boards (deferred to follow-on plan if needed).
- Major service decomposition of the GitHub project fetching and polling pipeline.
- Adding new external dependencies or libraries.
- Large architectural rewrites of the caching or real-time sync layers.
- Performance optimization of surfaces outside the board and chat components (e.g., settings pages, authentication flows).
- Mobile or offline-specific performance concerns.
