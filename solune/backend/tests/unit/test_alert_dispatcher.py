"""Tests for the alert dispatcher service (src/services/alert_dispatcher.py).

Covers:
- dispatch_alert logs a WARNING when cooldown has elapsed
- dispatch_alert suppresses duplicate alerts within cooldown window
- dispatch_alert sends webhook when webhook_url is configured
- dispatch_alert continues on webhook failure
- cooldown is per alert_type (independent cooldowns)
"""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch

from src.services.alert_dispatcher import AlertDispatcher


class TestAlertDispatcherBasic:
    """Tests for basic alert dispatch behavior."""

    async def test_dispatch_logs_warning(self, caplog):
        """First dispatch of an alert type should log a WARNING."""
        dispatcher = AlertDispatcher(cooldown_minutes=15)
        import logging

        with caplog.at_level(logging.WARNING):
            await dispatcher.dispatch_alert(
                alert_type="pipeline_stall",
                summary="Pipeline stalled",
                details={"issue_number": 42},
            )
        assert "Alert dispatched" in caplog.text
        assert "pipeline_stall" in caplog.text

    async def test_dispatch_updates_cooldown(self):
        """After dispatch, cooldown timestamp should be recorded."""
        dispatcher = AlertDispatcher(cooldown_minutes=15)
        await dispatcher.dispatch_alert(
            alert_type="pipeline_stall",
            summary="Stall",
            details={},
        )
        assert "pipeline_stall" in dispatcher._last_fired
        assert isinstance(dispatcher._last_fired["pipeline_stall"], datetime)


class TestAlertDispatcherCooldown:
    """Tests for cooldown enforcement."""

    async def test_suppress_within_cooldown(self, caplog):
        """Duplicate alert within cooldown window should be suppressed."""
        dispatcher = AlertDispatcher(cooldown_minutes=15)
        # First alert
        await dispatcher.dispatch_alert("test_type", "First", {})

        import logging

        with caplog.at_level(logging.DEBUG):
            # Second alert within cooldown
            await dispatcher.dispatch_alert("test_type", "Second", {})

        # Should see "suppressed" in DEBUG log
        assert "suppressed" in caplog.text.lower()

    async def test_allow_after_cooldown_expires(self, caplog):
        """Alert should fire after cooldown window has elapsed."""
        from datetime import UTC

        dispatcher = AlertDispatcher(cooldown_minutes=15)
        # Manually set last_fired to 20 minutes ago
        dispatcher._last_fired["test_type"] = datetime.now(UTC) - timedelta(minutes=20)

        import logging

        with caplog.at_level(logging.WARNING):
            await dispatcher.dispatch_alert("test_type", "After cooldown", {})

        assert "Alert dispatched" in caplog.text

    async def test_independent_cooldowns_per_type(self):
        """Different alert types should have independent cooldowns."""
        dispatcher = AlertDispatcher(cooldown_minutes=15)
        await dispatcher.dispatch_alert("type_a", "A", {})
        await dispatcher.dispatch_alert("type_b", "B", {})

        assert "type_a" in dispatcher._last_fired
        assert "type_b" in dispatcher._last_fired


class TestAlertDispatcherWebhook:
    """Tests for webhook delivery."""

    async def test_webhook_sends_post(self):
        """When webhook_url is set, a POST should be sent (fire-and-forget)."""
        import asyncio

        dispatcher = AlertDispatcher(webhook_url="https://hooks.example.com/alert")

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.post = AsyncMock()

            await dispatcher.dispatch_alert(
                alert_type="rate_limit_critical",
                summary="Rate limit critical",
                details={"remaining": 5},
            )

            # Give the fire-and-forget task time to run
            await asyncio.sleep(0.05)

            mock_client.post.assert_called_once()
            call_kwargs = mock_client.post.call_args
            assert call_kwargs[0][0] == "https://hooks.example.com/alert"
            payload = call_kwargs[1]["json"]
            assert payload["alert_type"] == "rate_limit_critical"
            assert payload["service"] == "solune-backend"

    async def test_no_webhook_when_url_empty(self):
        """When webhook_url is empty, no POST should be sent."""
        dispatcher = AlertDispatcher(webhook_url="")

        with patch.object(dispatcher, "_send_webhook", new_callable=AsyncMock) as mock_send:
            await dispatcher.dispatch_alert("test", "Test", {})
            mock_send.assert_not_called()

    async def test_webhook_failure_does_not_raise(self, caplog):
        """Webhook failure should be logged but not raise."""
        import asyncio

        dispatcher = AlertDispatcher(webhook_url="https://hooks.example.com/alert")

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.post = AsyncMock(side_effect=Exception("Connection refused"))

            import logging

            with caplog.at_level(logging.WARNING):
                # Should not raise
                await dispatcher.dispatch_alert(
                    alert_type="test",
                    summary="Test",
                    details={},
                )
                # Give the fire-and-forget task time to run
                await asyncio.sleep(0.05)
            assert "Webhook delivery failed" in caplog.text
