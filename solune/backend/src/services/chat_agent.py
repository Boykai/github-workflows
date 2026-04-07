"""ChatAgentService — Microsoft Agent Framework chat orchestrator.

Replaces the priority-dispatch cascade in chat.py with a single agent.run()
call.  The agent decides which tool to invoke based on its instructions.

v0.2.0 — Intelligent Chat Agent (Microsoft Agent Framework)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from src.logging_utils import get_logger
from src.models.chat import ActionType, ChatMessage, SenderType
from src.services.agent_tools import RuntimeContext, set_runtime_context

logger = get_logger(__name__)


@dataclass
class AgentResponse:
    """Simplified representation of an agent framework response."""

    content: str = ""
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    action_type: ActionType | None = None
    action_data: dict[str, Any] | None = None


class ChatAgentService:
    """Orchestrates chat through the Microsoft Agent Framework.

    Manages a singleton agent instance and maps Solune session IDs to
    AgentSession objects for multi-turn memory.

    Public API:
        run(message, session_id, context) -> ChatMessage
        run_stream(message, session_id, context) -> AsyncIterator[str]
    """

    def __init__(self, agent_provider: Any) -> None:
        """Initialize with an AgentProvider instance.

        Args:
            agent_provider: An AgentProvider wrapping the configured agent.
        """
        self._provider = agent_provider
        self._sessions: dict[str, Any] = {}
        logger.info(
            "ChatAgentService initialized with provider: %s",
            agent_provider.name,
        )

    @property
    def provider_name(self) -> str:
        """Name of the underlying agent provider."""
        return self._provider.name

    def _get_or_create_session(self, session_id: str) -> Any:
        """Get an existing agent session or create a new one.

        Args:
            session_id: Solune session ID (maps to AgentSession).

        Returns:
            The agent session object.
        """
        if session_id not in self._sessions:
            self._sessions[session_id] = {"id": session_id, "messages": []}
            logger.debug("Created new agent session for %s", session_id)
        return self._sessions[session_id]

    def clear_session(self, session_id: str) -> None:
        """Remove a session from the cache.

        Args:
            session_id: Solune session ID to clear.
        """
        removed = self._sessions.pop(session_id, None)
        if removed:
            logger.debug("Cleared agent session %s", session_id)

    async def run(
        self,
        message: str,
        session_id: str | UUID,
        context: RuntimeContext,
    ) -> ChatMessage:
        """Process a chat message through the agent.

        Sets runtime context, invokes the agent, and converts the response
        to a ChatMessage.

        Args:
            message: User's chat message content.
            session_id: Solune session ID.
            context: Runtime context with project/token info.

        Returns:
            ChatMessage with the agent's response.
        """
        sid = str(session_id)

        # Set runtime context for tool functions
        set_runtime_context(context)

        # Get or create session
        session = self._get_or_create_session(sid)
        session["messages"].append({"role": "user", "content": message})

        # Invoke the agent
        try:
            agent = self._provider.agent
            response = await agent.run(message, session_id=sid)
            agent_response = self._convert_response(response)
        except Exception as exc:
            logger.error("Agent run failed: %s", exc, exc_info=True)
            return ChatMessage(
                session_id=UUID(sid) if not isinstance(session_id, UUID) else session_id,
                sender_type=SenderType.ASSISTANT,
                content=f"I encountered an error processing your request: {exc}",
            )

        # Build ChatMessage from AgentResponse
        chat_msg = ChatMessage(
            session_id=UUID(sid) if not isinstance(session_id, UUID) else session_id,
            sender_type=SenderType.ASSISTANT,
            content=agent_response.content,
            action_type=agent_response.action_type,
            action_data=agent_response.action_data,
        )

        session["messages"].append({"role": "assistant", "content": agent_response.content})
        return chat_msg

    async def run_stream(
        self,
        message: str,
        session_id: str | UUID,
        context: RuntimeContext,
    ):
        """Process a chat message with streaming response.

        Yields tokens progressively as the agent generates them.

        Args:
            message: User's chat message content.
            session_id: Solune session ID.
            context: Runtime context with project/token info.

        Yields:
            String tokens as they are generated.
        """
        sid = str(session_id)
        set_runtime_context(context)
        session = self._get_or_create_session(sid)
        session["messages"].append({"role": "user", "content": message})

        try:
            agent = self._provider.agent
            async for token in agent.run_stream(message, session_id=sid):
                yield token
        except Exception as exc:
            logger.error("Agent stream failed: %s", exc, exc_info=True)
            yield f"Error: {exc}"

    def _convert_response(self, response: Any) -> AgentResponse:
        """Convert an agent framework response to AgentResponse.

        Handles tool call results and maps them to action_type/action_data.

        Args:
            response: Raw response from agent.run().

        Returns:
            AgentResponse with extracted content and actions.
        """
        # Handle different response formats
        if isinstance(response, str):
            return AgentResponse(content=response)

        if isinstance(response, dict):
            content = response.get("content", "")
            action = response.get("action")
            action_data = response.get("action_data")

            action_type = None
            if action == "task_create":
                action_type = ActionType.TASK_CREATE
            elif action == "status_update":
                action_type = ActionType.STATUS_UPDATE
            elif action == "issue_create":
                action_type = ActionType.ISSUE_CREATE

            return AgentResponse(
                content=content,
                action_type=action_type,
                action_data=action_data,
            )

        # Agent framework response object
        if hasattr(response, "messages"):
            messages = response.messages
            if messages:
                last_msg = messages[-1]
                content = getattr(last_msg, "content", str(last_msg))
                return AgentResponse(content=content)

        return AgentResponse(content=str(response))


# ── Singleton ────────────────────────────────────────────────────────────

_chat_agent_service: ChatAgentService | None = None


def get_chat_agent_service() -> ChatAgentService:
    """Get or create the global ChatAgentService instance.

    Raises:
        ValueError: If the agent framework is not configured or
            dependencies are missing.
    """
    global _chat_agent_service
    if _chat_agent_service is None:
        from src.prompts.agent_instructions import build_agent_instructions
        from src.services.agent_provider import create_agent_provider
        from src.services.agent_tools import (
            analyze_transcript,
            ask_clarifying_question,
            create_issue_recommendation,
            create_task_proposal,
            get_pipeline_list,
            get_project_context,
            update_task_status,
        )

        instructions = build_agent_instructions()
        tools = [
            create_task_proposal,
            create_issue_recommendation,
            update_task_status,
            analyze_transcript,
            ask_clarifying_question,
            get_project_context,
            get_pipeline_list,
        ]

        provider = create_agent_provider(instructions, tools)
        _chat_agent_service = ChatAgentService(provider)
    return _chat_agent_service


def reset_chat_agent_service() -> None:
    """Reset the global ChatAgentService (for testing)."""
    global _chat_agent_service
    _chat_agent_service = None
