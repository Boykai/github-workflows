# Feature Specification: Use Selected Agent Pipeline Config from Project Page When Creating GitHub Issues via Chat

**Feature Branch**: `030-chat-pipeline-config`
**Created**: 2026-03-08
**Status**: Draft
**Input**: User description: "The chat should use the currently selected Agent Pipeline configuration from Project page, when defining the Agent Pipeline for new GitHub Issues created via user chat"

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Automatic Pipeline Inheritance on Issue Creation (Priority: P1)

As a user interacting with the chat interface, I want new GitHub Issues I create through chat to automatically use the Agent Pipeline configuration I have currently selected on the Project page, so that I do not have to manually pick a pipeline every time I create an issue.

**Why this priority**: This is the core value proposition. Without automatic inheritance, every issue created via chat requires manual pipeline selection, which defeats the purpose of having a Project-level default. Delivering this story alone provides the majority of the user benefit.

**Independent Test**: Can be fully tested by selecting a pipeline on the Project page, opening chat, creating a new issue, and verifying the issue is tagged with the correct pipeline. Delivers the primary value of zero-effort pipeline assignment.

**Acceptance Scenarios**:

1. **Given** a user has selected "Pipeline Alpha" on the Project page, **When** the user creates a new GitHub Issue via chat, **Then** the newly created issue is automatically assigned "Pipeline Alpha" as its Agent Pipeline.
2. **Given** a user changes the selected pipeline on the Project page from "Pipeline Alpha" to "Pipeline Beta" (without reloading or restarting chat), **When** the user then creates a new GitHub Issue via chat, **Then** the issue is assigned "Pipeline Beta" — reflecting the most recent selection.
3. **Given** a user has selected a pipeline on the Project page, **When** the user creates multiple issues via chat in the same session, **Then** every issue uses the currently selected pipeline at the time each issue is created.

---

### User Story 2 — Warning When No Pipeline Is Selected (Priority: P2)

As a user who has not yet selected an Agent Pipeline on the Project page, I want the chat to warn me before creating an issue without a pipeline, so that I do not accidentally create issues with a missing or incorrect pipeline assignment.

**Why this priority**: Prevents silent misconfiguration. Without a warning, users may unknowingly create issues that lack a pipeline or use an unintended default, causing downstream confusion and rework.

**Independent Test**: Can be tested by ensuring no pipeline is selected on the Project page, then attempting to create an issue via chat. The chat must display a clear warning or prompt before proceeding.

**Acceptance Scenarios**:

1. **Given** no Agent Pipeline is currently selected on the Project page, **When** the user initiates issue creation via chat, **Then** the chat displays an inline warning indicating that no pipeline is selected and prompts the user to select one or proceed with a default.
2. **Given** the warning is displayed, **When** the user chooses to proceed anyway, **Then** the system falls back to a defined default pipeline (or surfaces an explicit error if no default exists) and creates the issue.
3. **Given** the warning is displayed, **When** the user navigates to the Project page and selects a pipeline, **Then** the chat reflects the new selection without requiring a page reload or chat restart.

---

### User Story 3 — Pipeline Confirmation in Chat (Priority: P3)

As a user who has just created an issue via chat, I want to see which Agent Pipeline was applied in the confirmation message, so that I can verify the correct pipeline was used without navigating away from the chat.

**Why this priority**: Builds user confidence and transparency. While the system works correctly behind the scenes, surfacing the pipeline name in the confirmation message removes ambiguity and reduces the need for users to manually verify on the issue itself.

**Independent Test**: Can be tested by creating an issue via chat with a selected pipeline and checking the confirmation or summary message for the pipeline name.

**Acceptance Scenarios**:

1. **Given** "Pipeline Alpha" is selected on the Project page, **When** the user creates an issue via chat and the issue is successfully created, **Then** the chat confirmation message includes the text "Agent Pipeline: Pipeline Alpha" (or an equivalent indicator showing the applied pipeline name).
2. **Given** no pipeline was selected and the system used a default, **When** the issue is created, **Then** the confirmation message indicates that the default pipeline was applied and names it.

---

### User Story 4 — Handling Deleted or Unavailable Pipelines (Priority: P3)

As a user whose previously selected pipeline has been deleted or become unavailable mid-session, I want the system to notify me and prompt re-selection, so that I do not create issues referencing a non-existent pipeline.

**Why this priority**: Edge case that prevents data integrity issues. While less common than the primary flow, creating an issue tied to a deleted pipeline could cause failures in downstream automation.

**Independent Test**: Can be tested by selecting a pipeline, then deleting that pipeline (or simulating its unavailability), and attempting to create an issue via chat.

**Acceptance Scenarios**:

1. **Given** the user had selected "Pipeline Alpha" on the Project page and "Pipeline Alpha" is subsequently deleted, **When** the user creates a new issue via chat, **Then** the chat notifies the user that the selected pipeline is no longer available and prompts them to select a different pipeline.
2. **Given** the pipeline becomes unavailable mid-session, **When** the user has not yet created an issue, **Then** the system detects the stale reference and updates the chat state to reflect that no valid pipeline is selected.

---

### Edge Cases

- What happens when the user has multiple projects open and switches between them — does the chat pipeline context update to the currently active project's pipeline?
- What happens when the pipeline selection is changed by another user or an automated process while the current user's chat session is active?
- What happens when the user opens chat in a new tab or window — does it inherit the same pipeline state as the Project page?
- How does the system behave if the pipeline service is temporarily unavailable when the user creates an issue?
- What happens if the user creates an issue via chat while the Project page is still loading (race condition on initial load)?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST read the currently selected Agent Pipeline configuration from the Project page at the time a new GitHub Issue is created via user chat.
- **FR-002**: System MUST pass the resolved Agent Pipeline configuration as part of the GitHub Issue creation payload, populating the Agent Pipeline field on the new issue.
- **FR-003**: System MUST NOT default to a hardcoded or previously cached Agent Pipeline when a valid Project-page selection exists.
- **FR-004**: System MUST keep the Agent Pipeline selection state in sync between the Project page and the chat context in real time, reflecting any changes the user makes without requiring a page reload or chat restart.
- **FR-005**: System SHOULD display a warning or prompt in the chat if no Agent Pipeline is currently selected on the Project page at the time of issue creation, preventing silent misconfiguration.
- **FR-006**: System MUST fall back to a defined default Agent Pipeline (or surface an explicit error) when no pipeline is selected and the user proceeds with issue creation.
- **FR-007**: System SHOULD surface the applied Agent Pipeline name in the chat's issue-creation confirmation or summary message so the user can verify the correct pipeline was used.
- **FR-008**: System SHOULD detect when a previously selected Agent Pipeline configuration has been deleted or become unavailable and notify the user, prompting re-selection before issue creation proceeds.
- **FR-009**: System MUST scope the pipeline selection to the currently active project, preventing a different project's pipeline from being used inadvertently in multi-project contexts.

### Key Entities

- **Agent Pipeline Configuration**: Represents a named, versioned set of agent tool and behavior definitions. Key attributes: unique identifier, display name, project association, active/inactive status.
- **Project**: The workspace context that owns pipeline configurations. A user works within one active project at a time; the selected pipeline is scoped to this project.
- **Chat-Created Issue**: A GitHub Issue initiated through the chat interface. Carries a reference to the Agent Pipeline Configuration that was active at creation time.

## Assumptions

- The Project page already has a mechanism for selecting an Agent Pipeline configuration (e.g., a dropdown or selector component).
- Both the Project page and the chat interface share the same application session and can access a common source of truth for the selected pipeline.
- A "default" pipeline can be defined at the project level or system level to serve as a fallback when no explicit selection exists.
- The chat interface already supports creating GitHub Issues; this feature extends that flow rather than building issue creation from scratch.
- Pipeline deletion or unavailability can be detected by the system through existing validation or status checks.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of issues created via chat when a pipeline is selected on the Project page are assigned the correct pipeline — zero manual corrections required.
- **SC-002**: Users can create an issue via chat with the correct pipeline in under 30 seconds, with no additional pipeline-selection steps compared to the current flow.
- **SC-003**: When no pipeline is selected, 100% of issue-creation attempts via chat result in either a user-visible warning/prompt or a clearly identified default pipeline assignment — no silent misconfiguration occurs.
- **SC-004**: Pipeline selection changes on the Project page are reflected in the chat context within 2 seconds, without requiring a page reload or chat restart.
- **SC-005**: 95% of users report confidence that the correct pipeline was applied, as measured by post-creation verification (e.g., checking the confirmation message rather than navigating to the issue).
