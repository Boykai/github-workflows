# Security Contracts: Security, Privacy & Vulnerability Audit

This directory defines the target state of security-relevant configuration files and API behaviors after remediation.

## backend/src/config.py — Target Validation Rules

```python
class Settings(BaseSettings):
    # Existing fields with new validators
    encryption_key: str | None = None
    github_webhook_secret: str | None = None
    session_secret_key: str  # No default — must be provided
    debug: bool = False
    cookie_secure: bool = False
    cors_origins: str = "http://localhost:5173"
    enable_docs: bool = False  # NEW: independent of debug

    @model_validator(mode="after")
    def validate_production_security(self) -> "Settings":
        """Enforce security requirements in non-debug mode."""
        if not self.debug:
            if not self.encryption_key:
                raise ValueError(
                    "ENCRYPTION_KEY is required in production (non-debug) mode"
                )
            if not self.github_webhook_secret:
                raise ValueError(
                    "GITHUB_WEBHOOK_SECRET is required in production (non-debug) mode"
                )
            if not self.effective_cookie_secure:
                raise ValueError(
                    "Cookie Secure flag must be enabled in production (non-debug) mode"
                )

        if len(self.session_secret_key) < 64:
            raise ValueError(
                f"SESSION_SECRET_KEY must be at least 64 characters "
                f"(got {len(self.session_secret_key)})"
            )

        # Validate CORS origins format
        for origin in self.cors_origins_list:
            parsed = urlparse(origin)
            if not parsed.scheme or not parsed.hostname:
                raise ValueError(
                    f"Malformed CORS origin: '{origin}' — "
                    f"must include scheme and hostname (e.g., https://example.com)"
                )

        return self
```

## backend/src/main.py — API Docs Gating

```python
# Target: Gate on ENABLE_DOCS, not DEBUG
app = FastAPI(
    docs_url="/api/docs" if settings.enable_docs else None,
    redoc_url="/api/redoc" if settings.enable_docs else None,
    # ...
)
```

## backend/src/api/auth.py — OAuth Callback Cookie Delivery

```python
# Target: Set cookie on callback response, redirect with no credentials
@router.get("/github/callback")
async def github_callback(code: str, state: str):
    # ... validate state, exchange code for token, create session ...
    response = RedirectResponse(url=f"{settings.frontend_url}/auth/callback")
    _set_session_cookie(response, session_token)  # HttpOnly, Secure, SameSite=strict
    return response
    # NO query parameters in redirect URL
```

```python
# Target: Dev login accepts credentials in POST body
@router.post("/dev-login")  # Changed from GET to POST
async def dev_login(body: DevLoginRequest):  # Pydantic model, not query params
    github_token = body.github_token
    # ...
```

## backend/src/dependencies.py — Project Authorization Dependency

```python
async def require_project_access(
    project_id: str,
    session: Session = Depends(get_current_session),
) -> str:
    """Verify the authenticated user has access to the target project.
    
    Raises HTTPException(403) if access is denied.
    Returns the validated project_id.
    """
    # Check user's project list via GitHub API or cached project membership
    user_projects = await get_user_projects(session.access_token)
    if project_id not in {p.id for p in user_projects}:
        raise HTTPException(
            status_code=403,
            detail="Access denied: you do not have access to this project"
        )
    return project_id
```

## backend/src/api/signal.py — Constant-Time Comparison

```python
# Target: Use hmac.compare_digest instead of !=
import hmac

if x_signal_secret is None or not hmac.compare_digest(
    x_signal_secret, settings.signal_webhook_secret
):
    raise HTTPException(status_code=403, detail="Invalid webhook secret")
```

## backend/src/services/encryption.py — Mandatory Encryption

```python
# Target: Remove plaintext passthrough in encrypt()
def encrypt(self, plaintext: str) -> str:
    """Encrypt a string. ENCRYPTION_KEY must be set."""
    if not self._fernet:
        raise RuntimeError("Encryption not available: ENCRYPTION_KEY not configured")
    return self._fernet.encrypt(plaintext.encode()).decode()

# decrypt() retains legacy plaintext detection for migration
def decrypt(self, ciphertext: str) -> str:
    """Decrypt a string. Handles legacy plaintext for migration."""
    if self._is_legacy_plaintext(ciphertext):
        logger.warning("Legacy plaintext token detected — schedule migration")
        return ciphertext
    if not self._fernet:
        raise RuntimeError("Encryption not available: ENCRYPTION_KEY not configured")
    return self._fernet.decrypt(ciphertext.encode()).decode()
```

## backend/src/services/database.py — File Permissions

```python
# Target: Explicit directory and file permissions
import os

db_dir.mkdir(parents=True, exist_ok=True)
os.chmod(db_dir, 0o700)  # Owner-only access

# After database file creation:
if db_path.exists():
    os.chmod(db_path, 0o600)  # Owner read/write only
```

## backend/src/services/github_auth.py — Minimum OAuth Scopes

```python
# Target: Remove 'repo' scope
params = {
    "client_id": self._client_id,
    "redirect_uri": self._redirect_uri,
    "scope": "read:user read:org project",  # Removed 'repo'
    "state": state,
}
```

## backend/src/api/webhooks.py — No Debug Bypass

```python
# Target: Always require signature verification
if not settings.github_webhook_secret:
    raise HTTPException(
        status_code=503,
        detail="Webhook secret not configured"
    )
# Verify signature (no debug bypass)
_verify_webhook_signature(payload, signature, settings.github_webhook_secret)
```

## frontend/Dockerfile — Non-Root User

```dockerfile
FROM nginx:alpine

# Create nginx cache directories with correct ownership
RUN mkdir -p /var/cache/nginx /var/run && \
    chown -R nginx:nginx /var/cache/nginx /var/run /etc/nginx/conf.d

# Copy built assets
COPY --from=build --chown=nginx:nginx /app/dist /usr/share/nginx/html
COPY --chown=nginx:nginx nginx.conf /etc/nginx/conf.d/default.conf

# Switch to non-root user
USER nginx

# Listen on unprivileged port
EXPOSE 8080
```

## frontend/nginx.conf — Security Headers

```nginx
server {
    listen 8080;  # Unprivileged port for non-root
    server_tokens off;  # Hide nginx version

    # Security headers
    add_header Content-Security-Policy "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' https://avatars.githubusercontent.com; connect-src 'self' wss:; frame-ancestors 'none'" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Permissions-Policy "camera=(), microphone=(), geolocation=()" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    # X-XSS-Protection removed (deprecated)
}
```

## docker-compose.yml — Network Binding & Volume Path

```yaml
services:
  backend:
    ports:
      - "127.0.0.1:8000:8000"  # Localhost only
    volumes:
      - ghchat-data:/var/lib/ghchat/data  # Outside app root

  frontend:
    ports:
      - "127.0.0.1:5173:8080"  # Localhost only, maps to unprivileged port
```

## frontend/src/hooks/useAuth.ts — Cookie-Only Auth

```typescript
// Target: Remove URL parameter reading
// The OAuth callback sets an HttpOnly cookie directly.
// useAuth just checks session status via API call.
const checkSession = async () => {
  const response = await fetch('/api/v1/auth/session', {
    credentials: 'include',  // Send cookies
  });
  // No reading from window.location.search
};
```

## frontend/src/hooks/useChatHistory.ts — Lightweight References

```typescript
interface ChatReference {
  id: string;
  timestamp: number;  // Unix epoch ms
}

// Target: Store only references with TTL
const TTL_MS = 24 * 60 * 60 * 1000; // 24 hours

const saveReference = (messageId: string) => {
  const refs: ChatReference[] = loadReferences();
  const now = Date.now();
  // Prune expired entries
  const valid = refs.filter(r => now - r.timestamp < TTL_MS);
  valid.push({ id: messageId, timestamp: now });
  localStorage.setItem(STORAGE_KEY, JSON.stringify(valid));
};

// Clear all on logout
const clearOnLogout = () => {
  localStorage.removeItem(STORAGE_KEY);
};
```

## .github/workflows/branch-issue-link.yml — Scoped Permissions

```yaml
permissions: {}  # Default: no permissions

jobs:
  link:
    permissions:
      issues: write      # Required: comment on issues to add branch links
      contents: read     # Required: read branch information
```

**Note**: Current permissions are already minimal and appropriate. Add a justification comment explaining why `issues: write` is needed.

## backend/src/services/github_projects/service.py — Sanitized Errors

```python
# Target: Log full error, raise sanitized message
if "errors" in result:
    error_msg = "; ".join(e.get("message", str(e)) for e in result["errors"])
    logger.error("GraphQL API error: %s", error_msg)
    raise ValueError("An error occurred while communicating with the GitHub API")
```

## Rate Limiting Contract (slowapi)

```python
# backend/src/main.py or dedicated rate_limit.py
from slowapi import Limiter
from slowapi.util import get_remote_address

def get_user_key(request: Request) -> str:
    """Extract user ID from session for per-user rate limiting."""
    session = getattr(request.state, "session", None)
    if session and session.github_user_id:
        return str(session.github_user_id)
    return get_remote_address(request)

limiter = Limiter(key_func=get_user_key)

# Endpoint decoration:
@router.post("/chat")
@limiter.limit("30/minute")
async def chat_endpoint(request: Request, ...): ...

@router.post("/agent")
@limiter.limit("30/minute")
async def agent_endpoint(request: Request, ...): ...

@router.post("/workflow")
@limiter.limit("20/minute")
async def workflow_endpoint(request: Request, ...): ...

# OAuth callback: per-IP
@router.get("/github/callback")
@limiter.limit("10/minute", key_func=get_remote_address)
async def github_callback(request: Request, ...): ...
```
