"""Tests for ChatAgentService (src/services/chat_agent.py).

Mocks the ``Agent`` returned by ``create_agent`` and verifies:
- Session mapping
- Response conversion (text → ChatMessage with action_type/action_data)
- Error handling (graceful fallback on agent failure)
"""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID

import pytest

from src.models.chat import ActionType, SenderType
from src.services.chat_agent import ChatAgentService, reset_chat_agent_service


@pytest.fixture(autouse=True)
def _reset_singleton():
    """Reset the singleton before each test."""
    reset_chat_agent_service()
    yield
    reset_chat_agent_service()


def _make_agent_response(text: str):
    """Create a mock AgentResponse with the given text."""
    response = MagicMock()
    response.text = text
    response.messages = []
    return response


def _make_agent_response_with_messages(texts: list[str]):
    """Create a mock AgentResponse with multiple messages."""
    response = MagicMock()
    response.text = None
    messages = []
    for t in texts:
        msg = MagicMock()
        msg.text = t
        messages.append(msg)
    response.messages = messages
    return response


class TestChatAgentServiceRun:
    @patch("src.services.chat_agent.create_agent")
    async def test_run_returns_chat_message(self, mock_create_agent):
        mock_agent = MagicMock()
        mock_agent.create_session.return_value = MagicMock(session_id="00000000-0000-0000-0000-000000000001")
        mock_agent.run = AsyncMock(
            return_value=_make_agent_response("Hello! How can I help?")
        )
        mock_create_agent.return_value = mock_agent

        service = ChatAgentService()
        result = await service.run(
            user_message="Hi",
            session_id="00000000-0000-0000-0000-000000000001",
            project_name="Test Project",
            project_id="PVT_1",
        )

        assert result.sender_type == SenderType.ASSISTANT
        assert "Hello" in result.content
        assert result.action_type is None
        assert result.action_data is None

    @patch("src.services.chat_agent.create_agent")
    async def test_run_extracts_task_create_action(self, mock_create_agent):
        mock_agent = MagicMock()
        mock_agent.create_session.return_value = MagicMock(session_id="00000000-0000-0000-0000-000000000001")
        # Simulate agent returning text with embedded JSON action
        mock_agent.run = AsyncMock(
            return_value=_make_agent_response(
                'Here is your task proposal:\n'
                '```json\n'
                '{"action_type": "task_create", "proposed_title": "Fix bug", '
                '"proposed_description": "Fix the login flow"}\n'
                '```'
            )
        )
        mock_create_agent.return_value = mock_agent

        service = ChatAgentService()
        result = await service.run(
            user_message="Create a task for fixing the login bug",
            session_id="00000000-0000-0000-0000-000000000001",
        )

        assert result.action_type == ActionType.TASK_CREATE
        assert result.action_data is not None
        assert result.action_data["proposed_title"] == "Fix bug"

    @patch("src.services.chat_agent.create_agent")
    async def test_run_extracts_issue_create_action(self, mock_create_agent):
        mock_agent = MagicMock()
        mock_agent.create_session.return_value = MagicMock(session_id="00000000-0000-0000-0000-000000000001")
        mock_agent.run = AsyncMock(
            return_value=_make_agent_response(
                'I recommend creating this issue:\n'
                '{"action_type": "issue_create", "title": "Add dark mode"}'
            )
        )
        mock_create_agent.return_value = mock_agent

        service = ChatAgentService()
        result = await service.run(
            user_message="I want dark mode",
            session_id="00000000-0000-0000-0000-000000000001",
        )

        assert result.action_type == ActionType.ISSUE_CREATE
        assert result.action_data["title"] == "Add dark mode"

    @patch("src.services.chat_agent.create_agent")
    async def test_run_extracts_status_update_action(self, mock_create_agent):
        mock_agent = MagicMock()
        mock_agent.create_session.return_value = MagicMock(session_id="00000000-0000-0000-0000-000000000001")
        mock_agent.run = AsyncMock(
            return_value=_make_agent_response(
                '{"action_type": "status_update", "task_reference": "Fix login", "target_status": "Done"}'
            )
        )
        mock_create_agent.return_value = mock_agent

        service = ChatAgentService()
        result = await service.run(
            user_message="Move fix login to done",
            session_id="00000000-0000-0000-0000-000000000001",
        )

        assert result.action_type == ActionType.STATUS_UPDATE
        assert result.action_data["task_reference"] == "Fix login"

    @patch("src.services.chat_agent.create_agent")
    async def test_run_handles_agent_error(self, mock_create_agent):
        mock_agent = MagicMock()
        mock_agent.create_session.return_value = MagicMock(session_id="00000000-0000-0000-0000-000000000001")
        mock_agent.run = AsyncMock(side_effect=RuntimeError("API error"))
        mock_create_agent.return_value = mock_agent

        service = ChatAgentService()
        result = await service.run(
            user_message="Hello",
            session_id="00000000-0000-0000-0000-000000000001",
        )

        assert result.sender_type == SenderType.ASSISTANT
        assert "error" in result.content.lower()
        assert result.action_type is None

    @patch("src.services.chat_agent.create_agent")
    async def test_run_with_messages_fallback(self, mock_create_agent):
        mock_agent = MagicMock()
        mock_agent.create_session.return_value = MagicMock(session_id="00000000-0000-0000-0000-000000000001")
        mock_agent.run = AsyncMock(
            return_value=_make_agent_response_with_messages(["Part 1", "Part 2"])
        )
        mock_create_agent.return_value = mock_agent

        service = ChatAgentService()
        result = await service.run(
            user_message="Hello",
            session_id="00000000-0000-0000-0000-000000000001",
        )

        assert "Part 1" in result.content
        assert "Part 2" in result.content


class TestChatAgentServiceSession:
    @patch("src.services.chat_agent.create_agent")
    async def test_reuses_session_for_same_id(self, mock_create_agent):
        mock_agent = MagicMock()
        mock_session = MagicMock(session_id="00000000-0000-0000-0000-000000000001")
        mock_agent.create_session.return_value = mock_session
        mock_agent.run = AsyncMock(
            return_value=_make_agent_response("OK")
        )
        mock_create_agent.return_value = mock_agent

        service = ChatAgentService()
        await service.run(user_message="msg1", session_id="00000000-0000-0000-0000-000000000001")
        await service.run(user_message="msg2", session_id="00000000-0000-0000-0000-000000000001")

        # create_session should only be called once for the same session_id
        assert mock_agent.create_session.call_count == 1

    @patch("src.services.chat_agent.create_agent")
    async def test_creates_different_sessions_for_different_ids(self, mock_create_agent):
        mock_agent = MagicMock()
        mock_agent.create_session.return_value = MagicMock()
        mock_agent.run = AsyncMock(
            return_value=_make_agent_response("OK")
        )
        mock_create_agent.return_value = mock_agent

        service = ChatAgentService()
        await service.run(user_message="msg1", session_id="00000000-0000-0000-0000-00000000000a")
        await service.run(user_message="msg2", session_id="00000000-0000-0000-0000-00000000000b")

        assert mock_agent.create_session.call_count == 2


class TestChatAgentServiceConvertResponse:
    def test_plain_text_response(self):
        service = ChatAgentService()
        response = _make_agent_response("Just a plain message")
        result = service._convert_response(response, "00000000-0000-0000-0000-000000000001")

        assert result.content == "Just a plain message"
        assert result.action_type is None

    def test_empty_response_gets_default_text(self):
        service = ChatAgentService()
        response = _make_agent_response("")
        result = service._convert_response(response, "00000000-0000-0000-0000-000000000001")

        assert result.content == "I've processed your request."

    def test_json_action_extracted(self):
        service = ChatAgentService()
        response = _make_agent_response(
            'Here is the result: {"action_type": "task_create", "proposed_title": "Test"}'
        )
        result = service._convert_response(response, "00000000-0000-0000-0000-000000000001")

        assert result.action_type == ActionType.TASK_CREATE
        assert result.action_data["proposed_title"] == "Test"

    def test_no_action_for_non_action_json(self):
        service = ChatAgentService()
        response = _make_agent_response('{"key": "value"}')
        result = service._convert_response(response, "00000000-0000-0000-0000-000000000001")

        assert result.action_type is None
        assert result.action_data is None


class TestChatAgentServiceSingleton:
    def test_reset_clears_singleton(self):
        from src.services.chat_agent import get_chat_agent_service, reset_chat_agent_service

        svc1 = get_chat_agent_service()
        reset_chat_agent_service()
        svc2 = get_chat_agent_service()
        assert svc1 is not svc2
