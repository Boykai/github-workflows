# Feature Specification: Performance Review

**Feature Branch**: `039-performance-review`  
**Created**: 2026-03-13  
**Status**: Draft  
**Input**: User description: "Perform a balanced first pass focused on measurable, low-risk performance gains across backend and frontend."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Establish Performance Baselines (Priority: P1)

As a developer, I need to capture current backend and frontend performance baselines before making any optimization changes, so that I can measure improvements objectively and detect regressions.

**Why this priority**: Without baselines, no optimization can be proven effective. This story blocks all other work because success criteria and regression guardrails depend on measured before/after comparisons.

**Independent Test**: Can be fully tested by running baseline measurements on a representative board (idle API call count over a fixed interval, board load time, render profiling, network activity inspection) and recording results in a structured format. Delivers a measurement framework that prevents blind optimization.

**Acceptance Scenarios**:

1. **Given** an open board with no user interaction, **When** idle activity is measured over a 5-minute window, **Then** the number of outbound API calls and their endpoints are recorded as the backend baseline.
2. **Given** a board with a representative number of tasks (20+ items across multiple columns), **When** the board is loaded and interactions are profiled, **Then** render times, rerender counts, and network request volume are recorded as the frontend baseline.
3. **Given** existing automated tests for cache, polling, WebSocket fallback, and board refresh behavior, **When** baseline measurement is complete, **Then** a before/after checklist is defined that maps each test area to its target improvement.

---

### User Story 2 - Reduce Backend API Consumption During Idle Board Viewing (Priority: P1)

As a user viewing a project board, I expect that the application does not make unnecessary or repeated API calls to GitHub when nothing has changed, so that the system stays within rate limits and responds quickly when I do interact.

**Why this priority**: Excessive idle API consumption is the highest-value backend issue. It wastes rate-limit budget, adds latency, and can cause service degradation for all users. Fixing this directly improves reliability and cost.

**Independent Test**: Can be fully tested by opening a board, leaving it idle, and verifying that no repeated unchanged refresh calls are sent over a measured interval. Delivers immediate rate-limit savings and reduced backend load.

**Acceptance Scenarios**:

1. **Given** an open board with WebSocket connected and no data changes, **When** the board is idle for 5 minutes, **Then** no repeated board refresh API calls are emitted to GitHub.
2. **Given** a board with warm sub-issue cache data, **When** a board refresh is triggered, **Then** the total number of GitHub API calls is materially reduced compared to a cold-cache refresh.
3. **Given** fallback polling is active (WebSocket unavailable), **When** polling intervals fire, **Then** expensive board refreshes are not triggered unless data has actually changed.
4. **Given** WebSocket change detection is active, **When** a subscription refresh fires with unchanged data, **Then** no downstream board data fetch is triggered.

---

### User Story 3 - Decouple Frontend Refresh Paths (Priority: P1)

As a user interacting with a board, I expect that lightweight real-time task updates (via WebSocket or polling) do not trigger expensive full board data reloads, so that the interface remains responsive during normal use.

**Why this priority**: Broad query invalidation on every task update is a primary cause of frontend sluggishness and unnecessary network activity. Decoupling lightweight updates from heavy board queries is essential for responsive interactions.

**Independent Test**: Can be fully tested by triggering a WebSocket task update and verifying that only the task query is invalidated (not the board data query), while manual refresh still triggers a full board reload. Delivers a coherent refresh policy that prevents polling storms.

**Acceptance Scenarios**:

1. **Given** a board is open and receiving WebSocket updates, **When** a task-level change arrives, **Then** only task data is refreshed without invalidating the board data query.
2. **Given** fallback polling is active, **When** a polling interval fires, **Then** only lightweight task data is refreshed unless a manual refresh is explicitly requested.
3. **Given** a user clicks the manual refresh button, **When** the refresh is processed, **Then** the full board data query is invalidated and refetched, bypassing caches as intended.
4. **Given** WebSocket updates, fallback polling, auto-refresh, and manual refresh all exist, **When** any refresh path fires, **Then** the behavior follows a single coherent policy without duplicating or conflicting with other paths.

---

### User Story 4 - Optimize Frontend Board Rendering (Priority: P2)

As a user interacting with a large project board, I expect that the board renders smoothly without unnecessary lag during scrolling, dragging, or hovering, so that board management feels fast and fluid.

**Why this priority**: Rendering costs from full-list rerenders, unstabilized props, and hot event listeners are secondary to the refresh-path fixes but still cause noticeable UI lag on boards with many items.

**Independent Test**: Can be fully tested by profiling board interactions (column scrolling, card dragging, popover opening) before and after optimization, measuring rerender counts and frame rates. Delivers measurable rendering improvement on boards with 20+ items.

**Acceptance Scenarios**:

1. **Given** a board with 20+ items across multiple columns, **When** a single card is updated, **Then** only the affected card and its column rerender (not the entire board).
2. **Given** a board column component, **When** the column list is rendered, **Then** derived-data computations (sorting, aggregation) are not repeated on every render cycle.
3. **Given** a user is dragging a chat popup or interacting with a popover, **When** mouse move events fire, **Then** event listeners are throttled to prevent excessive handler invocations.
4. **Given** heavy card and list components, **When** parent props change without affecting the component's own data, **Then** the component does not rerender.

---

### User Story 5 - Verify Improvements and Prevent Regressions (Priority: P2)

As a developer, I need verification that the optimizations are real (not just inferred) and that future changes do not silently regress performance, so that the improvements are durable and trustworthy.

**Why this priority**: Without verification and regression coverage, optimizations may be illusory or fragile. This story ensures the work delivers proven, lasting value.

**Independent Test**: Can be fully tested by running extended backend and frontend test suites covering cache behavior, WebSocket change detection, fallback polling, and board refresh logic, plus a manual network/profile pass comparing against baselines. Delivers confidence that improvements are real and regressions are caught.

**Acceptance Scenarios**:

1. **Given** backend cache behavior tests exist, **When** the test suite runs after optimization, **Then** all cache TTL, stale fallback, and sub-issue cache tests pass.
2. **Given** frontend refresh hook tests exist, **When** the test suite runs after optimization, **Then** all WebSocket fallback, refresh invalidation, and timer deduplication tests pass.
3. **Given** baseline measurements were captured in Phase 1, **When** post-optimization measurements are taken, **Then** idle API call count, board load time, and rerender counts show measurable improvement against the baselines.
4. **Given** a manual end-to-end check is performed, **When** WebSocket updates, fallback polling, manual refresh, and board interactions are exercised, **Then** all behave correctly and responsively.

---

### User Story 6 - Confirm Backend State Against Existing Spec (Priority: P2)

As a developer, I need to verify which backend optimizations from Spec 022 (API rate-limit protection) are fully implemented versus partially landed, so that effort is directed at gaps rather than redoing completed work.

**Why this priority**: The backend already implements some optimizations (300-second board cache TTL, sub-issue cache clearing on manual refresh). Confirming the current state avoids duplicate effort and focuses work on actual gaps.

**Independent Test**: Can be fully tested by auditing the codebase against Spec 022 acceptance criteria and running existing tests that cover WebSocket change detection, board cache TTL alignment, and sub-issue cache invalidation. Delivers a clear gap analysis that scopes the remaining backend work.

**Acceptance Scenarios**:

1. **Given** Spec 022 defines acceptance criteria for idle-rate-limit reduction, **When** the backend codebase is audited, **Then** each criterion is marked as fully implemented, partially implemented, or missing.
2. **Given** the board endpoint sets a 300-second TTL, **When** the cache behavior is tested, **Then** the TTL is confirmed as correctly aligned with Spec 022 targets.
3. **Given** sub-issue cache invalidation occurs on manual refresh, **When** the invalidation path is tested, **Then** the behavior matches Spec 022 requirements.

---

### Edge Cases

- What happens when the WebSocket connection drops mid-session? Fallback polling should activate without triggering a full board refresh storm.
- What happens when cached board data expires while the user is actively interacting? The refresh should be non-disruptive and not cause visible UI flicker.
- What happens on a board with zero items? Optimization should not introduce errors on empty boards.
- What happens when multiple users view the same board simultaneously? Cache behavior should remain correct without cross-user interference.
- What happens if GitHub API rate limits are already exhausted? The system should gracefully degrade using cached data rather than failing or retrying aggressively.
- What happens when a board has 100+ items across many columns? Rendering optimizations should handle large boards without introducing layout or interaction bugs.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST capture backend performance baselines (idle API call count, endpoint frequency, request cost) before any optimization changes are applied.
- **FR-002**: System MUST capture frontend performance baselines (board load time, rerender count, network request volume) before any optimization changes are applied.
- **FR-003**: System MUST NOT emit repeated board refresh API calls when board data has not changed and the board is idle.
- **FR-004**: System MUST use content-based change detection on WebSocket subscription refreshes to skip downstream fetches when data is unchanged.
- **FR-005**: System MUST reduce board refresh API call count when sub-issue caches are warm compared to cold-cache refreshes.
- **FR-006**: System MUST NOT trigger expensive board refreshes during fallback polling unless data has actually changed.
- **FR-007**: System MUST decouple lightweight task-level updates (WebSocket, polling) from the expensive board data query; only manual refresh should invalidate the full board query.
- **FR-008**: System MUST maintain a single coherent refresh policy across WebSocket updates, fallback polling, auto-refresh, and manual refresh paths without conflicts or duplication.
- **FR-009**: System MUST limit rerenders on board interactions so that a single-card update does not cause a full board rerender.
- **FR-010**: System MUST avoid recomputing derived data (sorting, aggregation) on every render cycle in board page components.
- **FR-011**: System MUST throttle high-frequency event listeners (drag, popover positioning) to prevent excessive handler invocations.
- **FR-012**: System MUST memoize heavy card and column components to prevent rerenders when their own data has not changed.
- **FR-013**: System MUST extend or adjust test coverage for backend cache behavior, WebSocket change detection, fallback polling, and frontend board refresh logic.
- **FR-014**: System MUST validate improvements against Phase 1 baselines through automated tests and at least one manual network/profile pass.
- **FR-015**: System MUST audit the backend codebase against Spec 022 acceptance criteria and address any gaps in WebSocket change detection, board cache TTL alignment, or sub-issue cache invalidation.

### Assumptions

- The existing board cache TTL of 300 seconds is correctly implemented and aligned with Spec 022 targets; the assumption will be verified during the Spec 022 audit (FR-015).
- Sub-issue cache clearing on manual refresh is already implemented; verification will confirm this during Phase 1.
- A "representative board" for baseline measurement contains at least 20 items across multiple columns.
- The application already uses WebSocket connections for real-time updates with fallback polling when WebSocket is unavailable.
- Performance targets are based on standard web application expectations (sub-second interactions, minimal idle network activity) unless specific thresholds are defined during baseline measurement.
- Memoization and throttling changes are low-risk and do not require new library dependencies.
- Board virtualization, major service decomposition, and architectural rewrites are explicitly out of scope for this first pass unless baseline results prove them necessary.

### Scope Exclusions

- Board virtualization (deferred to optional Phase 4 unless measurements justify it)
- Major service decomposition of the GitHub projects service
- Introduction of new framework or library dependencies
- Broader architectural rewrites beyond targeted optimizations
- Changes to authentication, authorization, or data model structure

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Idle board viewing produces zero unnecessary API calls to GitHub over a 5-minute measurement window when no data has changed.
- **SC-002**: Board refresh with warm sub-issue caches uses at least 30% fewer GitHub API calls compared to cold-cache baseline.
- **SC-003**: Fallback polling does not trigger full board data refreshes; only lightweight task-level queries fire during polling intervals.
- **SC-004**: A single task update via WebSocket results in task data refresh only, with no board data query invalidation.
- **SC-005**: Board interaction rerender count for a single-card update is reduced by at least 50% compared to pre-optimization baseline.
- **SC-006**: High-frequency event listeners (drag, popover) fire throttled handlers at a maximum rate rather than on every mouse event.
- **SC-007**: All existing backend tests (cache, board, projects/WebSocket, polling) pass after optimization changes.
- **SC-008**: All existing frontend tests (real-time sync, board refresh hooks) pass after optimization changes.
- **SC-009**: Manual end-to-end verification confirms WebSocket updates arrive promptly, fallback polling operates safely, manual refresh bypasses caches, and board interactions remain responsive.
- **SC-010**: Post-optimization baselines show measurable improvement in at least 3 of the 4 key metrics: idle API call count, board load time, rerender count, and network request volume.
