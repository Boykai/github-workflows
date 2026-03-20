"""Edge-case tests for the Signal bridge service."""

from __future__ import annotations

import base64
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, Mock

import pytest

from src.models.signal import (
    SignalConflictBanner,
    SignalConnection,
    SignalConnectionStatus,
    SignalDeliveryStatus,
    SignalMessageDirection,
    SignalNotificationMode,
)
from src.services import signal_bridge


def _connected_connection(**overrides) -> SignalConnection:
    defaults = {
        "id": "conn-1",
        "github_user_id": "user-1",
        "signal_phone_encrypted": "ciphertext",
        "signal_phone_hash": "hash-1",
        "status": SignalConnectionStatus.CONNECTED,
        "notification_mode": SignalNotificationMode.ALL,
        "linked_at": "2024-01-01T00:00:00+00:00",
    }
    defaults.update(overrides)
    return SignalConnection(**defaults)


def _mock_async_client(*, get_response=None, post_response=None) -> AsyncMock:
    client = AsyncMock()
    client.get = AsyncMock(return_value=get_response)
    client.post = AsyncMock(return_value=post_response)
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=False)
    return client


class TestSignalBridgeHelpers:
    @pytest.mark.asyncio
    async def test_request_qr_code_base64_encodes_png_bytes(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(signal_bridge, "request_qr_code", AsyncMock(return_value=b"png-bytes"))

        result = await signal_bridge.request_qr_code_base64("Solune")

        assert result == base64.b64encode(b"png-bytes").decode()

    @pytest.mark.asyncio
    async def test_get_registered_phone_prefers_configured_phone(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(
            signal_bridge,
            "get_settings",
            Mock(return_value=SimpleNamespace(signal_phone_number="+15550001111")),
        )

        result = await signal_bridge._get_registered_phone()

        assert result == "+15550001111"

    @pytest.mark.asyncio
    async def test_get_registered_phone_falls_back_to_accounts(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(
            signal_bridge,
            "get_settings",
            Mock(return_value=SimpleNamespace(signal_phone_number="")),
        )
        monkeypatch.setattr(signal_bridge, "get_accounts", AsyncMock(return_value=["+15550002222"]))

        result = await signal_bridge._get_registered_phone()

        assert result == "+15550002222"

    @pytest.mark.asyncio
    async def test_get_registered_phone_returns_none_when_account_lookup_fails(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(
            signal_bridge,
            "get_settings",
            Mock(return_value=SimpleNamespace(signal_phone_number="")),
        )
        monkeypatch.setattr(
            signal_bridge,
            "get_accounts",
            AsyncMock(side_effect=RuntimeError("sidecar offline")),
        )

        result = await signal_bridge._get_registered_phone()

        assert result is None

    @pytest.mark.asyncio
    async def test_check_link_complete_requires_configured_phone_when_present(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        response = MagicMock()
        response.raise_for_status = MagicMock()
        response.json.return_value = ["+15550003333"]
        client = _mock_async_client(get_response=response)

        monkeypatch.setattr(signal_bridge.httpx, "AsyncClient", Mock(return_value=client))
        monkeypatch.setattr(
            signal_bridge,
            "get_settings",
            Mock(
                return_value=SimpleNamespace(
                    signal_api_url="http://signal:8080",
                    signal_phone_number="+15550004444",
                )
            ),
        )

        result = await signal_bridge.check_link_complete()

        assert result == {"linked": False, "number": None}


class TestSignalBridgeDatabaseHelpers:
    @pytest.mark.asyncio
    async def test_get_connection_by_user_returns_connection(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        cursor = AsyncMock()
        cursor.fetchone = AsyncMock(return_value=_connected_connection().model_dump())
        db = AsyncMock()
        db.execute = AsyncMock(return_value=cursor)
        monkeypatch.setattr(signal_bridge, "get_db", Mock(return_value=db))

        result = await signal_bridge.get_connection_by_user("user-1")

        assert isinstance(result, SignalConnection)
        assert result.github_user_id == "user-1"

    @pytest.mark.asyncio
    async def test_create_connection_handles_phone_conflict_and_relink(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        existing = _connected_connection(id="old-conn", github_user_id="other-user")
        db = AsyncMock()
        db.execute = AsyncMock()
        db.commit = AsyncMock()
        encryption = Mock()
        encryption.encrypt.return_value = "encrypted-phone"

        monkeypatch.setattr(signal_bridge, "get_db", Mock(return_value=db))
        monkeypatch.setattr(signal_bridge, "_get_encryption", Mock(return_value=encryption))
        monkeypatch.setattr(
            signal_bridge,
            "get_connection_by_phone_hash",
            AsyncMock(return_value=existing),
        )

        conn = await signal_bridge.create_connection("user-1", "+15551234567")

        assert conn.github_user_id == "user-1"
        assert conn.status == SignalConnectionStatus.CONNECTED
        assert conn.signal_phone_encrypted == "encrypted-phone"
        assert db.commit.await_count == 2
        executed_sql = [call.args[0] for call in db.execute.await_args_list]
        assert any(
            "UPDATE signal_connections SET status = 'disconnected'" in sql for sql in executed_sql
        )
        assert any("INSERT INTO signal_conflict_banners" in sql for sql in executed_sql)
        assert any(
            "DELETE FROM signal_connections WHERE github_user_id = ?" in sql for sql in executed_sql
        )

    @pytest.mark.asyncio
    async def test_disconnect_and_purge_returns_true_when_row_deleted(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        cursor = SimpleNamespace(rowcount=1)
        db = AsyncMock()
        db.execute = AsyncMock(return_value=cursor)
        db.commit = AsyncMock()
        monkeypatch.setattr(signal_bridge, "get_db", Mock(return_value=db))

        result = await signal_bridge.disconnect_and_purge("user-1")

        assert result is True

    @pytest.mark.asyncio
    async def test_get_banners_for_user_builds_models(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        banner = SignalConflictBanner(github_user_id="user-1", message="Conflict")
        cursor = AsyncMock()
        cursor.fetchall = AsyncMock(return_value=[banner.model_dump()])
        db = AsyncMock()
        db.execute = AsyncMock(return_value=cursor)
        monkeypatch.setattr(signal_bridge, "get_db", Mock(return_value=db))

        result = await signal_bridge.get_banners_for_user("user-1")

        assert len(result) == 1
        assert result[0].message == "Conflict"

    @pytest.mark.asyncio
    async def test_dismiss_banner_reports_update_result(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        cursor = SimpleNamespace(rowcount=0)
        db = AsyncMock()
        db.execute = AsyncMock(return_value=cursor)
        db.commit = AsyncMock()
        monkeypatch.setattr(signal_bridge, "get_db", Mock(return_value=db))

        result = await signal_bridge.dismiss_banner("banner-1", "user-1")

        assert result is False

    @pytest.mark.asyncio
    async def test_create_signal_message_truncates_content_preview(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        db = AsyncMock()
        db.execute = AsyncMock()
        db.commit = AsyncMock()
        monkeypatch.setattr(signal_bridge, "get_db", Mock(return_value=db))

        message = await signal_bridge.create_signal_message(
            connection_id="conn-1",
            direction=SignalMessageDirection.OUTBOUND,
            chat_message_id="chat-1",
            content_preview="x" * 300,
        )

        assert message.content_preview == "x" * 200
        params = db.execute.await_args.args[1]
        assert params[4] == "x" * 200

    @pytest.mark.asyncio
    async def test_update_signal_message_status_sets_delivered_timestamp(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        db = AsyncMock()
        db.execute = AsyncMock()
        db.commit = AsyncMock()
        monkeypatch.setattr(signal_bridge, "get_db", Mock(return_value=db))

        await signal_bridge.update_signal_message_status("msg-1", SignalDeliveryStatus.DELIVERED)

        params = db.execute.await_args.args[1]
        assert params[0] == SignalDeliveryStatus.DELIVERED.value
        assert params[3] is not None

    @pytest.mark.asyncio
    async def test_store_inbound_message_creates_chat_and_audit_rows(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        add_message = AsyncMock()
        create_signal_message = AsyncMock()
        monkeypatch.setattr("src.api.chat.add_message", add_message)
        monkeypatch.setattr(signal_bridge, "create_signal_message", create_signal_message)

        conn = _connected_connection()
        message_id = await signal_bridge.store_inbound_message(conn, "hello from signal", "proj-1")

        add_message.assert_awaited_once()
        create_signal_message.assert_awaited_once()
        _, kwargs = create_signal_message.await_args
        assert kwargs["connection_id"] == conn.id
        assert kwargs["direction"] == SignalMessageDirection.INBOUND
        assert kwargs["delivery_status"] == SignalDeliveryStatus.DELIVERED
        assert kwargs["chat_message_id"] == message_id


class TestSignalBridgeListenerAndInboundRouting:
    @pytest.mark.asyncio
    async def test_start_signal_ws_listener_skips_when_already_running(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        existing_task = Mock()
        existing_task.done.return_value = False
        monkeypatch.setattr(signal_bridge, "_ws_listener_task", existing_task)
        get_phone = AsyncMock()
        monkeypatch.setattr(signal_bridge, "_get_registered_phone", get_phone)

        await signal_bridge.start_signal_ws_listener()

        get_phone.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_start_signal_ws_listener_creates_background_task(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        created: dict[str, object] = {}

        class _TaskRegistry:
            def create_task(self, coro: object, *, name: str | None = None) -> str:
                created["name"] = name
                created["coro_name"] = getattr(coro, "cr_code", None).co_name
                coro.close()
                return "task-handle"

        monkeypatch.setattr(signal_bridge, "_ws_listener_task", None)
        monkeypatch.setattr(
            signal_bridge, "_get_registered_phone", AsyncMock(return_value="+15550005555")
        )
        monkeypatch.setattr("src.services.task_registry.task_registry", _TaskRegistry())

        await signal_bridge.start_signal_ws_listener()

        assert signal_bridge._ws_listener_task == "task-handle"
        assert created == {"name": "signal-ws-listener", "coro_name": "_ws_listen_loop"}
        signal_bridge._ws_listener_task = None

    @pytest.mark.asyncio
    async def test_process_inbound_ws_message_ignores_attachment_without_text(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        send_auto_reply = AsyncMock()
        store_inbound_message = AsyncMock()
        monkeypatch.setattr(signal_bridge, "_send_auto_reply", send_auto_reply)
        monkeypatch.setattr(signal_bridge, "store_inbound_message", store_inbound_message)

        payload = {
            "envelope": {
                "source": "+15551234567",
                "syncMessage": {
                    "sentMessage": {
                        "destination": "+15551234567",
                        "attachments": [{"contentType": "image/png"}],
                        "message": "",
                    }
                },
            }
        }

        await signal_bridge._process_inbound_ws_message(payload)

        send_auto_reply.assert_awaited_once()
        store_inbound_message.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_process_inbound_ws_message_prompts_for_project_tag_when_multiple_projects(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        send_auto_reply = AsyncMock()
        task_registry_calls: dict[str, object] = {}

        class _TaskRegistry:
            def create_task(self, coro: object, *, name: str | None = None) -> None:
                task_registry_calls["name"] = name
                coro.close()

        monkeypatch.setattr(
            signal_bridge,
            "get_connection_by_phone_hash",
            AsyncMock(return_value=_connected_connection(last_active_project_id=None)),
        )
        monkeypatch.setattr(signal_bridge, "_send_auto_reply", send_auto_reply)
        monkeypatch.setattr(
            signal_bridge,
            "_list_user_projects",
            AsyncMock(return_value=[("Alpha Project", "p1"), ("Beta Project", "p2")]),
        )
        monkeypatch.setattr("src.services.task_registry.task_registry", _TaskRegistry())

        payload = {
            "envelope": {
                "source": "+15551234567",
                "syncMessage": {
                    "sentMessage": {
                        "destination": "+15551234567",
                        "message": "Ship the fix",
                    }
                },
            }
        }

        await signal_bridge._process_inbound_ws_message(payload)

        send_auto_reply.assert_awaited_once()
        assert "#alpha-project" in send_auto_reply.await_args.args[1]
        assert task_registry_calls == {}

    @pytest.mark.asyncio
    async def test_process_inbound_ws_message_autoselects_single_project_and_queues_ai_processing(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        conn = _connected_connection(last_active_project_id=None)
        send_auto_reply = AsyncMock()
        update_last_active_project = AsyncMock()
        store_inbound_message = AsyncMock(return_value="chat-1")
        captured: dict[str, object] = {}

        class _TaskRegistry:
            def create_task(self, coro: object, *, name: str | None = None) -> None:
                captured["name"] = name
                captured["coro_name"] = getattr(coro, "cr_code", None).co_name
                coro.close()

        monkeypatch.setattr(
            signal_bridge,
            "get_connection_by_phone_hash",
            AsyncMock(return_value=conn),
        )
        monkeypatch.setattr(
            signal_bridge,
            "_list_user_projects",
            AsyncMock(return_value=[("Solo Project", "project-1")]),
        )
        monkeypatch.setattr(signal_bridge, "_send_auto_reply", send_auto_reply)
        monkeypatch.setattr(signal_bridge, "update_last_active_project", update_last_active_project)
        monkeypatch.setattr(signal_bridge, "store_inbound_message", store_inbound_message)
        monkeypatch.setattr("src.services.task_registry.task_registry", _TaskRegistry())

        payload = {
            "envelope": {
                "source": "+15551234567",
                "syncMessage": {
                    "sentMessage": {
                        "destination": "+15551234567",
                        "message": "Run the release checklist",
                    }
                },
            }
        }

        await signal_bridge._process_inbound_ws_message(payload)

        update_last_active_project.assert_awaited_once_with(conn.github_user_id, "project-1")
        store_inbound_message.assert_awaited_once_with(
            conn, "Run the release checklist", "project-1"
        )
        send_auto_reply.assert_awaited_once()
        assert captured == {"name": "signal-ai-process", "coro_name": "_safe_process"}

    @pytest.mark.asyncio
    async def test_resolve_project_by_name_returns_none_on_lookup_error(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(
            signal_bridge,
            "_list_user_projects",
            AsyncMock(side_effect=RuntimeError("cache failure")),
        )

        result = await signal_bridge._resolve_project_by_name("user-1", "alpha-project")

        assert result is None

    @pytest.mark.asyncio
    async def test_list_user_projects_returns_cached_entries(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        cached = [SimpleNamespace(name="Alpha", project_id="p1")]
        cache = Mock()
        cache.get.return_value = cached
        monkeypatch.setattr("src.services.cache.cache", cache)
        monkeypatch.setattr(
            "src.services.cache.get_user_projects_cache_key",
            Mock(return_value="projects:user-1"),
        )

        result = await signal_bridge._list_user_projects("user-1")

        assert result == [("Alpha", "p1")]

    @pytest.mark.asyncio
    async def test_list_user_projects_returns_empty_without_sessions(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        cache = Mock()
        cache.get.return_value = None
        monkeypatch.setattr("src.services.cache.cache", cache)
        monkeypatch.setattr(
            "src.services.cache.get_user_projects_cache_key",
            Mock(return_value="projects:user-1"),
        )
        monkeypatch.setattr("src.services.database.get_db", Mock(return_value=AsyncMock()))
        monkeypatch.setattr(
            "src.services.session_store.get_sessions_by_user", AsyncMock(return_value=[])
        )

        result = await signal_bridge._list_user_projects("user-1")

        assert result == []

    @pytest.mark.asyncio
    async def test_list_user_projects_fetches_and_caches_projects(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        cache = Mock()
        cache.get.return_value = None
        session = SimpleNamespace(updated_at=2, access_token="token", github_username="octocat")
        fetched = [SimpleNamespace(name="Alpha", project_id="p1")]
        github_projects_service = Mock()
        github_projects_service.list_user_projects = AsyncMock(return_value=fetched)

        monkeypatch.setattr("src.services.cache.cache", cache)
        monkeypatch.setattr(
            "src.services.cache.get_user_projects_cache_key",
            Mock(return_value="projects:user-1"),
        )
        monkeypatch.setattr("src.services.database.get_db", Mock(return_value=AsyncMock()))
        monkeypatch.setattr(
            "src.services.session_store.get_sessions_by_user",
            AsyncMock(return_value=[session]),
        )
        monkeypatch.setattr(
            "src.services.github_projects.github_projects_service",
            github_projects_service,
        )

        result = await signal_bridge._list_user_projects("user-1")

        assert result == [("Alpha", "p1")]
        cache.set.assert_called_once_with("projects:user-1", fetched)
