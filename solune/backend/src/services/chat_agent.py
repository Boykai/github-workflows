"""Chat Agent Service — orchestrates the Agent Framework for chat interactions.

Holds a singleton ``Agent`` instance, manages ``AgentSession`` ↔ Solune
``session_id`` mapping, and converts ``AgentResponse`` messages into the
existing ``ChatMessage`` format so the REST API contract stays unchanged.

Usage::

    service = get_chat_agent_service()
    message = await service.run(
        user_message="Create a task for fixing login",
        session_id="abc-123",
        project_name="My Project",
        project_id="PVT_1",
        github_token="gho_...",
    )
"""

from __future__ import annotations

import asyncio
import json
import re
from collections.abc import AsyncIterator
from typing import Any
from uuid import UUID, uuid4

from agent_framework import Agent, AgentSession

from src.logging_utils import get_logger
from src.models.chat import ActionType, ChatMessage, SenderType
from src.prompts.agent_instructions import build_agent_instructions
from src.services.agent_middleware import LoggingAgentMiddleware, SecurityMiddleware
from src.services.agent_provider import create_agent
from src.services.agent_tools import ALL_TOOLS, set_runtime_context

logger = get_logger(__name__)


class ChatAgentService:
    """High-level service bridging the Agent Framework and Solune's chat API.

    Thread-safety: session map is protected by an ``asyncio.Lock``.
    """

    def __init__(self) -> None:
        self._agent: Agent | None = None
        self._sessions: dict[str, AgentSession] = {}
        self._lock = asyncio.Lock()

    # ── Lazy agent init ────────────────────────────────────────────────

    def _ensure_agent(
        self, project_name: str | None = None, project_id: str | None = None
    ) -> Agent:
        """Lazily create the agent on first use."""
        if self._agent is None:
            instructions = build_agent_instructions(
                project_name=project_name,
                project_id=project_id,
            )
            middleware = [LoggingAgentMiddleware(), SecurityMiddleware()]
            self._agent = create_agent(
                instructions=instructions,
                tools=ALL_TOOLS,
                middleware=middleware,
            )
        return self._agent

    # ── Session management ─────────────────────────────────────────────

    async def _get_or_create_session(self, session_id: str, agent: Agent) -> AgentSession:
        """Map a Solune session_id to an AgentSession."""
        async with self._lock:
            if session_id not in self._sessions:
                self._sessions[session_id] = agent.create_session(session_id=session_id)
                logger.debug("Created new AgentSession for session_id=%s", session_id)
            return self._sessions[session_id]

    # ── Main entry point ───────────────────────────────────────────────

    async def run(
        self,
        user_message: str,
        session_id: str,
        project_name: str = "",
        project_id: str = "",
        github_token: str | None = None,
        file_urls: list[str] | None = None,
        metadata_context: dict[str, Any] | None = None,
    ) -> ChatMessage:
        """Send a user message to the agent and return a ChatMessage response.

        Args:
            user_message: The user's chat message.
            session_id: Solune session ID.
            project_name: Current project name.
            project_id: Current project ID.
            github_token: GitHub OAuth token (for Copilot provider).
            file_urls: Optional file URLs attached to the message.
            metadata_context: Optional repo metadata for richer responses.

        Returns:
            ChatMessage with optional action_type/action_data for proposals.
        """
        agent = self._ensure_agent(project_name, project_id)
        session = await self._get_or_create_session(session_id, agent)

        # Set runtime context for tools (via contextvars — works with all agent types)
        runtime_ctx: dict[str, Any] = {
            "project_name": project_name,
            "project_id": project_id,
            "session_id": session_id,
            "github_token": github_token,
        }
        if metadata_context:
            runtime_ctx["metadata_context"] = metadata_context
        if file_urls:
            runtime_ctx["file_urls"] = file_urls

        set_runtime_context(runtime_ctx)
        try:
            response = await agent.run(
                user_message,
                session=session,
            )
            return self._convert_response(response, session_id)

        except Exception as e:
            logger.error("Agent run failed: %s", e, exc_info=True)
            return ChatMessage(
                session_id=UUID(session_id) if session_id else uuid4(),
                sender_type=SenderType.ASSISTANT,
                content=(
                    "I'm sorry, I encountered an error processing your request. "
                    "Please try again or rephrase your message."
                ),
            )

    # ── Streaming entry point ──────────────────────────────────────────

    async def run_stream(
        self,
        user_message: str,
        session_id: str,
        project_name: str = "",
        project_id: str = "",
        github_token: str | None = None,
        file_urls: list[str] | None = None,
        metadata_context: dict[str, Any] | None = None,
    ) -> AsyncIterator[str]:
        """Stream agent response tokens as SSE-compatible strings.

        Yields partial text chunks.  The final chunk may contain action
        metadata as a JSON ``data:`` line.
        """
        agent = self._ensure_agent(project_name, project_id)
        session = await self._get_or_create_session(session_id, agent)

        runtime_ctx: dict[str, Any] = {
            "project_name": project_name,
            "project_id": project_id,
            "session_id": session_id,
            "github_token": github_token,
        }
        if metadata_context:
            runtime_ctx["metadata_context"] = metadata_context
        if file_urls:
            runtime_ctx["file_urls"] = file_urls

        set_runtime_context(runtime_ctx)
        try:
            stream = agent.run(
                user_message,
                stream=True,
                session=session,
            )

            accumulated_text = ""
            async for update in stream:
                if hasattr(update, "text") and update.text:
                    chunk = update.text
                    accumulated_text += chunk
                    yield chunk

            # After streaming completes, check if the accumulated response
            # contains tool output that needs to be sent as final metadata
            action_data = self._extract_action_data(accumulated_text)
            if action_data:
                yield "\n" + json.dumps({"action_data": action_data})

        except Exception as e:
            logger.error("Agent stream failed: %s", e, exc_info=True)
            yield "I'm sorry, I encountered an error. Please try again."

    # ── Response conversion ────────────────────────────────────────────

    def _convert_response(self, response: Any, session_id: str) -> ChatMessage:
        """Convert an ``AgentResponse`` to a ``ChatMessage``.

        If the response text contains structured tool output (JSON with
        ``action_type``), we extract it into ``action_data``.
        """
        text = ""
        if hasattr(response, "text") and response.text:
            text = response.text
        elif hasattr(response, "messages") and response.messages:
            parts = [msg.text for msg in response.messages if hasattr(msg, "text") and msg.text]
            text = "\n".join(parts)

        # Try to extract structured action data from tool output
        action_type = None
        action_data = None

        extracted = self._extract_action_data(text)
        if extracted:
            action_type_str = extracted.get("action_type", "")
            # Map tool action types to ChatMessage ActionTypes
            action_map = {
                "task_create": ActionType.TASK_CREATE,
                "issue_create": ActionType.ISSUE_CREATE,
                "status_update": ActionType.STATUS_UPDATE,
            }
            if action_type_str in action_map:
                action_type = action_map[action_type_str]
                action_data = extracted
                # Clean tool JSON from the displayed text
                text = self._clean_tool_output(text)

        if not text:
            text = "I've processed your request."

        return ChatMessage(
            session_id=UUID(session_id) if session_id else uuid4(),
            sender_type=SenderType.ASSISTANT,
            content=text,
            action_type=action_type,
            action_data=action_data,
        )

    def _extract_action_data(self, text: str) -> dict[str, Any] | None:
        """Try to extract JSON action data from the response text."""
        if not text:
            return None

        # Strategy 1: fenced code blocks (```json ... ```)
        for match in re.finditer(r"```json\s*(.*?)```", text, re.DOTALL):
            try:
                data = json.loads(match.group(1))
                if isinstance(data, dict) and "action_type" in data:
                    return data
            except (json.JSONDecodeError, TypeError):
                continue

        # Strategy 2: brute-force scan for top-level JSON objects containing
        # "action_type".  This handles nested braces (e.g. recommendation dicts)
        # by iterating from each '{' and counting brace depth.
        for start_idx in range(len(text)):
            if text[start_idx] != "{":
                continue
            depth = 0
            for end_idx in range(start_idx, len(text)):
                if text[end_idx] == "{":
                    depth += 1
                elif text[end_idx] == "}":
                    depth -= 1
                if depth == 0:
                    candidate = text[start_idx : end_idx + 1]
                    if '"action_type"' in candidate:
                        try:
                            data = json.loads(candidate)
                            if isinstance(data, dict) and "action_type" in data:
                                return data
                        except (json.JSONDecodeError, TypeError):
                            pass
                    break

        return None

    def _clean_tool_output(self, text: str) -> str:
        """Remove JSON tool output blocks from display text."""
        # Remove ```json ... ``` blocks containing action_type
        text = re.sub(
            r"```json\s*\{.*?\"action_type\".*?\}\s*```",
            "",
            text,
            flags=re.DOTALL,
        )
        # Remove bare JSON objects with action_type using the same depth-aware
        # approach: find the outermost {...} containing "action_type" and remove.
        action_data = self._extract_action_data(text)
        if action_data:
            # Re-serialize and remove the exact JSON string if present
            try:
                json_str = json.dumps(action_data)
                text = text.replace(json_str, "")
            except (TypeError, ValueError):
                pass
        return text.strip()


# ── Singleton ──────────────────────────────────────────────────────────────

_chat_agent_service: ChatAgentService | None = None


def get_chat_agent_service() -> ChatAgentService:
    """Return the singleton ChatAgentService, creating it on first call."""
    global _chat_agent_service
    if _chat_agent_service is None:
        _chat_agent_service = ChatAgentService()
    return _chat_agent_service


def reset_chat_agent_service() -> None:
    """Reset the singleton (for testing)."""
    global _chat_agent_service
    _chat_agent_service = None
