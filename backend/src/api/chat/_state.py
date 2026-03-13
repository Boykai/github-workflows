"""Shared in-memory state and helpers for the chat package.

This module holds the mutable chat state (messages, proposals, recommendations)
and utility functions used by multiple chat sub-modules.  Keeping state here
avoids circular imports between the sub-modules.
"""

from __future__ import annotations

import asyncio
from uuid import UUID

from src.logging_utils import get_logger
from src.models.chat import ChatMessage, SenderType
from src.models.recommendation import AITaskProposal, IssueRecommendation
from src.models.user import UserSession

logger = get_logger(__name__)

# In-memory storage for chat messages and proposals (MVP — lost on restart)
_messages: dict[str, list[ChatMessage]] = {}
_proposals: dict[str, AITaskProposal] = {}
# In-memory storage for issue recommendations
_recommendations: dict[str, IssueRecommendation] = {}


def get_session_messages(session_id: UUID) -> list[ChatMessage]:
    """Get messages for a session."""
    return _messages.get(str(session_id), [])


def add_message(session_id: UUID, message: ChatMessage) -> None:
    """Add a message to a session (in-memory + write-through to DB)."""
    key = str(session_id)
    if key not in _messages:
        _messages[key] = []
    _messages[key].append(message)

    # Phase A write-through: persist to SQLite (fire-and-forget)
    async def _persist() -> None:
        try:
            from src.services.chat_store import save_message
            from src.services.database import get_db

            db = get_db()
            action_data_str = None
            if message.action_data:
                import json

                action_data_str = json.dumps(message.action_data)
            await save_message(
                db,
                session_id=str(session_id),
                message_id=str(message.message_id),
                sender_type=message.sender_type.value,
                content=message.content,
                action_type=message.action_type.value if message.action_type else None,
                action_data=action_data_str,
            )
        except Exception as e:
            logger.debug("Chat message persistence failed (non-fatal): %s", e)

    try:
        asyncio.create_task(_persist())
    except RuntimeError:
        pass  # No running event loop


def _trigger_signal_delivery(
    session: UserSession,
    message: ChatMessage,
    project_name: str | None = None,
) -> None:
    """Fire-and-forget Signal delivery for assistant/system messages.

    Only delivers for non-user messages when the user has an active Signal connection.
    """
    if message.sender_type == SenderType.USER:
        return

    async def _deliver() -> None:
        try:
            from src.services.signal_delivery import deliver_chat_message_via_signal

            await deliver_chat_message_via_signal(
                github_user_id=session.github_user_id,
                message=message,
                project_name=project_name,
                project_id=session.selected_project_id,
            )
        except Exception as e:
            logger.debug("Signal delivery trigger failed (non-fatal): %s", e)

    try:
        asyncio.create_task(_deliver())
    except RuntimeError:
        pass  # No running event loop — skip silently
