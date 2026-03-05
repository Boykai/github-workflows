"""Chore chat — in-memory conversation state for sparse-input template building."""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime

from src.utils import BoundedDict

logger = logging.getLogger(__name__)

# In-memory conversation store: conversation_id → conversation data
_conversations: BoundedDict[str, dict] = BoundedDict(maxlen=200)

# Limits to prevent unbounded memory growth
_MAX_CONVERSATIONS = 100
_MAX_AGE_SECONDS = 3600  # 1 hour

SYSTEM_PROMPT = """\
You are a helpful assistant that helps users create GitHub Issue Templates for recurring \
maintenance tasks (called "chores"). The user has given you a brief idea for a chore and \
you need to guide them through building a complete, structured GitHub Issue Template.

Your job:
1. Ask clarifying questions about the chore (purpose, scope, steps, acceptance criteria).
2. Ask about labels, assignees, and any project-specific context.
3. When you have enough information, generate a complete GitHub Issue Template in markdown \
format with YAML front matter.
4. When the template is ready, include it in your response wrapped in a code block with \
the marker: ```template ... ```

Rules:
- Keep responses concise and conversational.
- Ask one or two questions at a time, not all at once.
- If the user says "done", "looks good", "that works", or similar, finalize the template.
- Always include YAML front matter (name, about, title, labels, assignees) in the final template.
"""


def _is_template_ready(response: str) -> tuple[bool, str | None]:
    """Check if the AI response contains a finalized template.

    Returns (is_ready, template_content_or_none).
    """
    marker = "```template"
    if marker in response:
        start = response.index(marker) + len(marker)
        end = response.find("```", start)
        if end == -1:
            # Unterminated fence — not a complete template yet
            return False, None
        content = response[start:end].strip()
        return True, content
    return False, None


def _evict_stale_conversations() -> None:
    """Remove expired conversations and enforce size limit."""
    now = datetime.now(UTC)
    expired = [
        cid
        for cid, data in _conversations.items()
        if (now - datetime.fromisoformat(data["created_at"])).total_seconds() > _MAX_AGE_SECONDS
    ]
    for cid in expired:
        del _conversations[cid]

    # If still over capacity, evict oldest first
    if len(_conversations) >= _MAX_CONVERSATIONS:
        sorted_ids = sorted(
            _conversations,
            key=lambda cid: _conversations[cid]["created_at"],
        )
        for cid in sorted_ids[: len(_conversations) - _MAX_CONVERSATIONS + 1]:
            del _conversations[cid]


def get_or_create_conversation(conversation_id: str | None) -> tuple[str, list[dict]]:
    """Get an existing conversation or create a new one.

    Returns (conversation_id, messages).
    """
    if conversation_id and conversation_id in _conversations:
        return conversation_id, _conversations[conversation_id]["messages"]

    _evict_stale_conversations()

    new_id = str(uuid.uuid4())
    _conversations[new_id] = {
        "messages": [{"role": "system", "content": SYSTEM_PROMPT}],
        "created_at": datetime.now(UTC).isoformat(),
    }
    return new_id, _conversations[new_id]["messages"]


def add_user_message(conversation_id: str, content: str) -> None:
    """Add a user message to the conversation."""
    if conversation_id in _conversations:
        _conversations[conversation_id]["messages"].append({"role": "user", "content": content})


def add_assistant_message(conversation_id: str, content: str) -> None:
    """Add an assistant response to the conversation."""
    if conversation_id in _conversations:
        _conversations[conversation_id]["messages"].append(
            {"role": "assistant", "content": content}
        )


def cleanup_conversation(conversation_id: str) -> None:
    """Remove a conversation from the store (e.g., after finalization)."""
    _conversations.pop(conversation_id, None)


def is_template_ready(response: str) -> tuple[bool, str | None]:
    """Public wrapper for template readiness detection."""
    return _is_template_ready(response)


async def generate_chat_response(
    conversation_id: str | None,
    user_content: str,
    *,
    github_token: str,
) -> tuple[str, str, bool, str | None]:
    """Run a full chat turn: add user message, call AI, add response, detect template.

    Returns (conversation_id, response_text, template_ready, template_content).
    """
    from src.services.ai_agent import get_ai_agent_service

    conv_id, messages = get_or_create_conversation(conversation_id)
    add_user_message(conv_id, user_content)

    ai_service = get_ai_agent_service()
    response = await ai_service._call_completion(
        messages=messages,
        temperature=0.7,
        max_tokens=2000,
        github_token=github_token,
    )

    add_assistant_message(conv_id, response)

    ready, content = is_template_ready(response)
    if ready:
        cleanup_conversation(conv_id)

    return conv_id, response, ready, content
