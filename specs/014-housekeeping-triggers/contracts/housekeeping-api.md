# API Contract: Housekeeping Issue Templates with Configurable Triggers

**Feature**: 014-housekeeping-triggers | **Date**: 2026-02-28

## Base Path

All endpoints are prefixed with `/api/v1/housekeeping`.

## Authentication

All endpoints require an authenticated session (same auth middleware as existing API routes via `get_current_session` dependency).

---

## Issue Templates

### List Templates

```
GET /api/v1/housekeeping/templates
```

**Query Parameters**:
| Param | Type | Required | Description |
|-------|------|----------|-------------|
| category | string | No | Filter by `built-in` or `custom` |

**Response** `200 OK`:
```json
{
  "templates": [
    {
      "id": "uuid-1",
      "name": "Security and Privacy Review",
      "title_pattern": "🔒 Security and Privacy Review – {date}",
      "body_content": "## Security and Privacy Review\n\nReview the codebase...",
      "category": "built-in",
      "created_at": "2026-02-28T00:00:00Z",
      "updated_at": "2026-02-28T00:00:00Z"
    }
  ]
}
```

### Get Template

```
GET /api/v1/housekeeping/templates/{template_id}
```

**Response** `200 OK`: Single template object (same shape as list item).

**Response** `404 Not Found`: `{"detail": "Template not found"}`

### Create Template

```
POST /api/v1/housekeeping/templates
```

**Request Body**:
```json
{
  "name": "Custom Review Template",
  "title_pattern": "📋 {task_name} – {date}",
  "body_content": "## Review\n\nPerform the following checks..."
}
```

**Response** `201 Created`: Created template object with generated `id`.

**Response** `422 Unprocessable Entity`: Validation errors (e.g., duplicate name).

### Update Template

```
PUT /api/v1/housekeeping/templates/{template_id}
```

**Request Body**: Same as create (all fields optional for partial update).

**Response** `200 OK`: Updated template object.

**Response** `404 Not Found`: `{"detail": "Template not found"}`

**Response** `403 Forbidden`: `{"detail": "Cannot modify built-in templates"}` (if attempting to modify a built-in template).

### Delete Template

```
DELETE /api/v1/housekeeping/templates/{template_id}
```

**Response** `200 OK`: `{"deleted": true}`

**Response** `404 Not Found`: `{"detail": "Template not found"}`

**Response** `403 Forbidden`: `{"detail": "Cannot delete built-in templates"}`

**Response** `409 Conflict`:
```json
{
  "detail": "Template is referenced by active housekeeping tasks",
  "referencing_tasks": ["task-uuid-1", "task-uuid-2"]
}
```
To force delete, include query parameter `?force=true`.

---

## Housekeeping Tasks

### List Tasks

```
GET /api/v1/housekeeping/tasks
```

**Query Parameters**:
| Param | Type | Required | Description |
|-------|------|----------|-------------|
| project_id | string | Yes | GitHub Project node ID |
| enabled | boolean | No | Filter by enabled/disabled |

**Response** `200 OK`:
```json
{
  "tasks": [
    {
      "id": "uuid-1",
      "name": "Weekly Security Review",
      "description": "Automated weekly security and privacy review",
      "template_id": "template-uuid-1",
      "template_name": "Security and Privacy Review",
      "sub_issue_config": null,
      "trigger_type": "time",
      "trigger_value": "0 9 * * 1",
      "last_triggered_at": "2026-02-21T09:00:00Z",
      "last_triggered_issue_count": 0,
      "enabled": true,
      "cooldown_minutes": 5,
      "project_id": "PVT_abc123",
      "created_at": "2026-02-01T00:00:00Z",
      "updated_at": "2026-02-20T00:00:00Z"
    }
  ]
}
```

### Get Task

```
GET /api/v1/housekeeping/tasks/{task_id}
```

**Response** `200 OK`: Single task object (same shape as list item).

**Response** `404 Not Found`: `{"detail": "Housekeeping task not found"}`

### Create Task

```
POST /api/v1/housekeeping/tasks
```

**Request Body**:
```json
{
  "name": "Weekly Security Review",
  "description": "Automated weekly security and privacy review",
  "template_id": "template-uuid-1",
  "sub_issue_config": null,
  "trigger_type": "time",
  "trigger_value": "0 9 * * 1",
  "cooldown_minutes": 5,
  "project_id": "PVT_abc123"
}
```

**Validation** (performed before save — FR-011):
- `template_id` must reference an existing template
- `trigger_type` must be `time` or `count`
- If `trigger_type` is `time`, `trigger_value` must be a valid cron expression or named preset (`daily`, `weekly`, `monthly`)
- If `trigger_type` is `count`, `trigger_value` must be a positive integer string
- `sub_issue_config` if provided must match the agent pipeline mapping structure
- `name` must be unique within the `project_id`

**Response** `201 Created`: Created task object with generated `id` and `last_triggered_issue_count` set to current parent issue count.

**Response** `422 Unprocessable Entity`:
```json
{
  "detail": "Validation failed",
  "errors": [
    {"field": "trigger_value", "message": "Invalid cron expression: '* * * * * *'"},
    {"field": "template_id", "message": "Template 'uuid-xxx' does not exist"}
  ]
}
```

### Update Task

```
PUT /api/v1/housekeeping/tasks/{task_id}
```

**Request Body**: Same as create (all fields optional for partial update).

**Response** `200 OK`: Updated task object.

**Response** `404 Not Found`: `{"detail": "Housekeeping task not found"}`

**Response** `422 Unprocessable Entity`: Validation errors.

### Delete Task

```
DELETE /api/v1/housekeeping/tasks/{task_id}
```

**Response** `200 OK`: `{"deleted": true}`

**Response** `404 Not Found`: `{"detail": "Housekeeping task not found"}`

### Enable/Disable Task

```
PATCH /api/v1/housekeeping/tasks/{task_id}/toggle
```

**Request Body**:
```json
{
  "enabled": false
}
```

**Response** `200 OK`: Updated task object with new `enabled` state.

---

## Trigger Execution

### Manual Run ("Run Now")

```
POST /api/v1/housekeeping/tasks/{task_id}/run
```

**Query Parameters**:
| Param | Type | Required | Description |
|-------|------|----------|-------------|
| force | boolean | No | Skip cooldown warning (default: false) |

**Response** `200 OK` (success):
```json
{
  "trigger_event": {
    "id": "event-uuid-1",
    "task_id": "task-uuid-1",
    "timestamp": "2026-02-28T12:00:00Z",
    "trigger_type": "manual",
    "issue_url": "https://github.com/owner/repo/issues/42",
    "issue_number": 42,
    "status": "success",
    "sub_issues_created": 5
  }
}
```

**Response** `409 Conflict` (cooldown active, `force` not set):
```json
{
  "detail": "Task was triggered recently",
  "last_triggered_at": "2026-02-28T11:57:00Z",
  "cooldown_remaining_seconds": 180,
  "message": "Use ?force=true to override cooldown"
}
```

**Response** `422 Unprocessable Entity` (invalid template or config):
```json
{
  "detail": "Cannot execute task: referenced template does not exist"
}
```

### Evaluate Time-Based Triggers (called by GitHub Actions cron)

```
POST /api/v1/housekeeping/evaluate-triggers
```

**Headers**: Requires a service token or webhook secret for authentication (not user session).

**Request Body**:
```json
{
  "trigger_source": "scheduled",
  "project_id": "PVT_abc123"
}
```

**Response** `200 OK`:
```json
{
  "evaluated": 5,
  "triggered": 2,
  "skipped": 3,
  "results": [
    {
      "task_id": "uuid-1",
      "task_name": "Weekly Security Review",
      "action": "triggered",
      "issue_url": "https://github.com/owner/repo/issues/43"
    },
    {
      "task_id": "uuid-2",
      "task_name": "Monthly Bug Bash",
      "action": "skipped",
      "reason": "Not yet due (next: 2026-03-01T00:00:00Z)"
    }
  ]
}
```

---

## Trigger History

### Get Task History

```
GET /api/v1/housekeeping/tasks/{task_id}/history
```

**Query Parameters**:
| Param | Type | Required | Description |
|-------|------|----------|-------------|
| limit | integer | No | Max results (default: 50, max: 200) |
| offset | integer | No | Pagination offset (default: 0) |
| status | string | No | Filter by `success` or `failure` |

**Response** `200 OK`:
```json
{
  "history": [
    {
      "id": "event-uuid-1",
      "task_id": "task-uuid-1",
      "timestamp": "2026-02-28T09:00:00Z",
      "trigger_type": "scheduled",
      "issue_url": "https://github.com/owner/repo/issues/42",
      "issue_number": 42,
      "status": "success",
      "error_details": null,
      "sub_issues_created": 5
    },
    {
      "id": "event-uuid-2",
      "task_id": "task-uuid-1",
      "timestamp": "2026-02-21T09:00:00Z",
      "trigger_type": "scheduled",
      "issue_url": null,
      "issue_number": null,
      "status": "failure",
      "error_details": "GitHub API rate limit exceeded",
      "sub_issues_created": 0
    }
  ],
  "total": 15,
  "limit": 50,
  "offset": 0
}
```

---

## Webhook Extension

### Issue Created Event (count-based trigger evaluation)

The existing webhook endpoint at `POST /api/v1/webhooks/github` is extended to handle `issues` events with action `opened`. When a new parent issue is created:

1. Verify webhook signature (existing HMAC-SHA256 validation)
2. Extract issue metadata (number, title, project association)
3. For each enabled count-based housekeeping task in the project:
   - Calculate: `current_issue_count - task.last_triggered_issue_count`
   - If `>= int(task.trigger_value)` AND outside cooldown → execute task
4. Return `200 OK` (webhook response must be fast; execution is async)

---

## Error Responses

All endpoints follow the existing FastAPI error response pattern:

| Status | Description |
|--------|-------------|
| 400 | Bad request (malformed input) |
| 401 | Unauthorized (no valid session) |
| 403 | Forbidden (e.g., modifying built-in template) |
| 404 | Resource not found |
| 409 | Conflict (cooldown, template in use) |
| 422 | Validation error (detailed field-level errors) |
| 500 | Internal server error |

## Rate Limiting

The `evaluate-triggers` endpoint should implement rate limiting (max 1 call per minute per project) to prevent abuse from misconfigured cron schedules.
