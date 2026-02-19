"""Unit tests for FastAPI API endpoints."""

import os

os.environ.setdefault("GITHUB_CLIENT_ID", "test_id")
os.environ.setdefault("GITHUB_CLIENT_SECRET", "test_secret")
os.environ.setdefault("SESSION_SECRET_KEY", "test_key")

from dataclasses import dataclass
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from src.config import get_settings

# Clear cached settings so env vars are picked up
get_settings.cache_clear()

from src.main import app
from src.models.board import (
    BoardColumn,
    BoardDataResponse,
    BoardProject,
    StatusColor,
    StatusField,
    StatusOption,
)
from src.models.chat import (
    AITaskProposal,
    IssueRecommendation,
    ProposalStatus,
    RecommendationStatus,
    WorkflowConfiguration,
    WorkflowResult,
)
from src.models.project import GitHubProject, ProjectType, StatusColumn
from src.models.task import Task
from src.models.user import UserSession

# ---------------------------------------------------------------------------
# Shared helpers & fixtures
# ---------------------------------------------------------------------------

TEST_SESSION_ID = uuid4()
TEST_USER_ID = "12345"
TEST_USERNAME = "testuser"
TEST_ACCESS_TOKEN = "gho_test_token"
TEST_PROJECT_ID = "PVT_test123"


def _make_session(**overrides) -> UserSession:
    """Create a test UserSession with sensible defaults."""
    defaults = {
        "session_id": TEST_SESSION_ID,
        "github_user_id": TEST_USER_ID,
        "github_username": TEST_USERNAME,
        "github_avatar_url": "https://avatar.test/u/1",
        "access_token": TEST_ACCESS_TOKEN,
        "selected_project_id": TEST_PROJECT_ID,
    }
    defaults.update(overrides)
    return UserSession(**defaults)


def _make_project(project_id=TEST_PROJECT_ID, name="Test Project") -> GitHubProject:
    return GitHubProject(
        project_id=project_id,
        owner_id="O_test",
        owner_login=TEST_USERNAME,
        name=name,
        type=ProjectType.USER,
        url=f"https://github.com/users/{TEST_USERNAME}/projects/1",
        status_columns=[
            StatusColumn(field_id="F1", name="Todo", option_id="opt1"),
            StatusColumn(field_id="F1", name="In Progress", option_id="opt2"),
            StatusColumn(field_id="F1", name="Done", option_id="opt3"),
        ],
    )


def _make_task(
    project_id=TEST_PROJECT_ID, title="Test Task", status="Todo", github_item_id="PVTI_1"
) -> Task:
    return Task(
        project_id=project_id,
        github_item_id=github_item_id,
        title=title,
        status=status,
        status_option_id="opt1",
    )


@pytest.fixture
async def client():
    """Create async HTTP client for testing FastAPI endpoints."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def mock_session():
    """Return a default authenticated session and auto-patch the dependency."""
    session = _make_session()
    with patch("src.api.auth.get_current_session", return_value=session):
        yield session


@pytest.fixture(autouse=True)
def _clean_chat_state():
    """Reset in-memory chat/proposal/recommendation stores between tests."""
    import src.api.chat as _chat_mod
    import src.api.workflow as _wf_mod

    _chat_mod._messages.clear()
    _chat_mod._proposals.clear()
    _chat_mod._recommendations.clear()
    _wf_mod._recent_requests.clear()
    yield
    _chat_mod._messages.clear()
    _chat_mod._proposals.clear()
    _chat_mod._recommendations.clear()
    _wf_mod._recent_requests.clear()


# ===================================================================
# Health
# ===================================================================


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


# ===================================================================
# Auth – existing
# ===================================================================


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


# ===================================================================
# Auth – callback / dev-login gaps
# ===================================================================


class TestAuthGitHubCallback:
    """Tests for GET /auth/github/callback."""

    @pytest.mark.asyncio
    async def test_callback_invalid_state_returns_400(self, client):
        """Should reject callback with invalid OAuth state."""
        response = await client.get(
            "/api/v1/auth/github/callback",
            params={"code": "test_code", "state": "bad_state"},
            follow_redirects=False,
        )
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_callback_success_redirects_to_frontend(self, client):
        """Should redirect to frontend URL on successful OAuth."""
        session = _make_session()
        with (
            patch(
                "src.api.auth.github_auth_service.validate_state",
                return_value=True,
            ),
            patch(
                "src.api.auth.github_auth_service.create_session",
                new_callable=AsyncMock,
                return_value=session,
            ),
        ):
            response = await client.get(
                "/api/v1/auth/github/callback",
                params={"code": "good_code", "state": "valid"},
                follow_redirects=False,
            )
        assert response.status_code == 302
        assert "session_token=" in response.headers["location"]

    @pytest.mark.asyncio
    async def test_callback_value_error_returns_400(self, client):
        """Should return 400 when create_session raises ValueError."""
        with (
            patch(
                "src.api.auth.github_auth_service.validate_state",
                return_value=True,
            ),
            patch(
                "src.api.auth.github_auth_service.create_session",
                new_callable=AsyncMock,
                side_effect=ValueError("OAuth error"),
            ),
        ):
            response = await client.get(
                "/api/v1/auth/github/callback",
                params={"code": "bad_code", "state": "valid"},
                follow_redirects=False,
            )
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_callback_unexpected_error_returns_500(self, client):
        """Should return 500 on unexpected exception."""
        with (
            patch(
                "src.api.auth.github_auth_service.validate_state",
                return_value=True,
            ),
            patch(
                "src.api.auth.github_auth_service.create_session",
                new_callable=AsyncMock,
                side_effect=RuntimeError("boom"),
            ),
        ):
            response = await client.get(
                "/api/v1/auth/github/callback",
                params={"code": "bad_code", "state": "valid"},
                follow_redirects=False,
            )
        assert response.status_code == 500


class TestAuthDevLogin:
    """Tests for POST /auth/dev-login."""

    @pytest.mark.asyncio
    async def test_dev_login_forbidden_when_not_debug(self, client):
        """Should return 403 when debug mode is off."""
        with patch("src.config.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(debug=False)
            response = await client.post(
                "/api/v1/auth/dev-login",
                params={"github_token": "ghp_test"},
            )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_dev_login_success(self, client):
        """Should create session and return user info in debug mode."""
        session = _make_session()
        with (
            patch("src.config.get_settings") as mock_settings,
            patch(
                "src.api.auth.github_auth_service.create_session_from_token",
                new_callable=AsyncMock,
                return_value=session,
            ),
        ):
            mock_settings.return_value = MagicMock(debug=True)
            response = await client.post(
                "/api/v1/auth/dev-login",
                params={"github_token": "ghp_test"},
            )
        assert response.status_code == 200
        assert response.json()["github_username"] == TEST_USERNAME

    @pytest.mark.asyncio
    async def test_dev_login_bad_token(self, client):
        """Should return 401 when token is invalid."""
        with (
            patch("src.config.get_settings") as mock_settings,
            patch(
                "src.api.auth.github_auth_service.create_session_from_token",
                new_callable=AsyncMock,
                side_effect=Exception("bad token"),
            ),
        ):
            mock_settings.return_value = MagicMock(debug=True)
            response = await client.post(
                "/api/v1/auth/dev-login",
                params={"github_token": "ghp_bad"},
            )
        assert response.status_code == 401


class TestAuthMe:
    """Tests for GET /auth/me with valid session."""

    @pytest.mark.asyncio
    async def test_me_with_valid_session(self, client, mock_session):
        """Should return user info when session is valid."""
        response = await client.get(
            "/api/v1/auth/me",
            cookies={"session_id": str(mock_session.session_id)},
        )
        assert response.status_code == 200
        assert response.json()["github_username"] == TEST_USERNAME


class TestAuthSetSessionCookie:
    """Tests for POST /auth/session with valid token."""

    @pytest.mark.asyncio
    async def test_set_session_cookie_success(self, client):
        """Should set cookie and return user info."""
        session = _make_session()
        with patch(
            "src.api.auth.github_auth_service.get_session",
            return_value=session,
        ):
            response = await client.post(
                "/api/v1/auth/session",
                params={"session_token": str(session.session_id)},
            )
        assert response.status_code == 200
        assert response.json()["github_username"] == TEST_USERNAME
        assert "session_id" in response.cookies


# ===================================================================
# Chat endpoints
# ===================================================================


class TestChatGetMessages:
    """Tests for GET /chat/messages."""

    @pytest.mark.asyncio
    async def test_get_messages_empty(self, client, mock_session):
        """Should return empty list initially."""
        response = await client.get(
            "/api/v1/chat/messages",
            cookies={"session_id": str(mock_session.session_id)},
        )
        assert response.status_code == 200
        assert response.json()["messages"] == []

    @pytest.mark.asyncio
    async def test_get_messages_returns_stored(self, client, mock_session):
        """Should return previously added messages."""
        from src.api.chat import add_message
        from src.models.chat import ChatMessage, SenderType

        msg = ChatMessage(
            session_id=mock_session.session_id,
            sender_type=SenderType.USER,
            content="hello",
        )
        add_message(mock_session.session_id, msg)

        response = await client.get(
            "/api/v1/chat/messages",
            cookies={"session_id": str(mock_session.session_id)},
        )
        assert response.status_code == 200
        assert len(response.json()["messages"]) == 1

    @pytest.mark.asyncio
    async def test_get_messages_requires_auth(self, client):
        """Should return 401 without session cookie."""
        response = await client.get("/api/v1/chat/messages")
        assert response.status_code == 401


class TestChatClearMessages:
    """Tests for DELETE /chat/messages."""

    @pytest.mark.asyncio
    async def test_clear_messages(self, client, mock_session):
        """Should clear all messages."""
        from src.api.chat import add_message
        from src.models.chat import ChatMessage, SenderType

        msg = ChatMessage(
            session_id=mock_session.session_id,
            sender_type=SenderType.USER,
            content="hello",
        )
        add_message(mock_session.session_id, msg)

        response = await client.delete(
            "/api/v1/chat/messages",
            cookies={"session_id": str(mock_session.session_id)},
        )
        assert response.status_code == 200
        assert response.json()["message"] == "Chat history cleared"

    @pytest.mark.asyncio
    async def test_clear_messages_when_none_exist(self, client, mock_session):
        """Should succeed even with no messages."""
        response = await client.delete(
            "/api/v1/chat/messages",
            cookies={"session_id": str(mock_session.session_id)},
        )
        assert response.status_code == 200


class TestChatSendMessage:
    """Tests for POST /chat/messages."""

    @pytest.mark.asyncio
    async def test_send_message_no_project(self, client):
        """Should return 422 when no project selected."""
        session = _make_session(selected_project_id=None)
        with patch("src.api.auth.get_current_session", return_value=session):
            response = await client.post(
                "/api/v1/chat/messages",
                json={"content": "Hello"},
                cookies={"session_id": str(session.session_id)},
            )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_send_message_ai_not_configured(self, client, mock_session):
        """Should return error message when AI is not configured."""
        with patch(
            "src.api.chat.get_ai_agent_service",
            side_effect=ValueError("No AI configured"),
        ):
            response = await client.post(
                "/api/v1/chat/messages",
                json={"content": "Create a task"},
                cookies={"session_id": str(mock_session.session_id)},
            )
        assert response.status_code == 200
        assert "not configured" in response.json()["content"]

    @pytest.mark.asyncio
    async def test_send_message_feature_request(self, client, mock_session):
        """Should return issue recommendation for feature requests."""
        mock_ai = MagicMock()
        mock_ai.detect_feature_request_intent = AsyncMock(return_value=True)
        rec = IssueRecommendation(
            session_id=mock_session.session_id,
            original_input="Add dark mode",
            title="Add dark mode",
            user_story="As a user I want dark mode",
            ui_ux_description="Toggle switch",
            functional_requirements=["Dark theme"],
        )
        mock_ai.generate_issue_recommendation = AsyncMock(return_value=rec)

        with (
            patch("src.api.chat.get_ai_agent_service", return_value=mock_ai),
            patch("src.api.chat.cache") as mock_cache,
        ):
            mock_cache.get.return_value = None
            response = await client.post(
                "/api/v1/chat/messages",
                json={"content": "Add dark mode"},
                cookies={"session_id": str(mock_session.session_id)},
            )
        assert response.status_code == 200
        data = response.json()
        assert data["action_type"] == "issue_create"
        assert "dark mode" in data["content"].lower()

    @pytest.mark.asyncio
    async def test_send_message_feature_request_failure(self, client, mock_session):
        """Should return error when issue recommendation generation fails."""
        mock_ai = MagicMock()
        mock_ai.detect_feature_request_intent = AsyncMock(return_value=True)
        mock_ai.generate_issue_recommendation = AsyncMock(side_effect=RuntimeError("AI down"))

        with (
            patch("src.api.chat.get_ai_agent_service", return_value=mock_ai),
            patch("src.api.chat.cache") as mock_cache,
        ):
            mock_cache.get.return_value = None
            response = await client.post(
                "/api/v1/chat/messages",
                json={"content": "Add dark mode"},
                cookies={"session_id": str(mock_session.session_id)},
            )
        assert response.status_code == 200
        assert "couldn't generate" in response.json()["content"].lower()

    @pytest.mark.asyncio
    async def test_send_message_status_change(self, client, mock_session):
        """Should return status update proposal for status change requests."""

        @dataclass
        class _StatusChange:
            task_reference: str = "Test Task"
            target_status: str = "Done"
            confidence: float = 0.9

        task = _make_task()
        project = _make_project()
        mock_ai = MagicMock()
        mock_ai.detect_feature_request_intent = AsyncMock(return_value=False)
        mock_ai.parse_status_change_request = AsyncMock(return_value=_StatusChange())
        mock_ai.identify_target_task.return_value = task

        def _cache_get(key):
            if "projects" in key:
                return [project]
            return [task]

        with (
            patch("src.api.chat.get_ai_agent_service", return_value=mock_ai),
            patch("src.api.chat.cache") as mock_cache,
        ):
            mock_cache.get.side_effect = _cache_get
            response = await client.post(
                "/api/v1/chat/messages",
                json={"content": "Move Test Task to Done"},
                cookies={"session_id": str(mock_session.session_id)},
            )
        assert response.status_code == 200
        data = response.json()
        assert data["action_type"] == "status_update"

    @pytest.mark.asyncio
    async def test_send_message_status_change_task_not_found(self, client, mock_session):
        """Should return error when target task cannot be identified."""

        @dataclass
        class _StatusChange:
            task_reference: str = "Nonexistent"
            target_status: str = "Done"
            confidence: float = 0.9

        mock_ai = MagicMock()
        mock_ai.detect_feature_request_intent = AsyncMock(return_value=False)
        mock_ai.parse_status_change_request = AsyncMock(return_value=_StatusChange())
        mock_ai.identify_target_task.return_value = None

        with (
            patch("src.api.chat.get_ai_agent_service", return_value=mock_ai),
            patch("src.api.chat.cache") as mock_cache,
        ):
            mock_cache.get.side_effect = lambda key: None if "projects" in key else []
            response = await client.post(
                "/api/v1/chat/messages",
                json={"content": "Move Nonexistent to Done"},
                cookies={"session_id": str(mock_session.session_id)},
            )
        assert response.status_code == 200
        assert "couldn't find" in response.json()["content"].lower()

    @pytest.mark.asyncio
    async def test_send_message_task_generation(self, client, mock_session):
        """Should generate a task proposal for general descriptions."""

        @dataclass
        class _Generated:
            title: str = "Generated Title"
            description: str = "Generated description " * 20

        mock_ai = MagicMock()
        mock_ai.detect_feature_request_intent = AsyncMock(return_value=False)
        mock_ai.parse_status_change_request = AsyncMock(return_value=None)
        mock_ai.generate_task_from_description = AsyncMock(return_value=_Generated())

        with (
            patch("src.api.chat.get_ai_agent_service", return_value=mock_ai),
            patch("src.api.chat.cache") as mock_cache,
        ):
            mock_cache.get.return_value = None
            response = await client.post(
                "/api/v1/chat/messages",
                json={"content": "Fix the login bug"},
                cookies={"session_id": str(mock_session.session_id)},
            )
        assert response.status_code == 200
        data = response.json()
        assert data["action_type"] == "task_create"

    @pytest.mark.asyncio
    async def test_send_message_task_generation_failure(self, client, mock_session):
        """Should return error when task generation fails."""
        mock_ai = MagicMock()
        mock_ai.detect_feature_request_intent = AsyncMock(return_value=False)
        mock_ai.parse_status_change_request = AsyncMock(return_value=None)
        mock_ai.generate_task_from_description = AsyncMock(side_effect=RuntimeError("fail"))

        with (
            patch("src.api.chat.get_ai_agent_service", return_value=mock_ai),
            patch("src.api.chat.cache") as mock_cache,
        ):
            mock_cache.get.return_value = None
            response = await client.post(
                "/api/v1/chat/messages",
                json={"content": "Do something"},
                cookies={"session_id": str(mock_session.session_id)},
            )
        assert response.status_code == 200
        assert "couldn't generate" in response.json()["content"].lower()

    @pytest.mark.asyncio
    async def test_send_message_with_project_context(self, client, mock_session):
        """Should use cached project/task context."""
        project = _make_project()

        @dataclass
        class _Generated:
            title: str = "Title"
            description: str = "Desc " * 50

        mock_ai = MagicMock()
        mock_ai.detect_feature_request_intent = AsyncMock(return_value=False)
        mock_ai.parse_status_change_request = AsyncMock(return_value=None)
        mock_ai.generate_task_from_description = AsyncMock(return_value=_Generated())

        with (
            patch("src.api.chat.get_ai_agent_service", return_value=mock_ai),
            patch("src.api.chat.cache") as mock_cache,
        ):
            mock_cache.get.side_effect = lambda key: (
                [project] if "projects" in key else [_make_task()]
            )
            response = await client.post(
                "/api/v1/chat/messages",
                json={"content": "Build feature X"},
                cookies={"session_id": str(mock_session.session_id)},
            )
        assert response.status_code == 200


class TestChatConfirmProposal:
    """Tests for POST /chat/proposals/{proposal_id}/confirm."""

    def _store_proposal(self, session_id, **overrides):
        from src.api.chat import _proposals

        defaults = {
            "session_id": session_id,
            "original_input": "input",
            "proposed_title": "Title",
            "proposed_description": "Desc",
        }
        defaults.update(overrides)
        proposal = AITaskProposal(**defaults)
        _proposals[str(proposal.proposal_id)] = proposal
        return proposal

    @pytest.mark.asyncio
    async def test_confirm_not_found(self, client, mock_session):
        """Should return 404 for unknown proposal."""
        response = await client.post(
            "/api/v1/chat/proposals/nonexistent/confirm",
            json={},
            cookies={"session_id": str(mock_session.session_id)},
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_confirm_wrong_session(self, client, mock_session):
        """Should return 404 when proposal belongs to another session."""
        other_session_id = uuid4()
        proposal = self._store_proposal(other_session_id)
        response = await client.post(
            f"/api/v1/chat/proposals/{proposal.proposal_id}/confirm",
            json={},
            cookies={"session_id": str(mock_session.session_id)},
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_confirm_expired(self, client, mock_session):
        """Should return 422 for expired proposal."""
        proposal = self._store_proposal(mock_session.session_id)
        proposal.expires_at = datetime.utcnow() - timedelta(minutes=1)  # noqa: DTZ003

        response = await client.post(
            f"/api/v1/chat/proposals/{proposal.proposal_id}/confirm",
            json={},
            cookies={"session_id": str(mock_session.session_id)},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_confirm_already_confirmed(self, client, mock_session):
        """Should return 422 for non-pending proposal."""
        proposal = self._store_proposal(mock_session.session_id)
        proposal.status = ProposalStatus.CONFIRMED

        response = await client.post(
            f"/api/v1/chat/proposals/{proposal.proposal_id}/confirm",
            json={},
            cookies={"session_id": str(mock_session.session_id)},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_confirm_success(self, client, mock_session):
        """Should confirm proposal and create GitHub issue."""
        proposal = self._store_proposal(mock_session.session_id)

        with (
            patch(
                "src.api.chat.github_projects_service.get_project_repository",
                new_callable=AsyncMock,
                return_value=("owner", "repo"),
            ),
            patch(
                "src.api.chat.github_projects_service.create_issue",
                new_callable=AsyncMock,
                return_value={
                    "number": 42,
                    "node_id": "I_node",
                    "html_url": "https://github.com/owner/repo/issues/42",
                },
            ),
            patch(
                "src.api.chat.github_projects_service.add_issue_to_project",
                new_callable=AsyncMock,
                return_value="PVTI_item",
            ),
            patch(
                "src.api.chat.connection_manager.broadcast_to_project",
                new_callable=AsyncMock,
            ),
            patch(
                "src.api.chat.github_projects_service.update_item_status_by_name",
                new_callable=AsyncMock,
            ),
            patch("src.api.chat.get_workflow_orchestrator") as mock_orch,
            patch("src.api.chat.get_workflow_config", return_value=None),
            patch("src.api.chat.set_workflow_config"),
        ):
            mock_orch.return_value.assign_agent_for_status = AsyncMock()
            response = await client.post(
                f"/api/v1/chat/proposals/{proposal.proposal_id}/confirm",
                json={},
                cookies={"session_id": str(mock_session.session_id)},
            )
        assert response.status_code == 200
        assert response.json()["status"] == "confirmed"

    @pytest.mark.asyncio
    async def test_confirm_with_edits(self, client, mock_session):
        """Should apply title/description edits before confirming."""
        proposal = self._store_proposal(mock_session.session_id)

        with (
            patch(
                "src.api.chat.github_projects_service.get_project_repository",
                new_callable=AsyncMock,
                return_value=("owner", "repo"),
            ),
            patch(
                "src.api.chat.github_projects_service.create_issue",
                new_callable=AsyncMock,
                return_value={
                    "number": 43,
                    "node_id": "I_n2",
                    "html_url": "https://github.com/owner/repo/issues/43",
                },
            ),
            patch(
                "src.api.chat.github_projects_service.add_issue_to_project",
                new_callable=AsyncMock,
                return_value="PVTI_2",
            ),
            patch(
                "src.api.chat.connection_manager.broadcast_to_project",
                new_callable=AsyncMock,
            ),
            patch(
                "src.api.chat.github_projects_service.update_item_status_by_name",
                new_callable=AsyncMock,
            ),
            patch("src.api.chat.get_workflow_orchestrator") as mock_orch,
            patch("src.api.chat.get_workflow_config", return_value=None),
            patch("src.api.chat.set_workflow_config"),
        ):
            mock_orch.return_value.assign_agent_for_status = AsyncMock()
            response = await client.post(
                f"/api/v1/chat/proposals/{proposal.proposal_id}/confirm",
                json={"edited_title": "New Title", "edited_description": "New Desc"},
                cookies={"session_id": str(mock_session.session_id)},
            )
        assert response.status_code == 200
        data = response.json()
        assert data["edited_title"] == "New Title"

    @pytest.mark.asyncio
    async def test_confirm_github_error(self, client, mock_session):
        """Should return 422 when GitHub API call fails."""
        proposal = self._store_proposal(mock_session.session_id)

        with (
            patch(
                "src.api.chat.github_projects_service.get_project_repository",
                new_callable=AsyncMock,
                return_value=("owner", "repo"),
            ),
            patch(
                "src.api.chat.github_projects_service.create_issue",
                new_callable=AsyncMock,
                side_effect=RuntimeError("API error"),
            ),
        ):
            response = await client.post(
                f"/api/v1/chat/proposals/{proposal.proposal_id}/confirm",
                json={},
                cookies={"session_id": str(mock_session.session_id)},
            )
        assert response.status_code == 422


class TestChatCancelProposal:
    """Tests for DELETE /chat/proposals/{proposal_id}."""

    @pytest.mark.asyncio
    async def test_cancel_not_found(self, client, mock_session):
        """Should return 404 for unknown proposal."""
        response = await client.delete(
            "/api/v1/chat/proposals/nonexistent",
            cookies={"session_id": str(mock_session.session_id)},
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_cancel_wrong_session(self, client, mock_session):
        """Should return 404 when proposal belongs to another session."""
        from src.api.chat import _proposals

        other_id = uuid4()
        proposal = AITaskProposal(
            session_id=other_id,
            original_input="x",
            proposed_title="T",
            proposed_description="D",
        )
        _proposals[str(proposal.proposal_id)] = proposal

        response = await client.delete(
            f"/api/v1/chat/proposals/{proposal.proposal_id}",
            cookies={"session_id": str(mock_session.session_id)},
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_cancel_success(self, client, mock_session):
        """Should cancel proposal and return message."""
        from src.api.chat import _proposals

        proposal = AITaskProposal(
            session_id=mock_session.session_id,
            original_input="x",
            proposed_title="T",
            proposed_description="D",
        )
        _proposals[str(proposal.proposal_id)] = proposal

        response = await client.delete(
            f"/api/v1/chat/proposals/{proposal.proposal_id}",
            cookies={"session_id": str(mock_session.session_id)},
        )
        assert response.status_code == 200
        assert response.json()["message"] == "Proposal cancelled"


# ===================================================================
# Workflow endpoints
# ===================================================================


class TestWorkflowConfirmRecommendation:
    """Tests for POST /workflow/recommendations/{id}/confirm."""

    def _store_recommendation(self, session_id, **overrides):
        from src.api.chat import _recommendations

        defaults = {
            "session_id": session_id,
            "original_input": "Add feature X",
            "title": "Feature X",
            "user_story": "As a user",
            "ui_ux_description": "Button",
            "functional_requirements": ["Req1"],
        }
        defaults.update(overrides)
        rec = IssueRecommendation(**defaults)
        _recommendations[str(rec.recommendation_id)] = rec
        return rec

    @pytest.mark.asyncio
    async def test_confirm_not_found(self, client, mock_session):
        response = await client.post(
            "/api/v1/workflow/recommendations/bad_id/confirm",
            cookies={"session_id": str(mock_session.session_id)},
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_confirm_wrong_session(self, client, mock_session):
        rec = self._store_recommendation(uuid4())
        response = await client.post(
            f"/api/v1/workflow/recommendations/{rec.recommendation_id}/confirm",
            cookies={"session_id": str(mock_session.session_id)},
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_confirm_already_confirmed(self, client, mock_session):
        rec = self._store_recommendation(mock_session.session_id)
        rec.status = RecommendationStatus.CONFIRMED
        response = await client.post(
            f"/api/v1/workflow/recommendations/{rec.recommendation_id}/confirm",
            cookies={"session_id": str(mock_session.session_id)},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_confirm_no_project(self, client):
        session = _make_session(selected_project_id=None)
        with patch("src.api.auth.get_current_session", return_value=session):
            from src.api.chat import _recommendations

            rec = IssueRecommendation(
                session_id=session.session_id,
                original_input="X",
                title="T",
                user_story="U",
                ui_ux_description="D",
                functional_requirements=["R"],
            )
            _recommendations[str(rec.recommendation_id)] = rec
            response = await client.post(
                f"/api/v1/workflow/recommendations/{rec.recommendation_id}/confirm",
                cookies={"session_id": str(session.session_id)},
            )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_confirm_success(self, client, mock_session):
        rec = self._store_recommendation(mock_session.session_id)
        result = WorkflowResult(
            success=True,
            issue_id="I_1",
            issue_number=10,
            issue_url="https://github.com/o/r/issues/10",
            project_item_id="PVTI_1",
            current_status="Backlog",
            message="Created",
        )

        with (
            patch(
                "src.api.workflow.github_projects_service.get_project_repository",
                new_callable=AsyncMock,
                return_value=("owner", "repo"),
            ),
            patch("src.api.workflow.get_workflow_config", return_value=None),
            patch("src.api.workflow.set_workflow_config"),
            patch("src.api.workflow.get_workflow_orchestrator") as mock_orch,
            patch(
                "src.api.workflow.connection_manager.broadcast_to_project",
                new_callable=AsyncMock,
            ),
            patch("src.api.workflow.get_agent_slugs", return_value=["speckit.specify"]),
        ):
            mock_orch.return_value.execute_full_workflow = AsyncMock(return_value=result)
            response = await client.post(
                f"/api/v1/workflow/recommendations/{rec.recommendation_id}/confirm",
                cookies={"session_id": str(mock_session.session_id)},
            )
        assert response.status_code == 200
        assert response.json()["success"] is True

    @pytest.mark.asyncio
    async def test_confirm_workflow_exception(self, client, mock_session):
        """Should return failure result when workflow raises exception."""
        rec = self._store_recommendation(mock_session.session_id)

        with (
            patch(
                "src.api.workflow.github_projects_service.get_project_repository",
                new_callable=AsyncMock,
                return_value=("owner", "repo"),
            ),
            patch("src.api.workflow.get_workflow_config", return_value=None),
            patch("src.api.workflow.set_workflow_config"),
            patch("src.api.workflow.get_workflow_orchestrator") as mock_orch,
        ):
            mock_orch.return_value.execute_full_workflow = AsyncMock(
                side_effect=RuntimeError("workflow fail")
            )
            response = await client.post(
                f"/api/v1/workflow/recommendations/{rec.recommendation_id}/confirm",
                cookies={"session_id": str(mock_session.session_id)},
            )
        assert response.status_code == 200
        assert response.json()["success"] is False

    @pytest.mark.asyncio
    async def test_confirm_no_repo_falls_back_to_settings(self, client, mock_session):
        """Should fall back to default repo from settings when no repo found."""
        rec = self._store_recommendation(mock_session.session_id)
        result = WorkflowResult(success=True, message="OK", issue_number=1)

        mock_settings = MagicMock(
            default_repo_owner="default_owner",
            default_repo_name="default_repo",
            default_assignee="bot",
        )

        with (
            patch(
                "src.api.workflow.github_projects_service.get_project_repository",
                new_callable=AsyncMock,
                return_value=None,
            ),
            patch("src.api.workflow.get_workflow_config", return_value=None),
            patch("src.api.workflow.set_workflow_config"),
            patch("src.api.workflow.get_workflow_orchestrator") as mock_orch,
            patch(
                "src.api.workflow.connection_manager.broadcast_to_project",
                new_callable=AsyncMock,
            ),
            patch("src.api.workflow.get_agent_slugs", return_value=[]),
            patch("src.config.get_settings", return_value=mock_settings),
        ):
            mock_orch.return_value.execute_full_workflow = AsyncMock(return_value=result)
            response = await client.post(
                f"/api/v1/workflow/recommendations/{rec.recommendation_id}/confirm",
                cookies={"session_id": str(mock_session.session_id)},
            )
        assert response.status_code == 200


class TestWorkflowRejectRecommendation:
    """Tests for POST /workflow/recommendations/{id}/reject."""

    def _store_recommendation(self, session_id):
        from src.api.chat import _recommendations

        rec = IssueRecommendation(
            session_id=session_id,
            original_input="X",
            title="T",
            user_story="U",
            ui_ux_description="D",
            functional_requirements=["R"],
        )
        _recommendations[str(rec.recommendation_id)] = rec
        return rec

    @pytest.mark.asyncio
    async def test_reject_not_found(self, client, mock_session):
        response = await client.post(
            "/api/v1/workflow/recommendations/bad_id/reject",
            cookies={"session_id": str(mock_session.session_id)},
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_reject_wrong_session(self, client, mock_session):
        rec = self._store_recommendation(uuid4())
        response = await client.post(
            f"/api/v1/workflow/recommendations/{rec.recommendation_id}/reject",
            cookies={"session_id": str(mock_session.session_id)},
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_reject_already_rejected(self, client, mock_session):
        rec = self._store_recommendation(mock_session.session_id)
        rec.status = RecommendationStatus.REJECTED
        response = await client.post(
            f"/api/v1/workflow/recommendations/{rec.recommendation_id}/reject",
            cookies={"session_id": str(mock_session.session_id)},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_reject_success(self, client, mock_session):
        rec = self._store_recommendation(mock_session.session_id)
        response = await client.post(
            f"/api/v1/workflow/recommendations/{rec.recommendation_id}/reject",
            cookies={"session_id": str(mock_session.session_id)},
        )
        assert response.status_code == 200
        assert response.json()["message"] == "Recommendation rejected"


class TestWorkflowGetConfig:
    """Tests for GET /workflow/config."""

    @pytest.mark.asyncio
    async def test_get_config_no_project(self, client):
        session = _make_session(selected_project_id=None)
        with patch("src.api.auth.get_current_session", return_value=session):
            response = await client.get(
                "/api/v1/workflow/config",
                cookies={"session_id": str(session.session_id)},
            )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_config_existing(self, client, mock_session):
        config = WorkflowConfiguration(
            project_id=TEST_PROJECT_ID,
            repository_owner="owner",
            repository_name="repo",
        )
        with patch("src.api.workflow.get_workflow_config", return_value=config):
            response = await client.get(
                "/api/v1/workflow/config",
                cookies={"session_id": str(mock_session.session_id)},
            )
        assert response.status_code == 200
        assert response.json()["repository_owner"] == "owner"

    @pytest.mark.asyncio
    async def test_get_config_default(self, client, mock_session):
        """Should return default config when none exists."""
        with (
            patch("src.api.workflow.get_workflow_config", return_value=None),
            patch("src.api.workflow.cache") as mock_cache,
        ):
            mock_cache.get.return_value = None
            response = await client.get(
                "/api/v1/workflow/config",
                cookies={"session_id": str(mock_session.session_id)},
            )
        assert response.status_code == 200


class TestWorkflowUpdateConfig:
    """Tests for PUT /workflow/config."""

    @pytest.mark.asyncio
    async def test_update_config_no_project(self, client):
        session = _make_session(selected_project_id=None)
        with patch("src.api.auth.get_current_session", return_value=session):
            response = await client.put(
                "/api/v1/workflow/config",
                json={
                    "project_id": "x",
                    "repository_owner": "o",
                    "repository_name": "r",
                },
                cookies={"session_id": str(session.session_id)},
            )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_config_success(self, client, mock_session):
        with patch("src.api.workflow.set_workflow_config") as mock_set:
            response = await client.put(
                "/api/v1/workflow/config",
                json={
                    "project_id": "ignored",
                    "repository_owner": "new_owner",
                    "repository_name": "new_repo",
                },
                cookies={"session_id": str(mock_session.session_id)},
            )
        assert response.status_code == 200
        assert response.json()["repository_owner"] == "new_owner"
        # project_id should be overridden to match session
        assert response.json()["project_id"] == TEST_PROJECT_ID
        mock_set.assert_called_once()


class TestWorkflowListAgents:
    """Tests for GET /workflow/agents."""

    @pytest.mark.asyncio
    async def test_list_agents_no_project(self, client):
        session = _make_session(selected_project_id=None)
        with patch("src.api.auth.get_current_session", return_value=session):
            response = await client.get(
                "/api/v1/workflow/agents",
                cookies={"session_id": str(session.session_id)},
            )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_list_agents_success(self, client, mock_session):
        with (
            patch("src.api.workflow.get_workflow_config", return_value=None),
            patch("src.api.workflow.cache") as mock_cache,
            patch(
                "src.api.workflow.github_projects_service.list_available_agents",
                new_callable=AsyncMock,
                return_value=[],
            ),
        ):
            mock_cache.get.return_value = None
            response = await client.get(
                "/api/v1/workflow/agents",
                cookies={"session_id": str(mock_session.session_id)},
            )
        assert response.status_code == 200
        assert "agents" in response.json()

    @pytest.mark.asyncio
    async def test_list_agents_with_config(self, client, mock_session):
        config = WorkflowConfiguration(
            project_id=TEST_PROJECT_ID,
            repository_owner="cfg_owner",
            repository_name="cfg_repo",
        )
        with (
            patch("src.api.workflow.get_workflow_config", return_value=config),
            patch(
                "src.api.workflow.github_projects_service.list_available_agents",
                new_callable=AsyncMock,
                return_value=[],
            ),
        ):
            response = await client.get(
                "/api/v1/workflow/agents",
                cookies={"session_id": str(mock_session.session_id)},
            )
        assert response.status_code == 200


class TestWorkflowTransitions:
    """Tests for GET /workflow/transitions."""

    @pytest.mark.asyncio
    async def test_get_transitions(self, client, mock_session):
        with patch("src.api.workflow.get_transitions", return_value=[]):
            response = await client.get(
                "/api/v1/workflow/transitions",
                cookies={"session_id": str(mock_session.session_id)},
            )
        assert response.status_code == 200
        assert response.json() == []


class TestWorkflowPipelineStates:
    """Tests for GET /workflow/pipeline-states."""

    @pytest.mark.asyncio
    async def test_list_pipeline_states(self, client, mock_session):
        with patch("src.api.workflow.get_all_pipeline_states", return_value={}):
            response = await client.get(
                "/api/v1/workflow/pipeline-states",
                cookies={"session_id": str(mock_session.session_id)},
            )
        assert response.status_code == 200
        assert response.json()["count"] == 0

    @pytest.mark.asyncio
    async def test_get_pipeline_state_not_found(self, client, mock_session):
        with patch("src.api.workflow.get_pipeline_state", return_value=None):
            response = await client.get(
                "/api/v1/workflow/pipeline-states/999",
                cookies={"session_id": str(mock_session.session_id)},
            )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_pipeline_state_success(self, client, mock_session):
        from src.services.workflow_orchestrator import PipelineState

        state = PipelineState(
            issue_number=1,
            project_id=TEST_PROJECT_ID,
            status="Backlog",
            agents=["speckit.specify"],
            current_agent_index=0,
        )
        with patch("src.api.workflow.get_pipeline_state", return_value=state):
            response = await client.get(
                "/api/v1/workflow/pipeline-states/1",
                cookies={"session_id": str(mock_session.session_id)},
            )
        assert response.status_code == 200
        assert response.json()["issue_number"] == 1

    @pytest.mark.asyncio
    async def test_get_pipeline_state_wrong_project(self, client, mock_session):
        """Should return 404 when pipeline state belongs to a different project."""
        from src.services.workflow_orchestrator import PipelineState

        state = PipelineState(
            issue_number=1,
            project_id="OTHER_PROJECT",
            status="Backlog",
            agents=["speckit.specify"],
            current_agent_index=0,
        )
        with patch("src.api.workflow.get_pipeline_state", return_value=state):
            response = await client.get(
                "/api/v1/workflow/pipeline-states/1",
                cookies={"session_id": str(mock_session.session_id)},
            )
        assert response.status_code == 404


class TestWorkflowNotifyInReview:
    """Tests for POST /workflow/notify/in-review."""

    @pytest.mark.asyncio
    async def test_notify_no_project(self, client):
        session = _make_session(selected_project_id=None)
        with patch("src.api.auth.get_current_session", return_value=session):
            response = await client.post(
                "/api/v1/workflow/notify/in-review",
                params={
                    "issue_id": "I_1",
                    "issue_number": "1",
                    "title": "T",
                    "reviewer": "R",
                },
                cookies={"session_id": str(session.session_id)},
            )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_notify_success(self, client, mock_session):
        with patch(
            "src.api.workflow.connection_manager.broadcast_to_project",
            new_callable=AsyncMock,
        ):
            response = await client.post(
                "/api/v1/workflow/notify/in-review",
                params={
                    "issue_id": "I_1",
                    "issue_number": "1",
                    "title": "T",
                    "reviewer": "R",
                },
                cookies={"session_id": str(mock_session.session_id)},
            )
        assert response.status_code == 200
        assert response.json()["message"] == "Notification sent"


class TestWorkflowPollingStatus:
    """Tests for GET /workflow/polling/status."""

    @pytest.mark.asyncio
    async def test_polling_status(self, client, mock_session):
        with patch(
            "src.services.copilot_polling.get_polling_status",
            return_value={"is_running": False},
        ):
            response = await client.get(
                "/api/v1/workflow/polling/status",
                cookies={"session_id": str(mock_session.session_id)},
            )
        assert response.status_code == 200


class TestWorkflowPollingCheckIssue:
    """Tests for POST /workflow/polling/check-issue/{issue_number}."""

    @pytest.mark.asyncio
    async def test_check_issue_no_project(self, client):
        session = _make_session(selected_project_id=None)
        with patch("src.api.auth.get_current_session", return_value=session):
            response = await client.post(
                "/api/v1/workflow/polling/check-issue/1",
                cookies={"session_id": str(session.session_id)},
            )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_check_issue_success(self, client, mock_session):
        with (
            patch(
                "src.api.workflow.github_projects_service.get_project_repository",
                new_callable=AsyncMock,
                return_value=("owner", "repo"),
            ),
            patch(
                "src.services.copilot_polling.check_issue_for_copilot_completion",
                new_callable=AsyncMock,
                return_value={"status": "no_pr_found"},
            ),
        ):
            response = await client.post(
                "/api/v1/workflow/polling/check-issue/1",
                cookies={"session_id": str(mock_session.session_id)},
            )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_check_issue_broadcasts_on_success(self, client, mock_session):
        with (
            patch(
                "src.api.workflow.github_projects_service.get_project_repository",
                new_callable=AsyncMock,
                return_value=("owner", "repo"),
            ),
            patch(
                "src.services.copilot_polling.check_issue_for_copilot_completion",
                new_callable=AsyncMock,
                return_value={"status": "success", "task_title": "T", "pr_number": 5},
            ),
            patch(
                "src.api.workflow.connection_manager.broadcast_to_project",
                new_callable=AsyncMock,
            ) as mock_broadcast,
        ):
            response = await client.post(
                "/api/v1/workflow/polling/check-issue/1",
                cookies={"session_id": str(mock_session.session_id)},
            )
        assert response.status_code == 200
        mock_broadcast.assert_called_once()


class TestWorkflowPollingStop:
    """Tests for POST /workflow/polling/stop."""

    @pytest.mark.asyncio
    async def test_stop_when_not_running(self, client, mock_session):
        with (
            patch(
                "src.services.copilot_polling.get_polling_status",
                return_value={"is_running": False},
            ),
            patch("src.services.copilot_polling.stop_polling"),
        ):
            response = await client.post(
                "/api/v1/workflow/polling/stop",
                cookies={"session_id": str(mock_session.session_id)},
            )
        assert response.status_code == 200
        assert "not running" in response.json()["message"].lower()

    @pytest.mark.asyncio
    async def test_stop_when_running(self, client, mock_session):
        with (
            patch(
                "src.services.copilot_polling.get_polling_status",
                side_effect=[
                    {"is_running": True},
                    {"is_running": False},
                ],
            ),
            patch("src.services.copilot_polling.stop_polling"),
        ):
            response = await client.post(
                "/api/v1/workflow/polling/stop",
                cookies={"session_id": str(mock_session.session_id)},
            )
        assert response.status_code == 200


class TestWorkflowPollingCheckAll:
    """Tests for POST /workflow/polling/check-all."""

    @pytest.mark.asyncio
    async def test_check_all_no_project(self, client):
        session = _make_session(selected_project_id=None)
        with patch("src.api.auth.get_current_session", return_value=session):
            response = await client.post(
                "/api/v1/workflow/polling/check-all",
                cookies={"session_id": str(session.session_id)},
            )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_check_all_success(self, client, mock_session):
        with (
            patch(
                "src.api.workflow.github_projects_service.get_project_repository",
                new_callable=AsyncMock,
                return_value=("owner", "repo"),
            ),
            patch(
                "src.services.copilot_polling.check_in_progress_issues",
                new_callable=AsyncMock,
                return_value=[],
            ),
        ):
            response = await client.post(
                "/api/v1/workflow/polling/check-all",
                cookies={"session_id": str(mock_session.session_id)},
            )
        assert response.status_code == 200
        assert response.json()["checked_count"] == 0


class TestWorkflowPollingStart:
    """Tests for POST /workflow/polling/start."""

    @pytest.mark.asyncio
    async def test_start_no_project(self, client):
        session = _make_session(selected_project_id=None)
        with patch("src.api.auth.get_current_session", return_value=session):
            response = await client.post(
                "/api/v1/workflow/polling/start",
                cookies={"session_id": str(session.session_id)},
            )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_start_already_running(self, client, mock_session):
        with patch(
            "src.services.copilot_polling.get_polling_status",
            return_value={"is_running": True},
        ):
            response = await client.post(
                "/api/v1/workflow/polling/start",
                cookies={"session_id": str(mock_session.session_id)},
            )
        assert response.status_code == 200
        assert "already running" in response.json()["message"].lower()


# ===================================================================
# Projects endpoints
# ===================================================================


class TestListProjects:
    """Tests for GET /projects."""

    @pytest.mark.asyncio
    async def test_list_projects_requires_auth(self, client):
        response = await client.get("/api/v1/projects")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_list_projects_cached(self, client, mock_session):
        project = _make_project()
        with patch("src.api.projects.cache") as mock_cache:
            mock_cache.get.return_value = [project]
            response = await client.get(
                "/api/v1/projects",
                cookies={"session_id": str(mock_session.session_id)},
            )
        assert response.status_code == 200
        assert len(response.json()["projects"]) == 1

    @pytest.mark.asyncio
    async def test_list_projects_from_github(self, client, mock_session):
        project = _make_project()
        with (
            patch("src.api.projects.cache") as mock_cache,
            patch(
                "src.api.projects.github_projects_service.list_user_projects",
                new_callable=AsyncMock,
                return_value=[project],
            ),
        ):
            mock_cache.get.return_value = None
            response = await client.get(
                "/api/v1/projects",
                cookies={"session_id": str(mock_session.session_id)},
            )
        assert response.status_code == 200
        assert len(response.json()["projects"]) == 1

    @pytest.mark.asyncio
    async def test_list_projects_refresh(self, client, mock_session):
        project = _make_project()
        with (
            patch("src.api.projects.cache"),
            patch(
                "src.api.projects.github_projects_service.list_user_projects",
                new_callable=AsyncMock,
                return_value=[project],
            ),
        ):
            response = await client.get(
                "/api/v1/projects",
                params={"refresh": True},
                cookies={"session_id": str(mock_session.session_id)},
            )
        assert response.status_code == 200


class TestGetProject:
    """Tests for GET /projects/{project_id}."""

    @pytest.mark.asyncio
    async def test_get_project_cached(self, client, mock_session):
        project = _make_project()
        with patch("src.api.projects.cache") as mock_cache:
            mock_cache.get.return_value = [project]
            response = await client.get(
                f"/api/v1/projects/{TEST_PROJECT_ID}",
                cookies={"session_id": str(mock_session.session_id)},
            )
        assert response.status_code == 200
        assert response.json()["project_id"] == TEST_PROJECT_ID

    @pytest.mark.asyncio
    async def test_get_project_not_found(self, client, mock_session):
        with (
            patch("src.api.projects.cache") as mock_cache,
            patch(
                "src.api.projects.github_projects_service.list_user_projects",
                new_callable=AsyncMock,
                return_value=[],
            ),
        ):
            mock_cache.get.return_value = None
            response = await client.get(
                "/api/v1/projects/NONEXISTENT",
                cookies={"session_id": str(mock_session.session_id)},
            )
        assert response.status_code == 404


class TestGetProjectTasks:
    """Tests for GET /projects/{project_id}/tasks."""

    @pytest.mark.asyncio
    async def test_get_tasks_cached(self, client, mock_session):
        task = _make_task()
        with patch("src.api.projects.cache") as mock_cache:
            mock_cache.get.return_value = [task]
            response = await client.get(
                f"/api/v1/projects/{TEST_PROJECT_ID}/tasks",
                cookies={"session_id": str(mock_session.session_id)},
            )
        assert response.status_code == 200
        assert len(response.json()["tasks"]) == 1

    @pytest.mark.asyncio
    async def test_get_tasks_from_github(self, client, mock_session):
        task = _make_task()
        with (
            patch("src.api.projects.cache") as mock_cache,
            patch(
                "src.api.projects.github_projects_service.get_project_items",
                new_callable=AsyncMock,
                return_value=[task],
            ),
        ):
            mock_cache.get.return_value = None
            response = await client.get(
                f"/api/v1/projects/{TEST_PROJECT_ID}/tasks",
                cookies={"session_id": str(mock_session.session_id)},
            )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_tasks_refresh(self, client, mock_session):
        task = _make_task()
        with (
            patch("src.api.projects.cache"),
            patch(
                "src.api.projects.github_projects_service.get_project_items",
                new_callable=AsyncMock,
                return_value=[task],
            ),
        ):
            response = await client.get(
                f"/api/v1/projects/{TEST_PROJECT_ID}/tasks",
                params={"refresh": True},
                cookies={"session_id": str(mock_session.session_id)},
            )
        assert response.status_code == 200


class TestSelectProject:
    """Tests for POST /projects/{project_id}/select."""

    @pytest.mark.asyncio
    async def test_select_project_success(self, client, mock_session):
        project = _make_project()
        with (
            patch("src.api.projects.cache") as mock_cache,
            patch(
                "src.api.projects.github_auth_service.update_session",
            ),
            patch(
                "src.api.projects.github_projects_service.get_project_repository",
                new_callable=AsyncMock,
                return_value=None,
            ),
            patch(
                "src.services.copilot_polling.get_polling_status",
                return_value={"is_running": False},
            ),
        ):
            mock_cache.get.return_value = [project]
            response = await client.post(
                f"/api/v1/projects/{TEST_PROJECT_ID}/select",
                cookies={"session_id": str(mock_session.session_id)},
            )
        assert response.status_code == 200
        assert response.json()["selected_project_id"] == TEST_PROJECT_ID

    @pytest.mark.asyncio
    async def test_select_project_not_found(self, client, mock_session):
        with (
            patch("src.api.projects.cache") as mock_cache,
            patch(
                "src.api.projects.github_projects_service.list_user_projects",
                new_callable=AsyncMock,
                return_value=[],
            ),
        ):
            mock_cache.get.return_value = None
            response = await client.post(
                "/api/v1/projects/NONEXISTENT/select",
                cookies={"session_id": str(mock_session.session_id)},
            )
        assert response.status_code == 404


# ===================================================================
# Tasks endpoints
# ===================================================================


class TestCreateTask:
    """Tests for POST /tasks."""

    @pytest.mark.asyncio
    async def test_create_task_no_project(self, client):
        session = _make_session(selected_project_id=None)
        with patch("src.api.auth.get_current_session", return_value=session):
            response = await client.post(
                "/api/v1/tasks",
                json={"project_id": "", "title": "Task"},
                cookies={"session_id": str(session.session_id)},
            )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_task_success(self, client, mock_session):
        with (
            patch(
                "src.api.tasks.github_projects_service.get_project_repository",
                new_callable=AsyncMock,
                return_value=("owner", "repo"),
            ),
            patch(
                "src.api.tasks.github_projects_service.create_issue",
                new_callable=AsyncMock,
                return_value={
                    "number": 5,
                    "node_id": "I_5",
                    "html_url": "https://github.com/o/r/issues/5",
                },
            ),
            patch(
                "src.api.tasks.github_projects_service.add_issue_to_project",
                new_callable=AsyncMock,
                return_value="PVTI_5",
            ),
            patch("src.api.tasks.cache"),
            patch(
                "src.api.tasks.connection_manager.broadcast_to_project",
                new_callable=AsyncMock,
            ),
        ):
            response = await client.post(
                "/api/v1/tasks",
                json={"project_id": TEST_PROJECT_ID, "title": "New Task"},
                cookies={"session_id": str(mock_session.session_id)},
            )
        assert response.status_code == 200
        assert response.json()["title"] == "New Task"
        assert response.json()["issue_number"] == 5

    @pytest.mark.asyncio
    async def test_create_task_add_to_project_fails(self, client, mock_session):
        """Should return 422 when add_issue_to_project returns None."""
        with (
            patch(
                "src.api.tasks.github_projects_service.get_project_repository",
                new_callable=AsyncMock,
                return_value=("owner", "repo"),
            ),
            patch(
                "src.api.tasks.github_projects_service.create_issue",
                new_callable=AsyncMock,
                return_value={
                    "number": 6,
                    "node_id": "I_6",
                    "html_url": "https://github.com/o/r/issues/6",
                },
            ),
            patch(
                "src.api.tasks.github_projects_service.add_issue_to_project",
                new_callable=AsyncMock,
                return_value=None,
            ),
        ):
            response = await client.post(
                "/api/v1/tasks",
                json={"project_id": TEST_PROJECT_ID, "title": "New Task"},
                cookies={"session_id": str(mock_session.session_id)},
            )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_task_uses_session_project(self, client, mock_session):
        """Should use session's selected project when project_id not in request."""
        with (
            patch(
                "src.api.tasks.github_projects_service.get_project_repository",
                new_callable=AsyncMock,
                return_value=("owner", "repo"),
            ),
            patch(
                "src.api.tasks.github_projects_service.create_issue",
                new_callable=AsyncMock,
                return_value={
                    "number": 7,
                    "node_id": "I_7",
                    "html_url": "https://github.com/o/r/issues/7",
                },
            ),
            patch(
                "src.api.tasks.github_projects_service.add_issue_to_project",
                new_callable=AsyncMock,
                return_value="PVTI_7",
            ),
            patch("src.api.tasks.cache"),
            patch(
                "src.api.tasks.connection_manager.broadcast_to_project",
                new_callable=AsyncMock,
            ),
        ):
            response = await client.post(
                "/api/v1/tasks",
                json={"project_id": "", "title": "Task from session"},
                cookies={"session_id": str(mock_session.session_id)},
            )
        assert response.status_code == 200


class TestUpdateTaskStatus:
    """Tests for PATCH /tasks/{task_id}/status."""

    @pytest.mark.asyncio
    async def test_update_status_no_project(self, client):
        session = _make_session(selected_project_id=None)
        with patch("src.api.auth.get_current_session", return_value=session):
            response = await client.patch(
                "/api/v1/tasks/task1/status",
                params={"status": "Done"},
                cookies={"session_id": str(session.session_id)},
            )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_update_status_task_not_found(self, client, mock_session):
        with (
            patch("src.api.tasks.cache") as mock_cache,
            patch(
                "src.api.tasks.github_projects_service.get_project_items",
                new_callable=AsyncMock,
                return_value=[],
            ),
        ):
            mock_cache.get.return_value = None
            response = await client.patch(
                "/api/v1/tasks/nonexistent/status",
                params={"status": "Done"},
                cookies={"session_id": str(mock_session.session_id)},
            )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_status_success(self, client, mock_session):
        task = _make_task(github_item_id="PVTI_target")
        with (
            patch("src.api.tasks.cache") as mock_cache,
            patch(
                "src.api.tasks.connection_manager.broadcast_to_project",
                new_callable=AsyncMock,
            ),
        ):
            mock_cache.get.return_value = [task]
            response = await client.patch(
                "/api/v1/tasks/PVTI_target/status",
                params={"status": "Done"},
                cookies={"session_id": str(mock_session.session_id)},
            )
        assert response.status_code == 200
        assert response.json()["status"] == "Done"

    @pytest.mark.asyncio
    async def test_update_status_fetches_when_not_cached(self, client, mock_session):
        task = _make_task(github_item_id="PVTI_x")
        with (
            patch("src.api.tasks.cache") as mock_cache,
            patch(
                "src.api.tasks.github_projects_service.get_project_items",
                new_callable=AsyncMock,
                return_value=[task],
            ),
            patch(
                "src.api.tasks.connection_manager.broadcast_to_project",
                new_callable=AsyncMock,
            ),
        ):
            mock_cache.get.return_value = None
            response = await client.patch(
                "/api/v1/tasks/PVTI_x/status",
                params={"status": "In Progress"},
                cookies={"session_id": str(mock_session.session_id)},
            )
        assert response.status_code == 200


# ===================================================================
# Board endpoints
# ===================================================================


class TestListBoardProjects:
    """Tests for GET /board/projects."""

    @pytest.mark.asyncio
    async def test_list_board_projects_requires_auth(self, client):
        response = await client.get("/api/v1/board/projects")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_list_board_projects_cached(self, client, mock_session):
        bp = BoardProject(
            project_id="P1",
            name="Board",
            url="https://github.com/u/p/1",
            owner_login="u",
            status_field=StatusField(
                field_id="SF1",
                options=[
                    StatusOption(option_id="O1", name="Todo", color=StatusColor.GRAY),
                ],
            ),
        )
        with patch("src.api.board.cache") as mock_cache:
            mock_cache.get.return_value = [bp]
            response = await client.get(
                "/api/v1/board/projects",
                cookies={"session_id": str(mock_session.session_id)},
            )
        assert response.status_code == 200
        assert len(response.json()["projects"]) == 1

    @pytest.mark.asyncio
    async def test_list_board_projects_from_github(self, client, mock_session):
        bp = BoardProject(
            project_id="P1",
            name="Board",
            url="https://github.com/u/p/1",
            owner_login="u",
            status_field=StatusField(
                field_id="SF1",
                options=[
                    StatusOption(option_id="O1", name="Todo", color=StatusColor.GRAY),
                ],
            ),
        )
        with (
            patch("src.api.board.cache") as mock_cache,
            patch(
                "src.api.board.github_projects_service.list_board_projects",
                new_callable=AsyncMock,
                return_value=[bp],
            ),
        ):
            mock_cache.get.return_value = None
            response = await client.get(
                "/api/v1/board/projects",
                cookies={"session_id": str(mock_session.session_id)},
            )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_list_board_projects_github_error(self, client, mock_session):
        with (
            patch("src.api.board.cache") as mock_cache,
            patch(
                "src.api.board.github_projects_service.list_board_projects",
                new_callable=AsyncMock,
                side_effect=RuntimeError("API error"),
            ),
        ):
            mock_cache.get.return_value = None
            response = await client.get(
                "/api/v1/board/projects",
                cookies={"session_id": str(mock_session.session_id)},
            )
        assert response.status_code == 502

    @pytest.mark.asyncio
    async def test_list_board_projects_refresh(self, client, mock_session):
        with (
            patch("src.api.board.cache"),
            patch(
                "src.api.board.github_projects_service.list_board_projects",
                new_callable=AsyncMock,
                return_value=[],
            ),
        ):
            response = await client.get(
                "/api/v1/board/projects",
                params={"refresh": True},
                cookies={"session_id": str(mock_session.session_id)},
            )
        assert response.status_code == 200


class TestGetBoardData:
    """Tests for GET /board/projects/{project_id}."""

    def _make_board_data(self):
        bp = BoardProject(
            project_id="P1",
            name="Board",
            url="https://github.com/u/p/1",
            owner_login="u",
            status_field=StatusField(
                field_id="SF1",
                options=[
                    StatusOption(option_id="O1", name="Todo", color=StatusColor.GRAY),
                ],
            ),
        )
        return BoardDataResponse(
            project=bp,
            columns=[
                BoardColumn(
                    status=StatusOption(option_id="O1", name="Todo", color=StatusColor.GRAY),
                    items=[],
                )
            ],
        )

    @pytest.mark.asyncio
    async def test_get_board_data_cached(self, client, mock_session):
        board_data = self._make_board_data()
        with patch("src.api.board.cache") as mock_cache:
            mock_cache.get.return_value = board_data
            response = await client.get(
                "/api/v1/board/projects/P1",
                cookies={"session_id": str(mock_session.session_id)},
            )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_board_data_from_github(self, client, mock_session):
        board_data = self._make_board_data()
        with (
            patch("src.api.board.cache") as mock_cache,
            patch(
                "src.api.board.github_projects_service.get_board_data",
                new_callable=AsyncMock,
                return_value=board_data,
            ),
        ):
            mock_cache.get.return_value = None
            response = await client.get(
                "/api/v1/board/projects/P1",
                cookies={"session_id": str(mock_session.session_id)},
            )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_board_data_not_found(self, client, mock_session):
        with (
            patch("src.api.board.cache") as mock_cache,
            patch(
                "src.api.board.github_projects_service.get_board_data",
                new_callable=AsyncMock,
                side_effect=ValueError("not found"),
            ),
        ):
            mock_cache.get.return_value = None
            response = await client.get(
                "/api/v1/board/projects/INVALID",
                cookies={"session_id": str(mock_session.session_id)},
            )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_board_data_github_error(self, client, mock_session):
        with (
            patch("src.api.board.cache") as mock_cache,
            patch(
                "src.api.board.github_projects_service.get_board_data",
                new_callable=AsyncMock,
                side_effect=RuntimeError("API fail"),
            ),
        ):
            mock_cache.get.return_value = None
            response = await client.get(
                "/api/v1/board/projects/P1",
                cookies={"session_id": str(mock_session.session_id)},
            )
        assert response.status_code == 502

    @pytest.mark.asyncio
    async def test_get_board_data_refresh(self, client, mock_session):
        board_data = self._make_board_data()
        with (
            patch("src.api.board.cache"),
            patch(
                "src.api.board.github_projects_service.get_board_data",
                new_callable=AsyncMock,
                return_value=board_data,
            ),
        ):
            response = await client.get(
                "/api/v1/board/projects/P1",
                params={"refresh": True},
                cookies={"session_id": str(mock_session.session_id)},
            )
        assert response.status_code == 200


# ===================================================================
# Additional coverage tests for remaining gaps
# ===================================================================


class TestChatResolveRepository:
    """Tests for _resolve_repository fallback paths in chat.py."""

    @pytest.mark.asyncio
    async def test_resolve_repository_via_workflow_config(self, client, mock_session):
        """Should fall back to workflow config when project items have no repo."""
        from src.api.chat import _proposals

        proposal = AITaskProposal(
            session_id=mock_session.session_id,
            original_input="input",
            proposed_title="Title",
            proposed_description="Desc",
        )
        _proposals[str(proposal.proposal_id)] = proposal

        config = WorkflowConfiguration(
            project_id=TEST_PROJECT_ID,
            repository_owner="cfg_owner",
            repository_name="cfg_repo",
        )

        with (
            patch(
                "src.api.chat.github_projects_service.get_project_repository",
                new_callable=AsyncMock,
                return_value=None,
            ),
            patch("src.api.chat.get_workflow_config", return_value=config),
            patch(
                "src.api.chat.github_projects_service.create_issue",
                new_callable=AsyncMock,
                return_value={
                    "number": 99,
                    "node_id": "I_99",
                    "html_url": "https://github.com/cfg_owner/cfg_repo/issues/99",
                },
            ),
            patch(
                "src.api.chat.github_projects_service.add_issue_to_project",
                new_callable=AsyncMock,
                return_value="PVTI_99",
            ),
            patch(
                "src.api.chat.connection_manager.broadcast_to_project",
                new_callable=AsyncMock,
            ),
            patch(
                "src.api.chat.github_projects_service.update_item_status_by_name",
                new_callable=AsyncMock,
            ),
            patch("src.api.chat.get_workflow_orchestrator") as mock_orch,
            patch("src.api.chat.set_workflow_config"),
        ):
            mock_orch.return_value.assign_agent_for_status = AsyncMock()
            response = await client.post(
                f"/api/v1/chat/proposals/{proposal.proposal_id}/confirm",
                json={},
                cookies={"session_id": str(mock_session.session_id)},
            )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_resolve_repository_via_settings(self, client, mock_session):
        """Should fall back to default settings when no project repo or config."""
        from src.api.chat import _proposals

        proposal = AITaskProposal(
            session_id=mock_session.session_id,
            original_input="input",
            proposed_title="Title",
            proposed_description="Desc",
        )
        _proposals[str(proposal.proposal_id)] = proposal

        mock_settings = MagicMock(
            default_repo_owner="setting_owner",
            default_repo_name="setting_repo",
            default_assignee="",
        )

        with (
            patch(
                "src.api.chat.github_projects_service.get_project_repository",
                new_callable=AsyncMock,
                return_value=None,
            ),
            patch("src.api.chat.get_workflow_config", return_value=None),
            patch("src.config.get_settings", return_value=mock_settings),
            patch(
                "src.api.chat.github_projects_service.create_issue",
                new_callable=AsyncMock,
                return_value={
                    "number": 100,
                    "node_id": "I_100",
                    "html_url": "https://github.com/setting_owner/setting_repo/issues/100",
                },
            ),
            patch(
                "src.api.chat.github_projects_service.add_issue_to_project",
                new_callable=AsyncMock,
                return_value="PVTI_100",
            ),
            patch(
                "src.api.chat.connection_manager.broadcast_to_project",
                new_callable=AsyncMock,
            ),
            patch(
                "src.api.chat.github_projects_service.update_item_status_by_name",
                new_callable=AsyncMock,
            ),
            patch("src.api.chat.get_workflow_orchestrator") as mock_orch,
            patch("src.api.chat.set_workflow_config"),
        ):
            mock_orch.return_value.assign_agent_for_status = AsyncMock()
            response = await client.post(
                f"/api/v1/chat/proposals/{proposal.proposal_id}/confirm",
                json={},
                cookies={"session_id": str(mock_session.session_id)},
            )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_resolve_repository_no_repo_found(self, client, mock_session):
        """Should return error when no repo can be resolved."""
        from src.api.chat import _proposals

        proposal = AITaskProposal(
            session_id=mock_session.session_id,
            original_input="input",
            proposed_title="Title",
            proposed_description="Desc",
        )
        _proposals[str(proposal.proposal_id)] = proposal

        mock_settings = MagicMock(
            default_repo_owner=None,
            default_repo_name=None,
        )

        with (
            patch(
                "src.api.chat.github_projects_service.get_project_repository",
                new_callable=AsyncMock,
                return_value=None,
            ),
            patch("src.api.chat.get_workflow_config", return_value=None),
            patch("src.config.get_settings", return_value=mock_settings),
        ):
            response = await client.post(
                f"/api/v1/chat/proposals/{proposal.proposal_id}/confirm",
                json={},
                cookies={"session_id": str(mock_session.session_id)},
            )
        assert response.status_code == 422


class TestChatSendMessageEdgeCases:
    """Additional edge-case tests for POST /chat/messages."""

    @pytest.mark.asyncio
    async def test_feature_detection_exception_falls_through(self, client, mock_session):
        """When feature detection raises, should fall through to status change."""

        @dataclass
        class _Generated:
            title: str = "Title"
            description: str = "Desc " * 50

        mock_ai = MagicMock()
        mock_ai.detect_feature_request_intent = AsyncMock(
            side_effect=RuntimeError("detection error")
        )
        mock_ai.parse_status_change_request = AsyncMock(return_value=None)
        mock_ai.generate_task_from_description = AsyncMock(return_value=_Generated())

        with (
            patch("src.api.chat.get_ai_agent_service", return_value=mock_ai),
            patch("src.api.chat.cache") as mock_cache,
        ):
            mock_cache.get.return_value = None
            response = await client.post(
                "/api/v1/chat/messages",
                json={"content": "Do something"},
                cookies={"session_id": str(mock_session.session_id)},
            )
        assert response.status_code == 200
        assert response.json()["action_type"] == "task_create"

    @pytest.mark.asyncio
    async def test_feature_request_with_technical_notes(self, client, mock_session):
        """Should include technical notes in recommendation response."""
        mock_ai = MagicMock()
        mock_ai.detect_feature_request_intent = AsyncMock(return_value=True)
        rec = IssueRecommendation(
            session_id=mock_session.session_id,
            original_input="Add export",
            title="CSV Export",
            user_story="As a user I want export",
            ui_ux_description="Button",
            functional_requirements=["Export CSV"],
            technical_notes="Use streaming for large files. " * 30,
        )
        mock_ai.generate_issue_recommendation = AsyncMock(return_value=rec)

        with (
            patch("src.api.chat.get_ai_agent_service", return_value=mock_ai),
            patch("src.api.chat.cache") as mock_cache,
        ):
            mock_cache.get.return_value = None
            response = await client.post(
                "/api/v1/chat/messages",
                json={"content": "Add export"},
                cookies={"session_id": str(mock_session.session_id)},
            )
        assert response.status_code == 200
        assert "Technical Notes" in response.json()["content"]

    @pytest.mark.asyncio
    async def test_status_change_with_column_match(self, client, mock_session):
        """Should match status columns from cached projects."""

        @dataclass
        class _StatusChange:
            task_reference: str = "Test Task"
            target_status: str = "In Progress"
            confidence: float = 0.9

        task = _make_task()
        project = _make_project()
        mock_ai = MagicMock()
        mock_ai.detect_feature_request_intent = AsyncMock(return_value=False)
        mock_ai.parse_status_change_request = AsyncMock(return_value=_StatusChange())
        mock_ai.identify_target_task.return_value = task

        with (
            patch("src.api.chat.get_ai_agent_service", return_value=mock_ai),
            patch("src.api.chat.cache") as mock_cache,
        ):
            mock_cache.get.side_effect = lambda key: [project] if "projects" in key else [task]
            response = await client.post(
                "/api/v1/chat/messages",
                json={"content": "Move Test Task to In Progress"},
                cookies={"session_id": str(mock_session.session_id)},
            )
        assert response.status_code == 200
        data = response.json()
        assert data["action_type"] == "status_update"
        assert data["action_data"]["status_option_id"] == "opt2"


class TestTasksResolveRepo:
    """Tests for _resolve_repository_for_project fallbacks in tasks.py."""

    @pytest.mark.asyncio
    async def test_resolve_via_workflow_config(self, client, mock_session):
        config = WorkflowConfiguration(
            project_id=TEST_PROJECT_ID,
            repository_owner="wf_owner",
            repository_name="wf_repo",
        )
        with (
            patch(
                "src.api.tasks.github_projects_service.get_project_repository",
                new_callable=AsyncMock,
                return_value=None,
            ),
            patch("src.api.tasks.get_workflow_config", return_value=config),
            patch(
                "src.api.tasks.github_projects_service.create_issue",
                new_callable=AsyncMock,
                return_value={
                    "number": 50,
                    "node_id": "I_50",
                    "html_url": "https://github.com/wf_owner/wf_repo/issues/50",
                },
            ),
            patch(
                "src.api.tasks.github_projects_service.add_issue_to_project",
                new_callable=AsyncMock,
                return_value="PVTI_50",
            ),
            patch("src.api.tasks.cache"),
            patch(
                "src.api.tasks.connection_manager.broadcast_to_project",
                new_callable=AsyncMock,
            ),
        ):
            response = await client.post(
                "/api/v1/tasks",
                json={"project_id": TEST_PROJECT_ID, "title": "Task"},
                cookies={"session_id": str(mock_session.session_id)},
            )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_resolve_via_settings(self, client, mock_session):
        mock_settings = MagicMock(
            default_repo_owner="set_owner",
            default_repo_name="set_repo",
        )
        with (
            patch(
                "src.api.tasks.github_projects_service.get_project_repository",
                new_callable=AsyncMock,
                return_value=None,
            ),
            patch("src.api.tasks.get_workflow_config", return_value=None),
            patch("src.config.get_settings", return_value=mock_settings),
            patch(
                "src.api.tasks.github_projects_service.create_issue",
                new_callable=AsyncMock,
                return_value={
                    "number": 51,
                    "node_id": "I_51",
                    "html_url": "https://github.com/set_owner/set_repo/issues/51",
                },
            ),
            patch(
                "src.api.tasks.github_projects_service.add_issue_to_project",
                new_callable=AsyncMock,
                return_value="PVTI_51",
            ),
            patch("src.api.tasks.cache"),
            patch(
                "src.api.tasks.connection_manager.broadcast_to_project",
                new_callable=AsyncMock,
            ),
        ):
            response = await client.post(
                "/api/v1/tasks",
                json={"project_id": TEST_PROJECT_ID, "title": "Task"},
                cookies={"session_id": str(mock_session.session_id)},
            )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_resolve_no_repo_returns_422(self, client, mock_session):
        mock_settings = MagicMock(
            default_repo_owner=None,
            default_repo_name=None,
        )
        with (
            patch(
                "src.api.tasks.github_projects_service.get_project_repository",
                new_callable=AsyncMock,
                return_value=None,
            ),
            patch("src.api.tasks.get_workflow_config", return_value=None),
            patch("src.config.get_settings", return_value=mock_settings),
        ):
            response = await client.post(
                "/api/v1/tasks",
                json={"project_id": TEST_PROJECT_ID, "title": "Task"},
                cookies={"session_id": str(mock_session.session_id)},
            )
        assert response.status_code == 422


class TestGetProjectFallback:
    """Tests for GET /projects/{project_id} refresh fallback."""

    @pytest.mark.asyncio
    async def test_get_project_refreshes_when_not_cached(self, client, mock_session):
        """Should refresh project list when project not in cache."""
        project = _make_project()
        call_count = 0

        def mock_cache_get(key):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return []  # First call: project not in list
            return None  # Second call: force refresh

        with (
            patch("src.api.projects.cache") as mock_cache,
            patch(
                "src.api.projects.github_projects_service.list_user_projects",
                new_callable=AsyncMock,
                return_value=[project],
            ),
        ):
            mock_cache.get.side_effect = mock_cache_get
            response = await client.get(
                f"/api/v1/projects/{TEST_PROJECT_ID}",
                cookies={"session_id": str(mock_session.session_id)},
            )
        assert response.status_code == 200


class TestWorkflowDuplicateDetection:
    """Tests for duplicate detection in workflow confirm."""

    @pytest.mark.asyncio
    async def test_duplicate_request_blocked(self, client, mock_session):
        """Should block duplicate recommendation confirmations."""
        import hashlib

        import src.api.workflow as _wf_mod
        from src.api.chat import _recommendations

        rec1 = IssueRecommendation(
            session_id=mock_session.session_id,
            original_input="Same input text",
            title="T1",
            user_story="U",
            ui_ux_description="D",
            functional_requirements=["R"],
        )
        _recommendations[str(rec1.recommendation_id)] = rec1

        input_hash = hashlib.sha256(b"Same input text").hexdigest()
        _wf_mod._recent_requests[input_hash] = (datetime.utcnow(), "other_id")  # noqa: DTZ003

        with patch(
            "src.api.workflow.github_projects_service.get_project_repository",
            new_callable=AsyncMock,
            return_value=("owner", "repo"),
        ):
            response = await client.post(
                f"/api/v1/workflow/recommendations/{rec1.recommendation_id}/confirm",
                cookies={"session_id": str(mock_session.session_id)},
            )
        assert response.status_code == 422
        assert "similar request" in response.json()["error"].lower()


class TestWorkflowRepoInfoParsing:
    """Tests for _get_repository_info URL parsing."""

    @pytest.mark.asyncio
    async def test_config_with_user_project_url(self, client, mock_session):
        """Should parse owner from users/ URL."""
        project = _make_project()
        project.url = "https://github.com/users/testowner/projects/1"

        with (
            patch("src.api.workflow.get_workflow_config", return_value=None),
            patch("src.api.workflow.cache") as mock_cache,
        ):
            mock_cache.get.return_value = [project]
            response = await client.get(
                "/api/v1/workflow/config",
                cookies={"session_id": str(mock_session.session_id)},
            )
        assert response.status_code == 200
        assert response.json()["repository_owner"] == "testowner"

    @pytest.mark.asyncio
    async def test_config_with_org_project_url(self, client, mock_session):
        """Should parse owner from orgs/ URL."""
        project = _make_project()
        project.url = "https://github.com/orgs/myorg/projects/5"

        with (
            patch("src.api.workflow.get_workflow_config", return_value=None),
            patch("src.api.workflow.cache") as mock_cache,
        ):
            mock_cache.get.return_value = [project]
            response = await client.get(
                "/api/v1/workflow/config",
                cookies={"session_id": str(mock_session.session_id)},
            )
        assert response.status_code == 200
        assert response.json()["repository_owner"] == "myorg"


class TestWorkflowPollingFallbacks:
    """Tests for polling endpoint repository fallback logic."""

    @pytest.mark.asyncio
    async def test_check_issue_fallback_to_config(self, client, mock_session):
        config = WorkflowConfiguration(
            project_id=TEST_PROJECT_ID,
            repository_owner="cfg_owner",
            repository_name="cfg_repo",
        )
        with (
            patch(
                "src.api.workflow.github_projects_service.get_project_repository",
                new_callable=AsyncMock,
                return_value=None,
            ),
            patch("src.api.workflow.get_workflow_config", return_value=config),
            patch(
                "src.services.copilot_polling.check_issue_for_copilot_completion",
                new_callable=AsyncMock,
                return_value={"status": "no_pr"},
            ),
        ):
            response = await client.post(
                "/api/v1/workflow/polling/check-issue/1",
                cookies={"session_id": str(mock_session.session_id)},
            )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_check_issue_fallback_to_settings(self, client, mock_session):
        mock_settings = MagicMock(
            default_repo_owner="def_owner",
            default_repo_name="def_repo",
        )
        with (
            patch(
                "src.api.workflow.github_projects_service.get_project_repository",
                new_callable=AsyncMock,
                return_value=None,
            ),
            patch("src.api.workflow.get_workflow_config", return_value=None),
            patch("src.config.get_settings", return_value=mock_settings),
            patch(
                "src.services.copilot_polling.check_issue_for_copilot_completion",
                new_callable=AsyncMock,
                return_value={"status": "no_pr"},
            ),
        ):
            response = await client.post(
                "/api/v1/workflow/polling/check-issue/1",
                cookies={"session_id": str(mock_session.session_id)},
            )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_check_issue_no_repo_returns_422(self, client, mock_session):
        mock_settings = MagicMock(
            default_repo_owner=None,
            default_repo_name=None,
        )
        with (
            patch(
                "src.api.workflow.github_projects_service.get_project_repository",
                new_callable=AsyncMock,
                return_value=None,
            ),
            patch("src.api.workflow.get_workflow_config", return_value=None),
            patch("src.config.get_settings", return_value=mock_settings),
        ):
            response = await client.post(
                "/api/v1/workflow/polling/check-issue/1",
                cookies={"session_id": str(mock_session.session_id)},
            )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_check_all_fallback_to_config(self, client, mock_session):
        config = WorkflowConfiguration(
            project_id=TEST_PROJECT_ID,
            repository_owner="cfg_owner",
            repository_name="cfg_repo",
        )
        with (
            patch(
                "src.api.workflow.github_projects_service.get_project_repository",
                new_callable=AsyncMock,
                return_value=None,
            ),
            patch("src.api.workflow.get_workflow_config", return_value=config),
            patch(
                "src.services.copilot_polling.check_in_progress_issues",
                new_callable=AsyncMock,
                return_value=[],
            ),
        ):
            response = await client.post(
                "/api/v1/workflow/polling/check-all",
                cookies={"session_id": str(mock_session.session_id)},
            )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_check_all_broadcasts_success_results(self, client, mock_session):
        with (
            patch(
                "src.api.workflow.github_projects_service.get_project_repository",
                new_callable=AsyncMock,
                return_value=("owner", "repo"),
            ),
            patch(
                "src.services.copilot_polling.check_in_progress_issues",
                new_callable=AsyncMock,
                return_value=[
                    {
                        "status": "success",
                        "issue_number": 5,
                        "task_title": "Task",
                        "pr_number": 10,
                    }
                ],
            ),
            patch(
                "src.api.workflow.connection_manager.broadcast_to_project",
                new_callable=AsyncMock,
            ) as mock_broadcast,
        ):
            response = await client.post(
                "/api/v1/workflow/polling/check-all",
                cookies={"session_id": str(mock_session.session_id)},
            )
        assert response.status_code == 200
        mock_broadcast.assert_called_once()

    @pytest.mark.asyncio
    async def test_start_polling_success(self, client, mock_session):
        with (
            patch(
                "src.services.copilot_polling.get_polling_status",
                return_value={"is_running": False},
            ),
            patch(
                "src.api.workflow.github_projects_service.get_project_repository",
                new_callable=AsyncMock,
                return_value=("owner", "repo"),
            ),
            patch(
                "src.services.copilot_polling.poll_for_copilot_completion",
                new_callable=AsyncMock,
            ),
            patch("src.services.copilot_polling._polling_task", None),
        ):
            response = await client.post(
                "/api/v1/workflow/polling/start",
                cookies={"session_id": str(mock_session.session_id)},
            )
        assert response.status_code == 200
        assert "started" in response.json()["message"].lower()

    @pytest.mark.asyncio
    async def test_start_polling_fallback_to_config(self, client, mock_session):
        config = WorkflowConfiguration(
            project_id=TEST_PROJECT_ID,
            repository_owner="cfg_owner",
            repository_name="cfg_repo",
        )
        with (
            patch(
                "src.services.copilot_polling.get_polling_status",
                return_value={"is_running": False},
            ),
            patch(
                "src.api.workflow.github_projects_service.get_project_repository",
                new_callable=AsyncMock,
                return_value=None,
            ),
            patch("src.api.workflow.get_workflow_config", return_value=config),
            patch(
                "src.services.copilot_polling.poll_for_copilot_completion",
                new_callable=AsyncMock,
            ),
            patch("src.services.copilot_polling._polling_task", None),
        ):
            response = await client.post(
                "/api/v1/workflow/polling/start",
                cookies={"session_id": str(mock_session.session_id)},
            )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_start_polling_no_repo_returns_422(self, client, mock_session):
        mock_settings = MagicMock(
            default_repo_owner=None,
            default_repo_name=None,
        )
        with (
            patch(
                "src.services.copilot_polling.get_polling_status",
                return_value={"is_running": False},
            ),
            patch(
                "src.api.workflow.github_projects_service.get_project_repository",
                new_callable=AsyncMock,
                return_value=None,
            ),
            patch("src.api.workflow.get_workflow_config", return_value=None),
            patch("src.config.get_settings", return_value=mock_settings),
        ):
            response = await client.post(
                "/api/v1/workflow/polling/start",
                cookies={"session_id": str(mock_session.session_id)},
            )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_check_all_fallback_to_settings(self, client, mock_session):
        mock_settings = MagicMock(
            default_repo_owner="def_owner",
            default_repo_name="def_repo",
        )
        with (
            patch(
                "src.api.workflow.github_projects_service.get_project_repository",
                new_callable=AsyncMock,
                return_value=None,
            ),
            patch("src.api.workflow.get_workflow_config", return_value=None),
            patch("src.config.get_settings", return_value=mock_settings),
            patch(
                "src.services.copilot_polling.check_in_progress_issues",
                new_callable=AsyncMock,
                return_value=[],
            ),
        ):
            response = await client.post(
                "/api/v1/workflow/polling/check-all",
                cookies={"session_id": str(mock_session.session_id)},
            )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_check_all_no_repo_returns_422(self, client, mock_session):
        mock_settings = MagicMock(
            default_repo_owner=None,
            default_repo_name=None,
        )
        with (
            patch(
                "src.api.workflow.github_projects_service.get_project_repository",
                new_callable=AsyncMock,
                return_value=None,
            ),
            patch("src.api.workflow.get_workflow_config", return_value=None),
            patch("src.config.get_settings", return_value=mock_settings),
        ):
            response = await client.post(
                "/api/v1/workflow/polling/check-all",
                cookies={"session_id": str(mock_session.session_id)},
            )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_start_polling_fallback_to_settings(self, client, mock_session):
        mock_settings = MagicMock(
            default_repo_owner="def_owner",
            default_repo_name="def_repo",
        )
        with (
            patch(
                "src.services.copilot_polling.get_polling_status",
                return_value={"is_running": False},
            ),
            patch(
                "src.api.workflow.github_projects_service.get_project_repository",
                new_callable=AsyncMock,
                return_value=None,
            ),
            patch("src.api.workflow.get_workflow_config", return_value=None),
            patch("src.config.get_settings", return_value=mock_settings),
            patch(
                "src.services.copilot_polling.poll_for_copilot_completion",
                new_callable=AsyncMock,
            ),
            patch("src.services.copilot_polling._polling_task", None),
        ):
            response = await client.post(
                "/api/v1/workflow/polling/start",
                cookies={"session_id": str(mock_session.session_id)},
            )
        assert response.status_code == 200


class TestWorkflowConfirmRepoFallbackToUrl:
    """Test confirm_recommendation falling back to URL parsing."""

    @pytest.mark.asyncio
    async def test_confirm_no_repo_raises_validation_error(self, client, mock_session):
        from src.api.chat import _recommendations

        rec = IssueRecommendation(
            session_id=mock_session.session_id,
            original_input="X",
            title="T",
            user_story="U",
            ui_ux_description="D",
            functional_requirements=["R"],
        )
        _recommendations[str(rec.recommendation_id)] = rec

        mock_settings = MagicMock(
            default_repo_owner=None,
            default_repo_name=None,
            default_assignee="",
        )

        with (
            patch(
                "src.api.workflow.github_projects_service.get_project_repository",
                new_callable=AsyncMock,
                return_value=None,
            ),
            patch("src.api.workflow.get_workflow_config", return_value=None),
            patch("src.config.get_settings", return_value=mock_settings),
            patch("src.api.workflow.cache") as mock_cache,
        ):
            mock_cache.get.return_value = None
            response = await client.post(
                f"/api/v1/workflow/recommendations/{rec.recommendation_id}/confirm",
                cookies={"session_id": str(mock_session.session_id)},
            )
        assert response.status_code == 422


class TestAuthLogoutWithSession:
    """Test logout with valid session cookie."""

    @pytest.mark.asyncio
    async def test_logout_with_session_revokes(self, client):
        with patch("src.api.auth.github_auth_service.revoke_session") as mock_revoke:
            response = await client.post(
                "/api/v1/auth/logout",
                cookies={"session_id": "some_session_id"},
            )
        assert response.status_code == 200
        mock_revoke.assert_called_once_with("some_session_id")


class TestSelectProjectWithPolling:
    """Tests for POST /projects/{project_id}/select with polling."""

    @pytest.mark.asyncio
    async def test_select_starts_polling_with_repo(self, client, mock_session):
        """Should start polling when repo info is available."""
        project = _make_project()
        with (
            patch("src.api.projects.cache") as mock_cache,
            patch("src.api.projects.github_auth_service.update_session"),
            patch(
                "src.api.projects.github_projects_service.get_project_repository",
                new_callable=AsyncMock,
                return_value=("owner", "repo"),
            ),
            patch(
                "src.services.copilot_polling.get_polling_status",
                return_value={"is_running": False},
            ),
            patch(
                "src.services.copilot_polling.poll_for_copilot_completion",
                new_callable=AsyncMock,
            ),
            patch("src.services.copilot_polling._polling_task", None),
        ):
            mock_cache.get.return_value = [project]
            response = await client.post(
                f"/api/v1/projects/{TEST_PROJECT_ID}/select",
                cookies={"session_id": str(mock_session.session_id)},
            )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_select_stops_existing_polling(self, client, mock_session):
        """Should stop existing polling before starting new one."""
        project = _make_project()
        with (
            patch("src.api.projects.cache") as mock_cache,
            patch("src.api.projects.github_auth_service.update_session"),
            patch(
                "src.api.projects.github_projects_service.get_project_repository",
                new_callable=AsyncMock,
                return_value=("owner", "repo"),
            ),
            patch(
                "src.services.copilot_polling.get_polling_status",
                return_value={"is_running": True},
            ),
            patch("src.services.copilot_polling.stop_polling"),
            patch(
                "src.services.copilot_polling.poll_for_copilot_completion",
                new_callable=AsyncMock,
            ),
            patch("src.services.copilot_polling._polling_task", None),
        ):
            mock_cache.get.return_value = [project]
            response = await client.post(
                f"/api/v1/projects/{TEST_PROJECT_ID}/select",
                cookies={"session_id": str(mock_session.session_id)},
            )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_select_polling_fallback_to_config(self, client, mock_session):
        """Should fall back to workflow config for repo info."""
        project = _make_project()
        config = WorkflowConfiguration(
            project_id=TEST_PROJECT_ID,
            repository_owner="cfg_owner",
            repository_name="cfg_repo",
        )
        with (
            patch("src.api.projects.cache") as mock_cache,
            patch("src.api.projects.github_auth_service.update_session"),
            patch(
                "src.api.projects.github_projects_service.get_project_repository",
                new_callable=AsyncMock,
                return_value=None,
            ),
            patch(
                "src.services.copilot_polling.get_polling_status",
                return_value={"is_running": False},
            ),
            patch(
                "src.api.workflow.get_workflow_config",
                return_value=config,
            ),
            patch(
                "src.services.copilot_polling.poll_for_copilot_completion",
                new_callable=AsyncMock,
            ),
            patch("src.services.copilot_polling._polling_task", None),
        ):
            mock_cache.get.return_value = [project]
            response = await client.post(
                f"/api/v1/projects/{TEST_PROJECT_ID}/select",
                cookies={"session_id": str(mock_session.session_id)},
            )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_select_polling_fallback_to_settings(self, client, mock_session):
        """Should fall back to default settings for repo info."""
        project = _make_project()
        mock_settings = MagicMock(
            default_repo_owner="def_owner",
            default_repo_name="def_repo",
        )
        with (
            patch("src.api.projects.cache") as mock_cache,
            patch("src.api.projects.github_auth_service.update_session"),
            patch(
                "src.api.projects.github_projects_service.get_project_repository",
                new_callable=AsyncMock,
                return_value=None,
            ),
            patch(
                "src.services.copilot_polling.get_polling_status",
                return_value={"is_running": False},
            ),
            patch(
                "src.api.workflow.get_workflow_config",
                return_value=None,
            ),
            patch("src.config.get_settings", return_value=mock_settings),
            patch(
                "src.services.copilot_polling.poll_for_copilot_completion",
                new_callable=AsyncMock,
            ),
            patch("src.services.copilot_polling._polling_task", None),
        ):
            mock_cache.get.return_value = [project]
            response = await client.post(
                f"/api/v1/projects/{TEST_PROJECT_ID}/select",
                cookies={"session_id": str(mock_session.session_id)},
            )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_select_polling_no_repo_skips_polling(self, client, mock_session):
        """Should skip polling when no repo found."""
        project = _make_project()
        mock_settings = MagicMock(
            default_repo_owner=None,
            default_repo_name=None,
        )
        with (
            patch("src.api.projects.cache") as mock_cache,
            patch("src.api.projects.github_auth_service.update_session"),
            patch(
                "src.api.projects.github_projects_service.get_project_repository",
                new_callable=AsyncMock,
                return_value=None,
            ),
            patch(
                "src.services.copilot_polling.get_polling_status",
                return_value={"is_running": False},
            ),
            patch(
                "src.api.workflow.get_workflow_config",
                return_value=None,
            ),
            patch("src.config.get_settings", return_value=mock_settings),
        ):
            mock_cache.get.return_value = [project]
            response = await client.post(
                f"/api/v1/projects/{TEST_PROJECT_ID}/select",
                cookies={"session_id": str(mock_session.session_id)},
            )
        assert response.status_code == 200
