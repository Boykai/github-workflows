"""Tests for rate limiting configuration and behavior (US7 — FR-015).

T033:
- Rate limiter is configured with per-user and per-IP key helpers
- Rate limiter is disabled during testing
- Rate limit key function returns session-based key for authenticated requests
- Rate limit key function falls back to IP for unauthenticated requests
"""

from unittest.mock import MagicMock

from src.middleware.rate_limit import get_user_key, limiter


class TestRateLimiterConfiguration:
    """Rate limiter must be properly configured."""

    def test_limiter_exists(self):
        """A limiter instance must be configured."""
        assert limiter is not None

    def test_limiter_disabled_in_tests(self):
        """Rate limiting is disabled when TESTING env var is set."""
        # The conftest sets TESTING=1, so the limiter should be disabled
        assert limiter.enabled is False


class TestRateLimitKeyFunction:
    """Rate limit key function must identify users correctly."""

    def test_authenticated_user_gets_session_key(self):
        """Authenticated requests are keyed by session ID."""
        request = MagicMock()
        request.cookies = {"session_id": "test-session-abc123"}
        request.state.rate_limit_key = None
        request.client = MagicMock()
        request.client.host = "192.168.1.1"

        key = get_user_key(request)
        assert key == "user:test-session-abc123"

    def test_unauthenticated_user_gets_ip_key(self):
        """Unauthenticated requests fall back to IP address."""
        request = MagicMock()
        request.cookies = {}
        request.state.rate_limit_key = None
        request.client = MagicMock()
        request.client.host = "10.0.0.1"

        key = get_user_key(request)
        assert key == "ip:10.0.0.1"

    def test_missing_session_cookie_falls_back_to_ip(self):
        """When session cookie is absent, key is IP-based."""
        request = MagicMock()
        request.cookies = {"other_cookie": "value"}
        request.state.rate_limit_key = None
        request.client = MagicMock()
        request.client.host = "172.16.0.1"

        key = get_user_key(request)
        assert key == "ip:172.16.0.1"

    def test_github_user_id_key_takes_precedence(self):
        """When rate_limit_key is set by middleware, it takes precedence."""
        request = MagicMock()
        request.cookies = {"session_id": "session-xyz"}
        request.state.rate_limit_key = "github:12345"
        request.client = MagicMock()
        request.client.host = "10.0.0.1"

        key = get_user_key(request)
        assert key == "github:12345"
