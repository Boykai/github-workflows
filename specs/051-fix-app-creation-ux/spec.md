# Feature Specification: Debug & Fix Apps Page — New App Creation UX

**Feature Branch**: `051-fix-app-creation-ux`  
**Created**: 2026-03-17  
**Status**: Draft  
**Input**: User description: "The 'Create New App' flow creates a GitHub repo and commits template files, but has three critical gaps: (1) template files silently fail to copy, (2) no Parent Issue is created to kickstart the Agent Pipeline, and (3) the frontend lacks pipeline selection and post-creation feedback."

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Reliable Template File Copying (Priority: P1)

As a user creating a new app, I want all template files to be reliably copied into my new repository so that the agent pipeline has the configuration files it needs to operate from day one.

Currently, when a file fails to read (e.g., due to encoding issues), it is silently skipped. The user has no idea that critical configuration files are missing until agents fail later. This story ensures every file copy attempt is tracked, failures are collected, and the user is informed of any issues.

**Why this priority**: Without reliable template files, the entire downstream agent pipeline is broken. This is the foundation — nothing else works correctly if the repository is missing its configuration files.

**Independent Test**: Can be fully tested by creating a new app and verifying that all expected template directories and files appear in the new repository, and that any failures are surfaced as warnings to the user.

**Acceptance Scenarios**:

1. **Given** a user creates a new app, **When** all template files copy successfully, **Then** the new repository contains `.github/agents/`, `.github/prompts/`, `.github/workflows/`, `.specify/`, and `.gitignore` with correct content.
2. **Given** a user creates a new app, **When** one or more template files fail to copy (e.g., encoding error), **Then** the app is still created, the successfully copied files are committed, and the user sees a warning listing which files failed.
3. **Given** a user creates a new app, **When** template file copying partially fails, **Then** the failure does not block app creation — the app record is saved and the user can still access it.
4. **Given** a user creates a new app, **When** the repository branch is not yet ready on GitHub (propagation delay), **Then** the system retries with increasing wait times for up to 15 seconds before giving up, rather than failing after 5 seconds.

---

### User Story 2 — Automatic Parent Issue & Pipeline Launch (Priority: P2)

As a user creating a new app with a pipeline selected, I want the system to automatically create a Parent Issue in my repository and start the agent pipeline so that my project begins executing immediately without manual setup.

Today, the `pipeline_id` field exists on app creation but is stored without being used. No Parent Issue is created, no sub-issues are spawned, and no polling is started. This story closes that gap by wiring up the existing building blocks.

**Why this priority**: The Parent Issue and pipeline launch delivers the highest user value, but it depends on reliable template files (Story 1) being in place first. Template files provide the agent configuration that the pipeline needs to execute. This story is P2 because it cannot function correctly without P1, even though it represents the primary reason users create apps through this flow.

**Independent Test**: Can be fully tested by creating a new app with a pipeline selected and verifying that a Parent Issue appears in the repository's Issues tab, sub-issues are created according to the pipeline configuration, and the polling service becomes active.

**Acceptance Scenarios**:

1. **Given** a user creates a new app with a pipeline selected, **When** the repository and template files are committed, **Then** a Parent Issue titled "Build {app display name}" is created in the repository with a tracking table in the body.
2. **Given** a Parent Issue is created, **When** the pipeline configuration defines agent tasks, **Then** sub-issues are created for each agent task and linked to the Parent Issue.
3. **Given** sub-issues are created, **When** the pipeline state is initialized, **Then** the polling service starts monitoring for agent assignments within 60 seconds.
4. **Given** a user creates a new app with a pipeline selected, **When** the Parent Issue creation fails (e.g., GitHub API error), **Then** the app is still created successfully, a warning is shown to the user, and the app record stores no parent issue reference.
5. **Given** a user creates a new app without selecting a pipeline, **When** the app is created, **Then** no Parent Issue is created and no pipeline is started.
6. **Given** an app is created with a Parent Issue, **When** the app is later deleted, **Then** the Parent Issue is closed (not deleted) in the repository.

---

### User Story 3 — Pipeline Selection in Create Dialog (Priority: P3)

As a user creating a new app, I want to select a pipeline from a dropdown in the create dialog so that I can choose which agent workflow to run on my new project.

Currently, the create dialog has no pipeline selector. The `pipeline_id` field exists in the data model but there is no UI for users to choose a pipeline. This story adds a dropdown populated with available pipelines from the current project.

**Why this priority**: Pipeline selection is the user-facing entry point for Story 2. Without it, users cannot trigger automatic pipeline launch even after the backend supports it.

**Independent Test**: Can be fully tested by opening the Create App dialog, verifying a pipeline dropdown appears with available options, selecting a pipeline, submitting the form, and confirming the `pipeline_id` is included in the creation request.

**Acceptance Scenarios**:

1. **Given** a user opens the Create App dialog, **When** the dialog loads, **Then** a pipeline selector dropdown is visible with available pipelines from the current project.
2. **Given** the pipeline dropdown is shown, **When** no pipeline is selected, **Then** the default value is "None" and app creation proceeds without a pipeline.
3. **Given** the user selects a pipeline and submits the form, **When** the creation request is sent, **Then** the `pipeline_id` is included in the payload.

---

### User Story 4 — Complete Warning Display (Priority: P3)

As a user creating a new app, I want to see all warnings from the creation process — not just the first one — so that I have a complete picture of any issues that occurred.

Currently, only the first warning (`warnings[0]`) is displayed, and it uses an error style rather than a warning style. Users may miss important information about partial failures.

**Why this priority**: Correct warning display ensures users are fully informed about the state of their newly created app, but the app creation still works without this improvement.

**Independent Test**: Can be fully tested by creating an app that produces multiple warnings (e.g., template file failure + secret configuration issue) and verifying that all warnings appear in the UI with appropriate warning styling.

**Acceptance Scenarios**:

1. **Given** app creation produces multiple warnings, **When** the creation completes, **Then** all warnings are displayed to the user (not just the first one).
2. **Given** warnings are displayed, **When** the user views them, **Then** they use a warning visual style (not error style) to correctly convey severity.

---

### User Story 5 — Parent Issue & Pipeline Visibility (Priority: P4)

As a user viewing an existing app, I want to see the Parent Issue link and pipeline status so that I can quickly navigate to the project's issue tracker and understand if an agent pipeline is active.

**Why this priority**: This is a visibility/convenience improvement. The app works without it, but it improves the user's ability to monitor and manage their apps.

**Independent Test**: Can be fully tested by viewing an app that has a Parent Issue and verifying the link is displayed and clickable, and by viewing an app without a Parent Issue and verifying the UI handles the absence gracefully.

**Acceptance Scenarios**:

1. **Given** an app has a Parent Issue, **When** the user views the app detail page, **Then** a clickable link to the Parent Issue is displayed along with the pipeline name.
2. **Given** an app has an active pipeline, **When** the user views the app list, **Then** a small badge or indicator shows the pipeline status on the app card.
3. **Given** an app was created before this feature (no Parent Issue), **When** the user views the app, **Then** the detail view and list view display correctly without errors — no broken links or missing data.

---

### User Story 6 — Improved Creation Success Feedback (Priority: P4)

As a user who just created a new app, I want to see a summary of what was accomplished so that I know exactly what succeeded and what needs attention.

**Why this priority**: This is a UX polish that provides better feedback but does not affect functionality.

**Independent Test**: Can be fully tested by creating a new app and verifying that a structured summary toast appears showing the status of each creation step.

**Acceptance Scenarios**:

1. **Given** a user successfully creates a new app with all steps completing, **When** creation finishes, **Then** a summary toast displays: ✓ Repository created / ✓ Template files committed / ✓ Pipeline started.
2. **Given** a user creates an app with some warnings, **When** creation finishes, **Then** the summary toast includes ⚠ indicators for steps that had warnings.
3. **Given** a user creates an app without a pipeline, **When** creation finishes, **Then** the summary toast omits the pipeline step rather than showing it as skipped.

---

### Edge Cases

- What happens when the user creates an app but GitHub experiences high latency? The branch-readiness check must retry with exponential backoff (up to ~15 seconds) before reporting failure.
- What happens when template files contain binary or non-UTF-8 content? Failures must be caught, logged, and reported as warnings without crashing the creation flow.
- What happens when the pipeline configuration references agents or tasks that don't exist? The Parent Issue should still be created; invalid task references should generate warnings.
- What happens when two users create apps simultaneously with the same name? The existing name-uniqueness validation should prevent conflicts.
- What happens when an app with a Parent Issue is deleted while pipeline polling is active? Polling should stop gracefully, and the Parent Issue should be closed.
- What happens when the GitHub API rate limit is hit during Parent Issue or sub-issue creation? The operation should fail gracefully with a warning, not crash the creation flow.
- What happens when a user views an app created before this feature existed (no `parent_issue_number` or `parent_issue_url`)? The UI must handle null/missing values without errors.

## Requirements *(mandatory)*

### Functional Requirements

**Template File Reliability**

- **FR-001**: System MUST collect and report all file-copy failures during template file copying rather than silently skipping them.
- **FR-002**: System MUST return a warnings list from the template file building process so callers can surface issues to users.
- **FR-003**: System MUST retry branch-readiness checks with exponential backoff, waiting up to approximately 15 seconds before reporting failure (increased from the current 5-second maximum).
- **FR-004**: System MUST add template file warnings to the `warnings[]` array on the App response object.

**Parent Issue & Pipeline**

- **FR-005**: System MUST store `parent_issue_number` and `parent_issue_url` as part of the App record, persisted in the database.
- **FR-006**: System MUST load and use the pipeline configuration when a `pipeline_id` is provided during app creation.
- **FR-007**: System MUST create a Parent Issue in the new repository after template files are committed, when a pipeline is selected. The issue title MUST follow the format "Build {app display name}".
- **FR-008**: System MUST include a tracking table in the Parent Issue body (matching the existing tracking table pattern used elsewhere in the platform).
- **FR-009**: System MUST treat Parent Issue creation as best-effort — failures add a warning but do not block app creation.
- **FR-010**: System MUST create sub-issues for each agent task defined in the pipeline configuration, linked to the Parent Issue.
- **FR-011**: System MUST initialize polling after sub-issues are created so the agent pipeline begins executing.
- **FR-012**: System MUST close (not delete) the Parent Issue when an app is deleted.
- **FR-013**: System MUST skip Parent Issue creation entirely when no pipeline is selected.

**Frontend — Creation Dialog**

- **FR-014**: System MUST display a pipeline selector dropdown in the Create App dialog, populated with available pipelines from the current project.
- **FR-015**: System MUST default the pipeline selector to "None" (no pipeline).
- **FR-016**: System MUST include the selected `pipeline_id` in the app creation request payload.

**Frontend — Warning Display**

- **FR-017**: System MUST display all warnings from app creation, not just the first one.
- **FR-018**: System MUST use a warning visual style (not error style) for creation warnings.

**Frontend — Visibility & Feedback**

- **FR-019**: System MUST display the Parent Issue as a clickable link on the app detail view when one exists.
- **FR-020**: System MUST display a pipeline indicator badge on app cards when the app has an active pipeline.
- **FR-021**: System MUST show a structured creation summary after app creation, indicating the status of each step (repository, template files, pipeline).
- **FR-022**: System MUST handle apps without parent issues gracefully — no broken links, no errors, no missing-data indicators in list or detail views.

**Cross-Cutting**

- **FR-023**: System MUST support both `same-repo` and `external-repo` app types for Parent Issue creation, targeting the appropriate owner/repo. A `same-repo` app uses the current Solune project's repository, while an `external-repo` app creates a new, separate GitHub repository. The Parent Issue is created in whichever repository the app targets.

### Key Entities

- **App**: The central record representing a created application. Extended with `parent_issue_number` (integer, nullable) and `parent_issue_url` (string, nullable) to track the associated GitHub Parent Issue. Also stores `pipeline_id` (already exists) for the selected pipeline configuration.
- **Parent Issue**: A GitHub Issue created in the app's repository that serves as the top-level tracking item for the agent pipeline. Contains a tracking table in the body and has sub-issues linked to it.
- **Pipeline Configuration**: An existing entity that defines the agent workflow — which agents run, in what order, and what tasks they perform. Referenced by `pipeline_id` on the App record.
- **Sub-Issue**: GitHub Issues created under the Parent Issue, one per agent task defined in the pipeline configuration. These drive the agent polling and execution loop.

### Assumptions

- Pipeline presets are sourced from the current Solune project (not from the newly created repository, which won't have any presets yet).
- The Parent Issue body includes the app description, a link back to the Solune dashboard, and the agent tracking table — matching the existing `recommendations/confirm` pattern.
- The `.specify/memory/` directory is excluded from template files because it contains project-specific learned context that should not be pre-populated in new repositories. New apps should build their own memory through agent interactions.
- Closing the Parent Issue on app deletion is included in this feature scope (not deferred).
- The existing name-uniqueness validation for apps prevents duplicate repository creation conflicts.
- Standard session-based authentication is used for all operations (no special auth changes needed).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of template files are either successfully copied or explicitly reported as warnings — zero silent failures.
- **SC-002**: New apps created with a pipeline selected have a Parent Issue with tracking table and sub-issues within 60 seconds of creation.
- **SC-003**: Users can complete the full app creation flow (including pipeline selection) in under 2 minutes.
- **SC-004**: All creation warnings are visible to the user — no information is hidden or truncated.
- **SC-005**: Apps created before this feature continue to display correctly in list and detail views with no errors.
- **SC-006**: Branch-readiness retries tolerate up to 15 seconds of GitHub propagation delay without failing.
- **SC-007**: Parent Issue creation failure does not increase the app creation error rate — apps are still created successfully with a warning.
- **SC-008**: 100% of app detail views for apps with Parent Issues display a working, clickable link to the issue.
