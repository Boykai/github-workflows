"""Unit tests for the agent creator service.

Covers pure functions (parse_command, fuzzy_match_status, _yaml_quote,
_generate_config_files, _format_preview, _format_pipeline_report),
the admin check (is_admin_user), and top-level handle_agent_command routing.
"""

from __future__ import annotations

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
    _generate_config_files,
    _yaml_quote,
    clear_session,
    fuzzy_match_status,
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

    COLUMNS = ["Todo", "In Progress", "In Review", "Code Review", "Done"]

    def test_exact_match(self):
        resolved, ambiguous, matches = fuzzy_match_status("Done", self.COLUMNS)
        assert resolved == "Done"
        assert ambiguous is False
        assert matches == ["Done"]

    def test_normalized_exact_match(self):
        """in-review normalises to the same as 'In Review'."""
        resolved, ambiguous, matches = fuzzy_match_status("in-review", self.COLUMNS)
        assert resolved == "In Review"
        assert ambiguous is False

    def test_case_insensitive_match(self):
        resolved, ambiguous, matches = fuzzy_match_status("TODO", self.COLUMNS)
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
        resolved, ambiguous, matches = fuzzy_match_status("progress", self.COLUMNS)
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
        resolved, ambiguous, matches = fuzzy_match_status("", self.COLUMNS)
        # Empty string matches everything via contains — expect ambiguous
        assert ambiguous is True


# ═══════════════════════════════════════════════════════════════════════
# _yaml_quote
# ═══════════════════════════════════════════════════════════════════════


class TestYamlQuote:
    """Tests for YAML-safe string quoting."""

    def test_simple_string(self):
        assert _yaml_quote("hello") == '"hello"'

    def test_colon_in_value(self):
        result = _yaml_quote("Monitors issues: daily")
        assert result == '"Monitors issues: daily"'

    def test_hash_in_value(self):
        result = _yaml_quote("Section # Comment")
        assert result == '"Section # Comment"'

    def test_brackets(self):
        result = _yaml_quote("[array] {object}")
        assert result == '"[array] {object}"'

    def test_newlines_escaped(self):
        result = _yaml_quote("line1\nline2")
        assert "\\n" in result

    def test_quotes_escaped(self):
        result = _yaml_quote('say "hello"')
        assert '\\"' in result

    def test_unicode_preserved(self):
        result = _yaml_quote("café 日本語")
        assert "café" in result
        assert "日本語" in result


# ═══════════════════════════════════════════════════════════════════════
# _generate_config_files
# ═══════════════════════════════════════════════════════════════════════


class TestGenerateConfigFiles:
    """Tests for config file generation."""

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

    def test_returns_three_files(self, preview: AgentPreview):
        files = _generate_config_files(preview)
        assert len(files) == 3

    def test_yaml_file_path(self, preview: AgentPreview):
        files = _generate_config_files(preview)
        assert files[0]["path"] == ".github/agents/security-reviewer.yml"

    def test_prompt_file_path(self, preview: AgentPreview):
        files = _generate_config_files(preview)
        assert files[1]["path"] == ".github/agents/prompts/security-reviewer.md"

    def test_readme_file_path(self, preview: AgentPreview):
        files = _generate_config_files(preview)
        assert files[2]["path"] == ".github/agents/README.md"

    def test_yaml_uses_quoted_values(self, preview: AgentPreview):
        """YAML values should be JSON-quoted for safety."""
        files = _generate_config_files(preview)
        yaml_content = files[0]["content"]
        # Name should appear quoted
        assert '"SecurityReviewer"' in yaml_content
        assert '"In Review"' in yaml_content

    def test_yaml_special_chars_are_safe(self):
        """YAML with special characters should be properly escaped."""
        preview = AgentPreview(
            name="Test: Agent",
            slug="test-agent",
            description="Handles issues: daily # report",
            system_prompt="prompt",
            status_column="In Review",
            tools=["tool: with colon"],
        )
        files = _generate_config_files(preview)
        yaml_content = files[0]["content"]
        # Values should be quoted, not raw
        assert '"Test: Agent"' in yaml_content
        assert '"Handles issues: daily # report"' in yaml_content

    def test_prompt_file_content(self, preview: AgentPreview):
        files = _generate_config_files(preview)
        content = files[1]["content"]
        assert "# SecurityReviewer" in content
        assert "You are a security reviewer..." in content

    def test_readme_content(self, preview: AgentPreview):
        files = _generate_config_files(preview)
        content = files[2]["content"]
        assert "## SecurityReviewer" in content
        assert "Reviews PRs for security vulnerabilities" in content
        assert "In Review" in content


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

    async def test_no_admin_set_returns_false(self, seeded_db: aiosqlite.Connection):
        assert await is_admin_user(seeded_db, "12345") is False

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
