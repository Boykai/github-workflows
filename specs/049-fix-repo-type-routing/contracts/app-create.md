# API Contract: App Creation (Updated for Repo-Type Routing)

## POST /api/apps

Creates a new application with directory scaffolding.

### Request Body (AppCreate)

```yaml
type: object
required: [name, display_name]
properties:
  name:
    type: string
    pattern: "^[a-z0-9][a-z0-9-]*[a-z0-9]$"
    minLength: 2
    maxLength: 64
  display_name:
    type: string
    minLength: 1
    maxLength: 128
  description:
    type: string
    default: ""
  branch:
    type: string
    nullable: true
    description: "Target branch (required for same-repo and external-repo)"
  pipeline_id:
    type: string
    nullable: true
  project_id:
    type: string
    nullable: true
    description: |
      User's selected project ID. Only sent for same-repo apps.
      For new-repo/external-repo, the backend determines the correct project.
  repo_type:
    type: string
    enum: [same-repo, new-repo, external-repo]
    default: same-repo
  external_repo_url:
    type: string
    nullable: true
    description: |
      Required when repo_type is external-repo.
      Must match: https://github.com/{owner}/{repo}
      GitHub Enterprise URLs are rejected.
  repo_owner:
    type: string
    nullable: true
    description: "Required for new-repo type"
  repo_visibility:
    type: string
    enum: [public, private]
    default: private
  create_project:
    type: boolean
    default: true
  ai_enhance:
    type: boolean
    default: true
  azure_client_id:
    type: string
    nullable: true
  azure_client_secret:
    type: string
    nullable: true
    writeOnly: true
```

### Response — 201 Created

Returns the created `App` object.

### Behavioral Changes by Repo Type

#### same-repo (default)
- **Scaffold**: Commits files to `settings.default_repo_owner`/`settings.default_repo_name` on `branch`
- **Pipeline**: Uses `payload.project_id` to resolve target repo
- **No change from current behavior**

#### new-repo
- **Scaffold**: Creates new repo via `create_repository()`, commits template files there
- **Pipeline**: Uses `app.github_project_id` (ignores `payload.project_id`)
- **Fix**: `create_app_endpoint` now routes `launch_project_id = app.github_project_id`

#### external-repo
- **Scaffold**: Parses `external_repo_url` → commits files to external repo on `branch`
- **Project**: Auto-creates Project V2 on external repo if none exists
- **Pipeline**: Uses `app.github_project_id` (auto-created project)
- **Fix**: Both scaffold routing and project auto-creation are new behavior

### Error Responses

| Status | Condition |
|--------|-----------|
| 400 | `external_repo_url` missing for external-repo type |
| 400 | `external_repo_url` is not a valid `github.com` URL |
| 400 | `branch` missing for same-repo or external-repo |
| 400 | Insufficient permissions on external repo |
| 409 | App name already exists |
| 422 | Pydantic validation failure |
