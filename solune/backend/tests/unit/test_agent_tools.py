"""Unit tests for agent function tools (src/services/agent_tools.py).

Each tool is tested with mocked runtime context (contextvars).
Covers:
- Runtime context set/get round-trip
- create_task_proposal — happy path + length truncation
- create_issue_recommendation — happy path + defaults
- update_task_status — happy path
- analyze_transcript — happy path
- ask_clarifying_question — returns question as message
- get_project_context — returns context from contextvars
- get_pipeline_list — returns placeholder
- TOOL_REGISTRY completeness
"""

from __future__ import annotations

import pytest

from src.services.agent_tools import (
    TOOL_REGISTRY,
    analyze_transcript,
    ask_clarifying_question,
    create_issue_recommendation,
    create_task_proposal,
    get_pipeline_list,
    get_project_context,
    get_runtime_context,
    set_runtime_context,
    update_task_status,
)

# ── Helpers ────────────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def _inject_test_context():
    """Set a deterministic runtime context before each test."""
    set_runtime_context(
        project_id="PVT_test",
        session_id="sess-001",
        github_token="ghp_fake",
        project_name="Test Project",
    )


# ── Runtime context ────────────────────────────────────────────────────────


class TestRuntimeContext:
    """Tests for set_runtime_context / get_runtime_context."""

    def test_round_trip(self):
        set_runtime_context(
            project_id="PVT_42",
            session_id="sess-42",
            github_token="tok-42",
            project_name="Proj42",
        )
        ctx = get_runtime_context()
        assert ctx["project_id"] == "PVT_42"
        assert ctx["session_id"] == "sess-42"
        assert ctx["github_token"] == "tok-42"
        assert ctx["project_name"] == "Proj42"

    def test_defaults_when_not_set(self):
        """get_runtime_context returns safe defaults for optional fields."""
        # github_token defaults to None, project_name defaults to "Unknown Project"
        set_runtime_context(project_id="PVT_1", session_id="s1")
        ctx = get_runtime_context()
        assert ctx["github_token"] is None
        assert ctx["project_name"] == "Unknown Project"


# ── create_task_proposal ───────────────────────────────────────────────────


class TestCreateTaskProposal:
    async def test_happy_path(self):
        result = await create_task_proposal("Fix login bug", "Detailed steps to fix login.")
        assert result["action_type"] == "task_create"
        assert result["title"] == "Fix login bug"
        assert result["description"] == "Detailed steps to fix login."
        assert "Fix login bug" in result["message"]

    async def test_title_truncation(self):
        long_title = "A" * 300
        result = await create_task_proposal(long_title, "desc")
        assert len(result["title"]) == 256
        assert result["title"].endswith("...")

    async def test_description_truncation(self):
        long_desc = "B" * 70000
        result = await create_task_proposal("title", long_desc)
        assert len(result["description"]) == 65535
        assert result["description"].endswith("...")

    async def test_empty_inputs(self):
        result = await create_task_proposal("", "")
        assert result["action_type"] == "task_create"
        assert result["title"] == ""
        assert result["description"] == ""


# ── create_issue_recommendation ────────────────────────────────────────────


class TestCreateIssueRecommendation:
    async def test_happy_path(self):
        result = await create_issue_recommendation(
            title="Add dark mode",
            user_story="As a user I want dark mode so that I can use the app at night",
            functional_requirements=["System MUST toggle theme"],
            priority="P1",
            size="M",
        )
        assert result["action_type"] == "issue_create"
        assert result["title"] == "Add dark mode"
        assert result["priority"] == "P1"
        assert result["size"] == "M"
        assert len(result["functional_requirements"]) == 1

    async def test_defaults(self):
        result = await create_issue_recommendation(
            title="Minimal issue",
            user_story="As a dev I want this",
        )
        assert result["priority"] == "P2"
        assert result["size"] == "M"
        assert result["ui_ux_description"] == "No UI/UX description provided."
        assert result["functional_requirements"] == []

    async def test_title_truncation(self):
        long_title = "C" * 300
        result = await create_issue_recommendation(title=long_title, user_story="story")
        assert len(result["title"]) == 256
        assert result["title"].endswith("...")

    async def test_priority_uppercased(self):
        result = await create_issue_recommendation(
            title="t", user_story="s", priority="p3", size="xl"
        )
        assert result["priority"] == "P3"
        assert result["size"] == "XL"


# ── update_task_status ─────────────────────────────────────────────────────


class TestUpdateTaskStatus:
    async def test_happy_path(self):
        result = await update_task_status("Fix login bug", "In Progress")
        assert result["action_type"] == "status_update"
        assert result["task_reference"] == "Fix login bug"
        assert result["target_status"] == "In Progress"

    async def test_message_contains_reference(self):
        result = await update_task_status("auth task", "Done")
        assert "auth task" in result["message"]
        assert "Done" in result["message"]


# ── analyze_transcript ─────────────────────────────────────────────────────


class TestAnalyzeTranscript:
    async def test_happy_path(self):
        transcript = "Speaker A: We need dark mode\nSpeaker B: Agreed"
        result = await analyze_transcript(transcript)
        assert result["action_type"] == "issue_create"
        assert result["transcript_length"] == len(transcript)

    async def test_empty_transcript(self):
        result = await analyze_transcript("")
        assert result["transcript_length"] == 0


# ── ask_clarifying_question ────────────────────────────────────────────────


class TestAskClarifyingQuestion:
    async def test_returns_question(self):
        result = await ask_clarifying_question("What framework are you using?")
        assert result["action_type"] is None
        assert result["message"] == "What framework are you using?"


# ── get_project_context ────────────────────────────────────────────────────


class TestGetProjectContext:
    async def test_returns_context(self):
        result = await get_project_context()
        assert result["project_id"] == "PVT_test"
        assert result["project_name"] == "Test Project"


# ── get_pipeline_list ──────────────────────────────────────────────────────


class TestGetPipelineList:
    async def test_returns_placeholder(self):
        result = await get_pipeline_list()
        assert result["project_id"] == "PVT_test"
        assert isinstance(result["pipelines"], list)


# ── TOOL_REGISTRY ──────────────────────────────────────────────────────────


class TestToolRegistry:
    def test_all_tools_registered(self):
        expected = {
            "create_task_proposal",
            "create_issue_recommendation",
            "update_task_status",
            "analyze_transcript",
            "ask_clarifying_question",
            "get_project_context",
            "get_pipeline_list",
        }
        assert set(TOOL_REGISTRY.keys()) == expected

    def test_all_values_callable(self):
        for name, fn in TOOL_REGISTRY.items():
            assert callable(fn), f"{name} is not callable"
