"""Chat Agent Service — v0.2.0 replacement for the priority-dispatch cascade.

``ChatAgentService`` holds an :class:`AgentProvider` singleton, manages
``session_id`` ↔ agent-session mapping, and converts agent responses into
:class:`ChatMessage` instances that the REST API can return unchanged.

The service is designed as a drop-in layer between ``chat.py`` and the
underlying LLM provider.  When the agent framework is unavailable the
caller can fall back to the legacy :class:`AIAgentService` dispatch.

Usage::

    service = get_chat_agent_service()
    response = await service.run(
        message="Add dark mode to the app",
        session_id=session.session_id,
        project_id=selected_project_id,
        project_name="My Project",
        github_token=session.access_token,
    )
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from src.logging_utils import get_logger
from src.models.chat import ActionType, ChatMessage, SenderType
from src.services.agent_provider import AgentProvider, create_agent_provider
from src.services.agent_tools import set_runtime_context
from src.utils import utcnow

logger = get_logger(__name__)


class ChatAgentService:
    """High-level service that wraps an AgentProvider for the chat API.

    Responsibilities:
    * Manage per-session agent state (session mapping).
    * Inject runtime context via ``set_runtime_context`` before each run.
    * Convert raw agent responses → ``ChatMessage``.
    """

    def __init__(self, provider: AgentProvider | None = None) -> None:
        self._provider = provider or create_agent_provider()
        self._sessions: dict[str, dict[str, Any]] = {}
        logger.info("ChatAgentService initialized with provider: %s", self._provider.provider_name)

    # ── Session management ────────────────────────────────────────────

    def get_or_create_session(self, session_id: str) -> dict[str, Any]:
        """Return existing session state or create a new empty one."""
        if session_id not in self._sessions:
            self._sessions[session_id] = {
                "session_id": session_id,
                "history": [],
                "created_at": utcnow().isoformat(),
            }
            logger.debug("Created new agent session for %s", session_id)
        return self._sessions[session_id]

    def clear_session(self, session_id: str) -> None:
        """Remove a session's state."""
        self._sessions.pop(session_id, None)

    @property
    def active_sessions(self) -> int:
        """Return the number of active sessions."""
        return len(self._sessions)

    # ── Core run methods ──────────────────────────────────────────────

    async def run(
        self,
        *,
        message: str,
        session_id: str,
        project_id: str,
        project_name: str = "Unknown Project",
        github_token: str | None = None,
    ) -> ChatMessage:
        """Send *message* to the agent and return a ``ChatMessage``.

        Args:
            message: User message text.
            session_id: Solune session ID (UUID string).
            project_id: Active GitHub project node ID.
            project_name: Human-readable project name.
            github_token: OAuth token for the Copilot provider.

        Returns:
            A :class:`ChatMessage` ready for the REST API response.
        """
        # Inject runtime context for tool functions
        set_runtime_context(
            project_id=project_id,
            session_id=session_id,
            github_token=github_token,
            project_name=project_name,
        )

        # Track session
        session = self.get_or_create_session(session_id)
        session["history"].append({"role": "user", "content": message})

        # Call the agent provider
        try:
            result = await self._provider.run(message, session_id=session_id)
        except Exception as exc:
            logger.error("Agent provider failed: %s", exc, exc_info=True)
            return ChatMessage(
                session_id=UUID(session_id),
                sender_type=SenderType.ASSISTANT,
                content="I'm sorry, I encountered an error processing your request. Please try again.",
            )

        # Convert to ChatMessage
        return self._result_to_chat_message(result, session_id)

    async def run_stream(
        self,
        *,
        message: str,
        session_id: str,
        project_id: str,
        project_name: str = "Unknown Project",
        github_token: str | None = None,
    ):
        """Stream agent response tokens as dicts with ``"delta"`` keys.

        Yields dicts suitable for SSE serialisation.
        """
        set_runtime_context(
            project_id=project_id,
            session_id=session_id,
            github_token=github_token,
            project_name=project_name,
        )

        session = self.get_or_create_session(session_id)
        session["history"].append({"role": "user", "content": message})

        async for chunk in self._provider.run_stream(message, session_id=session_id):
            yield chunk

    # ── Response conversion ───────────────────────────────────────────

    @staticmethod
    def _result_to_chat_message(result: dict[str, Any], session_id: str) -> ChatMessage:
        """Convert a raw agent result dict into a ``ChatMessage``."""
        content = result.get("content") or result.get("message") or ""
        action_type_raw = result.get("action_type")
        action_data = result.get("action_data")

        action_type: ActionType | None = None
        if action_type_raw:
            try:
                action_type = ActionType(action_type_raw)
            except ValueError:
                logger.warning("Unknown action_type from agent: %s", action_type_raw)

        return ChatMessage(
            session_id=UUID(session_id),
            sender_type=SenderType.ASSISTANT,
            content=content,
            action_type=action_type,
            action_data=action_data,
        )


# ── Global singleton ──────────────────────────────────────────────────────

_chat_agent_service_instance: ChatAgentService | None = None


def get_chat_agent_service() -> ChatAgentService:
    """Get or create the global ChatAgentService singleton.

    Raises:
        ValueError: If the agent provider cannot be created (e.g. missing
            credentials).
    """
    global _chat_agent_service_instance
    if _chat_agent_service_instance is None:
        _chat_agent_service_instance = ChatAgentService()
    return _chat_agent_service_instance


def reset_chat_agent_service() -> None:
    """Reset the global singleton (used in tests)."""
    global _chat_agent_service_instance
    _chat_agent_service_instance = None
