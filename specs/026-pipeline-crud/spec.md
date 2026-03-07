# Feature Specification: Pipeline Page — CRUD for Agent Pipeline Configurations with Model Selection and Saved Workflow Management

**Feature Branch**: `026-pipeline-crud`  
**Created**: 2026-03-07  
**Status**: Draft  
**Input**: User description: "On the pipeline page, I want the user to be able to CRUD Agent Pipeline configurations. They should also be able to select the agent model for each agent, be smart with the UI/UX here. Saved Agent workflows should be displayed on the bottom, when selected it goes into edit mode for the user, populating the Agent Pipeline board and stages."

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Create a New Agent Pipeline Configuration (Priority: P1)

A user opens the pipeline page and sees an empty Agent Pipeline Board at the top with a clear call-to-action to create their first pipeline. They click "New Pipeline," give the pipeline a name, then add one or more stages. Within each stage they assign agents, and for each agent they select a model from a context-aware model picker that groups models by provider and displays useful metadata (context size, cost tier). Once satisfied, they click "Save" and the new pipeline appears in the Saved Workflows section at the bottom of the page.

**Why this priority**: Creating a pipeline is the foundational action. Without it, no other CRUD operations, model selection, or saved workflow features are meaningful. This is the entry point for the entire feature.

**Independent Test**: Can be fully tested by opening the pipeline page, clicking "New Pipeline," naming it, adding a stage with an agent, selecting a model for that agent, saving, and confirming the pipeline appears in the Saved Workflows list.

**Acceptance Scenarios**:

1. **Given** the user is on the pipeline page with no active pipeline, **When** they click "New Pipeline," **Then** the board enters creation mode with an empty canvas and the pipeline name field is editable.
2. **Given** the user is in creation mode, **When** they add a stage and assign an agent to it, **Then** the stage appears on the board with the agent card displayed inside it.
3. **Given** the user has added an agent to a stage, **When** they open the model picker on that agent card, **Then** available models are displayed grouped by provider with metadata (context size, cost tier) visible for each model.
4. **Given** the user has selected a model for an agent, **When** they view the agent card, **Then** the selected model name and provider are displayed on the card.
5. **Given** the user has configured a pipeline with at least one stage and one agent with a model, **When** they click "Save," **Then** the pipeline is persisted and appears in the Saved Workflows section at the bottom.
6. **Given** the user has not named the pipeline, **When** they click "Save," **Then** the system prompts them to provide a name before saving.

---

### User Story 2 — Load and Edit a Saved Pipeline (Priority: P1)

A user scrolls to the Saved Workflows section at the bottom of the pipeline page and sees a list of their previously saved pipelines, each showing the pipeline name, last modified date, and agent/stage count. They click on a saved workflow card. The Agent Pipeline Board populates with all the stages, agents, and model selections from that saved pipeline, and a visual indicator (such as a banner or highlighted header) shows they are now in edit mode. They modify a stage, change an agent's model, and click "Save" to persist the changes.

**Why this priority**: Loading and editing saved workflows is the primary way users interact with existing configurations. Without this, saved pipelines are view-only and lose their utility.

**Independent Test**: Can be fully tested by saving a pipeline (from Story 1), clicking its card in Saved Workflows, verifying all stages/agents/models are restored on the board, changing a model, saving, and confirming the change persists on reload.

**Acceptance Scenarios**:

1. **Given** the user has one or more saved pipelines, **When** they view the Saved Workflows section, **Then** each pipeline card shows the pipeline name, last modified date, and agent/stage count.
2. **Given** the user clicks a saved workflow card, **When** the board loads, **Then** all stages, agents, and model selections from the saved pipeline are fully restored on the Agent Pipeline Board.
3. **Given** a saved workflow is loaded, **When** the user views the board, **Then** a visual indicator (banner or highlighted header) communicates that they are editing an existing workflow, showing the pipeline name.
4. **Given** the user is in edit mode, **When** they change an agent's model and click "Save," **Then** the changes are persisted and the Saved Workflows card reflects the updated last modified date.
5. **Given** the user is in edit mode, **When** they add a new stage or remove an existing one and save, **Then** the updated stage count is reflected in the Saved Workflows card.

---

### User Story 3 — Delete a Saved Pipeline (Priority: P2)

A user selects a saved workflow from the Saved Workflows section. A "Delete" action becomes available in the toolbar. They click "Delete," and a confirmation dialog appears asking them to confirm permanent removal. Upon confirmation, the pipeline is deleted and removed from the Saved Workflows list. The board resets to its empty/new state.

**Why this priority**: Delete completes the CRUD lifecycle and allows users to manage clutter. It is lower priority than create/edit because it is a less frequent action, but essential for a complete workflow.

**Independent Test**: Can be fully tested by creating and saving a pipeline, selecting it, clicking "Delete," confirming in the dialog, and verifying the pipeline no longer appears in Saved Workflows.

**Acceptance Scenarios**:

1. **Given** a saved workflow is loaded in edit mode, **When** the user clicks "Delete," **Then** a confirmation dialog appears warning that the action is permanent.
2. **Given** the confirmation dialog is shown, **When** the user confirms deletion, **Then** the pipeline is permanently removed from the Saved Workflows list and the board resets to its empty state.
3. **Given** the confirmation dialog is shown, **When** the user cancels, **Then** the pipeline remains loaded in edit mode and no changes occur.
4. **Given** no workflow is selected or the board is in a new-pipeline state, **When** the user views the toolbar, **Then** the "Delete" action is disabled or hidden.

---

### User Story 4 — Model Selection per Agent (Priority: P2)

A user is configuring a pipeline (new or existing) and wants to choose the best model for a specific agent. They click the model selector on an agent card and see a list of available models grouped by provider (e.g., OpenAI, Anthropic, Google) or by capability tier (e.g., Premium, Standard, Economy). Each model entry shows relevant metadata such as context window size and cost tier. They select a model and the agent card updates immediately to reflect the choice. The model picker remembers recently used models for quick re-selection.

**Why this priority**: Model selection is a core differentiating feature of the pipeline builder. While a pipeline can technically be created with a default model, the ability to choose models per agent is central to the user value proposition described in the issue.

**Independent Test**: Can be fully tested by opening the model picker on any agent card, verifying models are grouped with metadata, selecting a model, and confirming the agent card updates to show the selection.

**Acceptance Scenarios**:

1. **Given** the user clicks the model selector on an agent card, **When** the model picker opens, **Then** available models are displayed grouped by provider or capability tier.
2. **Given** the model picker is open, **When** the user views a model entry, **Then** they see the model name, provider, context window size, and cost tier.
3. **Given** the user selects a model, **When** the model picker closes, **Then** the agent card immediately displays the selected model name and provider.
4. **Given** the user has previously selected models in this session, **When** they open the model picker again, **Then** recently used models appear at the top for quick access.
5. **Given** the user has not yet selected a model for a new agent, **When** they view the agent card, **Then** a sensible default model is pre-selected or a prompt to "Select model" is displayed.

---

### User Story 5 — Unsaved Changes Protection and Stage Reordering (Priority: P3)

A user is editing a pipeline and has made changes but not saved. They attempt to click a different saved workflow or navigate away from the page. A confirmation dialog appears asking whether they want to save, discard, or cancel the navigation. Additionally, while editing, the user can drag and drop stages to reorder them on the board and inline-rename stages by clicking on the stage title.

**Why this priority**: Unsaved changes protection prevents accidental data loss and is critical for a polished experience, but it does not enable any new capability. Stage reordering and inline rename are quality-of-life improvements that enhance usability but are not blocking for core CRUD operations.

**Independent Test**: Can be fully tested by making a change to a loaded pipeline, clicking a different saved workflow card, verifying the confirmation dialog appears, and testing each response option (save, discard, cancel). Stage reordering can be tested by dragging a stage to a new position and verifying it persists after save.

**Acceptance Scenarios**:

1. **Given** the user has unsaved changes on the board, **When** they click a different saved workflow card, **Then** a confirmation dialog asks them to save, discard, or cancel.
2. **Given** the confirmation dialog is shown, **When** the user clicks "Save," **Then** changes are saved and the newly selected workflow loads.
3. **Given** the confirmation dialog is shown, **When** the user clicks "Discard," **Then** changes are discarded and the newly selected workflow loads.
4. **Given** the confirmation dialog is shown, **When** the user clicks "Cancel," **Then** the dialog closes and the user remains on the current pipeline.
5. **Given** the user has unsaved changes, **When** they attempt to navigate away from the pipeline page, **Then** the browser's built-in navigation guard prompts them to confirm leaving.
6. **Given** a pipeline has multiple stages, **When** the user drags a stage to a new position, **Then** the stage order updates visually and persists when saved.
7. **Given** the user clicks on a stage title, **When** the title becomes editable, **Then** they can type a new name and press Enter or click away to confirm the rename.

---

### User Story 6 — Empty States and Contextual Actions (Priority: P3)

A new user opens the pipeline page for the first time. The Agent Pipeline Board shows a welcoming empty state with a call-to-action to create their first pipeline. The Saved Workflows section also shows an empty state explaining that saved workflows will appear here once created. Toolbar actions (Save, Delete, Discard) are contextually disabled or hidden based on the current state (no active pipeline, no unsaved changes, no workflow selected).

**Why this priority**: Empty states and contextual toolbar behavior are polish items that significantly improve first-time user experience and prevent confusion, but core CRUD functionality works without them.

**Independent Test**: Can be fully tested by loading the pipeline page with no saved workflows and verifying both empty states render with appropriate messaging and CTAs. Toolbar states can be tested by checking button enabled/disabled states in each context.

**Acceptance Scenarios**:

1. **Given** the user has no saved pipelines, **When** they view the pipeline page, **Then** the board area shows an empty state with a "Create your first pipeline" call-to-action.
2. **Given** the user has no saved pipelines, **When** they view the Saved Workflows section, **Then** an empty state explains that saved workflows will appear here once created.
3. **Given** no pipeline is loaded on the board, **When** the user views the toolbar, **Then** "Save," "Delete," and "Discard" are disabled and "New Pipeline" is enabled.
4. **Given** a pipeline is loaded with no unsaved changes, **When** the user views the toolbar, **Then** "Save" and "Discard" are disabled, "Delete" is enabled, and "New Pipeline" is enabled.
5. **Given** a pipeline is loaded with unsaved changes, **When** the user views the toolbar, **Then** "Save" and "Discard" are enabled.

---

### Edge Cases

- What happens when the user tries to save a pipeline with no stages? The system displays a validation message requiring at least one stage before saving.
- What happens when the user tries to save a pipeline with a stage that has no agents? The system allows saving but displays a warning that one or more stages have no agents assigned.
- What happens when the model list fails to load? The model picker displays an error message with a retry option; the user can still save the pipeline with the previously selected or default model.
- What happens when the user creates a pipeline with a name that already exists among their saved workflows? The system does not allow duplicate names and displays a validation message indicating the name is already in use, prompting the user to choose a different name.
- What happens when the user rapidly clicks "Save" multiple times? Only the first save request is processed; subsequent clicks are debounced until the save completes.
- What happens when a save operation fails (e.g., network error)? The user sees an error notification with a "Retry" option, and no data is lost from the board.
- What happens when the Saved Workflows list is very large? The list supports scrolling or pagination so performance is not degraded.
- What happens when two users edit the same pipeline simultaneously? The last save wins, but the user is notified if the pipeline was modified since they loaded it, and given the option to reload or overwrite.

## Requirements *(mandatory)*

### Functional Requirements

#### Pipeline CRUD

- **FR-001**: System MUST allow users to create a new Agent Pipeline configuration by clicking "New Pipeline," which initializes an empty board in creation mode with an editable pipeline name field.
- **FR-002**: System MUST allow users to add one or more stages to a pipeline, with each stage having a user-defined name and the ability to contain one or more agents.
- **FR-003**: System MUST allow users to assign agents to stages within a pipeline, with each agent displaying as a distinct card within its parent stage.
- **FR-004**: System MUST allow users to save a configured pipeline, creating a new record on first save or updating the existing record when editing a previously saved pipeline.
- **FR-005**: System MUST allow users to delete a saved pipeline, preceded by a confirmation dialog that warns the action is permanent. Upon confirmation, the pipeline is permanently removed.
- **FR-006**: System MUST allow users to discard unsaved changes on the board, reverting to the last saved state (or clearing the board if it was a new unsaved pipeline).

#### Model Selection

- **FR-007**: System MUST provide a model picker for each agent within a pipeline stage, allowing the user to select from available models.
- **FR-008**: The model picker MUST display available models grouped logically (by provider or capability tier), with each model entry showing the model name, provider, context window size, and cost tier.
- **FR-009**: The model picker MUST surface recently used models at the top of the list for quick re-selection within the same session.
- **FR-010**: Each agent card MUST display the currently selected model name and provider. If no model is selected, the card MUST show a prompt or pre-select a sensible default.

#### Saved Workflows

- **FR-011**: System MUST display a Saved Workflows section at the bottom of the pipeline page listing all previously saved pipeline configurations.
- **FR-012**: Each entry in the Saved Workflows section MUST show at minimum the pipeline name, last modified date, and agent/stage count. A brief description, if available, SHOULD also be displayed.
- **FR-013**: Clicking a saved workflow entry MUST load the full pipeline configuration (all stages, agent assignments, and model selections) onto the Agent Pipeline Board and transition the UI into edit mode.
- **FR-014**: Edit mode MUST be visually distinct from creation mode, indicated by a banner, highlighted header, or other clear visual cue showing the name of the pipeline being edited.

#### Board Interactions

- **FR-015**: System MUST support drag-and-drop reordering of stages on the Agent Pipeline Board. The new order MUST persist when the pipeline is saved.
- **FR-016**: System MUST support inline renaming of stages by clicking on the stage title, editing the text, and confirming with Enter or by clicking away.
- **FR-017**: Toolbar actions (New Pipeline, Save, Delete, Discard) MUST be contextually enabled or disabled based on the current board state (empty board, active pipeline with no changes, active pipeline with unsaved changes).

#### Data Protection

- **FR-018**: System MUST prompt the user to confirm or discard unsaved changes when they attempt to load a different saved workflow while unsaved changes exist on the board.
- **FR-019**: System MUST trigger a browser navigation guard when the user attempts to leave the pipeline page with unsaved changes, warning them that changes may be lost.
- **FR-020**: Save operations MUST be debounced so that rapid repeated clicks result in only one save request.

#### Empty States

- **FR-021**: The Agent Pipeline Board MUST display an empty state with a call-to-action ("Create your first pipeline") when no pipeline is loaded.
- **FR-022**: The Saved Workflows section MUST display an empty state with explanatory text when the user has no saved pipelines.

### Key Entities

- **Pipeline**: A named collection of ordered stages representing an agent workflow. Key attributes: name, description (optional), creation date, last modified date, ordered list of stages.
- **Stage**: A named step within a pipeline that contains one or more agents. Key attributes: name, display order, list of assigned agents.
- **Agent Assignment**: An agent placed within a stage, configured with a specific model. Key attributes: reference to the agent, selected model, agent-specific configuration.
- **Model**: An available AI model that can be assigned to an agent. Key attributes: name, provider, context window size, cost tier, capability category.
- **Saved Workflow**: A persisted pipeline configuration that appears in the Saved Workflows list. Represents the full serialized state of a pipeline including all stages, agents, and model selections.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can create a new pipeline, add stages with agents, select models, and save the configuration in under 5 minutes on first use.
- **SC-002**: Loading a saved workflow fully populates the board (all stages, agents, and model selections) in under 2 seconds.
- **SC-003**: 100% of CRUD operations (create, read, update, delete) complete successfully and persist across page reloads.
- **SC-004**: Users can identify which model is assigned to each agent at a glance without opening any menus or dialogs.
- **SC-005**: The unsaved changes confirmation dialog prevents accidental data loss in 100% of navigation-away and workflow-switch scenarios.
- **SC-006**: The model picker presents models in a grouped, scannable format that allows users to find and select a model in under 15 seconds.
- **SC-007**: Saved Workflows list accurately reflects all saved pipelines with correct metadata (name, date, counts) at all times.
- **SC-008**: Empty states provide clear guidance so that first-time users can create their first pipeline without external help or documentation.
- **SC-009**: Stage reordering via drag-and-drop updates the visual order immediately and persists correctly after save.
- **SC-010**: Toolbar actions are never misleadingly enabled — destructive or inapplicable actions are always disabled in contexts where they cannot be performed.

## Assumptions

- An existing models list or configuration is available that provides model metadata (name, provider, context window size, cost tier). The model data source already exists and does not need to be created as part of this feature.
- The pipeline page already exists in the application's routing structure (e.g., `/pipeline`) and this feature enhances it with CRUD capabilities.
- Agent entities already exist within the application. This feature adds the ability to assign agents to pipeline stages and select models for them, but does not create the agent management system itself.
- Pipeline configurations are stored per user or per project scope — the system does not need to support shared/collaborative pipeline editing in this iteration.
- Optimistic UI updates are used for save and delete operations to provide responsive feedback, with rollback on failure.
- The Saved Workflows list will contain a manageable number of entries (under 100) for the initial release; pagination or virtualization may be added later if needed.

## Scope Exclusions

- Pipeline execution or running — this feature covers configuration only, not triggering or monitoring pipeline runs.
- Agent creation or deletion — agents are managed separately; this feature only assigns existing agents to pipeline stages.
- Model management — models are read from an existing source; adding, editing, or removing models is out of scope.
- Collaborative editing — real-time multi-user editing of the same pipeline is not supported.
- Pipeline versioning or history — only the current saved state is maintained; rollback to previous versions is not included.
- Pipeline import/export — sharing pipeline configurations via file or link is not included.
- Pipeline templates — pre-built pipeline templates for common workflows are not included in this iteration.
