"""Tests for board API routes (src/api/board.py).

Covers:
- GET /api/v1/board/projects              → list_board_projects
- GET /api/v1/board/projects/{project_id} → get_board_data
"""

from unittest.mock import patch

from src.models.board import (
    BoardColumn,
    BoardDataResponse,
    BoardItem,
    BoardProject,
    ContentType,
    StatusColor,
    StatusField,
    StatusOption,
)

# ── Helpers ─────────────────────────────────────────────────────────────────


def _make_board_project(**kw) -> BoardProject:
    defaults = {
        "project_id": "PVT_abc",
        "name": "Test Board",
        "url": "https://github.com/users/testuser/projects/1",
        "owner_login": "testuser",
        "status_field": StatusField(
            field_id="SF_1",
            options=[
                StatusOption(option_id="opt1", name="Todo", color=StatusColor.GRAY),
                StatusOption(option_id="opt2", name="Done", color=StatusColor.GREEN),
            ],
        ),
    }
    defaults.update(kw)
    return BoardProject(**defaults)


def _make_board_data(project: BoardProject | None = None) -> BoardDataResponse:
    proj = project or _make_board_project()
    return BoardDataResponse(
        project=proj,
        columns=[
            BoardColumn(
                status=proj.status_field.options[0],
                items=[
                    BoardItem(
                        item_id="PVTI_1",
                        content_type=ContentType.ISSUE,
                        title="Fix bug",
                        status="Todo",
                        status_option_id="opt1",
                    )
                ],
                item_count=1,
            ),
            BoardColumn(
                status=proj.status_field.options[1],
                items=[],
                item_count=0,
            ),
        ],
    )


# ── GET /board/projects ────────────────────────────────────────────────────


class TestListBoardProjects:
    async def test_returns_projects(self, client, mock_github_service):
        bp = _make_board_project()
        mock_github_service.list_board_projects.return_value = [bp]
        resp = await client.get("/api/v1/board/projects")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["projects"]) == 1
        assert data["projects"][0]["name"] == "Test Board"

    async def test_uses_cache_on_second_call(self, client, mock_github_service):
        bp = _make_board_project()
        mock_github_service.list_board_projects.return_value = [bp]

        # First call — populates cache
        resp1 = await client.get("/api/v1/board/projects")
        assert resp1.status_code == 200
        # Second call — should use cache (service not called again)
        with patch("src.api.board.cache") as mock_cache:
            mock_cache.get.return_value = [bp]
            resp2 = await client.get("/api/v1/board/projects")
            assert resp2.status_code == 200
            mock_cache.get.assert_called_once()

    async def test_refresh_bypasses_cache(self, client, mock_github_service):
        bp = _make_board_project()
        mock_github_service.list_board_projects.return_value = [bp]
        resp = await client.get("/api/v1/board/projects", params={"refresh": True})
        assert resp.status_code == 200
        mock_github_service.list_board_projects.assert_called_once()

    async def test_github_api_error(self, client, mock_github_service):
        mock_github_service.list_board_projects.side_effect = RuntimeError("network")
        resp = await client.get("/api/v1/board/projects", params={"refresh": True})
        # Should raise GitHubAPIError (mapped to 502 via AppException handler)
        assert resp.status_code == 502


# ── GET /board/projects/{project_id} ───────────────────────────────────────


class TestGetBoardData:
    async def test_returns_board_data(self, client, mock_github_service):
        bd = _make_board_data()
        mock_github_service.get_board_data.return_value = bd
        resp = await client.get("/api/v1/board/projects/PVT_abc")
        assert resp.status_code == 200
        data = resp.json()
        assert data["project"]["project_id"] == "PVT_abc"
        assert len(data["columns"]) == 2
        assert data["columns"][0]["item_count"] == 1

    async def test_project_not_found(self, client, mock_github_service):
        mock_github_service.get_board_data.side_effect = ValueError("not found")
        resp = await client.get("/api/v1/board/projects/PVT_bad")
        assert resp.status_code == 404

    async def test_github_error_on_board_data(self, client, mock_github_service):
        mock_github_service.get_board_data.side_effect = RuntimeError("timeout")
        resp = await client.get("/api/v1/board/projects/PVT_error", params={"refresh": True})
        assert resp.status_code == 502

    async def test_refresh_board_data(self, client, mock_github_service):
        bd = _make_board_data()
        mock_github_service.get_board_data.return_value = bd
        resp = await client.get("/api/v1/board/projects/PVT_abc", params={"refresh": True})
        assert resp.status_code == 200
        mock_github_service.get_board_data.assert_called_once()
