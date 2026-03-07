# Feature Specification: Pipeline Page — Fix Model List, Tools Z-Index, Tile Dragging, Agent Clone, and Remove Add Stage

**Feature Branch**: `029-pipeline-ux-fixes`  
**Created**: 2026-03-07  
**Status**: Draft  
**Input**: User description: "On the pipeline page, fix the Pipeline Model list to show user-specific GitHub models, fix the Tools module z-index so it is not hidden, restrict drag-and-drop to Agent tiles only (lock Status tiles), add a Clone button to Agent tiles, and remove the Add Stage button."

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Dynamic GitHub Model List in Select Model Dropdown (Priority: P1)

A pipeline builder opens the Pipeline Creation page and clicks "+ Add Agent." In the "Select model" dropdown, they see the list of models available from their authenticated GitHub account for running Custom GitHub Agents. This list is fetched dynamically at runtime and reflects the models their specific account has access to — different users may see different models depending on their GitHub plan and permissions.

**Why this priority**: An incorrect or mismatched model list means users cannot select the right model for their agents. This is a data-accuracy issue that directly impacts the correctness of every pipeline configuration created through the UI. If the wrong models are listed, agents may fail at runtime or produce unexpected results.

**Independent Test**: Can be fully tested by logging in with a GitHub account that has a known set of available models, opening Pipeline Creation → + Add Agent → Select model, and verifying the dropdown lists exactly the models available for that account.

**Acceptance Scenarios**:

1. **Given** an authenticated user with access to models A, B, and C on their GitHub account, **When** they open Pipeline Creation and click "+ Add Agent" then open the "Select model" dropdown, **Then** the dropdown displays exactly models A, B, and C.
2. **Given** two users with different GitHub accounts (User X has models A, B; User Y has models A, B, C, D), **When** each user opens the "Select model" dropdown, **Then** User X sees only models A and B, and User Y sees models A, B, C, and D.
3. **Given** the GitHub models endpoint is unavailable or returns an error, **When** the user opens the "Select model" dropdown, **Then** a user-friendly message is displayed (e.g., "Unable to load models. Please try again.") instead of an empty dropdown or application crash.
4. **Given** the GitHub models endpoint returns an empty list, **When** the user opens the "Select model" dropdown, **Then** a message is displayed indicating no models are currently available for their account.

---

### User Story 2 — Tools Module Renders Above All Other Elements (Priority: P1)

A pipeline builder is creating a new pipeline and clicks "+ Add Agent," then clicks "+ Tools" to add tools to the agent. The Tools module (popover/modal) renders fully visible above all other pipeline canvas elements, cards, panels, and overlays. No part of the Tools module is hidden, clipped, or obscured by surrounding elements.

**Why this priority**: If the Tools module is hidden behind other elements, users physically cannot add tools to their agents. This is a blocking usability issue that prevents core pipeline configuration functionality.

**Independent Test**: Can be fully tested by opening Pipeline Creation → + Add Agent → + Tools and visually confirming the Tools module is fully visible and not obscured by any adjacent elements, regardless of scroll position or canvas state.

**Acceptance Scenarios**:

1. **Given** the user is in Pipeline Creation with an agent form open, **When** they click "+ Tools", **Then** the Tools module renders fully visible above all other elements on the page.
2. **Given** the Tools module is open and the pipeline canvas has multiple agent tiles and panels visible, **When** the user scrolls or interacts with surrounding elements, **Then** the Tools module remains on top and is never partially hidden or clipped.
3. **Given** the Tools module is open, **When** the user clicks outside the Tools module, **Then** the module closes normally without any visual glitches.

---

### User Story 3 — Status Tiles Are Locked; Agent Tiles Remain Draggable (Priority: P1)

A pipeline builder is creating a new pipeline configuration. Status tiles (representing pipeline stages/statuses) are fixed in place and cannot be moved — they do not respond to drag events and do not show a grab cursor. Agent tiles remain fully draggable and repositionable within the pipeline canvas, with a grab cursor on hover indicating they can be moved.

**Why this priority**: Allowing Status tiles to be dragged creates confusion and can break the pipeline layout. Status tiles represent fixed pipeline stages and should never be repositioned by the user. Conversely, Agent tiles must remain draggable since assigning agents to stages is the core interaction of pipeline configuration.

**Independent Test**: Can be fully tested by attempting to drag a Status tile (should not move) and then dragging an Agent tile (should move smoothly), verifying cursor affordances and drag behavior for each tile type.

**Acceptance Scenarios**:

1. **Given** the Pipeline Creation canvas with Status tiles and Agent tiles, **When** the user hovers over a Status tile, **Then** no grab/move cursor is displayed.
2. **Given** the user attempts to click and drag a Status tile, **When** the drag gesture is initiated, **Then** the Status tile does not move and no drag operation begins.
3. **Given** the user hovers over an Agent tile, **When** the cursor is positioned over the tile, **Then** a grab cursor is displayed indicating the tile is draggable.
4. **Given** the user clicks and drags an Agent tile, **When** the drag gesture is initiated, **Then** the Agent tile follows the cursor and can be repositioned within the pipeline canvas.
5. **Given** a pipeline canvas with both tile types, **When** the user inspects all tiles, **Then** Status tiles are visually distinguishable from Agent tiles (e.g., different cursor, locked icon, or distinct border style) to communicate that Status tiles are fixed.

---

### User Story 4 — Clone Button on Agent Tiles (Priority: P2)

A pipeline builder views Agent tiles during Pipeline Creation and sees a "Clone" button on each Agent tile. Clicking the Clone button creates a complete copy of that agent's configuration — including its selected model, configured tools, and all parameters — and inserts the cloned Agent tile into the pipeline as a new, independent instance ready for editing.

**Why this priority**: Cloning agents saves significant time when building pipelines with multiple agents that share similar configurations. Instead of manually recreating each agent from scratch, users can clone an existing agent and modify only the differences. This is a productivity feature that enhances the core pipeline-building workflow.

**Independent Test**: Can be fully tested by creating an agent with a model and tools configured, clicking the Clone button, and verifying the new agent tile has identical configuration to the original but is independently editable.

**Acceptance Scenarios**:

1. **Given** an Agent tile with a model, three tools, and custom parameters configured, **When** the user clicks the "Clone" button on that agent tile, **Then** a new Agent tile appears in the pipeline with the same model, same three tools, and same parameters.
2. **Given** the user has cloned an Agent tile, **When** they edit the cloned agent's model or tools, **Then** the original agent tile remains unchanged (deep copy, not a reference).
3. **Given** the user has cloned an Agent tile, **When** they inspect the cloned tile, **Then** the clone has a unique identity (different internal ID) and can be independently configured, renamed, or deleted.
4. **Given** an Agent tile with no tools or model configured, **When** the user clicks "Clone", **Then** the cloned tile also has no tools or model, matching the original's empty state.

---

### User Story 5 — Remove Add Stage Button (Priority: P2)

A pipeline builder opens the Pipeline Creation page. The "Add Stage" button and all associated stage-creation functionality have been removed from the UI. The pipeline canvas displays only the existing stages without any option to manually add new stages from this view.

**Why this priority**: The "Add Stage" button is an unused control that adds clutter and confusion to the Pipeline Creation interface. Removing it simplifies the UI and eliminates a potential source of user error. Stage management is handled elsewhere in the application.

**Independent Test**: Can be fully tested by loading the Pipeline Creation page and confirming that no "Add Stage" button, link, or control is visible anywhere on the page.

**Acceptance Scenarios**:

1. **Given** the Pipeline Creation page is loaded, **When** the user inspects the entire page, **Then** no "Add Stage" button or stage-addition control is visible.
2. **Given** the Pipeline Creation page is loaded, **When** the user interacts with the pipeline canvas, **Then** there is no way to trigger stage creation from the Pipeline Creation UI.

---

### Edge Cases

- What happens when the GitHub models API returns a very large number of models (50+)? The dropdown should be scrollable and remain performant.
- What happens when the user's authentication token expires while the model list is being fetched? The system should display an appropriate error and prompt re-authentication rather than showing stale or empty data.
- What happens when the user clones an agent multiple times in rapid succession? Each clone should produce a distinct independent copy with a unique ID; no duplicates or race conditions should occur.
- What happens when the user clones an agent whose tools include nested configuration objects? The deep copy must capture all nested data — modifying a nested tool parameter on the clone must not affect the original.
- What happens when all agents on the canvas are clones of the same original? Each should be fully independent and editable without cross-contamination.
- What happens when the Tools module is opened near the bottom or right edge of the viewport? The module should reposition or scroll to remain fully visible, never rendering off-screen.
- What happens when a Status tile is focused via keyboard navigation? The tile should not respond to keyboard-triggered move events (e.g., arrow keys should not reposition Status tiles).
- What happens when the model list is cached and the user's available models change (e.g., plan upgrade)? The cache should be session-scoped and refreshed on page reload or when the user explicitly retries.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST fetch the list of available GitHub models for Custom GitHub Agents dynamically from the authenticated user's GitHub account at runtime and populate the "Select model" dropdown in "+ Add Agent" with that list, replacing any static or mismatched model list.
- **FR-002**: System MUST cache the fetched model list for the duration of the user's session to avoid redundant calls, and refresh the cache on page reload or explicit retry.
- **FR-003**: System MUST display a user-friendly error state in the "Select model" dropdown when the model list API call fails (e.g., network error, authentication failure), rather than crashing or showing an empty dropdown with no explanation.
- **FR-004**: System MUST display a clear message when the model list API returns an empty list, indicating no models are currently available for the user's account.
- **FR-005**: System MUST ensure the Tools module rendered via "+ Add Agent → + Tools" has a stacking context higher than all surrounding pipeline canvas elements, panels, and overlays, so it is never hidden or clipped by other UI elements.
- **FR-006**: System MUST disable drag-and-drop interactions entirely on Status tiles within the Pipeline Creation canvas — Status tiles must not be moveable, must not display a grab/move cursor, and must not respond to drag events.
- **FR-007**: System MUST preserve full drag-and-drop reordering and repositioning functionality exclusively on Agent tiles within the Pipeline Creation canvas, with a grab cursor on hover.
- **FR-008**: System MUST visually differentiate Status tiles from Agent tiles to communicate that Status tiles are fixed (e.g., no grab cursor, locked appearance, or distinct border style) while Agent tiles show interactive drag affordances.
- **FR-009**: System MUST provide a "Clone" button on each Agent tile in the Pipeline Creation view.
- **FR-010**: System MUST perform a complete deep copy of the agent definition when the Clone button is clicked — including the selected model, all configured tools (with nested configuration), and all other parameters — and insert the cloned Agent tile into the pipeline as an independently editable instance with a new unique identifier.
- **FR-011**: System MUST ensure that editing a cloned Agent tile does not affect the original agent tile or any other clones (full independence after cloning).
- **FR-012**: System MUST remove the "Add Stage" button and all associated stage-creation logic from the Pipeline Creation UI.

### Key Entities

- **Pipeline Model**: A model available from GitHub for running Custom GitHub Agents. The list of available models varies by user account and is fetched dynamically from the GitHub API. Attributes: model identifier, display name.
- **Agent Tile**: A visual card on the Pipeline Creation canvas representing a configured agent. Attributes: unique ID, agent name, selected model, configured tools (with nested parameters), assignment to a pipeline stage. Agent tiles are draggable and clonable.
- **Status Tile**: A visual card on the Pipeline Creation canvas representing a pipeline stage/status. Attributes: stage name, position. Status tiles are fixed in place and cannot be moved by the user.
- **Tools Module**: A popover or modal UI component launched from "+ Add Agent → + Tools" that allows users to select and configure tools for an agent. Must render above all other elements on the page.

## Assumptions

- The GitHub API (or equivalent endpoint) provides a way to retrieve the list of models available for Custom GitHub Agents for the authenticated user. The exact endpoint may need to be confirmed during implementation, but the capability exists.
- The user's GitHub authentication token is available in the frontend session and can be used to make authenticated API calls to retrieve the model list.
- The current static or mismatched model list is populated from a hardcoded source or a different endpoint that does not reflect per-user model availability. This source will be replaced.
- The Tools module z-index issue is caused by a CSS stacking context problem (e.g., parent element with `overflow: hidden`, `transform`, or an explicit lower `z-index`). The fix involves adjusting the stacking context or portaling the Tools module to the document body.
- The existing drag-and-drop implementation already distinguishes between tile types (Status vs. Agent) in the data model, making it straightforward to apply a drag-disabled guard to Status tiles.
- The "Add Stage" button removal is a straightforward deletion of a UI element and its event handlers, with no dependent features relying on it.
- Agent cloning produces a fully independent copy — the application's state management supports adding new agent tiles dynamically during Pipeline Creation.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The "Select model" dropdown displays exactly the models available on the authenticated user's GitHub account — verified by comparing the dropdown contents against the user's known model list for at least 2 different accounts.
- **SC-002**: When the model API is unavailable, the "Select model" dropdown displays a user-friendly error message instead of crashing or showing empty/stale data — verified by simulating a network failure.
- **SC-003**: The Tools module is fully visible and not obscured by any pipeline canvas element when opened — verified across 5 different pipeline configurations with varying numbers of agents and stages.
- **SC-004**: Status tiles cannot be moved under any interaction method (mouse drag, touch drag, keyboard) — verified by attempting to drag every Status tile on a pipeline with at least 3 stages.
- **SC-005**: Agent tiles remain fully draggable and repositionable — verified by completing 10 consecutive drag-and-drop operations with no failures.
- **SC-006**: Agent tiles display a grab cursor on hover; Status tiles do not — verified by hovering over each tile type.
- **SC-007**: Clicking "Clone" on an Agent tile produces an exact deep copy verified by comparing all properties (model, tools with nested config, parameters) between the original and clone, then modifying the clone and confirming the original is unchanged.
- **SC-008**: The "Add Stage" button is absent from the Pipeline Creation UI — verified by inspecting the full page for any stage-addition controls.
- **SC-009**: Users can clone an agent and modify the clone independently within 10 seconds of the clone action.
- **SC-010**: The model list cache is session-scoped — after page reload, a fresh model list is fetched from the API.
