"""Unit tests for agent_mcp_sync module."""

from __future__ import annotations

import base64
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.services.agents.agent_mcp_sync import (
    BUILTIN_MCPS,
    _build_active_mcp_dict,
    _merge_mcps_into_frontmatter,
    _parse_agent_file,
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

    def test_no_active_mcps_yields_only_builtins(self):
        """T017: with no active MCPs, result has only built-in MCPs."""
        # When no active MCPs are passed, mcp-servers should be empty
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
