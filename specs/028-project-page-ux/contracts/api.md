# API Contracts: Project Page UX Overhaul

**Feature Branch**: `028-project-page-ux`
**Date**: 2026-03-07

## A1: Board Data Response — Sub-Issue Filtering

**Endpoint**: `GET /api/board/projects/{project_id}`
**File**: `backend/src/api/board.py`

### Behavior Change

When building the `BoardDataResponse`, columns with "Done" or "Closed" status categories MUST exclude items that are sub-issues of any parent item in the project.

### Filtering Logic

```python
# During board data assembly in service.py:

# 1. Collect all sub-issue item IDs across all parent items
all_sub_issue_item_ids: set[str] = set()
for board_item in all_items:
    for sub_issue in board_item.sub_issues:
        all_sub_issue_item_ids.add(sub_issue.id)

# 2. When building "Done"/"Closed" columns, filter out sub-issues
for column in columns:
    if is_done_or_closed_status(column.status):
        column.items = [
            item for item in column.items
            if item.item_id not in all_sub_issue_item_ids
        ]
        column.item_count = len(column.items)
```

### Done/Closed Status Detection

A status option is considered "Done" or "Closed" if:
- `status.name.lower()` is in `{"done", "closed", "completed"}`
- OR the status is the last column in the project board (convention)

### Response Shape (Unchanged)

```json
{
  "project": { "project_id": "...", "name": "..." },
  "columns": [
    {
      "status": { "option_id": "...", "name": "Done", "color": "..." },
      "items": [
        // Only parent issues — no sub-issues
        { "item_id": "...", "title": "...", "sub_issues": [...] }
      ],
      "item_count": 5,
      "estimate_total": 40
    }
  ],
  "rate_limit": null
}
```

---

## A2: Available Agents Response — Extended Metadata

**Endpoint**: `GET /api/agents/{project_id}`
**File**: `backend/src/api/agents.py`

### Behavior Change

The agent list response MUST include `default_model_name` and `tools` count for each agent, enabling the frontend to display model and tool metadata on agent tiles.

### Current Response Shape

```json
[
  {
    "id": "abc-123",
    "name": "Linter",
    "slug": "linter",
    "description": "Code linting agent",
    "system_prompt": "...",
    "default_model_id": "gpt-4o",
    "default_model_name": "GPT-4o",
    "tools": ["eslint", "prettier", "tsc"],
    "status_column": "In Progress",
    "source": "local"
  }
]
```

### Frontend Mapping

The frontend maps the `Agent` response to `AvailableAgent`:

```typescript
// In the hook or service that fetches agents:
const availableAgents: AvailableAgent[] = agents.map(agent => ({
  slug: agent.slug,
  display_name: agent.name,
  description: agent.description,
  avatar_url: null,
  source: agent.source,
  default_model_name: agent.default_model_name || null,
  tools_count: agent.tools?.length ?? null,
}));
```

### No Backend Schema Change Required

The `Agent` model already includes `default_model_name: str` and `tools: list[str]`. The API already serializes these fields. The only change is on the frontend: the `AvailableAgent` type needs `default_model_name` and `tools_count` fields added, and the mapping logic updated.

---

## A3: Pipeline Configurations List

**Endpoint**: `GET /api/pipelines/{project_id}`
**File**: `backend/src/api/pipelines.py`

### Usage (No API Change)

The existing endpoint returns saved pipeline configurations. The frontend's `AgentPresetSelector` component will now fetch this endpoint to populate the "Saved Configurations" section of the dropdown.

### Response Shape (Existing)

```json
{
  "pipelines": [
    {
      "id": "pipeline-001",
      "name": "Default Pipeline",
      "project_id": "proj-123",
      "stages": [
        {
          "id": "stage-1",
          "name": "Backlog",
          "order": 0,
          "agents": [
            {
              "id": "node-1",
              "agent_slug": "speckit.specify",
              "agent_display_name": "Spec Kit - Specify",
              "model_id": "gpt-4o",
              "model_name": "GPT-4o",
              "config": {}
            }
          ]
        }
      ]
    }
  ]
}
```

### Frontend Mapping

```typescript
// Convert PipelineConfig to preset-compatible mappings
function pipelineConfigToMappings(
  config: PipelineConfig,
  columnNames: string[]
): Record<string, AgentAssignment[]> {
  const mappings: Record<string, AgentAssignment[]> = {};
  
  for (const stage of config.stages) {
    // Match stage name to column name (case-insensitive)
    const matchedColumn = columnNames.find(
      col => col.toLowerCase() === stage.name.toLowerCase()
    );
    if (matchedColumn) {
      mappings[matchedColumn] = stage.agents.map(agent => ({
        id: crypto.randomUUID(),
        slug: agent.agent_slug,
        display_name: agent.agent_display_name || null,
      }));
    }
  }
  
  return mappings;
}
```

---

## A4: Pipeline Config Selection Persistence

### Client-Side Storage

| Key | Value | Scope |
|-----|-------|-------|
| `pipeline-config:{project_id}` | Config ID string or `"builtin:custom"` / `"builtin:copilot"` / `"builtin:speckit"` | Per-project |

### Lifecycle

1. **Page load**: Read `localStorage.getItem(`pipeline-config:${projectId}`)` → restore selection
2. **Config change**: `localStorage.setItem(`pipeline-config:${projectId}`, configId)` → persist immediately
3. **New issue creation**: Include active config ID in the issue creation context (existing `useAgentConfig.save()` flow persists agent mappings to backend)

### No New Backend Endpoint

The selected config ID is stored client-side only. The agent mappings derived from the selected config are persisted to the backend via the existing `PUT /api/board/projects/{project_id}/workflow` endpoint when the user saves. This means the backend doesn't need to know about config selection — it only receives the resulting agent-per-column mappings.
