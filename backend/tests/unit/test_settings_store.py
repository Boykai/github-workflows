"""Unit tests for settings store operations.

Covers:
- get_global_settings() / update_global_settings()
- upsert_user_preferences() / get_effective_user_settings()
- upsert_project_settings() / get_effective_project_settings()
- flatten_user_preferences_update() / flatten_global_settings_update()
"""

from unittest.mock import patch

import pytest

from src.services.database import seed_global_settings
from src.services.settings_store import (
    flatten_global_settings_update,
    flatten_user_preferences_update,
    get_effective_project_settings,
    get_effective_user_settings,
    get_global_settings,
    update_global_settings,
    upsert_project_settings,
    upsert_user_preferences,
)

# ── Helper to seed global settings before each test ──


@pytest.fixture
async def seeded_db(mock_db, mock_settings):
    """mock_db with global settings seeded (required by most store functions)."""
    with patch("src.services.database.get_settings", return_value=mock_settings):
        await seed_global_settings(mock_db)
    return mock_db


# =============================================================================
# Global settings
# =============================================================================


class TestGetGlobalSettings:
    async def test_returns_seeded_defaults(self, seeded_db):
        gs = await get_global_settings(seeded_db)
        assert gs.ai.provider.value == "copilot"
        assert gs.display.theme.value == "light"
        assert gs.display.default_view.value == "chat"

    async def test_raises_if_not_seeded(self, mock_db):
        with pytest.raises(RuntimeError, match="not found"):
            await get_global_settings(mock_db)


class TestUpdateGlobalSettings:
    async def test_updates_ai_provider(self, seeded_db):
        result = await update_global_settings(seeded_db, {"ai_provider": "azure_openai"})
        assert result.ai.provider.value == "azure_openai"

    async def test_empty_updates_returns_current(self, seeded_db):
        result = await update_global_settings(seeded_db, {})
        assert result.ai.provider.value == "copilot"

    async def test_multiple_fields(self, seeded_db):
        result = await update_global_settings(
            seeded_db,
            {"theme": "dark", "ai_temperature": 0.5},
        )
        assert result.display.theme.value == "dark"
        assert result.ai.temperature == 0.5


# =============================================================================
# User preferences
# =============================================================================


class TestUpsertUserPreferences:
    async def test_insert_new_user(self, seeded_db):
        await upsert_user_preferences(seeded_db, "user1", {"theme": "dark"})
        eff = await get_effective_user_settings(seeded_db, "user1")
        assert eff.display.theme.value == "dark"

    async def test_update_existing_user(self, seeded_db):
        await upsert_user_preferences(seeded_db, "user1", {"theme": "dark"})
        await upsert_user_preferences(seeded_db, "user1", {"theme": "light"})
        eff = await get_effective_user_settings(seeded_db, "user1")
        assert eff.display.theme.value == "light"


class TestGetEffectiveUserSettings:
    async def test_defaults_from_global(self, seeded_db):
        """User with no preferences should get global defaults."""
        eff = await get_effective_user_settings(seeded_db, "new_user")
        assert eff.ai.provider.value == "copilot"
        assert eff.display.default_view.value == "chat"

    async def test_user_overrides_global(self, seeded_db):
        await upsert_user_preferences(seeded_db, "u1", {"default_view": "board"})
        eff = await get_effective_user_settings(seeded_db, "u1")
        assert eff.display.default_view.value == "board"
        # Other fields still from global
        assert eff.ai.provider.value == "copilot"


# =============================================================================
# Project settings
# =============================================================================


class TestUpsertProjectSettings:
    async def test_insert_new_project(self, seeded_db):
        await upsert_project_settings(
            seeded_db, "u1", "proj1", {"board_display_config": '{"show_labels": true}'}
        )
        eff = await get_effective_project_settings(seeded_db, "u1", "proj1")
        assert eff.project.project_id == "proj1"
        assert eff.project.board_display_config is not None

    async def test_update_existing_project(self, seeded_db):
        await upsert_project_settings(
            seeded_db, "u1", "proj1", {"board_display_config": '{"show_labels": true}'}
        )
        await upsert_project_settings(
            seeded_db, "u1", "proj1", {"board_display_config": '{"show_labels": false}'}
        )
        eff = await get_effective_project_settings(seeded_db, "u1", "proj1")
        assert eff.project.board_display_config is not None


class TestGetEffectiveProjectSettings:
    async def test_inherits_user_and_global(self, seeded_db):
        """Project settings should layer: global → user → project."""
        await upsert_user_preferences(seeded_db, "u1", {"theme": "dark"})
        eff = await get_effective_project_settings(seeded_db, "u1", "proj1")
        assert eff.display.theme.value == "dark"
        assert eff.ai.provider.value == "copilot"

    async def test_empty_project(self, seeded_db):
        eff = await get_effective_project_settings(seeded_db, "u1", "proj1")
        assert eff.project.project_id == "proj1"
        assert eff.project.board_display_config is None
        assert eff.project.agent_pipeline_mappings is None


# =============================================================================
# Flattening helpers
# =============================================================================


class TestFlattenUserPreferencesUpdate:
    def test_flat_ai_section(self):
        result = flatten_user_preferences_update({"ai": {"provider": "copilot", "model": "gpt-4"}})
        assert result == {"ai_provider": "copilot", "ai_model": "gpt-4"}

    def test_flat_display_section(self):
        result = flatten_user_preferences_update({"display": {"theme": "dark"}})
        assert result == {"theme": "dark"}

    def test_bool_to_int(self):
        result = flatten_user_preferences_update({"display": {"sidebar_collapsed": True}})
        assert result["sidebar_collapsed"] == 1

    def test_empty_returns_empty(self):
        assert flatten_user_preferences_update({}) == {}

    def test_multiple_sections(self):
        result = flatten_user_preferences_update(
            {
                "ai": {"temperature": 0.5},
                "notifications": {"task_status_change": False},
            }
        )
        assert result["ai_temperature"] == 0.5
        assert result["notify_task_status_change"] == 0


class TestFlattenGlobalSettingsUpdate:
    def test_includes_user_fields(self):
        result = flatten_global_settings_update({"ai": {"provider": "copilot"}})
        assert "ai_provider" in result

    def test_handles_allowed_models(self):
        result = flatten_global_settings_update({"allowed_models": ["gpt-4", "gpt-3.5"]})
        assert '"gpt-4"' in result["allowed_models"]

    def test_allowed_models_none_skipped(self):
        result = flatten_global_settings_update({"allowed_models": None})
        assert "allowed_models" not in result
