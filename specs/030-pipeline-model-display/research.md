# Research: Display Models Used in Agent Pipeline Section of Parent Issue Description

**Feature**: 030-pipeline-model-display | **Date**: 2026-03-08

## R1: Model Data Source — Where to Get Model Names for Pipeline Agents

**Task**: Determine how to obtain the model name for each agent in the pipeline tracking table without adding new data fetching or async operations.

**Decision**: Extract the model name from the existing `AgentAssignment.config` dictionary. When agents are assigned to pipeline statuses via the Settings UI (`useAgentConfig.ts`), the frontend stores model information in the assignment's `config` field as `{ model_id: "...", model_name: "..." }`. This `config` dict is persisted in the `agent_pipeline_mappings` JSON column of the `project_settings` SQLite table and is available on the `AgentAssignment` object when `build_agent_pipeline_steps()` is called. The extraction logic is: `agent.config.get("model_name", "")` if `agent.config` is a dict, else `""`. An empty string maps to the "TBD" placeholder in the rendered table.

**Rationale**: The `AgentAssignment` model (`backend/src/models/agent.py`) has a `config: dict | None` field described as "Reserved for future per-assignment config." The frontend already populates this field with model data (see `frontend/src/hooks/useAgentConfig.ts` lines 150–156 where `model_id` and `model_name` are stored in `config`). The same `AgentAssignment` objects are passed to `append_tracking_to_body()` by the chores service (`backend/src/services/chores/service.py:360`) and the workflow orchestrator (`backend/src/services/workflow_orchestrator/orchestrator.py:486`). No additional database queries or API calls are needed — the data is already in the objects flowing through the pipeline.

**Alternatives Considered**:
- **Query `agent_configs` table for `default_model_name`**: Rejected — would require making `build_agent_pipeline_steps()` async and adding a database dependency to a pure function. The `AgentAssignment.config` dict already carries the model name as set by the user in the pipeline configuration.
- **Look up model from `AvailableAgent.default_model_name`**: Rejected — requires fetching the available agents list, which involves GitHub API discovery. Over-engineered for a string that's already available in the assignment config.
- **Add `model_name` as a top-level field on `AgentAssignment`**: Considered but rejected — would require a data migration and changes to all serialization/deserialization points. The `config` dict approach is already established and working.

---

## R2: Backward Compatibility — Parsing Old Pipeline Tables

**Task**: Determine how to handle existing GitHub issues that have the old 4-column pipeline table (without Model column) when parsing.

**Decision**: Use two row-parsing regexes to support both table formats: `_ROW_RE` for the new 5-column format and `_ROW_RE_OLD` for the legacy 4-column format (without Model). The parser first attempts to match `_ROW_RE` (e.g., `| 1 | Status | `agent` | Model | State |`); if that fails, it falls back to `_ROW_RE_OLD` (e.g., `| 1 | Status | `agent` | State |`). When an old-format row is matched, the model field is set to `""`. This ensures that `parse_tracking_from_body()`, `get_current_agent_from_tracking()`, `get_next_pending_agent()`, and `determine_next_action()` all continue to work on issues created before this change.

**Rationale**: There will be a transition period where both old (4-column) and new (5-column) tables exist in GitHub issues. The polling loop (`determine_next_action()`) reads the tracking table on every cycle — it must handle both formats. Using two explicit regexes keeps the parsing logic straightforward and makes it easy to reason about and test each format separately. When old issues are updated (e.g., agent marked active/done via `update_agent_state()`), the table will be re-rendered with the new format, naturally migrating it forward.

**Alternatives Considered**:
- **Single regex with optional Model column**: Considered but rejected — while it reduces the number of regex definitions, it makes the pattern harder to read and debug. Explicit regexes for each format keep the code paths clear and align better with the existing tests and tasks.
- **Migration script to update all existing issues**: Rejected — over-engineered. Issues are naturally migrated when their tracking table is re-rendered during pipeline state changes. No manual migration needed.
- **Version marker in the tracking section**: Rejected — adds metadata that serves no purpose beyond parsing. The regexes handle both formats transparently.

---

## R3: Model Column Placement — Before or After State Column

**Task**: Determine where to place the new Model column in the pipeline tracking table for optimal readability.

**Decision**: Place the Model column between the Agent column and the State column. The new table format is:

```markdown
| # | Status | Agent | Model | State |
|---|--------|-------|-------|-------|
| 1 | Backlog | `speckit.specify` | gpt-4o | ✅ Done |
```

**Rationale**: The State column (⏳ Pending / 🔄 Active / ✅ Done) is the most frequently scanned column — users look at it to quickly assess pipeline progress. Placing it at the end (rightmost position) preserves its current location and avoids disrupting users' existing visual scanning patterns. The Model column logically belongs next to the Agent column since it describes a property of the agent's configuration. The order # → Status → Agent → Model → State follows a natural "where → who → how → what" information hierarchy: which status stage (where), which agent (who), which model it uses (how), and what's its current state (what).

**Alternatives Considered**:
- **Model column after State (rightmost)**: Rejected — State is the most important dynamic column; keeping it at the end where users already look is better. Adding Model after State would push the most frequently scanned column to a less prominent position.
- **Model column before Status**: Rejected — breaks the natural reading flow. The # and Status columns establish context for the row; model is an agent property and belongs near the Agent column.
- **Model as sub-row under Agent (not a column)**: Rejected — sub-rows in Markdown tables are not supported. Would require switching to a different format (e.g., details/summary blocks), breaking the established table pattern.
