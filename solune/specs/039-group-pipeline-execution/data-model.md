# Data Model: Group-Aware Pipeline Execution & Tracking Table

**Feature Branch**: `039-group-pipeline-execution`
**Date**: 2026-03-13
**Input**: [spec.md](./spec.md), [research.md](./research.md)

## Entity Relationship Diagram

```
                    EXISTING (pipeline config layer)
┌─────────────────┐
│ PipelineConfig   │
│─────────────────│
│ stages: Stage[]  │──┐
└─────────────────┘  │ 1:N
    ┌────────────────┘
    ▼
┌─────────────────────┐
│ PipelineStage        │
│─────────────────────│
│ groups: Group[]      │──┐
│ agents: AgentNode[]  │  │ (deprecated, backward-compat flattened view)
└─────────────────────┘  │ 1:N
    ┌────────────────────┘
    ▼
┌──────────────────────────┐
│ ExecutionGroup            │   ← EXISTS in pipeline.py
│──────────────────────────│
│ id, order, execution_mode │
│ agents: AgentNode[]       │──┐
└──────────────────────────┘  │ 1:N
    ┌─────────────────────────┘
    ▼
┌──────────────────────────┐
│ PipelineAgentNode         │   ← EXISTS in pipeline.py
│──────────────────────────│
│ id, agent_slug, model_id  │
└──────────────────────────┘

            ↓ load_pipeline_as_agent_mappings() converts to workflow layer ↓

                    NEW + UPDATED (workflow execution layer)
┌────────────────────────────────┐
│ WorkflowConfiguration          │
│────────────────────────────────│
│ agent_mappings: dict[str,      │   ← EXISTING (flat, unchanged)
│   list[AgentAssignment]]       │
│ group_mappings: dict[str,      │   ← NEW
│   list[ExecutionGroupMapping]] │
│ stage_execution_modes: dict    │   ← EXISTING
└────────────────────────────────┘
         │
         │ group_mappings[status] provides ordered groups
         ▼
┌─────────────────────────────┐
│ ExecutionGroupMapping (NEW)  │
│─────────────────────────────│
│ group_id: str                │
│ order: int                   │
│ execution_mode: str          │
│ agents: list[AgentAssignment]│
└─────────────────────────────┘

         ↓ At execution time, converted to runtime state ↓

                    NEW + UPDATED (runtime state layer)
┌──────────────────────────────┐
│ PipelineState (UPDATED)       │
│──────────────────────────────│
│ agents: list[str]             │   ← EXISTING (flat, kept for fallback)
│ current_agent_index: int      │   ← EXISTING (flat fallback)
│ groups: list[PipelineGroupInfo]│  ← NEW
│ current_group_index: int      │   ← NEW
│ current_agent_index_in_group  │   ← NEW
└──────────────────────────────┘
         │
         │ groups[current_group_index]
         ▼
┌──────────────────────────────┐
│ PipelineGroupInfo (NEW)       │
│──────────────────────────────│
│ group_id: str                 │
│ execution_mode: str           │
│ agents: list[str]             │
│ agent_statuses: dict[str,str] │   (for parallel completion tracking)
└──────────────────────────────┘

         ↓ Tracking table renders group info ↓

                    UPDATED (tracking table layer)
┌──────────────────────────────┐
│ AgentStep (UPDATED)           │
│──────────────────────────────│
│ index: int                    │   ← EXISTING
│ status: str                   │   ← EXISTING
│ agent_name: str               │   ← EXISTING
│ model: str                    │   ← EXISTING
│ state: str                    │   ← EXISTING
│ group_label: str              │   ← NEW ("G1 (series)", "G2 (parallel)")
│ group_order: int              │   ← NEW
│ group_execution_mode: str     │   ← NEW
└──────────────────────────────┘
```

## New Entity Definitions

### ExecutionGroupMapping *(NEW)*

A workflow-layer representation of an execution group within a pipeline stage. Created during the conversion from `PipelineConfig` → `WorkflowConfiguration`.

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| group_id | str | ✅ | — | Unique group identifier (carried from `ExecutionGroup.id`) |
| order | int | ✅ | `0` | Execution order within the stage (0-based) |
| execution_mode | str | ✅ | `"sequential"` | `"sequential"` or `"parallel"` |
| agents | list[AgentAssignment] | ✅ | `[]` | Ordered list of agent assignments in this group |

**Validation Rules**:
- `execution_mode` must be `"sequential"` or `"parallel"`
- `order` must be a non-negative integer
- `agents` can be empty (empty groups are skipped during execution)

**Location**: `backend/src/models/workflow.py`

### PipelineGroupInfo *(NEW)*

Runtime tracking of an execution group during pipeline execution. Created from `ExecutionGroupMapping` when a pipeline starts.

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| group_id | str | ✅ | — | Group identifier (matches `ExecutionGroupMapping.group_id`) |
| execution_mode | str | ✅ | `"sequential"` | `"sequential"` or `"parallel"` |
| agents | list[str] | ✅ | `[]` | Ordered list of agent slugs in this group |
| agent_statuses | dict[str, str] | ❌ | `{}` | Per-agent completion status for parallel groups. Values: `"pending"`, `"active"`, `"completed"`, `"failed"` |

**Location**: `backend/src/services/workflow_orchestrator/models.py`

## Updated Entity Definitions

### WorkflowConfiguration *(UPDATED)*

Added one new field. All existing fields unchanged.

| Field | Type | Change | Default | Description |
|-------|------|--------|---------|-------------|
| group_mappings | dict[str, list[ExecutionGroupMapping]] | **NEW** | `{}` | Status name → ordered list of execution groups. Empty dict for legacy pipelines |

**Backward Compatibility**: Default `{}` means all existing pipelines work without changes.

### PipelineState *(UPDATED)*

Added three new fields. All existing fields unchanged.

| Field | Type | Change | Default | Description |
|-------|------|--------|---------|-------------|
| groups | list[PipelineGroupInfo] | **NEW** | `[]` | Groups for the current status. Empty for legacy pipelines |
| current_group_index | int | **NEW** | `0` | Index into `groups` list |
| current_agent_index_in_group | int | **NEW** | `0` | Index into current group's agents list |

**Updated Properties**:

```python
@property
def current_agent(self) -> str | None:
    if self.groups:
        if self.current_group_index < len(self.groups):
            group = self.groups[self.current_group_index]
            if self.current_agent_index_in_group < len(group.agents):
                return group.agents[self.current_agent_index_in_group]
        return None
    # Flat fallback (existing behavior)
    if self.current_agent_index < len(self.agents):
        return self.agents[self.current_agent_index]
    return None

@property
def is_complete(self) -> bool:
    if self.groups:
        if self.current_group_index >= len(self.groups):
            return True
        group = self.groups[self.current_group_index]
        if group.execution_mode == "parallel" and group.agent_statuses:
            return all(
                s in ("completed", "failed")
                for s in group.agent_statuses.values()
            )
        return False
    # Flat fallback (existing behavior)
    if self.execution_mode == "parallel" and self.parallel_agent_statuses:
        return all(s in ("completed", "failed") for s in self.parallel_agent_statuses.values())
    return self.current_agent_index >= len(self.agents)
```

### AgentStep *(UPDATED)*

Added three new fields. All existing fields unchanged.

| Field | Type | Change | Default | Description |
|-------|------|--------|---------|-------------|
| group_label | str | **NEW** | `""` | Display label, e.g., `"G1 (series)"`, `"G2 (parallel)"` |
| group_order | int | **NEW** | `0` | Group execution order within the stage |
| group_execution_mode | str | **NEW** | `""` | `"sequential"` or `"parallel"` (empty for legacy) |

## Relationships

| Relationship | From | To | Cardinality | Change | Description |
|-------------|------|------|-------------|--------|-------------|
| contains | WorkflowConfiguration | ExecutionGroupMapping | 1:N per status | **NEW** | Config holds ordered groups per status |
| contains | ExecutionGroupMapping | AgentAssignment | 1:N | **NEW** | Group holds ordered agent assignments |
| tracks | PipelineState | PipelineGroupInfo | 1:N | **NEW** | Runtime state holds groups for current status |
| renders | AgentStep | (group info) | 1:1 | **NEW** | Each step carries its group label |

## State Transitions

### Group Execution Lifecycle

```
Pipeline enters status
    │
    ├── groups configured?
    │   ├── YES → Initialize groups from group_mappings[status]
    │   │         Set current_group_index = 0
    │   │         current_agent_index_in_group = 0
    │   │
    │   │    ┌──────────────────────────────┐
    │   │    │ Process Current Group          │
    │   │    │                                │
    │   │    │  Mode = sequential?            │
    │   │    │  ├── YES → Assign agent[idx]   │
    │   │    │  │         Wait for completion  │
    │   │    │  │         idx++               │
    │   │    │  │         Repeat until group done│
    │   │    │  │                              │
    │   │    │  └── NO (parallel)              │
    │   │    │      → Assign ALL agents (2s stagger) │
    │   │    │        Wait for ALL to complete  │
    │   │    │        (or fail)                │
    │   │    └──────────────────────────────┘
    │   │         │
    │   │    Group complete?
    │   │    ├── YES → current_group_index++
    │   │    │         current_agent_index_in_group = 0
    │   │    │         More groups? → Process next group
    │   │    │         No more groups? → Transition to next status
    │   │    └── NO → Continue waiting
    │   │
    │   └── NO → Flat fallback (existing sequential/parallel logic)
    │
    └── Status transition
```

### Parallel Group Agent States

```
pending → active (assigned to Copilot)
active → completed (agent posts Done!)
active → failed (agent errors or times out)
```

All agents in a parallel group are set to "active" during assignment. The group is complete when all agents are "completed" or "failed".

## Python Model Definitions

### ExecutionGroupMapping (NEW — workflow.py)

```python
class ExecutionGroupMapping(BaseModel):
    """A group of agents within a workflow status sharing an execution mode."""

    group_id: str = Field(..., description="Unique group identifier")
    order: int = Field(default=0, description="Execution order within the stage")
    execution_mode: str = Field(
        default="sequential", description="'sequential' or 'parallel'"
    )
    agents: list[AgentAssignment] = Field(
        default_factory=list, description="Ordered agent assignments in this group"
    )

    @field_validator("execution_mode")
    @classmethod
    def validate_execution_mode(cls, v: str) -> str:
        if v not in ("sequential", "parallel"):
            raise ValueError("execution_mode must be 'sequential' or 'parallel'")
        return v
```

### PipelineGroupInfo (NEW — models.py)

```python
@dataclass
class PipelineGroupInfo:
    """Runtime tracking of an execution group within a pipeline status."""

    group_id: str
    execution_mode: str = "sequential"
    agents: list[str] = field(default_factory=list)
    agent_statuses: dict[str, str] = field(default_factory=dict)
```

## Migration Logic

### No Data Migration Needed

This feature does **not** require a database migration or data transformation:

- `WorkflowConfiguration` is persisted per-project in the database, but `group_mappings` defaults to `{}` — existing configs work as-is
- `PipelineState` is in-memory only (not persisted to database) — reconstructed from the tracking table on restart
- `AgentStep` is parsed/rendered from the issue body markdown — new fields are extracted only when the Group column is present
- The tracking table format change is forward-only: new issues get the 6-column format; existing issues retain 5-column or 4-column format and are parsed by fallback regex

### Conversion Path

```
PipelineConfig (database)
    │
    │ load_pipeline_as_agent_mappings() — UPDATED
    │ Now iterates stage.groups instead of stage.agents
    │ Builds both agent_mappings (flat) AND group_mappings (structured)
    │
    ▼
WorkflowConfiguration (in-memory/database)
    │
    │ build_agent_pipeline_steps() — UPDATED
    │ When group_mappings present: iterate groups, set group_label
    │ When absent: existing flat behavior
    │
    ▼
Tracking Table (issue body)
    │
    │ parse_tracking_from_body() — UPDATED
    │ 6-column regex → 5-column fallback → 4-column fallback
    │
    ▼
AgentStep[] (in-memory)
    │
    │ _reconstruct_pipeline_state() — UPDATED
    │ Reconstructs PipelineGroupInfo from AgentStep.group_label
    │
    ▼
PipelineState (in-memory)
```
