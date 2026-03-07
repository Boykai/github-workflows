# Research: Pipeline Page — CRUD for Agent Pipeline Configurations

**Feature**: 026-pipeline-crud | **Date**: 2026-03-07

## R1: Pipeline Data Persistence Strategy

**Task**: Determine the best approach for storing saved pipeline configurations given the existing SQLite + aiosqlite stack.

**Decision**: Create a dedicated `pipeline_configs` table in SQLite with JSON-serialized stage/agent data.

**Rationale**: The existing `project_settings.workflow_config` column stores a single `WorkflowConfiguration` JSON blob per project. Pipeline CRUD requires multiple named configurations per project with independent lifecycle (create, update, delete by ID). A dedicated table provides:
- Individual record addressing via primary key (UUID)
- Efficient list queries (`SELECT * FROM pipeline_configs WHERE project_id = ?`)
- Standard SQL-based deletion without JSON manipulation
- Natural migration path following the established pattern (`013_pipeline_configs.sql`)

**Alternatives Considered**:
- **JSON array in `project_settings`**: Rejected — mixing concerns with existing workflow config, no individual record IDs, requires full read-modify-write for every CRUD operation, no efficient single-record queries.
- **Separate JSON file per pipeline**: Rejected — SQLite already established as the persistence layer; file-based storage adds complexity and breaks transactional consistency.

---

## R2: Pipeline State Model Design

**Task**: Design the state model for a pipeline configuration that supports ordered stages with agent assignments and per-agent model selection.

**Decision**: Use a hierarchical JSON structure: `Pipeline → Stage[] → AgentNode[]`, where each `AgentNode` contains an `agentSlug`, `modelId`, and optional config. Stages maintain explicit `order` fields for drag-and-drop reordering.

**Rationale**: The spec requires ordered stages (FR-002, FR-015) with agents that have per-agent model selection (FR-007). A flat list of stage objects with nested agent arrays is the simplest serializable structure that captures all relationships. The `order` field on stages supports drag-and-drop reordering without array index dependency. This mirrors the existing `agent_mappings: dict[str, list[AgentAssignment]]` pattern in `WorkflowConfiguration` but scoped to individual pipeline configs.

**Alternatives Considered**:
- **Graph-based model**: Rejected — the spec describes a linear stage pipeline, not a DAG. YAGNI per Constitution Principle V.
- **Normalized tables for stages and agents**: Rejected — adds migration complexity and JOIN overhead for what is essentially a document-oriented data model (pipeline configs are always loaded/saved as complete units).

---

## R3: Model Selection Data Source

**Task**: Determine where model metadata (name, provider, context window, cost tier) comes from and how to serve it to the frontend.

**Decision**: Serve model metadata from a backend API endpoint (`GET /api/v1/models`) backed by a static configuration file or in-memory registry. Cache on the frontend with TanStack Query (staleTime: 5 minutes).

**Rationale**: The spec assumes "an existing models list or configuration is available" (Assumptions section). The system already has a pattern for serving agent discovery data via `GET /workflow/agents` (which returns `AvailableAgent[]`). A similar endpoint for models provides a single source of truth, allows backend-side updates without frontend redeployment, and follows the established API pattern. Frontend caching with TanStack Query avoids redundant requests (spec technical note: "cache results to avoid redundant requests").

**Alternatives Considered**:
- **Hardcoded in frontend**: Rejected — no single source of truth, requires frontend redeployment to update model list.
- **Fetching from external provider APIs**: Rejected — out of scope (spec excludes model management); adds latency, auth complexity, and external dependency.

---

## R4: Edit Mode vs. New Mode State Management

**Task**: Determine how to track whether the pipeline board is in "new pipeline" or "editing existing" mode, and how to manage unsaved changes.

**Decision**: Track `editingPipelineId: string | null` in the `usePipelineConfig` hook. When `null`, the board is in creation mode; when set, it's in edit mode. Maintain a local `boardState` (the working copy) separate from the persisted state, with an `isDirty` flag computed by deep comparison. This follows the exact pattern used in `useAgentConfig.ts` (lines 41–113).

**Rationale**: The existing `useAgentConfig` hook already implements this pattern with `localMappings` vs. server state and `isDirty` tracking. Reusing this proven pattern ensures consistency and reduces cognitive load. The spec requires visual distinction between modes (FR-014) and unsaved changes protection (FR-018, FR-019), both of which depend on this state.

**Alternatives Considered**:
- **URL state (route params)**: Rejected as primary mechanism — URL can be used for deep-linking (`/pipeline?id=xxx`) but the core state must be in the hook for reactivity. URL state is additive, not a replacement.
- **Separate components for new vs. edit**: Rejected — duplicates UI code, violates DRY (Constitution Principle V).

---

## R5: Drag-and-Drop Stage Reordering

**Task**: Determine the best approach for drag-and-drop stage reordering within the pipeline board.

**Decision**: Reuse the existing `@dnd-kit/core` + `@dnd-kit/sortable` libraries already installed in the project. Wrap stages in a `SortableContext` within the `PipelineBoard` component. Use `arrayMove` from `@dnd-kit/sortable` for reorder operations.

**Rationale**: `@dnd-kit` is already installed (core ^6.3.1, sortable ^10.0.0, modifiers, utilities) and actively used in `AgentConfigRow.tsx` for agent drag-and-drop. Using the same library for stage reordering ensures consistency, requires no new dependencies, and leverages the team's existing familiarity. The sortable preset provides vertical list reordering out of the box.

**Alternatives Considered**:
- **Manual drag implementation**: Rejected — reinventing wheel when @dnd-kit is already available.
- **react-beautiful-dnd**: Rejected — in maintenance mode, and @dnd-kit is already the project standard.

---

## R6: Reusable ModelSelector Component

**Task**: Design a reusable model picker component that can be embedded inline on agent cards.

**Decision**: Create a `ModelSelector` popover component using existing UI primitives (button trigger + popover panel). Models are grouped by `provider`, each entry shows `name`, `contextWindowSize`, `costTier`. Recently used models (tracked in component/session state) appear in a pinned "Recent" group at the top.

**Rationale**: The spec requires models "grouped logically (e.g., by provider or capability tier)" (FR-008) with metadata visible and recently used models surfaced (FR-009). A popover triggered from the agent card provides inline selection without page navigation or full-screen modals, matching the "compact dropdown or popover" suggestion in the UI/UX description. Grouping by provider is the most natural taxonomy for users selecting AI models.

**Alternatives Considered**:
- **Side panel / drawer**: Rejected for initial implementation — adds layout complexity; can be added later if the model list grows very large. YAGNI.
- **Full-page modal**: Rejected — too heavy for a frequent inline action.
- **Native `<select>` dropdown**: Rejected — cannot display grouped metadata (context size, cost tier) in a native dropdown.

---

## R7: Unsaved Changes Protection Pattern

**Task**: Determine the best approach for preventing accidental data loss from unsaved changes.

**Decision**: Implement two layers of protection:
1. **In-app dialog**: A custom `UnsavedChangesDialog` component triggered when clicking a different saved workflow or discarding. Uses the existing card/button UI components.
2. **Browser navigation guard**: Use `window.onbeforeunload` event to warn when navigating away from the page with unsaved changes. Additionally use React Router's `useBlocker` hook for in-app route changes.

**Rationale**: The spec requires both in-app confirmation (FR-018) and browser navigation guards (FR-019). The dual approach covers all exit paths. The existing codebase does not have a navigation guard pattern, so this introduces the minimal necessary implementation. `useBlocker` is a standard React Router v7 API for this purpose.

**Alternatives Considered**:
- **Browser-only `beforeunload`**: Rejected — doesn't cover clicking a different saved workflow within the same page.
- **Auto-save**: Rejected — spec explicitly requires save as a manual action with toolbar button.

---

## R8: API Endpoint Design for Pipeline CRUD

**Task**: Design REST API endpoints for pipeline configuration CRUD.

**Decision**: Follow the existing FastAPI router pattern with project-scoped endpoints:

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/api/v1/pipelines` | List all pipeline configs for the current project |
| `POST` | `/api/v1/pipelines` | Create a new pipeline config |
| `GET` | `/api/v1/pipelines/{pipeline_id}` | Get a single pipeline config |
| `PUT` | `/api/v1/pipelines/{pipeline_id}` | Update an existing pipeline config |
| `DELETE` | `/api/v1/pipelines/{pipeline_id}` | Delete a pipeline config |
| `GET` | `/api/v1/models` | List available AI models with metadata |

**Rationale**: This follows standard REST conventions and mirrors the existing API structure in the codebase (e.g., agents API: `GET/POST /{project_id}`, `PATCH/DELETE /{project_id}/{agent_id}`). Project scoping is handled via session context (same as other APIs). The models endpoint is separate because models are a shared resource, not scoped to a specific pipeline.

**Alternatives Considered**:
- **Nesting under `/workflow/pipelines`**: Rejected — pipelines are a distinct resource, not a sub-resource of workflow config.
- **GraphQL**: Rejected — the project uses REST exclusively; adding GraphQL would be an unnecessary paradigm shift.
