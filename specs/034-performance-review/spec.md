# Feature Specification: Performance Review

**Feature Branch**: `034-performance-review`  
**Created**: 2026-03-11  
**Status**: Draft  
**Input**: User description: "Perform a balanced first pass focused on measurable, low-risk performance gains across backend and frontend. Start by capturing baselines and instrumentation, then fix the highest-value issues already surfaced by the codebase: backend GitHub API churn around board refreshes and polling, and frontend board responsiveness issues caused by broad query invalidation, full-list rerenders, and hot event listeners. Defer broader architectural refactors like virtualization and large service decomposition unless the first pass fails to meet targets."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Baseline Performance Measurement (Priority: P1)

A team lead opens the project board and wants confidence that the system's current performance is understood before any optimization work begins. They need documented baselines for backend API activity during idle board viewing, board endpoint response cost, WebSocket/polling refresh behavior, and frontend render hot spots so that improvements can be proven with data rather than assumed.

**Why this priority**: Without baselines, no optimization can be validated. This story blocks all other performance work because success criteria and regression guardrails depend on measured before/after comparisons.

**Independent Test**: Can be fully tested by opening a board, recording idle API call counts over a fixed interval, measuring board endpoint response times, profiling frontend render counts, and documenting the results as a measurement checklist.

**Acceptance Scenarios**:

1. **Given** a user opens a project board and leaves it idle for 5 minutes, **When** network activity is monitored, **Then** the number of outbound API calls and their endpoints are recorded as the backend baseline.
2. **Given** a board with a representative number of tasks is loaded, **When** the board data endpoint is requested, **Then** the response time and GitHub API call count are recorded as the board endpoint cost baseline.
3. **Given** the board is open with WebSocket connected, **When** no data changes occur on the backend, **Then** the number of WebSocket messages and any triggered refreshes are recorded as the real-time baseline.
4. **Given** the board is open with fallback polling active (WebSocket unavailable), **When** no data changes occur, **Then** the polling frequency and any triggered data fetches are recorded as the polling baseline.
5. **Given** the board is rendered with a representative project, **When** a component profiling session captures renders, **Then** the render counts, durations, and hot-spot components are recorded as the frontend render baseline.

---

### User Story 2 - Reduced Backend API Consumption During Idle Board Viewing (Priority: P1)

A user opens the project board and leaves it in the background while working on other tasks. The system should not make unnecessary GitHub API calls when no data has changed, preserving rate limit budget and reducing server load.

**Why this priority**: Unnecessary API churn during idle viewing is the highest-value backend issue. It wastes rate limit budget, increases server cost, and can lead to rate limiting that degrades the experience for all users.

**Independent Test**: Can be tested by opening a board, leaving it idle for a measured interval, and verifying that the outbound GitHub API call count is at or below the target threshold with no repeated unchanged refresh calls.

**Acceptance Scenarios**:

1. **Given** a board is open and idle with WebSocket connected, **When** no upstream data changes occur over 5 minutes, **Then** no redundant board data refresh calls are made to the GitHub API.
2. **Given** a WebSocket subscription detects no changes, **When** the subscription evaluation fires, **Then** the system skips the board refresh rather than fetching unchanged data.
3. **Given** the sub-issue cache is warm from a previous board load, **When** the board data is refreshed, **Then** cached sub-issue data is reused and the total GitHub API call count for the refresh is measurably lower than a cold refresh.
4. **Given** fallback polling is active because WebSocket is unavailable, **When** the polling interval fires, **Then** the poll does not trigger an expensive full board data refresh unless a lightweight check indicates data has changed.

---

### User Story 3 - Coherent Frontend Refresh Policy (Priority: P2)

A user interacts with the board and expects that lightweight task updates (e.g., status changes via WebSocket) appear quickly without triggering a full board data reload, while manual refresh still bypasses all caches and fetches fresh data.

**Why this priority**: Decoupling lightweight updates from expensive full board queries eliminates the prior "polling storm" behavior, improves perceived responsiveness, and reduces unnecessary network traffic.

**Independent Test**: Can be tested by triggering a WebSocket task update and verifying the board reflects the change without a full board data query, then clicking manual refresh and verifying a full data reload occurs.

**Acceptance Scenarios**:

1. **Given** a WebSocket message arrives indicating a task status change, **When** the frontend processes the message, **Then** only the affected task data is updated in the UI without invalidating the full board data query.
2. **Given** fallback polling detects a lightweight change, **When** the polling handler processes it, **Then** only task-level queries are refreshed, not the full board data query.
3. **Given** a user clicks the manual refresh button, **When** the refresh executes, **Then** all caches are bypassed and a full board data reload is performed from the server.
4. **Given** the auto-refresh timer fires, **When** no manual refresh is in progress, **Then** the auto-refresh follows the same lightweight policy as WebSocket updates rather than triggering a full board reload.

---

### User Story 4 - Responsive Board Rendering on Interaction (Priority: P2)

A user drags a card, scrolls the board, or opens a popover and expects the UI to respond without noticeable lag. Redundant rerenders of board columns and cards, repeated derived-data calculations, and hot event listeners should not cause jank during normal board interactions.

**Why this priority**: Even with backend improvements, user-perceived performance depends on frontend rendering efficiency. Low-risk render optimizations improve the experience without introducing new dependencies or architectural complexity.

**Independent Test**: Can be tested by profiling board interactions (drag, scroll, popover open) with a browser profiling tool and verifying that render counts and durations are within acceptable thresholds.

**Acceptance Scenarios**:

1. **Given** a board with 50+ visible cards across multiple columns, **When** a user drags a card between columns, **Then** only the affected source and destination columns rerender, not the entire board.
2. **Given** the board page component computes derived state (sorting, aggregation), **When** the underlying data has not changed, **Then** the derived computation is not repeated on each render cycle.
3. **Given** a user opens a chat popover or agent popover, **When** the popover is positioned, **Then** the positioning listener does not fire at an excessive rate (throttled to a reasonable interval).
4. **Given** a board column contains 20+ issue cards, **When** the column rerenders due to a single card update, **Then** sibling cards that have not changed do not rerender.

---

### User Story 5 - Verification and Regression Coverage (Priority: P3)

A developer making future changes to cache, refresh, or rendering logic has confidence that regressions will be caught by automated tests. Backend cache behavior, WebSocket change detection, fallback polling, and frontend board refresh logic all have adequate test coverage.

**Why this priority**: Without regression coverage, performance improvements are fragile and may be undone by future changes. Tests ensure the gains are maintained over time.

**Independent Test**: Can be tested by running the backend and frontend test suites and verifying that all new and extended tests pass, covering the targeted cache, polling, WebSocket, and refresh behaviors.

**Acceptance Scenarios**:

1. **Given** the backend test suite runs, **When** cache TTL, stale fallback, and sub-issue cache invalidation tests execute, **Then** all tests pass and cover the optimized cache behavior.
2. **Given** the backend test suite runs, **When** WebSocket change-detection and polling behavior tests execute, **Then** all tests pass and verify that unchanged data does not trigger refreshes.
3. **Given** the frontend test suite runs, **When** real-time sync and board refresh hook tests execute, **Then** all tests pass and verify the decoupled refresh policy.
4. **Given** a manual network/profile pass is performed, **When** the board is loaded and interacted with, **Then** the observed behavior matches the automated test expectations.

---

### Edge Cases

- What happens when the WebSocket connection drops mid-session and the system falls back to polling? The transition must not trigger a burst of full board refreshes.
- How does the system behave when the GitHub API rate limit is already near exhaustion? Idle board viewing must not consume remaining budget on redundant calls.
- What happens when a board has zero tasks or only one column? Rendering optimizations must not break empty-state or minimal-state rendering.
- How does the system handle concurrent manual refresh and auto-refresh? Only one refresh should execute; the other should be deduplicated or deferred.
- What happens when cached sub-issue data becomes stale while the user is viewing the board? A staleness indicator or graceful fallback should be provided rather than serving silently outdated data indefinitely.
- What happens when a large board (100+ cards) is loaded for the first time with a cold cache? The initial load should still complete within acceptable time, and the system should not attempt optimizations that assume warm caches.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST capture and document backend performance baselines (idle API call count, board endpoint cost, WebSocket/polling refresh frequency) before any optimization changes are applied.
- **FR-002**: System MUST capture and document frontend performance baselines (component render counts, render durations, hot-spot identification) before any optimization changes are applied.
- **FR-003**: System MUST verify the current implementation state against Spec 022 targets for WebSocket change detection, board cache TTL alignment, and sub-issue cache invalidation, identifying any gaps.
- **FR-004**: System MUST NOT emit redundant board data refresh calls to the GitHub API when no upstream data has changed during idle board viewing with an active WebSocket connection.
- **FR-005**: System MUST reuse warm sub-issue cache data during board refreshes, measurably reducing the total GitHub API call count compared to cold-cache refreshes.
- **FR-006**: System MUST NOT trigger expensive full board data refreshes from fallback polling unless a lightweight check confirms data has actually changed.
- **FR-007**: System MUST decouple lightweight task updates (received via WebSocket or polling) from the expensive full board data query, updating only the affected task data in the UI.
- **FR-008**: System MUST ensure manual refresh bypasses all caches and performs a full board data reload from the server.
- **FR-009**: System MUST enforce a single coherent refresh policy across WebSocket updates, fallback polling, auto-refresh, and manual refresh, preventing conflicting refresh behaviors.
- **FR-010**: System MUST reduce unnecessary rerenders of board columns and issue cards when only a subset of the board data has changed.
- **FR-011**: System MUST avoid repeated derived-data computation (sorting, aggregation) in board page components when the underlying data has not changed.
- **FR-012**: System MUST throttle or rationalize hot event listeners (drag handlers, popover positioning) to prevent excessive callback execution during board interactions.
- **FR-013**: System MUST extend or adjust automated test coverage for backend cache behavior, WebSocket change detection, fallback polling, and frontend board refresh logic.
- **FR-014**: System MUST validate all performance improvements with both automated tests and at least one manual network/profile pass to confirm results are real and not merely inferred.

### Key Entities

- **Board Data**: The full project board state including columns, cards, and metadata. This is the expensive resource to fetch and the primary target for cache optimization.
- **Sub-Issue Data**: Child issue details fetched as part of board data. Cacheable independently to reduce redundant GitHub API calls during board refreshes.
- **Task Update**: A lightweight change to a single task's properties (status, assignee, labels). Should be processable without a full board data reload.
- **Refresh Event**: An event that triggers data fetching. Can originate from WebSocket, fallback polling, auto-refresh timer, or manual user action. Each source should follow a unified refresh policy.
- **Performance Baseline**: A documented set of measurements taken before optimization, serving as the reference point for validating improvements and detecting regressions.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Idle board viewing (no data changes, 5-minute window) produces at least 50% fewer outbound API calls compared to the pre-optimization baseline.
- **SC-002**: Board data refresh with warm sub-issue caches completes with at least 30% fewer GitHub API calls compared to cold-cache refreshes.
- **SC-003**: Lightweight task updates via WebSocket are reflected in the UI within 2 seconds without triggering a full board data reload.
- **SC-004**: Fallback polling, when no data has changed, does not trigger any full board data refreshes over a 5-minute observation window.
- **SC-005**: Board interactions (drag-and-drop, scroll, popover) remain responsive with no user-perceptible lag on boards with up to 100 cards across 5+ columns.
- **SC-006**: Dragging a card between columns causes only the source and destination columns to rerender, not the entire board.
- **SC-007**: All new and extended automated tests pass across backend (cache, polling, WebSocket) and frontend (real-time sync, board refresh) test suites.
- **SC-008**: Manual network/profile verification confirms that measured improvements match automated test expectations, with no regressions in existing functionality.
- **SC-009**: The system maintains existing user-facing behavior — manual refresh still bypasses caches, board loads still complete successfully, and real-time updates still appear promptly.

## Assumptions

- The existing Spec 022 implementation is partially landed (board cache TTL of 300 seconds and sub-issue cache clearing on manual refresh are in place), and this work targets any remaining gaps rather than reimplementing completed items.
- A "representative project" for baseline measurement contains approximately 50–100 tasks across 4–6 columns, which is typical for active project boards in this system.
- The GitHub API rate limit budget is shared across all system operations, so reducing idle consumption directly benefits other features that need API access.
- Low-risk optimizations (memoization, prop stabilization, listener throttling, cache reuse) are sufficient for the first pass. Architectural changes (virtualization, service decomposition) are explicitly deferred unless first-pass measurements prove they are necessary.
- Existing backend and frontend test infrastructure is adequate for the additional regression coverage needed.
- WebSocket is the primary real-time transport, with HTTP polling as the fallback. Both paths must be optimized, but WebSocket is the higher-priority path.

## Scope Boundaries

### In Scope (First Pass)

- Performance baseline capture and documentation (backend and frontend)
- Spec 022 gap analysis and completion of any missing implementations
- Backend: WebSocket subscription refresh logic optimization
- Backend: Sub-issue caching behavior improvements for board data
- Backend: Elimination of unnecessary GitHub API calls in polling and repository resolution
- Frontend: Decoupling lightweight task updates from full board data queries
- Frontend: Unified refresh policy across all refresh sources
- Frontend: Low-risk render optimizations (memoization, prop stabilization, derived-data caching)
- Frontend: Throttling of hot event listeners (drag, popover positioning)
- Regression test coverage for all optimized paths
- Manual verification pass

### Out of Scope (Deferred Unless Metrics Justify)

- Board virtualization for large boards
- Major service decomposition of GitHub project fetching/polling
- New dependency additions for performance (e.g., virtualization libraries)
- Larger architectural rewrites beyond targeted optimization
- Bounded cache policies beyond current TTL-based approach
- Request budget instrumentation and render timing dashboards

## Dependencies

- **Spec 022 (API Rate Limit Protection)**: This work builds on Spec 022's acceptance criteria and must verify its implementation state before proceeding with optimizations.
- **Existing test suites**: Backend and frontend test infrastructure must be functional for regression coverage.
- **GitHub API access**: Baseline measurement requires access to the GitHub API to observe real call patterns.
