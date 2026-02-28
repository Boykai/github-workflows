# Feature Specification: Housekeeping Issue Templates with Configurable Triggers

**Feature Branch**: `014-housekeeping-triggers`  
**Created**: 2026-02-28  
**Status**: Draft  
**Input**: User description: "Add Housekeeping Issue Templates with Configurable Triggers for Recurring Project Maintenance"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Create and Configure a Housekeeping Task (Priority: P1)

As a project maintainer, I want to create a named housekeeping task that references a stored GitHub Issue template and is configured with a trigger (time-based or count-based) so that recurring maintenance work is defined once and fires automatically.

**Why this priority**: This is the foundational capability — without the ability to define housekeeping tasks, no automated maintenance can occur. Every other story depends on task definitions existing.

**Independent Test**: Can be fully tested by creating a housekeeping task with a name, description, template reference, and trigger configuration, then verifying it persists and displays correctly in the task list.

**Acceptance Scenarios**:

1. **Given** a project with at least one stored issue template, **When** a maintainer creates a new housekeeping task with a name, description, template reference, and a time-based trigger (e.g., weekly), **Then** the task is saved and appears in the housekeeping task list with all configured values.
2. **Given** a project with at least one stored issue template, **When** a maintainer creates a new housekeeping task with a count-based trigger (e.g., every 10 parent issues), **Then** the task is saved with the count-based trigger configuration and the current issue count is recorded as the baseline.
3. **Given** an existing housekeeping task, **When** a maintainer edits its name, description, trigger type, or trigger value, **Then** the updated configuration is saved and reflected immediately.
4. **Given** an existing housekeeping task, **When** a maintainer deletes it, **Then** the task and its configuration are removed, and its history is no longer displayed.
5. **Given** a maintainer attempting to create a task, **When** the referenced issue template does not exist or the sub-issue configuration is invalid, **Then** the system displays an inline validation error and prevents saving.

---

### User Story 2 - Automatic Trigger Execution (Priority: P1)

As a project maintainer, I want housekeeping tasks to fire automatically based on their configured trigger — either on a time schedule or after a set number of new parent issues — so that maintenance happens without manual intervention.

**Why this priority**: Automation is the core value proposition. Without triggers firing, the system is just a task list with no recurring behavior.

**Independent Test**: Can be tested by configuring a time-based task with a short interval and verifying a GitHub Issue is created on schedule, or by configuring a count-based task and creating the required number of parent issues to trigger it.

**Acceptance Scenarios**:

1. **Given** an enabled housekeeping task with a time-based trigger set to a daily schedule, **When** the scheduled time arrives, **Then** the system creates a parent GitHub Issue from the stored template and generates sub issues based on the agent pipeline configuration.
2. **Given** an enabled housekeeping task with a count-based trigger set to fire every 5 parent issues, **When** the 5th new parent issue is created since the last trigger, **Then** the system creates a parent GitHub Issue from the stored template and generates sub issues.
3. **Given** a housekeeping task that was just triggered, **When** a trigger condition is met again within the minimum cooldown window, **Then** the system does not create a duplicate issue (idempotency guard).
4. **Given** a housekeeping task with no custom sub-issue mapping defined, **When** the task fires, **Then** the system defaults to the Spec Kit agent pipeline reconfiguration for generating sub issues.
5. **Given** a disabled housekeeping task, **When** its trigger condition is met, **Then** no issue is created and no history entry is logged.

---

### User Story 3 - Built-in Starter Templates (Priority: P2)

As a new project maintainer, I want the system to ship with pre-configured housekeeping task templates for common maintenance activities (Security and Privacy Review, Test Coverage Refresh, Bug Bash) so that I can start using recurring maintenance immediately without manual setup.

**Why this priority**: Starter templates reduce time-to-value and provide best-practice examples. However, the system is functional without them if maintainers create their own tasks.

**Independent Test**: Can be tested by verifying that a fresh project installation includes three pre-configured templates and that each can be used to create a housekeeping task without modification.

**Acceptance Scenarios**:

1. **Given** a fresh project setup, **When** a maintainer views the available housekeeping templates, **Then** at least three built-in templates are present: "Security and Privacy Review", "Test Coverage Refresh", and "Bug Bash".
2. **Given** the "Security and Privacy Review" template, **When** it is used to create a housekeeping task, **Then** the generated parent issue references the codebase context and the sub issues align to the agent pipeline for security and privacy review.
3. **Given** the "Test Coverage Refresh" template, **When** it is used to create a housekeeping task, **Then** the generated parent issue targets quality testing improvements and bug resolution.
4. **Given** the "Bug Bash" template, **When** it is used to create a housekeeping task, **Then** the generated parent issue targets finding and resolving bugs across the codebase.
5. **Given** a built-in template, **When** a maintainer wishes to customize it, **Then** they can duplicate it and modify the copy without altering the original built-in template.

---

### User Story 4 - Manual "Run Now" Trigger (Priority: P2)

As a project maintainer, I want to manually trigger any housekeeping task on demand so that I can initiate maintenance activities immediately when needed, regardless of the configured schedule or count threshold.

**Why this priority**: On-demand execution provides flexibility for urgent situations (e.g., a security incident requiring an immediate review). It complements but does not replace automated triggers.

**Independent Test**: Can be tested by selecting any existing housekeeping task, clicking "Run Now", and verifying a GitHub Issue is created and the event is logged in the task history.

**Acceptance Scenarios**:

1. **Given** an enabled housekeeping task, **When** a maintainer triggers the "Run Now" action, **Then** a parent GitHub Issue is created from the stored template with sub issues, and the trigger type is recorded as "manual" in the history.
2. **Given** a disabled housekeeping task, **When** a maintainer triggers the "Run Now" action, **Then** the task still executes (manual override bypasses the enabled/disabled state) and the event is logged.
3. **Given** a housekeeping task that was manually triggered, **When** the "Run Now" action is invoked again within the cooldown window, **Then** the system warns the user about the recent execution and requires confirmation before proceeding.

---

### User Story 5 - Manage Reusable Issue Templates (Priority: P2)

As a project maintainer, I want to create, edit, and delete reusable GitHub Issue templates independently of housekeeping tasks so that I can maintain a library of templates that multiple tasks can reference.

**Why this priority**: Template management enables reuse and modularity. While tasks can reference templates at creation, independent template management allows evolving templates without recreating tasks.

**Independent Test**: Can be tested by creating a new issue template, verifying it appears in the template library, editing its content, and confirming the change persists.

**Acceptance Scenarios**:

1. **Given** the template management interface, **When** a maintainer creates a new issue template with a name, title pattern, and body content, **Then** the template is saved and available for selection in housekeeping task configuration.
2. **Given** an existing issue template referenced by one or more housekeeping tasks, **When** a maintainer edits the template content, **Then** future task triggers use the updated template content.
3. **Given** an existing issue template referenced by active housekeeping tasks, **When** a maintainer attempts to delete it, **Then** the system warns that active tasks reference this template and requires confirmation before deletion.
4. **Given** an existing issue template not referenced by any task, **When** a maintainer deletes it, **Then** the template is removed from the library.

---

### User Story 6 - View Trigger and Run History (Priority: P3)

As a project maintainer, I want to view a history log for each housekeeping task showing when it was triggered, what type of trigger fired, the resulting GitHub Issue, and whether it succeeded or failed, so that I can audit and troubleshoot recurring maintenance.

**Why this priority**: History provides observability and auditability. While not required for the system to function, it is essential for trust and debugging.

**Independent Test**: Can be tested by triggering a housekeeping task (manually or automatically), then viewing its history log to verify the entry includes timestamp, trigger type, issue URL, and status.

**Acceptance Scenarios**:

1. **Given** a housekeeping task with previous trigger events, **When** a maintainer views the task's history, **Then** a chronological list of entries is displayed, each showing timestamp, trigger type (scheduled, count-based, or manual), the resulting GitHub Issue URL, and status (success or failure).
2. **Given** a housekeeping task trigger that fails (e.g., GitHub API error), **When** the maintainer views the history, **Then** the failed entry shows a "failure" status with a description of the error.
3. **Given** a housekeeping task with no prior trigger events, **When** a maintainer views the history, **Then** an empty state message indicates no runs have occurred yet.

---

### User Story 7 - Enable and Disable Housekeeping Tasks (Priority: P3)

As a project maintainer, I want to enable or disable individual housekeeping tasks without deleting them so that I can temporarily pause maintenance activities while preserving their configuration and history.

**Why this priority**: Enable/disable is a convenience feature that avoids destructive deletion. It supports operational flexibility but is not required for core functionality.

**Independent Test**: Can be tested by disabling an active task, verifying its trigger no longer fires, then re-enabling it and confirming triggers resume.

**Acceptance Scenarios**:

1. **Given** an enabled housekeeping task, **When** a maintainer disables it, **Then** the task's automatic triggers stop firing, but its configuration and history remain intact.
2. **Given** a disabled housekeeping task, **When** a maintainer re-enables it, **Then** automatic triggers resume based on the configured schedule or count from the current state (not retroactively).
3. **Given** a disabled housekeeping task, **When** viewed in the task list, **Then** it is visually distinguished as disabled (e.g., greyed out or labeled "Paused").

---

### Edge Cases

- What happens when a housekeeping task's referenced template is deleted while the task is enabled? The task should become invalid and not fire until a valid template is reassigned. An alert should notify the maintainer.
- What happens when the GitHub API is unavailable during a scheduled trigger? The system should log a failure entry in the history and retry on the next trigger cycle without creating duplicate issues.
- What happens when multiple count-based tasks reach their threshold simultaneously from the same parent issue creation event? Each task should be evaluated and triggered independently without interference.
- What happens when a time-based trigger fires but the system was offline during the scheduled time? The system should detect the missed trigger on next startup and execute it once (catch-up), logging it as a delayed scheduled trigger.
- What happens when a housekeeping task is deleted while a trigger is in-flight (issue creation in progress)? The in-flight operation should complete, but no further triggers should occur.
- What happens when two maintainers attempt to "Run Now" on the same task simultaneously? The idempotency guard should ensure only one issue is created; the second request should receive a notification that the task was already triggered.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST allow users to create a housekeeping task with a unique name, optional description, and a reference to a stored GitHub Issue template.
- **FR-002**: System MUST support two mutually exclusive trigger modes per housekeeping task: time-based (configurable schedule using cron expressions or named presets such as daily, weekly, monthly) and count-based (fires after X new parent GitHub Issues created since the last trigger).
- **FR-003**: System MUST create a parent GitHub Issue from the stored template when a housekeeping task is triggered, then generate sub issues based on the project board's agent pipeline configuration.
- **FR-004**: System MUST default to the Spec Kit agent pipeline reconfiguration for sub-issue generation when no custom sub-issue mapping is defined for a housekeeping task.
- **FR-005**: System MUST provide at least three built-in pre-configured starter templates: "Security and Privacy Review", "Test Coverage Refresh", and "Bug Bash", each referencing the `#codebase` context for agent pipeline processing.
- **FR-006**: System MUST store and manage reusable GitHub Issue templates independently, allowing templates to be created, edited, and deleted separately from housekeeping task definitions.
- **FR-007**: System MUST track per housekeeping task: the last trigger timestamp and the last trigger parent-issue-count baseline, to accurately evaluate both trigger types.
- **FR-008**: System MUST allow users to manually trigger any housekeeping task on demand ("Run Now"), bypassing the configured trigger condition, and record this as a manual trigger event in the task history.
- **FR-009**: System MUST display a trigger/run history log per housekeeping task showing: timestamp, trigger type (scheduled, count-based, manual), resulting GitHub Issue URL, and status (success/failure).
- **FR-010**: System MUST enforce idempotency guards to prevent a task from being double-triggered within a minimum cooldown window.
- **FR-011**: System SHOULD validate that the referenced GitHub Issue template and agent pipeline sub-issue configuration exist and are valid before saving a housekeeping task, surfacing errors inline.
- **FR-012**: System SHOULD support enabling and disabling individual housekeeping tasks without deleting them, preserving their configuration and history.
- **FR-013**: System MUST allow users to edit existing housekeeping task configurations (name, description, template reference, trigger type, trigger value).
- **FR-014**: System MUST allow users to delete housekeeping tasks, removing their configuration from the system.
- **FR-015**: System SHOULD warn users when deleting a template that is currently referenced by active housekeeping tasks.

### Key Entities

- **Housekeeping Task**: A named, recurring maintenance task definition. Key attributes: unique identifier, name, description, template reference, sub-issue configuration (defaults to Spec Kit agent pipeline), trigger type (time or count), trigger value (cron string or integer threshold), last triggered timestamp, last triggered issue count baseline, enabled status.
- **Issue Template**: A reusable GitHub Issue template that defines the title pattern and body content for parent issues created by housekeeping tasks. Key attributes: unique identifier, name, title pattern, body content, category (built-in or custom).
- **Trigger Event**: A historical record of a housekeeping task execution. Key attributes: timestamp, trigger type (scheduled, count-based, manual), resulting GitHub Issue URL, status (success/failure), error details (if failed).
- **Agent Pipeline Configuration**: The project board's sub-issue generation mapping that determines which sub issues are created under the parent issue. Defaults to Spec Kit agent pipeline reconfiguration when no custom mapping is provided.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Maintainers can create and configure a new housekeeping task in under 3 minutes, including selecting a template and setting a trigger.
- **SC-002**: Time-based housekeeping tasks fire within 5 minutes of their scheduled time with 99% reliability.
- **SC-003**: Count-based housekeeping tasks fire within 1 minute of the threshold parent issue being created.
- **SC-004**: The system ships with at least 3 built-in starter templates usable without any additional configuration.
- **SC-005**: Manual "Run Now" triggers create the parent issue and sub issues within 30 seconds of user action.
- **SC-006**: No duplicate issues are created from the same trigger event, even under concurrent trigger conditions.
- **SC-007**: Trigger history log displays all past events accurately with zero data loss for completed trigger entries.
- **SC-008**: Maintainers can enable/disable a task in a single action without losing configuration or history.
- **SC-009**: 90% of first-time users can set up a recurring housekeeping task using a built-in template without consulting documentation.
- **SC-010**: All template and task configuration validation errors are surfaced inline before save, reducing configuration errors by 80% compared to post-save error discovery.

## Assumptions

- The project already has a GitHub Projects board configured with an agent pipeline (Spec Kit or custom).
- GitHub Issues API supports sub-issue creation or tasklist-based linking as used by the existing workflow system.
- The existing GitHub Actions scheduled workflow system or internal cron scheduler is available for time-based trigger integration.
- The parent issue creation event pipeline is accessible for hooking count-based trigger evaluation.
- The `#codebase` context reference is supported by the agent pipeline for built-in template processing.
- Standard web application performance expectations apply (page loads under 2 seconds, API responses under 3 seconds) unless otherwise specified.
- Authentication and authorization follow the existing project access control model — only authorized maintainers can create, edit, or trigger housekeeping tasks.
