"""Pluggable alert dispatcher with per-type cooldown enforcement.

Supports log-only mode (default) and optional webhook delivery via
configurable ``alert_webhook_url``.  Cooldown prevents the same alert
type from firing more than once per ``cooldown_minutes``.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from src.logging_utils import get_logger

logger = get_logger(__name__)


class AlertDispatcher:
    """Dispatches SLA-breach alerts with cooldown enforcement.

    Parameters
    ----------
    webhook_url:
        URL for webhook delivery.  Empty string means log-only mode.
    cooldown_minutes:
        Minimum minutes between alerts of the same type.
    """

    def __init__(self, webhook_url: str = "", cooldown_minutes: int = 15) -> None:
        self._webhook_url = webhook_url
        self._cooldown_minutes = cooldown_minutes
        self._last_fired: dict[str, datetime] = {}

    async def dispatch_alert(
        self,
        alert_type: str,
        summary: str,
        details: dict[str, Any],
    ) -> None:
        """Dispatch an alert if the cooldown window has elapsed.

        1. Check cooldown — suppress if same ``alert_type`` fired recently.
        2. Log the alert as a structured WARNING.
        3. POST to webhook if configured (fire-and-forget).
        4. Update the cooldown timestamp.
        """
        now = datetime.now(UTC)

        # ── Cooldown check ──
        last = self._last_fired.get(alert_type)
        if last is not None:
            elapsed = (now - last).total_seconds() / 60.0
            if elapsed < self._cooldown_minutes:
                logger.debug(
                    "Alert suppressed (cooldown): type=%s, elapsed=%.1f min, cooldown=%d min",
                    alert_type,
                    elapsed,
                    self._cooldown_minutes,
                )
                return

        # ── Log the alert ──
        fired_at = now.isoformat()
        logger.warning(
            "Alert dispatched: type=%s summary=%s details=%s fired_at=%s",
            alert_type,
            summary,
            details,
            fired_at,
        )

        # ── Optional webhook delivery ──
        if self._webhook_url:
            await self._send_webhook(alert_type, summary, details, fired_at)

        # ── Update cooldown ──
        self._last_fired[alert_type] = now

    async def _send_webhook(
        self,
        alert_type: str,
        summary: str,
        details: dict[str, Any],
        fired_at: str,
    ) -> None:
        """POST alert payload to the configured webhook URL."""
        import httpx

        payload = {
            "alert_type": alert_type,
            "summary": summary,
            "details": details,
            "fired_at": fired_at,
            "service": "solune-backend",
        }
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.post(
                    self._webhook_url,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                )
                logger.debug("Webhook response: status=%d", resp.status_code)
        except Exception as exc:
            logger.warning(
                "Webhook delivery failed for alert %s: %s",
                alert_type,
                exc,
            )
