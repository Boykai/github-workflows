# Feature Specification: Auto Merge — Automatically Squash-Merge Parent PRs When Pipelines Complete

**Feature Branch**: `001-auto-merge-pipelines`  
**Created**: 2026-03-22  
**Status**: Draft  
**Input**: User description: "Auto Merge: Automatically squash-merge parent PRs when pipelines complete"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Enable Auto Merge and Merge Automatically on Pipeline Success (Priority: P1)

As a developer, I want to toggle Auto Merge on for my project so that when all pipeline steps complete successfully, the parent pull request is automatically squash-merged to the default branch without requiring my manual intervention.

**Why this priority**: This is the core value proposition of the feature. Without automatic merging on successful pipeline completion, no other aspect of the feature delivers value. It eliminates the most common manual step in the developer workflow.

**Independent Test**: Can be fully tested by enabling Auto Merge on a project, running a pipeline to successful completion, and verifying the parent PR is squash-merged automatically. Delivers immediate value by removing the manual merge step.

**Acceptance Scenarios**:

1. **Given** a project with Auto Merge enabled at the project level, **When** a pipeline completes all steps successfully, **Then** the system automatically squash-merges the parent pull request to the default branch.
2. **Given** a project with Auto Merge disabled at the project level but enabled at the pipeline level, **When** that pipeline completes successfully, **Then** the system automatically squash-merges the parent pull request.
3. **Given** a project with Auto Merge enabled, **When** the pipeline completes and the PR is still in draft state, **Then** the system marks the PR as ready-for-review before attempting the merge.
4. **Given** a project with Auto Merge enabled, **When** the pipeline completes and all CI checks pass and the PR is in a mergeable state, **Then** the PR is squash-merged and the merge commit appears on the default branch.
5. **Given** a project with Auto Merge enabled, **When** the merge attempt fails due to a non-recoverable error, **Then** the system notifies the developer with details about the failure and marks the pipeline with an error status.

---

### User Story 2 - Skip Human Agent Step When Auto Merge Is Active (Priority: P1)

As a developer, I want the human review/merge agent step to be automatically skipped when Auto Merge is enabled, so that the pipeline proceeds directly to the merge flow without waiting for human intervention, while preserving a clear audit trail of the skip.

**Why this priority**: The human agent step is the manual bottleneck that Auto Merge is designed to eliminate. Without skipping it, the pipeline would still block on human action, defeating the purpose of the feature.

**Independent Test**: Can be fully tested by configuring a pipeline with a human agent as the last step, enabling Auto Merge, running the pipeline, and verifying the human step is marked as SKIPPED with appropriate audit records.

**Acceptance Scenarios**:

1. **Given** a pipeline with Auto Merge enabled and a human agent configured as the last step, **When** the pipeline reaches the human agent step, **Then** the step is marked with a ⏭ SKIPPED indicator in the tracking table.
2. **Given** a pipeline with Auto Merge enabled and a human agent as the last step, **When** the human step is skipped, **Then** the human sub-issue is closed with a comment stating "Skipped — Auto Merge enabled."
3. **Given** a pipeline with Auto Merge enabled and a human agent as the last step, **When** the human step is skipped, **Then** the pipeline proceeds directly to the auto-merge flow without assigning the human agent.
4. **Given** a pipeline with Auto Merge disabled, **When** the pipeline reaches the human agent step, **Then** the human agent is assigned as normal and the step is not skipped.

---

### User Story 3 - CI Failure Recovery via DevOps Agent (Priority: P2)

As a developer, I want a DevOps agent to automatically attempt to fix CI failures (test failures, merge conflicts) on auto-merge-enabled pipelines, so that transient or simple failures are resolved without my manual intervention.

**Why this priority**: While the core merge flow (P1) delivers the primary value, CI failures are the most common reason merges are blocked. Automated recovery for simple failures significantly increases the success rate of auto-merge and reduces developer interruptions.

**Independent Test**: Can be tested by enabling Auto Merge on a pipeline, introducing a CI failure on the PR, and verifying the DevOps agent is dispatched to investigate and attempt a fix.

**Acceptance Scenarios**:

1. **Given** an auto-merge-enabled pipeline whose PR has a failing CI check, **When** the CI failure is detected via webhook, **Then** the system dispatches the DevOps agent to investigate and attempt a fix.
2. **Given** the DevOps agent has been dispatched for a CI failure, **When** the agent successfully resolves the issue and CI passes, **Then** the system retries the auto-merge process.
3. **Given** the DevOps agent has failed to resolve the CI issue after 2 attempts, **When** the second attempt completes without success, **Then** the system marks the pipeline with an error status and notifies the developer.
4. **Given** the DevOps agent is already active on a pipeline, **When** another CI failure event arrives for the same pipeline, **Then** the system does not dispatch a duplicate DevOps agent.

---

### User Story 4 - Project-Level Auto Merge Toggle in UI (Priority: P2)

As a project owner, I want to toggle Auto Merge on or off from the Projects page using a clearly visible toggle button, so that I can control whether all pipelines in my project automatically merge upon completion.

**Why this priority**: The UI toggle is how users enable and configure the feature. While backend logic can function without it (e.g., via direct API calls), a user-facing control is essential for practical adoption.

**Independent Test**: Can be tested by navigating to the Projects page, clicking the Auto Merge toggle, and verifying the setting persists and is reflected in the project configuration.

**Acceptance Scenarios**:

1. **Given** the Projects page is loaded, **When** the user views a project, **Then** an Auto Merge toggle button is visible adjacent to the existing Queue Mode toggle, using the same visual styling pattern.
2. **Given** the Auto Merge toggle is in the off state, **When** the user clicks it, **Then** the setting is saved and the toggle renders in its active (green/primary) state.
3. **Given** a project has active pipelines and Auto Merge is currently off, **When** the user enables Auto Merge, **Then** a confirmation dialog appears listing the number of active pipelines that will be affected.
4. **Given** the user confirms the retroactive toggle, **Then** all currently active pipelines are affected by the Auto Merge setting at their next merge decision point.

---

### User Story 5 - Pipeline-Level Auto Merge Toggle (Priority: P3)

As a developer, I want to enable or disable Auto Merge at the individual pipeline level, so that I can override the project-level setting for specific pipelines when needed.

**Why this priority**: Pipeline-level control provides fine-grained configuration. While the project-level toggle covers most use cases, per-pipeline overrides are needed for advanced workflows where certain pipelines should not auto-merge.

**Independent Test**: Can be tested by navigating to the pipeline configuration panel, toggling Auto Merge on for a specific pipeline, and verifying the setting is persisted independently from the project-level setting.

**Acceptance Scenarios**:

1. **Given** the pipeline configuration panel is open, **When** the user views the settings, **Then** an Auto Merge toggle is available.
2. **Given** Auto Merge is disabled at the project level, **When** the user enables it at the pipeline level, **Then** that specific pipeline uses Auto Merge (either level being true activates the feature).
3. **Given** Auto Merge is enabled at both project and pipeline levels, **When** the user disables it at the pipeline level only, **Then** Auto Merge remains active for that pipeline because the project-level setting is still enabled.

---

### User Story 6 - Real-Time Notifications for Auto Merge Events (Priority: P3)

As a developer, I want to receive real-time toast notifications when auto-merge actions occur (success, failure, DevOps agent triggered), so that I stay informed about the status of my pipelines without needing to check manually.

**Why this priority**: Notifications are an enhancement to visibility and developer experience. The core feature works without them, but they significantly improve trust and awareness of automated actions.

**Independent Test**: Can be tested by triggering an auto-merge event and verifying that the appropriate toast notification appears in the UI in real time.

**Acceptance Scenarios**:

1. **Given** a pipeline with Auto Merge enabled completes a successful squash-merge, **When** the merge is finalized, **Then** the user sees a success toast notification stating "PR #X squash-merged."
2. **Given** a pipeline with Auto Merge enabled fails to merge, **When** the merge attempt fails, **Then** the user sees an error toast notification with failure details.
3. **Given** a DevOps agent is dispatched to fix a CI failure, **When** the dispatch occurs, **Then** the user sees an info toast notification stating "DevOps agent resolving CI failure on #X."

---

### Edge Cases

- What happens when the target branch has branch protection rules requiring reviews not satisfied by the merge bot? The merge attempt will fail, and the system must surface a clear error message guiding the user to adjust branch protection settings or ensure the required reviews are in place.
- What happens when multiple pipelines on the same project have simultaneous CI failures? The system must serialize DevOps agent dispatches per project to prevent competing invocations, similar to the existing queue mode mechanism.
- What happens when Auto Merge is toggled on for a project that already has completed pipelines awaiting human review? The system handles this retroactively via a lazy check at the merge decision point — existing in-memory pipeline states are not eagerly updated, but the next merge decision point checks the current project-level setting.
- What happens when the PR is in a CONFLICTING state? The system returns a "devops_needed" status and dispatches the DevOps agent to attempt conflict resolution. If the DevOps agent cannot resolve the conflict after 2 attempts, the pipeline is marked as error.
- What happens when the merge API call succeeds but the webhook confirmation is delayed? The system should rely on the merge API response for success confirmation rather than waiting for a webhook event.
- What happens when a user disables Auto Merge while a pipeline is mid-execution? The system checks the Auto Merge flag at the merge decision point, so disabling it before the pipeline reaches that point will prevent the auto-merge.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide a project-level Auto Merge setting that can be toggled on or off, defaulting to off. The setting is persisted in the project configuration and applies to all pipelines in the project.
- **FR-002**: System MUST provide a pipeline-level Auto Merge setting that can be toggled on or off, defaulting to off. The setting is persisted in the pipeline configuration.
- **FR-003**: System MUST resolve the effective Auto Merge flag at pipeline start by evaluating both project-level and pipeline-level settings — if either is true, Auto Merge is active for that pipeline run.
- **FR-004**: System MUST apply a visible "auto-merge" label to the associated issue when Auto Merge is activated for a pipeline, providing at-a-glance visibility in the issue tracker.
- **FR-005**: System MUST skip the human agent step when Auto Merge is active and the human agent is the last step in the pipeline. The skipped step is marked with a ⏭ SKIPPED indicator in the tracking table, and the associated human sub-issue is closed with a "Skipped — Auto Merge enabled" comment.
- **FR-006**: System MUST attempt to squash-merge the parent PR upon pipeline completion when Auto Merge is active. This includes discovering the PR, marking draft PRs as ready-for-review, verifying CI status, verifying mergeability, and executing the squash merge.
- **FR-007**: System MUST detect CI failures on auto-merge-enabled pipelines via webhook events and dispatch a DevOps agent to investigate and attempt remediation.
- **FR-008**: System MUST limit DevOps agent retry attempts to a maximum of 2 per pipeline. After 2 failed attempts, the pipeline is marked with an error status and the user is notified.
- **FR-009**: System MUST prevent duplicate DevOps agent dispatches — if a DevOps agent is already active on a pipeline, additional CI failure events for the same pipeline do not trigger a new dispatch.
- **FR-010**: System MUST provide a DevOps repository agent that is automatically discoverable by the existing agent scanning mechanism, specialized for reading CI logs, identifying failures, resolving merge conflicts, and re-triggering checks.
- **FR-011**: System MUST handle retroactive Auto Merge activation — toggling Auto Merge on at the project level applies to all currently active pipelines at their next merge decision point, without eagerly updating all in-memory pipeline states.
- **FR-012**: System MUST persist the Auto Merge setting in the database for both project settings and pipeline configurations, surviving application restarts.
- **FR-013**: System MUST display the Auto Merge toggle on the Projects page adjacent to the existing Queue Mode toggle, using consistent visual styling (same chip/badge pattern, with the merge icon).
- **FR-014**: System MUST display the Auto Merge toggle in the pipeline configuration panel.
- **FR-015**: System MUST show a confirmation dialog when enabling Auto Merge on a project that has active pipelines, listing the number of affected pipelines.
- **FR-016**: System MUST send real-time notifications to users via existing broadcast infrastructure for auto-merge events: success ("PR #X squash-merged"), failure (with error details), and DevOps agent dispatch ("DevOps agent resolving CI failure on #X").

### Key Entities

- **Auto Merge Setting (Project Level)**: A boolean flag on the project configuration that indicates whether all pipelines under the project should attempt auto-merge upon completion. Defaults to off. Related to the project settings entity.
- **Auto Merge Setting (Pipeline Level)**: A boolean flag on the pipeline configuration that indicates whether a specific pipeline should attempt auto-merge upon completion. Defaults to off. Related to the pipeline configuration entity.
- **Pipeline State (Auto Merge Flag)**: A resolved boolean flag on the pipeline's runtime state, computed from the project and pipeline-level settings at pipeline start. Determines behavior at the merge decision point.
- **DevOps Agent**: A repository-scoped agent definition that specializes in diagnosing CI failures, reading logs, resolving conflicts, and applying targeted fixes. Discovered via the existing agent directory scan.
- **DevOps Attempt Tracker**: A counter stored in pipeline metadata that tracks the number of DevOps agent dispatch attempts per pipeline, capped at 2.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Developers can enable Auto Merge for a project in under 10 seconds via a single toggle interaction on the Projects page.
- **SC-002**: When Auto Merge is active and a pipeline completes successfully with all CI checks passing, the parent PR is squash-merged within 60 seconds of pipeline completion without any manual intervention.
- **SC-003**: The human agent step is reliably skipped when Auto Merge is active, reducing pipeline completion time by eliminating the human review wait period (which can range from minutes to hours).
- **SC-004**: The DevOps agent resolves at least 50% of simple CI failures (e.g., flaky tests, minor conflicts) automatically, reducing the number of pipelines requiring manual developer intervention.
- **SC-005**: No more than 2 DevOps agent attempts are made per pipeline failure, preventing runaway retry loops.
- **SC-006**: Users receive real-time notifications for all auto-merge events within 5 seconds of the event occurring.
- **SC-007**: The audit trail for every auto-merged pipeline is complete — each skipped step, merge action, and DevOps dispatch is recorded and visible in the pipeline tracking table and issue comments.
- **SC-008**: Toggling Auto Merge on a project with active pipelines takes effect at the next merge decision point for each pipeline, without requiring pipeline restarts.
- **SC-009**: The Auto Merge toggle is visually consistent with existing project settings toggles, requiring no learning curve for existing users.

## Assumptions

- The merge strategy is always squash merge. No other merge strategies (merge commit, rebase) are supported for auto-merge.
- Branch protection rules on the target branch must be compatible with the merge bot's permissions. If required reviews are configured, the Copilot review must satisfy the required review count.
- The existing agent directory scanning mechanism will discover the DevOps agent without additional backend code changes.
- The existing WebSocket broadcast infrastructure supports the new event types needed for auto-merge notifications.
- The existing queue mode serialization pattern can be adapted or referenced for serializing DevOps agent dispatches per project.
- The "devops: Done!" marker is the standard completion signal used to detect when the DevOps agent has finished its work.
- Draft PRs can be programmatically marked as ready-for-review via the existing platform API.

## Dependencies

- Existing project settings persistence layer (settings_store, settings API).
- Existing pipeline configuration persistence layer (pipeline CRUD endpoints).
- Existing webhook event handling infrastructure.
- Existing agent discovery mechanism (directory scan of repository agents).
- Existing real-time broadcast (WebSocket) infrastructure.
- Existing pipeline orchestrator and state management system.
- Existing PR discovery and merge API integrations.
