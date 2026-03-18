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


async def _insert_pipeline_config(db, pipeline_id: str = "pipe-123") -> None:
    """Insert a fake pipeline_configs record to satisfy FK constraints."""
    await db.execute(
        """INSERT INTO pipeline_configs (id, project_id, name, created_at, updated_at)
        VALUES (?, 'proj-1', 'Test Pipeline', '2024-01-01T00:00:00Z', '2024-01-01T00:00:00Z')""",
        (pipeline_id,),
    )
    await db.commit()


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
    svc.set_repository_secret.return_value = None
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

        with patch(
            "src.services.template_files.build_template_files", new_callable=AsyncMock
        ) as mock_templates:
            mock_templates.return_value = ([{"path": ".gitignore", "content": "node_modules/\n"}], [])
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

        with patch(
            "src.services.template_files.build_template_files", new_callable=AsyncMock
        ) as mock_templates:
            mock_templates.return_value = ([], [])
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

        with patch(
            "src.services.template_files.build_template_files", new_callable=AsyncMock
        ) as mock_templates:
            mock_templates.return_value = ([], [])
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
        with patch(
            "src.services.template_files.build_template_files", new_callable=AsyncMock
        ) as mock_templates:
            mock_templates.return_value = ([], [])
            await create_app_with_new_repo(
                mock_db, payload, access_token="tok", github_service=github_svc
            )

        # Second creation with same name should fail
        with pytest.raises(ConflictError):
            with patch(
                "src.services.template_files.build_template_files", new_callable=AsyncMock
            ) as mock_templates:
                mock_templates.return_value = ([], [])
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
        github_svc.create_project_v2.assert_awaited_once_with(
            "tok", owner="alice", title="My Project"
        )
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


# ---------------------------------------------------------------------------
# Tests — AppCreate.validate_azure_credentials (paired-field model validator)
# ---------------------------------------------------------------------------


class TestAppCreateAzureValidation:
    """Validates the @model_validator that enforces paired Azure credentials."""

    def test_both_omitted_is_valid(self) -> None:
        payload = AppCreate(
            name="my-app",
            display_name="My App",
            repo_type="new-repo",
            repo_owner="alice",
        )
        assert payload.azure_client_id is None
        assert payload.azure_client_secret is None

    def test_both_provided_is_valid(self) -> None:
        payload = AppCreate(
            name="my-app",
            display_name="My App",
            repo_type="new-repo",
            repo_owner="alice",
            azure_client_id="client-id-value",
            azure_client_secret="client-secret-value",
        )
        assert payload.azure_client_id == "client-id-value"
        assert payload.azure_client_secret == "client-secret-value"

    def test_only_client_id_raises(self) -> None:
        from pydantic import ValidationError as PydanticValidationError

        with pytest.raises(PydanticValidationError, match="both be provided or both omitted"):
            AppCreate(
                name="my-app",
                display_name="My App",
                repo_type="new-repo",
                repo_owner="alice",
                azure_client_id="client-id-value",
                # azure_client_secret omitted
            )

    def test_only_client_secret_raises(self) -> None:
        from pydantic import ValidationError as PydanticValidationError

        with pytest.raises(PydanticValidationError, match="both be provided or both omitted"):
            AppCreate(
                name="my-app",
                display_name="My App",
                repo_type="new-repo",
                repo_owner="alice",
                # azure_client_id omitted
                azure_client_secret="client-secret-value",
            )

    def test_empty_string_client_id_rejected_by_min_length(self) -> None:
        from pydantic import ValidationError as PydanticValidationError

        with pytest.raises(PydanticValidationError):
            AppCreate(
                name="my-app",
                display_name="My App",
                repo_type="new-repo",
                repo_owner="alice",
                azure_client_id="",  # min_length=1 should reject this
                azure_client_secret="secret",
            )


# ---------------------------------------------------------------------------
# Tests — create_app_with_new_repo with Azure credentials
# ---------------------------------------------------------------------------


class TestCreateAppWithNewRepoAzureCredentials:
    """Validate Azure secrets storage in create_app_with_new_repo."""

    @pytest.mark.asyncio
    async def test_stores_both_secrets_when_provided(self, mock_db) -> None:
        from src.services.app_service import create_app_with_new_repo

        github_svc = _mock_github_service()
        payload = _new_repo_payload(
            azure_client_id="my-client-id",
            azure_client_secret="my-client-secret",
        )

        with patch(
            "src.services.template_files.build_template_files", new_callable=AsyncMock
        ) as mock_templates:
            mock_templates.return_value = ([], [])
            app = await create_app_with_new_repo(
                mock_db, payload, access_token="tok", github_service=github_svc
            )

        # Both secrets stored, no warnings
        assert github_svc.set_repository_secret.await_count == 2
        calls = github_svc.set_repository_secret.call_args_list
        secret_names = {c[0][3] for c in calls}
        secret_values = {c[0][4] for c in calls}
        assert secret_names == {"AZURE_CLIENT_ID", "AZURE_CLIENT_SECRET"}
        assert secret_values == {"my-client-id", "my-client-secret"}
        assert app.warnings is None  # no warning when storage succeeds

    @pytest.mark.asyncio
    async def test_skips_secret_storage_when_credentials_absent(self, mock_db) -> None:
        from src.services.app_service import create_app_with_new_repo

        github_svc = _mock_github_service()
        payload = _new_repo_payload()  # no azure credentials

        with patch(
            "src.services.template_files.build_template_files", new_callable=AsyncMock
        ) as mock_templates:
            mock_templates.return_value = ([], [])
            app = await create_app_with_new_repo(
                mock_db, payload, access_token="tok", github_service=github_svc
            )

        github_svc.set_repository_secret.assert_not_awaited()
        assert app.warnings is None

    @pytest.mark.asyncio
    async def test_secret_storage_failure_surfaces_warning(self, mock_db) -> None:
        """When secret storage fails, the app is still created and a warning is set."""
        from src.services.app_service import create_app_with_new_repo

        github_svc = _mock_github_service()
        github_svc.set_repository_secret.side_effect = Exception("403 Forbidden")
        payload = _new_repo_payload(
            azure_client_id="my-client-id",
            azure_client_secret="my-client-secret",
        )

        with patch(
            "src.services.template_files.build_template_files", new_callable=AsyncMock
        ) as mock_templates:
            mock_templates.return_value = ([], [])
            app = await create_app_with_new_repo(
                mock_db, payload, access_token="tok", github_service=github_svc
            )

        # App is still created successfully
        assert app.name == "test-app"
        assert app.status == AppStatus.ACTIVE
        # Warning is surfaced for the frontend
        assert app.warnings is not None
        assert len(app.warnings) == 1
        assert "Azure credentials could not be stored" in app.warnings[0]


# ---------------------------------------------------------------------------
# Tests — parent issue creation
# ---------------------------------------------------------------------------


class TestCreateAppWithParentIssue:
    """Validate parent issue creation when pipeline_id is provided."""

    @pytest.mark.asyncio
    async def test_creates_parent_issue_when_pipeline_id_provided(self, mock_db) -> None:
        from src.services.app_service import create_app_with_new_repo

        await _insert_pipeline_config(mock_db)
        github_svc = _mock_github_service()
        github_svc.create_issue = AsyncMock(
            return_value={
                "number": 42,
                "html_url": "https://github.com/alice/test-app/issues/42",
            }
        )
        payload = _new_repo_payload(pipeline_id="pipe-123")

        with patch(
            "src.services.template_files.build_template_files", new_callable=AsyncMock
        ) as mock_templates:
            mock_templates.return_value = ([], [])
            app = await create_app_with_new_repo(
                mock_db, payload, access_token="tok", github_service=github_svc
            )

        assert app.parent_issue_number == 42
        assert app.parent_issue_url == "https://github.com/alice/test-app/issues/42"
        github_svc.create_issue.assert_awaited_once()
        # Verify issue title follows the pattern
        call_kwargs = github_svc.create_issue.call_args
        assert call_kwargs.kwargs["title"] == "Build Test App"

    @pytest.mark.asyncio
    async def test_no_parent_issue_when_pipeline_id_absent(self, mock_db) -> None:
        from src.services.app_service import create_app_with_new_repo

        github_svc = _mock_github_service()
        payload = _new_repo_payload()  # no pipeline_id

        with patch(
            "src.services.template_files.build_template_files", new_callable=AsyncMock
        ) as mock_templates:
            mock_templates.return_value = ([], [])
            app = await create_app_with_new_repo(
                mock_db, payload, access_token="tok", github_service=github_svc
            )

        assert app.parent_issue_number is None
        assert app.parent_issue_url is None

    @pytest.mark.asyncio
    async def test_parent_issue_failure_adds_warning(self, mock_db) -> None:
        """Parent issue creation failure should add a warning, not block app creation."""
        from src.services.app_service import create_app_with_new_repo

        await _insert_pipeline_config(mock_db)
        github_svc = _mock_github_service()
        github_svc.create_issue = AsyncMock(side_effect=Exception("API error"))
        payload = _new_repo_payload(pipeline_id="pipe-123")

        with patch(
            "src.services.template_files.build_template_files", new_callable=AsyncMock
        ) as mock_templates:
            mock_templates.return_value = ([], [])
            app = await create_app_with_new_repo(
                mock_db, payload, access_token="tok", github_service=github_svc
            )

        # App is still created
        assert app.name == "test-app"
        assert app.status == AppStatus.ACTIVE
        # Parent issue fields are null
        assert app.parent_issue_number is None
        assert app.parent_issue_url is None
        # Warning is surfaced
        assert app.warnings is not None
        assert any("Parent issue could not be created" in w for w in app.warnings)


# ---------------------------------------------------------------------------
# Tests — template file warning propagation
# ---------------------------------------------------------------------------


class TestTemplateWarningPropagation:
    """Validate that template file warnings are surfaced to the caller."""

    @pytest.mark.asyncio
    async def test_template_warnings_propagated_to_app(self, mock_db) -> None:
        from src.services.app_service import create_app_with_new_repo

        github_svc = _mock_github_service()
        payload = _new_repo_payload()

        with patch(
            "src.services.template_files.build_template_files", new_callable=AsyncMock
        ) as mock_templates:
            mock_templates.return_value = (
                [{"path": ".gitignore", "content": "node_modules/\n"}],
                ["Could not read template file .specify/memory/notes.md: encoding error"],
            )
            app = await create_app_with_new_repo(
                mock_db, payload, access_token="tok", github_service=github_svc
            )

        assert app.warnings is not None
        assert len(app.warnings) == 1
        assert "Could not read template file" in app.warnings[0]

    @pytest.mark.asyncio
    async def test_template_and_azure_warnings_combined(self, mock_db) -> None:
        """Both template and Azure warnings should appear in the warnings list."""
        from src.services.app_service import create_app_with_new_repo

        github_svc = _mock_github_service()
        github_svc.set_repository_secret.side_effect = Exception("403 Forbidden")
        payload = _new_repo_payload(
            azure_client_id="my-client-id",
            azure_client_secret="my-client-secret",
        )

        with patch(
            "src.services.template_files.build_template_files", new_callable=AsyncMock
        ) as mock_templates:
            mock_templates.return_value = (
                [],
                ["Could not read .specify/memory/notes.md: encoding error"],
            )
            app = await create_app_with_new_repo(
                mock_db, payload, access_token="tok", github_service=github_svc
            )

        # Both warnings should be present
        assert app.warnings is not None
        assert len(app.warnings) == 2
        assert any("Could not read" in w for w in app.warnings)
        assert any("Azure credentials could not be stored" in w for w in app.warnings)


# ---------------------------------------------------------------------------
# Tests — delete app with parent issue
# ---------------------------------------------------------------------------


class TestDeleteAppWithParentIssue:
    """Validate that delete_app closes the parent issue when present."""

    @pytest.mark.asyncio
    async def test_closes_parent_issue_on_delete(self, mock_db) -> None:
        from src.services.app_service import create_app_with_new_repo, delete_app, stop_app

        await _insert_pipeline_config(mock_db)
        github_svc = _mock_github_service()
        github_svc.create_issue = AsyncMock(
            return_value={
                "number": 42,
                "html_url": "https://github.com/alice/test-app/issues/42",
            }
        )
        github_svc.update_issue_state = AsyncMock(return_value=True)
        payload = _new_repo_payload(pipeline_id="pipe-123")

        with patch(
            "src.services.template_files.build_template_files", new_callable=AsyncMock
        ) as mock_templates:
            mock_templates.return_value = ([], [])
            app = await create_app_with_new_repo(
                mock_db, payload, access_token="tok", github_service=github_svc
            )

        assert app.parent_issue_number == 42

        # Stop the app first (required before deletion)
        await stop_app(mock_db, "test-app")

        # Delete should close the parent issue
        await delete_app(
            mock_db,
            "test-app",
            access_token="tok",
            github_service=github_svc,
        )

        github_svc.update_issue_state.assert_awaited_once_with(
            "tok",
            owner="alice",
            repo="test-app",
            issue_number=42,
            state="closed",
        )

    @pytest.mark.asyncio
    async def test_delete_without_parent_issue_skips_close(self, mock_db) -> None:
        from src.services.app_service import create_app_with_new_repo, delete_app, stop_app

        github_svc = _mock_github_service()
        github_svc.update_issue_state = AsyncMock(return_value=True)
        payload = _new_repo_payload()  # no pipeline_id

        with patch(
            "src.services.template_files.build_template_files", new_callable=AsyncMock
        ) as mock_templates:
            mock_templates.return_value = ([], [])
            await create_app_with_new_repo(
                mock_db, payload, access_token="tok", github_service=github_svc
            )

        await stop_app(mock_db, "test-app")
        await delete_app(
            mock_db,
            "test-app",
            access_token="tok",
            github_service=github_svc,
        )

        github_svc.update_issue_state.assert_not_awaited()
