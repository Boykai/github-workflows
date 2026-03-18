# Feature Specification: Debug & Fix Apps Page — New App Creation UX

**Feature Branch**: `051-app-creation-ux`  
**Created**: 2026-03-18  
**Status**: Draft  
**Input**: User description: "The 'Create New App' flow creates a GitHub repo and commits template files, but has three critical gaps: (1) template files silently fail to copy, (2) no Parent Issue is created to kickstart the Agent Pipeline, and (3) the frontend lacks pipeline selection and post-creation feedback."

## Overview

The Solune "Create New App" flow currently creates a GitHub repository and commits scaffold template files, but three critical gaps prevent the feature from delivering its full value:

1. **Silent template failures** — When template files fail to read (encoding issues, missing directories), they are silently skipped with only a server-side log warning. Users receive no indication that their new repository may be missing critical files.
2. **No Parent Issue or Pipeline kickstart** — After creating a repository, the system never creates a Parent Issue or starts the Agent Pipeline. All the building blocks exist (issue creation, sub-issue orchestration, polling) but are not wired into the app creation flow.
3. **Limited frontend feedback** — The creation dialog lacks pipeline selection, only the first warning is displayed to users, and there is no structured post-creation summary.

### Assumptions

- Pipeline presets are sourced from the current Solune project (not the newly created repository, which has no presets yet)
- Parent issue body includes the app description, a link back to the Solune dashboard, and the agent tracking table — matching the existing `recommendations/confirm` pattern
- Parent issue title follows the format: `"Build {app.display_name}"`
- Parent issue creation is best-effort — failure generates a warning but does not block app creation
- Pipeline selection is optional — when no pipeline is selected, no parent issue is created
- Template file read failures surface as warnings, not hard errors, to avoid blocking otherwise successful app creation
- On app deletion, the parent issue is closed (not deleted) to preserve the audit trail
- The `.specify/memory/` directory is intentionally excluded from template copying
- Standard web application performance expectations apply (operations complete within a few seconds)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Reliable Template File Delivery (Priority: P1)

As a user creating a new app, I need all scaffold template files to be successfully committed to the new repository so that the agent pipeline and CI/CD workflows function correctly from the start. When some files fail to copy, I must be informed so I can take corrective action.

**Why this priority**: Template files are the foundation of the new repository. Without `.github/agents/`, `.github/prompts/`, `.github/workflows/`, `.specify/`, and `.gitignore`, the agent pipeline and CI/CD cannot function. Silent failures here have cascading downstream effects.

**Independent Test**: Can be fully tested by creating a new-repo app and verifying (a) all expected directories/files are present in the GitHub repository, and (b) if any file fails, a descriptive warning appears in the creation response.

**Acceptance Scenarios**:

1. **Given** a user creates a new-repo app, **When** all template files are readable, **Then** the repository contains `.github/agents/`, `.github/prompts/`, `.github/workflows/`, `.specify/`, and `.gitignore` after creation.
2. **Given** a user creates a new-repo app, **When** one or more template files fail to read (e.g., encoding issue), **Then** the remaining files are still committed, and a warning listing the failed files is included in the creation response.
3. **Given** the GitHub API is under heavy load, **When** the branch HEAD OID is not available within 5 seconds, **Then** the system retries with increasing intervals for up to approximately 15 seconds before reporting failure.

---

### User Story 2 - Automatic Parent Issue and Pipeline Launch (Priority: P1)

As a user creating a new app with a pipeline selected, I need the system to automatically create a Parent Issue in the new repository and start the agent pipeline so that work begins immediately without manual intervention.

**Why this priority**: The entire purpose of the agent pipeline is automation. Without the parent issue and sub-issue orchestration, users must manually create issues and trigger agents — defeating the purpose of the Solune platform.

**Independent Test**: Can be fully tested by creating a new-repo app with a pipeline selected and verifying that (a) a parent issue exists in the new repo's Issues tab, (b) the parent issue contains a tracking table, (c) sub-issues are created, and (d) the polling service is active within 60 seconds.

**Acceptance Scenarios**:

1. **Given** a user creates a new-repo app with a pipeline selected, **When** the repository and template files are committed successfully, **Then** a Parent Issue titled "Build {app display name}" is created in the repository with a tracking table in the body.
2. **Given** a parent issue is created successfully, **When** the pipeline has agent mappings, **Then** sub-issues are created for each agent stage and the polling service starts monitoring.
3. **Given** a user creates a new-repo app with a pipeline selected, **When** parent issue creation fails (e.g., GitHub API error), **Then** the app is still created successfully and a warning is added indicating that the pipeline could not be started.
4. **Given** a user creates a new-repo app without selecting a pipeline (pipeline = "None"), **When** app creation completes, **Then** no parent issue is created and no pipeline is started.
5. **Given** a user creates a same-repo or external-repo app with a pipeline selected, **When** the app is created, **Then** the parent issue is created in the target repository (same owner/repo for same-repo, external owner/repo for external-repo).

---

### User Story 3 - Pipeline Selection in Create Dialog (Priority: P2)

As a user creating a new app, I want to choose a pipeline from available presets in the creation dialog so that the appropriate agent workflow is associated with my app from the start.

**Why this priority**: While the backend already accepts a `pipeline_id`, the frontend provides no way to select one. Without this, users cannot take advantage of automated pipeline orchestration during app creation.

**Independent Test**: Can be fully tested by opening the Create App dialog, verifying the pipeline dropdown appears with available options, selecting a pipeline, submitting the form, and confirming the `pipeline_id` is sent in the API payload.

**Acceptance Scenarios**:

1. **Given** a user opens the Create App dialog, **When** the dialog renders, **Then** a pipeline selector dropdown is visible with available pipeline presets and a "None" default option.
2. **Given** a user selects a pipeline and submits the form, **When** the API request is sent, **Then** the `pipeline_id` field is included in the payload.
3. **Given** there are no pipeline presets available, **When** the dialog renders, **Then** the pipeline selector is disabled or hidden with a helpful message.

---

### User Story 4 - Complete Warning Display (Priority: P2)

As a user creating a new app, I need to see all warnings from the creation process (not just the first one) so that I can address every issue that occurred during setup.

**Why this priority**: Multiple things can go wrong during app creation (Azure secrets, template files, pipeline start). Showing only the first warning hides potentially critical information from users.

**Independent Test**: Can be fully tested by triggering a creation scenario where multiple warnings are generated (e.g., Azure secret failure + template file failure) and verifying all warnings appear as distinct toast notifications.

**Acceptance Scenarios**:

1. **Given** app creation produces multiple warnings, **When** the result is displayed to the user, **Then** all warnings are shown as individual toast notifications using a warning style (not error style).
2. **Given** app creation produces no warnings, **When** the result is displayed, **Then** only a success message appears.

---

### User Story 5 - Parent Issue Link in App Detail View (Priority: P2)

As a user viewing an app's details, I want to see a link to the Parent Issue and the associated pipeline name so that I can quickly navigate to the issue tracker and understand the app's automation status.

**Why this priority**: After creation, users need to monitor pipeline progress. A direct link to the parent issue and visibility of the pipeline association reduces friction.

**Independent Test**: Can be fully tested by navigating to an app detail page for an app that has a parent issue and verifying the link is clickable and the pipeline name is displayed.

**Acceptance Scenarios**:

1. **Given** an app has a `parent_issue_url`, **When** the app detail view renders, **Then** the parent issue URL is displayed as a clickable link alongside the GitHub repository and project links.
2. **Given** an app has an associated pipeline, **When** the app detail view renders, **Then** the pipeline name is displayed.
3. **Given** an existing app does not have a parent issue (created before this feature), **When** the app detail view renders, **Then** the view displays correctly without the parent issue section.

---

### User Story 6 - Pipeline Status Badge on App Card (Priority: P3)

As a user browsing the apps list, I want to see a small badge on each app card indicating whether the app has an active pipeline or parent issue so that I can quickly identify which apps have automation running.

**Why this priority**: Provides at-a-glance information without requiring users to open each app's detail view. Useful but not essential for core functionality.

**Independent Test**: Can be fully tested by viewing the apps list with a mix of apps (some with pipelines, some without) and verifying badges appear only on the correct cards.

**Acceptance Scenarios**:

1. **Given** an app has a parent issue and active pipeline, **When** the app card renders in the list, **Then** a small badge indicating pipeline/issue status is visible.
2. **Given** an app has no parent issue, **When** the app card renders, **Then** no pipeline badge appears.

---

### User Story 7 - Structured Creation Success Feedback (Priority: P3)

As a user who just created a new app, I want a brief summary toast showing the status of each creation step so that I understand exactly what succeeded and what needs attention.

**Why this priority**: Improves user confidence and transparency but is cosmetic compared to the core functional requirements.

**Independent Test**: Can be fully tested by creating a new-repo app and verifying the success toast includes a structured summary with checkmarks for completed steps and warning indicators for any issues.

**Acceptance Scenarios**:

1. **Given** a user creates a new-repo app with a pipeline and all steps succeed, **When** the creation completes, **Then** a success toast shows: ✓ Repository created / ✓ Template files committed / ✓ Pipeline started.
2. **Given** a user creates a new-repo app and some steps produce warnings, **When** the creation completes, **Then** the summary toast includes warning indicators (⚠) next to the affected steps with brief explanations.

---

### Edge Cases

- What happens when a user creates a new-repo app but the repository already exists with the same name under the chosen owner? The system should return a clear validation error before attempting creation.
- What happens when GitHub rate limits are hit during parent issue or sub-issue creation? The pipeline launch should fail gracefully with a warning, and the app should still be created successfully.
- What happens when the user deletes an app that has an associated parent issue? The parent issue should be closed (not deleted) in the GitHub repository to preserve the audit trail.
- What happens when the polling service fails to start after sub-issue creation? The app creation succeeds, a warning is added, and the user can manually trigger the pipeline later.
- What happens when an existing app (created before this feature) is displayed in the detail view or card list? It should display correctly with no parent issue link or pipeline badge — backward compatibility is maintained.
- What happens when the selected pipeline has no agent mappings defined? The parent issue is still created, but no sub-issues are generated and no polling is started. A warning is added.
- What happens when the user creates a same-repo type app and selects a pipeline? The parent issue is created in the same repository rather than in a new one. The pipeline uses the same-repo's owner/repo as the target.

## Requirements *(mandatory)*

### Functional Requirements

**Backend — Template File Resilience**

- **FR-001**: System MUST collect and return a list of file paths that failed to read during template file building, rather than silently skipping them.
- **FR-002**: System MUST include template file failure warnings in the `warnings[]` array on the App response when template files partially fail.
- **FR-003**: System MUST retry polling for the repository branch HEAD availability with exponential backoff for approximately 10 retries over a maximum wait of approximately 15 seconds, replacing the current 5 retries × 1 second.

**Backend — Parent Issue and Pipeline Integration**

- **FR-004**: System MUST store `parent_issue_number` (integer) and `parent_issue_url` (text) fields on the App record, persisted in the database.
- **FR-005**: System MUST load the pipeline configuration when a `pipeline_id` is provided during app creation.
- **FR-006**: System MUST create a Parent Issue in the target repository after template files are committed, when a pipeline is selected.
- **FR-007**: The Parent Issue title MUST follow the format "Build {app.display_name}".
- **FR-008**: The Parent Issue body MUST include the app description and an agent tracking table.
- **FR-009**: System MUST treat parent issue creation as best-effort — failure adds a warning but does not block app creation.
- **FR-010**: System MUST create sub-issues for each agent stage defined in the pipeline configuration after the parent issue is created.
- **FR-011**: System MUST start the polling service for the pipeline after sub-issues are created.
- **FR-012**: System MUST handle same-repo, external-repo, and new-repo types, creating the parent issue in the appropriate target repository.
- **FR-013**: System MUST close (not delete) the parent issue when the associated app is deleted.

**Frontend — Pipeline Selection**

- **FR-014**: The Create App dialog MUST include a pipeline selector dropdown populated with available pipeline presets from the current Solune project.
- **FR-015**: The pipeline selector MUST default to "None" (no pipeline selected).
- **FR-016**: The selected `pipeline_id` MUST be sent in the API creation payload.

**Frontend — Warning and Feedback Display**

- **FR-017**: The creation result handler MUST display all warnings from the `warnings[]` array as individual toast notifications.
- **FR-018**: Warnings MUST be displayed using a warning toast style (not error style).
- **FR-019**: After successful creation, a structured summary toast MUST be shown indicating the status of each creation step (repository, template files, pipeline).

**Frontend — App Display Enhancements**

- **FR-020**: The App detail view MUST display the `parent_issue_url` as a clickable link when present.
- **FR-021**: The App detail view MUST display the associated pipeline name when present.
- **FR-022**: The App card MUST show a small badge when the app has an active pipeline or parent issue.
- **FR-023**: Apps created before this feature (without parent issue data) MUST display correctly without errors in both list and detail views.

**Data Migration**

- **FR-024**: A database migration MUST add `parent_issue_number` (INTEGER) and `parent_issue_url` (TEXT) nullable columns to the `apps` table.

### Key Entities *(include if feature involves data)*

- **App**: Represents a Solune-managed application. Gains two new fields: `parent_issue_number` (the GitHub issue number associated with the app's build pipeline) and `parent_issue_url` (the full URL to the parent issue on GitHub). Both are optional and null for apps without a pipeline.
- **Parent Issue**: A GitHub Issue created in the target repository that serves as the root tracking item for the agent pipeline. Contains a tracking table and links back to the Solune dashboard. Child sub-issues are created beneath it for each agent stage.
- **Pipeline Configuration**: An existing entity that defines the agent stages and mappings for automated workflows. Referenced by `pipeline_id` during app creation to determine which agents to assign.
- **Template Files**: Scaffold files (`.github/agents/`, `.github/prompts/`, `.github/workflows/`, `.specify/`, `.gitignore`) copied from the Solune source into new repositories. Failures during copying are now tracked and surfaced as warnings.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: When creating a new-repo app, all expected scaffold directories (`.github/agents/`, `.github/prompts/`, `.github/workflows/`, `.specify/`, `.gitignore`) are present in the created repository within 30 seconds of creation.
- **SC-002**: When template files partially fail, 100% of failures are surfaced to the user as warnings — zero silent failures.
- **SC-003**: The branch HEAD availability check tolerates GitHub delays of up to 15 seconds without failing, a 3× improvement over the current 5-second maximum.
- **SC-004**: When a pipeline is selected during app creation, a Parent Issue with tracking table and sub-issues exists in the target repository within 60 seconds of app creation.
- **SC-005**: Parent issue creation failures do not block app creation — the app is still created successfully with a warning in 100% of failure cases.
- **SC-006**: Users can see and select a pipeline from the Create App dialog, with the selected value correctly sent to the backend.
- **SC-007**: All warnings from app creation are displayed to the user, not just the first one.
- **SC-008**: Apps created before this feature continue to display correctly in both list and detail views with no visual errors or missing data.
- **SC-009**: When an app with a parent issue is deleted, the parent issue is closed (not deleted) within 10 seconds.
- **SC-010**: The first pipeline agent is assigned within 60 seconds of app creation when a pipeline is selected and sub-issues are created.
