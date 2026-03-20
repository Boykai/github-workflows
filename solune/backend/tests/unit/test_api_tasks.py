"""Tests for tasks API routes (src/api/tasks.py).

Covers:
- POST  /api/v1/tasks          → create_task
- PATCH /api/v1/tasks/{id}/status → update_task_status
- _resolve_repository_for_project() helper
"""

from unittest.mock import AsyncMock, patch

import pytest

from src.models.task import Task
from src.models.workflow import WorkflowConfiguration

# ── Helpers ─────────────────────────────────────────────────────────────────


def _task(**kw) -> Task:
    defaults = {
        "project_id": "PVT_abc",
        "github_item_id": "PVTI_1",
        "title": "Test task",
        "status": "Todo",
        "status_option_id": "opt1",
    }
    defaults.update(kw)
    return Task(**defaults)


# ── POST /tasks ─────────────────────────────────────────────────────────────


class TestCreateTask:
    async def test_create_task_success(
        self, client, mock_session, mock_github_service, mock_websocket_manager
    ):
        mock_session.selected_project_id = "PVT_abc"
        mock_github_service.get_project_repository.return_value = ("owner", "repo")
        mock_github_service.create_issue.return_value = {
            "id": 200042,
            "number": 42,
            "node_id": "I_abc",
            "html_url": "https://github.com/owner/repo/issues/42",
        }
        mock_github_service.add_issue_to_project.return_value = "PVTI_new"

        with patch(
            "src.api.tasks._create_parent_issue_sub_issues",
            new_callable=AsyncMock,
            return_value=None,
        ):
            resp = await client.post(
                "/api/v1/tasks",
                json={"project_id": "PVT_abc", "title": "New task", "description": "desc"},
            )
        assert resp.status_code == 200
        data = resp.json()
        assert data["title"] == "New task"
        assert data["issue_number"] == 42
        mock_websocket_manager.broadcast_to_project.assert_called_once()

    async def test_create_task_precreates_pipeline_sub_issues(
        self, client, mock_session, mock_github_service
    ):
        mock_session.selected_project_id = "PVT_abc"
        mock_github_service.get_project_repository.return_value = ("owner", "repo")
        mock_github_service.create_issue.return_value = {
            "id": 200042,
            "number": 42,
            "node_id": "I_abc",
            "html_url": "https://github.com/owner/repo/issues/42",
        }
        mock_github_service.add_issue_to_project.return_value = "PVTI_new"

        config = WorkflowConfiguration(
            project_id="PVT_abc",
            repository_owner="owner",
            repository_name="repo",
        )

        with (
            patch(
                "src.api.tasks.get_workflow_config",
                new_callable=AsyncMock,
                return_value=config,
            ),
            patch("src.api.tasks.get_workflow_orchestrator") as mock_orchestrator,
        ):
            mock_orchestrator.return_value.create_all_sub_issues = AsyncMock(
                return_value={"easy": {"number": 101, "node_id": "I_sub"}}
            )

            resp = await client.post(
                "/api/v1/tasks",
                json={"project_id": "PVT_abc", "title": "New task", "description": "desc"},
            )

        assert resp.status_code == 200
        create_subissues_ctx = mock_orchestrator.return_value.create_all_sub_issues.await_args.args[
            0
        ]
        assert create_subissues_ctx.project_id == "PVT_abc"
        assert create_subissues_ctx.repository_owner == "owner"
        assert create_subissues_ctx.repository_name == "repo"
        assert create_subissues_ctx.issue_number == 42
        assert create_subissues_ctx.issue_id == "I_abc"
        assert create_subissues_ctx.project_item_id == "PVTI_new"

    async def test_create_task_subissue_bootstrap_failure_does_not_fail_request(
        self, client, mock_session, mock_github_service
    ):
        mock_session.selected_project_id = "PVT_abc"
        mock_github_service.get_project_repository.return_value = ("owner", "repo")
        mock_github_service.create_issue.return_value = {
            "id": 200042,
            "number": 42,
            "node_id": "I_abc",
            "html_url": "https://github.com/owner/repo/issues/42",
        }
        mock_github_service.add_issue_to_project.return_value = "PVTI_new"

        with patch(
            "src.api.tasks._create_parent_issue_sub_issues",
            new_callable=AsyncMock,
            side_effect=RuntimeError("sub-issue bootstrap failed"),
        ):
            resp = await client.post(
                "/api/v1/tasks",
                json={"project_id": "PVT_abc", "title": "New task"},
            )

        assert resp.status_code == 200
        assert resp.json()["issue_number"] == 42

    async def test_create_task_no_project_selected(self, client, mock_session):
        mock_session.selected_project_id = None
        resp = await client.post(
            "/api/v1/tasks",
            json={"project_id": "", "title": "New task"},
        )
        # ValidationError → 422 (from AppException handler, status=422)
        assert resp.status_code == 422

    async def test_create_task_uses_session_project(
        self, client, mock_session, mock_github_service, mock_websocket_manager
    ):
        """When request.project_id is empty, falls back to session project."""
        mock_session.selected_project_id = "PVT_session"
        mock_github_service.get_project_repository.return_value = ("o", "r")
        mock_github_service.create_issue.return_value = {
            "id": 200001,
            "number": 1,
            "node_id": "I_1",
            "html_url": "https://github.com/o/r/issues/1",
        }
        mock_github_service.add_issue_to_project.return_value = "PVTI_1"

        with patch(
            "src.api.tasks._create_parent_issue_sub_issues",
            new_callable=AsyncMock,
            return_value=None,
        ):
            resp = await client.post(
                "/api/v1/tasks",
                json={"project_id": "", "title": "Fallback"},
            )
        assert resp.status_code == 200

    async def test_create_task_add_to_project_fails(
        self, client, mock_session, mock_github_service
    ):
        mock_session.selected_project_id = "PVT_abc"
        mock_github_service.get_project_repository.return_value = ("o", "r")
        mock_github_service.create_issue.return_value = {
            "id": 200002,
            "number": 1,
            "node_id": "I_1",
            "html_url": "https://github.com/o/r/issues/1",
        }
        mock_github_service.add_issue_to_project.return_value = None
        resp = await client.post(
            "/api/v1/tasks",
            json={"project_id": "PVT_abc", "title": "Fail add"},
        )
        assert resp.status_code == 422  # ValidationError


# ── PATCH /tasks/{id}/status ────────────────────────────────────────────────


class TestUpdateTaskStatus:
    """Task status update endpoint now returns 501 Not Implemented."""

    async def test_update_status_returns_501(self, client, mock_session):
        mock_session.selected_project_id = None
        resp = await client.patch(
            "/api/v1/tasks/PVTI_1/status",
            params={"status": "Done"},
        )
        assert resp.status_code == 501
        body = resp.json()
        assert body["error"] == "Not implemented"

    async def test_update_status_501_with_project(self, client, mock_session):
        mock_session.selected_project_id = "PVT_abc"
        resp = await client.patch(
            "/api/v1/tasks/PVTI_1/status",
            params={"status": "Done"},
        )
        assert resp.status_code == 501


# ── resolve_repository (shared helper from src.utils) ──────────────────────


class TestResolveRepository:
    async def test_resolve_from_project_repository(self):
        from src.utils import resolve_repository

        mock_svc = AsyncMock()
        mock_svc.get_project_repository.return_value = ("owner", "repo")
        with patch("src.services.github_projects.github_projects_service", mock_svc):
            owner, repo = await resolve_repository("token", "PVT_1")
        assert owner == "owner"
        assert repo == "repo"

    async def test_resolve_from_workflow_config(self):
        from src.models.chat import WorkflowConfiguration
        from src.utils import resolve_repository

        mock_svc = AsyncMock()
        mock_svc.get_project_repository.return_value = None
        config = WorkflowConfiguration(
            project_id="PVT_1",
            repository_owner="cfg_owner",
            repository_name="cfg_repo",
        )
        with (
            patch("src.services.github_projects.github_projects_service", mock_svc),
            patch(
                "src.services.workflow_orchestrator.get_workflow_config",
                new_callable=AsyncMock,
                return_value=config,
            ),
        ):
            owner, _repo = await resolve_repository("token", "PVT_1")
        assert owner == "cfg_owner"

    async def test_resolve_from_default_settings(self):
        from src.config import Settings
        from src.utils import resolve_repository

        mock_svc = AsyncMock()
        mock_svc.get_project_repository.return_value = None
        settings = Settings(
            github_client_id="id",
            github_client_secret="s",
            session_secret_key="k" * 32,
            default_repository="def_owner/def_repo",
            _env_file=None,
        )
        with (
            patch("src.services.github_projects.github_projects_service", mock_svc),
            patch(
                "src.services.workflow_orchestrator.get_workflow_config",
                new_callable=AsyncMock,
                return_value=None,
            ),
            patch("src.config.get_settings", return_value=settings),
        ):
            owner, _repo = await resolve_repository("token", "PVT_1")
        assert owner == "def_owner"

    async def test_resolve_raises_when_nothing_found(self):
        from src.config import Settings
        from src.exceptions import ValidationError
        from src.utils import resolve_repository

        mock_svc = AsyncMock()
        mock_svc.get_project_repository.return_value = None
        settings = Settings(
            github_client_id="id",
            github_client_secret="s",
            session_secret_key="k" * 32,
            _env_file=None,
        )
        with (
            patch("src.services.github_projects.github_projects_service", mock_svc),
            patch(
                "src.services.workflow_orchestrator.get_workflow_config",
                new_callable=AsyncMock,
                return_value=None,
            ),
            patch("src.config.get_settings", return_value=settings),
        ):
            with pytest.raises(ValidationError):
                await resolve_repository("token", "PVT_1")
