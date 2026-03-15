# Data Model: Reinvent Agent Pipeline Creation UX

**Feature Branch**: `037-pipeline-builder-ux`
**Date**: 2026-03-12
**Input**: [spec.md](./spec.md), [research.md](./research.md)

## Entity Relationship Diagram

```
┌─────────────────┐
│ PipelineConfig   │
│─────────────────│
│ id: string       │
│ project_id       │
│ name             │
│ description      │
│ is_preset        │
│ preset_id        │
│ created_at       │
│ updated_at       │
├─────────────────┤
│ stages: Stage[]  │──┐
└─────────────────┘  │  1:N
                      │
    ┌─────────────────┘
    ▼
┌─────────────────────┐
│ PipelineStage        │
│─────────────────────│
│ id: string           │
│ name: string         │
│ order: number        │
│ execution_mode?      │ ← DEPRECATED (retained for backward compat)
│ agents?              │ ← DEPRECATED (retained for backward compat)
├─────────────────────┤
│ groups: Group[]      │──┐
└─────────────────────┘  │  1:N
                          │
    ┌─────────────────────┘
    ▼
┌─────────────────────────┐
│ ExecutionGroup           │
│─────────────────────────│
│ id: string               │
│ order: number            │
│ execution_mode: string   │  "sequential" | "parallel"
├─────────────────────────┤
│ agents: AgentNode[]      │──┐
└─────────────────────────┘  │  1:N
                              │
    ┌─────────────────────────┘
    ▼
┌─────────────────────────┐
│ PipelineAgentNode        │
│─────────────────────────│
│ id: string               │
│ agent_slug: string       │
│ agent_display_name       │
│ model_id: string         │
│ model_name: string       │
│ tool_ids: string[]       │
│ tool_count: number       │
│ config: Record<>         │
└─────────────────────────┘
```

## Entity Definitions

### PipelineConfig

The top-level pipeline definition. Unchanged from current model.

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| id | string | ✅ | generated | Unique identifier |
| project_id | string | ✅ | — | Owning project |
| name | string | ✅ | — | Pipeline display name (1–100 chars) |
| description | string | ❌ | `""` | Optional description (max 500 chars) |
| stages | PipelineStage[] | ✅ | `[]` | Ordered list of stages |
| is_preset | boolean | ❌ | `false` | Whether this is a preset pipeline |
| preset_id | string | ❌ | `""` | Preset identifier |
| created_at | string (ISO 8601) | ✅ | generated | Creation timestamp |
| updated_at | string (ISO 8601) | ✅ | generated | Last update timestamp |

### PipelineStage

A column in the pipeline. **Updated** to include `groups` array.

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| id | string | ✅ | generated | Unique identifier |
| name | string | ✅ | — | Stage display name (1–100 chars) |
| order | number | ✅ | — | Left-to-right display/execution order |
| groups | ExecutionGroup[] | ❌ | `[]` | Ordered list of execution groups (new) |
| agents | PipelineAgentNode[] | ❌ | `[]` | **DEPRECATED** — flat agent list for backward compatibility |
| execution_mode | `"sequential"` \| `"parallel"` | ❌ | `"sequential"` | **DEPRECATED** — stage-level mode for backward compatibility |

**Invariants**:
- When `groups` is populated, `agents` and `execution_mode` are ignored by the UI
- When `groups` is empty/absent, legacy migration wraps `agents` into a single group
- A stage always has at least one group (empty groups are valid)

### ExecutionGroup *(NEW)*

A container within a stage holding one or more agents with a shared execution mode.

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| id | string | ✅ | generated | Unique identifier |
| order | number | ✅ | — | Top-to-bottom execution order within stage |
| execution_mode | `"sequential"` \| `"parallel"` | ✅ | `"sequential"` | How agents in this group execute |
| agents | PipelineAgentNode[] | ✅ | `[]` | Ordered list of agent assignments |

**Invariants**:
- `execution_mode` must be one of `"sequential"` or `"parallel"`
- Groups within a stage execute in `order` sequence (top-to-bottom)
- Agents within a `"sequential"` group execute in array order
- Agents within a `"parallel"` group execute concurrently
- A group with zero agents is valid (displays empty-state prompt)
- A `"parallel"` group with fewer than 2 agents is valid (no auto-downgrade at group level — user intent is preserved)

### PipelineAgentNode

An individual agent assignment. **Unchanged** from current model.

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| id | string | ✅ | generated | Unique identifier (per-assignment, not per-agent) |
| agent_slug | string | ✅ | — | Agent type identifier (e.g., `"speckit.specify"`) |
| agent_display_name | string | ❌ | `""` | Human-readable agent name |
| model_id | string | ❌ | `""` | Selected AI model ID |
| model_name | string | ❌ | `""` | Selected AI model display name |
| tool_ids | string[] | ❌ | `[]` | Assigned tool identifiers |
| tool_count | number | ❌ | `0` | Count of assigned tools |
| config | Record<string, unknown> | ❌ | `{}` | Additional agent configuration |

## Relationships

| Relationship | From | To | Cardinality | Description |
|-------------|------|------|-------------|-------------|
| contains | PipelineConfig | PipelineStage | 1:N | Pipeline has ordered stages |
| contains | PipelineStage | ExecutionGroup | 1:N | Stage has ordered groups |
| contains | ExecutionGroup | PipelineAgentNode | 1:N | Group has ordered agents |

## Validation Rules

### PipelineConfig
- `name` must be 1–100 characters
- `description` must be ≤500 characters
- `stages` array can be empty (empty pipeline)

### PipelineStage
- `name` must be 1–100 characters
- `order` must be a non-negative integer
- Stage order values must be unique within a pipeline

### ExecutionGroup
- `execution_mode` must be `"sequential"` or `"parallel"`
- `order` must be a non-negative integer
- Group order values must be unique within a stage
- At least one group must exist per stage (enforced at UI level; backend accepts empty groups array for migration flexibility)

### PipelineAgentNode
- `agent_slug` must be non-empty
- `id` must be unique within the pipeline (not just within the group)

## State Transitions

### Pipeline Lifecycle

```
Empty → Creating (user clicks "New Pipeline")
Creating → Editing (user adds first stage)
Editing → Saved (user saves pipeline)
Saved → Editing (user loads and modifies pipeline)
```

### ExecutionGroup Mode Toggle

```
Sequential ←→ Parallel (single toggle interaction, FR-004)
```

No intermediate states. The toggle is immediate and visual layout updates synchronously.

### Agent Drag-and-Drop States

```
Idle → Drag Started (user picks up agent card)
Drag Started → Dragging Over (agent hovers over valid drop target)
Dragging Over → Dropped (agent released on valid target)
Dragging Over → Cancelled (agent released outside valid target, or browser loses focus)
Dropped → Idle (state updated, agent in new position)
Cancelled → Idle (agent returns to original position)
```

### Legacy Migration

```
Old Format (no groups) → Detection at load time → Migration (wrap agents in single group) → New Format (groups populated)
New Format → Save → Persisted in new format (migration is one-way)
```

## TypeScript Type Definitions (Frontend)

```typescript
/** NEW — Execution group within a pipeline stage */
export interface ExecutionGroup {
  id: string;
  order: number;
  execution_mode: 'sequential' | 'parallel';
  agents: PipelineAgentNode[];
}

/** UPDATED — PipelineStage with optional groups */
export interface PipelineStage {
  id: string;
  name: string;
  order: number;
  /** @new Ordered execution groups within this stage */
  groups?: ExecutionGroup[];
  /** @deprecated Use groups[].agents instead. Retained for backward compatibility. */
  agents: PipelineAgentNode[];
  /** @deprecated Use groups[].execution_mode instead. Retained for backward compatibility. */
  execution_mode?: 'sequential' | 'parallel';
}
```

## Python Model Definitions (Backend)

```python
class ExecutionGroup(BaseModel):
    """A group of agents within a stage sharing an execution mode."""
    id: str
    order: int = 0
    execution_mode: str = Field(default="sequential")
    agents: list[PipelineAgentNode] = Field(default_factory=list)

    @field_validator("execution_mode")
    @classmethod
    def validate_execution_mode(cls, v: str) -> str:
        if v not in ("sequential", "parallel"):
            raise ValueError("execution_mode must be 'sequential' or 'parallel'")
        return v


class PipelineStage(BaseModel):
    """A named step within a pipeline containing execution groups."""
    id: str
    name: str = Field(..., min_length=1, max_length=100)
    order: int
    groups: list[ExecutionGroup] = Field(default_factory=list)
    # Deprecated — retained for backward compatibility
    agents: list[PipelineAgentNode] = Field(default_factory=list)
    execution_mode: str = Field(default="sequential")
```

## Migration Logic

### Detection

A pipeline is in legacy format if any stage has:
- `groups` is undefined, null, or an empty array, AND
- `agents` is a non-empty array

### Transformation

For each legacy stage:
1. Create a single `ExecutionGroup` with:
   - `id`: newly generated
   - `order`: 0
   - `execution_mode`: stage's `execution_mode` (default `"sequential"`)
   - `agents`: stage's `agents` array (preserving order)
2. Set `stage.groups = [newGroup]`
3. Retain `stage.agents` and `stage.execution_mode` for backward compat (deprecated fields)

### Idempotency

If `stage.groups` is already populated, the migration is a no-op for that stage. This makes the migration safe to run repeatedly.
