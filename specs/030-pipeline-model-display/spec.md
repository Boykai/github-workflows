# Feature Specification: Display Models Used in Agent Pipeline Section of Parent Issue Description

**Feature Branch**: `030-pipeline-model-display`  
**Created**: 2026-03-08  
**Status**: Draft  
**Input**: User description: "The GitHub Parent Issue description - Agent Pipeline section, should also list the models to be used for the Agent Pipeline"

## User Scenarios & Testing *(mandatory)*

### User Story 1 — View Model Assignments in Agent Pipeline Table (Priority: P1)

A developer or project stakeholder opens a GitHub Parent Issue for a Project Solune feature. In the Agent Pipeline section of the issue description, they see a table listing each agent in the pipeline along with its current status, state, and now also the specific model assigned to that agent (e.g., "gpt-4o", "claude-3-5-sonnet"). This allows them to quickly understand the full pipeline configuration — which agents are involved, what models they use, and what state each agent is in — without navigating away from the issue.

**Why this priority**: This is the core value proposition of the feature. Without the model column in the pipeline table, stakeholders must navigate to separate agent configuration pages to determine which model each agent uses. Adding the model information directly in the pipeline table eliminates that friction and makes the Parent Issue a single source of truth for pipeline configuration.

**Independent Test**: Can be fully tested by creating a Parent Issue with an agent pipeline where agents have models assigned, and verifying the pipeline table in the issue description includes a "Model" column showing the correct model for each agent.

**Acceptance Scenarios**:

1. **Given** a Parent Issue with an agent pipeline containing 3 agents each assigned a model, **When** a user views the issue description, **Then** the Agent Pipeline table includes a "Model" column displaying the model name for each agent.
2. **Given** a Parent Issue with an agent pipeline where Agent A uses "gpt-4o" and Agent B uses "claude-3-5-sonnet", **When** a user views the pipeline table, **Then** Agent A's row shows "gpt-4o" and Agent B's row shows "claude-3-5-sonnet" in the Model column.
3. **Given** a Parent Issue with a single-agent pipeline, **When** a user views the pipeline table, **Then** the Model column is present and shows the model for that single agent.

---

### User Story 2 — Display Placeholder When Model Is Not Assigned (Priority: P1)

A developer views a Parent Issue where some agents in the pipeline do not yet have a model configured. Instead of seeing an empty cell or broken formatting, they see a clear placeholder text (e.g., "TBD") in the Model column for any agent without a model assignment. This maintains visual consistency and clearly communicates that a model still needs to be selected.

**Why this priority**: Without a placeholder, empty Model cells could be confusing — users might wonder if the data failed to load, if the model was removed, or if it's a rendering bug. A clear placeholder communicates intent and keeps the table scannable. This is essential for the feature to be usable in real workflows where pipelines are configured incrementally.

**Independent Test**: Can be fully tested by creating a Parent Issue with a pipeline where at least one agent has no model assigned, and verifying the pipeline table displays a placeholder (e.g., "TBD") in the Model column for that agent.

**Acceptance Scenarios**:

1. **Given** a Parent Issue with an agent pipeline where Agent A has a model and Agent B does not, **When** a user views the pipeline table, **Then** Agent A's Model column shows the model name and Agent B's Model column shows "TBD".
2. **Given** a Parent Issue with a pipeline where no agents have models assigned, **When** a user views the pipeline table, **Then** every agent's Model column shows "TBD".
3. **Given** an agent that previously had no model and then gets one assigned, **When** the pipeline table is updated, **Then** the placeholder is replaced with the actual model name.

---

### User Story 3 — Pipeline Table Updates When Agent Models Change (Priority: P2)

A developer changes the model assignment for an agent in the pipeline configuration. The Agent Pipeline section in the Parent Issue description is automatically updated to reflect the new model, keeping the issue description in sync with the actual configuration. The developer does not need to manually edit the issue.

**Why this priority**: The value of displaying models in the pipeline table is significantly diminished if the information becomes stale. Dynamic synchronization ensures the Parent Issue remains a reliable, up-to-date reference for the pipeline configuration. This builds on the core display feature (P1) by ensuring ongoing accuracy.

**Independent Test**: Can be fully tested by changing an agent's model assignment in the pipeline configuration, then refreshing the Parent Issue and verifying the Model column reflects the updated model name.

**Acceptance Scenarios**:

1. **Given** a Parent Issue with an agent using model "gpt-4o", **When** the agent's model is changed to "claude-3-5-sonnet" and the pipeline tracking is updated, **Then** the pipeline table in the issue description now shows "claude-3-5-sonnet" for that agent.
2. **Given** a Parent Issue with an agent that had a model assigned, **When** the model assignment is removed, **Then** the pipeline table updates to show the placeholder "TBD" for that agent.
3. **Given** multiple agents in the pipeline with model changes happening to different agents, **When** the pipeline table is updated, **Then** each agent's row reflects its current model assignment independently.

---

### Edge Cases

- What happens when the model name is very long (e.g., "custom-fine-tuned-gpt-4o-2026-03-extended-context")? The table should display the full model name without truncation, and the table should remain readable in GitHub's issue view without breaking the Markdown layout.
- What happens when the pipeline has agents with identical names but different models? Each agent's row should independently display its own model based on its unique configuration, regardless of agent name duplication.
- What happens when the Agent Pipeline section is regenerated from scratch (e.g., issue body is rebuilt)? The model column should be included in the regenerated table with current model data.
- What happens when a pipeline has no agents? The table should render with the Model column header but no data rows, consistent with existing behavior for empty pipelines.
- What happens when model identifiers contain special Markdown characters (e.g., pipes `|`, backticks)? The model name should be properly escaped so the Markdown table renders correctly.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST include a "Model" column in the Agent Pipeline tracking table rendered in the Parent Issue description, showing the model name associated with each agent.
- **FR-002**: System MUST display a placeholder value of "TBD" in the Model column for any agent that does not have a model configured.
- **FR-003**: System MUST format the Model column using valid GitHub-flavored Markdown so the table renders correctly in the GitHub issue description view.
- **FR-004**: System MUST update the Model column values in the Agent Pipeline table whenever agent model assignments change and the pipeline tracking section is refreshed in the issue body.
- **FR-005**: System MUST handle pipelines with one or more agents, correctly listing the model for each agent in the pipeline order.
- **FR-006**: System MUST preserve all existing Agent Pipeline table columns (number, status, agent, state) and formatting when adding the Model column, ensuring no regression in the current issue description structure.
- **FR-007**: System SHOULD display the model name using the same identifier or label used elsewhere in Project Solune (e.g., the agent configuration pages) to maintain consistency.
- **FR-008**: System MUST properly escape any special Markdown characters in model names to prevent rendering issues in the GitHub issue table.

### Key Entities

- **Agent Pipeline Step**: A single entry in the Agent Pipeline tracking table representing one agent's position and state in the pipeline. Attributes: sequence number, pipeline status, agent name, execution state, and now also the assigned model name.
- **Model Assignment**: The association between an agent in a pipeline and the specific model it is configured to use. Attributes: model identifier, display name. May be unset (represented by placeholder).

## Assumptions

- The model name or identifier for each agent is available at the time the Agent Pipeline tracking table is rendered. The existing pipeline configuration data structures already include model fields (model_id, model_name) for each agent node.
- The existing rendering function for the Agent Pipeline tracking table can be extended to accept and display model information without changing its call signature in a breaking way.
- The model label displayed in the pipeline table matches the model_name field already stored in the agent or pipeline configuration — no additional lookup or transformation is needed.
- The existing pipeline tracking update flow (used when marking agents active or done) already has access to the pipeline configuration, making it straightforward to include model data when refreshing the tracking section.
- GitHub-flavored Markdown tables with an additional column will render correctly in all standard GitHub issue views (web, mobile, API).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Every agent row in the Agent Pipeline table of a Parent Issue description includes a visible Model column — verified by inspecting at least 3 Parent Issues with different pipeline configurations.
- **SC-002**: Agents with models assigned display the correct model name in the Model column — verified by cross-referencing the pipeline table with the agent configuration for at least 2 pipelines with different model assignments.
- **SC-003**: Agents without models assigned display "TBD" in the Model column — verified by creating a pipeline with at least one unassigned agent and confirming the placeholder appears.
- **SC-004**: The pipeline table renders correctly in GitHub's issue view with the new Model column — verified by viewing the issue in a browser and confirming the Markdown table is properly formatted with aligned columns and no rendering artifacts.
- **SC-005**: After changing an agent's model assignment and triggering a pipeline tracking update, the Model column in the Parent Issue reflects the new model — verified by performing a model change and refreshing the issue page.
- **SC-006**: All existing pipeline table information (number, status, agent name, state) remains intact and correctly displayed after the Model column is added — verified by comparing the table structure before and after the change.
