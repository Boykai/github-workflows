# Feature Specification: Performance Review

**Feature Branch**: `056-performance-review`
**Created**: 2026-03-21
**Status**: Draft
**Input**: User description: "Perform a balanced first pass focused on measurable, low-risk performance gains across backend and frontend. Start by capturing baselines and instrumentation, then fix the highest-value issues already surfaced by the codebase: backend GitHub API churn around board refreshes and polling, and frontend board responsiveness issues caused by broad query invalidation, full-list rerenders, and hot event listeners. Defer broader architectural refactors like virtualization and large service decomposition unless the first pass fails to meet targets."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Establish Performance Baselines Before Changes (Priority: P1)

As a development team, we need to capture current backend and frontend performance baselines before making any behavioral changes, so that every optimization can be measured against a known starting point and regressions are caught immediately.

**Why this priority**: Without baselines, improvements cannot be proven — they are only assumed. Every subsequent optimization depends on having reliable before/after comparisons. This story blocks all other work.

**Independent Test**: Can be fully tested by running the baseline measurement process on the current system and verifying that all key metrics are captured and recorded. Delivers a measurement checklist that serves as the foundation for all optimization validation.

**Acceptance Scenarios**:

1. **Given** a user has a board open and is not interacting with it, **When** the baseline measurement process runs for a fixed interval (e.g., 5 minutes), **Then** the total number of backend API calls made during idle viewing is recorded as a baseline metric.
2. **Given** a board endpoint is requested, **When** the baseline measurement captures the request, **Then** the request cost (response time, payload size, and downstream API calls triggered) is recorded.
3. **Given** the system uses real-time updates or polling fallback, **When** the baseline measurement runs, **Then** the frequency and type of refresh events (real-time messages, polling requests, query invalidations) are recorded.
4. **Given** a board with a representative number of tasks is loaded, **When** the frontend is profiled, **Then** render hot spots (components rerendering most frequently, event listener fire rates) are identified and documented.
5. **Given** existing automated tests cover cache behavior, polling, real-time update fallback, and board refresh, **When** the baseline is established, **Then** those test results are captured as the "before" reference for the regression checklist.

---

### User Story 2 - Reduce Idle Backend API Consumption (Priority: P1)

As a user viewing a project board without making changes, the system should not waste API budget by repeatedly refreshing data that has not changed, so that rate limits are preserved for intentional actions and the system remains responsive under load.

**Why this priority**: Unnecessary API calls during idle viewing are the highest-cost waste identified in the codebase. Reducing them directly protects the shared API rate limit budget and improves reliability for all users.

**Independent Test**: Can be fully tested by opening a board, leaving it idle for a measured interval, and counting the API calls made. Compare against the baseline to verify reduction. Delivers immediate API budget savings.

**Acceptance Scenarios**:

1. **Given** a user has a board open and no data has changed on the server, **When** the system checks for updates via its real-time channel, **Then** no redundant refresh requests are sent to the upstream API.
2. **Given** a board's cached data is still within its validity window, **When** the system receives a check for updates, **Then** the cached data is served without triggering a new upstream API call.
3. **Given** sub-issue data was previously fetched for a board, **When** the board data is refreshed and sub-issue data has not changed, **Then** the cached sub-issue data is reused rather than re-fetched.
4. **Given** the system is using a polling fallback instead of real-time updates, **When** a poll cycle runs, **Then** it does not trigger an expensive full board data refresh unless data has actually changed.
5. **Given** the system resolves repository information for API calls, **When** the resolution has already been performed recently, **Then** the previously resolved result is reused rather than duplicated.

---

### User Story 3 - Coherent Frontend Refresh Policy (Priority: P2)

As a user, when task data updates arrive (via real-time channel or polling), the board should update the affected tasks without triggering a full expensive board data reload, so that the interface stays current without unnecessary delays or visual disruption.

**Why this priority**: Broad query invalidation on every lightweight update causes unnecessary full-board reloads, which compound with backend API churn. Fixing the refresh policy reduces both frontend lag and backend load, but depends on the backend idle API fixes being in place first.

**Independent Test**: Can be fully tested by triggering a lightweight task update (e.g., status change) while monitoring network activity and confirming that only the affected data is refetched, not the entire board query. Delivers faster, less disruptive updates.

**Acceptance Scenarios**:

1. **Given** a user is viewing a board and a single task is updated via real-time channel, **When** the update arrives, **Then** only the affected task data is refreshed — the full board data query is not re-executed.
2. **Given** the real-time channel is unavailable and the system falls back to polling, **When** a poll cycle detects changes, **Then** the fallback refresh follows the same lightweight update policy as the real-time path.
3. **Given** a user manually triggers a board refresh, **When** the refresh executes, **Then** a full board data reload is performed (bypassing caches as intended).
4. **Given** multiple refresh sources exist (real-time updates, polling fallback, auto-refresh timer, manual refresh), **When** any of these sources trigger, **Then** they follow a single coherent refresh policy without conflicting or duplicating each other.
5. **Given** the real-time channel reconnects after a disconnection, **When** the reconnection occurs, **Then** a single catch-up refresh is performed rather than a storm of queued refreshes.

---

### User Story 4 - Responsive Board Interactions (Priority: P2)

As a user interacting with a project board (browsing columns, dragging tasks, opening popovers), the interface should feel responsive and smooth, without noticeable lag from unnecessary rerendering or excessive event processing.

**Why this priority**: Board responsiveness directly affects user satisfaction. Low-risk rendering improvements (reducing unnecessary recalculations, stabilizing component updates, and throttling high-frequency event listeners) can deliver noticeable gains without architectural risk.

**Independent Test**: Can be fully tested by interacting with a board of representative size (browsing, dragging, hovering) and profiling render counts and event listener fire rates. Compare against baseline to verify improvement. Delivers a smoother user experience.

**Acceptance Scenarios**:

1. **Given** a board with multiple columns and tasks is displayed, **When** the user scrolls or browses between columns, **Then** only visible or affected columns and cards rerender — unchanged items remain stable.
2. **Given** a user drags a task card across the board, **When** the drag interaction is in progress, **Then** positioning and layout updates are throttled to avoid excessive event processing without introducing visible stutter.
3. **Given** a page component derives sorted or aggregated data from the board state, **When** the underlying data has not changed, **Then** the derived computation is not repeated on every render cycle.
4. **Given** a popover or overlay is positioned relative to a board element, **When** the positioning listener fires, **Then** updates are throttled or debounced so that repositioning does not cause cascading rerenders.
5. **Given** a board of representative size is loaded, **When** interaction responsiveness is measured against the baseline, **Then** there is a measurable reduction in unnecessary rerenders and event listener invocations.

---

### User Story 5 - Verification and Regression Coverage (Priority: P3)

As a development team, after applying optimizations, we need to verify that improvements are real (not inferred) and that existing behavior has not regressed, so that the changes can be shipped with confidence.

**Why this priority**: Without verification, optimizations might not achieve their goals or could introduce subtle regressions. This story depends on the optimization work being complete, making it naturally lower priority in sequencing.

**Independent Test**: Can be fully tested by running the full automated test suite, repeating the baseline measurements, and performing a manual network and profile pass. Delivers proof that the optimizations achieved their targets.

**Acceptance Scenarios**:

1. **Given** backend optimizations have been applied, **When** the backend automated test suite runs (covering cache behavior, board endpoints, real-time subscriptions, and polling logic), **Then** all existing tests pass and new coverage for the optimization changes is included.
2. **Given** frontend optimizations have been applied, **When** the frontend automated test suite runs (covering real-time sync, board refresh hooks, and render behavior), **Then** all existing tests pass and new coverage for the optimization changes is included.
3. **Given** all optimizations are applied, **When** the baseline measurements are repeated, **Then** the results show measurable improvement against the original baselines for idle API calls, refresh event frequency, and rerender counts.
4. **Given** all optimizations are applied, **When** a manual end-to-end check is performed, **Then** real-time updates refresh task data quickly, polling fallback remains safe, manual refresh still bypasses caches, and board interactions remain responsive.

---

### User Story 6 - Second-Wave Planning Guidance (Priority: P3)

As a development team, if the first-pass optimizations do not meet performance targets, we need a clear follow-on plan for deeper structural changes, so that the next round of work is scoped and justified by data rather than speculation.

**Why this priority**: This story is explicitly out of scope for implementation unless measurements prove it necessary. Its value is in providing a documented path forward rather than immediate code changes.

**Independent Test**: Can be fully tested by reviewing the documented plan after first-pass measurements are complete. If targets are met, this story is satisfied by its existence as a reference. If targets are not met, the plan provides actionable next steps. Delivers decision-making guidance for future work.

**Acceptance Scenarios**:

1. **Given** first-pass optimizations have been applied and measured, **When** board responsiveness on large boards still does not meet targets, **Then** a documented recommendation exists for board virtualization as the next step.
2. **Given** first-pass optimizations have been applied and measured, **When** backend API consumption still exceeds acceptable levels, **Then** a documented recommendation exists for deeper service consolidation as the next step.
3. **Given** the team expects ongoing performance work, **When** planning future iterations, **Then** a recommendation exists for adding lightweight instrumentation around refresh cost, cache hit rates, and refresh-source attribution.

---

### Edge Cases

- What happens when the real-time channel disconnects and reconnects multiple times in rapid succession? The system should coalesce reconnection refreshes into a single catch-up rather than queuing a burst.
- How does the system behave when cached data expires during an active user session? It should refresh transparently without disrupting the user's current interaction (e.g., an open modal or in-progress drag).
- What happens when a manual refresh is triggered while an automatic refresh is already in progress? The manual refresh should take precedence, and the automatic refresh should be cancelled or its result discarded.
- How does the system handle boards with zero tasks? Optimizations should not introduce errors on empty boards.
- What happens when the upstream API is temporarily unavailable? The system should serve stale cached data with an appropriate indicator rather than showing an error or empty state.
- What if a user switches between multiple boards rapidly? In-flight requests for the previous board should be cancelled and not applied to the current view.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST capture and record backend performance baselines (idle API call count, request cost, refresh event frequency) before any optimization changes are applied.
- **FR-002**: System MUST capture and record frontend performance baselines (render hot spots, event listener fire rates, query invalidation frequency) before any optimization changes are applied.
- **FR-003**: System MUST NOT send redundant upstream API refresh requests when board data has not changed during idle viewing.
- **FR-004**: System MUST reuse cached board data within its validity window instead of triggering new upstream API calls.
- **FR-005**: System MUST reuse previously fetched sub-issue data when it has not changed, rather than re-fetching on every board refresh.
- **FR-006**: System MUST ensure that polling fallback does not trigger expensive full board data refreshes when no data has changed.
- **FR-007**: System MUST ensure that repository resolution results are reused rather than duplicated across API call paths.
- **FR-008**: System MUST decouple lightweight task updates (via real-time channel or polling) from full board data query re-execution.
- **FR-009**: System MUST ensure manual refresh triggers a full board data reload that bypasses caches.
- **FR-010**: System MUST enforce a single coherent refresh policy across all refresh sources (real-time updates, polling fallback, auto-refresh, manual refresh).
- **FR-011**: System MUST reduce unnecessary component rerenders on the board when underlying data has not changed.
- **FR-012**: System MUST throttle or debounce high-frequency event listeners (drag positioning, popover repositioning) to avoid excessive processing.
- **FR-013**: System MUST avoid repeating derived-data computations (sorting, aggregation) when the source data has not changed.
- **FR-014**: System MUST extend or adjust automated test coverage to verify cache behavior, change detection, polling safety, and refresh logic after optimizations.
- **FR-015**: System MUST produce before/after measurement comparisons demonstrating that optimizations achieved measurable improvement.

### Assumptions

- The existing board endpoint already sets a 300-second cache TTL and clears sub-issue cache on manual refresh. This work builds on that foundation rather than reimplementing it.
- The existing real-time update channel and polling fallback are already functional. This work optimizes their refresh behavior, not their connection management.
- A "representative board size" for profiling is defined as a project with at least 5 columns and 50+ tasks, reflecting typical production usage.
- Performance targets for idle API reduction and render optimization will be derived from baseline measurements rather than set as absolute numbers upfront.
- The first pass intentionally avoids introducing new dependencies, board virtualization, or major service decomposition unless baseline results prove lighter fixes insufficient.
- Data retention, error handling, and authentication follow existing system patterns and do not need new policies for this feature.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Idle board viewing produces at least 50% fewer upstream API calls compared to the baseline measurement over the same time interval.
- **SC-002**: Board data refreshes with warm sub-issue caches complete with measurably fewer downstream API calls than cold refreshes.
- **SC-003**: Polling fallback does not trigger full board data refreshes when no upstream data has changed, verified by network activity inspection.
- **SC-004**: Lightweight task updates (status changes, field edits) refresh the affected data without re-executing the full board data query, verified by network and render profiling.
- **SC-005**: Board interaction responsiveness (browsing, dragging, popover positioning) shows a measurable reduction in unnecessary rerenders compared to the baseline profile.
- **SC-006**: All existing automated tests continue to pass after optimizations, with additional coverage for the changed cache, polling, refresh, and render behaviors.
- **SC-007**: At least one manual end-to-end verification confirms that real-time updates arrive promptly, polling fallback is safe, manual refresh bypasses caches, and board interactions feel responsive.
- **SC-008**: Users experience no visible regression in board functionality — all task operations, board navigation, and refresh behaviors work as before.
