"""Tests for main application factory and supporting classes (src/main.py).

Covers:
- create_app() → correct routers, CORS, exception handlers
- lifespan startup/shutdown
- _session_cleanup_loop background task
- _auto_start_copilot_polling webhook token fallback
"""

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

from httpx import ASGITransport, AsyncClient

from src.main import _auto_start_copilot_polling, _session_cleanup_loop, create_app

# ── create_app ──────────────────────────────────────────────────────────────


class TestCreateApp:
    def test_app_has_api_router(self):
        """The app should include routes at /api/v1."""
        app = create_app()
        paths = [r.path for r in app.routes]
        # At a minimum the auth callback route should exist
        assert any("/api/v1" in p for p in paths)

    async def test_app_exception_handler(self, client):
        """AppException should return structured JSON error."""

        # Trigger an endpoint that raises AppException (e.g. 404)
        resp = await client.get("/api/v1/projects/NONEXIST")
        assert resp.status_code == 404

    async def test_health_check_or_docs_disabled_in_prod(self):
        """When enable_docs=False, docs should be disabled."""
        with patch("src.main.get_settings") as mock_s:
            mock_s.return_value = MagicMock(
                debug=False,
                enable_docs=False,
                cors_origins_list=["*"],
                host="0.0.0.0",
                port=8000,
                database_path=":memory:",
                session_cleanup_interval=3600,
            )
            app = create_app()
        assert app.docs_url is None
        assert app.redoc_url is None


# ── Lifespan ────────────────────────────────────────────────────────────────


class TestLifespan:
    async def test_lifespan_startup_shutdown(self):
        """Lifespan should init database on startup and close on shutdown."""
        from src.main import lifespan

        mock_db = AsyncMock()
        mock_app = MagicMock()

        # The background loops (_session_cleanup_loop, _polling_watchdog_loop)
        # run inside an asyncio.TaskGroup, so they must be mocked out.
        async def _noop_loop():
            """Coroutine that yields immediately so the TaskGroup can exit."""
            return

        with (
            patch("src.main.get_settings") as mock_s,
            patch("src.main.setup_logging"),
            patch(
                "src.services.database.init_database",
                new_callable=AsyncMock,
                return_value=mock_db,
            ) as mock_init,
            patch(
                "src.services.database.seed_global_settings",
                new_callable=AsyncMock,
            ) as mock_seed,
            patch(
                "src.services.database.close_database",
                new_callable=AsyncMock,
            ) as mock_close,
            patch("src.main._session_cleanup_loop", side_effect=_noop_loop),
            patch("src.main._polling_watchdog_loop", side_effect=_noop_loop),
            patch("src.main._auto_start_copilot_polling", new_callable=AsyncMock),
            patch(
                "src.services.signal_bridge.start_signal_ws_listener",
                new_callable=AsyncMock,
            ),
            patch(
                "src.services.signal_bridge.stop_signal_ws_listener",
                new_callable=AsyncMock,
            ),
            patch(
                "src.services.pipeline_state_store.init_pipeline_state_store",
                new_callable=AsyncMock,
            ),
        ):
            mock_s.return_value = MagicMock(
                debug=True,
                session_cleanup_interval=999999,
                alert_webhook_url="",
                alert_cooldown_minutes=15,
                otel_enabled=False,
                otel_endpoint="http://localhost:4317",
                otel_service_name="solune-backend",
                sentry_dsn="",
            )
            async with lifespan(mock_app):
                mock_init.assert_awaited_once()
                mock_seed.assert_awaited_once_with(mock_db)

            mock_close.assert_awaited_once()

    async def test_lifespan_cleanup_on_startup_failure(self):
        """Resources initialised before failure should still be cleaned up.

        Validates the try/finally guard: if start_signal_ws_listener()
        raises, the DB and cleanup task that were already started must
        still be torn down, but stop_signal_ws_listener() must NOT be
        called because Signal was never started.
        """
        from src.main import lifespan

        mock_db = AsyncMock()
        mock_app = MagicMock()

        with (
            patch("src.main.get_settings") as mock_s,
            patch("src.main.setup_logging"),
            patch(
                "src.services.database.init_database",
                new_callable=AsyncMock,
                return_value=mock_db,
            ),
            patch(
                "src.services.database.seed_global_settings",
                new_callable=AsyncMock,
            ),
            patch(
                "src.services.database.close_database",
                new_callable=AsyncMock,
            ) as mock_close,
            patch(
                "src.services.signal_bridge.start_signal_ws_listener",
                new_callable=AsyncMock,
                side_effect=RuntimeError("signal connect failed"),
            ),
            patch(
                "src.services.signal_bridge.stop_signal_ws_listener",
                new_callable=AsyncMock,
            ) as mock_stop_signal,
            patch(
                "src.services.pipeline_state_store.init_pipeline_state_store",
                new_callable=AsyncMock,
            ),
        ):
            mock_s.return_value = MagicMock(
                debug=True,
                session_cleanup_interval=999999,
                alert_webhook_url="",
                alert_cooldown_minutes=15,
                otel_enabled=False,
                otel_endpoint="http://localhost:4317",
                otel_service_name="solune-backend",
                sentry_dsn="",
            )
            try:
                async with lifespan(mock_app):
                    pass  # pragma: no cover
            except RuntimeError:
                pass

            # DB should still be closed even though startup failed
            mock_close.assert_awaited_once()
            # Signal was never started, so stop must NOT be called
            mock_stop_signal.assert_not_awaited()


class TestSessionCleanupLoop:
    """Tests for _session_cleanup_loop background task."""

    async def test_purges_expired_sessions(self):
        """Should call purge_expired_sessions and log when count > 0."""
        call_count = 0

        async def _fake_sleep(seconds):
            nonlocal call_count
            call_count += 1
            if call_count > 1:
                raise asyncio.CancelledError

        with (
            patch("src.main.get_settings") as mock_s,
            patch("src.main.asyncio.sleep", side_effect=_fake_sleep),
            patch("src.services.database.get_db", return_value=MagicMock()),
            patch(
                "src.services.session_store.purge_expired_sessions",
                new_callable=AsyncMock,
                return_value=3,
            ) as mock_purge,
        ):
            mock_s.return_value = MagicMock(session_cleanup_interval=10)
            await _session_cleanup_loop()
            mock_purge.assert_awaited_once()

    async def test_handles_exception_in_loop(self):
        """Should log exception and continue looping."""
        call_count = 0

        async def _fake_sleep(seconds):
            nonlocal call_count
            call_count += 1
            if call_count > 1:
                raise asyncio.CancelledError

        with (
            patch("src.main.get_settings") as mock_s,
            patch("src.main.asyncio.sleep", side_effect=_fake_sleep),
            patch("src.services.database.get_db", return_value=MagicMock()),
            patch(
                "src.services.session_store.purge_expired_sessions",
                new_callable=AsyncMock,
                side_effect=RuntimeError("DB error"),
            ),
        ):
            mock_s.return_value = MagicMock(session_cleanup_interval=10)
            # Should not raise; should catch and continue until CancelledError
            await _session_cleanup_loop()

    async def test_backoff_uses_base_interval_on_success(self):
        """On success (consecutive_failures==0) sleep equals base interval.

        Regression test: the original implementation used
        ``min(interval * 2**0, 300)`` which capped the default 3600s
        interval down to 300s, running cleanup 12x more often.
        """
        sleep_values: list[float] = []

        async def _capture_sleep(seconds):
            sleep_values.append(seconds)
            raise asyncio.CancelledError

        with (
            patch("src.main.get_settings") as mock_s,
            patch("src.main.asyncio.sleep", side_effect=_capture_sleep),
            patch("src.services.database.get_db", return_value=MagicMock()),
        ):
            mock_s.return_value = MagicMock(session_cleanup_interval=3600)
            await _session_cleanup_loop()

        # First sleep should be the full configured interval, not capped to 300
        assert sleep_values[0] == 3600

    async def test_backoff_increases_on_consecutive_failures(self):
        """After failures, sleep uses exponential backoff capped correctly."""
        sleep_values: list[float] = []
        call_count = 0

        async def _capture_sleep(seconds):
            nonlocal call_count
            sleep_values.append(seconds)
            call_count += 1
            if call_count >= 3:
                raise asyncio.CancelledError

        with (
            patch("src.main.get_settings") as mock_s,
            patch("src.main.asyncio.sleep", side_effect=_capture_sleep),
            patch("src.services.database.get_db", return_value=MagicMock()),
            patch(
                "src.services.session_store.purge_expired_sessions",
                new_callable=AsyncMock,
                side_effect=RuntimeError("DB error"),
            ),
        ):
            mock_s.return_value = MagicMock(session_cleanup_interval=10)
            await _session_cleanup_loop()

        # 1st call: consecutive_failures=0 → sleep=10 (base interval)
        assert sleep_values[0] == 10
        # 2nd call: consecutive_failures=1 → min(10*2, max(10,300)) = 20
        assert sleep_values[1] == 20
        # 3rd call: consecutive_failures=2 → min(10*4, 300) = 40
        assert sleep_values[2] == 40


class TestGenericExceptionHandler:
    """Tests for the generic exception handler."""

    async def test_unhandled_exception_returns_500(self):
        """Unhandled exceptions should return 500 with JSON body."""
        app = create_app()

        # Add a route that raises a raw Exception
        from fastapi import APIRouter

        err_router = APIRouter()

        @err_router.get("/_test_500")
        async def _raise():
            raise RuntimeError("boom")

        app.include_router(err_router, prefix="/api/v1")

        transport = ASGITransport(app=app, raise_app_exceptions=False)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.get("/api/v1/_test_500")

        assert resp.status_code == 500
        assert resp.json() == {"error": "Internal server error"}


class TestShutdownPollingLogging:
    """Regression test: shutdown must log errors instead of silently swallowing them."""

    async def test_shutdown_logs_polling_stop_error(self):
        """If stop_polling() raises during shutdown, the error must be logged
        rather than silently swallowed by a bare ``except: pass``."""
        from src.main import lifespan

        mock_db = AsyncMock()
        mock_app = MagicMock()

        async def _noop_loop():
            return

        with (
            patch("src.main.get_settings") as mock_s,
            patch("src.main.setup_logging"),
            patch(
                "src.services.database.init_database",
                new_callable=AsyncMock,
                return_value=mock_db,
            ),
            patch(
                "src.services.database.seed_global_settings",
                new_callable=AsyncMock,
            ),
            patch(
                "src.services.database.close_database",
                new_callable=AsyncMock,
            ),
            patch(
                "src.services.signal_bridge.start_signal_ws_listener",
                new_callable=AsyncMock,
            ),
            patch(
                "src.services.signal_bridge.stop_signal_ws_listener",
                new_callable=AsyncMock,
            ),
            patch("src.main._auto_start_copilot_polling", new_callable=AsyncMock),
            patch("src.main._session_cleanup_loop", side_effect=_noop_loop),
            patch("src.main._polling_watchdog_loop", side_effect=_noop_loop),
            patch(
                "src.services.pipeline_state_store.init_pipeline_state_store",
                new_callable=AsyncMock,
            ),
            patch(
                "src.services.copilot_polling.get_polling_status",
                return_value={"is_running": True},
            ),
            patch(
                "src.services.copilot_polling.stop_polling",
                side_effect=RuntimeError("polling stop failed"),
            ),
            patch("src.main.logger") as mock_logger,
        ):
            mock_s.return_value = MagicMock(
                debug=True,
                session_cleanup_interval=999999,
                alert_webhook_url="",
                alert_cooldown_minutes=15,
                otel_enabled=False,
                otel_endpoint="http://localhost:4317",
                otel_service_name="solune-backend",
                sentry_dsn="",
            )
            async with lifespan(mock_app):
                pass

            # The error must have been logged, not silently swallowed
            mock_logger.warning.assert_called()
            # Verify the warning includes the shutdown context and traceback
            warning_args = mock_logger.warning.call_args
            assert "Error stopping Copilot polling during shutdown" in str(warning_args)
            assert warning_args.kwargs.get("exc_info") is True


# ── _auto_start_copilot_polling webhook token fallback ──────────────────────


def _make_mock_db(session_rows=None, project_settings_rows=None):
    """Build a mock async DB that handles both user_sessions and project_settings queries."""

    async def _execute(sql, *args, **kwargs):
        cursor = AsyncMock()
        if "user_sessions" in sql:
            cursor.fetchone = AsyncMock(return_value=session_rows)
        elif "project_settings" in sql:
            cursor.fetchall = AsyncMock(return_value=project_settings_rows or [])
        else:
            cursor.fetchone = AsyncMock(return_value=None)
            cursor.fetchall = AsyncMock(return_value=[])
        return cursor

    db = AsyncMock()
    db.execute = AsyncMock(side_effect=_execute)
    return db


class TestAutoStartWebhookFallback:
    """Tests for the webhook-token fallback in _auto_start_copilot_polling."""

    async def test_fallback_starts_polling_with_webhook_token(self):
        """When no sessions exist but GITHUB_WEBHOOK_TOKEN and DEFAULT_REPOSITORY
        are set, polling should start using stored project settings."""

        wf_config = json.dumps(
            {"repository_owner": "Boykai", "repository_name": "github-workflows"}
        )
        ps_rows = [{"project_id": "PVT_abc123", "workflow_config": wf_config}]
        mock_db = _make_mock_db(session_rows=None, project_settings_rows=ps_rows)

        mock_settings = MagicMock(
            default_project_id=None,
            github_webhook_token="ghp_test_token",
            default_repo_owner="Boykai",
            default_repo_name="github-workflows",
        )

        with (
            patch(
                "src.services.copilot_polling.get_polling_status",
                return_value={"is_running": False},
            ),
            patch("src.services.database.get_db", return_value=mock_db),
            patch("src.main.get_settings", return_value=mock_settings),
            patch(
                "src.services.session_store.get_session",
                new_callable=AsyncMock,
                return_value=None,
            ),
            patch(
                "src.services.copilot_polling.ensure_polling_started",
                new_callable=AsyncMock,
                return_value=True,
            ) as mock_start,
        ):
            await _auto_start_copilot_polling()

            mock_start.assert_awaited_once_with(
                access_token="ghp_test_token",
                project_id="PVT_abc123",
                owner="Boykai",
                repo="github-workflows",
                caller="webhook_token_fallback",
            )

    async def test_fallback_skipped_when_no_token(self):
        """Without GITHUB_WEBHOOK_TOKEN, fallback should not attempt polling."""
        mock_db = _make_mock_db(session_rows=None)
        mock_settings = MagicMock(
            default_project_id=None,
            github_webhook_token=None,
            default_repo_owner="Boykai",
            default_repo_name="github-workflows",
        )

        with (
            patch(
                "src.services.copilot_polling.get_polling_status",
                return_value={"is_running": False},
            ),
            patch("src.services.database.get_db", return_value=mock_db),
            patch("src.main.get_settings", return_value=mock_settings),
            patch(
                "src.services.session_store.get_session",
                new_callable=AsyncMock,
                return_value=None,
            ),
            patch(
                "src.services.copilot_polling.ensure_polling_started",
                new_callable=AsyncMock,
            ) as mock_start,
        ):
            await _auto_start_copilot_polling()
            mock_start.assert_not_awaited()

    async def test_fallback_skipped_when_no_matching_project(self):
        """When project_settings has no matching repo, polling should not start."""
        wf_config = json.dumps({"repository_owner": "Other", "repository_name": "other-repo"})
        ps_rows = [{"project_id": "PVT_other", "workflow_config": wf_config}]
        mock_db = _make_mock_db(session_rows=None, project_settings_rows=ps_rows)

        mock_settings = MagicMock(
            default_project_id=None,
            github_webhook_token="ghp_test_token",
            default_repo_owner="Boykai",
            default_repo_name="github-workflows",
        )

        with (
            patch(
                "src.services.copilot_polling.get_polling_status",
                return_value={"is_running": False},
            ),
            patch("src.services.database.get_db", return_value=mock_db),
            patch("src.main.get_settings", return_value=mock_settings),
            patch(
                "src.services.session_store.get_session",
                new_callable=AsyncMock,
                return_value=None,
            ),
            patch(
                "src.services.copilot_polling.ensure_polling_started",
                new_callable=AsyncMock,
            ) as mock_start,
        ):
            await _auto_start_copilot_polling()
            mock_start.assert_not_awaited()

    async def test_fallback_owner_only_match(self):
        """When repo_name is empty but owner matches, use as fallback."""
        wf_config = json.dumps({"repository_owner": "Boykai", "repository_name": ""})
        ps_rows = [{"project_id": "PVT_owner_only", "workflow_config": wf_config}]
        mock_db = _make_mock_db(session_rows=None, project_settings_rows=ps_rows)

        mock_settings = MagicMock(
            default_project_id=None,
            github_webhook_token="ghp_test_token",
            default_repo_owner="Boykai",
            default_repo_name="github-workflows",
        )

        with (
            patch(
                "src.services.copilot_polling.get_polling_status",
                return_value={"is_running": False},
            ),
            patch("src.services.database.get_db", return_value=mock_db),
            patch("src.main.get_settings", return_value=mock_settings),
            patch(
                "src.services.session_store.get_session",
                new_callable=AsyncMock,
                return_value=None,
            ),
            patch(
                "src.services.copilot_polling.ensure_polling_started",
                new_callable=AsyncMock,
                return_value=True,
            ) as mock_start,
        ):
            await _auto_start_copilot_polling()

            mock_start.assert_awaited_once_with(
                access_token="ghp_test_token",
                project_id="PVT_owner_only",
                owner="Boykai",
                repo="github-workflows",
                caller="webhook_token_fallback",
            )

    async def test_session_strategy_preferred_over_fallback(self):
        """When a valid session exists, it should be used instead of webhook token."""
        mock_session = MagicMock(
            access_token="ghp_session_token",
            selected_project_id="PVT_session",
        )

        session_row = {"session_id": "sid123"}

        async def _execute(sql, *args, **kwargs):
            cursor = AsyncMock()
            if "user_sessions" in sql:
                cursor.fetchone = AsyncMock(return_value=session_row)
            else:
                cursor.fetchone = AsyncMock(return_value=None)
                cursor.fetchall = AsyncMock(return_value=[])
            return cursor

        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(side_effect=_execute)

        with (
            patch(
                "src.services.copilot_polling.get_polling_status",
                return_value={"is_running": False},
            ),
            patch("src.services.database.get_db", return_value=mock_db),
            patch(
                "src.services.session_store.get_session",
                new_callable=AsyncMock,
                return_value=mock_session,
            ),
            patch(
                "src.utils.resolve_repository",
                new_callable=AsyncMock,
                return_value=("Boykai", "github-workflows"),
            ),
            patch(
                "src.services.copilot_polling.ensure_polling_started",
                new_callable=AsyncMock,
                return_value=True,
            ) as mock_start,
        ):
            await _auto_start_copilot_polling()

            mock_start.assert_awaited_once_with(
                access_token="ghp_session_token",
                project_id="PVT_session",
                owner="Boykai",
                repo="github-workflows",
                caller="lifespan_auto_start",
            )

    async def test_fallback_used_when_session_resolve_fails(self):
        """If session exists but resolve_repository fails, fall through to webhook fallback."""
        mock_session = MagicMock(
            access_token="ghp_bad_token",
            selected_project_id="PVT_expired",
        )
        session_row = {"session_id": "sid_expired"}
        wf_config = json.dumps(
            {"repository_owner": "Boykai", "repository_name": "github-workflows"}
        )
        ps_rows = [{"project_id": "PVT_fallback", "workflow_config": wf_config}]

        call_count = 0

        async def _execute(sql, *args, **kwargs):
            nonlocal call_count
            call_count += 1
            cursor = AsyncMock()
            if "user_sessions" in sql:
                cursor.fetchone = AsyncMock(return_value=session_row)
            elif "project_settings" in sql:
                cursor.fetchall = AsyncMock(return_value=ps_rows)
            else:
                cursor.fetchone = AsyncMock(return_value=None)
                cursor.fetchall = AsyncMock(return_value=[])
            return cursor

        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(side_effect=_execute)

        mock_settings = MagicMock(
            default_project_id=None,
            github_webhook_token="ghp_webhook",
            default_repo_owner="Boykai",
            default_repo_name="github-workflows",
        )

        with (
            patch(
                "src.services.copilot_polling.get_polling_status",
                return_value={"is_running": False},
            ),
            patch("src.services.database.get_db", return_value=mock_db),
            patch("src.main.get_settings", return_value=mock_settings),
            patch(
                "src.services.session_store.get_session",
                new_callable=AsyncMock,
                return_value=mock_session,
            ),
            patch(
                "src.utils.resolve_repository",
                new_callable=AsyncMock,
                side_effect=Exception("token expired"),
            ),
            patch(
                "src.services.copilot_polling.ensure_polling_started",
                new_callable=AsyncMock,
                return_value=True,
            ) as mock_start,
        ):
            await _auto_start_copilot_polling()

            # Should have used the webhook token fallback
            mock_start.assert_awaited_once_with(
                access_token="ghp_webhook",
                project_id="PVT_fallback",
                owner="Boykai",
                repo="github-workflows",
                caller="webhook_token_fallback",
            )
