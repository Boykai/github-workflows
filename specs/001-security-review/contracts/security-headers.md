# Security Contracts: Security, Privacy & Vulnerability Audit

**Feature**: 001-security-review | **Date**: 2026-03-26

## Overview

This document defines the security contracts that all API endpoints and infrastructure components must satisfy. These are behavioral contracts verified by inspection, not OpenAPI schema changes — the security audit hardens existing endpoints rather than introducing new ones.

---

## Contract 1: Authentication Cookie Contract

**Applies to**: OAuth callback (`/api/v1/auth/github/callback`), all authenticated endpoints

### Response Cookie Requirements

```
Set-Cookie: session_id=<UUID>;
  HttpOnly;
  SameSite=Strict;
  Secure;              # Mandatory in production
  Max-Age=28800;       # 8 hours default
  Path=/
```

### Prohibited Patterns

- ❌ `?session_token=...` in any redirect URL
- ❌ `?access_token=...` in any redirect URL
- ❌ Any credential in URL query parameters or fragments
- ❌ Frontend JavaScript reading credentials from `window.location.search`

### Verification

```bash
# After OAuth login, inspect browser URL — must contain no credentials
# Inspect Set-Cookie header on the callback response. Reproducing this
# accurately usually requires a real OAuth callback or captured response.
curl -v GET /api/v1/auth/github/callback 2>&1 | grep -i "set-cookie"
# Expected: HttpOnly; SameSite=Strict; Secure (in production)
```

---

## Contract 2: Startup Validation Contract

**Applies to**: Application startup in non-debug mode

### Required Environment Variables

| Variable | Validation | Failure Behavior |
|----------|-----------|-----------------|
| `ENCRYPTION_KEY` | Non-empty, valid Fernet key | Refuse to start |
| `GITHUB_WEBHOOK_SECRET` | Non-empty | Refuse to start |
| `SESSION_SECRET_KEY` | Length ≥ 64 characters | Fatal in prod; warn in debug |
| `COOKIE_SECURE` | `true` (or HTTPS `frontend_url`) | Refuse to start |
| `ADMIN_GITHUB_USER_ID` | Integer > 0 | Refuse to start |

### Verification

```bash
# Start without ENCRYPTION_KEY in non-debug mode
ENCRYPTION_KEY="" DEBUG=false python -m src.main
# Expected: Exit with error "ENCRYPTION_KEY must be set in production"

# Start with short SESSION_SECRET_KEY in non-debug mode
SESSION_SECRET_KEY="too-short" DEBUG=false python -m src.main
# Expected: Exit with error "SESSION_SECRET_KEY must be at least 64 characters"
```

---

## Contract 3: Project Access Control Contract

**Applies to**: All endpoints accepting `project_id`

### Authorization Flow

```
Request with project_id
  → Extract session from cookie
  → Call verify_project_access(request, project_id, session)
    → Query GitHub API for user's projects
    → If project_id in user's projects → Allow
    → If project_id NOT in user's projects → 403 Forbidden
    → If GitHub API fails → 403 (fail closed)
```

### Protected Endpoints

| Endpoint | Method | Project ID Source |
|----------|--------|-------------------|
| `/api/v1/tasks` | POST | Request body |
| `/api/v1/projects/{project_id}/settings` | GET/PUT | URL path |
| `/api/v1/workflow/*` | Various | Request body/path |
| WebSocket `/ws/{project_id}` | CONNECT | URL path |

### Error Response

```json
{
  "detail": "You do not have access to this project"
}
```
**HTTP Status**: 403 Forbidden

---

## Contract 4: Rate Limiting Contract

**Applies to**: Expensive and sensitive endpoints

### Limits

| Endpoint Category | Limit | Key Type |
|-------------------|-------|----------|
| Chat / AI (`send_message`) | 10/minute | Per-user (GitHub user ID) |
| Agent invocation | Per-endpoint configured | Per-user |
| Workflow operations | Per-endpoint configured | Per-user |
| OAuth callback | Per-endpoint configured | Per-IP |

### Key Resolution Priority

1. `github_user_id` (from session middleware)
2. `session_id` (from cookie)
3. Remote IP address (for unauthenticated requests)

### Error Response

```json
{
  "detail": "Rate limit exceeded. Retry after {retry_after} seconds."
}
```
**HTTP Status**: 429 Too Many Requests
**Headers**: `Retry-After: {seconds}`

---

## Contract 5: Webhook Verification Contract

**Applies to**: GitHub webhooks (`/api/v1/webhooks/github`), Signal webhooks (`/api/v1/signal/webhook/inbound`)

### Requirements

- Signature verification MUST be performed on every request
- Verification MUST NOT be conditional on `DEBUG` flag
- All secret comparisons MUST use constant-time functions (`hmac.compare_digest`)
- Missing webhook secret configuration → request rejected (503 or 401)

### GitHub Webhook Verification

```
X-Hub-Signature-256: sha256=<hex_digest>
  → Compute HMAC-SHA256(secret, body)
  → hmac.compare_digest(expected, received)
  → If mismatch → 401 "Invalid or missing webhook signature"
```

### Signal Webhook Verification

```
X-Signal-Webhook-Secret: <secret>
  → hmac.compare_digest(header_value, configured_secret)
  → If mismatch → 403 "Invalid webhook secret"
  → If not configured → 503 "Signal webhook not configured"
```

---

## Contract 6: Security Headers Contract

**Applies to**: All HTTP responses from nginx frontend

### Required Headers

| Header | Value | Enforcement |
|--------|-------|-------------|
| `Content-Security-Policy` | Restrictive policy (see data-model.md) | `always` directive |
| `Strict-Transport-Security` | `max-age=31536000; includeSubDomains` | `always` directive |
| `Referrer-Policy` | `strict-origin-when-cross-origin` | `always` directive |
| `Permissions-Policy` | `camera=(), microphone=(), geolocation=()` | `always` directive |
| `X-Content-Type-Options` | `nosniff` | `always` directive |
| `X-Frame-Options` | `SAMEORIGIN` | `always` directive |

### Prohibited Headers

- ❌ `X-XSS-Protection` (deprecated)
- ❌ `Server: nginx/x.x.x` (version disclosure)

### Verification

```bash
curl -sI https://app.example.com | grep -iE "(content-security|strict-transport|referrer-policy|permissions-policy|x-content-type|x-frame|x-xss|server)"
# Expected: All required headers present, no X-XSS-Protection, no nginx version
```

---

## Contract 7: Data Privacy Contract

**Applies to**: Frontend chat history storage

### Requirements

- Chat message content MUST be stored in memory (React state) only
- localStorage MUST NOT contain message content
- On logout, all application data MUST be cleared from localStorage
- Legacy localStorage data from previous versions MUST be cleaned up

### Verification

```javascript
// After chat usage:
Object.keys(localStorage).filter(k => k.startsWith('solune'))
// Expected: Empty or lightweight references only (no message content)

// After logout:
Object.keys(localStorage).filter(k => k.startsWith('solune'))
// Expected: Empty
```

---

## Contract 8: Container Security Contract

**Applies to**: All Docker containers

### Requirements

| Container | User | UID | Port |
|-----------|------|-----|------|
| Backend | `appuser` (or similar) | Non-zero | Internal |
| Frontend | `nginx-app` | Non-zero | 8080 (non-privileged) |

### Filesystem Permissions

| Path | Permission | Owner |
|------|-----------|-------|
| Database directory | `0700` | Application user |
| Database file | `0600` | Application user |
| Application directory | Read-only (except data volume) | Application user |

### Network Binding

| Environment | Binding | Exposure |
|-------------|---------|----------|
| Development | `127.0.0.1` only | Localhost |
| Production | Internal only | Via reverse proxy |

### Verification

```bash
docker exec <frontend> id
# Expected: uid=<non-zero>(nginx-app)

docker exec <backend> stat -c '%a' /var/lib/solune/data
# Expected: 700

docker exec <backend> stat -c '%a' /var/lib/solune/data/*.db
# Expected: 600
```
