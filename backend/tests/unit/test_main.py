"""Unit tests for the main FastAPI application module."""

import os
import time
from unittest.mock import MagicMock, patch

# Set required env vars before any src imports trigger Settings validation
os.environ.setdefault("GITHUB_CLIENT_ID", "test_id")
os.environ.setdefault("GITHUB_CLIENT_SECRET", "test_secret")
os.environ.setdefault("SESSION_SECRET_KEY", "test_key")

from fastapi import FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from src.config import get_settings  # noqa: E402
from src.exceptions import NotFoundError  # noqa: E402

get_settings.cache_clear()

from src.main import RateLimiter  # noqa: E402


class TestRateLimiterInit:
    """Tests for RateLimiter initialization."""

    def test_default_params(self):
        """Should initialize with default max_requests and window_seconds."""
        limiter = RateLimiter()

        assert limiter.max_requests == 4000
        assert limiter.window_seconds == 3600

    def test_custom_params(self):
        """Should accept custom max_requests and window_seconds."""
        limiter = RateLimiter(max_requests=100, window_seconds=60)

        assert limiter.max_requests == 100
        assert limiter.window_seconds == 60


class TestRateLimiterCheckLimit:
    """Tests for RateLimiter.check_limit."""

    def test_within_limit(self):
        """Should allow requests within the limit."""
        limiter = RateLimiter(max_requests=10)

        allowed, remaining = limiter.check_limit("session1")

        assert allowed is True
        assert remaining == 10

    def test_at_limit(self):
        """Should deny requests when exactly at the limit."""
        limiter = RateLimiter(max_requests=2)
        limiter.record_request("session1", count=2)

        allowed, remaining = limiter.check_limit("session1")

        assert allowed is False
        assert remaining == 0

    def test_over_limit(self):
        """Should deny when over limit."""
        limiter = RateLimiter(max_requests=5)
        limiter.record_request("session1", count=6)

        allowed, remaining = limiter.check_limit("session1")

        assert allowed is False
        assert remaining == 0

    def test_window_cleanup(self):
        """Should clean up requests outside the time window."""
        limiter = RateLimiter(max_requests=5, window_seconds=1)
        # Insert an old timestamp manually
        limiter._requests["session1"].append((time.time() - 10, 5))

        allowed, remaining = limiter.check_limit("session1")

        assert allowed is True
        assert remaining == 5

    def test_separate_sessions(self):
        """Different sessions should have independent limits."""
        limiter = RateLimiter(max_requests=5)
        limiter.record_request("session1", count=5)

        allowed, remaining = limiter.check_limit("session2")

        assert allowed is True
        assert remaining == 5


class TestRateLimiterRecordRequest:
    """Tests for RateLimiter.record_request."""

    def test_record_increments_count(self):
        """Should record requests and reduce remaining count."""
        limiter = RateLimiter(max_requests=10)

        limiter.record_request("session1", count=3)
        _, remaining = limiter.check_limit("session1")

        assert remaining == 7

    def test_record_default_count(self):
        """Default count should be 1."""
        limiter = RateLimiter(max_requests=10)

        limiter.record_request("session1")
        _, remaining = limiter.check_limit("session1")

        assert remaining == 9


class TestRateLimiterGitHubRemaining:
    """Tests for update_github_remaining and get_github_remaining."""

    def test_update_and_get(self):
        """Should store and retrieve GitHub remaining limit."""
        limiter = RateLimiter()

        limiter.update_github_remaining("session1", 4500)
        result = limiter.get_github_remaining("session1")

        assert result == 4500

    def test_get_unknown_session(self):
        """Should return None for unknown session."""
        limiter = RateLimiter()

        result = limiter.get_github_remaining("unknown")

        assert result is None

    def test_update_overwrites(self):
        """Should overwrite previous value."""
        limiter = RateLimiter()
        limiter.update_github_remaining("session1", 4500)

        limiter.update_github_remaining("session1", 3000)

        assert limiter.get_github_remaining("session1") == 3000


class TestCreateApp:
    """Tests for the create_app factory function."""

    @patch("src.main.get_settings")
    def test_returns_fastapi_instance(self, mock_get_settings):
        """create_app should return a FastAPI instance."""
        mock_settings = MagicMock()
        mock_settings.debug = True
        mock_settings.cors_origins_list = ["http://localhost:3000"]
        mock_get_settings.return_value = mock_settings

        from src.main import create_app

        app = create_app()

        assert isinstance(app, FastAPI)

    @patch("src.main.get_settings")
    def test_app_title(self, mock_get_settings):
        """App should have the correct title."""
        mock_settings = MagicMock()
        mock_settings.debug = True
        mock_settings.cors_origins_list = ["http://localhost:3000"]
        mock_get_settings.return_value = mock_settings

        from src.main import create_app

        app = create_app()

        assert app.title == "Agent Projects API"

    @patch("src.main.get_settings")
    def test_docs_url_debug_mode(self, mock_get_settings):
        """Docs URL should be set in debug mode."""
        mock_settings = MagicMock()
        mock_settings.debug = True
        mock_settings.cors_origins_list = ["http://localhost:3000"]
        mock_get_settings.return_value = mock_settings

        from src.main import create_app

        app = create_app()

        assert app.docs_url == "/api/docs"

    @patch("src.main.get_settings")
    def test_docs_url_production_mode(self, mock_get_settings):
        """Docs URL should be None in production mode."""
        mock_settings = MagicMock()
        mock_settings.debug = False
        mock_settings.cors_origins_list = ["http://localhost:3000"]
        mock_get_settings.return_value = mock_settings

        from src.main import create_app

        app = create_app()

        assert app.docs_url is None


class TestExceptionHandlers:
    """Tests for exception handlers via TestClient."""

    @patch("src.main.get_settings")
    def test_app_exception_handler(self, mock_get_settings):
        """AppException should return structured JSON error."""
        mock_settings = MagicMock()
        mock_settings.debug = True
        mock_settings.cors_origins_list = ["*"]
        mock_get_settings.return_value = mock_settings

        from src.main import create_app

        app = create_app()

        @app.get("/test-app-error")
        async def raise_app_error():
            raise NotFoundError("Item missing")

        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/test-app-error")

        assert response.status_code == 404
        data = response.json()
        assert data["error"] == "Item missing"
        assert "details" in data

    @patch("src.main.get_settings")
    def test_generic_exception_handler(self, mock_get_settings):
        """Unhandled exceptions should return 500."""
        mock_settings = MagicMock()
        mock_settings.debug = True
        mock_settings.cors_origins_list = ["*"]
        mock_get_settings.return_value = mock_settings

        from src.main import create_app

        app = create_app()

        @app.get("/test-generic-error")
        async def raise_generic_error():
            raise RuntimeError("unexpected")

        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/test-generic-error")

        assert response.status_code == 500
        data = response.json()
        assert data["error"] == "Internal server error"
