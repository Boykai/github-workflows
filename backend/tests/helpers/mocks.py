"""Reusable mock builders for backend tests.

Provides pre-configured mock objects for common service dependencies,
reducing duplicated setup across test files.
"""

from unittest.mock import AsyncMock, MagicMock, Mock

from src.services.completion_providers import CompletionProvider


class MockCompletionProvider(CompletionProvider):
    """Test double for CompletionProvider that returns configurable responses."""

    def __init__(self, response: str = ""):
        self._response = response
        self._side_effect = None
        self.last_messages = None
        self.last_github_token = None

    async def complete(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1000,
        github_token: str | None = None,
    ) -> str:
        self.last_messages = messages
        self.last_github_token = github_token
        if self._side_effect:
            raise self._side_effect
        return self._response

    def set_response(self, response: str) -> None:
        self._response = response
        self._side_effect = None

    def set_error(self, error: Exception) -> None:
        self._side_effect = error

    @property
    def name(self) -> str:
        return "mock"


def make_mock_provider(response: str = "") -> MockCompletionProvider:
    """Create a pre-configured MockCompletionProvider instance.

    Used across AIAgentService test classes to avoid duplicating the
    mock_provider fixture definition.
    """
    return MockCompletionProvider(response=response)


def make_mock_github_service(**overrides) -> Mock:
    """Create a pre-configured GitHubProjectsService mock.

    Uses ``Mock()`` as the base with selective ``AsyncMock`` for async methods,
    matching production code's mix of sync and async methods.  Override any
    return value via keyword arguments keyed by method name.
    """
    mock = Mock(name="GitHubProjectsService")
    # Async methods
    mock.get_project_repository = AsyncMock(
        return_value=overrides.pop("get_project_repository", ("owner", "repo"))
    )
    mock.create_issue = AsyncMock(
        return_value=overrides.pop(
            "create_issue",
            {
                "id": 300042,
                "number": 42,
                "node_id": "I_abc",
                "html_url": "https://github.com/owner/repo/issues/42",
            },
        )
    )
    mock.add_issue_to_project = AsyncMock(
        return_value=overrides.pop("add_issue_to_project", "PVTI_new")
    )
    mock.get_issue_with_comments = AsyncMock(
        return_value=overrides.pop("get_issue_with_comments", None)
    )
    mock.assign_copilot_to_issue = AsyncMock(
        return_value=overrides.pop("assign_copilot_to_issue", None)
    )
    mock.update_item_status_by_name = AsyncMock(
        return_value=overrides.pop("update_item_status_by_name", None)
    )
    mock.validate_assignee = AsyncMock()
    mock.assign_issue = AsyncMock()
    mock.find_existing_pr_for_issue = AsyncMock(
        return_value=overrides.pop("find_existing_pr_for_issue", None)
    )
    mock.update_issue_body = AsyncMock()
    mock.update_issue_state = AsyncMock(return_value=overrides.pop("update_issue_state", None))
    mock.update_sub_issue_project_status = AsyncMock()
    mock.create_sub_issue = AsyncMock(return_value=overrides.pop("create_sub_issue", None))
    # Sync methods
    mock.format_issue_context_as_prompt = Mock(
        return_value=overrides.pop("format_issue_context_as_prompt", None)
    )
    mock.tailor_body_for_agent = Mock(return_value=overrides.pop("tailor_body_for_agent", None))
    # Apply remaining overrides
    for method_name, return_value in overrides.items():
        getattr(mock, method_name).return_value = return_value
    return mock


def make_mock_github_auth_service(**overrides) -> AsyncMock:
    """Create a pre-configured GitHubAuthService mock."""
    mock = AsyncMock(name="GitHubAuthService")
    for method_name, return_value in overrides.items():
        getattr(mock, method_name).return_value = return_value
    return mock


def make_mock_ai_agent_service(**overrides) -> AsyncMock:
    """Create a pre-configured AIAgentService mock."""
    mock = AsyncMock(name="AIAgentService")
    for method_name, return_value in overrides.items():
        getattr(mock, method_name).return_value = return_value
    return mock


def make_mock_websocket_manager(**overrides) -> AsyncMock:
    """Create a pre-configured ConnectionManager mock."""
    mock = AsyncMock(name="ConnectionManager")
    mock.get_connection_count.return_value = overrides.pop("connection_count", 0)
    mock.get_total_connections.return_value = overrides.pop("total_connections", 0)
    for method_name, return_value in overrides.items():
        getattr(mock, method_name).return_value = return_value
    return mock


def make_mock_db_connection() -> MagicMock:
    """Create a mock aiosqlite Connection for testing database operations.

    In aiosqlite, ``fetchone`` / ``fetchall`` live on the **cursor** returned
    by ``await db.execute(...)``, not on the connection itself.  This mock
    mirrors that structure so tests exercise realistic call chains.
    """
    mock = MagicMock(name="DatabaseConnection")

    # Cursor mock — returned by execute() to match the real aiosqlite API.
    mock_cursor = MagicMock(name="DatabaseCursor")
    mock_cursor.fetchone = AsyncMock(return_value=None)
    mock_cursor.fetchall = AsyncMock(return_value=[])

    mock.execute = AsyncMock(return_value=mock_cursor)
    mock.executemany = AsyncMock()
    mock.executescript = AsyncMock()
    mock.commit = AsyncMock()
    mock.close = AsyncMock()
    return mock
