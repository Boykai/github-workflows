# Research: Pipeline Page — MCP Tool Selection, Model Override, Flow Graph Cards, Preset Configs & Agent Stamp Isolation

**Feature**: 028-pipeline-mcp-config | **Date**: 2026-03-07

## R1: Per-Agent MCP Tool Storage Strategy

**Task**: Determine how to persist MCP tool selections for each agent within a pipeline, given the existing `PipelineAgentNode` model and the `agent_tool_associations` junction table.

**Decision**: Extend `PipelineAgentNode` with a `tool_ids: list[str]` field stored inline within the pipeline's JSON `stages` column. Do NOT use the `agent_tool_associations` junction table for pipeline-scoped tool assignments.

**Rationale**: Pipeline configurations are stored as a single JSON document (`stages` column in `pipeline_configs` table). The existing `PipelineAgentNode` already contains `agent_slug`, `model_id`, `model_name`, and `config`. Adding `tool_ids` as an inline list keeps the pipeline document self-contained — every pipeline load/save is a single row read/write with no JOINs. The `agent_tool_associations` table serves agent-level (global) tool assignments on the Agents page and should not be polluted with pipeline-scoped overrides, which would break agent stamp isolation (FR-006). Tool metadata (names, descriptions) can be resolved by joining with `useTools()` on the frontend at render time.

**Alternatives Considered**:
- **`pipeline_agent_tools` junction table**: Rejected — requires additional migration, JOIN on every pipeline load, and complicates the document-oriented pipeline pattern. The pipeline is always loaded as a complete unit; a junction table adds overhead for no benefit.
- **Reuse `agent_tool_associations` with a `pipeline_id` scope column**: Rejected — muddies the existing agent-tool relationship model, makes it harder to distinguish global vs. pipeline-scoped assignments, and risks violating agent stamp isolation if cleanup logic is imperfect.

---

## R2: Agent Stamp Isolation Architecture

**Task**: Ensure that model and tool overrides in the pipeline builder never mutate the source agent's global configuration on the Agents page.

**Decision**: Pipeline-scoped overrides (model, tools) are stored exclusively within the `PipelineAgentNode` embedded in the pipeline document. The pipeline save path (`PUT /api/v1/pipelines/{project_id}/{pipeline_id}`) writes only to the `pipeline_configs` table. It never touches `agent_configs` or `agent_tool_associations`. On the frontend, the `usePipelineConfig` hook maintains a local working copy of agent nodes with override fields; changes flow only to `pipelinesApi.update()`, not to `agentsApi` or `agentToolsApi`.

**Rationale**: The spec mandates (FR-006) that "the source agent's global stamp on the Agents page MUST remain unchanged." The simplest guarantee is architectural: the pipeline save code path has no write access to agent tables. This is already the case in the existing implementation (spec 026 `PipelineService` only operates on `pipeline_configs`). Extending `PipelineAgentNode` with `tool_ids` maintains this property — tool assignments live inside the pipeline JSON, not in the `agent_tool_associations` table. No additional guard logic or transaction isolation is needed because the code paths are structurally disjoint.

**Alternatives Considered**:
- **Copy-on-write agent records for pipelines**: Rejected — duplicates agent data, requires synchronization when source agents are updated, significantly increases complexity.
- **Transaction-level isolation with rollback**: Rejected — over-engineered; the simpler approach of separate code paths provides the same guarantee with zero additional complexity.

---

## R3: MCP Tool Selector Integration for Pipeline Builder

**Task**: Determine whether to build a new tool selection component for the pipeline builder or reuse the existing `ToolSelectorModal`.

**Decision**: Reuse the existing `ToolSelectorModal` component from `frontend/src/components/tools/ToolSelectorModal.tsx`. Invoke it from each agent card in the pipeline builder, passing the agent's current `tool_ids` as the initial selection and receiving the updated selection on close.

**Rationale**: The `ToolSelectorModal` already implements the tiled grid multi-select UX described in the spec (FR-002). It accepts a list of available tools (from `useTools()`) and emits selected tool IDs. Creating a duplicate component would violate DRY (Constitution Principle V). The only adaptation needed is to wire the modal's `onConfirm` callback to update the `PipelineAgentNode.tool_ids` in the pipeline's local working copy rather than calling `agentToolsApi.update()`.

**Alternatives Considered**:
- **New `PipelineToolSelector` component**: Rejected — would duplicate the tile grid, multi-select toggle, and search/filter logic already present in `ToolSelectorModal`. YAGNI.
- **Inline tool chips with add button**: Rejected — doesn't match the spec requirement for a "lightweight pop-out/flyout module" with a "tiled, multi-select grid."

---

## R4: Pipeline-Level Model Override Mechanism

**Task**: Design how the pipeline-level model dropdown (with "Auto" option) should interact with per-agent model fields.

**Decision**: Add a `PipelineModelDropdown` component at the top of the pipeline builder form. When a model is selected:
- If the value is a specific model (e.g., "gpt-4o"), iterate all `PipelineAgentNode` objects in all stages and set `model_id` and `model_name` to the selected model. This is a local state operation on the working copy.
- If the value is "Auto", iterate all agents and reset `model_id` to `""` and `model_name` to `""`, causing each agent to fall back to its saved stamp model at runtime.

The pipeline-level selection is NOT stored as a separate field in the database. It is a convenience control that batch-updates the individual agent nodes. After batch update, the user can still override individual agents, creating a "mixed" state.

**Rationale**: Storing the pipeline-level model as a separate database field creates a conflict: does the pipeline-level model win, or does the per-agent model? By making it a batch-update convenience (no persistent field), we avoid this ambiguity. The individual agent `model_id` fields are the source of truth. The spec's "Auto" behavior (FR-005, FR-006) maps naturally to clearing the override fields — when `model_id` is empty, the runtime uses the agent's own stamp setting. This is consistent with the existing `PipelineAgentNode` model where empty `model_id` means "use default."

**Alternatives Considered**:
- **Dedicated `pipeline_model` column in `pipeline_configs`**: Rejected — creates ambiguity about precedence, requires merge logic at runtime, adds complexity.
- **Nested override hierarchy (pipeline > stage > agent)**: Rejected — the spec only describes pipeline-level and per-agent overrides. Stage-level is YAGNI.

---

## R5: Compact Flow Graph Implementation

**Task**: Determine the best approach for rendering compact flow graphs on Saved Workflows and Recent Activity cards.

**Decision**: Implement a custom `PipelineFlowGraph` SVG component that renders a horizontal node-edge diagram within a constrained card area (~200px wide × 60px tall). Each stage is a rounded rectangle node; edges connect stages left-to-right. Agent count is displayed as a small number inside each node. The component receives `stages: PipelineStage[]` as props and renders statically (no interaction).

**Rationale**: The flow graph is a read-only miniature visualization (FR-009). It needs to fit within a card layout (~300px wide) and render dozens of instances on the page without performance impact. A custom SVG component is the lightest possible approach — no external dependency, full control over sizing, and trivial to memoize. The graph structure is always a linear pipeline (stages in order), not a complex DAG, so a full graph library is unnecessary.

**Alternatives Considered**:
- **React Flow in read-only mode**: Rejected — adds ~150KB to the bundle, requires `ReactFlowProvider` setup, has features (zoom, pan, handles) we don't need. The spec's technical notes suggest it as an option but also mention "custom SVG renderer." Given the simplicity of the visualization, SVG is preferred per Constitution Principle V.
- **D3.js force layout**: Rejected — even heavier than React Flow, designed for dynamic layouts. Our graph is static and linear.
- **CSS-only flow diagram**: Rejected — harder to control precise positioning and edge routing; SVG provides more reliable cross-browser rendering for node-edge diagrams.

---

## R6: Preset Pipeline Configuration Seeding Strategy

**Task**: Determine how to seed the "Spec Kit" and "GitHub Copilot" preset pipeline configurations.

**Decision**: Define preset configurations as static data in two locations:
1. **Backend**: A SQL migration (`015_pipeline_mcp_presets.sql`) that adds an `is_preset` boolean column and a `preset_id` text column to `pipeline_configs`. Preset pipelines are inserted on first startup for each project via the `PipelineService.seed_presets()` method (called on project initialization, idempotent via `preset_id` uniqueness).
2. **Frontend**: A static TypeScript module (`frontend/src/data/preset-pipelines.ts`) defining the preset configurations for display purposes and as templates for "Save as Copy" functionality.

Presets are flagged with `is_preset = 1` and a unique `preset_id` ("spec-kit", "github-copilot"). They appear in the Saved Workflows list with a distinguishing badge (FR-012). Editing a preset triggers a "Save as Copy" prompt, creating a new user-owned pipeline with `is_preset = 0`.

**Rationale**: The spec requires presets to be visible on first visit (SC-006) and visually distinguished (FR-012). A migration-based approach ensures presets exist in the database and are queryable via the same API as user pipelines. The `seed_presets()` method is idempotent (checks `preset_id` before inserting), so it's safe to call on every project load. The frontend static definitions provide the template data for "Save as Copy" without an additional API round-trip.

**Alternatives Considered**:
- **Frontend-only presets (not in database)**: Rejected — would require special handling in the Saved Workflows list (mixing API data with hardcoded data), complicates the flow graph rendering, and prevents presets from appearing in "select from saved pipelines" dropdowns.
- **Admin API for preset management**: Rejected — YAGNI. Only 2 presets are needed, and they're defined at build time.
- **Config file loaded at startup**: Rejected — essentially equivalent to the migration approach but adds a new config-loading mechanism. The migration pattern is already established.

---

## R7: Always-Available Save with Inline Validation

**Task**: Design the validation UX for the always-enabled Save button.

**Decision**: The Save button is always enabled (never `disabled`). On click:
1. Run client-side validation against the pipeline working copy.
2. If validation fails, set a `validationErrors` state object in `usePipelineConfig` mapping field names to error messages (e.g., `{ name: "Pipeline name is required" }`).
3. Components read `validationErrors` and render red borders + helper text on offending fields.
4. On the next edit to a field with an error, the error for that field is cleared.
5. If validation passes, proceed with the save mutation.

Required validations:
- Pipeline name: non-empty, 1–100 characters
- At least one stage with at least one agent (warning, not blocking — spec allows saving with no agents but displays a warning)

**Rationale**: The spec explicitly requires (FR-007) that Save is always clickable and errors are shown inline. This follows the "submit then validate" UX pattern, which is more discoverable than disabling the button. The `validationErrors` state object is a lightweight approach that doesn't require a form library. Field-level error clearing on edit provides immediate feedback.

**Alternatives Considered**:
- **Disable Save until form is valid**: Rejected — directly contradicts FR-007 which requires Save to be always clickable.
- **React Hook Form or Formik**: Rejected — adds a dependency for a form with only 2–3 fields. The pipeline builder is not a traditional form; it's a visual canvas. A form library would be awkward to integrate. YAGNI.
- **Toast-based error reporting**: Rejected — spec requires "inline validation errors (highlighted fields + helper text)," not toasts.

---

## R8: Project Pipeline Assignment for GitHub Issues

**Task**: Determine how to link a project to a saved pipeline configuration and inject that configuration into newly created GitHub Issues.

**Decision**: Add an `assigned_pipeline_id` column to the `project_settings` table. When set, the pipeline ID is read during GitHub Issue creation in `github_projects/service.py`. The issue creation method injects a `pipeline_config_id` field into the issue metadata (stored as a custom field or a comment/label depending on the GitHub Projects API capabilities). A new API endpoint `PUT /api/v1/pipelines/{project_id}/assignment` sets/clears the assigned pipeline.

**Rationale**: The spec requires (FR-011) that assigned pipelines automatically apply to new issues. The simplest integration point is the existing `github_projects/service.py` which already handles issue creation. Adding a column to `project_settings` follows the established pattern (that table already stores `workflow_config`, `agent_pipeline_mappings`, etc.). The issue creation hook reads the assignment and injects metadata, keeping the pipeline assignment logic centralized.

**Alternatives Considered**:
- **Separate `project_pipeline_assignments` table**: Rejected — only one pipeline per project is assigned at a time (the spec says "the assigned Agent Pipeline configuration," singular). A single column suffices.
- **GitHub Actions webhook**: Rejected — adds external dependency, latency, and complexity. The issue creation already goes through our backend.

---

## R9: "Add Agent" Picker Data Source

**Task**: Determine how the "+ Add Agent" picker should source its list of available agents.

**Decision**: Reuse the existing `useAgents()` hook (which fetches from `GET /api/v1/agents/{project_id}`) to populate the agent picker. Filter to agents with `status === 'active'`. The picker is a popover/dropdown rendered inside the `StageCard` component, consistent with the existing "Add Agent" button pattern already implemented in spec 026.

**Rationale**: The spec requires (FR-001) that the picker is "populated exclusively with agents saved on the Agents page." The `useAgents()` hook already provides this exact data. No new API endpoint is needed. The existing `StageCard` already has an "Add Agent" button; it just needs to be wired to the agent list from the hook rather than a static list.

**Alternatives Considered**:
- **Dedicated agent search endpoint**: Rejected — the agent list is already small enough (< 50 per project) to load in full. Search/filter can be done client-side if needed.
- **Agent discovery from `.github/agents/` only**: Rejected — the spec says "agents saved on the Agents page," which includes both repo-sourced and locally created agents.

---

## R10: Saved Workflow Card Enhancement Strategy

**Task**: Determine how to enrich Saved Workflow cards to show stages, agents, models, tool counts, and the flow graph.

**Decision**: Modify the existing `SavedWorkflowsList` component to fetch full pipeline data (not just summaries) and render enriched cards. Each card displays:
- Pipeline name and description
- Preset badge (if `is_preset`)
- Compact flow graph (`PipelineFlowGraph` component)
- Expandable details: stages → agents → model name + tool count per agent

The list endpoint `GET /api/v1/pipelines/{project_id}` already returns `PipelineConfigSummary` objects. Extend the summary to include `stages` (the full JSON) so the frontend has enough data to render flow graphs and agent details without a per-pipeline detail fetch. Alternatively, the list endpoint returns full `PipelineConfig` objects (the pipeline list is small enough — under 100 per project — to justify returning full data).

**Rationale**: The spec requires (FR-008) detailed information on each card. Returning full pipeline data in the list endpoint avoids N+1 requests (one detail fetch per card). The pipeline list is bounded (< 100 per project per constraint) and each pipeline's JSON is small (< 10KB), so the total response size is manageable (< 1MB worst case). This follows the existing pattern in the codebase where list endpoints return enough data for card rendering.

**Alternatives Considered**:
- **Summary list + lazy detail fetch on hover/expand**: Rejected — adds complexity, perceived latency on card interaction, and N+1 query pattern.
- **GraphQL with field selection**: Rejected — the project uses REST exclusively.
