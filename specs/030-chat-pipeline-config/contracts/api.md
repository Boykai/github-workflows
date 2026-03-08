# API Contracts: Use Selected Agent Pipeline Config from Project Page When Creating GitHub Issues via Chat

**Feature**: 030-chat-pipeline-config | **Date**: 2026-03-08

## Base URL

All endpoints are prefixed with `/api/v1` and require an authenticated session (same auth pattern as existing endpoints).

---

## Modified Endpoints

### Confirm Chat Proposal (Modified Response)

```
POST /api/v1/chat/proposals/{proposal_id}/confirm
```

**Description**: Confirms an AI-generated task proposal, creating a GitHub Issue with the resolved Agent Pipeline configuration. The backend resolves the pipeline at confirmation time using the project-level assignment, with fallback to user mappings and system defaults.

**Path Parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| `proposal_id` | string | The unique ID of the proposal to confirm |

**Request Body** (unchanged):

```json
{
  "edited_title": "Optional edited title",
  "edited_description": "Optional edited description"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `edited_title` | string | No | User-edited title (max 256 chars) |
| `edited_description` | string | No | User-edited description (max 65536 chars) |

**Response** (200 OK — extended with pipeline fields):

```json
{
  "proposal_id": "abc123",
  "proposed_title": "Implement feature X",
  "proposed_description": "...",
  "final_title": "Implement feature X",
  "final_description": "...",
  "status": "confirmed",
  "action_type": "task_create",
  "created_at": "2026-03-08T10:00:00Z",
  "issue_number": 42,
  "issue_url": "https://github.com/owner/repo/issues/42",
  "pipeline_name": "Full Review Pipeline",
  "pipeline_source": "pipeline"
}
```

**New Response Fields**:

| Field | Type | Description |
|-------|------|-------------|
| `pipeline_name` | string \| null | Display name of the resolved Agent Pipeline. `null` if default mappings were used. |
| `pipeline_source` | string \| null | Source of the pipeline resolution: `"pipeline"` (project assignment), `"user"` (user-specific mappings), or `"default"` (system defaults). |

**Pipeline Resolution Logic** (backend):

1. Read `assigned_pipeline_id` from `project_settings` where `github_user_id = "__workflow__"` and `project_id = {current_project}`.
2. If `assigned_pipeline_id` is non-empty:
   - Fetch `PipelineConfig` from `pipeline_configs` by ID.
   - If pipeline exists: convert stages → agent_mappings. Return `source = "pipeline"`, `pipeline_name = config.name`.
   - If pipeline was deleted: clear stale `assigned_pipeline_id`, fall through to step 3.
3. Call `load_user_agent_mappings(github_user_id, project_id)`.
   - If user mappings exist: return `source = "user"`, `pipeline_name = null`.
4. Use `DEFAULT_AGENT_MAPPINGS`. Return `source = "default"`, `pipeline_name = null`.

**Error Responses** (unchanged):

- `400 Bad Request` — Invalid proposal ID or already confirmed/rejected
- `401 Unauthorized` — Missing or invalid session
- `404 Not Found` — Proposal not found
- `422 Unprocessable Entity` — Missing project selection

---

## Existing Endpoints (Used, Not Modified)

### Get Pipeline Assignment

```
GET /api/v1/pipelines/{project_id}/assignment
```

**Description**: Returns the currently assigned pipeline for a project. Used by the new `useSelectedPipeline` hook in the chat to determine whether a pipeline is selected.

**Response** (200 OK):

```json
{
  "project_id": "PVT_abc123",
  "pipeline_id": "uuid-of-pipeline"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `project_id` | string | The project identifier |
| `pipeline_id` | string | The assigned pipeline ID. Empty string `""` if no pipeline is assigned. |

### Set Pipeline Assignment

```
PUT /api/v1/pipelines/{project_id}/assignment
```

**Description**: Updates the assigned pipeline for a project. Called by the Projects page pipeline selector. When the assignment changes, React Query cache invalidation causes the chat's `useSelectedPipeline` hook to refetch, keeping the chat in sync (FR-004).

**Request Body**:

```json
{
  "pipeline_id": "uuid-of-pipeline"
}
```

**Response** (200 OK): Same as GET response above.

### List Pipelines

```
GET /api/v1/pipelines/{project_id}
```

**Description**: Lists all saved pipeline configurations for a project. Used by `useSelectedPipeline` to resolve the pipeline name from the assigned pipeline ID.

**Response** (200 OK):

```json
{
  "pipelines": [
    {
      "id": "uuid-1",
      "name": "Full Review Pipeline",
      "description": "...",
      "is_preset": false,
      "created_at": "2026-03-01T00:00:00Z",
      "updated_at": "2026-03-07T00:00:00Z"
    }
  ]
}
```
