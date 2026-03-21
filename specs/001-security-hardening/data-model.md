# Data Model: Phase 4 — Security Hardening

**Feature**: `001-security-hardening`  
**Date**: 2026-03-21  
**Input**: spec.md entities + research.md decisions

## Entities

### 1. Encryption Key (Configuration)

Not a database entity — loaded from the `ENCRYPTION_KEY` environment variable at startup.

| Field | Type | Description |
|-------|------|-------------|
| `primary_key` | `bytes` | Current Fernet key (first in comma-separated list) — used for encryption |
| `previous_keys` | `list[bytes]` | Previous Fernet keys (remaining in list) — used for decryption only |

**Validation Rules**:
- At least one valid base64-encoded 32-byte Fernet key must be present
- Application MUST refuse to start if the key is absent or invalid
- Comma-separated format: `current_key[,previous_key1[,previous_key2]]`

**State Transitions**: N/A (static configuration)

### 2. UserSession (Existing — Modified)

Existing table `user_sessions` with one new column.

| Field | Type | Nullable | Description |
|-------|------|----------|-------------|
| `session_id` | `TEXT (UUID)` | No | Primary key — random UUID |
| `github_user_id` | `TEXT` | No | GitHub numeric user ID |
| `github_username` | `TEXT` | No | GitHub login name |
| `github_avatar_url` | `TEXT` | Yes | User avatar URL |
| `access_token` | `TEXT` | No | **Encrypted** GitHub OAuth access token |
| `refresh_token` | `TEXT` | Yes | **Encrypted** OAuth refresh token |
| `token_expires_at` | `TEXT (ISO)` | Yes | Token expiration timestamp |
| `selected_project_id` | `TEXT` | Yes | Currently selected GitHub Project ID |
| `active_app_name` | `TEXT` | Yes | Active application context |
| `created_at` | `TEXT (ISO)` | No | Session creation time |
| `updated_at` | `TEXT (ISO)` | No | Last activity time |
| **`revoked_at`** | `TEXT (ISO)` | Yes | **NEW** — Revocation timestamp; NULL = active |

**Validation Rules**:
- `access_token` must be Fernet-encrypted (never plaintext)
- `revoked_at` is NULL for active sessions; non-NULL means revoked
- Sessions with `revoked_at IS NOT NULL` must be rejected on lookup

**State Transitions**:
```
Created (revoked_at = NULL)
  → Active (revoked_at = NULL, updated_at refreshed)
  → Revoked (revoked_at = <timestamp>)
  → Expired (updated_at + session_expire_hours < now)
  → Deleted (purged from database)
```

**Relationships**:
- One user (`github_user_id`) → many sessions

### 3. Revocation Record (Audit — Embedded in UserSession)

Revocation is recorded by setting `revoked_at` on the `user_sessions` row. No separate entity needed.

| Attribute | Source |
|-----------|--------|
| Which session | `session_id` |
| When revoked | `revoked_at` column |
| Who revoked | Inferred from request context (self-revocation via `/logout`, admin via future admin endpoint) |

### 4. Webhook Delivery Deduplication (In-Memory)

Not a database entity — maintained in application memory.

| Field | Type | Description |
|-------|------|-------------|
| `delivery_id` | `str` | Unique delivery ID from `X-GitHub-Delivery` header |
| `first_seen_at` | `datetime` | UTC timestamp when delivery was first received |

**Validation Rules**:
- TTL: 60 minutes from `first_seen_at`
- Max capacity: 10,000 entries (with LRU eviction as overflow safety)
- Entries older than 60 minutes are lazily pruned on each lookup

**State Transitions**:
```
New delivery arrives
  → Not in cache → Process + add to cache
  → In cache + TTL valid → Skip (return 200)
  → In cache + TTL expired → Remove from cache → Process + re-add
```

### 5. OAuth Scope Set (Configuration + Runtime)

Not a database entity — defined in code and validated at login time.

| Field | Type | Description |
|-------|------|-------------|
| `required_scopes` | `frozenset[str]` | Scopes the application requires (defined in code) |
| `granted_scopes` | `set[str]` | Scopes the OAuth provider returned for the user |
| `missing_scopes` | `set[str]` | `required_scopes - granted_scopes` |

**Current required scopes** (from `github_auth.py` line 74):
- `read:user` — User identity
- `read:org` — Organization membership
- `project` — GitHub Projects V2
- `repo` — Repository read/write

**Validation Rules**:
- `missing_scopes` must be empty for login to succeed
- If non-empty, return structured error with the list of missing scopes
- Scope comparison is case-sensitive, space-delimited

## Migration

### Migration 034: Add `revoked_at` to `user_sessions`

```sql
-- Migration 034: Session revocation support
ALTER TABLE user_sessions ADD COLUMN revoked_at TEXT DEFAULT NULL;
CREATE INDEX IF NOT EXISTS idx_user_sessions_revoked
    ON user_sessions(revoked_at)
    WHERE revoked_at IS NOT NULL;
```

### Migration 035: Encrypt existing plaintext tokens (one-time)

No schema change — handled in application code during startup or as a management command. Existing plaintext tokens (detected by `gho_`/`ghp_` prefix) are encrypted in-place on first access.

## Entity Relationship Summary

```
┌──────────────┐         ┌────────────────────────┐
│ GitHub User   │ 1───N  │ user_sessions          │
│ (external)    │         │ - session_id (PK)      │
│               │         │ - access_token (enc)   │
│               │         │ - refresh_token (enc)  │
│               │         │ - revoked_at (NEW)     │
└──────────────┘         └────────────────────────┘

┌──────────────────────────┐      ┌─────────────────────────┐
│ Webhook Delivery (memory)│      │ OAuth Scope Set (code)  │
│ - delivery_id            │      │ - required_scopes       │
│ - first_seen_at          │      │ - granted_scopes        │
│ - TTL: 60 minutes        │      │ - missing_scopes        │
└──────────────────────────┘      └─────────────────────────┘

┌────────────────────────────────┐
│ Encryption Key (env var)       │
│ - primary_key (MultiFernet)    │
│ - previous_keys (rotation)     │
└────────────────────────────────┘
```
