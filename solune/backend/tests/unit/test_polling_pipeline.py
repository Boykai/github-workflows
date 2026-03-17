"""Tests for copilot polling pipeline utilities (src/services/copilot_polling/pipeline.py).

Covers:
- _get_rate_limit_remaining(): parsing rate-limit info, missing data
- _wait_if_rate_limited(): above threshold (no wait), below threshold (returns True)
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.services.copilot_polling.pipeline import (
    _get_rate_limit_remaining,
    _wait_if_rate_limited,
)
from src.services.copilot_polling.state import RATE_LIMIT_PAUSE_THRESHOLD


# ── _get_rate_limit_remaining ─────────────────────────────────────────────


class TestGetRateLimitRemaining:
    """Tests for parsing cached rate-limit info."""

    def test_returns_remaining_and_reset(self):
        """Parses remaining and reset_at from cached rate-limit dict."""
        rl = {"remaining": 500, "reset_at": 1700000000}
        with patch("src.services.copilot_polling.pipeline._cp") as mock_cp:
            mock_cp.github_projects_service.get_last_rate_limit.return_value = rl
            remaining, reset_at = _get_rate_limit_remaining()
        assert remaining == 500
        assert reset_at == 1700000000

    def test_returns_none_when_no_data(self):
        """Returns (None, None) when no rate-limit data is cached."""
        with patch("src.services.copilot_polling.pipeline._cp") as mock_cp:
            mock_cp.github_projects_service.get_last_rate_limit.return_value = None
            remaining, reset_at = _get_rate_limit_remaining()
        assert remaining is None
        assert reset_at is None

    def test_returns_none_on_type_error(self):
        """Returns (None, None) when values are not convertible to int."""
        rl = {"remaining": "invalid", "reset_at": "bad"}
        with patch("src.services.copilot_polling.pipeline._cp") as mock_cp:
            mock_cp.github_projects_service.get_last_rate_limit.return_value = rl
            remaining, reset_at = _get_rate_limit_remaining()
        # "invalid" can't be converted to int
        assert remaining is None
        assert reset_at is None

    def test_handles_none_remaining_value(self):
        """Handles remaining=None in the rate-limit dict."""
        rl = {"remaining": None, "reset_at": 1700000000}
        with patch("src.services.copilot_polling.pipeline._cp") as mock_cp:
            mock_cp.github_projects_service.get_last_rate_limit.return_value = rl
            remaining, reset_at = _get_rate_limit_remaining()
        assert remaining is None
        assert reset_at == 1700000000

    def test_string_values_coerced_to_int(self):
        """String numeric values are coerced to int."""
        rl = {"remaining": "100", "reset_at": "1700000000"}
        with patch("src.services.copilot_polling.pipeline._cp") as mock_cp:
            mock_cp.github_projects_service.get_last_rate_limit.return_value = rl
            remaining, reset_at = _get_rate_limit_remaining()
        assert remaining == 100
        assert reset_at == 1700000000


# ── _wait_if_rate_limited ─────────────────────────────────────────────────


class TestWaitIfRateLimited:
    """Tests for rate-limit pause logic."""

    async def test_no_rate_limit_data_returns_false(self):
        """Returns False (proceed) when no rate-limit data is available."""
        with patch(
            "src.services.copilot_polling.pipeline._get_rate_limit_remaining",
            return_value=(None, None),
        ):
            result = await _wait_if_rate_limited("test context")
        assert result is False

    async def test_above_threshold_returns_false(self):
        """Returns False (proceed) when remaining is above the pause threshold."""
        with patch(
            "src.services.copilot_polling.pipeline._get_rate_limit_remaining",
            return_value=(RATE_LIMIT_PAUSE_THRESHOLD + 100, 1700000000),
        ):
            result = await _wait_if_rate_limited("test context")
        assert result is False

    async def test_below_threshold_waits_and_returns_true(self):
        """Returns True (abort) when remaining is at or below pause threshold."""
        future_reset = 99999999999
        with (
            patch(
                "src.services.copilot_polling.pipeline._get_rate_limit_remaining",
                return_value=(RATE_LIMIT_PAUSE_THRESHOLD - 10, future_reset),
            ),
            patch("src.services.copilot_polling.pipeline.asyncio.sleep", new_callable=AsyncMock) as mock_sleep,
        ):
            result = await _wait_if_rate_limited("test context")
        assert result is True
        mock_sleep.assert_awaited_once()

    async def test_at_exact_threshold_waits(self):
        """Returns True when remaining equals exactly the pause threshold."""
        future_reset = 99999999999
        with (
            patch(
                "src.services.copilot_polling.pipeline._get_rate_limit_remaining",
                return_value=(RATE_LIMIT_PAUSE_THRESHOLD, future_reset),
            ),
            patch("src.services.copilot_polling.pipeline.asyncio.sleep", new_callable=AsyncMock) as mock_sleep,
        ):
            result = await _wait_if_rate_limited("test context")
        assert result is True
        mock_sleep.assert_awaited_once()
