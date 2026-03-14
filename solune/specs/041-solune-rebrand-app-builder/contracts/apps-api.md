# API Contract: App Management

**Feature**: `041-solune-rebrand-app-builder` | **Date**: 2026-03-14
**Base Path**: `/api/v1/apps`
**Auth**: All endpoints require authenticated session (existing `get_current_session` dependency)

## Endpoints

### List Applications

```
GET /api/v1/apps
```

**Description**: Returns all registered applications.

**Query Parameters**:
| Param | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `status` | string | No | — | Filter by status: `creating`, `active`, `stopped`, `error` |

**Response** `200 OK`:
```json
{
  "apps": [
    {
      "name": "my-app",
      "display_name": "My Application",
      "description": "A sample app",
      "directory_path": "apps/my-app",
      "associated_pipeline_id": "pipeline-123",
      "status": "active",
      "repo_type": "same-repo",
      "external_repo_url": null,
      "port": 3001,
      "error_message": null,
      "created_at": "2026-03-14T21:00:00Z",
      "updated_at": "2026-03-14T21:05:00Z"
    }
  ],
  "total": 1
}
```

---

### Create Application

```
POST /api/v1/apps
```

**Description**: Creates a new application, scaffolds its directory, and optionally creates a tracking issue.

**Request Body**:
```json
{
  "name": "my-app",
  "display_name": "My Application",
  "description": "A sample app built with Solune",
  "pipeline_id": "pipeline-123",
  "repo_type": "same-repo"
}
```

**Validation**:
- `name`: Required. Must match `^[a-z0-9][a-z0-9-]*[a-z0-9]$`, length 2-64. Must be unique. Rejects reserved names.
- `display_name`: Required. Non-empty, max 128 characters.
- `description`: Optional. Defaults to empty string.
- `pipeline_id`: Optional. Must reference an existing pipeline if provided.
- `repo_type`: Optional. Defaults to `same-repo`.

**Response** `201 Created`:
```json
{
  "name": "my-app",
  "display_name": "My Application",
  "description": "A sample app built with Solune",
  "directory_path": "apps/my-app",
  "associated_pipeline_id": "pipeline-123",
  "status": "creating",
  "repo_type": "same-repo",
  "external_repo_url": null,
  "port": null,
  "error_message": null,
  "created_at": "2026-03-14T21:00:00Z",
  "updated_at": "2026-03-14T21:00:00Z"
}
```

**Error Responses**:
- `400 Bad Request`: Invalid name format, reserved name, or missing required fields
- `409 Conflict`: App with this name already exists

---

### Get Application Details

```
GET /api/v1/apps/{app_name}
```

**Path Parameters**:
| Param | Type | Description |
|-------|------|-------------|
| `app_name` | string | The unique app identifier |

**Response** `200 OK`: Same shape as single app object above.

**Error Responses**:
- `404 Not Found`: App does not exist

---

### Update Application

```
PUT /api/v1/apps/{app_name}
```

**Description**: Updates an application's configuration. Cannot change the name or status (use lifecycle endpoints for status).

**Request Body** (all fields optional):
```json
{
  "display_name": "Updated Name",
  "description": "Updated description",
  "pipeline_id": "new-pipeline-456"
}
```

**Response** `200 OK`: Updated app object.

**Error Responses**:
- `404 Not Found`: App does not exist
- `400 Bad Request`: Invalid field values

---

### Delete Application

```
DELETE /api/v1/apps/{app_name}
```

**Description**: Deletes an application. The app must be in `stopped`, `error`, or `creating` status.

**Response** `204 No Content`: App deleted successfully.

**Error Responses**:
- `404 Not Found`: App does not exist
- `409 Conflict`: App is currently active (must be stopped first)

---

### Start Application

```
POST /api/v1/apps/{app_name}/start
```

**Description**: Starts an application, assigns a port, and transitions status to `active`.

**Response** `200 OK`:
```json
{
  "name": "my-app",
  "status": "active",
  "port": 3001,
  "error_message": null
}
```

**Error Responses**:
- `404 Not Found`: App does not exist
- `409 Conflict`: App is already active, or in `creating` status

---

### Stop Application

```
POST /api/v1/apps/{app_name}/stop
```

**Description**: Stops a running application, releases its port, transitions status to `stopped`.

**Response** `200 OK`:
```json
{
  "name": "my-app",
  "status": "stopped",
  "port": null,
  "error_message": null
}
```

**Error Responses**:
- `404 Not Found`: App does not exist
- `409 Conflict`: App is not currently active

---

### Get Application Status

```
GET /api/v1/apps/{app_name}/status
```

**Description**: Returns the current status and runtime information for an application.

**Response** `200 OK`:
```json
{
  "name": "my-app",
  "status": "active",
  "port": 3001,
  "error_message": null
}
```

**Error Responses**:
- `404 Not Found`: App does not exist

---

## Error Response Format

All error responses follow the existing API pattern:

```json
{
  "detail": "Human-readable error message"
}
```

## Status Transition Summary

| Endpoint | Valid From States | Resulting State |
|----------|-------------------|-----------------|
| `POST /apps` | — | `creating` |
| `POST /apps/{name}/start` | `stopped` | `active` |
| `POST /apps/{name}/stop` | `active` | `stopped` |
| `DELETE /apps/{name}` | `stopped`, `error`, `creating` | (deleted) |
