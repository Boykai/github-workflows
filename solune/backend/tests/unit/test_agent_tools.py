"""Tests for agent function tools (src/services/agent_tools.py).

Each tool is tested with the runtime context set via contextvars,
verifying that tools correctly access context and return structured
dicts for the confirm/reject flow.

v0.2.0 — Intelligent Chat Agent (Microsoft Agent Framework)
"""

import pytest

from src.services.agent_tools import (
    RuntimeContext,
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

# ── Runtime context helpers ──────────────────────────────────────────────


def _make_context(**overrides) -> RuntimeContext:
    """Build a RuntimeContext with sensible defaults."""
    defaults = {
        "project_id": "PVT_test_123",
        "session_id": "sess-abc-123",
        "github_token": "ghp_test_token",
        "project_name": "Test Project",
        "metadata_context": None,
    }
    defaults.update(overrides)
    return RuntimeContext(**defaults)


# ── RuntimeContext round-trip ────────────────────────────────────────────


class TestRuntimeContext:
    """Verify set/get round-trip for the contextvars-based runtime context."""

    def test_set_and_get_context(self):
        ctx = _make_context()
        set_runtime_context(ctx)
        retrieved = get_runtime_context()

        assert retrieved.project_id == ctx.project_id
        assert retrieved.session_id == ctx.session_id
        assert retrieved.github_token == ctx.github_token
        assert retrieved.project_name == ctx.project_name
        assert retrieved.metadata_context is None

    def test_context_with_metadata(self):
        metadata = {"labels": [{"name": "bug"}], "branches": ["main"]}
        ctx = _make_context(metadata_context=metadata)
        set_runtime_context(ctx)
        retrieved = get_runtime_context()

        assert retrieved.metadata_context == metadata

    def test_context_overwrite(self):
        """Setting context twice replaces the previous values."""
        set_runtime_context(_make_context(project_id="first"))
        set_runtime_context(_make_context(project_id="second"))
        assert get_runtime_context().project_id == "second"

    def test_context_without_github_token(self):
        ctx = _make_context(github_token=None)
        set_runtime_context(ctx)
        assert get_runtime_context().github_token is None


# ── create_task_proposal ─────────────────────────────────────────────────


class TestCreateTaskProposal:
    @pytest.fixture(autouse=True)
    def _set_ctx(self):
        set_runtime_context(_make_context())

    async def test_returns_task_create_action(self):
        result = await create_task_proposal("Fix login bug", "The login flow is broken")

        assert result["action"] == "task_create"
        assert result["title"] == "Fix login bug"
        assert result["description"] == "The login flow is broken"

    async def test_includes_project_and_session(self):
        result = await create_task_proposal("T", "D")

        assert result["project_id"] == "PVT_test_123"
        assert result["session_id"] == "sess-abc-123"

    async def test_empty_title(self):
        result = await create_task_proposal("", "Some description")
        assert result["title"] == ""

    async def test_long_description(self):
        long_desc = "x" * 10_000
        result = await create_task_proposal("Title", long_desc)
        assert result["description"] == long_desc


# ── create_issue_recommendation ──────────────────────────────────────────


class TestCreateIssueRecommendation:
    @pytest.fixture(autouse=True)
    def _set_ctx(self):
        set_runtime_context(_make_context())

    async def test_returns_issue_create_action(self):
        result = await create_issue_recommendation(
            title="Add dark mode",
            user_story="As a user I want dark mode",
        )

        assert result["action"] == "issue_create"
        assert result["title"] == "Add dark mode"
        assert result["user_story"] == "As a user I want dark mode"

    async def test_includes_optional_fields(self):
        result = await create_issue_recommendation(
            title="Title",
            user_story="Story",
            ui_ux_description="Toggle in header",
            functional_requirements=["FR-1", "FR-2"],
            technical_notes="Use CSS variables",
        )

        assert result["ui_ux_description"] == "Toggle in header"
        assert result["functional_requirements"] == ["FR-1", "FR-2"]
        assert result["technical_notes"] == "Use CSS variables"

    async def test_default_optional_fields(self):
        result = await create_issue_recommendation(title="T", user_story="S")

        assert result["ui_ux_description"] == ""
        assert result["functional_requirements"] == []
        assert result["technical_notes"] == ""

    async def test_includes_project_and_session(self):
        result = await create_issue_recommendation(title="T", user_story="S")
        assert result["project_id"] == "PVT_test_123"
        assert result["session_id"] == "sess-abc-123"


# ── update_task_status ───────────────────────────────────────────────────


class TestUpdateTaskStatus:
    @pytest.fixture(autouse=True)
    def _set_ctx(self):
        set_runtime_context(_make_context())

    async def test_returns_status_update_action(self):
        result = await update_task_status("login bug", "Done")

        assert result["action"] == "status_update"
        assert result["task_reference"] == "login bug"
        assert result["target_status"] == "Done"

    async def test_includes_project_and_session(self):
        result = await update_task_status("ref", "In Progress")
        assert result["project_id"] == "PVT_test_123"
        assert result["session_id"] == "sess-abc-123"

    async def test_empty_reference(self):
        result = await update_task_status("", "Done")
        assert result["task_reference"] == ""


# ── analyze_transcript ───────────────────────────────────────────────────


class TestAnalyzeTranscript:
    @pytest.fixture(autouse=True)
    def _set_ctx(self):
        set_runtime_context(_make_context())

    async def test_returns_issue_create_action(self):
        transcript = "Alice: We need dark mode. Bob: Agreed."
        result = await analyze_transcript(transcript)

        assert result["action"] == "issue_create"
        assert result["transcript_length"] == len(transcript)

    async def test_includes_project(self):
        result = await analyze_transcript("transcript content")
        assert result["project_id"] == "PVT_test_123"

    async def test_empty_transcript(self):
        result = await analyze_transcript("")
        assert result["transcript_length"] == 0


# ── ask_clarifying_question ──────────────────────────────────────────────


class TestAskClarifyingQuestion:
    async def test_returns_clarify_action(self):
        result = await ask_clarifying_question("What framework are you using?")

        assert result["action"] == "clarify"
        assert result["question"] == "What framework are you using?"

    async def test_does_not_require_context(self):
        """ask_clarifying_question should not need runtime context."""
        result = await ask_clarifying_question("Could you elaborate?")
        assert result["action"] == "clarify"


# ── get_project_context ──────────────────────────────────────────────────


class TestGetProjectContext:
    @pytest.fixture(autouse=True)
    def _set_ctx(self):
        set_runtime_context(_make_context(project_name="My Project"))

    async def test_returns_project_info(self):
        result = await get_project_context()

        assert result["project_id"] == "PVT_test_123"
        assert result["project_name"] == "My Project"


# ── get_pipeline_list ────────────────────────────────────────────────────


class TestGetPipelineList:
    @pytest.fixture(autouse=True)
    def _set_ctx(self):
        set_runtime_context(_make_context())

    async def test_returns_pipeline_info(self):
        result = await get_pipeline_list()

        assert result["project_id"] == "PVT_test_123"
        assert isinstance(result["pipelines"], list)
