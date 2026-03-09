# Feature Specification: Performance Review

**Feature Branch**: `032-performance-review`  
**Created**: 2026-03-09  
**Status**: Draft  
**Input**: User description: "Perform a balanced first pass focused on measurable, low-risk performance gains across backend and frontend. Start by capturing baselines and instrumentation, then fix the highest-value issues already surfaced by the codebase: backend GitHub API churn around board refreshes and polling, and frontend board responsiveness issues caused by broad query invalidation, full-list rerenders, and hot event listeners. Defer broader architectural refactors like virtualization and large service decomposition unless the first pass fails to meet targets."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Idle Board Viewing Without Unnecessary API Activity (Priority: P1)

A user opens a project board and leaves it open without interacting. The system keeps the board data current through real-time updates (WebSocket) or safe fallback polling, but does not make redundant or expensive backend calls when no data has actually changed. The user's rate-limit budget is preserved for intentional actions rather than consumed by idle background work.

**Why this priority**: Excessive idle API consumption is the highest-impact problem. It wastes rate-limit budget, increases backend load, and can degrade the experience for all users sharing the same token. Fixing this delivers measurable value immediately and is a prerequisite for trusting that other optimizations are not masked by noise.

**Independent Test**: Can be verified by opening a board, leaving it idle for a fixed observation window (e.g., 5 minutes), and counting the number of outgoing API calls. Compare the count against an established baseline to confirm the reduction.

**Acceptance Scenarios**:

1. **Given** a user has an open board with no data changes occurring, **When** 5 minutes elapse with no user interaction, **Then** the number of backend API calls made during that window is at most 50% of the pre-optimization baseline.
2. **Given** a user has an open board receiving real-time updates, **When** a WebSocket message arrives indicating no data change, **Then** the system does not trigger a full board data refresh.
3. **Given** the WebSocket connection is unavailable and fallback polling is active, **When** polling detects no data change, **Then** the system does not trigger an expensive board data refresh.

---

### User Story 2 - Responsive Board Interactions (Priority: P2)

A user interacts with a project board — scrolling through columns, hovering over cards, dragging items, or clicking to view details. The board responds without noticeable lag or jank. Lightweight task-level updates (e.g., a task status change arriving via WebSocket) do not cause the entire board to re-render or freeze during interaction.

**Why this priority**: Board responsiveness directly affects user productivity and satisfaction. If interactions feel sluggish, users lose trust in the tool regardless of how efficient the backend is. This story targets the frontend rendering and refresh-path decoupling that most visibly impacts daily use.

**Independent Test**: Can be verified by profiling board interactions (drag, scroll, card click) on a representative board size and confirming that interaction response times and rerender counts stay within acceptable thresholds.

**Acceptance Scenarios**:

1. **Given** a board with 50+ visible cards across multiple columns, **When** the user scrolls through the board, **Then** the scrolling is smooth with no perceptible frame drops.
2. **Given** a board is displayed and a lightweight task update arrives via WebSocket, **When** the update is applied, **Then** only the affected card or a minimal portion of the board re-renders — not the full board.
3. **Given** a user is dragging a card between columns, **When** a background refresh or real-time update arrives, **Then** the drag operation is not interrupted and no visible stutter occurs.
4. **Given** a user manually triggers a board refresh, **When** the refresh completes, **Then** the full board data is reloaded (bypassing caches where intended) and the board updates within 3 seconds.

---

### User Story 3 - Measurable Baselines Before and After Optimization (Priority: P1)

Before any optimization code is changed, the team captures quantitative baselines for both backend and frontend performance. After optimizations are applied, the same measurements are repeated to prove improvements and catch regressions. This data-driven approach ensures that changes deliver real value rather than assumed improvements.

**Why this priority**: Without baselines, there is no way to verify that optimizations are effective or to detect regressions. This story is a blocking prerequisite for all optimization work and is equally critical to the idle API story.

**Independent Test**: Can be verified by running the measurement protocol (API call counts, render profiling, network activity inspection) before and after changes are applied, and comparing the results against defined targets.

**Acceptance Scenarios**:

1. **Given** the measurement protocol is defined, **When** baselines are captured before any optimization changes, **Then** a documented before-state exists covering idle API call counts, board endpoint request cost, polling/WebSocket refresh frequency, and frontend render hot spots.
2. **Given** optimizations have been applied, **When** the same measurements are repeated, **Then** the after-state shows measurable improvement against each baseline metric and no metric has regressed beyond an acceptable tolerance.
3. **Given** existing automated tests cover cache behavior, polling logic, WebSocket fallback, and board refresh, **When** the optimization changes are applied, **Then** all existing tests continue to pass without modification (unless intentionally updated to reflect new expected behavior).

---

### User Story 4 - Coherent Refresh Policy Across Update Channels (Priority: P2)

The system has multiple ways to refresh board data: WebSocket real-time updates, fallback polling, auto-refresh timers, and manual user-triggered refresh. A user expects that these channels work together coherently — they should not duplicate work, conflict with each other, or cause "refresh storms" where multiple channels simultaneously trigger expensive operations.

**Why this priority**: Incoherent refresh behavior is a root cause of both the backend API churn and the frontend rerender issues. Establishing a single coherent refresh policy is foundational for both performance and correctness.

**Independent Test**: Can be verified by simulating each refresh trigger (WebSocket message, poll tick, auto-refresh timer, manual refresh button) in isolation and combination, and confirming that only the expected data operations occur.

**Acceptance Scenarios**:

1. **Given** WebSocket is connected and delivering updates, **When** a fallback polling tick fires, **Then** the polling tick is suppressed or results in a no-op (no duplicate refresh).
2. **Given** a lightweight task update arrives via any channel, **When** the update is processed, **Then** only the relevant task data is updated — the expensive full board data query is not triggered.
3. **Given** the user clicks the manual refresh button, **When** the refresh executes, **Then** caches are bypassed as intended and a full board data reload occurs exactly once.
4. **Given** multiple refresh triggers fire within a short window (e.g., WebSocket + auto-refresh + poll), **When** these are processed, **Then** at most one board data refresh is executed (deduplication).

---

### User Story 5 - Backend Cache Effectiveness for Board Data (Priority: P3)

When the backend serves board data, previously fetched sub-issue data and board metadata that has not changed should be served from cache rather than re-fetched from the external API. Warm caches should materially reduce the number of external API calls required per board refresh.

**Why this priority**: Cache effectiveness directly reduces API consumption and board load times, but the improvements are only meaningful after idle churn and refresh-path issues are resolved (Stories 1 and 4). This story addresses the remaining call volume once the unnecessary calls are eliminated.

**Independent Test**: Can be verified by warming the cache with an initial board load, then triggering a subsequent board refresh (without manual cache bypass) and counting the number of external API calls. Compare against the cold-cache call count.

**Acceptance Scenarios**:

1. **Given** a board has been loaded once and sub-issue data is cached, **When** the board is refreshed without manual cache bypass, **Then** cached sub-issue data is reused and external API calls for sub-issues are reduced by at least 50% compared to a cold-cache load.
2. **Given** cache entries exist for board data, **When** the cache time-to-live (TTL) has not expired, **Then** subsequent requests serve data from cache without making external API calls for the cached data.
3. **Given** a user manually refreshes the board, **When** the refresh is processed, **Then** sub-issue caches are appropriately cleared so that fresh data is fetched.

---

### User Story 6 - Low-Risk Frontend Render Optimization (Priority: P3)

The frontend board and chat surfaces are optimized to reduce unnecessary computational work during rendering. Repeated derived-data calculations in page components are minimized, heavy card and list components avoid unnecessary re-renders, and high-frequency event listeners (drag positioning, popover anchoring) are throttled to avoid layout thrashing.

**Why this priority**: These are low-risk, incremental improvements that reduce CPU work and improve perceived responsiveness. They are intentionally scoped to avoid introducing new dependencies or major architectural changes (such as virtualization) in the first pass.

**Independent Test**: Can be verified by profiling render counts and component update frequency during typical board interactions, and comparing against pre-optimization baselines.

**Acceptance Scenarios**:

1. **Given** a board page is displayed with multiple columns and cards, **When** a single card's data changes, **Then** only the affected card component and its direct parent column re-render — not all columns or all cards.
2. **Given** a user drags a chat popup or interacts with a popover, **When** the drag/position listener fires, **Then** the listener is throttled so that it does not execute on every pixel movement.
3. **Given** board data is loaded and derived state (sorting, aggregation) is computed, **When** the underlying data has not changed, **Then** the derived state is not recomputed.

---

### Edge Cases

- What happens when the WebSocket connection drops and reconnects while the user is mid-interaction (e.g., dragging a card)? The system should queue any missed updates and apply them after reconnection without interrupting the user's action.
- What happens when a board has zero cards or a single column? Optimizations should not introduce errors on minimal or empty board states.
- What happens when cached data becomes stale but the cache TTL has not yet expired? The system should serve stale data gracefully and refresh in the background when appropriate, without showing errors.
- What happens when multiple users are viewing the same board simultaneously and one user triggers a manual refresh? Only the requesting user's session should bypass caches — other users should continue receiving updates through the normal real-time channels.
- What happens when fallback polling activates during a period of high external API rate limiting? Polling should respect rate-limit constraints and degrade gracefully (e.g., back off the polling interval) rather than making calls that will be throttled.

## Requirements *(mandatory)*

### Functional Requirements

#### Phase 1 — Baseline and Guardrails

- **FR-001**: The team MUST capture quantitative performance baselines for backend API activity (idle call count, board endpoint request cost, polling/WebSocket refresh frequency) before any optimization changes are made.
- **FR-002**: The team MUST capture quantitative performance baselines for frontend rendering (board load time, interaction response time, rerender frequency, network request activity) before any optimization changes are made.
- **FR-003**: The team MUST verify the current implementation state of prior optimization work (Spec 022) including WebSocket change detection, board cache TTL alignment, and sub-issue cache invalidation, and document which items are fully implemented versus partially landed.

#### Phase 2 — Backend API Consumption

- **FR-004**: The system MUST NOT emit repeated full board data refreshes when WebSocket messages indicate no data has changed.
- **FR-005**: The system MUST ensure that warm sub-issue caches materially reduce the number of external API calls during board refresh (target: at least 50% reduction in sub-issue API calls on warm-cache refresh versus cold-cache refresh).
- **FR-006**: The system MUST ensure that fallback polling does not trigger expensive full board data refreshes unintentionally; polling should only trigger lightweight checks or no-ops when data is unchanged.
- **FR-007**: The system MUST consolidate any duplicated repository-resolution logic so that a single shared path is used, eliminating redundant external API calls from alternate resolution flows.

#### Phase 2 — Frontend Refresh Path

- **FR-008**: The system MUST decouple lightweight task-level updates (e.g., status changes arriving via WebSocket) from the expensive full board data query, so that task updates do not trigger a full board reload.
- **FR-009**: The system MUST implement a single coherent refresh policy that governs the interaction between WebSocket updates, fallback polling, auto-refresh timers, and manual refresh, preventing duplicate or conflicting refreshes.
- **FR-010**: The system MUST deduplicate refresh triggers so that multiple near-simultaneous refresh signals result in at most one board data refresh operation.

#### Phase 3 — Frontend Render Optimization

- **FR-011**: The system MUST reduce unnecessary re-renders of board column and card components so that updates to a single card do not cause all columns or all cards to re-render.
- **FR-012**: The system MUST minimize repeated derived-data computation (sorting, aggregation) in board page components by ensuring derived state is only recomputed when its input data actually changes.
- **FR-013**: The system MUST throttle or debounce high-frequency event listeners (drag positioning, popover anchoring) so they do not fire on every frame or pixel movement.

#### Phase 3 — Verification and Regression

- **FR-014**: The team MUST re-capture the same performance baselines measured in Phase 1 after optimizations are applied, and demonstrate measurable improvement on each metric.
- **FR-015**: The system MUST pass all existing automated tests (backend and frontend) after optimizations are applied, with test modifications only where the expected behavior has intentionally changed.
- **FR-016**: The team MUST perform at least one manual end-to-end verification confirming that WebSocket updates refresh task data promptly, fallback polling remains safe, manual refresh bypasses caches as intended, and board interactions remain responsive.

### Key Entities

- **Board Data**: The full project board state including columns, cards, and their ordering. This is the expensive payload that should be refreshed judiciously.
- **Task Update**: A lightweight change to a single task's attributes (status, assignee, title). These arrive via real-time channels and should be applied without full board reloads.
- **Sub-Issue Data**: Child issue details associated with board cards. These are cacheable and represent a significant portion of external API call volume during board refresh.
- **Performance Baseline**: A documented snapshot of quantitative metrics (API call counts, render timings, network activity) captured at a specific point in time for before/after comparison.
- **Refresh Trigger**: Any event that can initiate a board data update — WebSocket message, poll tick, auto-refresh timer, or manual user action. These must be coordinated under a single policy.

### Assumptions

- The existing Spec 022 implementation has partially landed key cache and refresh improvements (300-second board cache TTL, sub-issue cache clearing on manual refresh). This specification targets remaining gaps rather than reimplementing completed work.
- A "representative board size" for frontend profiling is defined as a board with at least 5 columns and 50+ cards across those columns.
- Rate-limit budgets are shared per authentication token, meaning idle consumption by one user's open board reduces the budget available for all users sharing that token.
- The existing automated test suites for cache behavior, polling, WebSocket fallback, and board refresh are sufficient to serve as regression guardrails and do not need fundamental restructuring.
- Performance targets (e.g., "50% reduction in idle API calls") are measured against the baselines captured in Phase 1, not against arbitrary absolute numbers.
- Board virtualization, major service decomposition, new dependency additions, and larger architectural rewrites are explicitly out of scope for the first pass unless Phase 1 baselines indicate the low-risk optimizations are insufficient.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Idle API call volume for an open board with no data changes is reduced by at least 50% compared to the pre-optimization baseline over a 5-minute observation window.
- **SC-002**: Warm-cache board refresh requires at least 50% fewer external API calls for sub-issue data compared to a cold-cache board refresh.
- **SC-003**: Board interaction response time (scroll, drag, card click) remains under 100 milliseconds on a board with 50+ cards, with no perceptible frame drops during scrolling.
- **SC-004**: A single task-level update arriving via WebSocket causes re-renders of at most the affected card and its parent column — not the full board.
- **SC-005**: Multiple near-simultaneous refresh triggers (e.g., WebSocket + poll + auto-refresh within 1 second) result in at most one actual board data refresh operation.
- **SC-006**: All existing backend and frontend automated tests pass after optimizations are applied, with no unintentional test modifications.
- **SC-007**: Manual end-to-end verification confirms that WebSocket updates, fallback polling, manual refresh, and board interactions all function correctly after optimizations.
- **SC-008**: Quantitative before/after comparison is documented for every baseline metric captured in Phase 1, proving that each optimization delivers measurable improvement with no regressions.
