# API Contracts: Repository Cleanup Operations

**Feature**: 015-stale-cleanup-button  
**Date**: 2026-03-01  
**Base Path**: `/api/v1/cleanup`

All endpoints require a valid session cookie (GitHub OAuth). Responses use standard JSON. Authentication failures return 401. The authenticated user must have `push` access to the repository.

---

## POST /cleanup/preflight

**Description**: Perform a preflight check that fetches all branches, open PRs, and open issues on the linked project board. Computes and returns categorized lists of items scheduled for deletion and items to be preserved, with preservation reasons. Also verifies user permissions. No mutations are performed.

**Auth**: Required (session cookie via `get_session_dep`)

### Request Body

```json
{
  "owner": "Boykai",
  "repo": "github-workflows",
  "project_id": "PVT_kwHOABcRss4A..."
}
```

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `owner` | string | Yes | Repository owner (user or org) |
| `repo` | string | Yes | Repository name |
| `project_id` | string | Yes | GitHub Projects v2 project node ID |

### Response 200 OK

```json
{
  "branches_to_delete": [
    {
      "name": "stale-experiment",
      "eligible_for_deletion": true,
      "linked_issue_number": null,
      "linked_issue_title": null,
      "linking_method": null,
      "preservation_reason": null
    }
  ],
  "branches_to_preserve": [
    {
      "name": "main",
      "eligible_for_deletion": false,
      "linked_issue_number": null,
      "linked_issue_title": null,
      "linking_method": null,
      "preservation_reason": "Default protected branch"
    },
    {
      "name": "015-stale-cleanup-button",
      "eligible_for_deletion": false,
      "linked_issue_number": 1059,
      "linked_issue_title": "Add 'Clean Up' Button",
      "linking_method": "naming_convention",
      "preservation_reason": "Linked to open issue #1059 on project board"
    }
  ],
  "prs_to_close": [
    {
      "number": 999,
      "title": "Old feature attempt",
      "head_branch": "stale-experiment",
      "referenced_issues": [],
      "eligible_for_deletion": true,
      "preservation_reason": null
    }
  ],
  "prs_to_preserve": [
    {
      "number": 1065,
      "title": "Add clean-up button feature",
      "head_branch": "copilot/add-clean-up-button-feature",
      "referenced_issues": [1059],
      "eligible_for_deletion": false,
      "preservation_reason": "References open issue #1059 on project board"
    }
  ],
  "open_issues_on_board": 12,
  "has_permission": true,
  "permission_error": null
}
```

### Response 403 Forbidden — Insufficient Permissions

```json
{
  "error": "Insufficient permissions to perform cleanup",
  "details": {
    "required": "push",
    "current": "read",
    "message": "You need at least push access to this repository to delete branches and close pull requests."
  }
}
```

### Response 401 Unauthorized

```json
{
  "error": "Authentication required"
}
```

### Response 422 Unprocessable Entity — Invalid Input

```json
{
  "error": "Validation error",
  "details": {
    "field": "project_id",
    "message": "Project not found or not accessible"
  }
}
```

---

## POST /cleanup/execute

**Description**: Execute the cleanup operation. Deletes the specified branches and closes the specified PRs sequentially, respecting rate limits. Returns a summary report with per-item results. The main branch is rejected server-side even if included in the request.

**Auth**: Required (session cookie via `get_session_dep`)

### Request Body

```json
{
  "owner": "Boykai",
  "repo": "github-workflows",
  "project_id": "PVT_kwHOABcRss4A...",
  "branches_to_delete": ["stale-experiment", "old-feature"],
  "prs_to_close": [999, 1001]
}
```

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `owner` | string | Yes | Repository owner |
| `repo` | string | Yes | Repository name |
| `project_id` | string | Yes | Project board ID (for audit trail) |
| `branches_to_delete` | string[] | Yes | Branch names to delete; `main` is rejected |
| `prs_to_close` | number[] | Yes | PR numbers to close |

### Response 200 OK

```json
{
  "operation_id": "550e8400-e29b-41d4-a716-446655440000",
  "branches_deleted": 2,
  "branches_preserved": 0,
  "prs_closed": 2,
  "prs_preserved": 0,
  "errors": [],
  "results": [
    {
      "item_type": "branch",
      "identifier": "stale-experiment",
      "action": "deleted",
      "reason": null,
      "error": null
    },
    {
      "item_type": "branch",
      "identifier": "old-feature",
      "action": "deleted",
      "reason": null,
      "error": null
    },
    {
      "item_type": "pr",
      "identifier": "999",
      "action": "closed",
      "reason": null,
      "error": null
    },
    {
      "item_type": "pr",
      "identifier": "1001",
      "action": "closed",
      "reason": null,
      "error": null
    }
  ]
}
```

### Response 200 OK — Partial Failure

```json
{
  "operation_id": "550e8400-e29b-41d4-a716-446655440000",
  "branches_deleted": 1,
  "branches_preserved": 0,
  "prs_closed": 1,
  "prs_preserved": 0,
  "errors": [
    {
      "item_type": "branch",
      "identifier": "protected-branch",
      "action": "failed",
      "reason": null,
      "error": "403 Forbidden: Branch is protected by branch protection rules"
    },
    {
      "item_type": "pr",
      "identifier": "1001",
      "action": "failed",
      "reason": null,
      "error": "404 Not Found: Pull request not found or already closed"
    }
  ],
  "results": [
    {
      "item_type": "branch",
      "identifier": "stale-experiment",
      "action": "deleted",
      "reason": null,
      "error": null
    },
    {
      "item_type": "branch",
      "identifier": "protected-branch",
      "action": "failed",
      "reason": null,
      "error": "403 Forbidden: Branch is protected by branch protection rules"
    },
    {
      "item_type": "pr",
      "identifier": "999",
      "action": "closed",
      "reason": null,
      "error": null
    },
    {
      "item_type": "pr",
      "identifier": "1001",
      "action": "failed",
      "reason": null,
      "error": "404 Not Found: Pull request not found or already closed"
    }
  ]
}
```

### Response 400 Bad Request — Main Branch Included

```json
{
  "error": "Cannot delete the main branch",
  "details": {
    "message": "The 'main' branch was included in the deletion list and has been rejected. The main branch is unconditionally protected."
  }
}
```

### Response 403 Forbidden — Insufficient Permissions

```json
{
  "error": "Insufficient permissions to perform cleanup",
  "details": {
    "required": "push",
    "current": "read",
    "message": "You need at least push access to this repository to delete branches and close pull requests."
  }
}
```

### Response 401 Unauthorized

```json
{
  "error": "Authentication required"
}
```

---

## GET /cleanup/history

**Description**: Retrieve the audit trail of past cleanup operations for the authenticated user on a specific repository.

**Auth**: Required (session cookie via `get_session_dep`)

### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `owner` | string | Yes | Repository owner |
| `repo` | string | Yes | Repository name |
| `limit` | number | No | Max results (default: 10, max: 50) |

### Response 200 OK

```json
{
  "operations": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "started_at": "2026-03-01T15:30:00Z",
      "completed_at": "2026-03-01T15:31:15Z",
      "status": "completed",
      "branches_deleted": 5,
      "branches_preserved": 3,
      "prs_closed": 2,
      "prs_preserved": 4,
      "errors_count": 0,
      "details": {
        "results": [
          {
            "item_type": "branch",
            "identifier": "stale-experiment",
            "action": "deleted",
            "reason": null,
            "error": null
          }
        ]
      }
    }
  ],
  "count": 1
}
```

### Response 401 Unauthorized

```json
{
  "error": "Authentication required"
}
```

---

## Error Handling

All endpoints follow the existing error response patterns:

| Status | Meaning | When |
|--------|---------|------|
| 400 | Bad Request | Main branch included in deletion list, validation failure |
| 401 | Unauthorized | No session cookie, expired session |
| 403 | Forbidden | User lacks push access to repository |
| 404 | Not Found | Repository or project not found |
| 422 | Unprocessable Entity | Invalid project ID, project not accessible |
| 429 | Too Many Requests | GitHub API rate limit exceeded (returned after retries exhausted) |
| 500 | Internal Server Error | Unexpected server failure |

### Rate Limit Behavior

When the GitHub API returns 429 or 403 with rate-limit headers during execution:
1. The backend retries with exponential backoff (up to 3 retries, 1s–30s).
2. If retries are exhausted for an individual item, that item is marked as `failed` with an error message.
3. The operation continues with remaining items (no abort on individual failure).
4. The summary report includes all failures with actionable error messages.

### Authentication Error Flow

When a 401 is returned during any cleanup operation, the frontend should:
1. Display an inline message: "Your session has expired. Please sign in again."
2. Provide a re-authentication link/button that triggers `authApi.login()`.
