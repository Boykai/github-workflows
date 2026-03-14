# Feature Specification: Group-Aware Pipeline Execution & Tracking Table

**Feature Branch**: `039-group-pipeline-execution`  
**Created**: 2026-03-13  
**Status**: Draft  
**Input**: User description: "Plan: Group-Aware Pipeline Execution & Tracking Table"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Sequential Group Execution (Priority: P1)

A project administrator configures a pipeline stage with a single execution group set to "sequential" mode containing multiple agents. When an issue enters that stage, agents within the group run one after another in the configured order — just as they did before groups existed, but now the group boundary is preserved and visible in the tracking table.

**Why this priority**: This is the foundational behavior. Without correct sequential group execution, no other group features work. It also ensures full backward compatibility with existing pipelines that have no explicit groups.

**Independent Test**: Can be fully tested by creating a pipeline with one sequential group of 2–3 agents, moving an issue through that stage, and verifying agents execute in order with the tracking table reflecting group membership.

**Acceptance Scenarios**:

1. **Given** a pipeline stage has one group in sequential mode with agents A → B → C, **When** an issue enters the stage, **Then** agent A is assigned first; upon completion agent B is assigned; upon completion agent C is assigned.
2. **Given** a pipeline stage has one group in sequential mode, **When** the tracking table is rendered in the GitHub Issue body, **Then** each row displays the group label (e.g., "G1 (series)") in a dedicated Group column.
3. **Given** a legacy pipeline with no explicit groups, **When** an issue enters any stage, **Then** agents execute sequentially as before and the tracking table renders correctly without a Group column (backward-compatible fallback).

---

### User Story 2 - Parallel Group Execution (Priority: P1)

A project administrator configures a pipeline stage with an execution group set to "parallel" mode containing multiple agents. When an issue enters that stage, all agents in the parallel group are assigned simultaneously (with a short stagger between assignments for rate-limit safety). The stage does not advance until every agent in the parallel group has completed.

**Why this priority**: Parallel execution is the primary new capability this feature unlocks. Users already configure parallel groups in the UI, but the backend ignores them — delivering this closes the feature gap.

**Independent Test**: Can be fully tested by creating a pipeline with one parallel group of 3 agents, moving an issue into that stage, and verifying all 3 agents are assigned concurrently and the stage advances only after all have posted "Done!".

**Acceptance Scenarios**:

1. **Given** a pipeline stage has one group in parallel mode with agents X, Y, Z, **When** an issue enters the stage, **Then** all three agents are assigned within seconds of each other.
2. **Given** agents X and Z have completed but agent Y is still active, **When** the system checks for stage completion, **Then** the stage remains in progress and does not advance.
3. **Given** all agents in a parallel group have completed, **When** the system evaluates next steps, **Then** execution moves to the next group or the next status in the pipeline.
4. **Given** a parallel group's agents are assigned, **When** the tracking table is rendered, **Then** each agent row shows "G1 (parallel)" in the Group column and individual agent states are tracked independently.

---

### User Story 3 - Mixed Group Ordering Within a Stage (Priority: P2)

A project administrator configures a pipeline stage with multiple groups — for example, Group 1 (sequential: agents A, B) followed by Group 2 (parallel: agents C, D, E). Groups execute in their configured order: Group 1 completes entirely before Group 2 begins.

**Why this priority**: Mixed groups within a single stage represent the full power of the execution group model. This builds directly on P1 stories and enables sophisticated multi-agent workflows.

**Independent Test**: Can be fully tested by creating a stage with two groups (one sequential, one parallel), running an issue through it, and verifying Group 1 agents finish sequentially before Group 2 agents start in parallel.

**Acceptance Scenarios**:

1. **Given** a stage has Group 1 (sequential: A, B) and Group 2 (parallel: C, D, E), **When** an issue enters the stage, **Then** agent A is assigned first.
2. **Given** Group 1 agent B has completed, **When** the system advances the pipeline, **Then** Group 2 agents C, D, E are all assigned simultaneously.
3. **Given** all groups in a stage are complete, **When** the system evaluates next steps, **Then** the issue transitions to the next pipeline status.

---

### User Story 4 - Tracking Table Displays Group Information (Priority: P2)

When viewing a GitHub Issue that has an agent pipeline, the tracking table in the issue body shows a "Group" column indicating which execution group each agent belongs to and the group's execution mode (e.g., "G1 (series)", "G2 (parallel)"). This allows anyone inspecting the issue to understand the intended execution structure at a glance.

**Why this priority**: Visibility into group membership is essential for debugging and monitoring. Without it, users cannot verify that their pipeline configuration is being honored.

**Independent Test**: Can be fully tested by triggering a pipeline on an issue and inspecting the rendered markdown table in the issue body for the Group column.

**Acceptance Scenarios**:

1. **Given** a pipeline with groups is assigned to an issue, **When** the tracking table is rendered, **Then** a "Group" column appears between the "Status" and "Agent" columns.
2. **Given** a stage has two groups, **When** the tracking table is rendered, **Then** agents in Group 1 display "G1 (series)" or "G1 (parallel)" and agents in Group 2 display "G2 (series)" or "G2 (parallel)".
3. **Given** an issue has a tracking table with the Group column, **When** the system re-parses the table (e.g., after polling), **Then** group information is correctly preserved and not lost on re-render.

---

### User Story 5 - Backward Compatibility with Legacy Pipelines (Priority: P2)

Existing pipelines that do not use execution groups continue to work exactly as before. Issues already tracked with the old 5-column or 4-column table format are parsed correctly. New pipelines without explicit groups fall back to a single implicit sequential group.

**Why this priority**: The system must not break for existing users. Backward compatibility ensures a safe, incremental rollout.

**Independent Test**: Can be fully tested by running existing pipeline configurations (without groups) and verifying agents execute sequentially and the tracking table uses the legacy format.

**Acceptance Scenarios**:

1. **Given** a pipeline configuration with no execution groups defined, **When** an issue enters a stage, **Then** agents run sequentially as a single implicit group and no Group column appears in the tracking table.
2. **Given** a GitHub Issue body contains a tracking table in the old 5-column format, **When** the system parses it, **Then** all agent steps are correctly reconstructed without errors.
3. **Given** a GitHub Issue body contains a tracking table in the legacy 4-column format, **When** the system parses it, **Then** all agent steps are correctly reconstructed with models defaulting to empty.

---

### User Story 6 - Parallel Group Partial Failure Handling (Priority: P3)

When an agent in a parallel group fails, the remaining agents in that group continue executing. The group is marked as partially failed, and the system records which agents failed for later inspection or retry.

**Why this priority**: Failure resilience is important for production reliability but is less critical than delivering the core parallel execution capability.

**Independent Test**: Can be fully tested by simulating one agent failure in a parallel group and verifying remaining agents still complete and the group status reflects partial failure.

**Acceptance Scenarios**:

1. **Given** a parallel group with agents X, Y, Z where agent Y fails, **When** the system evaluates group completion, **Then** agents X and Z continue executing independently.
2. **Given** a parallel group has partially failed (some agents completed, some failed), **When** the tracking table is rendered, **Then** each agent's individual state accurately reflects its outcome (Done, Failed, etc.).
3. **Given** a parallel group has partially failed, **When** all remaining agents have completed, **Then** the system advances to the next group or status and records the failure for potential retry.

---

### Edge Cases

- What happens when a stage has zero groups defined? The system falls back to the legacy flat agent list behavior.
- What happens when a group has zero agents? The system skips the empty group and advances to the next group.
- What happens when all agents in a parallel group fail? The group is marked fully failed; pipeline advancement handles this as a failed stage transition.
- What happens when groups are reordered in the UI after a pipeline has already started? In-flight pipelines use the group configuration captured at pipeline start time; mid-execution changes do not affect running issues.
- What happens when the system reconstructs pipeline state from an issue that was partially processed under the old format? The system uses the legacy flat fallback — no group information is inferred for issues that started without groups.
- What happens when multiple stages each have multiple groups? Groups are numbered per-stage (G1, G2, …), resetting for each status. Cross-stage group numbering does not conflict.
- What happens when rate limiting occurs during parallel agent assignment? Agents are assigned with a configurable stagger delay between each assignment to avoid triggering rate limits. If a rate-limit error is returned, the system retries the assignment after a backoff period.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST preserve execution group information when converting pipeline configuration to workflow configuration, including group identity, order, execution mode, and agent membership.
- **FR-002**: System MUST execute agents within a sequential group one at a time in their configured order, waiting for each agent to complete before assigning the next.
- **FR-003**: System MUST execute all agents within a parallel group simultaneously, with a short stagger delay between assignments to respect rate limits.
- **FR-004**: System MUST execute groups within a stage in their configured order — a subsequent group begins only after the preceding group has fully completed.
- **FR-005**: System MUST track each agent's completion status independently within a parallel group and only consider the group complete when all agents have finished (completed or failed).
- **FR-006**: System MUST render a "Group" column in the tracking table when group information is present, displaying labels such as "G1 (series)" or "G2 (parallel)".
- **FR-007**: System MUST parse tracking tables in three formats: 6-column (with Group), 5-column (current), and 4-column (legacy) — selecting the appropriate parser automatically based on table structure.
- **FR-008**: System MUST preserve group labels when re-rendering the tracking table after state updates (e.g., marking an agent as Done).
- **FR-009**: System MUST fall back to legacy sequential behavior when no execution groups are defined in the workflow configuration, ensuring full backward compatibility.
- **FR-010**: System MUST number groups per-stage (G1, G2, …) independently for each status, not globally across the pipeline.
- **FR-011**: System MUST reconstruct group-aware pipeline state from the tracking table during polling, using group column data when present and falling back to flat behavior for legacy issues.
- **FR-012**: System MUST allow remaining agents in a parallel group to continue executing when one agent fails, marking the group as partially failed upon completion.
- **FR-013**: System MUST record failed agents within a parallel group for visibility and potential retry.
- **FR-014**: System MUST skip empty groups (groups with zero agents) and advance to the next group without error.

### Key Entities

- **Execution Group Mapping**: Represents a group of agents within a pipeline stage that share an execution mode (sequential or parallel). Attributes include group identity, display order within the stage, execution mode, and an ordered list of agent assignments.
- **Pipeline Group Info**: Runtime representation of a group during pipeline execution. Tracks group identity, execution mode, the list of agents, and per-agent completion status for parallel groups.
- **Agent Step (extended)**: A single row in the tracking table, now extended with group label, group order, and group execution mode to support rendering and reconstruction of group information.
- **Pipeline State (extended)**: Runtime state of a pipeline for a specific issue, now extended with a list of groups for the current status, the index of the currently executing group, and the index of the current agent within that group.

### Assumptions

- The frontend already fully supports ExecutionGroup configuration (creating, editing, toggling series/parallel). No frontend changes are required.
- The stagger delay between parallel agent assignments (initially 2 seconds) is sufficient to avoid GitHub API rate limits under normal usage. No hard cap on parallel agents is imposed unless abuse is observed.
- Pipeline configurations are captured at execution start time. Changes to pipeline configuration mid-execution do not affect in-flight issues.
- Group numbering (G1, G2, …) is purely a display convention for the tracking table and does not affect execution logic.
- The tracking table format change (adding a Group column) only applies to new issues processed with group-aware pipelines. Existing issues retain their current format and are parsed using legacy fallback patterns.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Agents in a parallel group all begin execution within the configured stagger window (e.g., within 10 seconds for a 5-agent group with 2-second stagger), rather than waiting for each previous agent to finish.
- **SC-002**: A pipeline with mixed groups (e.g., sequential Group 1 with 2 agents, parallel Group 2 with 3 agents) completes in less time than if all 5 agents ran sequentially — specifically, Group 2 wall-clock time approximates that of its slowest agent rather than the sum of all agents.
- **SC-003**: 100% of existing pipelines (those without explicit execution groups) continue to function identically after the change, with no regressions in agent execution order or tracking table rendering.
- **SC-004**: The tracking table in the GitHub Issue body accurately reflects group membership and execution mode for every agent, verified by manual inspection of at least one pipeline run with mixed groups.
- **SC-005**: Tracking tables in all three supported formats (6-column, 5-column, 4-column) are correctly parsed without errors, verified by unit tests covering each format.
- **SC-006**: When one agent in a parallel group fails, remaining agents complete successfully and their final states are accurately reflected in the tracking table.
- **SC-007**: Pipeline state is correctly reconstructed from the tracking table during polling recovery, including group information for new-format tables and flat fallback for legacy tables.
