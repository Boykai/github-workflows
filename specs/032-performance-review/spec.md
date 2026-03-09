# Feature Specification: Performance Review

**Feature Branch**: `032-performance-review`  
**Created**: 2026-03-09  
**Status**: Draft  
**Input**: User description: "Perform a balanced first pass focused on measurable, low-risk performance gains across backend and frontend. Start by capturing baselines and instrumentation, then fix the highest-value issues already surfaced by the codebase: backend GitHub API churn around board refreshes and polling, and frontend board responsiveness issues caused by broad query invalidation, full-list rerenders, and hot event listeners. Defer broader architectural refactors like virtualization and large service decomposition unless the first pass fails to meet targets."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Baseline Performance Measurement (Priority: P1)

As the development team, before any optimization changes are made, current performance baselines must be captured across both backend and frontend so that improvements can be proven with data and regressions can be detected immediately.

**Why this priority**: Without baselines, no optimization can be verified as effective, and there is no safety net against regressions. This is a mandatory prerequisite that blocks all other optimization work.

**Independent Test**: Can be verified by executing a repeatable measurement protocol that records idle API call count, board endpoint response time, board render time, and component rerender counts, then confirming the results are documented and reproducible.

**Acceptance Scenarios**:

1. **Given** the measurement protocol is defined, **When** baseline measurements are captured for the backend, **Then** the following are recorded: idle API call count over a 5-minute window for an open board, board endpoint response time, and sub-issue fetch count per board refresh.
2. **Given** the measurement protocol is defined, **When** baseline measurements are captured for the frontend, **Then** the following are recorded: board initial render time for a representative project, rerender count for a single-card update, and event handler invocation frequency during drag interactions.
3. **Given** baseline measurements are captured, **When** optimization changes are applied, **Then** the same protocol is re-run and before/after comparisons are documented with improvement percentages.

---

### User Story 2 - Idle Board Viewing Without Excessive API Calls (Priority: P1)

As a user viewing a project board that has no active changes, the system should not make unnecessary API calls in the background. Repeated identical refreshes waste rate-limit budget and can degrade or block subsequent intentional actions when the budget is exhausted.

**Why this priority**: Excessive idle API consumption is the highest-impact backend issue. It directly affects rate-limit headroom for all users and is the single largest source of avoidable cost.

**Independent Test**: Can be verified by opening a board with no pending changes and observing outbound API activity over a fixed interval (e.g., 5 minutes). The count of outbound API calls should remain below a defined threshold.

**Acceptance Scenarios**:

1. **Given** a user is viewing an open board with no data changes, **When** 5 minutes elapse without any user interaction, **Then** the system makes no more than 2 outbound API calls during that window (excluding the initial load).
2. **Given** a board is open and change detection reports no changes, **When** the next refresh cycle fires, **Then** no board data refresh is triggered.
3. **Given** a board is open and the real-time connection drops to fallback polling, **When** the polling cycle completes and detects no data changes, **Then** no expensive board data refresh is triggered.

---

### User Story 3 - Fast and Coherent Board Refresh on Real-Time Updates (Priority: P1)

As a user collaborating on a board, when a teammate makes a change (e.g., moves a card, updates a status), the update should appear quickly without triggering a full board reload or a cascade of redundant queries.

**Why this priority**: The refresh path directly determines the user's perception of real-time collaboration. If lightweight task updates trigger expensive full-board queries, users experience unnecessary latency and API waste simultaneously.

**Independent Test**: Can be verified by making a single task change on one client and measuring update latency and network activity on a second client. Lightweight updates should not cause full board data re-fetches.

**Acceptance Scenarios**:

1. **Given** a user is viewing a board and a collaborator updates a task field via a real-time channel, **When** the update arrives, **Then** only the affected task data is refreshed and the full board query is not invalidated.
2. **Given** a user is on fallback polling (real-time connection unavailable), **When** the polling cycle detects a lightweight task change, **Then** the system refreshes only the relevant task data without re-fetching the entire board.
3. **Given** a user explicitly clicks the manual refresh button, **When** the refresh executes, **Then** all caches (including sub-issue caches) are bypassed and a full board data fetch occurs.

---

### User Story 4 - Sub-Issue Cache Reduces Redundant Fetches (Priority: P2)

As a user viewing a board with cards that have sub-issues, the system should reuse cached sub-issue data across multiple board refreshes instead of re-fetching sub-issues on every board load.

**Why this priority**: Sub-issue fetching can multiply the API call count for board refreshes significantly. Caching sub-issue data materially reduces per-refresh cost and is a high-value, low-risk optimization.

**Independent Test**: Can be verified by loading a board with sub-issues, observing the initial sub-issue API call count, then triggering an automatic refresh and confirming that warm sub-issue cache eliminates redundant calls.

**Acceptance Scenarios**:

1. **Given** a board is loaded with cards containing sub-issues, **When** an automatic (non-manual) board refresh occurs, **Then** sub-issue data is served from cache and no additional sub-issue API calls are made.
2. **Given** a user clicks the manual refresh button, **When** the board reloads, **Then** sub-issue caches are invalidated and fresh sub-issue data is fetched.
3. **Given** sub-issue cache entries exist, **When** the cache TTL expires, **Then** subsequent board refreshes fetch fresh sub-issue data.
4. **Given** sub-issue data is partially cached (some sub-issues cached, others not), **When** a board refresh occurs, **Then** the system fetches only the missing sub-issues, not all of them.

---

### User Story 5 - Responsive Board Interactions on Medium-to-Large Boards (Priority: P2)

As a user working with a board containing 50–200 cards, dragging cards, opening card details, and scrolling columns should feel responsive and smooth without visible lag or jank.

**Why this priority**: Frontend rendering cost is noticeable on medium-to-large boards and directly affects usability. While lower priority than fixing API churn (which can block functionality entirely), render responsiveness is a key quality-of-experience indicator.

**Independent Test**: Can be verified by profiling a board with 100+ cards: measure initial render time, drag-interaction frame rate, and column scroll smoothness. Compare before/after metrics.

**Acceptance Scenarios**:

1. **Given** a board with 100 cards across 5 columns is loaded, **When** the user drags a card from one column to another, **Then** the interaction completes without visible frame drops (target: ≥30 fps during drag).
2. **Given** a board with 100 cards is displayed, **When** a single card's status changes, **Then** only the affected card and its containing column re-render, not the entire board.
3. **Given** the user scrolls a column containing 40 cards, **When** scrolling at normal speed, **Then** the scroll interaction is smooth with no perceptible jank.

---

### User Story 6 - Chat and Popover Interactions Without Performance Degradation (Priority: P3)

As a user interacting with the chat popup (dragging, resizing) or agent popovers, these interactions should not cause noticeable lag due to excessive event listener activity.

**Why this priority**: While lower impact than board rendering, hot event listeners on drag and positioning logic can cause frame drops during common interactions. These are low-risk fixes with visible improvement.

**Independent Test**: Can be verified by profiling the chat drag interaction and popover open/reposition. Measure event handler invocations per second and frame rate during interaction.

**Acceptance Scenarios**:

1. **Given** the chat popup is visible, **When** the user drags it to a new position, **Then** the drag interaction maintains ≥30 fps with throttled position updates (no per-pixel event handler execution).
2. **Given** an agent popover is open, **When** the viewport is resized or scrolled, **Then** the popover repositions smoothly without triggering excessive re-renders of unrelated components.

---

### User Story 7 - Regression-Safe Optimization with Test Coverage (Priority: P2)

As the development team, optimization changes must not break existing functionality. Existing tests must continue to pass, and coverage must be extended where optimization changes introduce new behavior.

**Why this priority**: Without regression guardrails, optimization changes risk introducing subtle bugs that are harder to detect than the performance issues they fix.

**Independent Test**: Can be verified by running the full backend and frontend test suites before and after optimization changes and confirming all existing tests pass, with new tests added for changed behavior.

**Acceptance Scenarios**:

1. **Given** optimization changes have been applied, **When** the existing backend test suite is run, **Then** all tests pass without modification.
2. **Given** optimization changes have been applied, **When** the existing frontend test suite is run, **Then** all tests pass without modification.
3. **Given** new cache behavior or refresh logic has been introduced, **When** the new behavior is reviewed, **Then** corresponding tests exist that validate the new behavior and can catch regressions.

---

### Edge Cases

- What happens when the real-time connection is lost and re-established during an active board session? The system must not trigger a cascade of redundant board refreshes on reconnection.
- How does the system behave when the board cache TTL expires while the user is actively interacting with the board? Active interactions must not be interrupted by cache expiration-triggered refreshes.
- What happens when a manual refresh is triggered while an automatic refresh is already in progress? The manual refresh must take priority and the automatic refresh must be cancelled or deduplicated.
- How does the fallback polling path behave when the backend returns identical data to the previous poll? No board refresh should be triggered if the data has not changed.
- What happens when a board has zero cards? The optimization must not introduce errors for empty board states.
- What happens when sub-issue data is partially cached (some sub-issues cached, others not)? The system must fetch only the missing sub-issues, not refetch all of them.
- What happens when multiple users are concurrently editing the same board? Real-time updates from all users must be reflected without compounding into redundant refresh storms.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST capture and record performance baselines (idle API call count, board endpoint cost, render times, rerender counts) before any optimization code changes are applied.
- **FR-002**: System MUST verify current backend implementation state against Spec 022 acceptance criteria before beginning optimization work, to avoid redoing already-completed items.
- **FR-003**: System MUST NOT trigger board data refreshes when change detection reports no changes to the board data.
- **FR-004**: System MUST NOT trigger full board data refreshes during fallback polling when no data changes are detected compared to the previous poll result.
- **FR-005**: System MUST decouple lightweight task updates (field changes received via real-time channels or polling) from the expensive full board data query, refreshing only the affected task data.
- **FR-006**: System MUST ensure manual refresh bypasses all caches (including sub-issue caches) and performs a complete board data fetch.
- **FR-007**: System MUST cache sub-issue data and serve it from cache on automatic (non-manual) board refreshes, reducing redundant sub-issue API calls.
- **FR-008**: System MUST invalidate sub-issue caches when the cache TTL expires or when a manual refresh is triggered.
- **FR-009**: System MUST ensure that only affected cards and their containing columns re-render when a single card's data changes, rather than re-rendering the entire board.
- **FR-010**: System MUST reduce repeated derived-data computation (sorting, aggregation) in board page components by stabilizing computation results across renders.
- **FR-011**: System MUST throttle or debounce event listeners for drag interactions (chat popup) and popover positioning to prevent per-pixel event handler execution.
- **FR-012**: System MUST ensure that real-time connection reconnection does not trigger a cascade of redundant board refreshes.
- **FR-013**: System MUST ensure that concurrent refresh requests (e.g., manual refresh during an in-progress automatic refresh) are deduplicated, with manual refresh taking priority.
- **FR-014**: System MUST maintain or extend existing test coverage for cache behavior, change detection, fallback polling, and board refresh logic to serve as regression guardrails.
- **FR-015**: System MUST ensure all refresh sources (real-time updates, fallback polling, auto-refresh, manual refresh) follow a single coherent refresh policy and do not produce compounding refresh storms.

### Key Entities

- **Board Data Cache**: Represents the cached state of a project board, including its columns, cards, and metadata. Has a TTL (currently 300 seconds) and can be invalidated by manual refresh or data changes.
- **Sub-Issue Cache**: Represents cached sub-issue data associated with board cards. Has its own TTL and is invalidated on manual refresh or TTL expiry. Reduces per-refresh API call count.
- **Refresh Event**: Represents a trigger to update board data. Has a source (real-time update, fallback polling, auto-refresh timer, or manual user action) and a scope (lightweight task update vs. full board refresh).
- **Performance Baseline**: A recorded set of metrics captured before optimization changes, including idle API call count, board endpoint response time, board render time, and component rerender counts.

## Assumptions

- The current board endpoint already implements a 300-second cache TTL and clears sub-issue cache on manual refresh, as noted in the issue context. Optimization work builds on this existing foundation rather than reimplementing it.
- Change detection for real-time updates is at least partially implemented (per Spec 022). The first phase will confirm exactly what is implemented vs. what remains.
- The target board size for performance testing is 50–200 cards across 3–7 columns, which represents a typical medium-to-large project board.
- Rate-limit budget improvements are measured against the idle scenario (board open with no active changes) as the primary indicator, since this represents the largest avoidable waste.
- Fallback polling is already present as a degraded-mode path when real-time connections fail. Optimization focuses on making this path cheaper, not replacing it.
- Board virtualization, major service decomposition, and new frontend dependencies are explicitly out of scope for this first pass. They may be pursued in a follow-on phase only if measurements prove the lighter optimizations are insufficient.
- The existing test suites for cache, polling, real-time fallback, and board refresh provide adequate coverage to serve as regression guardrails. Test extension is limited to areas directly affected by the optimization changes.
- If the first pass still leaves material UI lag on large boards or excessive backend complexity, a follow-on plan will be prepared for structural changes (virtualization, deeper service decomposition, bounded cache policies, stronger instrumentation).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Idle API call count for an open board with no changes is reduced by at least 50% compared to the pre-optimization baseline over a 5-minute observation window.
- **SC-002**: Board refresh triggered by a single-card real-time update completes in under 1 second as perceived by the user, without triggering a full board data re-fetch.
- **SC-003**: Sub-issue data is served from cache on automatic board refreshes, reducing sub-issue-related API calls by at least 80% compared to the no-cache baseline.
- **SC-004**: Board initial render time for a 100-card board is not degraded (stays within 10% of baseline) after optimization changes.
- **SC-005**: A single-card status change on a 100-card board causes no more than 3 component re-renders (the card, its column, and the board container), rather than re-rendering all cards.
- **SC-006**: Chat popup drag interaction maintains at least 30 frames per second during continuous drag movement.
- **SC-007**: No existing tests in the backend or frontend test suites are broken by the optimization changes.
- **SC-008**: All optimization improvements are validated with before/after measurements using the same repeatable measurement protocol.
- **SC-009**: Fallback polling (when real-time connection is unavailable) does not trigger full board data refreshes when the polled data is unchanged from the previous cycle.
- **SC-010**: Manual refresh continues to bypass all caches and return fully fresh data within the current expected response time (no regression).
