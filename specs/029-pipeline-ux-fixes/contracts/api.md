# API Contracts: Pipeline Page — Fix Model List, Tools Z-Index, Tile Dragging, Agent Clone, and Remove Add Stage

**Feature**: 029-pipeline-ux-fixes | **Date**: 2026-03-07

## Overview

This feature has minimal API surface changes. The primary change is switching the frontend model data source from a static pipeline endpoint to the existing dynamic settings endpoint. No new endpoints are created.

## Removed Endpoint

### GET /api/v1/pipelines/models/available (REMOVED)

**Reason**: This endpoint returned a hardcoded list of 6 AI models from `PipelineService.list_models()`. It does not reflect per-user model availability on GitHub. The frontend will instead use the existing `GET /api/v1/settings/models/copilot` endpoint which dynamically fetches models from the GitHub API using the user's auth token.

**Previous behavior**:
```
GET /api/v1/pipelines/models/available
Authorization: Bearer <session_token>

Response 200:
[
  { "id": "gpt-4o", "name": "GPT-4o", "provider": "OpenAI", ... },
  { "id": "gpt-4o-mini", "name": "GPT-4o Mini", "provider": "OpenAI", ... },
  { "id": "claude-sonnet-4", "name": "Claude Sonnet 4", "provider": "Anthropic", ... },
  ...
]
```

**Migration path**: The frontend `pipelinesApi.listModels()` method is removed. The `usePipelineModels()` hook is replaced with `useModels()` from `@/hooks/useModels`. No frontend consumers will call this endpoint after the change.

## Existing Endpoint (Used as Replacement)

### GET /api/v1/settings/models/copilot (UNCHANGED)

This existing endpoint already fetches per-user GitHub models dynamically. It is now used by both the per-agent `ModelSelector` and the pipeline-level `PipelineModelDropdown`.

**Request**:
```
GET /api/v1/settings/models/copilot
Authorization: Bearer <session_token>
Query params:
  force_refresh (optional, boolean): Bypass cache and fetch fresh values
```

**Response 200** (success):
```json
{
  "status": "ok",
  "models": [
    {
      "id": "gpt-4o",
      "name": "GPT-4o",
      "provider": "copilot"
    },
    {
      "id": "claude-sonnet-4-20250514",
      "name": "Claude Sonnet 4",
      "provider": "copilot"
    }
    // ... varies per user account
  ]
}
```

**Response 200** (error):
```json
{
  "status": "error",
  "message": "Unable to load models. Please try again.",
  "models": []
}
```

**Frontend consumption**: Via `modelsApi.list(forceRefresh?)` → `settingsApi.fetchModels('copilot', forceRefresh)`. Cached by TanStack Query with `staleTime: Infinity`. The `useModels()` hook provides:
- `models: AIModel[]` — the model list
- `isLoading: boolean` — initial load state
- `isRefreshing: boolean` — force refresh state
- `refreshModels: () => Promise<void>` — manual refresh trigger
- `error: string | null` — error message

## All Other Pipeline Endpoints (UNCHANGED)

The following endpoints remain unchanged:

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/pipelines/{project_id}` | List pipelines |
| GET | `/pipelines/{project_id}/{pipeline_id}` | Get pipeline detail |
| POST | `/pipelines/{project_id}` | Create pipeline |
| PUT | `/pipelines/{project_id}/{pipeline_id}` | Update pipeline |
| DELETE | `/pipelines/{project_id}/{pipeline_id}` | Delete pipeline |
| POST | `/pipelines/{project_id}/seed-presets` | Seed preset pipelines |
| GET | `/pipelines/{project_id}/assignment` | Get pipeline assignment |
| PUT | `/pipelines/{project_id}/assignment` | Set pipeline assignment |

The pipeline create/update endpoints already handle `PipelineAgentNode` with `tool_ids`, `model_id`, `model_name`, and `config` fields — no changes needed to support agent cloning (clones are created client-side and saved as part of the normal pipeline update flow).
