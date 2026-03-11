# Feature Specification: GitHub Label-Based Agent Pipeline State Tracking

**Feature Branch**: `034-label-pipeline-state`  
**Created**: 2026-03-11  
**Status**: Draft  
**Input**: User description: "GitHub Label-Based Agent Pipeline State Tracking"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Instant Pipeline State Recovery After Restart (Priority: P1)

When the Solune backend restarts or loses its in-memory cache, the system currently reconstructs pipeline state by parsing Markdown tracking tables from issue bodies — requiring multiple GitHub API calls per stalled issue (up to 15–25 calls). With label-based state tracking, the system reads `pipeline:<config>` and `agent:<slug>` labels from the already-fetched GraphQL board query to instantly rebuild pipeline state with zero additional API calls.

**Why this priority**: This is the highest-value change. Recovery from restarts and stalled issues is the most expensive operation in the current system. Labels eliminate the reconstruction cost entirely for the common case.

**Independent Test**: Can be tested by simulating a cache miss on a parent issue that has both `pipeline:speckit-full` and `agent:speckit.plan` labels. The system should build a valid `PipelineState` from labels alone, without fetching the issue body or sub-issues.

**Acceptance Scenarios**:

1. **Given** a parent issue with `pipeline:speckit-full` and `agent:speckit.plan` labels and an empty in-memory cache, **When** the polling loop encounters this issue, **Then** the system builds a correct `PipelineState` using only the label data and the known pipeline configuration — without making any additional API calls beyond the board query.
2. **Given** a parent issue with `pipeline:speckit-full` and `agent:speckit.plan` labels, **When** the fast-path reconstruction produces a `PipelineState`, **Then** the resulting state matches what would have been produced by the existing Markdown-table-based reconstruction (same current agent index, same pipeline config).
3. **Given** a parent issue missing the `pipeline:<config>` label (e.g., created before this feature), **When** the polling loop encounters this issue, **Then** the system falls through to the existing cache → tracking table → reconstruction chain with no errors or behavioral change.

---

### User Story 2 - Automatic Label Application During Pipeline Lifecycle (Priority: P1)

As issues move through the agent pipeline, the system automatically applies and swaps labels to reflect the current state. When a parent issue is created with a pipeline configuration, it receives a `pipeline:<config>` label. When agents are assigned, the `agent:<slug>` label is swapped atomically. When an agent's sub-issue becomes active, it receives the `active` label (removed from the previous sub-issue). This happens transparently alongside existing tracking table updates.

**Why this priority**: Without label writes, the read-path (Story 1) has no labels to consume. This is a co-equal prerequisite.

**Independent Test**: Can be tested by running a single agent assignment and verifying the correct labels are applied via the existing `update_issue_state()` API.

**Acceptance Scenarios**:

1. **Given** a new parent issue is being created with pipeline config `speckit-full`, **When** `create_issue_from_recommendation()` runs, **Then** the issue is created with the `pipeline:speckit-full` label included in its initial label set.
2. **Given** a parent issue currently has `agent:speckit.specify` label and the pipeline transitions to the next agent, **When** `assign_agent_for_status()` runs, **Then** the old `agent:speckit.specify` label is removed and `agent:speckit.plan` label is added in a single `update_issue_state()` call.
3. **Given** an agent sub-issue for `speckit.specify` has the `active` label, **When** the pipeline transitions to `speckit.plan`, **Then** the `active` label is removed from the `speckit.specify` sub-issue and added to the `speckit.plan` sub-issue.
4. **Given** a parent issue has an `agent:speckit.implement` label, **When** the pipeline completes (all agents done), **Then** the `agent:*` label is removed from the parent issue.

---

### User Story 3 - Stalled Issue Detection and Recovery via Labels (Priority: P2)

When the recovery system detects a stalled pipeline (an agent that has been idle beyond the grace period), the system applies a `stalled` label to the parent issue for instant visual identification. When the issue is successfully re-assigned, the `stalled` label is removed. Additionally, recovery can use the presence of `agent:<slug>` labels to skip expensive reconciliation when the pipeline is demonstrably active.

**Why this priority**: Stalled detection is a secondary benefit — it improves recovery efficiency but the pipeline still functions without it.

**Independent Test**: Can be tested by simulating a stalled pipeline scenario, verifying the `stalled` label is applied, then re-assigning the agent and verifying the label is removed.

**Acceptance Scenarios**:

1. **Given** a parent issue with `agent:speckit.plan` label has been idle beyond the configured grace period, **When** `recover_stalled_issues()` runs, **Then** the `stalled` label is added to the parent issue.
2. **Given** a parent issue with the `stalled` label, **When** the agent is successfully re-assigned, **Then** the `stalled` label is removed from the issue.
3. **Given** a parent issue with a valid `agent:<slug>` label and the agent is within the grace period, **When** recovery runs, **Then** the system skips expensive reconciliation for this issue.

---

### User Story 4 - Label-Enriched Board Display (Priority: P2)

Users viewing the project board can instantly see which agent is active on each pipeline issue, which pipeline configuration is in use, and whether any issues are stalled — all derived from labels that are already fetched by the board's GraphQL query. This provides at-a-glance status without clicking into individual issues.

**Why this priority**: Enhances user experience but is not essential for pipeline function. Frontend changes can proceed in parallel after labels are being written.

**Independent Test**: Can be tested by loading the project board with issues that have pipeline labels and verifying the UI renders badges and indicators correctly.

**Acceptance Scenarios**:

1. **Given** a parent issue on the board has `agent:speckit.plan` label, **When** the board renders, **Then** an active agent badge showing "speckit.plan" appears on the issue card.
2. **Given** a parent issue has `pipeline:speckit-full` label, **When** the board renders, **Then** a pipeline config tag showing "speckit-full" appears on the issue card.
3. **Given** a parent issue has `stalled` label, **When** the board renders, **Then** a visual warning indicator (distinct from normal status) appears on the issue card.
4. **Given** the board toolbar, **When** a user selects a pipeline config filter, **Then** only issues with the matching `pipeline:<config>` label are displayed.

---

### User Story 5 - Simplified Recovery with Label-Assisted Validation (Priority: P3)

The recovery subsystem uses labels to reduce API call overhead during self-healing and reconciliation. When `pipeline:<config>` label is present, the system reads the agent list directly from the config (skipping `get_sub_issues()` API call). When `agent:<slug>` is present, reconciliation starts from that agent's index instead of re-checking all agents. A consolidated validation function cross-checks labels against the tracking table and fixes whichever is stale.

**Why this priority**: Optimization of existing recovery paths. The pipeline works without it, but this dramatically reduces API consumption.

**Independent Test**: Can be tested by measuring API call counts during recovery of a stalled issue — comparing the label-assisted path versus the existing full-reconstruction path.

**Acceptance Scenarios**:

1. **Given** a parent issue with `pipeline:speckit-full` label, **When** `_self_heal_tracking_table()` runs, **Then** it reads the agent list from the `speckit-full` config directly without calling `get_sub_issues()`.
2. **Given** a parent issue with `agent:speckit.tasks` label (agent index 3 in the pipeline), **When** `_validate_and_reconcile_tracking_table()` runs, **Then** it only validates agents from index 3 onward (skipping already-completed agents 1 and 2).
3. **Given** a label/tracking-table mismatch (e.g., label says `agent:speckit.plan` but table says `speckit.tasks` is active), **When** `validate_pipeline_labels()` runs, **Then** it determines which source is stale by checking GitHub ground truth (comments, sub-issue state) and corrects the stale source.

---

### Edge Cases

- What happens when a parent issue was created before this feature (no pipeline labels)? The system falls through to the existing reconstruction chain with no behavioral change.
- What happens when labels are manually removed by a user? The system falls through to the existing tracking-table-based flow and re-applies labels on the next pipeline transition.
- What happens when the repository's label limit is approached? The label budget analysis shows worst case 10 labels out of GitHub's 100 per-issue limit — well within bounds.
- What happens when two recovery cycles run concurrently and both try to swap labels? The `update_issue_state()` call is idempotent; the last write wins, and the next polling cycle reconciles any inconsistency.
- What happens when an agent slug contains special characters? Label names must comply with GitHub's label naming rules (max 50 characters, no commas). Agent slugs like `speckit.plan` are valid.
- What happens if label creation fails (e.g., network error)? Label application failures are logged but do not block pipeline progression. The tracking table remains the authoritative source of truth; labels are supplementary.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST define label constants for pipeline state tracking: `PIPELINE_LABEL_PREFIX` ("pipeline:"), `AGENT_LABEL_PREFIX` ("agent:"), `ACTIVE_LABEL` ("active"), and `STALLED_LABEL` ("stalled").
- **FR-002**: System MUST provide parsing utilities to extract pipeline config name from a `pipeline:<config>` label and agent slug from an `agent:<slug>` label.
- **FR-003**: System MUST provide builder utilities to construct label strings from pipeline config names and agent slugs.
- **FR-004**: System MUST pre-create pipeline labels in the repository with distinct colors when a project is connected: `pipeline:*` = blue (#0052cc), `agent:*` = purple (#7057ff), `active` = green (#0e8a16), `stalled` = red (#d73a4a).
- **FR-005**: System MUST apply `pipeline:<config>` label when creating a parent issue with a pipeline configuration. This label is set once and never changed.
- **FR-006**: System MUST apply `agent:<slug>` label when assigning an agent, swapping the previous `agent:*` label for the new one in a single operation.
- **FR-007**: System MUST apply `active` label to the current agent's sub-issue when transitioning agents, removing it from the previous sub-issue.
- **FR-008**: System MUST remove the `agent:*` label from the parent issue when the pipeline completes.
- **FR-009**: System MUST apply `stalled` label when recovery detects a stalled pipeline and remove it upon successful re-assignment.
- **FR-010**: System MUST include labels in the `Task` model so they are available to polling and API consumers.
- **FR-011**: System MUST implement a fast-path in pipeline state reconstruction that builds `PipelineState` from labels when `agent:<slug>` and `pipeline:<config>` labels are both present — requiring zero additional API calls.
- **FR-012**: System MUST fall through to the existing reconstruction chain (cache → tracking table → full reconstruction) when pipeline labels are absent.
- **FR-013**: System MUST expose labels in task/board API responses so the frontend can render pipeline state indicators.
- **FR-014**: System MUST provide a consolidated label validation function that cross-checks labels against the tracking table and corrects the stale source.
- **FR-015**: System MUST maintain the existing tracking table as the detailed audit trail. Labels supplement but do not replace the tracking table.
- **FR-016**: System MUST enforce at most one `agent:` label per parent issue at any time to prevent label bloat.
- **FR-017**: System MUST treat label application failures as non-blocking — pipeline progression continues using the tracking table, and failures are logged as warnings.

### Key Entities *(include if feature involves data)*

- **Pipeline Label**: A GitHub issue label with prefix `pipeline:` followed by the pipeline configuration name (e.g., `pipeline:speckit-full`). Applied once at issue creation. Identifies which pipeline config governs the issue's agent sequence.
- **Agent Label**: A GitHub issue label with prefix `agent:` followed by the agent slug (e.g., `agent:speckit.plan`). Swapped atomically on each agent transition. Represents the currently active agent.
- **Active Label**: A GitHub issue label named `active` applied to the sub-issue corresponding to the currently active agent. Moved from sub-issue to sub-issue on transitions.
- **Stalled Label**: A GitHub issue label named `stalled` applied to parent issues where recovery has detected idle agents beyond the grace period. Removed when the issue is successfully re-assigned.
- **Label Color Scheme**: A predefined set of colors for each label category to enable visual scanning on the GitHub board: blue for pipeline, purple for agent, green for active, red for stalled.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Pipeline state recovery after a restart completes with 3–5 API calls per issue (down from 15–25) when pipeline labels are present.
- **SC-002**: Users can identify the active agent, pipeline config, and stalled status on any board card without clicking into the issue.
- **SC-003**: The existing pipeline lifecycle (Backlog → Ready → In Progress → In Review → Done) continues to function identically for issues created before this feature (no pipeline labels).
- **SC-004**: All label transitions (apply, swap, remove) complete within the existing polling cycle time without adding measurable latency.
- **SC-005**: Label budget stays within 10 labels per parent issue in the worst case, well under GitHub's 100-label limit.
- **SC-006**: 100% of pipeline transitions correctly apply, swap, or remove labels as specified — verified by unit tests covering every transition point.
- **SC-007**: The fast-path reconstruction produces identical `PipelineState` objects compared to full reconstruction for all pipeline configurations.
- **SC-008**: Recovery of stalled issues with labels present skips redundant reconciliation steps, reducing recovery time proportionally to the number of completed agents in the pipeline.

### Assumptions

- The existing `update_issue_state()` function in `issues.py` supports `labels_add` and `labels_remove` parameters and will be used for all label operations (no new GitHub API integration needed).
- The GraphQL board query already fetches `labels(first: 20)` with `id`, `name`, and `color` fields — no changes to the query are needed.
- Pipeline configuration names and agent slugs are stable identifiers that do not change during a pipeline's lifecycle.
- The repository has the `repo` scope required to create and manage labels.
- Label creation at project connect time is preferred over lazy creation to ensure consistent colors and descriptions.
- Parallel agent execution (multiple active agents) is deferred to a future iteration. The current design supports exactly one `agent:` label per parent issue.
- The `stalled` label is informational and does not affect pipeline logic — it is applied and removed for visual identification and fast-path detection only.

### Dependencies

- Existing `update_issue_state()` function in `backend/src/services/github_projects/issues.py` for label add/remove operations.
- Existing GraphQL board query in `backend/src/services/github_projects/board.py` that already fetches labels.
- Existing `PipelineState` model and pipeline configuration system.
- Existing agent tracking table parsing utilities in `backend/src/services/agent_tracking.py`.

### Scope Boundaries

**In scope:**

- Label constants, parsing utilities, and builder functions
- Label write path at all pipeline transition points
- Fast-path pipeline state reconstruction from labels
- Label-assisted recovery and reconciliation optimization
- Task model extension to include labels
- API response enrichment with labels
- Frontend display of agent badge, pipeline tag, stalled indicator, and pipeline config filter

**Out of scope:**

- REST API label-based filtering for board queries (GraphQL project-column filtering remains superior)
- Changes to Done! comment markers or completion detection logic
- Parallel agent execution support (deferred to future iteration)
- Migration of existing issues to add labels retroactively (they gracefully fall through to existing reconstruction)
- Changes to the GraphQL board query itself (labels are already fetched)
