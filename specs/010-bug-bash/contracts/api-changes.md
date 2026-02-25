# API Contracts: Bug Bash — Modified Endpoints

**Date**: 2026-02-24 | **Branch**: `010-bug-bash`

This document covers only **changed** API behaviors. Endpoints not listed here remain unchanged.

---

## Authentication (FR-001, FR-002)

### `GET /api/v1/auth/github/callback`

**Change**: Session token delivery mechanism.

**Before**:
```
HTTP/1.1 302 Found
Location: {frontend_url}?session_token={session_id}
```

**After**:
```
HTTP/1.1 302 Found
Location: {frontend_url}/auth/callback
Set-Cookie: session_id={session_id}; HttpOnly; Secure; SameSite=Lax; Path=/; Max-Age=28800
```

The session token is now delivered via a secure HTTP-only cookie instead of a URL query parameter. The frontend reads it from the cookie jar automatically on subsequent API requests.

---

### `POST /api/v1/auth/dev-login`

**Change**: Gated behind `debug` mode.

**Before**: Always available.

**After**:
- `debug=True`: Available (unchanged behavior).
- `debug=False`: Returns `404 Not Found`.

```json
// Response when debug=False:
{
  "detail": "Not Found"
}
```

---

## Health (FR-020)

### `GET /api/v1/health`

**Change**: Structured health check replacing static response.

**Before**:
```json
// HTTP 200 (always)
{
  "status": "ok"
}
```

**After**:
```json
// HTTP 200 (all checks pass)
{
  "status": "pass",
  "checks": {
    "database": [{"status": "pass", "time": "3ms"}],
    "github_api": [{"status": "pass", "time": "87ms"}],
    "polling_loop": [{"status": "pass", "observed_value": "running"}]
  }
}

// HTTP 503 (one or more checks fail)
{
  "status": "fail",
  "checks": {
    "database": [{"status": "fail", "output": "database is locked"}],
    "github_api": [{"status": "pass", "time": "92ms"}],
    "polling_loop": [{"status": "pass", "observed_value": "running"}]
  }
}
```

**Status codes**: `200` for `pass`/`warn`, `503` for `fail`.

---

## Error Responses (FR-009)

### All endpoints returning `429 Too Many Requests`

**Change**: Add `Retry-After` header.

**Before**:
```
HTTP/1.1 429 Too Many Requests
Content-Type: application/json

{"detail": "Rate limit exceeded"}
```

**After**:
```
HTTP/1.1 429 Too Many Requests
Retry-After: 60
Content-Type: application/json

{"error": "Rate limit exceeded", "details": {}}
```

The `Retry-After` header value comes from the upstream GitHub API's `retry-after` or `x-ratelimit-reset` header, converted to seconds.

---

## All Responses (FR-024)

### Request-ID Header

**Change**: All responses include `X-Request-ID`.

```
HTTP/1.1 200 OK
X-Request-ID: a1b2c3d4e5f6...

{...response body...}
```

- If the incoming request includes `X-Request-ID`, it is propagated.
- If absent, a new UUID4 hex string is generated.

---

## Tasks (FR-010)

### `PUT /api/v1/tasks/{task_id}/status`

**Change**: Stub endpoint now returns 501.

**Before**:
```json
// HTTP 200 (always, regardless of whether GitHub was updated)
{
  "status": "ok"
}
```

**After**:
```json
// HTTP 501 Not Implemented
{
  "error": "Not implemented",
  "details": {"message": "Task status update via GitHub Projects API is not yet implemented"}
}
```

---

## Settings (FR-005)

### `PUT /api/v1/settings/global`

**Change**: Requires session-owner authorization.

**Before**: Any authenticated user can modify.

**After**:
- Session owner (admin): 200 OK (unchanged response body).
- Non-admin authenticated user: 403 Forbidden.

```json
// HTTP 403 (non-admin)
{
  "error": "Access denied",
  "details": {"message": "Only the session owner can modify settings"}
}
```

---

## Webhooks (FR-004)

### `POST /api/v1/webhooks/github`

**Change**: Mandatory signature verification in production.

**Before**: May process unsigned payloads when `github_webhook_secret` is unset.

**After**:
- `github_webhook_secret` set: Verify `X-Hub-Signature-256` header. Reject with 401 if invalid/missing.
- `github_webhook_secret` unset + `debug=True`: Log warning, allow (development).
- `github_webhook_secret` unset + `debug=False`: Reject with 401.

```json
// HTTP 401 (invalid/missing signature)
{
  "error": "Authentication required",
  "details": {"message": "Invalid or missing webhook signature"}
}
```
