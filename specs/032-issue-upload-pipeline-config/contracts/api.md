# API Contracts: Projects Page — Upload GitHub Parent Issue Description & Select Agent Pipeline Config

**Feature**: 032-issue-upload-pipeline-config | **Date**: 2026-03-10

## Base URL

All endpoints are prefixed with `/api/v1` and require an authenticated session (same auth pattern as existing endpoints).

---

## Primary Endpoint (Existing — No Changes)

### Launch Pipeline with Issue Description

```text
POST /api/v1/pipelines/{project_id}/launch
```

**Description**: Launches an agent pipeline by creating a GitHub Issue from the provided description, converting the selected pipeline's stages into agent assignments, creating per-agent sub-issues, and adding everything to the project board. This endpoint already exists and requires no modifications for this feature.

**Path Parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| `project_id` | string | The GitHub project node ID (e.g., `PVT_abc123`) |

**Request Body** (`PipelineIssueLaunchRequest`):

```json
{
  "issue_description": "## Feature: Dark Mode Support\n\nAs a user, I want...",
  "pipeline_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `issue_description` | string | Yes | min 1, max 65,536 chars | Full text of the GitHub Parent Issue description (Markdown or plain text) |
| `pipeline_id` | string | Yes | min 1 char (UUID) | ID of the selected Agent Pipeline Config |

**Response** (200 OK — `WorkflowResult`):

```json
{
  "success": true,
  "issue_id": "I_abc123",
  "issue_number": 42,
  "issue_url": "https://github.com/owner/repo/issues/42",
  "project_item_id": "PVTI_xyz789",
  "current_status": "Backlog",
  "message": "Issue #42 created and launched with the selected pipeline."
}
```

| Field | Type | Description |
|-------|------|-------------|
| `success` | boolean | Whether the launch completed successfully |
| `issue_id` | string \| null | GitHub node ID of the created issue |
| `issue_number` | integer \| null | GitHub issue number |
| `issue_url` | string \| null | Full URL to the created GitHub issue |
| `project_item_id` | string \| null | Project board item ID |
| `current_status` | string \| null | Board column the issue was placed in |
| `message` | string | Human-readable result description |

**Backend Processing Steps**:

1. Normalize `issue_description` (collapse excessive whitespace, trim).
2. Resolve GitHub repository (`owner`, `repo`) from `project_id` via GitHub Projects API.
3. Fetch `PipelineConfig` from `pipeline_configs` by `pipeline_id`. Return `404` if not found.
4. Set `assigned_pipeline_id` in `project_settings` for the project.
5. Convert pipeline stages → `WorkflowConfiguration.agent_mappings`.
6. Append agent tracking metadata to issue body (status table with agent assignments).
7. Validate total issue body length ≤ `GITHUB_ISSUE_BODY_MAX_LENGTH` (65,535 chars). Return `422` if exceeded.
8. Determine blocking mode from pipeline config + assignment override.
9. Create GitHub Issue via GitHub API (`POST /repos/{owner}/{repo}/issues`).
10. Add issue to project board (`addProjectV2ItemById` mutation).
11. Create per-agent sub-issues (one per agent in the pipeline).
12. Enqueue issue for blocking queue (if blocking enabled).
13. Return `WorkflowResult`.

**Error Responses**:

| Status | Error | Condition |
|--------|-------|-----------|
| `401 Unauthorized` | `AuthorizationError` | Missing or invalid session |
| `404 Not Found` | `NotFoundError` | `pipeline_id` does not match any existing pipeline config |
| `422 Unprocessable Entity` | `ValidationError` | Empty `issue_description`, empty `pipeline_id`, body exceeds max length, or missing project selection in session |
| `500 Internal Server Error` | `AppException` | GitHub API failure, database error, or orchestration failure |

---

## Supporting Endpoints (Existing — No Changes)

### List Pipeline Configs

```text
GET /api/v1/pipelines/{project_id}
```

**Description**: Lists all saved pipeline configurations for a project. Used by the frontend to populate the pipeline selector dropdown.

**Query Parameters**:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `sort` | string | `updated_at` | Sort field (`name`, `updated_at`, `created_at`) |
| `order` | string | `desc` | Sort order (`asc`, `desc`) |

**Response** (200 OK — `PipelineConfigListResponse`):

```json
{
  "pipelines": [
    {
      "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "name": "Full Review Pipeline",
      "description": "Complete code review with security and quality agents",
      "stage_count": 3,
      "agent_count": 5,
      "total_tool_count": 12,
      "is_preset": false,
      "preset_id": "",
      "stages": [
        {
          "id": "stage-1",
          "name": "Backlog",
          "order": 0,
          "agents": [
            {
              "id": "agent-1",
              "agent_slug": "speckit.specify",
              "agent_display_name": "Spec Writer",
              "model_id": "claude-sonnet-4-20250514",
              "model_name": "Claude Sonnet 4",
              "tool_ids": [],
              "tool_count": 0,
              "config": {}
            }
          ]
        }
      ],
      "blocking": false,
      "updated_at": "2026-03-10T10:00:00Z"
    }
  ],
  "total": 1
}
```

### Seed Pipeline Presets

```text
POST /api/v1/pipelines/{project_id}/seed-presets
```

**Description**: Seeds default pipeline presets for a project if none exist. Called by the frontend on first load of the Projects page to ensure at least one pipeline config is available.

**Response** (200 OK — `PresetSeedResult`):

```json
{
  "seeded": true,
  "count": 3,
  "pipelines": ["Default Pipeline", "Full Review Pipeline", "Quick Deploy"]
}
```
