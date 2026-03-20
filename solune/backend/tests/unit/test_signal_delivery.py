"""Unit tests for Signal delivery service.

Covers:
- format_signal_message() — message formatting for Signal
- _get_header() — header emoji selection
- should_deliver() — notification preference filtering
- _format_body() — body summarisation for action types
"""

from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

from src.models.chat import ActionType, ChatMessage, SenderType
from src.models.signal import SignalConnectionStatus, SignalDeliveryStatus, SignalNotificationMode
from src.services.signal_delivery import (
    MAX_SIGNAL_MESSAGE_LENGTH,
    _delivery_task,
    _format_body,
    _get_header,
    deliver_chat_message_via_signal,
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

    def test_status_update_headers(self):
        pending = _make_message(
            action_type=ActionType.STATUS_UPDATE,
            action_data={"status": "pending"},
        )
        confirmed = _make_message(
            action_type=ActionType.STATUS_UPDATE,
            action_data={"status": "confirmed"},
        )

        assert "Status Change Proposal" in _get_header(pending)
        assert "Status Updated" in _get_header(confirmed)

    def test_issue_create_headers(self):
        pending = _make_message(
            action_type=ActionType.ISSUE_CREATE,
            action_data={"status": "pending"},
        )
        confirmed = _make_message(
            action_type=ActionType.ISSUE_CREATE,
            action_data={"status": "confirmed"},
        )

        assert "Issue Recommendation" in _get_header(pending)
        assert "Issue Created" in _get_header(confirmed)


class TestFormatBody:
    def test_task_create_body_uses_title(self):
        msg = _make_message(
            action_type=ActionType.TASK_CREATE,
            action_data={"proposed_title": "Write tests"},
            content="Detailed rationale",
        )

        assert _format_body(msg) == "*Write tests*\n\nDetailed rationale"

    def test_status_update_body_summarizes_task_and_target(self):
        msg = _make_message(
            action_type=ActionType.STATUS_UPDATE,
            action_data={"task_title": "Coverage", "target_status": "done"},
            content="Marked complete",
        )

        assert _format_body(msg) == "*Coverage* → _done_\n\nMarked complete"

    def test_issue_create_body_uses_title(self):
        msg = _make_message(
            action_type=ActionType.ISSUE_CREATE,
            action_data={"proposed_title": "Fix flaky tests"},
            content="Please file this",
        )

        assert _format_body(msg) == "*Fix flaky tests*\n\nPlease file this"


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

    def test_actions_only_blocks_confirmed_action(self):
        msg = _make_message(
            action_type=ActionType.STATUS_UPDATE,
            action_data={"status": "confirmed"},
        )
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

    def test_confirmations_only_blocks_action_without_confirmation(self):
        msg = _make_message(
            action_type=ActionType.ISSUE_CREATE,
            action_data={"status": "pending"},
        )
        assert should_deliver(SignalNotificationMode.CONFIRMATIONS_ONLY, msg) is False


class TestDeliveryTask:
    async def test_delivery_task_marks_message_delivered_on_success(self):
        with (
            patch("src.services.signal_delivery._deliver_with_retry", AsyncMock()) as deliver_mock,
            patch(
                "src.services.signal_delivery.update_signal_message_status", AsyncMock()
            ) as status_mock,
        ):
            await _delivery_task("+15551234567", "hello", "audit-1")

        deliver_mock.assert_awaited_once_with("+15551234567", "hello")
        status_mock.assert_awaited_once_with("audit-1", SignalDeliveryStatus.DELIVERED)

    async def test_delivery_task_marks_message_failed_on_error(self):
        with (
            patch(
                "src.services.signal_delivery._deliver_with_retry",
                AsyncMock(side_effect=RuntimeError("boom")),
            ),
            patch(
                "src.services.signal_delivery.update_signal_message_status", AsyncMock()
            ) as status_mock,
        ):
            await _delivery_task("+15551234567", "hello", "audit-2")

        status_mock.assert_awaited_once()
        assert status_mock.await_args.args[:2] == ("audit-2", SignalDeliveryStatus.FAILED)
        assert status_mock.await_args.kwargs["error_detail"] == "boom"


class TestDeliverChatMessageViaSignal:
    async def test_skips_when_no_connection_or_connection_not_connected(self):
        msg = _make_message()

        with patch(
            "src.services.signal_delivery.get_connection_by_user", AsyncMock(return_value=None)
        ):
            await deliver_chat_message_via_signal("user-1", msg)

        disconnected = SimpleNamespace(status=SignalConnectionStatus.PENDING)
        with patch(
            "src.services.signal_delivery.get_connection_by_user",
            AsyncMock(return_value=disconnected),
        ):
            await deliver_chat_message_via_signal("user-1", msg)

    async def test_skips_when_notification_preferences_filter_message(self):
        msg = _make_message()
        connection = SimpleNamespace(
            id="conn-1",
            status=SignalConnectionStatus.CONNECTED,
            notification_mode=SignalNotificationMode.ACTIONS_ONLY,
            signal_phone_encrypted="ciphertext",
        )

        with (
            patch(
                "src.services.signal_delivery.get_connection_by_user",
                AsyncMock(return_value=connection),
            ),
            patch("src.services.signal_delivery.create_signal_message", AsyncMock()) as create_mock,
        ):
            await deliver_chat_message_via_signal("user-1", msg)

        create_mock.assert_not_awaited()

    async def test_skips_when_phone_decryption_fails(self):
        msg = _make_message()
        connection = SimpleNamespace(
            id="conn-1",
            status=SignalConnectionStatus.CONNECTED,
            notification_mode=SignalNotificationMode.ALL,
            signal_phone_encrypted="ciphertext",
        )
        fake_encryption = SimpleNamespace(decrypt=Mock(side_effect=RuntimeError("bad key")))

        with (
            patch(
                "src.services.signal_delivery.get_connection_by_user",
                AsyncMock(return_value=connection),
            ),
            patch("src.services.signal_bridge._get_encryption", return_value=fake_encryption),
            patch("src.services.signal_delivery.create_signal_message", AsyncMock()) as create_mock,
        ):
            await deliver_chat_message_via_signal("user-1", msg)

        create_mock.assert_not_awaited()

    async def test_creates_audit_row_and_background_task(self):
        msg = _make_message(action_type=ActionType.TASK_CREATE, action_data={"status": "pending"})
        connection = SimpleNamespace(
            id="conn-1",
            status=SignalConnectionStatus.CONNECTED,
            notification_mode=SignalNotificationMode.ALL,
            signal_phone_encrypted="ciphertext",
        )
        fake_encryption = SimpleNamespace(decrypt=lambda value: "+15551234567")
        audit = SimpleNamespace(id="audit-1")
        captured = {}

        def _capture_task(coro, *, name):
            captured["coro"] = coro
            captured["name"] = name
            coro.close()

        with (
            patch(
                "src.services.signal_delivery.get_connection_by_user",
                AsyncMock(return_value=connection),
            ),
            patch("src.services.signal_bridge._get_encryption", return_value=fake_encryption),
            patch(
                "src.services.signal_delivery.get_settings",
                return_value=SimpleNamespace(frontend_url="https://frontend.example"),
            ),
            patch(
                "src.services.signal_delivery.create_signal_message", AsyncMock(return_value=audit)
            ) as create_mock,
            patch(
                "src.services.task_registry.task_registry.create_task", side_effect=_capture_task
            ) as create_task_mock,
        ):
            await deliver_chat_message_via_signal(
                "user-1",
                msg,
                project_name="Project Mercury",
                project_id="project-123",
            )

        create_mock.assert_awaited_once()
        assert create_mock.await_args.kwargs["connection_id"] == "conn-1"
        assert create_mock.await_args.kwargs["delivery_status"] == SignalDeliveryStatus.PENDING
        assert "Project Mercury" in create_mock.await_args.kwargs["content_preview"]
        assert (
            "https://frontend.example/projects/project-123/chat"
            in create_mock.await_args.kwargs["content_preview"]
        )
        create_task_mock.assert_called_once()
        assert captured["name"] == "signal-delivery-audit-1"
