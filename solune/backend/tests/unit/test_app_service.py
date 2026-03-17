from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from src.exceptions import ConflictError, NotFoundError, ValidationError
from src.models.app import AppCreate, AppStatus, AppUpdate, RepoType
from src.services.app_service import (
    _build_scaffold_files,
    create_app,
    delete_app,
    get_app,
    get_app_status,
    list_apps,
    resolve_working_directory,
    start_app,
    stop_app,
    update_app,
    validate_app_name,
)


async def _insert_app(mock_db, **overrides) -> None:
    defaults = {
        "name": "demo-app",
        "display_name": "Demo App",
        "description": "Original description",
        "directory_path": "apps/demo-app",
        "associated_pipeline_id": None,
        "status": AppStatus.STOPPED.value,
        "repo_type": RepoType.SAME_REPO.value,
        "external_repo_url": None,
        "port": 3000,
        "error_message": None,
        "created_at": "2026-03-16T00:00:00Z",
        "updated_at": "2026-03-16T00:00:00Z",
    }
    defaults.update(overrides)
    await mock_db.execute(
        """
        INSERT INTO apps (
            name, display_name, description, directory_path,
            associated_pipeline_id, status, repo_type, external_repo_url,
            port, error_message, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            defaults["name"],
            defaults["display_name"],
            defaults["description"],
            defaults["directory_path"],
            defaults["associated_pipeline_id"],
            defaults["status"],
            defaults["repo_type"],
            defaults["external_repo_url"],
            defaults["port"],
            defaults["error_message"],
            defaults["created_at"],
            defaults["updated_at"],
        ),
    )
    await mock_db.commit()


class TestValidateAppName:
    def test_accepts_valid_name(self):
        validate_app_name("valid-app-1")

    @pytest.mark.parametrize("name", ["A", "bad_name", "api", "../evil", "bad/slash"])
    def test_rejects_invalid_names(self, name: str):
        with pytest.raises(ValidationError):
            validate_app_name(name)


class TestBuildScaffoldFiles:
    def test_creates_expected_scaffold_structure(self):
        files = _build_scaffold_files("demo-app", "Demo App", "Example description")

        assert len(files) == 5
        assert files[0]["path"] == "apps/demo-app/README.md"
        assert files[1]["path"] == "apps/demo-app/config.json"
        assert files[2]["path"] == "apps/demo-app/src/.gitkeep"
        assert "Demo App" in files[0]["content"]
        assert "Example description" in files[0]["content"]


class TestAppServiceCrud:
    @pytest.mark.asyncio
    async def test_create_app_inserts_scaffolded_record(self, mock_db):
        github_service = AsyncMock()
        github_service.get_branch_head_oid.return_value = "head-sha"
        github_service.commit_files.return_value = "commit-sha"
        payload = AppCreate(
            name="demo-app",
            display_name="Demo App",
            description="Example description",
            branch="app/demo-app",
            ai_enhance=False,
        )

        with patch(
            "src.services.app_service.get_settings",
            return_value=SimpleNamespace(default_repo_owner="owner", default_repo_name="repo"),
        ):
            app = await create_app(
                mock_db,
                payload,
                access_token="token",
                github_service=github_service,
            )

        assert app.name == "demo-app"
        assert app.display_name == "Demo App"
        assert app.description == "Example description"
        assert app.status == AppStatus.ACTIVE
        github_service.get_branch_head_oid.assert_awaited_once_with(
            "token", "owner", "repo", "app/demo-app"
        )
        github_service.commit_files.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_create_app_rejects_duplicates(self, mock_db):
        await _insert_app(mock_db)

        with pytest.raises(ConflictError):
            await create_app(
                mock_db,
                AppCreate(
                    name="demo-app",
                    display_name="Duplicate",
                    description="duplicate",
                    branch="app/demo-app",
                    ai_enhance=False,
                ),
                access_token="token",
                github_service=AsyncMock(),
            )

    @pytest.mark.asyncio
    async def test_create_app_requires_existing_branch(self, mock_db):
        github_service = AsyncMock()
        github_service.get_branch_head_oid.return_value = None

        with (
            patch(
                "src.services.app_service.get_settings",
                return_value=SimpleNamespace(default_repo_owner="owner", default_repo_name="repo"),
            ),
            pytest.raises(ValidationError, match="Branch"),
        ):
            await create_app(
                mock_db,
                AppCreate(
                    name="demo-app",
                    display_name="Demo App",
                    description="Example description",
                    branch="app/demo-app",
                    ai_enhance=False,
                ),
                access_token="token",
                github_service=github_service,
            )

    @pytest.mark.asyncio
    async def test_list_get_and_update_app(self, mock_db):
        await _insert_app(mock_db)
        await _insert_app(
            mock_db, name="other-app", display_name="Other App", status=AppStatus.ACTIVE.value
        )

        apps = await list_apps(mock_db)
        stopped_apps = await list_apps(mock_db, status_filter=AppStatus.STOPPED)
        app = await get_app(mock_db, "demo-app")
        updated = await update_app(
            mock_db,
            "demo-app",
            AppUpdate(display_name="Renamed Demo", description="Updated description"),
        )

        assert [app.name for app in apps] == ["other-app", "demo-app"]
        assert [app.name for app in stopped_apps] == ["demo-app"]
        assert app.display_name == "Demo App"
        assert updated.display_name == "Renamed Demo"
        assert updated.description == "Updated description"
        assert updated.associated_pipeline_id is None

    @pytest.mark.asyncio
    async def test_get_app_raises_for_missing_record(self, mock_db):
        with pytest.raises(NotFoundError):
            await get_app(mock_db, "missing-app")


class TestAppServiceLifecycle:
    @pytest.mark.asyncio
    async def test_start_stop_status_and_delete_lifecycle(self, mock_db):
        await _insert_app(mock_db, status=AppStatus.STOPPED.value, port=4321)

        started = await start_app(mock_db, "demo-app")
        status = await get_app_status(mock_db, "demo-app")
        stopped = await stop_app(mock_db, "demo-app")

        assert started.status == AppStatus.ACTIVE
        assert status.status == AppStatus.ACTIVE
        assert stopped.status == AppStatus.STOPPED
        assert stopped.port is None

        await delete_app(mock_db, "demo-app")

        with pytest.raises(NotFoundError):
            await get_app(mock_db, "demo-app")

    @pytest.mark.asyncio
    async def test_delete_rejects_active_app(self, mock_db):
        await _insert_app(mock_db, status=AppStatus.ACTIVE.value)

        with pytest.raises(ValidationError, match="must stop the app first"):
            await delete_app(mock_db, "demo-app")

    @pytest.mark.asyncio
    async def test_invalid_transitions_raise_validation_errors(self, mock_db):
        await _insert_app(mock_db, name="creating-app", status=AppStatus.CREATING.value, port=None)
        await _insert_app(mock_db, name="error-app", status=AppStatus.ERROR.value, port=None)

        with pytest.raises(ValidationError, match="invalid transition"):
            await stop_app(mock_db, "creating-app")

        with pytest.raises(ValidationError, match="invalid transition"):
            await start_app(mock_db, "error-app")


class TestResolveWorkingDirectory:
    def test_uses_app_directory_when_active_app_present(self):
        assert resolve_working_directory("demo-app") == "apps/demo-app"

    def test_defaults_to_platform_directory(self):
        assert resolve_working_directory(None) == "solune"
