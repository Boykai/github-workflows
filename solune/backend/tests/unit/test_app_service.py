from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from src.exceptions import ConflictError, NotFoundError, ValidationError
from src.models.app import AppCreate, AppStatus, AppUpdate, RepoType
from src.services.app_service import (
    _APP_UPDATABLE_COLUMNS,
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

    def test_updatable_columns_whitelist_exists(self):
        """Regression: _APP_UPDATABLE_COLUMNS must guard dynamic SQL SET clauses."""
        assert isinstance(_APP_UPDATABLE_COLUMNS, frozenset)
        assert _APP_UPDATABLE_COLUMNS == frozenset(
            {"display_name", "description", "associated_pipeline_id"}
        )

    @pytest.mark.asyncio
    async def test_update_app_raises_validation_error_when_whitelist_rejects_payload(
        self, mock_db, monkeypatch
    ):
        """Regression: whitelist mismatches should surface as API-safe validation errors."""
        await _insert_app(mock_db)
        monkeypatch.setattr("src.services.app_service._APP_UPDATABLE_COLUMNS", frozenset())

        with pytest.raises(ValidationError) as exc_info:
            await update_app(mock_db, "demo-app", AppUpdate(display_name="Renamed Demo"))

        assert exc_info.value.message == "Invalid fields in update payload."
        assert exc_info.value.details == {"invalid_fields": ["display_name"]}


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


class TestExternalRepoScaffoldRouting:
    """T008: Verify external-repo scaffold uses parsed owner/repo from URL."""

    @pytest.mark.asyncio
    async def test_external_repo_scaffold_uses_parsed_url(self, mock_db):
        github_service = AsyncMock()
        github_service.get_branch_head_oid.return_value = "ext-head-sha"
        github_service.commit_files.return_value = "ext-commit-sha"
        payload = AppCreate(
            name="ext-app",
            display_name="Ext App",
            description="External app",
            branch="main",
            repo_type=RepoType.EXTERNAL_REPO,
            external_repo_url="https://github.com/ext-owner/ext-repo",
            ai_enhance=False,
        )

        app = await create_app(
            mock_db,
            payload,
            access_token="token",
            github_service=github_service,
        )

        assert app.name == "ext-app"
        assert app.status == AppStatus.ACTIVE
        github_service.get_branch_head_oid.assert_awaited_once_with(
            "token", "ext-owner", "ext-repo", "main"
        )
        commit_call = github_service.commit_files.call_args
        assert commit_call[1]["owner"] == "ext-owner"
        assert commit_call[1]["repo"] == "ext-repo"

    @pytest.mark.asyncio
    async def test_external_repo_permission_error_surfaces(self, mock_db):
        github_service = AsyncMock()
        github_service.get_branch_head_oid.side_effect = Exception("403 Forbidden")
        payload = AppCreate(
            name="ext-app",
            display_name="Ext App",
            branch="main",
            repo_type=RepoType.EXTERNAL_REPO,
            external_repo_url="https://github.com/other/private-repo",
            ai_enhance=False,
        )

        with pytest.raises(Exception, match="403 Forbidden"):
            await create_app(
                mock_db,
                payload,
                access_token="token",
                github_service=github_service,
            )


class TestExternalRepoUrlModelValidation:
    """T009: Verify AppCreate model validation for external_repo_url."""

    def test_valid_external_url_passes(self):
        payload = AppCreate(
            name="ext-app",
            display_name="Ext",
            branch="main",
            repo_type=RepoType.EXTERNAL_REPO,
            external_repo_url="https://github.com/owner/repo",
        )
        assert payload.external_repo_url == "https://github.com/owner/repo"

    def test_external_url_with_git_suffix_passes(self):
        payload = AppCreate(
            name="ext-app",
            display_name="Ext",
            branch="main",
            repo_type=RepoType.EXTERNAL_REPO,
            external_repo_url="https://github.com/owner/repo.git",
        )
        assert payload.external_repo_url == "https://github.com/owner/repo.git"

    def test_missing_url_for_external_repo_raises(self):
        from pydantic import ValidationError as PydanticValidationError

        with pytest.raises(PydanticValidationError, match="external_repo_url is required"):
            AppCreate(
                name="ext-app",
                display_name="Ext",
                branch="main",
                repo_type=RepoType.EXTERNAL_REPO,
            )

    def test_invalid_url_for_external_repo_raises(self):
        from pydantic import ValidationError as PydanticValidationError

        with pytest.raises(PydanticValidationError):
            AppCreate(
                name="ext-app",
                display_name="Ext",
                branch="main",
                repo_type=RepoType.EXTERNAL_REPO,
                external_repo_url="https://notgithub.com/owner/repo",
            )

    def test_same_repo_does_not_require_url(self):
        payload = AppCreate(
            name="sr-app",
            display_name="SR",
            branch="main",
            repo_type=RepoType.SAME_REPO,
        )
        assert payload.external_repo_url is None

    def test_new_repo_does_not_require_url(self):
        payload = AppCreate(
            name="nr-app",
            display_name="NR",
            branch="main",
            repo_type=RepoType.NEW_REPO,
        )
        assert payload.external_repo_url is None


class TestExternalRepoProjectAutoCreation:
    """T012: Verify external-repo with pipeline triggers project auto-creation."""

    @staticmethod
    async def _insert_pipeline(db, pipeline_id: str = "pipe-ext") -> None:
        await db.execute(
            "INSERT INTO pipeline_configs (id, project_id, name, created_at, updated_at) "
            "VALUES (?, ?, ?, datetime('now'), datetime('now'))",
            (pipeline_id, "PVT_test", "Test Pipeline"),
        )
        await db.commit()

    @pytest.mark.asyncio
    async def test_project_created_and_stored(self, mock_db):
        await self._insert_pipeline(mock_db, "pipe-ext")
        github_service = AsyncMock()
        github_service.get_branch_head_oid.return_value = "head-sha"
        github_service.commit_files.return_value = "commit-sha"
        github_service.create_project_v2.return_value = {
            "id": "PVT_ext_proj",
            "url": "https://github.com/users/ext-owner/projects/1",
        }
        github_service.get_repository_info.return_value = {"node_id": "R_ext123"}
        github_service.link_project_to_repository.return_value = None

        payload = AppCreate(
            name="ext-proj-app",
            display_name="Ext Proj App",
            branch="main",
            repo_type=RepoType.EXTERNAL_REPO,
            external_repo_url="https://github.com/ext-owner/ext-repo",
            pipeline_id="pipe-ext",
            ai_enhance=False,
        )

        app = await create_app(
            mock_db,
            payload,
            access_token="token",
            github_service=github_service,
        )

        assert app.github_project_id == "PVT_ext_proj"
        assert app.github_project_url == "https://github.com/users/ext-owner/projects/1"
        github_service.create_project_v2.assert_awaited_once_with(
            "token", owner="ext-owner", title="Ext Proj App"
        )
        github_service.link_project_to_repository.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_project_creation_failure_is_non_fatal(self, mock_db):
        await self._insert_pipeline(mock_db, "pipe-ext")
        github_service = AsyncMock()
        github_service.get_branch_head_oid.return_value = "head-sha"
        github_service.commit_files.return_value = "commit-sha"
        github_service.create_project_v2.side_effect = Exception("Project creation failed")

        payload = AppCreate(
            name="ext-fail-app",
            display_name="Ext Fail App",
            branch="main",
            repo_type=RepoType.EXTERNAL_REPO,
            external_repo_url="https://github.com/ext-owner/ext-repo",
            pipeline_id="pipe-ext",
            ai_enhance=False,
        )

        app = await create_app(
            mock_db,
            payload,
            access_token="token",
            github_service=github_service,
        )

        assert app.name == "ext-fail-app"
        assert app.github_project_id is None
        assert app.github_project_url is None

    @pytest.mark.asyncio
    async def test_no_project_created_without_pipeline(self, mock_db):
        github_service = AsyncMock()
        github_service.get_branch_head_oid.return_value = "head-sha"
        github_service.commit_files.return_value = "commit-sha"

        payload = AppCreate(
            name="ext-no-pipe",
            display_name="Ext No Pipe",
            branch="main",
            repo_type=RepoType.EXTERNAL_REPO,
            external_repo_url="https://github.com/ext-owner/ext-repo",
            ai_enhance=False,
        )

        app = await create_app(
            mock_db,
            payload,
            access_token="token",
            github_service=github_service,
        )

        assert app.github_project_id is None
        github_service.create_project_v2.assert_not_awaited()
