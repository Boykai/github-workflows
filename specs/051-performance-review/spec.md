# Feature Specification: Performance Review

**Feature Branch**: `051-performance-review`  
**Created**: 2026-03-18  
**Status**: Draft  
**Input**: User description: "Perform a balanced first pass focused on measurable, low-risk performance gains across backend and frontend."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Idle Board Does Not Waste Resources (Priority: P1)

A user opens a project board and leaves it visible without interacting. The system must not repeatedly call external services when no data has changed. The user expects their rate-limit budget to be preserved and the board to remain responsive when they return.

**Why this priority**: Unnecessary background activity is the highest-cost problem. It depletes rate-limit budget, increases server load, and produces no user value. Eliminating it is the single highest-leverage fix and blocks accurate measurement of all other improvements.

**Independent Test**: Open a board, leave it idle for five minutes, and count external service calls made during that interval. The count must stay at or below two calls per minute on average (see SC-001).

**Acceptance Scenarios**:

1. **Given** a board is open and visible with no user interaction, **When** five minutes elapse, **Then** the system makes no more than two external data-source calls per minute on average during that interval.
2. **Given** a board is open and no underlying data has changed, **When** the system's change-detection mechanism fires, **Then** no full board data refresh is triggered.
3. **Given** a board is open and new data arrives via real-time channel, **When** the change is a lightweight task update (status, assignee, label), **Then** only the affected task data is refreshed, not the full board query.

---

### User Story 2 - Board Loads and Refreshes Quickly (Priority: P1)

A user navigates to a project board or triggers a manual refresh. The board data loads promptly, leveraging cached sub-issue data when available and only bypassing caches on explicit manual refresh.

**Why this priority**: Board load time is the most visible performance metric for users. Slow loads directly degrade the user experience and are the primary complaint driving this work.

**Independent Test**: Navigate to a board with cached sub-issue data and measure time-to-interactive. Then trigger a manual refresh and confirm caches are bypassed.

**Acceptance Scenarios**:

1. **Given** a user navigates to a board with warm caches, **When** the board data loads, **Then** the system reuses cached sub-issue data and the board is interactive within at least 30% less time than the pre-optimization baseline (see SC-002).
2. **Given** a user triggers a manual refresh, **When** the refresh completes, **Then** all caches (including sub-issue caches) are cleared and fresh data is fetched.
3. **Given** a board has 50+ tasks across multiple columns, **When** the board loads, **Then** the board renders and is interactive without visible lag or jank.

---

### User Story 3 - Real-Time Updates Arrive Without Disruption (Priority: P2)

A user is viewing a board when a teammate updates a task. The change appears on the user's board promptly via the real-time channel without causing a full page refresh, scroll-position loss, or visible flicker.

**Why this priority**: Real-time sync is a core collaboration feature. If updates cause disruptive full-board refreshes or lose scroll position, users perceive the app as unreliable even when data is correct.

**Independent Test**: Have two users view the same board. One user changes a task status. Verify the other user sees the update within a few seconds without the board visually resetting.

**Acceptance Scenarios**:

1. **Given** a user is viewing a board and a teammate changes a task's status, **When** the change is delivered via real-time channel, **Then** the affected card updates in place without a full board re-render.
2. **Given** the real-time channel is unavailable and the system falls back to polling, **When** a polling cycle detects a change, **Then** only the changed data is refreshed, not the entire board query.
3. **Given** a user has scrolled to a specific column or position, **When** a real-time update arrives, **Then** the user's scroll position and any open popovers are preserved.

---

### User Story 4 - Board Interactions Feel Responsive (Priority: P2)

A user interacts with a board by dragging cards, opening popovers, or hovering over elements. These interactions respond fluidly without input lag, dropped frames, or stale visual states.

**Why this priority**: Interaction responsiveness is a key quality-of-experience factor. Even if data loads quickly, laggy drag-and-drop or slow popovers make the product feel unpolished.

**Independent Test**: On a board with 50+ cards, drag a card between columns and open a popover. Measure frame rate during the interaction. Verify no dropped frames or visible lag.

**Acceptance Scenarios**:

1. **Given** a board with 50+ cards, **When** a user drags a card between columns, **Then** the drag interaction maintains a smooth frame rate without visible jank.
2. **Given** a user opens a popover or agent selector on the board, **When** the popover renders, **Then** it appears within 100 milliseconds and repositions smoothly on scroll.
3. **Given** a board with many cards visible, **When** the user scrolls through columns, **Then** scrolling feels fluid and card content does not flicker or re-render unnecessarily.

---

### User Story 5 - Fallback Polling Remains Safe (Priority: P3)

When the real-time channel is unavailable, the system falls back to polling. This fallback must not trigger expensive full board refreshes, must not create a "polling storm," and must respect rate-limit budgets.

**Why this priority**: Fallback polling is a reliability mechanism. While it is not the primary path, it must not regress performance when activated. Historical issues with polling storms make this an important guardrail.

**Independent Test**: Disable the real-time channel and observe polling behavior for five minutes. Verify polling intervals are consistent, calls are lightweight, and no repeated expensive refreshes occur.

**Acceptance Scenarios**:

1. **Given** the real-time channel is disconnected, **When** the system activates fallback polling, **Then** polling intervals are consistent and do not escalate in frequency.
2. **Given** fallback polling is active, **When** a polling cycle finds no changes, **Then** no expensive board data refresh is triggered.
3. **Given** fallback polling is active, **When** a polling cycle detects a change, **Then** only changed data is refreshed rather than triggering a full board reload.

---

### User Story 6 - Performance Baselines Are Captured Before Changes (Priority: P1)

Before any optimization work begins, the team captures measurable baselines for backend and frontend performance. These baselines define the "before" state and provide the regression guardrails for all subsequent work.

**Why this priority**: Without baselines, there is no way to prove improvements or detect regressions. This story is a prerequisite for all optimization work and blocks Phases 2 and 3.

**Independent Test**: Run the baseline capture procedure and verify that all defined metrics are recorded with specific numeric values.

**Acceptance Scenarios**:

1. **Given** the baseline capture procedure is run, **When** an idle board is observed over a fixed interval, **Then** the number of external service calls per minute is recorded.
2. **Given** the baseline capture procedure is run, **When** a board load is profiled, **Then** time-to-interactive, number of render cycles, and network request count are recorded.
3. **Given** baselines are captured, **When** optimization work is complete, **Then** each metric can be compared against the baseline to quantify improvement or regression.

---

### Edge Cases

- What happens when the real-time channel disconnects and reconnects repeatedly in quick succession? The system must not trigger overlapping refresh storms during rapid reconnection cycles.
- What happens when a board has zero tasks? Optimizations must not break empty-board rendering or introduce errors on empty data sets.
- What happens when cached data expires while the user is actively interacting with the board? The refresh must not disrupt in-progress drag operations or unsaved state.
- What happens when multiple users trigger manual refreshes simultaneously for the same board? The system must deduplicate or throttle to avoid redundant expensive fetches.
- How does the system behave when the external data source is rate-limited or temporarily unavailable? Stale cached data should be served gracefully with appropriate user feedback rather than showing errors or blank states.
- What happens when a very large board (100+ tasks) is loaded for the first time with cold caches? The initial load must still complete within a reasonable time and not time out.

## Requirements *(mandatory)*

### Functional Requirements

#### Phase 1 — Baseline and Verification

- **FR-001**: The system MUST provide a procedure to measure idle external service call volume for an open board over a fixed interval (minimum 5 minutes).
- **FR-002**: The system MUST provide a procedure to measure board endpoint request cost including sub-issue fetch count and total response time.
- **FR-003**: The system MUST provide a procedure to profile frontend board load time-to-interactive, render cycle count, and network request volume.
- **FR-004**: The system MUST verify current implementation state against existing rate-limit protection targets: idle external service calls at or below two per minute, board cache TTL of 300 seconds, and sub-issue cache invalidation on manual refresh.

#### Phase 2 — Backend Optimization

- **FR-005**: The system MUST implement change detection in the real-time subscription flow so that a full board refresh is only triggered when actual data changes are detected.
- **FR-006**: The system MUST reuse cached sub-issue data during board refreshes unless the user explicitly triggers a manual refresh.
- **FR-007**: The system MUST ensure that fallback polling does not trigger expensive full board data refreshes when no changes are detected.
- **FR-008**: The system MUST consolidate duplicated repository-resolution logic into a single shared path to eliminate redundant external calls.
- **FR-009**: The system MUST ensure that idle board viewing (no user interaction, no data changes) produces no more than two external service calls per minute on average.

#### Phase 2 — Frontend Refresh-Path Optimization

- **FR-010**: The system MUST decouple lightweight task updates (status, assignee, label changes) from the full board data query in the real-time update path.
- **FR-011**: The system MUST ensure that real-time channel updates, fallback polling, auto-refresh, and manual refresh follow a single coherent refresh policy.
- **FR-012**: The system MUST preserve user scroll position and open UI elements (popovers, modals) when real-time updates arrive.
- **FR-013**: The system MUST ensure that manual refresh bypasses all caches and fetches fresh data, while auto-refresh and real-time updates use cached data where valid.

#### Phase 3 — Frontend Render Optimization

- **FR-014**: The system MUST eliminate redundant derived-data recalculations (sorting, filtering, aggregation) in board page components during re-renders that do not change the source data.
- **FR-015**: The system MUST stabilize component identity for board columns and cards so that unchanged items are not re-rendered when sibling items update.
- **FR-016**: The system MUST throttle high-frequency event listeners (drag positioning, popover repositioning) to fire no more frequently than once per animation frame.

#### Phase 3 — Verification and Regression

- **FR-017**: The system MUST include automated test coverage for backend cache behavior, change detection, fallback polling safety, and board refresh deduplication.
- **FR-018**: The system MUST include automated test coverage for frontend real-time sync, board refresh hooks, and query invalidation behavior.
- **FR-019**: The system MUST pass a manual end-to-end verification confirming real-time updates, fallback polling, manual refresh, and board interaction responsiveness.

### Scope Boundaries

**In scope for first pass:**
- Performance baseline capture and measurement procedures
- Backend idle API call reduction and change-detection fixes
- Backend sub-issue cache reuse and refresh deduplication
- Frontend refresh-path cleanup (decouple task updates from board query)
- Frontend low-risk render optimizations (memoization, prop stabilization, listener throttling)
- Regression test coverage for changed behavior

**Explicitly out of scope for first pass (deferred to Phase 4 if needed):**
- Board virtualization (rendering only visible cards/columns)
- Major service decomposition or architectural restructuring
- Adding new external dependencies
- Request-budget instrumentation or structured performance logging
- Broader caching architecture changes beyond the existing rate-limit protection targets (≤2 idle calls/min, 300s board cache TTL, manual-refresh sub-issue invalidation)

### Key Entities

- **Board**: A project board containing columns and task cards. The primary data unit for refresh, caching, and rendering optimization.
- **Task Card**: An individual work item displayed on the board. Subject to real-time updates and the primary unit for granular refresh.
- **Sub-Issue Cache**: Cached sub-issue data associated with board tasks. Reused during non-manual refreshes to reduce external call volume.
- **Refresh Policy**: The rules governing when and how board data is refreshed across four triggers: real-time updates, fallback polling, auto-refresh timers, and manual user refresh.
- **Performance Baseline**: A set of recorded metrics captured before optimization work, used as the comparison point for measuring improvements and detecting regressions.

## Assumptions

- The existing rate-limit protection implementation has partially landed (300-second cache TTL and manual-refresh sub-issue cache clearing are already in place). This specification targets remaining gaps rather than reimplementing completed work.
- The real-time channel (WebSocket) is the primary update path; fallback polling is activated only when the real-time channel is unavailable.
- "Expensive board refresh" refers to a full re-fetch of all board data including sub-issues from the external data source, as opposed to a lightweight task-level update.
- Representative board size for testing is 50–100 tasks across 4–6 columns, which reflects typical usage. Boards with 100+ tasks are considered edge cases for the first pass.
- The system already has automated test infrastructure for both backend and frontend that can be extended without introducing new test frameworks.
- Rate-limit budget constraints are defined by the external data source (GitHub API) and are not configurable by the application. The optimization target is to minimize consumption, not to change limits.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Idle board external service call volume is reduced by at least 50% compared to the pre-optimization baseline, and remains at or below two calls per minute on average.
- **SC-002**: Board load time-to-interactive with warm caches improves by at least 30% compared to the pre-optimization baseline.
- **SC-003**: Sub-issue cache reuse reduces the number of external sub-issue fetch calls by at least 40% during non-manual board refreshes compared to the baseline.
- **SC-004**: Real-time task updates (status, assignee, label) are reflected on the board within 3 seconds without triggering a full board data refresh.
- **SC-005**: Fallback polling, when active, produces no more than one lightweight check per polling interval and never triggers an expensive full board refresh unless actual changes are detected.
- **SC-006**: Board interactions (drag-and-drop, popover open/close, scrolling) maintain a frame rate of at least 30 frames per second on a board with 50+ cards.
- **SC-007**: All existing automated tests continue to pass after optimization changes, and new regression tests are added covering cache behavior, change detection, refresh policy, and polling safety.
- **SC-008**: A manual end-to-end verification confirms that real-time updates work, fallback polling is safe, manual refresh bypasses caches, and board interactions are responsive.
