# Data Model: Security, Privacy & Vulnerability Audit

**Feature**: 001-security-review | **Date**: 2026-03-15

## Overview

This security audit is primarily a hardening exercise — it modifies existing behavior and configuration rather than introducing new entities. The data model documents the security-relevant entities, their security attributes, and the validation/state transitions that the audit affects.

## Entities

### Session

Represents an authenticated user's active session.

| Field | Type | Constraints | Security Notes |
|-------|------|-------------|----------------|
| session_id | string (UUID) | Primary key, auto-generated | Never exposed in URLs |
| user_id | integer | FK → GitHub user ID | Ties session to identity |
| github_token | string (encrypted) | Fernet-encrypted at rest | Encrypted via `ENCRYPTION_KEY` |
| created_at | datetime (UTC) | Auto-set on creation | Used for expiration calc |
| expires_at | datetime (UTC) | created_at + 8 hours | Hard expiration enforced |

**Delivery mechanism**: `Set-Cookie` header with `HttpOnly; SameSite=Strict; Secure; Path=/; Max-Age=28800`.

**State transitions**:
```
[No Session] → OAuth callback → [Active Session] → 8hr expiry or logout → [Expired/Deleted]
                                 [Active Session] → token refresh (within 5min buffer) → [Active Session]
```

### Project Access Grant

Represents the ownership/access relationship between a user and a project.

| Field | Type | Constraints | Security Notes |
|-------|------|-------------|----------------|
| project_id | string | FK → project | Verified on every request |
| user_id | integer | FK → session user | Must match session identity |
| role | string | owner (currently single-role) | Extensible for future RBAC |

**Access verification**: Implemented as `verify_project_access` FastAPI dependency — runs before any endpoint logic executes.

### Encryption Key Configuration

Server-side secret for at-rest encryption.

| Field | Type | Constraints | Security Notes |
|-------|------|-------------|----------------|
| ENCRYPTION_KEY | env string | Required in production, valid Fernet key | Startup fails if missing or invalid |
| GITHUB_WEBHOOK_SECRET | env string | Required in production | HMAC-SHA256 verification |
| SESSION_SECRET_KEY | env string | Required, ≥ 64 characters in production | Session signing entropy |
| COOKIE_SECURE | boolean | Required `true` in production | HTTPS-only cookie transmission |

**Validation behavior (production mode, `DEBUG=false`)**:
```
Missing ENCRYPTION_KEY → ERROR: refuse to start (Settings validation)
Invalid ENCRYPTION_KEY → ERROR: ValueError raised at first use via EncryptionService(debug=False)
Missing GITHUB_WEBHOOK_SECRET → ERROR: refuse to start (Settings validation)
SESSION_SECRET_KEY < 64 chars → ERROR: refuse to start (Settings validation)
COOKIE_SECURE = false → ERROR: refuse to start (Settings validation)
```

> **Note**: Invalid `ENCRYPTION_KEY` validation occurs at `EncryptionService` instantiation (lazy, on first use), not at application startup. Settings validation catches missing keys; format validation happens on first encryption service call.

### Rate Limit Record

Tracks per-user/per-IP request counts.

| Field | Type | Constraints | Security Notes |
|-------|------|-------------|----------------|
| key | string | user session ID or IP address | Per-user preferred over per-IP |
| endpoint | string | Route path | Scoped to specific endpoints |
| count | integer | Incremented per request | Reset on window expiration |
| window_start | datetime | Auto-set | Defines rate window boundary |
| limit | string | e.g., "10/minute" | Configured per-endpoint |

**Storage**: In-memory via `slowapi` defaults. No persistence required.

### Chat Message Reference (Client-Side)

Lightweight client-side pointer to server-stored messages.

| Field | Type | Constraints | Security Notes |
|-------|------|-------------|----------------|
| message_id | string | Reference only (no content) | Full content loaded from server |
| timestamp | datetime | Used for TTL eviction | Expired references auto-removed |

**Storage**: React state (in-memory only). Not persisted to localStorage. Max 100 entries with FIFO eviction.

## Relationships

```
User (GitHub identity)
  ├── 1:N → Session (one active session per browser)
  ├── 1:N → Project (owner relationship)
  └── 1:N → Rate Limit Record (per-endpoint tracking)

Project
  ├── N:1 → User (owner)
  ├── 1:N → Task
  ├── 1:N → Workflow
  └── 1:1 → Settings

Session
  ├── N:1 → User
  └── contains → encrypted GitHub OAuth token (Fernet)
```

## Validation Rules

### Startup Validation (Production Mode)

All validations run at application startup when `DEBUG=false`:

1. `ENCRYPTION_KEY` must be set and must be a valid Fernet key
2. `GITHUB_WEBHOOK_SECRET` must be set and non-empty
3. `SESSION_SECRET_KEY` must be set and ≥ 64 characters
4. `COOKIE_SECURE` must be `true`
5. `ADMIN_GITHUB_USER_ID` must be set (no auto-promotion)
6. All `CORS_ORIGINS` entries must be valid URLs with scheme + hostname

### Runtime Validation

1. Every project-scoped request must pass `verify_project_access` before execution
2. All webhook signatures verified via `hmac.compare_digest` (constant-time)
3. Rate limits enforced per-user on AI/write endpoints, per-IP on OAuth callback
4. Avatar URLs validated as HTTPS + known GitHub domains before rendering
5. GraphQL errors logged internally, generic message returned to client

## Security Boundaries

```
┌─────────────────────────────────────────────────────┐
│ External (Untrusted)                                │
│  Browser → HTTPS → nginx (security headers)         │
│                      ├── Static assets              │
│                      └── /api/* → Backend           │
├─────────────────────────────────────────────────────┤
│ Backend (Trusted, runs as appuser)                  │
│  FastAPI                                            │
│   ├── Auth middleware (session cookie validation)    │
│   ├── Rate limiting (slowapi)                       │
│   ├── Project access verification (per-endpoint)    │
│   ├── Webhook signature verification (HMAC-SHA256)  │
│   └── Encrypted storage (Fernet → SQLite)          │
├─────────────────────────────────────────────────────┤
│ Data (Restricted, 0700/0600 permissions)            │
│  SQLite at /var/lib/solune/data/settings.db         │
│   └── OAuth tokens encrypted with ENCRYPTION_KEY    │
└─────────────────────────────────────────────────────┘
```
