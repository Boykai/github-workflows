# Feature Specification: Debug & Fix Apps Page — New App Creation UX

**Feature Branch**: `051-fix-app-creation-ux`  
**Created**: 2026-03-17  
**Status**: Draft  
**Input**: User description: "Plan: Debug & Fix Apps Page — New App Creation UX"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Reliable Template File Copying During App Creation (Priority: P1)

As a user creating a new app, I want all template files to be reliably copied into my new repository so that my project is properly initialized with the correct directory structure and configuration files.

Currently, files that fail to read (e.g., due to encoding issues) are silently skipped, leaving the new repository in an incomplete state without any indication to the user. This story ensures template copying is robust and transparent.

**Why this priority**: Template files are the foundation of every new app. If they fail silently, the entire downstream pipeline (agents, workflows, prompts) breaks with no explanation. This is the most critical gap because it affects every single app creation.

**Independent Test**: Create a new app and verify that `.github/agents/`, `.github/prompts/`, `.github/workflows/`, `.specify/`, and `.gitignore` are all present in the created repository. Simulate a file read failure and confirm a warning is surfaced to the user.

**Acceptance Scenarios**:

1. **Given** a user creates a new app, **When** all template files are readable, **Then** all expected directories and files are committed to the new repository without warnings.
2. **Given** a user creates a new app, **When** one or more template files fail to read (e.g., encoding error), **Then** the app is still created, and specific warnings identifying each failed file are returned to the user.
3. **Given** a user creates a new app under high GitHub API load, **When** the branch-readiness check takes longer than 5 seconds, **Then** the system retries with exponential backoff for up to ~15 seconds before reporting a timeout failure.

---

### User Story 2 - Automatic Parent Issue Creation to Launch Agent Pipeline (Priority: P1)

As a user creating a new app with a pipeline selected, I want a Parent Issue to be automatically created in the new repository so that the Agent Pipeline is kickstarted without requiring manual intervention.

Currently, the `pipeline_id` field exists on the app creation payload but is stored without being used. This story wires up the existing building blocks so that selecting a pipeline during creation results in automatic issue creation and agent orchestration.

**Why this priority**: The Parent Issue is the entry point for the entire Agent Pipeline. Without it, the automated build workflow never starts — users must manually create issues and configure agents, defeating the purpose of the platform.

**Independent Test**: Create a new app with a pipeline selected and verify that a Parent Issue appears in the repository's Issues tab, containing a tracking table and sub-issues, and that the polling service begins monitoring agent assignments.

**Acceptance Scenarios**:

1. **Given** a user creates a new app with a pipeline selected, **When** the repository and template files are successfully committed, **Then** a Parent Issue titled "Build {app display name}" is created in the repository with a tracking table body.
2. **Given** a Parent Issue is successfully created, **When** the pipeline configuration is loaded, **Then** sub-issues are created for each agent in the pipeline, and polling is started to monitor agent assignments.
3. **Given** a user creates a new app with a pipeline selected, **When** the Parent Issue creation fails (e.g., GitHub API error), **Then** the app is still created successfully, and a warning is added indicating the pipeline could not be started.
4. **Given** a user creates a new app without selecting a pipeline (pipeline = "None"), **When** the creation completes, **Then** no Parent Issue is created and the app functions as a standalone repository.
5. **Given** the app targets a "same-repo" or "external-repo" type, **When** a pipeline is selected, **Then** the Parent Issue and sub-issues are created in the correct target repository.
6. **Given** a Parent Issue was created for an app, **When** the app record is saved, **Then** the `parent_issue_number` and `parent_issue_url` fields are persisted on the App record.

---

### User Story 3 - Pipeline Selection in Create App Dialog (Priority: P2)

As a user creating a new app, I want to select a pipeline from a dropdown in the Create App dialog so that I can choose which automated workflow to run on the new repository.

**Why this priority**: Pipeline selection is the user-facing trigger for the entire automated build process. Without it, users have no way to opt into pipeline-driven workflows at creation time. It depends on the backend wiring (P1) being in place.

**Independent Test**: Open the Create App dialog, verify a pipeline selector dropdown is visible, select a pipeline, submit the form, and confirm the `pipeline_id` is included in the creation payload.

**Acceptance Scenarios**:

1. **Given** a user opens the Create App dialog, **When** the dialog loads, **Then** a pipeline selector dropdown is displayed with available pipelines from the current Solune project.
2. **Given** a user views the pipeline selector, **When** no pipeline is desired, **Then** a "None" option is available as the default selection.
3. **Given** a user selects a pipeline and submits the form, **When** the creation request is sent, **Then** the selected `pipeline_id` is included in the request payload.

---

### User Story 4 - Complete Warning Display After App Creation (Priority: P2)

As a user who just created a new app, I want to see all warnings (not just the first one) so that I have full visibility into any issues that occurred during creation.

Currently, the frontend only displays `createdApp.warnings[0]`, hiding subsequent warnings from the user.

**Why this priority**: Users need full transparency into what happened during app creation. Hiding warnings leads to confusion when things don't work as expected downstream.

**Independent Test**: Create an app that generates multiple warnings (e.g., a template file failure and an Azure secret failure) and verify all warnings are displayed in the UI using a warning toast style.

**Acceptance Scenarios**:

1. **Given** an app creation generates multiple warnings, **When** the creation completes, **Then** all warnings are displayed to the user (not just the first).
2. **Given** warnings are displayed, **When** the user views them, **Then** they use a warning toast style (not error style) to distinguish from hard failures.
3. **Given** an app creation completes successfully with no warnings, **When** the result is shown, **Then** a summary toast displays: ✓ Repository created / ✓ Template files committed / ✓ Pipeline started (if applicable).
4. **Given** an app creation completes with partial success, **When** the result is shown, **Then** the summary toast shows checkmarks for successes and ⚠ for each warning.

---

### User Story 5 - Parent Issue Link and Pipeline Info in App Detail View (Priority: P3)

As a user viewing an existing app's details, I want to see the Parent Issue link and pipeline association so that I can quickly navigate to the tracking issue and understand the app's pipeline status.

**Why this priority**: This is a quality-of-life improvement for ongoing management. It depends on Parent Issue data (P1) being available and is less critical than the creation flow itself.

**Independent Test**: View an app that has an associated Parent Issue and verify the issue URL is displayed as a clickable link and the pipeline name is shown. Also verify that apps without a Parent Issue display correctly without errors.

**Acceptance Scenarios**:

1. **Given** an app has a `parent_issue_url`, **When** the user views the app detail page, **Then** the Parent Issue is displayed as a clickable link that opens in a new tab.
2. **Given** an app has an associated pipeline, **When** the user views the app detail page, **Then** the pipeline name is displayed alongside the Parent Issue link.
3. **Given** an app was created before this feature (no Parent Issue data), **When** the user views the app detail page, **Then** the page renders correctly without errors, and the Parent Issue section is simply absent.
4. **Given** an app has an active pipeline, **When** the user views the apps list, **Then** a small badge/indicator on the app card shows the pipeline status.

---

### Edge Cases

- What happens when GitHub API rate limits are hit during Parent Issue or sub-issue creation? The system treats this as a best-effort failure, adds a warning, and does not block app creation.
- What happens when the selected pipeline has no agent mappings? The Parent Issue is created but no sub-issues are generated; a warning informs the user.
- What happens when a user deletes an app that has a Parent Issue? The Parent Issue is closed (not deleted) in the repository.
- What happens when template files include binary content that cannot be read as text? The file is skipped, and a specific warning identifying the file is returned.
- What happens when the branch-readiness poll exhausts all retries? The system returns a clear error indicating the branch was not ready in time, with guidance to retry.
- What happens when two users create apps simultaneously with the same pipeline? Each app gets its own independent Parent Issue and sub-issues in its own repository.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST collect and return specific warnings for each template file that fails to copy, identifying the file path and failure reason.
- **FR-002**: System MUST NOT silently skip template files that fail to read — every failure MUST be recorded and surfaced.
- **FR-003**: System MUST retry branch-readiness checks with exponential backoff, supporting up to ~15 seconds of total wait time (approximately 10 retries).
- **FR-004**: System MUST include all template file warnings in the `warnings[]` array on the App response.
- **FR-005**: System MUST store `parent_issue_number` and `parent_issue_url` on the App data model, persisted in the database.
- **FR-006**: System MUST load and use the pipeline configuration when a `pipeline_id` is provided during app creation.
- **FR-007**: System MUST create a Parent Issue titled "Build {app display name}" after successful repository and template file commit, when a pipeline is selected.
- **FR-008**: System MUST include a tracking table in the Parent Issue body, following the existing pattern used in the recommendations/confirm flow.
- **FR-009**: System MUST create sub-issues for each agent in the pipeline and start polling for agent assignments after Parent Issue creation.
- **FR-010**: System MUST treat Parent Issue creation as best-effort — failure adds a warning but does not block app creation.
- **FR-011**: System MUST handle both "same-repo" and "external-repo" app types, creating the Parent Issue in the correct target repository.
- **FR-012**: System MUST provide a pipeline selector dropdown in the Create App dialog, populated with pipelines from the current Solune project.
- **FR-013**: System MUST default the pipeline selector to "None" (no pipeline).
- **FR-014**: System MUST display all warnings from app creation to the user, not just the first warning.
- **FR-015**: System MUST use warning-style toasts (not error-style) for creation warnings.
- **FR-016**: System MUST display a summary toast after app creation showing the status of each step (repository, template files, pipeline).
- **FR-017**: System MUST display the Parent Issue as a clickable link in the app detail view when available.
- **FR-018**: System MUST display a pipeline status badge on app cards in the apps list when an active pipeline exists.
- **FR-019**: System MUST maintain backward compatibility — apps created before this feature (without Parent Issue data) MUST display correctly without errors.
- **FR-020**: System MUST close (not delete) the Parent Issue when an app is deleted.

### Key Entities *(include if feature involves data)*

- **App**: Core entity representing a created application. Extended with `parent_issue_number` (integer, nullable) and `parent_issue_url` (string, nullable) to track the associated GitHub issue.
- **Pipeline Configuration**: Existing entity that defines the sequence of agents and their mappings. Referenced by `pipeline_id` on the App to determine which agents to orchestrate.
- **Parent Issue**: A GitHub Issue created in the target repository that serves as the entry point for the Agent Pipeline. Contains a tracking table and links to sub-issues.
- **Sub-Issue**: Individual GitHub Issues created under the Parent Issue, one per agent in the pipeline configuration.
- **Template Files**: The set of files (`.github/agents/`, `.github/prompts/`, `.github/workflows/`, `.specify/`, `.gitignore`) copied into new repositories during app creation.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of template files that are readable are successfully committed to new repositories — no silent failures.
- **SC-002**: Users see specific, actionable warnings for every template file that fails to copy within 5 seconds of app creation completing.
- **SC-003**: Branch-readiness checks succeed under normal GitHub load conditions (up to ~15 seconds of latency) without timing out.
- **SC-004**: When a pipeline is selected, a Parent Issue with tracking table and sub-issues appears in the target repository within 60 seconds of app creation.
- **SC-005**: Users can select a pipeline during app creation in under 10 seconds (dropdown loads and is interactive quickly).
- **SC-006**: All creation warnings are visible to the user — no information is hidden or truncated.
- **SC-007**: Users can navigate from the app detail view to the Parent Issue in one click.
- **SC-008**: Existing apps created before this feature continue to display correctly in both list and detail views with zero errors.
- **SC-009**: App creation with pipeline selection completes end-to-end (repo + files + Parent Issue + sub-issues + polling) within 90 seconds under normal conditions.
- **SC-010**: Parent Issue creation failures do not increase the app creation failure rate — creation still succeeds with a warning.

## Assumptions

- Pipeline presets are sourced from the current Solune project, not from the newly created repository (which has no presets yet).
- The Parent Issue body includes the app description, a Solune dashboard link, and a tracking table, matching the existing `recommendations/confirm` pattern.
- The `.specify/memory/` directory exclusion from template files is intentional and will be verified during implementation. If it should be included, it will be added.
- Exponential backoff for branch-readiness uses a standard doubling pattern (e.g., 1s, 2s, 4s...) capped at a reasonable maximum per-retry delay.
- The "close parent issue on app deletion" behavior is included in this feature scope as specified in the plan.
- Database migration for new App model fields will follow the existing migration pattern in the repository.
