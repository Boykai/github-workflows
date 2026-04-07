"""Tests for agent tools (src/services/agent_tools.py).

Each tool is tested with mocked runtime context via ``set_runtime_context``.
"""

import json

from src.services.agent_tools import (
    ALL_TOOLS,
    analyze_transcript,
    ask_clarifying_question,
    create_issue_recommendation,
    create_task_proposal,
    get_project_context,
    get_runtime_context,
    set_runtime_context,
    update_task_status,
)

# ── Runtime context helpers ────────────────────────────────────────────────


class TestRuntimeContext:
    def test_default_context_is_empty(self):
        # Reset by setting to None-like
        set_runtime_context({})
        ctx = get_runtime_context()
        assert ctx == {}

    def test_set_and_get_context(self):
        set_runtime_context({"project_name": "TestProject", "session_id": "abc"})
        ctx = get_runtime_context()
        assert ctx["project_name"] == "TestProject"
        assert ctx["session_id"] == "abc"


# ── create_task_proposal ──────────────────────────────────────────────────


class TestCreateTaskProposal:
    async def test_creates_task_proposal(self):
        set_runtime_context({"project_name": "MyProject"})
        result = await create_task_proposal.func(
            title="Fix login bug",
            description="Fix the authentication flow",
        )
        data = json.loads(result)
        assert data["action_type"] == "task_create"
        assert data["proposed_title"] == "Fix login bug"
        assert data["proposed_description"] == "Fix the authentication flow"
        assert data["project_name"] == "MyProject"

    async def test_truncates_long_title(self):
        set_runtime_context({"project_name": "P"})
        result = await create_task_proposal.func(
            title="A" * 300,
            description="desc",
        )
        data = json.loads(result)
        assert len(data["proposed_title"]) == 256

    async def test_uses_default_project_name(self):
        set_runtime_context({})
        result = await create_task_proposal.func(title="T", description="D")
        data = json.loads(result)
        assert data["project_name"] == "Unknown"


# ── create_issue_recommendation ────────────────────────────────────────────


class TestCreateIssueRecommendation:
    async def test_creates_recommendation(self):
        set_runtime_context({"project_name": "MyProject", "session_id": "00000000-0000-0000-0000-000000000001"})
        result = await create_issue_recommendation.func(
            title="Add dark mode",
            user_story="As a user I want dark mode so I can work at night",
            functional_requirements="Toggle in settings, Persist preference",
        )
        data = json.loads(result)
        assert data["action_type"] == "issue_create"
        assert "recommendation" in data
        rec = data["recommendation"]
        assert rec["title"] == "Add dark mode"
        assert len(rec["functional_requirements"]) == 2
        assert "Toggle in settings" in rec["functional_requirements"]

    async def test_handles_single_requirement(self):
        set_runtime_context({"project_name": "P", "session_id": ""})
        result = await create_issue_recommendation.func(
            title="Fix bug",
            user_story="story",
            functional_requirements="Single requirement",
        )
        data = json.loads(result)
        rec = data["recommendation"]
        assert rec["functional_requirements"] == ["Single requirement"]

    async def test_normalizes_priority_and_size(self):
        set_runtime_context({"project_name": "P", "session_id": ""})
        result = await create_issue_recommendation.func(
            title="T",
            user_story="S",
            functional_requirements="R",
            priority="p0",
            size="xl",
        )
        data = json.loads(result)
        rec = data["recommendation"]
        assert rec["metadata"]["priority"] == "P0"
        assert rec["metadata"]["size"] == "XL"

    async def test_invalid_priority_defaults_to_p2(self):
        set_runtime_context({"project_name": "P", "session_id": ""})
        result = await create_issue_recommendation.func(
            title="T",
            user_story="S",
            functional_requirements="R",
            priority="invalid",
        )
        data = json.loads(result)
        assert data["recommendation"]["metadata"]["priority"] == "P2"

    async def test_invalid_size_defaults_to_m(self):
        set_runtime_context({"project_name": "P", "session_id": ""})
        result = await create_issue_recommendation.func(
            title="T",
            user_story="S",
            functional_requirements="R",
            size="HUGE",
        )
        data = json.loads(result)
        assert data["recommendation"]["metadata"]["size"] == "M"


# ── update_task_status ────────────────────────────────────────────────────


class TestUpdateTaskStatus:
    async def test_creates_status_update(self):
        result = await update_task_status.func(
            task_reference="Fix login bug",
            target_status="Done",
        )
        data = json.loads(result)
        assert data["action_type"] == "status_update"
        assert data["task_reference"] == "Fix login bug"
        assert data["target_status"] == "Done"


# ── analyze_transcript ────────────────────────────────────────────────────


class TestAnalyzeTranscript:
    async def test_analyzes_transcript(self):
        set_runtime_context({"project_name": "MyProject"})
        result = await analyze_transcript.func(
            transcript_content="Speaker 1: We need to add dark mode",
        )
        data = json.loads(result)
        assert data["action_type"] == "issue_create"
        assert data["source"] == "transcript"
        assert data["transcript_length"] > 0
        assert data["project_name"] == "MyProject"


# ── ask_clarifying_question ───────────────────────────────────────────────


class TestAskClarifyingQuestion:
    async def test_asks_question(self):
        result = await ask_clarifying_question.func(
            question="What framework are you using?",
        )
        data = json.loads(result)
        assert data["action_type"] == "clarification"
        assert data["question"] == "What framework are you using?"


# ── get_project_context ───────────────────────────────────────────────────


class TestGetProjectContext:
    async def test_returns_project_info(self):
        set_runtime_context({"project_name": "MyProject", "project_id": "PVT_123"})
        result = await get_project_context.func()
        data = json.loads(result)
        assert data["project_name"] == "MyProject"
        assert data["project_id"] == "PVT_123"

    async def test_defaults_when_no_context(self):
        set_runtime_context({})
        result = await get_project_context.func()
        data = json.loads(result)
        assert data["project_name"] == "Unknown"
        assert data["project_id"] == ""


# ── ALL_TOOLS registry ────────────────────────────────────────────────────


class TestToolRegistry:
    def test_all_tools_list(self):
        assert len(ALL_TOOLS) == 6

    def test_all_tools_have_names(self):
        expected_names = {
            "create_task_proposal",
            "create_issue_recommendation",
            "update_task_status",
            "analyze_transcript",
            "ask_clarifying_question",
            "get_project_context",
        }
        actual_names = {t.name for t in ALL_TOOLS}
        assert actual_names == expected_names
