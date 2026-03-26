# Feature Specification: Performance Review

**Feature Branch**: `001-performance-review`  
**Created**: 2026-03-26  
**Status**: Draft  
**Input**: User description: "Perform a balanced first pass focused on measurable, low-risk performance gains across backend and frontend. Start by capturing baselines and instrumentation, then fix the highest-value issues already surfaced by the codebase: backend GitHub API churn around board refreshes and polling, and frontend board responsiveness issues caused by broad query invalidation, full-list rerenders, and hot event listeners. Defer broader architectural refactors like virtualization and large service decomposition unless the first pass fails to meet targets."

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Establish Performance Baselines (Priority: P1)

As a developer working on the project board application, I need documented performance baselines for both backend and frontend behavior so that every optimization can be measured against a known starting point and regressions can be detected immediately.

**Why this priority**: Without baselines, no subsequent optimization can be proven effective. Every other user story depends on having concrete before-and-after measurements. This is the gating prerequisite for all performance work.

**Independent Test**: Can be fully tested by running the measurement procedure against the current codebase (no code changes required) and producing a baseline report that includes idle API call counts, board endpoint response cost, WebSocket/polling refresh rates, and frontend render-hot-spot identification.

**Acceptance Scenarios**:

1. **Given** an open project board in idle state (no user interaction), **When** the board is observed for a fixed five-minute interval, **Then** the total number of outbound API calls to GitHub is counted and recorded as the backend idle baseline.
2. **Given** a board endpoint request, **When** the request is served from a warm cache versus a cold cache, **Then** the response time and GitHub API call count for each case are recorded as the board-request-cost baseline.
3. **Given** an active WebSocket connection to the board, **When** no upstream data changes occur over five minutes, **Then** the number of refresh or refetch events triggered is counted and recorded as the WebSocket idle baseline.
4. **Given** a representative project board loaded in the browser, **When** the board renders with a typical number of columns and cards, **Then** the initial render time and the number of component mounts are captured as the frontend render baseline.
5. **Given** existing automated tests covering cache behavior, polling, WebSocket fallback, and board refresh, **When** those tests are executed, **Then** their current pass/fail status and timing are recorded as the regression-guardrail baseline.

---

### User Story 2 — Reduce Backend API Consumption During Idle Board Viewing (Priority: P1)

As a user with a project board open in the background, I expect the application to consume minimal GitHub API quota when nothing has changed, so that rate limits are preserved for active work and other users sharing the same token are not impacted.

**Why this priority**: Excessive idle API consumption is the highest-cost backend issue identified. It directly affects rate-limit budgets, shared token fairness, and can cause user-visible failures when limits are exhausted.

**Independent Test**: Can be tested by opening a board, leaving it idle for a fixed interval, and confirming the outbound GitHub API call count is at or below the target threshold. Automated tests validate cache behavior, change-detection logic, and polling guard conditions.

**Acceptance Scenarios**:

1. **Given** a board is open and the WebSocket connection is active with no upstream changes, **When** five minutes elapse, **Then** the system emits zero unnecessary board-data refresh calls to GitHub.
2. **Given** the board data cache is warm and the data has not changed, **When** a WebSocket subscription event fires, **Then** the system detects no change and skips the expensive board-data refetch.
3. **Given** sub-issue data has been previously fetched and cached, **When** a board refresh occurs without a manual refresh trigger, **Then** the cached sub-issue data is reused and no additional GitHub API calls are made for sub-issues.
4. **Given** the fallback polling mechanism is active (WebSocket unavailable), **When** polling fires on its regular interval, **Then** it does not trigger a full board-data refresh unless the polling response indicates actual data changes.
5. **Given** the board endpoint cache has a defined time-to-live, **When** a request arrives within the TTL window, **Then** the cached response is returned without any upstream GitHub API call.

---

### User Story 3 — Decouple Frontend Refresh Paths (Priority: P2)

As a user interacting with the project board, I expect that lightweight real-time task updates (status changes, assignment updates) arrive quickly without triggering a full board data reload, so that the board remains responsive and network usage stays low.

**Why this priority**: Broad query invalidation on every WebSocket or polling event causes unnecessary full board reloads, increasing perceived latency and wasting bandwidth. Decoupling lightweight updates from the heavy board query is the highest-leverage frontend fix.

**Independent Test**: Can be tested by triggering a lightweight task update (e.g., a task status change via WebSocket) and confirming via network inspection that only the targeted data is refetched, not the entire board dataset.

**Acceptance Scenarios**:

1. **Given** a board is displayed and a WebSocket message indicates a single task status change, **When** the message is processed, **Then** only the affected task data is updated in the UI without refetching the full board dataset.
2. **Given** fallback polling is active, **When** a polling cycle detects a lightweight change (task update, not structural board change), **Then** the system updates the affected data without invalidating the board-level query.
3. **Given** a user clicks the manual refresh button, **When** the refresh executes, **Then** the full board dataset is refetched (bypassing caches as intended) and all data is updated.
4. **Given** WebSocket updates, fallback polling, auto-refresh, and manual refresh all exist as refresh mechanisms, **When** any combination of these fires, **Then** they follow a single coherent refresh policy with no duplicated or conflicting refetch behavior.

---

### User Story 4 — Optimize Frontend Board Rendering (Priority: P2)

As a user navigating and interacting with a project board that has many columns and cards, I expect the board to feel smooth and responsive during common interactions like scrolling, dragging cards, and opening popovers, without noticeable lag or jank.

**Why this priority**: Even with optimized data fetching, excessive rerenders and unthrottled event listeners cause perceptible UI lag. These are low-risk fixes (memoization, throttling, stable props) that improve user experience without architectural changes.

**Independent Test**: Can be tested by profiling the board during common interactions (scroll, drag, popover open) and confirming that rerender counts and event-listener fire rates are reduced compared to baseline.

**Acceptance Scenarios**:

1. **Given** a board with multiple columns each containing several cards, **When** a single card is updated (e.g., status change), **Then** only the affected card and its parent column rerender, not the entire board.
2. **Given** a user is dragging a card across columns, **When** the drag is in progress, **Then** drag-related event listeners fire at a throttled rate (not on every pixel movement) and the UI remains responsive.
3. **Given** a popover (e.g., agent assignment) is open, **When** the popover position is recalculated, **Then** positioning listeners are throttled or debounced so they do not cause excessive layout recalculations.
4. **Given** board-level derived data (sorting, grouping, aggregation) is computed from raw board data, **When** the raw data has not changed, **Then** the derived data is not recomputed.

---

### User Story 5 — Verification and Regression Coverage (Priority: P3)

As a developer maintaining this codebase, I need automated tests and a manual verification procedure that confirm the performance improvements are real and that future changes do not regress the gains, so that the team has lasting confidence in the optimization work.

**Why this priority**: Optimizations without verification are assumptions. This story ensures that every improvement from Stories 2–4 is proven by automated tests and at least one manual pass, and that regression coverage prevents future degradation.

**Independent Test**: Can be tested by running the full automated test suite (backend and frontend) and performing one manual network/profile pass against a representative board, comparing results to the baselines from Story 1.

**Acceptance Scenarios**:

1. **Given** backend cache behavior changes from Story 2, **When** the backend test suite is executed, **Then** all existing cache, board, projects/WebSocket, and polling tests pass, and new or extended tests cover the change-detection and idle-refresh-prevention logic.
2. **Given** frontend refresh-path changes from Story 3, **When** the frontend test suite is executed, **Then** all existing real-time sync and board refresh tests pass, and new or extended tests cover the decoupled refresh policy.
3. **Given** all optimizations from Stories 2–4 are applied, **When** backend idle API activity is measured over a five-minute interval, **Then** the measured call count is at least 50% lower than the baseline from Story 1.
4. **Given** all optimizations from Stories 2–4 are applied, **When** a board load and interaction profile is captured, **Then** the measured rerender count for common interactions is reduced compared to the baseline from Story 1.
5. **Given** a manual end-to-end test is performed, **When** the tester verifies WebSocket updates, fallback polling safety, manual refresh cache bypass, and board interaction responsiveness, **Then** all behaviors work correctly and meet user expectations.

---

### User Story 6 — Optional Second-Wave Planning (Priority: P4)

As a technical lead, if the first-pass optimizations from Stories 2–4 do not meet the performance targets, I need a documented follow-on plan identifying the next set of structural changes to pursue, so that the team has a clear path forward without repeating analysis work.

**Why this priority**: This is explicitly out of scope for the first implementation pass. It exists only as a contingency deliverable if measurements from Story 5 show that targets are not met.

**Independent Test**: Can be tested by reviewing the follow-on plan document for completeness: it must identify specific structural changes (virtualization, service decomposition, bounded cache policies, instrumentation) with expected impact and effort estimates.

**Acceptance Scenarios**:

1. **Given** the first-pass optimizations are complete and measured, **When** backend idle API targets are still not met, **Then** a follow-on plan recommends deeper consolidation in the project fetching and polling pipeline with estimated effort.
2. **Given** the first-pass optimizations are complete and measured, **When** large board UI lag persists, **Then** a follow-on plan recommends board virtualization as the next step with estimated effort.
3. **Given** this is a first-pass performance review, **When** the first pass meets all targets, **Then** no second-wave plan is required (this story is skipped).

---

### Edge Cases

- What happens when the WebSocket connection drops mid-session? The system must fall back to polling without triggering a storm of full board refreshes.
- What happens when the cache TTL expires at the same moment a WebSocket change event arrives? The system must handle the race condition gracefully, serving fresh data without duplicate fetches.
- What happens when a user triggers a manual refresh while an auto-refresh or polling refresh is already in flight? The system must deduplicate concurrent refresh requests and ensure the manual refresh takes precedence (bypassing cache).
- What happens when a board has zero columns or zero cards? Rendering optimizations must not break on empty board states.
- What happens when the GitHub API rate limit is already exhausted? The system must gracefully degrade (serve cached data, show user-friendly messaging) rather than retrying in a tight loop.
- What happens when multiple users share the same GitHub token and one user's board is idle while another is active? Idle-board API savings must be real and not shifted to other code paths.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST capture and document backend performance baselines (idle API call count, board endpoint request cost, WebSocket/polling refresh rates) before any optimization code changes are made.
- **FR-002**: System MUST capture and document frontend performance baselines (initial board render time, component mount counts, rerender frequency during interactions) before any optimization code changes are made.
- **FR-003**: System MUST verify the current implementation state of WebSocket change detection, board cache TTL alignment, and sub-issue cache invalidation, documenting which pieces are fully landed versus partially implemented.
- **FR-004**: System MUST eliminate unnecessary board-data refresh calls to GitHub when the WebSocket subscription detects no upstream data changes.
- **FR-005**: System MUST reuse cached sub-issue data during non-manual board refreshes, avoiding redundant GitHub API calls for previously fetched sub-issues.
- **FR-006**: System MUST prevent fallback polling from triggering full board-data refreshes unless the polling response indicates actual data changes.
- **FR-007**: System MUST ensure board endpoint cache serves cached responses within the TTL window without any upstream GitHub API call.
- **FR-008**: System MUST decouple lightweight real-time task updates (status, assignment) from the expensive board-level data query, so that a single task change does not trigger a full board refetch.
- **FR-009**: System MUST ensure fallback polling updates only affected data, not the full board dataset, for lightweight changes.
- **FR-010**: System MUST ensure manual refresh bypasses all caches and refetches the complete board dataset.
- **FR-011**: System MUST enforce a single coherent refresh policy across WebSocket updates, fallback polling, auto-refresh, and manual refresh, with no duplicated or conflicting refetch behavior.
- **FR-012**: System MUST reduce unnecessary rerenders so that a single-card update only rerenders the affected card and its parent column, not the entire board.
- **FR-013**: System MUST throttle or debounce drag-related and popover-positioning event listeners to prevent excessive layout recalculations during user interactions.
- **FR-014**: System MUST avoid recomputing board-level derived data (sorting, grouping, aggregation) when the underlying raw data has not changed.
- **FR-015**: System MUST extend or adjust automated test coverage for backend cache behavior, WebSocket change detection, fallback polling, and frontend board refresh logic to serve as regression guardrails.
- **FR-016**: System MUST include at least one manual verification pass comparing post-optimization measurements to the baselines established in FR-001 and FR-002.
- **FR-017**: System MUST NOT introduce new external dependencies, board virtualization, or major service decomposition in this first pass unless baseline measurements prove lighter fixes are insufficient.

### Key Entities

- **Board Data Cache**: Represents the cached board dataset served by the backend endpoint. Attributes include cache key, time-to-live, cached payload, and timestamp of last upstream fetch. Related to board endpoint responses and sub-issue data.
- **Sub-Issue Cache**: Represents cached sub-issue data associated with board items. Attributes include parent issue reference, cached sub-issue list, and cache freshness indicator. Invalidated on manual refresh; reused on automatic refreshes.
- **Refresh Event**: Represents a trigger to update board data. Attributes include source (WebSocket, fallback polling, auto-refresh, manual refresh), scope (full board vs. targeted task), and deduplication identifier. Governs which data path is invoked.
- **Performance Baseline**: Represents a recorded measurement snapshot. Attributes include metric name, measured value, measurement timestamp, and measurement conditions. Used for before-and-after comparison and regression detection.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: An idle board (no user interaction, no upstream data changes) generates at least 50% fewer outbound API calls over a five-minute interval compared to the pre-optimization baseline.
- **SC-002**: A warm-cache board endpoint request completes without any upstream API call, returning cached data within the defined TTL window.
- **SC-003**: A single-task WebSocket update is reflected in the UI without triggering a full board data reload; network inspection shows only targeted data fetched.
- **SC-004**: Board interaction profiling (drag, scroll, popover) shows a measurable reduction in rerender counts compared to baseline, with no user-perceptible jank on representative board sizes.
- **SC-005**: All existing automated tests (backend cache, board, projects/WebSocket, polling; frontend real-time sync, board refresh) continue to pass after optimization changes.
- **SC-006**: New or extended automated tests cover the idle-refresh-prevention logic, decoupled refresh policy, and change-detection behavior, providing regression guardrails for future changes.
- **SC-007**: A manual end-to-end verification confirms that WebSocket updates arrive promptly, fallback polling does not cause unnecessary refreshes, manual refresh bypasses caches correctly, and board interactions remain responsive.
- **SC-008**: No new external dependencies are introduced and no major architectural changes (virtualization, service decomposition) are included unless post-baseline measurements explicitly justify them.

## Assumptions

- The current board endpoint already implements a 300-second cache TTL and clears sub-issue cache on manual refresh. This specification targets any remaining gaps rather than reimplementing these features.
- WebSocket change detection may be partially landed; the baseline phase (FR-003) will confirm the current state before optimization work begins.
- "Representative board size" for frontend profiling means a board with at least 5 columns and 20+ cards, reflecting typical usage. Extreme board sizes (100+ columns, 500+ cards) are deferred to the optional second-wave plan.
- Existing automated tests provide a reasonable regression baseline. The specification does not require building a new test framework, only extending or adjusting existing test files.
- Standard web application performance expectations apply: users expect sub-second visual feedback for interactions and data updates within a few seconds of upstream changes.
- The fallback polling mechanism exists for environments where WebSocket connections are unreliable. It must remain functional but should not trigger the same expensive refresh paths as real-time updates.
