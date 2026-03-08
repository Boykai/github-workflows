from unittest.mock import AsyncMock, patch

from src.models.tools import RepoMcpConfigResponse, RepoMcpServerConfig


class TestToolsPresetsApi:
    async def test_list_presets_returns_catalog(self, client):
        resp = await client.get("/api/v1/tools/presets")

        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] >= 1
        preset_ids = {preset["id"] for preset in data["presets"]}
        assert "github-readonly" in preset_ids
        github_preset = next(p for p in data["presets"] if p["id"] == "github-readonly")
        assert "api.githubcopilot.com/mcp/readonly" in github_preset["config_content"]


class TestRepoMcpConfigApi:
    async def test_repo_config_returns_service_payload(self, client, mock_github_service):
        mock_github_service.get_project_repository.return_value = ("octo", "widgets")
        response_model = RepoMcpConfigResponse(
            paths_checked=[".copilot/mcp.json", ".vscode/mcp.json"],
            available_paths=[".copilot/mcp.json", ".vscode/mcp.json"],
            primary_path=".copilot/mcp.json",
            servers=[
                RepoMcpServerConfig(
                    name="github",
                    config={"type": "http", "url": "https://api.githubcopilot.com/mcp/readonly"},
                    source_paths=[".copilot/mcp.json", ".vscode/mcp.json"],
                )
            ],
        )

        with patch(
            "src.api.tools.ToolsService.get_repo_mcp_config",
            AsyncMock(return_value=response_model),
        ) as repo_config_mock:
            resp = await client.get("/api/v1/tools/PVT_123/repo-config")

        assert resp.status_code == 200
        data = resp.json()
        assert data["primary_path"] == ".copilot/mcp.json"
        assert data["available_paths"] == [".copilot/mcp.json", ".vscode/mcp.json"]
        assert data["servers"][0]["name"] == "github"
        repo_config_mock.assert_awaited_once_with(
            owner="octo",
            repo="widgets",
            access_token="test-token",
        )

    async def test_repo_config_returns_400_when_repository_cannot_be_resolved(
        self,
        client,
    ):
        with patch(
            "src.api.tools.resolve_repository",
            AsyncMock(side_effect=RuntimeError("resolution failed")),
        ):
            resp = await client.get("/api/v1/tools/PVT_123/repo-config")

        assert resp.status_code == 400
        data = resp.json()
        assert "detail" in data
        assert "Cannot resolve repository" in data["detail"]

    async def test_repo_config_returns_502_when_service_fetch_fails(
        self,
        client,
        mock_github_service,
    ):
        mock_github_service.get_project_repository.return_value = ("octo", "widgets")

        with patch(
            "src.api.tools.ToolsService.get_repo_mcp_config",
            AsyncMock(side_effect=RuntimeError("GitHub API error: 500 boom")),
        ):
            resp = await client.get("/api/v1/tools/PVT_123/repo-config")

        assert resp.status_code == 502
        data = resp.json()
        assert data["error"] == "Failed to fetch repository MCP config"
