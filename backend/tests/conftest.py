"""
Pytest configuration for backend tests.
"""

import pytest

from src.models.user import UserSession

# =============================================================================
# Shared Test Constants
# =============================================================================

TEST_ACCESS_TOKEN = "test-token"
TEST_GITHUB_USER_ID = "12345"
TEST_GITHUB_USERNAME = "testuser"


# =============================================================================
# Fixtures
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
