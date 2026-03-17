"""Tests for rate limiting configuration and behavior (US7 — FR-015).

T033:
- Rate limiter is configured with per-user and per-IP key helpers
- Rate limiter is disabled during testing
- Rate limit key function returns session-based key for authenticated requests
- Rate limit key function falls back to IP for unauthenticated requests
"""

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from src.middleware.rate_limit import RateLimitKeyMiddleware, get_user_key, limiter


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
        request.state.rate_limit_key = "user:12345"
        request.client = MagicMock()
        request.client.host = "10.0.0.1"

        key = get_user_key(request)
        assert key == "user:12345"


class TestRateLimitKeyMiddleware:
    @pytest.mark.asyncio
    async def test_passthrough_for_non_http_scopes(self):
        called = False

        async def app(scope, receive, send):
            nonlocal called
            called = True

        middleware = RateLimitKeyMiddleware(app)

        await middleware({"type": "websocket"}, None, None)

        assert called is True

    @pytest.mark.asyncio
    async def test_sets_rate_limit_key_from_resolved_session(self, monkeypatch):
        seen_key = None

        async def app(scope, receive, send):
            nonlocal seen_key
            seen_key = scope["state"].get("rate_limit_key")

        async def fake_get_session(_db, session_id):
            assert session_id == "session-123"
            return SimpleNamespace(github_user_id="gh-user-42")

        monkeypatch.setattr("src.services.database.get_db", lambda: object())
        monkeypatch.setattr("src.services.session_store.get_session", fake_get_session)

        middleware = RateLimitKeyMiddleware(app)
        scope = {
            "type": "http",
            "method": "GET",
            "path": "/limited",
            "headers": [(b"cookie", b"session_id=session-123")],
            "query_string": b"",
            "state": {},
            "client": ("127.0.0.1", 1234),
            "server": ("testserver", 80),
            "scheme": "http",
            "http_version": "1.1",
        }

        async def receive():
            return {"type": "http.request", "body": b"", "more_body": False}

        async def send(_message):
            return None

        await middleware(scope, receive, send)

        assert seen_key == "user:gh-user-42"

    @pytest.mark.asyncio
    async def test_keeps_fallback_behavior_when_session_has_no_github_user(self, monkeypatch):
        seen_key = "sentinel"

        async def app(scope, receive, send):
            nonlocal seen_key
            seen_key = scope["state"].get("rate_limit_key")

        async def fake_get_session(_db, _session_id):
            return SimpleNamespace(github_user_id=None)

        monkeypatch.setattr("src.services.database.get_db", lambda: object())
        monkeypatch.setattr("src.services.session_store.get_session", fake_get_session)

        middleware = RateLimitKeyMiddleware(app)
        scope = {
            "type": "http",
            "method": "GET",
            "path": "/limited",
            "headers": [(b"cookie", b"session_id=session-123")],
            "query_string": b"",
            "state": {},
            "client": ("127.0.0.1", 1234),
            "server": ("testserver", 80),
            "scheme": "http",
            "http_version": "1.1",
        }

        async def receive():
            return {"type": "http.request", "body": b"", "more_body": False}

        async def send(_message):
            return None

        await middleware(scope, receive, send)

        assert seen_key is None

    @pytest.mark.asyncio
    async def test_swallows_resolution_errors_and_continues(self, monkeypatch):
        called = False

        async def app(scope, receive, send):
            nonlocal called
            called = True
            assert scope["state"].get("rate_limit_key") is None

        monkeypatch.setattr("src.services.database.get_db", lambda: object())

        async def fake_get_session(_db, _session_id):
            raise RuntimeError("db unavailable")

        monkeypatch.setattr("src.services.session_store.get_session", fake_get_session)

        middleware = RateLimitKeyMiddleware(app)
        scope = {
            "type": "http",
            "method": "GET",
            "path": "/limited",
            "headers": [(b"cookie", b"session_id=session-123")],
            "query_string": b"",
            "state": {},
            "client": ("127.0.0.1", 1234),
            "server": ("testserver", 80),
            "scheme": "http",
            "http_version": "1.1",
        }

        async def receive():
            return {"type": "http.request", "body": b"", "more_body": False}

        async def send(_message):
            return None

        await middleware(scope, receive, send)

        assert called is True
