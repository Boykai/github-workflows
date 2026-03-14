"""Regression tests — blocking feature removal.

Verifies that the blocking feature has been completely removed from the
codebase: no importable modules, no database schema artifacts, no API
endpoints, and no model fields.  These tests guard against accidental
re-introduction.
"""

from __future__ import annotations

import importlib

import aiosqlite
import pytest

# ── Module-level removal ────────────────────────────────────────


class TestBlockingModulesRemoved:
    """Backend blocking modules must not be importable."""

    def test_blocking_model_not_importable(self):
        """src.models.blocking must not exist."""
        with pytest.raises((ImportError, ModuleNotFoundError)):
            importlib.import_module("src.models.blocking")

    def test_blocking_queue_service_not_importable(self):
        """src.services.blocking_queue must not exist."""
        with pytest.raises((ImportError, ModuleNotFoundError)):
            importlib.import_module("src.services.blocking_queue")

    def test_blocking_queue_store_not_importable(self):
        """src.services.blocking_queue_store must not exist."""
        with pytest.raises((ImportError, ModuleNotFoundError)):
            importlib.import_module("src.services.blocking_queue_store")


# ── Schema removal (migration 021) ─────────────────────────────


class TestBlockingSchemaRemoved:
    """After all migrations, no blocking-related schema artifacts remain."""

    async def test_blocking_queue_table_dropped(self, mock_db: aiosqlite.Connection):
        """blocking_queue table must not exist after migrations."""
        cursor = await mock_db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='blocking_queue'"
        )
        row = await cursor.fetchone()
        assert row is None, "blocking_queue table still exists after migration 021"

    async def test_pipeline_configs_no_blocking_column(self, mock_db: aiosqlite.Connection):
        """pipeline_configs.blocking column must not exist."""
        cursor = await mock_db.execute("PRAGMA table_info(pipeline_configs)")
        columns = [r[1] if isinstance(r, tuple) else r["name"] for r in await cursor.fetchall()]
        assert "blocking" not in columns, "pipeline_configs still has a 'blocking' column"

    async def test_chores_no_blocking_column(self, mock_db: aiosqlite.Connection):
        """chores.blocking column must not exist."""
        cursor = await mock_db.execute("PRAGMA table_info(chores)")
        columns = [r[1] if isinstance(r, tuple) else r["name"] for r in await cursor.fetchall()]
        assert "blocking" not in columns, "chores table still has a 'blocking' column"

    async def test_project_settings_no_blocking_override_column(
        self, mock_db: aiosqlite.Connection
    ):
        """project_settings.pipeline_blocking_override column must not exist."""
        cursor = await mock_db.execute("PRAGMA table_info(project_settings)")
        columns = [r[1] if isinstance(r, tuple) else r["name"] for r in await cursor.fetchall()]
        assert "pipeline_blocking_override" not in columns, (
            "project_settings still has 'pipeline_blocking_override' column"
        )


# ── API endpoint removal ────────────────────────────────────────


class TestBlockingAPIEndpointsRemoved:
    """No blocking-related API endpoints should be exposed."""

    async def test_no_blocking_queue_endpoints(self, client):
        """GET /api/v1/board/projects/.../blocking-queue should 404 or 405."""
        resp = await client.get("/api/v1/board/projects/PVT_proj1/blocking-queue")
        assert resp.status_code in (404, 405), (
            f"Blocking queue endpoint still responds with {resp.status_code}"
        )

    async def test_no_blocking_queue_enqueue_endpoint(self, client):
        """POST to blocking-queue enqueue should 404 or 405."""
        resp = await client.post(
            "/api/v1/board/projects/PVT_proj1/blocking-queue/enqueue",
            json={"issue_number": 1},
        )
        assert resp.status_code in (404, 405, 422), (
            f"Blocking enqueue endpoint still responds with {resp.status_code}"
        )

    async def test_no_blocking_queue_activate_endpoint(self, client):
        """POST to blocking-queue activate should 404 or 405."""
        resp = await client.post(
            "/api/v1/board/projects/PVT_proj1/blocking-queue/1/activate",
        )
        assert resp.status_code in (404, 405), (
            f"Blocking activate endpoint still responds with {resp.status_code}"
        )

    async def test_no_blocking_queue_complete_endpoint(self, client):
        """POST to blocking-queue complete should 404 or 405."""
        resp = await client.post(
            "/api/v1/board/projects/PVT_proj1/blocking-queue/1/complete",
        )
        assert resp.status_code in (404, 405), (
            f"Blocking complete endpoint still responds with {resp.status_code}"
        )


# ── Model field removal ─────────────────────────────────────────


class TestBlockingModelFieldsRemoved:
    """Pydantic and dataclass models must not contain blocking-related fields."""

    def test_pipeline_config_no_blocking_field(self):
        from src.models.pipeline import PipelineConfig

        fields = set(PipelineConfig.model_fields.keys())
        assert "blocking" not in fields
        assert "is_blocking" not in fields
        assert "pipeline_blocking_override" not in fields

    def test_pipeline_config_create_no_blocking_field(self):
        from src.models.pipeline import PipelineConfigCreate

        fields = set(PipelineConfigCreate.model_fields.keys())
        assert "blocking" not in fields
        assert "is_blocking" not in fields

    def test_chore_models_no_blocking_field(self):
        from src.models.chores import Chore, ChoreCreate

        for model in (Chore, ChoreCreate):
            fields = set(model.model_fields.keys())
            assert "blocking" not in fields, f"{model.__name__} still has 'blocking' field"
            assert "is_blocking" not in fields, f"{model.__name__} still has 'is_blocking' field"

    def test_pipeline_state_no_blocking_field(self):
        from src.services.workflow_orchestrator.models import PipelineState

        field_names = {f.name for f in PipelineState.__dataclass_fields__.values()}
        assert "is_blocking" not in field_names
        assert "blocking" not in field_names
        assert "blocking_source_issue" not in field_names

    def test_recommendation_model_no_blocking_field(self):
        from src.models.recommendation import IssueRecommendation

        fields = set(IssueRecommendation.model_fields.keys())
        assert "blocking" not in fields
        assert "is_blocking" not in fields


# ── Constants removal ───────────────────────────────────────────


class TestBlockingConstantsRemoved:
    """No blocking-related constants in src.constants."""

    def test_no_blocking_labels(self):
        import src.constants as const

        # Check that none of the module-level names reference blocking
        blocking_names = [
            name for name in dir(const) if "blocking" in name.lower() and not name.startswith("_")
        ]
        assert blocking_names == [], f"Blocking constants still exist: {blocking_names}"
