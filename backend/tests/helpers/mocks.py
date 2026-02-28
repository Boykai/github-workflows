"""Reusable mock builders for backend tests.

Provides pre-configured mock objects for common service dependencies,
reducing duplicated setup across test files.
"""

from unittest.mock import AsyncMock, MagicMock


def make_mock_github_service(**overrides) -> AsyncMock:
    """Create a pre-configured GitHubProjectsService mock.

    Commonly overridden methods are set to sensible defaults:
    - get_project_repository → ("owner", "repo")
    - create_issue → dict with number, node_id, html_url
    - add_issue_to_project → "PVTI_new"

    Override any return value via keyword arguments keyed by method name.
    """
    mock = AsyncMock(name="GitHubProjectsService")
    mock.get_project_repository.return_value = overrides.pop(
        "get_project_repository", ("owner", "repo")
    )
    mock.create_issue.return_value = overrides.pop(
        "create_issue",
        {
            "number": 42,
            "node_id": "I_abc",
            "html_url": "https://github.com/owner/repo/issues/42",
        },
    )
    mock.add_issue_to_project.return_value = overrides.pop(
        "add_issue_to_project", "PVTI_new"
    )
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
    """Create a mock aiosqlite Connection for testing database operations."""
    mock = MagicMock(name="DatabaseConnection")
    mock.execute = AsyncMock()
    mock.executemany = AsyncMock()
    mock.executescript = AsyncMock()
    mock.commit = AsyncMock()
    mock.close = AsyncMock()
    mock.fetchone = AsyncMock(return_value=None)
    mock.fetchall = AsyncMock(return_value=[])
    return mock
