# Feature Specification: Custom Agent Creation via Chat (#agent)

**Feature Branch**: `001-custom-agent-creation`  
**Created**: 2026-02-28  
**Status**: Draft  
**Input**: User description: "Users can type #agent <description> #<status-name> in either the in-app ChatPopup or Signal to create a fully configured custom GitHub agent through a guided multi-step conversation. The system creates all artifacts: database config, GitHub Project column, GitHub Issue, PR with config files, and updates the project board."

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Create a Custom Agent via In-App Chat (Priority: P1)

An admin user opens the in-app chat widget while viewing a specific GitHub project. They type a command like `#agent Reviews PRs for security vulnerabilities #in-review` and the system begins a guided conversation. The system infers the target project from the current UI context, resolves the status column (matching "in-review" to "In Review"), uses AI to generate a full agent configuration (name, description, system prompt, tools), and presents a formatted preview. The user reviews, optionally requests edits ("change the name to SecBot"), and confirms. The system then executes a creation pipeline that produces all required artifacts: a saved agent configuration, a GitHub Project column (if new), a GitHub Issue with the agent spec, a dedicated branch with configuration files, a Pull Request, and an updated project board status. A per-step status report is displayed in the chat.

**Why this priority**: This is the core value proposition — enabling admin users to create fully configured agents through natural language conversation without manual file editing or multi-tool coordination. It delivers the complete end-to-end flow.

**Independent Test**: Can be fully tested by an admin user typing `#agent <description> #<status>` in the chat widget, completing the guided flow, and verifying all artifacts are created (saved agent configuration, GitHub Issue, Pull Request with config files, project board update).

**Acceptance Scenarios**:

1. **Given** an admin user is viewing a project in the app and the chat widget is open, **When** they type `#agent Reviews PRs for security vulnerabilities #in-review`, **Then** the system infers the target project from the UI context, resolves "in-review" to the existing "In Review" column, generates an agent preview (name, description, system prompt, assigned column, tools), and displays it in chat.
2. **Given** the system has presented an agent preview, **When** the user says "looks good", **Then** the system executes the creation pipeline and reports per-step success/failure status with checkmarks or crosses.
3. **Given** the system has presented an agent preview, **When** the user says "change name to SecBot", **Then** the system updates the preview with the new name and re-displays it for confirmation.
4. **Given** the creation pipeline is executing, **When** one step fails (e.g., column creation), **Then** the system continues attempting remaining steps and reports which steps succeeded and which failed with clear error messages.
5. **Given** a non-admin user attempts to use the `#agent` command, **When** the command is sent, **Then** the system rejects the request with an appropriate permissions error message.

---

### User Story 2 — Create a Custom Agent via Signal (Priority: P2)

An admin user sends a `#agent` command via Signal messaging. Since Signal lacks UI context, if the user has access to multiple projects, the system asks which project should be used (presenting a numbered list). The user selects a project, and the same guided conversation flow proceeds: status resolution, AI-generated preview, edit loop, confirmation, and pipeline execution with per-step reporting.

**Why this priority**: Extends the core functionality to the Signal messaging channel, enabling agent creation from mobile or external contexts. Depends on the core pipeline from P1 being functional.

**Independent Test**: Can be tested by an admin sending `#agent Triages new issues #backlog` via Signal, selecting a project from the presented list, completing the guided flow, and verifying all artifacts are created.

**Acceptance Scenarios**:

1. **Given** an admin user sends `#agent Triages new issues #backlog` via Signal and has access to multiple projects, **When** the system receives the command, **Then** it presents a numbered list of available projects and asks the user to choose.
2. **Given** the user has selected a project from the Signal prompt, **When** the conversation continues, **Then** the system proceeds with status resolution, preview generation, and the same guided flow as the in-app chat.
3. **Given** an admin user sends `#agent Triages new issues #backlog` via Signal and has access to only one project, **When** the system receives the command, **Then** it automatically uses that project without asking.

---

### User Story 3 — Status Column Resolution and Creation (Priority: P3)

When the user provides a status name (e.g., `#in-review`, `#backlog`, `#code-review`), the system matches it against existing columns in the target project, tolerating common variations in formatting. If a match is found, it uses that column. If no match is found, it informs the user that a new column will be created with that name. If no status is provided, the system asks the user to choose from existing columns or suggest a new one.

**Why this priority**: Status column resolution is critical for correctly placing agents on the project board, but the core orchestration flow (P1) must exist first for this to be meaningful.

**Independent Test**: Can be tested by providing various status name formats (`#in-review`, `#InReview`, `#IN_REVIEW`) and verifying correct resolution against existing project columns.

**Acceptance Scenarios**:

1. **Given** a project has columns "To Do", "In Progress", "In Review", "Done", **When** the user provides `#in-review`, **Then** the system matches it to the "In Review" column despite the formatting difference.
2. **Given** a project has columns "To Do", "In Progress", "Done", **When** the user provides `#code-review`, **Then** the system informs the user that a new "Code Review" column will be created.
3. **Given** the user does not provide a status name, **When** the command is parsed, **Then** the system presents existing columns and asks the user to choose one or suggest a new name.
4. **Given** a status column match is found, **When** the agent is created, **Then** the agent is placed at the last position in the assigned status column by default.

---

### User Story 4 — AI-Generated Agent Preview and Edit Loop (Priority: P4)

After resolving context and status, the system uses AI to generate a complete agent configuration from the user's natural language description. The preview includes: agent name, one-line description, full system prompt, assigned status column, and the full set of available tools. The user can request multiple rounds of edits before confirming.

**Why this priority**: Provides the interactive refinement experience that makes agent creation user-friendly. Depends on command parsing and context resolution working first.

**Independent Test**: Can be tested by providing a description, verifying the AI-generated preview contains all required fields, requesting edits, and confirming the preview updates correctly.

**Acceptance Scenarios**:

1. **Given** the user has provided a description like "Reviews PRs for security vulnerabilities", **When** the system generates a preview, **Then** the preview includes a concise name, one-line description, detailed system prompt, resolved status column, and all available tools.
2. **Given** a preview is displayed, **When** the user says "update the system prompt to also check for SQL injection", **Then** the system regenerates only the system prompt with the requested change and re-displays the full preview.
3. **Given** a preview is displayed, **When** the user says "create", "confirm", "yes", or "looks good", **Then** the system proceeds to execute the creation pipeline.
4. **Given** a preview is displayed, **When** the user requests multiple sequential edits, **Then** each edit is applied cumulatively and the latest preview reflects all changes.

---

### User Story 5 — Creation Pipeline Execution and Artifact Generation (Priority: P5)

Upon confirmation, the system executes a multi-step creation process that produces all necessary artifacts: a saved agent configuration, a GitHub Project column (if new), a GitHub Issue with detailed spec, a dedicated branch with configuration files, a Pull Request, and a project board status update. Each step reports its success or failure independently. The system uses best-effort execution — if a step fails, it continues with remaining steps.

**Why this priority**: This is the "delivery" portion of the feature. It depends on all upstream steps (parsing, resolution, preview, confirmation) but is what ultimately produces value (the created artifacts).

**Independent Test**: Can be tested by confirming a generated agent config and verifying each artifact exists (saved configuration, issue, branch with files, Pull Request, board status).

**Acceptance Scenarios**:

1. **Given** the user has confirmed an agent configuration, **When** the pipeline executes successfully, **Then** the following artifacts are created: a saved agent configuration, a GitHub Project column (if new), a GitHub Issue labeled "agent-config", a dedicated branch with agent configuration files and a README entry, a Pull Request referencing the issue, and the issue is moved to "In Review" on the project board.
2. **Given** the pipeline is executing, **When** a step fails, **Then** the system continues attempting remaining steps and produces a report showing checkmarks for successes and crosses for failures with error details.
3. **Given** a step fails because the target already exists (e.g., column already present), **When** the system detects this, **Then** it treats the step as successful and continues.
4. **Given** the pipeline completes, **When** the status report is displayed, **Then** each step is listed with its outcome (success/failure) and the overall result is clear to the user.

---

### Edge Cases

- What happens when the user provides a description that is too vague for the AI to generate a meaningful agent? The system should generate a best-effort preview and highlight areas the user may want to refine.
- What happens when the user provides a status name that closely matches multiple existing columns (e.g., `#review` matching both "In Review" and "Code Review")? The system should present the ambiguous matches and ask the user to choose.
- What happens when the target repository has changed since the command started? The system should use the latest state of the repository at the time of execution.
- What happens when the user abandons the conversation mid-flow (e.g., closes the chat or stops responding)? The conversation state should be cleaned up after a reasonable timeout period; no partial artifacts should be created since the creation process only starts after explicit confirmation.
- What happens when the same agent name already exists? The system should detect the conflict and ask the user to choose a different name before proceeding.
- What happens when network connectivity to GitHub is lost during pipeline execution? The system should report which steps completed before the failure and which were skipped, following the best-effort approach.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST recognize and parse the `#agent <description> #<status-name>` command syntax from both in-app chat and Signal messaging channels.
- **FR-002**: System MUST restrict the `#agent` command to admin users only; non-admin users MUST receive an appropriate error message.
- **FR-003**: System MUST infer the target project from the current UI context when the command is sent from the in-app chat.
- **FR-004**: System MUST prompt the user to select a project when invoked from Signal and the user has access to multiple projects.
- **FR-005**: System MUST automatically select the project when invoked from Signal and the user has access to only one project.
- **FR-006**: System MUST resolve the provided status name to an existing project column by matching common variations (e.g., "in-review", "InReview", "in_review" all resolve to "In Review").
- **FR-007**: System MUST inform the user when a provided status name does not match any existing column and offer to create a new column with that name.
- **FR-008**: System MUST ask the user to select or create a status column when no status name is provided in the command.
- **FR-009**: System MUST present ambiguous status matches (multiple close matches) to the user for selection rather than assuming one.
- **FR-010**: System MUST use AI to generate a complete agent configuration (name, description, system prompt) from the user's natural language description.
- **FR-011**: System MUST automatically include all available tools in the generated agent configuration without requiring user selection.
- **FR-012**: System MUST present a formatted preview of the generated agent configuration before proceeding to creation.
- **FR-013**: System MUST support an iterative edit loop where the user can request changes to any part of the preview and see updated results.
- **FR-014**: System MUST proceed to creation only upon explicit user confirmation (e.g., "create", "confirm", "yes", "looks good").
- **FR-015**: System MUST produce the following artifacts upon successful creation: a saved agent configuration, a GitHub Project column (if new), a GitHub Issue with the agent spec, a dedicated branch with agent configuration files, a Pull Request referencing the issue, and the issue moved to "In Review" on the project board.
- **FR-016**: System MUST persist the agent configuration so it is available for use after creation.
- **FR-017**: System MUST create a GitHub Issue in the target repository with the agent specification, labeled "agent-config".
- **FR-018**: System MUST create a dedicated branch for the new agent's configuration files, derived from the repository's main line of development.
- **FR-019**: System MUST include the following configuration files for the new agent on the dedicated branch: an agent configuration file, a prompt definition file, and a README entry (create or append).
- **FR-020**: System MUST open a Pull Request from the agent branch to the main development line, referencing the created issue.
- **FR-021**: System MUST move the created issue to "In Review" status on the project board after the Pull Request is opened.
- **FR-022**: System MUST use best-effort execution — if a creation step fails, continue attempting remaining steps where possible.
- **FR-023**: System MUST report per-step success or failure status with clear indicators (checkmarks/crosses) and error messages for failures.
- **FR-024**: System MUST NOT undo successfully completed steps when a subsequent step fails.
- **FR-025**: System MUST place the agent at the last position in the assigned status column by default.
- **FR-026**: System MUST detect and report conflicts when an agent with the same name already exists.
- **FR-027**: System MUST maintain conversation state across the multi-step guided flow, scoped to the individual user session, for the duration of the conversation.
- **FR-028**: System MUST allow the user to override the inferred project context (e.g., "use project X instead").

### Key Entities

- **Agent Configuration**: Represents a fully defined custom agent. Key attributes: name (unique identifier), description (one-line summary), system prompt (behavioral instructions), assigned status column, tools (full set of available tools).
- **Creation Process**: A sequence of steps that produces all artifacts for a new agent. Each step has an individual success/failure state. Exists only during the active creation session.
- **Conversation State**: Tracks the multi-step guided flow for a single user session. Attributes: current step, target project/repository, generated preview, pending edits, resolved status column. Scoped per user session for the duration of the conversation.
- **Agent Artifacts**: The set of configuration files and documentation produced for a new agent: agent configuration file, prompt definition file, and README entry.

## Scope

### In Scope

- Creating a single agent through a guided conversational flow via `#agent` command
- Command support in both in-app chat and Signal messaging channels
- AI-generated agent configuration from natural language descriptions
- Interactive preview and iterative editing before confirmation
- Full artifact creation: saved configuration, GitHub Issue, branch with config files, Pull Request, project board update
- Status column resolution (matching existing columns) and creation of new columns
- Best-effort creation process with per-step status reporting
- Admin-only access control

### Out of Scope

- Editing or updating existing agents after creation (future feature)
- Deleting agents via the `#agent` command
- Batch creation of multiple agents in a single conversation
- Retrying failed creation steps (`#agent retry` — suggested for future implementation)
- Listing or discovering existing agents via the `#agent` command
- Agent execution or runtime behavior (handled by existing agent system)
- Support for non-GitHub project management platforms
- Automated testing or validation of the created agent's behavior

## Assumptions

- Admin user authentication and authorization are already implemented in the system and can be reused for the `#agent` command.
- The system's AI capabilities can generate meaningful agent names, descriptions, and system prompts from natural language input.
- The system has sufficient permissions to create branches, issues, pull requests, and update project boards in target repositories.
- The in-app chat widget already provides the currently selected project context with each message.
- Signal messaging integration already supports multi-turn conversations and can relay formatted messages (or plain-text equivalents) back to the user.
- The existing agent configuration storage can accommodate the fields needed for custom agents without modification.
- "In Review" (or equivalent) is a standard status column expected to exist on most project boards; if it does not exist, the final creation step may fail gracefully.
- Conversation state cleanup follows the same timeout patterns used for other session-scoped state in the application.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: An admin user can go from typing the `#agent` command to having all artifacts created (saved agent configuration, GitHub Issue, Pull Request with config files, project board update) in under 5 minutes, including the preview and confirmation steps.
- **SC-002**: 90% of agent creation attempts that reach the confirmation step result in all creation steps completing successfully.
- **SC-003**: Users can complete the full guided conversation (command → preview → confirm → artifacts) in 5 or fewer conversational exchanges on average.
- **SC-004**: Status name resolution correctly handles common variations (hyphenated, underscored, mixed case, concatenated) with 95% accuracy against existing project columns.
- **SC-005**: When a creation step fails, the user receives a clear, actionable status report within the same conversation, and all other independent steps still complete.
- **SC-006**: The `#agent` command works identically across both communication channels (in-app chat and Signal), producing the same artifacts regardless of the channel used.
- **SC-007**: The edit loop allows at least 3 rounds of revisions before confirmation without state loss or degradation of the preview quality.
- **SC-008**: Non-admin users are blocked from using the `#agent` command 100% of the time, with a clear error message displayed.
