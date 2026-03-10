# Feature Specification: Parallel Agent Layout in Pipelines

**Feature Branch**: `033-parallel-agent-layout`
**Created**: 2026-03-10
**Status**: Draft
**Input**: User description: "Pipelines: Support Side-by-Side (Parallel) Agent Layout When Creating or Editing Agent Pipelines"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Add Parallel Agents to a Pipeline Stage (Priority: P1)

As a pipeline builder, I want to place two or more Agents side-by-side within a single pipeline stage so that those Agents are designated to execute in parallel. Currently, the Pipelines page only supports stacking Agents vertically (sequential/series execution). I need an affordance — such as an "Add Parallel Agent" button or a drag-and-drop target on the side of an existing Agent card — to group Agents horizontally within the same stage during both Create and Edit pipeline workflows.

**Why this priority**: This is the core interaction that enables the entire feature. Without the ability to place Agents side-by-side, no parallel execution can be configured. Every other story depends on this capability existing.

**Independent Test**: Can be fully tested by opening the Create Pipeline page, adding two Agents into the same stage using the parallel affordance, saving the pipeline, and confirming both Agents appear side-by-side within a visually grouped container.

**Acceptance Scenarios**:

1. **Given** a user is on the Create Pipeline page with at least one Agent already placed, **When** the user activates the "Add Parallel Agent" affordance on that Agent's card, **Then** a second Agent slot appears side-by-side (horizontally) within the same stage container.
2. **Given** a user is on the Edit Pipeline page viewing an existing sequential pipeline, **When** the user drags an Agent onto the side of another Agent (not between stages), **Then** both Agents are grouped into a single parallel stage.
3. **Given** a parallel stage already contains two Agents, **When** the user adds a third Agent to that stage, **Then** all three Agents appear side-by-side within the same stage container and the layout remains readable.
4. **Given** a user has configured a parallel stage with multiple Agents, **When** the user saves the pipeline, **Then** the parallel grouping is persisted and visible when the pipeline is reopened for editing.

---

### User Story 2 - Parallel Agents Execute Simultaneously at Runtime (Priority: P1)

As a pipeline builder, I want all Agents within a parallel stage to trigger and run at the same time when the pipeline reaches that stage. The pipeline must not advance to the next stage until every Agent in the current parallel stage has completed successfully. This enables me to run independent tasks concurrently, reducing overall pipeline execution time.

**Why this priority**: Parallel execution is the behavioral contract that gives the side-by-side layout its meaning. Without concurrent dispatch and a completion barrier, the visual grouping would be cosmetic only and deliver no value.

**Independent Test**: Can be fully tested by creating a pipeline with one parallel stage containing two Agents, running the pipeline, and verifying (via timestamps or execution logs) that both Agents started at the same time and the next stage did not begin until both completed.

**Acceptance Scenarios**:

1. **Given** a pipeline with a parallel stage containing Agents A and B followed by a sequential Agent C, **When** the pipeline executes and reaches the parallel stage, **Then** Agents A and B both start at the same time.
2. **Given** Agent A in a parallel stage completes in 5 seconds and Agent B completes in 30 seconds, **When** the pipeline is running, **Then** Agent C does not start until Agent B also completes (after 30 seconds).
3. **Given** a pipeline with mixed stages — sequential Stage 1, parallel Stage 2 (Agents X and Y), sequential Stage 3 — **When** the pipeline runs end-to-end, **Then** Stage 1 completes before Stage 2 starts, X and Y run concurrently in Stage 2, and Stage 3 starts only after both X and Y complete.

---

### User Story 3 - Visual Differentiation of Parallel vs. Sequential Stages (Priority: P2)

As a pipeline builder, I want parallel stages to be visually distinct from sequential stages on the pipeline canvas so I can immediately understand the execution flow at a glance. Parallel Agents should appear inside a shared container with a clear label or icon indicating they run in parallel, and connector lines should only appear between stage groups — not between parallel siblings.

**Why this priority**: Clear visual communication prevents user confusion and design errors. Without differentiation, users cannot verify at a glance whether Agents are parallel or sequential, leading to misconfigured pipelines and unexpected behavior.

**Independent Test**: Can be fully tested by creating a pipeline with both parallel and sequential stages, then visually inspecting the canvas to confirm parallel stages have a distinct container, label/icon, and correct connector placement.

**Acceptance Scenarios**:

1. **Given** a pipeline canvas with a parallel stage containing Agents A and B, **When** the user views the canvas, **Then** Agents A and B are enclosed in a shared visual container with a "Runs in Parallel" label or a parallel-execution icon (e.g., split-lane or two-arrow icon).
2. **Given** a pipeline with sequential Agent 1, parallel stage (Agents 2a, 2b), and sequential Agent 3, **When** the user views the canvas, **Then** vertical connector lines appear between Stage 1 and the parallel container and between the parallel container and Stage 3 — but no connectors appear between Agents 2a and 2b.
3. **Given** a user hovers over an Agent within a parallel stage, **When** the tooltip appears, **Then** it reads "These agents run at the same time" (or equivalent).
4. **Given** a user hovers over an Agent in a sequential stage, **When** the tooltip appears, **Then** it reads "This agent runs after the previous completes" (or equivalent).

---

### User Story 4 - Parallel Stage Failure Handling (Priority: P2)

As a pipeline builder, I want clear and predictable behavior when one or more Agents within a parallel stage fail. The pipeline should halt, the stage should be marked as failed, and I should be able to see which specific Agent(s) within the parallel group failed so I can diagnose and fix the issue.

**Why this priority**: Without defined failure behavior, parallel execution introduces ambiguity and risk. Users need confidence that failures are surfaced clearly and that the pipeline does not silently continue past a broken stage.

**Independent Test**: Can be fully tested by creating a pipeline with a parallel stage where one Agent is configured to fail, running the pipeline, and verifying the stage shows a failed state with the specific failing Agent identified.

**Acceptance Scenarios**:

1. **Given** a parallel stage with Agents A and B where Agent A fails, **When** the pipeline is running, **Then** the pipeline halts after the parallel stage, the stage is marked as failed, and Agent A is visually indicated as the failed Agent.
2. **Given** a parallel stage with Agents A, B, and C where Agent B fails but A and C succeed, **When** the user views the pipeline run results, **Then** Agent B shows a failed status, Agents A and C show completed status, and the overall stage shows failed.
3. **Given** a parallel stage where all Agents complete successfully, **When** the pipeline is running, **Then** the stage is marked as completed and the pipeline advances to the next stage.

---

### User Story 5 - Remove Agent from Parallel Stage (Priority: P3)

As a pipeline builder, I want to remove an Agent from a parallel stage so it reverts to its own sequential stage (or is deleted), without disrupting the remaining Agents in the parallel group or the rest of the pipeline.

**Why this priority**: Users need the ability to undo parallel groupings and restructure pipelines flexibly. This is a secondary editing capability that enhances usability but is not required for the core parallel workflow.

**Independent Test**: Can be fully tested by creating a parallel stage with three Agents, removing one, and confirming the remaining two stay grouped in the parallel stage while the pipeline structure remains intact.

**Acceptance Scenarios**:

1. **Given** a parallel stage containing Agents A, B, and C, **When** the user removes Agent B from the parallel group, **Then** Agents A and C remain in the parallel stage and Agent B is either moved to its own sequential position or deleted.
2. **Given** a parallel stage containing exactly two Agents, **When** the user removes one Agent, **Then** the remaining Agent reverts to a standard sequential stage (the parallel container is dissolved).

---

### User Story 6 - Reorder Agents and Stages via Drag-and-Drop (Priority: P3)

As a pipeline builder, I want to reorder Agents within a parallel stage (changing their left-to-right position) and reorder entire stages (parallel or sequential) within the pipeline via drag-and-drop so I can easily restructure my pipeline without recreating stages from scratch.

**Why this priority**: Reordering is a convenience feature that improves the editing experience. The core feature works without it, but it significantly reduces friction for users building complex pipelines.

**Independent Test**: Can be fully tested by creating a pipeline with multiple stages (both parallel and sequential), dragging Agents to reorder within a parallel stage, and dragging stages to reorder the pipeline sequence.

**Acceptance Scenarios**:

1. **Given** a parallel stage with Agents A, B, and C in that order, **When** the user drags Agent C to the left of Agent A, **Then** the order becomes C, A, B within the same parallel stage.
2. **Given** a pipeline with Stage 1 (sequential), Stage 2 (parallel), and Stage 3 (sequential), **When** the user drags Stage 2 to the position after Stage 3, **Then** the pipeline order becomes Stage 1, Stage 3, Stage 2.

---

### User Story 7 - Real-Time Status Indicators for Parallel Agents (Priority: P3)

As a pipeline builder monitoring a running pipeline, I want to see a visual status indicator for each Agent within a parallel stage showing whether it is running, completed, or failed — updated in real time — so I can track progress and identify bottlenecks or failures immediately.

**Why this priority**: Real-time feedback during execution enhances observability but is not required for the basic parallel execution functionality. It becomes important once users begin running parallel pipelines in production.

**Independent Test**: Can be fully tested by running a pipeline with a parallel stage, observing the canvas during execution, and verifying each Agent shows its current status (running spinner, completed checkmark, failed icon) as it progresses.

**Acceptance Scenarios**:

1. **Given** a parallel stage with Agents A and B is currently executing, **When** the user views the pipeline run, **Then** both Agents show a "running" indicator (e.g., spinner or animated icon).
2. **Given** Agent A completes while Agent B is still running, **When** the user views the pipeline run, **Then** Agent A shows a "completed" indicator and Agent B continues showing "running."
3. **Given** Agent B fails, **When** the user views the pipeline run, **Then** Agent B shows a "failed" indicator with a visual cue (e.g., red icon or border).

---

### Edge Cases

- What happens when a parallel stage contains only one Agent? It should behave identically to a sequential stage (no visual parallel container shown).
- What happens when a user attempts to add more than the maximum supported number of parallel Agents? The system should gracefully handle layouts with 2–4+ parallel Agents while remaining readable; if a hard limit is enforced, the user should receive a clear message.
- How does the system handle a parallel Agent that times out or hangs indefinitely? The pipeline should apply any configured timeout policy per-Agent, mark the timed-out Agent as failed, and halt the stage.
- What happens to existing pipelines that were created before parallel support? They should continue to function as sequential-only pipelines with no changes required (backward compatibility).
- What happens when a user saves a pipeline with an empty parallel stage (all Agents removed)? The empty stage should be automatically removed or the user should be prompted before saving.
- How does the system behave if two parallel Agents attempt to modify the same shared resource? This is outside the scope of this feature; Agent isolation and resource contention are governed by each Agent's own configuration.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST allow users to add two or more Agents into the same pipeline stage so they are designated as parallel (side-by-side) during both Create and Edit pipeline workflows.
- **FR-002**: System MUST execute all Agents within a parallel stage simultaneously at runtime, triggering them at the same time regardless of individual Agent duration.
- **FR-003**: System MUST NOT advance the pipeline to the next stage or Agent until every Agent within the current parallel stage has completed successfully.
- **FR-004**: System MUST visually differentiate parallel stage groups from sequential (stacked) stages on the pipeline canvas using a shared container, distinct iconography, and/or labeling (e.g., "Runs in Parallel" label or split-lane icon).
- **FR-005**: System MUST preserve existing sequential (stacked/series) execution behavior so that Agents not grouped in a parallel stage continue to run in order, one after another.
- **FR-006**: System MUST handle partial failure within a parallel stage by halting the pipeline at that stage, marking the stage as failed, and identifying which specific Agent(s) failed.
- **FR-007**: System MUST persist the parallel vs. sequential layout configuration as part of the pipeline definition when saving a Create or Edit operation.
- **FR-008**: System MUST maintain backward compatibility — existing pipelines created before this feature must continue to function as sequential-only with no modification required.
- **FR-009**: System SHOULD allow users to remove an Agent from a parallel stage, reverting the group to sequential if only one Agent remains, without disrupting other Agents in the pipeline.
- **FR-010**: System SHOULD support reordering of parallel Agents within a stage and reordering of stages (parallel or sequential) via drag-and-drop on the pipeline canvas.
- **FR-011**: System SHOULD display a real-time visual status indicator per Agent during pipeline execution, showing running, completed, or failed states.
- **FR-012**: System SHOULD display connector lines only between stage groups (not between parallel sibling Agents) to clearly communicate the execution flow.
- **FR-013**: System SHOULD show contextual tooltips differentiating parallel execution ("These agents run at the same time") from sequential execution ("This agent runs after the previous completes") on hover.

### Key Entities

- **Pipeline**: A saved workflow definition consisting of an ordered sequence of stages. Contains metadata (name, description, project association) and the ordered list of stages.
- **Stage**: A unit within a pipeline that contains one or more Agents. A stage with one Agent represents sequential execution. A stage with multiple Agents represents parallel execution. Stages execute in order within the pipeline.
- **Agent**: An individual task executor within a stage. Each Agent has its own configuration and executes independently. Within a parallel stage, all Agents start simultaneously.
- **Pipeline Run**: An instance of a pipeline being executed. Tracks the status of each stage and each Agent within each stage, including start time, end time, and outcome (running, completed, failed).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can create a pipeline with at least one parallel stage containing 2+ Agents and save it successfully within 2 minutes of starting the Create workflow.
- **SC-002**: All Agents within a parallel stage begin execution within 2 seconds of each other when the pipeline run reaches that stage.
- **SC-003**: The pipeline does not advance to the next stage until 100% of Agents in the current parallel stage have completed.
- **SC-004**: Users can visually distinguish parallel stages from sequential stages on the pipeline canvas without needing to click or hover (clear at a glance).
- **SC-005**: Existing sequential-only pipelines continue to execute correctly with no user intervention after the feature is deployed (zero regressions).
- **SC-006**: When an Agent fails within a parallel stage, the specific failing Agent is identifiable within the pipeline run view within 5 seconds of the failure occurring.
- **SC-007**: The pipeline canvas remains readable and usable with up to 4 parallel Agents in a single stage across common screen sizes (1280px width and above).
- **SC-008**: 90% of users can successfully configure a parallel stage on their first attempt without consulting documentation.

## Assumptions

- The current pipeline data model uses a flat ordered list of Agents. This feature will require evolving to a stage-based structure where each stage contains an ordered array of Agents.
- The existing drag-and-drop interactions on the pipeline canvas will be extended (not replaced) to support the new parallel grouping gesture.
- Agent isolation is already enforced — parallel Agents do not share state or resources, and resource contention is outside the scope of this feature.
- The pipeline execution engine can support concurrent Agent dispatch (e.g., via async concurrency primitives available in the runtime environment).
- There is no hard upper limit on the number of Agents in a parallel stage, but the UI is optimized for 2–4 Agents and should remain functional beyond that range.
- Timeout and retry policies for individual Agents are managed at the Agent level and are unaffected by whether the Agent runs in a parallel or sequential stage.
