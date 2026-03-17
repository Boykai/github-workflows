"""Unit tests for create_app_with_new_repo and create_standalone_project."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from src.models.app import AppCreate, AppStatus, RepoType

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _insert_schema(mock_db) -> None:
    """Ensure the apps table exists in the in-memory DB (handled by conftest mock_db)."""
    # mock_db from conftest already has migrations applied, so nothing extra needed.


def _new_repo_payload(**overrides) -> AppCreate:
    defaults = {
        "name": "test-app",
        "display_name": "Test App",
        "description": "A test application",
        "repo_type": RepoType.NEW_REPO,
        "repo_owner": "alice",
        "repo_visibility": "private",
        "create_project": True,
        "ai_enhance": False,
    }
    defaults.update(overrides)
    return AppCreate(**defaults)


def _mock_github_service() -> AsyncMock:
    svc = AsyncMock()
    svc.create_repository.return_value = {
        "id": 123,
        "node_id": "R_abc",
        "name": "test-app",
        "full_name": "alice/test-app",
        "html_url": "https://github.com/alice/test-app",
        "default_branch": "main",
    }
    svc.get_repository_info.return_value = {
        "repository_id": "R_abc",
        "default_branch": "main",
        "head_oid": "abc123",
    }
    svc.commit_files.return_value = "commit-sha-1"
    svc.create_project_v2.return_value = {
        "id": "PVT_proj1",
        "number": 1,
        "url": "https://github.com/users/alice/projects/1",
    }
    svc.link_project_to_repository.return_value = None
    svc._rest.return_value = {"login": "alice"}
    return svc


# ---------------------------------------------------------------------------
# Tests — create_app_with_new_repo
# ---------------------------------------------------------------------------


class TestCreateAppWithNewRepo:
    @pytest.mark.asyncio
    async def test_happy_path_with_project(self, mock_db) -> None:
        from src.services.app_service import create_app_with_new_repo

        github_svc = _mock_github_service()
        payload = _new_repo_payload()

        with patch("src.services.template_files.build_template_files", new_callable=AsyncMock) as mock_templates:
            mock_templates.return_value = [{"path": ".gitignore", "content": "node_modules/\n"}]
            app = await create_app_with_new_repo(
                mock_db, payload, access_token="tok", github_service=github_svc
            )

        assert app.name == "test-app"
        assert app.display_name == "Test App"
        assert app.status == AppStatus.ACTIVE
        assert app.repo_type == RepoType.NEW_REPO
        assert app.github_repo_url == "https://github.com/alice/test-app"
        assert app.github_project_url == "https://github.com/users/alice/projects/1"
        assert app.github_project_id == "PVT_proj1"

        github_svc.create_repository.assert_awaited_once()
        github_svc.create_project_v2.assert_awaited_once()
        github_svc.link_project_to_repository.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_happy_path_without_project(self, mock_db) -> None:
        from src.services.app_service import create_app_with_new_repo

        github_svc = _mock_github_service()
        payload = _new_repo_payload(create_project=False)

        with patch("src.services.template_files.build_template_files", new_callable=AsyncMock) as mock_templates:
            mock_templates.return_value = []
            app = await create_app_with_new_repo(
                mock_db, payload, access_token="tok", github_service=github_svc
            )

        assert app.github_repo_url == "https://github.com/alice/test-app"
        assert app.github_project_url is None
        assert app.github_project_id is None
        github_svc.create_project_v2.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_repo_failure_raises(self, mock_db) -> None:
        from src.services.app_service import create_app_with_new_repo

        github_svc = _mock_github_service()
        github_svc.create_repository.side_effect = ValueError("Repo creation failed")
        payload = _new_repo_payload()

        with pytest.raises(ValueError, match="Repo creation failed"):
            with patch("src.services.template_files.build_template_files", new_callable=AsyncMock):
                await create_app_with_new_repo(
                    mock_db, payload, access_token="tok", github_service=github_svc
                )

    @pytest.mark.asyncio
    async def test_project_failure_partial_success(self, mock_db) -> None:
        """Project creation failure after repo success should result in app with null project fields."""
        from src.services.app_service import create_app_with_new_repo

        github_svc = _mock_github_service()
        github_svc.create_project_v2.side_effect = ValueError("Project creation failed")
        payload = _new_repo_payload()

        with patch("src.services.template_files.build_template_files", new_callable=AsyncMock) as mock_templates:
            mock_templates.return_value = []
            app = await create_app_with_new_repo(
                mock_db, payload, access_token="tok", github_service=github_svc
            )

        # App should still be created — partial success
        assert app.name == "test-app"
        assert app.status == AppStatus.ACTIVE
        assert app.github_repo_url == "https://github.com/alice/test-app"
        assert app.github_project_url is None
        assert app.github_project_id is None

    @pytest.mark.asyncio
    async def test_duplicate_name_raises(self, mock_db) -> None:
        from src.exceptions import ConflictError
        from src.services.app_service import create_app_with_new_repo

        github_svc = _mock_github_service()
        payload = _new_repo_payload()

        # First creation
        with patch("src.services.template_files.build_template_files", new_callable=AsyncMock) as mock_templates:
            mock_templates.return_value = []
            await create_app_with_new_repo(
                mock_db, payload, access_token="tok", github_service=github_svc
            )

        # Second creation with same name should fail
        with pytest.raises(ConflictError):
            with patch("src.services.template_files.build_template_files", new_callable=AsyncMock) as mock_templates:
                mock_templates.return_value = []
                await create_app_with_new_repo(
                    mock_db, payload, access_token="tok", github_service=github_svc
                )

    @pytest.mark.asyncio
    async def test_missing_repo_owner_raises(self, mock_db) -> None:
        from src.exceptions import ValidationError
        from src.services.app_service import create_app_with_new_repo

        github_svc = _mock_github_service()
        payload = _new_repo_payload(repo_owner=None)

        with pytest.raises(ValidationError, match="repo_owner"):
            with patch("src.services.template_files.build_template_files", new_callable=AsyncMock):
                await create_app_with_new_repo(
                    mock_db, payload, access_token="tok", github_service=github_svc
                )


# ---------------------------------------------------------------------------
# Tests — create_standalone_project
# ---------------------------------------------------------------------------


class TestCreateStandaloneProject:
    @pytest.mark.asyncio
    async def test_happy_path_without_repo_link(self) -> None:
        from src.services.app_service import create_standalone_project

        github_svc = _mock_github_service()

        result = await create_standalone_project(
            access_token="tok",
            owner="alice",
            title="My Project",
            github_service=github_svc,
        )

        assert result["project_id"] == "PVT_proj1"
        assert result["project_number"] == 1
        assert result["project_url"] == "https://github.com/users/alice/projects/1"
        github_svc.create_project_v2.assert_awaited_once_with("tok", owner="alice", title="My Project")
        github_svc.link_project_to_repository.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_happy_path_with_repo_link(self) -> None:
        from src.services.app_service import create_standalone_project

        github_svc = _mock_github_service()

        result = await create_standalone_project(
            access_token="tok",
            owner="alice",
            title="Linked Project",
            github_service=github_svc,
            repo_owner="alice",
            repo_name="my-repo",
        )

        assert result["project_id"] == "PVT_proj1"
        github_svc.link_project_to_repository.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_linking_failure_is_non_blocking(self) -> None:
        from src.services.app_service import create_standalone_project

        github_svc = _mock_github_service()
        github_svc.link_project_to_repository.side_effect = ValueError("Link failed")

        # Should NOT raise
        result = await create_standalone_project(
            access_token="tok",
            owner="alice",
            title="Project",
            github_service=github_svc,
            repo_owner="alice",
            repo_name="my-repo",
        )
        assert result["project_id"] == "PVT_proj1"

    @pytest.mark.asyncio
    async def test_project_creation_failure_raises(self) -> None:
        from src.services.app_service import create_standalone_project

        github_svc = _mock_github_service()
        github_svc.create_project_v2.side_effect = ValueError("GitHub error")

        with pytest.raises(ValueError, match="GitHub error"):
            await create_standalone_project(
                access_token="tok",
                owner="alice",
                title="Fail Project",
                github_service=github_svc,
            )
