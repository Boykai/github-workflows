import base64
import json
from unittest.mock import AsyncMock, patch

from src.models.tools import McpToolConfigSyncResult, McpToolConfigUpdate
from src.services.tools.service import ToolsService

PROJECT_ID = "project-123"
USER_ID = "user-123"
TOOL_ID = "tool-123"


def _github_file_response(content: dict, *, sha: str = "sha-1"):
    encoded = base64.b64encode((json.dumps(content) + "\n").encode("utf-8")).decode("utf-8")
    return {"sha": sha, "content": encoded}


class _FakeResponse:
    def __init__(self, status_code: int, payload: dict | None = None, text: str = "") -> None:
        self.status_code = status_code
        self._payload = payload or {}
        self.text = text

    def json(self):
        return self._payload


class _FakeAsyncClient:
    def __init__(
        self, *, get_responses: dict[str, list[_FakeResponse]], put_status: int = 200
    ) -> None:
        self.get_responses = {url: list(responses) for url, responses in get_responses.items()}
        self.put_status = put_status
        self.put_calls: list[tuple[str, dict]] = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def get(self, url: str, headers=None):
        responses = self.get_responses.get(url)
        if not responses:
            return _FakeResponse(404)
        return responses.pop(0)

    async def put(self, url: str, headers=None, json=None):
        self.put_calls.append((url, json or {}))
        return _FakeResponse(self.put_status, {"content": {}})


async def _insert_tool(
    db,
    *,
    tool_id: str = TOOL_ID,
    name: str = "Context7",
    description: str = "Original description",
    endpoint_url: str = "https://example.com/mcp",
    config_content: str = '{"mcpServers":{"context7":{"type":"http","url":"https://example.com/mcp"}}}',
    github_repo_target: str = "octo/original-repo",
) -> None:
    await db.execute(
        """INSERT INTO mcp_configurations
           (id, github_user_id, project_id, name, description, endpoint_url, config_content,
            sync_status, sync_error, synced_at, github_repo_target, is_active, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, 'synced', '', NULL, ?, 1, datetime('now'), datetime('now'))""",
        (
            tool_id,
            USER_ID,
            PROJECT_ID,
            name,
            description,
            endpoint_url,
            config_content,
            github_repo_target,
        ),
    )
    await db.commit()


class TestToolsServiceUpdate:
    async def test_update_tool_resyncs_using_new_values(self, mock_db):
        await _insert_tool(mock_db)
        service = ToolsService(mock_db)

        sync_result = McpToolConfigSyncResult(
            id=TOOL_ID,
            sync_status="synced",
            sync_error="",
            synced_at="2025-01-01T00:00:00+00:00",
        )

        with (
            patch.object(service, "_remove_from_github", AsyncMock()) as remove_mock,
            patch.object(
                service, "sync_tool_to_github", AsyncMock(return_value=sync_result)
            ) as sync_mock,
        ):
            result = await service.update_tool(
                project_id=PROJECT_ID,
                tool_id=TOOL_ID,
                github_user_id=USER_ID,
                data=McpToolConfigUpdate(
                    name="Docs MCP",
                    description="Updated description",
                    config_content='{"mcpServers":{"docs":{"type":"stdio","command":"npx","args":["docs-server"]}}}',
                    github_repo_target="octo/new-repo",
                ),
                owner="fallback-owner",
                repo="fallback-repo",
                access_token="token",
            )

        remove_mock.assert_awaited_once()
        removed_tool, removed_owner, removed_repo, removed_token = remove_mock.await_args.args
        assert removed_tool.id == TOOL_ID
        assert removed_tool.name == "Context7"
        assert removed_owner == "octo"
        assert removed_repo == "original-repo"
        assert removed_token == "token"

        sync_mock.assert_awaited_once_with(
            TOOL_ID,
            PROJECT_ID,
            USER_ID,
            "octo",
            "new-repo",
            "token",
        )

        assert result.name == "Docs MCP"
        assert result.description == "Updated description"
        assert result.endpoint_url == "npx"
        assert result.github_repo_target == "octo/new-repo"
        assert result.sync_status == "synced"

        stored_tool = await service.get_tool(PROJECT_ID, TOOL_ID, USER_ID)
        assert stored_tool is not None
        assert stored_tool.name == "Docs MCP"
        assert stored_tool.description == "Updated description"
        assert stored_tool.endpoint_url == "npx"
        assert stored_tool.github_repo_target == "octo/new-repo"
        assert (
            stored_tool.config_content
            == '{"mcpServers":{"docs":{"type":"stdio","command":"npx","args":["docs-server"]}}}'
        )

    async def test_update_tool_allows_keeping_same_name(self, mock_db):
        await _insert_tool(mock_db, name="Shared MCP")
        service = ToolsService(mock_db)

        with (
            patch.object(service, "_remove_from_github", AsyncMock()),
            patch.object(
                service,
                "sync_tool_to_github",
                AsyncMock(
                    return_value=McpToolConfigSyncResult(
                        id=TOOL_ID,
                        sync_status="synced",
                        sync_error="",
                        synced_at="2025-01-01T00:00:00+00:00",
                    )
                ),
            ),
        ):
            result = await service.update_tool(
                project_id=PROJECT_ID,
                tool_id=TOOL_ID,
                github_user_id=USER_ID,
                data=McpToolConfigUpdate(
                    name="Shared MCP",
                    description="Renamed description only",
                ),
                owner="octo",
                repo="repo",
                access_token="token",
            )

        assert result.name == "Shared MCP"
        assert result.description == "Renamed description only"


class TestToolsServiceMcpSync:
    async def test_validate_mcp_config_accepts_local_and_sse_servers(self, mock_db):
        service = ToolsService(mock_db)

        is_valid, error = service.validate_mcp_config(
            json.dumps(
                {
                    "mcpServers": {
                        "github": {
                            "type": "http",
                            "url": "https://api.githubcopilot.com/mcp/readonly",
                            "tools": ["*"],
                            "headers": {"X-MCP-Toolsets": "repos,issues"},
                        },
                        "azure": {
                            "type": "local",
                            "command": "npx",
                            "args": ["-y", "@azure/mcp@latest", "server", "start"],
                        },
                        "cloudflare": {
                            "type": "sse",
                            "url": "https://docs.mcp.cloudflare.com/sse",
                        },
                    }
                }
            )
        )

        assert is_valid is True
        assert error == ""

    async def test_sync_tool_to_github_writes_both_supported_paths(self, mock_db):
        await _insert_tool(mock_db)
        service = ToolsService(mock_db)
        base_url = "https://api.github.com/repos/octo/repo/contents"
        fake_client = _FakeAsyncClient(
            get_responses={
                f"{base_url}/.copilot/mcp.json": [_FakeResponse(404)],
                f"{base_url}/.vscode/mcp.json": [
                    _FakeResponse(
                        200,
                        _github_file_response(
                            {
                                "mcpServers": {
                                    "existing": {
                                        "type": "http",
                                        "url": "https://existing.example/mcp",
                                    }
                                }
                            },
                            sha="sha-vscode",
                        ),
                    )
                ],
            }
        )

        with patch("httpx.AsyncClient", return_value=fake_client):
            result = await service.sync_tool_to_github(
                TOOL_ID,
                PROJECT_ID,
                USER_ID,
                "octo",
                "repo",
                "token",
            )

        assert result.sync_status == "synced"
        assert result.synced_paths == [".copilot/mcp.json", ".vscode/mcp.json"]
        assert len(fake_client.put_calls) == 2

        put_by_url = dict(fake_client.put_calls)
        copilot_body = put_by_url[f"{base_url}/.copilot/mcp.json"]
        vscode_body = put_by_url[f"{base_url}/.vscode/mcp.json"]

        copilot_content = json.loads(base64.b64decode(copilot_body["content"]).decode("utf-8"))
        vscode_content = json.loads(base64.b64decode(vscode_body["content"]).decode("utf-8"))

        assert "context7" in copilot_content["mcpServers"]
        assert set(vscode_content["mcpServers"].keys()) == {"existing", "context7"}
        assert vscode_body["sha"] == "sha-vscode"

    async def test_get_repo_mcp_config_reads_both_paths(self, mock_db):
        service = ToolsService(mock_db)
        base_url = "https://api.github.com/repos/octo/repo/contents"
        fake_client = _FakeAsyncClient(
            get_responses={
                f"{base_url}/.copilot/mcp.json": [
                    _FakeResponse(
                        200,
                        _github_file_response(
                            {
                                "mcpServers": {
                                    "github": {
                                        "type": "http",
                                        "url": "https://api.githubcopilot.com/mcp/readonly",
                                    }
                                }
                            },
                            sha="sha-copilot",
                        ),
                    )
                ],
                f"{base_url}/.vscode/mcp.json": [
                    _FakeResponse(
                        200,
                        _github_file_response(
                            {
                                "mcpServers": {
                                    "github": {
                                        "type": "http",
                                        "url": "https://api.githubcopilot.com/mcp/readonly",
                                    },
                                    "azure": {
                                        "type": "local",
                                        "command": "npx",
                                    },
                                }
                            },
                            sha="sha-vscode",
                        ),
                    )
                ],
            }
        )

        with patch("httpx.AsyncClient", return_value=fake_client):
            result = await service.get_repo_mcp_config(
                owner="octo",
                repo="repo",
                access_token="token",
            )

        assert result.primary_path == ".copilot/mcp.json"
        assert result.available_paths == [".copilot/mcp.json", ".vscode/mcp.json"]
        assert [server.name for server in result.servers] == ["azure", "github"]
        github_server = next(server for server in result.servers if server.name == "github")
        assert github_server.source_paths == [".copilot/mcp.json", ".vscode/mcp.json"]
