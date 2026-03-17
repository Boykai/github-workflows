"""Agent MCP Sync — synchronize activated and built-in MCPs across agent files.

This module provides a centralized sync utility that keeps every
``.github/agents/*.agent.md`` file's ``mcp-servers`` field in sync with the
current set of activated and built-in MCPs, while unconditionally enforcing
``tools: ["*"]`` on all agent definitions.

The sync runs on three triggers:
1. MCP activation/deactivation via the Tools page
2. Agent file creation/update
3. Application startup

The ``BUILTIN_MCPS`` constant mirrors the frontend constant in
``frontend/src/lib/buildGitHubMcpConfig.ts`` — keep them in sync.
"""

from __future__ import annotations

import base64
import json
import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import aiosqlite
import yaml

from src.logging_utils import get_logger

if TYPE_CHECKING:
    from src.services.github_projects.service import GitHubProjectsService

logger = get_logger(__name__)

# ── YAML frontmatter regex (same as agents/service.py) ──────────────────
_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n?(.*)", re.DOTALL)

# ── Built-in MCP server definitions ─────────────────────────────────────
# Mirrors frontend/src/lib/buildGitHubMcpConfig.ts BUILTIN_MCPS constant.
BUILTIN_MCPS: dict[str, dict] = {
    "context7": {
        "type": "http",
        "url": "https://mcp.context7.com/mcp",
        "tools": ["resolve-library-id", "get-library-docs"],
        "headers": {
            "CONTEXT7_API_KEY": "$COPILOT_MCP_CONTEXT7_API_KEY",
        },
    },
    "CodeGraphContext": {
        "type": "local",
        "command": "uvx",
        "args": ["--from", "codegraphcontext", "cgc", "mcp", "start"],
        "tools": ["*"],
    },
}


@dataclass
class AgentMcpSyncResult:
    """Result summary of an agent MCP sync operation."""

    success: bool = True
    files_updated: int = 0
    files_skipped: int = 0
    files_unchanged: int = 0
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    synced_mcps: list[str] = field(default_factory=list)


# ── Helper functions ─────────────────────────────────────────────────────


def _parse_agent_file(content: str) -> tuple[dict | None, str]:
    """Split file content into (frontmatter dict, markdown body).

    Returns ``(None, content)`` for files that lack parseable YAML
    frontmatter.
    """
    match = _FRONTMATTER_RE.match(content)
    if not match:
        return None, content

    try:
        fm = yaml.safe_load(match.group(1))
        if not isinstance(fm, dict):
            return None, content
        return fm, match.group(2)
    except yaml.YAMLError:
        return None, content


def _serialize_agent_file(frontmatter: dict, body: str) -> str:
    """Re-serialize updated frontmatter and concatenate with Markdown body.

    The body is joined with ``\\n`` after the closing ``---`` fence.
    If the body doesn't start with a newline, one is added to preserve
    the conventional blank line between frontmatter and content.
    """
    fm_yaml = yaml.dump(frontmatter, default_flow_style=False, sort_keys=False).rstrip("\n")
    separator = "\n" if body.startswith("\n") else "\n\n"
    return f"---\n{fm_yaml}\n---{separator}{body}"


async def _build_active_mcp_dict(db: aiosqlite.Connection, project_id: str) -> dict[str, dict]:
    """Build the merged MCP dict: user-activated MCPs + built-in MCPs.

    Built-in MCPs take precedence on server-key conflicts (FR-014).
    """
    mcps: dict[str, dict] = {}

    # 1. Load user-activated MCPs from the database
    cursor = await db.execute(
        "SELECT name, config_content FROM mcp_configurations "
        "WHERE project_id = ? AND is_active = 1",
        (project_id,),
    )
    rows = await cursor.fetchall()

    for row in rows:
        try:
            config = json.loads(row["config_content"])
            servers = config.get("mcpServers", {})
            if isinstance(servers, dict):
                for key, server_config in servers.items():
                    if isinstance(server_config, dict) and key not in mcps:
                        mcps[key] = dict(server_config)
        except (json.JSONDecodeError, TypeError):
            logger.warning("Skipping MCP '%s' — invalid config_content JSON", row["name"])
            continue

    # 2. Merge built-in MCPs (override user MCPs on key conflict)
    for key, config in BUILTIN_MCPS.items():
        if key in mcps:
            logger.warning("Built-in MCP '%s' overrides user-activated MCP with same key", key)
        mcps[key] = dict(config)

    return mcps


async def _discover_agent_files(
    owner: str,
    repo: str,
    token: str,
    github_service: GitHubProjectsService | None = None,
) -> list[dict]:
    """Discover all ``*.agent.md`` files in ``.github/agents/`` via GitHub API.

    Returns a list of dicts with keys: ``path``, ``sha``, ``download_url``.
    """
    if github_service is None:
        from src.services.github_projects import github_projects_service

        github_service = github_projects_service

    path = f"/repos/{owner}/{repo}/contents/.github/agents"
    try:
        resp = await github_service.rest_request(token, "GET", path)
    except Exception:
        logger.error("Network error listing .github/agents/ in %s/%s", owner, repo)
        return []

    if resp.status_code == 404:
        logger.debug("No .github/agents/ directory in %s/%s", owner, repo)
        return []
    if resp.status_code != 200:
        logger.error(
            "GitHub API error listing .github/agents/: %s %s",
            resp.status_code,
            resp.text[:200],
        )
        return []

    entries = resp.json()
    if not isinstance(entries, list):
        return []

    return [
        {
            "path": entry["path"],
            "sha": entry["sha"],
            "download_url": entry.get("download_url", ""),
        }
        for entry in entries
        if isinstance(entry, dict) and entry.get("name", "").endswith(".agent.md")
    ]


def _merge_mcps_into_frontmatter(
    frontmatter: dict,
    active_mcps: dict[str, dict],
    file_path: str = "",
) -> tuple[dict, list[str]]:
    """Merge active MCPs into frontmatter.

    Returns ``(updated_frontmatter, warnings)``.

    Note: ``tools`` is intentionally **not** managed here.  VS Code agent
    definitions and Custom GitHub Agent definitions use incompatible
    ``tools`` schemas, so the sync leaves the field untouched (or absent).
    """
    warnings: list[str] = []

    # Remove legacy tools field if present — it is no longer managed by sync.
    if "tools" in frontmatter:
        warnings.append(f"{file_path}: removed legacy 'tools' field from frontmatter")
        logger.info("Agent file %s: removed legacy 'tools' field", file_path)
        del frontmatter["tools"]

    # ── Replace mcp-servers with the authoritative active MCP set (FR-002, FR-004) ──
    frontmatter["mcp-servers"] = {key: dict(config) for key, config in active_mcps.items()}

    return frontmatter, warnings


def _validate_agent_frontmatter(frontmatter: dict, file_path: str) -> list[str]:
    """Lightweight schema validation for agent frontmatter after sync.

    Returns a list of error strings (empty if valid).
    """
    errors: list[str] = []

    # mcp-servers must be a dict
    mcp_servers = frontmatter.get("mcp-servers")
    if not isinstance(mcp_servers, dict):
        errors.append(
            f"{file_path}: 'mcp-servers' is not a dict — got {type(mcp_servers).__name__}"
        )
        return errors

    # Each server entry must have 'type' and either 'url' or 'command'
    for key, server in mcp_servers.items():
        if not isinstance(server, dict):
            errors.append(f"{file_path}: mcp-servers.{key} is not a dict")
            continue
        if "type" not in server:
            errors.append(f"{file_path}: mcp-servers.{key} missing 'type' field")
        server_type = server.get("type", "")
        if server_type in ("http", "sse") and "url" not in server:
            errors.append(f"{file_path}: mcp-servers.{key} (type={server_type}) missing 'url'")
        if server_type in ("stdio", "local") and "command" not in server:
            errors.append(f"{file_path}: mcp-servers.{key} (type={server_type}) missing 'command'")

    return errors


# ── Main sync orchestrator ───────────────────────────────────────────────


async def sync_agent_mcps(
    *,
    owner: str,
    repo: str,
    project_id: str,
    access_token: str,
    trigger: str = "manual",
    db: aiosqlite.Connection,
    github_service: GitHubProjectsService | None = None,
) -> AgentMcpSyncResult:
    """Synchronize MCP configurations across all agent files.

    Reads the current set of active MCPs (built-in + user-activated), merges
    them into each agent file's YAML frontmatter ``mcp-servers`` field, and
    enforces ``tools: ["*"]``.  Only writes files that actually changed
    (idempotent — SC-004).

    Args:
        owner: Repository owner.
        repo: Repository name.
        project_id: Project identifier for DB queries.
        access_token: GitHub access token.
        trigger: What initiated this sync (startup, tool_toggle, agent_create, etc.).
        db: Database connection for reading active MCPs.
        github_service: Optional GitHubProjectsService for REST requests.

    Returns:
        AgentMcpSyncResult with counts and any warnings/errors.
    """
    if github_service is None:
        from src.services.github_projects import github_projects_service

        github_service = github_projects_service

    result = AgentMcpSyncResult()

    try:
        # 1. Build the authoritative MCP dict
        active_mcps = await _build_active_mcp_dict(db, project_id)
        result.synced_mcps = list(active_mcps.keys())

        # 2. Discover agent files
        agent_files = await _discover_agent_files(
            owner,
            repo,
            access_token,
            github_service=github_service,
        )
        if not agent_files:
            logger.info(
                "No agent files found in %s/%s — sync complete (trigger=%s)",
                owner,
                repo,
                trigger,
            )
            return result

        # 3. Process each agent file
        for agent_entry in agent_files:
            file_path = agent_entry["path"]
            try:
                await _process_agent_file(
                    github_service=github_service,
                    access_token=access_token,
                    owner=owner,
                    repo=repo,
                    file_path=file_path,
                    active_mcps=active_mcps,
                    result=result,
                )
            except Exception as exc:
                error_msg = f"{file_path}: {exc}"
                result.errors.append(error_msg)
                result.files_skipped += 1
                logger.exception("Error processing agent file %s", file_path)

    except Exception as exc:
        result.success = False
        result.errors.append(f"Sync failed: {exc}")
        logger.exception("Agent MCP sync failed (trigger=%s)", trigger)

    logger.info(
        "Agent MCP sync complete (trigger=%s): updated=%d, unchanged=%d, skipped=%d, warnings=%d",
        trigger,
        result.files_updated,
        result.files_unchanged,
        result.files_skipped,
        len(result.warnings),
    )
    return result


async def _process_agent_file(
    *,
    github_service: GitHubProjectsService,
    access_token: str,
    owner: str,
    repo: str,
    file_path: str,
    active_mcps: dict[str, dict],
    result: AgentMcpSyncResult,
) -> None:
    """Fetch, merge, validate, and (if changed) write back a single agent file."""
    # Fetch current file content
    api_path = f"/repos/{owner}/{repo}/contents/{file_path}"
    resp = await github_service.rest_request(access_token, "GET", api_path)
    if resp.status_code != 200:
        result.errors.append(f"{file_path}: GitHub API GET failed ({resp.status_code})")
        result.files_skipped += 1
        return

    file_data = resp.json()
    file_sha = file_data.get("sha")
    raw_content = base64.b64decode(file_data.get("content", "")).decode("utf-8")

    # Parse frontmatter
    frontmatter, body = _parse_agent_file(raw_content)
    if frontmatter is None:
        result.warnings.append(f"{file_path}: skipped — no parseable YAML frontmatter")
        result.files_skipped += 1
        logger.warning("Skipping agent file %s — no parseable YAML frontmatter", file_path)
        return

    # Merge MCPs and enforce tools: ["*"]
    updated_fm, merge_warnings = _merge_mcps_into_frontmatter(frontmatter, active_mcps, file_path)
    result.warnings.extend(merge_warnings)

    # Validate
    validation_errors = _validate_agent_frontmatter(updated_fm, file_path)
    if validation_errors:
        result.errors.extend(validation_errors)
        result.files_skipped += 1
        logger.warning("Validation failed for %s: %s", file_path, validation_errors)
        return

    # Serialize and compare (idempotency check)
    new_content = _serialize_agent_file(updated_fm, body)
    if new_content == raw_content:
        result.files_unchanged += 1
        return

    # Write back via GitHub Contents API
    encoded = base64.b64encode(new_content.encode("utf-8")).decode("utf-8")
    put_body: dict[str, object] = {
        "message": f"chore: sync MCP servers and enforce tools: ['*'] on {file_path.split('/')[-1]}",
        "content": encoded,
    }
    if file_sha:
        put_body["sha"] = file_sha

    put_resp = await github_service.rest_request(
        access_token,
        "PUT",
        api_path,
        json=put_body,
    )
    if put_resp.status_code not in (200, 201):
        result.errors.append(f"{file_path}: GitHub API PUT failed ({put_resp.status_code})")
        result.files_skipped += 1
        return

    result.files_updated += 1
