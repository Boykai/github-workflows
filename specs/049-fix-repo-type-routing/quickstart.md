# Quickstart: Fix Repo-Type Routing

**Feature**: 049-fix-repo-type-routing | **Branch**: `049-fix-repo-type-routing`

## Overview

This feature fixes three routing bugs in app creation:

1. **Pipeline launch routing**: Issues land in wrong repo for `new-repo` and `external-repo` apps
2. **Scaffold routing**: External-repo scaffold commits go to Solune's default repo instead of the external repo
3. **Missing project**: External-repo apps have no Project V2, so pipeline launch silently fails

## Changes Summary

### 1. `parse_github_url()` utility (utils.py)

New function that extracts `(owner, repo)` from a GitHub URL. Validates format and rejects non-github.com hosts.

### 2. External-repo scaffold routing (app_service.py)

The `create_app()` function's non-`NEW_REPO` branch currently uses `settings.default_repo_owner/name` for all scaffold operations. The fix checks if `repo_type == EXTERNAL_REPO`, parses `external_repo_url`, and passes the extracted owner/repo to `get_branch_head_oid()` and `commit_files()`.

### 3. External-repo project auto-creation (app_service.py)

After scaffold commit for external-repo apps, auto-create a Project V2 on the external repo using `create_project_v2()` + `link_project_to_repository()`. Store `github_project_id` and `github_project_url` on the app record.

### 4. Pipeline launch routing (apps.py)

Replace the current `launch_project_id = payload.project_id or app.github_project_id` with repo-type-aware logic:

```python
if app.repo_type == RepoType.SAME_REPO:
    launch_project_id = payload.project_id
else:
    launch_project_id = app.github_project_id
```

### 5. Frontend project_id scoping (CreateAppDialog.tsx)

Only include `project_id` in the payload when `repoType === 'same-repo'`:

```typescript
if (selectedPipelineId) {
  payload.pipeline_id = selectedPipelineId;
  if (repoType === 'same-repo' && projectId) {
    payload.project_id = projectId;
  }
}
```

## Verification

```bash
# Run backend tests
cd solune/backend && python -m pytest tests/ -x -q

# Run frontend tests  
cd solune/frontend && npx vitest run

# Manual verification: create apps of each type and verify issue/scaffold placement
```
