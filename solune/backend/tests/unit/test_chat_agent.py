"""Tests for ChatAgentService (src/services/chat_agent.py).

Mock Agent.run() to verify session mapping, response conversion,
runtime context injection, and error handling.

v0.2.0 — Intelligent Chat Agent (Microsoft Agent Framework)
"""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from src.models.chat import ActionType, SenderType
from src.services.agent_tools import RuntimeContext
from src.services.chat_agent import (
    AgentResponse,
    ChatAgentService,
    get_chat_agent_service,
    reset_chat_agent_service,
)

# Fixed UUIDs for deterministic tests
_SESSION_UUID = uuid4()
_SESSION_STR = str(_SESSION_UUID)
_SESSION_UUID_2 = uuid4()
_SESSION_STR_2 = str(_SESSION_UUID_2)


# ── Test fixtures ────────────────────────────────────────────────────────


def _make_provider(name: str = "mock") -> MagicMock:
    """Create a mock AgentProvider."""
    provider = MagicMock()
    provider.name = name
    provider.agent = AsyncMock()
    return provider


def _make_context(**overrides) -> RuntimeContext:
    defaults = {
        "project_id": "PVT_test",
        "session_id": _SESSION_STR,
        "github_token": "ghp_test",
        "project_name": "Test Project",
    }
    defaults.update(overrides)
    return RuntimeContext(**defaults)


# ── ChatAgentService initialization ──────────────────────────────────────


class TestChatAgentServiceInit:
    def test_init_stores_provider(self):
        provider = _make_provider()
        service = ChatAgentService(provider)
        assert service.provider_name == "mock"

    def test_init_empty_sessions(self):
        provider = _make_provider()
        service = ChatAgentService(provider)
        assert service._sessions == {}


# ── Session management ───────────────────────────────────────────────────


class TestSessionManagement:
    def test_get_or_create_new_session(self):
        service = ChatAgentService(_make_provider())
        session = service._get_or_create_session("sess-1")

        assert session["id"] == "sess-1"
        assert session["messages"] == []

    def test_get_existing_session(self):
        service = ChatAgentService(_make_provider())
        first = service._get_or_create_session("sess-1")
        first["messages"].append({"role": "user", "content": "hi"})

        second = service._get_or_create_session("sess-1")
        assert second is first
        assert len(second["messages"]) == 1

    def test_different_sessions_are_isolated(self):
        service = ChatAgentService(_make_provider())
        s1 = service._get_or_create_session("sess-1")
        s2 = service._get_or_create_session("sess-2")

        s1["messages"].append({"role": "user", "content": "hello"})
        assert len(s2["messages"]) == 0

    def test_clear_session(self):
        service = ChatAgentService(_make_provider())
        service._get_or_create_session("sess-1")
        service.clear_session("sess-1")
        assert "sess-1" not in service._sessions

    def test_clear_nonexistent_session(self):
        """Clearing a session that doesn't exist should not raise."""
        service = ChatAgentService(_make_provider())
        service.clear_session("nonexistent")  # no error


# ── run() — happy paths ─────────────────────────────────────────────────


class TestChatAgentServiceRun:
    async def test_run_returns_chat_message(self):
        provider = _make_provider()
        provider.agent.run = AsyncMock(return_value="Hello! How can I help?")
        service = ChatAgentService(provider)

        result = await service.run("hi", _SESSION_STR, _make_context())

        assert result.sender_type == SenderType.ASSISTANT
        assert result.content == "Hello! How can I help?"
        assert result.action_type is None

    async def test_run_with_uuid_session_id(self):
        provider = _make_provider()
        provider.agent.run = AsyncMock(return_value="response")
        service = ChatAgentService(provider)

        session_uuid = uuid4()
        result = await service.run("msg", session_uuid, _make_context())

        assert result.session_id == session_uuid

    async def test_run_with_string_session_id(self):
        provider = _make_provider()
        provider.agent.run = AsyncMock(return_value="response")
        service = ChatAgentService(provider)

        sid = str(uuid4())
        result = await service.run("msg", sid, _make_context())

        assert str(result.session_id) == sid

    async def test_run_records_messages_in_session(self):
        provider = _make_provider()
        provider.agent.run = AsyncMock(return_value="Got it")
        service = ChatAgentService(provider)

        await service.run("hello", _SESSION_STR, _make_context())

        session = service._sessions[_SESSION_STR]
        assert len(session["messages"]) == 2
        assert session["messages"][0] == {"role": "user", "content": "hello"}
        assert session["messages"][1] == {"role": "assistant", "content": "Got it"}


# ── run() — response conversion ─────────────────────────────────────────


class TestResponseConversion:
    async def test_dict_response_with_task_action(self):
        provider = _make_provider()
        provider.agent.run = AsyncMock(
            return_value={
                "content": "Created a task proposal",
                "action": "task_create",
                "action_data": {"title": "Fix bug", "description": "Fix the login bug"},
            }
        )
        service = ChatAgentService(provider)

        result = await service.run("create task", _SESSION_STR, _make_context())

        assert result.action_type == ActionType.TASK_CREATE
        assert result.action_data == {"title": "Fix bug", "description": "Fix the login bug"}

    async def test_dict_response_with_status_action(self):
        provider = _make_provider()
        provider.agent.run = AsyncMock(
            return_value={
                "content": "Updated status",
                "action": "status_update",
                "action_data": {"task": "bug fix", "status": "Done"},
            }
        )
        service = ChatAgentService(provider)

        result = await service.run("move to done", _SESSION_STR, _make_context())
        assert result.action_type == ActionType.STATUS_UPDATE

    async def test_dict_response_with_issue_action(self):
        provider = _make_provider()
        provider.agent.run = AsyncMock(
            return_value={
                "content": "Created issue recommendation",
                "action": "issue_create",
                "action_data": {"title": "Dark mode"},
            }
        )
        service = ChatAgentService(provider)

        result = await service.run("add dark mode", _SESSION_STR, _make_context())
        assert result.action_type == ActionType.ISSUE_CREATE

    async def test_dict_response_without_action(self):
        provider = _make_provider()
        provider.agent.run = AsyncMock(return_value={"content": "Just a message", "action": None})
        service = ChatAgentService(provider)

        result = await service.run("hello", _SESSION_STR, _make_context())
        assert result.action_type is None
        assert result.content == "Just a message"

    async def test_object_response_with_messages(self):
        """Agent framework response with .messages attribute."""
        msg = SimpleNamespace(content="Agent says hi")
        response = SimpleNamespace(messages=[msg])

        provider = _make_provider()
        provider.agent.run = AsyncMock(return_value=response)
        service = ChatAgentService(provider)

        result = await service.run("hello", _SESSION_STR, _make_context())
        assert result.content == "Agent says hi"

    async def test_fallback_to_str_conversion(self):
        provider = _make_provider()
        provider.agent.run = AsyncMock(return_value=42)
        service = ChatAgentService(provider)

        result = await service.run("hello", _SESSION_STR, _make_context())
        assert result.content == "42"


# ── run() — error handling ───────────────────────────────────────────────


class TestChatAgentServiceErrors:
    async def test_agent_error_returns_error_message(self):
        provider = _make_provider()
        provider.agent.run = AsyncMock(side_effect=RuntimeError("LLM timeout"))
        service = ChatAgentService(provider)

        result = await service.run("hello", _SESSION_STR, _make_context())

        assert result.sender_type == SenderType.ASSISTANT
        assert "error" in result.content.lower()
        assert "LLM timeout" in result.content

    async def test_agent_error_preserves_session_id(self):
        provider = _make_provider()
        provider.agent.run = AsyncMock(side_effect=ValueError("bad request"))
        service = ChatAgentService(provider)

        sid = uuid4()
        result = await service.run("msg", sid, _make_context())
        assert result.session_id == sid


# ── run_stream() ─────────────────────────────────────────────────────────


class TestChatAgentServiceStream:
    async def test_stream_yields_tokens(self):
        provider = _make_provider()

        async def mock_stream(message, session_id):
            for token in ["Hello", " ", "world"]:
                yield token

        provider.agent.run_stream = mock_stream
        service = ChatAgentService(provider)

        tokens = [token async for token in service.run_stream("hi", _SESSION_STR, _make_context())]

        assert tokens == ["Hello", " ", "world"]

    async def test_stream_records_user_message(self):
        provider = _make_provider()

        async def mock_stream(message, session_id):
            yield "response"

        provider.agent.run_stream = mock_stream
        service = ChatAgentService(provider)

        async for _ in service.run_stream("hello", _SESSION_STR, _make_context()):
            pass

        session = service._sessions[_SESSION_STR]
        assert session["messages"][0] == {"role": "user", "content": "hello"}

    async def test_stream_error_yields_error_message(self):
        provider = _make_provider()

        async def mock_stream(message, session_id):
            raise RuntimeError("stream failed")
            yield  # make it a generator

        provider.agent.run_stream = mock_stream
        service = ChatAgentService(provider)

        tokens = [token async for token in service.run_stream("hi", _SESSION_STR, _make_context())]

        assert any("Error" in t for t in tokens)


# ── Multi-turn memory ────────────────────────────────────────────────────


class TestMultiTurnMemory:
    async def test_messages_accumulate_across_runs(self):
        provider = _make_provider()
        provider.agent.run = AsyncMock(side_effect=["First", "Second"])
        service = ChatAgentService(provider)
        ctx = _make_context()

        await service.run("msg1", _SESSION_STR, ctx)
        await service.run("msg2", _SESSION_STR, ctx)

        session = service._sessions[_SESSION_STR]
        assert len(session["messages"]) == 4  # 2 user + 2 assistant

    async def test_different_sessions_independent(self):
        provider = _make_provider()
        provider.agent.run = AsyncMock(return_value="response")
        service = ChatAgentService(provider)

        await service.run("msg", _SESSION_STR, _make_context())
        await service.run("msg", _SESSION_STR_2, _make_context())

        assert len(service._sessions[_SESSION_STR]["messages"]) == 2
        assert len(service._sessions[_SESSION_STR_2]["messages"]) == 2


# ── AgentResponse dataclass ──────────────────────────────────────────────


class TestAgentResponse:
    def test_default_values(self):
        resp = AgentResponse()
        assert resp.content == ""
        assert resp.tool_calls == []
        assert resp.action_type is None
        assert resp.action_data is None

    def test_with_action(self):
        resp = AgentResponse(
            content="Created",
            action_type=ActionType.TASK_CREATE,
            action_data={"title": "Test"},
        )
        assert resp.action_type == ActionType.TASK_CREATE


# ── Singleton management ─────────────────────────────────────────────────


class TestSingleton:
    def test_reset_clears_instance(self):
        reset_chat_agent_service()
        # After reset, next call should try to create (and may fail
        # if agent-framework is not installed, which is expected)
        reset_chat_agent_service()  # double reset is safe

    def test_get_raises_when_agent_framework_missing(self):
        """get_chat_agent_service raises ValueError when packages aren't installed."""
        reset_chat_agent_service()
        with patch(
            "src.services.agent_provider.create_agent_provider",
            side_effect=ValueError("not installed"),
        ):
            with pytest.raises(ValueError, match="not installed"):
                get_chat_agent_service()
