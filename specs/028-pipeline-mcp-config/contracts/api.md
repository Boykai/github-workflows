# API Contracts: Pipeline Page — MCP Tool Selection, Model Override, Flow Graph Cards, Preset Configs & Agent Stamp Isolation

**Feature**: 028-pipeline-mcp-config | **Date**: 2026-03-07

## Base URL

All endpoints are prefixed with `/api/v1` and require an authenticated session (same auth pattern as existing endpoints in `/api/v1/workflow/*` and `/api/v1/agents/*`).

---

## Modified Endpoints

### List Pipelines (MODIFIED)

```
GET /api/v1/pipelines/{project_id}
```

**Description**: List all saved pipeline configurations for the given project. Now returns enriched summaries including full stage data, tool counts, and preset flags.

**Query Parameters**:
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `sort` | string | `updated_at` | Sort field: `updated_at`, `name`, `created_at` |
| `order` | string | `desc` | Sort order: `asc`, `desc` |

**Response** (200 OK):
```json
{
  "pipelines": [
    {
      "id": "uuid-1234",
      "name": "Code Review Pipeline",
      "description": "Automated code review with multiple agents",
      "stage_count": 2,
      "agent_count": 3,
      "total_tool_count": 7,
      "is_preset": false,
      "preset_id": "",
      "stages": [
        {
          "id": "stage-1",
          "name": "Analysis",
          "order": 0,
          "agents": [
            {
              "id": "agent-node-1",
              "agent_slug": "code-reviewer",
              "agent_display_name": "Code Reviewer",
              "model_id": "gpt-4o",
              "model_name": "GPT-4o",
              "tool_ids": ["tool-uuid-1", "tool-uuid-2"],
              "tool_count": 2,
              "config": {}
            }
          ]
        },
        {
          "id": "stage-2",
          "name": "Report",
          "order": 1,
          "agents": [
            {
              "id": "agent-node-2",
              "agent_slug": "reporter",
              "agent_display_name": "Reporter",
              "model_id": "",
              "model_name": "",
              "tool_ids": ["tool-uuid-3", "tool-uuid-4", "tool-uuid-5"],
              "tool_count": 3,
              "config": {}
            },
            {
              "id": "agent-node-3",
              "agent_slug": "summarizer",
              "agent_display_name": "Summarizer",
              "model_id": "claude-sonnet-4",
              "model_name": "Claude Sonnet 4",
              "tool_ids": ["tool-uuid-6", "tool-uuid-7"],
              "tool_count": 2,
              "config": {}
            }
          ]
        }
      ],
      "updated_at": "2026-03-07T10:30:00Z"
    },
    {
      "id": "preset-spec-kit",
      "name": "Spec Kit",
      "description": "Full specification workflow: specify → plan → tasks → implement → analyze",
      "stage_count": 5,
      "agent_count": 5,
      "total_tool_count": 0,
      "is_preset": true,
      "preset_id": "spec-kit",
      "stages": [ "..." ],
      "updated_at": "2026-03-07T00:00:00Z"
    }
  ],
  "total": 2
}
```

**Changes from spec 026**:
- Response now includes `total_tool_count`, `is_preset`, `preset_id`, and full `stages` array (previously only `stage_count` and `agent_count`).
- `PipelineAgentNode` objects within stages now include `tool_ids` and `tool_count`.

**Error Responses**:
- `401 Unauthorized` — Missing or invalid session

---

### Create Pipeline (MODIFIED)

```
POST /api/v1/pipelines/{project_id}
```

**Description**: Create a new pipeline configuration. Agent nodes now support `tool_ids`.

**Request Body**:
```json
{
  "name": "My Pipeline",
  "description": "Custom pipeline with tool selections",
  "stages": [
    {
      "id": "stage-uuid-1",
      "name": "Analysis",
      "order": 0,
      "agents": [
        {
          "id": "agent-node-uuid-1",
          "agent_slug": "copilot",
          "agent_display_name": "GitHub Copilot",
          "model_id": "gpt-4o",
          "model_name": "GPT-4o",
          "tool_ids": ["tool-uuid-1", "tool-uuid-2"],
          "tool_count": 2,
          "config": {}
        }
      ]
    }
  ]
}
```

**Validation**:
- `name`: Required, 1–100 characters (FR-007: missing name triggers inline validation)
- `description`: Optional, 0–500 characters
- `stages`: Optional array (empty pipeline is allowed with warning per edge case)
- Each agent's `tool_ids`: Optional list of strings (tool existence not validated — tools may be deleted)
- `tool_count` is auto-computed from `tool_ids` on save if not provided

**Response** (201 Created): Full `PipelineConfig` object with `is_preset: false`.

**Changes from spec 026**:
- Agent nodes in request body now accept `tool_ids` and `tool_count`.
- `is_preset` and `preset_id` are set automatically (`false` and `""` for user-created).

---

### Update Pipeline (MODIFIED)

```
PUT /api/v1/pipelines/{project_id}/{pipeline_id}
```

**Description**: Update an existing pipeline. Rejects updates to preset pipelines (returns 403).

**Request Body**: Same as Create (partial updates via `PipelineConfigUpdate`).

**Additional Validation**:
- If target pipeline has `is_preset = true`, return `403 Forbidden` with message "Cannot modify preset pipelines. Use 'Save as Copy' to create an editable version."

**Changes from spec 026**:
- Preset protection: updates to preset pipelines are blocked.

---

## New Endpoints

### Seed Preset Pipelines

```
POST /api/v1/pipelines/{project_id}/seed-presets
```

**Description**: Idempotently seed the "Spec Kit" and "GitHub Copilot" preset pipeline configurations for the given project. Called automatically on project initialization; can also be triggered manually.

**Request Body**: None

**Response** (200 OK):
```json
{
  "seeded": ["spec-kit", "github-copilot"],
  "skipped": [],
  "total": 2
}
```

If presets already exist:
```json
{
  "seeded": [],
  "skipped": ["spec-kit", "github-copilot"],
  "total": 2
}
```

**Behavior**:
- For each preset definition, checks if a pipeline with matching `preset_id` + `project_id` already exists.
- If not, inserts the preset pipeline with `is_preset = 1`.
- If yes, skips (idempotent).
- Returns counts of seeded vs. skipped presets.

**Error Responses**:
- `401 Unauthorized` — Missing or invalid session

---

### Set Project Pipeline Assignment

```
PUT /api/v1/pipelines/{project_id}/assignment
```

**Description**: Set or clear the project's assigned pipeline configuration. This pipeline will be auto-applied to newly created GitHub Issues.

**Request Body**:
```json
{
  "pipeline_id": "uuid-1234"
}
```

To clear assignment:
```json
{
  "pipeline_id": ""
}
```

**Validation**:
- If `pipeline_id` is non-empty, verify it exists in `pipeline_configs` for this project. Return `404` if not found.

**Response** (200 OK):
```json
{
  "project_id": "project-123",
  "pipeline_id": "uuid-1234"
}
```

**Error Responses**:
- `401 Unauthorized` — Missing or invalid session
- `404 Not Found` — Pipeline ID does not exist in this project

---

### Get Project Pipeline Assignment

```
GET /api/v1/pipelines/{project_id}/assignment
```

**Description**: Get the current pipeline assignment for the project.

**Response** (200 OK):
```json
{
  "project_id": "project-123",
  "pipeline_id": "uuid-1234"
}
```

If no pipeline assigned:
```json
{
  "project_id": "project-123",
  "pipeline_id": ""
}
```

---

## Unchanged Endpoints (Referenced)

These existing endpoints are used by the feature but not modified:

### List Available Models

```
GET /api/v1/pipelines/models/available
```

**Description**: Returns the list of available AI models. Already implemented in spec 026. The "Auto" option is added client-side (not from this endpoint).

### List Available Agents

```
GET /api/v1/agents/{project_id}
```

**Description**: Returns agents saved on the Agents page. Used to populate the "+ Add Agent" picker. Already implemented.

### List MCP Tools

```
GET /api/v1/tools
```

**Description**: Returns all available MCP tools. Used to populate the tool selector modal. Already implemented in spec 027.

---

## Frontend API Client Extensions

### New Methods in `pipelinesApi`

```typescript
const pipelinesApi = {
  // ... existing methods from spec 026 ...

  seedPresets: async (projectId: string): Promise<PresetSeedResult> => {
    return request(`/pipelines/${projectId}/seed-presets`, { method: 'POST' });
  },

  getAssignment: async (projectId: string): Promise<ProjectPipelineAssignment> => {
    return request(`/pipelines/${projectId}/assignment`);
  },

  setAssignment: async (
    projectId: string,
    pipelineId: string
  ): Promise<ProjectPipelineAssignment> => {
    return request(`/pipelines/${projectId}/assignment`, {
      method: 'PUT',
      body: JSON.stringify({ pipeline_id: pipelineId }),
    });
  },
};
```

### New Response Types

```typescript
interface PresetSeedResult {
  seeded: string[];
  skipped: string[];
  total: number;
}
```

---

## TanStack Query Keys

```typescript
export const pipelineKeys = {
  all: ['pipelines'] as const,
  list: (projectId: string) => [...pipelineKeys.all, 'list', projectId] as const,
  detail: (projectId: string, pipelineId: string) =>
    [...pipelineKeys.all, 'detail', projectId, pipelineId] as const,
  assignment: (projectId: string) =>
    [...pipelineKeys.all, 'assignment', projectId] as const,     // NEW
};
```
