# Research: Phase 4 — Security Hardening

**Feature**: `001-security-hardening`  
**Date**: 2026-03-21  
**Input**: spec.md unknowns and technical dependencies

## Research Tasks

### RT-1: Encryption Key Handling — Make Encryption Mandatory

**Context**: `ENCRYPTION_KEY` is currently optional with a silent plaintext fallback in debug mode. The spec requires fail-fast on missing key.

**Decision**: Enforce `ENCRYPTION_KEY` at all levels — `Settings` validation raises `ValueError` at startup if the key is absent regardless of debug mode; remove the passthrough mode from `EncryptionService`.

**Rationale**: The current architecture already validates `ENCRYPTION_KEY` in production via `_validate_production_secrets()` in `config.py` (line 115). In debug mode, it only logs a warning (line 146). The `EncryptionService` constructor silently accepts `key=None` and falls back to plaintext (lines 48-53 of `encryption.py`). Making it mandatory requires:
1. Remove the `| None` from `Settings.encryption_key` or add a debug-mode validator.
2. Have `EncryptionService.__init__` raise if `key` is None (no passthrough mode).
3. Remove the legacy plaintext detection in `decrypt()` since all new tokens will be encrypted (keep for one-time migration path).

**Alternatives considered**:
- **Lazy validation**: Only check on first encrypt/decrypt call — rejected because it defers failures to runtime.
- **Environment-variable-only guard**: Just check the env var without changing `EncryptionService` — rejected because it leaves a code path that can still process plaintext.

### RT-2: Encryption Key Rotation Strategy

**Context**: FR-004 requires supporting encryption key rotation — decrypting with previous keys while encrypting with the current key.

**Decision**: Introduce a `MultiFernet` approach using the `cryptography` library's built-in `MultiFernet` class. Accept a comma-separated list of keys via `ENCRYPTION_KEY` (primary first, previous keys after) and pass them to `MultiFernet`.

**Rationale**: `MultiFernet` is purpose-built for key rotation — it encrypts with the first key and attempts decryption with each key in order. This eliminates custom rotation logic. The existing `EncryptionService` uses `Fernet` directly, so upgrading to `MultiFernet` is a minimal change. The `ENCRYPTION_KEY` environment variable would contain `current_key,previous_key1,previous_key2`.

**Alternatives considered**:
- **Separate env vars** (`ENCRYPTION_KEY`, `ENCRYPTION_KEY_PREVIOUS`) — rejected because `MultiFernet` handles the list natively and a single env var is simpler.
- **Database-stored key metadata** — rejected as over-engineering for the single-instance SQLite architecture.

### RT-3: Session Revocation Mechanism

**Context**: Current session store has `delete_session()` for logout but no revocation check on every request. Sessions expire only by TTL.

**Decision**: Add a `revoked_sessions` table in SQLite and check it in `get_session()`. Revocation inserts a row; `get_session()` checks the table before returning. A background cleanup purges revocation records older than the session TTL.

**Rationale**: The current `get_session()` (in `session_store.py`) already queries SQLite for each session lookup. Adding a check against a `revoked_sessions` table is a minimal change to the existing flow. The `delete_session()` function removes the session entirely — revocation differs by keeping an audit record and invalidating the session_id in a lookup table for immediate effect.

**Alternatives considered**:
- **Token blacklist in-memory** — rejected because it doesn't survive process restarts. The spec requires revocation to persist.
- **Add a `revoked_at` column to `user_sessions`** — viable and simpler. Decision updated: use a `revoked_at` column on the existing `user_sessions` table instead of a separate table. This avoids a JOIN and keeps the schema simpler. `get_session()` checks `WHERE revoked_at IS NULL`.
- **Redis/external cache** — rejected; architecture is single-instance SQLite.

### RT-4: Webhook Deduplication with TTL

**Context**: Current `BoundedSet` (maxlen=1000) provides LRU-based deduplication but has no time-based expiration. The spec requires a 60-minute TTL window.

**Decision**: Replace `BoundedSet[str]` with a `TTLBoundedDict[str, datetime]` that stores the delivery ID → first-seen timestamp. On lookup, check both membership and TTL (60 minutes). Expired entries are pruned lazily on each lookup or in a background task.

**Rationale**: The current implementation in `webhooks.py` (line 27) uses `BoundedSet(maxlen=1000)` which evicts by insertion order with no TTL. This means a burst of 1001+ deliveries within 60 minutes would evict valid entries, and entries older than 60 minutes are never expired. A TTL-aware dict solves both problems. The `BoundedDict` utility already exists in `utils.py` and can be extended.

**Alternatives considered**:
- **External cache (Redis)** — rejected; single-instance architecture, no Redis dependency.
- **SQLite table for delivery IDs** — rejected; webhook deduplication is a hot path and in-memory is appropriate for single-instance.
- **Keep BoundedSet, increase capacity** — doesn't solve the TTL requirement.

### RT-5: OAuth Scope Validation

**Context**: The OAuth flow requests scopes `"read:user read:org project repo"` (line 74, `github_auth.py`) but never validates that the provider actually granted all requested scopes.

**Decision**: After `exchange_code_for_token()`, inspect the `X-OAuth-Scopes` header from GitHub's token response (or the `scope` field in the JSON response) and compare against the required set. If any required scopes are missing, reject the login with a clear error listing the missing scopes.

**Rationale**: GitHub's OAuth token endpoint returns the granted scopes in the response. The current `exchange_code_for_token()` (line 98) only extracts the token. Adding scope inspection is a minimal addition to the existing flow. The frontend needs to display a clear message — a structured error response with the `missing_scopes` list enables this.

**Alternatives considered**:
- **Runtime scope checking on each API call** — too late; the spec requires upfront validation. Runtime graceful handling (FR-020) is additive, not a replacement.
- **Re-request authorization with updated scope** — this is the remediation flow (FR-019), not the validation itself.

### RT-6: CSRF SameSite=Strict Upgrade

**Context**: Session cookies already use `samesite="strict"` (line 36 in `auth.py`). However, the CSRF middleware's `csrf_token` cookie uses `samesite="lax"` (line 68 in `csrf.py`).

**Decision**: Upgrade the CSRF cookie from `samesite="lax"` to `samesite="strict"`. Ensure the frontend handles the initial-load re-authentication scenario when arriving from an external link.

**Rationale**: The session cookie already uses `Strict` — the gap is only in the CSRF token cookie. Since the CSRF cookie is not `httpOnly` (it must be readable by JavaScript for the double-submit pattern), upgrading to `Strict` adds defense-in-depth. The frontend must handle the case where neither cookie is sent on cross-origin top-level navigations: the user sees the login page and is redirected to their intended destination after authenticating. The `redirect_after_login` mechanism needs to be implemented or verified.

**Alternatives considered**:
- **Keep Lax for CSRF cookie only** — rejected because the spec explicitly requires `SameSite=Strict` on all session-related cookies, and the CSRF cookie is part of the session security mechanism.
- **Remove double-submit and use only session cookie for CSRF** — rejected because the double-submit pattern provides an additional layer independent of cookie attributes.

### RT-7: Redirect After Login for SameSite=Strict

**Context**: When `SameSite=Strict` blocks cookies on cross-origin top-level navigation (e.g., clicking a link in an email), the user must re-authenticate. The spec requires preserving the user's intended destination.

**Decision**: Store the intended destination in a `return_to` query parameter during the OAuth flow or in `localStorage` on the frontend. After authentication, redirect to the stored destination.

**Rationale**: This is a UX concern, not a security mechanism. The standard pattern is to include a `return_to` parameter in the login redirect. The frontend already redirects to `/auth/callback` after OAuth — extending this to include the original destination is straightforward. Using `localStorage` is preferred over cookies (which won't be sent on the initial cross-origin navigation due to `Strict`).

**Alternatives considered**:
- **Server-side session storage for return URL** — rejected because the session doesn't exist yet at the point of the cross-origin navigation.
- **Cookie-based return URL** — rejected because `SameSite=Strict` means the cookie wouldn't be sent on the initial navigation.

## Summary

All technical unknowns resolved. Key decisions:
1. **Encryption**: `MultiFernet` for key rotation, mandatory at startup
2. **Session revocation**: `revoked_at` column on `user_sessions` table
3. **Webhook dedup**: TTL-aware bounded dict (in-memory, 60-min window)
4. **OAuth scopes**: Validate granted vs. required scopes post-token-exchange
5. **CSRF**: Upgrade CSRF cookie from `Lax` to `Strict`, add redirect-after-login
