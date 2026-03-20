import base64
import json
from unittest.mock import AsyncMock, patch

from src.models.tools import (
    McpToolConfigCreate,
    McpToolConfigSyncResult,
    McpToolConfigUpdate,
    RepoMcpServerUpdate,
)
from src.services.tools.service import DuplicateToolServerNameError, ToolsService

PROJECT_ID = "project-123"
USER_ID = "user-123"
TOOL_ID = "tool-123"


async def _insert_agent(
    db,
    *,
    agent_id: str = "agent-123",
    project_id: str = PROJECT_ID,
    created_by: str = USER_ID,
) -> None:
    await db.execute(
        """INSERT INTO agent_configs
           (id, name, slug, description, system_prompt, status_column,
            tools, project_id, owner, repo, created_by,
            github_issue_number, github_pr_number, branch_name, created_at, lifecycle_status)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), ?)""",
        (
            agent_id,
            "Reviewer",
            "reviewer",
            "Reviews pull requests",
            "Review carefully.",
            "",
            "[]",
            project_id,
            "octo",
            "repo",
            created_by,
            None,
            None,
            None,
            "active",
        ),
    )
    await db.commit()


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


class _FakeGitHubService:
    """Mock GitHubProjectsService that maps (method, path) → responses."""

    def __init__(
        self, *, get_responses: dict[str, list[_FakeResponse]], put_status: int = 200
    ) -> None:
        self.get_responses = {path: list(responses) for path, responses in get_responses.items()}
        self.put_status = put_status
        self.put_calls: list[tuple[str, dict]] = []

    async def rest_request(
        self,
        access_token: str,
        method: str,
        path: str,
        *,
        json: dict | None = None,
        params: dict | None = None,
        headers: dict | None = None,
    ) -> _FakeResponse:
        if method == "GET":
            responses = self.get_responses.get(path)
            if not responses:
                return _FakeResponse(404)
            return responses.pop(0)
        elif method == "PUT":
            self.put_calls.append((path, json or {}))
            return _FakeResponse(self.put_status, {"content": {}})
        elif method == "POST":
            return _FakeResponse(self.put_status, {"content": {}})
        return _FakeResponse(404)


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

    async def test_update_tool_rejects_conflicting_server_name(self, mock_db):
        await _insert_tool(mock_db, tool_id="tool-a", name="Docs MCP")
        await _insert_tool(
            mock_db,
            tool_id="tool-b",
            name="GitHub MCP",
            config_content='{"mcpServers":{"github":{"type":"http","url":"https://api.githubcopilot.com/mcp/readonly"}}}',
        )
        service = ToolsService(mock_db)

        try:
            await service.update_tool(
                project_id=PROJECT_ID,
                tool_id="tool-a",
                github_user_id=USER_ID,
                data=McpToolConfigUpdate(
                    config_content='{"mcpServers":{"github":{"type":"http","url":"https://example.com/other"}}}',
                ),
                owner="octo",
                repo="repo",
                access_token="token",
            )
        except DuplicateToolServerNameError as exc:
            assert "github" in str(exc)
            assert "GitHub MCP" in str(exc)
        else:
            raise AssertionError("Expected DuplicateToolServerNameError")


class TestToolsServiceCreate:
    async def test_create_tool_rejects_conflicting_server_name(self, mock_db):
        await _insert_tool(
            mock_db,
            tool_id="tool-existing",
            name="GitHub MCP",
            config_content='{"mcpServers":{"github-readonly":{"type":"http","url":"https://api.githubcopilot.com/mcp/readonly"}}}',
        )
        service = ToolsService(mock_db)

        try:
            await service.create_tool(
                project_id=PROJECT_ID,
                github_user_id=USER_ID,
                data=McpToolConfigCreate(
                    name="Another GitHub MCP",
                    description="",
                    config_content='{"mcpServers":{"github-readonly":{"type":"http","url":"https://api.githubcopilot.com/mcp/readonly"}}}',
                    github_repo_target="",
                ),
                owner="octo",
                repo="repo",
                access_token="token",
            )
        except DuplicateToolServerNameError as exc:
            assert "github-readonly" in str(exc)
            assert "GitHub MCP" in str(exc)
        else:
            raise AssertionError("Expected DuplicateToolServerNameError")


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

    async def test_extract_endpoint_url_supports_sse_and_local(self, mock_db):
        service = ToolsService(mock_db)

        assert (
            service._extract_endpoint_url(
                json.dumps(
                    {
                        "mcpServers": {
                            "cloudflare": {
                                "type": "sse",
                                "url": "https://docs.mcp.cloudflare.com/sse",
                            }
                        }
                    }
                )
            )
            == "https://docs.mcp.cloudflare.com/sse"
        )
        assert (
            service._extract_endpoint_url(
                json.dumps(
                    {
                        "mcpServers": {
                            "azure": {
                                "type": "local",
                                "command": "npx",
                            }
                        }
                    }
                )
            )
            == "npx"
        )

    async def test_sync_tool_to_github_writes_both_supported_paths(self, mock_db):
        await _insert_tool(mock_db)
        base_path = "/repos/octo/repo/contents"
        fake_svc = _FakeGitHubService(
            get_responses={
                f"{base_path}/.copilot/mcp.json": [_FakeResponse(404)],
                f"{base_path}/.vscode/mcp.json": [
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
        service = ToolsService(mock_db, github_service=fake_svc)

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
        assert len(fake_svc.put_calls) == 2

        put_by_path = dict(fake_svc.put_calls)
        copilot_body = put_by_path[f"{base_path}/.copilot/mcp.json"]
        vscode_body = put_by_path[f"{base_path}/.vscode/mcp.json"]

        copilot_content = json.loads(base64.b64decode(copilot_body["content"]).decode("utf-8"))
        vscode_content = json.loads(base64.b64decode(vscode_body["content"]).decode("utf-8"))

        assert "context7" in copilot_content["mcpServers"]
        assert set(vscode_content["mcpServers"].keys()) == {"existing", "context7"}
        assert vscode_body["sha"] == "sha-vscode"

    async def test_get_repo_mcp_config_reads_both_paths(self, mock_db):
        base_path = "/repos/octo/repo/contents"
        fake_svc = _FakeGitHubService(
            get_responses={
                f"{base_path}/.copilot/mcp.json": [
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
                f"{base_path}/.vscode/mcp.json": [
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
        service = ToolsService(mock_db, github_service=fake_svc)

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

    async def test_sync_tool_to_github_errors_when_server_name_conflicts(self, mock_db):
        await _insert_tool(
            mock_db,
            tool_id="tool-a",
            name="GitHub MCP",
            config_content='{"mcpServers":{"github":{"type":"http","url":"https://api.githubcopilot.com/mcp/readonly"}}}',
        )
        await _insert_tool(
            mock_db,
            tool_id="tool-b",
            name="GitHub MCP Full",
            config_content='{"mcpServers":{"github":{"type":"http","url":"https://api.githubcopilot.com/mcp/"}}}',
        )
        service = ToolsService(mock_db)

        result = await service.sync_tool_to_github(
            "tool-a",
            PROJECT_ID,
            USER_ID,
            "octo",
            "repo",
            "token",
        )

        assert result.sync_status == "error"
        assert "collision" in result.sync_error.lower()

    async def test_remove_from_github_preserves_server_names_still_used_elsewhere(self, mock_db):
        await _insert_tool(
            mock_db,
            tool_id="tool-a",
            name="GitHub MCP",
            config_content='{"mcpServers":{"github":{"type":"http","url":"https://api.githubcopilot.com/mcp/readonly"}}}',
        )
        base_path = "/repos/octo/repo/contents"
        fake_svc = _FakeGitHubService(
            get_responses={
                f"{base_path}/.copilot/mcp.json": [
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
                f"{base_path}/.vscode/mcp.json": [
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
                            sha="sha-vscode",
                        ),
                    )
                ],
            }
        )
        service = ToolsService(mock_db, github_service=fake_svc)
        tool = await service.get_tool(PROJECT_ID, "tool-a", USER_ID)
        assert tool is not None

        await service._remove_from_github(
            tool,
            "octo",
            "repo",
            "token",
            protected_server_names={"github"},
        )

        assert fake_svc.put_calls == []

    async def test_update_repo_mcp_server_updates_existing_server_in_each_present_path(
        self, mock_db
    ):
        base_path = "/repos/octo/repo/contents"
        fake_svc = _FakeGitHubService(
            get_responses={
                f"{base_path}/.copilot/mcp.json": [
                    _FakeResponse(
                        200,
                        _github_file_response(
                            {
                                "mcpServers": {
                                    "legacy": {
                                        "type": "http",
                                        "url": "https://legacy.example/mcp",
                                    }
                                }
                            },
                            sha="sha-copilot",
                        ),
                    )
                ],
                f"{base_path}/.vscode/mcp.json": [
                    _FakeResponse(
                        200,
                        _github_file_response(
                            {
                                "mcpServers": {
                                    "legacy": {
                                        "type": "http",
                                        "url": "https://legacy.example/mcp",
                                    },
                                    "other": {
                                        "type": "stdio",
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
        service = ToolsService(mock_db, github_service=fake_svc)

        result = await service.update_repo_mcp_server(
            owner="octo",
            repo="repo",
            access_token="token",
            server_name="legacy",
            data=RepoMcpServerUpdate(
                name="modern",
                config_content='{"mcpServers":{"ignored":{"type":"http","url":"https://modern.example/mcp"}}}',
            ),
        )

        assert result.name == "modern"
        assert result.source_paths == [".copilot/mcp.json", ".vscode/mcp.json"]
        put_by_path = dict(fake_svc.put_calls)
        copilot_content = json.loads(
            base64.b64decode(put_by_path[f"{base_path}/.copilot/mcp.json"]["content"]).decode(
                "utf-8"
            )
        )
        vscode_content = json.loads(
            base64.b64decode(put_by_path[f"{base_path}/.vscode/mcp.json"]["content"]).decode(
                "utf-8"
            )
        )
        assert set(copilot_content["mcpServers"].keys()) == {"modern"}
        assert set(vscode_content["mcpServers"].keys()) == {"modern", "other"}

    async def test_delete_repo_mcp_server_removes_server_from_present_paths(self, mock_db):
        base_path = "/repos/octo/repo/contents"
        fake_svc = _FakeGitHubService(
            get_responses={
                f"{base_path}/.copilot/mcp.json": [
                    _FakeResponse(
                        200,
                        _github_file_response(
                            {
                                "mcpServers": {
                                    "legacy": {
                                        "type": "http",
                                        "url": "https://legacy.example/mcp",
                                    }
                                }
                            },
                            sha="sha-copilot",
                        ),
                    )
                ],
                f"{base_path}/.vscode/mcp.json": [
                    _FakeResponse(
                        200,
                        _github_file_response(
                            {
                                "mcpServers": {
                                    "legacy": {
                                        "type": "http",
                                        "url": "https://legacy.example/mcp",
                                    },
                                    "other": {
                                        "type": "http",
                                        "url": "https://other.example/mcp",
                                    },
                                }
                            },
                            sha="sha-vscode",
                        ),
                    )
                ],
            }
        )
        service = ToolsService(mock_db, github_service=fake_svc)

        result = await service.delete_repo_mcp_server(
            owner="octo",
            repo="repo",
            access_token="token",
            server_name="legacy",
        )

        assert result.name == "legacy"
        assert result.source_paths == [".copilot/mcp.json", ".vscode/mcp.json"]
        put_by_path = dict(fake_svc.put_calls)
        copilot_content = json.loads(
            base64.b64decode(put_by_path[f"{base_path}/.copilot/mcp.json"]["content"]).decode(
                "utf-8"
            )
        )
        vscode_content = json.loads(
            base64.b64decode(put_by_path[f"{base_path}/.vscode/mcp.json"]["content"]).decode(
                "utf-8"
            )
        )
        assert copilot_content["mcpServers"] == {}
        assert set(vscode_content["mcpServers"].keys()) == {"other"}

    async def test_update_repo_mcp_server_rejects_invalid_json_in_existing_repo_file(self, mock_db):
        base_path = "/repos/octo/repo/contents"
        fake_svc = _FakeGitHubService(
            get_responses={
                f"{base_path}/.copilot/mcp.json": [
                    _FakeResponse(
                        200,
                        {
                            "sha": "sha-copilot",
                            "content": base64.b64encode(b"{not valid json").decode("utf-8"),
                        },
                    )
                ]
            }
        )
        service = ToolsService(mock_db, github_service=fake_svc)

        try:
            await service.update_repo_mcp_server(
                owner="octo",
                repo="repo",
                access_token="token",
                server_name="legacy",
                data=RepoMcpServerUpdate(
                    name="modern",
                    config_content='{"mcpServers":{"ignored":{"type":"http","url":"https://modern.example/mcp"}}}',
                ),
            )
        except ValueError as exc:
            assert ".copilot/mcp.json" in str(exc)
            assert "Invalid JSON" in str(exc)
        else:
            raise AssertionError("Expected ValueError for invalid repository MCP JSON")

    async def test_update_repo_mcp_server_preflights_all_paths_before_writing(self, mock_db):
        base_path = "/repos/octo/repo/contents"
        fake_svc = _FakeGitHubService(
            get_responses={
                f"{base_path}/.copilot/mcp.json": [
                    _FakeResponse(
                        200,
                        _github_file_response(
                            {
                                "mcpServers": {
                                    "legacy": {
                                        "type": "http",
                                        "url": "https://legacy.example/mcp",
                                    }
                                }
                            },
                            sha="sha-copilot",
                        ),
                    )
                ],
                f"{base_path}/.vscode/mcp.json": [
                    _FakeResponse(
                        200,
                        _github_file_response(
                            {
                                "mcpServers": {
                                    "legacy": {
                                        "type": "http",
                                        "url": "https://legacy.example/mcp",
                                    },
                                    "modern": {
                                        "type": "http",
                                        "url": "https://existing.example/mcp",
                                    },
                                }
                            },
                            sha="sha-vscode",
                        ),
                    )
                ],
            }
        )
        service = ToolsService(mock_db, github_service=fake_svc)

        try:
            await service.update_repo_mcp_server(
                owner="octo",
                repo="repo",
                access_token="token",
                server_name="legacy",
                data=RepoMcpServerUpdate(
                    name="modern",
                    config_content='{"mcpServers":{"ignored":{"type":"http","url":"https://modern.example/mcp"}}}',
                ),
            )
        except ValueError as exc:
            assert ".vscode/mcp.json" in str(exc)
            assert "already exists" in str(exc)
        else:
            raise AssertionError("Expected ValueError for rename collision")

        assert fake_svc.put_calls == []

    async def test_delete_repo_mcp_server_rejects_invalid_json_in_existing_repo_file(self, mock_db):
        base_path = "/repos/octo/repo/contents"
        fake_svc = _FakeGitHubService(
            get_responses={
                f"{base_path}/.copilot/mcp.json": [
                    _FakeResponse(
                        200,
                        {
                            "sha": "sha-copilot",
                            "content": base64.b64encode(b"{not valid json").decode("utf-8"),
                        },
                    )
                ]
            }
        )
        service = ToolsService(mock_db, github_service=fake_svc)

        try:
            await service.delete_repo_mcp_server(
                owner="octo",
                repo="repo",
                access_token="token",
                server_name="legacy",
            )
        except ValueError as exc:
            assert ".copilot/mcp.json" in str(exc)
            assert "Invalid JSON" in str(exc)
        else:
            raise AssertionError("Expected ValueError for invalid repository MCP JSON")


class TestToolsServiceValidation:
    async def test_get_github_service_falls_back_to_singleton(self, mock_db):
        service = ToolsService(mock_db)
        sentinel_service = object()

        with patch("src.services.github_projects.github_projects_service", sentinel_service):
            assert service._get_github_service() is sentinel_service

    async def test_validate_mcp_config_rejects_oversized_payload(self, mock_db):
        service = ToolsService(mock_db)

        is_valid, error = service.validate_mcp_config(
            json.dumps({"mcpServers": {"srv": {"type": "http", "url": "https://x"}}})
            + ("x" * 262145)
        )

        assert is_valid is False
        assert "maximum size" in error

    async def test_validate_mcp_config_rejects_invalid_json_and_accepts_inferred_types(
        self, mock_db
    ):
        service = ToolsService(mock_db)

        is_valid, error = service.validate_mcp_config("{not json")
        assert is_valid is False
        assert "Invalid JSON" in error

        inferred_http_valid, inferred_http_error = service.validate_mcp_config(
            json.dumps({"mcpServers": {"srv": {"url": "https://example.com/mcp"}}})
        )
        inferred_stdio_valid, inferred_stdio_error = service.validate_mcp_config(
            json.dumps({"mcpServers": {"srv": {"command": "npx"}}})
        )

        assert inferred_http_valid is True
        assert inferred_http_error == ""
        assert inferred_stdio_valid is True
        assert inferred_stdio_error == ""

    async def test_validate_mcp_config_rejects_invalid_shapes(self, mock_db):
        service = ToolsService(mock_db)

        invalid_cases = [
            ("[]", "JSON object"),
            (json.dumps({"mcpServers": {}}), "at least one server entry"),
            (json.dumps({"mcpServers": {"srv": "bad"}}), "must be an object"),
            (json.dumps({"mcpServers": {"srv": {"type": "ftp"}}}), "supported 'type'"),
            (json.dumps({"mcpServers": {"srv": {"type": "http"}}}), "must have a 'url'"),
            (json.dumps({"mcpServers": {"srv": {"type": "stdio"}}}), "must have a 'command'"),
            (
                json.dumps(
                    {"mcpServers": {"srv": {"type": "http", "url": "https://x", "headers": []}}}
                ),
                "field 'headers' must be an object",
            ),
            (
                json.dumps(
                    {"mcpServers": {"srv": {"type": "http", "url": "https://x", "tools": [1]}}}
                ),
                "field 'tools' must be '*' or a list of strings",
            ),
            (
                json.dumps(
                    {"mcpServers": {"srv": {"type": "http", "url": "https://x", "env": []}}}
                ),
                "field 'env' must be an object",
            ),
        ]

        for payload, expected in invalid_cases:
            is_valid, error = service.validate_mcp_config(payload)
            assert is_valid is False
            assert expected in error

    async def test_extract_helpers_handle_invalid_or_ambiguous_content(self, mock_db):
        service = ToolsService(mock_db)

        assert service._extract_endpoint_url("not-json") == ""
        assert service._extract_server_names("not-json") == set()
        assert (
            service._extract_endpoint_url(json.dumps({"mcpServers": {"srv": {"url": "https://x"}}}))
            == "https://x"
        )
        assert (
            service._extract_endpoint_url(json.dumps({"mcpServers": {"srv": {"command": "uvx"}}}))
            == "uvx"
        )
        assert (
            service._extract_endpoint_url(json.dumps({"mcpServers": {"srv": {"type": "http"}}}))
            == ""
        )
        assert service._extract_server_names(
            json.dumps({"mcpServers": {"  alpha  ": {}, "": {}, "beta": {}}})
        ) == {"alpha", "beta"}

        try:
            service._extract_single_server_config(
                json.dumps({"mcpServers": {"a": {}, "b": {}}}),
                server_name="renamed",
            )
        except ValueError as exc:
            assert "exactly one MCP server entry" in str(exc)
        else:
            raise AssertionError("Expected ValueError for multiple MCP servers")

        try:
            service._extract_single_server_config(
                json.dumps({"mcpServers": {"a": "bad"}}),
                server_name="renamed",
            )
        except ValueError as exc:
            assert "must be an object" in str(exc)
        else:
            raise AssertionError("Expected ValueError for non-object MCP server config")

        try:
            service._parse_repo_mcp_content("{not valid json", path=".copilot/mcp.json")
        except ValueError as exc:
            assert "Invalid JSON" in str(exc)
            assert ".copilot/mcp.json" in str(exc)
        else:
            raise AssertionError("Expected ValueError for invalid repo MCP JSON")

        try:
            service._parse_repo_mcp_content("[]", path=".copilot/mcp.json")
        except ValueError as exc:
            assert "must contain a JSON object" in str(exc)
        else:
            raise AssertionError("Expected ValueError for non-object repo MCP config")


class TestToolsServiceCrudAndAssociations:
    async def test_get_protected_server_names_collects_other_tool_servers(self, mock_db):
        await _insert_tool(
            mock_db,
            tool_id="tool-a",
            config_content='{"mcpServers":{"github":{"type":"http","url":"https://example.com/github"}}}',
        )
        await _insert_tool(
            mock_db,
            tool_id="tool-b",
            config_content='{"mcpServers":{"docs":{"type":"http","url":"https://example.com/docs"}}}',
        )
        service = ToolsService(mock_db)

        protected = await service._get_protected_server_names(
            project_id=PROJECT_ID,
            github_user_id=USER_ID,
            exclude_tool_id="tool-a",
        )

        assert protected == {"docs"}

    async def test_list_tools_and_missing_tool_lookup(self, mock_db):
        await _insert_tool(mock_db, tool_id="tool-a", name="First")
        await _insert_tool(mock_db, tool_id="tool-b", name="Second")
        service = ToolsService(mock_db)

        result = await service.list_tools(PROJECT_ID, USER_ID)

        assert result.count == 2
        assert {tool.id for tool in result.tools} == {"tool-a", "tool-b"}
        assert await service.get_tool(PROJECT_ID, "missing", USER_ID) is None

    async def test_create_tool_rejects_duplicate_name_and_project_limit(self, mock_db):
        await _insert_tool(mock_db, name="Docs MCP")
        service = ToolsService(mock_db)

        try:
            await service.create_tool(
                project_id=PROJECT_ID,
                github_user_id=USER_ID,
                data=McpToolConfigCreate(
                    name="Docs MCP",
                    description="",
                    config_content='{"mcpServers":{"docs":{"type":"http","url":"https://docs.example"}}}',
                    github_repo_target="",
                ),
                owner="octo",
                repo="repo",
                access_token="token",
            )
        except Exception as exc:
            assert "already exists" in str(exc)
        else:
            raise AssertionError("Expected duplicate tool name rejection")

        for index in range(2, 26):
            await _insert_tool(mock_db, tool_id=f"tool-{index}", name=f"Tool {index}")

        try:
            await service.create_tool(
                project_id=PROJECT_ID,
                github_user_id=USER_ID,
                data=McpToolConfigCreate(
                    name="Overflow",
                    description="",
                    config_content='{"mcpServers":{"overflow":{"type":"http","url":"https://overflow.example"}}}',
                    github_repo_target="",
                ),
                owner="octo",
                repo="repo",
                access_token="token",
            )
        except ValueError as exc:
            assert "Maximum of 25" in str(exc)
        else:
            raise AssertionError("Expected project tool limit rejection")

    async def test_create_tool_uses_explicit_repo_target_for_sync(self, mock_db):
        service = ToolsService(mock_db)

        with patch.object(
            service,
            "sync_tool_to_github",
            AsyncMock(
                return_value=McpToolConfigSyncResult(
                    id="generated-tool",
                    sync_status="synced",
                    sync_error="",
                    synced_at="2026-03-19T00:00:00+00:00",
                )
            ),
        ) as sync_mock:
            result = await service.create_tool(
                project_id=PROJECT_ID,
                github_user_id=USER_ID,
                data=McpToolConfigCreate(
                    name="Azure MCP",
                    description="",
                    config_content='{"mcpServers":{"azure":{"type":"local","command":"npx"}}}',
                    github_repo_target="other-owner/other-repo",
                ),
                owner="octo",
                repo="repo",
                access_token="token",
            )

        assert result.endpoint_url == "npx"
        assert result.github_repo_target == "other-owner/other-repo"
        assert sync_mock.await_args.args[3:5] == ("other-owner", "other-repo")

    async def test_delete_tool_returns_affected_agents_without_confirm(self, mock_db):
        await _insert_tool(mock_db)
        await _insert_agent(mock_db, agent_id="agent-1")
        await mock_db.execute(
            "INSERT INTO agent_tool_associations (agent_id, tool_id, assigned_at) VALUES (?, ?, datetime('now'))",
            ("agent-1", TOOL_ID),
        )
        await mock_db.commit()
        service = ToolsService(mock_db)

        result = await service.delete_tool(
            project_id=PROJECT_ID,
            tool_id=TOOL_ID,
            github_user_id=USER_ID,
            confirm=False,
            owner="octo",
            repo="repo",
            access_token="token",
        )

        assert result.success is False
        assert [agent.id for agent in result.affected_agents] == ["agent-1"]

    async def test_delete_tool_successfully_removes_tool_and_associations(self, mock_db):
        await _insert_tool(mock_db)
        await _insert_agent(mock_db, agent_id="agent-1")
        await mock_db.execute(
            "INSERT INTO agent_tool_associations (agent_id, tool_id, assigned_at) VALUES (?, ?, datetime('now'))",
            ("agent-1", TOOL_ID),
        )
        await mock_db.commit()
        service = ToolsService(mock_db)

        with (
            patch.object(service, "_remove_from_github", AsyncMock()) as remove_mock,
            patch(
                "src.services.agents.agent_mcp_sync.sync_agent_mcps",
                AsyncMock(side_effect=RuntimeError("sync failed")),
            ),
        ):
            result = await service.delete_tool(
                project_id=PROJECT_ID,
                tool_id=TOOL_ID,
                github_user_id=USER_ID,
                confirm=True,
                owner="octo",
                repo="repo",
                access_token="token",
            )

        assert result.success is True
        remove_mock.assert_awaited_once()
        assert await service.get_tool(PROJECT_ID, TOOL_ID, USER_ID) is None
        cursor = await mock_db.execute(
            "SELECT COUNT(*) AS cnt FROM agent_tool_associations WHERE tool_id = ?", (TOOL_ID,)
        )
        row = await cursor.fetchone()
        assert row["cnt"] == 0

    async def test_update_agent_tools_can_clear_existing_associations(self, mock_db):
        await _insert_tool(mock_db, tool_id="tool-a", name="First")
        await _insert_agent(mock_db, agent_id="agent-1")
        await mock_db.execute(
            "INSERT INTO agent_tool_associations (agent_id, tool_id, assigned_at) VALUES (?, ?, datetime('now'))",
            ("agent-1", "tool-a"),
        )
        await mock_db.execute(
            "UPDATE agent_configs SET tools = ? WHERE id = ?",
            (json.dumps(["tool-a"]), "agent-1"),
        )
        await mock_db.commit()
        service = ToolsService(mock_db)

        updated = await service.update_agent_tools("agent-1", [], PROJECT_ID, USER_ID)

        assert updated.tools == []
        cursor = await mock_db.execute("SELECT tools FROM agent_configs WHERE id = ?", ("agent-1",))
        row = await cursor.fetchone()
        assert json.loads(row["tools"]) == []

    async def test_get_and_update_agent_tools_cover_validation_paths(self, mock_db):
        await _insert_tool(mock_db, tool_id="tool-a", name="First")
        await _insert_tool(mock_db, tool_id="tool-b", name="Second")
        await _insert_agent(mock_db, agent_id="agent-1")
        service = ToolsService(mock_db)

        empty = await service.get_agent_tools("missing-agent", PROJECT_ID, USER_ID)
        assert empty.tools == []

        try:
            await service.update_agent_tools("missing-agent", ["tool-a"], PROJECT_ID, USER_ID)
        except ValueError as exc:
            assert "not found" in str(exc)
        else:
            raise AssertionError("Expected missing-agent validation error")

        try:
            await service.update_agent_tools(
                "agent-1", ["tool-a", "tool-missing"], PROJECT_ID, USER_ID
            )
        except ValueError as exc:
            assert "tool-missing" in str(exc)
        else:
            raise AssertionError("Expected invalid tool id validation error")

        updated = await service.update_agent_tools(
            "agent-1", ["tool-a", "tool-b"], PROJECT_ID, USER_ID
        )

        assert {tool.id for tool in updated.tools} == {"tool-a", "tool-b"}
        cursor = await mock_db.execute("SELECT tools FROM agent_configs WHERE id = ?", ("agent-1",))
        row = await cursor.fetchone()
        assert json.loads(row["tools"]) == ["tool-a", "tool-b"]


class TestToolsServiceRepoErrors:
    async def test_get_repo_mcp_config_raises_on_unexpected_github_status(self, mock_db):
        base_path = "/repos/octo/repo/contents"
        fake_svc = _FakeGitHubService(
            get_responses={
                f"{base_path}/.copilot/mcp.json": [_FakeResponse(500, text="server error")],
            }
        )
        service = ToolsService(mock_db, github_service=fake_svc)

        try:
            await service.get_repo_mcp_config(owner="octo", repo="repo", access_token="token")
        except RuntimeError as exc:
            assert "GitHub API error" in str(exc)
        else:
            raise AssertionError("Expected GitHub status error")

    async def test_sync_tool_to_github_marks_error_when_write_fails(self, mock_db):
        await _insert_tool(mock_db)
        base_path = "/repos/octo/repo/contents"
        fake_svc = _FakeGitHubService(
            get_responses={
                f"{base_path}/.copilot/mcp.json": [_FakeResponse(404)],
                f"{base_path}/.vscode/mcp.json": [_FakeResponse(404)],
            },
            put_status=500,
        )
        service = ToolsService(mock_db, github_service=fake_svc)

        result = await service.sync_tool_to_github(
            TOOL_ID, PROJECT_ID, USER_ID, "octo", "repo", "token"
        )

        assert result.sync_status == "error"
        assert "GitHub API write error" in result.sync_error

    async def test_remove_from_github_handles_invalid_tool_json_without_puts(self, mock_db):
        await _insert_tool(mock_db, config_content="not-json")
        base_path = "/repos/octo/repo/contents"
        fake_svc = _FakeGitHubService(
            get_responses={
                f"{base_path}/.copilot/mcp.json": [
                    _FakeResponse(
                        200,
                        _github_file_response(
                            {
                                "mcpServers": {
                                    "context7": {"type": "http", "url": "https://example.com"}
                                }
                            }
                        ),
                    )
                ],
                f"{base_path}/.vscode/mcp.json": [
                    _FakeResponse(
                        200,
                        _github_file_response(
                            {
                                "mcpServers": {
                                    "context7": {"type": "http", "url": "https://example.com"}
                                }
                            }
                        ),
                    )
                ],
            }
        )
        service = ToolsService(mock_db, github_service=fake_svc)
        tool = await service.get_tool(PROJECT_ID, TOOL_ID, USER_ID)
        assert tool is not None

        await service._remove_from_github(tool, "octo", "repo", "token")

        assert fake_svc.put_calls == []

    async def test_remove_from_github_removes_unprotected_servers_and_preserves_others(
        self, mock_db
    ):
        await _insert_tool(
            mock_db,
            config_content='{"mcpServers":{"context7":{"type":"http","url":"https://example.com/mcp"}}}',
        )
        base_path = "/repos/octo/repo/contents"
        fake_svc = _FakeGitHubService(
            get_responses={
                f"{base_path}/.copilot/mcp.json": [
                    _FakeResponse(
                        200,
                        _github_file_response(
                            {
                                "mcpServers": {
                                    "context7": {"type": "http", "url": "https://example.com/mcp"},
                                    "other": {"type": "stdio", "command": "npx"},
                                }
                            },
                            sha="sha-copilot",
                        ),
                    )
                ],
                f"{base_path}/.vscode/mcp.json": [
                    _FakeResponse(
                        200,
                        _github_file_response(
                            {
                                "mcpServers": {
                                    "context7": {"type": "http", "url": "https://example.com/mcp"}
                                }
                            },
                            sha="sha-vscode",
                        ),
                    )
                ],
            }
        )
        service = ToolsService(mock_db, github_service=fake_svc)
        tool = await service.get_tool(PROJECT_ID, TOOL_ID, USER_ID)
        assert tool is not None

        await service._remove_from_github(tool, "octo", "repo", "token")

        assert len(fake_svc.put_calls) == 2
        put_by_path = dict(fake_svc.put_calls)
        copilot_body = put_by_path[f"{base_path}/.copilot/mcp.json"]
        vscode_body = put_by_path[f"{base_path}/.vscode/mcp.json"]
        assert copilot_body["sha"] == "sha-copilot"
        assert vscode_body["sha"] == "sha-vscode"

        copilot_content = json.loads(base64.b64decode(copilot_body["content"]).decode("utf-8"))
        vscode_content = json.loads(base64.b64decode(vscode_body["content"]).decode("utf-8"))
        assert copilot_content["mcpServers"] == {"other": {"type": "stdio", "command": "npx"}}
        assert vscode_content["mcpServers"] == {}

    async def test_remove_from_github_normalizes_non_dict_repo_server_map(self, mock_db):
        await _insert_tool(mock_db)
        base_path = "/repos/octo/repo/contents"
        fake_svc = _FakeGitHubService(
            get_responses={
                f"{base_path}/.copilot/mcp.json": [
                    _FakeResponse(200, _github_file_response({"mcpServers": []}, sha="sha-copilot"))
                ],
                f"{base_path}/.vscode/mcp.json": [_FakeResponse(404)],
            }
        )
        service = ToolsService(mock_db, github_service=fake_svc)
        tool = await service.get_tool(PROJECT_ID, TOOL_ID, USER_ID)
        assert tool is not None

        await service._remove_from_github(tool, "octo", "repo", "token")

        assert len(fake_svc.put_calls) == 1
        _, put_body = fake_svc.put_calls[0]
        assert json.loads(base64.b64decode(put_body["content"]).decode("utf-8"))["mcpServers"] == {}
