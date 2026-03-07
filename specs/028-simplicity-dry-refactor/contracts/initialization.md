# Contract: Initialization Consolidation

**Feature**: `028-simplicity-dry-refactor` | **Phase**: 3

---

## Target Architecture

All service instantiation happens in a single location: the `lifespan()` context manager in `main.py`. Services are stored on `app.state` and accessed via dependency injection through `dependencies.py`.

```
lifespan() [main.py]
    │
    ├── Creates GitHubClientFactory
    ├── Creates GitHubProjectsService (facade)
    ├── Creates ConnectionManager
    ├── Creates database connection
    │
    └── Stores all on app.state
            │
            └── dependencies.py getters
                    │
                    ├── get_github_service(request) → GitHubProjectsService
                    ├── get_connection_manager(request) → ConnectionManager
                    ├── get_database(request) → aiosqlite.Connection
                    └── get_session_dep() → UserSession
```

---

## Eliminated Patterns

### Pattern 1: Module-Level Singleton

**Current** (in `service.py` / `__init__.py`):
```python
# Module-level instantiation — runs at import time
github_projects_service = GitHubProjectsService(...)
```

**After**: Removed. `GitHubProjectsService` is only instantiated in `lifespan()`.

### Pattern 2: Lazy Singleton

**Current** (various files):
```python
_instance = None
def get_instance():
    global _instance
    if _instance is None:
        _instance = SomeService(...)
    return _instance
```

**After**: Removed. All such patterns replaced with `app.state` access.

### Pattern 3: Direct Import

**Current** (17+ files):
```python
from src.services.github_projects import github_projects_service
```

**After**: Replaced with dependency injection:
```python
from src.dependencies import get_github_service
# In endpoint:
async def endpoint(service = Depends(get_github_service)):
    ...
```

---

## Dependencies.py Updates

### New/Updated Getters

```python
def get_github_service(request: Request) -> GitHubProjectsService:
    """Get GitHub service from app.state."""
    return request.app.state.github_service

def get_client_factory(request: Request) -> GitHubClientFactory:
    """Get client factory from app.state."""
    return request.app.state.client_factory

def get_connection_manager(request: Request) -> ConnectionManager:
    """Get WebSocket connection manager from app.state."""
    return request.app.state.connection_manager

def get_database(request: Request) -> aiosqlite.Connection:
    """Get database connection from app.state."""
    return request.app.state.db
```

### Test Support

Tests continue to use `app.dependency_overrides` (already in `conftest.py`):
```python
app.dependency_overrides[get_github_service] = lambda: mock_github_service
```

---

## Validation

| Check | Method |
|-------|--------|
| No module-level service instantiation | `grep -rn "= GitHubProjectsService(" backend/src/` returns only `lifespan()` |
| No direct singleton imports | `grep -rn "from.*import github_projects_service" backend/src/api/` returns zero hits |
| App starts successfully | `docker compose up` → health check passes |
| Auth flow works | OAuth login completes end-to-end |
| All tests pass | `pytest` green |
