# Security Contracts: Startup Validation

**Feature**: 001-security-review | **Date**: 2026-03-15

## Contract: Production Startup Gate

The application MUST validate all security-critical configuration at startup when running in production mode (`DEBUG=false`). Any validation failure MUST prevent the application from starting.

### Required Environment Variables

| Variable | Validation Rule | Error Message |
|----------|----------------|---------------|
| `ENCRYPTION_KEY` | Must be set; must be a valid Fernet key (base64-encoded 32 bytes) | `ENCRYPTION_KEY is required in production mode` / `ENCRYPTION_KEY is not a valid Fernet key` |
| `GITHUB_WEBHOOK_SECRET` | Must be set and non-empty | `GITHUB_WEBHOOK_SECRET is required in production mode` |
| `SESSION_SECRET_KEY` | Must be set; length ≥ 64 characters | `SESSION_SECRET_KEY must be at least 64 characters in production mode` |
| `COOKIE_SECURE` | Must be `true` | `Cookie Secure flag must be enabled in production mode` |
| `ADMIN_GITHUB_USER_ID` | Must be set and non-empty | `ADMIN_GITHUB_USER_ID is required in production mode` |

### CORS Origins Validation

Each entry in `CORS_ORIGINS` (comma-separated) MUST:
1. Parse as a valid URL via `urllib.parse.urlparse`
2. Have a non-empty `scheme` (http or https)
3. Have a non-empty `netloc` (hostname)

Invalid entries cause startup failure with a message identifying the malformed origin.

## Contract: Authentication Flow

### OAuth Callback Response

```
HTTP/1.1 302 Found
Location: {FRONTEND_URL}/
Set-Cookie: session={session_id}; HttpOnly; SameSite=Strict; Secure; Path=/; Max-Age=28800
```

**Constraints**:
- The `Location` URL MUST NOT contain any credentials, tokens, or session identifiers
- The session MUST be delivered exclusively via `Set-Cookie` header
- Cookie attributes MUST include `HttpOnly`, `SameSite=Strict`, and `Secure` (when `COOKIE_SECURE=true`)

### Dev Login (Development Only)

```
POST /api/v1/auth/dev/login
Content-Type: application/json

{
  "token": "<github_personal_access_token>"
}
```

**Constraints**:
- Credentials MUST be in the request body (JSON), never in URL parameters
- This endpoint MUST NOT exist when `DEBUG=false`

## Contract: Project Access Verification

### Authorization Check (FastAPI Dependency)

Every endpoint accepting a `project_id` parameter MUST use the `verify_project_access` dependency:

```python
@router.post("/projects/{project_id}/tasks")
async def create_task(
    project_id: str,
    session: Session = Depends(get_session_dep),
    _access: None = Depends(verify_project_access),
    # ... other params
):
```

**Behavior**:
- Returns `403 Forbidden` if the authenticated user does not own the project
- The 403 response MUST NOT reveal whether the project exists (prevent enumeration)
- Check runs BEFORE any business logic executes

### WebSocket Authorization

```
WS /api/v1/ws/{project_id}
Cookie: session={session_id}
```

**Behavior**:
- Connection MUST be rejected before any data frame is sent if the user does not own the project
- Rejection via WebSocket close code `4003` (Forbidden)

## Contract: Webhook Signature Verification

### GitHub Webhook

```
POST /api/v1/webhooks/github
X-Hub-Signature-256: sha256={hmac_hex_digest}
X-GitHub-Event: {event_type}
X-GitHub-Delivery: {delivery_id}
```

**Verification**:
1. Compute `HMAC-SHA256(GITHUB_WEBHOOK_SECRET, raw_body)`
2. Compare with `hmac.compare_digest` (constant-time)
3. Reject with `401 Unauthorized` on mismatch
4. Verification MUST NOT be conditional on `DEBUG` mode

### Signal Webhook

Same pattern: HMAC-SHA256 verification with `hmac.compare_digest`.

## Contract: Rate Limiting

### Per-User Endpoints

| Endpoint Pattern | Limit | Key Function |
|-----------------|-------|--------------|
| `POST /api/v1/chat/*/messages` | 10/minute | Session user ID |
| `POST /api/v1/agents/*` | 10/minute | Session user ID |
| `POST /api/v1/workflow/*` | 10/minute | Session user ID |

### Per-IP Endpoints

| Endpoint Pattern | Limit | Key Function |
|-----------------|-------|--------------|
| `GET /api/v1/auth/github/callback` | 20/minute | Client IP |

### Rate Limit Response

```
HTTP/1.1 429 Too Many Requests
Retry-After: {seconds_until_reset}
Content-Type: application/json

{
  "detail": "Rate limit exceeded. Try again in {seconds} seconds."
}
```

## Contract: HTTP Security Headers

All responses from the frontend nginx server MUST include:

| Header | Value |
|--------|-------|
| `Content-Security-Policy` | `default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' https://avatars.githubusercontent.com data:; connect-src 'self' ws: wss:; frame-ancestors 'none'` |
| `Strict-Transport-Security` | `max-age=31536000; includeSubDomains` |
| `Referrer-Policy` | `strict-origin-when-cross-origin` |
| `Permissions-Policy` | `camera=(), microphone=(), geolocation()` |
| `X-Frame-Options` | `SAMEORIGIN` |
| `X-Content-Type-Options` | `nosniff` |

**MUST NOT include**: `X-XSS-Protection` (deprecated), `Server` version disclosure.

## Contract: File Permissions

| Resource | Permission | Owner |
|----------|-----------|-------|
| `/var/lib/solune/data/` (directory) | `0700` | `appuser` |
| `/var/lib/solune/data/settings.db` (file) | `0600` | `appuser` |
| Container process (backend) | Non-root (`appuser`) | — |
| Container process (frontend) | Non-root (`nginx-app`) | — |
