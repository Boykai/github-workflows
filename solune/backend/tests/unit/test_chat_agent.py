"""Unit tests for ChatAgentService (src/services/chat_agent.py).

Covers:
- Initialization with default and custom providers
- Session management (create, get, clear, count)
- run() — happy path, error handling, response conversion
- run_stream() — basic streaming
- _result_to_chat_message — action_type mapping
- get_chat_agent_service / reset_chat_agent_service singleton lifecycle
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID

from src.models.chat import ActionType, SenderType
from src.services.agent_provider import AgentProvider
from src.services.chat_agent import (
    ChatAgentService,
    get_chat_agent_service,
    reset_chat_agent_service,
)

# ── Helpers ────────────────────────────────────────────────────────────────

SESSION_ID = "550e8400-e29b-41d4-a716-446655440000"
PROJECT_ID = "PVT_test"


def _mock_provider(*, run_result: dict | None = None, run_error: Exception | None = None):
    """Create a mock AgentProvider with configurable run() behaviour."""
    provider = MagicMock(spec=AgentProvider)
    provider.provider_name = "mock"

    if run_error:
        provider.run = AsyncMock(side_effect=run_error)
    else:
        provider.run = AsyncMock(
            return_value=run_result
            or {
                "content": "Hello from the agent",
                "action_type": None,
                "action_data": None,
            }
        )

    async def _stream(*args, **kwargs):
        yield {"delta": "chunk1", "done": False}
        yield {"delta": "chunk2", "done": True}

    provider.run_stream = _stream
    return provider


# ── Initialization ─────────────────────────────────────────────────────────


class TestChatAgentServiceInit:
    def test_init_with_custom_provider(self):
        provider = _mock_provider()
        service = ChatAgentService(provider=provider)
        assert service._provider is provider

    @patch("src.services.chat_agent.create_agent_provider")
    def test_init_default_provider(self, mock_factory):
        mock_factory.return_value = _mock_provider()
        service = ChatAgentService()
        mock_factory.assert_called_once()
        assert service._provider is mock_factory.return_value


# ── Session management ─────────────────────────────────────────────────────


class TestSessionManagement:
    def test_get_or_create_new_session(self):
        service = ChatAgentService(provider=_mock_provider())
        session = service.get_or_create_session(SESSION_ID)
        assert session["session_id"] == SESSION_ID
        assert session["history"] == []
        assert "created_at" in session

    def test_get_existing_session(self):
        service = ChatAgentService(provider=_mock_provider())
        s1 = service.get_or_create_session(SESSION_ID)
        s1["history"].append({"role": "user", "content": "hi"})
        s2 = service.get_or_create_session(SESSION_ID)
        assert s2 is s1
        assert len(s2["history"]) == 1

    def test_clear_session(self):
        service = ChatAgentService(provider=_mock_provider())
        service.get_or_create_session(SESSION_ID)
        assert service.active_sessions == 1
        service.clear_session(SESSION_ID)
        assert service.active_sessions == 0

    def test_clear_nonexistent_session(self):
        service = ChatAgentService(provider=_mock_provider())
        # Should not raise
        service.clear_session("nonexistent")

    def test_active_sessions_count(self):
        service = ChatAgentService(provider=_mock_provider())
        service.get_or_create_session("s1")
        service.get_or_create_session("s2")
        service.get_or_create_session("s3")
        assert service.active_sessions == 3


# ── run() ──────────────────────────────────────────────────────────────────


class TestRun:
    async def test_happy_path(self):
        provider = _mock_provider(
            run_result={
                "content": "I've created a task for you.",
                "action_type": "task_create",
                "action_data": {"title": "Fix bug"},
            }
        )
        service = ChatAgentService(provider=provider)

        msg = await service.run(
            message="Fix the login bug",
            session_id=SESSION_ID,
            project_id=PROJECT_ID,
            project_name="Test Project",
            github_token="ghp_fake",
        )

        assert msg.sender_type == SenderType.ASSISTANT
        assert msg.content == "I've created a task for you."
        assert msg.action_type == ActionType.TASK_CREATE
        assert msg.action_data == {"title": "Fix bug"}
        assert msg.session_id == UUID(SESSION_ID)

    async def test_records_user_message_in_session_history(self):
        provider = _mock_provider()
        service = ChatAgentService(provider=provider)

        await service.run(
            message="Hello agent",
            session_id=SESSION_ID,
            project_id=PROJECT_ID,
        )

        session = service.get_or_create_session(SESSION_ID)
        assert len(session["history"]) == 1
        assert session["history"][0]["content"] == "Hello agent"

    async def test_provider_called_with_message(self):
        provider = _mock_provider()
        service = ChatAgentService(provider=provider)

        await service.run(
            message="Add dark mode",
            session_id=SESSION_ID,
            project_id=PROJECT_ID,
        )

        provider.run.assert_called_once_with("Add dark mode", session_id=SESSION_ID)

    async def test_error_returns_friendly_message(self):
        provider = _mock_provider(run_error=RuntimeError("connection refused"))
        service = ChatAgentService(provider=provider)

        msg = await service.run(
            message="do something",
            session_id=SESSION_ID,
            project_id=PROJECT_ID,
        )

        assert msg.sender_type == SenderType.ASSISTANT
        assert "error" in msg.content.lower()
        # Should not leak internal error details
        assert "connection refused" not in msg.content

    async def test_no_action_type(self):
        provider = _mock_provider(
            run_result={"content": "Just a message", "action_type": None, "action_data": None}
        )
        service = ChatAgentService(provider=provider)

        msg = await service.run(
            message="hello",
            session_id=SESSION_ID,
            project_id=PROJECT_ID,
        )

        assert msg.action_type is None
        assert msg.action_data is None


# ── run_stream() ───────────────────────────────────────────────────────────


class TestRunStream:
    async def test_yields_chunks(self):
        provider = _mock_provider()
        service = ChatAgentService(provider=provider)

        chunks = [
            chunk
            async for chunk in service.run_stream(
                message="stream test",
                session_id=SESSION_ID,
                project_id=PROJECT_ID,
            )
        ]

        assert len(chunks) == 2
        assert chunks[0]["delta"] == "chunk1"
        assert chunks[1]["done"] is True

    async def test_records_message_in_history(self):
        provider = _mock_provider()
        service = ChatAgentService(provider=provider)

        async for _ in service.run_stream(
            message="stream msg",
            session_id=SESSION_ID,
            project_id=PROJECT_ID,
        ):
            pass

        session = service.get_or_create_session(SESSION_ID)
        assert session["history"][-1]["content"] == "stream msg"


# ── _result_to_chat_message ───────────────────────────────────────────────


class TestResultToChatMessage:
    def test_task_create_action(self):
        result = {
            "content": "Task drafted",
            "action_type": "task_create",
            "action_data": {"title": "Fix bug"},
        }
        msg = ChatAgentService._result_to_chat_message(result, SESSION_ID)
        assert msg.action_type == ActionType.TASK_CREATE
        assert msg.action_data == {"title": "Fix bug"}

    def test_issue_create_action(self):
        result = {"content": "Issue drafted", "action_type": "issue_create", "action_data": None}
        msg = ChatAgentService._result_to_chat_message(result, SESSION_ID)
        assert msg.action_type == ActionType.ISSUE_CREATE

    def test_status_update_action(self):
        result = {"content": "Updated", "action_type": "status_update", "action_data": None}
        msg = ChatAgentService._result_to_chat_message(result, SESSION_ID)
        assert msg.action_type == ActionType.STATUS_UPDATE

    def test_unknown_action_type_becomes_none(self):
        result = {"content": "Hmm", "action_type": "unknown_action", "action_data": None}
        msg = ChatAgentService._result_to_chat_message(result, SESSION_ID)
        assert msg.action_type is None

    def test_none_action_type(self):
        result = {"content": "Just text", "action_type": None, "action_data": None}
        msg = ChatAgentService._result_to_chat_message(result, SESSION_ID)
        assert msg.action_type is None

    def test_message_fallback_for_content(self):
        """If 'content' is missing, fall back to 'message' key."""
        result = {"message": "From message key", "action_type": None, "action_data": None}
        msg = ChatAgentService._result_to_chat_message(result, SESSION_ID)
        assert msg.content == "From message key"

    def test_empty_result(self):
        msg = ChatAgentService._result_to_chat_message({}, SESSION_ID)
        assert msg.content == ""
        assert msg.action_type is None


# ── Singleton lifecycle ────────────────────────────────────────────────────


class TestSingleton:
    def setup_method(self):
        reset_chat_agent_service()

    def teardown_method(self):
        reset_chat_agent_service()

    @patch("src.services.chat_agent.create_agent_provider")
    def test_get_creates_singleton(self, mock_factory):
        mock_factory.return_value = _mock_provider()
        s1 = get_chat_agent_service()
        s2 = get_chat_agent_service()
        assert s1 is s2
        mock_factory.assert_called_once()

    @patch("src.services.chat_agent.create_agent_provider")
    def test_reset_clears_singleton(self, mock_factory):
        mock_factory.return_value = _mock_provider()
        s1 = get_chat_agent_service()
        reset_chat_agent_service()
        s2 = get_chat_agent_service()
        assert s1 is not s2
