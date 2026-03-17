"""Tools service — CRUD, validation, GitHub sync for MCP tool configurations.

Stores MCP configurations in the ``mcp_configurations`` table and syncs them
to the connected GitHub repository's supported MCP config files via the
Contents API.
"""

from __future__ import annotations

import base64
import json
import uuid
from typing import TYPE_CHECKING

import aiosqlite

from src.logging_utils import get_logger
from src.models.tools import (
    AgentToolInfo,
    AgentToolsResponse,
    McpToolConfigCreate,
    McpToolConfigListResponse,
    McpToolConfigResponse,
    McpToolConfigSyncResult,
    McpToolConfigUpdate,
    RepoMcpConfigResponse,
    RepoMcpServerConfig,
    RepoMcpServerUpdate,
    ToolDeleteResult,
)
from src.utils import utcnow

if TYPE_CHECKING:
    from src.services.github_projects.service import GitHubProjectsService

logger = get_logger(__name__)

MAX_TOOLS_PER_PROJECT = 25
MAX_CONFIG_SIZE = 262144  # 256 KB
MCP_CONFIG_PATHS = (".copilot/mcp.json", ".vscode/mcp.json")
ALLOWED_SERVER_TYPES = {"http", "stdio", "local", "sse"}


class ToolsService:
    """Manages MCP tool configuration CRUD, validation, and GitHub sync."""

    def __init__(
        self,
        db: aiosqlite.Connection,
        github_service: GitHubProjectsService | None = None,
    ) -> None:
        self.db = db
        self._github_service = github_service

    def _get_github_service(self) -> GitHubProjectsService:
        """Return the injected service or fall back to the module-level singleton."""
        if self._github_service is not None:
            return self._github_service
        from src.services.github_projects import github_projects_service

        return github_projects_service

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

            if server_type not in ALLOWED_SERVER_TYPES:
                return (
                    False,
                    f"Server '{server_name}' must have a supported 'type' ({', '.join(sorted(ALLOWED_SERVER_TYPES))}), or include a 'command' or 'url' field",
                )

            if server_type in {"http", "sse"} and not server_config.get("url"):
                return False, f"Server '{server_name}' must have a 'url' field"

            if server_type in {"stdio", "local"} and not server_config.get("command"):
                return False, f"Server '{server_name}' must have a 'command' field"

            headers = server_config.get("headers")
            if headers is not None and not isinstance(headers, dict):
                return False, f"Server '{server_name}' field 'headers' must be an object"

            tools = server_config.get("tools")
            if tools is not None and not (
                tools == "*" or (isinstance(tools, list) and all(isinstance(t, str) for t in tools))
            ):
                return (
                    False,
                    f"Server '{server_name}' field 'tools' must be '*' or a list of strings",
                )

            env = server_config.get("env")
            if env is not None and not isinstance(env, dict):
                return False, f"Server '{server_name}' field 'env' must be an object"

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
                if server_type in {"http", "sse"}:
                    return cfg.get("url", "")
                if server_type in {"stdio", "local"}:
                    return cfg.get("command", "")
        except (json.JSONDecodeError, AttributeError):
            pass
        return ""

    @staticmethod
    def _extract_server_names(config_content: str) -> set[str]:
        """Extract normalized MCP server keys from a config blob."""
        try:
            data = json.loads(config_content)
        except json.JSONDecodeError:
            return set()

        servers = data.get("mcpServers") if isinstance(data, dict) else None
        if not isinstance(servers, dict):
            return set()

        return {str(name).strip() for name in servers if str(name).strip()}

    @staticmethod
    def _extract_single_server_config(
        config_content: str,
        *,
        server_name: str,
    ) -> dict[str, object]:
        """Extract exactly one server config and normalize it to the requested server name."""
        data = json.loads(config_content)
        servers = data.get("mcpServers") if isinstance(data, dict) else None
        if not isinstance(servers, dict) or len(servers) != 1:
            raise ValueError("Configuration must contain exactly one MCP server entry")

        server_config = next(iter(servers.values()))
        if not isinstance(server_config, dict):
            raise ValueError("MCP server config must be an object")

        return {server_name: dict(server_config)}

    @staticmethod
    def _parse_repo_mcp_content(raw: str, *, path: str) -> dict[str, object]:
        """Parse a repository MCP config file and surface invalid JSON clearly."""
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"Invalid JSON in repository MCP config file at {path}: {exc}"
            ) from exc

        if not isinstance(parsed, dict):
            raise ValueError(f"Repository MCP config file at {path} must contain a JSON object")

        return parsed

    async def _find_server_name_conflicts(
        self,
        *,
        project_id: str,
        github_user_id: str,
        config_content: str,
        exclude_tool_id: str | None = None,
    ) -> dict[str, list[str]]:
        """Return conflicting MCP server keys already claimed by other tools."""
        server_names = self._extract_server_names(config_content)
        if not server_names:
            return {}

        sql = (
            "SELECT id, name, config_content FROM mcp_configurations "
            "WHERE project_id = ? AND github_user_id = ?"
        )
        params: list[str] = [project_id, github_user_id]
        if exclude_tool_id:
            sql += " AND id != ?"
            params.append(exclude_tool_id)

        cursor = await self.db.execute(sql, tuple(params))
        rows = await cursor.fetchall()

        conflicts: dict[str, list[str]] = {}
        for row in rows:
            overlapping = server_names & self._extract_server_names(row["config_content"])
            for server_name in overlapping:
                conflicts.setdefault(server_name, []).append(row["name"])

        return conflicts

    async def _ensure_no_server_name_conflicts(
        self,
        *,
        project_id: str,
        github_user_id: str,
        config_content: str,
        exclude_tool_id: str | None = None,
    ) -> None:
        """Reject configs whose MCP server keys overlap with other saved tools."""
        conflicts = await self._find_server_name_conflicts(
            project_id=project_id,
            github_user_id=github_user_id,
            config_content=config_content,
            exclude_tool_id=exclude_tool_id,
        )
        if not conflicts:
            return

        details = ", ".join(
            f"'{server_name}' already used by {', '.join(sorted(tool_names))}"
            for server_name, tool_names in sorted(conflicts.items())
        )
        raise DuplicateToolServerNameError(
            "MCP server names must be unique per project because repository sync stores them under "
            f"`mcpServers` keys. Conflicts: {details}."
        )

    async def _get_protected_server_names(
        self,
        *,
        project_id: str,
        github_user_id: str,
        exclude_tool_id: str,
    ) -> set[str]:
        """Server keys still referenced by other tools and therefore not safe to remove."""
        cursor = await self.db.execute(
            "SELECT config_content FROM mcp_configurations WHERE project_id = ? AND github_user_id = ? AND id != ?",
            (project_id, github_user_id, exclude_tool_id),
        )
        rows = await cursor.fetchall()
        protected_names: set[str] = set()
        for row in rows:
            protected_names.update(self._extract_server_names(row["config_content"]))
        return protected_names

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

        await self._ensure_no_server_name_conflicts(
            project_id=project_id,
            github_user_id=github_user_id,
            config_content=data.config_content,
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

    async def update_tool(
        self,
        project_id: str,
        tool_id: str,
        github_user_id: str,
        data: McpToolConfigUpdate,
        owner: str,
        repo: str,
        access_token: str,
    ) -> McpToolConfigResponse:
        """Update an MCP tool configuration and re-sync it to GitHub."""
        existing_tool = await self.get_tool(project_id, tool_id, github_user_id)
        if not existing_tool:
            raise LookupError("Tool not found")

        next_name = (data.name or existing_tool.name).strip()
        next_description = (
            data.description if data.description is not None else existing_tool.description
        )
        next_config_content = data.config_content or existing_tool.config_content
        next_repo_target = (data.github_repo_target or existing_tool.github_repo_target).strip()

        if not next_name:
            raise ValueError("Name is required")

        is_valid, error_msg = self.validate_mcp_config(next_config_content)
        if not is_valid:
            raise ValueError(error_msg)

        cursor = await self.db.execute(
            "SELECT id FROM mcp_configurations WHERE project_id = ? AND github_user_id = ? AND name = ? AND id != ?",
            (project_id, github_user_id, next_name, tool_id),
        )
        duplicate = await cursor.fetchone()
        if duplicate:
            raise DuplicateToolNameError(
                f"An MCP tool named '{next_name}' already exists in this project"
            )

        await self._ensure_no_server_name_conflicts(
            project_id=project_id,
            github_user_id=github_user_id,
            config_content=next_config_content,
            exclude_tool_id=tool_id,
        )

        protected_server_names = await self._get_protected_server_names(
            project_id=project_id,
            github_user_id=github_user_id,
            exclude_tool_id=tool_id,
        )

        old_sync_owner, old_sync_repo = owner, repo
        if existing_tool.github_repo_target and "/" in existing_tool.github_repo_target:
            target_owner, target_repo = existing_tool.github_repo_target.split("/", 1)
            if target_owner.strip() and target_repo.strip():
                old_sync_owner, old_sync_repo = target_owner.strip(), target_repo.strip()

        try:
            await self._remove_from_github(
                existing_tool,
                old_sync_owner,
                old_sync_repo,
                access_token,
                protected_server_names=protected_server_names,
            )
        except Exception as e:
            logger.exception("Failed to remove old GitHub config for tool %s: %s", tool_id, e)

        now = utcnow().isoformat()
        endpoint_url = self._extract_endpoint_url(next_config_content)
        effective_repo_target = next_repo_target or f"{owner}/{repo}"

        await self.db.execute(
            "UPDATE mcp_configurations SET name = ?, description = ?, endpoint_url = ?, config_content = ?, github_repo_target = ?, sync_status = 'pending', sync_error = '', synced_at = NULL, updated_at = ? WHERE id = ? AND github_user_id = ?",
            (
                next_name,
                next_description,
                endpoint_url,
                next_config_content,
                effective_repo_target,
                now,
                tool_id,
                github_user_id,
            ),
        )
        await self.db.commit()

        sync_owner, sync_repo = owner, repo
        if effective_repo_target and "/" in effective_repo_target:
            target_owner, target_repo = effective_repo_target.split("/", 1)
            if target_owner.strip() and target_repo.strip():
                sync_owner, sync_repo = target_owner.strip(), target_repo.strip()

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
            name=next_name,
            description=next_description,
            endpoint_url=endpoint_url,
            config_content=next_config_content,
            sync_status=sync_result.sync_status,
            sync_error=sync_result.sync_error,
            synced_at=sync_result.synced_at,
            github_repo_target=effective_repo_target,
            is_active=existing_tool.is_active,
            created_at=existing_tool.created_at,
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
            protected_server_names = await self._get_protected_server_names(
                project_id=project_id,
                github_user_id=github_user_id,
                exclude_tool_id=tool_id,
            )
            await self._remove_from_github(
                tool,
                owner,
                repo,
                access_token,
                protected_server_names=protected_server_names,
            )
        except Exception as e:
            logger.exception("Failed to remove tool %s from GitHub: %s", tool_id, e)

        # Delete associations
        await self.db.execute("DELETE FROM agent_tool_associations WHERE tool_id = ?", (tool_id,))
        # Delete tool
        await self.db.execute(
            "DELETE FROM mcp_configurations WHERE id = ? AND github_user_id = ?",
            (tool_id, github_user_id),
        )
        await self.db.commit()

        logger.info("Deleted MCP tool %s", tool_id)

        # Trigger agent MCP sync to remove deleted tool from agent files (FR-007)
        try:
            from src.services.agents.agent_mcp_sync import sync_agent_mcps

            await sync_agent_mcps(
                owner=owner,
                repo=repo,
                project_id=project_id,
                access_token=access_token,
                trigger="tool_delete",
                db=self.db,
            )
        except Exception as sync_exc:
            logger.warning("Agent MCP sync after tool deletion failed (non-fatal): %s", sync_exc)

        return ToolDeleteResult(success=True, deleted_id=tool_id, affected_agents=[])

    # ── GitHub Sync ──

    async def get_repo_mcp_config(
        self,
        *,
        owner: str,
        repo: str,
        access_token: str,
    ) -> RepoMcpConfigResponse:
        """Read repository MCP configuration from all supported GitHub paths."""
        svc = self._get_github_service()
        merged_servers: dict[str, dict[str, object]] = {}
        source_paths: dict[str, list[str]] = {}
        available_paths: list[str] = []

        for path in MCP_CONFIG_PATHS:
            resp = await svc.rest_request(
                access_token,
                "GET",
                f"/repos/{owner}/{repo}/contents/{path}",
            )
            if resp.status_code == 404:
                continue
            if resp.status_code != 200:
                raise RuntimeError(f"GitHub API error: {resp.status_code} {resp.text[:200]}")

            available_paths.append(path)
            file_data = resp.json()
            raw = base64.b64decode(file_data.get("content", "")).decode("utf-8")
            parsed = json.loads(raw)
            servers = parsed.get("mcpServers") if isinstance(parsed, dict) else None
            if not isinstance(servers, dict):
                continue
            for server_name, server_config in servers.items():
                server_key = str(server_name)
                if isinstance(server_config, dict):
                    merged_servers[server_key] = dict(server_config)
                    source_paths.setdefault(server_key, []).append(path)

        ordered_servers = [
            RepoMcpServerConfig(
                name=name,
                config=merged_servers[name],
                source_paths=source_paths.get(name, []),
            )
            for name in sorted(merged_servers)
        ]
        primary_path = available_paths[0] if available_paths else None
        return RepoMcpConfigResponse(
            paths_checked=list(MCP_CONFIG_PATHS),
            available_paths=available_paths,
            primary_path=primary_path,
            servers=ordered_servers,
        )

    async def update_repo_mcp_server(
        self,
        *,
        owner: str,
        repo: str,
        access_token: str,
        server_name: str,
        data: RepoMcpServerUpdate,
    ) -> RepoMcpServerConfig:
        """Update a repository MCP server directly in supported repo config files."""
        is_valid, error_msg = self.validate_mcp_config(data.config_content)
        if not is_valid:
            raise ValueError(error_msg)

        next_name = data.name.strip()
        if not next_name:
            raise ValueError("Name is required")

        next_servers = self._extract_single_server_config(
            data.config_content, server_name=next_name
        )
        next_config: dict[str, object] = dict(next(iter(next_servers.values())))  # type: ignore[arg-type]

        svc = self._get_github_service()

        updated_paths: list[str] = []
        pending_updates: list[tuple[str, str | None, dict[str, object]]] = []

        for path in MCP_CONFIG_PATHS:
            api_path = f"/repos/{owner}/{repo}/contents/{path}"
            resp = await svc.rest_request(access_token, "GET", api_path)
            if resp.status_code == 404:
                continue
            if resp.status_code != 200:
                raise RuntimeError(
                    f"GitHub API error for {path}: {resp.status_code} {resp.text[:200]}"
                )

            file_data = resp.json()
            existing_sha = file_data.get("sha")
            raw = base64.b64decode(file_data.get("content", "")).decode("utf-8")
            existing_content = self._parse_repo_mcp_content(raw, path=path)
            mcp_servers = existing_content.get("mcpServers", {})
            if not isinstance(mcp_servers, dict):
                mcp_servers = {}

            if server_name not in mcp_servers:
                continue
            if next_name != server_name and next_name in mcp_servers:
                raise ValueError(f"An MCP server named '{next_name}' already exists in {path}")

            mcp_servers.pop(server_name, None)
            mcp_servers.update(next_servers)
            existing_content["mcpServers"] = mcp_servers

            pending_updates.append(
                (
                    api_path,
                    existing_sha if isinstance(existing_sha, str) else None,
                    existing_content,
                )
            )

        if not pending_updates:
            raise LookupError(f"Repository MCP server '{server_name}' not found")

        for api_path, existing_sha, existing_content in pending_updates:
            new_content = json.dumps(existing_content, indent=2) + "\n"
            encoded = base64.b64encode(new_content.encode("utf-8")).decode("utf-8")
            put_body: dict[str, object] = {
                "message": f"chore: update MCP server '{server_name}'",
                "content": encoded,
            }
            if existing_sha:
                put_body["sha"] = existing_sha

            put_resp = await svc.rest_request(
                access_token,
                "PUT",
                api_path,
                json=put_body,
            )
            if put_resp.status_code not in (200, 201):
                raise RuntimeError(
                    f"GitHub API write error for {api_path.rsplit('/contents/', 1)[-1]}: {put_resp.status_code} {put_resp.text[:200]}"
                )
            updated_paths.append(api_path.rsplit("/contents/", 1)[-1])

        return RepoMcpServerConfig(
            name=next_name,
            config=next_config,
            source_paths=updated_paths,
        )

    async def delete_repo_mcp_server(
        self,
        *,
        owner: str,
        repo: str,
        access_token: str,
        server_name: str,
    ) -> RepoMcpServerConfig:
        """Delete a repository MCP server directly from supported repo config files."""
        svc = self._get_github_service()

        removed_config: dict[str, object] | None = None
        removed_paths: list[str] = []
        for path in MCP_CONFIG_PATHS:
            api_path = f"/repos/{owner}/{repo}/contents/{path}"
            resp = await svc.rest_request(access_token, "GET", api_path)
            if resp.status_code == 404:
                continue
            if resp.status_code != 200:
                raise RuntimeError(
                    f"GitHub API error for {path}: {resp.status_code} {resp.text[:200]}"
                )

            file_data = resp.json()
            existing_sha = file_data.get("sha")
            raw = base64.b64decode(file_data.get("content", "")).decode("utf-8")
            existing_content = self._parse_repo_mcp_content(raw, path=path)
            mcp_servers = existing_content.get("mcpServers", {})
            if not isinstance(mcp_servers, dict) or server_name not in mcp_servers:
                continue

            removed_config = (
                dict(mcp_servers[server_name]) if isinstance(mcp_servers[server_name], dict) else {}
            )
            mcp_servers.pop(server_name, None)
            existing_content["mcpServers"] = mcp_servers

            new_content = json.dumps(existing_content, indent=2) + "\n"
            encoded = base64.b64encode(new_content.encode("utf-8")).decode("utf-8")
            put_body: dict[str, object] = {
                "message": f"chore: remove MCP server '{server_name}'",
                "content": encoded,
            }
            if existing_sha:
                put_body["sha"] = existing_sha

            put_resp = await svc.rest_request(
                access_token,
                "PUT",
                api_path,
                json=put_body,
            )
            if put_resp.status_code not in (200, 201):
                raise RuntimeError(
                    f"GitHub API write error for {path}: {put_resp.status_code} {put_resp.text[:200]}"
                )
            removed_paths.append(path)

        if removed_config is None:
            raise LookupError(f"Repository MCP server '{server_name}' not found")

        return RepoMcpServerConfig(
            name=server_name,
            config=removed_config,
            source_paths=removed_paths,
        )

    async def sync_tool_to_github(
        self,
        tool_id: str,
        project_id: str,
        github_user_id: str,
        owner: str,
        repo: str,
        access_token: str,
    ) -> McpToolConfigSyncResult:
        """Sync an MCP tool configuration to all supported GitHub MCP config files."""
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
            conflicts = await self._find_server_name_conflicts(
                project_id=project_id,
                github_user_id=github_user_id,
                config_content=tool.config_content,
                exclude_tool_id=tool_id,
            )
            if conflicts:
                details = ", ".join(
                    f"'{server_name}' also exists in {', '.join(sorted(tool_names))}"
                    for server_name, tool_names in sorted(conflicts.items())
                )
                raise RuntimeError(
                    f"MCP server-name collision detected during sync. Conflicts: {details}"
                )

            svc = self._get_github_service()

            synced_paths: list[str] = []
            tool_config = json.loads(tool.config_content)
            for path in MCP_CONFIG_PATHS:
                existing_sha = None
                existing_content: dict[str, object] = {"mcpServers": {}}
                api_path = f"/repos/{owner}/{repo}/contents/{path}"
                resp = await svc.rest_request(access_token, "GET", api_path)

                if resp.status_code == 200:
                    file_data = resp.json()
                    existing_sha = file_data.get("sha")
                    raw = base64.b64decode(file_data.get("content", "")).decode("utf-8")
                    existing_content = json.loads(raw)
                elif resp.status_code != 404:
                    raise RuntimeError(
                        f"GitHub API error for {path}: {resp.status_code} {resp.text[:200]}"
                    )

                mcp_servers = existing_content.get("mcpServers", {})
                if not isinstance(mcp_servers, dict):
                    mcp_servers = {}
                mcp_servers.update(tool_config.get("mcpServers", {}))
                existing_content["mcpServers"] = mcp_servers

                new_content = json.dumps(existing_content, indent=2) + "\n"
                encoded = base64.b64encode(new_content.encode("utf-8")).decode("utf-8")

                put_body: dict[str, object] = {
                    "message": f"chore: sync MCP tool '{tool.name}' configuration",
                    "content": encoded,
                }
                if existing_sha:
                    put_body["sha"] = existing_sha

                put_resp = await svc.rest_request(
                    access_token,
                    "PUT",
                    api_path,
                    json=put_body,
                )
                if put_resp.status_code not in (200, 201):
                    raise RuntimeError(
                        f"GitHub API write error for {path}: {put_resp.status_code} {put_resp.text[:200]}"
                    )
                synced_paths.append(path)

            # Update status
            now = utcnow().isoformat()
            await self.db.execute(
                "UPDATE mcp_configurations SET sync_status = 'synced', sync_error = '', synced_at = ?, updated_at = ? WHERE id = ?",
                (now, now, tool_id),
            )
            await self.db.commit()

            logger.info("Synced MCP tool %s to GitHub %s/%s", tool_id, owner, repo)

            # Trigger agent MCP sync to propagate changes to agent files (FR-007)
            try:
                from src.services.agents.agent_mcp_sync import sync_agent_mcps

                await sync_agent_mcps(
                    owner=owner,
                    repo=repo,
                    project_id=project_id,
                    access_token=access_token,
                    trigger="tool_toggle",
                    db=self.db,
                )
            except Exception as sync_exc:
                logger.warning("Agent MCP sync after tool sync failed (non-fatal): %s", sync_exc)

            return McpToolConfigSyncResult(
                id=tool_id,
                sync_status="synced",
                sync_error="",
                synced_at=now,
                synced_paths=synced_paths,
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
                id=tool_id,
                sync_status="error",
                sync_error=error_msg,
                synced_at=None,
                synced_paths=[],
            )

    async def _remove_from_github(
        self,
        tool: McpToolConfigResponse,
        owner: str,
        repo: str,
        access_token: str,
        *,
        protected_server_names: set[str] | None = None,
    ) -> None:
        """Remove an MCP server entry from all supported GitHub MCP config files."""
        svc = self._get_github_service()

        for path in MCP_CONFIG_PATHS:
            api_path = f"/repos/{owner}/{repo}/contents/{path}"
            resp = await svc.rest_request(access_token, "GET", api_path)
            if resp.status_code != 200:
                continue

            file_data = resp.json()
            existing_sha = file_data.get("sha")
            raw = base64.b64decode(file_data.get("content", "")).decode("utf-8")
            existing_content = json.loads(raw)

            try:
                tool_config = json.loads(tool.config_content)
                tool_server_names = list(tool_config.get("mcpServers", {}).keys())
            except (json.JSONDecodeError, AttributeError):
                tool_server_names = []

            protected_names = protected_server_names or set()
            removable_names = [name for name in tool_server_names if name not in protected_names]
            if not removable_names:
                continue

            mcp_servers = existing_content.get("mcpServers", {})
            if not isinstance(mcp_servers, dict):
                mcp_servers = {}
            for name in removable_names:
                mcp_servers.pop(name, None)
            existing_content["mcpServers"] = mcp_servers

            new_content = json.dumps(existing_content, indent=2) + "\n"
            encoded = base64.b64encode(new_content.encode("utf-8")).decode("utf-8")

            put_body: dict[str, object] = {
                "message": f"chore: remove MCP tool '{tool.name}' configuration",
                "content": encoded,
            }
            if existing_sha:
                put_body["sha"] = existing_sha

            await svc.rest_request(
                access_token,
                "PUT",
                api_path,
                json=put_body,
            )

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


class DuplicateToolServerNameError(Exception):
    """Raised when a tool config reuses an existing mcpServers key in the project."""
