# API Contracts: Simplicity & DRY Refactoring

**Feature**: 028-simplicity-dry-refactor | **Date**: 2026-03-07

## Overview

This refactoring does not introduce new REST API endpoints. All changes are internal: shared helper adoption, service decomposition, and initialization consolidation. The external API surface remains identical. This document defines the internal contracts between backend modules.

---

## Backend Helper Contracts

### 1. `require_selected_project` — Validation Dependency

**Location**: `backend/src/dependencies.py`

**Contract**:
```python
def require_selected_project(session: UserSession) -> str:
```

| Aspect | Detail |
|--------|--------|
| Input | `UserSession` (from `Depends(get_session)`) |
| Output | `str` — the validated project ID |
| Error | `ValidationError("No project selected. Please select a project first.")` |
| HTTP Status | 400 (via ValidationError handler) |

**Adoption Sites**:
| File | Current Pattern | New Pattern |
|------|----------------|-------------|
| `api/chat.py` L64, L142 | `if not session.selected_project_id: raise ...` | `project_id = require_selected_project(session)` |
| `api/workflow.py` L148, L303, L416+ | `if not session.selected_project_id: raise ...` | `project_id = require_selected_project(session)` |
| `api/tasks.py` L31-32 | `if not project_id: if not session...: raise ...` | `project_id = project_id or require_selected_project(session)` |
| `api/chores.py` | `if not session.selected_project_id: raise ...` | `project_id = require_selected_project(session)` |

---

### 2. `cached_fetch` — Cache Wrapper

**Location**: `backend/src/services/cache.py`

**Contract**:
```python
async def cached_fetch(
    cache: InMemoryCache,
    cache_key: str,
    fetch_fn: Callable[..., Awaitable[T]],
    *args: Any,
    refresh: bool = False,
    ttl_seconds: int = 300,
    use_stale_on_error: bool = True,
    **kwargs: Any,
) -> T:
```

| Aspect | Detail |
|--------|--------|
| Cache Hit (no refresh) | Returns cached value immediately |
| Cache Miss or Refresh | Calls `fetch_fn(*args, **kwargs)`, stores result, returns it |
| Fetch Error + Stale Available | Returns stale data, logs warning |
| Fetch Error + No Stale | Re-raises the original exception |

**Adoption Sites**:
| File | Current Pattern (lines saved) | New Pattern |
|------|-------------------------------|-------------|
| `api/projects.py` L114-198 | 25-line check/get/set with stale fallback | `await cached_fetch(cache, key, svc.list_user_projects, token, refresh=refresh)` |
| `api/board.py` L205-260 | 20-line check/get/set pattern | `await cached_fetch(cache, key, svc.list_board_projects, token, refresh=refresh)` |
| `api/chat.py` L161-185 | 10-line cache read for projects and tasks | `await cached_fetch(cache, key, svc.get_project_items, ...)` |

---

### 3. `handle_service_error` — Error Handler (Existing)

**Location**: `backend/src/logging_utils.py` L241

**Contract** (unchanged):
```python
def handle_service_error(
    exc: Exception,
    operation: str,
    error_cls: type[AppException] | None = None,
) -> NoReturn:
```

| Aspect | Detail |
|--------|--------|
| Logging | `logger.exception(f"Error in {operation}: {exc}")` |
| Raises | `error_cls(message=safe_error_response(exc, operation))` or `GitHubAPIError` by default |

**Adoption Sites**:
| File | Current Pattern | Lines Saved |
|------|----------------|-------------|
| `api/auth.py` L149-160 | `except Exception: logger.exception(...); raise HTTPException(...)` | ~8 lines per catch block |
| `api/workflow.py` L249-259 | `except Exception: logger.error(...); return WorkflowResult(...)` | ~6 lines per catch block |
| `api/board.py` | `except Exception: logger.exception(...); raise` | ~4 lines per catch block |
| `api/projects.py` | Generic error path (not rate-limit) | ~6 lines |

---

## Dependency Injection Contracts

### Service Registration (lifespan)

**Location**: `backend/src/main.py` — `lifespan()` function

```python
@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None]:
    # ... existing initialization ...
    
    # Service registration (consolidated)
    _app.state.github_service = GitHubProjectsService()
    _app.state.connection_manager = ConnectionManager()
    _app.state.github_auth_service = GitHubAuthService()
    
    yield
    
    # ... existing cleanup ...
```

### Dependency Providers (dependencies.py)

| Provider | Returns | Fallback |
|----------|---------|----------|
| `get_github_service(request)` | `GitHubProjectsService` | Module-level import (during migration only) |
| `get_connection_manager(request)` | `ConnectionManager` | Module-level import |
| `get_github_auth_service(request)` | `GitHubAuthService` | **NEW** — Module-level import |
| `require_selected_project(session)` | `str` | N/A — raises on invalid |

---

## Service Module Contracts

### Module Boundaries

Each decomposed module MUST:
1. Accept a `GitHubProjectsClient` instance via constructor
2. Contain fewer than 800 lines of code
3. Have no direct imports from other service modules (communicate via client only)
4. Preserve exact method signatures from the original monolith

### Facade Contract (`__init__.py`)

```python
# backend/src/services/github_projects/__init__.py

from src.services.github_projects.client import GitHubClientFactory, GitHubProjectsClient
from src.services.github_projects.service import GitHubProjectsService

# Re-export for backward compatibility
# All existing `from src.services.github_projects import X` continues to work
__all__ = [
    "GitHubClientFactory",
    "GitHubProjectsClient", 
    "GitHubProjectsService",
]
```

**Migration-period compatibility**: During the transition window, the module-level `github_projects_service` singleton is created in `__init__.py` and registered on `app.state` during lifespan. Both import paths resolve to the same instance.

---

## Test Consolidation Contracts

### conftest.py Fixture Contracts

**New fixtures** (moved from `tests/helpers/mocks.py`):

```python
@pytest.fixture
def mock_github_service_factory(**overrides) -> AsyncMock:
    """Configurable GitHubProjectsService mock with sensible defaults."""

@pytest.fixture
def mock_github_auth_service_factory(**overrides) -> AsyncMock:
    """Configurable GitHubAuthService mock."""

@pytest.fixture
def mock_ai_agent_service_factory(**overrides) -> AsyncMock:
    """Configurable AIAgentService mock."""

@pytest.fixture
def mock_websocket_manager_factory(**overrides) -> AsyncMock:
    """Configurable ConnectionManager mock."""

@pytest.fixture
def mock_db_connection() -> AsyncMock:
    """In-memory database connection mock with cursor support."""
```

**Deprecation**: `tests/helpers/mocks.py` factory functions are replaced by conftest fixtures. The file is removed or emptied with a deprecation comment.
