# API Contracts: Debug & Fix Apps Page — New App Creation UX

**Feature**: `051-fix-app-creation-ux` | **Date**: 2026-03-17

## Modified Endpoints

### POST /apps

**Change**: No request schema changes. Response schema extended with parent issue fields. Warning collection expanded to include template file warnings and pipeline setup warnings.

#### Request (unchanged)

```json
{
  "name": "my-new-app",
  "display_name": "My New App",
  "description": "An example application",
  "repo_type": "new-repo",
  "repo_owner": "Boykai",
  "repo_visibility": "private",
  "create_project": true,
  "pipeline_id": "preset-abc-123",
  "azure_client_id": "optional-client-id",
  "azure_client_secret": "optional-secret"
}
```

**`pipeline_id`** (existing field, now functional):
- When provided and non-null: triggers Parent Issue creation + sub-issues + pipeline polling
- When null or omitted: no Parent Issue created, app is standalone

#### Response (extended)

```json
{
  "name": "my-new-app",
  "display_name": "My New App",
  "description": "An example application",
  "directory_path": "apps/my-new-app",
  "associated_pipeline_id": "preset-abc-123",
  "status": "active",
  "repo_type": "new-repo",
  "external_repo_url": null,
  "github_repo_url": "https://github.com/Boykai/my-new-app",
  "github_project_url": "https://github.com/users/Boykai/projects/42",
  "github_project_id": "PVT_abc123",
  "parent_issue_number": 1,
  "parent_issue_url": "https://github.com/Boykai/my-new-app/issues/1",
  "port": null,
  "error_message": null,
  "created_at": "2026-03-17T18:00:00Z",
  "updated_at": "2026-03-17T18:00:00Z",
  "warnings": [
    "Failed to read template file '.github/agents/custom.md': UnicodeDecodeError",
    "Azure secret storage failed: credentials rejected"
  ]
}
```

**New response fields**:
| Field | Type | Description |
|-------|------|-------------|
| `parent_issue_number` | `integer \| null` | GitHub issue number, null if no pipeline selected or creation failed |
| `parent_issue_url` | `string \| null` | Full GitHub issue URL, null if no pipeline selected or creation failed |

**Extended `warnings[]` sources**:
| Source | Example Warning |
|--------|----------------|
| Template file failure | `"Failed to read template file '{path}': {error}"` |
| Azure secret storage | `"Azure secret storage failed: {error}"` (existing) |
| Project creation | `"GitHub Project creation failed: {error}"` (existing) |
| Parent issue creation | `"Pipeline setup: Failed to create parent issue: {error}"` |
| Sub-issue creation | `"Pipeline setup: Failed to create sub-issues: {error}"` |
| Polling start | `"Pipeline setup: Failed to start polling: {error}"` |

---

### GET /apps/{name}

**Change**: Response now includes `parent_issue_number` and `parent_issue_url` fields.

#### Response (extended)

Same schema as POST /apps response, minus the transient `warnings` field (warnings are only returned at creation time).

```json
{
  "name": "my-new-app",
  "parent_issue_number": 1,
  "parent_issue_url": "https://github.com/Boykai/my-new-app/issues/1",
  "...": "other existing fields"
}
```

**Backward compatibility**: Apps created before this feature return `parent_issue_number: null` and `parent_issue_url: null`.

---

### DELETE /apps/{name}

**Change**: If the app has a `parent_issue_number`, the endpoint now closes the corresponding GitHub issue before deleting the app record. This is best-effort — closure failure does not block deletion.

#### Behavior

1. Load app record
2. If `parent_issue_number` is set and `github_repo_url` is set:
   - Parse owner/repo from `github_repo_url`
   - Call GitHub API to close issue `parent_issue_number`
   - On failure: log warning, continue
3. Delete app record
4. Return success

#### Response (unchanged)

```json
{
  "message": "App 'my-new-app' deleted"
}
```

---

### GET /apps

**Change**: List response includes the new fields for each app.

No request changes. Each app in the array now includes `parent_issue_number` and `parent_issue_url`.

---

## Internal Service Contracts

### `build_template_files()` — Modified Return Type

**File**: `apps/solune/backend/src/services/template_files.py`

**Before**:
```python
def build_template_files(repo_name: str, display_name: str) -> list[dict[str, str]]:
```

**After**:
```python
def build_template_files(repo_name: str, display_name: str) -> tuple[list[dict[str, str]], list[str]]:
    """Returns (files, warnings) where warnings contains messages for each file that failed to read."""
```

### `create_app_with_new_repo()` — Extended Warning Collection

**File**: `apps/solune/backend/src/services/app_service.py`

**New internal steps** (after template commit, before DB insert):
```python
# Pseudo-contract for pipeline setup
if pipeline_id:
    try:
        workflow_config = load_or_create_workflow_configuration(pipeline_id, session)
        parent_issue = create_issue(owner, repo, title="Build {display_name}", body=tracking_body)
        add_to_project(parent_issue, project_id)
        sub_issues = orchestrator.create_all_sub_issues(workflow_context)
        pipeline_state = PipelineState(...)
        set_pipeline_state(parent_issue.number, pipeline_state)
        ensure_polling_started(access_token, project_id, owner, repo)
        # Store on app record
        parent_issue_number = parent_issue.number
        parent_issue_url = parent_issue.url
    except Exception as exc:
        warnings.append(f"Pipeline setup failed: {exc}")
```

### Branch-Readiness Polling — Modified Retry Logic

**Before**: 5 retries × 1s fixed delay (5s max)
**After**: 8 retries × exponential backoff (base=0.5s, max=3s, ~18.5s max)

```python
# Retry schedule:
# Attempt 0: 0.5s
# Attempt 1: 1.0s
# Attempt 2: 2.0s
# Attempt 3: 3.0s (capped)
# Attempt 4: 3.0s
# Attempt 5: 3.0s
# Attempt 6: 3.0s
# Attempt 7: 3.0s
# Total max wait: ~18.5s
```

---

## Error Handling Contract

| Scenario | HTTP Status | Behavior |
|----------|-------------|----------|
| Template files partially fail | 201 Created | App created, `warnings[]` includes file-specific messages |
| All template files fail | 201 Created | App created (empty repo), `warnings[]` includes all file messages |
| Azure secret storage fails | 201 Created | App created, `warnings[]` includes Azure error (existing) |
| Parent issue creation fails | 201 Created | App created, `parent_issue_*` fields null, `warnings[]` includes pipeline error |
| Sub-issue creation fails | 201 Created | App created, parent issue exists, `warnings[]` includes sub-issue error |
| Polling start fails | 201 Created | App created, parent issue + sub-issues exist, `warnings[]` includes polling error |
| Branch readiness exhausted | 500 Error | App creation fails with validation error |
| GitHub repo creation fails | 500 Error | App creation fails with GitHub API error |
| Invalid pipeline_id | 500 Error | App creation fails — pipeline config not found |
