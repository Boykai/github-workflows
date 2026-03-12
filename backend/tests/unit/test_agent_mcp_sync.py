"""Unit tests for agent_mcp_sync module."""

from __future__ import annotations

import base64
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.services.agents.agent_mcp_sync import (
    BUILTIN_MCPS,
    AgentMcpSyncResult,
    _build_active_mcp_dict,
    _discover_agent_files,
    _merge_mcps_into_frontmatter,
    _parse_agent_file,
    _process_agent_file,
    _serialize_agent_file,
    _validate_agent_frontmatter,
    sync_agent_mcps,
)

# ── Fixtures ─────────────────────────────────────────────────────────────

SAMPLE_AGENT_CONTENT = """\
---
name: Reviewer
description: Reviews pull requests
tools:
  - search
  - edit
---

You are a code reviewer.
"""

SAMPLE_AGENT_CONTENT_STAR = """\
---
name: Reviewer
description: Reviews pull requests
tools:
  - '*'
---

You are a code reviewer.
"""

SAMPLE_AGENT_NO_TOOLS = """\
---
name: Reviewer
description: Reviews pull requests
---

You are a code reviewer.
"""

SAMPLE_AGENT_NO_FRONTMATTER = """\
You are a code reviewer without frontmatter.
"""


# ── T009: _merge_mcps_into_frontmatter sets tools: ["*"] when missing ───


class TestMergeToolsEnforcement:
    def test_sets_tools_star_when_missing(self):
        """T009: tools field is added as ['*'] when absent."""
        fm = {"name": "Test", "description": "desc"}
        updated, warnings = _merge_mcps_into_frontmatter(fm, {}, "test.md")
        assert updated["tools"] == ["*"]
        assert len(warnings) == 0  # no override warning when field was absent

    def test_replaces_restrictive_tools_with_star(self):
        """T010: restrictive tools replaced, warning returned."""
        fm = {"name": "Test", "tools": ["search", "edit"]}
        updated, warnings = _merge_mcps_into_frontmatter(fm, {}, "agent.md")
        assert updated["tools"] == ["*"]
        assert len(warnings) == 1
        assert "['search', 'edit']" in warnings[0]
        assert "agent.md" in warnings[0]

    def test_leaves_tools_star_unchanged(self):
        """T011: already ['*'] → no change, no warning (idempotent)."""
        fm = {"name": "Test", "tools": ["*"]}
        updated, warnings = _merge_mcps_into_frontmatter(fm, {}, "agent.md")
        assert updated["tools"] == ["*"]
        assert len(warnings) == 0


# ── T014-T017: MCP merge logic ──────────────────────────────────────────


class TestMergeMcpServers:
    def test_adds_active_mcps_to_empty_field(self):
        """T014: 3 active MCPs added to empty mcp-servers."""
        active = {
            "server1": {"type": "http", "url": "https://s1.com"},
            "server2": {"type": "http", "url": "https://s2.com"},
            "server3": {"type": "stdio", "command": "npx", "args": ["s3"]},
        }
        fm = {"name": "Test", "tools": ["*"]}
        updated, _ = _merge_mcps_into_frontmatter(fm, active, "agent.md")
        assert len(updated["mcp-servers"]) == 3
        assert "server1" in updated["mcp-servers"]
        assert "server2" in updated["mcp-servers"]
        assert "server3" in updated["mcp-servers"]

    def test_no_duplicates_when_already_present(self):
        """T015: no duplicate entries on repeated merge."""
        active = {"context7": {"type": "http", "url": "https://mcp.context7.com/mcp"}}
        fm = {
            "name": "Test",
            "tools": ["*"],
            "mcp-servers": {"context7": {"type": "http", "url": "https://mcp.context7.com/mcp"}},
        }
        updated, _ = _merge_mcps_into_frontmatter(fm, active, "agent.md")
        # Keys should appear exactly once
        assert list(updated["mcp-servers"].keys()).count("context7") == 1

    def test_removes_deactivated_mcp(self):
        """T016: deactivated MCP removed, remaining MCPs kept."""
        active = {
            "server1": {"type": "http", "url": "https://s1.com"},
        }
        fm = {
            "name": "Test",
            "tools": ["*"],
            "mcp-servers": {
                "server1": {"type": "http", "url": "https://s1.com"},
                "removed_server": {"type": "http", "url": "https://old.com"},
            },
        }
        updated, _ = _merge_mcps_into_frontmatter(fm, active, "agent.md")
        assert "server1" in updated["mcp-servers"]
        assert "removed_server" not in updated["mcp-servers"]

    def test_no_active_mcps_yields_empty_mcp_servers(self):
        """T017: merge with empty active MCPs produces empty mcp-servers dict."""
        # _merge_mcps_into_frontmatter sets mcp-servers to exactly what is passed;
        # built-in MCPs are injected upstream by _build_active_mcp_dict, not here.
        fm = {"name": "Test", "tools": ["*"]}
        updated, _ = _merge_mcps_into_frontmatter(fm, {}, "agent.md")
        assert updated["mcp-servers"] == {}


# ── T024-T026: Built-in MCP tests ───────────────────────────────────────


class TestBuiltinMcps:
    def test_builtin_mcps_contains_context7_and_codegraph(self):
        """T024: BUILTIN_MCPS has context7 (http) and CodeGraphContext (local)."""
        assert "context7" in BUILTIN_MCPS
        assert BUILTIN_MCPS["context7"]["type"] == "http"
        assert "CodeGraphContext" in BUILTIN_MCPS
        assert BUILTIN_MCPS["CodeGraphContext"]["type"] == "local"

    def test_merge_always_includes_builtins(self):
        """T025: built-in MCPs always included even if removed from file."""
        active = dict(BUILTIN_MCPS)  # only built-ins
        fm = {"name": "Test", "tools": ["*"], "mcp-servers": {}}
        updated, _ = _merge_mcps_into_frontmatter(fm, active, "agent.md")
        assert "context7" in updated["mcp-servers"]
        assert "CodeGraphContext" in updated["mcp-servers"]

    @pytest.mark.asyncio
    async def test_build_active_mcp_dict_builtin_precedence(self):
        """T026: built-in MCPs override user MCPs with same key."""
        db = AsyncMock()
        cursor_mock = AsyncMock()
        cursor_mock.fetchall.return_value = [
            {
                "name": "UserContext7",
                "config_content": json.dumps(
                    {"mcpServers": {"context7": {"type": "http", "url": "https://user.com"}}}
                ),
            }
        ]
        db.execute.return_value = cursor_mock

        result = await _build_active_mcp_dict(db, "project-1")
        # Built-in should override user config
        assert result["context7"]["url"] == "https://mcp.context7.com/mcp"

    @pytest.mark.asyncio
    async def test_build_active_mcp_dict_invalid_json_skipped(self):
        """Invalid JSON in config_content is skipped gracefully."""
        db = AsyncMock()
        cursor_mock = AsyncMock()
        cursor_mock.fetchall.return_value = [
            {
                "name": "BadMCP",
                "config_content": "{invalid json}",
            },
            {
                "name": "GoodMCP",
                "config_content": json.dumps(
                    {"mcpServers": {"good_server": {"type": "http", "url": "https://good.com"}}}
                ),
            },
        ]
        db.execute.return_value = cursor_mock

        result = await _build_active_mcp_dict(db, "project-1")
        # Bad MCP skipped, good MCP + 2 built-ins present
        assert "good_server" in result
        assert "context7" in result
        assert "CodeGraphContext" in result
        assert len(result) == 3

    @pytest.mark.asyncio
    async def test_build_active_mcp_dict_multiple_user_mcps(self):
        """Multiple user-activated MCPs from separate tools are merged."""
        db = AsyncMock()
        cursor_mock = AsyncMock()
        cursor_mock.fetchall.return_value = [
            {
                "name": "UserMCP1",
                "config_content": json.dumps(
                    {"mcpServers": {
                        "server1": {"type": "http", "url": "https://s1.com"},
                        "server2": {"type": "http", "url": "https://s2.com"},
                    }}
                ),
            },
            {
                "name": "UserMCP2",
                "config_content": json.dumps(
                    {"mcpServers": {
                        "server3": {"type": "http", "url": "https://s3.com"},
                    }}
                ),
            },
        ]
        db.execute.return_value = cursor_mock

        result = await _build_active_mcp_dict(db, "project-1")
        # 3 user servers + 2 built-ins = 5
        assert len(result) == 5
        assert all(k in result for k in ("server1", "server2", "server3", "context7", "CodeGraphContext"))

    @pytest.mark.asyncio
    async def test_build_active_mcp_dict_duplicate_user_key_first_wins(self):
        """When two user tools define the same server key, the first one wins."""
        db = AsyncMock()
        cursor_mock = AsyncMock()
        cursor_mock.fetchall.return_value = [
            {
                "name": "UserMCP1",
                "config_content": json.dumps(
                    {"mcpServers": {"dup": {"type": "http", "url": "https://first.com"}}}
                ),
            },
            {
                "name": "UserMCP2",
                "config_content": json.dumps(
                    {"mcpServers": {"dup": {"type": "http", "url": "https://second.com"}}}
                ),
            },
        ]
        db.execute.return_value = cursor_mock

        result = await _build_active_mcp_dict(db, "project-1")
        assert result["dup"]["url"] == "https://first.com"


# ── T035-T037: Validation tests ─────────────────────────────────────────


class TestValidation:
    def test_valid_frontmatter_passes(self):
        """T035: valid frontmatter returns no errors."""
        fm = {
            "tools": ["*"],
            "mcp-servers": {
                "context7": {
                    "type": "http",
                    "url": "https://mcp.context7.com/mcp",
                }
            },
        }
        errors = _validate_agent_frontmatter(fm, "agent.md")
        assert errors == []

    def test_missing_type_field_fails(self):
        """T036: missing 'type' field produces error."""
        fm = {
            "tools": ["*"],
            "mcp-servers": {
                "bad_server": {"url": "https://example.com"},
            },
        }
        errors = _validate_agent_frontmatter(fm, "agent.md")
        assert any("missing 'type'" in e for e in errors)

    def test_unparseable_frontmatter_skipped(self):
        """T037: files without frontmatter return None from parse."""
        fm, body = _parse_agent_file("No frontmatter here\nJust text.")
        assert fm is None
        assert "No frontmatter here" in body


# ── Parse/Serialize tests ────────────────────────────────────────────────


class TestParseSerialize:
    def test_parse_valid_frontmatter(self):
        fm, body = _parse_agent_file(SAMPLE_AGENT_CONTENT)
        assert fm is not None
        assert fm["name"] == "Reviewer"
        assert "code reviewer" in body

    def test_parse_no_frontmatter(self):
        fm, body = _parse_agent_file(SAMPLE_AGENT_NO_FRONTMATTER)
        assert fm is None
        assert "code reviewer" in body

    def test_serialize_round_trip(self):
        fm, body = _parse_agent_file(SAMPLE_AGENT_CONTENT)
        assert fm is not None
        serialized = _serialize_agent_file(fm, body)
        assert serialized.startswith("---\n")
        assert "name: Reviewer" in serialized
        assert "code reviewer" in serialized


# ── T030-T031: Full sync_agent_mcps tests ────────────────────────────────


class TestSyncAgentMcps:
    @pytest.mark.asyncio
    async def test_sync_updates_files(self):
        """T030: sync correctly counts updated/unchanged/skipped files."""
        db = AsyncMock()
        cursor_mock = AsyncMock()
        cursor_mock.fetchall.return_value = []
        db.execute.return_value = cursor_mock

        agent_content = SAMPLE_AGENT_CONTENT
        encoded_content = base64.b64encode(agent_content.encode()).decode()

        # Mock discover: 1 agent file
        with patch(
            "src.services.agents.agent_mcp_sync._discover_agent_files",
            return_value=[
                {"path": ".github/agents/test.agent.md", "sha": "abc123", "download_url": ""}
            ],
        ):
            mock_get_response = MagicMock()
            mock_get_response.status_code = 200
            mock_get_response.json.return_value = {
                "sha": "abc123",
                "content": encoded_content,
            }

            mock_put_response = MagicMock()
            mock_put_response.status_code = 200

            mock_client = AsyncMock()
            mock_client.get.return_value = mock_get_response
            mock_client.put.return_value = mock_put_response

            with patch("httpx.AsyncClient") as mock_httpx:
                mock_httpx.return_value.__aenter__ = AsyncMock(return_value=mock_client)
                mock_httpx.return_value.__aexit__ = AsyncMock(return_value=False)

                result = await sync_agent_mcps(
                    owner="test",
                    repo="repo",
                    project_id="proj",
                    access_token="token",
                    trigger="tool_toggle",
                    db=db,
                )

        assert result.success is True
        assert result.files_updated == 1
        assert result.files_skipped == 0

    @pytest.mark.asyncio
    async def test_sync_idempotent_no_changes(self):
        """T031: second sync with same state produces files_updated=0."""
        db = AsyncMock()
        cursor_mock = AsyncMock()
        cursor_mock.fetchall.return_value = []
        db.execute.return_value = cursor_mock

        # Build content that already has tools: ["*"] and mcp-servers matching
        # the built-in MCPs (since _build_active_mcp_dict always includes them).
        fm = {
            "name": "Reviewer",
            "description": "Reviews pull requests",
            "tools": ["*"],
            "mcp-servers": {k: dict(v) for k, v in BUILTIN_MCPS.items()},
        }
        body = "\nYou are a code reviewer.\n"
        content = _serialize_agent_file(fm, body)
        encoded_content = base64.b64encode(content.encode()).decode()

        with patch(
            "src.services.agents.agent_mcp_sync._discover_agent_files",
            return_value=[
                {"path": ".github/agents/test.agent.md", "sha": "abc123", "download_url": ""}
            ],
        ):
            mock_get_response = MagicMock()
            mock_get_response.status_code = 200
            mock_get_response.json.return_value = {
                "sha": "abc123",
                "content": encoded_content,
            }

            mock_client = AsyncMock()
            mock_client.get.return_value = mock_get_response

            with patch("httpx.AsyncClient") as mock_httpx:
                mock_httpx.return_value.__aenter__ = AsyncMock(return_value=mock_client)
                mock_httpx.return_value.__aexit__ = AsyncMock(return_value=False)

                result = await sync_agent_mcps(
                    owner="test",
                    repo="repo",
                    project_id="proj",
                    access_token="token",
                    trigger="tool_toggle",
                    db=db,
                )

        assert result.success is True
        assert result.files_updated == 0
        assert result.files_unchanged == 1
        # put should not have been called
        mock_client.put.assert_not_called()

    @pytest.mark.asyncio
    async def test_sync_no_agent_files_returns_early(self):
        """Sync with no agent files returns success with zero counts."""
        db = AsyncMock()
        cursor_mock = AsyncMock()
        cursor_mock.fetchall.return_value = []
        db.execute.return_value = cursor_mock

        with patch(
            "src.services.agents.agent_mcp_sync._discover_agent_files",
            return_value=[],
        ):
            result = await sync_agent_mcps(
                owner="test",
                repo="repo",
                project_id="proj",
                access_token="token",
                trigger="startup",
                db=db,
            )

        assert result.success is True
        assert result.files_updated == 0
        assert result.files_unchanged == 0
        assert result.files_skipped == 0

    @pytest.mark.asyncio
    async def test_sync_handles_exception_in_process_agent_file(self):
        """Per-file exception is caught and recorded as error."""
        db = AsyncMock()
        cursor_mock = AsyncMock()
        cursor_mock.fetchall.return_value = []
        db.execute.return_value = cursor_mock

        with patch(
            "src.services.agents.agent_mcp_sync._discover_agent_files",
            return_value=[
                {"path": ".github/agents/bad.agent.md", "sha": "sha1", "download_url": ""}
            ],
        ):
            mock_client = AsyncMock()
            mock_client.get.side_effect = RuntimeError("network error")

            with patch("httpx.AsyncClient") as mock_httpx:
                mock_httpx.return_value.__aenter__ = AsyncMock(return_value=mock_client)
                mock_httpx.return_value.__aexit__ = AsyncMock(return_value=False)

                result = await sync_agent_mcps(
                    owner="test",
                    repo="repo",
                    project_id="proj",
                    access_token="token",
                    trigger="tool_toggle",
                    db=db,
                )

        assert result.success is True  # overall success; individual file errors
        assert result.files_skipped == 1
        assert len(result.errors) == 1
        assert "bad.agent.md" in result.errors[0]

    @pytest.mark.asyncio
    async def test_sync_multiple_files_counts(self):
        """Sync with mix of updated and unchanged files counts correctly."""
        db = AsyncMock()
        cursor_mock = AsyncMock()
        cursor_mock.fetchall.return_value = []
        db.execute.return_value = cursor_mock

        # File 1: needs updating (restrictive tools)
        content1 = SAMPLE_AGENT_CONTENT
        encoded1 = base64.b64encode(content1.encode()).decode()

        # File 2: already synced (tools: ["*"] + built-in MCPs)
        fm2 = {
            "name": "Linter",
            "description": "Lints code",
            "tools": ["*"],
            "mcp-servers": {k: dict(v) for k, v in BUILTIN_MCPS.items()},
        }
        body2 = "\nYou are a linter.\n"
        content2 = _serialize_agent_file(fm2, body2)
        encoded2 = base64.b64encode(content2.encode()).decode()

        with patch(
            "src.services.agents.agent_mcp_sync._discover_agent_files",
            return_value=[
                {"path": ".github/agents/a.agent.md", "sha": "sha1", "download_url": ""},
                {"path": ".github/agents/b.agent.md", "sha": "sha2", "download_url": ""},
            ],
        ):
            mock_get_resp_1 = MagicMock()
            mock_get_resp_1.status_code = 200
            mock_get_resp_1.json.return_value = {"sha": "sha1", "content": encoded1}

            mock_get_resp_2 = MagicMock()
            mock_get_resp_2.status_code = 200
            mock_get_resp_2.json.return_value = {"sha": "sha2", "content": encoded2}

            mock_put_response = MagicMock()
            mock_put_response.status_code = 200

            mock_client = AsyncMock()
            mock_client.get.side_effect = [mock_get_resp_1, mock_get_resp_2]
            mock_client.put.return_value = mock_put_response

            with patch("httpx.AsyncClient") as mock_httpx:
                mock_httpx.return_value.__aenter__ = AsyncMock(return_value=mock_client)
                mock_httpx.return_value.__aexit__ = AsyncMock(return_value=False)

                result = await sync_agent_mcps(
                    owner="test",
                    repo="repo",
                    project_id="proj",
                    access_token="token",
                    trigger="agent_create",
                    db=db,
                )

        assert result.success is True
        assert result.files_updated == 1
        assert result.files_unchanged == 1

    @pytest.mark.asyncio
    async def test_sync_reports_synced_mcps(self):
        """Sync result includes list of synced MCP keys."""
        db = AsyncMock()
        cursor_mock = AsyncMock()
        cursor_mock.fetchall.return_value = []
        db.execute.return_value = cursor_mock

        with patch(
            "src.services.agents.agent_mcp_sync._discover_agent_files",
            return_value=[],
        ):
            result = await sync_agent_mcps(
                owner="test",
                repo="repo",
                project_id="proj",
                access_token="token",
                trigger="startup",
                db=db,
            )

        # Built-in MCPs should always appear
        assert "context7" in result.synced_mcps
        assert "CodeGraphContext" in result.synced_mcps

    @pytest.mark.asyncio
    async def test_sync_global_exception_marks_failure(self):
        """A top-level exception during sync marks result.success=False."""
        db = AsyncMock()
        db.execute.side_effect = RuntimeError("DB down")

        result = await sync_agent_mcps(
            owner="test",
            repo="repo",
            project_id="proj",
            access_token="token",
            trigger="startup",
            db=db,
        )

        assert result.success is False
        assert len(result.errors) >= 1
        assert "Sync failed" in result.errors[0]


# ── _discover_agent_files tests ──────────────────────────────────────────


class TestDiscoverAgentFiles:
    @pytest.mark.asyncio
    async def test_returns_agent_md_files(self):
        """Returns only *.agent.md files from the API response."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = [
            {"name": "reviewer.agent.md", "path": ".github/agents/reviewer.agent.md", "sha": "abc"},
            {"name": "mcp.json", "path": ".github/agents/mcp.json", "sha": "def"},
            {"name": "linter.agent.md", "path": ".github/agents/linter.agent.md", "sha": "ghi"},
        ]

        with patch("httpx.AsyncClient") as mock_httpx:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_resp
            mock_httpx.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_httpx.return_value.__aexit__ = AsyncMock(return_value=False)

            files = await _discover_agent_files("owner", "repo", "token")

        assert len(files) == 2
        assert files[0]["path"] == ".github/agents/reviewer.agent.md"
        assert files[1]["path"] == ".github/agents/linter.agent.md"

    @pytest.mark.asyncio
    async def test_returns_empty_on_404(self):
        """Returns empty list when .github/agents/ doesn't exist."""
        mock_resp = MagicMock()
        mock_resp.status_code = 404

        with patch("httpx.AsyncClient") as mock_httpx:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_resp
            mock_httpx.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_httpx.return_value.__aexit__ = AsyncMock(return_value=False)

            files = await _discover_agent_files("owner", "repo", "token")

        assert files == []

    @pytest.mark.asyncio
    async def test_returns_empty_on_api_error(self):
        """Returns empty list on non-200/404 API response."""
        mock_resp = MagicMock()
        mock_resp.status_code = 500
        mock_resp.text = "Internal Server Error"

        with patch("httpx.AsyncClient") as mock_httpx:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_resp
            mock_httpx.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_httpx.return_value.__aexit__ = AsyncMock(return_value=False)

            files = await _discover_agent_files("owner", "repo", "token")

        assert files == []

    @pytest.mark.asyncio
    async def test_returns_empty_on_non_list_response(self):
        """Returns empty list when API returns non-list JSON (e.g., a single file object)."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"name": "not-a-list"}

        with patch("httpx.AsyncClient") as mock_httpx:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_resp
            mock_httpx.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_httpx.return_value.__aexit__ = AsyncMock(return_value=False)

            files = await _discover_agent_files("owner", "repo", "token")

        assert files == []

    @pytest.mark.asyncio
    async def test_skips_non_dict_entries(self):
        """Skips entries that are not dicts (e.g., strings)."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = [
            "not-a-dict",
            {"name": "valid.agent.md", "path": ".github/agents/valid.agent.md", "sha": "abc"},
        ]

        with patch("httpx.AsyncClient") as mock_httpx:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_resp
            mock_httpx.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_httpx.return_value.__aexit__ = AsyncMock(return_value=False)

            files = await _discover_agent_files("owner", "repo", "token")

        assert len(files) == 1

    @pytest.mark.asyncio
    async def test_download_url_defaults_to_empty(self):
        """download_url defaults to empty string when missing from entry."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = [
            {"name": "test.agent.md", "path": ".github/agents/test.agent.md", "sha": "abc"},
        ]

        with patch("httpx.AsyncClient") as mock_httpx:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_resp
            mock_httpx.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_httpx.return_value.__aexit__ = AsyncMock(return_value=False)

            files = await _discover_agent_files("owner", "repo", "token")

        assert files[0]["download_url"] == ""


# ── _process_agent_file tests ────────────────────────────────────────────


class TestProcessAgentFile:
    @pytest.mark.asyncio
    async def test_skips_on_get_failure(self):
        """File is skipped when GET returns non-200."""
        mock_client = AsyncMock()
        mock_resp = MagicMock()
        mock_resp.status_code = 404
        mock_client.get.return_value = mock_resp

        result = AgentMcpSyncResult()
        await _process_agent_file(
            client=mock_client,
            headers={},
            owner="o",
            repo="r",
            file_path=".github/agents/test.agent.md",
            active_mcps=dict(BUILTIN_MCPS),
            result=result,
        )

        assert result.files_skipped == 1
        assert len(result.errors) == 1
        assert "GET failed" in result.errors[0]

    @pytest.mark.asyncio
    async def test_skips_file_without_frontmatter(self):
        """File without YAML frontmatter is skipped."""
        encoded = base64.b64encode(SAMPLE_AGENT_NO_FRONTMATTER.encode()).decode()
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"sha": "sha1", "content": encoded}

        mock_client = AsyncMock()
        mock_client.get.return_value = mock_resp

        result = AgentMcpSyncResult()
        await _process_agent_file(
            client=mock_client,
            headers={},
            owner="o",
            repo="r",
            file_path=".github/agents/no_fm.agent.md",
            active_mcps=dict(BUILTIN_MCPS),
            result=result,
        )

        assert result.files_skipped == 1
        assert any("no parseable YAML frontmatter" in w for w in result.warnings)

    @pytest.mark.asyncio
    async def test_skips_on_validation_failure(self):
        """File is skipped when validation fails after merge."""
        # Create content with a server missing 'type' — this will fail validation
        content = "---\nname: Bad\ntools:\n  - '*'\n---\n\nBody\n"
        encoded = base64.b64encode(content.encode()).decode()

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"sha": "sha1", "content": encoded}

        mock_client = AsyncMock()
        mock_client.get.return_value = mock_resp

        # Pass an MCP with missing type field to trigger validation error
        bad_mcps = {"bad_server": {"url": "https://example.com"}}

        result = AgentMcpSyncResult()
        await _process_agent_file(
            client=mock_client,
            headers={},
            owner="o",
            repo="r",
            file_path=".github/agents/bad.agent.md",
            active_mcps=bad_mcps,
            result=result,
        )

        assert result.files_skipped == 1
        assert any("missing 'type'" in e for e in result.errors)

    @pytest.mark.asyncio
    async def test_skips_on_put_failure(self):
        """File is skipped when PUT returns a non-success status."""
        encoded = base64.b64encode(SAMPLE_AGENT_CONTENT.encode()).decode()
        mock_get_resp = MagicMock()
        mock_get_resp.status_code = 200
        mock_get_resp.json.return_value = {"sha": "sha1", "content": encoded}

        mock_put_resp = MagicMock()
        mock_put_resp.status_code = 422  # Unprocessable entity

        mock_client = AsyncMock()
        mock_client.get.return_value = mock_get_resp
        mock_client.put.return_value = mock_put_resp

        result = AgentMcpSyncResult()
        await _process_agent_file(
            client=mock_client,
            headers={},
            owner="o",
            repo="r",
            file_path=".github/agents/test.agent.md",
            active_mcps=dict(BUILTIN_MCPS),
            result=result,
        )

        assert result.files_skipped == 1
        assert any("PUT failed" in e for e in result.errors)

    @pytest.mark.asyncio
    async def test_successful_update(self):
        """File with restrictive tools is updated successfully."""
        encoded = base64.b64encode(SAMPLE_AGENT_CONTENT.encode()).decode()
        mock_get_resp = MagicMock()
        mock_get_resp.status_code = 200
        mock_get_resp.json.return_value = {"sha": "sha1", "content": encoded}

        mock_put_resp = MagicMock()
        mock_put_resp.status_code = 200

        mock_client = AsyncMock()
        mock_client.get.return_value = mock_get_resp
        mock_client.put.return_value = mock_put_resp

        result = AgentMcpSyncResult()
        await _process_agent_file(
            client=mock_client,
            headers={},
            owner="o",
            repo="r",
            file_path=".github/agents/test.agent.md",
            active_mcps=dict(BUILTIN_MCPS),
            result=result,
        )

        assert result.files_updated == 1
        assert result.files_skipped == 0
        # Verify the PUT payload includes the file sha
        put_call = mock_client.put.call_args
        assert put_call is not None
        body = put_call.kwargs.get("json") or put_call[1].get("json", {})
        assert body["sha"] == "sha1"

    @pytest.mark.asyncio
    async def test_records_tools_override_warning(self):
        """Warning is recorded when restrictive tools are overridden."""
        encoded = base64.b64encode(SAMPLE_AGENT_CONTENT.encode()).decode()
        mock_get_resp = MagicMock()
        mock_get_resp.status_code = 200
        mock_get_resp.json.return_value = {"sha": "sha1", "content": encoded}

        mock_put_resp = MagicMock()
        mock_put_resp.status_code = 200

        mock_client = AsyncMock()
        mock_client.get.return_value = mock_get_resp
        mock_client.put.return_value = mock_put_resp

        result = AgentMcpSyncResult()
        await _process_agent_file(
            client=mock_client,
            headers={},
            owner="o",
            repo="r",
            file_path=".github/agents/test.agent.md",
            active_mcps=dict(BUILTIN_MCPS),
            result=result,
        )

        assert any("tools overridden" in w for w in result.warnings)


# ── Additional parse/serialize tests ─────────────────────────────────────


class TestParseSerializeEdgeCases:
    def test_parse_invalid_yaml_returns_none(self):
        """Invalid YAML in frontmatter returns None."""
        content = "---\n: invalid: yaml: [[\n---\n\nBody"
        fm, _body = _parse_agent_file(content)
        assert fm is None

    def test_parse_non_dict_yaml_returns_none(self):
        """YAML that parses to a non-dict (e.g., list) returns None."""
        content = "---\n- item1\n- item2\n---\n\nBody"
        fm, _body = _parse_agent_file(content)
        assert fm is None

    def test_parse_empty_frontmatter_returns_none(self):
        """Empty YAML frontmatter (just whitespace) returns None."""
        content = "---\n\n---\n\nBody"
        fm, _body = _parse_agent_file(content)
        # yaml.safe_load on empty string returns None, which is not a dict
        assert fm is None

    def test_serialize_body_starting_with_newline(self):
        """Body starting with newline uses single \\n separator."""
        fm = {"name": "Test", "tools": ["*"]}
        body = "\nBody starts with newline.\n"
        result = _serialize_agent_file(fm, body)
        assert "---\n\nBody starts with newline." in result

    def test_serialize_body_without_leading_newline(self):
        """Body not starting with newline gets extra \\n separator."""
        fm = {"name": "Test", "tools": ["*"]}
        body = "Body without leading newline.\n"
        result = _serialize_agent_file(fm, body)
        assert "---\n\nBody without leading newline." in result

    def test_parse_content_with_no_body(self):
        """Frontmatter with minimal/empty body parses correctly."""
        content = "---\nname: Minimal\n---\n"
        fm, _body = _parse_agent_file(content)
        assert fm is not None
        assert fm["name"] == "Minimal"

    def test_serialize_preserves_frontmatter_keys(self):
        """Serialized output contains all frontmatter keys."""
        fm = {
            "name": "Agent",
            "description": "Test agent",
            "tools": ["*"],
            "mcp-servers": {"s1": {"type": "http", "url": "https://s1.com"}},
        }
        result = _serialize_agent_file(fm, "\nBody\n")
        assert "name: Agent" in result
        assert "description: Test agent" in result
        assert "mcp-servers:" in result


# ── Additional validation tests ──────────────────────────────────────────


class TestValidationEdgeCases:
    def test_tools_not_star_reports_error(self):
        """Frontmatter with tools != ['*'] reports validation error."""
        fm = {
            "tools": ["search"],
            "mcp-servers": {"s": {"type": "http", "url": "https://s.com"}},
        }
        errors = _validate_agent_frontmatter(fm, "agent.md")
        assert any("not ['*']" in e for e in errors)

    def test_mcp_servers_not_dict_reports_error(self):
        """Non-dict mcp-servers reports error and short-circuits."""
        fm = {"tools": ["*"], "mcp-servers": ["not", "a", "dict"]}
        errors = _validate_agent_frontmatter(fm, "agent.md")
        assert any("not a dict" in e for e in errors)

    def test_non_dict_server_entry_reports_error(self):
        """Non-dict server entry within mcp-servers reports error."""
        fm = {
            "tools": ["*"],
            "mcp-servers": {"bad": "not-a-dict"},
        }
        errors = _validate_agent_frontmatter(fm, "agent.md")
        assert any("not a dict" in e for e in errors)

    def test_http_missing_url_reports_error(self):
        """HTTP server without url field reports error."""
        fm = {
            "tools": ["*"],
            "mcp-servers": {"s": {"type": "http"}},
        }
        errors = _validate_agent_frontmatter(fm, "agent.md")
        assert any("missing 'url'" in e for e in errors)

    def test_sse_missing_url_reports_error(self):
        """SSE server without url field reports error."""
        fm = {
            "tools": ["*"],
            "mcp-servers": {"s": {"type": "sse"}},
        }
        errors = _validate_agent_frontmatter(fm, "agent.md")
        assert any("missing 'url'" in e for e in errors)

    def test_local_missing_command_reports_error(self):
        """Local server without command field reports error."""
        fm = {
            "tools": ["*"],
            "mcp-servers": {"s": {"type": "local"}},
        }
        errors = _validate_agent_frontmatter(fm, "agent.md")
        assert any("missing 'command'" in e for e in errors)

    def test_stdio_missing_command_reports_error(self):
        """stdio server without command field reports error."""
        fm = {
            "tools": ["*"],
            "mcp-servers": {"s": {"type": "stdio"}},
        }
        errors = _validate_agent_frontmatter(fm, "agent.md")
        assert any("missing 'command'" in e for e in errors)

    def test_valid_local_server_passes(self):
        """Local server with command passes validation."""
        fm = {
            "tools": ["*"],
            "mcp-servers": {"s": {"type": "local", "command": "npx"}},
        }
        errors = _validate_agent_frontmatter(fm, "agent.md")
        assert errors == []

    def test_multiple_errors_reported(self):
        """Multiple servers with issues produce multiple errors."""
        fm = {
            "tools": ["*"],
            "mcp-servers": {
                "s1": {"type": "http"},  # missing url
                "s2": {"type": "local"},  # missing command
                "s3": "not-a-dict",  # not a dict
            },
        }
        errors = _validate_agent_frontmatter(fm, "agent.md")
        assert len(errors) == 3

    def test_mcp_servers_missing_entirely(self):
        """Frontmatter without mcp-servers field reports error."""
        fm = {"tools": ["*"]}
        errors = _validate_agent_frontmatter(fm, "agent.md")
        assert any("not a dict" in e for e in errors)


# ── Additional _build_active_mcp_dict tests ──────────────────────────────


class TestBuildActiveMcpDictEdgeCases:
    @pytest.mark.asyncio
    async def test_non_dict_mcpservers_skipped(self):
        """config_content with mcpServers as a non-dict is skipped."""
        db = AsyncMock()
        cursor_mock = AsyncMock()
        cursor_mock.fetchall.return_value = [
            {
                "name": "BadShape",
                "config_content": json.dumps({"mcpServers": ["not", "a", "dict"]}),
            }
        ]
        db.execute.return_value = cursor_mock

        result = await _build_active_mcp_dict(db, "project-1")
        # Only built-in MCPs, bad shape skipped
        assert len(result) == len(BUILTIN_MCPS)

    @pytest.mark.asyncio
    async def test_non_dict_server_config_skipped(self):
        """Individual server entries that are not dicts are skipped."""
        db = AsyncMock()
        cursor_mock = AsyncMock()
        cursor_mock.fetchall.return_value = [
            {
                "name": "MixedMCP",
                "config_content": json.dumps(
                    {"mcpServers": {
                        "good": {"type": "http", "url": "https://good.com"},
                        "bad": "not-a-dict",
                    }}
                ),
            }
        ]
        db.execute.return_value = cursor_mock

        result = await _build_active_mcp_dict(db, "project-1")
        assert "good" in result
        assert "bad" not in result

    @pytest.mark.asyncio
    async def test_empty_db_returns_only_builtins(self):
        """Empty database returns only built-in MCPs."""
        db = AsyncMock()
        cursor_mock = AsyncMock()
        cursor_mock.fetchall.return_value = []
        db.execute.return_value = cursor_mock

        result = await _build_active_mcp_dict(db, "project-1")
        assert len(result) == len(BUILTIN_MCPS)
        assert set(result.keys()) == set(BUILTIN_MCPS.keys())

    @pytest.mark.asyncio
    async def test_config_without_mcpservers_key_skipped(self):
        """config_content JSON without mcpServers key is effectively no-op."""
        db = AsyncMock()
        cursor_mock = AsyncMock()
        cursor_mock.fetchall.return_value = [
            {
                "name": "NoMcpServers",
                "config_content": json.dumps({"otherField": "value"}),
            }
        ]
        db.execute.return_value = cursor_mock

        result = await _build_active_mcp_dict(db, "project-1")
        assert len(result) == len(BUILTIN_MCPS)


# ── Additional _merge_mcps_into_frontmatter tests ────────────────────────


class TestMergeMcpServersEdgeCases:
    def test_merge_replaces_entire_mcp_servers_dict(self):
        """mcp-servers is fully replaced, not merged incrementally."""
        active = {"new_server": {"type": "http", "url": "https://new.com"}}
        fm = {
            "name": "Test",
            "tools": ["*"],
            "mcp-servers": {"old_server": {"type": "http", "url": "https://old.com"}},
        }
        updated, _ = _merge_mcps_into_frontmatter(fm, active, "agent.md")
        assert "old_server" not in updated["mcp-servers"]
        assert "new_server" in updated["mcp-servers"]

    def test_merge_deep_copies_config(self):
        """Config dicts are copied, not shared by reference with active_mcps."""
        active = {"s": {"type": "http", "url": "https://s.com"}}
        fm = {"name": "Test", "tools": ["*"]}
        updated, _ = _merge_mcps_into_frontmatter(fm, active, "agent.md")
        # Mutating the result should not affect the input
        updated["mcp-servers"]["s"]["url"] = "https://changed.com"
        assert active["s"]["url"] == "https://s.com"

    def test_merge_with_tools_set_to_none_no_warning(self):
        """tools=None is treated as absent (no override warning)."""
        fm = {"name": "Test", "tools": None}
        updated, warnings = _merge_mcps_into_frontmatter(fm, {}, "agent.md")
        assert updated["tools"] == ["*"]
        # tools was None (not a real restrictive value), so the warning behavior
        # depends on the code — but the key thing is tools is enforced
        # The code does: if current_tools is not None → warns
        # Here tools is None so no warning
        assert len(warnings) == 0

    def test_merge_with_empty_tools_list_warns(self):
        """Empty tools list is overridden with warning."""
        fm = {"name": "Test", "tools": []}
        updated, warnings = _merge_mcps_into_frontmatter(fm, {}, "agent.md")
        assert updated["tools"] == ["*"]
        assert len(warnings) == 1


# ── AgentMcpSyncResult dataclass tests ───────────────────────────────────


class TestAgentMcpSyncResult:
    def test_default_values(self):
        """Default result has success=True and zeroed counts."""
        result = AgentMcpSyncResult()
        assert result.success is True
        assert result.files_updated == 0
        assert result.files_skipped == 0
        assert result.files_unchanged == 0
        assert result.warnings == []
        assert result.errors == []
        assert result.synced_mcps == []

    def test_mutable_lists_are_independent(self):
        """Each result instance has its own mutable lists."""
        r1 = AgentMcpSyncResult()
        r2 = AgentMcpSyncResult()
        r1.warnings.append("warning1")
        r1.errors.append("error1")
        r1.synced_mcps.append("mcp1")
        assert r2.warnings == []
        assert r2.errors == []
        assert r2.synced_mcps == []
