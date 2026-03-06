# Data Model: Align Agent Pipeline Columns with Project Board Status & Enable Drag/Drop

**Feature**: `023-pipeline-dragdrop` | **Date**: 2026-03-06

## Entities

### AgentAssignment (existing — no changes)

The fundamental unit representing an agent assigned to a status column in the pipeline.

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| `id` | `string` (UUID) | Unique identifier for this assignment instance | Required, UUID format |
| `slug` | `string` | Agent identifier (e.g., `speckit.specify`) | Required, non-empty |
| `display_name` | `string \| null` | Human-readable agent name | Optional |
| `config` | `Record<string, unknown> \| null` | Agent-specific configuration | Optional |

**Source**: `frontend/src/types/index.ts` lines 237–242

### Pipeline Column (derived from StatusOption — no changes)

Represents a workflow status stage in the Agent Pipeline. Derived from the Project Board's status field options.

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| `option_id` | `string` | GitHub Projects V2 status option ID | Required |
| `name` | `string` | Column display name (e.g., "Backlog", "In Progress") | Required, non-empty |
| `color` | `StatusColor` | Display color | Optional, one of StatusColor enum |
| `description` | `string \| null` | Optional description | Optional |

**Source**: `frontend/src/types/index.ts` (BoardStatusOption), `backend/src/models/board.py` (StatusOption)

### Agent Mappings (existing — no structural changes)

The configuration mapping status column names to ordered lists of agent assignments.

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| Key | `string` | Status column name (case-insensitive matching) | Must match a valid column name |
| Value | `AgentAssignment[]` | Ordered list of agents in this column | Array, may be empty |

**Source**: `frontend/src/types/index.ts` (WorkflowConfiguration.agent_mappings)

**Storage**: Persisted via `PUT /workflow/config` → `set_workflow_config()` → SQLite

### WorkflowConfiguration (existing — no changes)

Top-level configuration object that contains agent_mappings.

| Field | Type | Description |
|-------|------|-------------|
| `project_id` | `string` | GitHub project ID |
| `repository_owner` | `string` | Repository owner |
| `repository_name` | `string` | Repository name |
| `copilot_assignee` | `string` | Copilot assignee username |
| `review_assignee` | `string?` | Review assignee username |
| `agent_mappings` | `Record<string, AgentAssignment[]>` | Status → agents mapping |
| `status_backlog` | `string` | Backlog status name |
| `status_ready` | `string` | Ready status name |
| `status_in_progress` | `string` | In Progress status name |
| `status_in_review` | `string` | In Review status name |
| `enabled` | `boolean` | Whether workflow is enabled |

## Relationships

```text
ProjectBoard (GitHub API)
    │
    ├── StatusField
    │       └── StatusOption[] ──────► Pipeline Columns (display)
    │
    └── BoardColumn[]
            └── BoardItem[]

WorkflowConfiguration (SQLite)
    │
    └── agent_mappings: Record<string, AgentAssignment[]>
            │
            ├── Key = StatusOption.name ───► Pipeline Column (by name)
            │
            └── Value = AgentAssignment[]
                    └── Ordered list (index = row position)
```

## State Transitions

### Drag Operation State Machine

```text
┌─────────────┐
│   IDLE       │◄──────────────────────────────────────┐
│              │                                        │
└──────┬───────┘                                        │
       │ onDragStart                                    │
       ▼                                                │
┌─────────────┐                                        │
│  DRAGGING    │                                        │
│              │──── onDragOver ─► Update preview       │
└──────┬───────┘     (live reorder / column highlight)  │
       │                                                │
       ├── onDragEnd (valid target) ──► Update State ───┤
       │                                                │
       └── onDragCancel (invalid) ──► Revert ──────────┘
```

### State Update Flow (on successful drop)

```text
1. onDragEnd fires with {active, over} data
2. Determine source column (from active.data.current.sortable.containerId)
3. Determine target column (from over.data.current.sortable.containerId or droppable id)
4. If same column: reorder via arrayMove (existing behavior)
5. If different column: call moveAgentToColumn(source, target, agentId, targetIndex)
6. localMappings updated → isDirty becomes true → AgentSaveBar appears
7. User clicks "Save" → PUT /workflow/config → persist to SQLite
```

## New Hook Method

### `moveAgentToColumn` (added to useAgentConfig)

```typescript
moveAgentToColumn: (
  sourceStatus: string,
  targetStatus: string,
  agentId: string,
  targetIndex?: number
) => void
```

**Behavior**:
1. Remove agent with matching `id` from `localMappings[sourceStatus]`
2. Insert agent into `localMappings[targetStatus]` at `targetIndex` (or append if undefined)
3. Trigger re-render; `isDirty` computed via existing comparison logic

**Edge Cases**:
- Source status key not found → no-op
- Agent ID not found in source → no-op
- Target status key not found → create empty array, insert agent
- Target index out of bounds → clamp to array length (append)
