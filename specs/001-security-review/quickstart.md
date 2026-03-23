# Quickstart: Security, Privacy & Vulnerability Audit

**Feature**: 001-security-review | **Date**: 2026-03-23
**Input**: [plan.md](plan.md), [research.md](research.md), [data-model.md](data-model.md), [contracts/](contracts/)

## Overview

This guide provides a phased implementation roadmap for the 21 security findings. Each phase groups findings by severity with clear dependency ordering, affected files, and verification steps.

---

## Prerequisites

- Python ≥3.12, Node.js 25, Docker with Compose
- Repository cloned: `solune/` directory contains backend and frontend
- Environment variables configured (see `.env.example`)

## Implementation Phases

### Phase 1 — Critical (Fix Immediately)

**Dependencies**: None — these are foundational and must be completed first.

| # | Finding | Files | Approach |
|---|---------|-------|----------|
| 1 | Session token in URL → cookie delivery | `auth.py`, `useAuth.ts` | Set HttpOnly/Secure/SameSite=Strict cookie in OAuth callback; redirect with no URL credentials; frontend reads session from cookie jar |
| 2 | Encryption enforcement at startup | `config.py`, `encryption.py` | Add startup validation: fail if `ENCRYPTION_KEY`, `GITHUB_WEBHOOK_SECRET` missing in non-debug mode |
| 3 | Non-root container | `frontend/Dockerfile` | Add `USER nginx-app` directive; listen on port 8080 |

**Verification**:
```bash
# 1. Login — no credentials in URL
# Complete OAuth flow, inspect browser URL bar and history

# 2. Encryption enforcement
ENCRYPTION_KEY= GITHUB_WEBHOOK_SECRET= python -c "from src.config import get_settings; get_settings()"
# Expected: ValueError listing missing keys

# 3. Container user
docker exec solune-frontend id
# Expected: uid != 0
```

---

### Phase 2 — High (This Week)

**Dependencies**: Phase 1 must be complete (encryption key required for running the app).

| # | Finding | Files | Approach |
|---|---------|-------|----------|
| 4 | Project access authorization | `dependencies.py`, `tasks.py`, `projects.py`, `settings.py`, `workflow.py` | Add centralized `verify_project_access()` dependency; apply to all project-scoped endpoints |
| 5 | Timing attack on secrets | `signal.py` | Replace `!=` with `hmac.compare_digest()` for all secret comparisons |
| 6 | HTTP security headers | `nginx.conf` | Add CSP, HSTS, Referrer-Policy, Permissions-Policy; remove X-XSS-Protection; set `server_tokens off` |
| 7 | Dev login POST body | `auth.py` | Change dev-login to accept `DevLoginRequest` Pydantic model via POST body |
| 8 | OAuth scope minimization | `github_auth.py` | Document scope justification; retain `repo` if narrower scopes fail (test in staging) |
| 9 | Session key entropy | `config.py` | Add `len(session_secret_key) >= 64` check to startup validation |
| 10 | Docker port binding | `docker-compose.yml` | Change port mappings to `127.0.0.1:port:port` format |

**Verification**:
```bash
# 4. Authorization check
curl -H "Cookie: session=valid_session" http://localhost:8000/api/projects/UNOWNED_ID
# Expected: 403 Forbidden

# 5. Constant-time comparison (code review)
grep -rn "compare_digest" solune/backend/src/api/signal.py solune/backend/src/api/webhooks.py

# 6. Security headers
curl -sI http://localhost:5173/ | grep -E "Content-Security-Policy|Strict-Transport|Referrer-Policy|Permissions-Policy|Server:"

# 7. Dev login
curl -X POST http://localhost:8000/api/auth/dev-login -H "Content-Type: application/json" -d '{"github_token": "test"}'

# 9. Session key length
SESSION_SECRET_KEY=short python -c "from src.config import get_settings; get_settings()"
# Expected: ValueError about key length

# 10. Port binding
docker compose ps --format "{{.Ports}}"
# Expected: 127.0.0.1:xxxx->xxxx
```

---

### Phase 3 — Medium (Next Sprint)

**Dependencies**: Phase 2 complete. Rate limiting requires `slowapi` dependency (already in pyproject.toml).

| # | Finding | Files | Approach |
|---|---------|-------|----------|
| 11 | Rate limiting | `chat.py`, `agents.py`, `workflow.py`, `auth.py` | Add `@limiter.limit()` decorators with per-user/per-IP keys |
| 12 | Cookie Secure enforcement | `config.py` | Add `effective_cookie_secure` check to startup validation |
| 13 | Debug webhook bypass removal | `webhooks.py` | Remove debug-conditional verification; always require secret |
| 14 | API docs toggle | `main.py` | Gate on `ENABLE_DOCS` env var instead of `DEBUG` |
| 15 | Database permissions | `database.py` | Create dir with `0o700`, file with `0o600`; re-enforce on recovery |
| 16 | CORS validation | `config.py` | Add `cors_origins_list` property with URL scheme/hostname validation |
| 17 | Data volume mount | `docker-compose.yml` | Mount named volume at `/var/lib/solune/data` |
| 18 | Chat localStorage | `useChatHistory.ts` | Store history in React state only; clear legacy localStorage |
| 19 | GraphQL error sanitization | `service.py` / `projects.py` | Catch exceptions, log server-side, return generic responses |

**Verification**:
```bash
# 11. Rate limiting
for i in $(seq 1 15); do curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8000/api/chat/...; done
# Expected: 429 after threshold

# 15. Database permissions
stat -c "%a" /var/lib/solune/data /var/lib/solune/data/settings.db
# Expected: 700, 600

# 18. Chat localStorage (browser devtools after logout)
# localStorage should contain no message content
```

---

### Phase 4 — Low (Backlog)

**Dependencies**: None — independent of other phases.

| # | Finding | Files | Approach |
|---|---------|-------|----------|
| 20 | Workflow permissions | `branch-issue-link.yml` | Set default `permissions: {}`, grant only needed at job level |
| 21 | Avatar URL validation | `IssueCard.tsx` | Add `validateAvatarUrl()` with HTTPS + domain allowlist |

**Verification**:
```bash
# 20. Workflow permissions (code review)
grep -A5 "permissions:" .github/workflows/branch-issue-link.yml

# 21. Avatar validation (code review)
grep -A10 "validateAvatarUrl" solune/frontend/src/components/board/IssueCard.tsx
```

---

## Key Decision Points

| Decision | Impact | Mitigation |
|----------|--------|------------|
| `repo` OAuth scope retained | Broader than ideal | Documented with code comment; GitHub App migration deferred |
| Encryption key now mandatory | Breaking change for existing deployments | Migration path documented; generation command in error message |
| Per-user rate limiting preferred | Per-IP would penalize shared NAT/VPN | Per-IP used only for OAuth callback (unauthenticated) |
| Memory-only chat history | Content lost on page refresh | Acceptable trade-off for privacy; content available from backend |

## Behavioral Verification Checklist

| # | Check | SC | Method |
|---|-------|-----|--------|
| 1 | No credentials in URL after login | SC-001 | Browser inspection |
| 2 | Backend refuses to start without `ENCRYPTION_KEY` | SC-002 | Startup test |
| 3 | Frontend container runs as non-root | SC-003 | `docker exec id` |
| 4 | Unowned `project_id` returns 403 | SC-004 | API test |
| 5 | Unowned WebSocket rejected before data | SC-005 | WebSocket test |
| 6 | All secret comparisons use constant-time | SC-006 | Code review |
| 7 | Security headers present, no server version | SC-007 | `curl -I` |
| 8 | Rate limit returns 429 | SC-008 | Load test |
| 9 | No message content in localStorage after logout | SC-009 | Browser devtools |
| 10 | DB directory 0700, file 0600 | SC-010 | `stat` command |
| 11 | Malformed CORS origins rejected at startup | SC-011 | Startup test with invalid origin |
| 12 | No internal error details in API responses | SC-012 | API test with forced GitHub API error |
