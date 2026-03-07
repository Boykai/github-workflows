# API Contracts: Pipeline Page — CRUD for Agent Pipeline Configurations

**Feature**: 026-pipeline-crud | **Date**: 2026-03-07

## Base URL

All endpoints are prefixed with `/api/v1` and require an authenticated session (same auth pattern as existing endpoints in `/api/v1/workflow/*` and `/api/v1/agents/*`).

---

## Pipeline CRUD Endpoints

### List Pipelines

```
GET /api/v1/pipelines
```

**Description**: List all saved pipeline configurations for the current project.

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
      "stage_count": 3,
      "agent_count": 5,
      "updated_at": "2026-03-07T10:30:00Z"
    }
  ],
  "total": 1
}
```

**Error Responses**:
- `401 Unauthorized` — Missing or invalid session

---

### Create Pipeline

```
POST /api/v1/pipelines
```

**Description**: Create a new pipeline configuration.

**Request Body**:
```json
{
  "name": "Code Review Pipeline",
  "description": "Automated code review with multiple agents",
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
          "config": {}
        }
      ]
    }
  ]
}
```

**Validation**:
- `name`: Required, 1–100 characters
- `description`: Optional, 0–500 characters
- `stages`: Required array (may be empty for initial save)
- Each stage `name`: Required, 1–100 characters
- Must have at least one stage to save (FR-001: "adding one or more stages")

**Response** (201 Created):
```json
{
  "id": "uuid-new",
  "project_id": "project-123",
  "name": "Code Review Pipeline",
  "description": "Automated code review with multiple agents",
  "stages": [ /* full stage data as submitted */ ],
  "created_at": "2026-03-07T10:30:00Z",
  "updated_at": "2026-03-07T10:30:00Z"
}
```

**Error Responses**:
- `400 Bad Request` — Validation failure (missing name, empty stages, etc.)
- `401 Unauthorized` — Missing or invalid session
- `409 Conflict` — Pipeline with same name already exists in this project

---

### Get Pipeline

```
GET /api/v1/pipelines/{pipeline_id}
```

**Description**: Get a single pipeline configuration with all stages, agents, and model selections.

**Path Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| `pipeline_id` | string | UUID of the pipeline |

**Response** (200 OK):
```json
{
  "id": "uuid-1234",
  "project_id": "project-123",
  "name": "Code Review Pipeline",
  "description": "Automated code review with multiple agents",
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
          "config": {}
        }
      ]
    },
    {
      "id": "stage-uuid-2",
      "name": "Review",
      "order": 1,
      "agents": [
        {
          "id": "agent-node-uuid-2",
          "agent_slug": "copilot-review",
          "agent_display_name": "Copilot Review",
          "model_id": "claude-sonnet-4",
          "model_name": "Claude Sonnet 4",
          "config": {}
        }
      ]
    }
  ],
  "created_at": "2026-03-07T10:30:00Z",
  "updated_at": "2026-03-07T10:30:00Z"
}
```

**Error Responses**:
- `401 Unauthorized` — Missing or invalid session
- `404 Not Found` — Pipeline ID does not exist

---

### Update Pipeline

```
PUT /api/v1/pipelines/{pipeline_id}
```

**Description**: Update an existing pipeline configuration. Replaces the full stage/agent data.

**Path Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| `pipeline_id` | string | UUID of the pipeline |

**Request Body**:
```json
{
  "name": "Updated Pipeline Name",
  "description": "Updated description",
  "stages": [ /* full replacement stage array */ ]
}
```

**Validation**: Same rules as Create. All fields are optional — only provided fields are updated. If `stages` is provided, it fully replaces the existing stages array.

**Response** (200 OK):
```json
{
  "id": "uuid-1234",
  "project_id": "project-123",
  "name": "Updated Pipeline Name",
  "description": "Updated description",
  "stages": [ /* updated stages */ ],
  "created_at": "2026-03-07T10:30:00Z",
  "updated_at": "2026-03-07T11:00:00Z"
}
```

**Error Responses**:
- `400 Bad Request` — Validation failure
- `401 Unauthorized` — Missing or invalid session
- `404 Not Found` — Pipeline ID does not exist
- `409 Conflict` — Updated name conflicts with an existing pipeline name

---

### Delete Pipeline

```
DELETE /api/v1/pipelines/{pipeline_id}
```

**Description**: Permanently delete a pipeline configuration.

**Path Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| `pipeline_id` | string | UUID of the pipeline |

**Response** (200 OK):
```json
{
  "success": true,
  "deleted_id": "uuid-1234"
}
```

**Error Responses**:
- `401 Unauthorized` — Missing or invalid session
- `404 Not Found` — Pipeline ID does not exist

---

## Models Endpoint

### List Available Models

```
GET /api/v1/models
```

**Description**: List all available AI models with metadata for the model picker.

**Response** (200 OK):
```json
{
  "models": [
    {
      "id": "gpt-4o",
      "name": "GPT-4o",
      "provider": "OpenAI",
      "context_window_size": 128000,
      "cost_tier": "premium",
      "capability_category": "general"
    },
    {
      "id": "gpt-4o-mini",
      "name": "GPT-4o Mini",
      "provider": "OpenAI",
      "context_window_size": 128000,
      "cost_tier": "economy",
      "capability_category": "general"
    },
    {
      "id": "claude-sonnet-4",
      "name": "Claude Sonnet 4",
      "provider": "Anthropic",
      "context_window_size": 200000,
      "cost_tier": "premium",
      "capability_category": "coding"
    },
    {
      "id": "claude-haiku-3.5",
      "name": "Claude 3.5 Haiku",
      "provider": "Anthropic",
      "context_window_size": 200000,
      "cost_tier": "economy",
      "capability_category": "general"
    },
    {
      "id": "gemini-2.5-pro",
      "name": "Gemini 2.5 Pro",
      "provider": "Google",
      "context_window_size": 1000000,
      "cost_tier": "premium",
      "capability_category": "general"
    },
    {
      "id": "gemini-2.5-flash",
      "name": "Gemini 2.5 Flash",
      "provider": "Google",
      "context_window_size": 1000000,
      "cost_tier": "standard",
      "capability_category": "general"
    }
  ]
}
```

**Notes**:
- Models are grouped by `provider` on the frontend for the model picker UI.
- `cost_tier` values: `economy`, `standard`, `premium`.
- `context_window_size` is in tokens.
- This endpoint is not project-scoped — models are globally available.
- Results should be cached aggressively (5-minute staleTime in TanStack Query).

**Error Responses**:
- `401 Unauthorized` — Missing or invalid session

---

## Frontend API Client Methods

Added to `frontend/src/services/api.ts`:

```typescript
// Pipeline CRUD
pipelines: {
  list: (sort?: string, order?: string) =>
    GET<PipelineConfigListResponse>('/pipelines', { sort, order }),

  get: (pipelineId: string) =>
    GET<PipelineConfig>(`/pipelines/${pipelineId}`),

  create: (data: PipelineConfigCreate) =>
    POST<PipelineConfig>('/pipelines', data),

  update: (pipelineId: string, data: PipelineConfigUpdate) =>
    PUT<PipelineConfig>(`/pipelines/${pipelineId}`, data),

  delete: (pipelineId: string) =>
    DELETE<{ success: boolean; deleted_id: string }>(`/pipelines/${pipelineId}`),
},

// Models
models: {
  list: () =>
    GET<{ models: AIModel[] }>('/models'),
}
```

---

## Query Keys (TanStack Query)

| Key | Endpoint | staleTime |
|-----|----------|-----------|
| `['pipelines', 'list']` | `GET /pipelines` | 30s |
| `['pipelines', 'detail', pipelineId]` | `GET /pipelines/:id` | 60s |
| `['models']` | `GET /models` | 300s (5 min) |
