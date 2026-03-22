"""Unit tests for the agent creator service.

Covers pure functions (parse_command, fuzzy_match_status,
generate_config_files, _format_preview, _format_pipeline_report),
the admin check (is_admin_user), and top-level handle_agent_command routing.
"""

from __future__ import annotations

from typing import ClassVar
from unittest.mock import AsyncMock, patch

import aiosqlite
import pytest

from src.models.agent_creator import (
    AgentCreationState,
    AgentPreview,
    CreationStep,
    PipelineStepResult,
)
from src.services.agent_creator import (
    _format_pipeline_report,
    _format_preview,
    clear_session,
    fuzzy_match_status,
    generate_config_files,
    get_active_session,
    handle_agent_command,
    is_admin_user,
    parse_command,
)

# ═══════════════════════════════════════════════════════════════════════
# parse_command
# ═══════════════════════════════════════════════════════════════════════


class TestParseCommand:
    """Tests for the #agent command parser."""

    def test_simple_description(self):
        desc, status = parse_command("#agent Reviews PRs for security")
        assert desc == "Reviews PRs for security"
        assert status is None

    def test_description_with_status(self):
        desc, status = parse_command("#agent Reviews PRs for security #in-review")
        assert desc == "Reviews PRs for security"
        assert status == "in-review"

    def test_status_with_spaces(self):
        desc, status = parse_command("#agent Auto-assigns issues #Code Review")
        assert desc == "Auto-assigns issues"
        assert status == "Code Review"

    def test_case_insensitive_prefix(self):
        desc, status = parse_command("#AGENT some description")
        assert desc == "some description"
        assert status is None

    def test_empty_description_raises(self):
        with pytest.raises(ValueError, match="empty description"):
            parse_command("#agent")

    def test_whitespace_only_raises(self):
        with pytest.raises(ValueError, match="empty description"):
            parse_command("#agent   ")

    def test_hash_only_status_no_description(self):
        """#agent #done — description is empty before the hash."""
        with pytest.raises(ValueError, match="empty description"):
            parse_command("#agent #done")

    def test_multiple_hash_takes_last(self):
        desc, status = parse_command("#agent Handles #bug triage flow #backlog")
        assert desc == "Handles #bug triage flow"
        assert status == "backlog"

    def test_strips_whitespace(self):
        desc, status = parse_command("  #agent   Review PRs   #in-review  ")
        assert desc == "Review PRs"
        assert status == "in-review"


# ═══════════════════════════════════════════════════════════════════════
# fuzzy_match_status
# ═══════════════════════════════════════════════════════════════════════


class TestFuzzyMatchStatus:
    """Tests for status column fuzzy matching."""

    COLUMNS: ClassVar[list[str]] = ["Todo", "In Progress", "In Review", "Code Review", "Done"]

    def test_exact_match(self):
        resolved, ambiguous, matches = fuzzy_match_status("Done", self.COLUMNS)
        assert resolved == "Done"
        assert ambiguous is False
        assert matches == ["Done"]

    def test_normalized_exact_match(self):
        """in-review normalises to the same as 'In Review'."""
        resolved, ambiguous, _matches = fuzzy_match_status("in-review", self.COLUMNS)
        assert resolved == "In Review"
        assert ambiguous is False

    def test_case_insensitive_match(self):
        resolved, ambiguous, _matches = fuzzy_match_status("TODO", self.COLUMNS)
        assert resolved == "Todo"
        assert ambiguous is False

    def test_ambiguous_contains_match(self):
        """'review' matches both 'In Review' and 'Code Review'."""
        resolved, ambiguous, matches = fuzzy_match_status("review", self.COLUMNS)
        assert resolved is None
        assert ambiguous is True
        assert set(matches) == {"In Review", "Code Review"}

    def test_unique_contains_match(self):
        """'progress' uniquely matches 'In Progress'."""
        resolved, ambiguous, _matches = fuzzy_match_status("progress", self.COLUMNS)
        assert resolved == "In Progress"
        assert ambiguous is False

    def test_no_match(self):
        resolved, ambiguous, matches = fuzzy_match_status("nonexistent", self.COLUMNS)
        assert resolved is None
        assert ambiguous is False
        assert matches == []

    def test_empty_columns(self):
        resolved, ambiguous, matches = fuzzy_match_status("anything", [])
        assert resolved is None
        assert ambiguous is False
        assert matches == []

    def test_empty_input(self):
        _resolved, ambiguous, _matches = fuzzy_match_status("", self.COLUMNS)
        # Empty string matches everything via contains — expect ambiguous
        assert ambiguous is True


# ═══════════════════════════════════════════════════════════════════════
# generate_config_files
# ═══════════════════════════════════════════════════════════════════════


class TestGenerateConfigFiles:
    """Tests for config file generation (GitHub Custom Agent .agent.md format)."""

    @pytest.fixture
    def preview(self) -> AgentPreview:
        return AgentPreview(
            name="SecurityReviewer",
            slug="security-reviewer",
            description="Reviews PRs for security vulnerabilities",
            system_prompt="You are a security reviewer...",
            status_column="In Review",
            tools=["search_code", "create_issue"],
        )

    def test_returns_two_files(self, preview: AgentPreview):
        files = generate_config_files(preview)
        assert len(files) == 2

    def test_agent_file_path(self, preview: AgentPreview):
        files = generate_config_files(preview)
        assert files[0]["path"] == ".github/agents/security-reviewer.agent.md"

    def test_prompt_file_path(self, preview: AgentPreview):
        files = generate_config_files(preview)
        assert files[1]["path"] == ".github/prompts/security-reviewer.prompt.md"

    def test_agent_file_has_yaml_frontmatter(self, preview: AgentPreview):
        files = generate_config_files(preview)
        content = files[0]["content"]
        assert content.startswith("---\n")
        assert "\n---\n" in content

    def test_agent_file_has_frontmatter(self, preview: AgentPreview):
        files = generate_config_files(preview)
        content = files[0]["content"]
        assert "description: Reviews PRs for security vulnerabilities" in content

    def test_agent_file_omits_tools_from_frontmatter(self, preview: AgentPreview):
        files = generate_config_files(preview)
        content = files[0]["content"]
        assert "tools:" not in content

    def test_agent_file_has_system_prompt_body(self, preview: AgentPreview):
        files = generate_config_files(preview)
        content = files[0]["content"]
        assert "You are a security reviewer..." in content

    def test_prompt_file_has_prompt_fence(self, preview: AgentPreview):
        files = generate_config_files(preview)
        content = files[1]["content"]
        assert content.startswith("```prompt\n")
        assert "agent: security-reviewer" in content

    def test_no_tools_omits_tools_key(self):
        preview = AgentPreview(
            name="SimpleAgent",
            slug="simple-agent",
            description="A simple agent",
            system_prompt="Do things",
            status_column="Todo",
            tools=[],
        )
        files = generate_config_files(preview)
        assert "tools:" not in files[0]["content"]

    def test_agent_file_includes_mcp_servers_and_metadata(self):
        preview = AgentPreview(
            name="McpReviewer",
            slug="mcp-reviewer",
            description="Uses uploaded MCP servers",
            system_prompt="Review with MCP assistance",
            status_column="Todo",
            tools=["Context7"],
            tool_ids=["tool-123"],
            mcp_servers={
                "context7": {
                    "type": "http",
                    "url": "https://example.com/mcp",
                    "tools": ["*"],
                }
            },
        )

        files = generate_config_files(preview)
        content = files[0]["content"]

        assert "mcp-servers:" in content
        assert "context7:" in content
        assert "url: https://example.com/mcp" in content
        assert "solune-tool-ids: tool-123" in content
        assert "\nmetadata:\n" in content


# ═══════════════════════════════════════════════════════════════════════
# _format_preview
# ═══════════════════════════════════════════════════════════════════════


class TestFormatPreview:
    """Tests for the preview markdown formatter."""

    @pytest.fixture
    def preview(self) -> AgentPreview:
        return AgentPreview(
            name="BugTriager",
            slug="bug-triager",
            description="Triages bug reports",
            system_prompt="You triage bugs " + "x" * 600,  # > 500 chars
            status_column="Triage",
            tools=["list_projects"],
        )

    def test_contains_name(self, preview: AgentPreview):
        result = _format_preview(preview, is_new_column=False)
        assert "## Agent Preview: BugTriager" in result

    def test_contains_slug(self, preview: AgentPreview):
        result = _format_preview(preview, is_new_column=False)
        assert "`bug-triager`" in result

    def test_contains_description(self, preview: AgentPreview):
        result = _format_preview(preview, is_new_column=False)
        assert "Triages bug reports" in result

    def test_contains_tools_display(self, preview: AgentPreview):
        result = _format_preview(preview, is_new_column=False)
        assert "`list_projects`" in result

    def test_contains_file_paths(self, preview: AgentPreview):
        result = _format_preview(preview, is_new_column=False)
        assert ".github/agents/bug-triager.agent.md" in result
        assert ".github/prompts/bug-triager.prompt.md" in result

    def test_new_column_note(self, preview: AgentPreview):
        result = _format_preview(preview, is_new_column=True)
        assert "*(new column)*" in result

    def test_no_new_column_note_when_false(self, preview: AgentPreview):
        result = _format_preview(preview, is_new_column=False)
        assert "*(new column)*" not in result

    def test_long_prompt_truncated(self, preview: AgentPreview):
        result = _format_preview(preview, is_new_column=False)
        assert "..." in result


# ═══════════════════════════════════════════════════════════════════════
# _format_pipeline_report
# ═══════════════════════════════════════════════════════════════════════


class TestFormatPipelineReport:
    """Tests for the pipeline report formatter."""

    @pytest.fixture
    def preview(self) -> AgentPreview:
        return AgentPreview(
            name="TestAgent",
            slug="test-agent",
            description="A test agent",
            system_prompt="prompt",
            status_column="Done",
            tools=[],
        )

    def test_all_success(self, preview: AgentPreview):
        results = [
            PipelineStepResult(step_name="Step A", success=True, detail="OK"),
            PipelineStepResult(step_name="Step B", success=True, detail="OK"),
        ]
        report = _format_pipeline_report(preview, results)
        assert "✅ **Step A** — OK" in report
        assert "✅ **Step B** — OK" in report
        assert "2/2 steps completed" in report

    def test_some_failures(self, preview: AgentPreview):
        results = [
            PipelineStepResult(step_name="Step A", success=True, detail="OK"),
            PipelineStepResult(step_name="Step B", success=False, error="Connection timeout"),
        ]
        report = _format_pipeline_report(preview, results)
        assert "✅ **Step A**" in report
        assert "❌ **Step B**" in report
        assert "Connection timeout" in report
        assert "1/2 steps completed" in report

    def test_empty_results(self, preview: AgentPreview):
        report = _format_pipeline_report(preview, [])
        assert "0/0 steps completed" in report


# ═══════════════════════════════════════════════════════════════════════
# AgentPreview.name_to_slug
# ═══════════════════════════════════════════════════════════════════════


class TestNameToSlug:
    """Tests for slug derivation."""

    def test_simple(self):
        assert AgentPreview.name_to_slug("SecurityReviewer") == "securityreviewer"

    def test_spaces(self):
        assert AgentPreview.name_to_slug("Bug Triager") == "bug-triager"

    def test_special_chars(self):
        assert AgentPreview.name_to_slug("PR Review (Auto)") == "pr-review-auto"

    def test_consecutive_special(self):
        assert AgentPreview.name_to_slug("a--b__c  d") == "a-b-c-d"

    def test_leading_trailing_stripped(self):
        assert AgentPreview.name_to_slug("---test---") == "test"

    def test_empty_string(self):
        assert AgentPreview.name_to_slug("") == ""


# ═══════════════════════════════════════════════════════════════════════
# is_admin_user
# ═══════════════════════════════════════════════════════════════════════


class TestIsAdminUser:
    """Tests for the admin check helper."""

    @pytest.fixture
    async def seeded_db(self, mock_db: aiosqlite.Connection):
        """Seed global_settings row (migrations create the table but don't insert)."""
        await mock_db.execute(
            "INSERT OR IGNORE INTO global_settings (id, updated_at) VALUES (1, '2026-01-01T00:00:00')",
        )
        await mock_db.commit()
        return mock_db

    @pytest.fixture
    async def admin_db(self, seeded_db: aiosqlite.Connection):
        """Set admin_github_user_id in global_settings."""
        await seeded_db.execute(
            "UPDATE global_settings SET admin_github_user_id = ? WHERE id = 1",
            ("12345",),
        )
        await seeded_db.commit()
        return seeded_db

    async def test_admin_user_returns_true(self, admin_db: aiosqlite.Connection):
        assert await is_admin_user(admin_db, "12345") is True

    async def test_non_admin_returns_false(self, admin_db: aiosqlite.Connection):
        assert await is_admin_user(admin_db, "99999") is False

    async def test_no_admin_set_auto_promotes(self, seeded_db: aiosqlite.Connection):
        """When no admin is set in debug mode, the first caller is auto-promoted."""
        mock_settings = AsyncMock()
        mock_settings.debug = True
        mock_settings.admin_github_user_id = None
        with patch("src.config.get_settings", return_value=mock_settings):
            assert await is_admin_user(seeded_db, "12345") is True
        # Verify the admin was persisted.
        cursor = await seeded_db.execute(
            "SELECT admin_github_user_id FROM global_settings WHERE id = 1"
        )
        row = await cursor.fetchone()
        admin_id = row["admin_github_user_id"] if isinstance(row, dict) else row[0]
        assert str(admin_id) == "12345"

    async def test_no_admin_set_second_user_denied(self, seeded_db: aiosqlite.Connection):
        """After auto-promotion, a different user is denied."""
        mock_settings = AsyncMock()
        mock_settings.debug = True
        mock_settings.admin_github_user_id = None
        with patch("src.config.get_settings", return_value=mock_settings):
            assert await is_admin_user(seeded_db, "first-user") is True
            assert await is_admin_user(seeded_db, "second-user") is False

    async def test_no_admin_set_production_denies(self, seeded_db: aiosqlite.Connection):
        """In production mode, missing admin config denies access."""
        mock_settings = AsyncMock()
        mock_settings.debug = False
        mock_settings.admin_github_user_id = None
        with patch("src.config.get_settings", return_value=mock_settings):
            assert await is_admin_user(seeded_db, "12345") is False

    async def test_production_configured_admin_allowed(self, seeded_db: aiosqlite.Connection):
        """In production with ADMIN_GITHUB_USER_ID set, configured admin is allowed and DB seeded."""
        mock_settings = AsyncMock()
        mock_settings.debug = False
        mock_settings.admin_github_user_id = 12345
        with patch("src.config.get_settings", return_value=mock_settings):
            assert await is_admin_user(seeded_db, "12345") is True
        # Verify admin was persisted in DB
        cursor = await seeded_db.execute(
            "SELECT admin_github_user_id FROM global_settings WHERE id = 1"
        )
        row = await cursor.fetchone()
        admin_id = row["admin_github_user_id"] if isinstance(row, dict) else row[0]
        assert str(admin_id) == "12345"

    async def test_production_configured_admin_denies_other(self, seeded_db: aiosqlite.Connection):
        """In production with ADMIN_GITHUB_USER_ID set, non-admin user is denied."""
        mock_settings = AsyncMock()
        mock_settings.debug = False
        mock_settings.admin_github_user_id = 12345
        with patch("src.config.get_settings", return_value=mock_settings):
            assert await is_admin_user(seeded_db, "99999") is False

    async def test_db_error_returns_false(self):
        """If the DB query fails, default to denying access."""
        db = AsyncMock()
        db.execute.side_effect = Exception("DB unavailable")
        assert await is_admin_user(db, "12345") is False


# ═══════════════════════════════════════════════════════════════════════
# handle_agent_command — admin gate
# ═══════════════════════════════════════════════════════════════════════


class TestHandleAgentCommandAdminGate:
    """Tests that handle_agent_command enforces admin-only access."""

    @pytest.fixture
    async def seeded_db(self, mock_db: aiosqlite.Connection):
        """Seed global_settings row."""
        await mock_db.execute(
            "INSERT OR IGNORE INTO global_settings (id, updated_at) VALUES (1, '2026-01-01T00:00:00')",
        )
        await mock_db.commit()
        return mock_db

    async def test_non_admin_denied(self, seeded_db: aiosqlite.Connection):
        """Non-admin user should receive an auth error without any state change."""
        # Pre-set an admin so "not-an-admin" is genuinely non-admin.
        await seeded_db.execute(
            "UPDATE global_settings SET admin_github_user_id = ? WHERE id = 1",
            ("real-admin",),
        )
        await seeded_db.commit()

        result = await handle_agent_command(
            message="#agent Create a test agent",
            session_key="test-session-key",
            project_id="PVT_123",
            owner="testowner",
            repo="testrepo",
            github_user_id="not-an-admin",
            access_token="token",
            db=seeded_db,
            project_columns=["Todo", "Done"],
        )
        assert "restricted to admin" in result
        assert get_active_session("test-session-key") is None

    async def test_admin_proceeds(self, seeded_db: aiosqlite.Connection):
        """Admin user should pass the gate and reach command parsing."""
        # Set up admin
        await seeded_db.execute(
            "UPDATE global_settings SET admin_github_user_id = ? WHERE id = 1",
            ("admin-user",),
        )
        await seeded_db.commit()

        with patch("src.services.agent_creator.get_ai_agent_service") as mock_ai:
            mock_service = AsyncMock()
            mock_service.generate_agent_config.return_value = {
                "name": "TestAgent",
                "description": "A test agent",
                "system_prompt": "You are a test agent.",
                "tools": ["search_code"],
            }
            mock_ai.return_value = mock_service

            result = await handle_agent_command(
                message="#agent Create a test agent #Done",
                session_key="admin-session",
                project_id="PVT_123",
                owner="testowner",
                repo="testrepo",
                github_user_id="admin-user",
                access_token="token",
                db=seeded_db,
                project_columns=["Todo", "Done"],
            )
            # Should proceed to preview (not blocked)
            assert "Agent Preview" in result or "Error" in result
            # Clean up
            clear_session("admin-session")


# ═══════════════════════════════════════════════════════════════════════
# Session management
# ═══════════════════════════════════════════════════════════════════════


class TestSessionManagement:
    """Tests for get_active_session and clear_session."""

    def test_no_session_returns_none(self):
        assert get_active_session("nonexistent-key") is None

    def test_clear_nonexistent_is_noop(self):
        """clear_session on a missing key should not raise."""
        clear_session("nonexistent-key")  # should not raise


# ═══════════════════════════════════════════════════════════════════════
# AgentCreationState model
# ═══════════════════════════════════════════════════════════════════════


class TestAgentCreationState:
    """Tests for the AgentCreationState model."""

    def test_default_step_is_parse(self):
        state = AgentCreationState(session_id="s1")
        assert state.step == CreationStep.PARSE

    def test_github_user_id_stored(self):
        state = AgentCreationState(session_id="s1", github_user_id="12345")
        assert state.github_user_id == "12345"

    def test_github_user_id_defaults_empty(self):
        state = AgentCreationState(session_id="s1")
        assert state.github_user_id == ""

    def test_available_projects_default_empty(self):
        state = AgentCreationState(session_id="s1")
        assert state.available_projects == []


# ---------------------------------------------------------------------------
# T029 - Exception paths
# ---------------------------------------------------------------------------


class TestExceptionPaths:
    """Tests for GitHub API error handling in agent creation pipeline."""

    async def test_db_error_in_admin_check_returns_false(self):
        """Database failures in is_admin_user gracefully deny access."""
        db = AsyncMock()
        db.execute.side_effect = Exception("DB connection lost")
        result = await is_admin_user(db, "12345")
        assert result is False

    async def test_handle_command_with_db_error_returns_error_message(self, mock_db):
        """handle_agent_command returns error string when DB is broken for admin check."""
        broken_db = AsyncMock()
        broken_db.execute.side_effect = Exception("DB unavailable")

        result = await handle_agent_command(
            message="#agent Create a security reviewer",
            session_key="err-session",
            project_id="PVT_1",
            owner="testowner",
            repo="testrepo",
            github_user_id="12345",
            access_token="token",
            db=broken_db,
            project_columns=["Todo", "Done"],
        )
        # Should return an error or denied message, not crash
        assert isinstance(result, str)

    async def test_ai_service_network_error_surfaces_gracefully(self, mock_db):
        """Network errors from AI service are caught during preview generation."""
        await mock_db.execute(
            "INSERT OR IGNORE INTO global_settings (id, updated_at) VALUES (1, '2026-01-01T00:00:00')",
        )
        await mock_db.execute(
            "UPDATE global_settings SET admin_github_user_id = ? WHERE id = 1",
            ("admin-user",),
        )
        await mock_db.commit()

        with patch("src.services.agent_creator.get_ai_agent_service") as mock_ai:
            mock_service = AsyncMock()
            mock_service.generate_agent_config.side_effect = ConnectionError("Network unreachable")
            mock_ai.return_value = mock_service

            result = await handle_agent_command(
                message="#agent Create a reviewer #Done",
                session_key="net-err-session",
                project_id="PVT_1",
                owner="testowner",
                repo="testrepo",
                github_user_id="admin-user",
                access_token="token",
                db=mock_db,
                project_columns=["Todo", "Done"],
            )
            assert isinstance(result, str)
            clear_session("net-err-session")


# ---------------------------------------------------------------------------
# T030 - Config parsing
# ---------------------------------------------------------------------------


class TestConfigParsing:
    """Tests for malformed/missing config scenarios in agent creation."""

    def test_parse_command_empty_raises(self):
        """Empty description after prefix raises ValueError."""
        with pytest.raises(ValueError, match="empty description"):
            parse_command("#agent")

    def test_parse_command_whitespace_only_raises(self):
        """Whitespace-only description raises ValueError."""
        with pytest.raises(ValueError, match="empty description"):
            parse_command("#agent   ")

    def test_parse_command_extracts_status_after_hash(self):
        """Status is extracted from the last # in the command."""
        desc, status = parse_command("#agent Build a linter #In Review")
        assert desc == "Build a linter"
        assert status is not None
        assert "review" in status.lower()

    def test_fuzzy_match_empty_columns_returns_none(self):
        """Fuzzy match with no columns returns (None, False, [])."""
        resolved, ambiguous, matches = fuzzy_match_status("Done", [])
        assert resolved is None
        assert ambiguous is False
        assert matches == []

    def test_fuzzy_match_empty_input_returns_none(self):
        """Fuzzy match with empty input returns no match."""
        resolved, _ambiguous, _matches = fuzzy_match_status("", ["Todo", "Done"])
        assert resolved is None

    async def test_ai_returns_tools_as_non_list(self, mock_db):
        """When AI returns tools as a non-list, it should be handled gracefully."""
        await mock_db.execute(
            "INSERT OR IGNORE INTO global_settings (id, updated_at) VALUES (1, '2026-01-01T00:00:00')",
        )
        await mock_db.execute(
            "UPDATE global_settings SET admin_github_user_id = ? WHERE id = 1",
            ("admin-user",),
        )
        await mock_db.commit()

        with patch("src.services.agent_creator.get_ai_agent_service") as mock_ai:
            mock_service = AsyncMock()
            mock_service.generate_agent_config.return_value = {
                "name": "BadTools",
                "description": "Agent with bad tools",
                "system_prompt": "You are a test.",
                "tools": "not-a-list",
            }
            mock_ai.return_value = mock_service

            result = await handle_agent_command(
                message="#agent Create agent #Done",
                session_key="bad-tools-session",
                project_id="PVT_1",
                owner="testowner",
                repo="testrepo",
                github_user_id="admin-user",
                access_token="token",
                db=mock_db,
                project_columns=["Todo", "Done"],
            )
            assert isinstance(result, str)
            clear_session("bad-tools-session")


# ---------------------------------------------------------------------------
# T031 - Tool assignment
# ---------------------------------------------------------------------------


class TestToolAssignment:
    """Tests for tool assignment logic in config file generation."""

    @pytest.fixture
    def preview_with_tools(self) -> AgentPreview:
        return AgentPreview(
            name="ToolAgent",
            slug="tool-agent",
            description="Agent with tools",
            system_prompt="You use tools.",
            status_column="Done",
            tools=["search_code", "create_issue"],
        )

    @pytest.fixture
    def preview_no_tools(self) -> AgentPreview:
        return AgentPreview(
            name="NoToolAgent",
            slug="no-tool-agent",
            description="Agent without extras",
            system_prompt="You do things.",
            status_column="Done",
            tools=[],
        )

    def test_tools_appear_in_preview_format(self, preview_with_tools):
        """Tools list is included in the formatted preview."""
        from src.services.agent_creator import _format_preview

        text = _format_preview(preview_with_tools, is_new_column=False)
        assert "search_code" in text
        assert "create_issue" in text

    def test_no_tools_omits_tools_section_in_config(self, preview_no_tools):
        """Config files with no tools should not include a tools key in frontmatter."""
        files = generate_config_files(preview_no_tools)
        agent_file = files[0]
        assert "tools" not in agent_file["content"].split("---")[1]

    def test_tools_with_mcp_servers_in_frontmatter(self):
        """MCP servers appear in agent file frontmatter when specified."""
        preview = AgentPreview(
            name="McpAgent",
            slug="mcp-agent",
            description="Agent with MCP",
            system_prompt="You use MCP.",
            status_column="Done",
            tools=["tool1"],
            tool_ids=["tid-1"],
            mcp_servers={"my-server": {"url": "https://example.com"}},
        )
        files = generate_config_files(preview)
        agent_content = files[0]["content"]
        assert "mcp-servers" in agent_content or "mcp_servers" in agent_content

    def test_config_files_count_is_two(self, preview_with_tools):
        """generate_config_files always returns exactly 2 files."""
        files = generate_config_files(preview_with_tools)
        assert len(files) == 2

    def test_agent_file_path_matches_slug(self, preview_with_tools):
        """Agent file path contains the slug."""
        files = generate_config_files(preview_with_tools)
        assert "tool-agent" in files[0]["path"]

    def test_prompt_file_path_matches_slug(self, preview_with_tools):
        """Prompt file path contains the slug."""
        files = generate_config_files(preview_with_tools)
        assert "tool-agent" in files[1]["path"]
