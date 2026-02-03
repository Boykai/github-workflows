"""Unit tests for user models."""

import pytest
from datetime import datetime
from uuid import UUID

from src.models.user import UserSession, UserResponse


class TestUserSession:
    """Tests for UserSession model."""

    def test_create_session_with_required_fields(self):
        """Should create a session with required fields only."""
        session = UserSession(
            github_user_id="12345678",
            github_username="testuser",
            access_token="gho_test_token_12345",
        )
        
        assert session.github_user_id == "12345678"
        assert session.github_username == "testuser"
        assert session.access_token == "gho_test_token_12345"
        assert isinstance(session.session_id, UUID)
        assert session.github_avatar_url is None
        assert session.refresh_token is None
        assert session.token_expires_at is None
        assert session.selected_project_id is None

    def test_create_session_with_all_fields(self):
        """Should create a session with all fields."""
        expires_at = datetime(2026, 12, 31, 23, 59, 59)
        
        session = UserSession(
            github_user_id="12345678",
            github_username="testuser",
            github_avatar_url="https://avatars.githubusercontent.com/u/12345678",
            access_token="gho_test_token_12345",
            refresh_token="ghr_refresh_token_12345",
            token_expires_at=expires_at,
            selected_project_id="PVT_kwDOABCD1234",
        )
        
        assert session.github_avatar_url == "https://avatars.githubusercontent.com/u/12345678"
        assert session.refresh_token == "ghr_refresh_token_12345"
        assert session.token_expires_at == expires_at
        assert session.selected_project_id == "PVT_kwDOABCD1234"

    def test_session_has_timestamps(self):
        """Should auto-generate created_at and updated_at timestamps."""
        session = UserSession(
            github_user_id="12345678",
            github_username="testuser",
            access_token="gho_test_token",
        )
        
        assert isinstance(session.created_at, datetime)
        assert isinstance(session.updated_at, datetime)

    def test_session_generates_unique_ids(self):
        """Should generate unique session IDs."""
        session1 = UserSession(
            github_user_id="12345678",
            github_username="testuser",
            access_token="gho_test_token",
        )
        session2 = UserSession(
            github_user_id="12345678",
            github_username="testuser",
            access_token="gho_test_token",
        )
        
        assert session1.session_id != session2.session_id


class TestUserResponse:
    """Tests for UserResponse model."""

    def test_create_response(self):
        """Should create a response with required fields."""
        response = UserResponse(
            github_user_id="12345678",
            github_username="testuser",
        )
        
        assert response.github_user_id == "12345678"
        assert response.github_username == "testuser"
        assert response.github_avatar_url is None
        assert response.selected_project_id is None

    def test_from_session(self):
        """Should create UserResponse from UserSession."""
        session = UserSession(
            github_user_id="12345678",
            github_username="testuser",
            github_avatar_url="https://avatars.githubusercontent.com/u/12345678",
            access_token="gho_test_token",
            selected_project_id="PVT_kwDOABCD1234",
        )
        
        response = UserResponse.from_session(session)
        
        assert response.github_user_id == session.github_user_id
        assert response.github_username == session.github_username
        assert response.github_avatar_url == session.github_avatar_url
        assert response.selected_project_id == session.selected_project_id

    def test_from_session_excludes_sensitive_data(self):
        """Should not include access_token or refresh_token in response."""
        session = UserSession(
            github_user_id="12345678",
            github_username="testuser",
            access_token="gho_sensitive_token",
            refresh_token="ghr_sensitive_refresh",
        )
        
        response = UserResponse.from_session(session)
        
        # Verify sensitive fields are not in the response
        assert not hasattr(response, 'access_token')
        assert not hasattr(response, 'refresh_token')
        assert not hasattr(response, 'session_id')
