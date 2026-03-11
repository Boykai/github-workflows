# Feature Specification: GitHub Label-Based Agent Pipeline State Tracking

**Feature Branch**: `034-label-pipeline-state`  
**Created**: 2026-03-11  
**Status**: Draft  
**Input**: User description: "Refactor Solune's Agent Pipeline to use GitHub issue labels as durable, instantly-queryable pipeline state markers for zero-additional-API-call state detection"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Instant Pipeline State Detection on Board Load (Priority: P1)

As a system operator monitoring the project board, when the polling service processes board items, the system instantly determines each issue's pipeline state (which agent is active, which pipeline config is in use) by reading labels already present in the board query response — without making any additional API calls.

**Why this priority**: This is the highest-value capability. The current reconstruction/recovery paths are the most expensive operations in the polling loop, requiring 15–25 API calls per stalled issue. Label-based fast-path detection eliminates these calls entirely for the happy path, dramatically reducing API consumption and improving polling throughput.

**Independent Test**: Can be fully tested by creating a parent issue with `pipeline:speckit-full` and `agent:speckit.plan` labels, then verifying the system builds the correct pipeline state object from those labels alone — with zero additional API calls to GitHub.

**Acceptance Scenarios**:

1. **Given** a parent issue on the board has labels `pipeline:speckit-full` and `agent:speckit.plan`, **When** the polling loop processes this issue, **Then** the system builds the correct PipelineState immediately from labels and pipeline config without making any additional API calls.
2. **Given** a parent issue on the board has a `pipeline:speckit-full` label but no `agent:*` label, **When** the polling loop processes this issue, **Then** the system falls through to the existing cache → tracking table → reconstruction chain.
3. **Given** the board query returns issues with labels already included in the response, **When** the system processes each issue, **Then** no separate label-fetching API calls are made — labels come from the already-fetched board data.

---

### User Story 2 - Label Application During Pipeline Lifecycle (Priority: P1)

As a pipeline orchestrator, when issues move through the agent pipeline (creation → agent assignment → transition → completion), the system automatically applies and swaps the correct labels at each stage so that pipeline state is always readable from labels alone.

**Why this priority**: The write path is a prerequisite for the read path (Story 1). Without correctly applied labels, fast-path detection cannot function. This forms the foundation of the entire feature.

**Independent Test**: Can be fully tested by running a pipeline through its full lifecycle (issue creation → first agent → second agent → completion) and verifying the correct labels exist on the parent and sub-issues at each stage.

**Acceptance Scenarios**:

1. **Given** a new pipeline issue is being created, **When** the orchestrator creates the parent issue, **Then** a `pipeline:<config-name>` label is applied alongside existing labels (e.g., `parent`, `ai-generated`).
2. **Given** a pipeline issue exists with `agent:speckit.specify` label, **When** the system transitions to the next agent `speckit.plan`, **Then** the `agent:speckit.specify` label is removed and `agent:speckit.plan` is applied in a single operation.
3. **Given** a pipeline issue transitions to a new agent, **When** the agent's sub-issue becomes active, **Then** the `active` label is applied to the new sub-issue and removed from the previous sub-issue.
4. **Given** a pipeline has completed all agents, **When** pipeline completion is processed, **Then** the `agent:*` label is removed from the parent issue.

---

### User Story 3 - Faster Stalled Issue Recovery (Priority: P2)

As a system operator, when the recovery service detects stalled issues, it uses label presence to quickly determine pipeline state and recover — reducing the API calls needed from approximately 15–25 down to 3–5 per stalled issue.

**Why this priority**: Recovery is a critical reliability function, but it runs less frequently than the main polling loop. The cost savings are significant but secondary to the fast-path detection benefit.

**Independent Test**: Can be fully tested by simulating a stalled issue with correct labels, triggering recovery, and measuring that recovery completes with 3–5 API calls instead of 15–25.

**Acceptance Scenarios**:

1. **Given** a stalled issue has `pipeline:speckit-full` and `agent:speckit.plan` labels, **When** recovery runs, **Then** the system identifies the current agent index from the label and only verifies that agent's status (1 API call) instead of checking all agents sequentially (N API calls).
2. **Given** recovery detects an idle pipeline issue, **When** the issue has no recent agent activity beyond the grace period, **Then** a `stalled` label is applied to the parent issue for visual identification.
3. **Given** a previously stalled issue is successfully re-assigned to an agent, **When** the new agent assignment occurs, **Then** the `stalled` label is removed from the parent issue.

---

### User Story 4 - Stalled Issue Visual Indicator on Board (Priority: P2)

As a project manager viewing the board, I can see at a glance which issues are stalled, which agent is currently active, and which pipeline configuration is running — all from label badges displayed on board cards — so that I can quickly assess pipeline health without opening individual issues.

**Why this priority**: Visual indicators improve the operator experience and make pipeline monitoring more efficient, but the system functions correctly without them.

**Independent Test**: Can be fully tested by loading the board view with issues that have `agent:*`, `pipeline:*`, and `stalled` labels, and verifying the corresponding visual indicators appear on the board cards.

**Acceptance Scenarios**:

1. **Given** a board card represents an issue with `agent:speckit.plan` label, **When** the board renders, **Then** an active agent badge displaying "speckit.plan" is visible on the card.
2. **Given** a board card represents an issue with `pipeline:speckit-full` label, **When** the board renders, **Then** a pipeline configuration tag displaying "speckit-full" is visible on the card.
3. **Given** a board card represents an issue with `stalled` label, **When** the board renders, **Then** a stalled warning indicator is prominently displayed on the card.
4. **Given** a board card represents an issue without any pipeline labels, **When** the board renders, **Then** no pipeline-related badges or indicators are shown.

---

### User Story 5 - Pipeline Config Board Filtering (Priority: P3)

As a project manager, I can filter the board by pipeline configuration (e.g., show only `speckit-full` pipeline issues) so that I can focus on a specific workflow type when monitoring many concurrent pipelines.

**Why this priority**: Filtering is a convenience feature that becomes valuable only when multiple pipeline configurations are in active use. It depends on labels being applied correctly (Stories 1–2).

**Independent Test**: Can be fully tested by loading the board with issues from multiple pipeline configs, selecting a pipeline filter, and verifying only matching issues are displayed.

**Acceptance Scenarios**:

1. **Given** the board contains issues from `speckit-full` and `review-cycle` pipelines, **When** the user selects `speckit-full` from the pipeline config filter, **Then** only issues with the `pipeline:speckit-full` label are displayed.
2. **Given** a pipeline config filter is active, **When** the user clears the filter, **Then** all board issues are displayed regardless of pipeline configuration.

---

### User Story 6 - Label and Tracking Table Consistency Validation (Priority: P3)

As a system operator, the system automatically validates that labels and tracking table entries remain consistent, correcting any drift to maintain reliable state detection across both mechanisms.

**Why this priority**: This is a defensive/reliability feature. Labels and the tracking table should stay in sync, but network failures or partial operations could cause drift. Validation prevents silent state corruption.

**Independent Test**: Can be fully tested by intentionally creating a mismatch (e.g., label says `agent:speckit.plan` but tracking table says `speckit.specify`), triggering validation, and verifying the system detects and resolves the inconsistency.

**Acceptance Scenarios**:

1. **Given** a parent issue has `agent:speckit.plan` label but the tracking table records `speckit.specify` as active, **When** validation runs, **Then** the system resolves the inconsistency by treating the more recent source as authoritative and updating the stale source.
2. **Given** a parent issue has a `pipeline:speckit-full` label and the tracking table agrees, **When** validation runs, **Then** no corrective action is taken.
3. **Given** a parent issue is missing expected pipeline labels but has valid tracking table entries, **When** validation runs, **Then** the missing labels are re-applied based on tracking table data.

---

### Edge Cases

- What happens when a label mutation API call fails mid-swap (old `agent:*` removed but new not yet applied)? The system must handle partial label states gracefully and recover on next polling cycle.
- What happens when an issue exceeds the label budget (approaching GitHub's label limits)? The system must not fail; pipeline labels take priority over cosmetic labels.
- How does the system handle labels that were manually added or removed by a human user? Validation should detect and correct manual modifications.
- What happens when two concurrent processes attempt to swap `agent:*` labels simultaneously? The system must ensure only one `agent:*` label exists after resolution.
- What happens when the `active` label exists on multiple sub-issues simultaneously (e.g., due to a race condition)? The system must detect and correct this to a single active sub-issue.
- How does the system behave when the pipeline configuration referenced by a `pipeline:<config>` label no longer exists? The system should log a warning and fall through to existing recovery mechanisms.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST define label constants for pipeline state tracking: a pipeline config prefix (`pipeline:`), an agent prefix (`agent:`), an active sub-issue marker (`active`), and a stalled issue marker (`stalled`).
- **FR-002**: System MUST provide utility functions to build and parse pipeline labels — constructing labels from pipeline config names and agent slugs, and extracting config names and agent slugs from existing labels.
- **FR-003**: System MUST pre-create pipeline-related labels in the repository with distinct colors: blue for pipeline config labels, purple for agent labels, green for the active label, and red for the stalled label.
- **FR-004**: System MUST apply a `pipeline:<config>` label to parent issues at creation time, and this label MUST never be changed or removed during the issue lifecycle.
- **FR-005**: System MUST apply an `agent:<slug>` label to the parent issue when an agent is assigned, swapping the previous `agent:*` label for the new one in a single operation.
- **FR-006**: System MUST apply the `active` label to the current agent's sub-issue when that agent is assigned, and remove it from the previously active sub-issue.
- **FR-007**: System MUST remove the `agent:*` label from the parent issue when the pipeline completes.
- **FR-008**: System MUST apply the `stalled` label to a parent issue when recovery detects an idle pipeline, and remove it when the issue is successfully re-assigned.
- **FR-009**: System MUST include labels in the Task data model so that labels from the board query are available throughout the polling pipeline.
- **FR-010**: System MUST implement a fast-path state detection layer that builds PipelineState directly from `agent:<slug>` and `pipeline:<config>` labels without additional API calls, falling through to existing mechanisms when labels are absent.
- **FR-011**: System MUST use label-based stalled detection to skip expensive reconciliation when an `agent:*` label is present and the issue is within the grace period.
- **FR-012**: System MUST use the `parent` label to identify parent issues early in polling, replacing title-based parsing where applicable.
- **FR-013**: System MUST provide a consolidated validation function that cross-checks labels against the tracking table and corrects whichever source is stale.
- **FR-014**: System MUST simplify self-healing to use `pipeline:<config>` labels to retrieve agent lists from config directly, avoiding unnecessary sub-issue API calls.
- **FR-015**: System MUST simplify reconciliation to use `agent:<slug>` as a cursor, validating only agents from the current index onward instead of all agents.
- **FR-016**: System MUST simplify reconstruction to use labels for immediate current-agent identification, verifying only the current agent's status instead of iterating through all agents.
- **FR-017**: System MUST expose labels in task and board API responses so the frontend can display pipeline state.
- **FR-018**: The frontend MUST display an active agent badge on board cards by parsing the `agent:*` label.
- **FR-019**: The frontend MUST display a pipeline config tag on board cards by parsing the `pipeline:*` label.
- **FR-020**: The frontend MUST display a stalled warning indicator on board cards when the `stalled` label is present.
- **FR-021**: The frontend MUST provide a pipeline config filter in the board toolbar that filters issues by their `pipeline:*` label.
- **FR-022**: Labels MUST supplement — not replace — the tracking table. The tracking table remains the authoritative audit trail; labels serve as the fast-path primary signal.
- **FR-023**: System MUST maintain at most one `agent:*` label per parent issue at any time.
- **FR-024**: System MUST maintain at most one `active` label across all sub-issues of a given parent issue at any time.

### Key Entities

- **Pipeline Label**: A GitHub issue label with the prefix `pipeline:` followed by the pipeline configuration name (e.g., `pipeline:speckit-full`). Set once at issue creation. Identifies which pipeline configuration governs the issue's agent sequence.
- **Agent Label**: A GitHub issue label with the prefix `agent:` followed by the agent slug (e.g., `agent:speckit.plan`). Swapped atomically on each agent transition. Represents the currently active agent for the parent issue.
- **Active Label**: A GitHub issue label named `active` applied to the sub-issue corresponding to the currently running agent. Moved between sub-issues on agent transitions.
- **Stalled Label**: A GitHub issue label named `stalled` applied to parent issues where recovery has detected idle/stuck pipeline behavior. Removed on successful re-assignment.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Pipeline state detection for issues with valid labels completes with zero additional API calls beyond the board query (down from 1–5 calls per issue in the current approach).
- **SC-002**: Recovery of a stalled issue completes with 3–5 API calls (down from approximately 15–25 calls currently).
- **SC-003**: Self-healing operations that use the `pipeline:<config>` label to retrieve agent lists save 1–2 API calls per self-heal event by skipping sub-issue fetching.
- **SC-004**: Reconciliation operations that use `agent:<slug>` as a cursor save N-1 "Done!" status checks (where N is the number of agents in the pipeline) by validating only from the current agent onward.
- **SC-005**: All label write operations (apply, swap, remove) succeed within the standard response time and are reflected in the next board query.
- **SC-006**: Labels and tracking table remain consistent — validation detects and corrects drift within one polling cycle after the inconsistency occurs.
- **SC-007**: Board users can visually identify the active agent, pipeline configuration, and stalled status on any pipeline issue within 2 seconds of board load — without opening individual issues.
- **SC-008**: Board users can filter issues by pipeline configuration and see only matching results within 1 second of filter selection.
- **SC-009**: The label budget remains within the worst-case budget of 10 pipeline-related labels per issue (parent + ai-generated + pipeline:* + agent:* + blocking + stalled + user labels).
- **SC-010**: All existing pipeline functionality continues to work correctly when labels are absent (graceful degradation) — the system falls through to existing cache → tracking table → reconstruction paths.

## Assumptions

- The board query already fetches labels (via `labels(first: 20)`) and this data is available without schema changes.
- The application already has `repo` scope permissions sufficient to create, apply, and remove labels.
- The existing `update_issue_state()` function supports adding and removing labels.
- Pipeline configuration names and agent slugs are stable identifiers that do not change during a pipeline's lifecycle.
- The label limit per issue will not be a practical constraint given the worst-case budget of approximately 10 labels.
- Pre-creating labels at project connect time is acceptable and does not conflict with existing repository label management.

## Dependencies

- Existing tracking table infrastructure must remain operational as the authoritative audit trail.
- Existing board query already fetches labels — no changes needed to the board data source.
- Existing `update_issue_state()` supports label add/remove operations.
- Pipeline configuration definitions must be accessible to map `pipeline:<config>` labels back to agent sequences.
