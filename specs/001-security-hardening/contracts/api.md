# API Contracts: Phase 4 — Security Hardening

**Feature**: `001-security-hardening`  
**Date**: 2026-03-21  
**Format**: REST (FastAPI / OpenAPI style)

## Existing Endpoints Modified

### POST /api/v1/auth/logout

**Change**: Now explicitly revokes the session (sets `revoked_at`) instead of just deleting the cookie.

**Request**: No body required. Session identified by `solune_session` cookie.

**Response** (unchanged):
```json
{
  "message": "Logged out successfully"
}
```

**Behavior change**: Session row is updated with `revoked_at = now()` instead of being deleted. Future requests with the same session ID receive 401.

---

### GET /api/v1/auth/github/callback

**Change**: Validates OAuth scopes after token exchange. Returns error if required scopes are missing.

**Success Response** (unchanged): 302 redirect to `{frontend_url}/auth/callback`

**New Error Response** (scope validation failure):
```
HTTP 302 → {frontend_url}/auth/callback?error=insufficient_scopes&missing=repo,project
```

**Query parameters on error redirect**:
- `error`: `"insufficient_scopes"`
- `missing`: Comma-separated list of missing scope names

---

### POST /api/v1/webhooks/github

**Change**: Delivery ID deduplication uses TTL-based cache (60-minute window) instead of LRU-only.

**New behavior for duplicate delivery**:
```json
HTTP 200
{
  "status": "skipped",
  "reason": "duplicate delivery",
  "delivery_id": "<id>"
}
```

**New behavior for missing delivery ID**:
- Process normally (no deduplication possible)
- Log warning: `"Webhook received without X-GitHub-Delivery header"`

---

## New Endpoints

### POST /api/v1/auth/sessions/revoke

**Purpose**: Revoke a specific session (user self-service).

**Authentication**: Requires valid `solune_session` cookie.

**Request Body**:
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Validation**:
- `session_id` must be a valid UUID
- User can only revoke their own sessions (matched by `github_user_id`)

**Success Response**:
```json
HTTP 200
{
  "message": "Session revoked",
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "revoked_at": "2026-03-21T23:00:00Z"
}
```

**Error Responses**:
- `401 Unauthorized` — No valid session cookie
- `404 Not Found` — Session ID not found or belongs to another user
- `409 Conflict` — Session already revoked

---

### POST /api/v1/auth/sessions/revoke-all

**Purpose**: Revoke all sessions for the current user.

**Authentication**: Requires valid `solune_session` cookie.

**Request Body**: None.

**Success Response**:
```json
HTTP 200
{
  "message": "All sessions revoked",
  "revoked_count": 3
}
```

**Behavior**: Revokes ALL sessions for the authenticated user's `github_user_id`, including the current session. The response is sent before the current session becomes invalid.

**Error Responses**:
- `401 Unauthorized` — No valid session cookie

---

### GET /api/v1/auth/sessions

**Purpose**: List active sessions for the current user.

**Authentication**: Requires valid `solune_session` cookie.

**Success Response**:
```json
HTTP 200
{
  "sessions": [
    {
      "session_id": "550e8400-e29b-41d4-a716-446655440000",
      "created_at": "2026-03-21T10:00:00Z",
      "updated_at": "2026-03-21T22:00:00Z",
      "is_current": true
    },
    {
      "session_id": "660e8400-e29b-41d4-a716-446655440001",
      "created_at": "2026-03-20T08:00:00Z",
      "updated_at": "2026-03-20T16:00:00Z",
      "is_current": false
    }
  ]
}
```

**Note**: Excludes revoked sessions. Does not expose tokens or sensitive data.

---

## Cookie Changes

### Session Cookie (`solune_session`)

| Attribute | Before | After |
|-----------|--------|-------|
| `SameSite` | `Strict` | `Strict` (unchanged) |
| `HttpOnly` | `true` | `true` (unchanged) |
| `Secure` | Conditional | Conditional (unchanged) |

### CSRF Cookie (`csrf_token`)

| Attribute | Before | After |
|-----------|--------|-------|
| `SameSite` | `Lax` | **`Strict`** |
| `HttpOnly` | `false` | `false` (unchanged — JS must read it) |
| `Secure` | Conditional | Conditional (unchanged) |

---

## Error Schemas

### Insufficient Scopes Error (Frontend Query Params)

Delivered as query parameters on the redirect URL (not a JSON API response, since this is part of the OAuth redirect flow):

```
/auth/callback?error=insufficient_scopes&missing=repo,project
```

The frontend reads these parameters and displays a user-friendly message:
- "Your GitHub authorization is missing required permissions: **repo**, **project**"
- "Please re-authorize the application with the required permissions."
- Action button: "Re-authorize" → triggers new OAuth flow

### Revoked Session Error

```json
HTTP 401
{
  "detail": "Session has been revoked"
}
```

Returned when a request is made using a session ID that has a non-NULL `revoked_at` value.
