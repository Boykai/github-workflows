# API Contract: App Deletion (Parent Issue Close)

**Feature**: 051-app-creation-ux | **Date**: 2026-03-18

## DELETE /api/apps/{name}

Deletes an application and closes its parent issue if one exists.

### Request

No request body.

### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| name | string | App name (must be stopped, error, or creating) |

### Response — Success (204)

No response body.

### Response — Validation Error (422)

```json
{
  "detail": "Cannot delete app 'my-app': must stop the app first."
}
```

### Behavior Changes (This Feature)

1. **Close parent issue** (best-effort): When the app has a `parent_issue_number` and `parent_issue_url`, the handler extracts the `owner/repo` from the URL and calls the GitHub REST API to close the issue:

   ```
   PATCH /repos/{owner}/{repo}/issues/{parent_issue_number}
   Body: { "state": "closed" }
   ```

2. **Best-effort**: If closing fails (network error, permission issue, issue already closed), the failure is logged but does not block app deletion.

3. **Requires access_token and github_service**: The API endpoint must pass the user's access token and GitHub service instance to `delete_app()` so it can make the GitHub API call.

### Sequence Diagram

```
Client                     Backend                          GitHub API
  │                           │                                │
  │──DELETE /api/apps/{name}─>│                                │
  │                           │──get_app(name)                 │
  │                           │──validate status               │
  │                           │                                │
  │                           │──[if parent_issue_number]      │
  │                           │  PATCH issue state=closed─────>│
  │                           │  <──200 OK (or error, logged)──│
  │                           │                                │
  │                           │──DELETE FROM apps              │
  │<──204 No Content──────────│                                │
```

### Implementation Notes

- The `delete_app()` function gains optional `access_token: str` and `github_service: GitHubProjectsService` keyword arguments
- When both are provided and the app has `parent_issue_number`, the function attempts to close the issue
- The `owner` and `repo` are parsed from `github_repo_url` or `external_repo_url` depending on `repo_type`
- The API endpoint (`api/apps.py`) must inject these dependencies from the request context
