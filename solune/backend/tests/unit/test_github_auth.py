"""Unit tests for GitHub authentication service."""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from urllib.parse import parse_qs, urlparse
from uuid import uuid4

import pytest
from githubkit.retry import RETRY_RATE_LIMIT, RETRY_SERVER_ERROR

from src.models.user import UserSession
from src.services.github_auth import (
    _OAUTH_STATE_TTL,
    GITHUB_AUTHORIZE_URL,
    GITHUB_TOKEN_URL,
    GitHubAuthService,
    _oauth_states,
    _prune_expired_states,
)


class TestGitHubAuthServiceOAuth:
    """Tests for OAuth URL generation and state validation."""

    def setup_method(self):
        """Clear state before each test."""
        _oauth_states.clear()

    @patch("src.services.github_auth.get_settings")
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
        assert "scope=read%3Auser+read%3Aorg+project+repo" in url
        assert len(state) > 20  # State should be a secure token

    @patch("src.services.github_auth.get_settings")
    def test_generate_oauth_url_stores_state(self, mock_settings):
        """Should store state for later validation."""
        mock_settings.return_value = MagicMock(
            github_client_id="test_client_id",
            github_redirect_uri="http://localhost:8000/callback",
        )

        service = GitHubAuthService()
        _, state = service.generate_oauth_url()

        assert state in _oauth_states

    @patch("src.services.github_auth.get_settings")
    def test_validate_state_returns_true_for_valid_state(self, mock_settings):
        """Should validate valid, non-expired state."""
        mock_settings.return_value = MagicMock()

        service = GitHubAuthService()
        state = "test_state_12345"
        _oauth_states[state] = datetime.now(UTC)

        assert service.validate_state(state) is True
        assert state not in _oauth_states  # Should be consumed

    @patch("src.services.github_auth.get_settings")
    def test_validate_state_returns_false_for_unknown_state(self, mock_settings):
        """Should reject unknown state."""
        mock_settings.return_value = MagicMock()

        service = GitHubAuthService()

        assert service.validate_state("unknown_state") is False

    @patch("src.services.github_auth.get_settings")
    def test_validate_state_returns_false_for_expired_state(self, mock_settings):
        """Should reject expired state (older than 10 minutes)."""
        mock_settings.return_value = MagicMock()

        service = GitHubAuthService()
        state = "expired_state"
        _oauth_states[state] = datetime.now(UTC) - timedelta(minutes=15)

        assert service.validate_state(state) is False


class TestGitHubAuthServiceSessions:
    """Tests for session management (async, backed by session store)."""

    @pytest.mark.asyncio
    @patch("src.services.github_auth.get_db", return_value=MagicMock())
    @patch("src.services.github_auth.get_settings")
    async def test_get_session_returns_none_for_unknown_id(self, mock_settings, _mock_db):
        """Should return None for unknown session ID."""
        mock_settings.return_value = MagicMock()

        service = GitHubAuthService()

        with patch(
            "src.services.github_auth.store_get_session",
            new_callable=AsyncMock,
            return_value=None,
        ):
            assert await service.get_session("unknown_id") is None
            assert await service.get_session(uuid4()) is None

    @pytest.mark.asyncio
    @patch("src.services.github_auth.get_db", return_value=MagicMock())
    @patch("src.services.github_auth.get_settings")
    async def test_get_session_returns_session_for_valid_id(self, mock_settings, _mock_db):
        """Should return session for valid ID."""
        mock_settings.return_value = MagicMock()

        service = GitHubAuthService()
        session = UserSession(
            github_user_id="12345",
            github_username="testuser",
            access_token="test_token",
        )

        with patch(
            "src.services.github_auth.store_get_session",
            new_callable=AsyncMock,
            return_value=session,
        ):
            retrieved = await service.get_session(session.session_id)

        assert retrieved is not None
        assert retrieved.github_username == "testuser"

    @pytest.mark.asyncio
    @patch("src.services.github_auth.get_db", return_value=MagicMock())
    @patch("src.services.github_auth.get_settings")
    async def test_update_session_updates_timestamp(self, mock_settings, _mock_db):
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

        with patch(
            "src.services.github_auth.store_save_session",
            new_callable=AsyncMock,
        ):
            await service.update_session(session)

        assert session.updated_at > original_updated_at

    @pytest.mark.asyncio
    @patch("src.services.github_auth.get_db", return_value=MagicMock())
    @patch("src.services.github_auth.get_settings")
    async def test_revoke_session_removes_session(self, mock_settings, _mock_db):
        """Should remove session from storage."""
        mock_settings.return_value = MagicMock()

        service = GitHubAuthService()
        session = UserSession(
            github_user_id="12345",
            github_username="testuser",
            access_token="test_token",
        )

        with patch(
            "src.services.github_auth.store_delete_session",
            new_callable=AsyncMock,
            return_value=True,
        ):
            result = await service.revoke_session(session.session_id)

        assert result is True

    @pytest.mark.asyncio
    @patch("src.services.github_auth.get_db", return_value=MagicMock())
    @patch("src.services.github_auth.get_settings")
    async def test_revoke_session_returns_false_for_unknown_id(self, mock_settings, _mock_db):
        """Should return False for unknown session ID."""
        mock_settings.return_value = MagicMock()

        service = GitHubAuthService()

        with patch(
            "src.services.github_auth.store_delete_session",
            new_callable=AsyncMock,
            return_value=False,
        ):
            result = await service.revoke_session("unknown_id")

        assert result is False


class TestGitHubAuthServiceTokenExchange:
    """Tests for token exchange (async methods)."""

    @pytest.mark.asyncio
    @patch("src.services.github_auth.get_settings")
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

        with patch("src.services.github_auth.GitHub") as MockGitHub:
            mock_gh = AsyncMock()
            mock_gh.arequest = AsyncMock(return_value=mock_response)
            MockGitHub.return_value = mock_gh

            result = await service.exchange_code_for_token("test_code")

            assert result["access_token"] == "gho_test_token"
            mock_gh.arequest.assert_called_once()

    @pytest.mark.asyncio
    @patch("src.services.github_auth.get_settings")
    async def test_get_github_user_calls_user_api(self, mock_settings):
        """Should call GitHub user API with access token."""
        mock_settings.return_value = MagicMock()

        service = GitHubAuthService()

        user_dict = {
            "id": 12345678,
            "login": "testuser",
            "avatar_url": "https://avatars.githubusercontent.com/u/12345678",
        }
        mock_response = MagicMock()
        mock_response.parsed_data.model_dump.return_value = user_dict

        with patch("src.services.github_auth.GitHub") as MockGitHub:
            mock_gh = MagicMock()
            mock_gh.rest.users.async_get_authenticated = AsyncMock(return_value=mock_response)
            MockGitHub.return_value = mock_gh

            result = await service.get_github_user("test_access_token")

            assert result["login"] == "testuser"
            assert result["id"] == 12345678

    @pytest.mark.asyncio
    @patch("src.services.github_auth.get_db", return_value=MagicMock())
    @patch("src.services.github_auth.get_settings")
    async def test_create_session_creates_session_from_code(self, mock_settings, _mock_db):
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

        service.exchange_code_for_token = AsyncMock(return_value=token_response.json.return_value)
        service.get_github_user = AsyncMock(return_value=user_response.json.return_value)

        with patch(
            "src.services.github_auth.store_save_session",
            new_callable=AsyncMock,
        ):
            session = await service.create_session("test_code")

        assert session.github_user_id == "12345678"
        assert session.github_username == "testuser"
        assert session.access_token == "gho_test_token"
        assert session.refresh_token == "ghr_refresh"

    @pytest.mark.asyncio
    @patch("src.services.github_auth.get_settings")
    async def test_close_is_noop(self, mock_settings):
        """Close should be a no-op (SDK manages connections)."""
        mock_settings.return_value = MagicMock()
        service = GitHubAuthService()
        await service.close()  # Should not raise

    @pytest.mark.asyncio
    @patch("src.services.github_auth.get_settings")
    async def test_create_session_raises_on_oauth_error(self, mock_settings):
        """Should raise ValueError when token exchange returns an error."""
        mock_settings.return_value = MagicMock(
            github_client_id="cid",
            github_client_secret="csec",
            github_redirect_uri="http://localhost/cb",
        )
        service = GitHubAuthService()

        error_response = MagicMock()
        error_response.json.return_value = {
            "error": "bad_verification_code",
            "error_description": "The code has expired",
        }
        error_response.raise_for_status = MagicMock()
        service.exchange_code_for_token = AsyncMock(return_value=error_response.json.return_value)

        with pytest.raises(ValueError, match=r"OAuth error.*The code has expired"):
            await service.create_session("expired_code")

    @pytest.mark.asyncio
    @patch("src.services.github_auth.store_save_session", new_callable=AsyncMock)
    @patch("src.services.github_auth.get_db", return_value=MagicMock())
    @patch("src.services.github_auth.get_settings")
    async def test_refresh_token_happy_path(self, mock_settings, _mock_db, _mock_save):
        """Should refresh tokens and update session."""
        mock_settings.return_value = MagicMock(
            github_client_id="cid",
            github_client_secret="csec",
        )
        service = GitHubAuthService()

        session = UserSession(
            github_user_id="123",
            github_username="user",
            access_token="old_token",
            refresh_token="old_refresh",
        )

        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "access_token": "new_token",
            "refresh_token": "new_refresh",
            "expires_in": 7200,
        }
        mock_resp.raise_for_status = MagicMock()
        with patch("src.services.github_auth.GitHub") as MockGitHub:
            mock_gh = AsyncMock()
            mock_gh.arequest = AsyncMock(return_value=mock_resp)
            MockGitHub.return_value = mock_gh

            result = await service.refresh_token(session)

        assert result.access_token == "new_token"
        assert result.refresh_token == "new_refresh"
        assert result.token_expires_at is not None
        _mock_save.assert_awaited_once()

    @pytest.mark.asyncio
    @patch("src.services.github_auth.get_settings")
    async def test_refresh_token_no_refresh_token_raises(self, mock_settings):
        """Should raise ValueError when session has no refresh token."""
        mock_settings.return_value = MagicMock()
        service = GitHubAuthService()

        session = UserSession(
            github_user_id="123",
            github_username="user",
            access_token="tok",
            refresh_token=None,
        )

        with pytest.raises(ValueError, match="No refresh token available"):
            await service.refresh_token(session)

    @pytest.mark.asyncio
    @patch("src.services.github_auth.get_settings")
    async def test_refresh_token_error_response_raises(self, mock_settings):
        """Should raise ValueError when GitHub returns an error on refresh."""
        mock_settings.return_value = MagicMock(
            github_client_id="cid",
            github_client_secret="csec",
        )
        service = GitHubAuthService()

        session = UserSession(
            github_user_id="123",
            github_username="user",
            access_token="tok",
            refresh_token="ref",
        )

        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "error": "bad_refresh_token",
            "error_description": "Token has been revoked",
        }
        mock_resp.raise_for_status = MagicMock()
        with patch("src.services.github_auth.GitHub") as MockGitHub:
            mock_gh = AsyncMock()
            mock_gh.arequest = AsyncMock(return_value=mock_resp)
            MockGitHub.return_value = mock_gh

            with pytest.raises(ValueError, match=r"Token refresh error.*Token has been revoked"):
                await service.refresh_token(session)

    @pytest.mark.asyncio
    @patch("src.services.github_auth.store_save_session", new_callable=AsyncMock)
    @patch("src.services.github_auth.get_db", return_value=MagicMock())
    @patch("src.services.github_auth.get_settings")
    async def test_create_session_from_token(self, mock_settings, _mock_db, _mock_save):
        """Should create a session from a Personal Access Token."""
        mock_settings.return_value = MagicMock()
        service = GitHubAuthService()

        user_response = MagicMock()
        user_response.json.return_value = {
            "id": 99999,
            "login": "patuser",
            "avatar_url": "https://example.com/avatar.png",
        }
        user_response.raise_for_status = MagicMock()
        service.get_github_user = AsyncMock(return_value=user_response.json.return_value)

        session = await service.create_session_from_token("ghp_pat_token")

        assert session.github_user_id == "99999"
        assert session.github_username == "patuser"
        assert session.access_token == "ghp_pat_token"
        assert session.refresh_token is None
        assert session.token_expires_at is None
        _mock_save.assert_awaited_once()


# =============================================================================
# Mutation-killing tests — precise assertions on exact values, keys, and
# parameter forwarding to catch string, constant, and operator mutations.
# =============================================================================


class TestGenerateOauthUrlMutationKillers:
    """Kill mutations in generate_oauth_url: string keys, scope, URL
    construction, state storage."""

    def setup_method(self):
        _oauth_states.clear()

    @patch("src.services.github_auth.get_settings")
    def test_url_contains_exact_param_keys(self, mock_settings):
        """Catch key-name mutations: 'client_id' -> 'XXclient_idXX' etc."""
        mock_settings.return_value = MagicMock(
            github_client_id="cid123",
            github_redirect_uri="http://localhost/cb",
        )
        service = GitHubAuthService()
        url, _state = service.generate_oauth_url()

        parsed = urlparse(url)
        qs = parse_qs(parsed.query)

        assert "client_id" in qs, "Missing exact key 'client_id'"
        assert "redirect_uri" in qs, "Missing exact key 'redirect_uri'"
        assert "scope" in qs, "Missing exact key 'scope'"
        assert "state" in qs, "Missing exact key 'state'"
        # Verify no mutated keys present
        for key in qs:
            assert not key.startswith("XX"), f"Mutated key found: {key}"
            assert key == key.lower(), f"Uppercased key found: {key}"

    @patch("src.services.github_auth.get_settings")
    def test_scope_exact_value(self, mock_settings):
        """Catch scope string mutation: value -> 'XX...XX' or uppercased."""
        mock_settings.return_value = MagicMock(
            github_client_id="cid",
            github_redirect_uri="http://localhost/cb",
        )
        service = GitHubAuthService()
        url, _ = service.generate_oauth_url()

        parsed = urlparse(url)
        qs = parse_qs(parsed.query)
        scope = qs["scope"][0]

        assert scope == "read:user read:org project repo"

    @patch("src.services.github_auth.get_settings")
    def test_client_id_forwarded(self, mock_settings):
        """Catch mutation that drops or replaces client_id value."""
        mock_settings.return_value = MagicMock(
            github_client_id="my_exact_client_id",
            github_redirect_uri="http://localhost/cb",
        )
        service = GitHubAuthService()
        url, _ = service.generate_oauth_url()

        qs = parse_qs(urlparse(url).query)
        assert qs["client_id"] == ["my_exact_client_id"]

    @patch("src.services.github_auth.get_settings")
    def test_redirect_uri_forwarded(self, mock_settings):
        """Catch mutation that drops or replaces redirect_uri value."""
        mock_settings.return_value = MagicMock(
            github_client_id="cid",
            github_redirect_uri="http://example.com/oauth",
        )
        service = GitHubAuthService()
        url, _ = service.generate_oauth_url()

        qs = parse_qs(urlparse(url).query)
        assert qs["redirect_uri"] == ["http://example.com/oauth"]

    @patch("src.services.github_auth.get_settings")
    def test_state_token_is_string_of_correct_length(self, mock_settings):
        """Catch mutation: token_urlsafe(32) -> None or (33)."""
        mock_settings.return_value = MagicMock(
            github_client_id="cid",
            github_redirect_uri="http://localhost/cb",
        )
        service = GitHubAuthService()
        _, state = service.generate_oauth_url()

        assert isinstance(state, str)
        # token_urlsafe(32) produces a ~43-character base64url string
        assert 40 <= len(state) <= 50

    @patch("src.services.github_auth.get_settings")
    def test_state_stored_with_datetime(self, mock_settings):
        """Catch mutation: _oauth_states[state] = None."""
        mock_settings.return_value = MagicMock(
            github_client_id="cid",
            github_redirect_uri="http://localhost/cb",
        )
        service = GitHubAuthService()
        _, state = service.generate_oauth_url()

        assert state in _oauth_states
        stored = _oauth_states[state]
        assert isinstance(stored, datetime)
        # Should be very recent
        assert datetime.now(UTC) - stored < timedelta(seconds=5)

    @patch("src.services.github_auth.get_settings")
    def test_url_starts_with_github_authorize(self, mock_settings):
        """Catch mutation replacing URL = None."""
        mock_settings.return_value = MagicMock(
            github_client_id="cid",
            github_redirect_uri="http://localhost/cb",
        )
        service = GitHubAuthService()
        url, _ = service.generate_oauth_url()

        assert url.startswith(GITHUB_AUTHORIZE_URL + "?")

    @patch("src.services.github_auth.get_settings")
    def test_state_in_url_matches_returned_state(self, mock_settings):
        """Catch mutation: urlencode(None) or swapped return values."""
        mock_settings.return_value = MagicMock(
            github_client_id="cid",
            github_redirect_uri="http://localhost/cb",
        )
        service = GitHubAuthService()
        url, state = service.generate_oauth_url()

        qs = parse_qs(urlparse(url).query)
        assert qs["state"] == [state]

    @patch("src.services.github_auth.get_settings")
    def test_prune_called_during_generation(self, mock_settings):
        """Catch mutation that removes _prune_expired_states() call."""
        mock_settings.return_value = MagicMock(
            github_client_id="cid",
            github_redirect_uri="http://localhost/cb",
        )
        service = GitHubAuthService()

        # Insert an expired state
        _oauth_states["old_expired"] = datetime.now(UTC) - timedelta(minutes=15)

        service.generate_oauth_url()

        # Expired state should have been pruned
        assert "old_expired" not in _oauth_states

    @patch("src.services.github_auth.secrets")
    @patch("src.services.github_auth.get_settings")
    def test_token_urlsafe_called_with_32(self, mock_settings, mock_secrets):
        """Kill mutmut_2 (None) and mutmut_3 (33): verify exact arg."""
        mock_settings.return_value = MagicMock(
            github_client_id="cid",
            github_redirect_uri="http://localhost/cb",
        )
        mock_secrets.token_urlsafe.return_value = "fake_state_token"
        service = GitHubAuthService()
        _, state = service.generate_oauth_url()
        mock_secrets.token_urlsafe.assert_called_once_with(32)
        assert state == "fake_state_token"


class TestValidateStateMutationKillers:
    """Kill mutations in validate_state: comparison operators, pop vs get,
    TTL boundary."""

    def setup_method(self):
        _oauth_states.clear()

    @patch("src.services.github_auth.get_settings")
    def test_valid_state_returns_true(self, mock_settings):
        mock_settings.return_value = MagicMock()
        service = GitHubAuthService()
        _oauth_states["s1"] = datetime.now(UTC)
        assert service.validate_state("s1") is True

    @patch("src.services.github_auth.get_settings")
    def test_unknown_state_returns_false(self, mock_settings):
        mock_settings.return_value = MagicMock()
        service = GitHubAuthService()
        assert service.validate_state("nope") is False

    @patch("src.services.github_auth.get_settings")
    def test_expired_state_returns_false(self, mock_settings):
        mock_settings.return_value = MagicMock()
        service = GitHubAuthService()
        _oauth_states["exp"] = datetime.now(UTC) - timedelta(minutes=15)
        assert service.validate_state("exp") is False

    @patch("src.services.github_auth.get_settings")
    def test_state_consumed_after_validation(self, mock_settings):
        """Catch mutation: pop -> get (state not consumed)."""
        mock_settings.return_value = MagicMock()
        service = GitHubAuthService()
        _oauth_states["once"] = datetime.now(UTC)

        service.validate_state("once")
        # State must be removed — second call must fail
        assert "once" not in _oauth_states

    @patch("src.services.github_auth.get_settings")
    def test_state_at_exact_ttl_boundary_is_rejected(self, mock_settings):
        """Catch operator mutation: < -> <= (state exactly at TTL should fail)."""
        mock_settings.return_value = MagicMock()
        service = GitHubAuthService()
        # State created exactly _OAUTH_STATE_TTL ago
        _oauth_states["boundary"] = datetime.now(UTC) - _OAUTH_STATE_TTL
        assert service.validate_state("boundary") is False

    @patch("src.services.github_auth.get_settings")
    def test_state_just_before_ttl_is_accepted(self, mock_settings):
        """State 1 second before TTL should still be valid."""
        mock_settings.return_value = MagicMock()
        service = GitHubAuthService()
        _oauth_states["almost"] = datetime.now(UTC) - _OAUTH_STATE_TTL + timedelta(seconds=1)
        assert service.validate_state("almost") is True

    @patch("src.services.github_auth.get_settings")
    @patch("src.services.github_auth.datetime")
    def test_boundary_frozen_time(self, mock_dt, mock_settings):
        """Kill mutmut_7 (< → <=) using frozen time for exact boundary."""
        mock_settings.return_value = MagicMock()
        frozen = datetime(2025, 6, 1, tzinfo=UTC)
        mock_dt.now.return_value = frozen
        service = GitHubAuthService()
        _oauth_states["b"] = frozen - _OAUTH_STATE_TTL
        assert service.validate_state("b") is False


class TestExchangeCodeMutationKillers:
    """Kill mutations in exchange_code_for_token: verify exact params
    passed to GitHub API."""

    @pytest.mark.asyncio
    @patch("src.services.github_auth.get_settings")
    async def test_exact_request_params(self, mock_settings):
        """Catch mutations in data dict keys/values and headers."""
        mock_settings.return_value = MagicMock(
            github_client_id="cid_val",
            github_client_secret="csec_val",
            github_redirect_uri="http://redir.test/cb",
        )
        service = GitHubAuthService()

        mock_response = MagicMock()
        mock_response.json.return_value = {"access_token": "t"}

        with patch("src.services.github_auth.GitHub") as MockGH:
            mock_gh = AsyncMock()
            mock_gh.arequest = AsyncMock(return_value=mock_response)
            MockGH.return_value = mock_gh

            await service.exchange_code_for_token("the_code")

            mock_gh.arequest.assert_called_once()
            call_args = mock_gh.arequest.call_args

            # Verify HTTP method
            assert call_args[0][0] == "POST"
            # Verify URL
            assert call_args[0][1] == GITHUB_TOKEN_URL

            data = call_args[1]["data"]
            assert data["client_id"] == "cid_val"
            assert data["client_secret"] == "csec_val"
            assert data["code"] == "the_code"
            assert data["redirect_uri"] == "http://redir.test/cb"
            assert set(data.keys()) == {"client_id", "client_secret", "code", "redirect_uri"}

            headers = call_args[1]["headers"]
            assert headers["Accept"] == "application/json"

    @pytest.mark.asyncio
    @patch("src.services.github_auth.get_settings")
    async def test_github_sdk_constructor_args(self, mock_settings):
        """Kill SDK constructor mutations: TokenAuthStrategy, auto_retry, RetryChainDecision."""
        mock_settings.return_value = MagicMock(
            github_client_id="c",
            github_client_secret="s",
            github_redirect_uri="http://r",
        )
        service = GitHubAuthService()
        mock_response = MagicMock()
        mock_response.json.return_value = {"access_token": "t"}

        with (
            patch("src.services.github_auth.GitHub") as MockGH,
            patch("src.services.github_auth.TokenAuthStrategy") as MockTAS,
            patch("src.services.github_auth.RetryChainDecision") as MockRCD,
        ):
            sentinel_auth = MagicMock(name="auth")
            sentinel_retry = MagicMock(name="retry")
            MockTAS.return_value = sentinel_auth
            MockRCD.return_value = sentinel_retry
            mock_gh = AsyncMock()
            mock_gh.arequest = AsyncMock(return_value=mock_response)
            MockGH.return_value = mock_gh

            await service.exchange_code_for_token("code")

            MockTAS.assert_called_once_with("placeholder")
            MockRCD.assert_called_once_with(RETRY_RATE_LIMIT, RETRY_SERVER_ERROR)
            MockGH.assert_called_once_with(sentinel_auth, auto_retry=sentinel_retry)


class TestGetGithubUserMutationKillers:
    """Kill mutations in get_github_user: verify token is used and
    response is correctly unpacked."""

    @pytest.mark.asyncio
    @patch("src.services.github_auth.get_settings")
    async def test_token_forwarded_to_github_client(self, mock_settings):
        """Catch mutation: TokenAuthStrategy arg changed."""
        mock_settings.return_value = MagicMock()
        service = GitHubAuthService()

        mock_parsed = MagicMock()
        mock_parsed.model_dump.return_value = {"id": 1, "login": "u"}
        mock_resp = MagicMock()
        mock_resp.parsed_data = mock_parsed

        with patch("src.services.github_auth.GitHub") as MockGH:
            mock_gh = MagicMock()
            mock_gh.rest.users.async_get_authenticated = AsyncMock(return_value=mock_resp)
            MockGH.return_value = mock_gh

            result = await service.get_github_user("exact_token_123")

            # Verify TokenAuthStrategy was called with the exact token
            from githubkit import TokenAuthStrategy

            auth_arg = MockGH.call_args[0][0]
            assert isinstance(auth_arg, TokenAuthStrategy)

            # Verify model_dump is called (mutation: drop .model_dump())
            mock_parsed.model_dump.assert_called_once()
            assert result == {"id": 1, "login": "u"}

    @pytest.mark.asyncio
    @patch("src.services.github_auth.get_settings")
    async def test_github_sdk_constructor_args(self, mock_settings):
        """Kill SDK constructor mutations: token value, auto_retry, RetryChainDecision."""
        mock_settings.return_value = MagicMock()
        service = GitHubAuthService()
        mock_parsed = MagicMock()
        mock_parsed.model_dump.return_value = {"id": 1, "login": "u"}
        mock_resp = MagicMock()
        mock_resp.parsed_data = mock_parsed

        with (
            patch("src.services.github_auth.GitHub") as MockGH,
            patch("src.services.github_auth.TokenAuthStrategy") as MockTAS,
            patch("src.services.github_auth.RetryChainDecision") as MockRCD,
        ):
            sentinel_auth = MagicMock(name="auth")
            sentinel_retry = MagicMock(name="retry")
            MockTAS.return_value = sentinel_auth
            MockRCD.return_value = sentinel_retry
            mock_gh = MagicMock()
            mock_gh.rest.users.async_get_authenticated = AsyncMock(return_value=mock_resp)
            MockGH.return_value = mock_gh

            await service.get_github_user("exact_token_abc")

            MockTAS.assert_called_once_with("exact_token_abc")
            MockRCD.assert_called_once_with(RETRY_RATE_LIMIT, RETRY_SERVER_ERROR)
            MockGH.assert_called_once_with(sentinel_auth, auto_retry=sentinel_retry)


class TestCreateSessionMutationKillers:
    """Kill mutations in create_session: field mapping, error handling,
    expires_in branches."""

    @pytest.mark.asyncio
    @patch("src.services.github_auth.store_save_session", new_callable=AsyncMock)
    @patch("src.services.github_auth.get_db", return_value=MagicMock())
    @patch("src.services.github_auth.get_settings")
    async def test_session_fields_exact_mapping(self, mock_settings, _db, mock_save):
        """Catch mutations: wrong dict key, str() dropped, field swapped."""
        mock_settings.return_value = MagicMock(
            github_client_id="c",
            github_client_secret="s",
            github_redirect_uri="http://r",
        )
        service = GitHubAuthService()

        service.exchange_code_for_token = AsyncMock(
            return_value={
                "access_token": "tok_abc",
                "refresh_token": "ref_xyz",
                "expires_in": 3600,
            }
        )
        service.get_github_user = AsyncMock(
            return_value={
                "id": 42,
                "login": "alice",
                "avatar_url": "https://img/alice.png",
            }
        )

        session = await service.create_session("code1")

        assert session.github_user_id == "42"  # str() applied
        assert session.github_username == "alice"
        assert session.github_avatar_url == "https://img/alice.png"
        assert session.access_token == "tok_abc"
        assert session.refresh_token == "ref_xyz"
        assert session.token_expires_at is not None
        # Token should expire roughly 3600 seconds from now
        delta = session.token_expires_at - datetime.now(UTC)
        assert 3500 < delta.total_seconds() < 3700

    @pytest.mark.asyncio
    @patch("src.services.github_auth.store_save_session", new_callable=AsyncMock)
    @patch("src.services.github_auth.get_db", return_value=MagicMock())
    @patch("src.services.github_auth.get_settings")
    async def test_session_without_expires_in(self, mock_settings, _db, _save):
        """Kill mutation on 'if expires_in:' branch (false path)."""
        mock_settings.return_value = MagicMock(
            github_client_id="c",
            github_client_secret="s",
            github_redirect_uri="http://r",
        )
        service = GitHubAuthService()

        service.exchange_code_for_token = AsyncMock(
            return_value={
                "access_token": "tok",
                # No refresh_token, no expires_in
            }
        )
        service.get_github_user = AsyncMock(return_value={"id": 1, "login": "u"})

        session = await service.create_session("code2")

        assert session.token_expires_at is None
        assert session.refresh_token is None
        assert session.github_avatar_url is None

    @pytest.mark.asyncio
    @patch("src.services.github_auth.get_settings")
    async def test_create_session_error_without_description(self, mock_settings):
        """Catch mutation in error message format: uses error key as fallback."""
        mock_settings.return_value = MagicMock(
            github_client_id="c",
            github_client_secret="s",
            github_redirect_uri="http://r",
        )
        service = GitHubAuthService()

        service.exchange_code_for_token = AsyncMock(
            return_value={
                "error": "bad_code",
                # No error_description — should fall back to error key
            }
        )

        with pytest.raises(ValueError, match="bad_code"):
            await service.create_session("bad")

    @pytest.mark.asyncio
    @patch("src.services.github_auth.store_save_session", new_callable=AsyncMock)
    @patch("src.services.github_auth.get_db")
    @patch("src.services.github_auth.get_settings")
    async def test_session_saved_to_db(self, mock_settings, mock_db, mock_save):
        """Catch mutation: store_save_session call removed or args wrong."""
        mock_settings.return_value = MagicMock(
            github_client_id="c",
            github_client_secret="s",
            github_redirect_uri="http://r",
        )
        db_sentinel = MagicMock(name="db_sentinel")
        mock_db.return_value = db_sentinel
        service = GitHubAuthService()
        service.exchange_code_for_token = AsyncMock(return_value={"access_token": "t"})
        service.get_github_user = AsyncMock(return_value={"id": 1, "login": "u"})

        session = await service.create_session("c")

        mock_db.assert_called_once()
        mock_save.assert_awaited_once_with(db_sentinel, session)

    @pytest.mark.asyncio
    @patch("src.services.github_auth.store_save_session", new_callable=AsyncMock)
    @patch("src.services.github_auth.get_db", return_value=MagicMock())
    @patch("src.services.github_auth.get_settings")
    async def test_logger_called_with_username(self, mock_settings, _db, _save):
        """Catch mutation: logger.info args mutated to None."""
        mock_settings.return_value = MagicMock(
            github_client_id="c",
            github_client_secret="s",
            github_redirect_uri="http://r",
        )
        service = GitHubAuthService()
        service.exchange_code_for_token = AsyncMock(return_value={"access_token": "t"})
        service.get_github_user = AsyncMock(return_value={"id": 1, "login": "created_user"})

        with patch("src.services.github_auth.logger") as mock_logger:
            await service.create_session("c")
            mock_logger.info.assert_called_once()
            fmt_args = mock_logger.info.call_args[0]
            assert len(fmt_args) == 2
            assert fmt_args[0] == "Created session for user %s"
            assert fmt_args[1] == "created_user"

    @pytest.mark.asyncio
    @patch("src.services.github_auth.store_save_session", new_callable=AsyncMock)
    @patch("src.services.github_auth.get_db", return_value=MagicMock())
    @patch("src.services.github_auth.get_settings")
    async def test_arg_forwarding_to_helpers(self, mock_settings, _db, _save):
        """Kill mutmut_2 (code→None) and mutmut_27 (access_token→None)."""
        mock_settings.return_value = MagicMock(
            github_client_id="c",
            github_client_secret="s",
            github_redirect_uri="http://r",
        )
        service = GitHubAuthService()
        service.exchange_code_for_token = AsyncMock(return_value={"access_token": "tok_sentinel"})
        service.get_github_user = AsyncMock(return_value={"id": 1, "login": "u"})

        await service.create_session("exact_code_value")

        service.exchange_code_for_token.assert_awaited_once_with("exact_code_value")
        service.get_github_user.assert_awaited_once_with("tok_sentinel")


class TestRefreshTokenMutationKillers:
    """Kill mutations in refresh_token: param forwarding, field updates,
    expires_in branch, fallback refresh_token."""

    @pytest.mark.asyncio
    @patch("src.services.github_auth.store_save_session", new_callable=AsyncMock)
    @patch("src.services.github_auth.get_db")
    @patch("src.services.github_auth.get_settings")
    async def test_exact_request_params(self, mock_settings, mock_db, _save):
        """Catch mutations in data dict keys and grant_type value."""
        mock_settings.return_value = MagicMock(
            github_client_id="cid",
            github_client_secret="csec",
        )
        db_sentinel = MagicMock(name="db_sentinel")
        mock_db.return_value = db_sentinel
        service = GitHubAuthService()
        session = UserSession(
            github_user_id="1",
            github_username="u",
            access_token="old",
            refresh_token="old_ref",
        )

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"access_token": "new", "expires_in": 7200}

        with patch("src.services.github_auth.GitHub") as MockGH:
            mock_gh = AsyncMock()
            mock_gh.arequest = AsyncMock(return_value=mock_resp)
            MockGH.return_value = mock_gh

            await service.refresh_token(session)

            data = mock_gh.arequest.call_args[1]["data"]
            assert data["client_id"] == "cid"
            assert data["client_secret"] == "csec"
            assert data["grant_type"] == "refresh_token"
            assert data["refresh_token"] == "old_ref"
            assert set(data.keys()) == {"client_id", "client_secret", "grant_type", "refresh_token"}

            headers = mock_gh.arequest.call_args[1]["headers"]
            assert headers["Accept"] == "application/json"

    @pytest.mark.asyncio
    @patch("src.services.github_auth.store_save_session", new_callable=AsyncMock)
    @patch("src.services.github_auth.get_db")
    @patch("src.services.github_auth.get_settings")
    async def test_refresh_saves_to_db_with_correct_args(self, mock_settings, mock_db, mock_save):
        """Catch mutation: store_save_session call removed or db=None."""
        mock_settings.return_value = MagicMock(
            github_client_id="c",
            github_client_secret="s",
        )
        db_sentinel = MagicMock(name="db_sentinel")
        mock_db.return_value = db_sentinel
        service = GitHubAuthService()
        session = UserSession(
            github_user_id="1",
            github_username="u",
            access_token="old",
            refresh_token="ref",
        )

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"access_token": "new"}

        with patch("src.services.github_auth.GitHub") as MockGH:
            mock_gh = AsyncMock()
            mock_gh.arequest = AsyncMock(return_value=mock_resp)
            MockGH.return_value = mock_gh

            await service.refresh_token(session)

        mock_db.assert_called_once()
        mock_save.assert_awaited_once_with(db_sentinel, session)

    @pytest.mark.asyncio
    @patch("src.services.github_auth.store_save_session", new_callable=AsyncMock)
    @patch("src.services.github_auth.get_db", return_value=MagicMock())
    @patch("src.services.github_auth.get_settings")
    async def test_refresh_logger_called(self, mock_settings, _db, _save):
        """Catch mutation: logger.info args mutated."""
        mock_settings.return_value = MagicMock(
            github_client_id="c",
            github_client_secret="s",
        )
        service = GitHubAuthService()
        session = UserSession(
            github_user_id="1",
            github_username="refresh_user",
            access_token="old",
            refresh_token="ref",
        )

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"access_token": "new"}

        with patch("src.services.github_auth.GitHub") as MockGH:
            mock_gh = AsyncMock()
            mock_gh.arequest = AsyncMock(return_value=mock_resp)
            MockGH.return_value = mock_gh

            with patch("src.services.github_auth.logger") as mock_logger:
                await service.refresh_token(session)
                mock_logger.info.assert_called_once()
                fmt_args = mock_logger.info.call_args[0]
                assert len(fmt_args) == 2
                assert fmt_args[0] == "Refreshed token for user %s"
                assert fmt_args[1] == "refresh_user"

    @pytest.mark.asyncio
    @patch("src.services.github_auth.store_save_session", new_callable=AsyncMock)
    @patch("src.services.github_auth.get_db", return_value=MagicMock())
    @patch("src.services.github_auth.get_settings")
    async def test_refresh_keeps_old_refresh_token_when_missing(self, mock_settings, _db, _save):
        """Catch mutation: .get('refresh_token', session.refresh_token) changed."""
        mock_settings.return_value = MagicMock(
            github_client_id="c",
            github_client_secret="s",
        )
        service = GitHubAuthService()
        session = UserSession(
            github_user_id="1",
            github_username="u",
            access_token="old",
            refresh_token="keep_me",
        )

        mock_resp = MagicMock()
        # Response has NO refresh_token
        mock_resp.json.return_value = {"access_token": "new_tok", "expires_in": 3600}

        with patch("src.services.github_auth.GitHub") as MockGH:
            mock_gh = AsyncMock()
            mock_gh.arequest = AsyncMock(return_value=mock_resp)
            MockGH.return_value = mock_gh

            result = await service.refresh_token(session)

        assert result.access_token == "new_tok"
        assert result.refresh_token == "keep_me"  # preserved

    @pytest.mark.asyncio
    @patch("src.services.github_auth.store_save_session", new_callable=AsyncMock)
    @patch("src.services.github_auth.get_db", return_value=MagicMock())
    @patch("src.services.github_auth.get_settings")
    async def test_refresh_without_expires_in(self, mock_settings, _db, _save):
        """Kill mutation on 'if expires_in:' false path in refresh_token."""
        mock_settings.return_value = MagicMock(
            github_client_id="c",
            github_client_secret="s",
        )
        service = GitHubAuthService()
        session = UserSession(
            github_user_id="1",
            github_username="u",
            access_token="old",
            refresh_token="ref",
            token_expires_at=None,
        )

        mock_resp = MagicMock()
        # No expires_in in response
        mock_resp.json.return_value = {"access_token": "new"}

        with patch("src.services.github_auth.GitHub") as MockGH:
            mock_gh = AsyncMock()
            mock_gh.arequest = AsyncMock(return_value=mock_resp)
            MockGH.return_value = mock_gh

            result = await service.refresh_token(session)

        assert result.access_token == "new"
        # token_expires_at should NOT have been updated
        assert result.token_expires_at is None

    @pytest.mark.asyncio
    @patch("src.services.github_auth.store_save_session", new_callable=AsyncMock)
    @patch("src.services.github_auth.get_db", return_value=MagicMock())
    @patch("src.services.github_auth.get_settings")
    async def test_refresh_updates_timestamp(self, mock_settings, _db, _save):
        """Catch mutation: session.updated_at = datetime.now(UTC) removed."""
        mock_settings.return_value = MagicMock(
            github_client_id="c",
            github_client_secret="s",
        )
        service = GitHubAuthService()
        session = UserSession(
            github_user_id="1",
            github_username="u",
            access_token="old",
            refresh_token="ref",
        )
        original_updated = session.updated_at

        import time

        time.sleep(0.01)

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"access_token": "new"}

        with patch("src.services.github_auth.GitHub") as MockGH:
            mock_gh = AsyncMock()
            mock_gh.arequest = AsyncMock(return_value=mock_resp)
            MockGH.return_value = mock_gh

            result = await service.refresh_token(session)

        assert result.updated_at > original_updated

    @pytest.mark.asyncio
    @patch("src.services.github_auth.get_settings")
    async def test_refresh_error_without_description(self, mock_settings):
        """Catch mutation in error fallback: uses error key when no description."""
        mock_settings.return_value = MagicMock(
            github_client_id="c",
            github_client_secret="s",
        )
        service = GitHubAuthService()
        session = UserSession(
            github_user_id="1",
            github_username="u",
            access_token="t",
            refresh_token="r",
        )

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"error": "expired_token"}

        with patch("src.services.github_auth.GitHub") as MockGH:
            mock_gh = AsyncMock()
            mock_gh.arequest = AsyncMock(return_value=mock_resp)
            MockGH.return_value = mock_gh

            with pytest.raises(ValueError, match="expired_token"):
                await service.refresh_token(session)

    @pytest.mark.asyncio
    @patch("src.services.github_auth.store_save_session", new_callable=AsyncMock)
    @patch("src.services.github_auth.get_db")
    @patch("src.services.github_auth.get_settings")
    async def test_arequest_method_and_url(self, mock_settings, mock_db, _save):
        """Kill mutmut_7 (POST→None), 8 (URL→None), 26 (XXPOSTXX), 27 (post)."""
        mock_settings.return_value = MagicMock(
            github_client_id="c",
            github_client_secret="s",
        )
        mock_db.return_value = MagicMock()
        service = GitHubAuthService()
        session = UserSession(
            github_user_id="1",
            github_username="u",
            access_token="old",
            refresh_token="ref",
        )
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"access_token": "new"}

        with patch("src.services.github_auth.GitHub") as MockGH:
            mock_gh = AsyncMock()
            mock_gh.arequest = AsyncMock(return_value=mock_resp)
            MockGH.return_value = mock_gh

            await service.refresh_token(session)

            args = mock_gh.arequest.call_args[0]
            assert args[0] == "POST"
            assert args[1] == GITHUB_TOKEN_URL

    @pytest.mark.asyncio
    @patch("src.services.github_auth.store_save_session", new_callable=AsyncMock)
    @patch("src.services.github_auth.get_db")
    @patch("src.services.github_auth.get_settings")
    async def test_github_sdk_constructor_args(self, mock_settings, mock_db, _save):
        """Kill SDK constructor mutations: TokenAuthStrategy, auto_retry."""
        mock_settings.return_value = MagicMock(
            github_client_id="c",
            github_client_secret="s",
        )
        mock_db.return_value = MagicMock()
        service = GitHubAuthService()
        session = UserSession(
            github_user_id="1",
            github_username="u",
            access_token="old",
            refresh_token="ref",
        )
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"access_token": "new"}

        with (
            patch("src.services.github_auth.GitHub") as MockGH,
            patch("src.services.github_auth.TokenAuthStrategy") as MockTAS,
            patch("src.services.github_auth.RetryChainDecision") as MockRCD,
        ):
            sentinel_auth = MagicMock(name="auth")
            sentinel_retry = MagicMock(name="retry")
            MockTAS.return_value = sentinel_auth
            MockRCD.return_value = sentinel_retry
            mock_gh = AsyncMock()
            mock_gh.arequest = AsyncMock(return_value=mock_resp)
            MockGH.return_value = mock_gh

            await service.refresh_token(session)

            MockTAS.assert_called_once_with("placeholder")
            MockRCD.assert_called_once_with(RETRY_RATE_LIMIT, RETRY_SERVER_ERROR)
            MockGH.assert_called_once_with(sentinel_auth, auto_retry=sentinel_retry)

    @pytest.mark.asyncio
    @patch("src.services.github_auth.store_save_session", new_callable=AsyncMock)
    @patch("src.services.github_auth.get_db", return_value=MagicMock())
    @patch("src.services.github_auth.get_settings")
    async def test_token_expires_at_future_and_aware(self, mock_settings, _db, _save):
        """Kill mutmut_71 (+→-) and mutmut_72 (UTC→None)."""
        mock_settings.return_value = MagicMock(
            github_client_id="c",
            github_client_secret="s",
        )
        service = GitHubAuthService()
        session = UserSession(
            github_user_id="1",
            github_username="u",
            access_token="old",
            refresh_token="ref",
        )
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"access_token": "new", "expires_in": 7200}

        with patch("src.services.github_auth.GitHub") as MockGH:
            mock_gh = AsyncMock()
            mock_gh.arequest = AsyncMock(return_value=mock_resp)
            MockGH.return_value = mock_gh

            result = await service.refresh_token(session)

        assert result.token_expires_at > datetime.now(UTC)
        assert result.token_expires_at.tzinfo is not None
        delta = result.token_expires_at - datetime.now(UTC)
        assert 7100 < delta.total_seconds() < 7300

    @pytest.mark.asyncio
    @patch("src.services.github_auth.get_settings")
    async def test_no_refresh_token_exact_error(self, mock_settings):
        """Kill mutmut_3: error message XX prefix."""
        mock_settings.return_value = MagicMock()
        service = GitHubAuthService()
        session = UserSession(
            github_user_id="1",
            github_username="u",
            access_token="t",
            refresh_token=None,
        )
        with pytest.raises(ValueError, match=r"^No refresh token available$"):
            await service.refresh_token(session)


class TestCreateSessionFromTokenMutationKillers:
    """Kill mutations in create_session_from_token: field values, None
    fields, DB save, get_github_user call."""

    @pytest.mark.asyncio
    @patch("src.services.github_auth.store_save_session", new_callable=AsyncMock)
    @patch("src.services.github_auth.get_db")
    @patch("src.services.github_auth.get_settings")
    async def test_pat_session_exact_fields(self, mock_settings, mock_db, mock_save):
        """Catch mutations: wrong avatar key, None not assigned, str() dropped."""
        mock_settings.return_value = MagicMock()
        db_sentinel = MagicMock(name="db_sentinel")
        mock_db.return_value = db_sentinel
        service = GitHubAuthService()
        service.get_github_user = AsyncMock(
            return_value={
                "id": 77,
                "login": "pat_user",
                "avatar_url": "https://img/77.png",
            }
        )

        session = await service.create_session_from_token("ghp_token")

        assert session.github_user_id == "77"  # str(77)
        assert session.github_username == "pat_user"
        assert session.github_avatar_url == "https://img/77.png"
        assert session.access_token == "ghp_token"
        assert session.refresh_token is None
        assert session.token_expires_at is None
        mock_save.assert_awaited_once_with(db_sentinel, session)

    @pytest.mark.asyncio
    @patch("src.services.github_auth.store_save_session", new_callable=AsyncMock)
    @patch("src.services.github_auth.get_db")
    @patch("src.services.github_auth.get_settings")
    async def test_pat_token_forwarded_to_get_github_user(self, mock_settings, mock_db, _save):
        """Catch mutation: wrong token passed to get_github_user."""
        mock_settings.return_value = MagicMock()
        mock_db.return_value = MagicMock()
        service = GitHubAuthService()
        service.get_github_user = AsyncMock(return_value={"id": 1, "login": "u"})

        await service.create_session_from_token("ghp_exact_token")

        service.get_github_user.assert_awaited_once_with("ghp_exact_token")

    @pytest.mark.asyncio
    @patch("src.services.github_auth.store_save_session", new_callable=AsyncMock)
    @patch("src.services.github_auth.get_db")
    @patch("src.services.github_auth.get_settings")
    async def test_user_data_used_not_none(self, mock_settings, mock_db, mock_save):
        """Catch mutation: user_data = None (get_github_user result dropped)."""
        mock_settings.return_value = MagicMock()
        mock_db.return_value = MagicMock()
        service = GitHubAuthService()
        service.get_github_user = AsyncMock(
            return_value={
                "id": 42,
                "login": "alice",
                "avatar_url": "https://img/alice.png",
            }
        )

        session = await service.create_session_from_token("tok")

        # If user_data was None, these would crash or be wrong
        assert session.github_user_id == "42"
        assert session.github_username == "alice"

    @pytest.mark.asyncio
    @patch("src.services.github_auth.store_save_session", new_callable=AsyncMock)
    @patch("src.services.github_auth.get_db")
    @patch("src.services.github_auth.get_settings")
    async def test_logger_called_with_username(self, mock_settings, mock_db, _save):
        """Catch mutation: logger.info args mutated."""
        mock_settings.return_value = MagicMock()
        mock_db.return_value = MagicMock()
        service = GitHubAuthService()
        service.get_github_user = AsyncMock(return_value={"id": 1, "login": "logged_user"})

        with patch("src.services.github_auth.logger") as mock_logger:
            await service.create_session_from_token("tok")
            mock_logger.info.assert_called_once()
            fmt_args = mock_logger.info.call_args[0]
            assert len(fmt_args) == 2
            assert fmt_args[0] == "Created session from PAT for user %s"
            assert fmt_args[1] == "logged_user"


class TestRevokeSessionMutationKillers:
    """Kill mutations in revoke_session: return value forwarded, logged."""

    @pytest.mark.asyncio
    @patch("src.services.github_auth.store_delete_session", new_callable=AsyncMock)
    @patch("src.services.github_auth.get_db")
    @patch("src.services.github_auth.get_settings")
    async def test_returns_exact_store_result(self, mock_settings, mock_db, mock_delete):
        """Catch mutation: return value swapped or hardcoded."""
        mock_settings.return_value = MagicMock()
        db_sentinel = MagicMock(name="db_sentinel")
        mock_db.return_value = db_sentinel
        service = GitHubAuthService()

        mock_delete.return_value = True
        assert await service.revoke_session("id1") is True

        mock_delete.return_value = False
        assert await service.revoke_session("id2") is False

    @pytest.mark.asyncio
    @patch("src.services.github_auth.store_delete_session", new_callable=AsyncMock)
    @patch("src.services.github_auth.get_db")
    @patch("src.services.github_auth.get_settings")
    async def test_delete_called_with_db_and_session_id(self, mock_settings, mock_db, mock_delete):
        """Catch mutation: store_delete_session(session_id) missing db arg."""
        mock_settings.return_value = MagicMock()
        db_sentinel = MagicMock(name="db_sentinel")
        mock_db.return_value = db_sentinel
        service = GitHubAuthService()

        mock_delete.return_value = True
        await service.revoke_session("sess_abc")

        mock_delete.assert_awaited_once_with(db_sentinel, "sess_abc")

    @pytest.mark.asyncio
    @patch("src.services.github_auth.store_delete_session", new_callable=AsyncMock)
    @patch("src.services.github_auth.get_db")
    @patch("src.services.github_auth.get_settings")
    async def test_logger_called_on_success(self, mock_settings, mock_db, mock_delete):
        """Catch mutation: logger.info args mutated."""
        mock_settings.return_value = MagicMock()
        mock_db.return_value = MagicMock()
        service = GitHubAuthService()
        mock_delete.return_value = True

        with patch("src.services.github_auth.logger") as mock_logger:
            await service.revoke_session("sess_xyz")
            mock_logger.info.assert_called_once()
            fmt_args = mock_logger.info.call_args[0]
            assert len(fmt_args) == 2
            assert fmt_args[0] == "Revoked session %s"
            assert fmt_args[1] == "sess_xyz"


class TestUpdateSessionMutationKillers:
    """Kill mutations in update_session: timestamp, save call."""

    @pytest.mark.asyncio
    @patch("src.services.github_auth.store_save_session", new_callable=AsyncMock)
    @patch("src.services.github_auth.get_db")
    @patch("src.services.github_auth.get_settings")
    async def test_save_called_with_db_and_session(self, mock_settings, mock_db, mock_save):
        """Catch mutation: save call removed or args changed."""
        mock_settings.return_value = MagicMock()
        db_sentinel = MagicMock(name="db_sentinel")
        mock_db.return_value = db_sentinel
        service = GitHubAuthService()
        session = UserSession(
            github_user_id="1",
            github_username="u",
            access_token="t",
        )

        await service.update_session(session)

        mock_save.assert_awaited_once_with(db_sentinel, session)

    @pytest.mark.asyncio
    @patch("src.services.github_auth.store_save_session", new_callable=AsyncMock)
    @patch("src.services.github_auth.get_db")
    @patch("src.services.github_auth.get_settings")
    async def test_get_db_called(self, mock_settings, mock_db, _save):
        """Catch mutation: db = None (get_db() replaced with None)."""
        mock_settings.return_value = MagicMock()
        mock_db.return_value = MagicMock()
        service = GitHubAuthService()
        session = UserSession(
            github_user_id="1",
            github_username="u",
            access_token="t",
        )

        await service.update_session(session)
        mock_db.assert_called_once()


class TestGetSessionMutationKillers:
    """Kill mutations in get_session: db retrieval, session_id forwarding."""

    @pytest.mark.asyncio
    @patch("src.services.github_auth.store_get_session", new_callable=AsyncMock)
    @patch("src.services.github_auth.get_db")
    @patch("src.services.github_auth.get_settings")
    async def test_get_session_forwards_db_and_id(self, mock_settings, mock_db, mock_get):
        """Catch mutation: store_get_session(db, None) or store_get_session(session_id)."""
        mock_settings.return_value = MagicMock()
        db_sentinel = MagicMock(name="db_sentinel")
        mock_db.return_value = db_sentinel
        service = GitHubAuthService()

        expected_session = UserSession(
            github_user_id="1",
            github_username="u",
            access_token="t",
        )
        mock_get.return_value = expected_session

        result = await service.get_session("session_xyz")

        mock_db.assert_called_once()
        mock_get.assert_awaited_once_with(db_sentinel, "session_xyz")
        assert result is expected_session


class TestPruneExpiredStatesMutationKillers:
    """Kill mutations in _prune_expired_states: comparison operator,
    pop call."""

    def setup_method(self):
        _oauth_states.clear()

    def test_prune_removes_expired_states(self):
        """Catch mutation: >= changed to > or <=."""
        _oauth_states["expired"] = datetime.now(UTC) - timedelta(minutes=15)
        _oauth_states["fresh"] = datetime.now(UTC)

        _prune_expired_states()

        assert "expired" not in _oauth_states
        assert "fresh" in _oauth_states

    def test_prune_at_exact_ttl_boundary(self):
        """State exactly at TTL should be pruned (>= comparison)."""
        _oauth_states["boundary"] = datetime.now(UTC) - _OAUTH_STATE_TTL

        _prune_expired_states()

        assert "boundary" not in _oauth_states

    def test_prune_just_before_ttl_preserved(self):
        """State 1 second before TTL should NOT be pruned."""
        _oauth_states["almost"] = datetime.now(UTC) - _OAUTH_STATE_TTL + timedelta(seconds=1)

        _prune_expired_states()

        assert "almost" in _oauth_states

    def test_prune_empty_states_no_error(self):
        """Pruning empty states should not error."""
        _prune_expired_states()  # should not raise

    @patch("src.services.github_auth.datetime")
    def test_prune_at_exact_boundary_frozen_time(self, mock_dt):
        """Kill mutmut_5 (>= → >) using frozen time."""
        frozen = datetime(2025, 6, 1, tzinfo=UTC)
        mock_dt.now.return_value = frozen
        _oauth_states["boundary"] = frozen - _OAUTH_STATE_TTL
        _prune_expired_states()
        assert "boundary" not in _oauth_states


class TestModuleLevelConstants:
    """Kill mutations on module-level constants and the global service instance."""

    def test_oauth_state_ttl_is_10_minutes(self):
        assert _OAUTH_STATE_TTL == timedelta(minutes=10)

    def test_github_authorize_url(self):
        assert GITHUB_AUTHORIZE_URL == "https://github.com/login/oauth/authorize"

    def test_github_token_url(self):
        assert GITHUB_TOKEN_URL == "https://github.com/login/oauth/access_token"

    def test_global_service_instance_exists(self):
        from src.services.github_auth import github_auth_service

        assert isinstance(github_auth_service, GitHubAuthService)
