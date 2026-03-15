# Research: Parallel Agent Layout in Pipelines

**Feature Branch**: `033-parallel-agent-layout`
**Date**: 2026-03-10
**Status**: Complete

## Research Task 1: Parallel Execution Model for Pipeline Stages

**Context**: The current pipeline execution engine (`PipelineState` in `workflow_orchestrator/models.py`) tracks agents sequentially via `current_agent_index`. When a stage is reached, agents run one at a time. We need to determine how to extend this for concurrent dispatch.

### Decision: Use `asyncio.gather` with per-agent sub-issue creation

**Rationale**: The existing pipeline launch flow (`backend/src/api/pipelines.py:199-380`) already creates sub-issues for agents and assigns them via the Copilot polling service. For parallel stages, all agents in the stage should have their sub-issues created simultaneously and assigned concurrently. `asyncio.gather` is the idiomatic Python approach for fan-out/fan-in concurrency in an async codebase. It naturally provides the barrier semantics required (all must complete before proceeding).

**Alternatives considered**:

- **`asyncio.TaskGroup`** (Python 3.11+): More modern, but `asyncio.gather` with `return_exceptions=True` gives explicit control over partial failure handling which the spec requires (FR-006). TaskGroup cancels siblings on first failure, which is undesirable — we want all parallel agents to complete or fail independently so users can see which specific agents failed.
- **Background task queue (Celery/RQ)**: Over-engineered for this use case. The existing polling-based execution model does not use a task queue and adding one would violate the Simplicity principle.
- **Thread pool executor**: Unnecessary complexity since the codebase is fully async.

---

## Research Task 2: Data Model Extension for Parallel Stages

**Context**: The `PipelineStage` model currently has `id`, `name`, `order`, and `agents[]`. There is no field to distinguish whether a stage's agents should run in parallel or sequentially. The `pipeline_configs.stages` column stores JSON, so schema changes are non-destructive.

### Decision: Add `execution_mode` field to `PipelineStage` with default `"sequential"`

**Rationale**: A single string field (`"sequential"` | `"parallel"`) on the stage model is the minimal change that captures the user's intent. Defaulting to `"sequential"` ensures backward compatibility — existing pipelines without this field will behave exactly as before (FR-008). The JSON storage means no SQL migration is needed; the field is simply added to the Pydantic model with a default value.

**Alternatives considered**:

- **Separate `parallel_group_id` field**: Groups agents by a shared ID. More flexible but introduces unnecessary indirection — stages already group agents, so the stage itself is the natural grouping boundary.
- **Nested stage structure (stages within stages)**: Supports arbitrary nesting but violates YAGNI. The spec only requires one level of parallelism within a stage.
- **DAG representation**: The technical notes suggest considering a DAG. While powerful, the spec requirements are fully satisfied by the simpler stage-based model. A DAG can be introduced later if needed without breaking the stage API.

---

## Research Task 3: Frontend Drag-and-Drop for Parallel Agent Placement

**Context**: The `StageCard` component uses `@dnd-kit/sortable` with `verticalListSortingStrategy` for reordering agents within a stage. The current implementation only supports vertical stacking. We need to support horizontal (side-by-side) placement.

### Decision: Switch sorting strategy based on `execution_mode` and add "Add Parallel Agent" affordance

**Rationale**: `@dnd-kit/sortable` already supports `rectSortingStrategy` which works for grid/horizontal layouts. The `StageCard` already imports both strategies (`verticalListSortingStrategy` and `rectSortingStrategy`). When a stage's `execution_mode` is `"parallel"`, use `rectSortingStrategy` and render agents in a CSS flex-row container. The "Add Parallel Agent" affordance will be a `+` button on the side of an existing agent card, toggling the stage's `execution_mode` to `"parallel"` when a second agent is added.

**Alternatives considered**:

- **Drop zone detection (drop-onto vs drop-between)**: Complex gesture recognition to distinguish parallel grouping from sequential insertion. High implementation cost and discoverability issues. An explicit button is simpler and more accessible.
- **New drag-and-drop library**: The existing `@dnd-kit` already supports the required functionality. No need to switch libraries.
- **Separate parallel stage component**: Could create a distinct `ParallelStageCard`, but this duplicates logic. Better to extend the existing `StageCard` with conditional rendering based on `execution_mode`.

---

## Research Task 4: Visual Differentiation of Parallel Stages

**Context**: The spec requires parallel stages to be visually distinct — enclosed in a shared container with a label/icon, with connector lines only between stage groups (not between parallel siblings).

### Decision: Wrap parallel agents in a styled container with "Runs in Parallel" label and parallel icon

**Rationale**: When `execution_mode === "parallel"` and `agents.length > 1`, the `StageCard` renders agents in a horizontal flex layout within a distinct visual band. A `GitBranch` or custom split-lane icon from `lucide-react` (already in the project) signals parallel execution. Connector lines between stages are already rendered at the `PipelineBoard` level — no connectors need to be added between parallel siblings since they share the same stage container. Tooltips on hover are added via the existing `Tooltip` component (already imported in `StageCard`).

**Alternatives considered**:

- **Swimlane/track visualization**: Complex layout that requires significant canvas rework. Overkill for 2–4 agents side by side.
- **Separate visual component with its own state**: Violates DRY — the `StageCard` already manages agent rendering, and splitting it adds unnecessary complexity.

---

## Research Task 5: Partial Failure Handling in Parallel Stages

**Context**: FR-006 requires the pipeline to halt on partial failure, mark the stage as failed, and identify which agent(s) failed. The current `PipelineState` uses `current_agent_index` and `error` field for single-agent tracking.

### Decision: Extend `PipelineState` with per-agent status tracking for parallel stages

**Rationale**: For parallel stages, the `PipelineState` needs to track individual agent outcomes rather than a single sequential index. Add a `parallel_agent_statuses` dict mapping agent names to their status (`"pending"` | `"running"` | `"completed"` | `"failed"`). The stage is considered complete when all agents are `"completed"`. If any agent is `"failed"`, the stage is marked as failed and the pipeline halts. The existing `error` field captures the first failure message; a new `failed_agents` list captures all failing agent identifiers for UI display.

**Alternatives considered**:

- **Reuse `current_agent_index` with parallel semantics**: Ambiguous — an index implies sequential ordering. Parallel execution needs set-based completion tracking.
- **External status table**: Adding a new database table for per-agent-per-run status. Over-engineered for in-memory state tracking; the polling service already manages state in memory.

---

## Research Task 6: Backward Compatibility for Existing Pipelines

**Context**: FR-008 mandates that existing pipelines work without modification. The `stages` JSON in `pipeline_configs` does not currently include `execution_mode`.

### Decision: Default `execution_mode` to `"sequential"` via Pydantic default; no SQL migration needed

**Rationale**: Since stages are stored as JSON and deserialized by Pydantic, adding a new field with a default value means existing JSON (which lacks the field) will automatically deserialize with `execution_mode="sequential"`. This is a zero-migration, zero-risk change. The API layer is additive — the new field is optional in requests and always present in responses. No API versioning is needed since existing clients can simply ignore the new field.

**Alternatives considered**:

- **SQL migration to backfill**: Unnecessary since JSON deserialization handles the default.
- **API versioning (v2 endpoints)**: Overkill for an additive, backward-compatible change. The existing API contract is not broken.

---

## Research Task 7: Real-Time Status Indicators for Parallel Agents

**Context**: FR-011 (P3) requires showing running/completed/failed status per agent during pipeline execution. The app uses WebSocket for real-time updates.

### Decision: Extend existing WebSocket pipeline status events with per-agent status payload

**Rationale**: The application already has WebSocket infrastructure for real-time updates. Pipeline status events can include a `parallel_agent_statuses` object alongside the existing stage-level status. The frontend `PipelineFlowGraph` component (which visualizes running pipelines) can be extended to render per-agent status indicators (spinner for running, checkmark for completed, X for failed) using existing icon components from `lucide-react`.

**Alternatives considered**:

- **Polling-based status updates**: Higher latency and server load. WebSocket is already in place.
- **Server-Sent Events (SSE)**: Another valid option but WebSocket is already the established pattern in this codebase.
