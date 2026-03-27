"""Unit tests for roadmap auto-launch debounce and daily cap (FR-006, FR-007).

Covers:
- 5-minute debounce guard on _maybe_trigger_roadmap
- 10-cycle/day cap per project
- Daily counter reset on new UTC day
- Conditions: roadmap_enabled, roadmap_auto_launch
"""

from __future__ import annotations

import json
from datetime import UTC, date, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.services.copilot_polling.pipeline import (
    _ROADMAP_DAILY_CAP,
    _ROADMAP_DEBOUNCE_SECONDS,
    _maybe_trigger_roadmap,
    _roadmap_daily_count,
    _roadmap_last_trigger,
)


@pytest.fixture(autouse=True)
def _reset_roadmap_state():
    """Clear in-memory roadmap state before each test."""
    _roadmap_last_trigger.clear()
    _roadmap_daily_count.clear()
    yield
    _roadmap_last_trigger.clear()
    _roadmap_daily_count.clear()


def _make_mock_row(*, enabled: bool = True, auto_launch: bool = True, pipeline_id: str = "pipe1"):
    """Create a mock DB row with board_display_config JSON."""
    config_data = {
        "roadmap_enabled": enabled,
        "roadmap_auto_launch": auto_launch,
        "roadmap_pipeline_id": pipeline_id,
        "roadmap_seed": "Build great things",
        "roadmap_batch_size": 3,
    }
    row = MagicMock()
    row.__getitem__ = lambda self, key: json.dumps(config_data) if key == "board_display_config" else None
    return row


def _patch_db_and_generator(row, gen_return=None):
    """Return context managers that patch get_db, get_project_settings_row, and generate_roadmap_batch."""
    mock_db = MagicMock()
    mock_gen = AsyncMock(return_value=gen_return)

    return (
        patch("src.services.copilot_polling.pipeline.get_db", return_value=mock_db),
        patch("src.services.copilot_polling.pipeline.get_project_settings_row", new_callable=AsyncMock, return_value=row),
        patch("src.services.copilot_polling.pipeline.generate_roadmap_batch", new_callable=AsyncMock, return_value=gen_return) if gen_return else
        patch("src.services.copilot_polling.pipeline.generate_roadmap_batch", new_callable=AsyncMock),
    )


class TestDebounceGuard:
    """Tests for the 5-minute debounce mechanism."""

    @pytest.mark.asyncio
    async def test_debounce_blocks_rapid_triggers(self):
        """Second trigger within 5 minutes should be suppressed."""
        project_id = "PVT_test"
        _roadmap_last_trigger[project_id] = datetime.now(UTC)

        row = _make_mock_row()

        with (
            patch("src.services.database.get_db", return_value=MagicMock()),
            patch("src.services.settings_store.get_project_settings_row", new_callable=AsyncMock, return_value=row),
            patch("src.services.roadmap.generator.generate_roadmap_batch", new_callable=AsyncMock) as mock_gen,
        ):
            await _maybe_trigger_roadmap("token", project_id)
            # Generator should NOT have been called (debounce active)
            mock_gen.assert_not_called()

    @pytest.mark.asyncio
    async def test_debounce_allows_after_window(self):
        """Trigger after 5+ minutes should proceed."""
        project_id = "PVT_test"
        _roadmap_last_trigger[project_id] = datetime.now(UTC) - timedelta(seconds=_ROADMAP_DEBOUNCE_SECONDS + 1)

        row = _make_mock_row()
        mock_batch = MagicMock()
        mock_batch.items = []

        with (
            patch("src.services.database.get_db", return_value=MagicMock()),
            patch("src.services.settings_store.get_project_settings_row", new_callable=AsyncMock, return_value=row),
            patch("src.services.roadmap.generator.generate_roadmap_batch", new_callable=AsyncMock, return_value=mock_batch) as mock_gen,
        ):
            await _maybe_trigger_roadmap("token", project_id)
            # Generator SHOULD have been called
            mock_gen.assert_called_once()


class TestDailyCap:
    """Tests for the 10-cycle/day cap."""

    @pytest.mark.asyncio
    async def test_daily_cap_blocks_at_limit(self):
        """11th trigger on the same day should be suppressed."""
        project_id = "PVT_test"
        today = datetime.now(UTC).date()
        _roadmap_daily_count[project_id] = (today, _ROADMAP_DAILY_CAP)

        row = _make_mock_row()

        with (
            patch("src.services.database.get_db", return_value=MagicMock()),
            patch("src.services.settings_store.get_project_settings_row", new_callable=AsyncMock, return_value=row),
            patch("src.services.roadmap.generator.generate_roadmap_batch", new_callable=AsyncMock) as mock_gen,
        ):
            await _maybe_trigger_roadmap("token", project_id)
            mock_gen.assert_not_called()

    @pytest.mark.asyncio
    async def test_daily_cap_resets_on_new_day(self):
        """Counter should reset when the UTC date changes."""
        project_id = "PVT_test"
        yesterday = (datetime.now(UTC) - timedelta(days=1)).date()
        _roadmap_daily_count[project_id] = (yesterday, _ROADMAP_DAILY_CAP)

        row = _make_mock_row()
        mock_batch = MagicMock()
        mock_batch.items = []

        with (
            patch("src.services.database.get_db", return_value=MagicMock()),
            patch("src.services.settings_store.get_project_settings_row", new_callable=AsyncMock, return_value=row),
            patch("src.services.roadmap.generator.generate_roadmap_batch", new_callable=AsyncMock, return_value=mock_batch) as mock_gen,
        ):
            await _maybe_trigger_roadmap("token", project_id)
            mock_gen.assert_called_once()


class TestConditionChecks:
    """Tests for roadmap_enabled and roadmap_auto_launch conditions."""

    @pytest.mark.asyncio
    async def test_disabled_roadmap_skips(self):
        """When roadmap_enabled=False, no generation occurs."""
        row = _make_mock_row(enabled=False)

        with (
            patch("src.services.database.get_db", return_value=MagicMock()),
            patch("src.services.settings_store.get_project_settings_row", new_callable=AsyncMock, return_value=row),
            patch("src.services.roadmap.generator.generate_roadmap_batch", new_callable=AsyncMock) as mock_gen,
        ):
            await _maybe_trigger_roadmap("token", "PVT_test")
            mock_gen.assert_not_called()

    @pytest.mark.asyncio
    async def test_auto_launch_disabled_skips(self):
        """When roadmap_auto_launch=False, no generation occurs."""
        row = _make_mock_row(auto_launch=False)

        with (
            patch("src.services.database.get_db", return_value=MagicMock()),
            patch("src.services.settings_store.get_project_settings_row", new_callable=AsyncMock, return_value=row),
            patch("src.services.roadmap.generator.generate_roadmap_batch", new_callable=AsyncMock) as mock_gen,
        ):
            await _maybe_trigger_roadmap("token", "PVT_test")
            mock_gen.assert_not_called()

    @pytest.mark.asyncio
    async def test_no_settings_row_skips(self):
        """When no project settings exist, no generation occurs."""
        with (
            patch("src.services.database.get_db", return_value=MagicMock()),
            patch("src.services.settings_store.get_project_settings_row", new_callable=AsyncMock, return_value=None),
            patch("src.services.roadmap.generator.generate_roadmap_batch", new_callable=AsyncMock) as mock_gen,
        ):
            await _maybe_trigger_roadmap("token", "PVT_test")
            mock_gen.assert_not_called()
