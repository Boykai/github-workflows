"""Unit tests for agent instructions (src/prompts/agent_instructions.py).

Covers:
- AGENT_SYSTEM_INSTRUCTIONS content sanity checks
- get_agent_instructions() with and without project context
"""

from __future__ import annotations

from src.prompts.agent_instructions import AGENT_SYSTEM_INSTRUCTIONS, get_agent_instructions


class TestAgentSystemInstructions:
    def test_not_empty(self):
        assert len(AGENT_SYSTEM_INSTRUCTIONS) > 100

    def test_mentions_tools(self):
        assert "create_task_proposal" in AGENT_SYSTEM_INSTRUCTIONS
        assert "create_issue_recommendation" in AGENT_SYSTEM_INSTRUCTIONS
        assert "update_task_status" in AGENT_SYSTEM_INSTRUCTIONS
        assert "analyze_transcript" in AGENT_SYSTEM_INSTRUCTIONS
        assert "ask_clarifying_question" in AGENT_SYSTEM_INSTRUCTIONS

    def test_mentions_priorities(self):
        assert "P0" in AGENT_SYSTEM_INSTRUCTIONS
        assert "P3" in AGENT_SYSTEM_INSTRUCTIONS


class TestGetAgentInstructions:
    def test_without_project(self):
        instructions = get_agent_instructions()
        assert "create_task_proposal" in instructions
        # Should NOT contain project section
        assert "Active project" not in instructions

    def test_with_project(self):
        instructions = get_agent_instructions(project_name="My App")
        assert "My App" in instructions
        assert "Active project" in instructions

    def test_none_project_same_as_no_project(self):
        i1 = get_agent_instructions()
        i2 = get_agent_instructions(project_name=None)
        assert i1 == i2
