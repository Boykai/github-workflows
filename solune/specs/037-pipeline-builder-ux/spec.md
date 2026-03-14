# Feature Specification: Reinvent Agent Pipeline Creation UX

**Feature Branch**: `037-pipeline-builder-ux`  
**Created**: 2026-03-12  
**Status**: Draft  
**Input**: User description: "Replace the current fixed-column, single-group-per-stage pipeline builder with a modern kanban-style builder that supports multiple execution groups per column, cross-column drag-and-drop, and per-group series/parallel toggle."

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Compose Mixed Execution Groups Within a Stage (Priority: P1)

A pipeline author opens the builder and needs a single stage that first runs a linting agent, then fans out to three review agents running simultaneously, and finally runs a summary agent. Today the entire stage is locked to one execution mode so the author is forced to split work across multiple stages. With the new builder the author creates one stage, adds an execution group set to "series" for the linter, a second group set to "parallel" for the three reviewers, and a third group set to "series" for the summariser — all inside the same column.

**Why this priority**: This is the core value proposition. Without multiple execution groups per stage the remaining features (cross-column drag, per-group toggle) have no surface area to operate on. Delivering this alone gives users immediate compositional power that does not exist today.

**Independent Test**: Can be fully tested by creating a new pipeline, adding a single stage, adding multiple execution groups to that stage with different modes, assigning agents to each group, saving, and verifying the resulting pipeline configuration preserves the group structure.

**Acceptance Scenarios**:

1. **Given** a stage with zero execution groups, **When** the user adds a new execution group, **Then** the group appears inside the stage column with a default execution mode of "series" and an empty agent slot.
2. **Given** a stage with one execution group, **When** the user adds a second execution group, **Then** both groups are displayed vertically within the same column, each with its own mode indicator and agent list.
3. **Given** an execution group set to "parallel", **When** the user adds three agents to that group, **Then** all three agents are displayed in a side-by-side layout within the group container.
4. **Given** a stage with multiple groups, **When** the user saves the pipeline, **Then** the persisted configuration includes the ordered list of groups, each with its execution mode and agent assignments.
5. **Given** an execution group containing a single agent, **When** the user toggles the group mode from "series" to "parallel", **Then** the mode indicator updates and the layout remains unchanged until a second agent is added.

---

### User Story 2 — Drag and Drop Agents Across Stages (Priority: P2)

A pipeline author realises an agent assigned to Stage 2 would be more effective in Stage 3. Today the author must remove the agent from Stage 2 and manually re-add it to Stage 3. With the new builder the author picks up the agent card and drops it into the target group in Stage 3, preserving the agent's model selection and tool configuration.

**Why this priority**: Cross-column drag-and-drop is the second-most impactful usability improvement. It eliminates repetitive remove-and-re-add cycles and makes pipeline editing feel like a true visual workflow tool. It builds on the group structure delivered by P1.

**Independent Test**: Can be fully tested by creating a pipeline with two stages, adding an agent to Stage 1, dragging that agent card to Stage 2, and confirming the agent now appears in Stage 2 with its original model and tool settings intact.

**Acceptance Scenarios**:

1. **Given** an agent in Group A of Stage 1, **When** the user drags the agent card and drops it onto Group B in Stage 2, **Then** the agent is removed from Group A and appears in Group B with its model selection and tool configuration preserved.
2. **Given** an agent being dragged, **When** the user hovers the agent card over a valid drop target (an execution group in any stage), **Then** a visual drop indicator highlights the target group.
3. **Given** an agent being dragged, **When** the user drops the agent card outside any valid drop zone, **Then** the agent returns to its original position with no changes.
4. **Given** a stage with a single agent in its only group, **When** the user drags that agent to another stage, **Then** the source group becomes empty and displays an empty-state prompt.
5. **Given** an agent being dragged between stages, **When** the drag crosses a stage boundary, **Then** the operation completes in a single gesture without requiring an intermediate step (no clipboard, no modal).

---

### User Story 3 — Reorder Agents Within and Between Groups (Priority: P3)

A pipeline author wants to change the order of agents inside a "series" group so that Agent B runs before Agent A. The author also wants to move Agent C from one group to another group within the same stage. The author picks up the agent card and drops it at the desired position.

**Why this priority**: Intra-stage reordering and inter-group movement within a stage complete the drag-and-drop story. Users already have within-group reordering today; extending this to cross-group reordering within the same stage is a natural next step and polishes the experience.

**Independent Test**: Can be fully tested by creating a stage with two groups, placing agents in each, reordering agents within one group, and moving an agent from one group to the other, then verifying the final order matches the user's intent.

**Acceptance Scenarios**:

1. **Given** a "series" group with agents [A, B, C], **When** the user drags Agent C to the position before Agent A, **Then** the group's agent order becomes [C, A, B].
2. **Given** two groups in the same stage, **When** the user drags an agent from Group 1 and drops it into Group 2, **Then** the agent is removed from Group 1 and placed at the drop position in Group 2.
3. **Given** a "parallel" group with agents displayed in a grid, **When** the user drags an agent to a new grid position, **Then** the agent order updates to reflect the new arrangement.

---

### User Story 4 — Toggle Execution Mode Per Group (Priority: P4)

A pipeline author wants to switch an execution group from "parallel" to "series" so that the agents in it run one after another instead of concurrently. The author clicks the mode toggle on the group header and sees the layout change instantly.

**Why this priority**: The per-group toggle is the final piece of compositional flexibility. It depends on groups existing (P1) but can be delivered and tested independently.

**Independent Test**: Can be fully tested by creating a stage, adding a group with two agents, toggling the group mode, and verifying the visual layout and saved configuration change accordingly.

**Acceptance Scenarios**:

1. **Given** a group with two agents set to "parallel", **When** the user toggles the mode to "series", **Then** the agents re-layout from a side-by-side grid to a vertical list, and the mode indicator updates.
2. **Given** a group with two agents set to "series", **When** the user toggles the mode to "parallel", **Then** the agents re-layout from a vertical list to a side-by-side grid, and the mode indicator updates.
3. **Given** a group whose mode was just toggled, **When** the user saves the pipeline, **Then** the persisted configuration reflects the updated mode for that group.
4. **Given** a stage with three groups each in different modes, **When** the pipeline is saved and reopened, **Then** all three groups display their correct modes and layouts.

---

### User Story 5 — Manage Stage Columns (Priority: P5)

A pipeline author wants to add, remove, and reorder stage columns to define the high-level flow of the pipeline. The author can add a new stage to the end, insert a stage between existing stages, remove an empty or populated stage, and reorder stages.

**Why this priority**: Stage management is largely functional today. Enhancements to support the new group model (e.g., ensuring a removed stage's agents are not silently lost) are important but lower priority than the core group and DnD features.

**Independent Test**: Can be fully tested by adding stages, reordering them, removing a stage, and confirming the pipeline layout and saved configuration are correct.

**Acceptance Scenarios**:

1. **Given** a pipeline with two stages, **When** the user adds a new stage, **Then** the new stage appears as a new column to the right with a default name and an empty execution group.
2. **Given** a pipeline with three stages, **When** the user removes a stage that contains agents, **Then** the system displays a confirmation prompt listing the agents that will be unassigned before proceeding.
3. **Given** a pipeline with stages [A, B, C], **When** the user reorders Stage C to position 1, **Then** the stages display as [C, A, B] and execution order reflects the new arrangement.

---

### User Story 6 — Backward-Compatible Pipeline Loading (Priority: P6)

A user opens a pipeline that was saved under the old single-group-per-stage format. The builder automatically converts each stage's flat agent list into a single execution group with the stage's original execution mode, so the user sees their existing pipeline rendered correctly in the new group-based layout without any data loss.

**Why this priority**: Without backward compatibility users would lose access to all existing saved pipelines. This is a hard requirement but is lower priority in terms of implementation sequencing because the migration logic is deterministic and can be applied at load time.

**Independent Test**: Can be fully tested by loading a pipeline saved in the old format and confirming it renders correctly with one group per stage, preserving all agents, execution mode, and model selections.

**Acceptance Scenarios**:

1. **Given** a saved pipeline in the old format (flat agent list per stage, single execution mode), **When** the pipeline is loaded in the new builder, **Then** each stage is displayed with one execution group containing all original agents in their original order, using the stage's original execution mode.
2. **Given** a migrated pipeline displayed in the builder, **When** the user saves it without changes, **Then** the pipeline is persisted in the new group-based format with no data loss.
3. **Given** a migrated pipeline, **When** the user inspects the group structure, **Then** no duplicate agents, missing model selections, or altered tool configurations are present.

---

### Edge Cases

- What happens when a user drops an agent onto a group that already contains the maximum displayable number of agents? The group scrolls or expands to accommodate the new agent; no hard cap is enforced.
- How does the system handle a drag operation that is interrupted (e.g., browser loses focus mid-drag)? The drag is cancelled and the agent returns to its original position.
- What happens when a user deletes the last group in a stage? The stage retains one empty default group so it remains a valid drop target.
- How does the builder handle a pipeline with zero stages? It displays an empty-state prompt inviting the user to add the first stage.
- What happens when two users edit the same pipeline simultaneously? The last save wins; concurrent editing is out of scope for this feature (standard save-time conflict behavior applies).
- What happens when a user creates a group with zero agents and saves the pipeline? Empty groups are preserved in the saved configuration so the user's intended structure is not lost.
- How does keyboard-only navigation work with the new group and cross-column drag? Keyboard users can tab through groups and stages, use arrow keys to move within a group, and use a keyboard shortcut to initiate a move operation to pick up and place an agent in a target group.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST allow users to create multiple execution groups within a single pipeline stage.
- **FR-002**: System MUST allow users to set each execution group independently to either "series" (sequential) or "parallel" execution mode.
- **FR-003**: System MUST display a clear visual indicator on each group showing its current execution mode ("series" or "parallel").
- **FR-004**: System MUST allow users to toggle an execution group's mode between "series" and "parallel" with a single interaction.
- **FR-005**: System MUST support drag-and-drop of agent cards between execution groups across different stage columns in a single gesture.
- **FR-006**: System MUST support drag-and-drop of agent cards between execution groups within the same stage column.
- **FR-007**: System MUST preserve an agent's model selection and tool configuration when the agent is moved via drag-and-drop.
- **FR-008**: System MUST display a visual drop indicator when an agent card is dragged over a valid drop target.
- **FR-009**: System MUST cancel a drag operation and return the agent to its original position when dropped outside any valid drop zone.
- **FR-010**: System MUST support reordering of agents within an execution group via drag-and-drop.
- **FR-011**: System MUST persist the complete group structure (group order, execution mode per group, agent assignments per group) when a pipeline is saved.
- **FR-012**: System MUST load pipelines saved in the old single-group-per-stage format by converting each stage's flat agent list into a single execution group, preserving execution mode and agent order.
- **FR-013**: System MUST allow users to add a new execution group to any existing stage.
- **FR-014**: System MUST allow users to remove an execution group from a stage, reassigning or discarding its agents as the user chooses.
- **FR-015**: System MUST render "series" groups as a vertical list layout and "parallel" groups as a side-by-side grid layout.
- **FR-016**: System MUST display an empty-state prompt in a group that contains no agents.
- **FR-017**: System MUST display a confirmation prompt when a user attempts to remove a stage that contains agents, listing the agents that will be unassigned.
- **FR-018**: System MUST support keyboard navigation for all drag-and-drop operations, allowing users to move agents between groups and stages without a pointing device.
- **FR-019**: System MUST render execution groups within a stage in their defined order from top to bottom, reflecting the sequential execution order of groups within the stage.
- **FR-020**: System MUST allow users to reorder execution groups within a stage to change their execution sequence.

### Key Entities

- **Pipeline Config**: A named, saveable workflow definition. Contains an ordered list of stages and metadata (name, description, project association, preset status).
- **Stage**: A column in the pipeline representing a phase of execution. Contains an ordered list of execution groups. Stages execute in left-to-right order.
- **Execution Group**: A container within a stage that holds one or more agents and an execution mode ("series" or "parallel"). Groups within a stage execute in top-to-bottom order. Agents within a "series" group execute sequentially; agents within a "parallel" group execute concurrently.
- **Agent Node**: An individual agent assignment within an execution group. Carries the agent identity, model selection, and tool configuration. Can be moved between groups and stages via drag-and-drop.

## Assumptions

- The existing stage add/remove/reorder functionality will continue to work as it does today; this feature extends stages with group sub-structure rather than replacing the stage concept.
- Agent model selection and tool configuration are properties of the agent node assignment, not of the execution group. Moving an agent between groups preserves these settings.
- The pipeline execution engine (backend) already supports or will be updated separately to execute grouped agent configurations. This specification covers the builder UI; backend execution semantics are out of scope.
- Preset pipelines will be migrated to the new group-based format as part of the backward compatibility story. Preset definitions will each have one group per stage matching their current structure.
- Performance is acceptable for pipelines with up to 10 stages, each with up to 5 groups, and up to 10 agents per group (50 agents total per pipeline).
- Concurrent multi-user editing of the same pipeline is out of scope. Standard last-write-wins behavior applies.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can compose a pipeline with mixed series and parallel agent execution within a single stage in under 2 minutes (measured from opening an empty pipeline to saving a configuration with at least 2 groups in one stage, each containing at least one agent).
- **SC-002**: Users can move an agent from one stage to another via drag-and-drop in a single gesture taking under 3 seconds, with no loss of model selection or tool configuration.
- **SC-003**: 90% of first-time users can successfully create a pipeline with at least one multi-group stage on their first attempt without consulting documentation.
- **SC-004**: All existing pipelines saved in the old format load correctly in the new builder with zero data loss — same agents, same execution modes, same model selections.
- **SC-005**: All drag-and-drop operations (within group, between groups, between stages) are completable via keyboard alone, meeting accessibility standards.
- **SC-006**: Pipeline builder interactions (drag start, drop, mode toggle, group add/remove) respond to user input in under 200 milliseconds with no perceptible lag for pipelines containing up to 50 agent nodes.
- **SC-007**: Saving a pipeline with the new group-based structure and reopening it produces an identical visual layout — no group reordering, mode changes, or agent position shifts.
