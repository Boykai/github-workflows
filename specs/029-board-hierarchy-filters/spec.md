# Feature Specification: Project Board — Parent Issue Hierarchy, Sub-Issue Display, Agent Pipeline Fixes & Functional Filters

**Feature Branch**: `029-board-hierarchy-filters`  
**Created**: 2026-03-07  
**Status**: Draft  
**Input**: User description: "Project Board: Parent Issue Hierarchy, Sub-Issue Display Improvements, Agent Pipeline Fixes & Functional Filters"

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Parent-Only Project Board with Collapsible Sub-Issues (Priority: P1)

A project manager opens the Project Board and sees only top-level parent GitHub Issues as cards in each column. Sub-issues no longer clutter the board as separate cards. Each parent card shows a toggle control (chevron icon with a sub-issue count badge). Clicking the toggle expands a nested list of sub-issues directly within the parent card. Each sub-issue tile in the expanded list shows the assigned Agent name and Model name. Clicking the toggle again collapses the sub-issue list. The sub-issue list is collapsed by default on page load.

**Why this priority**: This is the core structural change to the Project Board. Showing only parent issues as top-level cards fundamentally reorganizes the board for clarity and usability. All other features (filters, sorting, grouping) operate on this parent-issue-only view, making this the foundation for the entire feature set.

**Independent Test**: Can be fully tested by loading a project with parent issues that have sub-issues, confirming only parent issues appear as top-level cards, expanding a parent card to see sub-issues with agent/model metadata, and collapsing it again.

**Acceptance Scenarios**:

1. **Given** a project board with 5 parent issues and 12 sub-issues across all columns, **When** the board renders, **Then** only the 5 parent issues appear as top-level cards — no sub-issues are shown as standalone cards.
2. **Given** a parent issue card with 3 sub-issues, **When** the user clicks the expand toggle, **Then** a nested list of 3 sub-issue tiles appears within the parent card, each showing the assigned Agent name and Model name.
3. **Given** an expanded parent issue card, **When** the user clicks the collapse toggle, **Then** the sub-issue list collapses and only the parent card with the count badge remains visible.
4. **Given** a parent issue card with sub-issues, **When** the board initially loads, **Then** the sub-issue list is collapsed by default and the count badge shows the number of sub-issues (e.g., "3 sub-issues").
5. **Given** a sub-issue that has no assigned agent or model, **When** the sub-issue tile renders inside the expanded parent card, **Then** the agent and model fields display gracefully as "Unassigned" or are omitted without leaving empty space.

---

### User Story 2 — Parent Issue Labels on Board Cards (Priority: P1)

A project manager views the Project Board and each parent issue card displays all of its associated GitHub labels as colored chips. The label chips use the label's configured color from GitHub and show the label name. This allows the project manager to quickly scan the board and identify issue categories, priorities, or tags at a glance without opening any card.

**Why this priority**: Labels are a primary organizational tool in GitHub. Displaying them directly on board cards is essential for quick visual triage and complements the parent-only board view by providing immediate context about each issue.

**Independent Test**: Can be fully tested by loading a project board where parent issues have GitHub labels, and confirming each card displays the correct colored label chips matching the labels assigned on GitHub.

**Acceptance Scenarios**:

1. **Given** a parent issue with labels "enhancement" (blue) and "p1" (red), **When** the parent card renders on the board, **Then** both labels appear as colored chips with the correct GitHub-configured colors and names.
2. **Given** a parent issue with no labels, **When** the parent card renders, **Then** no label section is shown on the card (no empty placeholder or "No labels" text).
3. **Given** a parent issue with more than 5 labels, **When** the parent card renders, **Then** all labels are displayed without overflowing the card layout (wrapping to a new line if needed).

---

### User Story 3 — Scrollable Project Board Columns (Priority: P1)

A project manager views a Project Board where one or more columns contain many parent issue cards. Each column is independently scrollable, so the user can scroll within a single column to find a specific card without affecting the scroll position of other columns or the page as a whole.

**Why this priority**: Without independent column scrolling, tall columns cause the entire page to scroll, making it difficult to navigate the board and compare issues across columns. This is a fundamental usability requirement for any kanban-style board.

**Independent Test**: Can be fully tested by loading a project board with at least one column containing more cards than can fit in the viewport, and confirming that column scrolls independently while other columns and the page remain stationary.

**Acceptance Scenarios**:

1. **Given** a project board where the "In Progress" column has 15 parent issue cards, **When** the user scrolls within the "In Progress" column, **Then** only that column scrolls — other columns and the page header remain stationary.
2. **Given** all columns have few cards that fit within the viewport, **When** the user views the board, **Then** no scrollbars appear on the columns.
3. **Given** multiple columns have overflowing content, **When** the user scrolls one column, **Then** the other columns' scroll positions are unaffected.

---

### User Story 4 — Agent Pipeline Model & Tool Count Fixes (Priority: P2)

A project manager views the Agent Pipeline panel and every agent tile correctly displays the associated model name (e.g., "GPT-4o", "Claude 3.5 Sonnet") and the tool count (e.g., "5 tools"). No models are missing from the display and no tool counts are incorrectly showing zero or are absent when tools are configured. This resolves existing data-binding bugs where some agent tiles were missing this information.

**Why this priority**: Accurate display of model names and tool counts is essential for project managers to understand the capabilities of each agent in the pipeline. Missing information leads to confusion and erodes trust in the pipeline configuration UI.

**Independent Test**: Can be fully tested by loading a project with an Agent Pipeline where agents have configured models and tools, and verifying every agent tile shows the correct model name and tool count — with no omissions.

**Acceptance Scenarios**:

1. **Given** an Agent Pipeline with 6 agents, each configured with a model and at least 1 tool, **When** the pipeline renders, **Then** all 6 agent tiles display their model name and correct tool count.
2. **Given** an agent configured with model "Claude 3.5 Sonnet" and 8 tools, **When** the agent tile renders, **Then** the tile shows "Claude 3.5 Sonnet" as the model and "8 tools" as the tool count.
3. **Given** an agent with no model configured but 3 tools, **When** the agent tile renders, **Then** the model field is omitted gracefully and the tool count "3 tools" still displays.
4. **Given** an agent with a model configured but 0 tools, **When** the agent tile renders, **Then** the model name displays and the tool count shows "0 tools" or is omitted gracefully.

---

### User Story 5 — Custom Pipeline Label Updates to Saved Configuration Name (Priority: P2)

A project manager views the Agent Pipeline section and sees the label "Custom" displayed when no saved pipeline configuration is active. When the user selects a saved pipeline configuration (e.g., "Frontend Review Pipeline"), the "Custom" label dynamically updates to display the selected configuration's name. If the user deselects or modifies the configuration such that it no longer matches a saved configuration, the label reverts to "Custom."

**Why this priority**: Clearly displaying the active pipeline configuration name helps users understand which configuration is in effect. The static "Custom" label is misleading when a named configuration is active.

**Independent Test**: Can be fully tested by loading a project with saved pipeline configurations, selecting one, and confirming the label updates from "Custom" to the configuration name — then deselecting to confirm it reverts.

**Acceptance Scenarios**:

1. **Given** no saved pipeline configuration is selected, **When** the Agent Pipeline section renders, **Then** the pipeline label displays "Custom."
2. **Given** the user selects a saved configuration named "Frontend Review Pipeline," **When** the selection is applied, **Then** the pipeline label updates to "Frontend Review Pipeline."
3. **Given** a saved configuration is active and the user deselects it or makes manual changes that diverge from the saved configuration, **When** the pipeline renders, **Then** the label reverts to "Custom."
4. **Given** the user selects a saved configuration and refreshes the page, **When** the page reloads, **Then** the pipeline label still displays the saved configuration name (selection persists).

---

### User Story 6 — Functional Filter Controls on the Project Board (Priority: P2)

A project manager clicks the "Filter" button on the Project Board toolbar. A filter panel opens, allowing the user to filter the displayed parent issue cards by one or more criteria: label, assignee, status, or milestone. Selecting filter criteria immediately updates the board to show only matching parent issue cards. The filter state is indicated visually on the Filter button (e.g., a highlight or badge showing active filters). Clearing filters restores the full board view.

**Why this priority**: Filtering is the most common board interaction for project managers who need to focus on specific subsets of work. Without functional filters, the board lacks basic project management capability.

**Independent Test**: Can be fully tested by loading a project board with diverse parent issues (different labels, assignees, milestones), applying various filter combinations, and confirming only matching cards appear on the board.

**Acceptance Scenarios**:

1. **Given** a project board with parent issues across multiple labels, **When** the user filters by label "enhancement," **Then** only parent issues with the "enhancement" label are displayed.
2. **Given** the user applies a filter by assignee "Boykai," **When** the board updates, **Then** only parent issues assigned to "Boykai" appear.
3. **Given** the user applies multiple filters (label "p1" AND assignee "Boykai"), **When** the board updates, **Then** only parent issues matching both criteria appear.
4. **Given** active filters are applied, **When** the user views the Filter button, **Then** a visual indicator (highlight, badge, or count) shows that filters are active.
5. **Given** active filters are applied, **When** the user clears all filters, **Then** the board restores the full parent issue view and the visual indicator is removed.

---

### User Story 7 — Functional Sort Controls on the Project Board (Priority: P2)

A project manager clicks the "Sort" button on the Project Board toolbar. A sort panel opens, allowing the user to sort parent issue cards within each column by created date, updated date, priority, or title — in ascending or descending order. Selecting a sort option immediately reorders the cards within each column. The sort state is indicated visually on the Sort button.

**Why this priority**: Sorting helps project managers quickly identify the most recent, oldest, or highest-priority items in each column. This is essential for daily standup reviews and sprint planning.

**Independent Test**: Can be fully tested by loading a project board with parent issues that have varied creation dates and titles, applying sort by title ascending, and confirming cards are reordered alphabetically within each column.

**Acceptance Scenarios**:

1. **Given** a project board column with parent issues created on different dates, **When** the user sorts by "Created Date — Newest First," **Then** the cards within each column are ordered by descending creation date.
2. **Given** the user sorts by "Title — A to Z," **When** the board updates, **Then** cards within each column are ordered alphabetically by title in ascending order.
3. **Given** the user sorts by "Priority — Highest First," **When** the board updates, **Then** cards within each column are ordered by priority level descending (P1 before P2 before P3).
4. **Given** an active sort is applied, **When** the user views the Sort button, **Then** a visual indicator shows that a non-default sort is active.

---

### User Story 8 — Functional Group By Controls on the Project Board (Priority: P3)

A project manager clicks the "Group By" button on the Project Board toolbar. A grouping panel opens, allowing the user to group parent issue cards by label, assignee, or milestone. Selecting a grouping option reorganizes cards into named groups within or across columns. The group headers are clearly visible, and the Group By state is indicated visually on the button.

**Why this priority**: Grouping provides an alternative organizational view that complements filtering and sorting. It is less frequently used than filter/sort but valuable for milestone reviews and team workload assessments.

**Independent Test**: Can be fully tested by loading a project board with parent issues assigned to different milestones, grouping by milestone, and confirming cards are reorganized into named milestone groups.

**Acceptance Scenarios**:

1. **Given** a project board with parent issues assigned to milestones "Sprint 1" and "Sprint 2," **When** the user groups by "Milestone," **Then** cards are reorganized into clearly labeled "Sprint 1" and "Sprint 2" groups.
2. **Given** the user groups by "Assignee," **When** the board updates, **Then** cards are organized into groups named by each assignee, with unassigned issues in a separate group.
3. **Given** an active grouping is applied, **When** the user views the Group By button, **Then** a visual indicator shows that grouping is active.
4. **Given** the user removes the active grouping, **When** the board updates, **Then** cards revert to the default column-based layout.

---

### Edge Cases

- What happens when a parent issue has zero sub-issues? The parent card should render normally with no expand toggle or sub-issue count badge visible.
- What happens when all issues on the board are sub-issues (no parent issues exist)? The board should display an empty state message indicating no parent issues are available.
- What happens when a sub-issue has no agent or model assigned? The sub-issue tile should display gracefully with "Unassigned" or omit the fields without layout breakage.
- What happens when a parent issue has a very large number of sub-issues (e.g., 50+)? The expanded sub-issue list within the card should be scrollable to prevent the parent card from growing excessively tall.
- What happens when the user applies a filter that matches no parent issues? The board should show an empty state message (e.g., "No issues match the current filters") rather than a blank board with no explanation.
- What happens when the user applies a sort and then adds a new parent issue? The new card should be inserted in the correct sort position within its column.
- What happens when a label has a very long name (100+ characters)? The label chip should truncate with an ellipsis and show the full name on hover.
- What happens when the user rapidly toggles expand/collapse on a parent card? The toggle should debounce or queue state changes to prevent visual flickering.
- What happens when the saved pipeline configuration is deleted while it is the active selection? The label should revert to "Custom" and the user should be notified that the configuration is no longer available.
- What happens when the user filters, sorts, and groups simultaneously? All three operations should compose correctly — filters narrow the set, sort orders within groups, and grouping organizes the filtered and sorted results.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST render only GitHub Parent Issues as top-level cards on each Project Board column, excluding sub-issues from the primary board view entirely.
- **FR-002**: System MUST display a collapsible sub-issue list section within each parent issue card, collapsed by default, expandable via a visible toggle control (chevron icon) with a badge showing the sub-issue count.
- **FR-003**: System MUST show the assigned Agent name and Model name on each sub-issue tile rendered inside the expanded sub-issue panel of a parent card.
- **FR-004**: System MUST display all GitHub labels associated with a parent issue as colored label chips on the parent card, using the label's configured color and name from GitHub.
- **FR-005**: System MUST make each Project Board column independently vertically scrollable so that cards in tall columns remain accessible without triggering page-level scrolling.
- **FR-006**: System MUST ensure all available model names are correctly displayed on every agent tile in the Agent Pipeline, with no models missing from the UI.
- **FR-007**: System MUST ensure accurate tool counts are displayed on every agent tile in the Agent Pipeline, resolving any missing or zero-count rendering bugs.
- **FR-008**: System MUST dynamically replace the "Custom" label in the Agent Pipeline with the name of the currently active saved pipeline configuration when the user selects one, and revert to "Custom" only when no named configuration is selected.
- **FR-009**: System MUST implement functional Filter controls on the Project Board that filter displayed parent issue cards by label, assignee, status, and milestone — supporting multiple simultaneous filter criteria.
- **FR-010**: System MUST implement functional Sort controls on the Project Board that reorder parent issue cards within each column by created date, updated date, priority, or title — in ascending or descending order.
- **FR-011**: System MUST implement functional Group By controls on the Project Board that reorganize parent issue cards into named groups by label, assignee, or milestone.
- **FR-012**: System SHOULD persist the user's active Filter, Sort, and Group By selections across page refreshes.
- **FR-013**: System SHOULD display a visual indicator (highlight, badge, or active state) on the Filter, Sort, and Group By buttons when any non-default configuration is active.

### Key Entities

- **Parent Issue**: A top-level GitHub Issue that may have child sub-issues. Parent issues are the primary unit of display on the Project Board. Attributes: title, status, assignee(s), labels, milestone, creation date, update date, priority, sub-issue list.
- **Sub-Issue**: A GitHub Issue linked to a parent issue via GitHub's parent/child relationship. Sub-issues are displayed only within the expanded panel of their parent card. Attributes: title, status, assigned Agent name, assigned Model name.
- **Agent Pipeline Configuration**: A saved, named configuration defining which agents are assigned to pipeline stages. The "Custom" label in the pipeline header reflects whether a named configuration is active. Attributes: name, project association, per-stage agent assignments.
- **Agent Tile**: A visual representation of an agent within the pipeline. Attributes: agent identifier, display name, model name, tool count, pipeline stage assignment.
- **Board Filter State**: The set of active filter, sort, and group-by criteria applied to the Project Board. Attributes: filter criteria (label, assignee, status, milestone), sort field and direction, group-by field. Persisted across page refreshes.

## Assumptions

- GitHub parent/child issue relationships are already available through the GitHub API (sub_issues or tracked-in metadata) and the existing backend data pipeline surfaces this relationship to the frontend.
- Agent and model assignment data for sub-issues is already available in the existing data model — the sub-issue tiles simply need to bind to and display this data.
- GitHub label color and name data is already fetched as part of the issue data pipeline and available to the frontend for rendering.
- The existing Agent Pipeline already has a mechanism for selecting saved pipeline configurations; the "Custom" label rename is a display-only change driven by the selection state.
- Filter, Sort, and Group By operations can be performed entirely on the client side using the in-memory parent issue array — no additional API calls are needed for these operations.
- Priority for sorting purposes is derived from issue labels (e.g., "p1", "p2", "p3") using a conventional mapping since GitHub does not have a native priority field.
- The current Project Board columns correspond to GitHub project status fields and this structure is not changed by this feature.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The Project Board displays only parent issues as top-level cards — zero sub-issues appear as standalone cards in any column, verified on a board with at least 10 parent issues and 20 sub-issues.
- **SC-002**: 100% of parent issue cards with sub-issues display a working expand/collapse toggle that reveals and hides sub-issue tiles on click.
- **SC-003**: Every sub-issue tile in an expanded parent card displays the assigned Agent name and Model name (or "Unassigned" if not set) with no missing data for configured assignments.
- **SC-004**: All GitHub labels on parent issues render as colored chips on the corresponding board cards, with correct colors matching the GitHub label configuration.
- **SC-005**: Each Project Board column scrolls independently — scrolling within one column does not affect other columns or the page scroll position, verified with columns containing 15+ cards.
- **SC-006**: 100% of agent tiles in the Agent Pipeline display their configured model name and tool count with no omissions, verified against the pipeline configuration data.
- **SC-007**: The Agent Pipeline label updates from "Custom" to the saved configuration name within 1 second of selection, and reverts to "Custom" when deselected.
- **SC-008**: Users can filter the board by label and see only matching parent issues within 1 second of applying the filter.
- **SC-009**: Users can sort board cards by title and see cards reorder within each column within 1 second.
- **SC-010**: Users can group board cards by assignee and see cards reorganized into named groups within 1 second.
- **SC-011**: Filter, Sort, and Group By selections persist across page refreshes — reloading the page restores the previously active configuration.
- **SC-012**: Active Filter, Sort, or Group By states are visually indicated on their respective toolbar buttons, distinguishable from the default state.
