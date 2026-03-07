# Data Model: Security, Privacy & Vulnerability Audit

**Feature Branch**: `026-security-review`

## Entities

### 1. Session (modified)

The existing `UserSession` model is modified to remove URL-based token delivery. Session credentials are now exclusively delivered via HttpOnly cookies.

**Current fields** (no schema change):
| Field | Type | Description |
|-------|------|-------------|
| session_id | UUID | Primary key, stored in HttpOnly cookie |
| github_user_id | int | GitHub user numeric ID |
| github_login | str | GitHub username |
| access_token | str | Encrypted GitHub OAuth token |
| selected_project_id | str \| None | Currently selected project |
| created_at | datetime | Session creation timestamp |
| expires_at | datetime | Session expiration (8h default) |

**Behavioral changes**:
- Session cookie attributes: `HttpOnly=True`, `SameSite=Strict` (changed from `Lax`), `Secure=True` (mandatory in non-debug)
- Session token is never placed in URL parameters
- `POST /session?session_token=...` endpoint removed

### 2. Project Authorization (new concept, no new table)

Project access is validated against the user's GitHub project membership. No new database table is needed — authorization is checked by querying the user's project list via the GitHub Projects V2 API (already cached in-memory).

**Authorization model**:
| Check | Source | Result |
|-------|--------|--------|
| User owns project | `github_projects_service.list_projects(access_token)` | project_id in user's project list |
| Access denied | project_id not in list | HTTP 403 Forbidden |
| WebSocket denied | project_id not in list | Close code 4403 |

**Centralized dependency** (`verify_project_access`):
```python
async def verify_project_access(
    session: UserSession,
    project_id: str,
) -> str:
    """Verify user has access to the specified project. Returns project_id if authorized."""
    # Raises HTTPException(403) if not authorized
```

### 3. Rate Limit State (new, in-memory)

Rate limit state is tracked in-memory by slowapi. No database table needed for single-instance deployment.

| Attribute | Type | Description |
|-----------|------|-------------|
| key | str | User ID (per-user) or IP address (per-IP) |
| endpoint_group | str | Rate limit category (chat, agents, workflow, oauth) |
| request_count | int | Number of requests in current window |
| window_start | datetime | Start of current rate limit window |
| limit | str | Rate expression (e.g., "10/minute", "5/minute") |

**Rate limit categories**:
| Category | Key Type | Limit | Endpoints |
|----------|----------|-------|-----------|
| AI/Chat | per-user | 10/minute | `POST /api/v1/chat/*` |
| Agent | per-user | 5/minute | `POST /api/v1/agents/*` |
| Workflow | per-user | 10/minute | `POST /api/v1/workflow/*` |
| OAuth | per-IP | 20/minute | `GET /api/v1/auth/callback` |

### 4. Chat Message Reference (modified behavior)

The frontend `useChatHistory` hook changes from storing full message content to storing lightweight references.

**Current storage** (localStorage):
```json
["full message text 1", "full message text 2", ...]
```

**New storage** (localStorage):
```json
{
  "entries": ["input text 1", "input text 2"],
  "expiresAt": 1709856000000
}
```

**Behavioral changes**:
- TTL-based expiration (24 hours default)
- All entries cleared on logout via `localStorage.removeItem()`
- Note: This hook stores *user input history* (shell-like up/down navigation), not full conversation transcripts. The content is user-typed input, not AI responses or sensitive data. The main security improvement is adding TTL and logout clearing.

### 5. Application Configuration (modified)

New and modified configuration fields in `Settings` (Pydantic BaseSettings):

| Field | Type | Default | Validation |
|-------|------|---------|------------|
| encryption_key | str \| None | None | **Required** in non-debug mode |
| github_webhook_secret | str \| None | None | **Required** in non-debug mode |
| session_secret_key | str | (required) | **Min 64 chars** in non-debug mode |
| cookie_secure | bool | False | **Must be True** (effective) in non-debug mode |
| enable_docs | bool | False | **New** — independent of DEBUG |
| cors_origins | str | "http://localhost:5173" | **Validated** — each origin must have scheme + hostname |
| database_path | str | "/var/lib/ghchat/data/settings.db" | **Changed** — outside app root |

**Startup validation** (non-debug mode):
1. `ENCRYPTION_KEY` must be set → fail with clear error
2. `GITHUB_WEBHOOK_SECRET` must be set → fail with clear error
3. `SESSION_SECRET_KEY` must be ≥64 characters → fail with clear error
4. `effective_cookie_secure` must be True → fail with clear error
5. Each `cors_origins` entry must be valid URL → fail with clear error

## State Transitions

### OAuth Login Flow (modified)

```
User clicks Login
  → Backend generates OAuth URL (scopes: "read:user read:org project")
  → User authorizes on GitHub
  → GitHub redirects to backend /auth/callback?code=...&state=...
  → Backend exchanges code for token, creates session
  → Backend sets HttpOnly/SameSite=Strict/Secure cookie on response
  → Backend redirects to frontend /auth/callback (NO credentials in URL)
  → Frontend /auth/callback calls GET /api/v1/auth/me (cookie sent automatically)
  → Frontend receives user data, updates auth state
```

### Application Startup (modified)

```
Load configuration from environment
  → Validate ENCRYPTION_KEY (required if non-debug)
  → Validate GITHUB_WEBHOOK_SECRET (required if non-debug)
  → Validate SESSION_SECRET_KEY length ≥ 64 (non-debug)
  → Validate effective_cookie_secure = True (non-debug)
  → Validate CORS origins format
  → Create database directory with 0700 permissions
  → Create/open database file with 0600 permissions
  → Run migrations
  → Start FastAPI app
```

## Validation Rules

| Rule | Field/Entity | Condition |
|------|-------------|-----------|
| Required in production | ENCRYPTION_KEY | `not debug and not encryption_key` → startup error |
| Required in production | GITHUB_WEBHOOK_SECRET | `not debug and not github_webhook_secret` → startup error |
| Minimum entropy | SESSION_SECRET_KEY | `not debug and len(key) < 64` → startup error |
| Secure cookies | effective_cookie_secure | `not debug and not secure` → startup error |
| Valid URL format | CORS origins | Each origin parsed with scheme + hostname |
| Project ownership | project_id parameter | User's project list must contain project_id |
| Avatar URL safety | avatar_url | Must be `https:` from `avatars.githubusercontent.com` |
| Constant-time | Secret comparisons | All use `hmac.compare_digest()` |
