# Feature Specification: Spec Kit Custom Agent Assignment by Status

**Feature Branch**: `002-speckit-agent-assignment`  
**Created**: February 13, 2026  
**Status**: Draft  
**Input**: User description: "Update and replace GitHub Copilot assignment for GitHub Issues to instead leverage the correct GitHub Copilot CUSTOM AGENT from Spec Kit. Status → Spec Kit Agent Type: Backlog → speckit.specify, Ready → speckit.plan THEN speckit.tasks, In Progress → speckit.implement"

## Clarifications

### Session 2026-02-13

- Q: Should the Backlog → Ready transition wait for `speckit.specify` to complete before proceeding? → A: Yes — hold the issue in Backlog until `speckit.specify` completes, then auto-transition to Ready.
- Q: What is the canonical completion signal for a Spec Kit agent? → A: Comment-based — the agent posts its output (markdown files) as GitHub Issue comments, then posts a final `<agent-name>: All done!>` comment as the completion signal.
- Q: Where should pipeline state (which agent is active, which have completed) be persisted? → A: In-memory with GitHub Issue comments as source of truth — completion markers on the issue serve as the durable record; on restart, the system reconstructs pipeline state by reading issue comments.
- Q: Should the existing polling service be extended to monitor all pipeline statuses, or should a separate pipeline monitor be introduced? → A: Extend existing polling service — add comment-based completion checks for Backlog and Ready statuses alongside the existing PR-based check for In Progress.
- Q: Should `speckit.implement` completion use the comment-based signal or the existing PR-based detection? → A: PR-based (existing) — keep detecting `speckit.implement` completion via PR un-drafting, since it's the only agent that produces a PR.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Status-Specific Agent Assignment on Issue Creation (Priority: P1)

When a user confirms an AI-generated issue recommendation and the system creates a GitHub Issue, the issue is added to the project in "Backlog" status and the system assigns GitHub Copilot with the `speckit.specify` custom agent. The agent receives the full issue context (title, description, comments) as its prompt so it can refine and elaborate the specification directly on the issue. The issue remains in "Backlog" until `speckit.specify` completes; only then does the system auto-transition the issue to "Ready".

**Why this priority**: This is the entry point for every new issue in the workflow. Without mapping Backlog to `speckit.specify`, the Spec Kit integration has no starting point. It replaces the previous generic Copilot assignment and delivers immediate value by having Copilot generate a detailed specification for each new issue.

**Independent Test**: Can be fully tested by confirming an AI issue recommendation and verifying that (1) the GitHub Issue is created, (2) it is placed in "Backlog" status, (3) GitHub Copilot is assigned with the `speckit.specify` custom agent, and (4) the agent prompt contains the full issue context. Delivers value by automatically producing a refined spec for every new feature request.

**Acceptance Scenarios**:

1. **Given** a user confirms an AI-generated issue recommendation, **When** the system creates the GitHub Issue and adds it to the project with "Backlog" status, **Then** GitHub Copilot is assigned to the issue with the `speckit.specify` custom agent and the issue remains in "Backlog" until the agent completes
2. **Given** the `speckit.specify` agent completes its work on a Backlog issue, **When** completion is detected, **Then** the system auto-transitions the issue to "Ready" status
3. **Given** the system assigns `speckit.specify` to a Backlog issue, **When** the assignment is processed, **Then** the agent prompt includes the full issue title, description, and any existing comments
4. **Given** the `speckit.specify` agent assignment fails (e.g., Copilot unavailable), **When** the failure is detected, **Then** the system logs the failure, falls back to the configured assignee if available, and the issue remains in "Backlog" status without blocking the workflow

---

### User Story 2 - Sequential Plan and Tasks Agents on Ready Status (Priority: P2)

When a GitHub Issue transitions to "Ready" status, the system assigns GitHub Copilot with the `speckit.plan` custom agent first. Once the plan agent completes its work (detected via PR completion or issue update), the system then assigns GitHub Copilot with the `speckit.tasks` custom agent to break down the plan into actionable tasks. Only after both agents have completed does the issue move to "In Progress".

**Why this priority**: This is the core differentiator from the previous workflow. Instead of a single generic Copilot assignment, "Ready" now triggers a two-step agent pipeline (plan then tasks) that produces structured implementation artifacts before any code is written. This ensures higher-quality implementation by front-loading planning.

**Independent Test**: Can be tested by manually moving an issue to "Ready" status and verifying that (1) `speckit.plan` is assigned first, (2) after plan completion, `speckit.tasks` is assigned, (3) after tasks completion, the status changes to "In Progress". Delivers value by ensuring every issue has a plan and task breakdown before implementation begins.

**Acceptance Scenarios**:

1. **Given** an issue status changes to "Ready", **When** the system detects the status change, **Then** GitHub Copilot is assigned with the `speckit.plan` custom agent and the issue remains in "Ready" status
2. **Given** the `speckit.plan` agent has completed its work, **When** the system detects plan completion, **Then** GitHub Copilot is reassigned with the `speckit.tasks` custom agent
3. **Given** the `speckit.tasks` agent has completed its work, **When** the system detects tasks completion, **Then** the issue status is updated to "In Progress"
4. **Given** either agent in the Ready pipeline fails, **When** the failure is detected, **Then** the system logs the error, notifies the user via the chat interface, and the issue remains in its current status for manual intervention

---

### User Story 3 - Implement Agent on In Progress Status (Priority: P3)

When a GitHub Issue transitions to "In Progress" status (after the plan and tasks agents have completed), the system assigns GitHub Copilot with the `speckit.implement` custom agent. The agent receives the full issue context including any plan and task artifacts generated by the previous agents.

**Why this priority**: This completes the agent pipeline by mapping the final active status to the implementation agent. It builds on P1 and P2 and delivers the expected end-to-end Spec Kit workflow.

**Independent Test**: Can be tested by transitioning an issue to "In Progress" and verifying that (1) GitHub Copilot is assigned with the `speckit.implement` custom agent, (2) the agent prompt includes the full issue context with plan and task artifacts. Delivers value by automating the implementation step with a context-rich prompt.

**Acceptance Scenarios**:

1. **Given** an issue transitions to "In Progress" status, **When** the system processes the transition, **Then** GitHub Copilot is assigned with the `speckit.implement` custom agent
2. **Given** the `speckit.implement` agent is assigned, **When** the assignment is processed, **Then** the agent prompt includes the issue title, description, comments, and all artifacts from the plan and tasks agents
3. **Given** the `speckit.implement` agent completes its work (PR created), **When** completion is detected, **Then** the issue transitions to "In Review" and the project owner is assigned as reviewer

---

### User Story 4 - Agent Mapping Configuration (Priority: P4)

An administrator or project owner can view and update the mapping between GitHub Project statuses and Spec Kit custom agent names through the workflow configuration. The configuration supports defining which agent(s) run at each status transition, including the sequential pipeline for "Ready" status.

**Why this priority**: While the default mapping (Backlog→specify, Ready→plan+tasks, In Progress→implement) covers the primary use case, teams may want to customize which agents run at each stage or skip certain agents. This flexibility is lower priority than the core pipeline.

**Independent Test**: Can be tested by updating the workflow configuration via the API and verifying that subsequent status transitions use the updated agent mappings. Delivers value by allowing teams to tailor the Spec Kit workflow to their needs.

**Acceptance Scenarios**:

1. **Given** a project owner accesses the workflow configuration, **When** they view the agent mapping settings, **Then** they see the current status-to-agent mapping for each workflow status
2. **Given** a project owner updates the agent mapping for a status, **When** the next issue reaches that status, **Then** the updated agent is used instead of the default
3. **Given** a project owner clears the agent mapping for a status, **When** an issue reaches that status, **Then** no custom agent is assigned and the system falls back to the configured assignee or generic Copilot assignment

---

### Edge Cases

- What happens when the `speckit.plan` agent completes but `speckit.tasks` assignment fails? The issue should remain in "Ready" with an error logged, and the user should be notified to retry.
- What happens if an issue is manually moved from "Backlog" directly to "In Progress", skipping "Ready"? The system should assign `speckit.implement` since the status-to-agent mapping is based on the target status, not the transition path.
- How does the system detect completion of sequential agents (plan then tasks) in the "Ready" pipeline? Completion is detected when the agent posts a `<agent-name>: All done!>` comment on the GitHub Issue. The system polls issue comments for this marker.
- What happens if an issue is moved backward in the workflow (e.g., from "In Progress" back to "Ready")? The system should re-trigger the agent(s) mapped to the new status, treating it as a fresh transition.
- What happens if the Spec Kit agent name is invalid or unrecognized by GitHub Copilot? The system should log a warning and fall back to generic Copilot assignment without a custom agent.
- How does the system handle concurrent status changes on the same issue? The system should process transitions sequentially per issue to avoid race conditions in agent assignment.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST replace the single `custom_agent` field in workflow configuration with a status-to-agent mapping that associates each workflow status with one or more Spec Kit agent names
- **FR-002**: System MUST assign GitHub Copilot with the `speckit.specify` custom agent when an issue enters "Backlog" status
- **FR-002a**: System MUST hold the issue in "Backlog" status until the `speckit.specify` agent completes, then auto-transition the issue to "Ready"
- **FR-003**: System MUST assign GitHub Copilot with the `speckit.plan` custom agent when an issue enters "Ready" status
- **FR-004**: System MUST detect when the `speckit.plan` agent completes its work on a "Ready" issue by monitoring for a comment matching the pattern `<agent-name>: All done!>` on the GitHub Issue
- **FR-005**: System MUST assign GitHub Copilot with the `speckit.tasks` custom agent after `speckit.plan` completes on a "Ready" issue
- **FR-006**: System MUST detect when the `speckit.tasks` agent completes its work on a "Ready" issue by monitoring for a comment matching the pattern `<agent-name>: All done!>` on the GitHub Issue
- **FR-007**: System MUST transition the issue from "Ready" to "In Progress" only after both `speckit.plan` and `speckit.tasks` agents have completed
- **FR-008**: System MUST assign GitHub Copilot with the `speckit.implement` custom agent when an issue enters "In Progress" status
- **FR-009**: System MUST pass the full issue context (title, description, comments, and artifacts from prior agents) as the prompt to each assigned custom agent
- **FR-009a**: System MUST detect completion of `speckit.specify`, `speckit.plan`, and `speckit.tasks` agents by polling for a GitHub Issue comment matching the pattern `<agent-name>: All done!>` (e.g., `speckit.specify: All done!>`)
- **FR-009b**: Each agent MUST post its output artifacts (markdown files) as GitHub Issue comments before posting the completion marker comment
- **FR-009c**: System MUST detect completion of the `speckit.implement` agent via the existing PR-based mechanism (PR is no longer a draft), not via the comment-based signal
- **FR-010**: System MUST log each agent assignment as a workflow transition, recording the specific agent name used
- **FR-011**: System MUST track the sub-state of sequential agent pipelines (e.g., "Ready: awaiting plan completion", "Ready: awaiting tasks completion") in memory, using GitHub Issue comments as the durable source of truth
- **FR-011a**: On system restart, the system MUST reconstruct pipeline state for in-progress issues by scanning their GitHub Issue comments for agent completion markers (`<agent-name>: All done!>`)
- **FR-011b**: The existing polling service MUST be extended to monitor issues in "Backlog" and "Ready" statuses for agent completion comments, in addition to the existing "In Progress" PR-based checks
- **FR-012**: System MUST handle agent assignment failures gracefully by logging the error, notifying the user, and leaving the issue in its current status
- **FR-013**: System MUST support configuring the status-to-agent mapping per project through the workflow configuration
- **FR-014**: System MUST provide default agent mappings (Backlog→speckit.specify, Ready→[speckit.plan, speckit.tasks], In Progress→speckit.implement) when no custom mapping is configured
- **FR-015**: System MUST support clearing agent mappings for a status to fall back to the configured assignee or generic Copilot
- **FR-016**: System MUST continue to transition from "In Progress" to "In Review" with project owner assignment when the implementation agent completes, consistent with the existing workflow
- **FR-017**: System MUST send real-time notifications to the chat interface when each agent assignment occurs and when each agent completes

### Key Entities

- **Agent Mapping**: Configuration that associates a workflow status name with an ordered list of Spec Kit custom agent names to execute when an issue enters that status
- **Agent Pipeline**: An ordered sequence of custom agents assigned to a single status (e.g., "Ready" has a pipeline of [speckit.plan, speckit.tasks] that execute sequentially)
- **Pipeline State**: Tracks the progress of a multi-agent pipeline for a specific issue, including which agent is currently active and which have completed
- **Agent Assignment Event**: A record of a custom agent being assigned to an issue, including the agent name, timestamp, and completion status

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of issues entering "Backlog" status are assigned to GitHub Copilot with the `speckit.specify` agent within 10 seconds
- **SC-002**: 100% of issues entering "Ready" status trigger the sequential plan-then-tasks agent pipeline
- **SC-003**: The `speckit.tasks` agent is assigned within 30 seconds of `speckit.plan` completion detection
- **SC-004**: Issues transition from "Ready" to "In Progress" only after both plan and tasks agents complete, with zero premature transitions
- **SC-005**: 100% of issues entering "In Progress" status are assigned to GitHub Copilot with the `speckit.implement` agent within 10 seconds
- **SC-006**: Users receive real-time notification within 2 seconds for each agent assignment and completion event
- **SC-007**: Agent assignment failures are logged and surfaced to users within 5 seconds, with the issue remaining in its current status
- **SC-008**: The end-to-end workflow (Backlog→Ready→In Progress→In Review) completes without manual intervention for 95% of issues

## Assumptions

1. **GitHub Copilot Custom Agent Support**: GitHub Copilot supports receiving a custom agent name (e.g., `speckit.specify`, `speckit.plan`, `speckit.tasks`, `speckit.implement`) when assigned to an issue, and routes work to the corresponding Spec Kit agent
2. **Spec Kit Installed**: The target repository has Spec Kit initialized (via `specify init`) with the relevant `/speckit.*` slash commands available to the Copilot agent
3. **Agent Completion Detection**: Completion of `speckit.specify`, `speckit.plan`, and `speckit.tasks` agents is detected by polling GitHub Issue comments for a marker comment matching the pattern `<agent-name>: All done!>`. Prior to this marker, the agent posts its output artifacts (markdown files) as issue comments. The `speckit.implement` agent uses the existing PR-based completion detection (PR is no longer a draft) since it is the only agent that produces a PR.
4. **Single Active Agent Per Issue**: Only one custom agent is active on an issue at a time; sequential agents in a pipeline do not run concurrently
5. **Existing Workflow Infrastructure**: The current workflow orchestrator, polling service, WebSocket notifications, and GitHub API integration remain available and functional. Pipeline state is held in memory and reconstructed from GitHub Issue comments on restart.
6. **Status Column Names**: The GitHub Project uses the standard status column names: "Backlog", "Ready", "In Progress", "In Review"
7. **Backward Compatibility**: The existing `custom_agent` field on `WorkflowConfiguration` can be replaced by the new agent mapping without breaking existing clients, since the feature is being fully replaced rather than extended

## Dependencies

- GitHub Copilot custom agent assignment capability (ability to pass agent name when assigning Copilot to an issue)
- Spec Kit initialized in the target repository with `speckit.specify`, `speckit.plan`, `speckit.tasks`, and `speckit.implement` agents available
- Existing Copilot PR completion polling service, extended to also poll issue comments for agent completion markers across Backlog and Ready statuses
- Existing workflow orchestrator and GitHub Projects API integration
- Existing WebSocket notification system for real-time user feedback

## Scope Boundaries

### In Scope

- Replacing the single `custom_agent` configuration with a per-status agent mapping
- Implementing status-specific agent assignment (Backlog→specify, Ready→plan+tasks, In Progress→implement)
- Implementing sequential agent pipeline for "Ready" status (plan then tasks)
- Tracking pipeline sub-states for multi-agent sequences
- Detecting agent completion to trigger the next agent in a pipeline
- Updating workflow configuration to support agent mappings
- Logging and audit trail for all agent assignments
- Real-time notifications for agent assignment and completion events
- Graceful error handling and fallback for agent failures

### Out of Scope

- Installing or configuring Spec Kit in the target repository (assumed pre-existing)
- Modifying Spec Kit's internal behavior or agent implementations
- Supporting agents from frameworks other than Spec Kit
- Parallel agent execution (agents within a pipeline always run sequentially)
- Custom agent parameters beyond the agent name and issue context prompt
- UI for visually managing agent pipeline configurations (API-only configuration)
- Modifying the "In Review" status handling (owner assignment remains unchanged)
