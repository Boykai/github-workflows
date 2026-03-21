# Feature Specification: Fix Premature Copilot Review Completion in Agent Pipeline

**Feature Branch**: `055-fix-copilot-review-completion`  
**Created**: 2026-03-21  
**Status**: Draft  
**Input**: User description: "Fix Premature Copilot Review Completion in Agent Pipeline"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Pipeline Correctly Sequences Agent Completion (Priority: P1)

As a pipeline operator, I need the system to only mark the copilot-review step as complete when it is genuinely the current active agent in the pipeline, so that earlier agents (such as speckit.implement) finishing their work does not falsely advance the pipeline past the review step.

**Why this priority**: This is the core bug. When speckit.implement finishes and its PR becomes ready, the system currently marks copilot-review as done even though copilot-review has not yet started. This causes the entire pipeline to skip the review step, undermining code quality assurance.

**Independent Test**: Can be fully tested by running a pipeline where speckit.implement completes and verifying that copilot-review is NOT marked as done until the pipeline has actually advanced to the copilot-review step.

**Acceptance Scenarios**:

1. **Given** a pipeline is running with current agent "speckit.implement", **When** the completion-detection function is invoked for copilot-review, **Then** the system returns "not done" immediately without making any external calls.
2. **Given** a pipeline is running with current agent "copilot-review", **When** the completion-detection function is invoked for copilot-review, **Then** the system performs its normal timestamp-based and stale-marker checks and returns the correct result.
3. **Given** a pipeline is running with current agent "speckit.implement", **When** the completion-detection function is called without pipeline context, **Then** the system still returns "not done" (defensive fallback).

---

### User Story 2 - Webhook Does Not Prematurely Move Issues to "In Review" (Priority: P1)

As a pipeline operator, I need webhook-triggered status changes to respect the pipeline's current position, so that an issue is not moved to "In Review" on the project board before the pipeline has actually reached the copilot-review step.

**Why this priority**: The webhook fires whenever ANY Copilot PR becomes ready for review. When speckit.implement finishes and its PR is ready, the webhook moves the issue to "In Review" on the board, creating a misleading state. This directly compounds the false-completion bug.

**Independent Test**: Can be fully tested by simulating a webhook "ready_for_review" event while the pipeline's current agent is speckit.implement and verifying the issue status is NOT changed to "In Review".

**Acceptance Scenarios**:

1. **Given** a pipeline-tracked issue with current agent "speckit.implement", **When** a webhook fires indicating a Copilot PR is ready for review, **Then** the system does NOT move the issue to "In Review" and logs that the move was skipped.
2. **Given** a pipeline-tracked issue with current agent "copilot-review", **When** a webhook fires indicating a Copilot PR is ready for review, **Then** the system moves the issue to "In Review" as normal.
3. **Given** a non-pipeline-tracked issue (no pipeline exists), **When** a webhook fires indicating a Copilot PR is ready for review, **Then** the system moves the issue to "In Review" as normal (backward compatibility).

---

### User Story 3 - Review-Request Timestamp Survives Server Restart (Priority: P2)

As a pipeline operator, I need the review-request timestamp to be durably stored so that a server restart does not lose the record of when the copilot review was requested, which would cause the system to either skip the confirmation delay or fail to detect review completion.

**Why this priority**: The current in-memory-only storage means any server restart clears the timestamp. The fallback recovery from issue body HTML comments is unreliable. Durable storage eliminates this class of failure, making the pipeline resilient to restarts.

**Independent Test**: Can be fully tested by recording a review-request timestamp, clearing the in-memory store (simulating a restart), and verifying the system recovers the timestamp from durable storage.

**Acceptance Scenarios**:

1. **Given** a copilot review is requested for an issue, **When** the timestamp is recorded, **Then** the system persists it to both in-memory storage and durable storage.
2. **Given** the in-memory timestamp store has been cleared (server restart), **When** the completion check looks up the timestamp, **Then** the system recovers it from durable storage before falling back to HTML comment parsing.
3. **Given** no timestamp exists in either in-memory or durable storage, **When** the completion check looks up the timestamp, **Then** the system falls back to parsing the issue body HTML comment (existing behavior preserved).

---

### User Story 4 - Pipeline Reconstruction Does Not Falsely Set Current Agent (Priority: P2)

As a pipeline operator, I need the pipeline reconstruction logic to correctly determine the current agent even when the project board status says "In Review," so that a server restart while earlier agents are still pending does not cause the system to skip ahead to copilot-review.

**Why this priority**: After a server restart, the pipeline is reconstructed from the board status. If the board says "In Review" (due to the webhook bug) but speckit.implement is still pending, reconstruction incorrectly sets copilot-review as the current agent. This safety net prevents cascading errors from the other bugs.

**Independent Test**: Can be fully tested by calling the reconstruction function with status "In Review" while agents marked "In Progress" are still pending, and verifying it reconstructs the pipeline with the correct current agent (the pending one, not copilot-review).

**Acceptance Scenarios**:

1. **Given** the project board shows status "In Review" but tracking data shows agents still marked "In Progress", **When** pipeline reconstruction is triggered, **Then** the system reconstructs the pipeline with the pending agent as current agent, not copilot-review.
2. **Given** the project board shows status "In Review" and all prior agents are genuinely complete, **When** pipeline reconstruction is triggered, **Then** the system correctly sets copilot-review as the current agent.

---

### Edge Cases

- What happens when the pipeline has only one agent (copilot-review itself)? The guard should allow normal completion detection since copilot-review IS the current agent.
- What happens when multiple webhooks fire in rapid succession for the same issue? The guard should prevent redundant status moves; only the first valid move should succeed.
- What happens when the durable timestamp store is unavailable (e.g., database connection failure)? The system should fall back to the existing HTML comment recovery without crashing.
- What happens when pipeline context is not available (e.g., legacy code paths calling completion detection without pipeline)? The system should log a warning and use defensive behavior (return "not done" or skip the move).
- What happens when a pipeline is reconstructed with an empty agents list? The system should handle this gracefully without index-out-of-bounds errors.
- What happens when the server restarts multiple times during a single pipeline run? Each restart should correctly recover state from durable storage and tracking data, never losing ground.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The completion-detection function for copilot-review MUST verify that copilot-review is the current pipeline agent before performing any completion checks. If it is not the current agent, the function MUST return "not done" immediately without making external calls.
- **FR-002**: The completion-detection function MUST accept an optional pipeline parameter to receive pipeline context from its callers.
- **FR-003**: Callers of the completion-detection function MUST pass the existing pipeline parameter through when available.
- **FR-004**: The review-status polling logic MUST verify the pipeline's current agent before processing copilot-review completion. If the current agent is not copilot-review and the pipeline has not yet reached the "In Review" stage, the system MUST skip copilot-review processing and let normal pipeline advancement handle the current agent.
- **FR-005**: The webhook handler for Copilot PR readiness MUST check pipeline state before moving an issue to "In Review". If a pipeline exists and its current agent is not copilot-review, the system MUST NOT move the issue status and MUST log the skip reason.
- **FR-006**: The webhook handler MUST preserve backward compatibility for non-pipeline-tracked issues by continuing to move them to "In Review" when no pipeline is found.
- **FR-007**: The system MUST persist copilot-review-request timestamps to durable storage when a review request is recorded.
- **FR-008**: The system MUST also continue to store timestamps in the existing in-memory store for fast access during normal operation.
- **FR-009**: When the in-memory timestamp is not found, the system MUST attempt recovery from durable storage before falling back to HTML comment parsing.
- **FR-010**: A data migration MUST create a durable storage structure for copilot review request records, supporting issue number, requested-at timestamp, and project identifier.
- **FR-011**: The pipeline reconstruction logic MUST verify tracking data for pending agents before setting the current agent based on board status alone. When tracking data indicates agents are still "In Progress," reconstruction MUST use the tracked state rather than the board status.
- **FR-012**: The system MUST log warning messages whenever a guard prevents a premature status change or false completion, including the current agent name and the action that was blocked.

### Key Entities

- **Pipeline**: Represents the sequential execution plan for an issue. Key attributes: list of agents, current agent index, current agent name, status.
- **Copilot Review Request**: Represents a recorded request for Copilot to review a PR. Key attributes: issue number, timestamp of when review was requested, associated project identifier.
- **Pipeline Agent**: Represents a step in the pipeline. Key attributes: agent name, completion status ("Done!" marker), order in pipeline.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: When a non-review pipeline agent completes, the copilot-review step is never falsely marked as done — 0% false-completion rate for copilot-review when it is not the current agent.
- **SC-002**: When a non-review pipeline agent's PR becomes ready, the issue is not moved to "In Review" on the project board — 0% premature status transitions for pipeline-tracked issues.
- **SC-003**: After a server restart, the system recovers copilot-review-request timestamps from durable storage within the same polling cycle — 100% recovery rate from durable storage when records exist.
- **SC-004**: Pipeline reconstruction correctly identifies the current agent in all scenarios, including when the board status disagrees with tracking data — 100% accuracy in current-agent determination.
- **SC-005**: All existing pipeline flows (where copilot-review IS the current agent) continue to work identically — 0 regressions in normal copilot-review completion.
- **SC-006**: Non-pipeline-tracked issues continue to have their status moved to "In Review" by webhooks — 100% backward compatibility for non-pipeline issues.

## Assumptions

- The pipeline object reliably tracks which agent is currently active and exposes a `current_agent` property.
- The existing `_pipeline_allows_copilot_review_request()` guard in the completion module is sufficient for guarding review requests; only the completion-detection side needs additional guards.
- The existing HTML comment fallback for timestamp recovery remains available as a last resort, but is unreliable and should not be the primary recovery mechanism.
- Backward compatibility with non-pipeline-tracked issues is required — the guards only apply when a pipeline is present.
- The scope of this fix excludes: refactoring the polling loop order, changing confirmation delay timing, and modifying the pipeline advancement function (which is already correct once called with the right agent).
- Durable storage for timestamps uses the same storage mechanism as other persistent pipeline data (the existing migrations infrastructure).
