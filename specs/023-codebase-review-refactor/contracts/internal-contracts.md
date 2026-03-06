# Internal Contracts: Full Codebase Review & Refactoring

**Branch**: `023-codebase-review-refactor` | **Date**: 2026-03-06

## Overview

This feature does not change any external API contracts. All HTTP endpoints, WebSocket messages, and response shapes remain identical. These contracts document the **internal interfaces** between decomposed service modules.

## Contract 1: GitHubClient Interface

The shared HTTP infrastructure that all sub-services depend on.

```python
class GitHubClient:
    """Shared HTTP client infrastructure for GitHub API access."""

    # Construction
    def __init__(self, client_factory: GitHubClientFactory | None = None): ...

    # Lifecycle
    async def close(self) -> None: ...

    # REST API
    async def rest(self, access_token: str, method: str, path: str, **kwargs) -> dict: ...
    async def rest_response(self, access_token: str, method: str, path: str, **kwargs) -> httpx.Response: ...
    async def rest_request(self, access_token: str, method: str, path: str) -> dict: ...

    # GraphQL API
    async def graphql(self, access_token: str, query: str, variables: dict | None = None) -> dict: ...

    # Rate Limit
    def get_last_rate_limit(self) -> dict | None: ...
    def clear_last_rate_limit(self) -> None: ...

    # Cycle Cache
    def clear_cycle_cache(self) -> None: ...
    async def cycle_cached(self, key: str, fetch: Callable[[], Awaitable[T]]) -> T: ...

    # Fallback (defined but currently unused — remove during decomposition)
    # async def _with_fallback(...) → REMOVED
```

**Invariants**:
- Rate limit headers extracted from every REST response automatically
- Cycle cache cleared between polling cycles via `clear_cycle_cache()`
- All REST/GraphQL methods accept `access_token` as first parameter

## Contract 2: Sub-Service Constructor Pattern

Every sub-service follows this constructor contract:

```python
class XxxService:
    def __init__(self, client: GitHubClient):
        self._client = client
```

**Invariants**:
- Sub-services are stateless except for the shared `GitHubClient` reference
- Sub-services do NOT create their own HTTP clients
- Sub-services access cycle cache through `self._client.cycle_cached()`

## Contract 3: Facade Delegation Pattern

The facade preserves the existing `GitHubProjectsService` public interface:

```python
class GitHubProjectsService:
    def __init__(self, client_factory: GitHubClientFactory | None = None):
        self._client = GitHubClient(client_factory)
        self._projects = ProjectsService(self._client)
        self._board = BoardService(self._client)
        self._issues = IssuesService(self._client)
        # ... etc

    # Every existing public method delegates to the appropriate sub-service:
    async def list_user_projects(self, access_token, username, limit=100):
        return await self._projects.list_user_projects(access_token, username, limit)

    # Static methods remain on the facade:
    @staticmethod
    def is_copilot_author(login: str) -> bool:
        return CopilotService.is_copilot_author(login)
```

**Invariants**:
- Every public method that existed before decomposition continues to exist on the facade
- Method signatures are identical — no parameter changes
- Return types are identical — no response shape changes
- The `__init__.py` re-exports `GitHubProjectsService` so `from src.services.github_projects import GitHubProjectsService` works unchanged

## Contract 4: Error Handling Helper Interface

```python
# In logging_utils.py (existing, to be adopted)

def handle_service_error(
    exc: Exception,
    operation: str,
    error_cls: type[Exception] = HTTPException
) -> None:
    """Log error with structured context and raise appropriate exception.
    
    Args:
        exc: The caught exception
        operation: Human-readable description of what was being attempted
        error_cls: Exception class to raise (default: HTTPException)
    """
    ...

def safe_error_response(
    exc: Exception,
    operation: str
) -> dict:
    """Return safe error dict without exposing internals.
    
    Args:
        exc: The caught exception
        operation: Human-readable description of what was being attempted
    Returns:
        dict with 'error' and 'detail' keys
    """
    ...
```

**Adoption pattern in API endpoints**:
```python
# Before (inline):
try:
    result = await service.do_thing(token, ...)
except HTTPException:
    raise
except Exception as e:
    logger.error(f"Failed to do thing: {e}")
    raise HTTPException(status_code=500, detail=str(e))

# After (shared helper):
try:
    result = await service.do_thing(token, ...)
except HTTPException:
    raise
except Exception as e:
    handle_service_error(e, "do thing")
```

## Contract 5: Validation Dependency Interface

```python
# In dependencies.py (new)

async def require_selected_project(
    session: UserSession = Depends(get_session)
) -> str:
    """Validate that a project is selected and return the project_id.
    
    Raises:
        HTTPException(400): If no project is selected
    Returns:
        The selected project_id string
    """
    if not session.selected_project_id:
        raise HTTPException(status_code=400, detail="No project selected")
    return session.selected_project_id
```

**Usage in endpoints**:
```python
# Before (inline):
@router.post("/chat")
async def send_chat(session: UserSession = Depends(get_session)):
    if not session.selected_project_id:
        raise HTTPException(status_code=400, detail="No project selected")
    project_id = session.selected_project_id
    ...

# After (dependency):
@router.post("/chat")
async def send_chat(
    project_id: str = Depends(require_selected_project),
    session: UserSession = Depends(get_session)
):
    ...
```

## Contract 6: Module Re-export Contract

The `__init__.py` file must re-export all public symbols:

```python
# backend/src/services/github_projects/__init__.py

from src.services.github_projects.service import GitHubProjectsService
from src.services.github_projects.client import GitHubClient, GitHubClientFactory

__all__ = [
    "GitHubProjectsService",
    "GitHubClient", 
    "GitHubClientFactory",
]
```

**Invariant**: Any import that worked before decomposition must continue to work after. No external file needs to change its import path.
