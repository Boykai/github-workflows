# Research: Simplicity & DRY Refactoring Plan (5 Phases)

**Feature**: `028-simplicity-dry-refactor` | **Date**: 2026-03-07

---

## R1: Repository Resolution — Current Duplication Map

**Decision**: Replace all duplicate implementations with the canonical `resolve_repository()` in `utils.py:145-186`.

**Rationale**: The existing `resolve_repository()` already implements the correct 3-step fallback strategy (project items → workflow config → default repo). The duplicate implementations are either incomplete subsets of this logic or diverge in error handling, creating inconsistency. Centralizing on the canonical version ensures uniform behavior and a single place to fix bugs.

**Current Duplicates Found**:

| Location | Pattern | Lines | Notes |
|----------|---------|-------|-------|
| `utils.py:145-186` | Canonical 3-step fallback | 42 | **Keep — this is the target** |
| `workflow.py:83-111` | `_get_repository_info()` — parses project URL from cache | 29 | Incomplete: no workflow-config or default-repo fallback |
| `main.py:~38-140` | Inline 3-step fallback during polling auto-start | ~100 | Duplicates canonical logic with polling-specific branches |
| `projects.py` | Inline repo resolution in project endpoint handlers | ~15 | Subset of canonical logic |
| `tasks.py` | Inline repo resolution in task endpoint handlers | ~15 | Subset of canonical logic |
| `chat.py` | Inline repo resolution in chat endpoint handlers | ~15 | Subset of canonical logic |
| `chores.py` | Inline repo resolution in chore endpoint handlers | ~15 | Subset of canonical logic |

**Alternatives Considered**:
- **Per-module wrappers** that call `resolve_repository` internally — rejected because it adds indirection without benefit; direct call is simpler.
- **Middleware-based resolution** — rejected because not all routes need repository context; would add unnecessary overhead.

---

## R2: Error Handling — Existing Helpers Usage Audit

**Decision**: Wire up `handle_service_error()` and `safe_error_response()` from `logging_utils.py:215-276` into endpoint handlers, replacing hand-rolled try/catch boilerplate.

**Rationale**: Both helpers already exist and are fully implemented but have zero callers. They provide: (1) server-side logging with full traceback, (2) user-safe error messages that don't leak internals, and (3) structured exception raising via `AppException` subclasses. The existing boilerplate in endpoints re-implements this pattern inconsistently — some log but don't raise structured exceptions, others raise but don't log.

**Current Boilerplate Locations**:

| File | Approximate Instances | Pattern |
|------|----------------------|---------|
| `board.py` | 3+ | `try: ... except Exception as e: logger.error(...); raise HTTPException(...)` |
| `workflow.py` | 4+ | Similar, sometimes with `JSONResponse` instead of `HTTPException` |
| `projects.py` | 3+ | Mix of `HTTPException` and `JSONResponse` error returns |
| `auth.py` | 2+ | Catch-log-raise with generic messages |

**Alternatives Considered**:
- **FastAPI exception handler middleware** — rejected because the existing `AppException` handler in `main.py:362-435` already catches structured exceptions; the gap is in endpoint-level code that doesn't raise `AppException`.
- **Decorator-based error handling** — rejected; adds magic and hides control flow. Explicit `handle_service_error()` calls are more readable.

---

## R3: Session Validation — Inline Guard Clause Audit

**Decision**: Create `require_selected_project(session) -> str` in `dependencies.py` that raises `HTTPException(400)` if `session.selected_project_id` is not set.

**Rationale**: Five endpoint files repeat the same guard clause: check if `session.selected_project_id` is truthy, raise 400 if not. This is a classic FastAPI dependency — a function that validates request state and returns the validated value or raises.

**Current Guard Clause Locations**:

| File | Pattern |
|------|---------|
| `chat.py` | `if not session.selected_project_id: raise HTTPException(400, ...)` |
| `workflow.py` | Same pattern |
| `tasks.py` | Same pattern |
| `chores.py` | Same pattern |
| `board.py` | Same pattern (some variants) |

**Signature**:
```python
def require_selected_project(session: UserSession) -> str:
    """Return selected_project_id or raise HTTP 400."""
    if not session.selected_project_id:
        raise HTTPException(status_code=400, detail="No project selected")
    return session.selected_project_id
```

**Alternatives Considered**:
- **FastAPI `Depends()` chain** — could be used as `project_id: str = Depends(require_selected_project)` but requires refactoring endpoint signatures. Simpler to start as a plain helper call; can evolve to `Depends()` later.
- **Pydantic validator on `UserSession`** — rejected because `selected_project_id` being None is valid application state (user hasn't selected a project yet); validation belongs at the endpoint level.

---

## R4: Cache Wrapper — Verbose Pattern Consolidation

**Decision**: Add `cached_fetch(cache_key, fetch_fn, refresh, *args)` to `cache.py` (or as a method on `InMemoryCache`) that encapsulates the check/get/set pattern.

**Rationale**: Three files (`projects.py`, `board.py`, `chat.py`) contain nearly identical 8-12 line blocks: check if cache has key, return cached value if not refreshing, call fetch function, store result, return result. A generic wrapper reduces each call site to one line.

**Pattern Being Replaced** (composite from multiple files):
```python
cache_key = get_xxx_cache_key(identifier)
if not refresh:
    cached = cache.get(cache_key)
    if cached is not None:
        return cached
result = await actual_fetch_function(args...)
cache.set(cache_key, result, ttl_seconds=TTL)
return result
```

**Proposed Wrapper**:
```python
async def cached_fetch(
    cache: InMemoryCache,
    key: str,
    fetch_fn: Callable[..., Awaitable[T]],
    *args: Any,
    refresh: bool = False,
    ttl_seconds: int = 300,
) -> T:
    if not refresh:
        cached = cache.get(key)
        if cached is not None:
            return cached
    result = await fetch_fn(*args)
    cache.set(key, result, ttl_seconds=ttl_seconds)
    return result
```

**Alternatives Considered**:
- **Decorator-based caching** (e.g., `@cached(ttl=300)`) — rejected because the cache key and refresh flag come from endpoint parameters, not function arguments; a decorator can't easily capture these.
- **Class method on `InMemoryCache`** — viable but `cached_fetch` as a standalone async function is simpler and doesn't require changing the class interface.

---

## R5: Service Decomposition — Module Boundary Design

**Decision**: Decompose `service.py` (4,937 LOC, 79 methods) into 8 focused modules using composition over inheritance, with a backward-compatible facade via `__init__.py` re-exports.

**Rationale**: The monolith groups unrelated concerns (HTTP infrastructure, project queries, issue CRUD, PR operations, Copilot management, field mutations, board queries, repository operations) into a single class. Developers modifying one concern must navigate 4,937 lines. Decomposition into focused modules under 800 LOC each reduces cognitive load and merge conflicts.

**Module Boundaries** (determined by method grouping analysis):

| Module | Methods (approx.) | Dependencies | ~LOC |
|--------|-------------------|-------------|------|
| `client.py` | `__init__`, `_request_with_retry`, `_graphql`, `_rest`, `_rest_response`, `rest_request`, `_with_fallback`, rate-limit tracking, request coalescing | `githubkit`, `httpx` | ~600 |
| `projects.py` | `list_user_projects`, `list_org_projects`, `_parse_projects`, `list_board_projects` | `client.py` | ~500 |
| `issues.py` | `create_issue`, `update_issue_body`, `update_issue_state`, `add_issue_to_project`, `_verify_item_on_project`, `create_draft_item`, completion detection | `client.py`, `fields.py` | ~600 |
| `pull_requests.py` | PR CRUD, merge, review methods | `client.py` | ~500 |
| `copilot.py` | Copilot assignment, bot ID detection, `is_copilot_author`, `is_copilot_swe_agent` | `client.py` | ~400 |
| `fields.py` | Field queries & mutations (status, iteration, custom fields) | `client.py` | ~300 |
| `board.py` | `get_board_data`, `_reconcile_board_items`, board queries | `client.py`, `fields.py` | ~400 |
| `repository.py` | Repo info, branch/commit workflow, `get_repository_info` | `client.py` | ~300 |

**Composition Pattern**:
```python
# Each module receives client as constructor parameter
class IssueService:
    def __init__(self, client: GitHubClient) -> None:
        self._client = client
```

**Facade Pattern** (in `__init__.py`):
```python
# Backward-compatible re-exports
from src.services.github_projects.client import GitHubClient
from src.services.github_projects.issues import IssueService
# ... etc.
# Composite facade class that delegates to sub-services
class GitHubProjectsService:
    def __init__(self, access_token: str) -> None:
        self.client = GitHubClient(access_token)
        self.issues = IssueService(self.client)
        # ... etc.
```

**Alternatives Considered**:
- **Inheritance hierarchy** (e.g., `IssueService(GitHubClient)`) — rejected because it couples concerns; a change to `GitHubClient` API affects all subclasses.
- **Mixin approach** — rejected because Python mixins create fragile MRO chains and make it hard to reason about which methods come from where.
- **Functional decomposition** (standalone functions instead of classes) — rejected because methods share state (access token, rate-limit tracking, request coalescing cache) that a class naturally encapsulates.

---

## R6: Initialization Pattern — Consolidation Strategy

**Decision**: Consolidate all service instantiation into `lifespan()` → `app.state` → `Depends(get_xxx_service)` in `dependencies.py`. Remove module-level globals and lazy singletons.

**Rationale**: Three competing patterns exist:
1. **`lifespan()` + `app.state`** (in `main.py:304-308`) — the correct pattern for FastAPI apps.
2. **Module-level globals** (e.g., `github_projects_service = GitHubProjectsService(...)` in `service.py`) — creates import-order dependencies and makes testing harder.
3. **Lazy singletons** (e.g., `_instance = None; def get_instance(): ...`) — adds complexity without benefit since `lifespan()` already handles initialization.

The `lifespan()` pattern is the FastAPI-recommended approach and is already partially in use. Consolidating to it alone simplifies the initialization graph and eliminates subtle bugs from competing patterns.

**Migration Steps**:
1. Ensure all services are created in `lifespan()` and stored on `app.state`.
2. Ensure `dependencies.py` getters read from `app.state` (already partly done).
3. Remove module-level `github_projects_service` singleton from `service.py` / `__init__.py`.
4. Update 17+ import sites to use dependency injection instead of direct import.

**Alternatives Considered**:
- **Keep module-level globals for testing convenience** — rejected; test `conftest.py` already overrides dependencies via FastAPI's `app.dependency_overrides`, so module-level globals are unnecessary.
- **Dependency injection container** (e.g., `python-inject`, `dependency-injector`) — rejected; FastAPI's built-in `Depends()` is sufficient and avoids adding a new library.

---

## R7: Frontend CRUD Hook Factory — Design Pattern

**Decision**: Create a generic `useCrudResource<T>` hook factory in `hooks/useCrudResource.ts` that encapsulates list/create/update/delete operations with consistent React Query patterns.

**Rationale**: `useAgents.ts` (90 lines) and `useChores.ts` (120 lines) implement nearly identical patterns: query keys factory, list query, and create/update/delete mutations with cache invalidation. The 3 settings hooks in `useSettings.ts` follow the same query+mutation pattern. A generic factory can reduce each to ~15-20 lines of configuration.

**Factory Interface**:
```typescript
interface CrudResourceConfig<T, CreateInput, UpdateInput> {
  resourceKey: string;
  endpoints: {
    list: (projectId: string) => Promise<T[]>;
    create?: (projectId: string, input: CreateInput) => Promise<T>;
    update?: (projectId: string, id: string, input: UpdateInput) => Promise<T>;
    delete?: (projectId: string, id: string) => Promise<void>;
  };
  staleTime?: number;
}

function useCrudResource<T, C, U>(
  config: CrudResourceConfig<T, C, U>,
  projectId: string | undefined,
): CrudResourceResult<T, C, U>;
```

**Alternatives Considered**:
- **Higher-order hook** (e.g., `createUseResource(config)` returning a hook function) — viable but less idiomatic in React; direct hook with config parameter is simpler.
- **Code generation from OpenAPI spec** — deferred per scope exclusions; the manual factory approach works without adding tooling dependencies.

---

## R8: Frontend Shared UI Components — Consolidation Strategy

**Decision**: Create three shared components: `PreviewCard.tsx`, `Modal.tsx`, and `ErrorAlert.tsx`.

**Rationale**:
- **PreviewCard**: `TaskPreview` (40 LOC), `StatusChangePreview` (50 LOC), and `IssueRecommendationPreview` (268 LOC) share a common structure — title, content area, and confirm/cancel buttons. A shared `PreviewCard` can encapsulate the card layout while each preview provides its specific content via props/children.
- **Modal**: 5+ modal components each implement escape-key handling, backdrop click, and body overflow management independently. A shared `Modal` component eliminates ~30 lines of boilerplate per modal.
- **ErrorAlert**: Error display patterns are repeated across components with minor variations in styling. A shared component ensures consistent UX.

**PreviewCard Interface**:
```typescript
interface PreviewCardProps {
  title: string;
  onConfirm: () => void;
  onCancel: () => void;
  confirmLabel?: string;
  cancelLabel?: string;
  isLoading?: boolean;
  error?: string | null;
  children: React.ReactNode;
}
```

**Modal Interface**:
```typescript
interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  children: React.ReactNode;
  size?: 'sm' | 'md' | 'lg';
}
```

**Alternatives Considered**:
- **Radix UI Dialog** — already a project dependency; could be used as the base for `Modal`. This is complementary, not competing — `Modal` wraps Radix primitives with project-specific conventions (escape, backdrop, overflow).
- **Headless UI approach** — rejected for PreviewCard because the components are simple enough that a concrete component with slots (children) is more appropriate than a headless pattern.

---

## R9: Query Key Centralization Strategy

**Decision**: Create `hooks/queryKeys.ts` as a single registry exporting all query key factories. Migrate scattered key definitions from individual hook files.

**Rationale**: Query keys are currently defined in 8+ separate hook files (some as exported factories like `agentKeys`, some as inline arrays like `['chat', 'messages']`). This makes it impossible to see all cache relationships at a glance and risks key collisions. A central registry provides a single source of truth.

**Registry Structure**:
```typescript
// hooks/queryKeys.ts
export const queryKeys = {
  agents: {
    all: ['agents'] as const,
    list: (projectId: string) => [...queryKeys.agents.all, 'list', projectId] as const,
    pending: (projectId: string) => [...queryKeys.agents.all, 'pending', projectId] as const,
  },
  chores: { /* ... */ },
  settings: { /* ... */ },
  projects: { /* ... */ },
  board: { /* ... */ },
  chat: { /* ... */ },
  workflow: { /* ... */ },
  // ... all other keys
} as const;
```

**Migration Strategy**: Update one hook file at a time, importing from the registry. Existing exports (e.g., `agentKeys`) become re-exports from the registry for backward compatibility.

**Alternatives Considered**:
- **Co-located keys with re-export barrel** — keeps keys in their hook files but re-exports from a barrel file. Rejected because it doesn't prevent inline key definitions and adds indirection without centralization benefit.
- **Enum-based keys** — rejected because query keys need to be arrays (React Query requirement), and enums add type complexity without benefit.

---

## R10: ChatInterface Split Strategy

**Decision**: Extract `ChatMessageList.tsx` and `ChatInput.tsx` from the 417-line `ChatInterface.tsx`.

**Rationale**: `ChatInterface.tsx` combines three distinct concerns: (1) message rendering with auto-scroll, (2) input handling with command autocomplete and history, and (3) proposal/preview management. Splitting the first two into dedicated components reduces the main component to orchestration logic (~150 lines), making each piece independently testable and easier to modify.

**Component Boundaries**:

| Component | Responsibility | ~LOC |
|-----------|---------------|------|
| `ChatMessageList.tsx` | Message rendering, auto-scroll, retry button, proposal/preview rendering | ~150 |
| `ChatInput.tsx` | Text input, command autocomplete, history navigation (↑/↓), send handling | ~120 |
| `ChatInterface.tsx` (remaining) | Orchestration: passes state between list and input, manages proposals | ~150 |

**Alternatives Considered**:
- **Three-way split** (also extracting proposal management into `ChatProposals.tsx`) — considered but deferred; the two-way split delivers most of the benefit with lower risk.
- **Custom hook extraction** instead of component split — rejected because the complexity is in the JSX rendering, not the state logic.

---

## R11: Test Mock Consolidation Strategy

**Decision**: Remove `tests/helpers/mocks.py` and consolidate all mock factories into `conftest.py` as pytest fixtures.

**Rationale**: The existing `conftest.py` (8.9K, 11 fixtures) already provides the canonical mock pattern. The separate `tests/helpers/mocks.py` file creates a competing factory location, leading to inconsistency when developers aren't sure which to use. Inline patches in `test_api_e2e.py` further fragment the pattern. Consolidating everything into `conftest.py` fixtures creates a single, discoverable source for test mocks.

**Migration Steps**:
1. Move unique factories from `tests/helpers/mocks.py` to `conftest.py`.
2. Replace inline patches in `test_api_e2e.py` with `conftest` fixtures.
3. Delete `tests/helpers/mocks.py`.
4. Verify all tests pass.

**Alternatives Considered**:
- **Keep `tests/helpers/` as a factory module, just remove duplicates** — rejected because pytest fixture discovery from `conftest.py` is the idiomatic pattern and provides automatic scope management.
- **Factory library** (e.g., `factory_boy`) — rejected; the existing fixtures are simple enough that a library adds unnecessary complexity.

---

## R12: Circular Import Prevention During Decomposition

**Decision**: Enforce a strict dependency DAG between decomposed modules. Use `ruff` and `import-linter` (or manual `grep`) to detect circular imports after each extraction.

**Rationale**: When splitting a monolith, circular imports are the most common failure mode. The dependency graph must be: `client.py` ← `{projects, issues, pull_requests, copilot, fields, repository}` ← `board.py` (board depends on fields). No module should import from the facade `__init__.py`.

**Dependency DAG**:
```
client.py (base — no internal imports)
    ├── projects.py
    ├── issues.py → fields.py
    ├── pull_requests.py
    ├── copilot.py
    ├── fields.py
    ├── board.py → fields.py
    └── repository.py
```

**Detection**: After each module extraction, run:
```bash
ruff check --select I  # import sorting/issues
python -c "import src.services.github_projects"  # smoke test
```

**Alternatives Considered**:
- **`import-linter` package** — provides declarative import rules but adds a dev dependency. Deferred; manual verification is sufficient for a one-time decomposition.
- **Lazy imports** to break cycles — rejected as a workaround; the proper solution is correct module boundaries.
