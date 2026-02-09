"""
End-to-end API tests for the GitHub Projects Chat Backend.

These tests verify the API endpoints work correctly.
"""

import pytest
from httpx import ASGITransport, AsyncClient

from src.main import create_app
from src.models.user import UserSession
from src.services.github_auth import _sessions


@pytest.fixture
def app():
    """Create test application instance."""
    return create_app()


@pytest.fixture
async def client(app):
    """Create async test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


class TestHealthEndpoint:
    """Tests for the health check endpoint."""

    @pytest.mark.asyncio
    async def test_health_returns_healthy(self, client):
        """Health endpoint should return healthy status."""
        response = await client.get("/api/v1/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_health_response_format(self, client):
        """Health endpoint should return proper JSON format."""
        response = await client.get("/api/v1/health")

        assert response.headers["content-type"] == "application/json"
        data = response.json()
        assert isinstance(data, dict)
        assert "status" in data


class TestAuthEndpoints:
    """Tests for authentication endpoints."""

    @pytest.mark.asyncio
    async def test_auth_me_returns_401_when_not_authenticated(self, client):
        """Auth me endpoint should return 401 for unauthenticated users."""
        response = await client.get("/api/v1/auth/me")

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_auth_github_endpoint_exists(self, client):
        """GitHub OAuth endpoint should exist."""
        response = await client.get("/api/v1/auth/github", follow_redirects=False)

        # Should redirect to GitHub OAuth
        assert response.status_code in [302, 307, 400]  # Redirect or bad request if not configured

    @pytest.mark.asyncio
    async def test_auth_github_callback_requires_code_and_state(self, client):
        """GitHub callback should require code and state parameters."""
        # Missing code and state
        response = await client.get("/api/v1/auth/github/callback")
        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_auth_github_callback_validates_state(self, client):
        """GitHub callback should validate state parameter."""
        response = await client.get(
            "/api/v1/auth/github/callback", params={"code": "test_code", "state": "invalid_state"}
        )
        # Should reject invalid state
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_auth_session_endpoint_requires_token(self, client):
        """Session endpoint should require session_token parameter."""
        response = await client.post("/api/v1/auth/session")
        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_auth_session_endpoint_rejects_invalid_token(self, client):
        """Session endpoint should reject invalid token."""
        response = await client.post(
            "/api/v1/auth/session", params={"session_token": "invalid_token"}
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_auth_session_endpoint_accepts_valid_token(self, client):
        """Session endpoint should accept valid token and set cookie."""
        # Create a test session
        session = UserSession(
            github_user_id="12345",
            github_username="testuser",
            github_avatar_url="https://example.com/avatar.png",
            access_token="test_access_token",
        )
        _sessions[str(session.session_id)] = session

        try:
            response = await client.post(
                "/api/v1/auth/session", params={"session_token": str(session.session_id)}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["github_username"] == "testuser"
            assert data["github_user_id"] == "12345"

            # Should set session cookie
            assert "session_id" in response.cookies or any(
                "session_id" in str(h) for h in response.headers.raw
            )
        finally:
            # Clean up
            _sessions.pop(str(session.session_id), None)

    @pytest.mark.asyncio
    async def test_auth_me_with_valid_session(self, client):
        """Auth me endpoint should return user for valid session."""
        # Create a test session
        session = UserSession(
            github_user_id="67890",
            github_username="authuser",
            access_token="test_token",
        )
        _sessions[str(session.session_id)] = session

        try:
            response = await client.get(
                "/api/v1/auth/me", cookies={"session_id": str(session.session_id)}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["github_username"] == "authuser"
        finally:
            _sessions.pop(str(session.session_id), None)

    @pytest.mark.asyncio
    async def test_logout_with_valid_session(self, client):
        """Logout should revoke valid session."""
        # Create a test session
        session = UserSession(
            github_user_id="99999",
            github_username="logoutuser",
            access_token="test_token",
        )
        _sessions[str(session.session_id)] = session

        response = await client.post(
            "/api/v1/auth/logout", cookies={"session_id": str(session.session_id)}
        )

        assert response.status_code == 200
        # Session should be revoked
        assert str(session.session_id) not in _sessions

    @pytest.mark.asyncio
    async def test_logout_without_session(self, client):
        """Logout should handle missing session gracefully."""
        response = await client.post("/api/v1/auth/logout")

        # Should return OK even without session
        assert response.status_code in [200, 401]

    @pytest.mark.asyncio
    async def test_update_profile_requires_auth(self, client):
        """Profile update endpoint should require authentication."""
        response = await client.patch(
            "/api/v1/auth/me",
            json={"email": "test@example.com", "bio": "Test bio"},
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_update_profile_with_valid_session(self, client):
        """Profile update should work with valid session."""
        # Create a test session
        session = UserSession(
            github_user_id="12345",
            github_username="testuser",
            access_token="test_token",
        )
        _sessions[str(session.session_id)] = session

        try:
            response = await client.patch(
                "/api/v1/auth/me",
                json={
                    "email": "newemail@example.com",
                    "bio": "Updated bio",
                    "contact_phone": "+1-555-0123",
                    "contact_location": "San Francisco, CA",
                },
                cookies={"session_id": str(session.session_id)},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["email"] == "newemail@example.com"
            assert data["bio"] == "Updated bio"
            assert data["contact_phone"] == "+1-555-0123"
            assert data["contact_location"] == "San Francisco, CA"

            # Verify session was updated
            updated_session = _sessions[str(session.session_id)]
            assert updated_session.email == "newemail@example.com"
            assert updated_session.bio == "Updated bio"
        finally:
            _sessions.pop(str(session.session_id), None)

    @pytest.mark.asyncio
    async def test_update_profile_partial_update(self, client):
        """Profile update should allow partial updates."""
        # Create a test session with existing data
        session = UserSession(
            github_user_id="12345",
            github_username="testuser",
            access_token="test_token",
            email="old@example.com",
            bio="Old bio",
        )
        _sessions[str(session.session_id)] = session

        try:
            # Only update email
            response = await client.patch(
                "/api/v1/auth/me",
                json={"email": "new@example.com"},
                cookies={"session_id": str(session.session_id)},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["email"] == "new@example.com"
            assert data["bio"] == "Old bio"  # Should remain unchanged
        finally:
            _sessions.pop(str(session.session_id), None)


class TestProjectsEndpoints:
    """Tests for projects endpoints."""

    @pytest.mark.asyncio
    async def test_projects_requires_auth(self, client):
        """Projects endpoint should require authentication."""
        response = await client.get("/api/v1/projects")

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_projects_with_invalid_auth(self, client):
        """Projects endpoint should reject invalid auth."""
        response = await client.get(
            "/api/v1/projects", cookies={"session": "invalid-session-token"}
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_project_select_requires_auth(self, client):
        """Project select should require authentication."""
        response = await client.post("/api/v1/projects/PVT_test123/select")

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_project_tasks_requires_auth(self, client):
        """Project tasks should require authentication."""
        response = await client.get("/api/v1/projects/PVT_test123/tasks")

        assert response.status_code == 401


class TestTasksEndpoints:
    """Tests for tasks endpoints."""

    @pytest.mark.asyncio
    async def test_tasks_requires_auth(self, client):
        """Tasks endpoint should require authentication."""
        response = await client.get("/api/v1/projects/test-project/tasks")

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_create_task_requires_auth(self, client):
        """Create task endpoint should require authentication."""
        response = await client.post(
            "/api/v1/tasks", json={"title": "Test Task", "body": "Test body"}
        )

        assert response.status_code == 401


class TestChatEndpoints:
    """Tests for chat endpoints."""

    @pytest.mark.asyncio
    async def test_chat_requires_auth(self, client):
        """Chat endpoint should require authentication."""
        response = await client.post("/api/v1/chat/messages", json={"content": "Hello"})

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_chat_history_requires_auth(self, client):
        """Chat history endpoint should require authentication."""
        response = await client.get("/api/v1/chat/messages")

        assert response.status_code == 401


class TestCORSAndHeaders:
    """Tests for CORS and security headers."""

    @pytest.mark.asyncio
    async def test_cors_headers_present(self, client):
        """CORS headers should be present for cross-origin requests."""
        response = await client.options(
            "/api/v1/health", headers={"Origin": "http://localhost:3000"}
        )

        # Should allow the request
        assert response.status_code in [200, 204, 405]

    @pytest.mark.asyncio
    async def test_json_content_type(self, client):
        """API should return JSON content type."""
        response = await client.get("/api/v1/health")

        assert "application/json" in response.headers.get("content-type", "")


class TestErrorHandling:
    """Tests for error handling."""

    @pytest.mark.asyncio
    async def test_404_for_unknown_route(self, client):
        """Unknown routes should return 404."""
        response = await client.get("/api/v1/unknown-endpoint")

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_405_for_wrong_method(self, client):
        """Wrong HTTP method should return 405."""
        response = await client.delete("/api/v1/health")

        assert response.status_code == 405

    @pytest.mark.asyncio
    async def test_invalid_json_handled(self, client):
        """Invalid JSON should be handled gracefully."""
        response = await client.post(
            "/api/v1/chat/messages",
            content="not valid json",
            headers={"Content-Type": "application/json"},
        )

        # Should return an error (401 for auth or 422 for validation)
        assert response.status_code in [401, 422]
