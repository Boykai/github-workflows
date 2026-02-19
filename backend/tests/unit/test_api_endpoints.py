"""Unit tests for FastAPI API endpoints."""

import os

os.environ.setdefault("GITHUB_CLIENT_ID", "test_id")
os.environ.setdefault("GITHUB_CLIENT_SECRET", "test_secret")
os.environ.setdefault("SESSION_SECRET_KEY", "test_key")

import pytest
from httpx import ASGITransport, AsyncClient

from src.config import get_settings

# Clear cached settings so env vars are picked up
get_settings.cache_clear()

from src.main import app


@pytest.fixture
async def client():
    """Create async HTTP client for testing FastAPI endpoints."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


class TestHealthEndpoint:
    """Tests for health check endpoint."""

    @pytest.mark.asyncio
    async def test_health_returns_200(self, client):
        """Should return 200 OK."""
        response = await client.get("/api/v1/health")

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_health_returns_healthy_status(self, client):
        """Should return healthy status in body."""
        response = await client.get("/api/v1/health")

        assert response.json() == {"status": "healthy"}


class TestAuthMeEndpoint:
    """Tests for GET /auth/me endpoint."""

    @pytest.mark.asyncio
    async def test_me_without_cookie_returns_401(self, client):
        """Should return 401 when no session cookie provided."""
        response = await client.get("/api/v1/auth/me")

        assert response.status_code == 401


class TestAuthLogoutEndpoint:
    """Tests for POST /auth/logout endpoint."""

    @pytest.mark.asyncio
    async def test_logout_without_cookie_returns_200(self, client):
        """Should return 200 even without session cookie."""
        response = await client.post("/api/v1/auth/logout")

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_logout_returns_message(self, client):
        """Should return logged out message."""
        response = await client.post("/api/v1/auth/logout")

        assert response.json()["message"] == "Logged out successfully"


class TestAuthSessionEndpoint:
    """Tests for POST /auth/session endpoint."""

    @pytest.mark.asyncio
    async def test_session_with_invalid_token_returns_401(self, client):
        """Should return 401 for invalid session token."""
        response = await client.post(
            "/api/v1/auth/session", params={"session_token": "invalid_token_123"}
        )

        assert response.status_code == 401


class TestAuthGitHubEndpoint:
    """Tests for GET /auth/github endpoint."""

    @pytest.mark.asyncio
    async def test_github_oauth_redirects(self, client):
        """Should return 302 redirect to GitHub."""
        response = await client.get("/api/v1/auth/github", follow_redirects=False)

        assert response.status_code == 302
        assert "github.com" in response.headers["location"]
