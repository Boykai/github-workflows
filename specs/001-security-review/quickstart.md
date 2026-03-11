# Quickstart: Security Review Remediation Program

**Branch**: `001-security-review` | **Date**: 2026-03-11

## Developer Guide — Security-Hardened Architecture

This document explains the key security changes introduced by the remediation and how to work with the hardened codebase.

---

## 1. Production Configuration Requirements

### Before: Optional security settings

```bash
# Many security settings were optional or auto-detected
ENCRYPTION_KEY=         # Optional — app warns and stores plaintext
SESSION_SECRET_KEY=abc  # Any length accepted
COOKIE_SECURE=          # Auto-detected from URL prefix
```

### After: Mandatory production settings

```bash
# Production mode (DEBUG=false) requires all of these:
ENCRYPTION_KEY=your-fernet-key-here          # REQUIRED — generated with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
GITHUB_WEBHOOK_SECRET=your-webhook-secret    # REQUIRED — configured in GitHub webhook settings
SESSION_SECRET_KEY=your-64-char-minimum-key  # REQUIRED — at least 64 characters
COOKIE_SECURE=true                           # RECOMMENDED — explicitly enable secure cookies
FRONTEND_URL=https://your-domain.com         # REQUIRED if COOKIE_SECURE is not true; must start with https:// to infer secure cookies
CORS_ORIGINS=https://your-domain.com         # REQUIRED — valid URL format with scheme

# In production, at least one of the following must hold:
#   - COOKIE_SECURE=true
#   - FRONTEND_URL starts with https://

# Development mode (DEBUG=true) skips these checks
DEBUG=true
```

### What Happens If Settings Are Missing

```text
$ DEBUG=false ENCRYPTION_KEY="" python -m uvicorn src.main:app
ERROR: Production security validation failed:

  - ENCRYPTION_KEY is required in production mode
  - SESSION_SECRET_KEY must be at least 64 characters (got 10)
```

The application refuses to start. Fix all listed violations before retrying.

---

## 2. Authentication Flow Changes

### Before: Token in URL

```text
GitHub OAuth → Backend callback → Redirect to frontend?session_token=abc123
Frontend reads token from URL → stores in state
```

### After: HttpOnly cookie

```text
GitHub OAuth → Backend callback → Sets HttpOnly cookie → Redirect to frontend (clean URL)
Browser sends cookie automatically on all API requests
Frontend calls /api/v1/auth/me to check session status
```

### Frontend Impact

```typescript
// REMOVED — do not read credentials from URL
const params = new URLSearchParams(window.location.search);
const token = params.get("session_token");

// NEW — session is cookie-based, checked via API
const { data: user } = useQuery({
  queryKey: ["auth", "me"],
  queryFn: () => fetch("/api/v1/auth/me", { credentials: "include" }),
});
```

### Dev Login Changes

```typescript
// REMOVED — PAT in URL query parameter
fetch(`/api/v1/auth/dev-login?token=${pat}`);

// NEW — PAT in POST body
fetch("/api/v1/auth/dev-login", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ token: pat }),
});
```

---

## 3. Project Authorization

### Before: No ownership check

```python
@router.post("/tasks/{project_id}")
async def create_task(project_id: str, session: UserSession = Depends(get_current_session)):
    # Any authenticated user could create tasks in any project
    ...
```

### After: Ownership verified

```python
from src.dependencies import verify_project_access

@router.post("/tasks/{project_id}", dependencies=[Depends(verify_project_access)])
async def create_task(
    project_id: str,
    session: UserSession = Depends(get_current_session),
):
    # project_id is verified — user has access
    ...
```

### Adding Authorization to New Endpoints

When creating new endpoints that accept a `project_id`:

1. Import `verify_project_access` from `src.dependencies`
2. Add it as a route-level dependency via `dependencies=[Depends(verify_project_access)]`
3. The dependency automatically verifies access and raises 403 if denied; `project_id` remains a normal path parameter

```python
@router.get("/new-feature/{project_id}", dependencies=[Depends(verify_project_access)])
async def new_feature(
    project_id: str,
    session: UserSession = Depends(get_current_session),
):
    # Safe — project access is verified before this code runs
    ...
```

---

## 4. Webhook Security

### Before: Debug bypass

```python
# In webhooks.py — debug mode skipped verification
if settings.debug and not settings.github_webhook_secret:
    # Skip verification in debug mode
    pass
```

### After: Always verify

```python
# Webhook verification is ALWAYS required, even in debug mode
# Developers must set a test secret locally:
#   GITHUB_WEBHOOK_SECRET=test-secret-for-development
```

### Timing-Safe Comparisons

All secret comparisons now use `hmac.compare_digest()`:

```python
import hmac

# CORRECT — constant-time comparison
if not hmac.compare_digest(received_secret, expected_secret):
    raise HTTPException(403, "Invalid webhook signature")

# WRONG — timing attack vulnerable (DO NOT USE)
if received_secret != expected_secret:
    raise HTTPException(403, "Invalid webhook signature")
```

---

## 5. Rate Limiting

### Checking Rate Limit Status

Rate-limited endpoints return headers on every response:

```text
X-RateLimit-Limit: 30
X-RateLimit-Remaining: 28
X-RateLimit-Reset: 1709300000
```

When the limit is exceeded:

```text
HTTP/1.1 429 Too Many Requests
Retry-After: 60
Content-Type: application/json

{"detail": "Rate limit exceeded. Please try again later."}
```

### Rate Limit Configuration

Default limits (configurable via environment variables):

| Endpoint | Limit | Key |
|----------|-------|-----|
| Chat send | 30/minute | Per authenticated user |
| Agent invoke | 10/minute | Per authenticated user |
| Workflow trigger | 10/minute | Per authenticated user |
| OAuth callback | 5/minute | Per IP address |

---

## 6. Client-Side Chat Privacy

### Before: Full messages in localStorage

```typescript
// Stored full message content — survives logout, readable by XSS
localStorage.setItem("chat-history", JSON.stringify(messages));
```

### After: References only with TTL

```typescript
// Store only lightweight references
interface ChatReference {
  id: string;
  conversationId: string;
  storedAt: number;
}

// References expire after 24 hours
// All chat data cleared on logout
```

### Logout Cleanup

The `useAuth` logout flow now clears all chat-related localStorage keys:

```typescript
async function logout() {
  await fetch("/api/v1/auth/logout", { method: "POST", credentials: "include" });
  // Clear all chat references from localStorage
  clearChatStorage();
  // Redirect to login
}
```

---

## 7. Avatar URL Safety

### Before: Direct rendering

```tsx
<img src={issue.author.avatarUrl} alt={issue.author.login} />
```

### After: Validated rendering

```tsx
const validUrl = getValidAvatarUrl(issue.author.avatarUrl);
<img
  src={validUrl ?? "/placeholder-avatar.svg"}
  alt={issue.author.login}
/>
```

Only `https://avatars.githubusercontent.com` URLs are rendered. All others show a placeholder.

---

## 8. Docker Security

### Container Users

| Container | User | UID |
|-----------|------|-----|
| Backend | `appuser` | Non-root |
| Frontend | `nginx-app` | Non-root |

### Port Bindings

| Service | Development | Production |
|---------|------------|------------|
| Backend | `127.0.0.1:8000:8000` | Not exposed (reverse proxy) |
| Frontend | `127.0.0.1:5173:8080` | Not exposed (reverse proxy) |

### Data Volume

```yaml
# Data stored outside application root
volumes:
  ghchat-data:
    # Mounted at /var/lib/ghchat/data (not ./data)
```

---

## 9. API Documentation Toggle

### Before: Gated on DEBUG

```python
# API docs available whenever DEBUG=true
app = FastAPI(docs_url="/docs" if settings.debug else None)
```

### After: Independent toggle

```python
# Controlled by ENABLE_DOCS, independent of DEBUG
app = FastAPI(docs_url="/docs" if settings.enable_docs else None)
```

Set `ENABLE_DOCS=true` to enable Swagger/ReDoc in any environment.

---

## 10. Migration Checklist for Existing Deployments

1. **Generate encryption key**: `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`
2. **Set required environment variables**: `ENCRYPTION_KEY`, `GITHUB_WEBHOOK_SECRET`, `SESSION_SECRET_KEY` (≥64 chars), `COOKIE_SECURE=true`
3. **Configure webhook secret**: Match the secret in your GitHub webhook settings
4. **Run database migration**: Migration 021 will mark existing credentials for re-encryption
5. **Re-authorize OAuth**: After scope reduction, users will be prompted to re-authorize with reduced permissions
6. **Update CORS origins**: Ensure all origins use valid URL format (`https://your-domain.com`)
7. **Set dev webhook secret**: Add `GITHUB_WEBHOOK_SECRET=test-secret` to your `.env` for local development
