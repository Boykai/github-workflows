# API Contract: Pipeline Builder — Group-Based Structure

**Feature Branch**: `037-pipeline-builder-ux`
**Date**: 2026-03-12
**Input**: [data-model.md](../data-model.md), [spec.md](../spec.md)

## Overview

The pipeline REST API (`/api/v1/pipelines/{projectId}`) is **backward compatible**. No new endpoints are added. The existing CRUD endpoints accept and return the updated `PipelineStage` schema, which now includes an optional `groups` field. Clients sending the old format (flat `agents` array, no `groups`) continue to work; the backend normalises legacy payloads on write.

## Base URL

```
/api/v1/pipelines/{projectId}
```

## Schema Changes

### ExecutionGroup (NEW)

```json
{
  "id": "string",
  "order": 0,
  "execution_mode": "sequential | parallel",
  "agents": [ /* PipelineAgentNode[] */ ]
}
```

### PipelineStage (UPDATED)

```json
{
  "id": "string",
  "name": "string",
  "order": 0,
  "groups": [                          // NEW — optional
    {
      "id": "group-1",
      "order": 0,
      "execution_mode": "sequential",
      "agents": [
        {
          "id": "agent-node-1",
          "agent_slug": "speckit.specify",
          "agent_display_name": "Specify",
          "model_id": "",
          "model_name": "",
          "tool_ids": [],
          "tool_count": 0,
          "config": {}
        }
      ]
    }
  ],
  "agents": [],                        // DEPRECATED — kept for backward compat
  "execution_mode": "sequential"       // DEPRECATED — kept for backward compat
}
```

### PipelineConfig (UNCHANGED structure)

```json
{
  "id": "string",
  "project_id": "string",
  "name": "string",
  "description": "string",
  "stages": [ /* PipelineStage[] with groups */ ],
  "is_preset": false,
  "preset_id": "",
  "created_at": "2026-03-12T00:00:00Z",
  "updated_at": "2026-03-12T00:00:00Z"
}
```

---

## Endpoints

### POST /api/v1/pipelines/{projectId}

**Create a new pipeline.**

#### Request Body

```json
{
  "name": "My Pipeline",
  "description": "Optional description",
  "stages": [
    {
      "id": "stage-1",
      "name": "Stage 1",
      "order": 0,
      "groups": [
        {
          "id": "group-1",
          "order": 0,
          "execution_mode": "sequential",
          "agents": []
        }
      ]
    }
  ]
}
```

**Backward-compatible request** (old format, no `groups`):

```json
{
  "name": "My Pipeline",
  "stages": [
    {
      "id": "stage-1",
      "name": "Stage 1",
      "order": 0,
      "agents": [
        { "id": "a1", "agent_slug": "copilot", "agent_display_name": "Copilot" }
      ],
      "execution_mode": "parallel"
    }
  ]
}
```

The backend normalises this to the group format before persisting.

#### Response

`201 Created` — returns the full `PipelineConfig` with `groups` populated.

---

### PUT /api/v1/pipelines/{projectId}/{pipelineId}

**Update an existing pipeline.**

#### Request Body

```json
{
  "name": "Updated Name",
  "stages": [
    {
      "id": "stage-1",
      "name": "Build",
      "order": 0,
      "groups": [
        {
          "id": "group-1",
          "order": 0,
          "execution_mode": "sequential",
          "agents": [
            {
              "id": "node-1",
              "agent_slug": "linter",
              "agent_display_name": "Linter",
              "model_id": "gpt-4o",
              "model_name": "GPT-4o",
              "tool_ids": [],
              "tool_count": 0,
              "config": {}
            }
          ]
        },
        {
          "id": "group-2",
          "order": 1,
          "execution_mode": "parallel",
          "agents": [
            {
              "id": "node-2",
              "agent_slug": "reviewer-a",
              "agent_display_name": "Reviewer A",
              "model_id": "",
              "model_name": "",
              "tool_ids": [],
              "tool_count": 0,
              "config": {}
            },
            {
              "id": "node-3",
              "agent_slug": "reviewer-b",
              "agent_display_name": "Reviewer B",
              "model_id": "",
              "model_name": "",
              "tool_ids": [],
              "tool_count": 0,
              "config": {}
            }
          ]
        }
      ]
    }
  ]
}
```

#### Response

`200 OK` — returns the updated `PipelineConfig`.

---

### GET /api/v1/pipelines/{projectId}/{pipelineId}

**Retrieve a pipeline.**

#### Response

`200 OK` — returns `PipelineConfig`.

**Note**: Pipelines saved in old format are returned as-is (no server-side migration on read). The frontend migration function handles conversion at load time. After the user saves, the pipeline is stored in the new group format.

---

### GET /api/v1/pipelines/{projectId}

**List all pipelines for a project.**

#### Response

```json
{
  "pipelines": [ /* PipelineConfigSummary[] */ ],
  "total": 5
}
```

`PipelineConfigSummary` is updated to reflect group-based stages in its `stages` field.

---

### DELETE /api/v1/pipelines/{projectId}/{pipelineId}

**Delete a pipeline.** No changes.

---

## Backend Normalization Rules

### On Write (Create / Update)

When the backend receives a `PipelineStage` payload:

1. **If `groups` is present and non-empty**: Validate each group's `execution_mode`. Persist as-is.
2. **If `groups` is absent or empty AND `agents` is non-empty**: Normalise to group format:
   - Create one `ExecutionGroup` with `order=0`, `execution_mode` from stage (default `"sequential"`), and `agents` from stage.
   - Set `stage.groups = [new_group]`.
3. **If both `groups` and `agents` are empty**: Persist with an empty `groups` array (valid empty stage).

### Execution Mode Normalization (per group)

The existing `_normalize_execution_modes` logic is updated to iterate over groups instead of stages:

```python
def _normalize_execution_modes(stages: list[PipelineStage]) -> list[PipelineStage]:
    for stage in stages:
        for group in stage.groups:
            if group.execution_mode not in ("sequential", "parallel"):
                group.execution_mode = "sequential"
    return stages
```

**Change from current behavior**: The current logic downgrades a parallel stage to sequential if it has fewer than 2 agents. The new logic **does not** auto-downgrade at the group level — the user's intent to set a group as "parallel" is preserved even with 0–1 agents (per spec: US-4 acceptance scenario 5).

---

## Preset Pipeline Updates

All preset pipelines are updated to use the group format. Each preset's existing stages are wrapped in a single group per stage, preserving the current execution mode. Example:

```python
# Before (old format)
{"id": "s1", "name": "Execute", "order": 0,
 "agents": [_agent("a1", "copilot", "Copilot")],
 "execution_mode": "sequential"}

# After (new format)
{"id": "s1", "name": "Execute", "order": 0,
 "groups": [{
   "id": "g1", "order": 0,
   "execution_mode": "sequential",
   "agents": [_agent("a1", "copilot", "Copilot")]
 }],
 "agents": [],
 "execution_mode": "sequential"}
```

---

## Error Responses

No changes to error response format. Existing validation errors apply:

| Status | Condition |
|--------|-----------|
| 400 | Invalid `execution_mode` in any group (not `"sequential"` or `"parallel"`) |
| 400 | `name` empty or exceeds 100 characters |
| 404 | Pipeline or project not found |
| 500 | Internal server error |
