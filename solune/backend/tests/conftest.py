"""
Pytest configuration for backend tests.

Provides shared fixtures for all backend tests:
- mock_session / mock_access_token  — identity stubs
- mock_db                           — in-memory SQLite with migrations
- mock_settings                     — deterministic Settings instance
- mock_github_service               — AsyncMock of GitHubProjectsService
- mock_github_auth_service          — AsyncMock of GitHubAuthService
- mock_ai_agent_service             — AsyncMock of AIAgentService
- mock_websocket_manager            — ConnectionManager stub
- client                            — httpx.AsyncClient wired to the FastAPI app
"""

import os

# Set test environment variables BEFORE any src imports can trigger
# module-level Settings() instantiation (e.g. github_auth_service, cache).
os.environ.setdefault("GITHUB_CLIENT_ID", "test-client-id")
os.environ.setdefault("GITHUB_CLIENT_SECRET", "test-client-secret")
os.environ.setdefault("SESSION_SECRET_KEY", "test-session-secret-key-that-is-long-enough")
os.environ.setdefault("DATABASE_PATH", ":memory:")
# Tests run in debug mode to bypass production secret requirements.
os.environ.setdefault("DEBUG", "true")
# Disable rate limiting during tests.
os.environ["TESTING"] = "1"

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import aiosqlite
import pytest
from httpx import ASGITransport, AsyncClient

from src.config import Settings
from src.models.user import UserSession
from src.services.ai_agent import AIAgentService
from src.services.github_auth import GitHubAuthService
from src.services.github_projects.service import GitHubProjectsService
from src.services.websocket import ConnectionManager

# =============================================================================
# Shared Test Constants
# =============================================================================

TEST_ACCESS_TOKEN = "test-token"
TEST_GITHUB_USER_ID = "12345"
TEST_GITHUB_USERNAME = "testuser"

MIGRATIONS_DIR = Path(__file__).resolve().parent.parent / "src" / "migrations"


# =============================================================================
# Helpers
# =============================================================================


async def _apply_migrations(db: aiosqlite.Connection) -> None:
    """Apply all SQL migration files to an in-memory database."""
    migration_files = sorted(MIGRATIONS_DIR.glob("*.sql"))
    for mf in migration_files:
        sql = mf.read_text()
        await db.executescript(sql)
    await db.commit()


# =============================================================================
# Fixtures — Identity
# =============================================================================


@pytest.fixture(scope="session")
def anyio_backend():
    """Use asyncio backend for async tests."""
    return "asyncio"


@pytest.fixture
def mock_session() -> UserSession:
    """Create a mock user session for testing.

    Use this fixture instead of creating UserSession instances directly
    to ensure consistent test data across all tests.
    """
    return UserSession(
        github_user_id=TEST_GITHUB_USER_ID,
        github_username=TEST_GITHUB_USERNAME,
        access_token=TEST_ACCESS_TOKEN,
    )


@pytest.fixture
def mock_access_token() -> str:
    """Return the standard test access token."""
    return TEST_ACCESS_TOKEN


# =============================================================================
# Fixtures — Database
# =============================================================================


@pytest.fixture
async def mock_db():
    """In-memory SQLite database with all migrations applied.

    Yields an aiosqlite Connection that behaves like the production DB.
    Automatically closed after each test.
    """
    db = await aiosqlite.connect(":memory:")
    db.row_factory = aiosqlite.Row
    await _apply_migrations(db)
    yield db
    await db.close()


# =============================================================================
# Fixtures — Configuration
# =============================================================================


@pytest.fixture
def mock_settings() -> Settings:
    """Deterministic Settings instance for testing (no env vars needed)."""
    return Settings(
        github_client_id="test-client-id",
        github_client_secret="test-client-secret",
        session_secret_key="test-session-secret-key-that-is-long-enough",
        ai_provider="copilot",
        debug=True,
        log_level="DEBUG",
        cors_origins="http://localhost:5173",
        database_path=":memory:",
    )


# =============================================================================
# Fixtures — Service Mocks
# =============================================================================


@pytest.fixture
def mock_github_service() -> AsyncMock:
    """AsyncMock replacing the global ``github_projects_service`` instance.

    Synchronous methods like ``get_last_rate_limit`` are explicitly set as
    ``MagicMock`` so they don't return unawaited coroutines when called
    without ``await`` in production code.
    """
    mock = AsyncMock(name="GitHubProjectsService", spec=GitHubProjectsService)
    mock.get_last_rate_limit = MagicMock(return_value=None)
    return mock


@pytest.fixture
def mock_github_auth_service() -> AsyncMock:
    """AsyncMock replacing the global ``github_auth_service`` instance."""
    return AsyncMock(name="GitHubAuthService", spec=GitHubAuthService)


@pytest.fixture
def mock_ai_agent_service() -> AsyncMock:
    """AsyncMock replacing the ``AIAgentService`` returned by ``get_ai_agent_service()``."""
    return AsyncMock(name="AIAgentService", spec=AIAgentService)


@pytest.fixture
def mock_websocket_manager() -> AsyncMock:
    """AsyncMock replacing the global ``connection_manager`` instance."""
    mock = AsyncMock(name="ConnectionManager", spec=ConnectionManager)
    mock.get_connection_count.return_value = 0
    mock.get_total_connections.return_value = 0
    return mock


# =============================================================================
# Fixtures — Cache Isolation
# =============================================================================


@pytest.fixture(autouse=True)
def _clear_resolve_repo_cache():
    """Clear resolve_repository cache entries between tests.

    resolve_repository() caches results in the global InMemoryCache to avoid
    repeated GitHub API calls.  This fixture ensures tests that mock different
    fallback paths are not polluted by a prior test's cached result.
    """
    from src.services.cache import cache as _cache

    # Clear all resolve_repo:* entries before and after each test
    keys_to_clear = [k for k in list(_cache._cache.keys()) if k.startswith("resolve_repo:")]
    for k in keys_to_clear:
        _cache.delete(k)
    yield
    keys_to_clear = [k for k in list(_cache._cache.keys()) if k.startswith("resolve_repo:")]
    for k in keys_to_clear:
        _cache.delete(k)


# =============================================================================
# Fixtures — Test Client
# =============================================================================


@pytest.fixture
async def client(
    mock_session: UserSession,
    mock_db: aiosqlite.Connection,
    mock_settings: Settings,
    mock_github_service: AsyncMock,
    mock_github_auth_service: AsyncMock,
    mock_ai_agent_service: AsyncMock,
    mock_websocket_manager: AsyncMock,
):
    """httpx.AsyncClient wired to the FastAPI app with all deps overridden.

    Patches:
    - get_session_dep → returns mock_session (auth bypass)
    - database.get_db → returns mock_db
    - get_settings → returns mock_settings
    - Global service singletons → AsyncMocks
    """
    from src.api.auth import get_session_dep
    from src.dependencies import get_connection_manager, get_github_service, verify_project_access
    from src.main import create_app

    app = create_app()

    # FastAPI dependency overrides
    app.dependency_overrides[get_session_dep] = lambda: mock_session
    app.dependency_overrides[get_github_service] = lambda: mock_github_service
    app.dependency_overrides[get_connection_manager] = lambda: mock_websocket_manager
    # Bypass project ownership check in unit tests — individual tests
    # that need to verify authorization behavior can re-enable it.
    app.dependency_overrides[verify_project_access] = lambda: None

    import contextlib

    patches = [
        patch("src.services.database.get_db", return_value=mock_db),
        patch("src.services.database._connection", mock_db),
        patch("src.config.get_settings", return_value=mock_settings),
        # github_projects_service — patched in every API module that imports it
        patch("src.api.board.github_projects_service", mock_github_service),
        patch("src.api.projects.github_projects_service", mock_github_service),
        patch("src.api.tasks.github_projects_service", mock_github_service),
        patch("src.api.workflow.github_projects_service", mock_github_service),
        patch("src.api.chores.github_projects_service", mock_github_service),
        # resolve_repository (src.utils) lazy-imports github_projects_service
        patch("src.services.github_projects.github_projects_service", mock_github_service),
        # github_auth_service — patched where imported
        patch("src.api.auth.github_auth_service", mock_github_auth_service),
        patch("src.api.projects.github_auth_service", mock_github_auth_service),
        # AI agent service
        patch("src.api.chat.get_ai_agent_service", return_value=mock_ai_agent_service),
        # connection_manager — patched in every API module that broadcasts
        patch("src.api.projects.connection_manager", mock_websocket_manager),
        patch("src.api.tasks.connection_manager", mock_websocket_manager),
        patch("src.api.workflow.connection_manager", mock_websocket_manager),
        # verify_project_access — bypass direct calls (not just dependency overrides)
        patch("src.api.tasks.verify_project_access", AsyncMock(return_value=None)),
        patch("src.api.workflow.verify_project_access", AsyncMock(return_value=None)),
        # get_db — patched for settings and MCP routes (direct call, not Depends)
        patch("src.api.settings.get_db", return_value=mock_db),
        patch("src.api.mcp.get_db", return_value=mock_db),
        patch("src.api.tools.get_db", return_value=mock_db),
    ]

    with contextlib.ExitStack() as stack:
        for p in patches:
            stack.enter_context(p)
        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport,
            base_url="http://testserver",
        ) as ac:
            yield ac

    app.dependency_overrides.clear()


# =============================================================================
# Factory helpers (consolidated from tests/helpers/mocks.py)
# =============================================================================


def make_mock_github_service(**overrides) -> AsyncMock:
    """Create a pre-configured GitHubProjectsService mock with spec."""
    mock = AsyncMock(name="GitHubProjectsService", spec=GitHubProjectsService)
    mock.get_project_repository.return_value = overrides.pop(
        "get_project_repository", ("owner", "repo")
    )
    mock.create_issue.return_value = overrides.pop(
        "create_issue",
        {
            "id": 300042,
            "number": 42,
            "node_id": "I_abc",
            "html_url": "https://github.com/owner/repo/issues/42",
        },
    )
    mock.add_issue_to_project.return_value = overrides.pop("add_issue_to_project", "PVTI_new")
    for method_name, return_value in overrides.items():
        getattr(mock, method_name).return_value = return_value
    return mock


def make_mock_github_auth_service(**overrides) -> AsyncMock:
    """Create a pre-configured GitHubAuthService mock with spec."""
    mock = AsyncMock(name="GitHubAuthService", spec=GitHubAuthService)
    for method_name, return_value in overrides.items():
        getattr(mock, method_name).return_value = return_value
    return mock


def make_mock_ai_agent_service(**overrides) -> AsyncMock:
    """Create a pre-configured AIAgentService mock with spec."""
    mock = AsyncMock(name="AIAgentService", spec=AIAgentService)
    for method_name, return_value in overrides.items():
        getattr(mock, method_name).return_value = return_value
    return mock


def make_mock_websocket_manager(**overrides) -> AsyncMock:
    """Create a pre-configured ConnectionManager mock with spec."""
    mock = AsyncMock(name="ConnectionManager", spec=ConnectionManager)
    mock.get_connection_count.return_value = overrides.pop("connection_count", 0)
    mock.get_total_connections.return_value = overrides.pop("total_connections", 0)
    for method_name, return_value in overrides.items():
        getattr(mock, method_name).return_value = return_value
    return mock


def make_mock_db_connection() -> MagicMock:
    """Create a mock aiosqlite Connection for testing database operations."""
    mock = MagicMock(name="DatabaseConnection")
    mock_cursor = MagicMock(name="DatabaseCursor")
    mock_cursor.fetchone = AsyncMock(return_value=None)
    mock_cursor.fetchall = AsyncMock(return_value=[])
    mock.execute = AsyncMock(return_value=mock_cursor)
    mock.executemany = AsyncMock()
    mock.executescript = AsyncMock()
    mock.commit = AsyncMock()
    mock.close = AsyncMock()
    return mock
