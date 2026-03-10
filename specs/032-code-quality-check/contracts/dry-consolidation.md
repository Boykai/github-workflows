# Contract: DRY Consolidation Patterns

**Phase**: 2 — DRY: Consolidate Duplicated Patterns
**Applies to**: `backend/src/api/`, `backend/src/utils.py`, `backend/src/dependencies.py`, `frontend/src/components/`

## Repository Resolution Contract

### Single Canonical Function

```python
# Location: backend/src/utils.py
async def resolve_repository(access_token: str, project_id: str) -> tuple[str, str]:
    """Resolve repository owner and name using 3-step fallback.
    
    Lookup order:
    1. Project items (GitHub GraphQL API)
    2. Workflow configuration (database)
    3. Default repository (app settings / .env)
    
    Returns: (owner, repo_name) tuple
    Raises: ValidationError if no repository found
    """
```

### Migration Pattern

```python
# BEFORE (non-compliant — workflow.py::_get_repository_info)
def _get_repository_info(session, cache):
    # Sync, cache-only, returns (owner, "")
    ...

# BEFORE (non-compliant — inline resolution in main.py)
# 102-line inline fallback logic
...

# AFTER (compliant — all call sites)
owner, repo = await resolve_repository(session.access_token, project_id)
```

### Affected Files

| File | Current Pattern | Migration |
|------|----------------|-----------|
| `api/workflow.py` | `_get_repository_info()` (lines 89-114) | Delete function, use `resolve_repository()` |
| `api/projects.py` | Already uses `resolve_repository()` | No change needed |
| `api/tasks.py` | Already uses `resolve_repository()` | No change needed |
| `api/chat.py` | Already uses `resolve_repository()` | No change needed |
| `api/chores.py` | Already uses `resolve_repository()` | No change needed |
| `main.py` | Inline 102-line fallback | Replace with `resolve_repository()` call |

## Cached Fetch Helper Contract

### Function Signature

```python
# Location: backend/src/utils.py (or new src/cache_utils.py)
from typing import TypeVar, Callable, Awaitable

T = TypeVar("T")

async def cached_fetch(
    cache_key: str,
    fetch_fn: Callable[..., Awaitable[T]],
    *args: object,
    refresh: bool = False,
    stale_fallback: bool = True,
) -> T:
    """Fetch data with cache-through pattern.
    
    1. If not refresh, check cache for fresh entry
    2. Call fetch_fn(*args) to get fresh data
    3. Cache the result
    4. On fetch error, serve stale cache if stale_fallback=True
    
    Returns: Cached or freshly fetched data
    Raises: Original exception if fetch fails and no stale data available
    """
```

### Usage Pattern

```python
# BEFORE (non-compliant — inline cache pattern in projects.py)
cache_key = get_user_projects_cache_key(session.github_user_id)
if not refresh:
    cached = cache.get(cache_key)
    if cached:
        return ProjectListResponse(projects=cached)
all_projects = await github_projects_service.list_user_projects(...)
cache.set(cache_key, all_projects)
return ProjectListResponse(projects=all_projects)

# AFTER (compliant)
cache_key = get_user_projects_cache_key(session.github_user_id)
projects = await cached_fetch(
    cache_key,
    github_projects_service.list_user_projects,
    session.access_token,
    refresh=refresh,
)
return ProjectListResponse(projects=projects)
```

## Validation Guard Contract

### Guard Function Signature

```python
# Location: backend/src/dependencies.py
def require_selected_project(session: UserSession) -> str:
    """Validate that a project is selected and return its ID.
    
    Returns: The selected project ID string
    Raises: ValidationError with consistent message if no project selected
    """
    if not session.selected_project_id:
        raise ValidationError("No project selected. Please select a project first.")
    return session.selected_project_id
```

### Guard Usage Pattern

```python
# BEFORE (non-compliant — inline check)
if not session.selected_project_id:
    raise ValidationError("Please select a project")  # Inconsistent message

# AFTER (compliant)
project_id = require_selected_project(session)
```

## Frontend Dialog Composition Contract

### Base Pattern: ConfirmationDialog

All modals and dialogs must compose the `ConfirmationDialog` component or follow its accessibility pattern:

```tsx
// Required ARIA attributes
<div role="dialog" aria-modal="true" aria-labelledby={titleId} aria-describedby={descId}>
  {/* Focus trap: Tab cycles within dialog */}
  {/* Escape key: Closes dialog */}
  {/* Backdrop click: Closes dialog */}
</div>
```

### cn() Usage Contract

```tsx
// BEFORE (non-compliant — template literal)
<div className={`flex items-center ${isActive ? 'bg-blue-500' : 'bg-gray-200'}`}>

// AFTER (compliant — cn() utility)
import { cn } from '@/lib/utils';

<div className={cn('flex items-center', isActive ? 'bg-blue-500' : 'bg-gray-200')}>
```

## Compliance Criteria

- [ ] Zero duplicate `resolve_repository()` implementations remain
- [ ] `_get_repository_info()` deleted from `workflow.py`
- [ ] Inline repository resolution removed from `main.py`
- [ ] `cached_fetch()` used by all cache-through endpoints
- [ ] `require_selected_project()` used by all endpoints requiring a selected project
- [ ] All modals compose `ConfirmationDialog` or follow its ARIA pattern
- [ ] All dynamic className constructions use `cn()`
