"""Tools service — CRUD, validation, GitHub sync for MCP tool configurations.

Stores MCP configurations in the ``mcp_configurations`` table and syncs them
to the connected GitHub repository's ``.copilot/mcp.json`` file via the
Contents API.
"""

from __future__ import annotations

import base64
import json
import logging
import uuid

import aiosqlite

from src.models.tools import (
    AgentToolInfo,
    AgentToolsResponse,
    McpToolConfigCreate,
    McpToolConfigListResponse,
    McpToolConfigResponse,
    McpToolConfigSyncResult,
    ToolDeleteResult,
)
from src.utils import utcnow

logger = logging.getLogger(__name__)

MAX_TOOLS_PER_PROJECT = 25
MAX_CONFIG_SIZE = 262144  # 256 KB
MCP_CONFIG_PATH = ".copilot/mcp.json"


class ToolsService:
    """Manages MCP tool configuration CRUD, validation, and GitHub sync."""

    def __init__(self, db: aiosqlite.Connection) -> None:
        self.db = db

    # ── Validation ──

    @staticmethod
    def validate_mcp_config(config_content: str) -> tuple[bool, str]:
        """Validate MCP configuration JSON against expected schema.

        Returns (is_valid, error_message).
        """
        if len(config_content.encode("utf-8")) > MAX_CONFIG_SIZE:
            return False, "Configuration exceeds maximum size of 256 KB"

        try:
            data = json.loads(config_content)
        except json.JSONDecodeError as exc:
            return False, f"Invalid JSON: {exc}"

        if not isinstance(data, dict):
            return False, "Configuration must be a JSON object"

        mcp_servers = data.get("mcpServers")
        if not isinstance(mcp_servers, dict) or len(mcp_servers) == 0:
            return (
                False,
                "Configuration must contain a 'mcpServers' object with at least one server entry",
            )

        for server_name, server_config in mcp_servers.items():
            if not isinstance(server_config, dict):
                return False, f"Server '{server_name}' must be an object"

            server_type = server_config.get("type")

            # Infer type from fields when not explicitly specified
            if server_type is None:
                if server_config.get("command"):
                    server_type = "stdio"
                elif server_config.get("url"):
                    server_type = "http"

            if server_type not in ("http", "stdio"):
                return False, f"Server '{server_name}' must have 'type' of 'http' or 'stdio', or include a 'command' (stdio) or 'url' (http) field"

            if server_type == "http" and not server_config.get("url"):
                return False, f"HTTP server '{server_name}' must have a 'url' field"

            if server_type == "stdio" and not server_config.get("command"):
                return False, f"Stdio server '{server_name}' must have a 'command' field"

        return True, ""

    @staticmethod
    def _extract_endpoint_url(config_content: str) -> str:
        """Extract the primary endpoint URL or command from MCP config."""
        try:
            data = json.loads(config_content)
            servers = data.get("mcpServers", {})
            for cfg in servers.values():
                server_type = cfg.get("type")
                # Infer type from fields when not explicitly specified
                if server_type is None:
                    if cfg.get("command"):
                        server_type = "stdio"
                    elif cfg.get("url"):
                        server_type = "http"
                if server_type == "http":
                    return cfg.get("url", "")
                if server_type == "stdio":
                    return cfg.get("command", "")
        except (json.JSONDecodeError, AttributeError):
            pass
        return ""

    # ── CRUD ──

    async def list_tools(self, project_id: str, github_user_id: str) -> McpToolConfigListResponse:
        """List all MCP tools for a project owned by the user."""
        cursor = await self.db.execute(
            "SELECT id, github_user_id, project_id, name, description, endpoint_url, "
            "config_content, sync_status, sync_error, synced_at, github_repo_target, "
            "is_active, created_at, updated_at "
            "FROM mcp_configurations "
            "WHERE project_id = ? AND github_user_id = ? "
            "ORDER BY created_at DESC",
            (project_id, github_user_id),
        )
        rows = await cursor.fetchall()

        tools = [
            McpToolConfigResponse(
                id=row["id"],
                name=row["name"],
                description=row["description"],
                endpoint_url=row["endpoint_url"],
                config_content=row["config_content"],
                sync_status=row["sync_status"],
                sync_error=row["sync_error"],
                synced_at=row["synced_at"],
                github_repo_target=row["github_repo_target"],
                is_active=bool(row["is_active"]),
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )
            for row in rows
        ]
        return McpToolConfigListResponse(tools=tools, count=len(tools))

    async def get_tool(
        self, project_id: str, tool_id: str, github_user_id: str
    ) -> McpToolConfigResponse | None:
        """Get a single MCP tool configuration."""
        cursor = await self.db.execute(
            "SELECT id, github_user_id, project_id, name, description, endpoint_url, "
            "config_content, sync_status, sync_error, synced_at, github_repo_target, "
            "is_active, created_at, updated_at "
            "FROM mcp_configurations "
            "WHERE id = ? AND project_id = ? AND github_user_id = ?",
            (tool_id, project_id, github_user_id),
        )
        row = await cursor.fetchone()
        if not row:
            return None

        return McpToolConfigResponse(
            id=row["id"],
            name=row["name"],
            description=row["description"],
            endpoint_url=row["endpoint_url"],
            config_content=row["config_content"],
            sync_status=row["sync_status"],
            sync_error=row["sync_error"],
            synced_at=row["synced_at"],
            github_repo_target=row["github_repo_target"],
            is_active=bool(row["is_active"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    async def create_tool(
        self,
        project_id: str,
        github_user_id: str,
        data: McpToolConfigCreate,
        owner: str,
        repo: str,
        access_token: str,
    ) -> McpToolConfigResponse:
        """Create a new MCP tool configuration and trigger sync."""
        # Validate config
        is_valid, error_msg = self.validate_mcp_config(data.config_content)
        if not is_valid:
            raise ValueError(error_msg)

        # Check duplicate name
        cursor = await self.db.execute(
            "SELECT COUNT(*) as cnt FROM mcp_configurations "
            "WHERE project_id = ? AND github_user_id = ? AND name = ?",
            (project_id, github_user_id, data.name),
        )
        row = await cursor.fetchone()
        if row and row["cnt"] > 0:
            raise DuplicateToolNameError(
                f"An MCP tool named '{data.name}' already exists in this project"
            )

        # Check per-project limit
        cursor = await self.db.execute(
            "SELECT COUNT(*) as cnt FROM mcp_configurations "
            "WHERE project_id = ? AND github_user_id = ?",
            (project_id, github_user_id),
        )
        row = await cursor.fetchone()
        if row and row["cnt"] >= MAX_TOOLS_PER_PROJECT:
            raise ValueError(f"Maximum of {MAX_TOOLS_PER_PROJECT} MCP tools per project reached")

        now = utcnow().isoformat()
        tool_id = str(uuid.uuid4())
        endpoint_url = self._extract_endpoint_url(data.config_content)
        github_repo_target = data.github_repo_target or f"{owner}/{repo}"

        await self.db.execute(
            "INSERT INTO mcp_configurations "
            "(id, github_user_id, project_id, name, description, endpoint_url, "
            "config_content, sync_status, sync_error, github_repo_target, "
            "is_active, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, 'pending', '', ?, 1, ?, ?)",
            (
                tool_id,
                github_user_id,
                project_id,
                data.name,
                data.description,
                endpoint_url,
                data.config_content,
                github_repo_target,
                now,
                now,
            ),
        )
        await self.db.commit()

        logger.info("Created MCP tool %s for project %s", tool_id, project_id)

        # Use the stored github_repo_target if it specifies a different owner/repo.
        sync_owner, sync_repo = owner, repo
        if github_repo_target and "/" in github_repo_target:
            target_owner, target_repo = github_repo_target.split("/", 1)
            target_owner = target_owner.strip()
            target_repo = target_repo.strip()
            if target_owner and target_repo:
                sync_owner, sync_repo = target_owner, target_repo

        # Trigger sync
        sync_result = await self.sync_tool_to_github(
            tool_id,
            project_id,
            github_user_id,
            sync_owner,
            sync_repo,
            access_token,
        )

        return McpToolConfigResponse(
            id=tool_id,
            name=data.name,
            description=data.description,
            endpoint_url=endpoint_url,
            config_content=data.config_content,
            sync_status=sync_result.sync_status,
            sync_error=sync_result.sync_error,
            synced_at=sync_result.synced_at,
            github_repo_target=github_repo_target,
            is_active=True,
            created_at=now,
            updated_at=now,
        )

    async def delete_tool(
        self,
        project_id: str,
        tool_id: str,
        github_user_id: str,
        confirm: bool,
        owner: str,
        repo: str,
        access_token: str,
    ) -> ToolDeleteResult:
        """Delete an MCP tool. Returns affected agents if confirm=False."""
        # Check tool exists
        tool = await self.get_tool(project_id, tool_id, github_user_id)
        if not tool:
            return ToolDeleteResult(success=False, deleted_id=None, affected_agents=[])

        # Check affected agents
        affected = await self.get_agents_using_tool(tool_id)
        if affected and not confirm:
            return ToolDeleteResult(success=False, deleted_id=None, affected_agents=affected)

        # Remove from GitHub
        try:
            await self._remove_from_github(tool, owner, repo, access_token)
        except Exception:
            logger.exception("Failed to remove tool %s from GitHub", tool_id)

        # Delete associations
        await self.db.execute("DELETE FROM agent_tool_associations WHERE tool_id = ?", (tool_id,))
        # Delete tool
        await self.db.execute(
            "DELETE FROM mcp_configurations WHERE id = ? AND github_user_id = ?",
            (tool_id, github_user_id),
        )
        await self.db.commit()

        logger.info("Deleted MCP tool %s", tool_id)
        return ToolDeleteResult(success=True, deleted_id=tool_id, affected_agents=[])

    # ── GitHub Sync ──

    async def sync_tool_to_github(
        self,
        tool_id: str,
        project_id: str,
        github_user_id: str,
        owner: str,
        repo: str,
        access_token: str,
    ) -> McpToolConfigSyncResult:
        """Sync an MCP tool configuration to GitHub .copilot/mcp.json."""
        import httpx

        tool = await self.get_tool(project_id, tool_id, github_user_id)
        if not tool:
            return McpToolConfigSyncResult(
                id=tool_id, sync_status="error", sync_error="Tool not found", synced_at=None
            )

        # Set pending
        await self.db.execute(
            "UPDATE mcp_configurations SET sync_status = 'pending', sync_error = '' WHERE id = ?",
            (tool_id,),
        )
        await self.db.commit()

        try:
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            }

            async with httpx.AsyncClient(timeout=30.0) as client:
                # Read current file
                existing_sha = None
                existing_content: dict = {"mcpServers": {}}
                get_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{MCP_CONFIG_PATH}"
                resp = await client.get(get_url, headers=headers)

                if resp.status_code == 200:
                    file_data = resp.json()
                    existing_sha = file_data.get("sha")
                    raw = base64.b64decode(file_data.get("content", "")).decode("utf-8")
                    existing_content = json.loads(raw)
                elif resp.status_code != 404:
                    raise RuntimeError(f"GitHub API error: {resp.status_code} {resp.text[:200]}")

                # Merge tool config
                tool_config = json.loads(tool.config_content)
                mcp_servers = existing_content.get("mcpServers", {})
                mcp_servers.update(tool_config.get("mcpServers", {}))
                existing_content["mcpServers"] = mcp_servers

                # Write updated file
                new_content = json.dumps(existing_content, indent=2) + "\n"
                encoded = base64.b64encode(new_content.encode("utf-8")).decode("utf-8")

                put_body: dict = {
                    "message": f"chore: sync MCP tool '{tool.name}' configuration",
                    "content": encoded,
                }
                if existing_sha:
                    put_body["sha"] = existing_sha

                put_resp = await client.put(get_url, headers=headers, json=put_body)
                if put_resp.status_code not in (200, 201):
                    raise RuntimeError(
                        f"GitHub API write error: {put_resp.status_code} {put_resp.text[:200]}"
                    )

            # Update status
            now = utcnow().isoformat()
            await self.db.execute(
                "UPDATE mcp_configurations SET sync_status = 'synced', sync_error = '', synced_at = ?, updated_at = ? WHERE id = ?",
                (now, now, tool_id),
            )
            await self.db.commit()

            logger.info("Synced MCP tool %s to GitHub %s/%s", tool_id, owner, repo)
            return McpToolConfigSyncResult(
                id=tool_id, sync_status="synced", sync_error="", synced_at=now
            )

        except Exception as exc:
            error_msg = str(exc)[:500]
            now = utcnow().isoformat()
            await self.db.execute(
                "UPDATE mcp_configurations SET sync_status = 'error', sync_error = ?, updated_at = ? WHERE id = ?",
                (error_msg, now, tool_id),
            )
            await self.db.commit()

            logger.exception("Failed to sync tool %s to GitHub", tool_id)
            return McpToolConfigSyncResult(
                id=tool_id, sync_status="error", sync_error=error_msg, synced_at=None
            )

    async def _remove_from_github(
        self,
        tool: McpToolConfigResponse,
        owner: str,
        repo: str,
        access_token: str,
    ) -> None:
        """Remove an MCP server entry from .copilot/mcp.json."""
        import httpx

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            get_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{MCP_CONFIG_PATH}"
            resp = await client.get(get_url, headers=headers)
            if resp.status_code != 200:
                return

            file_data = resp.json()
            existing_sha = file_data.get("sha")
            raw = base64.b64decode(file_data.get("content", "")).decode("utf-8")
            existing_content = json.loads(raw)

            # Remove tool servers
            try:
                tool_config = json.loads(tool.config_content)
                tool_server_names = list(tool_config.get("mcpServers", {}).keys())
            except (json.JSONDecodeError, AttributeError):
                tool_server_names = []

            mcp_servers = existing_content.get("mcpServers", {})
            for name in tool_server_names:
                mcp_servers.pop(name, None)
            existing_content["mcpServers"] = mcp_servers

            new_content = json.dumps(existing_content, indent=2) + "\n"
            encoded = base64.b64encode(new_content.encode("utf-8")).decode("utf-8")

            put_body: dict = {
                "message": f"chore: remove MCP tool '{tool.name}' configuration",
                "content": encoded,
            }
            if existing_sha:
                put_body["sha"] = existing_sha

            await client.put(get_url, headers=headers, json=put_body)

    # ── Agent-Tool Associations ──

    async def get_agents_using_tool(self, tool_id: str) -> list[AgentToolInfo]:
        """Get agents that use a specific tool."""
        cursor = await self.db.execute(
            "SELECT a.agent_id, ac.name, ac.description "
            "FROM agent_tool_associations a "
            "JOIN agent_configs ac ON a.agent_id = ac.id "
            "WHERE a.tool_id = ?",
            (tool_id,),
        )
        rows = await cursor.fetchall()
        return [
            AgentToolInfo(id=row["agent_id"], name=row["name"], description=row["description"])
            for row in rows
        ]

    async def get_agent_tools(
        self, agent_id: str, project_id: str, github_user_id: str
    ) -> AgentToolsResponse:
        """Get MCP tools assigned to an agent, scoped by project ownership."""
        # Verify agent belongs to this project and user
        cursor = await self.db.execute(
            "SELECT id FROM agent_configs WHERE id = ? AND project_id = ? AND created_by = ?",
            (agent_id, project_id, github_user_id),
        )
        if not await cursor.fetchone():
            return AgentToolsResponse(tools=[])

        cursor = await self.db.execute(
            "SELECT mc.id, mc.name, mc.description "
            "FROM agent_tool_associations ata "
            "JOIN mcp_configurations mc ON ata.tool_id = mc.id "
            "WHERE ata.agent_id = ?",
            (agent_id,),
        )
        rows = await cursor.fetchall()
        tools = [
            AgentToolInfo(id=row["id"], name=row["name"], description=row["description"])
            for row in rows
        ]
        return AgentToolsResponse(tools=tools)

    async def update_agent_tools(
        self, agent_id: str, tool_ids: list[str], project_id: str, github_user_id: str
    ) -> AgentToolsResponse:
        """Set the MCP tools for an agent (replace all)."""
        # Verify agent belongs to this project and user
        cursor = await self.db.execute(
            "SELECT id FROM agent_configs WHERE id = ? AND project_id = ? AND created_by = ?",
            (agent_id, project_id, github_user_id),
        )
        if not await cursor.fetchone():
            raise ValueError(f"Agent {agent_id} not found in this project")

        # Validate all tool IDs exist
        if tool_ids:
            placeholders = ",".join("?" for _ in tool_ids)
            cursor = await self.db.execute(
                f"SELECT id FROM mcp_configurations WHERE id IN ({placeholders}) "
                "AND project_id = ? AND github_user_id = ?",
                (*tool_ids, project_id, github_user_id),
            )
            valid_rows = await cursor.fetchall()
            valid_ids = {row["id"] for row in valid_rows}
            invalid_ids = [tid for tid in tool_ids if tid not in valid_ids]
            if invalid_ids:
                raise ValueError(f"Invalid tool IDs: {', '.join(invalid_ids)}")

        # Replace associations
        now = utcnow().isoformat()
        await self.db.execute("DELETE FROM agent_tool_associations WHERE agent_id = ?", (agent_id,))
        for tid in tool_ids:
            await self.db.execute(
                "INSERT OR IGNORE INTO agent_tool_associations (agent_id, tool_id, assigned_at) "
                "VALUES (?, ?, ?)",
                (agent_id, tid, now),
            )

        # Also update the tools JSON column on agent_configs
        tools_json = json.dumps(tool_ids)
        await self.db.execute(
            "UPDATE agent_configs SET tools = ? WHERE id = ?",
            (tools_json, agent_id),
        )
        await self.db.commit()

        return await self.get_agent_tools(agent_id, project_id, github_user_id)


class DuplicateToolNameError(Exception):
    """Raised when a tool with the same name already exists."""
