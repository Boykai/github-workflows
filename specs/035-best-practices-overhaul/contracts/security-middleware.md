# Contract: Security Middleware

**Feature**: `035-best-practices-overhaul` | **Phase**: 5 — Security Hardening
**Files**: `backend/src/main.py` (modification), `backend/src/middleware/csp.py` (new), `backend/src/dependencies.py` (modification)

## Purpose

Harden HTTP security: restrict CORS headers, add Content Security Policy, require explicit admin designation, and enforce user-scoped session access.

## CORS Hardening

### Current State (backend/src/main.py)

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],  # ← Security issue
)
```

### Target State

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=[
        "Authorization",
        "Content-Type",
        "Accept",
        "X-Request-ID",
        "X-Requested-With",
    ],
)
```

### Headers Rationale

| Header | Why Allowed |
|--------|-------------|
| `Authorization` | Bearer token for GitHub OAuth |
| `Content-Type` | JSON API requests |
| `Accept` | Content negotiation |
| `X-Request-ID` | Request correlation (used by request_id middleware) |
| `X-Requested-With` | AJAX detection (defense-in-depth) |

## CSP Middleware

### Interface

```python
# backend/src/middleware/csp.py

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class CSPMiddleware(BaseHTTPMiddleware):
    """Add Content-Security-Policy header to all responses."""

    def __init__(self, app, policy: str | None = None):
        super().__init__(app)
        self.policy = policy or self.default_policy()

    @staticmethod
    def default_policy() -> str:
        return "; ".join([
            "default-src 'self'",
            "script-src 'self'",
            "style-src 'self' 'unsafe-inline'",   # Required for Tailwind
            "img-src 'self' data: https:",         # Avatars from GitHub
            "font-src 'self'",
            "connect-src 'self' wss:",             # WebSocket + API
            "frame-ancestors 'none'",              # Prevent framing
            "base-uri 'self'",                     # Prevent base tag injection
            "form-action 'self'",                  # Restrict form targets
        ])

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        response.headers["Content-Security-Policy"] = self.policy
        return response
```

### Registration

```python
# In main.py, after CORS middleware:
from src.middleware.csp import CSPMiddleware
app.add_middleware(CSPMiddleware)
```

### CSP Directives Rationale

| Directive | Value | Why |
|-----------|-------|-----|
| `default-src` | `'self'` | Restrict all resources to same origin by default |
| `script-src` | `'self'` | Only serve scripts from application origin |
| `style-src` | `'self' 'unsafe-inline'` | Tailwind CSS injects inline styles at runtime |
| `img-src` | `'self' data: https:` | GitHub avatar URLs are external HTTPS; data URIs for inline images |
| `connect-src` | `'self' wss:` | API calls + WebSocket connections |
| `frame-ancestors` | `'none'` | Prevent clickjacking via framing |
| `base-uri` | `'self'` | Prevent base tag hijacking |
| `form-action` | `'self'` | Restrict form submission targets |

## Admin Designation

### Current State (backend/src/dependencies.py)

```python
if admin_user_id is None:
    # Auto-promote first authenticated user
    cursor = await db.execute(
        "UPDATE global_settings SET admin_github_user_id = ? WHERE ...",
        (session.github_user_id,),
    )
```

### Target State

```python
from src.config import get_settings

settings = get_settings()

if admin_user_id is None:
    if settings.admin_github_user_id:
        # Explicit admin designation via environment variable
        if session.github_user_id != settings.admin_github_user_id:
            raise HTTPException(status_code=403, detail="Admin access required")
        # Set the configured user as admin
        await db.execute(
            "UPDATE global_settings SET admin_github_user_id = ? WHERE id = 1",
            (settings.admin_github_user_id,),
        )
        await db.commit()
        return session
    else:
        # Fallback: auto-promote first user (with warning)
        logger.warning(
            "ADMIN_GITHUB_USER_ID not set — auto-promoting first user. "
            "Set ADMIN_GITHUB_USER_ID in environment for production."
        )
        # ... existing auto-promote logic ...
```

### Environment Variable

```text
# .env
ADMIN_GITHUB_USER_ID=12345678  # GitHub user ID (numeric)
```

Added to `config.py` Settings model:
```python
admin_github_user_id: int | None = None
```

## Session Access Control

### Contract

All session-scoped queries MUST include `session_id` in the WHERE clause to enforce user isolation. This is already enforced for chat persistence (see `chat-persistence.md`) and session store.

### Verification Checklist

1. CORS `allow_headers` does not contain `"*"`.
2. Every HTTP response includes `Content-Security-Policy` header.
3. With `ADMIN_GITHUB_USER_ID` set, first user is NOT auto-promoted.
4. Without `ADMIN_GITHUB_USER_ID`, first user IS auto-promoted (backward compatible) with warning log.
5. Chat messages cannot be read cross-session (session_id filter enforced).
