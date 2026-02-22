"""Tests for auth API routes (src/api/auth.py).

Covers:
- GET  /api/v1/auth/me           → get_current_user
- POST /api/v1/auth/logout       → logout
- POST /api/v1/auth/dev-login    → dev_login (debug-only)
- POST /api/v1/auth/session      → set_session_cookie
- GET  /api/v1/auth/github       → initiate_github_oauth
- GET  /api/v1/auth/github/callback → github_callback
"""

from unittest.mock import MagicMock, patch

from httpx import ASGITransport, AsyncClient

from src.constants import SESSION_COOKIE_NAME
from src.models.user import UserSession

# ── Helper ──────────────────────────────────────────────────────────────────


def _make_session(**overrides) -> UserSession:
    defaults = {
        "github_user_id": "12345",
        "github_username": "testuser",
        "access_token": "test-token",
    }
    defaults.update(overrides)
    return UserSession(**defaults)


# ── GET /auth/me ────────────────────────────────────────────────────────────


class TestGetCurrentUser:
    """Tests for the /auth/me endpoint.

    NOTE: /me does NOT use Depends(get_session_dep). It reads the session
    cookie directly and calls get_current_session → github_auth_service.get_session.
    """

    async def test_returns_user_info(self, client, mock_session, mock_github_auth_service):
        mock_github_auth_service.get_session.return_value = mock_session
        resp = await client.get(
            "/api/v1/auth/me",
            cookies={SESSION_COOKIE_NAME: str(mock_session.session_id)},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["github_username"] == mock_session.github_username
        assert data["github_user_id"] == mock_session.github_user_id

    async def test_unauthenticated_no_cookie(self, client, mock_github_auth_service):
        """Without a session cookie, the endpoint should 401."""
        resp = await client.get("/api/v1/auth/me")
        assert resp.status_code == 401


# ── POST /auth/logout ──────────────────────────────────────────────────────


class TestLogout:
    async def test_logout_success(self, client, mock_github_auth_service):
        resp = await client.post("/api/v1/auth/logout")
        assert resp.status_code == 200
        assert resp.json()["message"] == "Logged out successfully"


# ── POST /auth/session ─────────────────────────────────────────────────────


class TestSetSessionCookie:
    async def test_set_cookie_valid_token(self, client, mock_session, mock_github_auth_service):
        mock_github_auth_service.get_session.return_value = mock_session
        resp = await client.post(
            "/api/v1/auth/session",
            params={"session_token": str(mock_session.session_id)},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["github_username"] == mock_session.github_username

    async def test_set_cookie_invalid_token(self, client, mock_github_auth_service):
        mock_github_auth_service.get_session.return_value = None
        resp = await client.post("/api/v1/auth/session", params={"session_token": "bad"})
        assert resp.status_code == 401


# ── GET /auth/github ────────────────────────────────────────────────────────


class TestInitiateOAuth:
    async def test_redirects_to_github(self, client, mock_github_auth_service):
        # generate_oauth_url is a SYNC method
        mock_github_auth_service.generate_oauth_url = MagicMock(
            return_value=(
                "https://github.com/login/oauth/authorize?client_id=test",
                "state123",
            )
        )
        resp = await client.get("/api/v1/auth/github", follow_redirects=False)
        assert resp.status_code == 302
        assert "github.com" in resp.headers["location"]


# ── GET /auth/github/callback ──────────────────────────────────────────────


class TestGitHubCallback:
    async def test_callback_invalid_state(self, client, mock_github_auth_service):
        # validate_state is a SYNC method
        mock_github_auth_service.validate_state = MagicMock(return_value=False)
        resp = await client.get(
            "/api/v1/auth/github/callback",
            params={"code": "abc", "state": "bad"},
            follow_redirects=False,
        )
        assert resp.status_code == 400

    async def test_callback_success(self, client, mock_session, mock_github_auth_service):
        mock_github_auth_service.validate_state = MagicMock(return_value=True)
        mock_github_auth_service.create_session.return_value = mock_session
        resp = await client.get(
            "/api/v1/auth/github/callback",
            params={"code": "abc", "state": "ok"},
            follow_redirects=False,
        )
        assert resp.status_code == 302
        assert "session_token=" in resp.headers["location"]

    async def test_callback_create_session_error(self, client, mock_github_auth_service):
        mock_github_auth_service.validate_state = MagicMock(return_value=True)
        mock_github_auth_service.create_session.side_effect = ValueError("bad code")
        resp = await client.get(
            "/api/v1/auth/github/callback",
            params={"code": "bad", "state": "ok"},
            follow_redirects=False,
        )
        assert resp.status_code == 400


# ── POST /auth/dev-login ───────────────────────────────────────────────────


class TestDevLogin:
    async def test_dev_login_debug_mode(self, client, mock_session, mock_github_auth_service):
        """dev-login works when debug=True (mock_settings has debug=True)."""
        mock_github_auth_service.create_session_from_token.return_value = mock_session
        resp = await client.post(
            "/api/v1/auth/dev-login",
            params={"github_token": "ghp_test"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["github_username"] == mock_session.github_username

    async def test_dev_login_production_mode(self, mock_github_auth_service):
        """dev-login returns 403 when debug=False."""
        from src.api.auth import get_session_dep
        from src.config import Settings
        from src.main import create_app

        prod_settings = Settings(
            github_client_id="id",
            github_client_secret="secret",
            session_secret_key="key-key-key-key-key-key-key-key-key",
            debug=False,
            _env_file=None,
        )
        app = create_app()
        session = _make_session()
        app.dependency_overrides[get_session_dep] = lambda: session
        with (
            patch("src.config.get_settings", return_value=prod_settings),
            patch("src.api.auth.github_auth_service", mock_github_auth_service),
        ):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
                resp = await ac.post("/api/v1/auth/dev-login", params={"github_token": "ghp_test"})
        assert resp.status_code == 403
        app.dependency_overrides.clear()
