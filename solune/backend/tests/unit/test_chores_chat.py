"""Tests for chore chat state management (src/services/chores/chat.py).

Covers:
- get_or_create_conversation: new and existing conversations
- add_user_message / add_assistant_message: appending messages
- cleanup_conversation: removing from store
- is_template_ready / _is_template_ready: template detection
- _evict_stale_conversations: eviction logic
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from src.services.chores.chat import (
    _MAX_AGE_SECONDS,
    _MAX_CONVERSATIONS,
    SYSTEM_PROMPT,
    _conversations,
    _evict_stale_conversations,
    add_assistant_message,
    add_user_message,
    cleanup_conversation,
    get_or_create_conversation,
    is_template_ready,
)


@pytest.fixture(autouse=True)
def _clear_conversations():
    """Clear in-memory conversation store between tests."""
    _conversations.clear()
    yield
    _conversations.clear()


# ── get_or_create_conversation ────────────────────────────────────────────


class TestGetOrCreateConversation:
    """Tests for conversation creation and retrieval."""

    def test_create_new_conversation_with_none(self):
        """Passing None creates a new conversation with system prompt."""
        conv_id, messages = get_or_create_conversation(None)
        assert conv_id is not None
        assert len(messages) == 1
        assert messages[0]["role"] == "system"
        assert messages[0]["content"] == SYSTEM_PROMPT

    def test_create_new_conversation_with_unknown_id(self):
        """Passing an unknown ID creates a new conversation."""
        conv_id, messages = get_or_create_conversation("nonexistent-id")
        assert conv_id != "nonexistent-id"
        assert len(messages) == 1
        assert messages[0]["role"] == "system"

    def test_returns_existing_conversation(self):
        """Existing conversation is returned as-is."""
        conv_id, _messages = get_or_create_conversation(None)
        add_user_message(conv_id, "Hello")

        same_id, same_messages = get_or_create_conversation(conv_id)
        assert same_id == conv_id
        assert len(same_messages) == 2  # system + user
        assert same_messages[1]["content"] == "Hello"

    def test_new_conversation_stored_in_dict(self):
        """New conversation is stored in the _conversations dict."""
        conv_id, _ = get_or_create_conversation(None)
        assert conv_id in _conversations


# ── add_user_message / add_assistant_message ──────────────────────────────


class TestMessageAppending:
    """Tests for adding messages to conversations."""

    def test_add_user_message(self):
        """User message is appended to conversation."""
        conv_id, messages = get_or_create_conversation(None)
        add_user_message(conv_id, "What is a chore?")
        assert len(messages) == 2
        assert messages[-1] == {"role": "user", "content": "What is a chore?"}

    def test_add_assistant_message(self):
        """Assistant message is appended to conversation."""
        conv_id, messages = get_or_create_conversation(None)
        add_assistant_message(conv_id, "A chore is a recurring task.")
        assert len(messages) == 2
        assert messages[-1] == {"role": "assistant", "content": "A chore is a recurring task."}

    def test_add_message_to_unknown_conversation(self):
        """Adding message to unknown conversation is a no-op."""
        add_user_message("nonexistent", "Hello")
        add_assistant_message("nonexistent", "Hi")
        assert len(_conversations) == 0


# ── cleanup_conversation ──────────────────────────────────────────────────


class TestCleanupConversation:
    """Tests for removing conversations from store."""

    def test_removes_conversation(self):
        """Cleanup removes conversation from the store."""
        conv_id, _ = get_or_create_conversation(None)
        assert conv_id in _conversations
        cleanup_conversation(conv_id)
        assert conv_id not in _conversations

    def test_cleanup_nonexistent_is_noop(self):
        """Cleaning up a nonexistent conversation does not raise."""
        cleanup_conversation("nonexistent-id")


# ── is_template_ready ─────────────────────────────────────────────────────


class TestIsTemplateReady:
    """Tests for template readiness detection via code fence markers."""

    def test_detects_complete_template(self):
        """Detects template content between ```template ... ``` markers."""
        response = "Here is your template:\n```template\n---\nname: X\n---\nBody\n```\nDone!"
        ready, content = is_template_ready(response)
        assert ready is True
        assert "name: X" in content

    def test_unterminated_fence_returns_false(self):
        """Unterminated template fence is not considered ready."""
        response = "Here is your template:\n```template\n---\nname: X\n---\nBody"
        ready, content = is_template_ready(response)
        assert ready is False
        assert content is None

    def test_no_marker_returns_false(self):
        """Response without template marker is not ready."""
        response = "Let me ask some more questions about your chore."
        ready, content = is_template_ready(response)
        assert ready is False
        assert content is None

    def test_empty_template_content(self):
        """Empty template content between markers."""
        response = "```template\n```"
        ready, _content = is_template_ready(response)
        assert ready is True


# ── _evict_stale_conversations ────────────────────────────────────────────


class TestEvictStaleConversations:
    """Tests for TTL-based and capacity eviction."""

    def test_evicts_expired_conversations(self):
        """Conversations older than _MAX_AGE_SECONDS are removed."""
        old_time = (datetime.now(UTC) - timedelta(seconds=_MAX_AGE_SECONDS + 60)).isoformat()
        _conversations["old-conv"] = {
            "messages": [{"role": "system", "content": "prompt"}],
            "created_at": old_time,
        }
        _conversations["new-conv"] = {
            "messages": [{"role": "system", "content": "prompt"}],
            "created_at": datetime.now(UTC).isoformat(),
        }
        _evict_stale_conversations()
        assert "old-conv" not in _conversations
        assert "new-conv" in _conversations

    def test_enforces_max_capacity(self):
        """When at capacity, oldest conversations are evicted."""
        now = datetime.now(UTC)
        for i in range(_MAX_CONVERSATIONS + 5):
            ts = (now - timedelta(seconds=_MAX_CONVERSATIONS + 5 - i)).isoformat()
            _conversations[f"conv-{i}"] = {
                "messages": [],
                "created_at": ts,
            }
        _evict_stale_conversations()
        assert len(_conversations) <= _MAX_CONVERSATIONS
