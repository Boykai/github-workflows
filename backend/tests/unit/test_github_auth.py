"""Unit tests for GitHub authentication service."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from src.services.github_auth import GitHubAuthService, _sessions, _oauth_states
from src.models.user import UserSession


class TestGitHubAuthServiceOAuth:
    """Tests for OAuth URL generation and state validation."""

    def setup_method(self):
        """Clear state before each test."""
        _oauth_states.clear()
        _sessions.clear()

    @patch('src.services.github_auth.get_settings')
    def test_generate_oauth_url_returns_url_and_state(self, mock_settings):
        """Should generate OAuth URL with state parameter."""
        mock_settings.return_value = MagicMock(
            github_client_id="test_client_id",
            github_redirect_uri="http://localhost:8000/callback",
        )
        
        service = GitHubAuthService()
        url, state = service.generate_oauth_url()
        
        assert "https://github.com/login/oauth/authorize" in url
        assert "client_id=test_client_id" in url
        assert f"state={state}" in url
        assert len(state) > 20  # State should be a secure token

    @patch('src.services.github_auth.get_settings')
    def test_generate_oauth_url_stores_state(self, mock_settings):
        """Should store state for later validation."""
        mock_settings.return_value = MagicMock(
            github_client_id="test_client_id",
            github_redirect_uri="http://localhost:8000/callback",
        )
        
        service = GitHubAuthService()
        _, state = service.generate_oauth_url()
        
        assert state in _oauth_states

    @patch('src.services.github_auth.get_settings')
    def test_validate_state_returns_true_for_valid_state(self, mock_settings):
        """Should validate valid, non-expired state."""
        mock_settings.return_value = MagicMock()
        
        service = GitHubAuthService()
        state = "test_state_12345"
        _oauth_states[state] = datetime.utcnow()
        
        assert service.validate_state(state) is True
        assert state not in _oauth_states  # Should be consumed

    @patch('src.services.github_auth.get_settings')
    def test_validate_state_returns_false_for_unknown_state(self, mock_settings):
        """Should reject unknown state."""
        mock_settings.return_value = MagicMock()
        
        service = GitHubAuthService()
        
        assert service.validate_state("unknown_state") is False

    @patch('src.services.github_auth.get_settings')
    def test_validate_state_returns_false_for_expired_state(self, mock_settings):
        """Should reject expired state (older than 10 minutes)."""
        mock_settings.return_value = MagicMock()
        
        service = GitHubAuthService()
        state = "expired_state"
        _oauth_states[state] = datetime.utcnow() - timedelta(minutes=15)
        
        assert service.validate_state(state) is False


class TestGitHubAuthServiceSessions:
    """Tests for session management."""

    def setup_method(self):
        """Clear sessions before each test."""
        _sessions.clear()

    @patch('src.services.github_auth.get_settings')
    def test_get_session_returns_none_for_unknown_id(self, mock_settings):
        """Should return None for unknown session ID."""
        mock_settings.return_value = MagicMock()
        
        service = GitHubAuthService()
        
        assert service.get_session("unknown_id") is None
        assert service.get_session(uuid4()) is None

    @patch('src.services.github_auth.get_settings')
    def test_get_session_returns_session_for_valid_id(self, mock_settings):
        """Should return session for valid ID."""
        mock_settings.return_value = MagicMock()
        
        service = GitHubAuthService()
        session = UserSession(
            github_user_id="12345",
            github_username="testuser",
            access_token="test_token",
        )
        _sessions[str(session.session_id)] = session
        
        retrieved = service.get_session(session.session_id)
        
        assert retrieved is not None
        assert retrieved.github_username == "testuser"

    @patch('src.services.github_auth.get_settings')
    def test_update_session_updates_timestamp(self, mock_settings):
        """Should update the updated_at timestamp."""
        mock_settings.return_value = MagicMock()
        
        service = GitHubAuthService()
        session = UserSession(
            github_user_id="12345",
            github_username="testuser",
            access_token="test_token",
        )
        original_updated_at = session.updated_at
        
        # Small delay to ensure timestamp changes
        import time
        time.sleep(0.01)
        
        service.update_session(session)
        
        assert session.updated_at > original_updated_at
        assert str(session.session_id) in _sessions

    @patch('src.services.github_auth.get_settings')
    def test_revoke_session_removes_session(self, mock_settings):
        """Should remove session from storage."""
        mock_settings.return_value = MagicMock()
        
        service = GitHubAuthService()
        session = UserSession(
            github_user_id="12345",
            github_username="testuser",
            access_token="test_token",
        )
        _sessions[str(session.session_id)] = session
        
        result = service.revoke_session(session.session_id)
        
        assert result is True
        assert str(session.session_id) not in _sessions

    @patch('src.services.github_auth.get_settings')
    def test_revoke_session_returns_false_for_unknown_id(self, mock_settings):
        """Should return False for unknown session ID."""
        mock_settings.return_value = MagicMock()
        
        service = GitHubAuthService()
        
        result = service.revoke_session("unknown_id")
        
        assert result is False


class TestGitHubAuthServiceTokenExchange:
    """Tests for token exchange (async methods)."""

    @pytest.mark.asyncio
    @patch('src.services.github_auth.get_settings')
    async def test_exchange_code_for_token_calls_github(self, mock_settings):
        """Should call GitHub token endpoint with correct params."""
        mock_settings.return_value = MagicMock(
            github_client_id="test_client_id",
            github_client_secret="test_secret",
            github_redirect_uri="http://localhost:8000/callback",
        )
        
        service = GitHubAuthService()
        
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "access_token": "gho_test_token",
            "token_type": "bearer",
            "scope": "read:user",
        }
        mock_response.raise_for_status = MagicMock()
        
        service._client.post = AsyncMock(return_value=mock_response)
        
        result = await service.exchange_code_for_token("test_code")
        
        assert result["access_token"] == "gho_test_token"
        service._client.post.assert_called_once()

    @pytest.mark.asyncio
    @patch('src.services.github_auth.get_settings')
    async def test_get_github_user_calls_user_api(self, mock_settings):
        """Should call GitHub user API with access token."""
        mock_settings.return_value = MagicMock()
        
        service = GitHubAuthService()
        
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "id": 12345678,
            "login": "testuser",
            "avatar_url": "https://avatars.githubusercontent.com/u/12345678",
        }
        mock_response.raise_for_status = MagicMock()
        
        service._client.get = AsyncMock(return_value=mock_response)
        
        result = await service.get_github_user("test_access_token")
        
        assert result["login"] == "testuser"
        assert result["id"] == 12345678

    @pytest.mark.asyncio
    @patch('src.services.github_auth.get_settings')
    async def test_create_session_creates_session_from_code(self, mock_settings):
        """Should create a complete session from OAuth code."""
        mock_settings.return_value = MagicMock(
            github_client_id="test_client_id",
            github_client_secret="test_secret",
            github_redirect_uri="http://localhost:8000/callback",
        )
        
        service = GitHubAuthService()
        
        # Mock token exchange
        token_response = MagicMock()
        token_response.json.return_value = {
            "access_token": "gho_test_token",
            "refresh_token": "ghr_refresh",
            "expires_in": 3600,
        }
        token_response.raise_for_status = MagicMock()
        
        # Mock user info
        user_response = MagicMock()
        user_response.json.return_value = {
            "id": 12345678,
            "login": "testuser",
            "avatar_url": "https://avatars.githubusercontent.com/u/12345678",
        }
        user_response.raise_for_status = MagicMock()
        
        service._client.post = AsyncMock(return_value=token_response)
        service._client.get = AsyncMock(return_value=user_response)
        
        _sessions.clear()
        session = await service.create_session("test_code")
        
        assert session.github_user_id == "12345678"
        assert session.github_username == "testuser"
        assert session.access_token == "gho_test_token"
        assert session.refresh_token == "ghr_refresh"
        assert str(session.session_id) in _sessions
