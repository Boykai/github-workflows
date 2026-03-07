# Data Model: Simplicity & DRY Refactoring Across Backend and Frontend

**Feature**: 028-simplicity-dry-refactor | **Date**: 2026-03-07

## Overview

This refactoring does not introduce new database tables or persistent entities. All changes are structural: consolidating code patterns, decomposing modules, and extracting shared abstractions. This document defines the interfaces, type contracts, and module boundaries that emerge from the refactoring.

---

## Backend Entities

### Shared Helper Signatures

These are new or modified function signatures in the backend that replace duplicated patterns.

#### `require_selected_project` (dependencies.py)

```python
def require_selected_project(session: UserSession) -> str:
    """
    Validate that the user has a project selected in their session.
    
    Args:
        session: The current user session from authentication.
    
    Returns:
        The selected project ID string.
    
    Raises:
        ValidationError: If no project is selected.
    """
```

**Usage**: Replaces 12 inline guard clauses across `chat.py`, `workflow.py`, `tasks.py`, `chores.py`.

#### `cached_fetch` (services/cache.py)

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
    """
    Fetch data with cache-first strategy and optional stale fallback.
    
    Args:
        cache: The InMemoryCache instance.
        cache_key: Cache key string.
        fetch_fn: Async callable to fetch fresh data.
        *args: Positional arguments forwarded to fetch_fn.
        refresh: If True, skip cache and fetch fresh data.
        ttl_seconds: Time-to-live for the cache entry.
        use_stale_on_error: If True, return stale data on fetch failure.
        **kwargs: Keyword arguments forwarded to fetch_fn.
    
    Returns:
        The cached or freshly fetched data.
    
    Raises:
        Exception: Re-raised from fetch_fn if fetch fails and no stale data available.
    """
```

**Usage**: Replaces verbose cache check/get/set patterns in `projects.py`, `board.py`, `chat.py`.

#### `handle_service_error` (logging_utils.py — existing)

```python
def handle_service_error(
    exc: Exception,
    operation: str,
    error_cls: type[AppException] | None = None,
) -> NoReturn:
    """
    Log exception details and raise a structured AppException.
    
    Already implemented at logging_utils.py:241.
    No signature changes needed — only adoption across API modules.
    """
```

#### `safe_error_response` (logging_utils.py — existing)

```python
def safe_error_response(exc: Exception, operation: str) -> str:
    """
    Log exception and return a generic user-safe error message.
    
    Already implemented at logging_utils.py:215.
    No signature changes needed — only adoption across API modules.
    """
```

#### `resolve_repository` (utils.py — existing, canonical)

```python
async def resolve_repository(
    access_token: str,
    project_id: str,
) -> tuple[str, str]:
    """
    Resolve repository owner and name for a GitHub Project.
    3-step fallback: project items → workflow config → default repository.
    
    Already implemented at utils.py:145-187.
    No signature changes needed — only adoption by all callers.
    """
```

---

### Decomposed Service Module Interfaces

Each module receives a `client` reference (the HTTP/GraphQL executor) via its constructor.

#### Base Pattern

```python
class ServiceModule:
    """Base pattern for all decomposed service modules."""
    
    def __init__(self, client: "GitHubProjectsClient") -> None:
        self._client = client
```

#### Module: `client.py` (~400 LOC)

```python
class GitHubProjectsClient:
    """HTTP client, GraphQL execution, rate limiting, cycle cache."""
    
    def __init__(self, client_factory: GitHubClientFactory | None = None) -> None: ...
    async def close(self) -> None: ...
    
    # HTTP methods
    async def rest_request(self, method: str, url: str, ...) -> Any: ...
    async def _rest(self, access_token: str, method: str, url: str, ...) -> Any: ...
    async def _rest_response(self, access_token: str, method: str, url: str, ...) -> httpx.Response: ...
    
    # GraphQL
    async def _graphql(self, access_token: str, query: str, variables: dict) -> dict: ...
    
    # Resilience
    async def _with_fallback(self, primary_fn, fallback_fn, *args) -> Any: ...
    
    # Rate limiting
    def get_last_rate_limit(self) -> dict | None: ...
    def clear_last_rate_limit(self) -> None: ...
    
    # Cycle cache
    def clear_cycle_cache(self) -> None: ...
    def _invalidate_cycle_cache(self) -> None: ...
```

#### Module: `projects.py` (~600 LOC)

```python
class ProjectsModule:
    """Project listing, field options, item management."""
    
    async def list_user_projects(self, access_token: str) -> list[dict]: ...
    async def list_org_projects(self, access_token: str, org: str) -> list[dict]: ...
    async def get_project_items(self, access_token: str, project_id: str, ...) -> list[dict]: ...
    async def get_project_field_options(self, access_token: str, project_id: str, field_name: str) -> list[str]: ...
    async def update_project_item_field(self, access_token: str, project_id: str, item_id: str, ...) -> dict: ...
    async def move_project_item(self, access_token: str, project_id: str, item_id: str, ...) -> dict: ...
    async def get_project_repository(self, access_token: str, project_id: str) -> tuple[str, str]: ...
```

#### Module: `issues.py` (~700 LOC)

```python
class IssuesModule:
    """Issue CRUD, labels, comments, timeline."""
    
    async def create_issue(self, access_token: str, owner: str, repo: str, ...) -> dict: ...
    async def update_issue(self, access_token: str, owner: str, repo: str, issue_number: int, ...) -> dict: ...
    async def get_issue_details(self, access_token: str, owner: str, repo: str, issue_number: int) -> dict: ...
    async def add_issue_to_project(self, access_token: str, project_id: str, content_id: str) -> str: ...
    async def remove_issue_from_project(self, access_token: str, project_id: str, item_id: str) -> None: ...
    async def close_issue(self, access_token: str, owner: str, repo: str, issue_number: int) -> dict: ...
    async def reopen_issue(self, access_token: str, owner: str, repo: str, issue_number: int) -> dict: ...
    async def add_labels_to_issue(self, access_token: str, owner: str, repo: str, ...) -> dict: ...
    async def list_issue_comments(self, access_token: str, owner: str, repo: str, issue_number: int) -> list[dict]: ...
    async def create_issue_comment(self, access_token: str, owner: str, repo: str, ...) -> dict: ...
```

#### Module: `pull_requests.py` (~500 LOC)

```python
class PullRequestsModule:
    """Pull request operations."""
    
    async def list_pull_requests(self, access_token: str, owner: str, repo: str, ...) -> list[dict]: ...
    async def get_pull_request(self, access_token: str, owner: str, repo: str, pr_number: int) -> dict: ...
    async def create_pull_request(self, access_token: str, owner: str, repo: str, ...) -> dict: ...
    async def merge_pull_request(self, access_token: str, owner: str, repo: str, pr_number: int, ...) -> dict: ...
    async def list_pr_reviews(self, access_token: str, owner: str, repo: str, pr_number: int) -> list[dict]: ...
    async def list_pr_files(self, access_token: str, owner: str, repo: str, pr_number: int) -> list[dict]: ...
```

#### Module: `copilot.py` (~500 LOC)

```python
class CopilotModule:
    """Copilot/AI agent operations and detection."""
    
    @staticmethod
    def is_copilot_author(login: str) -> bool: ...
    @staticmethod
    def is_copilot_swe_agent(login: str) -> bool: ...
    async def list_available_agents(self, access_token: str) -> list[dict]: ...
    async def get_copilot_metrics(self, access_token: str) -> dict: ...
```

#### Module: `fields.py` (~400 LOC)

```python
class FieldsModule:
    """Project field management."""
    
    async def get_project_fields(self, access_token: str, project_id: str) -> list[dict]: ...
    async def get_field_values(self, access_token: str, project_id: str, field_id: str) -> list[str]: ...
    async def update_field_value(self, access_token: str, project_id: str, ...) -> dict: ...
    async def create_field(self, access_token: str, project_id: str, ...) -> dict: ...
    async def delete_field(self, access_token: str, project_id: str, field_id: str) -> None: ...
```

#### Module: `board.py` (~500 LOC)

```python
class BoardModule:
    """Board data and view transformations."""
    
    async def get_board_data(self, access_token: str, project_id: str, ...) -> dict: ...
    async def get_board_columns(self, access_token: str, project_id: str) -> list[dict]: ...
    async def get_board_items(self, access_token: str, project_id: str, ...) -> list[dict]: ...
    async def list_board_projects(self, access_token: str) -> list[dict]: ...
```

#### Module: `repository.py` (~700 LOC)

```python
class RepositoryModule:
    """Repository and file operations, branching, commits."""
    
    async def get_repository_info(self, access_token: str, owner: str, repo: str) -> dict: ...
    async def get_directory_contents(self, access_token: str, owner: str, repo: str, path: str) -> list[dict]: ...
    async def get_file_content(self, access_token: str, owner: str, repo: str, path: str) -> str: ...
    async def get_file_content_from_ref(self, access_token: str, owner: str, repo: str, path: str, ref: str) -> str: ...
    async def create_branch(self, access_token: str, owner: str, repo: str, ...) -> dict: ...
    async def get_branch_head_oid(self, access_token: str, owner: str, repo: str, branch: str) -> str: ...
    async def commit_files(self, access_token: str, owner: str, repo: str, ...) -> dict: ...
```

#### Composition Root: `GitHubProjectsService` (facade)

```python
class GitHubProjectsService:
    """
    Backward-compatible facade composing all service modules.
    
    All methods delegate to the appropriate module.
    Existing callers continue to use this class unchanged.
    """
    
    def __init__(self, client_factory: GitHubClientFactory | None = None) -> None:
        self._client = GitHubProjectsClient(client_factory)
        self._projects = ProjectsModule(self._client)
        self._issues = IssuesModule(self._client)
        self._pull_requests = PullRequestsModule(self._client)
        self._copilot = CopilotModule(self._client)
        self._fields = FieldsModule(self._client)
        self._board = BoardModule(self._client)
        self._repository = RepositoryModule(self._client)
    
    # All 79 public methods delegate to the appropriate module
    # e.g.:
    async def create_issue(self, *args, **kwargs):
        return await self._issues.create_issue(*args, **kwargs)
```

---

## Frontend Types

### CRUD Hook Factory Types

```typescript
// hooks/useCrudResource.ts

interface CrudResourceConfig<T, CreateInput, UpdateInput> {
  /** Base query key for this resource (e.g., ['agents']) */
  queryKey: readonly string[];
  
  /** API methods for CRUD operations */
  api: {
    list: (projectId: string) => Promise<T[]>;
    create?: (projectId: string, data: CreateInput) => Promise<T>;
    update?: (projectId: string, id: string, data: UpdateInput) => Promise<T>;
    delete?: (projectId: string, id: string) => Promise<void>;
  };
  
  /** Stale time for list queries (default: STALE_TIME_LONG) */
  staleTime?: number;
  
  /** Additional query keys to invalidate on mutation success */
  invalidateKeys?: readonly string[][];
}

interface CrudResourceHooks<T, CreateInput, UpdateInput> {
  useList: (projectId: string | undefined) => UseQueryResult<T[]>;
  useCreate: () => UseMutationResult<T, Error, { projectId: string; data: CreateInput }>;
  useUpdate: () => UseMutationResult<T, Error, { projectId: string; id: string; data: UpdateInput }>;
  useDelete: () => UseMutationResult<void, Error, { projectId: string; id: string }>;
}

function createCrudResource<T, CreateInput = Partial<T>, UpdateInput = Partial<T>>(
  config: CrudResourceConfig<T, CreateInput, UpdateInput>
): CrudResourceHooks<T, CreateInput, UpdateInput>;
```

### Query Key Registry Types

```typescript
// hooks/queryKeys.ts

export const queryKeys = {
  agents: {
    all: ['agents'] as const,
    list: (projectId?: string) => [...queryKeys.agents.all, 'list', projectId] as const,
    pending: (projectId?: string) => [...queryKeys.agents.all, 'pending', projectId] as const,
  },
  agentTools: {
    all: ['agent-tools'] as const,
    list: (agentId?: string) => [...queryKeys.agentTools.all, 'list', agentId] as const,
  },
  chores: {
    all: ['chores'] as const,
    list: (projectId?: string) => [...queryKeys.chores.all, 'list', projectId] as const,
    templates: (projectId?: string) => [...queryKeys.chores.all, 'templates', projectId] as const,
  },
  settings: {
    user: ['settings', 'user'] as const,
    global: ['settings', 'global'] as const,
    project: (projectId?: string) => ['settings', 'project', projectId] as const,
    models: (provider?: string) => ['settings', 'models', provider] as const,
  },
  signal: {
    connection: ['signal', 'connection'] as const,
    linkStatus: ['signal', 'linkStatus'] as const,
    preferences: ['signal', 'preferences'] as const,
    banners: ['signal', 'banners'] as const,
  },
  mcp: {
    all: ['mcp'] as const,
    list: ['mcp', 'list'] as const,
  },
  models: {
    all: ['models'] as const,
    available: ['models', 'available'] as const,
  },
  pipelines: {
    all: ['pipelines'] as const,
    list: ['pipelines', 'list'] as const,
    detail: (id?: string) => ['pipelines', 'detail', id] as const,
  },
  tools: {
    all: ['tools'] as const,
    list: (projectId?: string) => ['tools', 'list', projectId] as const,
  },
} as const;
```

### Settings Hook Factory Types

```typescript
// hooks/useSettings.ts (generic extraction)

interface SettingsHookConfig<T> {
  /** API method to fetch settings */
  apiGet: (...args: any[]) => Promise<T>;
  
  /** API method to update settings */
  apiUpdate: (...args: any[]) => Promise<T>;
  
  /** Query key for caching */
  queryKey: readonly unknown[];
  
  /** Whether the query is enabled (default: true) */
  enabled?: boolean;
  
  /** Stale time override */
  staleTime?: number;
}

interface SettingsHookResult<T> {
  data: T | undefined;
  isLoading: boolean;
  error: Error | null;
  update: UseMutationResult<T, Error, Partial<T>>;
}

function useSettingsHook<T>(config: SettingsHookConfig<T>): SettingsHookResult<T>;
```

### API Endpoint Factory Types

```typescript
// services/api.ts

interface ApiMethodConfig {
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH';
  path?: string;  // relative to basePath, supports :id interpolation
  body?: boolean;  // whether the method accepts a request body
}

interface ApiGroupConfig {
  [methodName: string]: ApiMethodConfig | ((...args: any[]) => Promise<any>);
}

function createApiGroup<T extends Record<string, (...args: any[]) => Promise<any>>>(
  basePath: string,
  methods: { [K in keyof T]: ApiMethodConfig },
): T;
```

### Shared UI Component Props

```typescript
// components/common/Modal.tsx
interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  description?: string;
  children: React.ReactNode;
  footer?: React.ReactNode;
  className?: string;
}

// components/common/PreviewCard.tsx
interface PreviewCardProps {
  title: string;
  children: React.ReactNode;
  onConfirm?: () => void;
  onReject?: () => void;
  confirmLabel?: string;
  rejectLabel?: string;
  isLoading?: boolean;
  variant?: 'default' | 'warning' | 'success';
  className?: string;
}

// components/common/ErrorAlert.tsx
interface ErrorAlertProps {
  error: Error | string | null;
  title?: string;
  onDismiss?: () => void;
  className?: string;
}
```

### ChatInterface Decomposition Types

```typescript
// components/chat/ChatMessageList.tsx
interface ChatMessageListProps {
  messages: ChatMessage[];
  pendingProposals: Map<string, AITaskProposal>;
  pendingStatusChanges: Map<string, StatusChangeProposal>;
  pendingRecommendations: Map<string, IssueCreateActionData>;
  onConfirmProposal: (id: string) => void;
  onRejectProposal: (id: string) => void;
  onConfirmStatusChange: (id: string) => void;
  onConfirmRecommendation: (id: string) => void;
  onRejectRecommendation: (id: string) => void;
  onRetryMessage: (id: string) => void;
}

// components/chat/ChatInput.tsx
interface ChatInputProps {
  onSendMessage: (message: string) => void;
  isSending: boolean;
  onNewChat: () => void;
}
```

---

## State Transitions

### Service Initialization Lifecycle (Post-Consolidation)

```
Application Start
    │
    ▼
lifespan() called
    │
    ├── init_database() → app.state.db
    ├── seed_global_settings()
    ├── GitHubProjectsService() → app.state.github_service
    ├── ConnectionManager() → app.state.connection_manager
    ├── GitHubAuthService() → app.state.github_auth_service
    └── start background tasks (polling, signal, watchdog)
    │
    ▼
Application Ready (yield)
    │
    ├── Request arrives
    │   ├── Depends(get_github_service) → app.state.github_service
    │   ├── Depends(get_connection_manager) → app.state.connection_manager
    │   └── Depends(require_selected_project) → validated project_id
    │
    ▼
Application Shutdown (finally)
    │
    ├── cancel background tasks
    ├── close services
    └── close database
```

### Migration Window (Facade Pattern)

```
During Migration:
    │
    ├── Old code: `from src.services.github_projects import github_projects_service`
    │   └── __init__.py → re-exports the same instance registered on app.state
    │
    ├── New code: `Depends(get_github_service)`
    │   └── dependencies.py → returns app.state.github_service
    │
    └── Both resolve to the SAME instance
    
Post-Migration:
    │
    ├── All API code uses Depends(get_github_service)
    ├── Background tasks receive service via app reference
    └── Module-level singleton removed from service.py
```

---

## Validation Rules

### `require_selected_project`
- Input: `session.selected_project_id`
- Valid: non-None, non-empty string
- Invalid: None or empty string → raises `ValidationError("No project selected. Please select a project first.")`

### `cached_fetch`
- `cache_key`: non-empty string
- `fetch_fn`: must be awaitable
- `ttl_seconds`: positive integer
- `refresh=True`: bypasses cache read, still writes to cache
- On fetch error with `use_stale_on_error=True`: returns stale data if available, otherwise re-raises

### Service Module Decomposition
- Each module MUST be <800 LOC (per SC-002)
- Each module MUST receive client via constructor (composition, not inheritance)
- All public method signatures MUST remain unchanged in the facade
- `__init__.py` MUST re-export all symbols that were previously public
