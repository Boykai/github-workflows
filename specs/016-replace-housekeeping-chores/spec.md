# Feature Specification: Replace Housekeeping with Chores

**Feature Branch**: `016-replace-housekeeping-chores`  
**Created**: 2026-03-02  
**Status**: Draft  
**Input**: User description: "Replace Housekeeping with Chores: Recurring scheduled maintenance tasks backed by GitHub Issue Templates with time-based and count-based triggers, agent pipeline integration, and interactive chat-driven template creation"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - View Chores Panel on Project Board (Priority: P1)

As a project manager, I want to see a "Chores" panel on the right side of my project board so I can monitor all recurring maintenance tasks at a glance alongside my project work.

**Why this priority**: The Chores panel is the foundational UI surface. Without it, no other chore functionality is accessible. It replaces the existing Housekeeping feature and must be visible for any subsequent interactions.

**Independent Test**: Can be fully tested by navigating to the project board page and verifying the Chores panel renders to the right of the board columns with correct layout and empty state messaging.

**Acceptance Scenarios**:

1. **Given** a user is on the project board page, **When** the page loads, **Then** a "Chores" panel is displayed to the right of the project board columns.
2. **Given** a project has no chores configured, **When** the Chores panel loads, **Then** an empty state message is shown with an "Add Chore" button.
3. **Given** a project has existing chores, **When** the Chores panel loads, **Then** each chore displays: name, schedule type & value, last triggered date, until next trigger, link to GitHub Issue Template, and a clickable Active/Paused status toggle.
4. **Given** the existing Housekeeping feature exists in the codebase, **When** this feature is deployed, **Then** all Housekeeping code, UI, routes, database tables, and references are fully removed.

---

### User Story 2 - Add a Chore with Rich Input (Priority: P1)

As a project manager, I want to create a new chore by providing detailed template content so that the system creates a GitHub Issue Template, commits it via PR, and tracks the new chore for recurring execution.

**Why this priority**: Creating chores is the core write operation of the feature. Without it, the Chores panel has no content. Rich input (detailed descriptions) is the primary creation path.

**Independent Test**: Can be fully tested by clicking "Add Chore," entering detailed markdown content (like the Bug Bash example), confirming creation, and verifying: a GitHub branch is created, the template file is committed, a PR is opened, a tracking GitHub Issue is created with "In review" status, and the chore appears immediately in the Chores panel as active.

**Acceptance Scenarios**:

1. **Given** a user clicks "Add Chore," **When** a pop-up modal appears, **Then** it contains a text input area for describing the chore or providing template content.
2. **Given** the user enters detailed, rich markdown content (multiple sections, headings, structured requirements), **When** the user submits, **Then** the system uses the content as the core body of a Markdown GitHub Issue Template (`.md` file with YAML front matter in `.github/ISSUE_TEMPLATE/`).
3. **Given** the user's rich input is missing template metadata (name, about, title, labels, assignees), **When** the template is generated, **Then** the system automatically populates the YAML front matter with reasonable defaults derived from the content.
4. **Given** the template content is finalized, **When** the system processes the creation, **Then** a new branch is created from `main`, the template `.md` file is committed to that branch in `.github/ISSUE_TEMPLATE/`, a PR is opened targeting `main`, a GitHub Issue is created to track/review the template, and the issue is placed in "In review" status on the project board.
5. **Given** the creation flow completes, **When** the chore appears in the Chores panel, **Then** it is immediately active (does not wait for the PR to be merged).

---

### User Story 3 - Add a Chore with Sparse Input via Chat Agent (Priority: P2)

As a project manager, I want to create a chore with minimal input (e.g., "create refactor chore") so that the app's chat agent helps me collaboratively build out a robust GitHub Issue Template through interactive conversation.

**Why this priority**: Supports users who have a general idea but need AI assistance to flesh it out. This is a secondary creation path that enhances usability but is not required for the core chore lifecycle.

**Independent Test**: Can be fully tested by clicking "Add Chore," entering sparse text (e.g., "create refactor chore"), verifying the interactive chat agent opens, answering follow-up questions, confirming the generated template, and verifying the same PR + Issue + chore creation flow as rich input.

**Acceptance Scenarios**:

1. **Given** a user enters sparse input (short phrase, no structured markdown), **When** the system detects sparse input, **Then** it opens an interactive chat conversation using the app's existing chat agent.
2. **Given** the chat agent is engaged, **When** the agent asks follow-up questions, **Then** the user can answer iteratively until a complete, robust GitHub Issue Template is collaboratively built.
3. **Given** the user confirms the final template from the chat conversation, **When** submission occurs, **Then** the same creation flow executes (branch, commit, PR, tracking issue, chore added to panel) as with rich input.

---

### User Story 4 - Configure Chore Schedule (Priority: P1)

As a project manager, I want to configure how often a chore triggers — either by time interval (days) or by number of new parent issues created — so that maintenance tasks recur on a cadence appropriate to my project.

**Why this priority**: Scheduling is what makes chores recurring. Without a configured schedule, chores never trigger, making the feature non-functional beyond template creation.

**Independent Test**: Can be fully tested by creating a chore, then from the Chores panel configuring either a time-based schedule (e.g., every 14 days) or a count-based schedule (e.g., every 5 parent issues), and verifying the schedule information displays correctly.

**Acceptance Scenarios**:

1. **Given** a chore exists in the Chores panel without a schedule, **When** the user configures the schedule from the panel, **Then** they can choose between "time-based (days)" or "count-based (parent issues created)" and set a numeric value.
2. **Given** a time-based schedule of 14 days is configured, **When** the Chores panel displays the chore, **Then** "Until next trigger" shows remaining time (e.g., "3 days, 4 hours").
3. **Given** a count-based schedule of 5 parent issues is configured, **When** the Chores panel displays the chore, **Then** "Until next trigger" shows remaining count (e.g., "2 parent issues").
4. **Given** a count-based schedule, **When** counting parent issues created since last trigger, **Then** issues created by Chore triggers are excluded from the count AND GitHub Sub Issues are excluded from the count — only non-chore Parent Issues are counted.

---

### User Story 5 - Chore Triggers and Executes Agent Pipeline (Priority: P1)

As a project manager, I want chores to automatically create a GitHub Issue from the template and execute the agent pipeline when the schedule condition is met, so that recurring maintenance work is performed by the configured AI agents without manual intervention.

**Why this priority**: This is the core automation value of the Chores feature — automatic issue creation + agent execution. Without it, chores are merely a list with no automated action.

**Independent Test**: Can be fully tested by configuring a chore with a short schedule, waiting for (or manually triggering) the condition to be met, and verifying: a new GitHub Parent Issue is created from the template, corresponding Sub Issues are created per the agent pipeline configuration, sub-issues are assigned to the configured agents, and the chore's cycle resets.

**Acceptance Scenarios**:

1. **Given** an active chore with a time-based schedule of N days, **When** N days have elapsed since last trigger (or since creation if never triggered), **Then** the system creates a new GitHub Issue using the chore's template content.
2. **Given** an active chore with a count-based schedule of N parent issues, **When** N non-chore, non-sub-issue Parent Issues have been created since last trigger, **Then** the system creates a new GitHub Issue using the chore's template content.
3. **Given** a chore triggers, **When** the GitHub Issue is created, **Then** the system reads the current agent pipeline configuration for the project, creates the issue as a Parent Issue, creates corresponding Sub Issues per the pipeline definition, and assigns sub-issues to the configured agents.
4. **Given** a chore has triggered, **When** the triggered issue and sub-issues are created, **Then** the chore's "last triggered" timestamp/count resets and a new cycle begins.
5. **Given** a chore has an open GitHub Issue from a previous trigger, **When** the schedule condition is met again, **Then** the system skips triggering (only 1 instance of a given chore type may be open at a time).

---

### User Story 6 - Toggle Chore Active / Paused (Priority: P2)

As a project manager, I want to pause and resume chores by clicking the status in the Chores panel so that I can temporarily suspend recurring tasks without removing them.

**Why this priority**: Provides user control over chore execution without destructive removal. Important for flexibility but not part of the core creation-trigger lifecycle.

**Independent Test**: Can be fully tested by clicking the Active/Paused status toggle on a chore in the panel and verifying the status updates, and that paused chores do not trigger even when their schedule condition is met.

**Acceptance Scenarios**:

1. **Given** a chore is Active, **When** the user clicks the status toggle, **Then** the status changes to Paused and the chore no longer triggers.
2. **Given** a chore is Paused, **When** the user clicks the status toggle, **Then** the status changes to Active and the chore resumes its schedule from the current point.

---

### User Story 7 - Remove a Chore (Priority: P2)

As a project manager, I want to remove a chore from the Chores panel so that it no longer appears or triggers, while preserving the GitHub Issue Template file in the repository.

**Why this priority**: Removing chores is essential for list management, but secondary to creation and triggering functionality.

**Independent Test**: Can be fully tested by selecting a chore and clicking "Remove Chore," verifying it disappears from the panel, any open associated GitHub Issue is closed/cancelled, and the template file remains in the repository.

**Acceptance Scenarios**:

1. **Given** a chore exists in the Chores panel, **When** the user removes it, **Then** the chore is deleted from the panel and no longer tracked.
2. **Given** a chore has a currently open GitHub Issue from a previous trigger, **When** the user removes the chore, **Then** that open GitHub Issue is closed/cancelled.
3. **Given** a chore is removed, **When** checking the repository, **Then** the GitHub Issue Template `.md` file remains in `.github/ISSUE_TEMPLATE/` (it is NOT deleted).

---

### User Story 8 - Manual Chore Trigger (Priority: P3)

As a project manager, I want to manually trigger a chore for testing purposes so that I can verify the end-to-end flow (issue creation + agent pipeline execution) without waiting for the schedule condition.

**Why this priority**: Useful for testing and debugging but not required for core chore functionality.

**Independent Test**: Can be fully tested by invoking the manual trigger action on a chore and verifying the same outcome as an automatic trigger (issue created, pipeline executed, cycle reset).

**Acceptance Scenarios**:

1. **Given** an active chore with no currently open triggered issue, **When** the user manually triggers it, **Then** a new GitHub Issue is created from the template and the agent pipeline executes, same as an automatic trigger.
2. **Given** an active chore with a currently open triggered issue, **When** the user attempts a manual trigger, **Then** the system prevents triggering and notifies the user that a previous instance is still open.

---

### Edge Cases

- What happens when a chore's template file is deleted from the repository but the chore still exists in the panel? The system should display a warning indicator on the chore and prevent triggering until the template is restored or the chore is removed.
- What happens when the agent pipeline configuration is not set for the project at trigger time? The system should create the Parent Issue but log a warning that sub-issues could not be created due to missing pipeline configuration, and surface this warning in the Chores panel.
- What happens when the GitHub API is unavailable during a trigger attempt? The system should retry with backoff and surface the failure state on the chore in the panel (e.g., "Trigger failed — retrying").
- What happens when a user tries to add a chore with a name that already exists? The system should prevent duplicate chore names within the same project and notify the user.
- What happens when the chore's open issue is closed externally (not by the chore system)? The system should detect this and clear the current_issue_number so the chore can trigger again on the next cycle.
- What happens when a count-based chore has no parent issues created since last trigger? "Until next trigger" should display the full threshold value (e.g., "5 parent issues").

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST remove all existing Housekeeping feature code, including backend services, API routes, models, database tables, frontend components, and all references throughout the codebase.
- **FR-002**: System MUST display a "Chores" panel to the right of the project board columns on the project board page.
- **FR-003**: Each chore in the panel MUST display: name, schedule type & value, last triggered date, until next trigger, link to GitHub Issue Template, and a clickable Active/Paused status toggle.
- **FR-004**: System MUST provide an "Add Chore" button that opens a pop-up modal with a text input area for the user to describe the chore or provide template content.
- **FR-005**: System MUST detect sparse user input and open an interactive chat conversation using the app's existing chat agent to collaboratively refine a GitHub Issue Template.
- **FR-006**: System MUST detect rich user input and use it directly as the GitHub Issue Template core content, automatically populating missing YAML front matter metadata (name, about, title, labels, assignees).
- **FR-007**: System MUST create GitHub Issue Templates as Markdown files (`.md`) with YAML front matter in `.github/ISSUE_TEMPLATE/`, per GitHub documentation standards.
- **FR-008**: After template content is finalized, system MUST create a new branch from `main`, commit the template file, open a PR targeting `main`, create a tracking GitHub Issue in "In review" status, and activate the chore immediately in the panel.
- **FR-009**: System MUST support two schedule types: time-based (configurable number of days) and count-based (configurable number of parent issues created since last trigger).
- **FR-010**: For count-based scheduling, system MUST exclude issues created by Chore triggers and exclude GitHub Sub Issues from the parent issue count.
- **FR-011**: System MUST allow schedule configuration from the Chores panel as a separate step after chore creation.
- **FR-012**: When a chore's schedule condition is met, system MUST check that no currently open GitHub Issue exists from a previous trigger of the same chore before triggering (1 open instance per chore maximum).
- **FR-013**: When a chore triggers, system MUST create a new GitHub Issue using the template content, read the current agent pipeline configuration, create the issue as a Parent Issue, create corresponding Sub Issues per the pipeline definition, and assign sub-issues to the configured agents.
- **FR-014**: After triggering, system MUST reset the chore's last triggered timestamp/count to begin a new cycle.
- **FR-015**: Users MUST be able to toggle a chore between Active and Paused by clicking the status in the panel. Paused chores MUST NOT trigger.
- **FR-016**: Users MUST be able to remove a chore from the panel. Removing a chore MUST close/cancel any currently open associated GitHub Issue. Removing a chore MUST NOT delete the template file from the repository.
- **FR-017**: System MUST provide a manual trigger capability for testing purposes, subject to the same 1-open-instance constraint.
- **FR-018**: System MUST run a background scheduler service that periodically checks all active chores across all projects and triggers those whose schedule conditions are met.

### Key Entities

- **Chore**: A recurring maintenance task definition. Key attributes: name, associated project, template file path, cached template content, schedule type (time or count), schedule value, status (active/paused), last triggered timestamp, last triggered parent issue count, current open issue number. Belongs to a Project.
- **GitHub Issue Template**: A Markdown file with YAML front matter stored in `.github/ISSUE_TEMPLATE/` in the repository. Created via branch + PR workflow. Used as the body content when a chore triggers. Not owned by the app database — stored in GitHub.
- **Triggered Issue**: A GitHub Parent Issue created from a chore's template when the schedule condition is met. Has corresponding Sub Issues created per the agent pipeline configuration. Only one may be open per chore at any time.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can create a new chore from detailed input and see it appear in the Chores panel within 30 seconds of submission.
- **SC-002**: Users can create a chore from sparse input via interactive chat agent conversation and finalize a template within 5 minutes.
- **SC-003**: Time-based chores trigger within 5 minutes of their scheduled time, creating a GitHub Issue and executing the agent pipeline without manual intervention.
- **SC-004**: Count-based chores trigger within 5 minutes of the parent issue count threshold being reached, with accurate exclusion of chore-generated issues and sub-issues.
- **SC-005**: The system correctly enforces the 1-open-instance-per-chore constraint, never creating duplicate triggered issues for the same chore.
- **SC-006**: All existing Housekeeping code is fully removed with zero references remaining in the codebase, and all existing tests pass after removal.
- **SC-007**: The Chores panel accurately displays "until next trigger" information — remaining time for time-based chores and remaining parent issue count for count-based chores — refreshing on page load.
- **SC-008**: 100% of chore CRUD operations (add, remove, toggle status, configure schedule) complete successfully and reflect immediately in the Chores panel UI.

## Assumptions

- The app's existing chat agent infrastructure supports interactive multi-turn conversations and can be extended to generate GitHub Issue Template content.
- The app's existing GitHub client utilities support creating branches, committing files, opening PRs, creating issues, and updating project board item status.
- The agent pipeline configuration for a project is accessible at trigger time and provides a definition for creating sub-issues and assigning them to agents.
- The background scheduler service can run periodic checks (e.g., every few minutes) without significant performance impact.
- GitHub Issue Templates use the standard Markdown format with YAML front matter (`name`, `about`, `title`, `labels`, `assignees`) as documented at https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/configuring-issue-templates-for-your-repository.
- "Sparse input" is defined as input that is short (e.g., fewer than ~50 words) and lacks structured markdown formatting (no headings, lists, or multiple sections).
- When a chore's associated open issue is closed externally (outside of the chore remove flow), the system detects this and clears the tracking reference so the next trigger cycle can proceed.
