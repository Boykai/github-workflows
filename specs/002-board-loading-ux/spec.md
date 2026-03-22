# Feature Specification: Board Loading UX — Skeleton, Stale-While-Revalidate, Refetch Indicator

**Feature Branch**: `002-board-loading-ux`  
**Created**: 2026-03-22  
**Status**: Draft  
**Input**: User description: "Replace the full-screen spinner with skeleton columns on first load, instantly show cached board data when re-visiting a project (stale-while-revalidate via keepPreviousData), and add a subtle refetch indicator during background refreshes. All frontend-only — the backend cache layer is already solid."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Instant Board Display from Cache (Priority: P1)

As a user returning to a previously visited project board, I want to see the board content immediately without any loading spinner, so that my workflow is not interrupted and the application feels fast and responsive.

When a user navigates back to a project they have visited recently (within the cache window), the board displays instantly using previously cached data. The user can begin reviewing and interacting with the board right away while any background data refresh happens silently.

**Why this priority**: This is the highest-impact improvement because it eliminates the most common loading delay — returning to a board the user was just working with. It directly addresses the perception of slowness and provides the biggest UX win with a stale-while-revalidate pattern.

**Independent Test**: Can be fully tested by visiting a project board, navigating away, then returning. The board should render instantly from cache, delivering immediate perceived performance improvement.

**Acceptance Scenarios**:

1. **Given** a user has previously loaded a project board (data is in the client cache), **When** they navigate back to that same project board, **Then** the board renders immediately with the cached data and no loading spinner is shown.
2. **Given** a user is viewing a cached board, **When** the cached data is stale and a background refresh completes with updated data, **Then** the board seamlessly updates to reflect the new data without a full page reload or spinner.
3. **Given** a user is viewing Project A's board, **When** they switch to Project B, **Then** Project A's board remains visible (dimmed) until Project B's data loads, rather than showing a blank screen or spinner.

---

### User Story 2 - Skeleton Board on First Load (Priority: P2)

As a user loading a project board for the first time (no cached data available), I want to see a skeleton layout that matches the board's column structure, so that I understand the page layout immediately and perceive the load as faster than a generic spinner.

Instead of a centered full-screen spinner, the board area shows skeleton placeholder columns that mirror the real board's grid layout. This provides spatial continuity and sets user expectations about what content is loading.

**Why this priority**: First-load experience is critical for new users and first visits to any project. While less frequent than returning to a cached board, it sets the first impression and perceived performance. Skeleton screens are a proven UX pattern (used by Google, Vercel, and other major platforms) that reduces perceived loading time.

**Independent Test**: Can be fully tested by loading a project board with a cleared cache (or a project never visited before). The skeleton columns should appear immediately and then transition to real board data.

**Acceptance Scenarios**:

1. **Given** a user navigates to a project board with no cached data, **When** the board data is loading for the first time, **Then** skeleton placeholder columns are displayed matching the board's column grid layout (5 columns).
2. **Given** skeleton columns are displayed during initial load, **When** the board data finishes loading, **Then** the skeleton is replaced with the real board content in a smooth transition.
3. **Given** skeleton columns are displayed, **When** the user inspects the page with assistive technology, **Then** the skeleton region is announced as loading (via appropriate accessibility attributes).

---

### User Story 3 - Background Refetch Indicator (Priority: P3)

As a user viewing a board that is being refreshed in the background, I want a subtle visual indicator that data is updating, so that I am aware fresh data is coming without being blocked from interacting with the current board.

When background data refresh is happening (either from stale cache revalidation or periodic refetch), a non-intrusive "Updating…" indicator appears and the board dims slightly. Users can still click, scroll, and interact with the board during this time. Once fresh data arrives, the board restores to full opacity.

**Why this priority**: This is a polish feature that improves transparency without blocking the user. While the first two stories handle the major UX issues (spinner elimination), this story adds the finishing touch that communicates data freshness to power users.

**Independent Test**: Can be fully tested by viewing a cached board and triggering a background refetch. The indicator should appear, the board should dim slightly, and interaction should remain fully functional.

**Acceptance Scenarios**:

1. **Given** a user is viewing a board with cached data, **When** a background data refresh begins, **Then** a subtle "Updating…" indicator appears and the board dims to reduced opacity.
2. **Given** the board is dimmed during a background refresh, **When** the refresh completes successfully, **Then** the board restores to full opacity with updated data and the indicator disappears.
3. **Given** the board is dimmed during a background refresh, **When** the user clicks on a board card or column, **Then** the interaction works normally — the indicator does not block any user actions.
4. **Given** a background refresh is in progress, **When** the refresh fails, **Then** a non-blocking error notification is shown informing the user that the refresh failed, and the board continues to display the previously cached data at full opacity.

---

### User Story 4 - Project Switching with Stale Data Visibility (Priority: P2)

As a user switching between multiple project boards, I want the previous project's board to remain visible (dimmed) while the new project loads, so that I never see a blank screen or jarring spinner between projects.

When switching from Project A to Project B, instead of clearing the screen and showing a spinner, the system keeps Project A's board visible with a dimmed appearance and "Updating…" indicator until Project B's data loads and replaces it.

**Why this priority**: Multi-project users frequently switch between boards. This scenario bridges between the cache display (P1) and the refetch indicator (P3) and represents a key real-world workflow.

**Independent Test**: Can be fully tested by opening Project A's board, then switching to Project B via navigation. Project A's board should remain visible (dimmed) until Project B renders.

**Acceptance Scenarios**:

1. **Given** a user is viewing Project A's board, **When** they switch to Project B, **Then** Project A's board remains visible with reduced opacity and an "Updating…" indicator until Project B's data loads.
2. **Given** Project A's board is dimmed while Project B loads, **When** Project B's data finishes loading, **Then** Project B's board replaces Project A's board at full opacity with a smooth transition.

---

### Edge Cases

- What happens when the cache expires between visits? The board falls back to skeleton loading (Story 2 behavior), not a blank screen.
- What happens if the user's network is offline during a background refresh? The board continues showing the cached data at full opacity and a non-blocking error notification informs the user.
- What happens if a background refresh returns identical data to what is cached? The board should not visually flash or re-render; the transition from dimmed to full opacity should still occur smoothly.
- What happens if the user navigates away while a background refresh is in progress? The refresh should be cancelled or its result silently discarded without errors.
- What happens if the board has zero columns or the project has no board configured? The skeleton should not appear for an empty board; an appropriate empty state should be shown instead.
- What happens if multiple rapid project switches occur (e.g., clicking through Project A → B → C quickly)? Only the final project's board should render; intermediate requests should be cancelled.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST display previously cached board data immediately when a user navigates to a project board that has been visited within the cache window, with no loading spinner shown.
- **FR-002**: System MUST expose whether currently displayed data is from a stale cache or is fresh, so the UI can distinguish between cached and live data.
- **FR-003**: System MUST display a skeleton board layout (matching the real board's column grid) when loading a project board for the first time with no cached data available.
- **FR-004**: The skeleton board MUST consist of 5 placeholder columns that match the real board's column dimensions and CSS grid layout.
- **FR-005**: The skeleton board MUST include appropriate accessibility attributes to announce the loading state to assistive technologies.
- **FR-006**: System MUST replace the existing full-screen spinner with the skeleton board layout for initial board loads.
- **FR-007**: System MUST show a non-intrusive "Updating…" indicator when a background data refresh is in progress (either from stale cache revalidation or periodic refetch).
- **FR-008**: System MUST dim the board to reduced opacity during background refreshes to visually signal that data is being updated.
- **FR-009**: System MUST restore the board to full opacity with a smooth transition when fresh data arrives after a background refresh.
- **FR-010**: The background refetch indicator MUST NOT block any user interactions — users must be able to click, scroll, and interact with the board normally during a refresh.
- **FR-011**: System MUST show a non-blocking error notification when a background refresh fails, while continuing to display the previously cached data.
- **FR-012**: Initial load failures MUST continue to show the existing full error state (not the background refetch error pattern).
- **FR-013**: When switching projects, the system MUST keep the previous project's board visible (dimmed) until the new project's data loads, rather than showing a blank screen or spinner.

### Assumptions

- The backend cache layer is already functioning correctly and does not require changes for this feature.
- This feature is entirely frontend-scoped — no backend API changes are needed.
- Existing skeleton sub-components (column and card skeletons) are already built and match the real board's dimensions.
- The client-side cache window is 60 seconds (staleTime), which is an existing configuration.
- The board grid layout uses 5 columns by default.
- The existing toast/notification system is available for error notifications.
- No parallel fetching optimization or conditional request (ETag) changes are in scope.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Returning to a previously visited project board displays content in under 100 milliseconds (instant from cache), eliminating the full-screen spinner for cached visits.
- **SC-002**: First-time board loads show skeleton columns within 100 milliseconds of navigation, providing immediate spatial layout feedback.
- **SC-003**: Users can interact with the board (click cards, scroll columns) without interruption during 100% of background refresh cycles.
- **SC-004**: Background refresh failures display a non-blocking notification within 2 seconds of failure, and the board remains fully usable with cached data.
- **SC-005**: Project switching never shows a blank screen or full-screen spinner — the previous board remains visible until the new board is ready.
- **SC-006**: The skeleton board is accessible, with assistive technologies correctly announcing the loading state.
- **SC-007**: All existing board functionality (viewing, interacting, navigating) continues to work identically after this change — no regressions introduced.
- **SC-008**: The feature passes all existing automated checks (linting, type checking, unit tests, and build) without modifications to existing tests.
