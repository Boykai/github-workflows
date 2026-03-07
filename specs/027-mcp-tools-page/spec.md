# Feature Specification: Add Tools Page with MCP Configuration Upload and Agent Tool Selection

**Feature Branch**: `027-mcp-tools-page`  
**Created**: 2026-03-07  
**Status**: Draft  
**Input**: User description: "Add a Tools page right under Agents page on the left nav bar. This page should look almost exactly like Agents. Except this should support a user uploading MCP configurations to be synced/added to GitHub repo/project for GitHub Custom Agents to use. Agents should then be able to have tools added, similar to how models are selected. Except, pop up a tile module in a grid pattern of MCPs for the user to select 0-to-many to add to an agent while creating. Check current documentation for how to integrate this into GitHub."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Browse and Manage MCP Tools (Priority: P1)

As a developer, I want a dedicated Tools page in the application so that I can view, organize, and manage all my MCP configurations in one central location, just like I manage my agents today.

**Why this priority**: The Tools page is the foundational surface for the entire feature. Without it, users have no way to view or interact with MCP configurations. Every other story depends on this page existing.

**Independent Test**: Can be fully tested by navigating to the Tools page, verifying the layout matches the Agents page pattern (header, action bar, card/list views, empty state), and confirming that MCP tools are displayed as cards with name, description, and sync status.

**Acceptance Scenarios**:

1. **Given** a user is on any page in the application, **When** they look at the left navigation bar, **Then** they see a "Tools" entry positioned directly below the "Agents" entry, using a consistent icon and styling pattern.
2. **Given** a user clicks the "Tools" navigation item, **When** the page loads, **Then** they see a page layout that mirrors the Agents page structure — including a page header, an action bar with an "Upload MCP Config" button, and either a list/grid of MCP tool cards or an empty state message.
3. **Given** no MCP configurations have been uploaded yet, **When** the user visits the Tools page, **Then** they see an empty state that mirrors the Agents page empty state pattern with a prompt to upload their first MCP configuration.
4. **Given** one or more MCP configurations exist, **When** the user views the Tools page, **Then** each configuration appears as a card showing its name, description, and current sync status (e.g., "Synced to GitHub", "Pending", "Error").

---

### User Story 2 - Upload and Sync MCP Configuration to GitHub (Priority: P1)

As a developer, I want to upload an MCP configuration file and have it automatically synced to my connected GitHub repository so that my GitHub Custom Agents can use the tools defined in that configuration.

**Why this priority**: Uploading and syncing MCP configurations is the core value proposition. Without this, the Tools page has no actionable purpose — it would just be an empty shell.

**Independent Test**: Can be fully tested by clicking "Upload MCP Config", providing a valid MCP configuration (via file upload or paste), confirming it is accepted and appears on the Tools page with a "Synced" status, and verifying the configuration was pushed to the connected GitHub repository.

**Acceptance Scenarios**:

1. **Given** the user is on the Tools page, **When** they click the "Upload MCP Config" button, **Then** a modal opens allowing them to either paste a JSON MCP configuration or upload a configuration file.
2. **Given** the upload modal is open and the user provides a valid MCP configuration, **When** they confirm the upload, **Then** the system validates the configuration format, accepts the upload, and begins syncing it to the connected GitHub repository.
3. **Given** a valid MCP configuration has been uploaded, **When** the sync completes successfully, **Then** a new MCP tool card appears on the Tools page with the configuration's name, description, and a "Synced to GitHub" status indicator.
4. **Given** the upload modal is open and the user provides an invalid or malformed configuration, **When** they attempt to confirm, **Then** the system displays a clear, actionable error message describing what is wrong with the configuration (e.g., "Missing required field: name") and does not proceed with the upload.
5. **Given** a valid MCP configuration has been uploaded but the sync to GitHub fails, **When** the user views the Tools page, **Then** the affected MCP card shows an "Error" status with a human-readable reason for the failure and a "Retry" button.

---

### User Story 3 - Select MCP Tools When Creating or Editing an Agent (Priority: P1)

As a developer creating or editing an agent, I want to select which MCP tools the agent should have access to via a visual tile-grid modal so that I can easily discover and assign the right tools — similar to how I select models today.

**Why this priority**: Tool assignment is the critical integration point between the Tools page and the Agent workflow. This is what makes uploaded MCP configurations usable by agents.

**Independent Test**: Can be fully tested by opening the Agent creation or edit form, clicking the "Add Tools" section, selecting one or more MCP tools in the tile-grid modal, confirming the selection, and verifying the selected tools appear as removable chips/tags on the agent form.

**Acceptance Scenarios**:

1. **Given** the user is on the Agent creation or Agent edit form, **When** they look at the form, **Then** they see an "Add Tools" section that mirrors the visual pattern of the existing "Select Model" interaction.
2. **Given** the user clicks the "Add Tools" section, **When** the tool selector opens, **Then** a full overlay modal appears displaying all available MCP tools in a responsive tile grid, with each tile showing the tool's icon/logo, name, and short description.
3. **Given** the tool selector modal is open, **When** the user clicks on one or more MCP tool tiles, **Then** each selected tile shows a clear visual active/selected state (e.g., checkmark overlay or highlighted border), and the user can select zero to many tools.
4. **Given** the user has selected tools in the modal, **When** they click "Confirm" (or equivalent), **Then** the modal closes and the selected tools appear as removable chips or tags in the "Add Tools" section of the agent form.
5. **Given** selected tools are displayed as chips on the agent form, **When** the user clicks the remove action on a chip, **Then** that tool is deselected and removed from the agent's tool list.
6. **Given** the user re-opens the tool selector modal after making previous selections, **When** the modal appears, **Then** previously selected tools are shown in their selected state, allowing the user to add or remove tools.
7. **Given** the user saves the agent with selected tools, **When** the agent record is persisted, **Then** the selected MCP tools are saved as part of the agent configuration and visible on the agent detail view.

---

### User Story 4 - Re-sync and Delete MCP Configurations (Priority: P2)

As a developer, I want to manually re-sync or delete MCP configurations from the Tools page so that I can fix sync issues and remove configurations I no longer need.

**Why this priority**: Re-sync and delete are essential management actions but are secondary to the core upload-and-assign workflow. Users need these for ongoing maintenance, but the feature delivers value without them initially.

**Independent Test**: Can be fully tested by triggering a re-sync on an existing MCP card and confirming the sync status updates, and by deleting an MCP card with confirmation and verifying it is removed from the Tools page and flagged/removed in GitHub.

**Acceptance Scenarios**:

1. **Given** an MCP card is displayed on the Tools page, **When** the user clicks the re-sync/refresh action on that card, **Then** the system re-pushes the configuration to the connected GitHub repository and updates the sync status accordingly.
2. **Given** an MCP card has an "Error" sync status, **When** the user clicks the retry action, **Then** the system attempts to re-sync the configuration and updates the status to either "Synced" or shows an updated error message.
3. **Given** the user clicks the delete action on an MCP card, **When** a confirmation prompt appears and the user confirms, **Then** the MCP configuration is removed from the Tools page and also removed or flagged in the connected GitHub repository.
4. **Given** the user cancels the deletion confirmation prompt, **When** the prompt closes, **Then** the MCP configuration remains unchanged on the Tools page.

---

### Edge Cases

- What happens when a user uploads an MCP configuration with the same name as an existing one? The system should warn the user and offer to overwrite or cancel.
- What happens when the GitHub repository connection is lost or the authentication token expires during sync? The system should display a clear error on the affected card and prompt the user to re-authenticate or check the repository connection.
- What happens when a user deletes an MCP tool that is currently assigned to one or more agents? The system should warn the user that the tool is in use by specific agents and require confirmation before proceeding. After deletion, affected agents should show the tool as "unavailable" or "removed".
- How does the system handle very large MCP configuration files? The system should enforce a reasonable file size limit and display a clear error if the limit is exceeded.
- What happens when a user tries to upload a non-JSON file or a JSON file that doesn't match the expected MCP schema? The system should reject the upload with a specific validation error before attempting any sync.
- What happens if the tile-grid modal is opened but no MCP tools have been uploaded yet? The modal should display an empty state with guidance directing the user to the Tools page to upload an MCP configuration first.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST add a "Tools" navigation item to the left sidebar, positioned directly below the "Agents" navigation item, using consistent styling and icon patterns.
- **FR-002**: System MUST render the Tools page with a layout and component structure that mirrors the Agents page, including page header, action bar, card/list views, and empty state.
- **FR-003**: System MUST display an empty state on the Tools page when no MCP configurations exist, mirroring the Agents page empty state pattern and prompting the user to upload their first configuration.
- **FR-004**: System MUST provide an "Upload MCP Config" button on the Tools page that opens a modal allowing users to upload or paste an MCP configuration in JSON format.
- **FR-005**: System MUST validate uploaded MCP configuration files for correct schema and format before accepting them, displaying actionable error messages for invalid uploads (e.g., missing required fields, malformed JSON).
- **FR-006**: System MUST automatically sync/push accepted MCP configurations to the connected GitHub repository for use by GitHub Custom Agents.
- **FR-007**: System MUST display each uploaded MCP configuration as a card on the Tools page showing at minimum: name, description, and current sync status (Synced, Pending, or Error).
- **FR-008**: System MUST show a human-readable error reason on MCP cards that have a failed sync status, along with a retry action.
- **FR-009**: System MUST provide a re-sync/refresh action on each MCP card to allow manual re-push of a configuration to the GitHub repository.
- **FR-010**: System MUST surface an "Add Tools" selector in the Agent creation and Agent edit forms, allowing users to select zero or more MCP tools to associate with an agent, analogous to the existing model selection interaction.
- **FR-011**: System MUST render the MCP tool selector as a modal overlay containing a responsive tile grid, where each tile shows the MCP icon/logo, name, and short description, with multi-select support via a clear visual active/selected state (checkmark or highlighted border).
- **FR-012**: System MUST persist the selected MCP tools on the agent record and display them as removable chips or tags on the agent form and agent detail view.
- **FR-013**: System MUST allow users to remove individual tools from an agent by clicking the remove action on a chip/tag, or by deselecting the tool inside the modal.
- **FR-014**: System MUST handle sync failures gracefully, displaying an error status on the affected MCP card with a user-readable reason and a retry option.
- **FR-015**: System SHOULD support deleting an MCP configuration from the Tools page with a confirmation prompt, which also removes or flags the configuration in the connected GitHub repository.
- **FR-016**: System MUST warn users when deleting an MCP tool that is currently assigned to one or more agents, listing which agents are affected, and require explicit confirmation before proceeding.
- **FR-017**: System MUST warn users when uploading a configuration with a name that matches an existing configuration, offering the choice to overwrite or cancel.
- **FR-018**: System MUST enforce a file size limit on MCP configuration uploads and display a clear error if the limit is exceeded.
- **FR-019**: System MUST display an empty state in the tool selector modal when no MCP configurations have been uploaded, with guidance directing the user to the Tools page.
- **FR-020**: System MUST follow the official GitHub documentation for MCP configuration file format, repository placement, and integration requirements to ensure compatibility with GitHub Custom Agents.

### Key Entities

- **MCP Configuration**: Represents an uploaded MCP tool configuration. Key attributes: unique identifier, name, description, raw configuration content, sync status (Synced, Pending, Error), last synced timestamp, target GitHub repository, and creation/modification timestamps.
- **Agent-Tool Association**: Represents the many-to-many relationship between agents and MCP tools. Key attributes: agent identifier, MCP tool identifier, and assignment timestamp.
- **Sync Status**: Represents the current state of a configuration's synchronization with GitHub. Possible values: Synced (successfully pushed), Pending (upload accepted, sync in progress), Error (sync failed with a reason).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can navigate to the Tools page in one click from the left navigation bar, and the page loads within 2 seconds.
- **SC-002**: Users can upload a valid MCP configuration and see it appear on the Tools page with a "Synced" status within 30 seconds of submission.
- **SC-003**: 100% of invalid MCP configuration uploads are rejected with a specific, actionable error message before any sync is attempted.
- **SC-004**: Users can select MCP tools for an agent in under 60 seconds via the tile-grid modal, including opening the modal, selecting tools, and confirming.
- **SC-005**: Selected tools are correctly persisted on the agent record and visible on the agent detail view after saving.
- **SC-006**: Users can remove a tool from an agent in under 5 seconds via chip removal or modal deselection.
- **SC-007**: Sync failures are surfaced to the user within 10 seconds with a human-readable error reason and an available retry action.
- **SC-008**: Re-syncing a configuration results in an updated sync status reflecting the outcome of the retry.
- **SC-009**: Deleting an MCP configuration that is assigned to agents triggers a warning listing all affected agents before the user can confirm.
- **SC-010**: The Tools page empty state provides a clear call to action, and 90% of first-time users successfully upload their first configuration without external help.
- **SC-011**: The tool selector modal renders responsively on screens from 768px to 1920px width, maintaining a usable tile grid layout.
- **SC-012**: The Tools page layout is visually indistinguishable from the Agents page layout in structure, spacing, and component patterns (header, action bar, cards, empty state).

## Assumptions

- The application already has an Agents page with an established layout pattern (header, action bar, card/list views, empty state) that the Tools page will mirror.
- The application has an existing left navigation sidebar where the "Agents" item currently exists, and a new "Tools" item can be added directly below it.
- The Agent creation and edit forms already have a model selection interaction pattern (e.g., "Select Model") that the "Add Tools" interaction will mirror.
- A connected GitHub repository or project is already configured in the application, and authenticated API access to push files to it is available.
- MCP configurations follow a JSON-based schema. The official GitHub documentation defines the required format and target file placement (e.g., within the `.github/` directory) for GitHub Custom Agents to consume.
- The existing data layer can be extended to store MCP configuration records with fields for sync status, timestamps, and configuration content.
- Users have appropriate permissions to upload configurations and modify agent settings.
- Standard web application performance expectations apply (page loads under 2 seconds, actions respond within 30 seconds).

## Out of Scope

- Creating or editing MCP configurations within the application (users upload pre-built configurations).
- Managing GitHub repository connections or authentication — assumed to be handled by existing application infrastructure.
- MCP server runtime behavior or execution — this feature covers configuration management and assignment only.
- Versioning or change history for MCP configurations.
- Bulk upload of multiple MCP configurations in a single action.
- Role-based access control for the Tools page — all users with access to the Agents page have access to the Tools page.
