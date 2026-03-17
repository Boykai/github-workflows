# REST API Contracts: Solune v0.1.0 Public Release

**Branch**: `050-solune-v010-release` | **Date**: 2026-03-17 | **Plan**: [plan.md](../plan.md)

## Overview

This document defines the new and modified REST API endpoints required for the Solune v0.1.0 release. All endpoints follow the existing API convention: base path `/api/v1/`, JSON request/response bodies, FastAPI auto-generated OpenAPI schema. Authentication is via GitHub OAuth session cookies (HttpOnly, SameSite=Strict).

---

## New Endpoints

### Pipeline Runs

#### `POST /api/v1/pipelines/{pipeline_id}/runs`

**Purpose**: Create and start a new pipeline run (FR-001, FR-016).

**Request**:
```json
{
  "trigger": "manual"
}
```

**Response** (201 Created):
```json
{
  "id": 1,
  "pipeline_config_id": 42,
  "project_id": "PVT_abc123",
  "status": "pending",
  "started_at": "2026-03-17T15:00:00Z",
  "completed_at": null,
  "trigger": "manual",
  "stages": [
    {
      "id": 1,
      "stage_id": "build",
      "group_id": 1,
      "status": "pending",
      "label_name": null
    }
  ]
}
```

**Error Responses**:
- `403 Forbidden`: User not authorized for this project (FR-006)
- `404 Not Found`: Pipeline configuration not found
- `422 Unprocessable Entity`: Invalid request body

---

#### `GET /api/v1/pipelines/{pipeline_id}/runs`

**Purpose**: List all runs for a pipeline configuration (FR-003).

**Query Parameters**:
- `status` (optional): Filter by status (`pending`, `running`, `completed`, `failed`, `cancelled`)
- `limit` (optional, default 50): Maximum results per page
- `offset` (optional, default 0): Pagination offset

**Response** (200 OK):
```json
{
  "runs": [
    {
      "id": 1,
      "pipeline_config_id": 42,
      "status": "completed",
      "started_at": "2026-03-17T15:00:00Z",
      "completed_at": "2026-03-17T15:30:00Z",
      "trigger": "manual",
      "stage_summary": {
        "total": 5,
        "completed": 5,
        "failed": 0,
        "running": 0,
        "pending": 0
      }
    }
  ],
  "total": 150,
  "limit": 50,
  "offset": 0
}
```

**Notes**:
- No artificial cap on total results (FR-003)
- Returns summary counts, not full stage details (use detail endpoint for full state)

---

#### `GET /api/v1/pipelines/{pipeline_id}/runs/{run_id}`

**Purpose**: Get detailed state for a specific pipeline run including all stage states (FR-001, FR-002).

**Response** (200 OK):
```json
{
  "id": 1,
  "pipeline_config_id": 42,
  "project_id": "PVT_abc123",
  "status": "running",
  "started_at": "2026-03-17T15:00:00Z",
  "completed_at": null,
  "trigger": "manual",
  "groups": [
    {
      "id": 1,
      "name": "Build & Lint",
      "execution_mode": "parallel",
      "order_index": 0,
      "stages": [
        {
          "id": 1,
          "stage_id": "build",
          "status": "completed",
          "started_at": "2026-03-17T15:00:00Z",
          "completed_at": "2026-03-17T15:05:00Z",
          "agent_id": "agent-build-01",
          "label_name": "solune:pipeline:1:stage:build:completed"
        },
        {
          "id": 2,
          "stage_id": "lint",
          "status": "running",
          "started_at": "2026-03-17T15:00:00Z",
          "completed_at": null,
          "agent_id": "agent-lint-01",
          "label_name": "solune:pipeline:1:stage:lint:running"
        }
      ]
    },
    {
      "id": 2,
      "name": "Test",
      "execution_mode": "sequential",
      "order_index": 1,
      "stages": [
        {
          "id": 3,
          "stage_id": "test-unit",
          "status": "pending",
          "started_at": null,
          "completed_at": null,
          "agent_id": null,
          "label_name": null
        }
      ]
    }
  ]
}
```

---

#### `POST /api/v1/pipelines/{pipeline_id}/runs/{run_id}/cancel`

**Purpose**: Cancel a running or pending pipeline run.

**Response** (200 OK):
```json
{
  "id": 1,
  "status": "cancelled",
  "stages_skipped": 3
}
```

**Error Responses**:
- `403 Forbidden`: User not authorized
- `404 Not Found`: Run not found
- `409 Conflict`: Run already completed, failed, or cancelled

---

#### `POST /api/v1/pipelines/{pipeline_id}/runs/{run_id}/recover`

**Purpose**: Recover a failed run by rebuilding state from persistent storage and resuming (FR-002).

**Response** (200 OK):
```json
{
  "id": 1,
  "status": "running",
  "recovered_stages": 3,
  "resumed_from_stage": "test-unit"
}
```

**Error Responses**:
- `404 Not Found`: Run not found
- `409 Conflict`: Run is not in a recoverable state (must be 'failed')

---

### Stage Groups

#### `GET /api/v1/pipelines/{pipeline_id}/groups`

**Purpose**: List stage groups for a pipeline configuration (FR-016).

**Response** (200 OK):
```json
{
  "groups": [
    {
      "id": 1,
      "name": "Build & Lint",
      "execution_mode": "parallel",
      "order_index": 0,
      "stage_count": 2
    },
    {
      "id": 2,
      "name": "Test",
      "execution_mode": "sequential",
      "order_index": 1,
      "stage_count": 3
    }
  ]
}
```

---

#### `PUT /api/v1/pipelines/{pipeline_id}/groups`

**Purpose**: Create or update stage groups for a pipeline (FR-016, FR-017). Replaces all groups atomically.

**Request**:
```json
{
  "groups": [
    {
      "name": "Build & Lint",
      "execution_mode": "parallel",
      "order_index": 0,
      "stage_ids": ["build", "lint"]
    },
    {
      "name": "Test",
      "execution_mode": "sequential",
      "order_index": 1,
      "stage_ids": ["test-unit", "test-integration", "test-e2e"]
    }
  ]
}
```

**Response** (200 OK): Returns the created groups with IDs.

**Validation**:
- Each stage_id must exist in the pipeline configuration
- No stage_id may appear in multiple groups
- `order_index` values must be unique and sequential starting from 0
- `execution_mode` must be `sequential` or `parallel`

---

### Chat Attachments

#### `POST /api/v1/chat/{conversation_id}/attachments`

**Purpose**: Upload a file attachment and forward to the linked GitHub issue (FR-021).

**Request**: `multipart/form-data`
- `file`: The file to upload (max 25MB, matching GitHub's limit)
- `github_issue_number` (optional): Target GitHub issue number

**Response** (201 Created):
```json
{
  "id": "att_abc123",
  "filename": "screenshot.png",
  "size_bytes": 245760,
  "mime_type": "image/png",
  "github_url": "https://github.com/owner/repo/issues/42#issuecomment-123",
  "uploaded_at": "2026-03-17T15:00:00Z"
}
```

**Error Responses**:
- `413 Payload Too Large`: File exceeds 25MB
- `415 Unsupported Media Type`: File type not allowed
- `502 Bad Gateway`: GitHub upload failed (edge case #7 — message still sent, attachment error returned inline)

---

### Onboarding

#### `GET /api/v1/onboarding/state`

**Purpose**: Get the current user's onboarding tour state (FR-038).

**Response** (200 OK):
```json
{
  "current_step": 5,
  "completed": false,
  "dismissed_at": null,
  "total_steps": 9
}
```

---

#### `PUT /api/v1/onboarding/state`

**Purpose**: Update the onboarding tour state (advance, dismiss, or restart).

**Request**:
```json
{
  "action": "advance",
  "step": 6
}
```

**Valid actions**: `advance` (set step), `dismiss` (pause tour), `complete` (mark done), `restart` (reset to step 1)

**Response** (200 OK): Returns updated state.

---

### Issue Upload with Pipeline Config

#### `POST /api/v1/issues/create-with-pipeline`

**Purpose**: Create a GitHub issue from a pasted description with pipeline config association (FR-022).

**Request**:
```json
{
  "project_id": "PVT_abc123",
  "title": "Implement feature X",
  "body": "Full issue description...",
  "pipeline_config_id": 42,
  "labels": ["enhancement"]
}
```

**Response** (201 Created):
```json
{
  "issue_number": 123,
  "issue_url": "https://github.com/owner/repo/issues/123",
  "pipeline_config_id": 42,
  "pipeline_config_name": "Default Pipeline"
}
```

---

## Modified Endpoints

### `GET /api/v1/health` (Enhanced)

**Changes**: Add startup validation status to health response (FR-005, FR-048).

**Response** (200 OK):
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "startup_checks": {
    "encryption_key": "configured",
    "session_secret": "configured",
    "database": "connected",
    "github_oauth": "configured"
  }
}
```

**Response** (503 Service Unavailable) — when startup validation fails:
```json
{
  "status": "unhealthy",
  "version": "0.1.0",
  "startup_checks": {
    "encryption_key": "missing",
    "session_secret": "using_default",
    "database": "connected",
    "github_oauth": "configured"
  },
  "errors": [
    "ENCRYPTION_KEY is not configured",
    "SESSION_SECRET_KEY is using default value"
  ]
}
```

---

### `POST /api/v1/auth/github/callback` (Hardened)

**Changes**: Set HttpOnly and SameSite=Strict on the session cookie; harden CSRF cookie (FR-004).

**Cookie Headers** (added/modified):
```
Set-Cookie: session=<token>; HttpOnly; SameSite=Strict; Path=/; Max-Age=28800
Set-Cookie: csrf_token=<token>; SameSite=Lax; Path=/; Max-Age=28800
```

**Notes**:
- `Secure` flag added automatically when served over HTTPS
- `csrf_token` does NOT set HttpOnly (must be readable by JavaScript for CSRF protection)
- `csrf_token` keeps `SameSite=Lax` (not Strict) — SameSite=Strict would block the OAuth redirect callback flow. The current `CSRFMiddleware` (middleware/csrf.py) already uses Lax; this contract matches that behaviour

---

### `PUT /api/v1/projects/{project_id}/mcp-config` (Extended)

**Changes**: After saving MCP config, trigger propagation to all agent files (FR-019).

**Response** (200 OK):
```json
{
  "config": { "tools": ["*"] },
  "agents_updated": 3,
  "propagation_status": "success"
}
```

---

## Common Response Patterns

### Error Response Format

All error responses follow this structure:

```json
{
  "detail": "Human-readable error message",
  "error_code": "MACHINE_READABLE_CODE",
  "field_errors": [
    {
      "field": "name",
      "message": "Must not be empty"
    }
  ]
}
```

### Authentication Errors

- `401 Unauthorized`: Session expired or missing
- `403 Forbidden`: User authenticated but not authorized for this resource (FR-006)

### Rate Limiting (FR-026)

Rate-limited endpoints return:
- `429 Too Many Requests` with `Retry-After` header
- Applied to: `/api/v1/auth/*` endpoints, `/api/v1/pipelines/*/runs` (POST)

### Input Validation (FR-008)

All request bodies are validated via Pydantic models. Invalid input returns:
- `422 Unprocessable Entity` with `field_errors` array detailing each validation failure

---

## HTTP Security Headers (FR-025)

Applied globally via nginx configuration (frontend) and FastAPI middleware (backend API):

```
Content-Security-Policy: default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https://avatars.githubusercontent.com; connect-src 'self'
Strict-Transport-Security: max-age=31536000; includeSubDomains
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: camera=(), microphone=(self), geolocation=()
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
```

**Notes**:
- `microphone=(self)` allows voice input feature (FR-020)
- `img-src` includes GitHub avatar domain for user profile images
- `style-src 'unsafe-inline'` required for Tailwind CSS runtime styles
