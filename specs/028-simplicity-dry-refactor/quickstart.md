# Quickstart: Simplicity & DRY Refactoring

**Feature**: 028-simplicity-dry-refactor | **Date**: 2026-03-07

## Prerequisites

- **Python** ≥3.12 (target 3.13)
- **Node.js** ≥20
- **Docker** + Docker Compose (for integration verification)
- Repository cloned and on the `028-simplicity-dry-refactor` branch

## Setup

### Backend

```bash
cd backend
pip install -e ".[dev]"
```

### Frontend

```bash
cd frontend
npm install
```

## Verification Commands

### Backend Tests

```bash
cd backend
python -m pytest tests/ -v              # Full suite (57 unit + 3 integration)
python -m pytest tests/unit/ -v          # Unit tests only
python -m pytest tests/test_api_e2e.py   # E2E tests
```

### Frontend Tests

```bash
cd frontend
npx vitest run                           # All unit tests
npx playwright test                      # E2E tests
```

### Linting

```bash
cd backend && ruff check src/ tests/     # Backend linting
cd frontend && npx eslint src/           # Frontend linting
```

### Integration Verification

```bash
docker compose up                        # Start all services
# Verify: OAuth flow works end-to-end
# Verify: All API endpoints respond correctly
```

---

## Implementation Order

### Phase 1 — Backend Quick Wins (Parallel Tasks)

All Phase 1 steps can be done in parallel as they touch different files with no interdependencies.

**Step 1.1 — Unify Repository Resolution**

Files to modify:
- `backend/src/api/workflow.py` — Delete `_get_repository_info()` (line 86), update callers to use `resolve_repository()`
- `backend/src/api/projects.py` — Update any direct resolution to use `resolve_repository()`
- `backend/src/api/tasks.py` — Update callers
- `backend/src/api/chat.py` — Already uses `resolve_repository()` via wrapper; verify consistency
- `backend/src/api/chores.py` — Update callers
- `backend/tests/unit/test_api_workflow.py` — Update mocks from `_get_repository_info` to `resolve_repository`

Verification: `grep -r "_get_repository_info" backend/` → 0 results

**Step 1.2 — Adopt Error Handling Helpers**

Files to modify:
- `backend/src/api/auth.py` — Replace catch→log→raise blocks with `handle_service_error()`
- `backend/src/api/workflow.py` — Replace generic catch blocks
- `backend/src/api/projects.py` — Replace non-rate-limit error paths
- `backend/src/api/board.py` — Replace catch blocks

Key pattern:
```python
# Before:
except Exception as e:
    logger.exception("Failed to create session: %s", e)
    raise HTTPException(status_code=500, detail="Failed to complete authentication") from e

# After:
from src.logging_utils import handle_service_error
except Exception as e:
    handle_service_error(e, "create session", error_cls=AuthenticationError)
```

**Step 1.3 — Validation Helper**

Files to create:
- `backend/src/dependencies.py` — Add `require_selected_project()` function

Files to modify:
- `backend/src/api/chat.py` — Replace inline guards (L64, L142)
- `backend/src/api/workflow.py` — Replace inline guards (L148, L303, L416+)
- `backend/src/api/tasks.py` — Replace inline guard (L31-32)
- `backend/src/api/chores.py` — Replace inline guards

Key pattern:
```python
# Before:
if not session.selected_project_id:
    raise ValidationError("No project selected")

# After:
from src.dependencies import require_selected_project
project_id = require_selected_project(session)
```

**Step 1.4 — Generic Cache Wrapper**

Files to modify:
- `backend/src/services/cache.py` — Add `cached_fetch()` function

Files to modify (adopt wrapper):
- `backend/src/api/projects.py` — Replace 25-line cache pattern
- `backend/src/api/board.py` — Replace 20-line cache pattern
- `backend/src/api/chat.py` — Replace 10-line cache reads

Key pattern:
```python
# Before:
cache_key = get_user_projects_cache_key(session.github_user_id)
if not refresh:
    cached = cache.get(cache_key)
    if cached:
        return ProjectListResponse(projects=cached)
projects = await github_projects_service.list_user_projects(session.access_token)
cache.set(cache_key, projects)

# After:
from src.services.cache import cached_fetch
projects = await cached_fetch(cache, cache_key, svc.list_user_projects, session.access_token, refresh=refresh)
```

---

### Phase 2 — Service Decomposition (depends on Phase 1)

Files to create (8 new modules):
- `backend/src/services/github_projects/client.py` — HTTP client, GraphQL execution (~400 LOC)
- `backend/src/services/github_projects/projects.py` — Project operations (~600 LOC)
- `backend/src/services/github_projects/issues.py` — Issue CRUD (~700 LOC)
- `backend/src/services/github_projects/pull_requests.py` — PR operations (~500 LOC)
- `backend/src/services/github_projects/copilot.py` — Copilot integration (~500 LOC)
- `backend/src/services/github_projects/fields.py` — Field management (~400 LOC)
- `backend/src/services/github_projects/board.py` — Board views (~500 LOC)
- `backend/src/services/github_projects/repository.py` — Repository/file operations (~700 LOC)

Files to modify:
- `backend/src/services/github_projects/service.py` — Refactor to composition facade
- `backend/src/services/github_projects/__init__.py` — Update re-exports for backward compatibility

Key pattern (composition):
```python
class GitHubProjectsService:
    def __init__(self, client_factory=None):
        self._client = GitHubProjectsClient(client_factory)
        self._projects = ProjectsModule(self._client)
        self._issues = IssuesModule(self._client)
        # ... all 8 modules ...
    
    # Delegate all public methods
    async def create_issue(self, *args, **kwargs):
        return await self._issues.create_issue(*args, **kwargs)
```

Verification: Each new module < 800 lines; all existing tests pass.

---

### Phase 3 — Initialization Consolidation (depends on Phase 2)

Files to modify:
- `backend/src/main.py` — Instantiate all services in `lifespan()`, register on `app.state`
- `backend/src/services/github_projects/service.py` — Remove module-level `github_projects_service = GitHubProjectsService()`
- `backend/src/services/github_auth.py` — Remove module-level `github_auth_service = GitHubAuthService()`
- `backend/src/dependencies.py` — Add `get_github_auth_service()` provider
- `backend/src/services/github_projects/__init__.py` — Update singleton management

Verification: `docker compose up` succeeds; OAuth flow works end-to-end.

---

### Phase 4 — Frontend DRY Consolidation (parallel with Phases 2–3)

**Step 4.1 — CRUD Hook Factory**

Files to create:
- `frontend/src/hooks/useCrudResource.ts` — Generic CRUD hook factory

Files to modify:
- `frontend/src/hooks/useAgents.ts` — Refactor to use factory
- `frontend/src/hooks/useChores.ts` — Refactor to use factory

**Step 4.2 — Settings Hook Unification**

Files to modify:
- `frontend/src/hooks/useSettings.ts` — Extract `useSettingsHook<T>()` generic; refactor user/global/project settings to use it

**Step 4.3 — Shared UI Components**

Files to create:
- `frontend/src/components/common/PreviewCard.tsx`
- `frontend/src/components/common/Modal.tsx`
- `frontend/src/components/common/ErrorAlert.tsx`

**Step 4.4 — Query Key Registry**

Files to create:
- `frontend/src/hooks/queryKeys.ts` — Centralized registry

Files to modify (update imports):
- All hook files that define local `xxxKeys` exports

**Step 4.5 — ChatInterface Split**

Files to create:
- `frontend/src/components/chat/ChatMessageList.tsx`
- `frontend/src/components/chat/ChatInput.tsx`

Files to modify:
- `frontend/src/components/chat/ChatInterface.tsx` — Delegate to sub-components

**Step 4.6 — API Endpoint Factory**

Files to modify:
- `frontend/src/services/api.ts` — Add `createApiGroup()` factory; refactor applicable groups

Verification: `npx vitest run` all green.

---

### Phase 5 — Test Cleanup (depends on Phases 1–3)

Files to modify:
- `backend/tests/conftest.py` — Absorb `make_mock_*` factories from helpers/mocks.py
- `backend/tests/test_api_e2e.py` — Replace inline `patch.object()` with conftest fixtures
- `backend/tests/helpers/mocks.py` — Remove or deprecate

Verification: Full test suite (backend + frontend) passes.

---

## Key Patterns to Follow

### Backend Error Handling Pattern
```python
from src.logging_utils import handle_service_error

try:
    result = await some_service_call()
except AppException:
    raise  # Re-raise structured exceptions as-is
except Exception as e:
    handle_service_error(e, "operation description")
```

### Backend Cache Pattern
```python
from src.services.cache import cached_fetch, cache

result = await cached_fetch(
    cache, cache_key, fetch_function, arg1, arg2,
    refresh=refresh, ttl_seconds=300
)
```

### Frontend CRUD Hook Pattern
```python
import { createCrudResource } from './useCrudResource';
import { queryKeys } from './queryKeys';
import { agentsApi } from '../services/api';

const { useList, useCreate, useUpdate, useDelete } = createCrudResource({
  queryKey: queryKeys.agents,
  api: agentsApi,
  staleTime: STALE_TIME_LONG,
});

// Export with domain-specific names
export const useAgentsList = useList;
export const useCreateAgent = useCreate;
```

### Frontend API Factory Pattern
```typescript
import { createApiGroup } from './api';

export const toolsApi = createApiGroup('/tools', {
  list: { path: '?project_id=:projectId' },
  sync: { method: 'POST', path: '/sync', hasBody: true },
  delete: { method: 'DELETE', path: '/:id' },
});
```

---

## Verification Checklist

- [ ] `grep -r "_get_repository_info" backend/src/` → 0 results
- [ ] `grep -rn "if not session.selected_project_id" backend/src/api/` → only in endpoints that legitimately don't require it
- [ ] `wc -l backend/src/services/github_projects/client.py` → < 800
- [ ] `wc -l backend/src/services/github_projects/projects.py` → < 800
- [ ] `wc -l backend/src/services/github_projects/issues.py` → < 800
- [ ] `wc -l backend/src/services/github_projects/pull_requests.py` → < 800
- [ ] `wc -l backend/src/services/github_projects/copilot.py` → < 800
- [ ] `wc -l backend/src/services/github_projects/fields.py` → < 800
- [ ] `wc -l backend/src/services/github_projects/board.py` → < 800
- [ ] `wc -l backend/src/services/github_projects/repository.py` → < 800
- [ ] `python -m pytest tests/ -v` → all pass
- [ ] `npx vitest run` → all pass
- [ ] `docker compose up` → OAuth flow works
- [ ] `frontend/src/hooks/queryKeys.ts` exists with all 9 key groups
- [ ] `frontend/src/hooks/useCrudResource.ts` exists
- [ ] `frontend/src/components/common/Modal.tsx` exists
- [ ] `frontend/src/components/common/PreviewCard.tsx` exists
- [ ] `frontend/src/components/common/ErrorAlert.tsx` exists
- [ ] `frontend/src/components/chat/ChatMessageList.tsx` exists
- [ ] `frontend/src/components/chat/ChatInput.tsx` exists
