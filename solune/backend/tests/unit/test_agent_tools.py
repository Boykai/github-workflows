"""Tests for agent function tools (src/services/agent_tools.py).

Each tool is tested with a mock tool_context dict that simulates the
runtime context injected by ChatAgentService.
"""

from unittest.mock import AsyncMock, MagicMock

# ── create_task_proposal ────────────────────────────────────────────────


class TestCreateTaskProposal:
    async def test_returns_task_create_action(self):
        from src.services.agent_tools import create_task_proposal

        result = await create_task_proposal(
            title="Add dark mode",
            description="Implement dark mode toggle in settings",
        )
        assert result["action_type"] == "task_create"
        assert result["action_data"]["proposed_title"] == "Add dark mode"
        assert (
            "description" in result["action_data"]["proposed_description"].lower()
            or result["action_data"]["proposed_description"]
        )

    async def test_truncates_long_title(self):
        from src.services.agent_tools import create_task_proposal

        long_title = "A" * 120
        result = await create_task_proposal(title=long_title, description="desc")
        assert len(result["action_data"]["proposed_title"]) <= 100

    async def test_includes_pipeline_from_context(self):
        from src.services.agent_tools import create_task_proposal

        result = await create_task_proposal(
            title="Test",
            description="Desc",
            tool_context={"pipeline_id": "pipe-123"},
        )
        assert result["action_data"]["pipeline_id"] == "pipe-123"

    async def test_uses_ai_service_when_description_missing(self):
        from src.services.agent_tools import create_task_proposal

        mock_ai = AsyncMock()
        mock_ai.generate_task_from_description.return_value = MagicMock(
            title="AI Title", description="AI Description"
        )

        result = await create_task_proposal(
            title="Quick task",
            description="",
            tool_context={"ai_service": mock_ai, "github_token": "tok"},
        )
        assert result["action_type"] == "task_create"

    async def test_message_contains_confirm_prompt(self):
        from src.services.agent_tools import create_task_proposal

        result = await create_task_proposal(title="Test", description="Desc")
        assert "confirm" in result["message"].lower()


# ── create_issue_recommendation ─────────────────────────────────────────


class TestCreateIssueRecommendation:
    async def test_returns_issue_create_action(self):
        from src.services.agent_tools import create_issue_recommendation

        result = await create_issue_recommendation(
            title="Add PDF export",
            user_story="As a user I want PDF export",
            functional_requirements=["System MUST export to PDF"],
        )
        assert result["action_type"] == "issue_create"
        assert result["action_data"]["proposed_title"] == "Add PDF export"
        assert "user_story" in result["action_data"]

    async def test_truncates_long_title(self):
        from src.services.agent_tools import create_issue_recommendation

        result = await create_issue_recommendation(
            title="X" * 300,
            user_story="Story",
        )
        assert len(result["action_data"]["proposed_title"]) <= 256

    async def test_default_ui_description(self):
        from src.services.agent_tools import create_issue_recommendation

        result = await create_issue_recommendation(title="Test", user_story="Story")
        assert result["action_data"]["ui_ux_description"] == "No UI/UX description provided."


# ── update_task_status ──────────────────────────────────────────────────


class TestUpdateTaskStatus:
    async def test_task_not_found(self):
        from src.services.agent_tools import update_task_status

        mock_ai = MagicMock()
        mock_ai.identify_target_task.return_value = None

        result = await update_task_status(
            task_reference="nonexistent",
            target_status="Done",
            tool_context={"ai_service": mock_ai, "current_tasks": []},
        )
        assert "couldn't find" in result["message"].lower()
        assert result["action_type"] == ""

    async def test_task_found(self):
        from src.services.agent_tools import update_task_status

        mock_task = MagicMock()
        mock_task.title = "Fix login"
        mock_task.status = "In Progress"
        mock_task.github_item_id = "PVTI_1"

        mock_ai = MagicMock()
        mock_ai.identify_target_task.return_value = mock_task

        result = await update_task_status(
            task_reference="login",
            target_status="Done",
            tool_context={
                "ai_service": mock_ai,
                "current_tasks": [mock_task],
                "project_columns": ["Todo", "In Progress", "Done"],
            },
        )
        assert result["action_type"] == "status_update"
        assert result["action_data"]["task_title"] == "Fix login"
        assert result["action_data"]["target_status"] == "Done"


# ── analyze_transcript ──────────────────────────────────────────────────


class TestAnalyzeTranscript:
    async def test_no_ai_service(self):
        from src.services.agent_tools import analyze_transcript

        result = await analyze_transcript(
            transcript_content="Some text",
            tool_context={},
        )
        assert "not available" in result["message"].lower()

    async def test_successful_analysis(self):
        from src.services.agent_tools import analyze_transcript

        mock_rec = MagicMock()
        mock_rec.recommendation_id = "rec-123"
        mock_rec.title = "Feature from transcript"
        mock_rec.user_story = "As a user..."
        mock_rec.original_context = "Full transcript"
        mock_rec.ui_ux_description = "UI description"
        mock_rec.functional_requirements = ["System MUST do X"]
        mock_rec.technical_notes = "Use React"

        mock_ai = AsyncMock()
        mock_ai.analyze_transcript.return_value = mock_rec

        result = await analyze_transcript(
            transcript_content="Meeting transcript text",
            tool_context={
                "ai_service": mock_ai,
                "github_token": "tok",
                "project_name": "Test Project",
                "session_id": "sess-1",
            },
        )
        assert result["action_type"] == "issue_create"
        assert "Feature from transcript" in result["message"]

    async def test_analysis_error_handled(self):
        from src.services.agent_tools import analyze_transcript

        mock_ai = AsyncMock()
        mock_ai.analyze_transcript.side_effect = RuntimeError("API down")

        result = await analyze_transcript(
            transcript_content="Some text",
            tool_context={"ai_service": mock_ai, "github_token": "tok"},
        )
        assert "couldn't extract" in result["message"].lower()


# ── ask_clarifying_question ─────────────────────────────────────────────


class TestAskClarifyingQuestion:
    async def test_returns_question_as_message(self):
        from src.services.agent_tools import ask_clarifying_question

        result = await ask_clarifying_question(question="What tech stack are you using?")
        assert result["message"] == "What tech stack are you using?"
        assert result["action_type"] == ""


# ── get_project_context ─────────────────────────────────────────────────


class TestGetProjectContext:
    async def test_returns_project_info(self):
        from src.services.agent_tools import get_project_context

        mock_task = MagicMock()
        mock_task.title = "Task 1"
        mock_task.status = "Todo"

        result = await get_project_context(
            tool_context={
                "project_name": "My Project",
                "project_columns": ["Todo", "Done"],
                "current_tasks": [mock_task],
            },
        )
        assert "My Project" in result["message"]

    async def test_empty_context(self):
        from src.services.agent_tools import get_project_context

        result = await get_project_context(tool_context={})
        assert "Unknown Project" in result["message"]


# ── get_pipeline_list ───────────────────────────────────────────────────


class TestGetPipelineList:
    async def test_no_pipelines_available(self):
        from src.services.agent_tools import get_pipeline_list

        result = await get_pipeline_list(tool_context={})
        # Should gracefully handle missing pipeline service
        assert result["action_type"] == ""
