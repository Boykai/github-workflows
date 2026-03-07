# Config Contracts: Security, Privacy & Vulnerability Audit

This directory defines the target state of configuration and infrastructure files after the security remediation.

## backend/src/config.py — Target Settings

### New/Modified Fields

```python
class Settings(BaseSettings):
    # ... existing fields ...

    # MODIFIED: Encryption key — mandatory in non-debug mode
    encryption_key: str | None = None

    # MODIFIED: Webhook secret — mandatory in non-debug mode
    github_webhook_secret: str | None = None

    # MODIFIED: Session secret — min 64 chars in non-debug mode
    session_secret_key: str

    # MODIFIED: Cookie secure — must be True (effective) in non-debug mode
    cookie_secure: bool = False

    # NEW: Independent docs toggle
    enable_docs: bool = False

    # MODIFIED: Database path — outside application root
    database_path: str = "/var/lib/ghchat/data/settings.db"

    # MODIFIED: CORS origins — validated at startup
    cors_origins: str = "http://localhost:5173"

    @model_validator(mode="after")
    def _validate_production_secrets(self) -> "Settings":
        """Enforce mandatory secrets in non-debug mode."""
        if not self.debug:
            errors = []
            if not self.encryption_key:
                errors.append("ENCRYPTION_KEY is required in production mode")
            if not self.github_webhook_secret:
                errors.append("GITHUB_WEBHOOK_SECRET is required in production mode")
            if len(self.session_secret_key) < 64:
                errors.append(
                    f"SESSION_SECRET_KEY must be at least 64 characters "
                    f"(got {len(self.session_secret_key)})"
                )
            if not self.effective_cookie_secure:
                errors.append(
                    "Cookie Secure flag must be enabled in production mode "
                    "(set COOKIE_SECURE=true or use an https:// FRONTEND_URL)"
                )
            if errors:
                raise ValueError(
                    "Production configuration errors:\n" + "\n".join(f"  - {e}" for e in errors)
                )
        return self

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse and validate CORS origins."""
        origins = [o.strip() for o in self.cors_origins.split(",") if o.strip()]
        for origin in origins:
            parsed = urlparse(origin)
            if not parsed.scheme or not parsed.hostname:
                raise ValueError(
                    f"Invalid CORS origin '{origin}': must include scheme and hostname "
                    f"(e.g., 'https://example.com')"
                )
        return origins
```

### Environment Variables

```bash
# Required in production (non-debug) mode
ENCRYPTION_KEY=<base64-encoded-32-byte-fernet-key>
GITHUB_WEBHOOK_SECRET=<webhook-secret-from-github>
SESSION_SECRET_KEY=<at-least-64-character-random-string>

# New: Independent API docs toggle (default: false)
ENABLE_DOCS=false

# Modified: Database path (default updated)
DATABASE_PATH=/var/lib/ghchat/data/settings.db

# Existing: CORS origins (now validated)
CORS_ORIGINS=https://your-domain.com
```

## backend/src/main.py — API Docs Toggle

```python
# Target: docs gated on ENABLE_DOCS, not DEBUG
app = FastAPI(
    title="GitHub Chat",
    docs_url="/api/docs" if settings.enable_docs else None,
    redoc_url="/api/redoc" if settings.enable_docs else None,
    # ...
)
```

## backend/src/api/auth.py — Session Endpoint Changes

### OAuth Callback (modified)

```python
@router.get("/callback")
async def oauth_callback(code: str, state: str) -> RedirectResponse:
    """Handle GitHub OAuth callback. Set session cookie and redirect."""
    session = await github_auth_service.exchange_code_for_session(code, state)
    response = RedirectResponse(url=f"{settings.frontend_url}/auth/callback")
    _set_session_cookie(response, str(session.session_id))
    return response
```

### Dev Login (modified to POST body)

```python
class DevLoginRequest(BaseModel):
    github_token: str

@router.post("/dev-login")
async def dev_login(
    request: DevLoginRequest,
    response: Response,
) -> UserResponse:
    """Dev login — accepts GitHub PAT in POST body (not URL)."""
    if not settings.debug:
        raise HTTPException(status_code=404)
    # ... authenticate with request.github_token
```

### Removed Endpoint

```python
# REMOVED: POST /session?session_token=... (credentials in URL)
```

## backend/src/api/signal.py — Constant-Time Comparison

```python
# Target: Replace != with hmac.compare_digest
import hmac

if x_signal_secret is None or not hmac.compare_digest(
    x_signal_secret, settings.signal_webhook_secret
):
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Invalid webhook secret",
    )
```

## backend/src/api/webhooks.py — Remove Debug Bypass

```python
# Target: Always verify webhook signature (no debug bypass)
if not settings.github_webhook_secret:
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Webhook secret not configured",
    )
if not verify_webhook_signature(body, x_hub_signature_256, settings.github_webhook_secret):
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Invalid webhook signature",
    )
```

## backend/src/services/database.py — Permission Hardening

```python
# Target: Restricted directory and file permissions
db_dir = Path(db_path).parent
if str(db_dir) != ".":
    db_dir.mkdir(parents=True, exist_ok=True, mode=0o700)

# After database file creation:
db_file = Path(db_path)
if db_file.exists():
    db_file.chmod(0o600)
```

## backend/src/dependencies.py — Project Authorization

```python
async def verify_project_access(
    session: Annotated[UserSession, Depends(get_session_dep)],
    project_id: str,
) -> str:
    """
    Verify the authenticated user has access to the specified project.

    Raises HTTPException(403) if the user does not own the project.
    Returns the validated project_id.
    """
    projects = await github_projects_service.list_projects(session.access_token)
    if not any(p.project_id == project_id for p in projects):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: you do not have access to this project",
        )
    return project_id
```

## Rate Limiting Contract

```python
# backend/src/middleware/rate_limit.py
from slowapi import Limiter
from slowapi.util import get_remote_address

def get_user_key(request: Request) -> str:
    """Extract user identifier for per-user rate limiting."""
    # Uses session user ID from cookie-authenticated request
    ...

limiter = Limiter(key_func=get_user_key)

# Endpoint decorators:
# @limiter.limit("10/minute")  — chat, workflow
# @limiter.limit("5/minute")   — agents
# @limiter.limit("20/minute", key_func=get_remote_address)  — OAuth callback
```

## docker-compose.yml — Target Configuration

```yaml
services:
  backend:
    ports:
      - "127.0.0.1:8000:8000"     # Bind to localhost only
    volumes:
      - ghchat-data:/var/lib/ghchat/data  # Outside app root

  frontend:
    ports:
      - "127.0.0.1:5173:8080"     # Bind to localhost; nginx on 8080 (non-root)
```

## backend/src/services/github_auth.py — OAuth Scope

```python
# Target: Remove 'repo' scope
GITHUB_AUTHORIZE_URL = "https://github.com/login/oauth/authorize"

def get_authorization_url(self) -> tuple[str, str]:
    state = secrets.token_urlsafe(32)
    params = {
        "client_id": self.settings.github_client_id,
        "redirect_uri": self.settings.github_redirect_uri,
        "scope": "read:user read:org project",  # REMOVED: 'repo'
        "state": state,
    }
    # ...
```
