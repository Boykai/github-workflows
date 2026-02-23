"""Tests for projects API routes (src/api/projects.py).

Covers:
- GET  /api/v1/projects                     → list_projects
- GET  /api/v1/projects/{id}                → get_project
- GET  /api/v1/projects/{id}/tasks           → get_project_tasks
- POST /api/v1/projects/{id}/select         → select_project
- _start_copilot_polling helper
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.api.projects import _start_copilot_polling
from src.models.project import GitHubProject, StatusColumn
from src.models.task import Task

# ── Helpers ─────────────────────────────────────────────────────────────────


def _project(**kw) -> GitHubProject:
    defaults = {
        "project_id": "PVT_abc",
        "owner_id": "O_123",
        "owner_login": "testuser",
        "name": "Test Project",
        "type": "user",
        "url": "https://github.com/users/testuser/projects/1",
        "status_columns": [
            StatusColumn(field_id="SF_1", name="Todo", option_id="opt1"),
            StatusColumn(field_id="SF_1", name="Done", option_id="opt2"),
        ],
    }
    defaults.update(kw)
    return GitHubProject(**defaults)


def _task(**kw) -> Task:
    defaults = {
        "project_id": "PVT_abc",
        "github_item_id": "PVTI_1",
        "title": "Sample task",
        "status": "Todo",
        "status_option_id": "opt1",
    }
    defaults.update(kw)
    return Task(**defaults)


# ── GET /projects ───────────────────────────────────────────────────────────


class TestListProjects:
    async def test_returns_projects(self, client, mock_github_service):
        p = _project()
        mock_github_service.list_user_projects.return_value = [p]
        resp = await client.get("/api/v1/projects", params={"refresh": True})
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["projects"]) == 1
        assert data["projects"][0]["name"] == "Test Project"

    async def test_returns_empty_list(self, client, mock_github_service):
        mock_github_service.list_user_projects.return_value = []
        resp = await client.get("/api/v1/projects", params={"refresh": True})
        assert resp.status_code == 200
        assert resp.json()["projects"] == []


# ── GET /projects/{id} ─────────────────────────────────────────────────────


class TestGetProject:
    async def test_get_existing_project(self, client, mock_github_service):
        p = _project()
        mock_github_service.list_user_projects.return_value = [p]
        resp = await client.get("/api/v1/projects/PVT_abc", params={"refresh": True})
        assert resp.status_code == 200
        assert resp.json()["project_id"] == "PVT_abc"

    async def test_project_not_found(self, client, mock_github_service):
        mock_github_service.list_user_projects.return_value = []
        with patch("src.api.projects.cache") as mock_cache:
            mock_cache.get.return_value = None
            resp = await client.get("/api/v1/projects/PVT_missing")
        assert resp.status_code == 404


# ── GET /projects/{id}/tasks ───────────────────────────────────────────────


class TestGetProjectTasks:
    async def test_returns_tasks(self, client, mock_github_service):
        t = _task()
        mock_github_service.get_project_items.return_value = [t]
        resp = await client.get("/api/v1/projects/PVT_abc/tasks", params={"refresh": True})
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["tasks"]) == 1
        assert data["tasks"][0]["title"] == "Sample task"

    async def test_returns_empty_tasks(self, client, mock_github_service):
        mock_github_service.get_project_items.return_value = []
        resp = await client.get("/api/v1/projects/PVT_abc/tasks", params={"refresh": True})
        assert resp.status_code == 200
        assert resp.json()["tasks"] == []


# ── POST /projects/{id}/select ─────────────────────────────────────────────


class TestSelectProject:
    async def test_select_project(
        self, client, mock_session, mock_github_service, mock_github_auth_service
    ):
        p = _project()
        mock_github_service.list_user_projects.return_value = [p]
        mock_github_auth_service.update_session.return_value = None

        # Patch out copilot polling startup
        with (
            patch("src.api.projects._start_copilot_polling", new_callable=AsyncMock),
            patch("src.api.projects.cache") as mock_cache,
        ):
            mock_cache.get.return_value = None
            resp = await client.post("/api/v1/projects/PVT_abc/select")
        assert resp.status_code == 200
        data = resp.json()
        assert data["selected_project_id"] == "PVT_abc"

    async def test_select_nonexistent_project(self, client, mock_github_service):
        mock_github_service.list_user_projects.return_value = []
        with patch("src.api.projects.cache") as mock_cache:
            mock_cache.get.return_value = None
            resp = await client.post("/api/v1/projects/PVT_missing/select")
        assert resp.status_code == 404


# ── Cache Hit Paths ────────────────────────────────────────────────────────


class TestCacheHitPaths:
    async def test_list_projects_cache_hit(self, client, mock_github_service):
        """Cache hit returns cached projects without calling GitHub."""
        p = _project()
        with patch("src.api.projects.cache") as mock_cache:
            mock_cache.get.return_value = [p]
            resp = await client.get("/api/v1/projects")
        assert resp.status_code == 200
        assert len(resp.json()["projects"]) == 1
        mock_github_service.list_user_projects.assert_not_called()

    async def test_get_project_cache_hit(self, client, mock_github_service):
        """get_project returns project from cached list."""
        p = _project()
        with patch("src.api.projects.cache") as mock_cache:
            mock_cache.get.return_value = [p]
            resp = await client.get("/api/v1/projects/PVT_abc")
        assert resp.status_code == 200
        assert resp.json()["project_id"] == "PVT_abc"

    async def test_get_project_tasks_cache_hit(self, client, mock_github_service):
        """get_project_tasks returns cached tasks."""
        t = _task()
        with patch("src.api.projects.cache") as mock_cache:
            mock_cache.get.return_value = [t]
            resp = await client.get("/api/v1/projects/PVT_abc/tasks")
        assert resp.status_code == 200
        assert len(resp.json()["tasks"]) == 1
        mock_github_service.get_project_items.assert_not_called()


# ── _start_copilot_polling ─────────────────────────────────────────────────

PROJ = "src.api.projects"


class TestStartCopilotPolling:
    @pytest.fixture
    def session(self, mock_session):
        mock_session.access_token = "tok"
        return mock_session

    @pytest.fixture
    def mock_gps(self):
        with patch("src.api.projects.github_projects_service") as m:
            yield m

    @pytest.mark.asyncio
    async def test_starts_polling_with_repo_info(self, session, mock_gps):
        """Happy path: get_project_repository returns repo info."""
        mock_gps.get_project_repository = AsyncMock(return_value=("owner", "repo"))
        with (
            patch(
                "src.services.copilot_polling.get_polling_status",
                return_value={"is_running": False},
            ),
            patch(
                "src.services.copilot_polling.poll_for_copilot_completion", new_callable=AsyncMock
            ),
            patch("src.services.copilot_polling._polling_task", None),
        ):
            await _start_copilot_polling(session, "proj-1")

    @pytest.mark.asyncio
    async def test_stops_existing_polling_first(self, session, mock_gps):
        """If polling is already running, stops it before restarting."""
        mock_gps.get_project_repository = AsyncMock(return_value=("o", "r"))
        with (
            patch(
                "src.services.copilot_polling.get_polling_status", return_value={"is_running": True}
            ),
            patch("src.services.copilot_polling.stop_polling") as mock_stop,
            patch(
                "src.services.copilot_polling.poll_for_copilot_completion", new_callable=AsyncMock
            ),
            patch("src.services.copilot_polling._polling_task", None),
            patch("asyncio.sleep", new_callable=AsyncMock),
        ):
            await _start_copilot_polling(session, "proj-1")
            mock_stop.assert_called_once()

    @pytest.mark.asyncio
    async def test_falls_back_to_workflow_config(self, session, mock_gps):
        """Falls back to workflow config when get_project_repository returns None."""
        mock_gps.get_project_repository = AsyncMock(return_value=None)
        config = MagicMock(repository_owner="cfg-owner", repository_name="cfg-repo")
        with (
            patch(
                "src.services.copilot_polling.get_polling_status",
                return_value={"is_running": False},
            ),
            patch(
                "src.services.copilot_polling.poll_for_copilot_completion", new_callable=AsyncMock
            ),
            patch("src.services.copilot_polling._polling_task", None),
            patch("src.api.workflow.get_workflow_config", new_callable=AsyncMock, return_value=config),
        ):
            await _start_copilot_polling(session, "proj-1")

    @pytest.mark.asyncio
    async def test_falls_back_to_settings(self, session, mock_gps):
        """Falls back to settings when both repo and config are None."""
        mock_gps.get_project_repository = AsyncMock(return_value=None)
        with (
            patch(
                "src.services.copilot_polling.get_polling_status",
                return_value={"is_running": False},
            ),
            patch(
                "src.services.copilot_polling.poll_for_copilot_completion", new_callable=AsyncMock
            ),
            patch("src.services.copilot_polling._polling_task", None),
            patch("src.api.workflow.get_workflow_config", new_callable=AsyncMock, return_value=None),
            patch("src.config.get_settings") as ms,
        ):
            ms.return_value = MagicMock(default_repo_owner="s-owner", default_repo_name="s-repo")
            await _start_copilot_polling(session, "proj-1")

    @pytest.mark.asyncio
    async def test_no_repo_info_skips_polling(self, session, mock_gps):
        """When no repo info available, polling is not started."""
        mock_gps.get_project_repository = AsyncMock(return_value=None)
        with (
            patch(
                "src.services.copilot_polling.get_polling_status",
                return_value={"is_running": False},
            ),
            patch(
                "src.services.copilot_polling.poll_for_copilot_completion", new_callable=AsyncMock
            ) as mock_poll,
            patch("src.api.workflow.get_workflow_config", new_callable=AsyncMock, return_value=None),
            patch("src.config.get_settings") as ms,
        ):
            ms.return_value = MagicMock(default_repo_owner="", default_repo_name="")
            await _start_copilot_polling(session, "proj-1")
            mock_poll.assert_not_called()
