from unittest.mock import AsyncMock, patch

from src.models.tools import McpToolConfigSyncResult, McpToolConfigUpdate
from src.services.tools.service import ToolsService

PROJECT_ID = "project-123"
USER_ID = "user-123"
TOOL_ID = "tool-123"


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
