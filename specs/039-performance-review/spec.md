# Feature Specification: Performance Review

**Feature Branch**: `039-performance-review`  
**Created**: 2026-03-13  
**Status**: Draft  
**Input**: User description: "Perform a balanced first pass focused on measurable, low-risk performance gains across backend and frontend. Start by capturing baselines and instrumentation, then fix the highest-value issues already surfaced by the codebase: backend GitHub API churn around board refreshes and polling, and frontend board responsiveness issues caused by broad query invalidation, full-list rerenders, and hot event listeners. Defer broader architectural refactors like virtualization and large service decomposition unless the first pass fails to meet targets."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Capture Performance Baselines Before Optimization (Priority: P1)

As a system operator, I want documented backend and frontend performance baselines captured before any optimization changes are applied, so that every improvement is provable through before-and-after comparison and regressions are detectable against concrete numbers.

**Why this priority**: Without baselines, no optimization result can be validated or trusted. Every other user story depends on having recorded measurements that define the starting point. This story blocks all optimization work.

**Independent Test**: Can be fully tested by instrumenting and recording current backend idle API activity, board endpoint request cost, WebSocket/polling refresh behavior, and frontend render hot spots on a representative board. Delivers a measurement checklist defining success thresholds and regression guardrails.

**Acceptance Scenarios**:

1. **Given** a board is open and idle (no user interaction), **When** the system is observed over a 5-minute window, **Then** the count of outbound service calls, refresh events, and data transfer volume are recorded as the backend idle baseline.
2. **Given** a board with a representative number of tasks (50–100 across 4–8 columns) is loaded, **When** the initial page load completes, **Then** the time to interactive, total render cycle count, and network request count are recorded as the frontend load baseline.
3. **Given** a user performs common board interactions (drag a card, click a task, open a detail panel), **When** each interaction completes, **Then** the response latency and rerender count for each interaction are recorded as the frontend interaction baseline.
4. **Given** real-time sync is active on an idle board, **When** no external data changes occur over a 5-minute window, **Then** the number of data refresh requests and query invalidations triggered are recorded as the real-time sync idle baseline.
5. **Given** baselines are captured, **When** the results are reviewed, **Then** the current backend state is compared against Spec 022 acceptance criteria to identify which items are already implemented and which still have gaps.

---

### User Story 2 - Reduce Idle Backend API Activity (Priority: P1)

As a board user, I want the system to stop making unnecessary outbound service calls when I am simply viewing a board without making changes, so that shared rate-limit budget is preserved for actual productive work and the system remains stable under concurrent use.

**Why this priority**: Unnecessary idle API activity continuously consumes shared rate-limit budget and can degrade the experience for all users. This is the highest-value backend fix because it addresses waste that occurs the entire time any user has a board open, not just during active interactions.

**Independent Test**: Can be fully tested by opening a board, leaving it idle for a measured interval, and comparing outbound service call counts against the baseline captured in User Story 1. Delivers immediate, measurable rate-limit savings.

**Acceptance Scenarios**:

1. **Given** a board is open and idle with real-time sync active, **When** no external data changes occur for 5 minutes, **Then** zero unnecessary outbound service calls are made beyond the minimum keep-alive or subscription heartbeat.
2. **Given** the real-time sync receives an incoming change notification, **When** the notification payload is identical to the currently cached board data, **Then** no full board data refresh is triggered.
3. **Given** a sub-issue cache is warm from a recent board load, **When** a subsequent board refresh is requested, **Then** the system reuses the cached sub-issue data instead of re-fetching it, measurably reducing the total outbound call count.
4. **Given** the fallback polling mechanism activates because the real-time connection is unavailable, **When** polling checks for changes, **Then** polling does not trigger full board data refreshes unless actual data changes are detected.
5. **Given** repository resolution is needed during a board request, **When** the resolution completes, **Then** the system uses a single consistent resolution path rather than duplicated fallback flows that add unnecessary calls.

---

### User Story 3 - Decouple Lightweight Updates from Full Board Refreshes (Priority: P2)

As a board user, I want real-time task updates (status changes, assignment changes, comment additions) to appear quickly without triggering a full board data reload, so that the board remains responsive and I see updates without disruptive loading states or unnecessary delays.

**Why this priority**: Full board data reloads on every minor update cause visible UI delays, unnecessary network traffic, and rate-limit consumption. Decoupling lightweight updates from expensive full refreshes is the key bridge between backend savings and frontend responsiveness.

**Independent Test**: Can be fully tested by triggering a small task change (e.g., moving a card to a different status column) and verifying that only the affected task data refreshes in the UI without a full board dataset reload.

**Acceptance Scenarios**:

1. **Given** a board is displayed and real-time sync delivers a single-task status change, **When** the update arrives, **Then** only the affected task's data is updated in the UI without reloading the full board dataset.
2. **Given** a user clicks the manual refresh button, **When** the refresh completes, **Then** a full board data reload occurs (bypassing all caches as intended), confirming that manual refresh remains a deliberate full-refresh escape hatch.
3. **Given** the auto-refresh timer fires, **When** no data changes have occurred since the last load, **Then** the refresh check completes without triggering a visible loading state or full data reload.
4. **Given** the system is using fallback polling instead of real-time sync, **When** a polling cycle detects no changes, **Then** no board query invalidation occurs and no full reload is triggered.
5. **Given** all refresh paths (real-time sync, fallback polling, auto-refresh, manual refresh) are active, **When** they operate simultaneously, **Then** they follow a single coherent refresh policy and do not create overlapping or duplicated refresh storms.

---

### User Story 4 - Improve Board Rendering Responsiveness (Priority: P2)

As a board user working with a board containing many tasks, I want board interactions (scrolling, dragging cards, opening task details, hovering over elements) to feel smooth and responsive, so that managing my project workflow is efficient and not frustrating.

**Why this priority**: Even with optimized data fetching, rendering inefficiencies can make the board feel sluggish during normal use. Reducing unnecessary rerenders, stabilizing props, and rationalizing hot event listeners directly improves the moment-to-moment user experience without architectural risk.

**Independent Test**: Can be fully tested by profiling board interactions on a representative board (50+ tasks) and comparing rerender counts and interaction latency against the baselines captured in User Story 1.

**Acceptance Scenarios**:

1. **Given** a board with 50+ visible tasks across multiple columns, **When** a user drags a card from one column to another, **Then** only the affected columns and the dragged card rerender, not the entire board.
2. **Given** a board is displayed, **When** a single task's data changes (from a real-time update), **Then** only that task's card rerenders, not all cards on the board.
3. **Given** a user opens a popover or detail panel, **When** the popover is displayed and positioned, **Then** position-tracking listeners do not cause continuous rerenders of unrelated board components.
4. **Given** a board page is loaded, **When** derived data (sorting, grouping, aggregation) is computed for display, **Then** the computation runs once per data change rather than on every render cycle.
5. **Given** a chat popup is open and being dragged, **When** the drag event fires continuously, **Then** the drag tracking is throttled so it does not cause continuous rerenders of components outside the popup.

---

### User Story 5 - Verify Improvements and Prevent Regressions (Priority: P3)

As a system operator, I want automated test coverage for the performance-critical refresh, caching, and rendering paths, so that future changes do not silently reintroduce the wasteful patterns being fixed in this pass.

**Why this priority**: Without regression coverage, performance fixes are fragile and easily undone by subsequent feature work. This story ensures durability of all improvements delivered by the earlier stories, protecting the investment across future development cycles.

**Independent Test**: Can be fully tested by running the automated test suite and confirming all performance-related test assertions pass, plus a manual network and profiling pass confirms the real-world improvement matches the automated results.

**Acceptance Scenarios**:

1. **Given** the backend test suite runs, **When** cache behavior tests execute, **Then** they validate that warm caches prevent redundant outbound calls and that cache TTLs match expected values.
2. **Given** the backend test suite runs, **When** change-detection tests execute, **Then** they validate that unchanged data does not trigger full data refreshes through the real-time sync path.
3. **Given** the backend test suite runs, **When** polling behavior tests execute, **Then** they validate that fallback polling does not trigger expensive board refreshes unintentionally.
4. **Given** the frontend test suite runs, **When** board refresh hook tests execute, **Then** they validate that lightweight updates do not trigger full board query invalidation and that manual refresh correctly bypasses caches.
5. **Given** a manual network profiling pass is performed on an idle board, **When** measured over a 5-minute window, **Then** idle activity shows a reduction of at least 50% compared to the pre-optimization baseline.
6. **Given** a manual rendering profiling pass is performed on a representative board, **When** common interactions are executed, **Then** rerender counts and interaction latencies show measurable improvement compared to the pre-optimization baseline.

---

### User Story 6 - Scope Boundary: Defer Heavy Architectural Changes (Priority: P3)

As a product owner, I want the first performance pass to focus exclusively on low-risk, high-value improvements and explicitly defer large structural changes, so that the system remains stable and the team can evaluate whether heavier refactoring is justified by the measurement data from this pass.

**Why this priority**: Constraining scope prevents destabilizing changes and ensures the first pass is deliverable with confidence. If measurements show the first pass is insufficient, a follow-on plan with heavier changes can be pursued with data-driven justification rather than speculation.

**Independent Test**: Can be verified by reviewing the delivered changes and confirming that no new external dependencies were added, no major component architecture was replaced, and a follow-on recommendation document exists if targets from the success criteria were not met.

**Acceptance Scenarios**:

1. **Given** the first performance pass is complete, **When** the changes are reviewed, **Then** no board virtualization, major service decomposition, or new external dependencies have been introduced.
2. **Given** the baseline and post-optimization measurements are compared, **When** any success criteria targets from SC-001 through SC-006 are not fully met, **Then** a documented follow-on plan identifies the specific heavier changes recommended and the measurement data justifying them.
3. **Given** the follow-on plan exists, **When** it is reviewed, **Then** it prioritizes virtualization for large boards and deeper service consolidation for persistent API churn as the recommended next options, consistent with the phased approach.

### Edge Cases

- What happens when a board has zero tasks? The system should function correctly; idle monitoring and refresh paths should not error or produce unnecessary activity on empty boards.
- What happens when the real-time connection drops mid-interaction? The fallback polling mechanism should activate gracefully without triggering a burst of full board data refreshes or creating a temporary spike in outbound calls.
- What happens when multiple users are viewing the same board simultaneously? Idle activity reduction should apply per-session; one user's idle board should not generate service calls proportional to the number of concurrent viewers.
- What happens when a board has an unusually large number of tasks (200+)? The low-risk rendering optimizations should degrade gracefully; if they are insufficient for boards of this size, the scenario should be documented as requiring the deferred virtualization approach.
- What happens when cached data becomes stale due to external changes not delivered through real-time sync? Manual refresh must always bypass all caches and return fresh data, serving as the user's reliable escape hatch for stale data.
- What happens when the system transitions between real-time sync and fallback polling? The transition should not trigger duplicate refreshes, temporary rate-limit spikes, or visible board flickering.
- What happens when a board endpoint request encounters a partial failure (e.g., sub-issue fetch fails but main board data succeeds)? The system should display available data and surface the partial failure gracefully rather than failing the entire board load.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST capture and document backend and frontend performance baselines before any optimization changes are applied.
- **FR-002**: System MUST confirm the current implementation state against Spec 022 acceptance criteria and identify any gaps before beginning optimization work.
- **FR-003**: System MUST NOT make outbound service calls for board data when the board is idle and no external data changes have occurred.
- **FR-004**: System MUST compare incoming change notifications against currently held data and skip full data refreshes when data is unchanged.
- **FR-005**: System MUST reuse warm sub-issue caches during board data refreshes, reducing the total outbound call count per refresh.
- **FR-006**: System MUST ensure fallback polling checks for data changes without triggering full board data refreshes unless changes are detected.
- **FR-007**: System MUST apply single-task real-time updates to the board UI without invalidating or reloading the full board dataset.
- **FR-008**: System MUST preserve manual refresh as a full data reload path that bypasses all caches.
- **FR-009**: System MUST consolidate repository resolution into a single consistent path to eliminate duplicated fallback flows.
- **FR-010**: System MUST enforce a single coherent refresh policy across real-time sync, fallback polling, auto-refresh, and manual refresh to prevent overlapping or duplicated refresh activity.
- **FR-011**: System MUST ensure that only affected UI components rerender when a single task changes, not the entire board surface.
- **FR-012**: System MUST reduce repeated derived-data computation (sorting, grouping, aggregation) so it runs per data change rather than per render cycle.
- **FR-013**: System MUST throttle or rationalize high-frequency event listeners (drag tracking, popover positioning) so they do not cause continuous rerenders of unrelated components.
- **FR-014**: System MUST maintain or extend automated test coverage for cache behavior, change detection, refresh paths, and board rendering to prevent regressions.
- **FR-015**: System MUST NOT introduce board virtualization, major service decomposition, or new external dependencies in the first performance pass.
- **FR-016**: System MUST produce a documented follow-on plan if the first pass does not meet the defined success criteria targets, including specific recommendations and supporting measurement data.

### Key Entities

- **Performance Baseline**: A recorded set of measurements (idle call count, load time, render count, interaction latency, refresh event count) captured before optimization, used as the reference point for validating improvements and detecting regressions.
- **Board Data Cache**: The stored board dataset with a defined time-to-live (currently 300 seconds per Spec 022), used to avoid redundant fetches; must be bypassed on manual refresh and reused when data is unchanged.
- **Sub-Issue Cache**: A secondary cache for sub-issue data associated with board tasks; must be reused across board refreshes when warm to reduce outbound call volume for the most expensive repeated fetches.
- **Real-Time Sync Channel**: The live connection (WebSocket or equivalent) delivering incremental task updates; lightweight updates through this channel must not trigger full board data reloads.
- **Fallback Polling**: The backup mechanism for detecting changes when the real-time connection is unavailable; must check for changes without triggering expensive full refreshes unless data has actually changed.
- **Refresh Policy**: The unified set of rules governing when and how board data is refreshed, covering real-time updates, fallback polling, auto-refresh timers, and manual refresh actions. All refresh sources must follow this single policy.
- **Data Hash**: A content fingerprint used to detect whether incoming data differs from cached data, enabling change-detection logic that skips unnecessary refreshes.
- **Follow-On Plan**: A documented set of recommendations for heavier structural changes (virtualization, service decomposition) to be pursued only if first-pass measurements prove them necessary.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Idle board viewing produces at least 50% fewer outbound service calls over a 5-minute window compared to the pre-optimization baseline.
- **SC-002**: Board data refresh with warm sub-issue caches requires at least 30% fewer outbound service calls compared to a cold-cache refresh.
- **SC-003**: A single-task real-time update is reflected in the UI within 2 seconds without triggering a full board data reload.
- **SC-004**: Fallback polling, when active on an idle board, produces zero unnecessary full board data refreshes when no data has changed.
- **SC-005**: Board interaction latency (drag, click, open detail) on a board with 50+ tasks shows measurable improvement compared to the pre-optimization baseline.
- **SC-006**: Rerender count for a single-task update on a board with 50+ tasks is reduced to only the affected card and its immediate container, not the full board.
- **SC-007**: All existing backend and frontend automated tests continue to pass after optimization changes.
- **SC-008**: New or extended regression tests cover cache reuse, change detection skip logic, fallback polling safety, refresh path decoupling, and board component rerender boundaries.
- **SC-009**: No new external dependencies or major architectural changes (virtualization, service decomposition) are introduced in the first pass.
- **SC-010**: If success criteria SC-001 through SC-006 are not fully met, a documented follow-on plan with specific recommendations and supporting measurement data is produced within the same delivery cycle.

## Assumptions

- The existing real-time sync infrastructure (WebSocket or equivalent) is functional and delivers incremental change notifications; this feature optimizes how those notifications are processed, not the underlying transport mechanism.
- A "representative board" for baseline measurement contains approximately 50–100 tasks across 4–8 columns, reflecting typical production usage patterns.
- The existing Spec 022 work (cache TTL alignment, sub-issue cache invalidation on manual refresh, 300-second board cache TTL) is partially or fully landed; this feature completes any remaining gaps and builds on that foundation rather than redoing it.
- Performance targets (50% idle reduction, 30% cache-hit savings) are reasonable first-pass goals; if the baselines reveal the current state is already close to these targets, the goals will be adjusted based on measurement data.
- The existing test infrastructure for both backend and frontend is sufficient to add regression tests without introducing new testing frameworks or dependencies.
- Industry-standard error handling (user-friendly messages with appropriate fallbacks) is used for partial failures unless otherwise specified.
- Standard session-based caching semantics apply: caches are per-session and do not leak across user sessions or board views.

## Dependencies

- **Spec 022 (API Rate Limit Protection)**: The current feature builds directly on cache and refresh behavior defined in Spec 022. The implementation status of Spec 022 must be confirmed in Phase 1 before optimization work begins. Already-landed items should not be redone.
- **Baseline Measurement (Phase 1)**: All optimization work in Phases 2 and 3 depends on completed baseline measurements from Phase 1. No code changes to optimize behavior should land before baselines are captured and documented.
- **Existing Test Infrastructure**: Regression test coverage depends on the current backend and frontend test, lint, and type-checking infrastructure being functional and capable of running the targeted test files.

## Scope Boundaries

**In scope for the first pass:**
- Backend and frontend performance baseline capture and documentation
- Confirming current implementation state against Spec 022 acceptance criteria
- Eliminating unnecessary idle outbound service calls
- Completing change-detection logic so unchanged data does not trigger refreshes
- Optimizing sub-issue cache reuse during board refreshes
- Ensuring fallback polling does not trigger expensive full refreshes
- Consolidating duplicated repository resolution into a single path
- Decoupling lightweight real-time updates from full board data queries
- Enforcing a single coherent refresh policy across all refresh sources
- Reducing unnecessary board component rerenders through memoization and prop stabilization
- Reducing repeated derived-data computation in board page components
- Throttling or rationalizing hot event listeners (drag, popover positioning)
- Extending automated regression test coverage for all changed paths
- Manual network and profiling verification pass

**Explicitly out of scope for the first pass (deferred unless measurements justify):**
- Board virtualization for large boards
- Major service decomposition in the data fetching pipeline
- Adding new external dependencies or libraries
- Broader architectural rewrites beyond the targeted refresh and render paths
- Persistent instrumentation, monitoring dashboards, or request-budget tracking (lightweight measurement for this feature only)
- Performance optimization of non-board surfaces (settings, configuration pages, etc.)
