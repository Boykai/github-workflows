# Feature Specification: Real-Time GitHub Project Board

**Feature Branch**: `001-github-project-board`  
**Created**: February 16, 2026  
**Status**: Draft  
**Input**: User description: "Add a new standalone page/route (/project-board) to the app that displays a real-time GitHub Project Board populated with live data from the GitHub Projects V2 GraphQL API"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - View Project Board with Live Data (Priority: P1)

As an authenticated user, I want to navigate to the Project Board page and see a Kanban-style board populated with my GitHub Project's data, so I can visualize my project's current status at a glance without leaving the application.

**Why this priority**: This is the core value proposition of the feature. Without the ability to view a project board with real data, no other functionality has meaning. Users need to see their project's columns, issues, and metadata in a visual board format.

**Independent Test**: Can be fully tested by navigating to /project-board, selecting a project from the dropdown, and verifying the board displays columns with issue cards containing all required metadata (title, assignees, priority, size, estimate, linked PRs).

**Acceptance Scenarios**:

1. **Given** I am an authenticated user on any page, **When** I click the "Project Board" link in the sidebar navigation, **Then** I am navigated to the /project-board route and see a project selector dropdown.

2. **Given** I am on the Project Board page, **When** I click the project selector dropdown, **Then** I see a list of all GitHub Projects I have access to (both owned and member projects).

3. **Given** I have selected a project from the dropdown, **When** the board loads, **Then** I see horizontal columns representing the project's status field values (e.g., Backlog, Ready, In progress, In review, Done).

4. **Given** the board has loaded, **When** I view a column header, **Then** I see a colored status dot, column name, total item count for that column, aggregate estimate total, and column description subtitle.

5. **Given** the board has loaded, **When** I view an issue card, **Then** I see the repository name, issue number, issue title, assignee avatar(s) in the top-right corner, and badges for Priority, Size, and Estimate values.

6. **Given** an issue has a linked pull request, **When** I view that issue card, **Then** I see a PR badge showing the linked PR number.

---

### User Story 2 - View Issue Details in Modal (Priority: P2)

As a user viewing the project board, I want to click on an issue card to see expanded details in a modal, so I can quickly review issue information without navigating away from the board view.

**Why this priority**: Once users can see the board, the natural next action is wanting more details about specific issues. This enhances the usefulness of the board without requiring users to leave the app.

**Independent Test**: Can be tested by clicking any issue card and verifying the modal opens with expanded issue information and includes a link to open the issue on GitHub.

**Acceptance Scenarios**:

1. **Given** I am viewing the project board with issue cards, **When** I click on an issue card, **Then** a modal opens displaying expanded issue information.

2. **Given** the issue detail modal is open, **When** I view the modal content, **Then** I see the full issue title, description summary, all custom field values, assignees, and linked PR information.

3. **Given** the issue detail modal is open, **When** I click the "Open in GitHub" link, **Then** the issue page opens on github.com in a new browser tab.

4. **Given** the issue detail modal is open, **When** I click outside the modal or press Escape or click a close button, **Then** the modal closes and I return to the board view.

---

### User Story 3 - Auto-Refresh Board Data (Priority: P3)

As a user viewing the project board, I want the board data to automatically refresh every 15 seconds, so I see the most current project status without manually refreshing the page.

**Why this priority**: Real-time updates enhance the user experience but are not critical for the board to be functional. Users could manually refresh, but auto-refresh provides a better experience for monitoring project progress.

**Independent Test**: Can be tested by observing the board for 15+ seconds, making a change to an issue in GitHub directly, and verifying the board reflects the change on the next refresh cycle.

**Acceptance Scenarios**:

1. **Given** I am viewing a project board, **When** 15 seconds elapse since the last data fetch, **Then** the board data is automatically refreshed from the API.

2. **Given** data is being refreshed, **When** the refresh is in progress, **Then** I see a subtle loading indicator that does not disrupt my view of the current data.

3. **Given** the auto-refresh fails due to a network error, **When** the error occurs, **Then** I see an appropriate error message and the board retains the previously loaded data.

---

### Edge Cases

- What happens when the user has no GitHub Projects? The board displays a helpful empty state message indicating no projects are available.
- What happens when a selected project has no items? The board displays empty columns with zero counts.
- What happens when the GitHub API is unavailable or returns an error? An error message is displayed with a retry option, and any previously loaded data is retained.
- What happens when an issue has no assignees? The assignee avatar area displays a default placeholder or is hidden.
- What happens when custom fields (Priority, Size, Estimate) are not configured on a project? Those badge areas display as empty or with a default "—" indicator.
- What happens when the user's authentication token expires during a session? An appropriate authentication error is displayed with guidance to re-authenticate.
- What happens when a column has many items (e.g., 50+ issues)? The column is scrollable to accommodate all cards without breaking the layout.

## Requirements *(mandatory)*

### Functional Requirements

#### Navigation & Page Structure
- **FR-001**: System MUST provide a "Project Board" link in the existing sidebar navigation.
- **FR-002**: System MUST render a dedicated page at the `/project-board` route.
- **FR-003**: System MUST display a project selector dropdown at the top of the Project Board page.

#### Project Discovery
- **FR-004**: System MUST fetch all GitHub Projects accessible to the authenticated user via the GitHub Projects V2 GraphQL API.
- **FR-005**: System MUST display project names in the dropdown selector for user selection.
- **FR-006**: System MUST use the user's authenticated GitHub OAuth access token (from session) for API authentication.

#### Board Display
- **FR-007**: System MUST render a Kanban-style board with horizontal columns representing the project's status field values.
- **FR-008**: Each column header MUST display: colored status dot matching the column's status color, column name, total item count for that column (e.g., "5"), aggregate estimate total, and column description subtitle.
- **FR-009**: Issue cards MUST display: repository name, issue number, issue title, assignee avatar(s) in the top-right corner, Priority badge with color coding, Size badge with color coding, and Estimate value badge.
- **FR-010**: Issue cards with linked pull requests MUST display a PR badge showing the linked PR number.

#### Backend API
- **FR-011**: Backend MUST provide an endpoint to list all available GitHub Projects for the authenticated user.
- **FR-012**: Backend MUST provide an endpoint to fetch a specific project's board data including columns/status field values, all items with issue details (title, number, repository, assignees, URL), and custom field values (Priority, Size, Estimate).
- **FR-013**: Backend MUST fetch linked PR data for each issue when retrieving board data.

#### Issue Detail Modal
- **FR-014**: System MUST open a detail modal when a user clicks an issue card.
- **FR-015**: The modal MUST display expanded issue information including full title, description, all custom fields, assignees, and linked PR details.
- **FR-016**: The modal MUST include a link that opens the issue/PR on github.com in a new browser tab.
- **FR-017**: The modal MUST be dismissible via clicking outside, pressing Escape, or clicking a close button.

#### Auto-Refresh
- **FR-018**: System MUST automatically refresh board data every 15 seconds via polling.
- **FR-019**: System MUST display appropriate loading states during data fetching.
- **FR-020**: System MUST display appropriate error states when API requests fail.

#### Styling
- **FR-021**: System MUST style the board using the existing app's design system and styling patterns.

### Key Entities

- **Project**: A GitHub Project V2 containing board configuration and items. Key attributes: name, ID, description, columns/status field definition.
- **Column/Status**: A status value within a project that groups items. Key attributes: name, color, description, position order.
- **BoardItem**: An issue, draft issue, or pull request within a project. Key attributes: title, number, repository name, assignees, URL, custom field values (Priority, Size, Estimate), linked pull requests.
- **Custom Field Value**: A project-specific field value applied to an issue. Key attributes: field name (Priority/Size/Estimate), value, color (for Priority and Size).
- **Assignee**: A GitHub user assigned to an issue. Key attributes: username, avatar URL.
- **Linked Pull Request**: A PR associated with an issue. Key attributes: PR number, URL.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can navigate to the Project Board page and view a populated board within 5 seconds of selecting a project.
- **SC-002**: The board displays all columns defined in the GitHub Project's status field with correct names and colors.
- **SC-003**: 100% of issues in the selected project are displayed as cards in their correct status columns.
- **SC-004**: Users can view expanded issue details by clicking any card and access the GitHub link within 2 clicks from the board.
- **SC-005**: Board data refreshes automatically every 15 seconds without user intervention.
- **SC-006**: The board remains usable and displays meaningful error messages when the GitHub API is temporarily unavailable.
- **SC-007**: Users can identify issue priority, size, and estimate at a glance from card badges without opening the detail modal.

## Assumptions

- Users are already authenticated with GitHub via the existing app authentication flow.
- The existing GITHUB_TOKEN has sufficient permissions to access GitHub Projects V2 GraphQL API.
- GitHub Projects being accessed have the Status field configured (standard for GitHub Projects V2).
- Custom fields (Priority, Size, Estimate) may or may not exist on each project; the UI handles missing fields gracefully.
- The existing app uses Tailwind CSS for styling and the new components will follow established patterns.
- The app has an existing sidebar navigation component where the new link will be added.

## Clarifications

### Session 2026-02-16

- Q: What defines an item as "completed" within a column for the item count display? → A: Display total item count per column only, not a completed/total ratio.

## Out of Scope

- Filtering, searching, or sorting within the board view.
- Drag-and-drop functionality to move cards between columns.
- Editing issues or project fields from within the app.
- Support for multiple status fields (single Status field per project).
- Caching of project data beyond the current session.
- Keyboard navigation within the board.
