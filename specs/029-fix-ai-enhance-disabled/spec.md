# Feature Specification: Fix — Use Exact User Input + Chat Agent Metadata When AI Enhance Is Disabled

**Feature Branch**: `029-fix-ai-enhance-disabled`  
**Created**: 2026-03-07  
**Status**: Draft  
**Input**: User description: "On the app user chat, when the AI Enhance is disabled I receive an error. If the 'AI Enhance' is disabled, use the user's exact chat input for the GitHub Parent Issue description but, use the Chat Agent to generate all the metadata needed for GitHub Issue creation (labels, estimates, title, etc) and add Agent Pipeline configuration information to description."

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Submit Chat Request with AI Enhance Disabled (Priority: P1)

As a Solune app user, I want to submit a chat request with the AI Enhance toggle turned off and have the system create a GitHub Parent Issue using my exact chat input as the description body, while the Chat Agent independently generates all required metadata (title, labels, size estimate, priority, assignees) and appends Agent Pipeline configuration to the description — without encountering the "I couldn't generate a task from your description" error.

**Why this priority**: This is the core bug fix. Users currently cannot create issues at all when AI Enhance is disabled because the system throws an error. Fixing this unblocks the entire non-enhanced workflow and restores a fundamental capability.

**Independent Test**: Can be fully tested by toggling AI Enhance off, typing any non-empty message in the chat, submitting it, and verifying that a GitHub issue is created with the raw user text as the description body and all metadata fields populated.

**Acceptance Scenarios**:

1. **Given** the user has the AI Enhance toggle disabled, **When** the user types a non-empty message in the chat input and submits it, **Then** the system creates a GitHub Parent Issue where the description body contains the user's exact, unmodified chat input text.
2. **Given** the user has the AI Enhance toggle disabled and submits a chat request, **When** the issue creation pipeline executes, **Then** the Chat Agent generates all required metadata — title, labels, size estimate, priority, and assignees — and attaches them to the created issue.
3. **Given** the user has the AI Enhance toggle disabled and submits a chat request, **When** the issue creation pipeline executes, **Then** the system appends Agent Pipeline configuration information to the issue description in a clearly delimited section separate from the user's raw input.
4. **Given** the user has the AI Enhance toggle disabled and submits any non-empty chat input, **When** the system processes the request, **Then** the user never sees the error message "I couldn't generate a task from your description. Please try again with more detail."

---

### User Story 2 — Seamless Submission Flow Without Visible Errors (Priority: P1)

As a Solune app user with AI Enhance disabled, I want the submission flow to feel seamless — no error messages, no stalled loading states, and no unexpected behavior — so that I have confidence the system handles my request correctly regardless of the AI Enhance setting.

**Why this priority**: Even if the issue is technically created, a poor user experience with transient errors or stalled states erodes trust. This story ensures the end-to-end flow is smooth and reliable.

**Independent Test**: Can be tested by submitting multiple chat requests in quick succession with AI Enhance off and verifying that each completes without any error toasts, stalled spinners, or UI freezes.

**Acceptance Scenarios**:

1. **Given** the user has AI Enhance disabled and submits a chat message, **When** the system processes the request, **Then** no error message, error toast, or error banner is displayed to the user at any point during the flow.
2. **Given** the user has AI Enhance disabled and submits a chat message, **When** the pipeline encounters the disabled AI Enhance flag, **Then** it silently bypasses the AI enhancement step without throwing or propagating an error.
3. **Given** the user has AI Enhance disabled and submits a chat message, **When** the pipeline is processing, **Then** the user sees appropriate loading/progress indicators (not a stalled or frozen state) until the issue is created.

---

### User Story 3 — Structural Parity Between Enhanced and Non-Enhanced Issues (Priority: P2)

As a project manager reviewing issues created by my team, I want GitHub issues created with AI Enhance disabled to be structurally identical to those created with AI Enhance enabled (same metadata fields, same Agent Pipeline config section, same label taxonomy) — differing only in that the description body contains raw user input instead of AI-enhanced content — so that my workflows, automations, and triage processes work consistently regardless of the enhancement setting.

**Why this priority**: Structural consistency ensures downstream processes (board views, automations, filters) are not broken by the enhancement toggle. Important but less urgent than the core bug fix.

**Independent Test**: Can be tested by creating two issues — one with AI Enhance on and one with AI Enhance off — from the same chat input, and comparing their structure: both should have the same metadata field types, the same Agent Pipeline configuration section, and the same label/estimate/assignee schema.

**Acceptance Scenarios**:

1. **Given** a user creates an issue with AI Enhance enabled and another with AI Enhance disabled using the same chat input, **When** both issues are inspected on GitHub, **Then** both have the same set of metadata field types (title, labels, size estimate, priority, assignees) populated.
2. **Given** an issue is created with AI Enhance disabled, **When** the issue is viewed on GitHub, **Then** the Agent Pipeline configuration section is present and formatted identically to how it appears on issues created with AI Enhance enabled.
3. **Given** an issue is created with AI Enhance disabled, **When** the issue description is viewed, **Then** the user's raw chat input appears first, followed by a clearly delimited Agent Pipeline configuration block (e.g., a markdown section with a heading or horizontal rule separator).

---

### User Story 4 — Independent Metadata Generation Failure Handling (Priority: P3)

As a Solune app user, if the Chat Agent metadata generation step itself fails (independent of AI Enhance), I want to see a specific, actionable error message that tells me what went wrong with metadata generation — not the generic "I couldn't generate a task" error — so that I know how to resolve the issue or retry.

**Why this priority**: This is a resilience improvement. The primary fix (P1) eliminates the error for the common case. This story covers the edge case where metadata generation itself fails and ensures the user gets helpful feedback.

**Independent Test**: Can be tested by simulating a metadata generation failure (e.g., via network interruption or mock) with AI Enhance disabled and verifying that a specific, actionable error is surfaced instead of the generic catch-all message.

**Acceptance Scenarios**:

1. **Given** the user has AI Enhance disabled and submits a chat request, **When** the Chat Agent metadata generation step fails due to an internal error, **Then** the system displays a specific error message indicating that metadata generation failed (not the generic "I couldn't generate a task" message).
2. **Given** the Chat Agent metadata generation step fails, **When** the error is surfaced to the user, **Then** the error message includes guidance on how to retry or what to check (e.g., "Metadata generation failed. Please try again.").

---

### Edge Cases

- What happens when the user submits an empty message with AI Enhance disabled? The system should validate that the chat input is non-empty before proceeding and display an appropriate input validation error (e.g., "Please enter a message").
- What happens when the user's chat input contains only whitespace? The system should treat whitespace-only input the same as empty input and prompt the user to provide content.
- What happens when the user's chat input contains special characters, markdown formatting, or very long text? The system should preserve the exact input — including all formatting, special characters, and full length — in the issue description without truncation or escaping.
- What happens when the AI Enhance toggle is toggled on/off mid-submission? The system should read the toggle state at the moment of submission and use that value for the entire pipeline execution; mid-flight toggle changes should not affect an in-progress request.
- What happens when the Chat Agent is temporarily unavailable but the user's raw input is valid? The system should still create the issue with the user's raw input as the description and surface a specific error about metadata generation failure, rather than blocking the entire issue creation.
- What happens when the AI Enhance feature is disabled at a system/admin level vs. user toggle level? The system should treat both as equivalent — if enhancement is off for any reason, the fallback metadata-only path should activate.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST detect when the AI Enhance toggle is disabled before invoking the content generation pipeline and branch into the fallback metadata-only path.
- **FR-002**: System MUST use the user's exact, unmodified chat input as the GitHub Parent Issue description body when AI Enhance is disabled — no summarization, paraphrasing, or reformatting.
- **FR-003**: System MUST invoke the Chat Agent to generate all required GitHub Issue metadata (title, labels, size estimate, priority, assignees, and any other structured fields) even when AI Enhance is disabled.
- **FR-004**: System MUST append Agent Pipeline configuration information to the GitHub Parent Issue description when AI Enhance is disabled, in a clearly delimited markdown section (e.g., under a heading or after a horizontal rule) that is visually distinct from the user's raw input.
- **FR-005**: System MUST NOT display the error message "I couldn't generate a task from your description. Please try again with more detail." when AI Enhance is disabled and the user has provided any non-empty chat input.
- **FR-006**: System MUST suppress or bypass any error thrown by the AI enhancement step when the toggle is off, ensuring the fallback path completes successfully and creates the GitHub issue.
- **FR-007**: System SHOULD validate that the Chat Agent metadata generation step succeeded independently of the AI Enhance step, and surface a specific, actionable error only if the metadata generation itself fails.
- **FR-008**: System MUST ensure the final GitHub issue created with AI Enhance disabled is structurally identical to one created with AI Enhance enabled, differing only in that the description body is the raw user input rather than AI-enhanced content.
- **FR-009**: System MUST validate that the user's chat input is non-empty (not blank or whitespace-only) before proceeding with issue creation, regardless of the AI Enhance toggle state.
- **FR-010**: System MUST read the AI Enhance toggle state at the moment of submission and use that value consistently throughout the entire pipeline execution for that request.

### Key Entities

- **Chat Request**: Represents a user's submission from the chat interface. Key attributes: chat input text (raw string), AI Enhance toggle state (boolean), submission timestamp, user identity.
- **AI Enhance Toggle**: A user-facing setting that controls whether the content enhancement pipeline is applied to the chat input. States: enabled (full AI pipeline) or disabled (metadata-only fallback path).
- **GitHub Parent Issue**: The resulting issue created on GitHub. Composed of: description body (raw user input or AI-enhanced content), title (Chat Agent–generated), labels, size estimate, priority, assignees, and Agent Pipeline configuration block.
- **Agent Pipeline Configuration**: A structured metadata block appended to the issue description that captures pipeline execution details (agents invoked, configuration parameters, execution context). Formatted as a clearly delimited markdown section.
- **Chat Agent**: The AI component responsible for generating GitHub Issue metadata (title, labels, estimates, priority, assignees) from the user's chat input. Operates independently of the AI Enhance content generation step.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users with AI Enhance disabled can successfully create GitHub issues 100% of the time when providing non-empty chat input, with zero occurrences of the "I couldn't generate a task" error.
- **SC-002**: The user's exact chat input appears verbatim in the GitHub issue description body with no modifications — character-for-character match with the original submission.
- **SC-003**: All metadata fields (title, labels, size estimate, priority, assignees) are populated on issues created with AI Enhance disabled, at the same rate and completeness as issues created with AI Enhance enabled.
- **SC-004**: The submission-to-issue-creation flow with AI Enhance disabled completes within the same time threshold as the AI Enhance enabled flow (user perceives no degradation).
- **SC-005**: Zero user-facing error messages are displayed during the submission flow when AI Enhance is disabled and valid (non-empty) input is provided.
- **SC-006**: Issues created with AI Enhance disabled pass the same structural validation as AI Enhance–enabled issues (same fields present, same Agent Pipeline config section, same label schema).
- **SC-007**: When metadata generation independently fails, users receive a specific, actionable error message instead of the generic catch-all error — reducing user confusion and support escalations.

## Assumptions

- The AI Enhance toggle is a boolean user-level setting accessible at the time of chat submission.
- The Chat Agent is capable of generating metadata (title, labels, estimates, etc.) from raw user input without requiring AI-enhanced content as input.
- The Agent Pipeline configuration block format is already defined and used in the AI Enhance–enabled flow; the same format will be reused in the disabled flow.
- The current error ("I couldn't generate a task from your description") is thrown because the pipeline assumes AI-enhanced content will always be available and fails when it is not.
- Input validation for empty/whitespace-only messages already exists or can be added as a pre-pipeline check without disrupting existing flows.
- The issue creation pipeline can be refactored into two explicit branches (full pipeline vs. metadata-only) without affecting existing AI Enhance–enabled behavior.
