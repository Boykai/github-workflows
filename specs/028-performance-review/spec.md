# Feature Specification: Performance Review — Balanced First Pass

**Feature Branch**: `028-performance-review`  
**Created**: 2026-03-08  
**Status**: Draft  
**Input**: User description: "Perform a balanced first pass focused on measurable, low-risk performance gains across backend and frontend. Start by capturing baselines and instrumentation, then fix the highest-value issues already surfaced by the codebase: backend GitHub API churn around board refreshes and polling, and frontend board responsiveness issues caused by broad query invalidation, full-list rerenders, and hot event listeners. Defer broader architectural refactors like virtualization and large service decomposition unless the first pass fails to meet targets."

## Assumptions

- The application uses GitHub APIs with a standard authenticated rate limit of 5,000 requests/hour.
- Spec 022 (API Rate Limit Protection) has been partially or fully implemented. The board endpoint already sets a 300-second cache TTL and clears sub-issue cache on manual refresh. This specification builds on that foundation and targets any remaining gaps.
- WebSocket change detection is at least partially implemented. Phase 1 will confirm exact implementation status before beginning optimization.
- The target board size for performance testing is 50–200 cards across 3–7 columns, representing a typical medium-to-large project board.
- Fallback polling is present as a degraded-mode path when WebSocket connections are unavailable.
- Board virtualization, major service decomposition, new frontend dependencies, and larger architectural rewrites are explicitly out of scope for this first pass. A follow-on phase may pursue them if first-pass measurements prove insufficient.
- Baseline measurement is mandatory before any optimization code changes so that improvements can be proven with data, not assumed.
- The existing test suites for cache, polling, WebSocket fallback, and board refresh are reusable as regression guardrails and should be extended only where directly affected by changes.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Baseline Measurement Before Any Changes (Priority: P1)

As the development team, before any optimization code changes are made, current performance baselines must be captured across both backend and frontend so that every subsequent improvement is proven with data and regressions are detected immediately.

**Why this priority**: Without baselines, there is no way to verify that optimizations are effective or that regressions have been introduced. This is a mandatory prerequisite that blocks all optimization work.

**Independent Test**: Can be verified by running a repeatable measurement protocol that records idle API call counts, board endpoint request cost, WebSocket/polling refresh behavior, board render time, and component rerender hot spots for a representative project board.

**Acceptance Scenarios**:

1. **Given** the measurement protocol is defined, **When** baseline measurements are captured, **Then** the following are recorded: idle API call count over 5 minutes, board endpoint response cost (number of outbound calls per refresh), WebSocket/polling refresh frequency, board initial render time, and rerender count for a single-card update.
2. **Given** the baseline measurement covers backend behavior, **When** the idle board is observed, **Then** repeated-refresh behavior and cache hit/miss patterns are documented.
3. **Given** the baseline measurement covers frontend behavior, **When** a board with 100+ cards is profiled, **Then** render hot spots, query invalidation patterns, and event listener frequency are documented.
4. **Given** optimization changes have been applied later, **When** the same measurement protocol is re-run, **Then** results are compared against the baselines and improvement percentages are documented.

---

### User Story 2 - Idle Board Viewing Without Excessive API Calls (Priority: P1)

As a user viewing a project board with no active changes, the system should not make unnecessary GitHub API calls in the background. Repeated identical refreshes waste rate-limit budget and can degrade or block board interactions entirely when the budget is exhausted.

**Why this priority**: Excessive idle API consumption is the highest-impact backend issue. It directly threatens rate-limit headroom for all users and is the single largest source of unnecessary API calls.

**Independent Test**: Can be verified by opening a board with no pending changes and observing network activity over 5 minutes. The count of outbound GitHub API calls should remain below a defined threshold, and no repeated unchanged refresh messages should appear.

**Acceptance Scenarios**:

1. **Given** a user is viewing an open board with no data changes, **When** 5 minutes elapse without user interaction, **Then** the system makes no more than 2 GitHub API calls during that window (excluding the initial load).
2. **Given** a board is open and WebSocket change detection reports no changes, **When** the next subscription cycle fires, **Then** no board data refresh is triggered and no refresh message is sent to the frontend.
3. **Given** a board is open and the WebSocket connection drops to fallback polling, **When** the polling cycle completes and detects no data changes, **Then** no expensive board data refresh is triggered.
4. **Given** the Spec 022 WebSocket change detection, board cache TTL alignment, and sub-issue cache invalidation targets, **When** the current backend state is audited, **Then** any still-missing pieces are identified and addressed rather than re-implementing completed items.

---

### User Story 3 - Coherent Refresh Policy Across All Update Paths (Priority: P1)

As a user collaborating on a board, when a teammate makes a change I should see the update reflected quickly. Lightweight task updates (field changes, status moves) should stay decoupled from the expensive full board data query. WebSocket updates, fallback polling, auto-refresh, and manual refresh should follow a single coherent policy and not recreate prior polling storms.

**Why this priority**: The refresh path directly determines the user's perception of real-time collaboration and is the primary source of unnecessary cascade queries that waste API budget and add latency.

**Independent Test**: Can be verified by making a single task change on one client and measuring update latency and network activity on a second client. Lightweight updates should not cause full board data re-fetches. Manual refresh should still bypass all caches.

**Acceptance Scenarios**:

1. **Given** a user is viewing a board and a collaborator updates a task field via WebSocket, **When** the update arrives, **Then** only the affected task data is refreshed and the full board data query is not invalidated.
2. **Given** a user is on fallback polling (WebSocket unavailable), **When** the polling cycle detects a lightweight task change, **Then** the system refreshes only the relevant task data without triggering a full board data re-fetch.
3. **Given** a user explicitly clicks the manual refresh button, **When** the refresh executes, **Then** all caches (including sub-issue caches) are bypassed and a complete board data fetch occurs.
4. **Given** the WebSocket connection drops and reconnects, **When** the reconnection completes, **Then** a single full refresh is performed, followed by change-detection-based updates (no cascade of redundant refreshes).

---

### User Story 4 - Responsive Board Interactions on Medium-to-Large Boards (Priority: P2)

As a user working with a board containing 50–200 cards, dragging cards, opening card details, and scrolling columns should feel responsive and smooth without visible lag or jank.

**Why this priority**: Frontend rendering cost is noticeable on medium-to-large boards and directly affects usability. While lower priority than fixing API churn (which can block functionality entirely), render responsiveness is a key quality-of-experience indicator. These are intentionally low-risk fixes.

**Independent Test**: Can be verified by profiling a board with 100+ cards: measure initial render time, drag-interaction frame rate, column scroll smoothness, and rerender counts. Compare before/after metrics against baselines.

**Acceptance Scenarios**:

1. **Given** a board with 100 cards across 5 columns is loaded, **When** the user drags a card from one column to another, **Then** the interaction completes without visible frame drops (target: ≥30 fps during drag).
2. **Given** a board with 100 cards is displayed, **When** a single card's status changes, **Then** only the affected card and its column re-render, not the entire board.
3. **Given** the user scrolls a column containing 40 cards, **When** scrolling at normal speed, **Then** the scroll interaction is smooth with no perceptible jank.
4. **Given** page-level components compute derived data (sorting, aggregation), **When** the board re-renders, **Then** derived data is not recomputed unless the underlying data has actually changed.

---

### User Story 5 - Chat and Popover Interactions Without Performance Degradation (Priority: P3)

As a user interacting with the chat popup (dragging, resizing) or agent popovers, these interactions should not cause noticeable lag due to excessive event listener activity.

**Why this priority**: While lower impact than board rendering, hot event listeners on drag and positioning logic can cause frame drops during common interactions. These are low-risk fixes with visible improvement.

**Independent Test**: Can be verified by profiling the chat drag interaction and popover open/reposition. Measure event handler invocations per second and frame rate during interaction.

**Acceptance Scenarios**:

1. **Given** the chat popup is visible, **When** the user drags it to a new position, **Then** the drag interaction maintains ≥30 fps with throttled position updates.
2. **Given** an agent popover is open, **When** the viewport is resized or scrolled, **Then** the popover repositions smoothly without triggering excessive re-renders of unrelated components.

---

### User Story 6 - Verification and Regression Coverage (Priority: P2)

As the development team, after optimization changes are applied, existing and extended test coverage must confirm that improvements are real and no regressions have been introduced.

**Why this priority**: Optimizations without verification are assumptions. Extending coverage around the changed areas ensures the improvements hold over time and future changes do not silently regress performance.

**Independent Test**: Can be verified by running the full backend and frontend test suites, confirming all pass, and performing at least one manual network/profile pass to validate the target improvements against the baselines.

**Acceptance Scenarios**:

1. **Given** optimization changes have been applied to backend cache behavior, WebSocket change detection, and fallback polling, **When** the backend test suite is run, **Then** all existing and newly added tests pass.
2. **Given** optimization changes have been applied to frontend refresh logic and render performance, **When** the frontend test suite is run, **Then** all existing and newly added tests pass.
3. **Given** the measurement protocol from Phase 1, **When** a post-optimization measurement pass is performed, **Then** improvements are confirmed against the baselines with documented before/after metrics.
4. **Given** at least one manual end-to-end check is performed, **When** WebSocket updates, fallback polling, manual refresh, and board interactions are exercised, **Then** all behave correctly and responsively.

---

### Edge Cases

- What happens when the WebSocket connection is lost and re-established during an active board session? The system must perform a single full refresh on reconnect, then resume change-detection-based updates without triggering a cascade of redundant refreshes.
- How does the system behave when the board cache TTL expires while the user is actively interacting with the board (e.g., mid-drag)? Active interactions must not be interrupted by cache expiration-triggered refreshes.
- What happens when a manual refresh is triggered while an automatic refresh is already in progress? The manual refresh must take priority and the automatic refresh must be cancelled or deduplicated.
- How does the fallback polling path behave when the backend returns identical data to the previous poll? No board refresh should be triggered if the data has not changed.
- What happens when a board has zero cards? The optimization must not introduce errors for empty board states.
- What happens when sub-issue data is partially cached (some sub-issues cached, others not)? The system must fetch only the missing sub-issues, not re-fetch all of them.
- What happens when a large number of issues change simultaneously (e.g., bulk update via GitHub)? Change detection should detect the difference and send exactly one refresh message with the updated data.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST capture and record performance baselines (idle API call count, board endpoint cost, board render time, rerender counts, WebSocket/polling refresh frequency) before any optimization code changes are applied.
- **FR-002**: System MUST confirm current backend implementation state against Spec 022 acceptance criteria (WebSocket change detection, board cache TTL alignment, sub-issue cache invalidation) before beginning optimization work, to target remaining gaps rather than redo completed items.
- **FR-003**: System MUST NOT trigger board data refreshes when WebSocket change detection reports no changes to the board data.
- **FR-004**: System MUST NOT trigger full board data refreshes during fallback polling when no data changes are detected compared to the previous poll result.
- **FR-005**: System MUST decouple lightweight task updates (field changes received via WebSocket or polling) from the expensive full board data query, refreshing only the affected task data.
- **FR-006**: System MUST ensure that WebSocket updates, fallback polling, auto-refresh, and manual refresh follow a single coherent refresh policy and do not recreate prior polling storms.
- **FR-007**: System MUST ensure manual refresh bypasses all caches (including sub-issue caches) and performs a complete board data fetch.
- **FR-008**: System MUST cache sub-issue data and serve it from cache on automatic (non-manual) board refreshes, reducing redundant sub-issue API calls.
- **FR-009**: System MUST invalidate sub-issue caches when the cache TTL expires or when a manual refresh is triggered.
- **FR-010**: System MUST ensure that only affected cards and their containing columns re-render when a single card's data changes, rather than re-rendering the entire board.
- **FR-011**: System MUST reduce repeated derived-data computation (sorting, aggregation) in board page components by stabilizing computation results across renders when the underlying data has not changed.
- **FR-012**: System MUST throttle or debounce event listeners for drag interactions (chat popup) and popover positioning to prevent per-pixel event handler execution.
- **FR-013**: System MUST ensure that WebSocket reconnection triggers a single full refresh followed by change-detection-based updates, not a cascade of redundant refreshes.
- **FR-014**: System MUST ensure that concurrent refresh requests (e.g., manual refresh during an in-progress automatic refresh) are deduplicated, with manual refresh taking priority.
- **FR-015**: System MUST maintain or extend existing test coverage for cache behavior, WebSocket change detection, fallback polling, and board refresh logic to serve as regression guardrails.
- **FR-016**: System MUST validate all optimization improvements with before/after measurements using the same repeatable measurement protocol.

### Key Entities

- **Performance Baseline**: A recorded set of metrics captured before optimization changes, including idle API call count over a fixed interval, board endpoint request cost (number of outbound calls per refresh), board initial render time, component rerender counts, and WebSocket/polling refresh frequency.
- **Board Data Cache**: Cached state of a project board including columns, cards, and metadata. Has a TTL aligned to the frontend refresh interval (300 seconds). Invalidated by manual refresh or detected data changes.
- **Sub-Issue Cache**: Per-issue cache storing sub-issue data with independent TTL. Serves cached data on automatic refreshes. Invalidated on manual refresh or TTL expiry.
- **Refresh Event**: A trigger to update board data. Has a source (WebSocket update, fallback polling, auto-refresh timer, or manual user action) and a scope (lightweight task update vs. full board refresh). All sources follow a single coherent policy.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Idle API call count for an open board with no changes is reduced by at least 50% compared to the pre-optimization baseline over a 5-minute observation window.
- **SC-002**: A single-card WebSocket update is reflected to the user within 2 seconds without triggering a full board data re-fetch.
- **SC-003**: Sub-issue data is served from cache on automatic board refreshes, reducing sub-issue-related API calls by at least 80% compared to the no-cache baseline.
- **SC-004**: Board initial render time for a 100-card board does not degrade (stays within 10% of baseline) after optimization changes.
- **SC-005**: A single-card status change on a 100-card board causes no more than 3 component re-renders (the card, its column, and the board container), rather than re-rendering all cards.
- **SC-006**: Chat popup drag interaction and popover repositioning maintain at least 30 frames per second during continuous movement.
- **SC-007**: No existing tests in the backend or frontend test suites are broken by the optimization changes.
- **SC-008**: All optimization improvements are validated with documented before/after measurements using the same repeatable measurement protocol.
- **SC-009**: Fallback polling (when WebSocket is unavailable) does not trigger full board data refreshes when the polled data is unchanged from the previous cycle.
- **SC-010**: Manual refresh continues to bypass all caches and return fully fresh data within the current expected response time (no regression).
