"""Unit tests for Signal delivery service.

Covers:
- format_signal_message() — message formatting for Signal
- _get_header() — header emoji selection
- should_deliver() — notification preference filtering
- _format_body() — body summarisation for action types
"""

from src.models.chat import ActionType, ChatMessage, SenderType
from src.models.signal import SignalNotificationMode
from src.services.signal_delivery import (
    MAX_SIGNAL_MESSAGE_LENGTH,
    _get_header,
    format_signal_message,
    should_deliver,
)

# =============================================================================
# Helpers
# =============================================================================


def _make_message(**overrides) -> ChatMessage:
    """Create a ChatMessage with sensible defaults."""
    defaults = {
        "session_id": "00000000-0000-0000-0000-000000000001",
        "sender_type": SenderType.ASSISTANT,
        "content": "Test message content",
    }
    defaults.update(overrides)
    return ChatMessage(**defaults)


# =============================================================================
# format_signal_message
# =============================================================================


class TestFormatSignalMessage:
    """Tests for message formatting."""

    def test_basic_assistant_message(self):
        msg = _make_message()
        text = format_signal_message(msg)

        assert "Assistant Message" in text
        assert "Test message content" in text

    def test_includes_project_name(self):
        msg = _make_message()
        text = format_signal_message(msg, project_name="MyProject")

        assert "MyProject" in text

    def test_includes_deep_link(self):
        msg = _make_message()
        text = format_signal_message(msg, deep_link_url="https://app.example.com/chat")

        assert "https://app.example.com/chat" in text

    def test_truncates_long_messages(self):
        # _format_body caps generic content at 1000 chars; use an action type
        # with a very long proposed_title so the assembled text exceeds the limit.
        long_title = "T" * (MAX_SIGNAL_MESSAGE_LENGTH + 500)
        msg = _make_message(
            content="body",
            action_type=ActionType.TASK_CREATE,
            action_data={"proposed_title": long_title},
        )
        text = format_signal_message(msg)

        assert "truncated" in text


# =============================================================================
# _get_header
# =============================================================================


class TestGetHeader:
    """Tests for header emoji selection."""

    def test_task_create_pending(self):
        msg = _make_message(
            action_type=ActionType.TASK_CREATE,
            action_data={"status": "pending"},
        )
        assert "Task Proposal" in _get_header(msg)

    def test_task_create_confirmed(self):
        msg = _make_message(
            action_type=ActionType.TASK_CREATE,
            action_data={"status": "confirmed"},
        )
        assert "Task Created" in _get_header(msg)

    def test_system_message(self):
        msg = _make_message(sender_type=SenderType.SYSTEM)
        assert "System Notification" in _get_header(msg)

    def test_generic_assistant_message(self):
        msg = _make_message()
        assert "Assistant Message" in _get_header(msg)


# =============================================================================
# should_deliver
# =============================================================================


class TestShouldDeliver:
    """Tests for notification preference filtering."""

    def test_mode_none_blocks_all(self):
        msg = _make_message()
        assert should_deliver(SignalNotificationMode.NONE, msg) is False

    def test_mode_all_delivers_everything(self):
        msg = _make_message()
        assert should_deliver(SignalNotificationMode.ALL, msg) is True

    def test_actions_only_delivers_pending_task_create(self):
        msg = _make_message(
            action_type=ActionType.TASK_CREATE,
            action_data={"status": "pending"},
        )
        assert should_deliver(SignalNotificationMode.ACTIONS_ONLY, msg) is True

    def test_actions_only_blocks_plain_message(self):
        msg = _make_message()
        assert should_deliver(SignalNotificationMode.ACTIONS_ONLY, msg) is False

    def test_confirmations_only_delivers_system(self):
        msg = _make_message(sender_type=SenderType.SYSTEM)
        assert should_deliver(SignalNotificationMode.CONFIRMATIONS_ONLY, msg) is True

    def test_confirmations_only_delivers_confirmed_action(self):
        msg = _make_message(
            action_type=ActionType.TASK_CREATE,
            action_data={"status": "confirmed"},
        )
        assert should_deliver(SignalNotificationMode.CONFIRMATIONS_ONLY, msg) is True

    def test_confirmations_only_blocks_pending(self):
        msg = _make_message(
            action_type=ActionType.TASK_CREATE,
            action_data={"status": "pending"},
        )
        assert should_deliver(SignalNotificationMode.CONFIRMATIONS_ONLY, msg) is False
