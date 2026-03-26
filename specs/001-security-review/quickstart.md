# Quickstart: Security, Privacy & Vulnerability Audit Verification

**Feature**: 001-security-review | **Date**: 2026-03-26

## Overview

This guide provides step-by-step verification procedures for all 21 security findings. Since 17 of 21 findings are already remediated in the current codebase, the primary task is behavioral verification rather than implementation.

---

## Prerequisites

- Docker and Docker Compose installed
- Access to the Solune repository
- Python 3.12+ with virtual environment
- Node.js 20+ for frontend verification

```bash
cd solune/backend
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

---

## Phase 1 — Critical (Verification)

### V1: Credentials Never in URLs (Finding 1)

```bash
# 1. Start the application
docker compose up -d

# 2. Initiate OAuth login and complete the flow
# 3. After redirect, inspect browser URL bar
#    Expected: No ?session_token=, ?access_token=, or similar parameters

# 4. Inspect browser history (Ctrl+H)
#    Expected: No entries containing credential values

# 5. Code review: grep for URL credential patterns
grep -rn "session_token" solune/backend/src/api/auth.py
grep -rn "window.location.search.*token" solune/frontend/src/
# Expected: No matches for credential extraction from URL
```

**Pass Criteria**: No credentials in browser URL, history, or access logs after login.

### V2: Encryption Enforced at Startup (Finding 2)

```bash
# Test 1: Missing ENCRYPTION_KEY
ENCRYPTION_KEY="" GITHUB_WEBHOOK_SECRET="test" SESSION_SECRET_KEY="$(python -c 'import secrets; print(secrets.token_hex(32))')" \
  DEBUG=false python -m src.main
# Expected: Application refuses to start with clear error about ENCRYPTION_KEY

# Test 2: Missing GITHUB_WEBHOOK_SECRET
ENCRYPTION_KEY="$(python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())')" \
  GITHUB_WEBHOOK_SECRET="" SESSION_SECRET_KEY="$(python -c 'import secrets; print(secrets.token_hex(32))')" \
  DEBUG=false python -m src.main
# Expected: Application refuses to start with clear error about GITHUB_WEBHOOK_SECRET

# Test 3: Short SESSION_SECRET_KEY in non-debug mode
SESSION_SECRET_KEY="too-short" DEBUG=false python -m src.main
# Expected: Application refuses to start with error about minimum 64 characters

# Test 4: Unit tests
pytest tests/unit/test_config.py -v -k "production"
```

**Pass Criteria**: Application fails to start for each missing/invalid secret in non-debug mode.

### V3: Non-Root Containers (Finding 3)

```bash
# Frontend container
docker exec $(docker ps -qf "name=frontend") id
# Expected: uid=<non-zero>(nginx-app) gid=...

# Backend container
docker exec $(docker ps -qf "name=backend") id
# Expected: uid=<non-zero>(appuser) gid=...

# Code review: Dockerfile USER directives
grep -n "USER" solune/frontend/Dockerfile
# Expected: USER nginx-app (or similar non-root user)
```

**Pass Criteria**: Both containers report non-root UID.

---

## Phase 2 — High (Verification)

### V4: Project Access Control (Finding 4)

```bash
# Unit test verification
pytest tests/unit/test_dependencies.py -v -k "project_access"

# Code review: verify_project_access usage
grep -rn "verify_project_access" solune/backend/src/api/
# Expected: Present in tasks.py, settings.py, workflow.py, and any endpoint accepting project_id
```

**Pass Criteria**: All project-scoped endpoints use `verify_project_access` dependency.

### V5: Constant-Time Comparisons (Findings 5, 6)

```bash
# Code review: all secret comparisons
grep -rn "compare_digest" solune/backend/src/
# Expected: hmac.compare_digest in signal.py, webhooks.py
#           secrets.compare_digest in csrf.py

# Negative check: no standard equality on secrets
grep -rn "!=" solune/backend/src/api/signal.py | grep -i "secret"
# Expected: No matches (all use compare_digest)
```

**Pass Criteria**: All secret comparisons use constant-time functions.

### V6: Security Headers (Finding 6)

```bash
# Start frontend and check headers
docker compose up -d frontend
curl -sI http://localhost:5173 | grep -iE "(content-security|strict-transport|referrer-policy|permissions-policy|x-content-type|x-frame|x-xss|server)"

# Expected output (all present):
# Content-Security-Policy: default-src 'self'; ...
# Strict-Transport-Security: max-age=31536000; includeSubDomains
# Referrer-Policy: strict-origin-when-cross-origin
# Permissions-Policy: camera=(), microphone=(), geolocation=()
# X-Content-Type-Options: nosniff
# X-Frame-Options: SAMEORIGIN

# Expected ABSENT:
# No X-XSS-Protection header
# Server header should NOT contain version number
```

**Pass Criteria**: All five required headers present; no deprecated headers; no version disclosure.

### V7: Dev Login Uses POST Body (Finding 7)

```bash
# Code review
grep -A 20 "dev.login\|dev-login" solune/backend/src/api/auth.py
# Expected: POST endpoint, PAT in request body, not URL parameters

# Verify no GET endpoint for dev login
grep -n "@router.get.*dev" solune/backend/src/api/auth.py
# Expected: No matches
```

**Pass Criteria**: Dev login accepts credentials in POST body only.

### V8: OAuth Scopes (Finding 8)

```bash
# Inspect current scopes
grep -n "scope" solune/backend/src/services/github_auth.py
# Expected: "read:user read:org project repo"
# Note: repo scope is documented as required for issue/PR/comment creation

# Verify justification comment exists
grep -B 3 "scope" solune/backend/src/services/github_auth.py
# Expected: Comment explaining why repo scope is needed
```

**Pass Criteria**: Scopes documented with justification. (Exception: `repo` scope retained per Finding 8 research.)

### V9: Session Secret Key Entropy (Finding 9)

```bash
# Code review
grep -n "session_secret_key" solune/backend/src/config.py | head -5
# Expected: Validation enforcing ≥ 64 characters

# Test with short key
SESSION_SECRET_KEY="short" python -c "from src.config import get_settings; get_settings()"
# Expected: Validation error
```

**Pass Criteria**: Keys shorter than 64 characters rejected at startup.

### V10: Localhost Binding (Finding 10)

```bash
# Inspect docker-compose
grep -A 2 "ports:" solune/docker-compose.yml
# Expected: "127.0.0.1:8000:8000" and "127.0.0.1:5173:8080"
# No 0.0.0.0 bindings

# Verify Signal API not exposed
grep "expose" solune/docker-compose.yml
# Expected: Signal API uses "expose" not "ports"
```

**Pass Criteria**: All services bound to 127.0.0.1; no 0.0.0.0 bindings.

---

## Phase 3 — Medium (Verification)

### V11: Rate Limiting (Finding 11)

```bash
# Code review: rate limit decorators
grep -rn "@limiter.limit" solune/backend/src/api/
# Expected: Decorators on chat, agent, workflow, and auth endpoints

# Verify middleware
grep -rn "RateLimitKeyMiddleware" solune/backend/src/
# Expected: Middleware registered in main.py

# Test (requires running server)
for i in $(seq 1 15); do curl -s -o /dev/null -w "%{http_code}\n" -X POST http://localhost:8000/api/v1/chat/send -H "Cookie: session_id=test"; done
# Expected: 429 responses after exceeding limit
```

**Pass Criteria**: Expensive endpoints return 429 after threshold exceeded.

### V12: Cookie Secure Flag (Finding 12)

```bash
# Code review
grep -n "cookie_secure\|effective_cookie_secure" solune/backend/src/config.py
# Expected: Production validation requires cookie_secure=true or HTTPS frontend_url
```

### V13: Webhook Debug Bypass (Finding 13)

```bash
# Code review: no DEBUG branching in webhook verification
grep -n "debug\|DEBUG" solune/backend/src/api/webhooks.py
# Expected: No conditional logic based on debug mode

# Verify always-verify behavior
grep -B 5 -A 10 "verify_webhook_signature" solune/backend/src/api/webhooks.py
# Expected: Verification called unconditionally
```

### V14: API Docs Toggle (Finding 14)

```bash
# Code review
grep -n "enable_docs\|docs_url\|redoc_url" solune/backend/src/main.py
# Expected: docs_url gated on settings.enable_docs, NOT settings.debug

grep -n "enable_docs" solune/backend/src/config.py
# Expected: enable_docs: bool = False (independent of debug)
```

### V15: Database Permissions (Finding 15)

```bash
# Code review
grep -n "0o700\|0o600\|chmod" solune/backend/src/services/database.py
# Expected: mkdir with mode=0o700, chmod(0o600) on database file

# Runtime verification
docker exec $(docker ps -qf "name=backend") stat -c '%a' /var/lib/solune/data
# Expected: 700
```

### V16: CORS Validation (Finding 16)

```bash
# Code review
grep -A 15 "cors_origins_list" solune/backend/src/config.py
# Expected: urlparse validation with scheme and hostname checks
```

### V17: Data Volume Location (Finding 17)

```bash
# Inspect docker-compose
grep -A 2 "volumes:" solune/docker-compose.yml | grep -v "^--$"
# Expected: /var/lib/solune/data (outside application root)
```

### V18: Chat History Storage (Finding 18)

```bash
# Code review: no localStorage for message content
grep -n "localStorage" solune/frontend/src/hooks/useChatHistory.ts
# Expected: Only clearLegacyStorage() references, no setItem for messages

# Verify memory-only storage
grep -n "useState" solune/frontend/src/hooks/useChatHistory.ts
# Expected: useState for message history (memory only)
```

### V19: Error Sanitization (Finding 19)

```bash
# Code review
grep -rn "handle_service_error" solune/backend/src/services/
# Expected: Used in service files to sanitize error messages

grep -rn "handle_service_error" solune/backend/src/logging_utils.py
# Expected: Logs full error, raises generic message
```

---

## Phase 4 — Low (Verification)

### V20: CI Workflow Permissions (Finding 20)

```bash
# Inspect workflow
head -20 .github/workflows/branch-issue-link.yml
# Expected: permissions: {} at workflow level, scoped per-job with justification comments
```

### V21: Avatar URL Validation (Finding 21)

```bash
# Code review
grep -A 20 "validateAvatarUrl" solune/frontend/src/components/IssueCard.tsx
# Expected: HTTPS check, hostname allowlist, SVG placeholder fallback
```

---

## Full Verification Checklist

| # | Check | Method | Expected |
|---|-------|--------|----------|
| 1 | No credentials in URLs after login | Browser inspection | Clean URL bar, history, logs |
| 2 | Backend refuses start without secrets | Startup test | Exit with clear error |
| 3 | Containers run as non-root | `docker exec id` | Non-zero UID |
| 4 | Unowned project_id → 403 | API test | 403 Forbidden |
| 5 | Unowned WebSocket → rejected | WebSocket test | Connection refused |
| 6 | All secret comparisons constant-time | Code review | `compare_digest` everywhere |
| 7 | Security headers present | `curl -I` | All 5 headers, no deprecated |
| 8 | Rate limit → 429 | Load test | 429 after threshold |
| 9 | No message content in localStorage after logout | DevTools | Empty |
| 10 | DB permissions 0700/0600 | `stat` in container | Correct modes |
| 11 | OAuth scopes documented | Code review | Justification comment present |
| 12 | No error internals in API responses | Error trigger test | Generic message only |
