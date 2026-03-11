# Data Model: Security Review Remediation Program

**Branch**: `001-security-review` | **Date**: 2026-03-11

This document defines the new validation models, middleware contracts, and entity modifications introduced by the security remediation. Existing models are extended, not replaced.

## Modified Configuration — Settings Validators

### Production Security Validator

**Location**: `backend/src/config.py` (extend existing `Settings` class)

```python
from pydantic import model_validator
from urllib.parse import urlparse

class Settings(BaseSettings):
    # ... existing fields ...

    @model_validator(mode="after")
    def validate_production_security(self) -> "Settings":
        """Enforce security requirements in non-debug (production) mode.

        Raises ValueError with all violations listed if any check fails.
        """
        if self.debug:
            return self

        violations: list[str] = []

        if not self.encryption_key:
            violations.append(
                "ENCRYPTION_KEY is required in production mode"
            )

        if not self.github_webhook_secret:
            violations.append(
                "GITHUB_WEBHOOK_SECRET is required in production mode"
            )

        if len(self.session_secret_key) < 64:
            violations.append(
                f"SESSION_SECRET_KEY must be at least 64 characters "
                f"(got {len(self.session_secret_key)})"
            )

        if not self.cookie_secure:
            violations.append(
                "COOKIE_SECURE must be True in production mode"
            )

        # Validate CORS origins format
        if self.cors_origins:
            for origin in self.cors_origins.split(","):
                origin = origin.strip()
                if not origin:
                    continue
                parsed = urlparse(origin)
                if parsed.scheme not in ("http", "https"):
                    violations.append(
                        f"CORS origin '{origin}' must have http:// or https:// scheme"
                    )
                if not parsed.hostname:
                    violations.append(
                        f"CORS origin '{origin}' must have a valid hostname"
                    )

        if violations:
            raise ValueError(
                "Production security validation failed:\n"

                + "\n".join(f"  - {v}" for v in violations)
            )

        return self
```

**Used by**: Application startup (automatic via Pydantic instantiation)

---

## New Dependencies

### verify_project_access

**Location**: `backend/src/dependencies.py` (add to existing file)

```python
from fastapi import Depends, HTTPException, status

async def verify_project_access(
    project_id: str,
    session: UserSession = Depends(get_current_session),
) -> str:
    """Verify the authenticated user has access to the specified project.

    Queries the GitHub Projects API using the user's token to confirm
    access. Returns the verified project_id on success.

    Raises:
        HTTPException(403): If the user does not have access to the project.
        HTTPException(401): If no valid session exists.
    """
    # Use the user's GitHub token to verify project access
    github_service = get_github_projects_service()
    try:
        # Attempt to fetch the project — this will fail with 403/404
        # if the user's token doesn't have access
        project = await github_service.get_project(
            project_id, token=session.github_token
        )
        if project is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: you do not have access to this project",
            )
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: you do not have access to this project",
        ) from e

    return project_id
```

**Used by**: `tasks.py`, `projects.py`, `settings.py`, `workflow.py`, WebSocket handlers

---

## New Validation Utilities

### Avatar URL Validator

**Location**: `frontend/src/components/board/IssueCard.tsx` (inline utility or extracted to `lib/`)

```typescript
const ALLOWED_AVATAR_HOSTS = new Set([
  "avatars.githubusercontent.com",
]);

function getValidAvatarUrl(url: string | undefined | null): string | null {
  if (!url) return null;

  try {
    const parsed = new URL(url);
    if (
      parsed.protocol === "https:" &&
      ALLOWED_AVATAR_HOSTS.has(parsed.hostname)
    ) {
      return url;
    }
  } catch {
    // Invalid URL
  }

  return null; // Falls back to placeholder in the component
}
```

**Used by**: `IssueCard.tsx` avatar rendering

### Chat Reference Model

**Location**: `frontend/src/hooks/useChatHistory.ts` (inline type)

```typescript
interface ChatReference {
  /** Message ID from the backend */
  id: string;
  /** Conversation this message belongs to */
  conversationId: string;
  /** Timestamp when this reference was stored (ms since epoch) */
  storedAt: number;
}

const CHAT_REFERENCE_TTL_MS = 24 * 60 * 60 * 1000; // 24 hours

function isExpired(ref: ChatReference): boolean {
  return Date.now() - ref.storedAt > CHAT_REFERENCE_TTL_MS;
}

function clearChatStorage(): void {
  const keys = Object.keys(localStorage);
  for (const key of keys) {
    if (key.startsWith("chat-") || key.startsWith("conversation-")) {
      localStorage.removeItem(key);
    }
  }
}
```

**Used by**: `useChatHistory.ts` for localStorage management

---

## Modified Entities

### Authentication Session (Cookie-Based)

**Location**: `backend/src/api/auth.py`

**Before**:

```python
# OAuth callback redirects with token in URL
return RedirectResponse(
    url=f"{settings.frontend_url}?session_token={session_token}"
)
```

**After**:

```python
# OAuth callback sets HttpOnly cookie and redirects clean
response = RedirectResponse(url=settings.frontend_url)
response.set_cookie(
    key="session_token",
    value=session_token,
    httponly=True,
    samesite="strict",
    secure=settings.cookie_secure,
    max_age=settings.cookie_max_age,
    path="/",
)
return response
```

**Impact**: Frontend `useAuth.ts` removes URL parameter reading; browser sends cookie automatically.

### Encryption Service (Production-Mandatory)

**Location**: `backend/src/services/encryption.py`

**Before**: Optional encryption — logs warning and passes through plaintext when `encryption_key` is absent.

**After**: Encryption is mandatory in production. The passthrough path remains only for `debug=True` mode to support local development without encryption setup.

### Rate Limiter Configuration

**Location**: `backend/src/main.py` (initialization)

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

def get_rate_limit_key(request: Request) -> str:
    """Rate limit key: session ID for authenticated, IP for anonymous."""
    session_token = request.cookies.get("session_token")
    if session_token:
        return f"user:{session_token[:16]}"  # Truncated for privacy
    return get_remote_address(request)

limiter = Limiter(key_func=get_rate_limit_key)
```

**Used by**: Decorated endpoints in `chat.py`, `agents.py`, `workflow.py`, `auth.py`

---

## Migration

### 021_encrypt_existing.sql

**Location**: `backend/src/migrations/021_encrypt_existing.sql`

**Purpose**: Document the migration path for existing plaintext credentials. This migration:

1. Adds a `encryption_status` column to track migration state
2. Marks existing rows as `pending_migration`
3. A startup task encrypts pending rows using the now-mandatory encryption key

```sql
-- Migration 021: Track encryption status for credential migration
-- Existing plaintext credentials must be encrypted after ENCRYPTION_KEY is set

ALTER TABLE sessions ADD COLUMN encryption_status TEXT DEFAULT 'encrypted';

-- Mark any existing rows that may have been stored without encryption
-- The application startup task will re-encrypt these rows
UPDATE sessions SET encryption_status = 'pending_migration'
WHERE encryption_status IS NULL OR encryption_status = '';
```

**Note**: The actual re-encryption happens in Python code during startup, not in SQL. The SQL migration only adds the tracking column.

---

## State Transitions

### Session Authentication Flow (After Remediation)

```text
[User clicks Login]
    → Browser redirects to GitHub OAuth
    → GitHub redirects to /api/v1/auth/github/callback
    → Backend validates OAuth code, creates session
    → Backend sets HttpOnly cookie on response
    → Backend returns 302 redirect to frontend (clean URL)
    → Browser stores cookie automatically
    → Frontend loads, cookie sent on all API requests
    → Frontend checks /api/v1/auth/me to verify session
```

### Startup Validation Flow

```text
[Application starts]
    → Pydantic Settings instantiated from environment
    → model_validator runs production security checks
    → IF debug=True: skip checks, log warnings for missing values
    → IF debug=False AND any violation: raise ValueError, refuse to start
    → IF all checks pass: continue to FastAPI app initialization
```

### Project Authorization Flow

```text
[API request with project_id]
    → FastAPI resolves dependencies
    → get_current_session() validates auth cookie
    → verify_project_access() checks ownership via GitHub API
    → IF access denied: return 403 before endpoint body executes
    → IF access granted: endpoint receives verified project_id
```
