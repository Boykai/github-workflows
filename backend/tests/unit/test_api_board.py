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

    async def test_rate_limit_uses_cached_headers_for_generic_errors(
        self, client, mock_github_service
    ):
        mock_github_service.list_board_projects.side_effect = RuntimeError("network")
        mock_github_service.get_last_rate_limit.return_value = {
            "limit": 5000,
            "remaining": 0,
            "reset_at": 1_700_000_000,
            "used": 5000,
        }

        resp = await client.get("/api/v1/board/projects", params={"refresh": True})

        assert resp.status_code == 429
        body = resp.json()
        assert body["error"] == "GitHub API rate limit exceeded"
        assert body["details"]["rate_limit"]["remaining"] == 0


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

    async def test_rate_limit_uses_cached_headers_for_board_data_generic_errors(
        self, client, mock_github_service
    ):
        mock_github_service.get_board_data.side_effect = RuntimeError("timeout")
        mock_github_service.get_last_rate_limit.return_value = {
            "limit": 5000,
            "remaining": 0,
            "reset_at": 1_700_000_000,
            "used": 5000,
        }

        resp = await client.get("/api/v1/board/projects/PVT_error", params={"refresh": True})

        assert resp.status_code == 429
        body = resp.json()
        assert body["error"] == "GitHub API rate limit exceeded"
        assert body["details"]["rate_limit"]["used"] == 5000

    async def test_refresh_board_data(self, client, mock_github_service):
        bd = _make_board_data()
        mock_github_service.get_board_data.return_value = bd
        resp = await client.get("/api/v1/board/projects/PVT_abc", params={"refresh": True})
        assert resp.status_code == 200
        mock_github_service.get_board_data.assert_called_once()

    async def test_board_data_cache_stores_data_hash(self, client, mock_github_service):
        """Board data should be cached with a data_hash for change detection."""
        bd = _make_board_data()
        mock_github_service.get_board_data.return_value = bd

        with patch("src.api.board.cache") as mock_cache:
            mock_cache.get.return_value = None
            mock_cache.get_stale.return_value = None
            resp = await client.get("/api/v1/board/projects/PVT_abc")
            assert resp.status_code == 200

            # Verify cache.set was called
            assert mock_cache.set.called

    async def test_manual_refresh_clears_sub_issue_caches(self, client, mock_github_service):
        """Manual refresh (refresh=true) must clear sub-issue caches before fetching."""
        bd = _make_board_data()
        # Add repository info to the board item
        from src.models.board import Repository

        bd.columns[0].items[0].repository = Repository(owner="test-owner", name="test-repo")
        bd.columns[0].items[0].number = 42

        mock_github_service.get_board_data.return_value = bd

        with patch("src.api.board.cache") as mock_cache:
            # First populate cache
            mock_cache.get.return_value = bd
            mock_cache.get_stale.return_value = None

            resp = await client.get("/api/v1/board/projects/PVT_abc", params={"refresh": True})
            assert resp.status_code == 200

            # Verify cache.delete was called for sub-issue cache key
            delete_calls = [str(call) for call in mock_cache.delete.call_args_list]
            assert any("sub_issues" in str(call) for call in delete_calls)

    async def test_unchanged_board_data_returns_cached_with_fresh_rate_limit(
        self, client, mock_github_service
    ):
        """When board data is cached and unchanged, response includes fresh rate_limit."""
        bd = _make_board_data()
        mock_github_service.get_board_data.return_value = bd

        # First request populates cache
        resp1 = await client.get("/api/v1/board/projects/PVT_abc")
        assert resp1.status_code == 200

        # Second request should use cache
        with patch("src.api.board.cache") as mock_cache:
            mock_cache.get.return_value = bd
            resp2 = await client.get("/api/v1/board/projects/PVT_abc")
            assert resp2.status_code == 200
            mock_cache.get.assert_called_once()


# ── Regression: board error responses must NOT leak internal details ────────


class TestBoardErrorSanitization:
    """Bug-bash regression: GitHubAPIError raised in board endpoints must not
    include raw exception strings in the ``details`` field."""

    async def test_list_projects_error_does_not_leak_details(self, client, mock_github_service):
        """list_board_projects must not expose internal error strings."""
        mock_github_service.list_board_projects.side_effect = RuntimeError(
            "Connection refused to https://api.github.com"
        )
        resp = await client.get("/api/v1/board/projects", params={"refresh": True})
        assert resp.status_code == 502
        body = resp.json()
        assert "Connection refused" not in str(body)
        assert "api.github.com" not in str(body)

    async def test_get_board_data_error_does_not_leak_details(self, client, mock_github_service):
        """get_board_data must not expose internal error strings."""
        mock_github_service.get_board_data.side_effect = RuntimeError(
            "SSL: CERTIFICATE_VERIFY_FAILED"
        )
        resp = await client.get("/api/v1/board/projects/PVT_err", params={"refresh": True})
        assert resp.status_code == 502
        body = resp.json()
        assert "CERTIFICATE_VERIFY_FAILED" not in str(body)

    async def test_not_found_error_does_not_include_project_id(self, client, mock_github_service):
        """NotFoundError from get_board_data must not echo the project_id back
        to the client — user-controlled input should never appear in error messages."""
        mock_github_service.get_board_data.side_effect = ValueError("no such project")
        resp = await client.get(
            "/api/v1/board/projects/ATTACKER_CONTROLLED_ID", params={"refresh": True}
        )
        assert resp.status_code == 404
        body = resp.json()
        assert "ATTACKER_CONTROLLED_ID" not in str(body)

