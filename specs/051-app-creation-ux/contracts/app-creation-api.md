# API Contract: App Creation

**Feature**: 051-app-creation-ux | **Date**: 2026-03-18

## POST /api/apps

Creates a new application with optional pipeline integration.

### Request

```json
{
  "name": "my-app",
  "display_name": "My App",
  "description": "An example application",
  "branch": "app/my-app",
  "pipeline_id": "preset-full-stack",
  "repo_type": "new-repo",
  "repo_owner": "my-org",
  "repo_visibility": "private",
  "create_project": true,
  "ai_enhance": true,
  "azure_client_id": "...",
  "azure_client_secret": "..."
}
```

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| name | string | Yes | — | App name (2–64 chars, `[a-z0-9-]`) |
| display_name | string | Yes | — | Human-readable name (1–128 chars) |
| description | string | No | `""` | App description |
| branch | string | No | null | Target branch for scaffold commit |
| pipeline_id | string | No | null | Pipeline config ID for auto-orchestration |
| repo_type | enum | No | `"same-repo"` | `same-repo`, `external-repo`, `new-repo` |
| repo_owner | string | No | null | GitHub owner for new-repo type |
| repo_visibility | enum | No | `"private"` | `public` or `private` (new-repo only) |
| create_project | boolean | No | `true` | Create GitHub Project V2 (new-repo only) |
| ai_enhance | boolean | No | `true` | Enable AI-enhanced description |
| azure_client_id | string | No | null | Azure client ID (paired with secret) |
| azure_client_secret | string | No | null | Azure client secret (paired with ID) |

### Response — Success (201)

```json
{
  "name": "my-app",
  "display_name": "My App",
  "description": "An example application",
  "directory_path": "apps/my-app",
  "associated_pipeline_id": "preset-full-stack",
  "status": "creating",
  "repo_type": "new-repo",
  "external_repo_url": null,
  "github_repo_url": "https://github.com/my-org/my-app",
  "github_project_url": "https://github.com/orgs/my-org/projects/42",
  "github_project_id": "PVT_abc123",
  "parent_issue_number": 1,
  "parent_issue_url": "https://github.com/my-org/my-app/issues/1",
  "port": null,
  "error_message": null,
  "created_at": "2026-03-18T03:36:18Z",
  "updated_at": "2026-03-18T03:36:18Z",
  "warnings": [
    "Failed to read template file: .specify/templates/broken-file.md"
  ]
}
```

**New Fields in Response** (added by this feature):

| Field | Type | Description |
|-------|------|-------------|
| parent_issue_number | integer \| null | GitHub issue number if pipeline was selected and parent issue created |
| parent_issue_url | string \| null | Full URL to the parent issue on GitHub |

**Warnings Array**:

The `warnings` field is a transient list populated when non-fatal operations fail during creation:

| Warning Source | Example Message |
|----------------|-----------------|
| Template file read failure | `"Failed to read template file: {path}"` |
| Azure secret storage failure | `"Azure credentials could not be stored: {reason}"` |
| Parent issue creation failure | `"Could not create parent issue: {reason}"` |
| Sub-issue creation failure | `"Could not create sub-issues for pipeline: {reason}"` |
| Polling start failure | `"Could not start pipeline polling: {reason}"` |

### Response — Validation Error (422)

```json
{
  "detail": "App name 'my-app' already exists."
}
```

### Response — Server Error (500)

```json
{
  "detail": "Failed to create repository: {GitHub API error}"
}
```

### Behavior Changes (This Feature)

1. **Template file warnings**: When `build_template_files()` fails to read one or more files, the failed paths are added to the `warnings[]` array (previously silent)
2. **Branch poll backoff**: Retry logic increased from 5 × 1s to ~10 × exponential backoff (~15s max)
3. **Parent issue creation** (when `pipeline_id` is provided):
   - Creates parent issue in target repo with title `"Build {display_name}"`
   - Creates sub-issues per agent stage
   - Starts polling service
   - Stores `parent_issue_number` and `parent_issue_url` on App record
   - All best-effort — failures add warnings
4. **No pipeline selected**: When `pipeline_id` is null/omitted, no parent issue or pipeline is created (unchanged behavior)

### Sequence Diagram

```
Client                     Backend                          GitHub API
  │                           │                                │
  │──POST /api/apps──────────>│                                │
  │                           │──create_repository()──────────>│
  │                           │<──repo created─────────────────│
  │                           │                                │
  │                           │──poll branch HEAD (≤15s)──────>│
  │                           │<──head_oid─────────────────────│
  │                           │                                │
  │                           │──build_template_files()        │
  │                           │  (collect warnings)            │
  │                           │──commit_files()───────────────>│
  │                           │<──committed────────────────────│
  │                           │                                │
  │                           │──[if pipeline_id]              │
  │                           │  create_issue()───────────────>│
  │                           │  <──issue created──────────────│
  │                           │  create_all_sub_issues()──────>│
  │                           │  <──sub-issues created─────────│
  │                           │  ensure_polling_started()      │
  │                           │                                │
  │                           │──store_secrets() (best-effort)>│
  │                           │──create_project() (optional)──>│
  │                           │──INSERT INTO apps              │
  │<──201 App response────────│                                │
```

## GET /api/apps/{name}

Returns a single app. Response includes the new `parent_issue_number` and `parent_issue_url` fields.

**No request changes** — the response schema matches the POST response above.

## GET /api/apps

Returns all apps. Each app in the response array includes the new `parent_issue_number` and `parent_issue_url` fields.

**No request changes** — each item in the response array matches the POST response schema.
