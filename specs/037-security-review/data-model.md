# Data Model: Security, Privacy & Vulnerability Audit

**Feature**: 037-security-review | **Date**: 2026-03-12

## Entities

### Session

Represents an authenticated user's login state. Delivered via a secure cookie instead of a URL parameter.

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| `session_token` | `str` | Opaque session identifier | Generated via `secrets.token_urlsafe(32)` |
| `user_id` | `int` | GitHub user ID | Required, from OAuth exchange |
| `username` | `str` | GitHub login name | Required, from OAuth exchange |
| `access_token` | `str` | Encrypted GitHub OAuth token | Encrypted at rest via `encryption.py` |
| `created_at` | `datetime` | Session creation timestamp | Set on creation |
| `expires_at` | `datetime` | Session expiry timestamp | Set on creation, enforced on read |

**Cookie attributes** (not stored in DB, set on HTTP response):
- `HttpOnly`: `True` — prevents JavaScript access
- `SameSite`: `Strict` — prevents CSRF
- `Secure`: `True` — HTTPS only (enforced at startup in non-debug mode)
- `Path`: `/` — available to all routes
- `Max-Age`: Session lifetime (configurable)

**State transitions**:
- `created` → `active`: Cookie set on OAuth callback response
- `active` → `expired`: Session TTL exceeded
- `active` → `invalidated`: User logs out (cookie cleared, DB row deleted)

### ProjectAccess

Represents the ownership relationship between a user and a project. Used by the centralized ownership check.

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| `project_id` | `str` | Project identifier | Required, from request path/body |
| `owner_id` | `int` | GitHub user ID of the project owner | Required, from projects table |

**Access check logic**:
```text
Given: session.user_id, request.project_id
Query: SELECT owner_id FROM projects WHERE id = project_id
Result: ALLOW if session.user_id == owner_id, else 403 Forbidden
```

### RateLimitState

Represents per-user or per-IP rate limiting counters managed by slowapi.

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| `key` | `str` | Rate limit key (user ID or IP address) | Format: `user:{user_id}` or `ip:{ip_address}` |
| `endpoint` | `str` | Rate-limited endpoint path | One of the configured endpoints |
| `window_start` | `datetime` | Current rate limit window start | Set on first request in window |
| `request_count` | `int` | Number of requests in current window | Incremented per request |
| `limit` | `int` | Maximum requests per window | From configuration |
| `window_seconds` | `int` | Window duration in seconds | From configuration |

**Rate limit configuration** (environment-configurable):

| Endpoint Category | Key Type | Default Limit | Window |
|-------------------|----------|---------------|--------|
| Chat / AI endpoints | `user:{id}` | 30 req | 60s |
| Workflow triggers | `user:{id}` | 10 req | 60s |
| Agent invocations | `user:{id}` | 20 req | 60s |
| OAuth callback | `ip:{addr}` | 10 req | 300s |

### ChatMessageReference

Represents a lightweight reference stored in browser localStorage (replacing full message content).

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| `message_id` | `str` | Unique message identifier | Required |
| `project_id` | `str` | Associated project | Required |
| `timestamp` | `number` | Message creation time (epoch ms) | Required |
| `ttl` | `number` | Time-to-live in milliseconds | Default: 7 days |

**State transitions**:
- `stored` → `expired`: Current time exceeds `timestamp + ttl`
- `stored` → `cleared`: User logs out (all references deleted)
- `expired` → `pruned`: Expired references removed on next read

### StartupValidation

Represents the mandatory configuration checks performed at application startup.

| Check | Environment Variable | Condition | Mode |
|-------|---------------------|-----------|------|
| Encryption key present | `ENCRYPTION_KEY` | Must be non-empty | Non-debug only |
| Webhook secret present | `GITHUB_WEBHOOK_SECRET` | Must be non-empty | Non-debug only |
| Session key entropy | `SESSION_SECRET_KEY` | Must be ≥ 64 characters | All modes |
| Cookie secure flag | `COOKIE_SECURE` | Must be `True` | Non-debug only |
| CORS origins valid | `CORS_ORIGINS` | Each origin is a well-formed URL | All modes |

**Failure behavior**: `SystemExit` with descriptive error message including the check name and expected condition.

## Relationships

```text
Session ──authenticates──▶ User
Session ──cookie-delivery──▶ OAuth Callback Response
ProjectAccess ──verifies──▶ Session.user_id against Project.owner_id
RateLimitState ──throttles──▶ API Endpoint (keyed by Session.user_id or client IP)
ChatMessageReference ──references──▶ Backend Chat Message (loaded on demand)
StartupValidation ──gates──▶ Application Startup
```

## Security Boundaries

```text
┌─────────────────────────────────────────────────────────────────┐
│  Browser (Frontend)                                              │
│  ┌──────────────────┐  ┌──────────────────────────────────────┐ │
│  │ localStorage     │  │ Cookie Jar                           │ │
│  │ • Message IDs    │  │ • session_token (HttpOnly, Secure,   │ │
│  │ • TTL metadata   │  │   SameSite=Strict)                   │ │
│  │ • NO full content│  │ • NOT accessible to JavaScript       │ │
│  └──────────────────┘  └──────────────────────────────────────┘ │
└─────────────────────────┬───────────────────────────────────────┘
                          │ HTTPS only
┌─────────────────────────▼───────────────────────────────────────┐
│  nginx (Reverse Proxy)                                           │
│  • Security headers (CSP, HSTS, Referrer-Policy, Permissions)    │
│  • server_tokens off                                             │
│  • No X-XSS-Protection                                           │
│  • Bound to 127.0.0.1 in dev                                    │
└─────────────────────────┬───────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────┐
│  FastAPI Backend                                                 │
│  ┌───────────────────┐  ┌─────────────────────────────────────┐ │
│  │ Rate Limiter      │  │ Auth Middleware                     │ │
│  │ • Per-user limits │  │ • Cookie session validation         │ │
│  │ • Per-IP (OAuth)  │  │ • Project ownership check           │ │
│  └───────────────────┘  └─────────────────────────────────────┘ │
│  ┌───────────────────┐  ┌─────────────────────────────────────┐ │
│  │ Webhook Handler   │  │ Config Validator                    │ │
│  │ • Always verified │  │ • Mandatory secrets                 │ │
│  │ • Constant-time   │  │ • Key entropy                      │ │
│  │ • No debug bypass │  │ • CORS validation                  │ │
│  └───────────────────┘  └─────────────────────────────────────┘ │
└─────────────────────────┬───────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────┐
│  SQLite Database                                                 │
│  • Directory: 0700 permissions                                   │
│  • Files: 0600 permissions                                       │
│  • OAuth tokens: encrypted at rest (mandatory ENCRYPTION_KEY)    │
│  • Volume: /var/lib/ghchat/data (outside app root)               │
└─────────────────────────────────────────────────────────────────┘
```
