"""Regression tests for bugs found during the bug bash (specs/025-bug-basher).

Each test covers a specific bug that was identified and fixed.
"""

from __future__ import annotations

import logging
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.services.settings_store import (
    get_effective_user_settings,
    update_global_settings,
    upsert_user_preferences,
)


# ── Fixtures ──


@pytest.fixture
async def seeded_db(mock_db, mock_settings):
    """mock_db with global settings seeded (required by settings store tests)."""
    from src.services.database import seed_global_settings

    with patch("src.services.database.get_settings", return_value=mock_settings):
        await seed_global_settings(mock_db)
    return mock_db


# =============================================================================
# Bug #1: test_settings_store — nullable field fallback to global default
# =============================================================================


class TestNullableFieldFallback:
    """Verify that setting a user preference to None falls back to the global default."""

    async def test_nullable_field_falls_back_to_global_default(self, seeded_db):
        """When a user explicitly clears a nullable field (sets to None),
        the effective setting should fall back to the global default, not remain None.

        Bug: The original test asserted fallback to 'Boykai/github-workflows' but
        the global default was never set to that value, so it was always None.
        """
        # Set global default to a known value
        await update_global_settings(seeded_db, {"default_repository": "org/repo"})

        # User sets their own value
        await upsert_user_preferences(seeded_db, "u1", {"default_repository": "user/custom"})
        eff = await get_effective_user_settings(seeded_db, "u1")
        assert eff.workflow.default_repository == "user/custom"

        # User clears their value — should fall back to global
        await upsert_user_preferences(seeded_db, "u1", {"default_repository": None})
        eff = await get_effective_user_settings(seeded_db, "u1")
        assert eff.workflow.default_repository == "org/repo"

    async def test_nullable_field_stays_none_when_global_is_none(self, seeded_db):
        """When both user preference and global default are None, effective is None."""
        # Global default_repository is None by default (mock_settings has no default_repository)
        await upsert_user_preferences(seeded_db, "u2", {"default_repository": "owner/repo"})
        await upsert_user_preferences(seeded_db, "u2", {"default_repository": None})
        eff = await get_effective_user_settings(seeded_db, "u2")
        assert eff.workflow.default_repository is None


# =============================================================================
# Bug #2: metadata_service — silent exception handler in stale fallback
# =============================================================================


class TestMetadataServiceStaleFallbackLogging:
    """Verify that the stale SQLite fallback logs errors instead of silencing them."""

    async def test_stale_fallback_logs_warning_on_sqlite_error(self, caplog):
        """When the stale SQLite fallback fails, it should log a warning
        instead of silently swallowing the exception.

        Bug: The except Exception: pass block silently swallowed all errors
        during the last-resort SQLite read, making it impossible to diagnose
        database failures.
        """
        from src.services.cache import InMemoryCache
        from src.services.metadata_service import MetadataService

        svc = MetadataService(l1_cache=InMemoryCache())

        # Make all paths fail: API fetch, initial SQLite, stale SQLite
        with (
            patch.object(svc, "_read_from_sqlite", side_effect=RuntimeError("DB gone")),
            patch.object(svc, "fetch_metadata", side_effect=RuntimeError("API down")),
            caplog.at_level(logging.WARNING),
        ):
            result = await svc.get_or_fetch("tok", "owner", "repo")

        # Should fall through to hardcoded constants
        assert result.source == "fallback"
        # The stale SQLite fallback error should now be logged
        assert any(
            "Failed to read stale metadata from SQLite" in record.message
            for record in caplog.records
        ), "Expected warning log for stale SQLite fallback failure"


# =============================================================================
# Bug #3: chores/service — SQL column name validation
# =============================================================================


class TestChoreColumnNameValidation:
    """Verify that SQL column name allowlist rejects invalid column names."""

    def test_validate_column_names_rejects_unknown_columns(self):
        """Unknown column names should raise ValueError before reaching SQL.

        Bug: The f-string SQL SET clause construction used dict keys directly
        as column names without validation. While callers currently pass safe
        Pydantic-validated keys, this is a defense-in-depth measure.
        """
        from src.services.chores.service import _validate_column_names

        # Valid columns should pass
        _validate_column_names({"schedule_type": "time", "updated_at": "2024-01-01"})

        # Invalid columns should raise
        with pytest.raises(ValueError, match="Invalid chore column names"):
            _validate_column_names({"schedule_type": "time", "DROP TABLE chores": "bad"})

    def test_validate_column_names_accepts_all_chore_model_fields(self):
        """All fields from the Chore model should be accepted."""
        from src.services.chores.service import _validate_column_names

        valid_columns = {
            "name": "test",
            "template_path": "/path",
            "template_content": "content",
            "schedule_type": "time",
            "schedule_value": 7,
            "status": "active",
            "last_triggered_at": "2024-01-01",
            "last_triggered_count": 0,
            "current_issue_number": 1,
            "current_issue_node_id": "I_1",
            "pr_number": 10,
            "pr_url": "https://example.com",
            "tracking_issue_number": 20,
            "created_at": "2024-01-01",
            "updated_at": "2024-01-01",
        }
        # Should not raise
        _validate_column_names(valid_columns)

    async def test_update_chore_rejects_sql_injection_column(self, mock_db):
        """Regression test: update_chore_fields rejects injected column names."""
        from src.services.chores.service import ChoresService

        svc = ChoresService(mock_db)

        with pytest.raises(ValueError, match="Invalid chore column names"):
            await svc.update_chore_fields("chore-1", **{"status; DROP TABLE": "bad"})
