"""Edge-case tests for guard service and Signal delivery."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
import yaml

from src.models.chat import ActionType, ChatMessage, SenderType
from src.models.signal import (
    SignalConnectionStatus,
    SignalDeliveryStatus,
    SignalNotificationMode,
)
from src.services.guard_service import _load_rules, check_guard, reset_cache
from src.services.signal_delivery import (
    _delivery_task,
    _format_body,
    deliver_chat_message_via_signal,
)


def _make_message(**overrides) -> ChatMessage:
    defaults = {
        "session_id": "00000000-0000-0000-0000-000000000001",
        "sender_type": SenderType.ASSISTANT,
        "content": "Message body",
    }
    defaults.update(overrides)
    return ChatMessage(**defaults)


@pytest.fixture(autouse=True)
def _clear_guard_cache() -> None:
    reset_cache()
    yield
    reset_cache()


class TestGuardServiceEdgeCases:
    def test_load_rules_without_guard_rules_key_returns_empty_list(self, tmp_path: Path) -> None:
        config_file = tmp_path / "guard-config.yml"
        config_file.write_text(yaml.dump({"other": []}), encoding="utf-8")

        assert _load_rules(config_file) == []

    def test_unknown_guard_level_is_treated_as_allowed(self, tmp_path: Path) -> None:
        config_file = tmp_path / "guard-config.yml"
        config_file.write_text(
            yaml.dump(
                {
                    "guard_rules": [
                        {
                            "path_pattern": "solune/backend/src/generated/*",
                            "guard_level": "review-only",
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )

        result = check_guard(
            ["solune/backend/src/generated/file.py"],
            config_path=config_file,
        )

        assert result.allowed == ["solune/backend/src/generated/file.py"]
        assert result.admin_blocked == []
        assert result.locked == []


class TestSignalFormattingEdgeCases:
    def test_format_body_summarizes_status_update(self) -> None:
        message = _make_message(
            content="Updated after investigation.",
            action_type=ActionType.STATUS_UPDATE,
            action_data={"task_title": "Triage flaky test", "target_status": "In Progress"},
        )

        formatted = _format_body(message)

        assert "*Triage flaky test*" in formatted
        assert "_In Progress_" in formatted
        assert "Updated after investigation." in formatted

    def test_format_body_summarizes_issue_create(self) -> None:
        message = _make_message(
            content="Issue recommendation details",
            action_type=ActionType.ISSUE_CREATE,
            action_data={"proposed_title": "Add retry coverage"},
        )

        formatted = _format_body(message)

        assert formatted.startswith("*Add retry coverage*")
        assert formatted.endswith("Issue recommendation details")

    def test_format_body_falls_back_to_truncated_plain_content(self) -> None:
        message = _make_message(content="x" * 1500)

        formatted = _format_body(message)

        assert formatted == "x" * 1000


class TestSignalDeliveryTask:
    @pytest.mark.asyncio
    async def test_delivery_task_marks_message_delivered(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        update_status = AsyncMock()
        monkeypatch.setattr("src.services.signal_delivery._deliver_with_retry", AsyncMock())
        monkeypatch.setattr(
            "src.services.signal_delivery.update_signal_message_status", update_status
        )

        await _delivery_task("+15551234567", "hello", "msg-1")

        update_status.assert_awaited_once_with("msg-1", SignalDeliveryStatus.DELIVERED)

    @pytest.mark.asyncio
    async def test_delivery_task_marks_message_failed_after_retries(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        update_status = AsyncMock()
        failing_delivery = AsyncMock(side_effect=TimeoutError("gateway timed out"))
        monkeypatch.setattr("src.services.signal_delivery._deliver_with_retry", failing_delivery)
        monkeypatch.setattr(
            "src.services.signal_delivery.update_signal_message_status", update_status
        )

        await _delivery_task("+15551234567", "hello", "msg-2")

        update_status.assert_awaited_once_with(
            "msg-2",
            SignalDeliveryStatus.FAILED,
            error_detail="gateway timed out",
        )


class TestDeliverChatMessageViaSignal:
    @pytest.mark.asyncio
    async def test_skips_when_connection_missing_or_disconnected(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        create_signal_message = AsyncMock()
        monkeypatch.setattr(
            "src.services.signal_delivery.get_connection_by_user", AsyncMock(return_value=None)
        )
        monkeypatch.setattr(
            "src.services.signal_delivery.create_signal_message", create_signal_message
        )

        await deliver_chat_message_via_signal("gh-user", _make_message())

        create_signal_message.assert_not_awaited()

        disconnected = SimpleNamespace(status=SignalConnectionStatus.DISCONNECTED)
        monkeypatch.setattr(
            "src.services.signal_delivery.get_connection_by_user",
            AsyncMock(return_value=disconnected),
        )

        await deliver_chat_message_via_signal("gh-user", _make_message())

        create_signal_message.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_skips_when_notification_preference_blocks_delivery(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        connection = SimpleNamespace(
            status=SignalConnectionStatus.CONNECTED,
            notification_mode=SignalNotificationMode.NONE,
        )
        create_signal_message = AsyncMock()
        monkeypatch.setattr(
            "src.services.signal_delivery.get_connection_by_user",
            AsyncMock(return_value=connection),
        )
        monkeypatch.setattr(
            "src.services.signal_delivery.create_signal_message", create_signal_message
        )

        await deliver_chat_message_via_signal("gh-user", _make_message())

        create_signal_message.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_skips_when_phone_decryption_fails(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from src.services import signal_bridge

        connection = SimpleNamespace(
            id="conn-1",
            status=SignalConnectionStatus.CONNECTED,
            notification_mode=SignalNotificationMode.ALL,
            signal_phone_encrypted="ciphertext",
        )
        encryption = Mock()
        encryption.decrypt.side_effect = ValueError("bad ciphertext")
        create_signal_message = AsyncMock()

        monkeypatch.setattr(
            "src.services.signal_delivery.get_connection_by_user",
            AsyncMock(return_value=connection),
        )
        monkeypatch.setattr(signal_bridge, "_get_encryption", Mock(return_value=encryption))
        monkeypatch.setattr(
            "src.services.signal_delivery.create_signal_message", create_signal_message
        )

        await deliver_chat_message_via_signal("gh-user", _make_message())

        create_signal_message.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_creates_audit_row_and_schedules_background_delivery(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        from src.services import signal_bridge

        connection = SimpleNamespace(
            id="conn-1",
            status=SignalConnectionStatus.CONNECTED,
            notification_mode=SignalNotificationMode.ALL,
            signal_phone_encrypted="ciphertext",
        )
        audit_row = SimpleNamespace(id="audit-1")
        encryption = Mock()
        encryption.decrypt.return_value = "+15551234567"
        create_signal_message = AsyncMock(return_value=audit_row)
        captured: dict[str, object] = {}

        class _TaskRegistry:
            def create_task(self, coro: object, *, name: str | None = None) -> None:
                captured["name"] = name
                captured["coro_name"] = getattr(coro, "cr_code", None).co_name
                coro.close()

        monkeypatch.setattr(
            "src.services.signal_delivery.get_connection_by_user",
            AsyncMock(return_value=connection),
        )
        monkeypatch.setattr(signal_bridge, "_get_encryption", Mock(return_value=encryption))
        monkeypatch.setattr(
            "src.services.signal_delivery.create_signal_message", create_signal_message
        )
        monkeypatch.setattr(
            "src.services.signal_delivery.get_settings",
            Mock(return_value=SimpleNamespace(frontend_url="https://solune.example")),
        )
        monkeypatch.setattr(
            "src.services.task_registry.task_registry",
            _TaskRegistry(),
        )

        message = _make_message(
            content="Please confirm this task.",
            action_type=ActionType.TASK_CREATE,
            action_data={"status": "pending", "proposed_title": "Ship coverage fix"},
        )

        await deliver_chat_message_via_signal(
            "gh-user",
            message,
            project_name="Solune",
            project_id="project-123",
        )

        create_signal_message.assert_awaited_once()
        _, kwargs = create_signal_message.await_args
        assert kwargs["connection_id"] == "conn-1"
        assert kwargs["delivery_status"] == SignalDeliveryStatus.PENDING
        assert kwargs["chat_message_id"] == str(message.message_id)
        assert kwargs["content_preview"].startswith("📋 *Task Proposal*")
        assert "Solune" in kwargs["content_preview"]
        assert captured == {
            "name": "signal-delivery-audit-1",
            "coro_name": "_delivery_task",
        }
