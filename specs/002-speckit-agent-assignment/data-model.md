# Data Model: Spec Kit Custom Agent Assignment by Status

**Feature**: 002-speckit-agent-assignment  
**Date**: 2026-02-13  
**Source**: [spec.md](spec.md), [research.md](research.md)

## Entities

### 1. WorkflowConfiguration (modified)

Existing Pydantic model. Replace `custom_agent: str` with `agent_mappings`.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| project_id | `str` | required | GitHub Project V2 node ID |
| repository_owner | `str` | required | GitHub repository owner |
| repository_name | `str` | required | GitHub repository name |
| copilot_assignee | `str` | `""` | Fallback assignee on agent failure |
| review_assignee | `str \| None` | `None` | Reviewer for In Review status |
| ~~custom_agent~~ | ~~`str`~~ | ~~`""`~~ | **REMOVED** — replaced by `agent_mappings` |
| **agent_mappings** | `dict[str, list[str]]` | `DEFAULT_AGENT_MAPPINGS` | **NEW** — status name → ordered agent list |
| status_backlog | `str` | `"Backlog"` | Backlog status column name |
| status_ready | `str` | `"Ready"` | Ready status column name |
| status_in_progress | `str` | `"In Progress"` | In Progress status column name |
| status_in_review | `str` | `"In Review"` | In Review status column name |
| enabled | `bool` | `True` | Whether workflow is active |

**Default agent mappings**:
```python
DEFAULT_AGENT_MAPPINGS: dict[str, list[str]] = {
    "Backlog": ["speckit.specify"],
    "Ready": ["speckit.plan", "speckit.tasks"],
    "In Progress": ["speckit.implement"],
}
```

**Validation rules**:
- `agent_mappings` keys must be non-empty strings (status names)
- `agent_mappings` values must be non-empty lists of non-empty strings (agent names)
- Agent names should follow the `speckit.*` naming pattern (warning if not, not enforced)

---

### 2. PipelineState (new)

Tracks per-issue pipeline progress through sequential agents.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| issue_number | `int` | required | GitHub issue number |
| project_id | `str` | required | GitHub Project V2 node ID |
| status | `str` | required | Current workflow status (Backlog, Ready, etc.) |
| agents | `list[str]` | required | Ordered list of agents for this status |
| current_agent_index | `int` | `0` | Index of currently active agent in `agents` |
| completed_agents | `list[str]` | `[]` | Agent names that have posted completion markers |
| started_at | `datetime \| None` | `None` | When current agent was assigned |
| error | `str \| None` | `None` | Last error message, if any |

**Computed properties**:
- `current_agent -> str | None`: `agents[current_agent_index]` if index in bounds, else `None`
- `is_complete -> bool`: `current_agent_index >= len(agents)`
- `next_agent -> str | None`: `agents[current_agent_index + 1]` if exists, else `None`

**State transitions**:
```
                    assign agent
    ┌─────────────────────────────────┐
    │                                 │
    ▼                                 │
[WAITING_COMPLETION] ──completion──► [ADVANCE_INDEX]
                     detected          │
                                       │ index < len(agents)?
                                       │
                              ┌────yes─┤────no──┐
                              ▼        │        ▼
                     [ASSIGN_NEXT]     │  [PIPELINE_COMPLETE]
                              │        │        │
                              └────────┘        ▼
                                         [TRANSITION_STATUS]
```

**Storage**: Module-level dict `_pipeline_states: dict[int, PipelineState]` (keyed by issue number)

**Reconstruction**: On restart, for each tracked issue:
1. Fetch issue comments via `get_issue_with_comments()`
2. Get agent list from `agent_mappings[current_status]`
3. Scan comments for `"<agent>: All done!>"` markers sequentially
4. Set `current_agent_index` to count of found markers
5. If all agents completed → trigger status transition

---

### 3. AgentNotification (new)

WebSocket notification payload for agent events.

| Field | Type | Description |
|-------|------|-------------|
| type | `str` | `"agent_assigned"` or `"agent_completed"` |
| issue_number | `int` | GitHub issue number |
| agent_name | `str` | Spec Kit agent name (e.g., `"speckit.plan"`) |
| status | `str` | Current workflow status |
| next_agent | `str \| None` | Next agent in pipeline (null if last) |
| timestamp | `str` | ISO 8601 timestamp |

---

### 4. WorkflowTransition (unchanged, usage updated)

Existing model. The `assigned_user` field already supports `"copilot:{agent_name}"` format. No structural changes needed — just ensure all agent assignments are logged using this model.

| Field | Type | Description |
|-------|------|-------------|
| issue_number | `int` | GitHub issue number |
| from_status | `str` | Previous status |
| to_status | `str` | New status |
| assigned_user | `str` | e.g., `"copilot:speckit.plan"` |
| timestamp | `str` | ISO 8601 timestamp |

---

## Relationships

```
WorkflowConfiguration
    │
    ├── agent_mappings: dict[str, list[str]]
    │       │
    │       └── "Ready" → ["speckit.plan", "speckit.tasks"]
    │                           │
    │                           ▼
    │                    PipelineState (per issue)
    │                        │
    │                        ├── tracks progress through agent list
    │                        └── emits AgentNotification on events
    │
    └── used by WorkflowOrchestrator
            │
            └── logs WorkflowTransition for each agent assignment
```

## Frontend Type (TypeScript)

```typescript
interface WorkflowConfiguration {
  project_id: string;
  repository_owner: string;
  repository_name: string;
  copilot_assignee: string;
  review_assignee: string | null;
  agent_mappings: Record<string, string[]>;  // NEW (replaces custom_agent)
  status_backlog: string;
  status_ready: string;
  status_in_progress: string;
  status_in_review: string;
  enabled: boolean;
}

interface AgentNotification {
  type: 'agent_assigned' | 'agent_completed';
  issue_number: number;
  agent_name: string;
  status: string;
  next_agent: string | null;
  timestamp: string;
}
```
