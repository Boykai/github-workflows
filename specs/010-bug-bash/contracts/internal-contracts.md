# Internal Contracts: Module Boundaries & Shared Utilities

**Date**: 2026-02-24 | **Branch**: `010-bug-bash`

This document defines the internal service-layer contracts that change as part of the bug bash.

---

## 1. Encryption Service (`backend/src/services/encryption.py`) — NEW

```python
"""Fernet-based encryption for sensitive token storage."""

class EncryptionService:
    """Singleton-safe utility; initialized at app startup."""

    def __init__(self, key: str | None):
        """
        Args:
            key: Base64-encoded 32-byte Fernet key from ENCRYPTION_KEY env var.
                 If None, operates in passthrough mode with a logged warning.
        """

    def encrypt(self, plaintext: str) -> str:
        """Encrypt plaintext → Fernet token string (URL-safe base64).
        In passthrough mode, returns plaintext unchanged.
        """

    def decrypt(self, ciphertext: str) -> str:
        """Decrypt Fernet token string → plaintext.
        Handles both encrypted and legacy plaintext values gracefully.
        Raises ValueError only on corrupted ciphertext (not legacy plaintext).
        """

    @property
    def enabled(self) -> bool:
        """True if a valid key was provided."""
```

**Usage contract**:
- Injected via FastAPI `Depends()` — never import the instance directly.
- `session_store.py` calls `encrypt()` on token write, `decrypt()` on token read.
- Must handle legacy (pre-encryption) plaintext gracefully on read.

---

## 2. Request-ID Middleware (`backend/src/middleware/request_id.py`) — NEW

```python
"""ASGI middleware that assigns/propagates X-Request-ID."""

# ContextVar accessible from any async handler
request_id_var: contextvars.ContextVar[str]

class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    - Reads X-Request-ID from incoming request headers.
    - If absent, generates uuid4().hex.
    - Sets request_id_var ContextVar for the duration of the request.
    - Adds X-Request-ID to the response headers.
    """
```

**Usage contract**:
- Added as middleware in `main.py` startup.
- Handlers and services read `request_id_var.get()` for logging/correlation.

---

## 3. Bounded Collections (`backend/src/utils.py`) — MODIFIED

```python
class BoundedSet(set):
    """Set with a maximum capacity. Evicts oldest entries via insertion order."""
    def __init__(self, maxlen: int): ...
    def add(self, item) -> None: ...

class BoundedDict(dict):
    """Dict with a maximum capacity. Evicts oldest entries (FIFO)."""
    def __init__(self, maxlen: int): ...
    def __setitem__(self, key, value) -> None: ...
```

**Usage contract**:
- `github_auth.py`: `_oauth_states` becomes `BoundedDict(maxlen=1000)` with expiry.
- `copilot_polling/state.py`: Replace bare `set()` and `dict()` globals.

---

## 4. Repository Resolution (`backend/src/utils.py`) — EXISTING

```python
def resolve_repository(
    repo_full_name: str | None,
    settings: "Settings"
) -> str:
    """
    Returns repo_full_name if provided, else falls back to
    settings.github_repo. Raises ValueError if neither is set.
    """
```

**Usage contract**:
- All route handlers (`workflow.py`, `projects.py`, `board.py`) MUST call this
  function instead of inline fallback logic.
- The 4+ inline duplications in `workflow.py` and others are replaced by single calls.

---

## 5. GitHub Header Builder (`backend/src/services/github_projects/service.py`) — MODIFIED

```python
def _build_headers(self, *, accept: str = "application/vnd.github.v3+json") -> dict:
    """
    Build standard GitHub API headers:
      Authorization: Bearer {self.token}
      Accept: {accept}
      X-Request-ID: {request_id_var.get("")}

    Single source of truth — replaces 10+ inline header dicts.
    """
```

**Usage contract**:
- All methods in `GitHubProjectsService` call `_build_headers()` instead of
  constructing header dictionaries inline.

---

## 6. PR Filtering (`backend/src/services/github_projects/service.py`) — MODIFIED

```python
def _filter_pull_requests(self, items: list[dict]) -> list[dict]:
    """
    Filter out items that represent pull requests.
    Centralizes the 3 duplicated filtering patterns.
    
    An item is a PR if it has a non-null 'pull_request' field
    or its 'type' == 'PullRequest'.
    """
```

**Usage contract**:
- Replaces 3 separate inline PR filter implementations.

---

## 7. Session Store (`backend/src/services/session_store.py`) — MODIFIED

**Change**: Token fields encrypted at rest.

```python
class SessionStore:
    async def create_session(
        self,
        github_user_id: str,
        github_username: str,
        access_token: str,    # plaintext in, encrypted at storage
        refresh_token: str,   # plaintext in, encrypted at storage
    ) -> str: ...

    async def get_session(self, session_id: str) -> dict | None:
        """Returns dict with plaintext tokens (decrypted on read)."""
```

**Behavior contract**:
- Tokens are Fernet-encrypted before INSERT/UPDATE.
- Tokens are Fernet-decrypted on SELECT (with legacy plaintext fallback).
- `EncryptionService` is injected at `SessionStore` construction.

---

## 8. Admin Authorization (`backend/src/dependencies.py`) — MODIFIED

```python
async def require_admin(session: dict = Depends(get_session)) -> dict:
    """
    Dependency that verifies the current session belongs to the admin user.
    
    Checks session's github_user_id against global_settings.admin_github_user_id.
    If no admin is set yet (first user), auto-promotes and persists.
    
    Raises HTTPException(403) if user is not admin.
    Returns the session dict if authorized.
    """
```

**Usage contract**:
- Applied to `PUT /api/v1/settings/global` and other admin-only routes.
- Uses the `admin_github_user_id` column added by Migration 003.
