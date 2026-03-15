# Contract: Domain Services

**Branch**: `033-code-quality-overhaul` | **Phase**: 4.4–4.7

## GitHubIssuesService

```python
class GitHubIssuesService(GitHubBaseClient):
    """Issue-related GitHub API operations."""

    async def create_issue(
        self, owner: str, repo: str, title: str, body: str | None = None,
        assignees: list[str] | None = None, labels: list[str] | None = None,
    ) -> dict[str, Any]: ...

    async def update_issue(
        self, owner: str, repo: str, issue_number: int,
        *, title: str | None = None, body: str | None = None,
        state: str | None = None,
    ) -> dict[str, Any]: ...

    async def get_issue_with_comments(
        self, owner: str, repo: str, issue_number: int,
    ) -> dict[str, Any]: ...

    async def add_issue_comment(
        self, node_id: str, body: str,
    ) -> dict[str, Any]: ...

    async def get_issue_body(
        self, owner: str, repo: str, issue_number: int,
    ) -> str: ...

    async def link_pr_to_issue(
        self, issue_node_id: str, pr_node_id: str,
    ) -> None: ...
```

## GitHubPullRequestService

```python
class GitHubPullRequestService(GitHubBaseClient):
    """Pull request-related GitHub API operations."""

    async def get_linked_pull_requests(
        self, owner: str, repo: str, issue_number: int,
    ) -> list[dict[str, Any]]: ...

    async def merge_pull_request(
        self, node_id: str, *, merge_method: str = "squash",
    ) -> dict[str, Any]: ...

    async def mark_ready_for_review(self, node_id: str) -> None: ...

    async def request_review(
        self, owner: str, repo: str, pr_number: int, reviewers: list[str],
    ) -> None: ...

    async def get_pr_comments(
        self, owner: str, repo: str, pr_number: int,
    ) -> list[dict[str, Any]]: ...
```

## GitHubBranchService

```python
class GitHubBranchService(GitHubBaseClient):
    """Branch and commit-related GitHub API operations."""

    async def create_branch(
        self, owner: str, repo: str, branch_name: str, base_ref: str,
    ) -> dict[str, Any]: ...

    async def create_commit_on_branch(
        self, branch_id: str, message: str, file_changes: dict[str, str],
    ) -> dict[str, Any]: ...

    async def create_pull_request(
        self, owner: str, repo: str, title: str, body: str,
        head: str, base: str,
    ) -> dict[str, Any]: ...

    async def get_default_branch(
        self, owner: str, repo: str,
    ) -> str: ...
```

## GitHubProjectBoardService

```python
class GitHubProjectBoardService(GitHubBaseClient):
    """Project board-related GitHub API operations."""

    async def get_project_items(
        self, project_id: str, *, status_filter: str | None = None,
    ) -> list[dict[str, Any]]: ...

    async def update_item_status(
        self, project_id: str, item_id: str, status_option_id: str,
    ) -> dict[str, Any]: ...

    async def list_board_projects(self) -> list[dict[str, Any]]: ...

    async def get_board_data(
        self, project_id: str,
    ) -> dict[str, Any]: ...

    async def get_status_columns(
        self, project_id: str,
    ) -> list[dict[str, Any]]: ...
```

## GitHubIdentities (Static Module)

```python
# Not a class — module-level functions in identities.py

def is_copilot_author(login: str) -> bool:
    """Check if a username is the Copilot bot."""

def is_copilot_swe_agent(login: str) -> bool:
    """Check if a username is the Copilot SWE agent."""

def is_copilot_reviewer_bot(login: str) -> bool:
    """Check if a username is the Copilot code review bot."""
```

## Shared Invariants

- All domain services receive the same token and RateLimitManager instance
- Domain services MUST NOT import each other (no cross-domain dependencies)
- Callers import the specific service they need, not the base client
- Method signatures are identical to current `GitHubProjectsService` methods (no API change to callers beyond the import path)
