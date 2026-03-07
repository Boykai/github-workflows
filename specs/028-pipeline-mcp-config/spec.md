# Feature Specification: Pipeline Page — MCP Tool Selection, Model Override, Flow Graph Cards, Preset Configs & Agent Stamp Isolation

**Feature Branch**: `028-pipeline-mcp-config`  
**Created**: 2026-03-07  
**Status**: Draft  
**Input**: User description: "Pipeline Page: MCP Tool Selection, Model Override, Flow Graph Cards, Preset Configs & Agent Stamp Isolation"

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Build a Multi-Agent Pipeline with Per-Agent MCP Tool Selection (Priority: P1)

As a pipeline author, I want to add agents from my saved Agents library to a new pipeline and then select specific MCP tools for each agent through a lightweight pop-out module, so that every agent in the pipeline has exactly the tools it needs without leaving the pipeline builder.

**Why this priority**: This is the core creation flow. Without the ability to add agents and assign MCP tools, the pipeline builder cannot produce a functional pipeline. It is the foundational interaction for all other features.

**Independent Test**: Can be fully tested by creating a new pipeline, adding two or more agents from the saved Agents list, opening the MCP tool selector for each agent, toggling tool selections, and verifying the selected tools appear on the agent cards. Delivers a usable pipeline creation experience.

**Acceptance Scenarios**:

1. **Given** the user is on the Pipeline creation form, **When** they click "+ Add Agent", **Then** a picker appears showing only agents saved on the Agents page.
2. **Given** an agent has been added to the pipeline, **When** the user clicks the agent's tool selector, **Then** a lightweight pop-out/flyout module appears displaying all available MCPs as a tiled grid.
3. **Given** the MCP tool selector is open, **When** the user clicks on individual MCP tiles, **Then** each tile toggles between selected and unselected states, allowing 0-to-many selections.
4. **Given** the user has selected 3 MCP tools for an agent, **When** the pop-out is closed, **Then** the agent card displays a tool count badge reading "3 tools".

---

### User Story 2 — Pipeline-Level Model Override with Agent Stamp Isolation (Priority: P1)

As a pipeline author, I want to set a single model for the entire pipeline via a top-level dropdown (or choose "Auto" to defer to each agent's own settings), so that I can quickly standardize models across agents without permanently changing the agents' saved configurations on the Agents page.

**Why this priority**: Model override and agent stamp isolation are critical to the pipeline's value proposition — users must be confident that pipeline-scoped changes do not pollute their global agent settings.

**Independent Test**: Can be fully tested by creating a pipeline with multiple agents, selecting a pipeline-level model, verifying all agents switch to that model, then selecting "Auto" and verifying agents revert to their saved stamp model. After saving, confirm the source agents on the Agents page retain their original model settings.

**Acceptance Scenarios**:

1. **Given** a pipeline with three agents each having different saved models, **When** the user selects "GPT-4o" from the pipeline-level model dropdown, **Then** all three agent cards update to display "GPT-4o" as their model.
2. **Given** the pipeline-level model is set to a specific model, **When** the user switches to "Auto", **Then** each agent card reverts to showing its own saved stamp model name.
3. **Given** a pipeline has been saved with model overrides, **When** the user navigates to the Agents page, **Then** each source agent's model setting remains unchanged from its original value.

---

### User Story 3 — Always-Available Save with Inline Validation (Priority: P1)

As a pipeline author, I want the Save button to always be clickable during pipeline creation, so that I can attempt to save at any time and receive clear, inline feedback about what is missing rather than guessing why the button is disabled.

**Why this priority**: A constantly-enabled Save button with inline validation dramatically improves usability and reduces confusion. Users immediately understand what fields need attention, which speeds up the creation workflow.

**Independent Test**: Can be fully tested by clicking Save on an empty pipeline form and verifying that required fields (e.g., pipeline name) are highlighted with red borders and helper text. After filling in required fields and clicking Save again, the pipeline saves successfully.

**Acceptance Scenarios**:

1. **Given** the pipeline creation form is open with no fields filled in, **When** the user clicks "Save", **Then** all required fields are highlighted with red borders and inline helper text describing what is missing.
2. **Given** the pipeline name field is empty and the user clicks Save, **When** the validation runs, **Then** the pipeline name input shows a red border and a message such as "Pipeline name is required".
3. **Given** the user has filled in all required fields after an initial failed save, **When** they click "Save" again, **Then** the pipeline is saved successfully and the validation highlights are cleared.

---

### User Story 4 — Enhanced Saved Workflows Cards with Agent Details and Flow Graph (Priority: P2)

As a pipeline author, I want the Saved Workflows section to display rich cards showing each pipeline's stages, agents, models, tool counts, and a compact flow graph of execution order, so that I can quickly understand and compare my saved pipelines at a glance.

**Why this priority**: Rich information cards and flow graphs transform the Saved Workflows section from a simple list into a powerful overview. This is essential for users managing multiple pipelines but is not blocking basic pipeline creation.

**Independent Test**: Can be fully tested by saving multiple pipelines with varying stages and agents, then navigating to the Saved Workflows section and verifying that each card displays the pipeline name, stages, agents per stage, model per agent, tool count per agent, and a compact inline flow graph.

**Acceptance Scenarios**:

1. **Given** a pipeline with two stages and three agents has been saved, **When** the user views the Saved Workflows section, **Then** the pipeline card displays the pipeline name, lists both stages, shows agents within each stage, and shows the model and tool count for each agent.
2. **Given** a saved pipeline card is rendered, **When** the user inspects the card, **Then** a compact flow graph (horizontal node-edge diagram) is visible showing agents' execution order across stages.
3. **Given** pipelines exist in the Recent Activity section, **When** the user views Recent Activity cards, **Then** they also display the same compact flow graph visualization.

---

### User Story 5 — Preset Pipeline Configurations (Priority: P2)

As a pipeline author, I want to see pre-seeded "Spec Kit" and "GitHub Copilot" pipeline configurations in the Saved Workflows section, so that I can use proven pipeline templates as starting points without building them from scratch.

**Why this priority**: Preset configurations provide immediate value for new users and establish best-practice templates. They depend on the Saved Workflows card UI (Story 4) but add significant onboarding value.

**Independent Test**: Can be fully tested by navigating to the Saved Workflows section and verifying two preset pipelines ("Spec Kit" and "GitHub Copilot") are visible, visually distinguished from user-created pipelines, and each pre-populated with their respective stage, agent, model, and tool configurations.

**Acceptance Scenarios**:

1. **Given** a fresh project with no user-created pipelines, **When** the user opens the Saved Workflows section, **Then** the "Spec Kit" and "GitHub Copilot" preset pipeline cards are displayed.
2. **Given** preset pipeline cards are visible, **When** the user inspects them, **Then** they are visually differentiated from user-created pipelines (e.g., a badge, icon, or distinct styling).
3. **Given** a preset pipeline is displayed, **When** the user reviews its details, **Then** it shows pre-populated stages, agents, models, and tool configurations appropriate for its use case.

---

### User Story 6 — Agent Pipeline Configuration Assignment for New Issues (Priority: P3)

As a project manager, I want to assign a saved Agent Pipeline configuration to my project so that any new GitHub Issues created in the project automatically inherit that pipeline configuration, ensuring consistent agent behavior across all new work items.

**Why this priority**: Automatic pipeline assignment to new issues is a powerful workflow automation feature. It depends on the pipeline creation and saving features (Stories 1-3) being stable and is more of an advanced workflow enhancement than a core creation need.

**Independent Test**: Can be fully tested by selecting a saved Agent Pipeline configuration for a project, creating a new GitHub Issue in that project, and verifying the issue's metadata includes the assigned pipeline configuration.

**Acceptance Scenarios**:

1. **Given** a project has at least one saved Agent Pipeline configuration, **When** the user selects a pipeline configuration for the project, **Then** the selection is saved and displayed as the project's active pipeline.
2. **Given** a project has an assigned Agent Pipeline configuration, **When** a new GitHub Issue is created in that project, **Then** the issue automatically inherits the assigned pipeline configuration as metadata.
3. **Given** the user changes the project's assigned pipeline configuration, **When** a new issue is created after the change, **Then** the new issue uses the newly assigned pipeline, and previously created issues remain unchanged.

---

### Edge Cases

- What happens when the user tries to add an agent that has been deleted from the Agents page after the pipeline builder was opened? The system should display a notification that the agent is no longer available and prevent its addition.
- What happens when all MCP tools in the registry are removed or unavailable? The tool selector should display an empty state message indicating no tools are currently available, and the agent's tool count should show "0 tools".
- What happens when the user selects a pipeline-level model and then individually overrides one agent's model? The individually overridden agent should retain its per-agent model, while other agents use the pipeline-level model. The pipeline-level dropdown should indicate a "Mixed" state or remain on the last selected value.
- What happens when the user saves a pipeline with no agents added? The Save should succeed if the pipeline name is provided, but the system should display a warning that the pipeline has no agents configured.
- What happens when a preset pipeline configuration ("Spec Kit" or "GitHub Copilot") is edited by the user? If presets are read-only, the system should prompt the user to "Save as Copy" to create an editable duplicate. If editable, the system should allow modifications but visually indicate it has been customized.
- What happens when the Saved Workflows section has dozens of pipelines? The section should support scrolling or pagination to remain performant and usable.
- What happens if a project's assigned pipeline configuration is deleted? The system should clear the assignment and notify the project owner that the pipeline is no longer available, falling back to no pipeline assignment for new issues.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST render a "+ Add Agent" button in the pipeline builder that opens a picker populated exclusively with agents saved on the Agents page.
- **FR-002**: System MUST render a lightweight pop-out/flyout module per agent in the pipeline builder that displays all available MCP tools as a tiled, multi-select grid allowing 0-to-many selections.
- **FR-003**: System MUST display each agent card in the pipeline builder with the agent's currently selected model name and a tool count indicator (e.g., "3 tools").
- **FR-004**: System MUST provide a pipeline-level model selection dropdown at the top of the pipeline creation form that, when a model is chosen, updates all agents' model fields within that pipeline session only.
- **FR-005**: System MUST include an "Auto" option in the pipeline-level model dropdown that causes each agent to use its own saved stamp model setting.
- **FR-006**: System MUST isolate all model and tool overrides made during pipeline creation to that specific pipeline — the source agent's global stamp on the Agents page MUST remain unchanged after pipeline save.
- **FR-007**: System MUST keep the "Save" button always clickable during pipeline creation and MUST display inline validation errors (highlighted fields with red borders and helper text) for any missing required fields such as pipeline name.
- **FR-008**: System MUST update the Saved Workflows section cards to display: pipeline name, list of stages, agents within each stage, the model assigned to each agent, and the number of tools assigned to each agent.
- **FR-009**: System MUST render a compact flow graph (node-edge diagram showing agents and execution order across stages) on both Saved Workflows cards and Recent Activity pipeline configuration cards.
- **FR-010**: System MUST seed the Saved Workflows section with two preset pipeline configurations: "Spec Kit" and "GitHub Copilot", each pre-populated with their respective stage, agent, model, and tool configurations.
- **FR-011**: System MUST allow Agent Pipelines to be selected from saved Agent Pipeline configurations, and MUST automatically apply the assigned Agent Pipeline configuration to any newly created GitHub Issues in the project.
- **FR-012**: System SHOULD visually differentiate preset pipeline configurations ("Spec Kit", "GitHub Copilot") from user-created pipelines in the Saved Workflows list (e.g., a badge or distinct styling).
- **FR-013**: System SHOULD persist MCP tool selections per agent per pipeline in the data model, supporting 0-to-many tools and allowing re-editing after save.

### Key Entities

- **Pipeline**: A named, saveable configuration that defines an ordered sequence of stages, each containing one or more agents. Attributes include name, description, stages list, pipeline-level model override, and a flag indicating whether it is a system preset.
- **Pipeline Stage**: A named step within a pipeline that groups one or more agents to execute together or in sequence. Attributes include stage name, execution order, and list of agent assignments.
- **Pipeline Agent Assignment**: A reference linking a saved agent stamp to a specific pipeline stage, with pipeline-scoped overrides for model and MCP tool selections. The overrides do not mutate the source agent stamp.
- **MCP Tool**: A registered tool/integration available for assignment to agents within a pipeline. Attributes include tool identifier, display name, description, and icon.
- **Preset Pipeline Configuration**: A system-seeded, read-only (or copy-on-edit) pipeline template such as "Spec Kit" or "GitHub Copilot", flagged as a system preset in the data model.
- **Project Pipeline Assignment**: A link between a project and a saved pipeline configuration, determining which pipeline is automatically applied to newly created GitHub Issues.

### Assumptions

- The Agents page already provides a way to create and save agent stamps with model settings, and these agents are retrievable for use in the pipeline builder.
- An MCP tool registry exists or will be created that provides a list of available tools with metadata (name, description, icon) for display in the tool selector.
- The pipeline data model supports storing pipeline-scoped overrides separately from the base agent stamp, allowing runtime merging without mutation.
- The "Spec Kit" and "GitHub Copilot" preset configurations will be defined and seeded at application startup or via a migration, with specific stage/agent/model/tool definitions to be finalized during planning.
- The flow graph visualization on cards requires only a simplified, read-only representation of agent execution order — not a fully interactive graph editor.
- GitHub Issue creation in the project triggers a hook or event that can inject pipeline configuration metadata onto the new issue.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can create a complete pipeline (name, stages, agents, MCP tools, model selection) in under 5 minutes.
- **SC-002**: 100% of MCP tool selections made during pipeline creation are persisted correctly and displayed upon re-opening the pipeline.
- **SC-003**: After saving a pipeline with model overrides, 100% of source agent stamps on the Agents page retain their original model settings (zero global mutations).
- **SC-004**: The Save button is always clickable, and clicking Save with missing required fields results in all offending fields being highlighted with inline error messages within 1 second.
- **SC-005**: Saved Workflows cards display pipeline stages, agents, models, tool counts, and a flow graph for 100% of saved pipelines.
- **SC-006**: The "Spec Kit" and "GitHub Copilot" preset pipeline configurations are visible in the Saved Workflows section on first visit to the Pipeline page.
- **SC-007**: 90% of users can identify the execution order of agents in a pipeline by viewing the flow graph on a Saved Workflows card without additional explanation.
- **SC-008**: When a project has an assigned pipeline configuration, 100% of newly created GitHub Issues in that project inherit the pipeline configuration metadata.
- **SC-009**: The MCP tool selector pop-out loads and displays all available tools within 2 seconds of being triggered.
- **SC-010**: Users can distinguish preset pipelines from user-created pipelines at a glance in the Saved Workflows list.
