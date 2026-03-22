"""Tests for copilot polling pipeline utilities (src/services/copilot_polling/pipeline.py).

Covers:
- _get_rate_limit_remaining(): parsing rate-limit info, missing data
- _wait_if_rate_limited(): above threshold (no wait), below threshold (returns True)
"""

import asyncio
from unittest.mock import AsyncMock, patch

from src.services.copilot_polling.pipeline import (
    _get_rate_limit_remaining,
    _wait_if_rate_limited,
)
from src.services.copilot_polling.state import (
    ASSIGNMENT_GRACE_PERIOD_SECONDS,
    RATE_LIMIT_PAUSE_THRESHOLD,
)

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
            patch(
                "src.services.copilot_polling.pipeline.asyncio.sleep", new_callable=AsyncMock
            ) as mock_sleep,
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
            patch(
                "src.services.copilot_polling.pipeline.asyncio.sleep", new_callable=AsyncMock
            ) as mock_sleep,
        ):
            result = await _wait_if_rate_limited("test context")
        assert result is True
        mock_sleep.assert_awaited_once()


# ---------------------------------------------------------------------------
# T026 - _dequeue_next_pipeline
# ---------------------------------------------------------------------------


class TestDequeueNextPipeline:
    """Tests for the _dequeue_next_pipeline helper."""

    async def test_dequeue_marks_pipeline_as_not_queued(self):
        """Dequeued pipeline has queued=False set via set_pipeline_state."""
        from src.services.copilot_polling.pipeline import _dequeue_next_pipeline

        mock_pipeline = AsyncMock()
        mock_pipeline.issue_number = 42
        mock_pipeline.queued = True

        mock_config = AsyncMock()

        with (
            patch("src.services.database.get_db", return_value=AsyncMock()),
            patch(
                "src.services.settings_store.is_queue_mode_enabled",
                new_callable=AsyncMock,
                return_value=True,
            ),
            patch(
                "src.services.copilot_polling.pipeline.get_project_launch_lock",
                return_value=asyncio.Lock(),
            ),
            patch("src.services.copilot_polling.pipeline._cp") as mock_cp,
        ):
            mock_cp.count_active_pipelines_for_project.return_value = 0
            mock_cp.get_queued_pipelines_for_project.return_value = [mock_pipeline]
            mock_cp.get_workflow_config = AsyncMock(return_value=mock_config)
            mock_cp.get_workflow_orchestrator.return_value = AsyncMock()
            mock_cp.WorkflowContext = lambda **kw: AsyncMock(**kw)

            await _dequeue_next_pipeline("token", "PVT_1", "completion")
            assert mock_pipeline.queued is False
            mock_cp.set_pipeline_state.assert_called_once_with(42, mock_pipeline)

    async def test_dequeue_does_nothing_when_queue_mode_off(self):
        """When queue mode is disabled, dequeue returns without action."""
        from src.services.copilot_polling.pipeline import _dequeue_next_pipeline

        with (
            patch("src.services.database.get_db", return_value=AsyncMock()),
            patch(
                "src.services.settings_store.is_queue_mode_enabled",
                new_callable=AsyncMock,
                return_value=False,
            ),
            patch("src.services.copilot_polling.pipeline._cp") as mock_cp,
        ):
            await _dequeue_next_pipeline("token", "PVT_1", "test")
            mock_cp.get_queued_pipelines_for_project.assert_not_called()

    async def test_dequeue_handles_empty_queue(self):
        """No crash when queue is empty."""
        from src.services.copilot_polling.pipeline import _dequeue_next_pipeline

        with (
            patch("src.services.database.get_db", return_value=AsyncMock()),
            patch(
                "src.services.settings_store.is_queue_mode_enabled",
                new_callable=AsyncMock,
                return_value=True,
            ),
            patch("src.services.copilot_polling.pipeline._cp") as mock_cp,
        ):
            mock_cp.get_queued_pipelines_for_project.return_value = []
            await _dequeue_next_pipeline("token", "PVT_1", "test")
            mock_cp.set_pipeline_state.assert_not_called()


# ---------------------------------------------------------------------------
# T027 - Grace period
# ---------------------------------------------------------------------------


class TestGracePeriod:
    """Tests for ASSIGNMENT_GRACE_PERIOD_SECONDS and stale reclaim timing."""

    def test_grace_period_constant_is_positive(self):
        """ASSIGNMENT_GRACE_PERIOD_SECONDS must be a positive integer."""
        assert ASSIGNMENT_GRACE_PERIOD_SECONDS > 0

    def test_grace_period_is_120_seconds(self):
        """Default grace period is 120 seconds."""
        assert ASSIGNMENT_GRACE_PERIOD_SECONDS == 120

    def test_pending_assignment_tracks_timestamp(self):
        """_pending_agent_assignments stores datetime values for age tracking."""
        from src.services.copilot_polling.state import _pending_agent_assignments
        from src.utils import utcnow

        key = "9999:test-agent"
        now = utcnow()
        _pending_agent_assignments[key] = now
        try:
            assert _pending_agent_assignments.get(key) == now
        finally:
            _pending_agent_assignments.pop(key, None)

    def test_pending_assignment_pop_removes_entry(self):
        """pop() removes and returns the value."""
        from src.services.copilot_polling.state import _pending_agent_assignments
        from src.utils import utcnow

        key = "8888:cleanup-agent"
        ts = utcnow()
        _pending_agent_assignments[key] = ts
        removed = _pending_agent_assignments.pop(key, None)
        assert removed == ts
        assert key not in _pending_agent_assignments


# ---------------------------------------------------------------------------
# T028 - BoundedDict edge cases
# ---------------------------------------------------------------------------


class TestBoundedDictEdgeCases:
    """Edge-case tests for BoundedDict FIFO eviction and callbacks."""

    def test_eviction_on_overflow(self):
        """Oldest entry is evicted when maxlen is reached."""
        from src.utils import BoundedDict

        bd = BoundedDict(maxlen=2)
        bd["a"] = 1
        bd["b"] = 2
        bd["c"] = 3
        assert "a" not in bd
        assert bd["b"] == 2
        assert bd["c"] == 3

    def test_on_evict_callback_fires(self):
        """on_evict callback is invoked with (key, value) of evicted entry."""
        from src.utils import BoundedDict

        evicted = []
        bd = BoundedDict(maxlen=1, on_evict=lambda k, v: evicted.append((k, v)))
        bd["first"] = 10
        bd["second"] = 20
        assert evicted == [("first", 10)]

    def test_update_existing_key_does_not_evict(self):
        """Updating an existing key moves it to end without evicting."""
        from src.utils import BoundedDict

        bd = BoundedDict(maxlen=2)
        bd["a"] = 1
        bd["b"] = 2
        bd["a"] = 10
        assert len(bd) == 2
        assert bd["a"] == 10

    def test_maxlen_zero_raises(self):
        """maxlen <= 0 raises ValueError."""
        import pytest as _pytest

        from src.utils import BoundedDict

        with _pytest.raises(ValueError, match="maxlen must be > 0"):
            BoundedDict(maxlen=0)

    def test_get_default_for_missing_key(self):
        """get() returns default when key is absent."""
        from src.utils import BoundedDict

        bd = BoundedDict(maxlen=5)
        assert bd.get("missing") is None
        assert bd.get("missing", 42) == 42

    def test_on_evict_callback_exception_is_swallowed(self):
        """A failing on_evict callback does not crash BoundedDict."""
        from src.utils import BoundedDict

        def bad_callback(k, v):
            raise RuntimeError("callback error")

        bd = BoundedDict(maxlen=1, on_evict=bad_callback)
        bd["a"] = 1
        bd["b"] = 2
        assert bd["b"] == 2
        assert len(bd) == 1
