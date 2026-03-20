"""Tests for signal_chat.py helpers and control-flow branches."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock
from uuid import NAMESPACE_URL, uuid5

import pytest

from src.models.signal import SignalConnection, SignalConnectionStatus, SignalNotificationMode
from src.services import signal_chat
from src.services.signal_chat import _signal_session_id


def _connected_connection(**overrides) -> SignalConnection:
    defaults = {
        "id": "conn-1",
        "github_user_id": "12345",
        "signal_phone_encrypted": "encrypted-phone",
        "signal_phone_hash": "hash123",
        "status": SignalConnectionStatus.CONNECTED,
        "notification_mode": SignalNotificationMode.ALL,
        "linked_at": "2024-01-01T00:00:00",
    }
    defaults.update(overrides)
    return SignalConnection(**defaults)


class TestSignalSessionId:
    """_signal_session_id returns a deterministic UUID5 for a GitHub user id."""

    def test_returns_expected_uuid(self):
        expected = uuid5(NAMESPACE_URL, "signal:12345")
        assert _signal_session_id("12345") == expected

    def test_deterministic(self):
        """Same input always yields the same UUID."""
        assert _signal_session_id("abc") == _signal_session_id("abc")

    def test_different_ids_differ(self):
        assert _signal_session_id("user-a") != _signal_session_id("user-b")

    def test_empty_string(self):
        expected = uuid5(NAMESPACE_URL, "signal:")
        assert _signal_session_id("") == expected

    def test_return_type_is_uuid(self):
        from uuid import UUID

        result = _signal_session_id("test")
        assert isinstance(result, UUID)


class TestAccessTokenLookup:
    @pytest.mark.asyncio
    async def test_returns_none_when_no_sessions(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr("src.services.database.get_db", Mock(return_value=AsyncMock()))
        monkeypatch.setattr(
            "src.services.session_store.get_sessions_by_user", AsyncMock(return_value=[])
        )

        result = await signal_chat._get_user_access_token("12345")

        assert result is None

    @pytest.mark.asyncio
    async def test_returns_most_recent_session_token(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        sessions = [
            SimpleNamespace(updated_at=1, access_token="older-token"),
            SimpleNamespace(updated_at=3, access_token="newer-token"),
        ]
        monkeypatch.setattr("src.services.database.get_db", Mock(return_value=AsyncMock()))
        monkeypatch.setattr(
            "src.services.session_store.get_sessions_by_user",
            AsyncMock(return_value=sessions),
        )

        result = await signal_chat._get_user_access_token("12345")

        assert result == "newer-token"


class TestReplyHelpers:
    @pytest.mark.asyncio
    async def test_reply_swallows_send_errors(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            "src.services.signal_bridge.send_message",
            AsyncMock(side_effect=RuntimeError("send failed")),
        )

        await signal_chat._reply("+15551234567", "hello")

    @pytest.mark.asyncio
    async def test_reply_with_audit_marks_delivery_success(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        create_signal_message = AsyncMock(return_value=SimpleNamespace(id="audit-1"))
        send_message = AsyncMock()
        update_signal_message_status = AsyncMock()
        monkeypatch.setattr(
            "src.services.signal_bridge.create_signal_message", create_signal_message
        )
        monkeypatch.setattr("src.services.signal_bridge.send_message", send_message)
        monkeypatch.setattr(
            "src.services.signal_bridge.update_signal_message_status",
            update_signal_message_status,
        )

        conn = _connected_connection()
        await signal_chat._reply_with_audit(conn, "+15551234567", "hello")

        create_signal_message.assert_awaited_once()
        update_signal_message_status.assert_awaited_once_with(
            "audit-1", signal_chat.SignalDeliveryStatus.DELIVERED
        )

    @pytest.mark.asyncio
    async def test_reply_with_audit_marks_delivery_failed(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        create_signal_message = AsyncMock(return_value=SimpleNamespace(id="audit-2"))
        send_message = AsyncMock(side_effect=RuntimeError("gateway down"))
        update_signal_message_status = AsyncMock()
        monkeypatch.setattr(
            "src.services.signal_bridge.create_signal_message", create_signal_message
        )
        monkeypatch.setattr("src.services.signal_bridge.send_message", send_message)
        monkeypatch.setattr(
            "src.services.signal_bridge.update_signal_message_status",
            update_signal_message_status,
        )

        conn = _connected_connection()
        await signal_chat._reply_with_audit(conn, "+15551234567", "hello")

        update_signal_message_status.assert_awaited_once_with(
            "audit-2",
            signal_chat.SignalDeliveryStatus.FAILED,
            error_detail="gateway down",
        )


class TestProcessSignalChat:
    @pytest.fixture(autouse=True)
    def _clear_pending(self) -> None:
        signal_chat._signal_pending.clear()
        yield
        signal_chat._signal_pending.clear()

    @pytest.mark.asyncio
    async def test_confirm_word_routes_to_handle_confirm(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        conn = _connected_connection()
        signal_chat._signal_pending[conn.github_user_id] = {"type": "task_create"}
        handle_confirm = AsyncMock()
        monkeypatch.setattr(signal_chat, "_handle_confirm", handle_confirm)

        await signal_chat.process_signal_chat(conn, "CONFIRM", "project-1", "+15551234567")

        handle_confirm.assert_awaited_once_with(conn, "+15551234567", "project-1")

    @pytest.mark.asyncio
    async def test_reject_word_routes_to_handle_reject(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        conn = _connected_connection()
        signal_chat._signal_pending[conn.github_user_id] = {"type": "task_create"}
        handle_reject = AsyncMock()
        monkeypatch.setattr(signal_chat, "_handle_reject", handle_reject)

        await signal_chat.process_signal_chat(conn, "reject", "project-1", "+15551234567")

        handle_reject.assert_awaited_once_with(conn, "+15551234567")

    @pytest.mark.asyncio
    async def test_agent_command_requires_admin(self, monkeypatch: pytest.MonkeyPatch) -> None:
        conn = _connected_connection()
        monkeypatch.setattr(
            "src.services.agent_creator.get_active_session", Mock(return_value=None)
        )
        monkeypatch.setattr(
            "src.services.agent_creator.is_admin_user", AsyncMock(return_value=False)
        )
        monkeypatch.setattr("src.services.agent_creator.handle_agent_command", AsyncMock())
        monkeypatch.setattr("src.services.database.get_db", Mock(return_value=AsyncMock()))
        reply = AsyncMock()
        monkeypatch.setattr(signal_chat, "_reply", reply)

        await signal_chat.process_signal_chat(
            conn, "#agent create reviewer", "project-1", "+15551234567"
        )

        reply.assert_awaited_once()
        assert "restricted to admin users" in reply.await_args.args[1]

    @pytest.mark.asyncio
    async def test_agent_command_success_replies_with_audit(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        conn = _connected_connection()
        monkeypatch.setattr(
            "src.services.agent_creator.get_active_session", Mock(return_value=None)
        )
        monkeypatch.setattr(
            "src.services.agent_creator.is_admin_user", AsyncMock(return_value=True)
        )
        monkeypatch.setattr(
            "src.services.agent_creator.handle_agent_command",
            AsyncMock(return_value="Agent created"),
        )
        monkeypatch.setattr("src.services.database.get_db", Mock(return_value=AsyncMock()))
        monkeypatch.setattr(
            signal_chat, "_get_user_access_token", AsyncMock(return_value="token-1")
        )
        monkeypatch.setattr(
            "src.utils.resolve_repository", AsyncMock(return_value=("owner", "repo"))
        )
        reply_with_audit = AsyncMock()
        monkeypatch.setattr(signal_chat, "_reply_with_audit", reply_with_audit)

        await signal_chat.process_signal_chat(
            conn, "#agent create reviewer", "project-1", "+15551234567"
        )

        reply_with_audit.assert_awaited_once_with(conn, "+15551234567", "Agent created")

    @pytest.mark.asyncio
    async def test_agent_command_failure_returns_fallback_reply(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        conn = _connected_connection()
        monkeypatch.setattr(
            "src.services.agent_creator.get_active_session", Mock(return_value=None)
        )
        monkeypatch.setattr(
            "src.services.agent_creator.is_admin_user", AsyncMock(return_value=True)
        )
        monkeypatch.setattr(
            "src.services.agent_creator.handle_agent_command",
            AsyncMock(side_effect=RuntimeError("boom")),
        )
        monkeypatch.setattr("src.services.database.get_db", Mock(return_value=AsyncMock()))
        monkeypatch.setattr(
            signal_chat, "_get_user_access_token", AsyncMock(return_value="token-1")
        )
        monkeypatch.setattr(
            "src.utils.resolve_repository", AsyncMock(return_value=("owner", "repo"))
        )
        reply = AsyncMock()
        monkeypatch.setattr(signal_chat, "_reply", reply)

        await signal_chat.process_signal_chat(
            conn, "#agent create reviewer", "project-1", "+15551234567"
        )

        reply.assert_awaited_once()
        assert "went wrong processing your #agent command" in reply.await_args.args[1]

    @pytest.mark.asyncio
    async def test_non_agent_message_falls_back_to_ai_pipeline(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        conn = _connected_connection()
        monkeypatch.setattr(
            "src.services.agent_creator.get_active_session", Mock(return_value=None)
        )
        monkeypatch.setattr("src.services.agent_creator.handle_agent_command", AsyncMock())
        run_ai_pipeline = AsyncMock()
        monkeypatch.setattr(signal_chat, "_run_ai_pipeline", run_ai_pipeline)

        await signal_chat.process_signal_chat(
            conn, "please draft a task", "project-1", "+15551234567"
        )

        run_ai_pipeline.assert_awaited_once_with(
            conn, "please draft a task", "project-1", "+15551234567"
        )

    @pytest.mark.asyncio
    async def test_active_agent_session_continues_without_repository_metadata(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        conn = _connected_connection()
        monkeypatch.setattr(
            "src.services.agent_creator.get_active_session", Mock(return_value={"step": 1})
        )
        monkeypatch.setattr(
            "src.services.agent_creator.is_admin_user", AsyncMock(return_value=True)
        )
        handle_agent_command = AsyncMock(return_value="Agent session continued")
        monkeypatch.setattr("src.services.agent_creator.handle_agent_command", handle_agent_command)
        monkeypatch.setattr("src.services.database.get_db", Mock(return_value=AsyncMock()))
        monkeypatch.setattr(
            signal_chat, "_get_user_access_token", AsyncMock(return_value="token-1")
        )
        monkeypatch.setattr(
            "src.utils.resolve_repository", AsyncMock(side_effect=RuntimeError("no repo"))
        )
        reply_with_audit = AsyncMock()
        monkeypatch.setattr(signal_chat, "_reply_with_audit", reply_with_audit)

        await signal_chat.process_signal_chat(conn, "next", "project-1", "+15551234567")

        handle_agent_command.assert_awaited_once()
        assert handle_agent_command.await_args.kwargs["owner"] is None
        assert handle_agent_command.await_args.kwargs["repo"] is None
        reply_with_audit.assert_awaited_once()


class TestHandleReject:
    @pytest.fixture(autouse=True)
    def _clear_pending(self) -> None:
        signal_chat._signal_pending.clear()
        yield
        signal_chat._signal_pending.clear()

    @pytest.mark.asyncio
    async def test_no_pending_proposal_replies_immediately(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        reply = AsyncMock()
        monkeypatch.setattr(signal_chat, "_reply", reply)

        await signal_chat._handle_reject(_connected_connection(), "+15551234567")

        reply.assert_awaited_once_with("+15551234567", "No pending proposal to cancel.")

    @pytest.mark.asyncio
    async def test_reject_updates_statuses_and_replies_with_audit(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        conn = _connected_connection()
        signal_chat._signal_pending[conn.github_user_id] = {
            "proposal_id": "proposal-1",
            "recommendation_id": "rec-1",
        }
        proposal = SimpleNamespace(proposal_id="proposal-1", status=None)
        recommendation = Mock()
        recommendation.status = None
        recommendation.model_dump.return_value = {"title": "Improve coverage"}
        add_message = AsyncMock()
        get_proposal = AsyncMock(return_value=proposal)
        get_recommendation = AsyncMock(return_value=recommendation)
        update_proposal_status = AsyncMock()
        update_recommendation_status = AsyncMock()
        reply_with_audit = AsyncMock()

        monkeypatch.setattr("src.api.chat.add_message", add_message)
        monkeypatch.setattr("src.api.chat.get_proposal", get_proposal)
        monkeypatch.setattr("src.api.chat.get_recommendation", get_recommendation)
        monkeypatch.setattr("src.services.database.get_db", Mock(return_value=AsyncMock()))
        monkeypatch.setattr(
            "src.services.chat_store.update_proposal_status", update_proposal_status
        )
        monkeypatch.setattr(
            "src.services.chat_store.update_recommendation_status",
            update_recommendation_status,
        )
        monkeypatch.setattr(signal_chat, "_reply_with_audit", reply_with_audit)

        await signal_chat._handle_reject(conn, "+15551234567")

        update_proposal_status.assert_awaited_once()
        update_recommendation_status.assert_awaited_once()
        add_message.assert_awaited_once()
        reply_with_audit.assert_awaited_once()


class TestHandleConfirm:
    @pytest.fixture(autouse=True)
    def _clear_pending(self) -> None:
        signal_chat._signal_pending.clear()
        yield
        signal_chat._signal_pending.clear()

    @pytest.mark.asyncio
    async def test_no_pending_confirmation_replies_immediately(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        reply = AsyncMock()
        monkeypatch.setattr(signal_chat, "_reply", reply)

        await signal_chat._handle_confirm(_connected_connection(), "+15551234567", "project-1")

        reply.assert_awaited_once_with("+15551234567", "No pending proposal to confirm.")

    @pytest.mark.asyncio
    async def test_missing_token_restores_pending_confirmation(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        conn = _connected_connection()
        signal_chat._signal_pending[conn.github_user_id] = {
            "type": "task_create",
            "proposal_id": "proposal-1",
        }
        reply = AsyncMock()
        monkeypatch.setattr(signal_chat, "_get_user_access_token", AsyncMock(return_value=None))
        monkeypatch.setattr(signal_chat, "_reply", reply)

        await signal_chat._handle_confirm(conn, "+15551234567", "project-1")

        assert signal_chat._signal_pending[conn.github_user_id]["proposal_id"] == "proposal-1"
        reply.assert_awaited_once()
        assert "Session expired" in reply.await_args.args[1]


class TestRunAiPipeline:
    @pytest.fixture(autouse=True)
    def _clear_pending(self) -> None:
        signal_chat._signal_pending.clear()
        yield
        signal_chat._signal_pending.clear()

    @staticmethod
    def _project(name: str = "Project One") -> SimpleNamespace:
        return SimpleNamespace(
            project_id="project-1",
            name=name,
            status_columns=[SimpleNamespace(name="Backlog"), SimpleNamespace(name="In Progress")],
        )

    @pytest.mark.asyncio
    async def test_missing_session_token_prompts_user_to_log_in(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        reply = AsyncMock()
        monkeypatch.setattr(signal_chat, "_get_user_access_token", AsyncMock(return_value=None))
        monkeypatch.setattr(signal_chat, "_reply", reply)

        await signal_chat._run_ai_pipeline(
            _connected_connection(),
            "please add a task",
            "project-1",
            "+15551234567",
        )

        reply.assert_awaited_once()
        assert "web session has expired" in reply.await_args.args[1]

    @pytest.mark.asyncio
    async def test_ai_not_configured_returns_user_facing_reply(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        reply = AsyncMock()
        monkeypatch.setattr(
            signal_chat, "_get_user_access_token", AsyncMock(return_value="token-1")
        )
        monkeypatch.setattr(
            "src.services.ai_agent.get_ai_agent_service", Mock(side_effect=ValueError)
        )
        monkeypatch.setattr(signal_chat, "_reply", reply)

        await signal_chat._run_ai_pipeline(
            _connected_connection(),
            "please add a task",
            "project-1",
            "+15551234567",
        )

        reply.assert_awaited_once()
        assert "AI is not configured" in reply.await_args.args[1]

    @pytest.mark.asyncio
    async def test_feature_request_path_stores_recommendation_and_pending_state(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        conn = _connected_connection()
        ai_service = Mock()
        ai_service.detect_feature_request_intent = AsyncMock(return_value=True)
        ai_service.generate_issue_recommendation = AsyncMock(
            return_value=SimpleNamespace(
                recommendation_id="rec-1",
                title="Improve coverage dashboard",
                user_story="As a maintainer, I want clearer coverage reporting.",
                functional_requirements=["Show totals", "Highlight regressions"],
            )
        )
        cache = Mock()
        cache.get.side_effect = [[self._project()], []]
        add_message = AsyncMock()
        store_recommendation = AsyncMock()
        reply_with_audit = AsyncMock()

        monkeypatch.setattr(
            signal_chat, "_get_user_access_token", AsyncMock(return_value="token-1")
        )
        monkeypatch.setattr(
            "src.services.ai_agent.get_ai_agent_service", Mock(return_value=ai_service)
        )
        monkeypatch.setattr("src.services.cache.cache", cache)
        monkeypatch.setattr("src.api.chat.add_message", add_message)
        monkeypatch.setattr("src.api.chat.store_recommendation", store_recommendation)
        monkeypatch.setattr(signal_chat, "_reply_with_audit", reply_with_audit)

        await signal_chat._run_ai_pipeline(
            conn, "we need a better dashboard", "project-1", "+15551234567"
        )

        assert signal_chat._signal_pending[conn.github_user_id] == {
            "type": "issue_create",
            "recommendation_id": "rec-1",
            "project_id": "project-1",
        }
        store_recommendation.assert_awaited_once()
        add_message.assert_awaited_once()
        reply_with_audit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_status_change_path_handles_missing_task_match(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        conn = _connected_connection()
        ai_service = Mock()
        ai_service.detect_feature_request_intent = AsyncMock(return_value=False)
        ai_service.parse_status_change_request = AsyncMock(
            return_value=SimpleNamespace(task_reference="missing task", target_status="Done")
        )
        ai_service.identify_target_task = Mock(return_value=None)
        cache = Mock()
        cache.get.side_effect = [
            [self._project()],
            [SimpleNamespace(title="Existing", status="Backlog")],
        ]
        add_message = AsyncMock()
        reply_with_audit = AsyncMock()

        monkeypatch.setattr(
            signal_chat, "_get_user_access_token", AsyncMock(return_value="token-1")
        )
        monkeypatch.setattr(
            "src.services.ai_agent.get_ai_agent_service", Mock(return_value=ai_service)
        )
        monkeypatch.setattr("src.services.cache.cache", cache)
        monkeypatch.setattr("src.api.chat.add_message", add_message)
        monkeypatch.setattr(signal_chat, "_reply_with_audit", reply_with_audit)

        await signal_chat._run_ai_pipeline(
            conn, "move missing task to done", "project-1", "+15551234567"
        )

        add_message.assert_awaited_once()
        reply_with_audit.assert_awaited_once()
        assert conn.github_user_id not in signal_chat._signal_pending

    @pytest.mark.asyncio
    async def test_status_change_path_creates_pending_status_update_proposal(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        conn = _connected_connection()
        target_task = SimpleNamespace(title="Existing", status="Backlog", github_item_id="item-1")
        ai_service = Mock()
        ai_service.detect_feature_request_intent = AsyncMock(return_value=False)
        ai_service.parse_status_change_request = AsyncMock(
            return_value=SimpleNamespace(task_reference="Existing", target_status="Done")
        )
        ai_service.identify_target_task = Mock(return_value=target_task)
        cache = Mock()
        cache.get.side_effect = [[self._project()], [target_task]]
        add_message = AsyncMock()
        store_proposal = AsyncMock()
        reply_with_audit = AsyncMock()

        monkeypatch.setattr(
            signal_chat, "_get_user_access_token", AsyncMock(return_value="token-1")
        )
        monkeypatch.setattr(
            "src.services.ai_agent.get_ai_agent_service", Mock(return_value=ai_service)
        )
        monkeypatch.setattr("src.services.cache.cache", cache)
        monkeypatch.setattr("src.api.chat.add_message", add_message)
        monkeypatch.setattr("src.api.chat.store_proposal", store_proposal)
        monkeypatch.setattr(signal_chat, "_reply_with_audit", reply_with_audit)

        await signal_chat._run_ai_pipeline(
            conn, "move Existing to done", "project-1", "+15551234567"
        )

        assert signal_chat._signal_pending[conn.github_user_id]["type"] == "status_update"
        store_proposal.assert_awaited_once()
        add_message.assert_awaited_once()
        reply_with_audit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_feature_detection_errors_fall_back_to_task_generation(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        conn = _connected_connection()
        ai_service = Mock()
        ai_service.detect_feature_request_intent = AsyncMock(
            side_effect=RuntimeError("parse failed")
        )
        ai_service.parse_status_change_request = AsyncMock(return_value=None)
        ai_service.generate_task_from_description = AsyncMock(
            return_value=SimpleNamespace(
                title="Write fallback tests", description="Cover the fallback path."
            )
        )
        cache = Mock()
        cache.get.side_effect = [[self._project()], []]
        add_message = AsyncMock()
        store_proposal = AsyncMock()
        reply_with_audit = AsyncMock()

        monkeypatch.setattr(
            signal_chat, "_get_user_access_token", AsyncMock(return_value="token-1")
        )
        monkeypatch.setattr(
            "src.services.ai_agent.get_ai_agent_service", Mock(return_value=ai_service)
        )
        monkeypatch.setattr("src.services.cache.cache", cache)
        monkeypatch.setattr("src.api.chat.add_message", add_message)
        monkeypatch.setattr("src.api.chat.store_proposal", store_proposal)
        monkeypatch.setattr(signal_chat, "_reply_with_audit", reply_with_audit)

        await signal_chat._run_ai_pipeline(
            conn, "write fallback tests", "project-1", "+15551234567"
        )

        store_proposal.assert_awaited_once()
        reply_with_audit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_task_generation_path_creates_pending_task_proposal(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        conn = _connected_connection()
        ai_service = Mock()
        ai_service.detect_feature_request_intent = AsyncMock(return_value=False)
        ai_service.parse_status_change_request = AsyncMock(return_value=None)
        ai_service.generate_task_from_description = AsyncMock(
            return_value=SimpleNamespace(
                title="Write regression tests",
                description="Cover the remaining workflow edge cases.",
            )
        )
        cache = Mock()
        cache.get.side_effect = [[self._project()], []]
        add_message = AsyncMock()
        store_proposal = AsyncMock()
        reply_with_audit = AsyncMock()

        monkeypatch.setattr(
            signal_chat, "_get_user_access_token", AsyncMock(return_value="token-1")
        )
        monkeypatch.setattr(
            "src.services.ai_agent.get_ai_agent_service", Mock(return_value=ai_service)
        )
        monkeypatch.setattr("src.services.cache.cache", cache)
        monkeypatch.setattr("src.api.chat.add_message", add_message)
        monkeypatch.setattr("src.api.chat.store_proposal", store_proposal)
        monkeypatch.setattr(signal_chat, "_reply_with_audit", reply_with_audit)

        await signal_chat._run_ai_pipeline(conn, "write more tests", "project-1", "+15551234567")

        assert signal_chat._signal_pending[conn.github_user_id]["type"] == "task_create"
        store_proposal.assert_awaited_once()
        add_message.assert_awaited_once()
        reply_with_audit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_pipeline_failure_adds_error_message_and_reply(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        conn = _connected_connection()
        ai_service = Mock()
        ai_service.detect_feature_request_intent = AsyncMock(return_value=False)
        ai_service.parse_status_change_request = AsyncMock(return_value=None)
        ai_service.generate_task_from_description = AsyncMock(side_effect=RuntimeError("boom"))
        cache = Mock()
        cache.get.side_effect = [[self._project()], []]
        add_message = AsyncMock()
        reply = AsyncMock()

        monkeypatch.setattr(
            signal_chat, "_get_user_access_token", AsyncMock(return_value="token-1")
        )
        monkeypatch.setattr(
            "src.services.ai_agent.get_ai_agent_service", Mock(return_value=ai_service)
        )
        monkeypatch.setattr("src.services.cache.cache", cache)
        monkeypatch.setattr("src.api.chat.add_message", add_message)
        monkeypatch.setattr(signal_chat, "_reply", reply)

        await signal_chat._run_ai_pipeline(conn, "write more tests", "project-1", "+15551234567")

        add_message.assert_awaited_once()
        reply.assert_awaited_once()
        assert "couldn't process your message" in reply.await_args.args[1]


class TestRunWorkflowOrchestration:
    @pytest.mark.asyncio
    async def test_successfully_bootstraps_pipeline_and_assigns_first_agent(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        config = SimpleNamespace(
            project_id="project-1",
            repository_owner="octo",
            repository_name="repo",
            copilot_assignee="copilot-swe-agent",
            status_backlog="Backlog",
            agent_mappings={},
        )
        orchestrator = SimpleNamespace(
            create_all_sub_issues=AsyncMock(return_value={"planner": {"number": 10}}),
            assign_agent_for_status=AsyncMock(return_value=True),
        )
        set_pipeline_state = Mock()
        set_workflow_config = AsyncMock()
        ensure_polling_started = AsyncMock()
        update_item_status_by_name = AsyncMock()

        monkeypatch.setattr(
            "src.config.get_settings",
            Mock(return_value=SimpleNamespace(default_assignee="copilot-swe-agent")),
        )
        monkeypatch.setattr(
            "src.services.copilot_polling.ensure_polling_started", ensure_polling_started
        )
        monkeypatch.setattr(
            "src.services.github_projects.github_projects_service.update_item_status_by_name",
            update_item_status_by_name,
        )
        monkeypatch.setattr(
            "src.services.workflow_orchestrator.get_workflow_config", AsyncMock(return_value=None)
        )
        monkeypatch.setattr(
            "src.services.workflow_orchestrator.set_workflow_config", set_workflow_config
        )
        monkeypatch.setattr(
            "src.services.workflow_orchestrator.get_workflow_orchestrator",
            Mock(return_value=orchestrator),
        )
        monkeypatch.setattr(
            "src.services.workflow_orchestrator.get_agent_slugs", Mock(return_value=["planner"])
        )
        monkeypatch.setattr(
            "src.services.workflow_orchestrator.set_pipeline_state", set_pipeline_state
        )
        monkeypatch.setattr(
            "src.services.workflow_orchestrator.config.load_user_agent_mappings",
            AsyncMock(return_value={"Backlog": [SimpleNamespace(slug="planner")]}),
        )
        monkeypatch.setattr("src.models.workflow.WorkflowConfiguration", Mock(return_value=config))
        monkeypatch.setattr("src.utils.utcnow", Mock(return_value="now"))

        result = await signal_chat._run_workflow_orchestration(
            token="token-1",
            project_id="project-1",
            owner="octo",
            repo="repo",
            issue_number=7,
            issue_node_id="node-7",
            item_id="item-7",
            session_id=_signal_session_id("12345"),
            github_user_id="12345",
        )

        assert result == {"sub_issues": 1, "agent": "planner", "error": None}
        set_workflow_config.assert_awaited()
        set_pipeline_state.assert_called_once()
        orchestrator.assign_agent_for_status.assert_awaited_once()
        ensure_polling_started.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_workflow_orchestration_returns_error_summary_on_exception(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr("src.config.get_settings", Mock(side_effect=RuntimeError("boom")))

        result = await signal_chat._run_workflow_orchestration(
            token="token-1",
            project_id="project-1",
            owner="octo",
            repo="repo",
            issue_number=7,
            issue_node_id="node-7",
            item_id="item-7",
            session_id=_signal_session_id("12345"),
        )

        assert result["sub_issues"] == 0
        assert result["agent"] is None
        assert result["error"] == "boom"

    @pytest.mark.asyncio
    async def test_existing_config_without_subissues_still_starts_polling(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        config = SimpleNamespace(
            project_id="project-1",
            repository_owner="",
            repository_name="",
            copilot_assignee="",
            status_backlog="Backlog",
            agent_mappings={},
        )
        orchestrator = SimpleNamespace(
            create_all_sub_issues=AsyncMock(return_value={}),
            assign_agent_for_status=AsyncMock(return_value=True),
        )
        ensure_polling_started = AsyncMock()

        monkeypatch.setattr(
            "src.config.get_settings",
            Mock(return_value=SimpleNamespace(default_assignee="copilot-swe-agent")),
        )
        monkeypatch.setattr(
            "src.services.copilot_polling.ensure_polling_started", ensure_polling_started
        )
        monkeypatch.setattr(
            "src.services.github_projects.github_projects_service.update_item_status_by_name",
            AsyncMock(),
        )
        monkeypatch.setattr(
            "src.services.workflow_orchestrator.get_workflow_config", AsyncMock(return_value=config)
        )
        monkeypatch.setattr(
            "src.services.workflow_orchestrator.get_workflow_orchestrator",
            Mock(return_value=orchestrator),
        )
        monkeypatch.setattr(
            "src.services.workflow_orchestrator.get_agent_slugs", Mock(return_value=[])
        )
        monkeypatch.setattr(
            "src.services.workflow_orchestrator.config.load_user_agent_mappings",
            AsyncMock(return_value=None),
        )

        result = await signal_chat._run_workflow_orchestration(
            token="token-1",
            project_id="project-1",
            owner="octo",
            repo="repo",
            issue_number=7,
            issue_node_id="node-7",
            item_id="item-7",
            session_id=_signal_session_id("12345"),
            github_user_id="12345",
        )

        assert result == {"sub_issues": 0, "agent": None, "error": None}
        assert config.repository_owner == "octo"
        assert config.repository_name == "repo"
        assert config.copilot_assignee == "copilot-swe-agent"
        ensure_polling_started.assert_awaited_once()


class TestHandleConfirmExecution:
    @pytest.fixture(autouse=True)
    def _clear_pending(self) -> None:
        signal_chat._signal_pending.clear()
        yield
        signal_chat._signal_pending.clear()

    @pytest.mark.asyncio
    async def test_issue_create_confirmation_creates_issue_and_records_confirmation(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        conn = _connected_connection()
        recommendation = Mock(
            title="Improve coverage dashboard",
            user_story="As a maintainer, I want clearer coverage reporting.",
            functional_requirements=["Show totals", "Highlight regressions"],
            technical_notes="Render branch deltas.",
        )
        recommendation.model_dump.return_value = {"title": recommendation.title}
        signal_chat._signal_pending[conn.github_user_id] = {
            "type": "issue_create",
            "recommendation_id": "rec-1",
            "project_id": "project-1",
        }
        gh = SimpleNamespace(
            create_issue=AsyncMock(
                return_value={
                    "number": 8,
                    "node_id": "node-8",
                    "id": 88,
                    "html_url": "https://example.test/issues/8",
                }
            ),
            add_issue_to_project=AsyncMock(return_value="item-8"),
        )
        cache = Mock()
        add_message = AsyncMock()
        reply_with_audit = AsyncMock()
        update_recommendation_status = AsyncMock()

        monkeypatch.setattr(
            signal_chat, "_get_user_access_token", AsyncMock(return_value="token-1")
        )
        monkeypatch.setattr(
            "src.utils.resolve_repository", AsyncMock(return_value=("octo", "repo"))
        )
        monkeypatch.setattr("src.utils.utcnow", Mock(return_value="now"))
        monkeypatch.setattr("src.api.chat.add_message", add_message)
        monkeypatch.setattr(
            "src.api.chat.get_recommendation", AsyncMock(return_value=recommendation)
        )
        monkeypatch.setattr("src.services.github_projects.github_projects_service", gh)
        monkeypatch.setattr("src.services.cache.cache", cache)
        monkeypatch.setattr(
            "src.services.cache.get_project_items_cache_key", Mock(return_value="project-cache")
        )
        monkeypatch.setattr(
            signal_chat,
            "_run_workflow_orchestration",
            AsyncMock(return_value={"sub_issues": 2, "agent": "planner", "error": "partial"}),
        )
        monkeypatch.setattr("src.services.database.get_db", Mock(return_value=AsyncMock()))
        monkeypatch.setattr(
            "src.services.chat_store.update_recommendation_status", update_recommendation_status
        )
        monkeypatch.setattr(signal_chat, "_reply_with_audit", reply_with_audit)

        await signal_chat._handle_confirm(conn, "+15551234567", "project-1")

        gh.create_issue.assert_awaited_once()
        update_recommendation_status.assert_awaited_once()
        add_message.assert_awaited_once()
        reply_with_audit.assert_awaited_once()
        cache.delete.assert_called_once_with("project-cache")

    @pytest.mark.asyncio
    async def test_task_create_confirmation_creates_issue_and_updates_proposal(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        conn = _connected_connection()
        proposal = SimpleNamespace(
            proposal_id="proposal-1",
            final_title="Add workflow alerts",
            final_description="Notify owners when pipelines stall.",
            edited_title="Edited title",
            edited_description="Edited description",
            status=None,
        )
        signal_chat._signal_pending[conn.github_user_id] = {
            "type": "task_create",
            "proposal_id": "proposal-1",
            "project_id": "project-1",
        }
        gh = SimpleNamespace(
            create_issue=AsyncMock(
                return_value={
                    "number": 9,
                    "node_id": "node-9",
                    "id": 99,
                    "html_url": "https://example.test/issues/9",
                }
            ),
            add_issue_to_project=AsyncMock(return_value="item-9"),
        )
        cache = Mock()
        add_message = AsyncMock()
        reply_with_audit = AsyncMock()
        update_proposal_status = AsyncMock()

        monkeypatch.setattr(
            signal_chat, "_get_user_access_token", AsyncMock(return_value="token-1")
        )
        monkeypatch.setattr(
            "src.utils.resolve_repository", AsyncMock(return_value=("octo", "repo"))
        )
        monkeypatch.setattr("src.api.chat.add_message", add_message)
        monkeypatch.setattr("src.api.chat.get_proposal", AsyncMock(return_value=proposal))
        monkeypatch.setattr("src.services.github_projects.github_projects_service", gh)
        monkeypatch.setattr("src.services.cache.cache", cache)
        monkeypatch.setattr(
            "src.services.cache.get_project_items_cache_key", Mock(return_value="project-cache")
        )
        monkeypatch.setattr(
            signal_chat,
            "_run_workflow_orchestration",
            AsyncMock(return_value={"sub_issues": 1, "agent": "builder", "error": None}),
        )
        monkeypatch.setattr("src.services.database.get_db", Mock(return_value=AsyncMock()))
        monkeypatch.setattr(
            "src.services.chat_store.update_proposal_status", update_proposal_status
        )
        monkeypatch.setattr(signal_chat, "_reply_with_audit", reply_with_audit)

        await signal_chat._handle_confirm(conn, "+15551234567", "project-1")

        gh.create_issue.assert_awaited_once()
        update_proposal_status.assert_awaited_once()
        add_message.assert_awaited_once()
        reply_with_audit.assert_awaited_once()
        cache.delete.assert_called_once_with("project-cache")

    @pytest.mark.asyncio
    async def test_issue_create_confirmation_replies_when_recommendation_expired(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        conn = _connected_connection()
        signal_chat._signal_pending[conn.github_user_id] = {
            "type": "issue_create",
            "recommendation_id": "rec-missing",
        }
        reply = AsyncMock()

        monkeypatch.setattr(
            signal_chat, "_get_user_access_token", AsyncMock(return_value="token-1")
        )
        monkeypatch.setattr(
            "src.utils.resolve_repository", AsyncMock(return_value=("octo", "repo"))
        )
        monkeypatch.setattr("src.api.chat.get_recommendation", AsyncMock(return_value=None))
        monkeypatch.setattr(signal_chat, "_reply", reply)

        await signal_chat._handle_confirm(conn, "+15551234567", "project-1")

        reply.assert_awaited_once()
        assert "Proposal expired" in reply.await_args.args[1]

    @pytest.mark.asyncio
    async def test_status_update_confirmation_replies_when_proposal_expired(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        conn = _connected_connection()
        signal_chat._signal_pending[conn.github_user_id] = {
            "type": "status_update",
            "proposal_id": "proposal-missing",
            "target_status": "Done",
            "task_id": "item-1",
        }
        reply = AsyncMock()

        monkeypatch.setattr(
            signal_chat, "_get_user_access_token", AsyncMock(return_value="token-1")
        )
        monkeypatch.setattr(
            "src.utils.resolve_repository", AsyncMock(return_value=("octo", "repo"))
        )
        monkeypatch.setattr("src.api.chat.get_proposal", AsyncMock(return_value=None))
        monkeypatch.setattr(signal_chat, "_reply", reply)

        await signal_chat._handle_confirm(conn, "+15551234567", "project-1")

        reply.assert_awaited_once()
        assert "Proposal expired" in reply.await_args.args[1]

    @pytest.mark.asyncio
    async def test_status_update_confirmation_updates_project_item_and_replies(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        conn = _connected_connection()
        proposal = SimpleNamespace(
            proposal_id="proposal-2",
            edited_title="Edited title",
            edited_description="Edited description",
            status=None,
        )
        signal_chat._signal_pending[conn.github_user_id] = {
            "type": "status_update",
            "proposal_id": "proposal-2",
            "project_id": "project-1",
            "task_id": "item-10",
            "task_title": "Document recovery flow",
            "target_status": "Done",
        }
        gh = SimpleNamespace(update_item_status_by_name=AsyncMock())
        cache = Mock()
        add_message = AsyncMock()
        reply_with_audit = AsyncMock()
        update_proposal_status = AsyncMock()

        monkeypatch.setattr(
            signal_chat, "_get_user_access_token", AsyncMock(return_value="token-1")
        )
        monkeypatch.setattr(
            "src.utils.resolve_repository", AsyncMock(return_value=("octo", "repo"))
        )
        monkeypatch.setattr("src.api.chat.add_message", add_message)
        monkeypatch.setattr("src.api.chat.get_proposal", AsyncMock(return_value=proposal))
        monkeypatch.setattr("src.services.github_projects.github_projects_service", gh)
        monkeypatch.setattr("src.services.cache.cache", cache)
        monkeypatch.setattr(
            "src.services.cache.get_project_items_cache_key", Mock(return_value="project-cache")
        )
        monkeypatch.setattr("src.services.database.get_db", Mock(return_value=AsyncMock()))
        monkeypatch.setattr(
            "src.services.chat_store.update_proposal_status", update_proposal_status
        )
        monkeypatch.setattr(signal_chat, "_reply_with_audit", reply_with_audit)

        await signal_chat._handle_confirm(conn, "+15551234567", "project-1")

        gh.update_item_status_by_name.assert_awaited_once()
        update_proposal_status.assert_awaited_once()
        add_message.assert_awaited_once()
        reply_with_audit.assert_awaited_once()
        cache.delete.assert_called_once_with("project-cache")
