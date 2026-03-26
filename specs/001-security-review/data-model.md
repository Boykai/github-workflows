# Data Model: Security, Privacy & Vulnerability Audit

**Feature**: 001-security-review | **Date**: 2026-03-26

## Overview

This document describes the security-relevant entities, their relationships, validation rules, and state transitions. The security audit is primarily a hardening exercise on existing entities — no new tables or major schema changes are introduced.

---

## Entities

### 1. Session

**Purpose**: Represents an authenticated user session after OAuth login.

| Field | Type | Constraints | Security Notes |
|-------|------|-------------|----------------|
| `session_id` | `str` (UUID) | Primary key, generated server-side | Never exposed in URLs |
| `github_user_id` | `int` | Foreign key to GitHub user | Used for rate-limit keying |
| `github_username` | `str` | Not null | Display only |
| `access_token` | `str` (encrypted) | Fernet-encrypted at rest | Mandatory encryption in production |
| `refresh_token` | `str` (encrypted, nullable) | Fernet-encrypted at rest | Nullable for PAT-based sessions |
| `token_expires_at` | `datetime` | UTC timezone-aware | Auto-refresh 5 min before expiry |
| `created_at` | `datetime` | UTC timezone-aware, auto-set | — |
| `expires_at` | `datetime` | UTC, `created_at + session_expire_hours` | Default 8 hours |

**Validation Rules**:
- `access_token` MUST be Fernet-encrypted when `encryption_key` is set (enforced in production)
- `session_id` is stored in an `HttpOnly; SameSite=Strict; Secure` cookie — never in URL parameters
- Session expiration checked on every authenticated request

**State Transitions**:
```
[Created] → (OAuth callback sets cookie) → [Active]
[Active] → (token near expiry) → [Refreshing] → [Active]
[Active] → (session_expire_hours elapsed) → [Expired] → (auto-cleanup)
[Active] → (user logout) → [Destroyed] → (cookie cleared, session deleted)
[Refreshing] → (refresh fails) → [Expired] → (user must re-authenticate)
```

---

### 2. Project

**Purpose**: Represents a user's GitHub project. Access control boundary for all project-scoped operations.

| Field | Type | Constraints | Security Notes |
|-------|------|-------------|----------------|
| `project_id` | `str` | GitHub Project V2 global node ID | Used as access control boundary |
| `owner_login` | `str` | GitHub username of project owner | Verified via GitHub API |
| `title` | `str` | Not null | — |

**Validation Rules**:
- Every endpoint accepting `project_id` MUST call `verify_project_access()` before any action
- Access verification queries GitHub API for user's project list (authoritative source)
- No local caching of ownership — always verified against GitHub API

**Access Control Matrix**:
| Operation | Auth Required | Ownership Check | Endpoint |
|-----------|--------------|-----------------|----------|
| Create task | ✅ | ✅ `verify_project_access` | `tasks.py` |
| WebSocket subscribe | ✅ | ✅ `verify_project_access` | `workflow.py` |
| Update settings | ✅ | ✅ `verify_project_access` | `settings.py` |
| Trigger workflow | ✅ | ✅ `verify_project_access` | `workflow.py` |
| List own projects | ✅ | N/A (returns only user's projects) | `projects.py` |

---

### 3. Configuration (Startup-Validated)

**Purpose**: Environment-based configuration validated at application startup.

| Variable | Type | Required In Production | Validation |
|----------|------|----------------------|------------|
| `ENCRYPTION_KEY` | `str` | ✅ Mandatory | Valid Fernet key |
| `GITHUB_WEBHOOK_SECRET` | `str` | ✅ Mandatory | Non-empty |
| `SESSION_SECRET_KEY` | `str` | ✅ Always | Length ≥ 64 characters |
| `COOKIE_SECURE` | `bool` | ✅ Mandatory (or HTTPS frontend_url) | `true` in production |
| `ADMIN_GITHUB_USER_ID` | `int` | ✅ Mandatory | > 0 |
| `CORS_ORIGINS` | `str` | Optional | Each origin: valid URL with scheme + hostname |
| `ENABLE_DOCS` | `bool` | Optional | Default `false` |
| `DEBUG` | `bool` | Optional | Default `false`; does NOT bypass security |
| `DATABASE_PATH` | `str` | ✅ In production | Absolute path |

**Validation State Machine**:
```
[Startup] → (load env vars) → [Parsing]
[Parsing] → (non-debug mode) → [Production Validation]
  → (missing ENCRYPTION_KEY) → [FATAL: Refuse to start]
  → (missing GITHUB_WEBHOOK_SECRET) → [FATAL: Refuse to start]
  → (SESSION_SECRET_KEY < 64 chars) → [FATAL: Refuse to start]
  → (COOKIE_SECURE not true AND frontend_url not HTTPS) → [FATAL: Refuse to start]
  → (malformed CORS origin) → [FATAL: Refuse to start]
  → (all valid) → [Running]
[Parsing] → (debug mode) → [Debug Validation]
  → (SESSION_SECRET_KEY < 64 chars) → [Running with warnings]
  → (warnings for missing optional values) → [Running with warnings]
```

---

### 4. Rate Limit Record (In-Memory)

**Purpose**: Tracks request counts per user/IP per time window for rate limiting.

| Field | Type | Constraints | Security Notes |
|-------|------|-------------|----------------|
| `key` | `str` | `user:{github_user_id}`, `user:{session_id}`, or `ip:{address}` | Priority: user ID > session > IP |
| `endpoint_pattern` | `str` | Route pattern (e.g., `/api/v1/chat/send`) | — |
| `request_count` | `int` | Incremented per request | — |
| `window_start` | `datetime` | UTC | Sliding window |
| `window_duration` | `timedelta` | Per-endpoint configured | Default: 1 minute |
| `limit` | `int` | Per-endpoint configured | e.g., 10/minute for chat |

**Key Resolution Priority**:
1. `github_user_id` from `RateLimitKeyMiddleware` (most reliable, survives cookie clearing)
2. Session cookie value (fallback for pre-resolution requests)
3. Remote IP address (for unauthenticated requests like OAuth callback)

---

### 5. Webhook Verification

**Purpose**: Validates incoming webhook payloads using cryptographic signatures.

| Webhook Source | Verification Method | Comparison Function | Bypass Possible |
|---------------|---------------------|---------------------|-----------------|
| GitHub | HMAC-SHA256 signature (`X-Hub-Signature-256`) | `hmac.compare_digest` | ❌ Never |
| Signal | Shared secret header (`X-Signal-Webhook-Secret`) | `hmac.compare_digest` | ❌ Never |

**Verification Rules**:
- Webhook verification MUST NOT branch on `DEBUG` flag
- Missing webhook secret → request rejected (not bypassed)
- All comparisons use constant-time functions

---

### 6. Security Headers (Nginx)

**Purpose**: HTTP response headers served by the nginx reverse proxy.

| Header | Value | Purpose |
|--------|-------|---------|
| `Content-Security-Policy` | `default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' https://avatars.githubusercontent.com data:; connect-src 'self' ws: wss:; frame-ancestors 'none'` | XSS and injection mitigation |
| `Strict-Transport-Security` | `max-age=31536000; includeSubDomains` | HTTPS enforcement |
| `Referrer-Policy` | `strict-origin-when-cross-origin` | Referrer leakage prevention |
| `Permissions-Policy` | `camera=(), microphone=(), geolocation=()` | API access restriction |
| `X-Content-Type-Options` | `nosniff` | MIME sniffing prevention |
| `X-Frame-Options` | `SAMEORIGIN` | Clickjacking prevention |
| `X-XSS-Protection` | *(not set — deprecated)* | Removed per best practice |
| `Server` | *(hidden via `server_tokens off`)* | Version disclosure prevention |

---

## Relationships

```
Session ──owns──▶ Project (verified via GitHub API, not local FK)
Session ──has──▶ Rate Limit Records (keyed by github_user_id)
Configuration ──validates at startup──▶ Session (encryption, cookie security)
Configuration ──validates at startup──▶ Webhook Verification (secret presence)
Configuration ──validates at startup──▶ CORS (origin format)
```

## Encryption Scope

| Data | At Rest | In Transit | Notes |
|------|---------|------------|-------|
| OAuth access tokens | Fernet-encrypted (SQLite) | HTTPS | Mandatory in production |
| OAuth refresh tokens | Fernet-encrypted (SQLite) | HTTPS | Mandatory in production |
| Session IDs | Plaintext (SQLite) | HttpOnly Secure cookie | Short-lived (8h default) |
| Chat messages | In-memory only | HTTPS/WSS | Never persisted to storage |
| Webhook secrets | Environment variable | N/A | Never logged or stored |
