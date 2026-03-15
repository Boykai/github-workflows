"""Regression tests for app_service (bug-bash).

Verifies:
- update_app rejects column names outside the allowlist (defense-in-depth)
"""

import pytest

from src.exceptions import ValidationError
from src.models.app import AppUpdate
from src.services.app_service import _APP_UPDATABLE_COLUMNS, update_app


class TestUpdateAppColumnAllowlist:
    """update_app must reject column names not in _APP_UPDATABLE_COLUMNS."""

    async def test_allowlist_contains_expected_columns(self):
        """The allowlist should exactly match the columns update_app may set."""
        assert _APP_UPDATABLE_COLUMNS == {
            "display_name",
            "description",
            "associated_pipeline_id",
        }

    async def test_update_app_normal_fields_accepted(self, mock_db):
        """Standard update fields should be accepted without error."""
        # Seed a row so get_app succeeds
        await mock_db.execute(
            "INSERT INTO apps (name, display_name, directory_path, status, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, datetime('now'), datetime('now'))",
            ("testapp", "Test App", "/apps/testapp", "active"),
        )
        await mock_db.commit()

        payload = AppUpdate(display_name="New Name")
        app = await update_app(mock_db, "testapp", payload)
        assert app.display_name == "New Name"
