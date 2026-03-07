# Feature Specification: Project Page — Agent Pipeline UX Overhaul, Drag/Drop Fixes, Issue Rendering & Layout Improvements

**Feature Branch**: `028-project-page-ux`  
**Created**: 2026-03-07  
**Status**: Draft  
**Input**: User description: "Update Agent Pipeline styling, agent metadata display, auto-formatted agent names, saved pipeline config selection, Done column parent-issue filter, Markdown-rendered issue descriptions, remove Add column, unified layout alignment, and drag/drop fixes on the project page."

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Fix Drag/Drop Interaction Bugs (Priority: P1)

A user opens the project page and drags an agent tile from one pipeline column to another. The tile follows the cursor precisely from the moment of grab — no positional jump or teleportation occurs. Dropping the tile onto a valid column updates the agent assignment immediately and persists the change. Similarly, dragging issue cards between kanban columns works smoothly and accurately.

**Why this priority**: Broken drag/drop is a blocking interaction bug that prevents users from configuring agent pipelines reliably. Fixing this is essential before any visual or layout improvements can be validated.

**Independent Test**: Can be fully tested by opening any project with an agent pipeline, grabbing an agent tile, and confirming the tile stays under the cursor from grab-start through drop, with no positional jump on mousedown.

**Acceptance Scenarios**:

1. **Given** the project page with an agent pipeline containing at least two columns with agents, **When** the user clicks and holds an agent tile, **Then** the tile remains positioned directly under the user's cursor at the exact grab point with no teleport or jump.
2. **Given** the user is dragging an agent tile, **When** the user moves the cursor over a valid drop column, **Then** the column visually indicates it is a valid drop target (highlight or border).
3. **Given** the user drops an agent tile onto a new column, **When** the drop completes, **Then** the agent assignment updates in the pipeline and the change persists.
4. **Given** the user drags an issue card between kanban columns, **When** the user drops the card, **Then** the card moves to the new column with no visual glitches or positional jumps.

---

### User Story 2 — Subtle Agent Pipeline Restyling & Unified Layout Alignment (Priority: P1)

A user navigates to the project page and sees the Agent Pipeline section styled consistently with the Pipeline Stages on the pipeline page — lighter borders, reduced visual weight, tighter spacing, and a more refined appearance. The Agent Pipeline columns and the Project Stages (kanban columns) are horizontally aligned by column index and both sections dynamically span the full page width in a unified layout.

**Why this priority**: Visual consistency and layout alignment are core to the production-quality experience. The current heavy styling and misalignment break the cohesive feel of the application.

**Independent Test**: Can be fully tested by opening the project page and visually comparing the Agent Pipeline section against the Pipeline Stages on the pipeline page, and verifying column-by-column horizontal alignment between the pipeline row and the kanban board.

**Acceptance Scenarios**:

1. **Given** the project page is loaded, **When** the user views the Agent Pipeline section, **Then** the styling matches the subtle design of the Pipeline Stages component (lighter borders, consistent border-radius, reduced background weight, consistent spacing).
2. **Given** the project page has N status columns, **When** the page renders, **Then** the Agent Pipeline section and the kanban columns are horizontally aligned by column index, and both sections span the full page width.
3. **Given** the browser window is resized, **When** the page reflows, **Then** the pipeline and kanban columns remain aligned and dynamically adjust their widths together.

---

### User Story 3 — Agent Tile Metadata & Auto-Formatted Names (Priority: P2)

A user views the Agent Pipeline on the project page and sees each agent tile displaying the agent's auto-formatted name, the configured model name (e.g., "GPT-4o"), and the number of tools assigned (e.g., "3 tools"). Agent identifiers are automatically formatted: single-word names are title-cased ("linter" → "Linter"), and dot-namespaced identifiers are humanized ("speckit.tasks" → "Spec Kit - Tasks").

**Why this priority**: Displaying model/tool metadata and formatted names improves scannability and gives users immediate context about each agent's capabilities without expanding the tile. This is important for informed pipeline configuration.

**Independent Test**: Can be fully tested by loading any project page with agents that have dot-namespaced identifiers, and verifying the formatted names, model labels, and tool counts render correctly on each tile.

**Acceptance Scenarios**:

1. **Given** an agent with slug "linter", **When** the agent tile renders, **Then** the displayed name reads "Linter".
2. **Given** an agent with slug "speckit.tasks", **When** the agent tile renders, **Then** the displayed name reads "Spec Kit - Tasks".
3. **Given** an agent configured with model "GPT-4o" and 5 tools, **When** the agent tile renders, **Then** the model name "GPT-4o" and "5 tools" are visible as secondary metadata beneath the agent name.
4. **Given** an agent with no configured model, **When** the agent tile renders, **Then** the model field is omitted gracefully (no empty labels or placeholder text shown).

---

### User Story 4 — Saved Agent Pipeline Configuration Selection (Priority: P2)

A user opens the Agent Pipeline section and sees a dropdown or selector control allowing them to choose from previously saved Agent Pipeline configurations for this project. When the user selects a new pipeline configuration, it is applied to the pipeline display and persisted. Any new GitHub Issues created within the project after this selection inherit the newly assigned pipeline configuration.

**Why this priority**: The ability to switch between saved pipeline configurations enables teams to reuse established workflows and ensures newly created issues automatically get the right agent assignments.

**Independent Test**: Can be fully tested by loading a project with at least two saved pipeline configurations, selecting a different configuration, creating a new issue, and verifying the new issue inherits the selected pipeline's agent assignments.

**Acceptance Scenarios**:

1. **Given** a project with multiple saved Agent Pipeline configurations, **When** the user opens the pipeline selector, **Then** all saved configurations for this project are listed.
2. **Given** the user selects a different pipeline configuration, **When** the selection is confirmed, **Then** the Agent Pipeline section updates to reflect the selected configuration.
3. **Given** a pipeline configuration has been selected, **When** the user creates a new GitHub Issue within the project, **Then** the new issue is associated with the selected pipeline configuration.
4. **Given** the user selects a configuration and navigates away, **When** the user returns to the project page, **Then** the previously selected configuration is still active (persists across sessions).

---

### User Story 5 — Markdown-Rendered Issue Descriptions (Priority: P2)

A user selects a GitHub Issue card on the kanban board. The issue detail view opens and the description content is rendered as properly formatted Markdown — headings, code blocks, lists, bold/italic text, and hyperlinks all display correctly, rather than showing raw Markdown text.

**Why this priority**: Readable issue descriptions are essential for understanding task context. Raw Markdown text is hard to read and undermines the professional appearance of the project board.

**Independent Test**: Can be fully tested by selecting a GitHub Issue with a Markdown body containing headings, code blocks, lists, bold, italic, and links, and verifying each element renders correctly in the detail view.

**Acceptance Scenarios**:

1. **Given** a GitHub Issue with Markdown headings, **When** the user opens the issue detail view, **Then** headings render with appropriate sizes and weights.
2. **Given** a GitHub Issue with fenced code blocks, **When** the user opens the issue detail view, **Then** code blocks render with monospace font and distinct background.
3. **Given** a GitHub Issue with bullet/numbered lists, bold text, italic text, and hyperlinks, **When** the user opens the issue detail view, **Then** each Markdown element renders correctly.
4. **Given** a GitHub Issue with no body content, **When** the user opens the issue detail view, **Then** no empty description section is shown.

---

### User Story 6 — Done Column Shows Only Parent Issues (Priority: P3)

A user views the kanban board on the project page. The "Done" column (and any column with a "done" or "closed" status) displays only top-level parent GitHub Issues. Sub-issues are excluded from the Done column entirely, reducing clutter and providing a clearer view of completed work items.

**Why this priority**: Filtering sub-issues from the Done column reduces visual noise and focuses the user's attention on meaningful completed milestones rather than granular sub-tasks.

**Independent Test**: Can be fully tested by viewing the Done column on a project with parent issues that have sub-issues, and confirming only parent issues appear.

**Acceptance Scenarios**:

1. **Given** a project board with a "Done" column containing both parent issues and sub-issues, **When** the board renders, **Then** only parent issues appear in the Done column.
2. **Given** a parent issue with three sub-issues all in "Done" status, **When** the board renders, **Then** the parent issue appears in the Done column but none of the three sub-issues appear.
3. **Given** a sub-issue is moved to "Done" status, **When** the board refreshes, **Then** the sub-issue does not appear in the Done column.

---

### User Story 7 — Remove Add Column Button (Priority: P3)

A user views the kanban board and the "+ Add column" button is no longer present. The board displays only the columns that exist for the project, with no option to manually add new columns from the board UI.

**Why this priority**: The Add Column button is unnecessary clutter; column management is handled elsewhere. Removing it simplifies the board interface.

**Independent Test**: Can be fully tested by loading the project page and confirming no "+ Add column" button or similar control exists on the board.

**Acceptance Scenarios**:

1. **Given** the project board is loaded, **When** the user inspects the board UI, **Then** no "+ Add column" button or column-addition control is visible.

---

### Edge Cases

- What happens when an agent slug contains multiple consecutive dots (e.g., "speckit..tasks")? The formatter should handle this gracefully, treating empty segments as no-ops (result: "Spec Kit - Tasks").
- What happens when an agent slug contains numeric segments (e.g., "agent.v2.runner")? The formatter should title-case alphabetic segments and preserve numeric segments (result: "Agent - V2 - Runner").
- What happens when an agent has an already-cased display_name (e.g., "MyCustomAgent")? The display_name should take precedence over slug formatting.
- What happens when drag/drop is attempted on a touch device? Touch sensors with appropriate activation delay and tolerance should prevent accidental drags while still supporting intentional touch-drag gestures.
- What happens when the pipeline has zero saved configurations? The selector should display a helpful empty state indicating no saved configurations exist.
- What happens when a GitHub Issue body is extremely long (thousands of lines of Markdown)? The rendered Markdown should be contained within a scrollable area to prevent layout breakage.
- What happens when all issues in the Done column are sub-issues? The Done column should render as empty with a zero count.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST restyle the Agent Pipeline section on the project page to match the subtle visual design of the Pipeline Stages component on the pipeline page (reduced border weight, lighter background, consistent spacing and border-radius).
- **FR-002**: System MUST display each agent tile's configured model name and total tool count as secondary metadata beneath the agent name.
- **FR-003**: System MUST auto-format agent name identifiers on render using a pure utility function: single-word names are title-cased (e.g., "linter" → "Linter"); dot-separated namespaced names are split, each segment is title-cased, and segments are joined with " - " (e.g., "speckit.tasks" → "Spec Kit - Tasks").
- **FR-004**: System MUST gracefully handle edge cases in agent name formatting: multiple consecutive dots, numeric segments, empty segments, and already-cased display names (display_name takes precedence over slug formatting when present).
- **FR-005**: System MUST provide a selection control (dropdown or similar) in the Agent Pipeline section allowing users to choose from all saved Agent Pipeline configurations associated with the project.
- **FR-006**: System MUST apply the selected Agent Pipeline configuration as the default for all newly created GitHub Issues within the project, persisting this association across sessions.
- **FR-007**: System MUST exclude GitHub Sub-Issues from the "Done" kanban column — only top-level parent GitHub Issues may appear in columns with a "done" or "closed" status.
- **FR-008**: System MUST render GitHub Issue descriptions as properly parsed Markdown (supporting headings, lists, code blocks, inline code, bold, italic, and hyperlinks) in the issue detail/selection view.
- **FR-009**: System MUST remove the "+ Add column" button from the project board UI.
- **FR-010**: System MUST align the Agent Pipeline section and Project Stages kanban columns by column index, with both sections dynamically spanning the full page width in a unified layout.
- **FR-011**: System MUST fix the drag/drop implementation so that agent tiles do not teleport or jump on initial click — the tile must remain positioned under the user's cursor at the exact grab point throughout the drag interaction.
- **FR-012**: System MUST audit and fix all drag/drop interactions on the project page using modern best practices to eliminate existing bugs, including correct pointer-offset calculation and transform application.
- **FR-013**: System SHOULD show a visual indicator (highlight or border change) on valid drop targets during drag operations for both agent tiles and issue cards.

### Key Entities

- **Agent Pipeline Configuration**: A saved, named configuration that defines which agents are assigned to which pipeline stages for a project. Attributes: name, project association, per-stage agent assignments. A project may have multiple saved configurations but one active/selected configuration at any time.
- **Agent Tile**: A visual representation of an agent within the pipeline. Attributes: agent identifier (slug), formatted display name, configured model name, tool count, and assignment to a pipeline stage.
- **Parent Issue**: A top-level GitHub Issue that may have sub-issues. Used to filter the Done column — only parent issues (issues with no parent) are displayed in Done/Closed columns.
- **Sub-Issue**: A GitHub Issue that is linked to a parent issue. Sub-issues are excluded from the Done column display.

## Assumptions

- The existing `@dnd-kit` library (already in the project's dependency tree) is the correct library for drag/drop and does not need to be replaced — the current bugs are caused by incorrect configuration/offset handling, not library limitations.
- Agent model name and tool count data are already available or retrievable from the agent configuration data model (the backend already stores per-agent configuration details including model and tools).
- Saved Agent Pipeline configurations already exist as a concept in the data model (the `agent_configs` table with `UNIQUE(name, project_id)` constraint). The selector simply needs to expose existing saved configurations for selection.
- The Pipeline Stages component on the AgentsPipelinePage provides the reference styling (using the `celestial-panel` class, `border-border/75`, `rounded-[1.2rem]`).
- The project board's column structure is the single source of truth for alignment — both the agent pipeline row and the kanban columns share the same number of columns derived from project status fields.
- Touch device support for drag/drop should follow the existing activation constraint pattern (delay + tolerance) already configured in the codebase.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can drag and drop agent tiles without any positional jump — the tile follows the cursor from grab-start, verified across 10 consecutive drag operations with zero teleport occurrences.
- **SC-002**: Agent Pipeline section on the project page is visually indistinguishable in style (borders, spacing, background) from the Pipeline Stages component on the pipeline page when compared side-by-side.
- **SC-003**: 100% of agent names with dot-notation identifiers display with the correct humanized format (e.g., "speckit.tasks" → "Spec Kit - Tasks") on first render.
- **SC-004**: Agent tiles display model name and tool count metadata for all agents that have this information configured — no metadata is missing for configured agents.
- **SC-005**: Users can select from saved pipeline configurations and the selection persists across page navigations and browser sessions.
- **SC-006**: All newly created GitHub Issues within the project inherit the currently selected pipeline configuration without additional user action.
- **SC-007**: The Done column displays zero sub-issues — only parent issues appear, verified against a dataset with at least 5 parent issues and 10 sub-issues.
- **SC-008**: GitHub Issue descriptions with Markdown content (headings, code blocks, lists, bold, italic, links) render correctly with proper formatting in the issue detail view.
- **SC-009**: The "+ Add column" button is absent from the project board UI.
- **SC-010**: Agent Pipeline columns and kanban columns maintain 1:1 horizontal alignment at all viewport widths above 1024px.
- **SC-011**: Users can complete a full agent drag-and-drop reordering workflow (grab, move, drop) in under 3 seconds with no visual glitches.
