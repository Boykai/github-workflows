# Feature Specification: Projects Page — Upload GitHub Parent Issue Description & Select Agent Pipeline Config

**Feature Branch**: `032-issue-upload-pipeline-config`
**Created**: 2026-03-10
**Status**: Draft
**Input**: User description: "On the Projects page. Add support for a user to upload a GitHub Parent Issue description directly and select the Agent Pipeline Config."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Paste a GitHub Parent Issue Description and Select Pipeline Config (Priority: P1)

A user navigates to the Projects page and wants to bootstrap an agent workflow from an existing GitHub issue. They paste the full text of a GitHub Parent Issue description into a text input area, choose an Agent Pipeline Config from a dropdown of available configurations, and submit the form. The system validates both inputs, triggers the agent pipeline with the provided data, and shows a success confirmation or navigates the user to the resulting project/agent run view.

**Why this priority**: This is the core workflow that delivers the primary value of the feature — allowing users to quickly start agent pipelines from GitHub issue context without manual re-entry.

**Independent Test**: Can be fully tested by pasting a sample issue description, selecting any available pipeline config, submitting, and verifying the pipeline is invoked with the correct inputs and a success state is displayed.

**Acceptance Scenarios**:

1. **Given** a user is on the Projects page and at least one Agent Pipeline Config exists, **When** the user pastes a GitHub Parent Issue description into the text input area and selects a pipeline config from the dropdown, **Then** both inputs are displayed in the form and the submit button becomes enabled.
2. **Given** the user has entered a valid issue description and selected a pipeline config, **When** the user clicks the submit/confirm button, **Then** the system passes both the issue description text and the selected pipeline config identifier to the downstream agent pipeline execution logic.
3. **Given** a successful submission, **When** the pipeline invocation completes, **Then** the user sees a success confirmation state or is navigated to the relevant project/agent run view.
4. **Given** a submission fails due to a server error, **When** the error response is received, **Then** the user sees an inline error message, and the form retains all entered data so nothing is lost.

---

### User Story 2 - Upload an Issue Description from a File (Priority: P2)

A user has the GitHub Parent Issue description saved as a Markdown or plain-text file on their local machine. Instead of pasting, they upload the file directly. The system reads the file content and populates the text input area so the user can review before submitting.

**Why this priority**: This is a convenience enhancement over paste. It reduces friction for users who export or download issue descriptions, but paste covers the core need.

**Independent Test**: Can be tested by uploading a `.md` or `.txt` file containing a sample issue description and verifying the text area is populated with the file content, then proceeding through submission.

**Acceptance Scenarios**:

1. **Given** a user is on the Projects page, **When** the user selects a `.md` or `.txt` file via the file upload control, **Then** the file content is read and displayed in the issue description text area.
2. **Given** a user uploads a file, **When** the content populates the text area, **Then** the user can edit the content before submitting.
3. **Given** a user selects an unsupported file type (e.g., `.exe`, `.jpg`), **When** the upload is attempted, **Then** the system shows an inline validation message indicating only `.md` and `.txt` files are accepted, and no content is loaded.

---

### User Story 3 - Inline Validation Prevents Incomplete Submissions (Priority: P1)

A user attempts to submit the form without providing the required inputs. The system displays clear, inline error messages indicating which fields are missing, and does not allow submission until both the issue description and pipeline config are provided.

**Why this priority**: Validation is essential to prevent empty or malformed submissions and to provide a smooth user experience. It is tightly coupled with the core submission workflow.

**Independent Test**: Can be tested by attempting to submit the form with an empty description, with no pipeline config selected, and with both missing — verifying that appropriate error messages appear and submission is blocked in each case.

**Acceptance Scenarios**:

1. **Given** the issue description text area is empty and no pipeline config is selected, **When** the user clicks submit, **Then** inline error messages appear for both fields and the form is not submitted.
2. **Given** the issue description is filled but no pipeline config is selected, **When** the user clicks submit, **Then** an inline error message appears only for the pipeline config field.
3. **Given** a pipeline config is selected but the issue description is empty, **When** the user clicks submit, **Then** an inline error message appears only for the issue description field.
4. **Given** a validation error is displayed, **When** the user corrects the missing input, **Then** the error message for that field is cleared immediately without requiring a re-submission attempt.

---

### User Story 4 - Dynamic Pipeline Config Selection (Priority: P2)

The Agent Pipeline Config dropdown is populated dynamically from the system's existing configurations. The list stays current without requiring a page reload. If no configurations are available or loading fails, the user is informed gracefully.

**Why this priority**: Dynamic population ensures users always see current configs, but the feature can initially work with a static or pre-fetched list.

**Independent Test**: Can be tested by verifying the dropdown loads available configs on page load, reflects newly added configs without a page refresh, and shows an empty/error state if the config fetch fails.

**Acceptance Scenarios**:

1. **Given** the user navigates to the Projects page, **When** the form section loads, **Then** the Agent Pipeline Config dropdown is populated with all available configurations from the system.
2. **Given** no Agent Pipeline Configs exist in the system, **When** the dropdown loads, **Then** the dropdown shows an informative empty state (e.g., "No pipeline configs available") and the submit button is disabled.
3. **Given** the config fetch fails due to a network or server error, **When** the dropdown attempts to load, **Then** a user-friendly error message is displayed and the user can retry loading.

---

### Edge Cases

- What happens when the pasted/uploaded issue description is extremely large (e.g., > 100 KB)? The system should enforce a reasonable maximum size and show a validation message if exceeded.
- What happens when the user navigates away from the page mid-form-entry? The system should not persist partial form state to the server, but standard browser behavior (unsaved changes warning) is acceptable.
- What happens if the selected pipeline config is deleted or becomes unavailable between selection and submission? The system should return a clear error message indicating the config is no longer available and prompt the user to re-select.
- What happens if the user submits while another submission is already in progress? The submit button should be disabled during submission to prevent duplicate requests.
- What happens if the file upload is cancelled midway? The text area should remain unchanged from its prior state.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide a multi-line text input area on the Projects page where users can paste a GitHub Parent Issue description.
- **FR-002**: System MUST provide a selection control (dropdown or similar) on the Projects page for users to choose from available Agent Pipeline Configs.
- **FR-003**: System MUST validate that both the issue description (non-empty, non-whitespace) and a pipeline config selection are present before allowing form submission.
- **FR-004**: System MUST display clear, inline error messages adjacent to each field when validation fails, specifying what is missing or invalid.
- **FR-005**: System MUST associate the submitted issue description text with the selected Agent Pipeline Config identifier and pass both to the downstream agent pipeline execution logic upon form submission.
- **FR-006**: System MUST display a success confirmation state or navigate the user to the relevant project or agent run view after a successful pipeline invocation.
- **FR-007**: System MUST preserve all form field values (issue description text and selected config) if a validation or submission error occurs, preventing data loss.
- **FR-008**: System MUST disable the submit button while a submission is in progress to prevent duplicate requests, and re-enable it upon completion or failure.
- **FR-009**: System SHOULD support file upload (`.md` and `.txt` files) as an alternative input method for the GitHub Parent Issue description, reading the file content into the text area.
- **FR-010**: System SHOULD reject file uploads of unsupported types with a clear inline validation message.
- **FR-011**: System SHOULD dynamically fetch and populate the Agent Pipeline Config selection list from the existing system configurations, keeping the list reactive (updated without full page reload).
- **FR-012**: System SHOULD display a meaningful empty state in the pipeline config selector when no configurations are available.
- **FR-013**: System SHOULD handle config-fetch errors gracefully with a user-friendly message and a retry mechanism.
- **FR-014**: System MUST match the existing Projects page design patterns, visual style, and component conventions (Project Solune aesthetic).
- **FR-015**: System MUST enforce a maximum size limit on the issue description input to prevent excessively large payloads.

### Key Entities

- **GitHub Parent Issue Description**: A free-text body (Markdown or plain text) representing the content of a GitHub issue. Captured as a text field. Provided by the user via paste or file upload.
- **Agent Pipeline Config**: A named configuration that defines how an agent pipeline should execute. Referenced by a unique identifier (ID or slug). Selected from a list of available configs in the system.
- **Pipeline Submission**: The association of one GitHub Parent Issue Description with one Agent Pipeline Config, submitted by the user to trigger a pipeline execution. Results in a project or agent run.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can paste an issue description, select a pipeline config, and trigger a pipeline run in under 60 seconds from landing on the Projects page.
- **SC-002**: 100% of submissions with missing fields are blocked by client-side validation before reaching the server.
- **SC-003**: Users who upload a `.md` or `.txt` file see the content populated in the text area within 2 seconds.
- **SC-004**: The pipeline config dropdown reflects all currently available configurations with no stale entries after configs are added or removed.
- **SC-005**: Users receive clear feedback (success confirmation or error message) within 5 seconds of submitting the form.
- **SC-006**: Zero data loss on form state — if a submission fails, 100% of previously entered data remains intact in the form fields.
- **SC-007**: The feature is visually consistent with the existing Projects page design, passing a visual review against current page patterns.

## Assumptions

- The existing Projects page component and layout are available and extensible for adding new form sections.
- A mechanism for retrieving the list of available Agent Pipeline Configs already exists or can be extended.
- The downstream agent pipeline execution logic accepts a text description and a config identifier as inputs.
- Standard web application performance expectations apply (sub-second UI interactions, reasonable network latency).
- File upload is limited to client-side file reading; no server-side file storage is needed for the uploaded issue description.
- Session-based or token-based authentication is already in place; no new auth mechanism is needed for this feature.
- The maximum issue description size will follow a reasonable default (e.g., 500 KB) consistent with typical GitHub issue sizes.
