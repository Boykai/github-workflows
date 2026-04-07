"""Tests for agent instructions (src/prompts/agent_instructions.py).

Verifies that the system instructions contain required components
and that build_agent_instructions correctly injects project context.

v0.2.0 — Intelligent Chat Agent (Microsoft Agent Framework)
"""

from src.prompts.agent_instructions import (
    AGENT_SYSTEM_INSTRUCTIONS,
    build_agent_instructions,
)


class TestAgentSystemInstructions:
    """Verify the static system instructions contain required components."""

    def test_mentions_clarifying_questions(self):
        assert "clarifying" in AGENT_SYSTEM_INSTRUCTIONS.lower()

    def test_mentions_tools(self):
        assert "create_task_proposal" in AGENT_SYSTEM_INSTRUCTIONS
        assert "create_issue_recommendation" in AGENT_SYSTEM_INSTRUCTIONS
        assert "update_task_status" in AGENT_SYSTEM_INSTRUCTIONS
        assert "analyze_transcript" in AGENT_SYSTEM_INSTRUCTIONS
        assert "ask_clarifying_question" in AGENT_SYSTEM_INSTRUCTIONS
        assert "get_project_context" in AGENT_SYSTEM_INSTRUCTIONS
        assert "get_pipeline_list" in AGENT_SYSTEM_INSTRUCTIONS

    def test_mentions_difficulty_assessment(self):
        assert "XS" in AGENT_SYSTEM_INSTRUCTIONS
        assert "XL" in AGENT_SYSTEM_INSTRUCTIONS

    def test_mentions_confirm_reject(self):
        assert "Confirm" in AGENT_SYSTEM_INSTRUCTIONS
        assert "Reject" in AGENT_SYSTEM_INSTRUCTIONS


class TestBuildAgentInstructions:
    def test_no_context_returns_base_instructions(self):
        result = build_agent_instructions()
        assert result == AGENT_SYSTEM_INSTRUCTIONS

    def test_with_project_name(self):
        result = build_agent_instructions(project_name="Solune Dashboard")
        assert "Solune Dashboard" in result
        assert "Current Project" in result

    def test_with_project_columns(self):
        result = build_agent_instructions(project_columns=["Todo", "In Progress", "Done"])
        assert "Todo" in result
        assert "In Progress" in result
        assert "Done" in result
        assert "Available status columns" in result

    def test_with_both_project_and_columns(self):
        result = build_agent_instructions(
            project_name="My Project",
            project_columns=["Backlog", "Active"],
        )
        assert "My Project" in result
        assert "Backlog" in result
        assert "Active" in result

    def test_none_project_name_excluded(self):
        result = build_agent_instructions(project_name=None)
        assert "Current Project" not in result

    def test_empty_columns_excluded(self):
        result = build_agent_instructions(project_columns=[])
        assert "Available status columns" not in result
