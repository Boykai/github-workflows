# Quickstart: Phase 4 — Security Hardening

**Feature**: `001-security-hardening`  
**Date**: 2026-03-21

## Prerequisites

- Python 3.12+ installed
- Node.js 18+ installed (for frontend)
- Repository cloned: `Boykai/github-workflows`
- Backend dependencies: `cd solune/backend && pip install -e ".[dev]"`
- Frontend dependencies: `cd solune/frontend && npm ci`

## Environment Setup

### Required Environment Variables

```bash
# Generate a Fernet encryption key (MANDATORY — app will not start without it)
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Set in .env or export:
export ENCRYPTION_KEY="<generated-fernet-key>"

# For key rotation (optional): comma-separated, current key first
# export ENCRYPTION_KEY="<new-key>,<old-key>"
```

### Existing Required Variables (unchanged)

```bash
export GITHUB_CLIENT_ID="<your-github-app-client-id>"
export GITHUB_CLIENT_SECRET="<your-github-app-client-secret>"
export SESSION_SECRET_KEY="<64+-character-random-string>"
export DEBUG=true  # false for production
```

## Verify Changes

### 1. Mandatory Encryption (Item 4.1)

```bash
# Test: App refuses to start without encryption key
unset ENCRYPTION_KEY
cd solune/backend && python -m uvicorn src.main:app
# Expected: Startup fails with clear error about missing ENCRYPTION_KEY

# Test: App starts with valid key
export ENCRYPTION_KEY="$(python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())')"
python -m uvicorn src.main:app
# Expected: App starts successfully
```

### 2. Session Revocation (Item 4.2)

```bash
# Test via API (after logging in):
# 1. List sessions
curl -b cookies.txt http://localhost:8000/api/v1/auth/sessions

# 2. Revoke a specific session
curl -X POST -b cookies.txt \
  -H "Content-Type: application/json" \
  -H "X-CSRF-Token: <csrf-token>" \
  -d '{"session_id": "<session-uuid>"}' \
  http://localhost:8000/api/v1/auth/sessions/revoke

# 3. Revoke all sessions
curl -X POST -b cookies.txt \
  -H "X-CSRF-Token: <csrf-token>" \
  http://localhost:8000/api/v1/auth/sessions/revoke-all

# 4. Verify revoked session is rejected
curl -b cookies.txt http://localhost:8000/api/v1/auth/me
# Expected: 401 Unauthorized — "Session has been revoked"
```

### 3. OAuth Scope Validation (Item 4.5)

```bash
# Test: Login with a GitHub OAuth app that has fewer scopes configured
# Expected: Redirect to /auth/callback?error=insufficient_scopes&missing=<scopes>
# Frontend displays: "Your GitHub authorization is missing required permissions"
```

### 4. Webhook Deduplication (Item 4.3)

```bash
# Test: Send same webhook twice within 60 minutes
DELIVERY_ID="test-$(date +%s)"

# First delivery — should be processed
curl -X POST http://localhost:8000/api/v1/webhooks/github \
  -H "X-GitHub-Event: ping" \
  -H "X-GitHub-Delivery: $DELIVERY_ID" \
  -H "X-Hub-Signature-256: sha256=<valid-sig>" \
  -d '{"zen": "test"}'
# Expected: 200 OK (processed)

# Second delivery — should be skipped
curl -X POST http://localhost:8000/api/v1/webhooks/github \
  -H "X-GitHub-Event: ping" \
  -H "X-GitHub-Delivery: $DELIVERY_ID" \
  -H "X-Hub-Signature-256: sha256=<valid-sig>" \
  -d '{"zen": "test"}'
# Expected: 200 OK with {"status": "skipped", "reason": "duplicate delivery"}
```

### 5. CSRF SameSite=Strict (Item 4.7)

```bash
# Test: Inspect response headers after login
curl -v http://localhost:8000/api/v1/auth/me 2>&1 | grep -i "set-cookie"
# Expected: csrf_token cookie has SameSite=Strict (not Lax)
# Expected: solune_session cookie has SameSite=Strict (unchanged)
```

## Running Tests

```bash
# Backend unit tests
cd solune/backend
python -m pytest tests/unit/ -x -q --timeout=30

# Specific security tests
python -m pytest tests/unit/test_token_encryption.py -v
python -m pytest tests/unit/test_session_store.py -v
python -m pytest tests/unit/test_webhooks.py -v
python -m pytest tests/unit/test_auth_security.py -v
python -m pytest tests/unit/test_csrf.py -v

# Frontend tests
cd solune/frontend
npx vitest run
```

## Key Files Modified

| File | Change |
|------|--------|
| `solune/backend/src/config.py` | Make `encryption_key` mandatory in all modes |
| `solune/backend/src/services/encryption.py` | `MultiFernet` support, remove passthrough mode |
| `solune/backend/src/services/session_store.py` | Revocation check in `get_session()`, new revocation functions |
| `solune/backend/src/api/auth.py` | New session list/revoke endpoints |
| `solune/backend/src/api/webhooks.py` | TTL-based deduplication cache |
| `solune/backend/src/services/github_auth.py` | OAuth scope validation post-token-exchange |
| `solune/backend/src/middleware/csrf.py` | CSRF cookie `SameSite=Strict` |
| `solune/backend/src/migrations/034_session_revocation.sql` | `revoked_at` column |
