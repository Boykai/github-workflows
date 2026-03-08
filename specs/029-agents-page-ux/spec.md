# Feature Specification: Agents Page — Sun/Moon Avatars, Featured Agents, Inline Editing with PR Flow, Bulk Model Update, Repo Name Display & Tools Editor

**Feature Branch**: `029-agents-page-ux`  
**Created**: 2026-03-07  
**Status**: Draft  
**Input**: User description: "On Agents page — Agents should have unique sun/moon themed avatars/icons; 'Featured Agents' should show the top 3 used agents, or any agents created in the past 3 days; The user should be able to edit the agent definition directly with mandatory save that creates a PR; Add an option to update all Agent models at once with confirmation; Repository should be the repo name (not owner) fitted to background bubble; The user should be able to easily edit/update the tools an Agent has"

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Inline Agent Definition Editing with PR-Based Save (Priority: P1)

As a user managing agents, I want to edit an agent's definition directly on the Agents page using a structured form editor and have those changes automatically submitted as a GitHub Pull Request when I save, so that I can make configuration changes without manually editing files or leaving the UI.

**Why this priority**: This is the core value proposition — enabling users to modify agent configurations through the UI while preserving a review-friendly Git workflow. Without this, users must resort to manual file edits outside the application.

**Independent Test**: Can be fully tested by opening an agent's detail view, clicking "Edit," modifying a field (e.g., the agent description), clicking "Save," and verifying a new PR is created with the correct file changes. Delivers immediate value by enabling in-app agent configuration management.

**Acceptance Scenarios**:

1. **Given** a user is viewing an agent's detail page, **When** they click the "Edit" button, **Then** the agent definition fields become editable in a structured form (not raw file text) and an unsaved-changes indicator appears after any modification.
2. **Given** a user has made changes to an agent definition, **When** they click "Save," **Then** the system creates a GitHub Pull Request containing the updated agent configuration file and displays a clickable link to the newly created PR.
3. **Given** a user has unsaved changes to an agent definition, **When** they attempt to navigate away from the page, **Then** a blocking confirmation modal appears offering options to save changes, discard changes, or cancel navigation.
4. **Given** a user clicks "Save" and the PR is successfully created, **Then** a success notification appears with a clickable link to the PR URL.
5. **Given** a user clicks "Save" but the PR creation fails (e.g., network error), **Then** an error message is displayed and the unsaved changes are preserved so the user can retry.

---

### User Story 2 — Tools Editor within Agent Configuration (Priority: P1)

As a user configuring an agent, I want to easily add, remove, and reorder the tools assigned to the agent through an interactive list editor, so that I can tailor the agent's capabilities without editing raw configuration files.

**Why this priority**: Tools are a fundamental part of agent configuration. An intuitive tools editor is essential for the inline editing experience to be complete and usable. This is tightly coupled with User Story 1.

**Independent Test**: Can be tested by opening an agent's configuration editor, adding a new tool from the available tools list, removing an existing tool, reordering tools, and verifying all changes are tracked as unsaved modifications.

**Acceptance Scenarios**:

1. **Given** a user is editing an agent's configuration, **When** they view the tools section, **Then** the currently assigned tools are displayed as an interactive, editable list.
2. **Given** a user is editing the tools list, **When** they add a tool, **Then** the tool appears in the list and the unsaved-changes indicator is updated.
3. **Given** a user is editing the tools list, **When** they remove a tool, **Then** the tool is removed from the list and the unsaved-changes indicator is updated.
4. **Given** a user is editing the tools list, **When** they reorder tools (via drag-and-drop or move controls), **Then** the new order is reflected immediately and tracked as an unsaved change.
5. **Given** a user has removed all tools from the agent, **When** they attempt to save, **Then** an inline validation error is displayed indicating that at least one tool must be assigned.

---

### User Story 3 — Sun/Moon Themed Agent Avatars (Priority: P2)

As a user browsing the Agents page, I want each agent to display a unique sun/moon themed avatar that is consistently assigned based on the agent's identity, so that I can visually distinguish agents at a glance.

**Why this priority**: Visual identity improves scannability and recognition across the page. While not functional, it significantly enhances the user experience when managing multiple agents.

**Independent Test**: Can be tested by loading the Agents page with multiple agents and verifying each agent card displays a distinct sun/moon icon, and that the same agent always receives the same avatar across page loads.

**Acceptance Scenarios**:

1. **Given** the Agents page loads with multiple agents, **When** the user views the agent cards, **Then** each agent displays a unique avatar from the sun/moon icon set (e.g., full moon, crescent moon, sun with rays, eclipse, sunrise, half moon).
2. **Given** an agent with a specific identifier, **When** the page is loaded on different occasions, **Then** the same avatar is always assigned to that agent (deterministic assignment).
3. **Given** two agents with different identifiers, **When** the page is loaded, **Then** they receive different avatars (unless the total number of agents exceeds the icon set size, in which case icons may repeat but adjacent agents should differ).

---

### User Story 4 — Featured Agents Section (Priority: P2)

As a user visiting the Agents page, I want to see a "Featured Agents" section at the top highlighting the most-used or recently created agents, so that I can quickly access the agents most relevant to me.

**Why this priority**: Surfacing high-value agents improves discoverability and reduces the time spent scrolling through a full agent list. This is an enhancement that adds polish but is not blocking for core functionality.

**Independent Test**: Can be tested by verifying the Featured Agents section appears at the top of the page and displays up to 3 agent cards based on usage count and creation date criteria.

**Acceptance Scenarios**:

1. **Given** the Agents page loads and there are 3 or more agents with recorded usage data, **When** the user views the Featured Agents section, **Then** the top 3 agents by invocation/usage count are displayed.
2. **Given** the Agents page loads and fewer than 3 agents have significant usage data, **When** the user views the Featured Agents section, **Then** the section supplements with agents created within the past 3 days to fill up to 3 slots.
3. **Given** there are no agents with usage data and no agents created in the past 3 days, **When** the user views the page, **Then** the Featured Agents section is hidden or displays a helpful empty state message.
4. **Given** an agent is both highly used and recently created, **When** the Featured Agents section is populated, **Then** the agent appears only once (no duplicates).

---

### User Story 5 — Bulk Update All Agent Models (Priority: P2)

As a user managing multiple agents, I want a single action to update the model used by all agents at once, with a clear confirmation step, so that I can keep all agents aligned on the same model version without editing each one individually.

**Why this priority**: Bulk operations save significant time when managing many agents. The confirmation step ensures users don't accidentally apply unintended changes across all agents.

**Independent Test**: Can be tested by clicking the "Update All Models" button, selecting a target model, reviewing the confirmation dialog listing all affected agents, confirming the action, and verifying all agents are updated.

**Acceptance Scenarios**:

1. **Given** the user is on the Agents page, **When** they click the "Update All Models" button, **Then** a dialog appears allowing them to select a target model.
2. **Given** the user has selected a target model, **When** the confirmation dialog appears, **Then** it lists all agents that will be affected along with the target model name.
3. **Given** the user reviews the confirmation dialog, **When** they click "Confirm," **Then** all listed agents are updated to the selected model and a success notification is shown.
4. **Given** the user reviews the confirmation dialog, **When** they click "Cancel," **Then** no changes are made and the dialog closes.
5. **Given** the bulk update is triggered, **When** the update completes, **Then** all affected agents immediately use the selected model via runtime configuration updates, and no GitHub Pull Request is created for that bulk action.

---

### User Story 6 — Repository Name Display with Dynamic Fitting (Priority: P3)

As a user viewing agent cards, I want the repository field to show only the repository name (not the owner prefix) and have the text dynamically fit within its styled background bubble, so that the display is clean and readable regardless of name length.

**Why this priority**: This is a visual polish improvement. It makes agent cards cleaner but does not add new functionality.

**Independent Test**: Can be tested by viewing agent cards with repositories of varying name lengths and verifying the display shows only the repo name (not "owner/repo"), text fits within the bubble, and long names truncate with an ellipsis.

**Acceptance Scenarios**:

1. **Given** an agent is associated with a repository "owner/my-repo," **When** the agent card is displayed, **Then** only "my-repo" is shown in the repository field.
2. **Given** an agent has a repository with a very long name, **When** the agent card is displayed, **Then** the text either scales down or truncates with an ellipsis to fit within the background bubble without overflow.
3. **Given** an agent has a repository with a short name, **When** the agent card is displayed, **Then** the text fits naturally within the bubble without excessive whitespace.

---

### Edge Cases

- What happens when an agent has no usage data and was created more than 3 days ago? It should not appear in the Featured Agents section but remains visible in the full agent list.
- How does the system handle concurrent edits if two users edit the same agent simultaneously? The PR-based flow inherently handles this — each save creates a separate PR, and merge conflicts are resolved through the standard Git workflow.
- What happens if the GitHub token is invalid or expired when the user attempts to save? The system should display an appropriate error message and preserve the user's unsaved changes for retry.
- What happens if a user removes all tools and then tries to navigate away without saving? The blocking modal should still appear since there are unsaved changes, regardless of validation state.
- What if the sun/moon icon set has fewer variants than the total number of agents? Icons may repeat, but the assignment should minimize adjacent duplicates by distributing icons evenly via the deterministic hash.
- What happens when the "Update All Models" action is triggered but there are agents with unsaved inline edits? The system should warn the user about unsaved changes on specific agents and require them to save or discard before proceeding with the bulk update.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST assign each agent a unique sun/moon themed avatar deterministically derived from the agent's identifier, selecting from a predefined set of sun and moon visual variants (e.g., full moon, crescent moon, sun with rays, eclipse, sunrise, half moon, new moon, waning crescent, solar flare, moonrise).
- **FR-002**: System MUST display the same avatar for the same agent across all page loads and sessions (deterministic, stable assignment).
- **FR-003**: System MUST display a "Featured Agents" section at the top of the Agents page showing up to 3 agents, prioritizing agents by usage/invocation count.
- **FR-004**: System MUST supplement the Featured Agents section with agents created within the past 3 days if fewer than 3 high-usage agents are available, up to a maximum of 3 total.
- **FR-005**: System MUST hide the Featured Agents section or show an appropriate empty state when no agents qualify (no usage data and none created within the past 3 days).
- **FR-006**: System MUST allow users to edit agent definitions inline on the Agents page via a structured form editor (not raw file/text editing).
- **FR-007**: System MUST display a persistent unsaved-changes indicator (e.g., banner, badge, or icon) whenever the agent form has been modified but not yet saved.
- **FR-008**: System MUST present a blocking confirmation modal when the user attempts to navigate away from an agent with unsaved changes, offering options to save, discard, or cancel.
- **FR-009**: System MUST create a GitHub Pull Request containing the updated agent configuration file changes when the user saves an edited agent definition.
- **FR-010**: System MUST display a clickable link to the created Pull Request in the UI after a successful save.
- **FR-011**: System MUST show a success notification (e.g., toast) after a PR is successfully created, including a link to the PR.
- **FR-012**: System MUST provide an "Update All Models" action accessible from the Agents page (e.g., in a toolbar or settings area).
- **FR-013**: System MUST display a confirmation dialog when "Update All Models" is triggered, listing all affected agents and the target model to be applied.
- **FR-014**: System MUST only proceed with the bulk model update upon explicit user confirmation in the dialog.
- **FR-015**: System MUST display the repository field on agent cards and detail views using only the repository name (excluding the owner/organization prefix).
- **FR-016**: System MUST dynamically fit or scale the repository name text within its styled background bubble/chip, using ellipsis truncation as a fallback for long names.
- **FR-017**: System MUST render the tools section of each agent's configuration as an interactive, editable list allowing users to add, remove, and reorder tools.
- **FR-018**: System MUST track all tools list modifications (add, remove, reorder) as part of the agent's unsaved-changes state.
- **FR-019**: System SHOULD validate that at least one tool remains assigned to an agent before allowing save, displaying an inline error if the tools list is empty.
- **FR-020**: System SHOULD preserve unsaved changes when a save attempt fails (e.g., network error), allowing the user to retry.

### Key Entities

- **Agent**: Represents a configured agent with an identifier, name, description, assigned model, associated repository, tools list, creation date, and usage/invocation count. Each agent maps to a configuration file in the repository.
- **Agent Avatar**: A visual representation derived deterministically from the agent's identifier, drawn from a curated set of sun/moon themed icons.
- **Agent Configuration File**: The underlying file (e.g., YAML or JSON) that stores the agent's definition, including model, description, and tools. This file is the target of PR-based edits.
- **Pull Request**: A GitHub PR created automatically when the user saves agent configuration changes. Contains the diff of the modified agent config file against the default branch.
- **Tool**: A capability or integration assigned to an agent. Each tool has a name/identifier and optional configuration. Tools are managed as an ordered list within the agent's configuration.
- **Featured Agents**: A derived view showing up to 3 agents selected by usage count (primary) and recency of creation (secondary, within the past 3 days).

## Assumptions

- Agents already have a unique identifier (name or ID) that can be used for deterministic avatar assignment.
- The system has access to a valid GitHub token for creating PRs on behalf of the user.
- Agent usage/invocation count data is available (or can be tracked) to power the Featured Agents ranking.
- Agent creation timestamps are stored and accessible for the "created in the past 3 days" criterion.
- The existing Agents page already displays agent cards with a repository field; this feature enhances the existing display.
- The tools available for assignment to agents are known and can be presented as a selectable list.
- Standard session-based authentication is used; no additional auth flow is needed for saving.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can edit an agent's definition, save changes, and receive a PR link within 30 seconds of clicking "Save."
- **SC-002**: 100% of agent avatars are deterministically stable — the same agent always displays the same sun/moon avatar across page loads.
- **SC-003**: The Featured Agents section correctly displays up to 3 agents, with zero duplicates and correct prioritization by usage count and recency.
- **SC-004**: Users can add, remove, and reorder tools in an agent's configuration with all changes reflected in the unsaved-changes state within 1 second of each interaction.
- **SC-005**: The unsaved-changes modal successfully prevents unintended data loss in 100% of navigation-away attempts when changes are pending.
- **SC-006**: The bulk "Update All Models" action updates the stored runtime model configuration for all applicable agents, with 100% of targeted agents reflecting the new model on subsequent reads, completing within 60 seconds for up to 50 agents.
- **SC-007**: Repository names display correctly (owner prefix stripped) and fit within the background bubble on 100% of agent cards, with ellipsis applied for names exceeding the available width.
- **SC-008**: 90% of users can complete an agent configuration edit (including tools changes) and save on their first attempt without external guidance.
