# Quickstart: Security, Privacy & Vulnerability Audit

**Feature**: 037-security-review | **Date**: 2026-03-12

## Overview

This feature remediates 21 security findings across OWASP Top 10 categories, organized into 4 phases by severity. Changes span the full stack: Python/FastAPI backend, React/TypeScript frontend, nginx reverse proxy, Docker deployment, and GitHub Actions CI/CD. The audit addresses credential leakage, encryption enforcement, access control, security headers, rate limiting, and defense-in-depth measures.

## Key Components

### 1. Backend: Cookie-Based Session Delivery (Critical — Phase 1)

Replace URL-based session token delivery with secure cookies on the OAuth callback:

```python
# In api/auth.py — OAuth callback handler
from fastapi.responses import RedirectResponse

@router.get("/github/callback")
async def oauth_callback(code: str, state: str):
    session = await github_auth.exchange_code(code, state)
    response = RedirectResponse(url=settings.frontend_url)
    response.set_cookie(
        key="session_id",
        value=session.token,
        httponly=True,
        samesite="strict",
        secure=settings.cookie_secure,
        max_age=settings.session_ttl_seconds,
        path="/",
    )
    return response
```

### 2. Backend: Mandatory Startup Validation (Critical — Phase 1)

Consolidated configuration checks in `config.py`:

```python
# In config.py — Settings validation
from pydantic import field_validator

class Settings(BaseSettings):
    encryption_key: str = ""
    github_webhook_secret: str = ""
    session_secret_key: str = ""
    cookie_secure: bool = False
    debug: bool = False

    @field_validator("session_secret_key")
    @classmethod
    def validate_session_key_length(cls, v: str) -> str:
        if len(v) < 64:
            raise ValueError("SESSION_SECRET_KEY must be at least 64 characters")
        return v

    def validate_production_secrets(self) -> None:
        """Call after construction to validate non-debug requirements."""
        if not self.debug:
            if not self.encryption_key:
                raise SystemExit("ENCRYPTION_KEY is required in non-debug mode")
            if not self.github_webhook_secret:
                raise SystemExit("GITHUB_WEBHOOK_SECRET is required in non-debug mode")
            if not self.cookie_secure:
                raise SystemExit("COOKIE_SECURE must be True in non-debug mode")
```

### 3. Backend: Centralized Project Ownership Check (High — Phase 2)

FastAPI dependency for consistent access control:

```python
# In dependencies.py
from fastapi import Depends, HTTPException

async def verify_project_ownership(
    project_id: str,
    session: UserSession = Depends(get_current_session),
    db = Depends(get_db),
) -> str:
    """Verify the authenticated user owns the specified project."""
    owner_id = await db.get_project_owner(project_id)
    if owner_id != session.user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    return project_id

# Usage in endpoints:
@router.post("/tasks/{project_id}")
async def create_task(
    project_id: str = Depends(verify_project_ownership),
    ...
):
    ...
```

### 4. Frontend: Non-Root Dockerfile (Critical — Phase 1)

```dockerfile
# In frontend/Dockerfile
FROM nginx:alpine

# Copy application files
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf

# Create writable directories for non-root nginx
RUN mkdir -p /tmp/nginx && \
    chown -R nginx:nginx /tmp/nginx /usr/share/nginx/html /var/log/nginx

# Run as non-root user
USER nginx
```

### 5. Nginx: Security Headers (High — Phase 2)

```nginx
# In frontend/nginx.conf
server_tokens off;

server {
    # Security headers
    add_header Content-Security-Policy "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' https://avatars.githubusercontent.com; connect-src 'self' wss:; font-src 'self'; object-src 'none'; frame-ancestors 'none'; base-uri 'self'; form-action 'self';" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Permissions-Policy "camera=(), microphone=(), geolocation=(), payment=()" always;
    # Remove deprecated header (do NOT add X-XSS-Protection)
}
```

### 6. Frontend: localStorage Refactor (Medium — Phase 3)

```typescript
// In hooks/useChatHistory.ts
interface ChatMessageRef {
  messageId: string;
  projectId: string;
  timestamp: number;
  ttl: number; // milliseconds, default 7 days
}

// Store only references, not full content
const storeMessageRef = (ref: ChatMessageRef) => {
  const refs = getStoredRefs();
  refs.push(ref);
  localStorage.setItem(CHAT_REFS_KEY, JSON.stringify(refs));
};

// Clear all on logout
const clearChatData = () => {
  localStorage.removeItem(CHAT_REFS_KEY);
};
```

## Implementation Phases

| Phase | Severity | Findings | Key Changes |
|-------|----------|----------|-------------|
| 1 | Critical | #1, #2, #3 | Cookie session, encryption enforcement, non-root container |
| 2 | High | #4–#10 | Access control, timing-safe comparison, security headers, OAuth scopes, port binding |
| 3 | Medium | #11–#19 | Rate limiting, debug isolation, localStorage, error sanitization, permissions |
| 4 | Low | #20–#21 | Workflow permissions, avatar URL validation |

## Development Steps

1. **Phase 1 — Critical** (Fix immediately)
   - Refactor OAuth callback to set session cookie (auth.py, useAuth.ts)
   - Add startup validation for mandatory secrets (config.py)
   - Add encryption key migration for existing plaintext rows (migration SQL)
   - Add `USER nginx` to frontend Dockerfile

2. **Phase 2 — High** (This week)
   - Implement centralized project ownership dependency (dependencies.py)
   - Wire ownership check into all project-scoped endpoints
   - Replace `!=` with `hmac.compare_digest()` in signal.py
   - Add security headers to nginx.conf
   - Move dev login PAT from URL to POST body (auth.py)
   - Narrow OAuth scopes (github_auth.py)
   - Add session key length validation (config.py)
   - Change docker-compose port bindings to 127.0.0.1

3. **Phase 3 — Medium** (Next sprint)
   - Add slowapi rate limiting to sensitive endpoints
   - Enforce cookie_secure in non-debug mode
   - Remove debug bypass from webhook verification
   - Gate API docs on ENABLE_DOCS env var
   - Set database directory/file permissions
   - Validate CORS origins at startup
   - Move data volume path in docker-compose
   - Refactor useChatHistory.ts for message ID storage
   - Sanitize GraphQL error messages

4. **Phase 4 — Low** (Backlog)
   - Narrow branch-issue-link.yml permissions
   - Add avatar URL domain validation in IssueCard.tsx

## Validation

```bash
# Backend tests
cd backend && python -m pytest tests/unit/ -v

# Frontend tests
cd frontend && npx vitest run --reporter=verbose

# Verify non-root container
docker exec frontend-container id
# Expected: uid=101(nginx) gid=101(nginx)

# Verify security headers
curl -I https://localhost:3000
# Expected: Content-Security-Policy, Strict-Transport-Security, Referrer-Policy, Permissions-Policy

# Verify no credentials in URL after login
# Complete OAuth flow, check browser URL bar — no ?session_token= parameter

# Verify startup fails without secrets
ENCRYPTION_KEY="" python -m src.main
# Expected: SystemExit with descriptive error
```
