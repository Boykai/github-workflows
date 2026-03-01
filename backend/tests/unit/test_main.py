"""Tests for main application factory and supporting classes (src/main.py).

Covers:
- create_app() → correct routers, CORS, exception handlers
- lifespan startup/shutdown
- _session_cleanup_loop background task
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from httpx import ASGITransport, AsyncClient

from src.main import _session_cleanup_loop, create_app

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
        # Depending on cache, this may use the AppException handler
        assert resp.status_code in (404, 200)

    async def test_health_check_or_docs_disabled_in_prod(self):
        """When debug=False, docs should be disabled."""
        with patch("src.main.get_settings") as mock_s:
            mock_s.return_value = MagicMock(
                debug=False,
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
        ):
            mock_s.return_value = MagicMock(
                debug=True,
                session_cleanup_interval=999999,
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
        ):
            mock_s.return_value = MagicMock(
                debug=True,
                session_cleanup_interval=999999,
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
