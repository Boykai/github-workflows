# Feature Specification: Performance Review

**Feature Branch**: `001-performance-review`  
**Created**: 2026-03-15  
**Status**: Draft  
**Input**: User description: "Perform a balanced first pass focused on measurable, low-risk performance gains across backend and frontend. Start by capturing baselines and instrumentation, then fix the highest-value issues already surfaced by the codebase: backend GitHub API churn around board refreshes and polling, and frontend board responsiveness issues caused by broad query invalidation, full-list rerenders, and hot event listeners. Defer broader architectural refactors like virtualization and large service decomposition unless the first pass fails to meet targets."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Establish Performance Baselines and Guardrails (Priority: P1)

As a system operator, I want documented performance baselines for both backend and frontend before any optimization work begins, so that every improvement is provable with before-and-after data rather than assumed, and regressions are caught immediately.

**Why this priority**: Without baselines, no optimization can be validated. This story blocks all subsequent optimization work because the success criteria, regression guardrails, and phase-gate decisions all depend on having concrete measurements to compare against.

**Independent Test**: Can be fully tested by recording current backend idle activity, board endpoint cost, refresh behavior, and frontend render profiles on a representative board. Delivers a measurement checklist that defines success and regression guardrails for every subsequent story.

**Acceptance Scenarios**:

1. **Given** a board is open and idle (no user interaction), **When** the system is observed over a 5-minute window, **Then** the number of outbound service calls, refresh events, and data transfer volume are recorded as the backend idle baseline.
2. **Given** a board with a representative number of tasks (50–100 across 4–8 columns) is loaded, **When** the initial page load completes, **Then** the time to interactive, number of render cycles, and network request count are recorded as the frontend load baseline.
3. **Given** a user performs common board interactions (drag a card, click a card, open task detail), **When** each interaction completes, **Then** the response latency and rerender count are recorded as the frontend interaction baseline.
4. **Given** real-time sync is active on an idle board, **When** no external data changes occur over a 5-minute window, **Then** the number of data refresh requests and query invalidations triggered are recorded as the real-time sync idle baseline.
5. **Given** baselines are captured, **When** the measurement checklist is reviewed, **Then** each metric has a documented current value, a target improvement value, and a regression threshold that would trigger investigation.

---

### User Story 2 - Confirm Current State Against Prior Rate-Limit Work (Priority: P1)

As a system operator, I want to verify which pieces of the prior rate-limit protection work (Spec 022) are fully implemented versus only partially landed, so that the optimization effort targets remaining gaps rather than redoing completed items.

**Why this priority**: The current codebase already includes some cache and refresh behavior improvements. Confirming their status prevents wasted effort and ensures the optimization pass builds on what exists rather than duplicating or conflicting with it.

**Independent Test**: Can be fully tested by auditing the current codebase against Spec 022 acceptance criteria and producing a checklist of implemented versus outstanding items. This can run in parallel with frontend baseline capture once the measurement framework is defined.

**Acceptance Scenarios**:

1. **Given** Spec 022 defines acceptance criteria for change detection, cache alignment, and sub-issue invalidation, **When** each criterion is tested against the current system behavior, **Then** a status report identifies each criterion as fully implemented, partially implemented, or not yet started.
2. **Given** the board endpoint currently uses a 300-second cache lifetime, **When** the cache behavior is verified, **Then** the actual observed lifetime matches the configured value and stale data is served correctly during the cache window.
3. **Given** sub-issue cache clearing is expected on manual refresh, **When** a manual refresh is triggered, **Then** the sub-issue cache is confirmed to be cleared and fresh data is fetched.
4. **Given** the status report is complete, **When** optimization planning begins, **Then** only the items marked as partially implemented or not started are included in the optimization scope.

---

### User Story 3 - Reduce Idle Backend Service Call Volume (Priority: P1)

As a board user, I want the system to stop making unnecessary outbound service calls when I am viewing a board without making changes, so that shared rate-limit budget is preserved for actual work and the system remains stable under concurrent use.

**Why this priority**: Unnecessary idle activity is the highest-value backend fix because it consumes shared resources continuously for every open board session. Eliminating this waste has an outsized impact relative to its risk.

**Independent Test**: Can be fully tested by opening a board, leaving it idle, and monitoring outbound service call counts over a fixed interval. Delivers immediate rate-limit savings visible in the baseline comparison.

**Acceptance Scenarios**:

1. **Given** a board is open and idle with real-time sync active, **When** no external data changes occur for 5 minutes, **Then** zero unnecessary outbound service calls are made beyond the minimum keep-alive or subscription heartbeat.
2. **Given** the real-time sync connection receives a change notification, **When** the notification content is identical to the currently cached board data, **Then** no full board data refresh is triggered.
3. **Given** a sub-issue cache is warm from a recent board load, **When** a subsequent board refresh is requested, **Then** the system reuses the cached sub-issue data instead of re-fetching it, measurably reducing the total outbound call count.
4. **Given** the fallback polling mechanism activates (real-time connection unavailable), **When** polling checks for changes, **Then** polling does not trigger full board data refreshes unless actual data changes are detected.
5. **Given** a background process runs periodic work, **When** the work does not detect changes relevant to the current board, **Then** no expensive board-level refresh is triggered from the background process.

---

### User Story 4 - Decouple Lightweight Updates from Full Board Refreshes (Priority: P2)

As a board user, I want real-time task updates (status changes, assignment changes, comment additions) to appear quickly without triggering a full board data reload, so that the board remains responsive and I see updates without disruptive loading states.

**Why this priority**: Full board data reloads on every minor update cause visible delays and unnecessary traffic. Decoupling lightweight updates from expensive full refreshes is the key bridge between backend savings and frontend responsiveness.

**Independent Test**: Can be fully tested by making a small task change (moving a card to a different status column) and verifying that only the affected task data refreshes, not the entire board dataset.

**Acceptance Scenarios**:

1. **Given** a board is displayed and real-time sync delivers a single-task status change, **When** the update arrives, **Then** only the affected task's data is updated in the UI without reloading the full board dataset.
2. **Given** a user clicks the manual refresh button, **When** the refresh completes, **Then** a full board data reload occurs (bypassing all caches as intended), confirming that manual refresh remains a deliberate full-refresh path.
3. **Given** the auto-refresh timer fires, **When** no data changes have occurred since the last load, **Then** the refresh check completes without triggering a visible loading state or full data reload.
4. **Given** the system transitions between real-time sync and fallback polling, **When** the transition occurs, **Then** it does not produce duplicate refreshes or a temporary spike in outbound calls.
5. **Given** real-time updates, fallback polling, auto-refresh, and manual refresh all coexist, **When** any combination is active, **Then** they follow a single coherent refresh policy that prevents conflicting or redundant refresh triggers.

---

### User Story 5 - Improve Board Rendering Responsiveness (Priority: P2)

As a board user working with a board containing many tasks, I want board interactions (scrolling, dragging cards, opening task details, hovering over elements) to feel smooth and responsive, so that managing my project workflow is efficient and not frustrating.

**Why this priority**: Even with optimized data fetching, rendering inefficiencies can make the board feel sluggish. Reducing unnecessary rerenders and rationalizing hot event listeners directly improves the moment-to-moment user experience. This is intentionally limited to low-risk changes.

**Independent Test**: Can be fully tested by profiling board interactions on a representative board and comparing rerender counts and interaction latency against the baseline captured in User Story 1.

**Acceptance Scenarios**:

1. **Given** a board with 50+ visible tasks across multiple columns, **When** a user drags a card from one column to another, **Then** only the affected columns and the dragged card rerender, not the entire board.
2. **Given** a board is displayed, **When** a single task's data changes (from a real-time update), **Then** only that task's card rerenders, not all cards on the board.
3. **Given** a user opens a popover or detail panel, **When** the popover is displayed, **Then** position-tracking listeners do not cause continuous rerenders of unrelated board components.
4. **Given** a board page is loaded, **When** derived data (sorting, grouping, aggregation) is computed for display, **Then** the computation runs once per data change rather than on every render cycle.
5. **Given** a drag interaction is in progress, **When** the drag position is tracked, **Then** the tracking updates are throttled so that unrelated components are not continuously rerendered during the drag.

---

### User Story 6 - Verify Improvements and Prevent Regressions (Priority: P3)

As a system operator, I want automated test coverage and manual verification for the performance-critical refresh, caching, and rendering paths, so that future changes do not silently reintroduce the wasteful patterns being fixed.

**Why this priority**: Without regression coverage, performance fixes are fragile and easily undone by subsequent feature work. This story ensures the durability of all improvements delivered by earlier stories.

**Independent Test**: Can be fully tested by running the automated test suite and confirming that all performance-related test assertions pass. A manual network and profiling pass confirms real-world improvement matches expectations.

**Acceptance Scenarios**:

1. **Given** the backend test suite runs, **When** cache behavior tests execute, **Then** they validate that warm caches prevent redundant outbound calls and that cache lifetimes align with expected values.
2. **Given** the backend test suite runs, **When** change-detection tests execute, **Then** they validate that unchanged data does not trigger full data refreshes.
3. **Given** the frontend test suite runs, **When** board refresh hook tests execute, **Then** they validate that lightweight updates do not trigger full board query invalidation and that manual refresh correctly bypasses caches.
4. **Given** a manual network profiling pass is performed on an idle board over 5 minutes, **When** the results are compared against the pre-optimization baseline, **Then** the measured idle activity shows a reduction of at least 50%.
5. **Given** a manual rendering profiling pass is performed on common board interactions, **When** the results are compared against the pre-optimization baseline, **Then** the measured rerender counts and interaction latencies show measurable improvement.

---

### User Story 7 - Scope Boundary: Defer Heavy Architectural Changes (Priority: P3)

As a product owner, I want the first performance pass to focus exclusively on low-risk, high-value improvements and explicitly defer large structural changes, so that the system remains stable and the team can evaluate whether heavier refactoring is justified by measurement data.

**Why this priority**: Constraining scope prevents destabilizing changes and ensures the first pass is deliverable. If measurements show the first pass is insufficient, a follow-on plan with heavier changes can be pursued with data-driven justification.

**Independent Test**: Can be verified by reviewing the delivered changes and confirming that no new external dependencies were added, no major component architecture was replaced, and a follow-on recommendation exists if targets were not met.

**Acceptance Scenarios**:

1. **Given** the first performance pass is complete, **When** the changes are reviewed, **Then** no board virtualization, major service decomposition, or new external dependencies have been introduced.
2. **Given** the baseline and post-optimization measurements are compared, **When** targets from the success criteria are not fully met, **Then** a documented follow-on plan identifies the specific heavier changes recommended and the measurement data justifying them.
3. **Given** repeated performance work is expected in the future, **When** the first pass concludes, **Then** a recommendation for lightweight permanent instrumentation (refresh cost tracking, cache hit rates, refresh-source attribution) is included to make regressions visible earlier.

### Edge Cases

- What happens when a board has zero tasks? The system should function correctly; idle monitoring and refresh paths should not error or produce unnecessary activity on empty boards.
- What happens when the real-time connection drops mid-interaction? The fallback polling mechanism should activate gracefully without triggering a burst of full board data refreshes.
- What happens when multiple users are viewing the same board simultaneously? Idle activity reduction should apply per-session; one user's idle board should not generate service calls proportional to the number of viewers.
- What happens when a board has an unusually large number of tasks (200+)? The rendering optimizations should degrade gracefully; if the low-risk fixes are insufficient, this scenario should be documented as requiring the deferred virtualization approach.
- What happens when cached data becomes stale due to external changes not delivered through real-time sync? Manual refresh must always bypass caches and return fresh data, serving as the user's escape hatch.
- What happens when the system transitions between real-time sync and fallback polling? The transition should not trigger duplicate refreshes or a temporary spike in outbound calls.
- What happens when multiple refresh sources (auto-refresh timer, fallback polling, real-time notification) fire simultaneously? The refresh policy should deduplicate these triggers so only one refresh executes.
- What happens when the background polling process encounters rate-limit pressure? The process should back off gracefully rather than retrying immediately and consuming more budget.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST capture and document backend and frontend performance baselines before any optimization changes are applied.
- **FR-002**: System MUST verify the implementation status of prior rate-limit protection work (Spec 022) before proceeding with optimization, to avoid duplicating completed work.
- **FR-003**: System MUST NOT make outbound service calls for board data when the board is idle and no external data changes have occurred.
- **FR-004**: System MUST compare incoming change notifications against currently held data and skip full data refreshes when data is unchanged.
- **FR-005**: System MUST reuse warm sub-issue caches during board data refreshes, reducing the total outbound call count per refresh.
- **FR-006**: System MUST ensure fallback polling checks for data changes without triggering full board data refreshes unless changes are detected.
- **FR-007**: System MUST ensure that background polling processes do not trigger expensive board-level refreshes when no relevant changes are detected.
- **FR-008**: System MUST apply single-task real-time updates to the board without invalidating or reloading the full board dataset.
- **FR-009**: System MUST preserve manual refresh as a full data reload path that bypasses all caches.
- **FR-010**: System MUST ensure that real-time sync, fallback polling, auto-refresh, and manual refresh follow a single coherent refresh policy that prevents conflicting or redundant triggers.
- **FR-011**: System MUST ensure that only affected UI components rerender when a single task changes, not the entire board surface.
- **FR-012**: System MUST reduce repeated derived-data computation (sorting, grouping, aggregation) so it runs per data change rather than per render cycle.
- **FR-013**: System MUST throttle or rationalize high-frequency event listeners (drag tracking, popover positioning) so they do not cause continuous rerenders of unrelated components.
- **FR-014**: System MUST maintain or extend automated test coverage for cache behavior, change detection, refresh paths, and board rendering to prevent regressions.
- **FR-015**: System MUST NOT introduce board virtualization, major service decomposition, or new external dependencies in the first performance pass.
- **FR-016**: System MUST produce a documented follow-on plan if the first pass does not meet the defined success criteria targets.

### Key Entities

- **Performance Baseline**: A recorded set of measurements (idle call count, load time, render count, interaction latency) captured before optimization, used as the reference point for validating improvements and detecting regressions.
- **Board Data Cache**: The stored board dataset with a defined time-to-live, used to avoid redundant fetches; must be bypassed on manual refresh and reused when data is unchanged.
- **Sub-Issue Cache**: A secondary cache for sub-issue data associated with board tasks; must be reused across board refreshes when warm to reduce outbound call volume.
- **Real-Time Sync Channel**: The live connection delivering incremental task updates; lightweight updates through this channel must not trigger full board data reloads.
- **Fallback Polling**: The backup mechanism for detecting changes when the real-time connection is unavailable; must check for changes without triggering expensive full refreshes.
- **Refresh Policy**: The unified set of rules governing when and how the board data is refreshed, covering real-time updates, fallback polling, auto-refresh timers, and manual refresh actions. All refresh sources must follow this single policy.
- **Measurement Checklist**: The before-and-after comparison document that records baseline values, post-optimization values, target thresholds, and regression thresholds for each performance metric.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Idle board viewing produces at least 50% fewer outbound service calls over a 5-minute window compared to the pre-optimization baseline.
- **SC-002**: Board data refresh with warm sub-issue caches requires at least 30% fewer outbound service calls compared to a cold-cache refresh.
- **SC-003**: A single-task real-time update is reflected in the UI within 2 seconds without triggering a full board data reload.
- **SC-004**: Fallback polling, when active, produces zero unnecessary full board data refreshes when no data has changed.
- **SC-005**: Board interaction latency (drag, click, open detail) on a board with 50+ tasks shows measurable improvement compared to the pre-optimization baseline.
- **SC-006**: Rerender count for a single-task update on a board with 50+ tasks is reduced to only the affected card and its immediate container, not the full board.
- **SC-007**: All existing backend and frontend automated tests continue to pass after optimization changes.
- **SC-008**: New or extended regression tests cover cache reuse, change detection skip logic, refresh path decoupling, and board component rerender boundaries.
- **SC-009**: No new external dependencies or major architectural changes (virtualization, service decomposition) are introduced in the first pass.
- **SC-010**: If success criteria SC-001 through SC-006 are not fully met, a documented follow-on plan with specific recommendations and supporting measurement data is produced within the same delivery cycle.

## Assumptions

- The existing real-time sync infrastructure (WebSocket or equivalent) is functional and delivers incremental change notifications; this feature optimizes how those notifications are processed, not the transport itself.
- A "representative board" for baseline measurement contains approximately 50–100 tasks across 4–8 columns, reflecting typical production usage.
- The existing Spec 022 work (cache TTL alignment, sub-issue cache invalidation on manual refresh, 300-second board cache TTL) is partially or fully landed; this feature completes any remaining gaps and builds on that foundation rather than redoing it.
- Performance targets (50% idle reduction, 30% cache-hit savings) are reasonable first-pass goals; if the baselines reveal the current state is already close to these targets, the goals will be adjusted based on measurement.
- The test infrastructure for both backend and frontend is sufficient to add regression tests without introducing new testing frameworks or dependencies.
- The current idle activity overhead is material enough to justify optimization; if baselines show minimal waste, the scope may be reduced accordingly.

## Dependencies

- **Spec 022 (API Rate Limit Protection)**: The current feature builds on cache and refresh behavior defined in Spec 022. The implementation status of Spec 022 must be confirmed in Phase 1 before optimization work begins, to avoid rework.
- **Baseline Measurement (Phase 1)**: All optimization work depends on completed baseline measurements. No code changes to optimize behavior should land before baselines are captured.

## Scope Boundaries

**In scope for the first pass:**
- Backend and frontend performance baseline capture and documentation
- Confirming current implementation state against Spec 022 acceptance criteria
- Eliminating unnecessary idle outbound service calls
- Optimizing sub-issue cache reuse during board refreshes
- Ensuring fallback polling does not trigger expensive full refreshes
- Ensuring background polling does not trigger unnecessary board-level refreshes
- Decoupling lightweight real-time updates from full board data queries
- Unifying the refresh policy across real-time sync, fallback polling, auto-refresh, and manual refresh
- Reducing unnecessary board component rerenders for single-task updates
- Stabilizing component props and memoizing heavy components where it demonstrably reduces rerenders
- Throttling or rationalizing hot event listeners (drag tracking, popover positioning)
- Reducing repeated derived-data computation in board display
- Extending automated regression test coverage for performance-critical paths
- Manual network and profiling verification pass

**Explicitly out of scope for the first pass (deferred unless measurements justify):**
- Board virtualization for large boards
- Major service decomposition in the data fetching pipeline
- Adding new external dependencies
- Broader architectural rewrites beyond targeted optimization
- Persistent instrumentation or monitoring dashboards (lightweight measurement for this feature only; permanent instrumentation deferred to follow-on if justified)
- Changes to the real-time sync transport layer itself (optimizations target how notifications are processed, not the connection mechanism)
