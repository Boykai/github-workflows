# Feature Specification: Recent Interactions — Filter Deleted Items & Display Only Parent Issues with Project Board Status Colors

**Feature Branch**: `026-recent-interactions-filter`  
**Created**: 2026-03-07  
**Status**: Draft  
**Input**: User description: "If items are deleted from Clean Up or otherwise, Recent Interactions should remove any deleted items and display only current items. These should ONLY be GitHub Issue PARENT ISSUES. Display them in themed colors to show their current status from project board."

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Automatic Removal of Deleted Items (Priority: P1)

As a user managing GitHub Issues, I want deleted issues to be automatically removed from the Recent Interactions panel so that I never see stale or orphaned entries that no longer exist in the repository.

When I delete an issue through the Clean Up feature, or when an issue is removed by any other means, the Recent Interactions panel should no longer display that item. On the next render or page load, the deleted entry must be gone. This applies regardless of how or when the deletion occurred — the panel must always reflect only issues that currently exist.

**Why this priority**: Displaying deleted or non-existent items is the most critical data-integrity problem. Users lose trust in the panel when it shows items that no longer exist, making it unusable as a quick-reference tool. This is the foundational behavior all other stories depend on.

**Independent Test**: Can be fully tested by deleting an issue (via Clean Up or directly) and verifying the Recent Interactions panel no longer shows that item after a page refresh or re-render.

**Acceptance Scenarios**:

1. **Given** the Recent Interactions panel displays issues A, B, and C, **When** issue B is deleted via the Clean Up feature, **Then** the panel no longer shows issue B on the next render.
2. **Given** the Recent Interactions panel displays issues A, B, and C, **When** issue C is deleted by any means other than Clean Up (e.g., direct deletion), **Then** the panel no longer shows issue C on the next render.
3. **Given** the Recent Interactions panel has cached references to issues D and E, **When** the user refreshes the page and issue D no longer exists, **Then** issue D is removed from the panel and does not reappear in subsequent sessions.

---

### User Story 2 — Display Only Parent Issues (Priority: P1)

As a user, I want the Recent Interactions panel to exclusively show GitHub Issue Parent Issues so that my view is not cluttered with sub-issues, pull requests, commits, or other non-parent item types.

The panel must filter out any item that is not a Parent Issue. Sub-issues (issues that have a parent), pull requests, commits, and any other non-issue item types must be excluded entirely. Only top-level GitHub Issues that do not have a parent issue should appear.

**Why this priority**: Equally critical to P1 — showing the wrong item types defeats the purpose of the panel. Users need a focused view of top-level work items to manage their workflow. Without this filter, the panel is a noisy list instead of an actionable overview.

**Independent Test**: Can be fully tested by interacting with a mix of parent issues, sub-issues, pull requests, and commits, then verifying that only parent issues appear in the Recent Interactions panel.

**Acceptance Scenarios**:

1. **Given** the user has recently interacted with parent issue #10, sub-issue #11 (child of #10), and pull request #12, **When** the Recent Interactions panel renders, **Then** only parent issue #10 is displayed.
2. **Given** the user has recently interacted with only sub-issues and pull requests, **When** the Recent Interactions panel renders, **Then** the panel shows an empty state message instead of any items.
3. **Given** a previously parentless issue #20 becomes a sub-issue of issue #15, **When** the Recent Interactions panel re-renders, **Then** issue #20 is no longer displayed (because it is now a sub-issue), and issue #15 is displayed if the user has interacted with it.

---

### User Story 3 — Project Board Status Colors (Priority: P2)

As a user, I want each Parent Issue in the Recent Interactions panel to be color-coded according to its current status on the project board so that I can immediately understand each issue's workflow state at a glance.

Each issue entry should display a visual color indicator (such as a background chip, left border accent, or badge) that corresponds to its project board status. The color mapping should follow a consistent, intuitive scheme — for example, neutral/grey for "Todo," blue for "In Progress," yellow/amber for "In Review," green for "Done," and red for "Blocked." The colors must align with the existing design system and update when an issue's status changes.

**Why this priority**: While not as foundational as filtering, status colors provide significant at-a-glance value. They transform the panel from a simple list into a workflow dashboard. This is a P2 because it enhances usability but the panel is still functional without it.

**Independent Test**: Can be fully tested by placing parent issues in different project board columns (Todo, In Progress, In Review, Done, Blocked) and verifying each displays the correct corresponding color in the Recent Interactions panel.

**Acceptance Scenarios**:

1. **Given** parent issue #30 is in the "In Progress" column on the project board, **When** the Recent Interactions panel renders, **Then** issue #30 is displayed with the "In Progress" themed color (blue).
2. **Given** parent issue #30 moves from "In Progress" to "Done" on the project board, **When** the Recent Interactions panel re-renders, **Then** issue #30 now displays the "Done" themed color (green).
3. **Given** parent issue #40 has no project board status or the status is unavailable, **When** the Recent Interactions panel renders, **Then** issue #40 is displayed with a neutral/default fallback color.

---

### User Story 4 — Empty State Messaging (Priority: P3)

As a user, I want to see a clear, friendly empty state message when the Recent Interactions panel has no valid Parent Issues to display so that I understand the panel is working correctly rather than broken.

When all items have been filtered out (e.g., all were deleted, all were sub-issues, or the user has no recent interactions), the panel should display an informative empty state message instead of showing a blank area.

**Why this priority**: Empty state messaging is a usability polish item. The panel functions correctly without it, but an empty blank space can confuse users into thinking the feature is broken. This is important for user experience but not blocking.

**Independent Test**: Can be fully tested by ensuring the user has no valid parent issues in Recent Interactions (e.g., all deleted or all sub-issues) and verifying the empty state message appears.

**Acceptance Scenarios**:

1. **Given** the user has no recent interactions at all, **When** the Recent Interactions panel renders, **Then** an empty state message is displayed (e.g., "No recent parent issues to display").
2. **Given** the user's only recent interactions were with sub-issues and pull requests, **When** the Recent Interactions panel renders, **Then** the empty state message is displayed because no valid parent issues exist.
3. **Given** the user had parent issues in Recent Interactions but all were subsequently deleted, **When** the panel re-renders after deletion, **Then** the empty state message is displayed.

---

### Edge Cases

- What happens when a parent issue is deleted between the time the list is loaded and when the user interacts with it? The entry should be gracefully removed with no error shown to the user.
- What happens when the project board status field has a custom label not in the predefined color map? The system should apply the neutral/default fallback color.
- What happens when the project board itself is deleted or the issue is removed from the project? The system should treat the status as unavailable and apply the fallback color.
- What happens when multiple project boards assign different statuses to the same issue? The system should use the status from the primary/default project board associated with the repository.
- What happens when network connectivity is intermittent and the live validation of issues fails? The system should retain the last known valid state and retry validation on the next render cycle, rather than clearing all items.
- What happens when the Recent Interactions cache contains hundreds of items? The system should validate items efficiently, with reasonable performance even for large caches (e.g., batch validation rather than one-by-one).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST remove any issue from the Recent Interactions panel that has been deleted, regardless of whether the deletion originated from the Clean Up feature or any other deletion pathway.
- **FR-002**: System MUST validate cached Recent Interactions entries against live data to detect deletions before rendering the panel.
- **FR-003**: System MUST ensure that stale or orphaned references to deleted issues do not persist in Recent Interactions across page refreshes or session reloads.
- **FR-004**: System MUST filter Recent Interactions to display ONLY GitHub Issue Parent Issues — sub-issues, pull requests, commits, and all other non-parent item types MUST be excluded from the list.
- **FR-005**: System MUST determine whether an issue is a parent issue by confirming it does not have a parent reference (i.e., it is a top-level issue, not a sub-issue of another issue).
- **FR-006**: System MUST fetch and display the current project board status for each Parent Issue shown in Recent Interactions.
- **FR-007**: System MUST apply a distinct themed color to each Recent Interactions entry corresponding to the issue's current project board status column, using the following default mapping:
  - "Todo" → neutral/grey
  - "In Progress" → blue
  - "In Review" → yellow/amber
  - "Done" → green
  - "Blocked" → red
- **FR-008**: System MUST update displayed status colors when an issue's project board status changes, without requiring a full page reload (on next render cycle or panel refresh).
- **FR-009**: System MUST display an empty state UI with appropriate messaging when the Recent Interactions panel contains no valid, non-deleted Parent Issues.
- **FR-010**: System SHOULD render a neutral/default fallback color when a Parent Issue's project board status is undefined, unavailable, or does not match any entry in the color mapping.
- **FR-011**: System SHOULD handle network errors or unavailable data sources gracefully by retaining the last known valid state of the panel and retrying on the next render cycle.

### Key Entities

- **Recent Interaction Entry**: A cached reference to an issue the user recently viewed or interacted with. Key attributes: issue identifier, timestamp of interaction, cached display title.
- **Parent Issue**: A GitHub Issue that is a top-level item — it has no parent issue. It may or may not have sub-issues beneath it. Key attributes: issue number, title, open/closed state, project board status.
- **Project Board Status**: The current workflow column/status assigned to an issue on the project board. Key attributes: status label (e.g., "Todo," "In Progress," "Done"), associated color token.
- **Status Color Map**: A configuration mapping that translates project board status labels to visual color tokens from the design system. Key attributes: status label, color token/value, fallback color.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of deleted issues are removed from the Recent Interactions panel within one render cycle (page load or panel refresh) — zero stale entries persist.
- **SC-002**: 100% of displayed items in the Recent Interactions panel are verified Parent Issues — no sub-issues, pull requests, commits, or other item types appear.
- **SC-003**: Each Parent Issue in the panel displays the correct project board status color that matches its current column assignment, with updates reflected within one render cycle of a status change.
- **SC-004**: Users can identify an issue's workflow state at a glance within 2 seconds by its color coding, without needing to open or hover over the item.
- **SC-005**: The empty state message is displayed whenever the panel has zero valid Parent Issues, with no blank or broken-looking UI state.
- **SC-006**: The panel renders within 3 seconds even when validating up to 50 cached interaction entries, maintaining a responsive user experience.
- **SC-007**: Issues with unknown or unavailable project board statuses display a clear fallback color rather than appearing broken or uncolored.

## Assumptions

- The application already has a Recent Interactions panel that displays a cached list of recently viewed or interacted items. This feature modifies its filtering and display behavior.
- The existing design system provides color tokens that can be mapped to project board statuses. The status color map will use existing tokens where possible.
- Parent Issues are identified by the absence of a parent reference — any issue that is not a sub-issue of another issue is considered a parent issue.
- The primary project board associated with the repository is the authoritative source for issue status colors. If an issue exists on multiple boards, the primary board's status takes precedence.
- Standard web application performance expectations apply (e.g., panel loads within 3 seconds, no visible jank during re-renders).
- Data validation occurs at render time or on a reasonable refresh interval — real-time websocket push updates are not required but may be implemented as an optimization.
