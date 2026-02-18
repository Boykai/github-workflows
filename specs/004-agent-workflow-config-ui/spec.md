# Feature Specification: Custom Agent Workflow Configuration UI

**Feature Branch**: `004-agent-workflow-config-ui`  
**Created**: February 17, 2026  
**Status**: Draft  
**Input**: User description: "Custom Agent Workflow Configuration UI — an interactive drag-and-drop agent assignment experience on the Project Board page. Allow users to customize GitHub Issue workflows by assigning agents per status column with drag-and-drop reordering, preset configurations, and local-first save/discard UX."

## Clarifications

### Session 2026-02-17

- Q: Who is authorized to modify agent configurations — any authenticated user, only repo owners/admins, or configurable per-project? → A: Any authenticated user who can view the board can also edit agent configs.
- Q: Should there be a maximum number of agents per status column? → A: Soft limit of 10 per column — warn the user but allow exceeding it.
- Q: How should duplicate agent instances in the same column be distinguished for reorder/remove operations? → A: Assign a unique instance ID (UUID) to each agent assignment at creation time.
- Q: How should available agents be discovered from the repository? → A: Use the GitHub API (GraphQL/REST/CLI) to list Custom GitHub Agents. If the API does not support agent listing, fall back to parsing `.github/agents/*.yml` files in the repository. The app must support switching between different GitHub Projects, with agent configuration scoped per-project.
- Q: What should be explicitly out of scope for this feature? → A: Per-agent configuration editing, agent execution monitoring/logs on the board, and user-created custom presets are out of scope. The three built-in presets (Custom, GitHub Copilot, Spec Kit) are in scope.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - View and Manage Agent Assignments on the Board (Priority: P1)

A user navigates to the Project Board page and sees a collapsible agent configuration row displayed above the issue card columns. The row is expanded by default and mirrors the board's status columns (dynamically fetched from the connected GitHub Project). Each column cell shows the ordered list of agents currently assigned to that status. The user can collapse the row via an accordion toggle to focus on issue cards, and expand it again when they want to configure agents.

**Why this priority**: This is the foundational UI surface for the entire feature. Without the visible agent row aligned to status columns, no other agent configuration interactions are possible. It delivers immediate value by giving users visibility into which agents are assigned to which workflow statuses.

**Independent Test**: Can be fully tested by loading the Project Board page with a connected project and verifying that (1) the agent row appears above the issue columns, (2) each column matches the project's status columns, (3) assigned agents are displayed as card-style tiles in the correct column, (4) the row can be collapsed and expanded via toggle. Delivers value by providing at-a-glance visibility of agent-to-status mappings.

**Acceptance Scenarios**:

1. **Given** a user navigates to the Project Board page with a project selected, **When** the board loads, **Then** a collapsible agent configuration row is displayed above the issue card area, expanded by default, with columns matching the project's status field options
2. **Given** the agent row is expanded, **When** the user clicks the collapse toggle, **Then** the row collapses to a minimal header, and clicking again re-expands it
3. **Given** a status column has agents assigned in the workflow configuration, **When** the board loads, **Then** those agents are displayed as card-style tiles stacked vertically in the corresponding column cell, in priority order (top = first)
4. **Given** a status column has no agents assigned, **When** the board loads, **Then** the column cell shows only a "+ Add Agent" button
5. **Given** the board is connected to a GitHub Project with custom statuses (e.g., "Triage", "Blocked"), **When** the board loads, **Then** the agent row columns match the project's actual status options, not hardcoded defaults

---

### User Story 2 - Add Agents to Status Columns (Priority: P1)

A user clicks the "+ Add Agent" button in any status column cell. A dropdown popover appears anchored to the button, listing all available agents — fetched from the selected repository's Custom GitHub Agents plus the default GitHub Copilot agent. The user selects an agent and it is added to the bottom of that column's agent stack. The same agent can be added multiple times to the same column (supporting 0-to-many runs per status). Changes are held locally and are not saved until the user explicitly clicks "Save".

**Why this priority**: Adding agents is the core write-action of the feature. Without the ability to add agents, the row is read-only and provides limited value. This is co-P1 with the view story because together they form the minimum usable configuration experience.

**Independent Test**: Can be fully tested by clicking "+ Add Agent" in a column, verifying the popover shows all available agents (including duplicates of agents already assigned), selecting one, and confirming it appears at the bottom of the column. Delivers value by allowing users to configure which agents run at each workflow stage.

**Acceptance Scenarios**:

1. **Given** the agent row is expanded, **When** the user clicks "+ Add Agent" in a status column, **Then** a dropdown popover appears listing all available agents from the selected repository plus the default GitHub Copilot agent
2. **Given** the add-agent popover is open, **When** the user selects an agent, **Then** the agent is added as a new card tile at the bottom of that column's stack, and the popover closes
3. **Given** a column already contains "speckit.specify", **When** the user opens the add-agent popover for that column, **Then** "speckit.specify" is still listed and available for selection (duplicates allowed)
4. **Given** the user adds an agent to a column, **When** the agent is added, **Then** the column is visually marked as modified (subtle highlighted border) and the floating save bar appears with "Save" and "Discard" buttons
5. **Given** the system cannot fetch available agents from the repository, **When** the user clicks "+ Add Agent", **Then** an error state is shown in the popover with a retry option

---

### User Story 3 - Reorder Agents via Drag-and-Drop (Priority: P2)

A user drags an agent tile within a status column to change its priority order. The top-most agent runs first, the bottom-most runs last. Drag-and-drop is constrained to within a single column (no cross-column dragging). Smooth animations provide visual feedback during the drag operation. The reordered state is held locally until saved.

**Why this priority**: Reordering controls execution priority, which is important for multi-agent workflows (e.g., plan before tasks in the Ready column). However, users can achieve correct ordering by adding agents in the right sequence, making this an enhancement over the add/remove flow.

**Independent Test**: Can be fully tested by adding multiple agents to a column, dragging one to a different position within the same column, and verifying the new order persists locally. Keyboard reordering (accessibility) can also be tested independently. Delivers value by letting users fine-tune agent execution order without removing and re-adding.

**Acceptance Scenarios**:

1. **Given** a column has two or more agents, **When** the user drags an agent tile to a different position within the same column, **Then** the agent stack reorders accordingly with smooth animation
2. **Given** a user is dragging an agent tile, **When** they attempt to drag it to a different column, **Then** the drop is rejected and the tile snaps back to its original position
3. **Given** a user reorders agents within a column, **When** the drag completes, **Then** the column is marked as modified and the floating save bar appears
4. **Given** a user is using keyboard navigation, **When** they focus on an agent tile and use keyboard shortcuts, **Then** they can reorder the tile up/down within the column (accessible drag-and-drop)

---

### User Story 4 - Remove Agents from Status Columns (Priority: P2)

A user clicks the "X" button on an agent tile to remove it from a status column. The removal is a local change held until saved. The affected column is visually highlighted as modified.

**Why this priority**: Removal completes the CRUD cycle for agent management. Together with add and reorder, it provides full control. It's P2 because the add flow is more critical for initial setup.

**Independent Test**: Can be fully tested by clicking the "X" button on an agent tile and verifying it disappears from the column, the column is marked as modified, and the save bar appears. Delivers value by allowing users to clean up unwanted agent assignments.

**Acceptance Scenarios**:

1. **Given** a column has one or more agents, **When** the user clicks the "X" button on an agent tile, **Then** the tile is removed from that column's stack
2. **Given** the user removes an agent, **When** the removal occurs, **Then** the column is visually marked as modified and the floating save bar appears
3. **Given** a column has a single agent and the user removes it, **When** the removal occurs, **Then** the column shows only the "+ Add Agent" button

---

### User Story 5 - Save and Discard Agent Configuration Changes (Priority: P1)

When the user makes any changes to agent assignments (add, remove, reorder), a floating save bar appears with a global "Save" button and a "Discard" button. Modified columns display a visual diff indicator (highlighted border/glow). Clicking "Save" persists all agent mapping changes to the backend. Clicking "Discard" reverts all columns to the last saved state. The save bar disappears when there are no unsaved changes.

**Why this priority**: Without save/discard, no changes can be persisted or safely reverted. This is co-P1 because the add-agent flow depends on the ability to commit changes.

**Independent Test**: Can be fully tested by making changes to agent mappings, verifying the save bar appears with modified column indicators, clicking "Save" and confirming the changes persist (reload the page and verify), then making new changes and clicking "Discard" to confirm revert. Delivers value by providing a safe, explicit save workflow with visual feedback.

**Acceptance Scenarios**:

1. **Given** the user has made no changes to agent mappings, **When** the board loads, **Then** no save bar is visible
2. **Given** the user has modified agent assignments in one or more columns, **When** changes exist, **Then** a floating save bar appears with "Save" and "Discard" buttons, and modified columns show a highlighted border/glow
3. **Given** the save bar is visible, **When** the user clicks "Save", **Then** all agent mapping changes are persisted to the backend, the save bar disappears, and column modification indicators are cleared
4. **Given** the save bar is visible, **When** the user clicks "Discard", **Then** all columns revert to their last saved state, the save bar disappears, and column modification indicators are cleared
5. **Given** the user clicks "Save" and the backend request fails, **When** the error occurs, **Then** an error message is displayed, changes remain in local state, and the user can retry

---

### User Story 6 - Apply Preset Agent Configurations (Priority: P2)

The agent row area provides three quick-select preset buttons: "Custom", "GitHub Copilot", and "Spec Kit". Selecting a preset shows a confirmation dialog ("This will replace your current agent configuration. Continue?"). Upon confirmation, the preset's agent mappings replace the current configuration as unsaved local changes. The user must still click "Save" to persist.

**Preset — Custom**: All columns empty (no agents assigned to any status). This is a clean-slate starting point.

**Preset — GitHub Copilot**: Backlog → (none), Ready → (none), In Progress → GitHub Copilot, In Review → GitHub Copilot Review, Done → (none).

**Preset — Spec Kit**: Backlog → speckit.specify, Ready → speckit.plan then speckit.tasks, In Progress → speckit.implement, In Review → GitHub Copilot Review, Done → (none).

**Why this priority**: Presets accelerate onboarding and provide sensible defaults, but users can manually configure agents without them. This is P2 because the core add/remove/save flow handles all use cases — presets are a convenience.

**Independent Test**: Can be fully tested by clicking a preset button, confirming the dialog, and verifying the agent mappings match the expected preset configuration in all columns. Then clicking "Discard" to confirm the preset was applied as unsaved changes. Delivers value by reducing setup time from minutes to one click.

**Acceptance Scenarios**:

1. **Given** the agent row is expanded, **When** the user clicks the "GitHub Copilot" preset button, **Then** a confirmation dialog appears asking "This will replace your current agent configuration. Continue?"
2. **Given** the confirmation dialog is showing, **When** the user confirms, **Then** all columns are updated with the GitHub Copilot preset mappings as unsaved local changes, and the save bar appears
3. **Given** the confirmation dialog is showing, **When** the user cancels, **Then** no changes are made and the dialog closes
4. **Given** the user applies the "Spec Kit" preset and confirms, **When** the preset is applied, **Then** columns are populated as specified: Backlog → speckit.specify, Ready → speckit.plan + speckit.tasks, In Progress → speckit.implement, In Review → GitHub Copilot Review, Done → (none)
5. **Given** the user has existing unsaved changes, **When** they apply a preset, **Then** the confirmation dialog warns that existing changes will be replaced

---

### User Story 7 - View Agent Details via Expandable Tiles (Priority: P3)

Each agent card tile has an expand/collapse toggle that reveals additional details about the agent: description, metadata, and other information the user might find useful. This allows users to learn about agents without leaving the board page.

**Why this priority**: This is an informational enhancement. Users can configure agents by name alone — expanded details improve discoverability but are not required for core functionality.

**Independent Test**: Can be fully tested by clicking the expand toggle on an agent tile and verifying that agent description and metadata are displayed. Clicking again collapses the details. Delivers value by providing in-context agent information.

**Acceptance Scenarios**:

1. **Given** an agent tile is displayed in a column, **When** the user clicks the expand toggle, **Then** the tile expands to show agent description, metadata, and other relevant information
2. **Given** an agent tile is expanded, **When** the user clicks the expand toggle again, **Then** the tile collapses back to its compact card view
3. **Given** agent metadata is unavailable (e.g., description not provided by the agent), **When** the tile is expanded, **Then** a graceful fallback is shown (e.g., "No description available")

---

### User Story 8 - Discover Available Agents from Repository (Priority: P2)

The system queries the user's selected project/repository to discover available Custom GitHub Agents and always includes the default GitHub Copilot agent. The available agents list is used to populate the "+ Add Agent" popover. Agent metadata (name, slug, description, avatar) is displayed to help users choose.

**Why this priority**: Agent discovery is required for the add-agent flow to work with real data. Without it, the popover would have no agents to show. It's P2 (not P1) because a hardcoded fallback list could be used during initial development.

**Independent Test**: Can be fully tested by selecting a repository that has Custom GitHub Agents configured, opening the add-agent popover, and verifying all expected agents appear with their metadata. Delivers value by dynamically surfacing available automation options.

**Acceptance Scenarios**:

1. **Given** a project is selected on the board page, **When** the user opens the add-agent popover, **Then** the popover lists all Custom GitHub Agents available in the selected repository plus the default GitHub Copilot agent
2. **Given** the repository has no Custom GitHub Agents, **When** the user opens the add-agent popover, **Then** only the default GitHub Copilot agent is listed
3. **Given** each agent in the popover, **When** displayed, **Then** it shows the agent's display name, slug, and description (if available)
4. **Given** the system fails to fetch agents from the repository, **When** the popover attempts to load, **Then** an error state is displayed with a retry option and the default Copilot agent is still available as a fallback

---

### User Story 9 - Pass-Through Statuses in Workflow Pipeline (Priority: P2)

When a status column has no agents assigned, the workflow pipeline treats it as a pass-through: issues are still moved into that status when the pipeline reaches it, then automatically moved to the next status. This ensures the workflow progresses even when some statuses have no automated agents.

**Why this priority**: This is critical for the "GitHub Copilot" preset (which has empty Backlog and Ready columns) and for any custom configuration where users intentionally leave statuses unassigned. It's P2 because the backend orchestrator must be updated, but the current behavior already moves issues through statuses.

**Independent Test**: Can be fully tested by configuring a workflow with an empty status column (no agents), then triggering an issue through the pipeline and verifying it passes through the empty status to the next one. Delivers value by supporting flexible workflow configurations where not every status needs an agent.

**Acceptance Scenarios**:

1. **Given** a status column has no agents assigned, **When** an issue reaches that status in the pipeline, **Then** the issue is moved into that status and then automatically moved to the next status
2. **Given** multiple consecutive statuses have no agents, **When** an issue reaches the first empty status, **Then** it passes through all empty statuses until it reaches one with agents assigned or the final status

---

### Edge Cases

- What happens when the user's GitHub Project has more columns than the standard 5 (Backlog, Ready, In Progress, In Review, Done)? The agent row dynamically adds cells for all status options from the project — no limit.
- What happens when the board data is still loading? The agent row shows a loading skeleton matching the expected column count.
- What happens when the user switches projects while having unsaved agent changes? A confirmation prompt warns about unsaved changes before switching.
- What happens when two users configure agents for the same project simultaneously? Last-write-wins — the most recent save overwrites previous configuration.
- What happens when a previously available agent is removed from the repository? The agent tile remains in the configuration but is marked with a warning indicator ("Agent not found in repository"). Users can remove it manually.
- What happens when the agent row has many agents in one column, making it very tall? The row expands vertically to accommodate all agents; the board page scrolls normally.
- What happens when a user adds more than 10 agents to a single column? A warning is displayed advising that this may affect pipeline performance, but the user is not blocked from proceeding.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST display a collapsible agent configuration row above the issue card area on the Project Board, aligned with the board's status columns
- **FR-002**: Status columns in the agent row MUST be dynamically fetched from the connected GitHub Project's status field options
- **FR-003**: The agent configuration row MUST default to expanded on page load
- **FR-004**: Each status column cell MUST display an ordered vertical stack of agent card-style tiles representing assigned agents
- **FR-005**: Agent tiles MUST show agent avatar/icon, name, an "X" removal button, and an expand/collapse toggle for description and metadata
- **FR-006**: Users MUST be able to reorder agent tiles within a column via drag-and-drop (top = highest priority, bottom = lowest)
- **FR-007**: Drag-and-drop MUST be constrained to within a single column — no cross-column dragging
- **FR-008**: Each status column MUST have a "+ Add Agent" button that opens a dropdown popover listing all available agents
- **FR-009**: The available agents list MUST be fetched from the selected repository using the GitHub API (GraphQL/REST/CLI); if the API does not support agent listing, the system MUST fall back to parsing `.github/agents/*.agent.md` files in the repository. The list MUST always include the default GitHub Copilot agent
- **FR-010**: The same agent MUST be allowed to appear multiple times in the same status column (duplicate assignments permitted)
- **FR-011**: Agent configuration changes (add, remove, reorder) MUST be held in local state until explicitly saved
- **FR-012**: A floating save bar MUST appear when unsaved changes exist, with a global "Save" button and a "Discard" button
- **FR-013**: Modified columns MUST display a visual diff indicator (highlighted border/glow) when they contain unsaved changes
- **FR-014**: The "Save" action MUST persist all agent mapping changes to the backend in a single request
- **FR-015**: The "Discard" action MUST revert all columns to their last saved state
- **FR-016**: Status columns with no agents assigned MUST display only the "+ Add Agent" button
- **FR-017**: The workflow pipeline MUST treat statuses with no assigned agents as pass-through — moving issues into the status and then automatically to the next status
- **FR-018**: System MUST provide three preset configurations: "Custom" (all columns empty), "GitHub Copilot", and "Spec Kit" with predefined agent-to-status mappings
- **FR-019**: Applying a preset MUST show a confirmation dialog before replacing current agent assignments
- **FR-020**: Presets MUST apply as unsaved local changes, requiring an explicit "Save" to persist
- **FR-021**: The agent row MUST expand and shrink vertically as agents are added or removed to accommodate the stack
- **FR-022**: Drag-and-drop MUST be accessible via keyboard navigation
- **FR-023**: The system MUST provide a backend endpoint to list available agents for the selected repository, returning agent metadata (slug, display name, description, avatar URL)
- **FR-024**: The system MUST display a warning when a user adds more than 10 agents to a single status column, but MUST NOT prevent the addition
- **FR-025**: Agent configurations MUST be scoped per-project; when the user switches between GitHub Projects, the agent configuration row MUST load the selected project's agent mappings

### Key Entities

- **AgentAssignment**: Represents a single agent assigned to a status column. Attributes: slug (agent identifier, not necessarily unique within a column), unique instance ID (UUID, generated at creation time to distinguish duplicate assignments of the same agent), optional per-assignment configuration (for future extensibility). An agent assignment belongs to a status column within a workflow configuration.
- **WorkflowConfiguration**: Extended to store agent assignments per status column. The `agent_mappings` field maps status names to ordered lists of agent assignments. Belongs to a GitHub Project.
- **AvailableAgent**: Represents an agent that can be assigned. Attributes: slug, display name, description, avatar URL. Sourced from the repository's Custom GitHub Agents plus the default Copilot agent.
- **AgentPreset**: A named template of predefined agent-to-status mappings. Attributes: preset name, preset description, mapping of status names to ordered agent assignment lists.

## Assumptions

### Out of Scope

- **Per-agent configuration editing**: The `config` field on `AgentAssignment` is reserved for future use; no UI for editing per-instance agent settings is included in this feature.
- **Agent execution monitoring/logs on the board**: The agent row shows configuration only, not live execution status or log output. Monitoring is handled elsewhere in the app.
- **User-created custom presets**: Users cannot create, save, or name their own presets. Only the three built-in presets (Custom, GitHub Copilot, Spec Kit) are provided.

- The GitHub API provides a mechanism to query Custom GitHub Agents available for a repository. If no standardized API exists, the system will fall back to parsing agent configuration files from the repository's `.github/agents/*.agent.md` directory via the GitHub Contents API.
- Agent configurations are scoped per-project. When the user switches between GitHub Projects on the board page, the agent configuration row loads the corresponding project's agent mappings.
- "GitHub Copilot Review" refers to a distinct agent for code review, separate from the standard GitHub Copilot agent used for implementation.
- The preset status names ("Backlog", "Ready", "In Progress", "In Review", "Done") will be matched case-insensitively against the GitHub Project's actual status field options when applying presets.
- The existing `WorkflowConfiguration` API (GET/PUT) will be extended rather than replaced, maintaining backward compatibility during migration.
- Users have already authenticated and selected a project before interacting with the agent configuration row.
- Any authenticated user who can view the board can also edit agent configurations. No role-based access control is applied to agent config editing.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can view their complete agent-to-status configuration on the Project Board page within 2 seconds of page load
- **SC-002**: Users can add an agent to a status column in 3 clicks or fewer (click "+ Add Agent", click agent in popover, see it appear)
- **SC-003**: Users can apply a preset configuration to all status columns in 2 clicks (select preset, confirm dialog)
- **SC-004**: Users can reorder agents within a column via drag-and-drop with visible animation feedback completing in under 300ms
- **SC-005**: 95% of save operations complete within 2 seconds, with visual confirmation of success or clear error messaging on failure
- **SC-006**: The agent configuration row correctly mirrors 100% of the status columns from the connected GitHub Project (no missing or extra columns)
- **SC-007**: Users can configure a complete agent workflow (across all statuses) and save in under 2 minutes without documentation
- **SC-008**: The workflow pipeline correctly passes through statuses with no assigned agents, advancing issues without stalling
- **SC-009**: Drag-and-drop is fully operable via keyboard for accessibility compliance
- **SC-010**: Unsaved changes are never silently lost — the save bar is visible whenever local state differs from saved state
