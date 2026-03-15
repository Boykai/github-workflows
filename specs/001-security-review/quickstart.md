# Quickstart: Security, Privacy & Vulnerability Audit

**Feature**: 001-security-review | **Date**: 2026-03-15

## Overview

This feature addresses 21 security findings from an OWASP Top 10 audit. Research reveals that **~19 of 21 findings are already remediated** in the current codebase. The remaining work focuses on closing 2–5 minor gaps and performing a comprehensive verification pass.

## Prerequisites

- Docker & Docker Compose installed
- GitHub OAuth App credentials (`GITHUB_CLIENT_ID`, `GITHUB_CLIENT_SECRET`)
- Python 3.12+ (for backend development)
- Node.js 22+ (for frontend development)

## Quick Verification

### 1. Verify Production Startup Validation

```bash
# Should fail — missing required secrets
cd solune/backend
DEBUG=false ENCRYPTION_KEY= python -m uvicorn src.main:app
# Expected: startup error about missing ENCRYPTION_KEY

# Should fail — short session key (generate a valid Fernet key first)
DEBUG=false ENCRYPTION_KEY=$(python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())") SESSION_SECRET_KEY=short python -m uvicorn src.main:app
# Expected: startup error about SESSION_SECRET_KEY length
```

### 2. Verify Container Security

```bash
# Build and run containers
docker compose up -d

# Check frontend runs as non-root
docker exec solune-frontend id
# Expected: uid=101(nginx-app) or similar non-root UID

# Check backend runs as non-root
docker exec solune-backend id
# Expected: uid=1000(appuser) or similar non-root UID

# Check port bindings (localhost only)
docker compose ps --format "{{.Name}}: {{.Ports}}"
# Expected: 127.0.0.1:8000->8000, 127.0.0.1:5173->8080
```

### 3. Verify Security Headers

```bash
# Check nginx security headers
curl -sI http://localhost:5173/ | grep -iE '(content-security|strict-transport|referrer-policy|permissions-policy|x-frame|x-content-type|server:)'
# Expected: All headers present; no server version disclosure
```

### 4. Verify Database Permissions

```bash
docker exec solune-backend ls -la /var/lib/solune/data/
# Expected: drwx------ (0700) for directory
docker exec solune-backend ls -la /var/lib/solune/data/settings.db
# Expected: -rw------- (0600) for database file
```

### 5. Verify Project Access Control

```bash
# As authenticated User A, create a project
# As authenticated User B, try to access User A's project
curl -X POST http://localhost:8000/api/v1/projects/{user_a_project_id}/tasks \
  -H "Cookie: session={user_b_session}" \
  -H "Content-Type: application/json" \
  -d '{"title": "test"}'
# Expected: 403 Forbidden
```

## Addressed Gaps (Verified Complete)

The following gaps were identified during the initial audit research and have since been closed:

### Gap 1: Invalid Encryption Key Handling ✅

**File**: `solune/backend/src/services/encryption.py`

Resolved: `EncryptionService` now raises `ValueError` on invalid key when `debug=False` (production mode). In debug mode, it logs a warning and falls back to plaintext for local development.

### Gap 2: Dev Login Endpoint Verification ✅

**File**: `solune/backend/src/api/auth.py`

Verified: Dev login endpoint (`POST /api/v1/auth/dev-login`) accepts credentials via `DevLoginRequest` POST body (`github_token` field) only. No URL query parameters accepted. Endpoint returns 404 when `DEBUG=false`.

### Gap 3: OAuth Scope Documentation ✅

**File**: `solune/backend/src/services/github_auth.py`

Resolved: The `repo` scope is documented as a known limitation — GitHub Projects V2 requires it for issue write operations. Comment added explaining the dependency.

### Gap 4: Explicit `server_tokens off` ✅

**File**: `solune/frontend/nginx.conf`

Resolved: Explicit `server_tokens off;` directive added to nginx configuration.

### Gap 5: Rate Limit Coverage Audit ✅

**Files**: Various endpoint files in `solune/backend/src/api/`

Verified: Rate limits applied to all endpoints identified in the audit — chat (10/min), agents (5/min), workflow (10/min), OAuth callback (20/min per-IP).

## Running Tests

```bash
# Backend tests
cd solune/backend && python -m pytest tests/ -v

# Frontend tests
cd solune/frontend && npx vitest run

# Backend lint
cd solune/backend && python -m ruff check src/

# Frontend lint
cd solune/frontend && npm run lint
```

## Key Files Reference

| Category | Files |
|----------|-------|
| Auth & Sessions | `solune/backend/src/api/auth.py`, `solune/frontend/src/hooks/useAuth.ts` |
| Config Validation | `solune/backend/src/config.py` |
| Encryption | `solune/backend/src/services/encryption.py` |
| Access Control | `solune/backend/src/api/tasks.py`, `projects.py`, `settings.py`, `workflow.py` |
| Rate Limiting | `solune/backend/src/middleware/rate_limit.py` |
| Security Headers | `solune/frontend/nginx.conf` |
| Webhook Verification | `solune/backend/src/api/webhooks.py`, `signal.py` |
| Database Security | `solune/backend/src/services/database.py` |
| Container Security | `solune/frontend/Dockerfile`, `solune/backend/Dockerfile`, `docker-compose.yml` |
| Client-Side Storage | `solune/frontend/src/hooks/useChatHistory.ts` |
| Avatar Validation | `solune/frontend/src/components/board/IssueCard.tsx` |
| OAuth Scopes | `solune/backend/src/services/github_auth.py` |
| Error Sanitization | `solune/backend/src/services/github_projects/service.py` |
| API Docs Toggle | `solune/backend/src/main.py` |
| GH Actions Permissions | `.github/workflows/branch-issue-link.yml` |
