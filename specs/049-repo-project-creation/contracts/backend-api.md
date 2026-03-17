# Contract: Backend REST API Endpoints

**Feature**: 049-repo-project-creation

This document defines the REST API contracts between the Solune frontend and backend for new repository and project creation features.

---

## Contract 1: Create App with New Repository

**Endpoint**: `POST /api/v1/apps`
**Producer**: Backend `create_app_endpoint()` in `solune/backend/src/api/apps.py`
**Consumer**: Frontend `appsApi.create()` in `solune/frontend/src/services/api.ts`

### Request

```json
{
  "name": "my-new-app",
  "display_name": "My New App",
  "description": "An app with a new repository",
  "repo_type": "new-repo",
  "repo_owner": "username-or-org",
  "repo_visibility": "private",
  "create_project": true,
  "ai_enhance": true
}
```

| Field | Type | Required | Default | Constraints |
|---|---|---|---|---|
| name | string | Yes | — | 2-64 chars, `^[a-z0-9][a-z0-9-]*[a-z0-9]$`, not reserved |
| display_name | string | Yes | — | 1-128 chars |
| description | string | No | `""` | — |
| repo_type | string | No | `"same-repo"` | One of: `same-repo`, `external-repo`, `new-repo` |
| branch | string | Conditional | — | Required when `repo_type != "new-repo"`; 1-256 chars |
| repo_owner | string | Conditional | — | Required when `repo_type = "new-repo"` |
| repo_visibility | string | No | `"private"` | One of: `public`, `private` |
| create_project | boolean | No | `true` | Only used when `repo_type = "new-repo"` |
| pipeline_id | string | No | `null` | — |
| external_repo_url | string | No | `null` | Used when `repo_type = "external-repo"` |
| ai_enhance | boolean | No | `true` | — |

### Response (201 Created)

```json
{
  "name": "my-new-app",
  "display_name": "My New App",
  "description": "An app with a new repository",
  "directory_path": "apps/my-new-app",
  "associated_pipeline_id": null,
  "status": "active",
  "repo_type": "new-repo",
  "external_repo_url": null,
  "github_repo_url": "https://github.com/username/my-new-app",
  "github_project_url": "https://github.com/users/username/projects/42",
  "github_project_id": "PVT_kwDO...",
  "port": null,
  "error_message": null,
  "created_at": "2026-03-17T04:57:35Z",
  "updated_at": "2026-03-17T04:57:35Z"
}
```

### Error Responses

| Status | Condition | Body |
|---|---|---|
| 400 | Invalid app name or missing required fields | `{"detail": "Invalid app name 'X': ..."}` |
| 400 | repo_owner missing for new-repo type | `{"detail": "repo_owner is required for new-repo type"}` |
| 409 | App name already exists | `{"detail": "App 'X' already exists."}` |
| 422 | GitHub repo creation failed (e.g., name conflict) | `{"detail": "Failed to create repository: ..."}` |

### Contract Rules

- When `repo_type = "new-repo"`, the backend creates a GitHub repository, commits template files, optionally creates and links a Project V2, then inserts a DB record.
- If project creation fails after repo success, the app is created with `github_project_url = null` and `github_project_id = null` — this is NOT an error response.
- The `branch` field is ignored for `repo_type = "new-repo"` — the default branch from the created repo is used.
- The response always includes the full `App` object with all fields.

---

## Contract 2: List Available Owners

**Endpoint**: `GET /api/v1/apps/owners`
**Producer**: Backend `list_owners_endpoint()` in `solune/backend/src/api/apps.py`
**Consumer**: Frontend `appsApi.owners()` in `solune/frontend/src/services/api.ts`

### Request

No request body. Authentication via session cookie.

### Response (200 OK)

```json
[
  {
    "login": "username",
    "avatar_url": "https://avatars.githubusercontent.com/u/12345",
    "type": "User"
  },
  {
    "login": "my-org",
    "avatar_url": "https://avatars.githubusercontent.com/u/67890",
    "type": "Organization"
  }
]
```

| Field | Type | Description |
|---|---|---|
| login | string | GitHub username or organization name |
| avatar_url | string | URL to the GitHub avatar image |
| type | string | Either `"User"` or `"Organization"` |

### Contract Rules

- The authenticated user's personal account is always the first item in the list.
- Organizations are filtered to only those where the user has repository creation permissions.
- The list is not cached on the backend; frontend uses TanStack Query with 30s stale time.

---

## Contract 3: Create Standalone Project

**Endpoint**: `POST /api/v1/projects/create`
**Producer**: Backend in `solune/backend/src/api/projects.py`
**Consumer**: Frontend `projectsApi.create()` in `solune/frontend/src/services/api.ts`

### Request

```json
{
  "title": "My Project Board",
  "owner": "username-or-org",
  "repo_owner": "username",
  "repo_name": "existing-repo"
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| title | string | Yes | Project title |
| owner | string | Yes | GitHub owner for the project |
| repo_owner | string | No | Repository owner to link (optional) |
| repo_name | string | No | Repository name to link (optional) |

### Response (201 Created)

```json
{
  "project_id": "PVT_kwDO...",
  "project_number": 42,
  "project_url": "https://github.com/users/username/projects/42"
}
```

| Field | Type | Description |
|---|---|---|
| project_id | string | GitHub Project V2 node ID |
| project_number | integer | Project number within the owner |
| project_url | string | URL to the project board on GitHub |

### Error Responses

| Status | Condition | Body |
|---|---|---|
| 400 | Missing required title or owner | `{"detail": "title and owner are required"}` |
| 422 | GitHub project creation failed | `{"detail": "Failed to create project: ..."}` |

### Contract Rules

- After successful creation, the project is configured with Solune default status columns (best-effort).
- If `repo_owner` and `repo_name` are provided, the project is linked to the specified repository (best-effort).
- The frontend auto-selects the new project after receiving the response.
- The project list query cache is invalidated after successful creation.
