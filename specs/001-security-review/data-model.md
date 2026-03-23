# Data Model: Security, Privacy & Vulnerability Audit

**Feature**: 001-security-review | **Date**: 2026-03-23
**Input**: [research.md](research.md) decisions, [spec.md](spec.md) key entities

## Overview

The security audit modifies the behavior and constraints of existing entities rather than introducing new ones. This document describes the security-relevant attributes, validation rules, and state transitions for each affected entity.

---

## Entities

### 1. Session

**Description**: Represents an authenticated user's active session, managed via HttpOnly cookies.

| Field | Type | Constraints | Security Relevance |
|-------|------|-------------|-------------------|
| `session_id` | UUID | Primary key, generated server-side | Stored in HttpOnly cookie, never in URL |
| `user_id` | Integer | Foreign key to GitHub user | Links session to authenticated identity |
| `github_token` | String (encrypted) | Encrypted at rest with Fernet | Protected by mandatory `ENCRYPTION_KEY` |
| `token_expires_at` | DateTime | Auto-refresh within 5-minute buffer | Prevents use of expired tokens |
| `refresh_token` | String (encrypted) | Encrypted at rest with Fernet | Protected by mandatory `ENCRYPTION_KEY` |
| `created_at` | DateTime | Set on creation | Session lifetime tracking |

**Validation rules**:
- Session ID is never exposed in URLs, query parameters, or response bodies (cookie-only delivery)
- GitHub tokens are always encrypted before database storage
- Session expiry defaults to 8 hours (`session_expire_hours`)
- Expired sessions are cleaned up every 3600 seconds (`session_cleanup_interval`)

**State transitions**:
```
[No Session] → OAuth Callback → [Active Session] → Token Refresh → [Active Session]
                                                   → Expiry/Logout → [Deleted]
```

### 2. Project

**Description**: Represents a user's project with ownership-based access control.

| Field | Type | Constraints | Security Relevance |
|-------|------|-------------|-------------------|
| `project_id` | String | Primary identifier | Subject to `verify_project_access` on every request |
| `owner_id` | Integer | GitHub user ID of project owner | Authorization check: `session.user_id == project.owner_id` |

**Validation rules**:
- Every endpoint accepting `project_id` must call `verify_project_access(request, project_id, session)`
- Unowned project access returns 403 Forbidden
- WebSocket connections to unowned projects are rejected before any data transmission

**Access control pattern**:
```python
# Centralized in dependencies.py
async def verify_project_access(
    request: Request,
    project_id: str,
    session: UserSession = Depends(_get_session_dep()),
) -> None:
    """Verify the authenticated user has access to project_id."""
    # ... raises HTTPException(403) on failure
```

### 3. Configuration (AppSettings)

**Description**: Application startup configuration with mandatory security validation in production mode.

| Field | Type | Default | Production Requirement |
|-------|------|---------|----------------------|
| `encryption_key` | String | None | **MANDATORY** — startup fails without it |
| `github_webhook_secret` | String | None | **MANDATORY** — startup fails without it |
| `session_secret_key` | String | None | **MANDATORY** — minimum 64 characters |
| `cookie_secure` | Boolean | False | **MANDATORY** — auto-detected from HTTPS or explicit |
| `debug` | Boolean | False | Controls validation strictness |
| `cors_origins` | String | "" | Each origin must be a valid URL with scheme + hostname |
| `enable_docs` | Boolean | False | Independent of `debug` — gates Swagger/ReDoc |
| `database_path` | String | `/var/lib/solune/data/settings.db` | Must be absolute path (or `:memory:` for tests) |
| `admin_github_user_id` | Integer | None | Required in production |

**Validation rules (non-debug mode)**:
1. `encryption_key` must be set → error if missing
2. `github_webhook_secret` must be set → error if missing
3. `session_secret_key` must be ≥ 64 characters → error if shorter
4. `effective_cookie_secure` must be True → error if False
5. `admin_github_user_id` must be set → error if missing
6. `database_path` must be absolute or `:memory:` → error if relative
7. All CORS origins must have valid scheme + hostname → error on malformed
8. All validation errors collected and raised together as `ValueError`

**State transitions**:
```
[Startup] → Validate → [Valid: Application Runs] 
                      → [Invalid: ValueError raised, application exits]
```

### 4. Chat Message Reference

**Description**: Lightweight in-memory reference for chat input history. No persistent storage.

| Field | Type | Storage | Security Relevance |
|-------|------|---------|-------------------|
| `history` | String[] | React state (memory only) | Never persisted to localStorage |
| `historyIndex` | Integer | React state (memory only) | Navigation position in history |
| `draftBuffer` | String | React ref (memory only) | Current unsaved input |

**Validation rules**:
- Content is never written to localStorage, sessionStorage, or IndexedDB
- Legacy localStorage entries are cleared on component mount
- All state is reset on logout
- History is lost on page refresh (by design — privacy over convenience)

### 5. Webhook Payload

**Description**: Incoming webhook payloads from GitHub and Signal that require signature verification.

| Field | Type | Constraints | Security Relevance |
|-------|------|-------------|-------------------|
| `payload` | Bytes | Raw request body | Used for HMAC computation |
| `signature` | String | `X-Hub-Signature-256` or `X-Signal-Secret` header | Verified with `hmac.compare_digest()` |
| `secret` | String | Server-side configured secret | Never logged, constant-time comparison only |

**Validation rules**:
- Signature verification is always required regardless of debug mode
- GitHub webhooks: HMAC-SHA256 verified via `hmac.compare_digest()`
- Signal webhooks: Direct secret comparison via `hmac.compare_digest()`
- Missing or invalid signatures return 401/403 immediately

---

## Relationships

```
Session ──owns──▶ User ──owns──▶ Project
                                    ▲
                                    │
                              verify_project_access()
                                    │
                     ┌──────────────┼──────────────┐
                     │              │              │
                  tasks.py    projects.py    workflow.py
                  settings.py  agents.py    pipelines.py
```

## File Permission Model

| Resource | Permission | Owner | Rationale |
|----------|-----------|-------|-----------|
| Database directory | `0700` (rwx------) | Application user | Only app process needs directory access |
| Database file | `0600` (rw-------) | Application user | Only app process needs read/write |
| Container process | Non-root UID | `appuser` / `nginx-app` | Limits blast radius of container escape |

## Rate Limiting Model

| Endpoint Category | Limit | Key | Library |
|-------------------|-------|-----|---------|
| Chat endpoints | 10/minute | Per-user | slowapi |
| Agent endpoints | 5/minute | Per-user | slowapi |
| Workflow endpoints | 10/minute | Per-user | slowapi |
| OAuth callback | 20/minute | Per-IP (`get_remote_address`) | slowapi |
