# Feature Specification: Standalone Project Board Page

**Feature Branch**: `003-project-board`  
**Created**: 2026-02-16  
**Status**: Draft  
**Input**: User description: "Implement standalone /project-board page with real-time GitHub Project Board integration"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - View Project Board (Priority: P1)

As an authenticated user, I want to select a GitHub Project and view its issues in a Kanban-style board layout so that I can quickly understand the current status of all work items at a glance.

The user navigates to the /project-board page via the sidebar navigation. At the top of the page, a dropdown lists all available GitHub Projects for the authenticated user. Upon selecting a project, the board renders with horizontal columns representing the project's status fields (e.g., "Todo", "In Progress", "Done"). Each column displays a colored status dot, the column name, the count of items in that column, an aggregate of story point estimates, and a brief description. Issue cards within each column show the repository name and issue number, the issue title, assignee avatars, a linked pull request badge (when applicable), and badges for priority, estimate, and size with appropriate color coding.

**Why this priority**: This is the core feature — without the ability to view the board, no other functionality is useful. It provides immediate value by giving users a visual overview of their project's progress.

**Independent Test**: Can be fully tested by navigating to /project-board, selecting a project from the dropdown, and verifying that columns and issue cards render correctly with all required data fields.

**Acceptance Scenarios**:

1. **Given** the user is authenticated and has at least one GitHub Project, **When** they navigate to /project-board, **Then** a dropdown appears listing all their available GitHub Projects.
2. **Given** the user has selected a project from the dropdown, **When** the board loads, **Then** columns appear for each status field showing colored status dots, column names, item counts, aggregate estimates, and descriptions.
3. **Given** a column contains issues, **When** the board renders, **Then** each issue card displays the repository name/issue number, title, assignee avatars, linked PR badge (if applicable), and priority/estimate/size badges with color coding.
4. **Given** the user has no GitHub Projects, **When** they navigate to /project-board, **Then** an empty state message is displayed explaining that no projects are available.

---

### User Story 2 - View Issue Details (Priority: P2)

As an authenticated user, I want to click on an issue card to see expanded details and navigate to GitHub so that I can review the full context of an issue without leaving the app and quickly jump to GitHub when needed.

When the user clicks an issue card on the board, a detail modal opens. The modal displays expanded issue information including the full title, description summary, assignees, linked pull requests, priority, estimate, size, and status. A prominent link allows the user to open the issue or pull request directly on github.com in a new browser tab. The modal can be closed by clicking outside it, pressing Escape, or clicking a close button.

**Why this priority**: Viewing details is the natural next step after seeing the board — it deepens the user's ability to understand individual work items without context-switching to GitHub for every issue.

**Independent Test**: Can be fully tested by clicking any issue card on a loaded board and verifying the modal appears with correct expanded details and a working link to github.com.

**Acceptance Scenarios**:

1. **Given** the board is loaded with issue cards, **When** the user clicks an issue card, **Then** a detail modal opens displaying expanded issue information (title, description summary, assignees, linked PRs, priority, estimate, size, status).
2. **Given** the detail modal is open, **When** the user clicks the "Open on GitHub" link, **Then** the issue or PR page opens on github.com in a new browser tab.
3. **Given** the detail modal is open, **When** the user clicks outside the modal, presses Escape, or clicks the close button, **Then** the modal closes and the board is visible again.

---

### User Story 3 - Auto-Refresh Board Data (Priority: P3)

As an authenticated user, I want the board to automatically refresh every 15 seconds so that I always see the most up-to-date project status without manually reloading the page.

The board data refreshes automatically every 15 seconds in the background. During refresh, a subtle loading indicator appears (without disrupting the current view). If a refresh fails due to a network or server error, an error notification is displayed with the option to retry. The auto-refresh pauses when the detail modal is open and resumes when the modal is closed.

**Why this priority**: Real-time data is important but secondary to the core viewing experience. The board is still valuable with manual refresh; auto-refresh adds polish and keeps data current.

**Independent Test**: Can be fully tested by loading a board, waiting 15 seconds, and verifying that data updates appear automatically, and that error states display correctly when the connection is interrupted.

**Acceptance Scenarios**:

1. **Given** the board is loaded with a selected project, **When** 15 seconds elapse, **Then** the board data refreshes automatically with a subtle loading indicator visible during the refresh.
2. **Given** the auto-refresh triggers, **When** the refresh succeeds, **Then** the board updates with the latest data without disrupting the user's scroll position or view state.
3. **Given** the auto-refresh triggers, **When** the refresh fails (network error, server error), **Then** an error notification is displayed with a retry option.
4. **Given** the detail modal is open, **When** 15 seconds elapse, **Then** the auto-refresh is paused until the modal is closed.

---

### User Story 4 - Loading and Error States (Priority: P4)

As an authenticated user, I want to see clear loading indicators and helpful error messages so that I understand what the system is doing and can take action when something goes wrong.

When the page first loads or a project is selected, a loading skeleton or spinner is displayed while data is being fetched. If the initial data fetch fails, an error state is shown with a clear message explaining the problem and a button to retry. If the user's authentication token is invalid or expired, a message prompts them to re-authenticate.

**Why this priority**: Loading and error states are essential for a polished user experience, but the core board functionality (US1) must work first.

**Independent Test**: Can be fully tested by simulating slow network conditions to verify loading states appear, and by simulating server errors to verify error messages and retry functionality.

**Acceptance Scenarios**:

1. **Given** the user navigates to /project-board, **When** the project list is loading, **Then** a loading indicator is displayed.
2. **Given** the user selects a project, **When** the board data is loading, **Then** a loading skeleton or spinner is displayed in the board area.
3. **Given** the data fetch fails, **When** the error state is displayed, **Then** the user sees a clear error message and a retry button.
4. **Given** the user's authentication token is invalid, **When** the page tries to load data, **Then** a message prompts the user to re-authenticate.

---

### Edge Cases

- What happens when a project has no status fields configured? The board displays an empty state message explaining that the project has no status columns configured.
- What happens when an issue has no assignees, no linked PRs, or missing priority/estimate/size fields? The card renders without those elements, showing only available data (no blank spaces or broken layouts).
- What happens when the user has a very large number of projects (50+)? The project dropdown supports scrolling and remains performant.
- What happens when a column has a very large number of issues (100+)? The column supports scrolling and the board remains responsive.
- What happens when the user loses network connectivity while viewing the board? The board retains the last successfully loaded data and displays a connectivity warning.
- What happens when a project is deleted or the user loses access while viewing? The next refresh shows an appropriate error message and prompts the user to select a different project.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide a /project-board route accessible via the sidebar navigation.
- **FR-002**: System MUST display a dropdown listing all available GitHub Projects for the authenticated user.
- **FR-003**: System MUST render a Kanban-style board with columns representing status fields upon project selection.
- **FR-004**: Each column MUST display a colored status dot, column name, item count, aggregate estimate, and description.
- **FR-005**: Each issue card MUST display the repository name and issue number, issue title, and assignee avatars.
- **FR-006**: Each issue card MUST display a linked pull request badge when a linked PR exists.
- **FR-007**: Each issue card MUST display priority, estimate, and size badges with appropriate color coding.
- **FR-008**: System MUST open a detail modal when an issue card is clicked, showing expanded issue information.
- **FR-009**: The detail modal MUST include a link to open the issue or PR on github.com in a new browser tab.
- **FR-010**: System MUST auto-refresh the board data every 15 seconds while the board is visible.
- **FR-011**: System MUST pause auto-refresh when the detail modal is open and resume when it is closed.
- **FR-012**: System MUST display a loading indicator while fetching project list and board data.
- **FR-013**: System MUST display an error message with a retry option when data fetching fails.
- **FR-014**: System MUST provide backend endpoints that proxy GitHub Projects V2 requests, including listing projects, fetching board data, and retrieving linked pull requests, authenticated via a GitHub token.
- **FR-015**: System MUST extend data types to support priority, size, estimate, linked PRs, assignee avatars, and repository name.
- **FR-016**: The board styling MUST match the application's existing design system.

### Key Entities

- **Project**: Represents a GitHub Project V2. Attributes include project ID, title, and description. A project contains multiple status columns.
- **Status Column**: Represents a status field within a project (e.g., "Todo", "In Progress", "Done"). Attributes include column name, color, description, item count, and aggregate estimate. A column contains multiple issue cards.
- **Issue Card**: Represents an issue or draft issue within a project column. Attributes include repository name, issue number, title, assignees (with avatars), linked pull requests, priority, estimate, size, and status.
- **Linked Pull Request**: Represents a pull request linked to an issue. Attributes include PR number, title, state (open, closed, merged), and URL.
- **Assignee**: Represents a user assigned to an issue. Attributes include username and avatar URL.

## Assumptions

- The application already has an authentication mechanism that provides a valid GitHub token for API access.
- The sidebar navigation already exists and can be extended with new route links.
- The application uses a component-based frontend architecture with an existing design system and styling framework.
- GitHub Projects V2 GraphQL API is used for all project data retrieval.
- The GitHub token has sufficient scopes (read:project, repo) to access the user's project boards.
- Performance targets follow standard web application expectations: initial page load under 3 seconds, dropdown interaction under 1 second.
- Error messages are user-friendly and do not expose technical details or tokens.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can navigate to the project board page and see their available projects listed within 3 seconds of page load.
- **SC-002**: Users can select a project and see the full Kanban board rendered within 3 seconds.
- **SC-003**: Users can click any issue card and see the detail modal open within 1 second.
- **SC-004**: The board data refreshes automatically every 15 seconds without user intervention.
- **SC-005**: 100% of issue cards display all available data fields (repo name, issue number, title, assignees, linked PR badge, priority, estimate, size) without layout breakage.
- **SC-006**: Users can open any issue on github.com from the detail modal in one click.
- **SC-007**: When a data fetch fails, users see a clear error message and can retry within one click.
- **SC-008**: The board remains usable and responsive with projects containing up to 100 issues across all columns.
