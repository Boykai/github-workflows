# Data Model: Bug Bash — Codebase Quality & Reliability Sweep

**Date**: 2026-02-24 | **Branch**: `010-bug-bash` | **Plan**: [plan.md](plan.md)

## Overview

This bug bash modifies existing entities rather than introducing new domain concepts. The primary data model changes are: (1) encrypted token storage in `user_sessions`, (2) admin user tracking in `global_settings`, and (3) formalization of in-memory bounded caches as a shared utility.

## Schema Changes

### Migration 003: Add Admin Column and Token Encryption Support

```sql
-- Migration 003: Add admin_github_user_id to global_settings
-- The first authenticated user auto-promotes to admin (session owner).
-- Used by FR-005 to gate settings modification endpoints.

ALTER TABLE global_settings ADD COLUMN admin_github_user_id TEXT DEFAULT NULL;
```

**Note**: The `access_token` and `refresh_token` columns in `user_sessions` remain `TEXT` — no schema change needed. Encrypted Fernet ciphertext is stored as a base64-encoded string in the same column type.

### Entity: user_sessions (modified behavior)

| Column | Type | Change |
|--------|------|--------|
| `session_id` | TEXT PK | No change |
| `github_user_id` | TEXT NOT NULL | No change |
| `github_username` | TEXT NOT NULL | No change |
| `github_avatar_url` | TEXT | No change |
| `access_token` | TEXT NOT NULL | **Now stores Fernet-encrypted ciphertext** (FR-003) |
| `refresh_token` | TEXT | **Now stores Fernet-encrypted ciphertext** (FR-003) |
| `token_expires_at` | TEXT | No change |
| `selected_project_id` | TEXT | No change |
| `created_at` | TEXT NOT NULL | No change |
| `updated_at` | TEXT NOT NULL | No change |

**Encryption behavior**:
- On write (`save_session`): `encrypt_token(plaintext)` → base64 ciphertext stored in column.
- On read (`_row_to_session`): `decrypt_token(ciphertext)` → plaintext. Returns `None` on failure (key change) → session treated as invalid/expired.
- Heuristic migration: tokens starting with `gho_`/`ghp_`/`ghr_` are plaintext; tokens starting with `gAAAAA` are already encrypted.

### Entity: global_settings (modified)

| Column | Type | Change |
|--------|------|--------|
| `id` | INTEGER PK DEFAULT 1 | No change |
| `admin_github_user_id` | TEXT DEFAULT NULL | **New** (FR-005) — stores the GitHub user ID of the session owner |
| All other columns | Various | No change |

**Admin assignment behavior**:
- On first use of an admin-gated endpoint: if `admin_github_user_id` is NULL, set it to the current session's `github_user_id` (auto-promote).
- Once set, only the matching user can access admin-gated endpoints. Other authenticated users get 403.

## In-Memory State Entities (formalized)

### BoundedSet / BoundedDict (new utility, FR-013)

Shared utility replacing 3+ copy-pasted pruning patterns. Not persisted — lives in `utils.py`.

| Parameter | Type | Description |
|-----------|------|-------------|
| `max_size` | int | Maximum number of entries before pruning |
| `prune_ratio` | float | Fraction to retain on prune (default: 0.5 — keep newest half) |

**Usage**: All in-memory sets/dicts in `copilot_polling/state.py` and `workflow_orchestrator/transitions.py` use these utilities for bounded growth.

### OAuth State Entry (formalized, FR-006)

Currently a plain dict in `github_auth.py`. Formalized with expiry tracking.

| Field | Type | Description |
|-------|------|-------------|
| `state` | str | Random state parameter |
| `created_at` | datetime | When the OAuth flow started |
| `redirect_uri` | str | Where to redirect after auth |

**Expiry**: Entries older than 10 minutes (configurable) are automatically cleaned by a periodic check or on access.

### Health Status (new response model, FR-020)

| Field | Type | Description |
|-------|------|-------------|
| `status` | str | `"pass"`, `"warn"`, or `"fail"` |
| `checks` | dict | Component check results keyed by name |

Each component check:

| Field | Type | Description |
|-------|------|-------------|
| `status` | str | `"pass"`, `"warn"`, or `"fail"` |
| `time` | str (optional) | Latency (e.g., `"12ms"`) |
| `output` | str (optional) | Error description on failure |
| `observed_value` | str (optional) | Current value (e.g., `"running"`) |

## Relationships

```
user_sessions.github_user_id ──> global_settings.admin_github_user_id
                                  (first session owner becomes admin)

user_sessions.access_token ──> encryption.py
                               (encrypt on write, decrypt on read)

copilot_polling/state.py globals ──> utils.prune_bounded_set/dict
                                     (shared pruning utility)
```

## Validation Rules

- `access_token` must be non-empty after decryption; None (decryption failure) invalidates the session.
- `admin_github_user_id` can only be set once (first-write-wins); no endpoint to change it.
- `BoundedSet.max_size` must be > 0; `prune_ratio` must be in (0, 1).
- `OAuth State` entries must have `created_at` within 10 minutes of current time to be valid.
- Health check sub-components must complete within their individual timeouts (DB: 2s, GitHub: 3s).
