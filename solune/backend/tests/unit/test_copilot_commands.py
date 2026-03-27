"""Unit tests for copilot_commands service."""

from unittest.mock import AsyncMock, patch

import pytest

from src.services.copilot_commands import (
    COPILOT_COMMAND_PROMPTS,
    COPILOT_COMMANDS,
    execute_copilot_command,
    is_copilot_command,
)

# ═══════════════════════════════════════════════════════════════════════════
# is_copilot_command
# ═══════════════════════════════════════════════════════════════════════════


class TestIsCopilotCommand:
    """Tests for detecting and parsing Copilot slash commands."""

    @pytest.mark.parametrize(
        "cmd",
        sorted(COPILOT_COMMANDS),
    )
    def test_detects_all_nine_commands(self, cmd: str):
        result = is_copilot_command(f"/{cmd} some args")
        assert result is not None
        assert result[0] == cmd

    @pytest.mark.parametrize(
        "cmd",
        sorted(COPILOT_COMMANDS),
    )
    def test_case_insensitive(self, cmd: str):
        result = is_copilot_command(f"/{cmd.upper()} args")
        assert result is not None
        assert result[0] == cmd

    def test_extracts_arguments(self):
        result = is_copilot_command("/explain What is a closure?")
        assert result == ("explain", "What is a closure?")

    def test_empty_args(self):
        result = is_copilot_command("/fix")
        assert result == ("fix", "")

    def test_strips_whitespace(self):
        result = is_copilot_command("  /explain   some code  ")
        assert result is not None
        assert result[0] == "explain"
        assert result[1] == "some code"

    def test_rejects_non_copilot_command(self):
        assert is_copilot_command("/help") is None

    def test_rejects_plain_text(self):
        assert is_copilot_command("explain something") is None

    def test_rejects_empty_string(self):
        assert is_copilot_command("") is None

    def test_rejects_agent_command(self):
        assert is_copilot_command("/agent create bot") is None

    def test_rejects_plan_command(self):
        assert is_copilot_command("/plan build a feature") is None

    def test_multiline_args(self):
        result = is_copilot_command("/explain line 1\nline 2")
        assert result is not None
        assert result[0] == "explain"
        assert "line 1\nline 2" in result[1]


# ═══════════════════════════════════════════════════════════════════════════
# COPILOT_COMMAND_PROMPTS
# ═══════════════════════════════════════════════════════════════════════════


class TestCopilotCommandPrompts:
    """Verify each command has a unique, non-empty system prompt."""

    def test_all_commands_have_prompts(self):
        for cmd in COPILOT_COMMANDS:
            assert cmd in COPILOT_COMMAND_PROMPTS, f"Missing prompt for /{cmd}"
            assert len(COPILOT_COMMAND_PROMPTS[cmd]) > 0

    def test_no_extra_prompts(self):
        assert set(COPILOT_COMMAND_PROMPTS.keys()) == COPILOT_COMMANDS

    def test_prompts_are_distinct(self):
        prompts = list(COPILOT_COMMAND_PROMPTS.values())
        assert len(set(prompts)) == len(prompts), "Duplicate prompts detected"


# ═══════════════════════════════════════════════════════════════════════════
# execute_copilot_command
# ═══════════════════════════════════════════════════════════════════════════


class TestExecuteCopilotCommand:
    """Tests for command execution via CopilotCompletionProvider."""

    @pytest.mark.asyncio
    async def test_calls_provider_with_correct_prompt(self):
        mock_provider = AsyncMock()
        mock_provider.complete.return_value = "Here is the explanation."

        with patch(
            "src.services.completion_providers.CopilotCompletionProvider",
            return_value=mock_provider,
        ):
            result = await execute_copilot_command("explain", "What is a closure?", "gh_token")

        assert result == "Here is the explanation."
        mock_provider.complete.assert_called_once()
        call_args = mock_provider.complete.call_args
        messages = call_args[0][0]
        assert messages[0]["role"] == "system"
        assert messages[0]["content"] == COPILOT_COMMAND_PROMPTS["explain"]
        assert messages[1]["role"] == "user"
        assert messages[1]["content"] == "What is a closure?"
        assert call_args[1]["github_token"] == "gh_token"

    @pytest.mark.asyncio
    async def test_empty_args_uses_command_as_content(self):
        mock_provider = AsyncMock()
        mock_provider.complete.return_value = "Response"

        with patch(
            "src.services.completion_providers.CopilotCompletionProvider",
            return_value=mock_provider,
        ):
            await execute_copilot_command("fix", "", "gh_token")

        call_args = mock_provider.complete.call_args
        messages = call_args[0][0]
        assert messages[1]["content"] == "/fix"

    @pytest.mark.asyncio
    async def test_handles_provider_error_gracefully(self):
        mock_provider = AsyncMock()
        mock_provider.complete.side_effect = RuntimeError("Network error")

        with patch(
            "src.services.completion_providers.CopilotCompletionProvider",
            return_value=mock_provider,
        ):
            result = await execute_copilot_command("explain", "test", "gh_token")

        assert "Error" in result
        assert "/explain" in result

    @pytest.mark.asyncio
    async def test_unknown_command_returns_error(self):
        result = await execute_copilot_command("nonexistent", "args", "gh_token")
        assert "Unknown Copilot command" in result
