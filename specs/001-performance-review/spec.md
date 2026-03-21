# Feature Specification: Performance Review

**Feature Branch**: `001-performance-review`  
**Created**: 2026-03-21  
**Status**: Draft  
**Input**: User description: "Perform a balanced first pass focused on measurable, low-risk performance gains across backend and frontend. Start by capturing baselines and instrumentation, then fix the highest-value issues already surfaced by the codebase: backend GitHub API churn around board refreshes and polling, and frontend board responsiveness issues caused by broad query invalidation, full-list rerenders, and hot event listeners. Defer broader architectural refactors like virtualization and large service decomposition unless the first pass fails to meet targets."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Board Stays Quiet When Idle (Priority: P1)

A user opens a project board and leaves it visible without interacting. The system should not make unnecessary backend requests to GitHub while the board data remains unchanged. Today, idle boards may still trigger repeated refresh cycles that consume API quota without providing new information.

**Why this priority**: Excessive idle API activity is the highest-cost performance issue because it wastes limited GitHub API quota, increases the risk of rate limiting, and degrades the experience for all users sharing the same quota. Fixing this delivers immediate, measurable savings with no user-facing behavior change.

**Independent Test**: Open a board, leave it idle for 10 minutes, and count the outbound requests to GitHub. Compare the count against a pre-optimization baseline to confirm a reduction of at least 50%.

**Acceptance Scenarios**:

1. **Given** a user has a board open and the underlying data has not changed, **When** the auto-refresh interval fires or the fallback polling triggers, **Then** the system does not issue a full board data fetch to GitHub.
2. **Given** a user has a board open and a WebSocket connection is healthy, **When** no change messages arrive during the auto-refresh interval, **Then** no board refresh request is made until data actually changes or the user manually refreshes.
3. **Given** a user has a board open and the WebSocket connection drops, **When** the system falls back to polling, **Then** the polling path does not trigger expensive board data fetches unless it detects that the data hash has changed.

---

### User Story 2 - Board Loads and Responds Quickly (Priority: P1)

A user navigates to a project board and interacts with it—scrolling, dragging cards between columns, opening card details. The board should render promptly on load and remain responsive during interactions, even for projects with many columns and cards.

**Why this priority**: Board responsiveness is the primary user-facing quality signal. Slow loads and laggy interactions directly impact perceived product quality and user productivity. This story targets low-risk rendering improvements that reduce wasted work without introducing new dependencies.

**Independent Test**: Load a board with at least 50 cards spread across 5+ columns. Measure initial render time and interaction latency (drag start, column scroll). Compare against a pre-optimization profile baseline to confirm measurable improvement.

**Acceptance Scenarios**:

1. **Given** a user navigates to a board with cached data available, **When** the page renders, **Then** the board appears within 2 seconds without a visible blank state.
2. **Given** a user drags a card from one column to another, **When** the drag is in progress, **Then** the board remains responsive with no perceptible frame drops or freezing.
3. **Given** a WebSocket message arrives with a task update, **When** the update is applied, **Then** only the affected card re-renders, not the entire board or all columns.

---

### User Story 3 - Manual Refresh Bypasses Caches (Priority: P2)

A user clicks the manual refresh button because they suspect the board is stale. The system should bypass all caches and fetch fresh data from GitHub, including sub-issue data that may be cached separately. This is the user's escape hatch for stale data.

**Why this priority**: Manual refresh is the user's explicit signal that they need fresh data. If it fails to deliver fresh results, users lose trust in the system's data accuracy. This story ensures the refresh contract is clear and reliable.

**Independent Test**: Modify a card's status directly in GitHub, then click manual refresh on the board. Confirm the updated status appears without waiting for an auto-refresh cycle.

**Acceptance Scenarios**:

1. **Given** the board has cached data and the user clicks manual refresh, **When** the refresh completes, **Then** the system fetches fresh data from GitHub bypassing the board cache and all sub-issue caches.
2. **Given** an auto-refresh is in progress and the user clicks manual refresh, **When** both requests overlap, **Then** the manual refresh takes priority and the auto-refresh is cancelled or its result is discarded.
3. **Given** the user clicks manual refresh while rate-limited, **When** the request fails due to quota exhaustion, **Then** the system displays the rate-limit warning with a retry time and preserves the existing cached board data.

---

### User Story 4 - Real-Time Updates Are Fast and Lightweight (Priority: P2)

A teammate moves a card or creates a new task. The user with the board open should see the change reflected quickly via WebSocket, without triggering a full board reload. Lightweight task-level updates should remain decoupled from the expensive board data query.

**Why this priority**: Real-time updates are a key collaboration feature. If every small change triggers a full board refresh, the system wastes API quota and briefly disrupts the user's view. Keeping task updates lightweight preserves both performance and user experience.

**Independent Test**: Have two users view the same board. One user changes a task status. Confirm the other user sees the update within 5 seconds without a full board reload appearing in the network log.

**Acceptance Scenarios**:

1. **Given** a WebSocket connection is active and a task status changes, **When** the change message arrives, **Then** the system updates only the task data query, not the board data query.
2. **Given** a WebSocket message indicates a new task was created, **When** the message is processed, **Then** the task appears in the correct column without requiring a manual or auto board refresh.
3. **Given** the WebSocket connection is lost and restored, **When** the reconnection occurs, **Then** the system reconciles any missed updates by invalidating the task query once, not triggering multiple board refreshes.

---

### User Story 5 - Performance Baselines Are Captured Before Changes (Priority: P1)

Before any optimization code changes are made, the development team must capture current performance baselines for both backend and frontend. These baselines serve as the "before" measurement that all improvements are validated against. Without baselines, improvements cannot be proven—only assumed.

**Why this priority**: This story is a hard prerequisite for all other stories. No optimization work should proceed without baseline measurements because success criteria and regression detection depend on having a known starting point.

**Independent Test**: Produce a baseline report documenting at least: idle API request count over a fixed interval, board endpoint response time, board initial render time, and the number of component re-renders during a standard interaction sequence.

**Acceptance Scenarios**:

1. **Given** no optimization changes have been applied, **When** the baseline measurement process runs, **Then** it produces a documented record of idle API activity for an open board over a 10-minute interval.
2. **Given** no optimization changes have been applied, **When** the frontend baseline is captured, **Then** it documents board load time, render hot spots, and the number of re-renders for a representative board interaction sequence.
3. **Given** baselines are captured, **When** optimization changes are applied and re-measured, **Then** the before-and-after comparison confirms whether each target was met or missed.

---

### User Story 6 - Regression Tests Guard Against Performance Regressions (Priority: P3)

After optimizations are applied, existing and new automated tests confirm that caching, refresh, polling, and rendering behavior is correct. The test suite should catch regressions if future changes accidentally reintroduce the problems being fixed.

**Why this priority**: Tests are the long-term guardrail. While lower priority than the fixes themselves, they ensure the improvements persist across future development. Without regression coverage, the same performance problems are likely to recur.

**Independent Test**: Run the targeted test suites (backend cache, board, polling, and frontend refresh/sync hooks) and confirm all tests pass. Verify that new or updated tests cover the specific behaviors changed by this feature.

**Acceptance Scenarios**:

1. **Given** backend cache behavior has been optimized, **When** the cache and board test suites run, **Then** all existing tests pass and new tests verify the optimized caching and change-detection behavior.
2. **Given** frontend refresh paths have been updated, **When** the real-time sync and board refresh hook test suites run, **Then** all existing tests pass and new tests verify the decoupled refresh behavior.
3. **Given** a future change accidentally reintroduces broad query invalidation on WebSocket fallback, **When** the test suite runs, **Then** at least one test fails to alert the developer to the regression.

---

### Edge Cases

- What happens when the WebSocket connection is unstable (repeatedly connecting and disconnecting)? The system should not trigger a cascade of board refresh requests on each reconnection; debounce logic must consolidate reconnection-driven invalidations.
- What happens when a user opens multiple boards in separate tabs? Each tab should manage its own refresh timer and WebSocket subscription independently without multiplying API consumption per additional tab.
- What happens when the GitHub API rate limit is exhausted mid-refresh? The system should return the most recent cached data with a clear rate-limit warning rather than showing an error or empty state.
- What happens when the board data cache expires during a period of WebSocket inactivity? The auto-refresh should silently re-fetch board data without jarring the user or causing a blank flash.
- What happens when a manual refresh and a WebSocket-driven task update arrive simultaneously? The manual refresh result should take precedence, and the task update should not overwrite the fresher manual refresh data.

## Requirements *(mandatory)*

### Functional Requirements

#### Baseline and Measurement

- **FR-001**: The team MUST capture backend performance baselines before applying any optimization changes, including idle API request count, board endpoint response cost, and polling/WebSocket refresh frequency over a fixed observation interval.
- **FR-002**: The team MUST capture frontend performance baselines before applying any optimization changes, including board initial render time, interaction latency, re-render counts for board components, and network activity during WebSocket and fallback polling.
- **FR-003**: The team MUST compare post-optimization measurements against captured baselines to validate that each targeted improvement is real and measurable.

#### Backend — Idle API Reduction

- **FR-004**: The system MUST NOT issue a full board data fetch to GitHub when the board data has not changed since the last fetch, as determined by content hash comparison.
- **FR-005**: The system MUST suppress repeated WebSocket subscription refresh cycles when the underlying project data is unchanged.
- **FR-006**: The fallback polling path MUST NOT trigger expensive board data refreshes unless it detects an actual data change (hash mismatch or explicit change signal).
- **FR-007**: The system MUST reuse warm sub-issue caches during board refreshes unless the user explicitly triggers a manual refresh, which clears sub-issue caches before fetching.

#### Backend — Cache and Refresh Contract

- **FR-008**: Manual refresh MUST bypass the board data cache and all sub-issue caches, fetching fresh data directly from GitHub.
- **FR-009**: Auto-refresh MUST use the backend cache when data is still within the cache TTL, avoiding unnecessary GitHub API calls.
- **FR-010**: The system MUST return stale cached data with appropriate warnings when a refresh fails due to rate limiting or transient errors, rather than showing an error state.

#### Frontend — Refresh Path Decoupling

- **FR-011**: WebSocket task-level messages (task updates, status changes, task creation) MUST invalidate only the task data query, not the board data query.
- **FR-012**: The board data query MUST only be refreshed by: (a) the 5-minute auto-refresh timer, (b) explicit manual refresh, or (c) a WebSocket message that indicates a structural board change.
- **FR-013**: Fallback polling MUST follow the same refresh policy as WebSocket—it MUST NOT trigger board data query invalidation for task-level changes.
- **FR-014**: When a manual refresh and an auto-refresh overlap, the manual refresh MUST take priority and the auto-refresh result MUST be discarded or cancelled.

#### Frontend — Render Optimization

- **FR-015**: Board column components MUST minimize unnecessary re-renders by stabilizing props and memoizing where re-render profiling confirms a measurable benefit.
- **FR-016**: Card components MUST re-render only when their own data changes, not when unrelated cards or columns update.
- **FR-017**: Hot event listeners (drag handlers, popover positioning) MUST be throttled or debounced to prevent excessive callback frequency during user interactions.
- **FR-018**: Derived data computations (sorting, filtering, aggregation) performed during page rendering MUST be memoized to avoid redundant recalculations on each render cycle.

#### Regression Coverage

- **FR-019**: Existing backend tests for cache behavior, board endpoints, WebSocket change detection, and polling logic MUST continue to pass after all changes.
- **FR-020**: Existing frontend tests for real-time sync, board refresh hooks, and query invalidation MUST continue to pass after all changes.
- **FR-021**: New or updated tests MUST cover the specific behaviors changed by this feature: change-detection-based refresh suppression, refresh path decoupling, and event listener throttling.

### Key Entities

- **Board Data Cache**: The server-side cached representation of board column and card data, keyed per project, with a configurable TTL. Used for auto-refresh responses and as a fallback during rate limiting.
- **Sub-Issue Cache**: A separate cache layer for sub-issue data associated with board cards, with its own TTL. Cleared on manual refresh but preserved during auto-refresh to reduce API calls.
- **Content Hash**: A hash of the board data payload used for change detection. Compared across refresh cycles to determine whether data has actually changed before sending it to the client.
- **Refresh Source**: The origin of a board refresh request (manual, auto-timer, WebSocket, fallback polling). Each source follows different cache-bypass rules defined by the refresh contract.
- **Rate Limit Budget**: The remaining GitHub API quota available for the current rate-limit window. Used to gate expensive operations and trigger fallback behavior when quota is low.

## Assumptions

- The existing 300-second (5-minute) board cache TTL and 5-minute auto-refresh interval are appropriate defaults and do not need to change in this pass.
- The existing WebSocket message types (task_update, task_created, status_changed, refresh) are sufficient to distinguish task-level changes from structural board changes.
- The existing debounce interval of 2 seconds for consolidating board reload triggers is sufficient and does not need adjustment.
- The existing rate-limit thresholds in the polling loop (pause at 50, slow at 200, skip expensive at 100) are reasonable and do not need adjustment in this pass.
- Board virtualization and lazy-loading of sub-issues are explicitly out of scope for the first pass unless baseline measurements show they are necessary to meet performance targets.
- Service-level decomposition of the GitHub projects service is out of scope for the first pass.
- No new third-party dependencies will be introduced for performance optimization in this pass.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Idle API activity for an open board with no data changes is reduced by at least 50% compared to the captured baseline, measured as outbound GitHub API request count over a 10-minute idle observation window.
- **SC-002**: Board initial render time for a representative project (50+ cards, 5+ columns) does not exceed the baseline by more than 10%, and ideally improves by at least 20%.
- **SC-003**: When a single task is updated via WebSocket, only the affected card component re-renders; no full-column or full-board re-render is triggered.
- **SC-004**: Manual refresh delivers fresh data within 5 seconds on a typical connection, bypassing all caches including sub-issue caches.
- **SC-005**: Fallback polling, when active, does not trigger more than one board data fetch per polling interval unless the data hash indicates a change.
- **SC-006**: All existing backend tests (cache, board, polling, WebSocket) and frontend tests (real-time sync, board refresh) pass without modification to test assertions.
- **SC-007**: At least one new or updated test per changed behavior area (cache change detection, refresh path decoupling, event listener throttling) is added to the test suite.
- **SC-008**: Board interactions (dragging cards, scrolling columns, opening card details) remain responsive with no user-perceptible degradation compared to the baseline.
- **SC-009**: Hot event listeners (drag, popover positioning) fire at a throttled rate, reducing callback frequency by at least 30% compared to the baseline during a standard drag interaction.
