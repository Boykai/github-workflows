"""Tests for secure authentication flow (US1 — SC-001, SC-002).

Verifies:
- Session token is delivered via Set-Cookie header, never in URL (SC-001)
- Dev-login returns 404 when debug=False (SC-002)
"""

from unittest.mock import AsyncMock, MagicMock, patch

from httpx import ASGITransport, AsyncClient

from src.constants import SESSION_COOKIE_NAME
from src.models.user import UserSession


def _make_session(**overrides) -> UserSession:
    defaults = {
        "github_user_id": "12345",
        "github_username": "testuser",
        "access_token": "test-token",
    }
    defaults.update(overrides)
    return UserSession(**defaults)


# ── SC-001: Session token in Set-Cookie, not URL ───────────────────────────


class TestCookieBasedTokenDelivery:
    """OAuth callback must set session token in HttpOnly cookie, not URL."""

    async def test_callback_sets_session_cookie(self):
        """After successful OAuth, session_id should be in Set-Cookie header."""
        from src.api.auth import get_session_dep
        from src.main import create_app

        mock_auth = AsyncMock(name="GitHubAuthService")
        session = _make_session()
        mock_auth.validate_state = MagicMock(return_value=True)
        mock_auth.create_session.return_value = session

        app = create_app()
        app.dependency_overrides[get_session_dep] = lambda: session
        with (
            patch("src.api.auth.github_auth_service", mock_auth),
            patch("src.config.get_settings", return_value=_prod_like_settings(debug=True)),
        ):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
                resp = await ac.get(
                    "/api/v1/auth/github/callback",
                    params={"code": "valid-code", "state": "valid-state"},
                    follow_redirects=False,
                )

        assert resp.status_code == 302
        # Cookie MUST be set
        cookie_header = resp.headers.get("set-cookie", "")
        assert SESSION_COOKIE_NAME in cookie_header, (
            f"Expected '{SESSION_COOKIE_NAME}' in Set-Cookie header, got: {cookie_header}"
        )
        app.dependency_overrides.clear()

    async def test_callback_does_not_leak_token_in_url(self):
        """Redirect URL must NOT contain session_token query parameter."""
        from src.api.auth import get_session_dep
        from src.main import create_app

        mock_auth = AsyncMock(name="GitHubAuthService")
        session = _make_session()
        mock_auth.validate_state = MagicMock(return_value=True)
        mock_auth.create_session.return_value = session

        app = create_app()
        app.dependency_overrides[get_session_dep] = lambda: session
        with (
            patch("src.api.auth.github_auth_service", mock_auth),
            patch("src.config.get_settings", return_value=_prod_like_settings(debug=True)),
        ):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
                resp = await ac.get(
                    "/api/v1/auth/github/callback",
                    params={"code": "valid-code", "state": "valid-state"},
                    follow_redirects=False,
                )

        assert resp.status_code == 302
        location = resp.headers.get("location", "")
        assert "session_token" not in location, f"session_token leaked in redirect URL: {location}"
        app.dependency_overrides.clear()

    async def test_cookie_attributes(self):
        """Set-Cookie must include HttpOnly, SameSite=Lax, Path=/."""
        from src.api.auth import get_session_dep
        from src.main import create_app

        mock_auth = AsyncMock(name="GitHubAuthService")
        session = _make_session()
        mock_auth.validate_state = MagicMock(return_value=True)
        mock_auth.create_session.return_value = session

        app = create_app()
        app.dependency_overrides[get_session_dep] = lambda: session
        with (
            patch("src.api.auth.github_auth_service", mock_auth),
            patch("src.config.get_settings", return_value=_prod_like_settings(debug=True)),
        ):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
                resp = await ac.get(
                    "/api/v1/auth/github/callback",
                    params={"code": "valid-code", "state": "valid-state"},
                    follow_redirects=False,
                )

        cookie_header = resp.headers.get("set-cookie", "").lower()
        assert "httponly" in cookie_header, "Cookie must be HttpOnly"
        assert "samesite=lax" in cookie_header, "Cookie must have SameSite=Lax"
        assert "path=/" in cookie_header, "Cookie must have Path=/"
        app.dependency_overrides.clear()


# ── SC-002: Dev-login gated behind debug mode ──────────────────────────────


class TestDevLoginGating:
    """dev-login must return 404 (not 403) when debug=False."""

    async def test_dev_login_returns_404_production(self):
        """dev-login endpoint should return 404 Not Found in production."""
        from src.api.auth import get_session_dep
        from src.main import create_app

        mock_auth = AsyncMock(name="GitHubAuthService")
        app = create_app()
        session = _make_session()
        app.dependency_overrides[get_session_dep] = lambda: session
        with (
            patch("src.config.get_settings", return_value=_prod_like_settings(debug=False)),
            patch("src.api.auth.github_auth_service", mock_auth),
        ):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
                resp = await ac.post(
                    "/api/v1/auth/dev-login",
                    params={"github_token": "ghp_test"},
                )

        assert resp.status_code == 404, f"Expected 404, got {resp.status_code}: {resp.json()}"
        app.dependency_overrides.clear()

    async def test_dev_login_works_in_debug(self, client, mock_session, mock_github_auth_service):
        """dev-login should still work when debug=True (regression check)."""
        mock_github_auth_service.create_session_from_token.return_value = mock_session
        resp = await client.post(
            "/api/v1/auth/dev-login",
            params={"github_token": "ghp_test"},
        )
        assert resp.status_code == 200
        assert resp.json()["github_username"] == mock_session.github_username


# ── Helpers ─────────────────────────────────────────────────────────────────


def _prod_like_settings(*, debug: bool):
    from src.config import Settings

    return Settings(
        github_client_id="test-client-id",
        github_client_secret="test-client-secret",
        session_secret_key="test-session-secret-key-that-is-long-enough",
        debug=debug,
        _env_file=None,
    )
