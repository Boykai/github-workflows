"""Unit tests for GitHub Copilot bot identity helpers."""

import pytest

from src.services.github_projects.identities import (
    is_copilot_author,
    is_copilot_reviewer_bot,
    is_copilot_swe_agent,
)


class TestIsCopilotAuthor:
    """Tests for is_copilot_author (substring match)."""

    @pytest.mark.parametrize(
        "login",
        [
            "copilot-swe-agent",
            "copilot-swe-agent[bot]",
            "copilot-pull-request-reviewer",
            "copilot-pull-request-reviewer[bot]",
            "some-copilot-thing",
            "Copilot",
            "COPILOT",
            "CoPiLoT-SWE-Agent[bot]",
        ],
    )
    def test_true_cases(self, login: str) -> None:
        assert is_copilot_author(login) is True

    @pytest.mark.parametrize(
        "login",
        [
            "octocat",
            "co-pilot",
            "c0pilot",
            "",
        ],
    )
    def test_false_cases(self, login: str) -> None:
        assert is_copilot_author(login) is False

    def test_none_input(self) -> None:
        assert is_copilot_author(None) is False


class TestIsCopilotSweAgent:
    """Tests for is_copilot_swe_agent (exact match after normalisation)."""

    @pytest.mark.parametrize(
        "login",
        [
            "copilot-swe-agent",
            "copilot-swe-agent[bot]",
            "Copilot-SWE-Agent",
            "Copilot-SWE-Agent[bot]",
            "COPILOT-SWE-AGENT[BOT]",
        ],
    )
    def test_true_cases(self, login: str) -> None:
        assert is_copilot_swe_agent(login) is True

    @pytest.mark.parametrize(
        "login",
        [
            "copilot-pull-request-reviewer",
            "copilot-pull-request-reviewer[bot]",
            "copilot",
            "copilot-swe-agent-extra",
            "not-copilot-swe-agent",
            "octocat",
            "",
        ],
    )
    def test_false_cases(self, login: str) -> None:
        assert is_copilot_swe_agent(login) is False

    def test_none_input(self) -> None:
        assert is_copilot_swe_agent(None) is False


class TestIsCopilotReviewerBot:
    """Tests for is_copilot_reviewer_bot (exact match after normalisation)."""

    @pytest.mark.parametrize(
        "login",
        [
            "copilot-pull-request-reviewer",
            "copilot-pull-request-reviewer[bot]",
            "Copilot-Pull-Request-Reviewer",
            "Copilot-Pull-Request-Reviewer[bot]",
            "COPILOT-PULL-REQUEST-REVIEWER[BOT]",
        ],
    )
    def test_true_cases(self, login: str) -> None:
        assert is_copilot_reviewer_bot(login) is True

    @pytest.mark.parametrize(
        "login",
        [
            "copilot-swe-agent",
            "copilot-swe-agent[bot]",
            "copilot",
            "copilot-pull-request-reviewer-extra",
            "not-copilot-pull-request-reviewer",
            "octocat",
            "",
        ],
    )
    def test_false_cases(self, login: str) -> None:
        assert is_copilot_reviewer_bot(login) is False

    def test_none_input(self) -> None:
        assert is_copilot_reviewer_bot(None) is False
