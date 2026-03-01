# Feature Specification: Add 'Human' Agent Type to Agent Pipeline

**Feature Branch**: `014-human-agent-pipeline`  
**Created**: 2026-02-28  
**Status**: Draft  
**Input**: User description: "Add 'Human' Agent Type to Agent Pipeline with Sub-Issue Assignment and Completion Detection"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Add a Human Step to a Pipeline (Priority: P1)

As a pipeline creator, I want to add a 'Human' step to any column in an Agent Pipeline so that I can include manual human tasks within my automated workflows.

When building or editing a pipeline, I open the '+ Add Agent' dropdown in any status column and see 'Human' listed alongside the automated agent options. I select 'Human', and a Human step card is added to that column. The card is visually distinct from automated agent cards (e.g., a person icon and a 'Human' label) so I can immediately tell which steps require manual intervention.

**Why this priority**: This is the foundational capability — without the ability to add a Human step, no other functionality in this feature is possible.

**Independent Test**: Can be fully tested by opening any Agent Pipeline, clicking '+ Add Agent' in any column, selecting 'Human', and verifying the card appears with the correct visual styling. Delivers the core value of making Human steps available.

**Acceptance Scenarios**:

1. **Given** a pipeline creator is viewing any Agent Pipeline column, **When** they open the '+ Add Agent' dropdown, **Then** 'Human' appears as a selectable option alongside existing automated agents.
2. **Given** the creator selects 'Human' from the dropdown, **When** the step is added, **Then** a Human step card appears in the column with a person icon and 'Human' label, visually distinct from automated agent cards.
3. **Given** an existing pipeline that was created before this feature, **When** the creator opens the '+ Add Agent' dropdown, **Then** 'Human' is available without any manual reconfiguration.
4. **Given** a newly created pipeline, **When** the creator opens the '+ Add Agent' dropdown, **Then** 'Human' is available by default.

---

### User Story 2 - Human Step Triggers Sub-Issue Creation and Assignment (Priority: P1)

As a pipeline creator, I want the system to automatically create a GitHub Sub Issue for the Human step when my pipeline is triggered, assigned to the person who created the parent issue, so that the human task is tracked and the right person is notified.

When a GitHub Issue containing a Human step in its pipeline is triggered, the system creates a Sub Issue for the Human step using the same mechanism it uses for automated agent steps. The Sub Issue is automatically assigned to the user who created the parent GitHub Issue.

**Why this priority**: This is equally critical as Story 1 — it connects the Human step to the existing issue tracking infrastructure, making the human task actionable and trackable.

**Independent Test**: Can be fully tested by creating a pipeline with a Human step, triggering it via a GitHub Issue, and verifying that a Sub Issue is created and assigned to the issue creator.

**Acceptance Scenarios**:

1. **Given** a pipeline with a Human step is triggered by a GitHub Issue, **When** the pipeline reaches the Human step, **Then** a Sub Issue is created using the same creation mechanism used for automated agent steps.
2. **Given** the Sub Issue is created for the Human step, **When** the Sub Issue appears, **Then** it is automatically assigned to the user who created the parent GitHub Issue.
3. **Given** the issue creator's identity cannot be resolved, **When** the system attempts to assign the Sub Issue, **Then** a clear error message is surfaced and the pipeline does not silently fail.

---

### User Story 3 - Human Step Completion Advances the Pipeline (Priority: P1)

As a pipeline creator, I want the pipeline to automatically continue when the human completes their task, so that downstream automated steps execute without manual pipeline intervention.

The Human step is treated as a blocking step — the pipeline does not advance past it until one of two completion conditions is met: (1) the associated Sub Issue is closed, or (2) the assigned user comments exactly 'Done!' on the parent GitHub Issue. Once either condition is detected, the Human step is marked complete and the next step in the pipeline executes.

**Why this priority**: Without completion detection, the Human step would be a dead end. This is essential for the pipeline to function as an end-to-end workflow.

**Independent Test**: Can be fully tested by triggering a pipeline with a Human step, closing the Sub Issue (or commenting 'Done!'), and verifying the pipeline advances to the next step.

**Acceptance Scenarios**:

1. **Given** a pipeline is waiting on a Human step, **When** the associated Sub Issue is closed, **Then** the Human step is marked as complete and the pipeline continues to the next step.
2. **Given** a pipeline is waiting on a Human step, **When** the assigned user comments exactly 'Done!' on the parent GitHub Issue, **Then** the Human step is marked as complete and the pipeline continues to the next step.
3. **Given** a pipeline is waiting on a Human step, **When** neither completion condition has been met, **Then** the pipeline does not advance past the Human step.
4. **Given** both completion conditions are triggered simultaneously (Sub Issue closed and 'Done!' comment posted at the same time), **When** the system processes both events, **Then** the pipeline advances only once (idempotent behavior).

---

### User Story 4 - Human Step Works in Any Pipeline Position (Priority: P2)

As a pipeline creator, I want to place the Human step at any position in my pipeline — beginning, middle, or end — so that I have full flexibility in designing mixed human-automated workflows.

The Human step behaves consistently regardless of where it is placed in the pipeline sequence. Steps before the Human step execute normally. Steps after the Human step wait until the Human step is complete before executing.

**Why this priority**: While the core functionality (Stories 1–3) is essential, positional flexibility is what makes the feature truly useful for diverse workflow designs.

**Independent Test**: Can be fully tested by creating three pipelines with the Human step at the beginning, middle, and end positions respectively, then verifying each executes correctly.

**Acceptance Scenarios**:

1. **Given** a Human step is placed as the first step in a pipeline column, **When** the pipeline is triggered, **Then** the Human step executes first and subsequent steps wait for its completion.
2. **Given** a Human step is placed between two automated agent steps, **When** the first automated step completes, **Then** the Human step activates and the third step waits until the Human step is complete.
3. **Given** a Human step is placed as the last step in a pipeline column, **When** all prior steps have completed, **Then** the Human step activates and the pipeline column is marked complete only after the Human step finishes.

---

### Edge Cases

- What happens when the issue creator's GitHub username cannot be resolved? The system surfaces a clear error message and does not silently skip assignment. A fallback behavior (such as leaving the Sub Issue unassigned with a visible warning) is provided.
- What happens when both completion signals (Sub Issue closed and 'Done!' comment) arrive simultaneously? The system processes the completion idempotently — the pipeline advances exactly once regardless of how many completion signals are received.
- What happens when someone other than the assigned user comments 'Done!' on the parent issue? The system only recognizes 'Done!' comments from the user assigned to the Human step's Sub Issue.
- What happens when the 'Done!' comment is not an exact match (e.g., 'Done' without exclamation, 'done!', or 'Done! ')? Only the exact string 'Done!' triggers completion.
- What happens if the Sub Issue is reopened after being closed? The pipeline has already advanced and does not revert. The reopened Sub Issue does not affect the pipeline state.
- What happens if the Human step's Sub Issue is deleted? The system treats this as an error condition and surfaces a warning. The 'Done!' comment path remains available as an alternative completion mechanism.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST include 'Human' as a selectable option in the '+ Add Agent' dropdown/menu for every status column across all Agent Pipelines by default.
- **FR-002**: System MUST apply the 'Human' agent option to all existing pipelines as well as any newly created pipelines without requiring manual reconfiguration.
- **FR-003**: System MUST auto-create a GitHub Sub Issue for the Human step using the same sub-issue creation mechanism used for automated agent steps when a pipeline containing a Human step is triggered.
- **FR-004**: System MUST automatically assign the generated Human Sub Issue to the user who created the parent GitHub Issue.
- **FR-005**: System MUST mark the Human step as complete and continue pipeline execution when the associated GitHub Sub Issue is closed.
- **FR-006**: System MUST mark the Human step as complete and continue pipeline execution when the assigned user comments exactly 'Done!' on the parent GitHub Issue, matching the same completion-signaling pattern used by automated agents.
- **FR-007**: System MUST NOT advance the pipeline past the Human step until one of the two completion conditions (Sub Issue closed OR 'Done!' comment from the assigned user) is detected.
- **FR-008**: System MUST ensure idempotent completion handling — if both completion conditions are triggered simultaneously, the pipeline advances only once.
- **FR-009**: System MUST support Human steps in any position within the pipeline sequence (first, middle, or last), ensuring steps after the Human step execute only after the Human step is complete.
- **FR-010**: System SHOULD visually distinguish the Human agent card from automated agent cards in the pipeline UI using a person icon and a 'Human' label.
- **FR-011**: System SHOULD handle edge cases where the issue creator cannot be resolved by surfacing a clear error message and providing a fallback assignment behavior (e.g., leaving the Sub Issue unassigned with a visible warning).
- **FR-012**: System MUST only accept 'Done!' comments from the user assigned to the Human step's Sub Issue as a valid completion signal.

### Key Entities

- **Human Step**: A pipeline step representing a manual human task. Shares the same lifecycle as automated agent steps (created, waiting, complete) but is completed by a human rather than an automated agent. Key attributes: step position in pipeline, assigned user, completion status, associated Sub Issue reference.
- **Sub Issue (Human)**: A GitHub Sub Issue created for a Human step. Identical in structure to Sub Issues created for automated agent steps, but assigned to the parent issue creator. Key attributes: parent issue reference, assignee (issue creator), open/closed state.
- **Completion Signal**: An event that marks a Human step as complete. Two valid sources: Sub Issue state change to 'closed', or an exact 'Done!' comment on the parent issue from the assigned user. Key attributes: signal type, source user, timestamp.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Pipeline creators can add a Human step to any column in any pipeline in under 10 seconds, using the same '+ Add Agent' interaction pattern as automated agents.
- **SC-002**: 100% of triggered pipelines with Human steps correctly create a Sub Issue and assign it to the parent issue creator without manual intervention.
- **SC-003**: Pipelines resume within 30 seconds of a completion signal (Sub Issue closed or 'Done!' comment) being detected.
- **SC-004**: Human steps function correctly in all pipeline positions (first, middle, last) with zero ordering errors.
- **SC-005**: Simultaneous completion signals (both Sub Issue closure and 'Done!' comment) result in exactly one pipeline advancement in 100% of cases.
- **SC-006**: Users can visually distinguish Human steps from automated agent steps at a glance without reading step details.
- **SC-007**: The Human agent option is available in all existing and new pipelines without any manual migration or reconfiguration steps.

## Assumptions

- The existing pipeline infrastructure already supports blocking/async steps (as used for automated agent steps), and the Human step can reuse this mechanism.
- The existing Sub Issue creation mechanism can accept an assignee parameter, allowing the system to inject the issue creator's username at creation time.
- The pipeline's completion detection infrastructure can be extended to listen for Sub Issue state changes and issue comment events without architectural changes.
- The 'Done!' comment pattern is already established for automated agent completion signaling, and the Human step reuses this exact pattern.
- The '+ Add Agent' dropdown is a shared UI component across all pipeline columns, so adding 'Human' as an option propagates to all columns automatically.
- Issue creator identity is available from the GitHub Issue metadata at the time the pipeline is triggered.
