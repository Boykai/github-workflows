"""Unit tests for app lifecycle service helpers."""

from __future__ import annotations

import json

import pytest

from src.exceptions import ConflictError, NotFoundError, ValidationError
from src.models.app import AppCreate, AppStatus
from src.services import app_service


@pytest.fixture
def apps_dir(tmp_path, monkeypatch):
    """Redirect app scaffolding to a temp apps directory for filesystem assertions."""
    apps_dir = tmp_path / "apps"
    apps_dir.mkdir()
    monkeypatch.setattr(app_service, "_APPS_DIR", apps_dir)
    monkeypatch.setattr(app_service, "_APPS_DIR_RESOLVED", apps_dir.resolve())
    return apps_dir


class TestValidateAppName:
    def test_rejects_reserved_names(self):
        with pytest.raises(ValidationError, match="reserved"):
            app_service.validate_app_name("admin")

    def test_rejects_path_traversal_like_input(self):
        with pytest.raises(ValidationError, match="Invalid app name"):
            app_service.validate_app_name("../escape")


class TestCreateApp:
    @pytest.mark.anyio
    async def test_scaffolds_directory_and_persists_app(self, mock_db, apps_dir):
        payload = AppCreate(
            name="demo-app",
            display_name="Demo App",
            description="Created for regression coverage.",
        )

        created = await app_service.create_app(mock_db, payload)

        assert created.name == "demo-app"
        assert created.display_name == "Demo App"
        assert created.directory_path == "apps/demo-app"
        assert created.status == AppStatus.ACTIVE

        app_dir = apps_dir / "demo-app"
        assert app_dir.is_dir()
        assert "Created for regression coverage." in (app_dir / "README.md").read_text(
            encoding="utf-8"
        )
        config = json.loads((app_dir / "config.json").read_text(encoding="utf-8"))
        assert config["name"] == "demo-app"
        assert config["display_name"] == "Demo App"
        assert (app_dir / "src" / ".gitkeep").exists()
        assert (app_dir / "CHANGELOG.md").exists()
        assert (app_dir / "docker-compose.yml").exists()

    @pytest.mark.anyio
    async def test_duplicate_app_name_raises_conflict(self, mock_db, apps_dir):
        payload = AppCreate(
            name="demo-app",
            display_name="Demo App",
            description="Created for regression coverage.",
        )

        await app_service.create_app(mock_db, payload)

        with pytest.raises(ConflictError, match="already exists"):
            await app_service.create_app(mock_db, payload)


class TestDeleteApp:
    @pytest.mark.anyio
    async def test_requires_stopped_app_before_delete(self, mock_db, apps_dir):
        payload = AppCreate(name="demo-app", display_name="Demo App", description="Lifecycle app")
        await app_service.create_app(mock_db, payload)

        with pytest.raises(ValidationError, match="must stop the app first"):
            await app_service.delete_app(mock_db, payload.name)

        status = await app_service.stop_app(mock_db, payload.name)
        assert status.status == AppStatus.STOPPED

        await app_service.delete_app(mock_db, payload.name)

        assert not (apps_dir / "demo-app").exists()
        with pytest.raises(NotFoundError, match="not found"):
            await app_service.get_app(mock_db, payload.name)
