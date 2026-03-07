# Contract: Service Decomposition Modules

**Feature**: `028-simplicity-dry-refactor` | **Phase**: 2

---

## Module Structure

All modules live under `backend/src/services/github_projects/`:

```
backend/src/services/github_projects/
├── __init__.py          # Facade: GitHubProjectsService + re-exports
├── client.py            # GitHubClient (HTTP infrastructure)
├── projects.py          # ProjectService
├── issues.py            # IssueService
├── pull_requests.py     # PullRequestService
├── copilot.py           # CopilotService
├── fields.py            # FieldService
├── board.py             # BoardService
├── repository.py        # RepositoryService
└── service.py           # REMOVED after decomposition
```

---

## 1. `GitHubClient` — HTTP Infrastructure

**File**: `client.py` | **Max LOC**: 600

### Public Interface

```python
class GitHubClient:
    def __init__(self, access_token: str, client_factory: GitHubClientFactory) -> None: ...
    async def graphql(self, query: str, variables: dict | None = None) -> dict: ...
    async def rest(self, method: str, path: str, **kwargs) -> dict: ...
    async def rest_response(self, method: str, path: str, **kwargs) -> httpx.Response: ...
    async def rest_request(self, method: str, url: str, **kwargs) -> dict: ...
    def get_last_rate_limit(self) -> dict | None: ...
    def clear_last_rate_limit(self) -> None: ...
    async def close(self) -> None: ...
```

### Internal Methods (Extracted from service.py)

- `_request_with_retry` — retry logic with exponential backoff
- `_graphql` — raw GraphQL execution
- `_rest` — raw REST execution
- `_rest_response` — REST with full response object
- `_with_fallback` — REST fallback chain
- Rate-limit tracking and request coalescing

### Dependencies

- `githubkit` (external)
- `httpx` (external)
- No internal module dependencies

---

## 2. `ProjectService`

**File**: `projects.py` | **Max LOC**: 500

### Public Interface

```python
class ProjectService:
    def __init__(self, client: GitHubClient) -> None: ...
    async def list_user_projects(self, login: str) -> list[Project]: ...
    async def list_org_projects(self, org: str) -> list[Project]: ...
    async def list_board_projects(self, login: str) -> list[Project]: ...
```

### Internal Methods

- `_parse_projects` — transforms GraphQL response to `Project` models

### Dependencies

- `GitHubClient`

---

## 3. `IssueService`

**File**: `issues.py` | **Max LOC**: 600

### Public Interface

```python
class IssueService:
    def __init__(self, client: GitHubClient, fields: FieldService) -> None: ...
    async def create_issue(self, owner: str, repo: str, title: str, body: str, ...) -> dict: ...
    async def update_issue_body(self, owner: str, repo: str, issue_number: int, body: str) -> dict: ...
    async def update_issue_state(self, owner: str, repo: str, issue_number: int, state: str) -> dict: ...
    async def add_issue_to_project(self, project_id: str, content_id: str) -> dict: ...
    async def create_draft_item(self, project_id: str, title: str, body: str) -> dict: ...
    # completion detection methods
```

### Dependencies

- `GitHubClient`
- `FieldService` (for setting fields on created/updated issues)

---

## 4. `PullRequestService`

**File**: `pull_requests.py` | **Max LOC**: 500

### Public Interface

```python
class PullRequestService:
    def __init__(self, client: GitHubClient) -> None: ...
    async def create_pull_request(self, owner: str, repo: str, ...) -> dict: ...
    async def merge_pull_request(self, owner: str, repo: str, pr_number: int, ...) -> dict: ...
    async def get_pull_request_reviews(self, owner: str, repo: str, pr_number: int) -> list: ...
    # other PR operations
```

### Dependencies

- `GitHubClient`

---

## 5. `CopilotService`

**File**: `copilot.py` | **Max LOC**: 400

### Public Interface

```python
class CopilotService:
    def __init__(self, client: GitHubClient) -> None: ...
    async def assign_copilot(self, owner: str, repo: str, issue_number: int) -> dict: ...
    async def get_copilot_bot_id(self) -> str | None: ...
    def is_copilot_author(self, author_login: str) -> bool: ...
    def is_copilot_swe_agent(self, author_login: str) -> bool: ...
```

### Dependencies

- `GitHubClient`

---

## 6. `FieldService`

**File**: `fields.py` | **Max LOC**: 300

### Public Interface

```python
class FieldService:
    def __init__(self, client: GitHubClient) -> None: ...
    async def get_project_fields(self, project_id: str) -> list[Field]: ...
    async def update_item_field(self, project_id: str, item_id: str, field_id: str, value: Any) -> dict: ...
    async def update_item_status(self, project_id: str, item_id: str, status: str) -> dict: ...
    # iteration, custom field methods
```

### Dependencies

- `GitHubClient`

---

## 7. `BoardService`

**File**: `board.py` | **Max LOC**: 400

### Public Interface

```python
class BoardService:
    def __init__(self, client: GitHubClient, fields: FieldService) -> None: ...
    async def get_board_data(self, project_id: str) -> BoardData: ...
    async def get_project_items(self, project_id: str, ...) -> list[Item]: ...
```

### Internal Methods

- `_reconcile_board_items` — reconciles API data with board state

### Dependencies

- `GitHubClient`
- `FieldService`

---

## 8. `RepositoryService`

**File**: `repository.py` | **Max LOC**: 300

### Public Interface

```python
class RepositoryService:
    def __init__(self, client: GitHubClient) -> None: ...
    async def get_repository_info(self, owner: str, repo: str) -> dict: ...
    async def get_branch(self, owner: str, repo: str, branch: str) -> dict: ...
    async def create_branch(self, owner: str, repo: str, ...) -> dict: ...
    async def create_commit(self, owner: str, repo: str, ...) -> dict: ...
```

### Dependencies

- `GitHubClient`

---

## Facade Contract

**File**: `__init__.py`

### Re-Export Interface

```python
# All public methods from the original GitHubProjectsService remain accessible
# through the facade class, which delegates to sub-services.

class GitHubProjectsService:
    """Backward-compatible facade over decomposed service modules."""

    def __init__(self, access_token: str, client_factory: GitHubClientFactory) -> None:
        self.client = GitHubClient(access_token, client_factory)
        self.projects = ProjectService(self.client)
        self.issues = IssueService(self.client, self.fields)
        self.pull_requests = PullRequestService(self.client)
        self.copilot = CopilotService(self.client)
        self.fields = FieldService(self.client)
        self.board = BoardService(self.client, self.fields)
        self.repository = RepositoryService(self.client)

    # Delegating methods for backward compatibility:
    async def list_user_projects(self, login: str) -> list:
        return await self.projects.list_user_projects(login)
    # ... (all 79 methods delegate to appropriate sub-service)
```

### Validation

- No existing import path breaks.
- `pytest` green after each module extraction.
- `ruff check` passes (no circular imports, no unused imports).
- Each module file < 800 LOC (verified with `wc -l`).
