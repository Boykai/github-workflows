"""Unit tests for Copilot PR polling service."""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from src.constants import cache_key_issue_pr
from src.services.copilot_polling import (
    _advance_pipeline,
    _check_agent_done_on_parent,
    _check_agent_done_on_sub_or_parent,
    _check_child_pr_completion,
    _check_copilot_review_done,
    _check_main_pr_completion,
    _claimed_child_prs,
    _close_completed_sub_issues,
    _discover_main_pr_for_review,
    _filter_events_after,
    _find_completed_child_pr,
    _get_sub_issue_number,
    _get_tracking_state_from_issue,
    _merge_child_pr_if_applicable,
    _pending_agent_assignments,
    _poll_loop,
    _posted_agent_outputs,
    _process_pipeline_completion,
    _processed_issue_prs,
    _reconstruct_pipeline_state,
    _reconstruct_sub_issue_mappings,
    _recovery_last_attempt,
    _self_heal_tracking_table,
    _transition_after_pipeline_complete,
    _update_issue_tracking,
    _validate_and_reconcile_tracking_table,
    check_backlog_issues,
    check_in_progress_issues,
    check_in_review_issues,
    check_in_review_issues_for_copilot_review,
    check_issue_for_copilot_completion,
    check_ready_issues,
    ensure_copilot_review_requested,
    get_polling_status,
    is_sub_issue,
    post_agent_outputs_from_pr,
    process_in_progress_issue,
    recover_stalled_issues,
    stop_polling,
)
from src.services.copilot_polling.agent_output import _detect_completion_signals
from src.services.copilot_polling.state import (
    COPILOT_REVIEW_CONFIRMATION_DELAY_SECONDS,
    COPILOT_REVIEW_REQUEST_BUFFER_SECONDS,
    _copilot_review_first_detected,
    _copilot_review_requested_at,
)
from src.services.workflow_orchestrator import PipelineState, _issue_main_branches
from src.utils import utcnow


@pytest.fixture
def mock_task():
    """Create a mock Task object."""
    task = MagicMock()
    task.github_item_id = "PVTI_123"
    task.github_content_id = "I_123"
    task.github_issue_id = "I_123"
    task.issue_number = 42
    task.repository_owner = "test-owner"
    task.repository_name = "test-repo"
    task.title = "Test Issue"
    task.status = "In Progress"
    return task


@pytest.fixture
def mock_task_no_issue():
    """Create a mock Task without issue number."""
    task = MagicMock()
    task.github_item_id = "PVTI_456"
    task.github_content_id = None
    task.github_issue_id = None
    task.issue_number = None
    task.repository_owner = None
    task.repository_name = None
    task.title = "Draft Task"
    task.status = "In Progress"
    return task


@pytest.fixture(autouse=True)
def clear_processed_cache():
    """Clear the processed cache before each test."""
    _processed_issue_prs.clear()
    _claimed_child_prs.clear()
    yield
    _processed_issue_prs.clear()
    _claimed_child_prs.clear()


class TestIsSubIssue:
    """Tests for is_sub_issue helper that filters agent sub-issues from the polling loop."""

    def test_parent_issue_not_sub_issue(self):
        """Normal parent issues should not be detected as sub-issues."""
        task = MagicMock()
        task.title = "Conduct Deep Security Review of Solune App"
        assert is_sub_issue(task) is False

    def test_sub_issue_with_agent_prefix(self):
        """Sub-issues with [agent-name] prefix should be detected."""
        task = MagicMock()
        task.title = "[speckit.specify] Conduct Deep Security Review"
        assert is_sub_issue(task) is True

    def test_sub_issue_speckit_plan(self):
        task = MagicMock()
        task.title = "[speckit.plan] Conduct Deep Security Review"
        assert is_sub_issue(task) is True

    def test_sub_issue_copilot_review(self):
        task = MagicMock()
        task.title = "[copilot-review] Conduct Deep Security Review"
        assert is_sub_issue(task) is True

    def test_empty_title(self):
        task = MagicMock()
        task.title = ""
        assert is_sub_issue(task) is False

    def test_none_title(self):
        task = MagicMock()
        task.title = None
        assert is_sub_issue(task) is False

    def test_title_with_brackets_not_at_start(self):
        """Titles with brackets in the middle should not match."""
        task = MagicMock()
        task.title = "Fix issue with [brackets] in title"
        assert is_sub_issue(task) is False

    def test_title_with_bracket_but_no_space_after(self):
        """Pattern requires space after closing bracket."""
        task = MagicMock()
        task.title = "[tag]NoSpaceAfter"
        assert is_sub_issue(task) is False

    def test_sub_issue_label(self):
        """A task with a 'sub-issue' label is classified as a sub-issue."""
        task = MagicMock()
        task.title = "Normal Title"
        task.labels = [{"name": "sub-issue"}]
        assert is_sub_issue(task) is True


class TestGetSubIssueNumber:
    """_get_sub_issue_number looks up the sub-issue number from pipeline state."""

    def test_returns_sub_issue_number(self):
        pipeline = MagicMock()
        pipeline.agent_sub_issues = {"implement": {"number": 99}}
        assert _get_sub_issue_number(pipeline, "implement", 42) == 99

    def test_falls_back_to_parent(self):
        pipeline = MagicMock()
        pipeline.agent_sub_issues = {}
        assert _get_sub_issue_number(pipeline, "implement", 42) == 42

    def test_none_pipeline(self):
        assert _get_sub_issue_number(None, "implement", 42) == 42

    def test_missing_agent(self):
        pipeline = MagicMock()
        pipeline.agent_sub_issues = {"other-agent": {"number": 55}}
        assert _get_sub_issue_number(pipeline, "implement", 42) == 42

    def test_sub_info_without_number(self):
        pipeline = MagicMock()
        pipeline.agent_sub_issues = {"implement": {"assignee": "user1"}}
        assert _get_sub_issue_number(pipeline, "implement", 42) == 42

    """Tests for polling status retrieval."""

    def test_returns_status_dict(self):
        """Test that get_polling_status returns expected keys."""
        status = get_polling_status()

        assert "is_running" in status
        assert "last_poll_time" in status
        assert "poll_count" in status
        assert "errors_count" in status
        assert "processed_issues_count" in status


class TestCheckInProgressIssues:
    """Tests for checking in-progress issues."""

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    @patch("src.services.copilot_polling.pipeline.process_in_progress_issue")
    async def test_filters_in_progress_with_issue_numbers(
        self, mock_process, mock_service, mock_task, mock_task_no_issue
    ):
        """Test that only in-progress issues with issue numbers are processed."""
        mock_service.get_project_items = AsyncMock(return_value=[mock_task, mock_task_no_issue])
        mock_process.return_value = {"status": "success"}

        await check_in_progress_issues(
            access_token="test-token",
            project_id="PVT_123",
            owner="fallback-owner",
            repo="fallback-repo",
        )

        # Should only process the task with issue_number
        assert mock_process.call_count == 1
        call_args = mock_process.call_args
        assert call_args.kwargs["issue_number"] == 42

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    async def test_skips_non_in_progress_issues(self, mock_service, mock_task):
        """Test that issues not in 'In Progress' are skipped."""
        mock_task.status = "Done"
        mock_service.get_project_items = AsyncMock(return_value=[mock_task])

        results = await check_in_progress_issues(
            access_token="test-token",
            project_id="PVT_123",
            owner="owner",
            repo="repo",
        )

        assert len(results) == 0

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    async def test_uses_task_repo_info_over_fallback(self, mock_service, mock_task):
        """Test that task's repository info is preferred over fallback."""
        mock_service.get_project_items = AsyncMock(return_value=[mock_task])

        with patch(
            "src.services.copilot_polling.pipeline.process_in_progress_issue"
        ) as mock_process:
            mock_process.return_value = None

            await check_in_progress_issues(
                access_token="test-token",
                project_id="PVT_123",
                owner="fallback-owner",
                repo="fallback-repo",
            )

            call_args = mock_process.call_args.kwargs
            assert call_args["owner"] == "test-owner"
            assert call_args["repo"] == "test-repo"

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    @patch("src.services.copilot_polling.pipeline.process_in_progress_issue")
    async def test_uses_fallback_when_task_has_no_repo_info(
        self, mock_process, mock_service, mock_task
    ):
        """Test that fallback repo info is used when task doesn't have it."""
        mock_task.repository_owner = None
        mock_task.repository_name = None
        mock_service.get_project_items = AsyncMock(return_value=[mock_task])
        mock_process.return_value = None

        await check_in_progress_issues(
            access_token="test-token",
            project_id="PVT_123",
            owner="fallback-owner",
            repo="fallback-repo",
        )

        call_args = mock_process.call_args.kwargs
        assert call_args["owner"] == "fallback-owner"
        assert call_args["repo"] == "fallback-repo"

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    async def test_handles_case_insensitive_status(self, mock_service, mock_task):
        """Test that status comparison is case-insensitive."""
        mock_task.status = "IN PROGRESS"  # Uppercase
        mock_service.get_project_items = AsyncMock(return_value=[mock_task])

        with patch(
            "src.services.copilot_polling.pipeline.process_in_progress_issue"
        ) as mock_process:
            mock_process.return_value = None

            await check_in_progress_issues(
                access_token="test-token",
                project_id="PVT_123",
                owner="owner",
                repo="repo",
            )

            # Should still be called despite uppercase
            assert mock_process.call_count == 1

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    async def test_handles_none_status_gracefully(self, mock_service, mock_task):
        """Test that tasks with None status are skipped."""
        mock_task.status = None
        mock_service.get_project_items = AsyncMock(return_value=[mock_task])

        with patch(
            "src.services.copilot_polling.pipeline.process_in_progress_issue"
        ) as mock_process:
            await check_in_progress_issues(
                access_token="test-token",
                project_id="PVT_123",
                owner="owner",
                repo="repo",
            )

            # Should not be called
            mock_process.assert_not_called()

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    @patch("src.services.copilot_polling.pipeline.process_in_progress_issue")
    async def test_collects_all_results(self, mock_process, mock_service, mock_task):
        """Test that results from all processed issues are collected."""
        task1 = MagicMock(
            **{
                "github_item_id": "PVTI_1",
                "issue_number": 1,
                "repository_owner": "owner",
                "repository_name": "repo",
                "title": "Issue 1",
                "status": "In Progress",
            }
        )
        task2 = MagicMock(
            **{
                "github_item_id": "PVTI_2",
                "issue_number": 2,
                "repository_owner": "owner",
                "repository_name": "repo",
                "title": "Issue 2",
                "status": "In Progress",
            }
        )

        mock_service.get_project_items = AsyncMock(return_value=[task1, task2])
        mock_process.side_effect = [
            {"status": "success", "issue_number": 1},
            {"status": "success", "issue_number": 2},
        ]

        results = await check_in_progress_issues(
            access_token="test-token",
            project_id="PVT_123",
            owner="owner",
            repo="repo",
        )

        assert len(results) == 2

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    @patch("src.services.copilot_polling.pipeline.process_in_progress_issue")
    @patch("src.services.copilot_polling.get_pipeline_state")
    async def test_skips_issues_with_active_pipeline_for_other_status(
        self, mock_get_pipeline, mock_process, mock_service, mock_task
    ):
        """Issues with a pipeline for a different status should have their pipeline
        updated to 'In Progress' (accepting Copilot's status change) and then be
        handled via comment-based agent completion detection — NOT by restoring
        the old status (which would re-trigger the agent)."""
        mock_service.get_project_items = AsyncMock(return_value=[mock_task])
        # Agent has NOT completed yet
        mock_service.check_agent_completion_comment = AsyncMock(return_value=False)

        # Simulate a pipeline for Backlog status (not In Progress)
        pipeline = PipelineState(
            issue_number=42,
            project_id="PVT_123",
            status="Backlog",
            agents=["speckit.specify"],
            current_agent_index=0,
            completed_agents=[],
            started_at=utcnow(),
        )
        mock_get_pipeline.return_value = pipeline

        with patch("src.services.copilot_polling.set_pipeline_state") as mock_set_pipeline:
            results = await check_in_progress_issues(
                access_token="test-token",
                project_id="PVT_123",
                owner="owner",
                repo="repo",
            )

        # Should NOT try to restore status (that causes duplicate agent triggers)
        mock_service.update_item_status_by_name.assert_not_called()
        # Legacy process_in_progress_issue should NOT be called (pipeline path used)
        mock_process.assert_not_called()
        # Pipeline should be updated to accept the "In Progress" status
        mock_set_pipeline.assert_called_once()
        assert pipeline.status == "In Progress"
        assert len(results) == 0

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    @patch("src.services.copilot_polling.get_pipeline_state")
    async def test_processes_issues_with_in_progress_pipeline(
        self, mock_get_pipeline, mock_service, mock_task
    ):
        """Issues with an active In Progress pipeline should use comment-based detection."""
        mock_service.get_project_items = AsyncMock(return_value=[mock_task])

        # Pipeline IS for In Progress — should use comment-based detection
        mock_get_pipeline.return_value = PipelineState(
            issue_number=42,
            project_id="PVT_123",
            status="In Progress",
            agents=["speckit.implement"],
            current_agent_index=0,
            completed_agents=[],
            started_at=utcnow(),
        )

        # Agent has NOT completed yet (no Done! marker)
        mock_service.check_agent_completion_comment = AsyncMock(return_value=False)

        results = await check_in_progress_issues(
            access_token="test-token",
            project_id="PVT_123",
            owner="owner",
            repo="repo",
        )

        # Should check for completion comment, not call process_in_progress_issue
        mock_service.check_agent_completion_comment.assert_called_once_with(
            access_token="test-token",
            owner="test-owner",
            repo="test-repo",
            issue_number=42,
            agent_name="speckit.implement",
        )
        assert len(results) == 0

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    @patch("src.services.copilot_polling.pipeline.process_in_progress_issue")
    @patch("src.services.copilot_polling.get_pipeline_state")
    async def test_processes_issues_with_completed_pipeline(
        self, mock_get_pipeline, mock_process, mock_service, mock_task
    ):
        """Issues with a completed pipeline (any status) should be processed normally."""
        mock_service.get_project_items = AsyncMock(return_value=[mock_task])
        mock_process.return_value = {"status": "success"}

        # Pipeline is complete (current_agent_index >= len(agents))
        mock_get_pipeline.return_value = PipelineState(
            issue_number=42,
            project_id="PVT_123",
            status="Backlog",
            agents=["speckit.specify"],
            current_agent_index=1,  # At end
            completed_agents=["speckit.specify"],
            started_at=utcnow(),
        )

        results = await check_in_progress_issues(
            access_token="test-token",
            project_id="PVT_123",
            owner="owner",
            repo="repo",
        )

        mock_process.assert_called_once()
        assert len(results) == 1

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    @patch("src.services.copilot_polling.pipeline.process_in_progress_issue")
    @patch("src.services.copilot_polling.get_pipeline_state")
    @patch("src.services.copilot_polling.get_workflow_config", new_callable=AsyncMock)
    @patch(
        "src.services.copilot_polling.pipeline._get_or_reconstruct_pipeline", new_callable=AsyncMock
    )
    @patch(
        "src.services.copilot_polling.pipeline._process_pipeline_completion", new_callable=AsyncMock
    )
    async def test_reconstructs_pipeline_when_in_memory_state_lost(
        self,
        mock_process_completion,
        mock_reconstruct,
        mock_config,
        mock_get_pipeline,
        mock_process,
        mock_service,
        mock_task,
    ):
        """When in-memory pipeline state is None (e.g. server restart),
        check_in_progress_issues should reconstruct from issue comments
        instead of falling through to the legacy path that skips agents."""
        from src.models.workflow import WorkflowConfiguration

        config = WorkflowConfiguration(
            project_id="PVT_123",
            repository_owner="owner",
            repository_name="repo",
        )
        mock_config.return_value = config
        mock_service.get_project_items = AsyncMock(return_value=[mock_task])

        # No in-memory pipeline (simulates server restart)
        mock_get_pipeline.return_value = None

        # Reconstructed pipeline has speckit.implement not yet done
        reconstructed = PipelineState(
            issue_number=42,
            project_id="PVT_123",
            status="In Progress",
            agents=["speckit.implement"],
            current_agent_index=0,
            completed_agents=[],
            started_at=utcnow(),
        )
        mock_reconstruct.return_value = reconstructed
        mock_process_completion.return_value = None  # Agent not done yet

        results = await check_in_progress_issues(
            access_token="test-token",
            project_id="PVT_123",
            owner="owner",
            repo="repo",
        )

        # Should reconstruct, NOT fall through to legacy path
        mock_reconstruct.assert_called_once()
        mock_process_completion.assert_called_once()
        mock_process.assert_not_called()
        assert len(results) == 0

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    @patch("src.services.copilot_polling.pipeline.process_in_progress_issue")
    @patch("src.services.copilot_polling.get_pipeline_state")
    @patch("src.services.copilot_polling.get_workflow_config", new_callable=AsyncMock)
    @patch(
        "src.services.copilot_polling.pipeline._get_or_reconstruct_pipeline", new_callable=AsyncMock
    )
    @patch(
        "src.services.copilot_polling.pipeline._process_pipeline_completion", new_callable=AsyncMock
    )
    async def test_reconstructed_complete_pipeline_transitions_properly(
        self,
        mock_process_completion,
        mock_reconstruct,
        mock_config,
        mock_get_pipeline,
        mock_process,
        mock_service,
        mock_task,
    ):
        """When reconstruction shows all In Progress agents are done,
        _process_pipeline_completion should handle the transition to
        In Review (not the legacy path)."""
        from src.models.workflow import WorkflowConfiguration

        config = WorkflowConfiguration(
            project_id="PVT_123",
            repository_owner="owner",
            repository_name="repo",
        )
        mock_config.return_value = config
        mock_service.get_project_items = AsyncMock(return_value=[mock_task])

        # No in-memory pipeline
        mock_get_pipeline.return_value = None

        # Reconstructed pipeline shows speckit.implement already done
        reconstructed = PipelineState(
            issue_number=42,
            project_id="PVT_123",
            status="In Progress",
            agents=["speckit.implement"],
            current_agent_index=1,
            completed_agents=["speckit.implement"],
            started_at=utcnow(),
        )
        mock_reconstruct.return_value = reconstructed
        mock_process_completion.return_value = {
            "status": "success",
            "action": "status_transitioned",
            "from_status": "In Progress",
            "to_status": "In Review",
        }

        results = await check_in_progress_issues(
            access_token="test-token",
            project_id="PVT_123",
            owner="owner",
            repo="repo",
        )

        # Pipeline path should handle transition
        mock_reconstruct.assert_called_once()
        mock_process_completion.assert_called_once()
        mock_process.assert_not_called()
        assert len(results) == 1
        assert results[0]["action"] == "status_transitioned"

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    @patch("src.services.copilot_polling.pipeline.process_in_progress_issue")
    @patch("src.services.copilot_polling.get_pipeline_state")
    @patch("src.services.copilot_polling.get_workflow_config", new_callable=AsyncMock)
    @patch(
        "src.services.copilot_polling.pipeline._get_or_reconstruct_pipeline", new_callable=AsyncMock
    )
    @patch(
        "src.services.copilot_polling.pipeline._process_pipeline_completion", new_callable=AsyncMock
    )
    async def test_status_mismatch_pipeline_uses_correct_transition_target(
        self,
        mock_process_completion,
        mock_reconstruct,
        mock_config,
        mock_get_pipeline,
        mock_process,
        mock_service,
        mock_task,
    ):
        """When the issue is In Progress but pipeline tracks Backlog,
        the transition target should be Ready (not In Review)."""
        from src.models.workflow import WorkflowConfiguration

        config = WorkflowConfiguration(
            project_id="PVT_123",
            repository_owner="owner",
            repository_name="repo",
        )
        mock_config.return_value = config
        mock_service.get_project_items = AsyncMock(return_value=[mock_task])

        # Pipeline tracks Backlog, but issue is in In Progress
        pipeline = PipelineState(
            issue_number=42,
            project_id="PVT_123",
            status="Backlog",
            agents=["speckit.specify"],
            current_agent_index=0,
            completed_agents=[],
            started_at=utcnow(),
        )
        mock_get_pipeline.return_value = pipeline

        mock_process_completion.return_value = None  # Agent not done yet

        with patch("src.services.copilot_polling.set_pipeline_state"):
            await check_in_progress_issues(
                access_token="test-token",
                project_id="PVT_123",
                owner="owner",
                repo="repo",
            )

        # Pipeline status should be updated, transition target should be Ready
        assert pipeline.status == "In Progress"
        mock_process_completion.assert_called_once()
        call_kwargs = mock_process_completion.call_args.kwargs
        assert call_kwargs["from_status"] == "Backlog"
        assert call_kwargs["to_status"] == "Ready"
        mock_process.assert_not_called()


class TestProcessInProgressIssue:
    """Tests for processing individual in-progress issues."""

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    async def test_returns_none_when_no_completed_pr(self, mock_service):
        """Test that None is returned when no completed Copilot PR."""
        mock_service.check_copilot_pr_completion = AsyncMock(return_value=None)

        result = await process_in_progress_issue(
            access_token="test-token",
            project_id="PVT_123",
            item_id="PVTI_123",
            owner="owner",
            repo="repo",
            issue_number=42,
            task_title="Test Issue",
        )

        assert result is None

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    @patch("src.services.copilot_polling.pipeline.asyncio.sleep")
    async def test_updates_status_when_copilot_pr_ready(self, mock_sleep, mock_service):
        """Test that draft PR is converted and status is updated when Copilot finishes."""
        mock_service.check_copilot_pr_completion = AsyncMock(
            return_value={
                "number": 100,
                "id": "PR_123",
                "is_draft": True,  # Copilot leaves PR in draft when done
                "state": "OPEN",
                "last_commit": {"sha": "abc123"},  # Has commits = finished
                "copilot_finished": True,
            }
        )
        mock_service.mark_pr_ready_for_review = AsyncMock(return_value=True)
        mock_service.update_item_status_by_name = AsyncMock(return_value=True)
        mock_service.request_copilot_review = AsyncMock(return_value=True)

        result = await process_in_progress_issue(
            access_token="test-token",
            project_id="PVT_123",
            item_id="PVTI_123",
            owner="owner",
            repo="repo",
            issue_number=42,
            task_title="Test Issue",
        )

        assert result["status"] == "success"
        assert result["issue_number"] == 42
        assert result["pr_number"] == 100
        assert result["action"] == "status_updated_to_in_review"

        # Verify draft PR was converted to ready
        mock_service.mark_pr_ready_for_review.assert_called_once()

        # Verify status update was called
        mock_service.update_item_status_by_name.assert_called_once()
        call_args = mock_service.update_item_status_by_name.call_args.kwargs
        assert call_args["status_name"] == "In Review"

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    async def test_skips_already_processed_issues(self, mock_service):
        """Test that already processed issue+PR combinations are skipped."""
        _processed_issue_prs.add(cache_key_issue_pr(42, 100, "PVT_123"))

        mock_service.check_copilot_pr_completion = AsyncMock(
            return_value={
                "number": 100,
                "id": "PR_123",
                "is_draft": False,
            }
        )

        result = await process_in_progress_issue(
            access_token="test-token",
            project_id="PVT_123",
            item_id="PVTI_123",
            owner="owner",
            repo="repo",
            issue_number=42,
            task_title="Test Issue",
        )

        assert result is None

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    @patch("src.services.copilot_polling.pipeline.asyncio.sleep")
    async def test_skips_mark_ready_when_already_not_draft(self, mock_sleep, mock_service):
        """Test that mark_pr_ready_for_review is skipped if PR is not a draft."""
        mock_service.check_copilot_pr_completion = AsyncMock(
            return_value={
                "number": 100,
                "id": "PR_123",
                "is_draft": False,  # Already not a draft
                "state": "OPEN",
            }
        )
        mock_service.update_item_status_by_name = AsyncMock(return_value=True)
        mock_service.request_copilot_review = AsyncMock(return_value=True)

        result = await process_in_progress_issue(
            access_token="test-token",
            project_id="PVT_123",
            item_id="PVTI_123",
            owner="owner",
            repo="repo",
            issue_number=42,
            task_title="Test Issue",
        )

        assert result["status"] == "success"
        # mark_pr_ready_for_review should NOT be called
        mock_service.mark_pr_ready_for_review.assert_not_called()

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    async def test_returns_error_when_mark_ready_fails(self, mock_service):
        """Test error handling when marking PR ready fails."""
        mock_service.check_copilot_pr_completion = AsyncMock(
            return_value={
                "number": 100,
                "id": "PR_123",
                "is_draft": True,
                "state": "OPEN",
                "last_commit": {"sha": "abc123"},
                "copilot_finished": True,
            }
        )
        mock_service.mark_pr_ready_for_review = AsyncMock(return_value=False)

        result = await process_in_progress_issue(
            access_token="test-token",
            project_id="PVT_123",
            item_id="PVTI_123",
            owner="owner",
            repo="repo",
            issue_number=42,
            task_title="Test Issue",
        )

        assert result["status"] == "error"
        assert "draft" in result["error"].lower()

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    @patch("src.services.copilot_polling.pipeline.asyncio.sleep")
    async def test_returns_error_when_status_update_fails(self, mock_sleep, mock_service):
        """Test error handling when status update fails."""
        mock_service.check_copilot_pr_completion = AsyncMock(
            return_value={
                "number": 100,
                "id": "PR_123",
                "is_draft": True,
                "state": "OPEN",
                "last_commit": {"sha": "abc123"},
                "copilot_finished": True,
            }
        )
        mock_service.mark_pr_ready_for_review = AsyncMock(return_value=True)
        mock_service.update_item_status_by_name = AsyncMock(return_value=False)

        result = await process_in_progress_issue(
            access_token="test-token",
            project_id="PVT_123",
            item_id="PVTI_123",
            owner="owner",
            repo="repo",
            issue_number=42,
            task_title="Test Issue",
        )

        assert result["status"] == "error"
        assert "status" in result["error"].lower()

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    @patch("src.services.copilot_polling.pipeline.asyncio.sleep")
    async def test_adds_to_processed_cache_on_success(self, mock_sleep, mock_service):
        """Test that successful processing adds to the cache."""
        mock_service.check_copilot_pr_completion = AsyncMock(
            return_value={
                "number": 100,
                "id": "PR_123",
                "is_draft": False,
            }
        )
        mock_service.update_item_status_by_name = AsyncMock(return_value=True)

        await process_in_progress_issue(
            access_token="test-token",
            project_id="PVT_123",
            item_id="PVTI_123",
            owner="owner",
            repo="repo",
            issue_number=42,
            task_title="Test Issue",
        )

        assert cache_key_issue_pr(42, 100, "PVT_123") in _processed_issue_prs


class TestCheckIssueForCopilotCompletion:
    """Tests for manual issue checking."""

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    async def test_returns_not_found_when_issue_not_in_project(self, mock_service):
        """Test that 'not_found' is returned when issue not in project."""
        mock_service.get_project_items = AsyncMock(return_value=[])

        result = await check_issue_for_copilot_completion(
            access_token="test-token",
            project_id="PVT_123",
            owner="owner",
            repo="repo",
            issue_number=999,
        )

        assert result["status"] == "not_found"
        assert result["issue_number"] == 999

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    async def test_returns_skipped_when_not_in_progress(self, mock_service, mock_task):
        """Test that 'skipped' is returned when issue not in progress."""
        mock_task.status = "Backlog"
        mock_service.get_project_items = AsyncMock(return_value=[mock_task])

        result = await check_issue_for_copilot_completion(
            access_token="test-token",
            project_id="PVT_123",
            owner="owner",
            repo="repo",
            issue_number=42,
        )

        assert result["status"] == "skipped"
        assert result["current_status"] == "Backlog"

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    @patch("src.services.copilot_polling.process_in_progress_issue")
    async def test_processes_in_progress_issue(self, mock_process, mock_service, mock_task):
        """Test that in-progress issues are processed."""
        mock_service.get_project_items = AsyncMock(return_value=[mock_task])
        mock_process.return_value = {"status": "success", "issue_number": 42}

        result = await check_issue_for_copilot_completion(
            access_token="test-token",
            project_id="PVT_123",
            owner="owner",
            repo="repo",
            issue_number=42,
        )

        assert result["status"] == "success"
        mock_process.assert_called_once()

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    @patch("src.services.copilot_polling.process_in_progress_issue")
    async def test_returns_no_action_when_process_returns_none(
        self, mock_process, mock_service, mock_task
    ):
        """Test that 'no_action' is returned when no completed PR found."""
        mock_service.get_project_items = AsyncMock(return_value=[mock_task])
        mock_process.return_value = None

        result = await check_issue_for_copilot_completion(
            access_token="test-token",
            project_id="PVT_123",
            owner="owner",
            repo="repo",
            issue_number=42,
        )

        assert result["status"] == "no_action"
        assert result["issue_number"] == 42


class TestPostAgentOutputsFromPr:
    """Tests for posting agent .md outputs from completed PRs as issue comments."""

    @pytest.fixture(autouse=True)
    def clear_cache(self):
        """Clear the posted agent outputs cache and main branch tracking between tests."""
        _posted_agent_outputs.clear()
        _issue_main_branches.clear()
        yield
        _posted_agent_outputs.clear()
        _issue_main_branches.clear()

    @pytest.fixture
    def mock_task_backlog(self):
        task = MagicMock()
        task.github_item_id = "PVTI_1"
        task.github_content_id = "I_1"
        task.issue_number = 10
        task.repository_owner = "owner"
        task.repository_name = "repo"
        task.title = "Feature Issue"
        task.status = "Backlog"
        return task

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    @patch("src.services.copilot_polling.get_workflow_config", new_callable=AsyncMock)
    @patch("src.services.copilot_polling.get_pipeline_state")
    async def test_posts_done_marker_on_parent_only_without_sub_issue(
        self, mock_pipeline, mock_config, mock_service, mock_task_backlog
    ):
        """Without sub-issues, only Done! marker is posted (on parent). Markdown files are skipped."""
        mock_config.return_value = MagicMock()
        mock_pipeline.return_value = PipelineState(
            issue_number=10,
            project_id="PVT_1",
            status="Backlog",
            agents=["speckit.specify"],
            current_agent_index=0,
        )

        mock_service.check_agent_completion_comment = AsyncMock(return_value=False)
        mock_service.check_copilot_pr_completion = AsyncMock(
            return_value={"number": 5, "state": "open"}
        )
        mock_service.get_pull_request = AsyncMock(
            return_value={"head_ref": "feature-branch", "number": 5}
        )
        mock_service.get_pr_changed_files = AsyncMock(
            return_value=[
                {"filename": "specs/spec.md", "status": "added"},
                {"filename": "src/main.py", "status": "modified"},
            ]
        )
        mock_service.get_file_content_from_ref = AsyncMock(
            return_value="# Spec\n\nThis is the spec."
        )
        mock_service.create_issue_comment = AsyncMock(return_value={"id": 1, "body": "ok"})

        results = await post_agent_outputs_from_pr(
            access_token="token",
            project_id="PVT_1",
            owner="owner",
            repo="repo",
            tasks=[mock_task_backlog],
        )

        assert len(results) == 1
        assert results[0]["status"] == "success"
        # No markdown files posted (no sub-issue)
        assert results[0]["files_posted"] == 0
        assert results[0]["agent_name"] == "speckit.specify"

        # Only Done! marker posted (on parent issue #10)
        assert mock_service.create_issue_comment.call_count == 1
        done_call = mock_service.create_issue_comment.call_args_list[0]
        done_call_body = done_call.kwargs.get("body") or done_call[1].get("body", "")
        assert "speckit.specify: Done!" in done_call_body
        done_call_issue = done_call.kwargs.get("issue_number") or done_call[1].get("issue_number")
        assert done_call_issue == 10  # Parent issue

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    @patch("src.services.copilot_polling.get_workflow_config", new_callable=AsyncMock)
    @patch("src.services.copilot_polling.get_pipeline_state")
    async def test_posts_md_on_sub_issue_and_done_on_parent(
        self, mock_pipeline, mock_config, mock_service, mock_task_backlog
    ):
        """With sub-issues, markdown goes to sub-issue, Done! goes to parent."""
        mock_config.return_value = MagicMock()
        pipeline = PipelineState(
            issue_number=10,
            project_id="PVT_1",
            status="Backlog",
            agents=["speckit.specify"],
            current_agent_index=0,
        )
        pipeline.agent_sub_issues = {
            "speckit.specify": {"number": 99, "node_id": "I_99"},
        }
        mock_pipeline.return_value = pipeline

        mock_service.check_agent_completion_comment = AsyncMock(return_value=False)
        mock_service.check_copilot_pr_completion = AsyncMock(
            return_value={"number": 5, "state": "open"}
        )
        mock_service.get_pull_request = AsyncMock(
            return_value={"head_ref": "feature-branch", "number": 5}
        )
        mock_service.get_pr_changed_files = AsyncMock(
            return_value=[
                {"filename": "specs/spec.md", "status": "added"},
                {"filename": "src/main.py", "status": "modified"},
            ]
        )
        mock_service.get_file_content_from_ref = AsyncMock(
            return_value="# Spec\n\nThis is the spec."
        )
        mock_service.create_issue_comment = AsyncMock(return_value={"id": 1, "body": "ok"})
        mock_service.update_issue_state = AsyncMock(return_value=True)

        results = await post_agent_outputs_from_pr(
            access_token="token",
            project_id="PVT_1",
            owner="owner",
            repo="repo",
            tasks=[mock_task_backlog],
        )

        assert len(results) == 1
        assert results[0]["status"] == "success"
        assert results[0]["files_posted"] == 1
        assert results[0]["agent_name"] == "speckit.specify"

        # 2 calls: 1 markdown on sub-issue, 1 Done! on parent
        assert mock_service.create_issue_comment.call_count == 2

        # First call: markdown on sub-issue #99
        md_call = mock_service.create_issue_comment.call_args_list[0]
        md_issue = md_call.kwargs.get("issue_number") or md_call[1].get("issue_number")
        md_body = md_call.kwargs.get("body") or md_call[1].get("body", "")
        assert md_issue == 99  # Sub-issue
        assert "spec.md" in md_body

        # Second call: Done! on parent issue #10
        done_call = mock_service.create_issue_comment.call_args_list[1]
        done_issue = done_call.kwargs.get("issue_number") or done_call[1].get("issue_number")
        done_body = done_call.kwargs.get("body") or done_call[1].get("body", "")
        assert done_issue == 10  # Parent issue
        assert "speckit.specify: Done!" in done_body

        # Sub-issue should have been closed
        mock_service.update_issue_state.assert_called_once()

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    @patch("src.services.copilot_polling.get_workflow_config", new_callable=AsyncMock)
    @patch("src.services.copilot_polling.get_pipeline_state")
    async def test_posts_summary_on_sub_issue_for_linter(
        self, mock_pipeline, mock_config, mock_service, mock_task_backlog
    ):
        """Agents without declared output files should post one concise summary."""
        mock_config.return_value = MagicMock()
        pipeline = PipelineState(
            issue_number=10,
            project_id="PVT_1",
            status="In Progress",
            agents=["linter"],
            current_agent_index=0,
        )
        pipeline.agent_sub_issues = {
            "linter": {"number": 99, "node_id": "I_99"},
        }
        mock_pipeline.return_value = pipeline

        mock_service.check_agent_completion_comment = AsyncMock(return_value=False)
        mock_service.check_copilot_pr_completion = AsyncMock(
            return_value={"number": 5, "state": "open"}
        )
        mock_service.get_pull_request = AsyncMock(
            return_value={"head_ref": "feature-branch", "number": 5}
        )
        mock_service.get_pr_changed_files = AsyncMock(
            return_value=[
                {"filename": "specs/053-pipeline-queue-mode/tasks.md", "status": "modified"},
                {"filename": "solune/backend/src/api/settings.py", "status": "modified"},
            ]
        )
        mock_service.get_file_content_from_ref = AsyncMock()
        mock_service.create_issue_comment = AsyncMock(return_value={"id": 1, "body": "ok"})
        mock_service.update_issue_state = AsyncMock(return_value=True)

        results = await post_agent_outputs_from_pr(
            access_token="token",
            project_id="PVT_1",
            owner="owner",
            repo="repo",
            tasks=[mock_task_backlog],
        )

        assert len(results) == 1
        assert results[0]["status"] == "success"
        assert results[0]["files_posted"] == 0
        assert results[0]["agent_name"] == "linter"

        assert mock_service.create_issue_comment.call_count == 2

        summary_call = mock_service.create_issue_comment.call_args_list[0]
        summary_issue = summary_call.kwargs.get("issue_number") or summary_call[1].get(
            "issue_number"
        )
        summary_body = summary_call.kwargs.get("body") or summary_call[1].get("body", "")
        assert summary_issue == 99
        assert "`linter` completed PR #5." in summary_body
        assert "Markdown touched: 1" in summary_body
        assert "Non-markdown touched: 1" in summary_body
        assert "Full file contents were intentionally not reposted here" in summary_body

        done_call = mock_service.create_issue_comment.call_args_list[1]
        done_issue = done_call.kwargs.get("issue_number") or done_call[1].get("issue_number")
        done_body = done_call.kwargs.get("body") or done_call[1].get("body", "")
        assert done_issue == 10
        assert "linter: Done!" in done_body

        mock_service.get_file_content_from_ref.assert_not_called()
        mock_service.update_issue_state.assert_called_once()

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    @patch("src.services.copilot_polling.get_workflow_config", new_callable=AsyncMock)
    @patch("src.services.copilot_polling.get_pipeline_state")
    async def test_skips_when_done_marker_already_exists(
        self, mock_pipeline, mock_config, mock_service, mock_task_backlog
    ):
        """Should skip posting if Done! marker is already present."""
        mock_config.return_value = MagicMock()
        mock_pipeline.return_value = PipelineState(
            issue_number=10,
            project_id="PVT_1",
            status="Backlog",
            agents=["speckit.specify"],
            current_agent_index=0,
        )
        mock_service.check_agent_completion_comment = AsyncMock(return_value=True)

        results = await post_agent_outputs_from_pr(
            access_token="token",
            project_id="PVT_1",
            owner="owner",
            repo="repo",
            tasks=[mock_task_backlog],
        )

        assert len(results) == 0
        mock_service.check_copilot_pr_completion.assert_not_called()

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    @patch("src.services.copilot_polling.get_workflow_config", new_callable=AsyncMock)
    @patch("src.services.copilot_polling.get_pipeline_state")
    async def test_handles_implement_agent_with_no_md_outputs(
        self, mock_pipeline, mock_config, mock_service, mock_task_backlog
    ):
        """Should process speckit.implement and post Done! marker even with no .md outputs."""
        mock_config.return_value = MagicMock()
        mock_pipeline.return_value = PipelineState(
            issue_number=10,
            project_id="PVT_1",
            status="In Progress",
            agents=["speckit.implement"],
            current_agent_index=0,
        )
        # Agent has NOT posted Done! yet
        mock_service.check_agent_completion_comment = AsyncMock(return_value=False)
        # PR is complete
        mock_service.check_copilot_pr_completion = AsyncMock(
            return_value={"number": 5, "copilot_finished": True}
        )
        mock_service.get_pull_request = AsyncMock(
            return_value={"head_ref": "copilot/feature", "id": "PR_1"}
        )
        mock_service.get_pr_changed_files = AsyncMock(return_value=[])
        mock_service.create_issue_comment = AsyncMock(return_value={"id": 1})

        results = await post_agent_outputs_from_pr(
            access_token="token",
            project_id="PVT_1",
            owner="owner",
            repo="repo",
            tasks=[mock_task_backlog],
        )

        # Should post Done! marker (0 .md files)
        assert len(results) == 1
        assert results[0]["files_posted"] == 0

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    @patch("src.services.copilot_polling.get_workflow_config", new_callable=AsyncMock)
    @patch("src.services.copilot_polling.get_pipeline_state")
    async def test_skips_when_no_pr_found(
        self, mock_pipeline, mock_config, mock_service, mock_task_backlog
    ):
        """Should skip when no completed PR is found for the issue."""
        mock_config.return_value = MagicMock()
        mock_pipeline.return_value = PipelineState(
            issue_number=10,
            project_id="PVT_1",
            status="Backlog",
            agents=["speckit.specify"],
            current_agent_index=0,
        )
        mock_service.check_agent_completion_comment = AsyncMock(return_value=False)
        mock_service.check_copilot_pr_completion = AsyncMock(return_value=None)

        results = await post_agent_outputs_from_pr(
            access_token="token",
            project_id="PVT_1",
            owner="owner",
            repo="repo",
            tasks=[mock_task_backlog],
        )

        assert len(results) == 0

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    @patch("src.services.copilot_polling.get_workflow_config", new_callable=AsyncMock)
    @patch("src.services.copilot_polling.get_pipeline_state")
    async def test_deduplicates_via_cache(
        self, mock_pipeline, mock_config, mock_service, mock_task_backlog
    ):
        """Should not re-post outputs for the same issue/agent/PR."""
        _posted_agent_outputs.add("10:speckit.specify:5")

        mock_config.return_value = MagicMock()
        mock_pipeline.return_value = PipelineState(
            issue_number=10,
            project_id="PVT_1",
            status="Backlog",
            agents=["speckit.specify"],
            current_agent_index=0,
        )
        mock_service.check_agent_completion_comment = AsyncMock(return_value=False)

        results = await post_agent_outputs_from_pr(
            access_token="token",
            project_id="PVT_1",
            owner="owner",
            repo="repo",
            tasks=[mock_task_backlog],
        )

        assert len(results) == 0
        mock_service.check_copilot_pr_completion.assert_not_called()

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling._check_main_pr_completion", new_callable=AsyncMock)
    @patch("src.services.copilot_polling.github_projects_service")
    @patch("src.services.copilot_polling.get_workflow_config", new_callable=AsyncMock)
    @patch("src.services.copilot_polling.get_pipeline_state")
    async def test_subsequent_agent_detects_completion_on_main_pr(
        self,
        mock_pipeline,
        mock_config,
        mock_service,
        mock_main_pr_check,
        mock_task_backlog,
    ):
        """Subsequent agent should detect completion via fresh signals on the main PR."""
        # Set up: main branch already established (first agent completed)
        _issue_main_branches[10] = {"branch": "copilot/feature", "pr_number": 5, "head_sha": "abc"}

        mock_config.return_value = MagicMock()
        mock_pipeline.return_value = PipelineState(
            issue_number=10,
            project_id="PVT_1",
            status="Ready",
            agents=["speckit.plan", "speckit.tasks"],
            current_agent_index=0,
            started_at=datetime(2026, 1, 1),
        )

        # check_copilot_pr_completion finds the main PR as completed
        mock_service.check_agent_completion_comment = AsyncMock(return_value=False)
        mock_service.check_copilot_pr_completion = AsyncMock(
            return_value={"number": 5, "copilot_finished": True}
        )
        # _check_main_pr_completion confirms fresh completion signals
        mock_main_pr_check.return_value = True
        mock_service.get_pull_request = AsyncMock(
            return_value={
                "head_ref": "copilot/feature",
                "id": "PR_5",
                "last_commit": {"sha": "def"},
            }
        )
        mock_service.get_pr_changed_files = AsyncMock(
            return_value=[{"filename": "specs/plan.md", "status": "added"}]
        )
        mock_service.get_file_content_from_ref = AsyncMock(return_value="# Plan")
        mock_service.create_issue_comment = AsyncMock(return_value={"id": 1})

        results = await post_agent_outputs_from_pr(
            access_token="token",
            project_id="PVT_1",
            owner="owner",
            repo="repo",
            tasks=[mock_task_backlog],
        )

        # Should have detected completion and posted outputs
        assert len(results) == 1
        assert results[0]["agent_name"] == "speckit.plan"
        assert results[0]["pr_number"] == 5

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling._check_main_pr_completion", new_callable=AsyncMock)
    @patch("src.services.copilot_polling.github_projects_service")
    @patch("src.services.copilot_polling.get_workflow_config", new_callable=AsyncMock)
    @patch("src.services.copilot_polling.get_pipeline_state")
    async def test_subsequent_agent_skips_main_pr_without_fresh_signals(
        self,
        mock_pipeline,
        mock_config,
        mock_service,
        mock_main_pr_check,
        mock_task_backlog,
    ):
        """Subsequent agent should NOT detect completion if no fresh signals on main PR."""
        _issue_main_branches[10] = {"branch": "copilot/feature", "pr_number": 5, "head_sha": "abc"}

        mock_config.return_value = MagicMock()
        mock_pipeline.return_value = PipelineState(
            issue_number=10,
            project_id="PVT_1",
            status="Ready",
            agents=["speckit.plan", "speckit.tasks"],
            current_agent_index=0,
            started_at=datetime(2026, 1, 1),
        )

        mock_service.check_agent_completion_comment = AsyncMock(return_value=False)
        mock_service.check_copilot_pr_completion = AsyncMock(
            return_value={"number": 5, "copilot_finished": True}
        )
        # No fresh completion signals
        mock_main_pr_check.return_value = False

        results = await post_agent_outputs_from_pr(
            access_token="token",
            project_id="PVT_1",
            owner="owner",
            repo="repo",
            tasks=[mock_task_backlog],
        )

        assert len(results) == 0

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling._check_main_pr_completion", new_callable=AsyncMock)
    @patch("src.services.copilot_polling._find_completed_child_pr", new_callable=AsyncMock)
    @patch("src.services.copilot_polling.github_projects_service")
    @patch("src.services.copilot_polling.get_workflow_config", new_callable=AsyncMock)
    @patch("src.services.copilot_polling.get_pipeline_state")
    async def test_subsequent_agent_rejects_stale_main_pr_events_in_new_status(
        self,
        mock_pipeline,
        mock_config,
        mock_service,
        mock_find_child,
        mock_main_pr_check,
        mock_task_backlog,
    ):
        """Regression test for #1171: first agent in a NEW status must not be
        fooled by stale timeline events on the main PR from a previous status.

        Scenario:
          - speckit.specify (Backlog) creates main PR #5 and completes legitimately
          - Pipeline transitions to Ready, speckit.plan is the first agent (index=0)
          - main_branch_info already exists → is_subsequent_agent=True
          - check_copilot_pr_completion would find main PR #5 with stale events
          - The freshness gate (is_first_uncompleted bypass) previously allowed this
          - Fix: check_copilot_pr_completion is now skipped for subsequent agents
        """
        # Main branch from speckit.specify (prior status) exists
        _issue_main_branches[10] = {
            "branch": "copilot/feature",
            "pr_number": 5,
            "head_sha": "abc",
        }

        mock_config.return_value = MagicMock()
        mock_pipeline.return_value = PipelineState(
            issue_number=10,
            project_id="PVT_1",
            status="Ready",
            agents=["speckit.plan", "speckit.tasks"],
            current_agent_index=0,  # First agent in Ready status
            completed_agents=[],  # No agents completed in this status yet
            started_at=datetime(2026, 1, 1),
        )

        mock_service.check_agent_completion_comment = AsyncMock(return_value=False)

        # check_copilot_pr_completion WOULD return the main PR with stale events
        # (but should never be called for subsequent agents)
        mock_service.check_copilot_pr_completion = AsyncMock(
            return_value={"number": 5, "copilot_finished": True}
        )

        # No child PR found (agent just started)
        mock_find_child.return_value = None

        # No fresh completion signals on the main PR
        mock_main_pr_check.return_value = False

        results = await post_agent_outputs_from_pr(
            access_token="token",
            project_id="PVT_1",
            owner="owner",
            repo="repo",
            tasks=[mock_task_backlog],
        )

        # Must NOT post false Done! — result must be empty
        assert len(results) == 0

        # check_copilot_pr_completion must NOT have been called for subsequent agents
        mock_service.check_copilot_pr_completion.assert_not_called()

        # _check_main_pr_completion SHOULD have been called (proper freshness check)
        mock_main_pr_check.assert_called_once()

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling._get_tracking_state_from_issue", new_callable=AsyncMock)
    @patch("src.services.copilot_polling.github_projects_service")
    @patch("src.services.copilot_polling.get_workflow_config", new_callable=AsyncMock)
    @patch("src.services.copilot_polling.get_pipeline_state")
    async def test_reconstructs_pipeline_from_tracking_table_on_restart(
        self,
        mock_pipeline,
        mock_config,
        mock_service,
        mock_tracking,
        mock_task_backlog,
    ):
        """After container restart (no in-memory pipeline), should reconstruct
        the pipeline from the durable tracking table and detect completion."""
        mock_config.return_value = MagicMock()
        # Simulate container restart: in-memory pipeline is None
        mock_pipeline.return_value = None

        # Tracking table shows speckit.specify as 🔄 Active in Backlog
        tracking_body = (
            "## Issue Body\n\n"
            "---\n\n"
            "## 🤖 Agent Pipeline\n\n"
            "| # | Status | Agent | Model | State |\n"
            "|---|--------|-------|-------|-------|\n"
            "| 1 | Backlog | `speckit.specify` | gpt-4o | 🔄 Active |\n"
            "| 2 | Ready | `speckit.plan` | gpt-4o | ⏳ Pending |\n"
        )
        mock_tracking.return_value = (tracking_body, [])  # body, comments (no Done! yet)

        # Main branch not in memory and no existing PR discovered
        mock_service.find_existing_pr_for_issue = AsyncMock(return_value=None)
        mock_service.get_pull_request = AsyncMock(
            return_value={
                "head_ref": "copilot/issue-10",
                "number": 11,
                "id": "PR_11",
                "last_commit": {"sha": "abc123"},
            }
        )

        # Agent has completed — PR is non-draft
        mock_service.check_agent_completion_comment = AsyncMock(return_value=False)
        mock_service.check_copilot_pr_completion = AsyncMock(
            return_value={"number": 11, "state": "open"}
        )
        mock_service.get_pr_changed_files = AsyncMock(
            return_value=[{"filename": "specs/spec.md", "status": "added"}]
        )
        mock_service.get_file_content_from_ref = AsyncMock(
            return_value="# Specification\nDetails here."
        )
        mock_service.create_issue_comment = AsyncMock(return_value={"id": 1, "body": "ok"})

        results = await post_agent_outputs_from_pr(
            access_token="token",
            project_id="PVT_1",
            owner="owner",
            repo="repo",
            tasks=[mock_task_backlog],
        )

        # Pipeline should have been reconstructed and completion detected
        assert len(results) == 1
        assert results[0]["status"] == "success"
        assert results[0]["agent_name"] == "speckit.specify"

        # Only Done! marker posted (no sub-issue → no markdown comments)
        assert mock_service.create_issue_comment.call_count == 1

        # Verify tracking table was fetched for reconstruction
        mock_tracking.assert_called_once()

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling._get_tracking_state_from_issue", new_callable=AsyncMock)
    @patch("src.services.copilot_polling.github_projects_service")
    @patch("src.services.copilot_polling.get_workflow_config", new_callable=AsyncMock)
    @patch("src.services.copilot_polling.get_pipeline_state")
    async def test_reconstruction_skips_when_no_active_agent_in_tracking(
        self,
        mock_pipeline,
        mock_config,
        mock_service,
        mock_tracking,
        mock_task_backlog,
    ):
        """If tracking table has no 🔄 Active agent, reconstruction should skip."""
        mock_config.return_value = MagicMock()
        mock_pipeline.return_value = None

        # All agents show ✅ Done or ⏳ Pending — no active agent
        tracking_body = (
            "## Issue Body\n\n"
            "---\n\n"
            "## 🤖 Agent Pipeline\n\n"
            "| # | Status | Agent | Model | State |\n"
            "|---|--------|-------|-------|-------|\n"
            "| 1 | Backlog | `speckit.specify` | gpt-4o | ✅ Done |\n"
            "| 2 | Ready | `speckit.plan` | gpt-4o | ⏳ Pending |\n"
        )
        mock_tracking.return_value = (tracking_body, [])

        results = await post_agent_outputs_from_pr(
            access_token="token",
            project_id="PVT_1",
            owner="owner",
            repo="repo",
            tasks=[mock_task_backlog],
        )

        # No pipeline reconstructed → no results
        assert len(results) == 0
        mock_service.check_copilot_pr_completion.assert_not_called()


class TestCheckChildPrCompletion:
    """Tests for _check_child_pr_completion function."""

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    async def test_returns_false_when_no_linked_prs(self, mock_service):
        """Should return False when no linked PRs exist."""
        mock_service.get_linked_pull_requests = AsyncMock(return_value=[])

        result = await _check_child_pr_completion(
            access_token="token",
            owner="owner",
            repo="repo",
            issue_number=42,
            main_branch="copilot/feature-123",
            main_pr_number=10,
            agent_name="speckit.implement",
        )

        assert result is False

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    async def test_skips_main_pr(self, mock_service):
        """Should skip the main PR itself when looking for child PRs."""
        mock_service.get_linked_pull_requests = AsyncMock(
            return_value=[
                {"number": 10, "state": "OPEN", "author": "copilot[bot]"},
            ]
        )

        result = await _check_child_pr_completion(
            access_token="token",
            owner="owner",
            repo="repo",
            issue_number=42,
            main_branch="copilot/feature-123",
            main_pr_number=10,  # Same as the linked PR
            agent_name="speckit.implement",
        )

        assert result is False

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    async def test_skips_non_copilot_prs(self, mock_service):
        """Should skip PRs not created by Copilot."""
        mock_service.get_linked_pull_requests = AsyncMock(
            return_value=[
                {"number": 20, "state": "OPEN", "author": "human-user"},
            ]
        )

        result = await _check_child_pr_completion(
            access_token="token",
            owner="owner",
            repo="repo",
            issue_number=42,
            main_branch="copilot/feature-123",
            main_pr_number=10,
            agent_name="speckit.implement",
        )

        assert result is False

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    async def test_returns_true_for_ready_child_pr(self, mock_service):
        """Should return True when child PR is not a draft."""
        mock_service.get_linked_pull_requests = AsyncMock(
            return_value=[
                {"number": 20, "state": "OPEN", "author": "copilot[bot]"},
            ]
        )
        mock_service.get_pull_request = AsyncMock(
            return_value={
                "base_ref": "copilot/feature-123",  # Targets main branch
                "is_draft": False,  # Ready for review
            }
        )

        result = await _check_child_pr_completion(
            access_token="token",
            owner="owner",
            repo="repo",
            issue_number=42,
            main_branch="copilot/feature-123",
            main_pr_number=10,
            agent_name="speckit.implement",
        )

        assert result is True

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    async def test_returns_true_for_copilot_finished_event(self, mock_service):
        """Should return True when child PR has copilot_finished event."""
        mock_service.get_linked_pull_requests = AsyncMock(
            return_value=[
                {"number": 20, "state": "OPEN", "author": "copilot[bot]"},
            ]
        )
        mock_service.get_pull_request = AsyncMock(
            return_value={
                "base_ref": "copilot/feature-123",
                "is_draft": True,  # Still draft
            }
        )
        mock_service.get_pr_timeline_events = AsyncMock(return_value=[])
        mock_service.check_copilot_finished_events = MagicMock(return_value=True)

        result = await _check_child_pr_completion(
            access_token="token",
            owner="owner",
            repo="repo",
            issue_number=42,
            main_branch="copilot/feature-123",
            main_pr_number=10,
            agent_name="speckit.implement",
        )

        assert result is True

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    async def test_returns_false_for_incomplete_child_pr(self, mock_service):
        """Should return False when child PR exists but is incomplete."""
        mock_service.get_linked_pull_requests = AsyncMock(
            return_value=[
                {"number": 20, "state": "OPEN", "author": "copilot[bot]"},
            ]
        )
        mock_service.get_pull_request = AsyncMock(
            return_value={
                "base_ref": "copilot/feature-123",
                "is_draft": True,
            }
        )
        mock_service.get_pr_timeline_events = AsyncMock(return_value=[])
        mock_service.check_copilot_finished_events = MagicMock(return_value=False)

        result = await _check_child_pr_completion(
            access_token="token",
            owner="owner",
            repo="repo",
            issue_number=42,
            main_branch="copilot/feature-123",
            main_pr_number=10,
            agent_name="speckit.implement",
        )

        assert result is False


class TestCheckMainPrCompletion:
    """Tests for _check_main_pr_completion function."""

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    async def test_returns_false_when_pr_details_unavailable(self, mock_service):
        """Should return False when main PR details can't be fetched."""
        mock_service.get_pull_request = AsyncMock(return_value=None)

        result = await _check_main_pr_completion(
            access_token="token",
            owner="owner",
            repo="repo",
            main_pr_number=10,
            issue_number=42,
            agent_name="speckit.implement",
        )

        assert result is False

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    async def test_returns_false_when_pr_not_open(self, mock_service):
        """Should return False when main PR is not open (closed/merged)."""
        mock_service.get_pull_request = AsyncMock(
            return_value={"state": "CLOSED", "is_draft": True}
        )

        result = await _check_main_pr_completion(
            access_token="token",
            owner="owner",
            repo="repo",
            main_pr_number=10,
            issue_number=42,
            agent_name="speckit.implement",
        )

        assert result is False

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    async def test_returns_true_when_pr_not_draft(self, mock_service):
        """Should return True when main PR is no longer a draft."""
        mock_service.get_pull_request = AsyncMock(return_value={"state": "OPEN", "is_draft": False})

        result = await _check_main_pr_completion(
            access_token="token",
            owner="owner",
            repo="repo",
            main_pr_number=10,
            issue_number=42,
            agent_name="speckit.implement",
        )

        assert result is True

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    async def test_returns_true_for_fresh_copilot_finished_event(self, mock_service):
        """Should return True when main PR has fresh copilot_finished event."""
        pipeline_start = datetime(2025, 1, 15, 17, 0, 0)
        mock_service.get_pull_request = AsyncMock(return_value={"state": "OPEN", "is_draft": True})
        # Event after pipeline start
        mock_service.get_pr_timeline_events = AsyncMock(
            return_value=[
                {
                    "event": "copilot_work_finished",
                    "created_at": "2025-01-15T17:30:00Z",
                }
            ]
        )
        mock_service.check_copilot_finished_events = MagicMock(return_value=True)

        result = await _check_main_pr_completion(
            access_token="token",
            owner="owner",
            repo="repo",
            main_pr_number=10,
            issue_number=42,
            agent_name="speckit.implement",
            pipeline_started_at=pipeline_start,
        )

        assert result is True
        # Verify only fresh events were passed
        call_args = mock_service.check_copilot_finished_events.call_args[0][0]
        assert len(call_args) == 1
        assert call_args[0]["event"] == "copilot_work_finished"

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    async def test_filters_stale_events(self, mock_service):
        """Should filter out stale events from before pipeline start."""
        pipeline_start = datetime(2025, 1, 15, 17, 0, 0)
        mock_service.get_pull_request = AsyncMock(return_value={"state": "OPEN", "is_draft": True})
        # Only stale event (before pipeline start)
        mock_service.get_pr_timeline_events = AsyncMock(
            return_value=[
                {
                    "event": "copilot_work_finished",
                    "created_at": "2025-01-15T16:00:00Z",
                }
            ]
        )
        mock_service.check_copilot_finished_events = MagicMock(return_value=False)

        result = await _check_main_pr_completion(
            access_token="token",
            owner="owner",
            repo="repo",
            main_pr_number=10,
            issue_number=42,
            agent_name="speckit.implement",
            pipeline_started_at=pipeline_start,
        )

        assert result is False
        # Verify stale events were filtered out
        call_args = mock_service.check_copilot_finished_events.call_args[0][0]
        assert len(call_args) == 0

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    async def test_uses_all_events_when_no_pipeline_start(self, mock_service):
        """Should use all events when no pipeline start time is available."""
        mock_service.get_pull_request = AsyncMock(return_value={"state": "OPEN", "is_draft": True})
        mock_service.get_pr_timeline_events = AsyncMock(
            return_value=[{"event": "copilot_work_finished", "created_at": "2025-01-15T16:00:00Z"}]
        )
        mock_service.check_copilot_finished_events = MagicMock(return_value=True)

        result = await _check_main_pr_completion(
            access_token="token",
            owner="owner",
            repo="repo",
            main_pr_number=10,
            issue_number=42,
            agent_name="speckit.implement",
            pipeline_started_at=None,
        )

        assert result is True
        # All events should be passed without filtering
        call_args = mock_service.check_copilot_finished_events.call_args[0][0]
        assert len(call_args) == 1

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    async def test_returns_false_when_no_completion_signals(self, mock_service):
        """Should return False when main PR is draft and no completion events."""
        mock_service.get_pull_request = AsyncMock(return_value={"state": "OPEN", "is_draft": True})
        mock_service.get_pr_timeline_events = AsyncMock(return_value=[])
        mock_service.check_copilot_finished_events = MagicMock(return_value=False)

        result = await _check_main_pr_completion(
            access_token="token",
            owner="owner",
            repo="repo",
            main_pr_number=10,
            issue_number=42,
            agent_name="speckit.implement",
        )

        assert result is False

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    async def test_handles_exceptions_gracefully(self, mock_service):
        """Should return False and not raise on exceptions."""
        mock_service.get_pull_request = AsyncMock(side_effect=Exception("API error"))

        result = await _check_main_pr_completion(
            access_token="token",
            owner="owner",
            repo="repo",
            main_pr_number=10,
            issue_number=42,
            agent_name="speckit.implement",
        )

        assert result is False


class TestFilterEventsAfter:
    """Tests for _filter_events_after function."""

    def test_filters_events_before_cutoff(self):
        """Should exclude events before the cutoff time."""
        cutoff = datetime(2025, 1, 15, 17, 0, 0)
        events = [
            {"event": "old", "created_at": "2025-01-15T16:00:00Z"},
            {"event": "new", "created_at": "2025-01-15T18:00:00Z"},
        ]

        result = _filter_events_after(events, cutoff)

        assert len(result) == 1
        assert result[0]["event"] == "new"

    def test_includes_events_without_timestamp(self):
        """Should include events that have no created_at (conservative)."""
        cutoff = datetime(2025, 1, 15, 17, 0, 0)
        events = [
            {"event": "no_timestamp"},
            {"event": "empty_timestamp", "created_at": ""},
        ]

        result = _filter_events_after(events, cutoff)

        assert len(result) == 2

    def test_includes_events_with_unparseable_timestamp(self):
        """Should include events with unparseable timestamps (conservative)."""
        cutoff = datetime(2025, 1, 15, 17, 0, 0)
        events = [{"event": "bad", "created_at": "not-a-date"}]

        result = _filter_events_after(events, cutoff)

        assert len(result) == 1

    def test_empty_events_list(self):
        """Should return empty list for empty input."""
        cutoff = datetime(2025, 1, 15, 17, 0, 0)

        result = _filter_events_after([], cutoff)

        assert result == []

    def test_exact_cutoff_time_excluded(self):
        """Events at exactly the cutoff time should be excluded."""
        cutoff = datetime(2025, 1, 15, 17, 0, 0)
        events = [
            {"event": "exact", "created_at": "2025-01-15T17:00:00Z"},
        ]

        result = _filter_events_after(events, cutoff)

        # Exact match should be excluded (we use > not >=)
        assert len(result) == 0


class TestMergeChildPrIfApplicable:
    """Tests for _merge_child_pr_if_applicable function."""

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    async def test_returns_none_when_no_linked_prs(self, mock_service):
        """Should return None when no linked PRs exist."""
        mock_service.get_linked_pull_requests = AsyncMock(return_value=[])

        result = await _merge_child_pr_if_applicable(
            access_token="token",
            owner="owner",
            repo="repo",
            issue_number=42,
            main_branch="copilot/feature-123",
            main_pr_number=10,
            completed_agent="speckit.plan",
        )

        assert result is None

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    async def test_merges_child_pr_successfully(self, mock_service):
        """Should merge child PR when it targets the main branch."""
        mock_service.get_linked_pull_requests = AsyncMock(
            return_value=[
                {"number": 20, "state": "OPEN", "author": "copilot[bot]"},
            ]
        )
        mock_service.get_pull_request = AsyncMock(
            return_value={
                "base_ref": "copilot/feature-123",
                "head_ref": "copilot/feature-123-plan",
                "node_id": "PR_node_123",
                "id": "PR_node_123",
                "mergeable": "MERGEABLE",
            }
        )
        mock_service.merge_pull_request = AsyncMock(return_value={"merge_commit": "abc123def"})
        mock_service.delete_branch = AsyncMock(return_value=True)

        result = await _merge_child_pr_if_applicable(
            access_token="token",
            owner="owner",
            repo="repo",
            issue_number=42,
            main_branch="copilot/feature-123",
            main_pr_number=10,
            completed_agent="speckit.plan",
        )

        assert result is not None
        assert result["status"] == "merged"
        assert result["pr_number"] == 20
        mock_service.merge_pull_request.assert_called_once()

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    async def test_skips_main_pr(self, mock_service):
        """Should skip the main PR when looking for child PRs to merge."""
        mock_service.get_linked_pull_requests = AsyncMock(
            return_value=[
                {"number": 10, "state": "OPEN", "author": "copilot[bot]"},
            ]
        )

        result = await _merge_child_pr_if_applicable(
            access_token="token",
            owner="owner",
            repo="repo",
            issue_number=42,
            main_branch="copilot/feature-123",
            main_pr_number=10,  # Same as the linked PR
            completed_agent="speckit.plan",
        )

        assert result is None

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    async def test_returns_merge_failed_when_merge_fails(self, mock_service):
        """Should return merge_failed status when a child PR is found but merge fails."""
        mock_service.get_linked_pull_requests = AsyncMock(
            return_value=[
                {"number": 20, "state": "OPEN", "author": "copilot[bot]"},
            ]
        )
        mock_service.get_pull_request = AsyncMock(
            return_value={
                "base_ref": "copilot/feature-123",
                "head_ref": "copilot/feature-123-plan",
                "id": "PR_node_123",
                "is_draft": False,
            }
        )
        mock_service.is_copilot_author = MagicMock(return_value=True)
        # Merge fails (returns None)
        mock_service.merge_pull_request = AsyncMock(return_value=None)

        result = await _merge_child_pr_if_applicable(
            access_token="token",
            owner="owner",
            repo="repo",
            issue_number=42,
            main_branch="copilot/feature-123",
            main_pr_number=10,
            completed_agent="speckit.plan",
        )

        assert result is not None
        assert result["status"] == "merge_failed"
        assert result["pr_number"] == 20
        assert result["agent"] == "speckit.plan"

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.completion.asyncio.sleep", new_callable=AsyncMock)
    @patch("src.services.copilot_polling.github_projects_service")
    async def test_waits_for_draft_pr_to_be_ready_before_merge(self, mock_service, mock_sleep):
        """Draft child PRs should be marked ready and given time to propagate before merge."""
        mock_service.get_linked_pull_requests = AsyncMock(
            return_value=[
                {"number": 20, "state": "OPEN", "author": "copilot[bot]"},
            ]
        )
        mock_service.get_pull_request = AsyncMock(
            side_effect=[
                {
                    "base_ref": "copilot/feature-123",
                    "head_ref": "copilot/feature-123-plan",
                    "id": "PR_node_123",
                    "is_draft": True,
                },
                {"state": "MERGED"},
            ]
        )
        mock_service.mark_pr_ready_for_review = AsyncMock(return_value=True)
        mock_service.merge_pull_request = AsyncMock(return_value={"merge_commit": "abc123def"})
        mock_service.delete_branch = AsyncMock(return_value=True)

        result = await _merge_child_pr_if_applicable(
            access_token="token",
            owner="owner",
            repo="repo",
            issue_number=42,
            main_branch="copilot/feature-123",
            main_pr_number=10,
            completed_agent="speckit.plan",
        )

        assert result is not None
        assert result["status"] == "merged"
        mock_service.mark_pr_ready_for_review.assert_awaited_once()
        assert any(call.args == (2.0,) for call in mock_sleep.await_args_list)


class TestDetectCompletionSignals:
    """Tests for completion detection fallthrough handling."""

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    @patch(
        "src.services.copilot_polling._get_linked_prs_including_sub_issues", new_callable=AsyncMock
    )
    @patch("src.services.copilot_polling._check_main_pr_completion", new_callable=AsyncMock)
    @patch("src.services.copilot_polling._find_completed_child_pr", new_callable=AsyncMock)
    @patch("src.services.copilot_polling.get_issue_main_branch")
    async def test_prefers_open_child_pr_when_main_pr_completion_detected(
        self,
        mock_get_branch,
        mock_find_child,
        mock_check_main,
        mock_linked_prs,
        mock_service,
    ):
        """Main PR completion must not bypass an open child PR that still needs merging."""
        pipeline = MagicMock()
        pipeline.started_at = utcnow()
        pipeline.agent_assigned_sha = "sha-old"
        pipeline.agent_sub_issues = {}

        mock_get_branch.return_value = {
            "branch": "copilot/feature-42",
            "pr_number": 100,
            "head_sha": "sha-main",
        }
        mock_find_child.return_value = None
        mock_check_main.return_value = True
        mock_linked_prs.return_value = [
            {"number": 101, "state": "OPEN", "author": "copilot[bot]"},
        ]
        mock_service.get_pull_request = AsyncMock(
            return_value={
                "id": "PR_node_101",
                "head_ref": "copilot/feature-42-plan",
                "base_ref": "copilot/feature-42",
                "last_commit": {"sha": "sha-child"},
                "is_draft": True,
            }
        )

        result = await _detect_completion_signals(
            access_token="token",
            owner="owner",
            repo="repo",
            issue_number=42,
            current_agent="speckit.plan",
            pipeline=pipeline,
        )

        assert result is not None
        assert result["number"] == 101
        assert result["is_child_pr"] is True
        assert result["copilot_finished"] is True


class TestReconstructPipelineState:
    """Tests for _reconstruct_pipeline_state function."""

    @pytest.fixture(autouse=True)
    def clear_pipeline_states(self):
        """Clear pipeline states between tests."""
        from src.services.workflow_orchestrator import _pipeline_states

        _pipeline_states.clear()
        yield
        _pipeline_states.clear()

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    @patch("src.services.copilot_polling.set_pipeline_state")
    async def test_reconstructs_from_comments(self, mock_set_state, mock_service):
        """Should reconstruct pipeline state from issue comments."""
        mock_service.get_issue_with_comments = AsyncMock(
            return_value={
                "comments": [
                    {"body": "speckit.specify: Done!"},
                    {"body": "speckit.plan: Done!"},
                ]
            }
        )

        result = await _reconstruct_pipeline_state(
            access_token="token",
            owner="owner",
            repo="repo",
            issue_number=42,
            project_id="PVT_123",
            status="Ready",
            agents=["speckit.specify", "speckit.plan", "speckit.tasks"],
        )

        assert result.issue_number == 42
        assert result.completed_agents == ["speckit.specify", "speckit.plan"]
        assert result.current_agent_index == 2
        assert result.current_agent == "speckit.tasks"
        mock_set_state.assert_called_once()

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    @patch("src.services.copilot_polling.set_pipeline_state")
    async def test_stops_at_first_incomplete(self, mock_set_state, mock_service):
        """Should stop reconstruction at first agent without Done! marker."""
        mock_service.get_issue_with_comments = AsyncMock(
            return_value={
                "comments": [
                    {"body": "speckit.specify: Done!"},
                    # speckit.plan: Done! is missing
                    {"body": "speckit.tasks: Done!"},  # This should be ignored
                ]
            }
        )

        result = await _reconstruct_pipeline_state(
            access_token="token",
            owner="owner",
            repo="repo",
            issue_number=42,
            project_id="PVT_123",
            status="Ready",
            agents=["speckit.specify", "speckit.plan", "speckit.tasks"],
        )

        # Should stop at speckit.plan since it's missing
        assert result.completed_agents == ["speckit.specify"]
        assert result.current_agent == "speckit.plan"

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    @patch("src.services.copilot_polling.set_pipeline_state")
    async def test_handles_no_comments(self, mock_set_state, mock_service):
        """Should handle issues with no comments."""
        mock_service.get_issue_with_comments = AsyncMock(return_value={"comments": []})

        result = await _reconstruct_pipeline_state(
            access_token="token",
            owner="owner",
            repo="repo",
            issue_number=42,
            project_id="PVT_123",
            status="Backlog",
            agents=["speckit.specify"],
        )

        assert result.completed_agents == []
        assert result.current_agent == "speckit.specify"

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    @patch("src.services.copilot_polling.set_pipeline_state")
    async def test_handles_api_error(self, mock_set_state, mock_service):
        """Should handle API errors gracefully."""
        mock_service.get_issue_with_comments = AsyncMock(side_effect=Exception("API Error"))

        result = await _reconstruct_pipeline_state(
            access_token="token",
            owner="owner",
            repo="repo",
            issue_number=42,
            project_id="PVT_123",
            status="Backlog",
            agents=["speckit.specify"],
        )

        # Should return empty pipeline state on error
        assert result.completed_agents == []

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    @patch("src.services.copilot_polling.set_pipeline_state")
    async def test_started_at_uses_cross_status_done_timestamp(self, mock_set_state, mock_service):
        """Regression test for #1171: when no agents in the current status have
        Done! markers but a prior-status agent has one, started_at must use that
        prior-status Done! timestamp — NOT the issue creation time.

        Without this, stale timeline events from the prior-status agent pass
        the freshness filter and cause false-positive completions.
        """
        prior_done_ts = "2026-03-02T19:12:00Z"
        issue_created_ts = "2026-03-02T18:00:00Z"

        mock_service.get_issue_with_comments = AsyncMock(
            return_value={
                "created_at": issue_created_ts,
                "comments": [
                    # Done! from a prior-status agent (e.g. speckit.specify in Backlog)
                    {"body": "speckit.specify: Done!", "created_at": prior_done_ts},
                    # No Done! from current-status agents (speckit.plan, speckit.tasks)
                ],
            }
        )

        result = await _reconstruct_pipeline_state(
            access_token="token",
            owner="owner",
            repo="repo",
            issue_number=42,
            project_id="PVT_123",
            status="Ready",
            agents=["speckit.plan", "speckit.tasks"],
        )

        assert result.completed_agents == []
        assert result.current_agent == "speckit.plan"
        # started_at must be the prior-status Done! timestamp, not issue creation
        expected_ts = datetime.fromisoformat(prior_done_ts)
        assert result.started_at == expected_ts, (
            f"started_at should be {expected_ts} (prior Done! timestamp) "
            f"but was {result.started_at}"
        )


class TestReconstructPipelineLinksParentIssue:
    """Tests that pipeline reconstruction links the discovered PR to the parent issue."""

    @pytest.fixture(autouse=True)
    def clear_pipeline_states(self):
        from src.services.workflow_orchestrator import _issue_main_branches, _pipeline_states

        _pipeline_states.clear()
        _issue_main_branches.clear()
        yield
        _pipeline_states.clear()
        _issue_main_branches.clear()

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    @patch("src.services.copilot_polling.set_pipeline_state")
    @patch("src.services.copilot_polling.get_issue_main_branch", return_value=None)
    async def test_links_pr_to_parent_on_reconstruct(
        self, mock_get_branch, mock_set_state, mock_service
    ):
        """When pipeline reconstruction discovers a PR, it should link it to the parent issue."""
        mock_service.get_issue_with_comments = AsyncMock(
            return_value={"comments": [{"body": "speckit.specify: Done!"}]}
        )
        mock_service.find_existing_pr_for_issue = AsyncMock(
            return_value={"number": 100, "head_ref": "copilot/feature-branch"}
        )
        mock_service.get_pull_request = AsyncMock(return_value={"last_commit": {"sha": "abc123"}})
        mock_service.link_pull_request_to_issue = AsyncMock(return_value=True)

        await _reconstruct_pipeline_state(
            access_token="token",
            owner="owner",
            repo="repo",
            issue_number=42,
            project_id="PVT_123",
            status="Ready",
            agents=["speckit.specify", "speckit.plan"],
        )

        mock_service.link_pull_request_to_issue.assert_called_once_with(
            access_token="token",
            owner="owner",
            repo="repo",
            pr_number=100,
            issue_number=42,
        )

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    @patch("src.services.copilot_polling.set_pipeline_state")
    @patch("src.services.copilot_polling.get_issue_main_branch", return_value=None)
    async def test_link_failure_does_not_block_reconstruct(
        self, mock_get_branch, mock_set_state, mock_service
    ):
        """If link_pull_request_to_issue fails, pipeline reconstruction should still succeed."""
        mock_service.get_issue_with_comments = AsyncMock(
            return_value={"comments": [{"body": "speckit.specify: Done!"}]}
        )
        mock_service.find_existing_pr_for_issue = AsyncMock(
            return_value={"number": 100, "head_ref": "copilot/feature-branch"}
        )
        mock_service.get_pull_request = AsyncMock(return_value={"last_commit": {"sha": "abc123"}})
        mock_service.link_pull_request_to_issue = AsyncMock(side_effect=Exception("API Error"))

        result = await _reconstruct_pipeline_state(
            access_token="token",
            owner="owner",
            repo="repo",
            issue_number=42,
            project_id="PVT_123",
            status="Ready",
            agents=["speckit.specify", "speckit.plan"],
        )

        # Reconstruction should succeed despite the link failure
        assert result.completed_agents == ["speckit.specify"]
        assert result.current_agent == "speckit.plan"


class TestCheckBacklogIssues:
    """Tests for check_backlog_issues function."""

    @pytest.fixture
    def mock_backlog_task(self):
        """Create a mock task in Backlog status."""
        task = MagicMock()
        task.github_item_id = "PVTI_123"
        task.github_content_id = "I_123"
        task.issue_number = 42
        task.repository_owner = "owner"
        task.repository_name = "repo"
        task.title = "Test Issue"
        task.status = "Backlog"
        return task

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    @patch("src.services.copilot_polling.get_workflow_config", new_callable=AsyncMock)
    async def test_returns_empty_when_no_config(self, mock_config, mock_service):
        """Should return empty list when no workflow config exists."""
        mock_config.return_value = None

        results = await check_backlog_issues(
            access_token="token",
            project_id="PVT_123",
            owner="owner",
            repo="repo",
        )

        assert results == []

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    @patch("src.services.copilot_polling.get_workflow_config", new_callable=AsyncMock)
    async def test_returns_empty_when_no_backlog_tasks(self, mock_config, mock_service):
        """Should return empty when no tasks in Backlog status."""
        mock_config.return_value = MagicMock(
            status_backlog="Backlog",
            agent_mappings={"Backlog": ["speckit.specify"]},
        )
        mock_service.get_project_items = AsyncMock(return_value=[])

        results = await check_backlog_issues(
            access_token="token",
            project_id="PVT_123",
            owner="owner",
            repo="repo",
        )

        assert results == []

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    @patch("src.services.copilot_polling.get_workflow_config", new_callable=AsyncMock)
    @patch("src.services.copilot_polling.get_pipeline_state")
    @patch("src.services.copilot_polling.pipeline._reconstruct_pipeline_state")
    async def test_checks_agent_completion(
        self,
        mock_reconstruct,
        mock_get_pipeline,
        mock_config,
        mock_service,
        mock_backlog_task,
    ):
        """Should check if current agent has completed."""
        mock_config.return_value = MagicMock(
            status_backlog="Backlog",
            status_ready="Ready",
            agent_mappings={"Backlog": ["speckit.specify"]},
        )
        mock_service.get_project_items = AsyncMock(return_value=[mock_backlog_task])
        mock_get_pipeline.return_value = PipelineState(
            issue_number=42,
            project_id="PVT_123",
            status="Backlog",
            agents=["speckit.specify"],
            current_agent_index=0,
        )
        mock_service.check_agent_completion_comment = AsyncMock(return_value=False)

        results = await check_backlog_issues(
            access_token="token",
            project_id="PVT_123",
            owner="owner",
            repo="repo",
        )

        mock_service.check_agent_completion_comment.assert_called_once_with(
            access_token="token",
            owner="owner",
            repo="repo",
            issue_number=42,
            agent_name="speckit.specify",
        )
        assert results == []


class TestCheckReadyIssues:
    """Tests for check_ready_issues function."""

    @pytest.fixture
    def mock_ready_task(self):
        """Create a mock task in Ready status."""
        task = MagicMock()
        task.github_item_id = "PVTI_123"
        task.github_content_id = "I_123"
        task.issue_number = 42
        task.repository_owner = "owner"
        task.repository_name = "repo"
        task.title = "Test Issue"
        task.status = "Ready"
        return task

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    @patch("src.services.copilot_polling.get_workflow_config", new_callable=AsyncMock)
    async def test_returns_empty_when_no_config(self, mock_config, mock_service):
        """Should return empty when no workflow config."""
        mock_config.return_value = None

        results = await check_ready_issues(
            access_token="token",
            project_id="PVT_123",
            owner="owner",
            repo="repo",
        )

        assert results == []

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    @patch("src.services.copilot_polling.get_workflow_config", new_callable=AsyncMock)
    @patch("src.services.copilot_polling.get_pipeline_state")
    @patch("src.services.copilot_polling.pipeline._reconstruct_pipeline_state")
    async def test_reconstructs_pipeline_when_none(
        self,
        mock_reconstruct,
        mock_get_pipeline,
        mock_config,
        mock_service,
        mock_ready_task,
    ):
        """Should reconstruct pipeline state when not in memory."""
        mock_config.return_value = MagicMock(
            status_ready="Ready",
            status_in_progress="In Progress",
            agent_mappings={"Ready": ["speckit.plan", "speckit.tasks"]},
        )
        mock_service.get_project_items = AsyncMock(return_value=[mock_ready_task])
        mock_get_pipeline.return_value = None
        mock_reconstruct.return_value = PipelineState(
            issue_number=42,
            project_id="PVT_123",
            status="Ready",
            agents=["speckit.plan", "speckit.tasks"],
            current_agent_index=0,
        )
        mock_service.check_agent_completion_comment = AsyncMock(return_value=False)

        await check_ready_issues(
            access_token="token",
            project_id="PVT_123",
            owner="owner",
            repo="repo",
        )

        mock_reconstruct.assert_called_once()


class TestTransitionAfterPipelineComplete:
    """Tests for _transition_after_pipeline_complete function."""

    @pytest.fixture(autouse=True)
    def clear_states(self):
        """Clear global states between tests."""
        from src.services.workflow_orchestrator import _pipeline_states

        _pipeline_states.clear()
        yield
        _pipeline_states.clear()

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    @patch("src.services.copilot_polling.connection_manager")
    @patch("src.services.copilot_polling.get_workflow_config", new_callable=AsyncMock)
    @patch("src.services.copilot_polling.remove_pipeline_state")
    async def test_transitions_status_successfully(
        self, mock_remove, mock_config, mock_ws, mock_service
    ):
        """Should transition issue status after pipeline completion."""
        mock_service.update_item_status_by_name = AsyncMock(return_value=True)
        mock_config.return_value = MagicMock(agent_mappings={})
        mock_ws.broadcast_to_project = AsyncMock()

        result = await _transition_after_pipeline_complete(
            access_token="token",
            project_id="PVT_123",
            item_id="PVTI_123",
            owner="owner",
            repo="repo",
            issue_number=42,
            issue_node_id="I_123",
            from_status="Backlog",
            to_status="Ready",
            task_title="Test Issue",
        )

        assert result["status"] == "success"
        assert result["from_status"] == "Backlog"
        assert result["to_status"] == "Ready"
        mock_service.update_item_status_by_name.assert_called_once()
        mock_remove.assert_called_once_with(42)

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    @patch("src.services.copilot_polling.connection_manager")
    async def test_returns_error_when_status_update_fails(self, mock_ws, mock_service):
        """Should return error when status update fails."""
        mock_service.update_item_status_by_name = AsyncMock(return_value=False)

        result = await _transition_after_pipeline_complete(
            access_token="token",
            project_id="PVT_123",
            item_id="PVTI_123",
            owner="owner",
            repo="repo",
            issue_number=42,
            issue_node_id="I_123",
            from_status="Backlog",
            to_status="Ready",
            task_title="Test Issue",
        )

        assert result["status"] == "error"
        assert "Failed to update status" in result["error"]

    @pytest.mark.asyncio
    @patch(
        "src.services.copilot_polling.helpers._discover_main_pr_for_review",
        new_callable=AsyncMock,
    )
    @patch("src.services.copilot_polling.github_projects_service")
    @patch("src.services.copilot_polling.connection_manager")
    @patch("src.services.copilot_polling.get_workflow_config", new_callable=AsyncMock)
    @patch("src.services.copilot_polling.remove_pipeline_state")
    async def test_in_review_transition_uses_comprehensive_discovery(
        self, mock_remove, mock_config, mock_ws, mock_service, mock_discover
    ):
        """In Review transition should use _discover_main_pr_for_review for PR lookup."""
        mock_service.update_item_status_by_name = AsyncMock(return_value=True)
        mock_config.return_value = MagicMock(agent_mappings={})
        mock_ws.broadcast_to_project = AsyncMock()

        # Simulate _discover_main_pr_for_review finding the PR via sub-issues
        mock_discover.return_value = {
            "pr_number": 500,
            "pr_id": "PR_node_500",
            "head_ref": "copilot/fix-feature",
            "is_draft": True,
        }
        mock_service.mark_pr_ready_for_review = AsyncMock(return_value=True)
        mock_service.request_copilot_review = AsyncMock(return_value=True)

        result = await _transition_after_pipeline_complete(
            access_token="token",
            project_id="PVT_123",
            item_id="PVTI_123",
            owner="owner",
            repo="repo",
            issue_number=42,
            issue_node_id="I_123",
            from_status="In Progress",
            to_status="In Review",
            task_title="Test Issue",
        )

        assert result["status"] == "success"
        # Should have called comprehensive discovery
        mock_discover.assert_awaited_once_with(
            access_token="token",
            owner="owner",
            repo="repo",
            parent_issue_number=42,
        )
        # Should have converted draft → ready
        mock_service.mark_pr_ready_for_review.assert_awaited_once()
        # Should have requested Copilot review
        mock_service.request_copilot_review.assert_awaited_once()

    @pytest.mark.asyncio
    @patch(
        "src.services.copilot_polling.helpers._discover_main_pr_for_review",
        new_callable=AsyncMock,
    )
    @patch("src.services.copilot_polling.github_projects_service")
    @patch("src.services.copilot_polling.connection_manager")
    @patch("src.services.copilot_polling.get_workflow_config", new_callable=AsyncMock)
    @patch("src.services.copilot_polling.remove_pipeline_state")
    async def test_in_review_transition_no_pr_found_logs_warning(
        self, mock_remove, mock_config, mock_ws, mock_service, mock_discover
    ):
        """When no PR found during In Review transition, should still transition but log warning."""
        mock_service.update_item_status_by_name = AsyncMock(return_value=True)
        mock_config.return_value = MagicMock(agent_mappings={})
        mock_ws.broadcast_to_project = AsyncMock()

        # Comprehensive discovery returns None
        mock_discover.return_value = None

        result = await _transition_after_pipeline_complete(
            access_token="token",
            project_id="PVT_123",
            item_id="PVTI_123",
            owner="owner",
            repo="repo",
            issue_number=42,
            issue_node_id="I_123",
            from_status="In Progress",
            to_status="In Review",
            task_title="Test Issue",
        )

        assert result["status"] == "success"
        mock_discover.assert_awaited_once()
        # Should NOT have tried to request review
        mock_service.request_copilot_review = AsyncMock()  # ensure attribute exists
        # The function should not have called request_copilot_review since no PR found

    @pytest.mark.asyncio
    @patch(
        "src.services.copilot_polling.pipeline._dequeue_next_pipeline",
        new_callable=AsyncMock,
    )
    @patch("src.services.copilot_polling.github_projects_service")
    @patch("src.services.copilot_polling.connection_manager")
    @patch("src.services.copilot_polling.get_workflow_config", new_callable=AsyncMock)
    @patch("src.services.copilot_polling.remove_pipeline_state")
    async def test_dequeue_called_for_in_review(
        self, mock_remove, mock_config, mock_ws, mock_service, mock_dequeue
    ):
        """Dequeue should fire when pipeline reaches In Review."""
        mock_service.update_item_status_by_name = AsyncMock(return_value=True)
        mock_config.return_value = MagicMock(agent_mappings={})
        mock_ws.broadcast_to_project = AsyncMock()

        await _transition_after_pipeline_complete(
            access_token="token",
            project_id="PVT_123",
            item_id="PVTI_123",
            owner="owner",
            repo="repo",
            issue_number=42,
            issue_node_id="I_123",
            from_status="In Progress",
            to_status="In Review",
            task_title="Test Issue",
        )

        mock_dequeue.assert_awaited_once_with(
            access_token="token",
            project_id="PVT_123",
            trigger="pipeline_complete(issue=#42, to=In Review)",
        )

    @pytest.mark.asyncio
    @patch(
        "src.services.copilot_polling.pipeline._dequeue_next_pipeline",
        new_callable=AsyncMock,
    )
    @patch("src.services.copilot_polling.github_projects_service")
    @patch("src.services.copilot_polling.connection_manager")
    @patch("src.services.copilot_polling.get_workflow_config", new_callable=AsyncMock)
    @patch("src.services.copilot_polling.remove_pipeline_state")
    async def test_dequeue_called_for_done(
        self, mock_remove, mock_config, mock_ws, mock_service, mock_dequeue
    ):
        """Dequeue should fire when pipeline reaches Done."""
        mock_service.update_item_status_by_name = AsyncMock(return_value=True)
        mock_config.return_value = MagicMock(agent_mappings={})
        mock_ws.broadcast_to_project = AsyncMock()

        await _transition_after_pipeline_complete(
            access_token="token",
            project_id="PVT_123",
            item_id="PVTI_123",
            owner="owner",
            repo="repo",
            issue_number=42,
            issue_node_id="I_123",
            from_status="In Review",
            to_status="Done",
            task_title="Test Issue",
        )

        mock_dequeue.assert_awaited_once_with(
            access_token="token",
            project_id="PVT_123",
            trigger="pipeline_complete(issue=#42, to=Done)",
        )

    @pytest.mark.asyncio
    @pytest.mark.parametrize("to_status", ["Ready", "In Progress"])
    @patch(
        "src.services.copilot_polling.pipeline._dequeue_next_pipeline",
        new_callable=AsyncMock,
    )
    @patch("src.services.copilot_polling.github_projects_service")
    @patch("src.services.copilot_polling.connection_manager")
    @patch("src.services.copilot_polling.get_workflow_config", new_callable=AsyncMock)
    @patch("src.services.copilot_polling.remove_pipeline_state")
    async def test_dequeue_not_called_for_intermediate_transitions(
        self, mock_remove, mock_config, mock_ws, mock_service, mock_dequeue, to_status
    ):
        """Dequeue must NOT fire for intermediate status transitions."""
        mock_service.update_item_status_by_name = AsyncMock(return_value=True)
        mock_config.return_value = MagicMock(agent_mappings={})
        mock_ws.broadcast_to_project = AsyncMock()

        await _transition_after_pipeline_complete(
            access_token="token",
            project_id="PVT_123",
            item_id="PVTI_123",
            owner="owner",
            repo="repo",
            issue_number=42,
            issue_node_id="I_123",
            from_status="Backlog",
            to_status=to_status,
            task_title="Test Issue",
        )

        mock_dequeue.assert_not_awaited()


class TestAdvancePipeline:
    """Tests for _advance_pipeline function."""

    @pytest.fixture(autouse=True)
    def clear_states(self):
        """Clear global states between tests."""
        from src.services.workflow_orchestrator import _pipeline_states

        _pipeline_states.clear()
        yield
        _pipeline_states.clear()

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling._update_issue_tracking", new_callable=AsyncMock)
    @patch("src.services.copilot_polling.github_projects_service")
    @patch("src.services.copilot_polling.connection_manager")
    @patch("src.services.copilot_polling.get_issue_main_branch")
    @patch("src.services.copilot_polling._merge_child_pr_if_applicable")
    @patch("src.services.copilot_polling.get_workflow_orchestrator")
    @patch("src.services.copilot_polling.get_workflow_config", new_callable=AsyncMock)
    @patch("src.services.copilot_polling.set_pipeline_state")
    async def test_advances_to_next_agent(
        self,
        mock_set_state,
        mock_config,
        mock_get_orchestrator,
        mock_merge,
        mock_get_branch,
        mock_ws,
        mock_service,
        mock_update_tracking,
    ):
        """Should advance pipeline and assign next agent."""
        pipeline = PipelineState(
            issue_number=42,
            project_id="PVT_123",
            status="Ready",
            agents=["speckit.plan", "speckit.tasks"],
            current_agent_index=0,
            completed_agents=[],
        )

        mock_get_branch.return_value = None
        mock_merge.return_value = None
        mock_ws.broadcast_to_project = AsyncMock()
        mock_orchestrator = MagicMock()
        mock_orchestrator.assign_agent_for_status = AsyncMock(return_value=True)
        mock_get_orchestrator.return_value = mock_orchestrator
        mock_config.return_value = MagicMock()
        mock_update_tracking.return_value = True

        result = await _advance_pipeline(
            access_token="token",
            project_id="PVT_123",
            item_id="PVTI_123",
            owner="owner",
            repo="repo",
            issue_number=42,
            issue_node_id="I_123",
            pipeline=pipeline,
            from_status="Ready",
            to_status="In Progress",
            task_title="Test Issue",
        )

        assert result["status"] == "success"
        assert result["completed_agent"] == "speckit.plan"
        assert result["agent_name"] == "speckit.tasks"
        assert "1/2" in result["pipeline_progress"]
        mock_orchestrator.assign_agent_for_status.assert_called_once()

        # Verify the completed agent is marked ✅ Done in tracking
        mock_update_tracking.assert_called_once_with(
            access_token="token",
            owner="owner",
            repo="repo",
            issue_number=42,
            agent_name="speckit.plan",
            new_state="done",
        )

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling._update_issue_tracking", new_callable=AsyncMock)
    @patch("src.services.copilot_polling.github_projects_service")
    @patch("src.services.copilot_polling.connection_manager")
    @patch("src.services.copilot_polling.get_issue_main_branch")
    @patch("src.services.copilot_polling._merge_child_pr_if_applicable")
    @patch("src.services.copilot_polling.get_workflow_orchestrator")
    @patch("src.services.copilot_polling.get_workflow_config", new_callable=AsyncMock)
    @patch("src.services.copilot_polling.set_pipeline_state")
    async def test_marks_completed_agent_done_in_tracking(
        self,
        mock_set_state,
        mock_config,
        mock_get_orchestrator,
        mock_merge,
        mock_get_branch,
        mock_ws,
        mock_service,
        mock_update_tracking,
    ):
        """_advance_pipeline must mark the completed agent as Done in the
        issue body tracking table so users see ✅ instead of stale 🔄."""
        pipeline = PipelineState(
            issue_number=99,
            project_id="PVT_X",
            status="Ready",
            agents=["speckit.plan", "speckit.tasks"],
            current_agent_index=0,
            completed_agents=[],
        )

        mock_get_branch.return_value = None
        mock_merge.return_value = None
        mock_ws.broadcast_to_project = AsyncMock()
        mock_orchestrator = MagicMock()
        mock_orchestrator.assign_agent_for_status = AsyncMock(return_value=True)
        mock_get_orchestrator.return_value = mock_orchestrator
        mock_config.return_value = MagicMock()
        mock_update_tracking.return_value = True

        await _advance_pipeline(
            access_token="tok",
            project_id="PVT_X",
            item_id="PVTI_X",
            owner="o",
            repo="r",
            issue_number=99,
            issue_node_id="I_X",
            pipeline=pipeline,
            from_status="Ready",
            to_status="In Progress",
            task_title="T",
        )

        mock_update_tracking.assert_called_once_with(
            access_token="tok",
            owner="o",
            repo="r",
            issue_number=99,
            agent_name="speckit.plan",
            new_state="done",
        )

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling._update_issue_tracking", new_callable=AsyncMock)
    @patch("src.services.copilot_polling.github_projects_service")
    @patch("src.services.copilot_polling.connection_manager")
    @patch("src.services.copilot_polling.get_issue_main_branch")
    @patch("src.services.copilot_polling._merge_child_pr_if_applicable")
    @patch("src.services.copilot_polling.set_pipeline_state")
    async def test_blocks_pipeline_advance_on_merge_failure(
        self,
        mock_set_state,
        mock_merge,
        mock_get_branch,
        mock_ws,
        mock_service,
        mock_update_tracking,
    ):
        """Should block pipeline advance when child PR merge fails.

        When _merge_child_pr_if_applicable returns merge_failed, the pipeline
        must NOT assign the next agent — this ensures each agent's work is
        merged before the next one starts.
        """
        pipeline = PipelineState(
            issue_number=42,
            project_id="PVT_123",
            status="Ready",
            agents=["speckit.plan", "speckit.tasks"],
            current_agent_index=0,
            completed_agents=[],
        )

        mock_get_branch.return_value = {
            "branch": "copilot/feature-42",
            "pr_number": 100,
            "head_sha": "sha123",
        }
        # Merge fails — child PR found but could not be merged
        mock_merge.return_value = {
            "status": "merge_failed",
            "pr_number": 101,
            "main_branch": "copilot/feature-42",
            "agent": "speckit.plan",
        }
        mock_ws.broadcast_to_project = AsyncMock()
        mock_update_tracking.return_value = True

        result = await _advance_pipeline(
            access_token="token",
            project_id="PVT_123",
            item_id="PVTI_123",
            owner="owner",
            repo="repo",
            issue_number=42,
            issue_node_id="I_123",
            pipeline=pipeline,
            from_status="Ready",
            to_status="In Progress",
            task_title="Test Issue",
        )

        assert result["status"] == "merge_blocked"
        assert result["blocked_pr"] == 101
        # Pipeline should NOT have advanced — the completed agent
        # should have been rolled back
        assert "speckit.plan" not in pipeline.completed_agents
        # External side effects (tracking update, sub-issue close) must
        # NOT have been applied — they are deferred until after a
        # successful merge to keep rollback consistent.
        mock_update_tracking.assert_not_called()

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling._update_issue_tracking", new_callable=AsyncMock)
    @patch("src.services.copilot_polling.github_projects_service")
    @patch(
        "src.services.copilot_polling._get_linked_prs_including_sub_issues", new_callable=AsyncMock
    )
    @patch("src.services.copilot_polling.connection_manager")
    @patch("src.services.copilot_polling.get_issue_main_branch")
    @patch("src.services.copilot_polling._merge_child_pr_if_applicable")
    @patch("src.services.copilot_polling.set_pipeline_state")
    async def test_blocks_pipeline_when_open_child_pr_exists_but_merge_returns_none(
        self,
        mock_set_state,
        mock_merge,
        mock_get_branch,
        mock_ws,
        mock_linked_prs,
        mock_service,
        mock_update_tracking,
    ):
        """A silent None merge result must still block advancement if the child PR is open."""
        pipeline = PipelineState(
            issue_number=42,
            project_id="PVT_123",
            status="Ready",
            agents=["speckit.plan", "speckit.tasks"],
            current_agent_index=0,
            completed_agents=[],
        )

        mock_get_branch.return_value = {
            "branch": "copilot/feature-42",
            "pr_number": 100,
            "head_sha": "sha123",
        }
        mock_merge.return_value = None
        mock_linked_prs.return_value = [
            {"number": 101, "state": "OPEN", "author": "copilot[bot]"},
        ]
        mock_service.get_pull_request = AsyncMock(
            return_value={
                "id": "PR_node_101",
                "head_ref": "copilot/feature-42-plan",
                "base_ref": "copilot/feature-42",
                "last_commit": {"sha": "sha-child"},
                "is_draft": False,
            }
        )
        mock_ws.broadcast_to_project = AsyncMock()
        mock_update_tracking.return_value = True

        result = await _advance_pipeline(
            access_token="token",
            project_id="PVT_123",
            item_id="PVTI_123",
            owner="owner",
            repo="repo",
            issue_number=42,
            issue_node_id="I_123",
            pipeline=pipeline,
            from_status="Ready",
            to_status="In Progress",
            task_title="Test Issue",
        )

        assert result["status"] == "merge_blocked"
        assert result["blocked_pr"] == 101
        assert "speckit.plan" not in pipeline.completed_agents
        mock_update_tracking.assert_not_called()

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.pipeline.asyncio.sleep", new_callable=AsyncMock)
    @patch("src.services.copilot_polling._update_issue_tracking", new_callable=AsyncMock)
    @patch("src.services.copilot_polling.github_projects_service")
    @patch("src.services.copilot_polling.connection_manager")
    @patch("src.services.copilot_polling.get_issue_main_branch")
    @patch("src.services.copilot_polling._merge_child_pr_if_applicable")
    @patch("src.services.copilot_polling.get_workflow_orchestrator")
    @patch("src.services.copilot_polling.get_workflow_config", new_callable=AsyncMock)
    @patch("src.services.copilot_polling.set_pipeline_state")
    async def test_assigns_new_parallel_group_after_sequential_completion(
        self,
        mock_set_state,
        mock_config,
        mock_get_orchestrator,
        mock_merge,
        mock_get_branch,
        mock_ws,
        mock_service,
        mock_update_tracking,
        mock_sleep,
    ):
        """A newly-entered parallel group must be assigned immediately.

        Regression for issue #3890: after a sequential group completed, the
        next parallel group was treated as already active because its status
        map was incomplete, so _advance_pipeline returned `parallel_wait`
        before assigning any of the pending agents.
        """
        from src.services.workflow_orchestrator.models import PipelineGroupInfo

        pipeline = PipelineState(
            issue_number=42,
            project_id="PVT_123",
            status="In Progress",
            agents=["speckit.implement", "linter", "archivist", "judge"],
            current_agent_index=0,
            completed_agents=[],
            groups=[
                PipelineGroupInfo(
                    group_id="g1",
                    execution_mode="sequential",
                    agents=["speckit.implement"],
                ),
                PipelineGroupInfo(
                    group_id="g2",
                    execution_mode="parallel",
                    agents=["linter", "archivist", "judge"],
                    agent_statuses={
                        "linter": "pending",
                        "archivist": "pending",
                        "judge": "pending",
                    },
                ),
            ],
            current_group_index=0,
            current_agent_index_in_group=0,
        )

        mock_get_branch.return_value = None
        mock_merge.return_value = None
        mock_ws.broadcast_to_project = AsyncMock()
        mock_orchestrator = MagicMock()
        mock_orchestrator.assign_agent_for_status = AsyncMock(return_value=True)
        mock_get_orchestrator.return_value = mock_orchestrator
        mock_config.return_value = MagicMock()
        mock_update_tracking.return_value = True

        result = await _advance_pipeline(
            access_token="token",
            project_id="PVT_123",
            item_id="PVTI_123",
            owner="owner",
            repo="repo",
            issue_number=42,
            issue_node_id="I_123",
            pipeline=pipeline,
            from_status="In Progress",
            to_status="In Review",
            task_title="Test Issue",
        )

        assert result["status"] == "success"
        assert result["action"] == "parallel_group_assigned"
        assert result["agent_name"] == "linter, archivist, judge"
        assert pipeline.current_group_index == 1
        assert pipeline.groups[1].agent_statuses == {
            "linter": "active",
            "archivist": "active",
            "judge": "active",
        }

        assert mock_orchestrator.assign_agent_for_status.await_count == 3
        called_indices = [
            call.kwargs["agent_index"]
            for call in mock_orchestrator.assign_agent_for_status.await_args_list
        ]
        assert called_indices == [1, 2, 3]


class TestFindCompletedChildPr:
    """Tests for _find_completed_child_pr function."""

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    async def test_returns_none_when_no_linked_prs(self, mock_service):
        """Should return None when no linked PRs exist."""
        mock_service.get_linked_pull_requests = AsyncMock(return_value=[])

        result = await _find_completed_child_pr(
            access_token="token",
            owner="owner",
            repo="repo",
            issue_number=211,
            main_branch="copilot/add-black-background-theme",
            main_pr_number=212,
            agent_name="speckit.plan",
        )

        assert result is None

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    async def test_returns_pr_info_when_child_pr_complete(self, mock_service):
        """Should return PR info when child PR has completion signals (like PR #214 for issue #211)."""
        # Simulate PRs #212 (main) and #214 (child)
        mock_service.get_linked_pull_requests = AsyncMock(
            return_value=[
                {"number": 212, "state": "OPEN", "author": "copilot[bot]"},  # Main PR
                {"number": 214, "state": "OPEN", "author": "copilot[bot]"},  # Child PR
            ]
        )
        # PR #214 details - targets the main branch, not 'main'
        mock_service.get_pull_request = AsyncMock(
            return_value={
                "id": "PR_214",
                "base_ref": "copilot/add-black-background-theme",
                "head_ref": "copilot/implement-black-background-theme",
                "is_draft": True,
                "last_commit": {"sha": "abc123"},
            }
        )
        mock_service.get_pr_timeline_events = AsyncMock(
            return_value=[{"event": "copilot_work_finished"}]
        )
        mock_service.check_copilot_finished_events = MagicMock(return_value=True)

        result = await _find_completed_child_pr(
            access_token="token",
            owner="owner",
            repo="repo",
            issue_number=211,
            main_branch="copilot/add-black-background-theme",
            main_pr_number=212,
            agent_name="speckit.plan",
        )

        assert result is not None
        assert result["number"] == 214
        assert result["is_child_pr"] is True
        assert result["copilot_finished"] is True

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    async def test_skips_main_pr(self, mock_service):
        """Should skip the main PR and only consider child PRs."""
        # Only the main PR exists, no child PR
        mock_service.get_linked_pull_requests = AsyncMock(
            return_value=[
                {"number": 212, "state": "OPEN", "author": "copilot[bot]"},
            ]
        )

        result = await _find_completed_child_pr(
            access_token="token",
            owner="owner",
            repo="repo",
            issue_number=211,
            main_branch="copilot/add-black-background-theme",
            main_pr_number=212,
            agent_name="speckit.plan",
        )

        assert result is None
        # Should not call get_pull_request for the main PR
        mock_service.get_pull_request.assert_not_called()

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    async def test_returns_none_when_child_pr_targets_unrelated_branch(self, mock_service):
        """Should return None when child PR targets an unrelated branch (not main branch or 'main')."""
        mock_service.get_linked_pull_requests = AsyncMock(
            return_value=[
                {"number": 212, "state": "OPEN", "author": "copilot[bot]"},
                {"number": 215, "state": "OPEN", "author": "copilot[bot]"},
            ]
        )
        # PR #215 targets an unrelated branch
        mock_service.get_pull_request = AsyncMock(
            return_value={
                "base_ref": "feature/other-work",  # Unrelated target
                "is_draft": False,
            }
        )

        result = await _find_completed_child_pr(
            access_token="token",
            owner="owner",
            repo="repo",
            issue_number=211,
            main_branch="copilot/add-black-background-theme",
            main_pr_number=212,
            agent_name="speckit.plan",
        )

        assert result is None

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    async def test_returns_pr_when_not_draft(self, mock_service):
        """Should return PR info when child PR is not draft (ready for review)."""
        mock_service.get_linked_pull_requests = AsyncMock(
            return_value=[
                {"number": 212, "state": "OPEN", "author": "copilot[bot]"},
                {"number": 214, "state": "OPEN", "author": "copilot[bot]"},
            ]
        )
        mock_service.get_pull_request = AsyncMock(
            return_value={
                "id": "PR_214",
                "base_ref": "copilot/add-black-background-theme",
                "head_ref": "copilot/implement-feature",
                "is_draft": False,  # Not draft = ready
                "last_commit": {"sha": "xyz789"},
            }
        )

        result = await _find_completed_child_pr(
            access_token="token",
            owner="owner",
            repo="repo",
            issue_number=211,
            main_branch="copilot/add-black-background-theme",
            main_pr_number=212,
            agent_name="speckit.plan",
        )

        assert result is not None
        assert result["number"] == 214
        assert result["copilot_finished"] is True
        # Should not check timeline events if not draft
        mock_service.get_pr_timeline_events.assert_not_called()

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    async def test_returns_pr_info_when_child_pr_merged(self, mock_service):
        """Should return PR info when child PR is MERGED (like PR #218 for issue #215)."""
        # Simulate PRs #216 (main) and #218 (merged child)
        mock_service.get_linked_pull_requests = AsyncMock(
            return_value=[
                {"number": 216, "state": "OPEN", "author": "copilot[bot]"},  # Main PR
                {"number": 218, "state": "MERGED", "author": "copilot[bot]"},  # Merged child PR
            ]
        )
        mock_service.get_pull_request = AsyncMock(
            return_value={
                "id": "PR_218",
                "base_ref": "copilot/apply-white-background-interface",
                "head_ref": "copilot/apply-white-background-interface-again",
                "last_commit": {"sha": "merged123"},
            }
        )

        result = await _find_completed_child_pr(
            access_token="token",
            owner="owner",
            repo="repo",
            issue_number=215,
            main_branch="copilot/apply-white-background-interface",
            main_pr_number=216,
            agent_name="speckit.tasks",
        )

        assert result is not None
        assert result["number"] == 218
        assert result["is_child_pr"] is True
        assert result["is_merged"] is True
        assert result["copilot_finished"] is True
        # Should not check timeline events for merged PRs
        mock_service.get_pr_timeline_events.assert_not_called()

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    async def test_returns_none_when_child_pr_still_in_progress(self, mock_service):
        """Should return None when child PR exists but is still in progress."""
        mock_service.get_linked_pull_requests = AsyncMock(
            return_value=[
                {"number": 212, "state": "OPEN", "author": "copilot[bot]"},
                {"number": 214, "state": "OPEN", "author": "copilot[bot]"},
            ]
        )
        mock_service.get_pull_request = AsyncMock(
            return_value={
                "base_ref": "copilot/add-black-background-theme",
                "is_draft": True,
                "title": "[WIP] Add black background theme",
            }
        )
        mock_service.get_pr_timeline_events = AsyncMock(return_value=[])
        mock_service.check_copilot_finished_events = MagicMock(return_value=False)

        result = await _find_completed_child_pr(
            access_token="token",
            owner="owner",
            repo="repo",
            issue_number=211,
            main_branch="copilot/add-black-background-theme",
            main_pr_number=212,
            agent_name="speckit.plan",
        )

        assert result is None

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    async def test_skips_claimed_child_pr_from_other_agent(self, mock_service):
        """Should skip child PR that was already claimed by another agent.

        This prevents speckit.tasks from re-using speckit.plan's merged PR.
        """
        # Pre-claim PR #226 for speckit.plan
        _claimed_child_prs.add("224:226:speckit.plan")

        # Simulate PRs #225 (main) and #226 (merged child claimed by speckit.plan)
        mock_service.get_linked_pull_requests = AsyncMock(
            return_value=[
                {"number": 225, "state": "OPEN", "author": "copilot[bot]"},  # Main PR
                {"number": 226, "state": "MERGED", "author": "copilot[bot]"},  # Claimed child PR
            ]
        )
        mock_service.get_pull_request = AsyncMock(
            return_value={
                "id": "PR_226",
                "base_ref": "copilot/apply-yellow-background-color-again",
                "head_ref": "copilot/apply-yellow-background-color-another-one",
                "last_commit": {"sha": "merged123"},
            }
        )

        # speckit.tasks should NOT see the PR that was claimed by speckit.plan
        result = await _find_completed_child_pr(
            access_token="token",
            owner="owner",
            repo="repo",
            issue_number=224,
            main_branch="copilot/apply-yellow-background-color-again",
            main_pr_number=225,
            agent_name="speckit.tasks",  # Different agent
        )

        assert result is None

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    async def test_allows_same_agent_to_see_claimed_pr(self, mock_service):
        """Should allow an agent to see its own claimed PR."""
        # Pre-claim PR #226 for speckit.plan
        _claimed_child_prs.add("224:226:speckit.plan")

        # Simulate PRs #225 (main) and #226 (merged child)
        mock_service.get_linked_pull_requests = AsyncMock(
            return_value=[
                {"number": 225, "state": "OPEN", "author": "copilot[bot]"},
                {"number": 226, "state": "MERGED", "author": "copilot[bot]"},
            ]
        )
        mock_service.get_pull_request = AsyncMock(
            return_value={
                "id": "PR_226",
                "base_ref": "copilot/apply-yellow-background-color-again",
                "head_ref": "copilot/apply-yellow-background-color-another-one",
                "last_commit": {"sha": "merged123"},
            }
        )

        # speckit.plan should still see its own claimed PR
        result = await _find_completed_child_pr(
            access_token="token",
            owner="owner",
            repo="repo",
            issue_number=224,
            main_branch="copilot/apply-yellow-background-color-again",
            main_pr_number=225,
            agent_name="speckit.plan",  # Same agent
        )

        assert result is not None
        assert result["number"] == 226

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    async def test_returns_completed_when_timeline_empty_and_title_has_no_wip(self, mock_service):
        """Should detect completion via title fallback when timeline API fails.

        When the timeline API returns 403 (empty list), a draft PR whose title
        no longer starts with '[WIP]' indicates Copilot finished work.
        """
        mock_service.get_linked_pull_requests = AsyncMock(
            return_value=[
                {"number": 300, "state": "OPEN", "author": "copilot[bot]"},
                {"number": 301, "state": "OPEN", "author": "copilot[bot]"},
            ]
        )
        mock_service.get_pull_request = AsyncMock(
            return_value={
                "id": "PR_301",
                "base_ref": "copilot/cleanup-feature",
                "head_ref": "copilot/cleanup-feature-tasks",
                "is_draft": True,
                "title": "Generate tasks.md for cleanup feature",
                "last_commit": {"sha": "abc123"},
            }
        )
        # Timeline returns empty (simulates 403 Forbidden)
        mock_service.get_pr_timeline_events = AsyncMock(return_value=[])
        mock_service.check_copilot_finished_events = MagicMock(return_value=False)

        result = await _find_completed_child_pr(
            access_token="token",
            owner="owner",
            repo="repo",
            issue_number=299,
            main_branch="copilot/cleanup-feature",
            main_pr_number=300,
            agent_name="speckit.tasks",
        )

        assert result is not None
        assert result["number"] == 301
        assert result["copilot_finished"] is True
        assert result["is_child_pr"] is True

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    async def test_returns_none_when_timeline_empty_and_title_has_wip(self, mock_service):
        """Should NOT detect completion when title still has [WIP] prefix.

        Even when timeline API fails, a [WIP] title means Copilot is still
        working — the fallback should not trigger.
        """
        mock_service.get_linked_pull_requests = AsyncMock(
            return_value=[
                {"number": 300, "state": "OPEN", "author": "copilot[bot]"},
                {"number": 301, "state": "OPEN", "author": "copilot[bot]"},
            ]
        )
        mock_service.get_pull_request = AsyncMock(
            return_value={
                "base_ref": "copilot/cleanup-feature",
                "is_draft": True,
                "title": "[WIP] Generate tasks.md for cleanup feature",
            }
        )
        mock_service.get_pr_timeline_events = AsyncMock(return_value=[])
        mock_service.check_copilot_finished_events = MagicMock(return_value=False)

        result = await _find_completed_child_pr(
            access_token="token",
            owner="owner",
            repo="repo",
            issue_number=299,
            main_branch="copilot/cleanup-feature",
            main_pr_number=300,
            agent_name="speckit.tasks",
        )

        assert result is None

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    async def test_no_title_fallback_when_timeline_has_events(self, mock_service):
        """Should NOT use title fallback when timeline returned real events.

        If the timeline API succeeded (non-empty list) but has no
        copilot_finished events, the title fallback must NOT trigger —
        the agent is genuinely still working.
        """
        mock_service.get_linked_pull_requests = AsyncMock(
            return_value=[
                {"number": 300, "state": "OPEN", "author": "copilot[bot]"},
                {"number": 301, "state": "OPEN", "author": "copilot[bot]"},
            ]
        )
        mock_service.get_pull_request = AsyncMock(
            return_value={
                "base_ref": "copilot/cleanup-feature",
                "is_draft": True,
                "title": "Generate tasks.md for cleanup feature",
            }
        )
        # Timeline has events but no copilot_finished
        mock_service.get_pr_timeline_events = AsyncMock(
            return_value=[{"event": "committed"}, {"event": "copilot_work_started"}]
        )
        mock_service.check_copilot_finished_events = MagicMock(return_value=False)

        result = await _find_completed_child_pr(
            access_token="token",
            owner="owner",
            repo="repo",
            issue_number=299,
            main_branch="copilot/cleanup-feature",
            main_pr_number=300,
            agent_name="speckit.tasks",
        )

        assert result is None


# ──────────────────────────────────────────────────────────────────────────────
# Self-Healing Recovery Tests
# ──────────────────────────────────────────────────────────────────────────────


class TestRecoverStalledIssues:
    """Tests for the self-healing recover_stalled_issues function."""

    TRACKING_BODY = (
        "## Issue Body\n\n"
        "---\n\n"
        "## 🤖 Agent Pipeline\n\n"
        "| # | Status | Agent | Model | State |\n"
        "|---|--------|-------|-------|-------|\n"
        "| 1 | Backlog | `speckit.specify` | gpt-4o | 🔄 Active |\n"
        "| 2 | Ready | `speckit.plan` | gpt-4o | ⏳ Pending |\n"
    )

    TRACKING_BODY_ALL_DONE = (
        "## Issue Body\n\n"
        "---\n\n"
        "## 🤖 Agent Pipeline\n\n"
        "| # | Status | Agent | Model | State |\n"
        "|---|--------|-------|-------|-------|\n"
        "| 1 | Backlog | `speckit.specify` | gpt-4o | ✅ Done |\n"
        "| 2 | Ready | `speckit.plan` | gpt-4o | ✅ Done |\n"
    )

    @pytest.fixture(autouse=True)
    def clear_recovery_state(self):
        """Clear global recovery state before each test."""
        _recovery_last_attempt.clear()
        _pending_agent_assignments.clear()
        yield
        _recovery_last_attempt.clear()
        _pending_agent_assignments.clear()

    @pytest.fixture
    def mock_backlog_task(self):
        task = MagicMock()
        task.github_item_id = "PVTI_100"
        task.github_content_id = "I_100"
        task.issue_number = 100
        task.repository_owner = "owner"
        task.repository_name = "repo"
        task.title = "Stalled Issue"
        task.status = "Backlog"
        return task

    @pytest.fixture
    def mock_in_review_task(self):
        task = MagicMock()
        task.github_item_id = "PVTI_200"
        task.github_content_id = "I_200"
        task.issue_number = 200
        task.repository_owner = "owner"
        task.repository_name = "repo"
        task.title = "Reviewed Issue"
        task.status = "In Review"
        return task

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.get_workflow_config", new_callable=AsyncMock)
    async def test_returns_empty_when_no_config(self, mock_config):
        """Should return empty list when no workflow config exists."""
        mock_config.return_value = None

        results = await recover_stalled_issues(
            access_token="token",
            project_id="PVT_1",
            owner="owner",
            repo="repo",
            tasks=[],
        )

        assert results == []

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.get_workflow_config", new_callable=AsyncMock)
    async def test_skips_done_status(self, mock_config, mock_in_review_task):
        """Should skip issues that are Done (only truly terminal status)."""
        mock_config.return_value = MagicMock(
            status_in_review="In Review",
            agent_mappings={"Backlog": ["speckit.specify"]},
        )
        # Create a Done task — recovery should skip it
        done_task = MagicMock()
        done_task.github_item_id = "PVTI_300"
        done_task.github_content_id = "I_300"
        done_task.issue_number = 300
        done_task.repository_owner = "owner"
        done_task.repository_name = "repo"
        done_task.title = "Done Issue"
        done_task.status = "Done"

        results = await recover_stalled_issues(
            access_token="token",
            project_id="PVT_1",
            owner="owner",
            repo="repo",
            tasks=[done_task],
        )

        assert results == []

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    @patch("src.services.copilot_polling.get_workflow_config", new_callable=AsyncMock)
    async def test_skips_issues_with_all_agents_done(
        self, mock_config, mock_service, mock_backlog_task
    ):
        """Should skip issues where all agents are ✅ Done."""
        mock_config.return_value = MagicMock(
            status_in_review="In Review",
            agent_mappings={"Backlog": ["speckit.specify"]},
        )
        mock_service.get_issue_with_comments = AsyncMock(
            return_value={"body": self.TRACKING_BODY_ALL_DONE}
        )

        results = await recover_stalled_issues(
            access_token="token",
            project_id="PVT_1",
            owner="owner",
            repo="repo",
            tasks=[mock_backlog_task],
        )

        assert results == []

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.get_workflow_orchestrator")
    @patch("src.services.copilot_polling.get_issue_main_branch")
    @patch("src.services.copilot_polling.github_projects_service")
    @patch("src.services.copilot_polling.get_workflow_config", new_callable=AsyncMock)
    async def test_recovers_when_copilot_not_assigned_and_no_wip_pr(
        self, mock_config, mock_service, mock_get_branch, mock_get_orch, mock_backlog_task
    ):
        """Should re-assign agent when Copilot is not assigned and no WIP PR."""
        mock_config.return_value = MagicMock(
            status_in_review="In Review",
            agent_mappings={"Backlog": ["speckit.specify"]},
        )
        mock_service.get_issue_with_comments = AsyncMock(return_value={"body": self.TRACKING_BODY})
        mock_service.is_copilot_assigned_to_issue = AsyncMock(return_value=False)
        mock_service.get_linked_pull_requests = AsyncMock(return_value=[])
        mock_service.check_agent_completion_comment = AsyncMock(return_value=False)
        mock_get_branch.return_value = None

        mock_orchestrator = MagicMock()
        mock_orchestrator.assign_agent_for_status = AsyncMock(return_value=True)
        mock_get_orch.return_value = mock_orchestrator

        results = await recover_stalled_issues(
            access_token="token",
            project_id="PVT_1",
            owner="owner",
            repo="repo",
            tasks=[mock_backlog_task],
        )

        assert len(results) == 1
        assert results[0]["status"] == "recovered"
        assert results[0]["issue_number"] == 100
        assert results[0]["agent_name"] == "speckit.specify"
        assert "Copilot NOT assigned" in results[0]["missing"]
        assert "no WIP PR found" in results[0]["missing"]
        mock_orchestrator.assign_agent_for_status.assert_called_once()

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.get_workflow_orchestrator")
    @patch("src.services.copilot_polling.get_issue_main_branch")
    @patch("src.services.copilot_polling.github_projects_service")
    @patch("src.services.copilot_polling.get_workflow_config", new_callable=AsyncMock)
    async def test_recovers_when_copilot_assigned_but_no_wip_pr(
        self, mock_config, mock_service, mock_get_branch, mock_get_orch, mock_backlog_task
    ):
        """Should re-assign agent when Copilot is assigned but no WIP PR found."""
        mock_config.return_value = MagicMock(
            status_in_review="In Review",
            agent_mappings={"Backlog": ["speckit.specify"]},
        )
        mock_service.get_issue_with_comments = AsyncMock(return_value={"body": self.TRACKING_BODY})
        mock_service.is_copilot_assigned_to_issue = AsyncMock(return_value=True)
        mock_service.get_linked_pull_requests = AsyncMock(return_value=[])
        mock_service.check_agent_completion_comment = AsyncMock(return_value=False)
        mock_get_branch.return_value = None

        mock_orchestrator = MagicMock()
        mock_orchestrator.assign_agent_for_status = AsyncMock(return_value=True)
        mock_get_orch.return_value = mock_orchestrator

        results = await recover_stalled_issues(
            access_token="token",
            project_id="PVT_1",
            owner="owner",
            repo="repo",
            tasks=[mock_backlog_task],
        )

        assert len(results) == 1
        assert results[0]["missing"] == ["no WIP PR found"]

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.get_issue_main_branch")
    @patch("src.services.copilot_polling.github_projects_service")
    @patch("src.services.copilot_polling.get_workflow_config", new_callable=AsyncMock)
    async def test_no_recovery_when_agent_healthy(
        self, mock_config, mock_service, mock_get_branch, mock_backlog_task
    ):
        """Should not recover when Copilot is assigned and WIP PR exists."""
        mock_config.return_value = MagicMock(
            status_in_review="In Review",
            agent_mappings={"Backlog": ["speckit.specify"]},
        )
        mock_service.get_issue_with_comments = AsyncMock(return_value={"body": self.TRACKING_BODY})
        mock_service.is_copilot_assigned_to_issue = AsyncMock(return_value=True)
        mock_service.get_linked_pull_requests = AsyncMock(
            return_value=[
                {"number": 50, "state": "OPEN", "author": "copilot[bot]"},
            ]
        )
        mock_service.get_pull_request = AsyncMock(
            return_value={
                "is_draft": True,
                "base_ref": "main",
                "head_ref": "copilot/feature",
            }
        )
        mock_service.check_copilot_session_error = AsyncMock(return_value=False)
        mock_get_branch.return_value = None

        results = await recover_stalled_issues(
            access_token="token",
            project_id="PVT_1",
            owner="owner",
            repo="repo",
            tasks=[mock_backlog_task],
        )

        assert results == []

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.get_workflow_orchestrator")
    @patch("src.services.copilot_polling.get_issue_main_branch")
    @patch("src.services.copilot_polling.github_projects_service")
    @patch("src.services.copilot_polling.get_workflow_config", new_callable=AsyncMock)
    async def test_recovers_when_copilot_errored_on_wip_pr(
        self, mock_config, mock_service, mock_get_branch, mock_get_orch, mock_backlog_task
    ):
        """Should re-assign agent when Copilot has errored/stopped on the WIP PR."""
        mock_config.return_value = MagicMock(
            status_in_review="In Review",
            agent_mappings={"Backlog": ["speckit.specify"]},
        )
        mock_service.get_issue_with_comments = AsyncMock(return_value={"body": self.TRACKING_BODY})
        mock_service.is_copilot_assigned_to_issue = AsyncMock(return_value=True)
        mock_service.get_linked_pull_requests = AsyncMock(
            return_value=[
                {"number": 50, "state": "OPEN", "author": "copilot[bot]"},
            ]
        )
        mock_service.get_pull_request = AsyncMock(
            return_value={
                "is_draft": True,
                "base_ref": "main",
                "head_ref": "copilot/feature",
            }
        )
        # Copilot errored on the WIP PR
        mock_service.check_copilot_session_error = AsyncMock(return_value=True)
        mock_service.check_agent_completion_comment = AsyncMock(return_value=False)
        mock_get_branch.return_value = None

        mock_orchestrator = MagicMock()
        mock_orchestrator.assign_agent_for_status = AsyncMock(return_value=True)
        mock_get_orch.return_value = mock_orchestrator

        results = await recover_stalled_issues(
            access_token="token",
            project_id="PVT_1",
            owner="owner",
            repo="repo",
            tasks=[mock_backlog_task],
        )

        assert len(results) == 1
        assert results[0]["status"] == "recovered"
        assert results[0]["issue_number"] == 100
        assert results[0]["agent_name"] == "speckit.specify"
        assert "Copilot errored/stopped on PR #50" in results[0]["missing"]
        mock_orchestrator.assign_agent_for_status.assert_called_once()

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.get_issue_main_branch")
    @patch("src.services.copilot_polling.github_projects_service")
    @patch("src.services.copilot_polling.get_workflow_config", new_callable=AsyncMock)
    async def test_respects_cooldown(
        self, mock_config, mock_service, mock_get_branch, mock_backlog_task
    ):
        """Should skip issues within cooldown period."""
        mock_config.return_value = MagicMock(
            status_in_review="In Review",
            agent_mappings={"Backlog": ["speckit.specify"]},
        )

        # Set a recent recovery attempt within cooldown
        _recovery_last_attempt[100] = utcnow()

        results = await recover_stalled_issues(
            access_token="token",
            project_id="PVT_1",
            owner="owner",
            repo="repo",
            tasks=[mock_backlog_task],
        )

        assert results == []
        # Should NOT have called get_issue_with_comments since it's on cooldown
        mock_service.get_issue_with_comments.assert_not_called()

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.get_workflow_orchestrator")
    @patch("src.services.copilot_polling.get_issue_main_branch")
    @patch("src.services.copilot_polling.github_projects_service")
    @patch("src.services.copilot_polling.get_workflow_config", new_callable=AsyncMock)
    async def test_sets_cooldown_after_recovery(
        self, mock_config, mock_service, mock_get_branch, mock_get_orch, mock_backlog_task
    ):
        """Should set cooldown timestamp after recovery attempt."""
        mock_config.return_value = MagicMock(
            status_in_review="In Review",
            agent_mappings={"Backlog": ["speckit.specify"]},
        )
        mock_service.get_issue_with_comments = AsyncMock(return_value={"body": self.TRACKING_BODY})
        mock_service.is_copilot_assigned_to_issue = AsyncMock(return_value=False)
        mock_service.get_linked_pull_requests = AsyncMock(return_value=[])
        mock_service.check_agent_completion_comment = AsyncMock(return_value=False)
        mock_get_branch.return_value = None

        mock_orchestrator = MagicMock()
        mock_orchestrator.assign_agent_for_status = AsyncMock(return_value=True)
        mock_get_orch.return_value = mock_orchestrator

        assert 100 not in _recovery_last_attempt

        await recover_stalled_issues(
            access_token="token",
            project_id="PVT_1",
            owner="owner",
            repo="repo",
            tasks=[mock_backlog_task],
        )

        assert 100 in _recovery_last_attempt

    @pytest.mark.asyncio
    @patch(
        "src.services.copilot_polling.pipeline._self_heal_tracking_table", new_callable=AsyncMock
    )
    @patch("src.services.copilot_polling.github_projects_service")
    @patch("src.services.copilot_polling.get_workflow_config", new_callable=AsyncMock)
    async def test_skips_issues_without_tracking_table_after_self_heal_fails(
        self, mock_config, mock_service, mock_heal, mock_backlog_task
    ):
        """Should skip issues without a tracking table only after self-healing also fails."""
        mock_config.return_value = MagicMock(
            status_in_review="In Review",
            agent_mappings={"Backlog": ["speckit.specify"]},
        )
        mock_service.get_issue_with_comments = AsyncMock(
            return_value={"body": "Just a plain issue body with no tracking table."}
        )
        mock_heal.return_value = None  # Self-healing found no sub-issues

        results = await recover_stalled_issues(
            access_token="token",
            project_id="PVT_1",
            owner="owner",
            repo="repo",
            tasks=[mock_backlog_task],
        )

        assert results == []
        mock_heal.assert_called_once()

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    @patch("src.services.copilot_polling.get_workflow_config", new_callable=AsyncMock)
    async def test_skips_tasks_without_issue_number(self, mock_config, mock_service):
        """Should skip tasks without an issue number."""
        mock_config.return_value = MagicMock(
            status_in_review="In Review",
            agent_mappings={"Backlog": ["speckit.specify"]},
        )
        task = MagicMock()
        task.issue_number = None
        task.status = "Backlog"

        results = await recover_stalled_issues(
            access_token="token",
            project_id="PVT_1",
            owner="owner",
            repo="repo",
            tasks=[task],
        )

        assert results == []

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.get_issue_main_branch")
    @patch("src.services.copilot_polling.github_projects_service")
    @patch("src.services.copilot_polling.get_workflow_config", new_callable=AsyncMock)
    async def test_skips_recovery_when_done_marker_exists(
        self, mock_config, mock_service, mock_get_branch, mock_backlog_task
    ):
        """Should NOT re-assign when agents are already Done in GitHub.

        When the tracking table shows agents as Active/Pending but GitHub
        says they completed (Done! markers exist), the reconciliation
        corrects the table and recovery sees all agents as Done — no
        re-assignment needed.
        """
        mock_config.return_value = MagicMock(
            status_in_review="In Review",
            agent_mappings={"Backlog": ["speckit.specify"]},
        )
        mock_service.get_issue_with_comments = AsyncMock(return_value={"body": self.TRACKING_BODY})
        # Copilot unassigned (self-unassigned after completion)
        mock_service.is_copilot_assigned_to_issue = AsyncMock(return_value=False)
        # No WIP PR found
        mock_service.get_linked_pull_requests = AsyncMock(return_value=[])
        mock_get_branch.return_value = None
        # Done! marker IS present — agents already completed
        mock_service.check_agent_completion_comment = AsyncMock(return_value=True)
        mock_service.update_issue_body = AsyncMock()

        results = await recover_stalled_issues(
            access_token="token",
            project_id="PVT_1",
            owner="owner",
            repo="repo",
            tasks=[mock_backlog_task],
        )

        # Should NOT have recovered — Done! marker means agent completed
        assert results == []
        # Cooldown should still be set to avoid repeated checks
        assert 100 in _recovery_last_attempt

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.get_workflow_orchestrator")
    @patch("src.services.copilot_polling.get_issue_main_branch")
    @patch(
        "src.services.copilot_polling._check_agent_done_on_sub_or_parent",
        new_callable=AsyncMock,
    )
    @patch("src.services.copilot_polling.github_projects_service")
    @patch("src.services.copilot_polling.get_workflow_config", new_callable=AsyncMock)
    async def test_uses_durable_completion_when_tracking_table_is_stale(
        self,
        mock_config,
        mock_service,
        mock_check_done,
        mock_get_branch,
        mock_get_orch,
    ):
        """Recovery should not resurrect earlier agents from a stale table.

        If the issue body still shows earlier steps as pending but later steps
        already completed, recovery must recompute the expected agent from
        durable Done! markers instead of reassigning the first stale pending row.
        """
        tracking_body = (
            "## Issue Body\n\n"
            "---\n\n"
            "## 🤖 Agent Pipeline\n\n"
            "| # | Status | Agent | Model | State |\n"
            "|---|--------|-------|-------|-------|\n"
            "| 1 | In Progress | `speckit.tasks` | gpt-4o | ⏳ Pending |\n"
            "| 2 | In Progress | `speckit.implement` | gpt-4o | ⏳ Pending |\n"
            "| 3 | In Progress | `copilot-review` | gpt-4o | ✅ Done |\n"
            "| 4 | In Progress | `judge` | gpt-4o | ⏳ Pending |\n"
        )
        mock_config.return_value = MagicMock(
            status_in_review="In Review",
            agent_mappings={
                "In Progress": [
                    "speckit.tasks",
                    "speckit.implement",
                    "copilot-review",
                    "judge",
                ]
            },
        )
        mock_service.get_issue_with_comments = AsyncMock(return_value={"body": tracking_body})
        mock_service.is_copilot_assigned_to_issue = AsyncMock(return_value=False)
        mock_service.get_linked_pull_requests = AsyncMock(return_value=[])
        mock_get_branch.return_value = None

        async def done_side_effect(*, agent_name, **kwargs):
            return agent_name in {
                "speckit.tasks",
                "speckit.implement",
                "copilot-review",
            }

        mock_check_done.side_effect = done_side_effect

        mock_orchestrator = MagicMock()
        mock_orchestrator.assign_agent_for_status = AsyncMock(return_value=True)
        mock_get_orch.return_value = mock_orchestrator

        task = MagicMock()
        task.github_item_id = "PVTI_2104"
        task.github_content_id = "I_2104"
        task.issue_number = 2104
        task.repository_owner = "owner"
        task.repository_name = "repo"
        task.title = "Pipeline issue"
        task.status = "In Progress"

        results = await recover_stalled_issues(
            access_token="token",
            project_id="PVT_1",
            owner="owner",
            repo="repo",
            tasks=[task],
        )

        assert len(results) == 1
        assert results[0]["agent_name"] == "judge"
        mock_orchestrator.assign_agent_for_status.assert_awaited_once()
        args = mock_orchestrator.assign_agent_for_status.await_args.args
        assert args[1] == "In Progress"
        assert mock_orchestrator.assign_agent_for_status.await_args.kwargs["agent_index"] == 3

    @pytest.mark.asyncio
    @patch(
        "src.services.copilot_polling._check_agent_done_on_sub_or_parent",
        new_callable=AsyncMock,
        return_value=False,
    )
    @patch("src.services.copilot_polling.github_projects_service")
    @patch("src.services.copilot_polling.get_workflow_config", new_callable=AsyncMock)
    async def test_skips_copilot_review_agent_stall_checks(
        self, mock_config, mock_service, mock_check_done
    ):
        """Recovery should skip copilot_assigned / has_wip_pr for copilot-review.

        copilot-review is a non-coding agent — it never has Copilot SWE assigned
        and never creates a WIP PR.  Recovery should skip the stall detection
        logic and set the cooldown without triggering re-assignment.
        """
        tracking_body = (
            "## Issue Body\n\n"
            "---\n\n"
            "## 🤖 Agent Pipeline\n\n"
            "| # | Status | Agent | Model | State |\n"
            "|---|--------|-------|-------|-------|\n"
            "| 1 | In Progress | `copilot-review` | gpt-4o | 🔄 Active |\n"
            "| 2 | In Progress | `judge` | gpt-4o | ⏳ Pending |\n"
        )
        mock_config.return_value = MagicMock(
            status_in_review="In Review",
            agent_mappings={"In Progress": ["copilot-review", "judge"]},
        )
        mock_service.get_project_items = AsyncMock(return_value=[])
        mock_service.get_issue_with_comments = AsyncMock(return_value={"body": tracking_body})
        # If recovery incorrectly proceeds to stall checks, it would call these.
        # Mark them as side-effect to ensure they're NOT called.
        mock_service.is_copilot_assigned_to_issue = AsyncMock(return_value=False)
        mock_service.get_linked_pull_requests = AsyncMock(return_value=[])

        task = MagicMock()
        task.github_item_id = "PVTI_300"
        task.github_content_id = "I_300"
        task.issue_number = 300
        task.repository_owner = "owner"
        task.repository_name = "repo"
        task.title = "Copilot Review Issue"
        task.status = "In Progress"

        results = await recover_stalled_issues(
            access_token="token",
            project_id="PVT_1",
            owner="owner",
            repo="repo",
            tasks=[task],
        )

        # Should NOT have recovered — copilot-review is a non-coding agent
        assert results == []
        # Cooldown should be set
        assert 300 in _recovery_last_attempt
        # Stall detection APIs should NOT have been called
        mock_service.is_copilot_assigned_to_issue.assert_not_called()
        mock_service.get_linked_pull_requests.assert_not_called()

    @pytest.mark.asyncio
    @patch(
        "src.services.copilot_polling._check_agent_done_on_sub_or_parent",
        new_callable=AsyncMock,
        return_value=False,
    )
    @patch("src.services.copilot_polling.github_projects_service")
    @patch("src.services.copilot_polling.get_workflow_config", new_callable=AsyncMock)
    async def test_skips_human_agent_stall_checks(self, mock_config, mock_service, mock_check_done):
        """Recovery should skip copilot_assigned / has_wip_pr for human agent.

        The human agent waits for user action — Copilot SWE is never assigned
        and no WIP PR is expected.  Recovery should skip stall detection.
        """
        tracking_body = (
            "## Issue Body\n\n"
            "---\n\n"
            "## 🤖 Agent Pipeline\n\n"
            "| # | Status | Agent | Model | State |\n"
            "|---|--------|-------|-------|-------|\n"
            "| 1 | In Progress | `human` | gpt-4o | 🔄 Active |\n"
        )
        mock_config.return_value = MagicMock(
            status_in_review="In Review",
            agent_mappings={"In Progress": ["human"]},
        )
        mock_service.get_project_items = AsyncMock(return_value=[])
        mock_service.get_issue_with_comments = AsyncMock(return_value={"body": tracking_body})
        mock_service.is_copilot_assigned_to_issue = AsyncMock(return_value=False)
        mock_service.get_linked_pull_requests = AsyncMock(return_value=[])

        task = MagicMock()
        task.github_item_id = "PVTI_400"
        task.github_content_id = "I_400"
        task.issue_number = 400
        task.repository_owner = "owner"
        task.repository_name = "repo"
        task.title = "Human Review Issue"
        task.status = "In Progress"

        results = await recover_stalled_issues(
            access_token="token",
            project_id="PVT_1",
            owner="owner",
            repo="repo",
            tasks=[task],
        )

        assert results == []
        assert 400 in _recovery_last_attempt
        mock_service.is_copilot_assigned_to_issue.assert_not_called()
        mock_service.get_linked_pull_requests.assert_not_called()

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.get_issue_main_branch")
    @patch(
        "src.services.copilot_polling._find_completed_child_pr",
        new_callable=AsyncMock,
    )
    @patch("src.services.copilot_polling.github_projects_service")
    @patch("src.services.copilot_polling.get_workflow_config", new_callable=AsyncMock)
    async def test_skips_recovery_when_merged_child_pr_exists(
        self, mock_config, mock_service, mock_find_child, mock_get_branch, mock_backlog_task
    ):
        """Should NOT re-assign when a merged child PR exists without Done! marker.

        When a child PR was merged but the Done! comment was never posted
        (e.g., processing was interrupted), recovery should detect the merged
        child PR, post the missing Done! marker, and skip re-assignment —
        preventing duplicate branches/PRs.
        """
        mock_config.return_value = MagicMock(
            status_in_review="In Review",
            agent_mappings={"Backlog": ["speckit.specify"]},
        )
        mock_service.get_issue_with_comments = AsyncMock(return_value={"body": self.TRACKING_BODY})
        mock_service.is_copilot_assigned_to_issue = AsyncMock(return_value=False)
        mock_service.get_linked_pull_requests = AsyncMock(return_value=[])
        # No Done! marker exists
        mock_service.check_agent_completion_comment = AsyncMock(return_value=False)
        mock_service.update_issue_body = AsyncMock()
        mock_service.create_issue_comment = AsyncMock(return_value={"id": "comment_1"})

        # Main branch info exists (pipeline is active)
        mock_get_branch.return_value = {"branch": "copilot/implement-feature", "pr_number": 50}
        # Merged child PR found
        mock_find_child.return_value = {
            "number": 60,
            "id": "PR_60",
            "head_ref": "copilot/speckit-specify-feature",
            "base_ref": "copilot/implement-feature",
            "copilot_finished": True,
            "is_child_pr": True,
            "is_merged": True,
        }

        results = await recover_stalled_issues(
            access_token="token",
            project_id="PVT_1",
            owner="owner",
            repo="repo",
            tasks=[mock_backlog_task],
        )

        # Should NOT have recovered — merged child PR means agent completed
        assert results == []
        # Should have posted the missing Done! marker
        mock_service.create_issue_comment.assert_called_once_with(
            access_token="token",
            owner="owner",
            repo="repo",
            issue_number=100,
            body="speckit.specify: Done!",
        )
        # Cooldown should still be set
        assert 100 in _recovery_last_attempt

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.get_workflow_orchestrator")
    @patch("src.services.copilot_polling.get_issue_main_branch")
    @patch(
        "src.services.copilot_polling._find_completed_child_pr",
        new_callable=AsyncMock,
    )
    @patch("src.services.copilot_polling.github_projects_service")
    @patch("src.services.copilot_polling.get_workflow_config", new_callable=AsyncMock)
    async def test_recovers_when_no_main_branch_info_and_no_merged_child(
        self,
        mock_config,
        mock_service,
        mock_find_child,
        mock_get_branch,
        mock_get_orch,
        mock_backlog_task,
    ):
        """Should still re-assign when no main branch info exists (first agent).

        When get_issue_main_branch returns None, the merged-child-PR guard
        cannot run (there's no main branch to search against).  Recovery
        should fall through to re-assignment.
        """
        mock_config.return_value = MagicMock(
            status_in_review="In Review",
            agent_mappings={"Backlog": ["speckit.specify"]},
        )
        mock_service.get_issue_with_comments = AsyncMock(return_value={"body": self.TRACKING_BODY})
        mock_service.is_copilot_assigned_to_issue = AsyncMock(return_value=False)
        mock_service.get_linked_pull_requests = AsyncMock(return_value=[])
        mock_service.check_agent_completion_comment = AsyncMock(return_value=False)
        # No main branch info — first agent or lost state
        mock_get_branch.return_value = None

        mock_orchestrator = MagicMock()
        mock_orchestrator.assign_agent_for_status = AsyncMock(return_value=True)
        mock_get_orch.return_value = mock_orchestrator

        results = await recover_stalled_issues(
            access_token="token",
            project_id="PVT_1",
            owner="owner",
            repo="repo",
            tasks=[mock_backlog_task],
        )

        # Should have recovered — no main branch info means we can't check for merged child
        assert len(results) == 1
        assert results[0]["status"] == "recovered"
        # _find_completed_child_pr should NOT have been called
        mock_find_child.assert_not_called()

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.get_issue_main_branch")
    @patch(
        "src.services.copilot_polling._find_completed_child_pr",
        new_callable=AsyncMock,
    )
    @patch("src.services.copilot_polling.github_projects_service")
    @patch("src.services.copilot_polling.get_workflow_config", new_callable=AsyncMock)
    async def test_merged_child_pr_guard_tolerates_marker_post_failure(
        self, mock_config, mock_service, mock_find_child, mock_get_branch, mock_backlog_task
    ):
        """Should skip re-assignment even if posting the Done! marker fails.

        The merged child PR proves the agent completed.  If the self-heal
        fails to post the marker, recovery should still skip re-assignment
        to prevent duplicates.
        """
        mock_config.return_value = MagicMock(
            status_in_review="In Review",
            agent_mappings={"Backlog": ["speckit.specify"]},
        )
        mock_service.get_issue_with_comments = AsyncMock(return_value={"body": self.TRACKING_BODY})
        mock_service.is_copilot_assigned_to_issue = AsyncMock(return_value=False)
        mock_service.get_linked_pull_requests = AsyncMock(return_value=[])
        mock_service.check_agent_completion_comment = AsyncMock(return_value=False)
        mock_service.update_issue_body = AsyncMock()
        # Marker post fails
        mock_service.create_issue_comment = AsyncMock(side_effect=Exception("API error"))

        mock_get_branch.return_value = {"branch": "copilot/implement-feature", "pr_number": 50}
        mock_find_child.return_value = {
            "number": 60,
            "is_merged": True,
            "copilot_finished": True,
            "is_child_pr": True,
        }

        results = await recover_stalled_issues(
            access_token="token",
            project_id="PVT_1",
            owner="owner",
            repo="repo",
            tasks=[mock_backlog_task],
        )

        # Should NOT have recovered even though posting failed
        assert results == []
        assert 100 in _recovery_last_attempt


# ────────────────────────────────────────────────────────────────────
# _validate_and_reconcile_tracking_table
# ────────────────────────────────────────────────────────────────────


class TestValidateAndReconcileTrackingTable:
    """Tests for tracking table validation against GitHub ground truth."""

    BODY_ACTIVE_PENDING = (
        "## Issue Body\n\n"
        "---\n\n"
        "## 🤖 Agents Pipelines\n\n"
        "| # | Status | Agent | Model | State |\n"
        "|---|--------|-------|-------|-------|\n"
        "| 1 | Backlog | `speckit.specify` | gpt-4o | 🔄 Active |\n"
        "| 2 | Ready | `speckit.plan` | gpt-4o | ⏳ Pending |\n"
    )

    BODY_ALL_PENDING = (
        "## Issue Body\n\n"
        "---\n\n"
        "## 🤖 Agents Pipelines\n\n"
        "| # | Status | Agent | Model | State |\n"
        "|---|--------|-------|-------|-------|\n"
        "| 1 | In Progress | `speckit.tasks` | gpt-4o | ⏳ Pending |\n"
        "| 2 | In Progress | `speckit.implement` | gpt-4o | ⏳ Pending |\n"
        "| 3 | In Progress | `copilot-review` | gpt-4o | ⏳ Pending |\n"
        "| 4 | In Progress | `judge` | gpt-4o | ⏳ Pending |\n"
    )

    @pytest.mark.asyncio
    @patch(
        "src.services.copilot_polling._check_agent_done_on_sub_or_parent",
        new_callable=AsyncMock,
        return_value=False,
    )
    @patch("src.services.copilot_polling.github_projects_service")
    async def test_no_corrections_when_table_matches_github(self, mock_service, mock_check_done):
        """No corrections when GitHub agrees with the tracking table."""
        from src.services.agent_tracking import parse_tracking_from_body

        steps = parse_tracking_from_body(self.BODY_ACTIVE_PENDING)
        updated_body, updated_steps, corrected = await _validate_and_reconcile_tracking_table(
            access_token="token",
            owner="owner",
            repo="repo",
            issue_number=100,
            body=self.BODY_ACTIVE_PENDING,
            steps=steps,
            pipeline=None,
        )

        assert corrected is False
        assert updated_body == self.BODY_ACTIVE_PENDING
        assert updated_steps is steps
        mock_service.update_issue_body.assert_not_called()

    @pytest.mark.asyncio
    @patch(
        "src.services.copilot_polling._check_agent_done_on_sub_or_parent",
        new_callable=AsyncMock,
    )
    @patch("src.services.copilot_polling.github_projects_service")
    async def test_corrects_active_agent_to_done(self, mock_service, mock_check_done):
        """Active agent corrected to Done when GitHub has Done! marker."""
        from src.services.agent_tracking import STATE_DONE, parse_tracking_from_body

        async def side_effect(*, agent_name, **kwargs):
            return agent_name == "speckit.specify"

        mock_check_done.side_effect = side_effect
        mock_service.update_issue_body = AsyncMock()

        steps = parse_tracking_from_body(self.BODY_ACTIVE_PENDING)
        _updated_body, updated_steps, corrected = await _validate_and_reconcile_tracking_table(
            access_token="token",
            owner="owner",
            repo="repo",
            issue_number=100,
            body=self.BODY_ACTIVE_PENDING,
            steps=steps,
            pipeline=None,
        )

        assert corrected is True
        assert STATE_DONE in updated_steps[0].state
        assert "Pending" in updated_steps[1].state
        mock_service.update_issue_body.assert_awaited_once()
        pushed_body = mock_service.update_issue_body.call_args.kwargs["body"]
        assert "✅ Done" in pushed_body
        assert "⏳ Pending" in pushed_body

    @pytest.mark.asyncio
    @patch(
        "src.services.copilot_polling._check_agent_done_on_sub_or_parent",
        new_callable=AsyncMock,
    )
    @patch("src.services.copilot_polling.github_projects_service")
    async def test_corrects_pending_agent_to_done(self, mock_service, mock_check_done):
        """Pending agent corrected to Done when GitHub has Done! marker."""
        from src.services.agent_tracking import STATE_DONE, parse_tracking_from_body

        async def side_effect(*, agent_name, **kwargs):
            return agent_name == "speckit.plan"

        mock_check_done.side_effect = side_effect
        mock_service.update_issue_body = AsyncMock()

        steps = parse_tracking_from_body(self.BODY_ACTIVE_PENDING)
        _updated_body, updated_steps, corrected = await _validate_and_reconcile_tracking_table(
            access_token="token",
            owner="owner",
            repo="repo",
            issue_number=100,
            body=self.BODY_ACTIVE_PENDING,
            steps=steps,
            pipeline=None,
        )

        assert corrected is True
        assert "Active" in updated_steps[0].state
        assert STATE_DONE in updated_steps[1].state
        mock_service.update_issue_body.assert_awaited_once()

    @pytest.mark.asyncio
    @patch(
        "src.services.copilot_polling._check_agent_done_on_sub_or_parent",
        new_callable=AsyncMock,
        return_value=True,
    )
    @patch("src.services.copilot_polling.github_projects_service")
    async def test_corrects_multiple_agents_in_one_pass(self, mock_service, mock_check_done):
        """All out-of-sync agents corrected in a single reconciliation pass."""
        from src.services.agent_tracking import STATE_DONE, parse_tracking_from_body

        mock_service.update_issue_body = AsyncMock()

        steps = parse_tracking_from_body(self.BODY_ALL_PENDING)
        _, updated_steps, corrected = await _validate_and_reconcile_tracking_table(
            access_token="token",
            owner="owner",
            repo="repo",
            issue_number=200,
            body=self.BODY_ALL_PENDING,
            steps=steps,
            pipeline=None,
        )

        assert corrected is True
        assert all(STATE_DONE in s.state for s in updated_steps)
        mock_service.update_issue_body.assert_awaited_once()

    @pytest.mark.asyncio
    @patch(
        "src.services.copilot_polling._check_agent_done_on_sub_or_parent",
        new_callable=AsyncMock,
        return_value=True,
    )
    @patch("src.services.copilot_polling.github_projects_service")
    async def test_continues_with_corrected_state_when_push_fails(
        self, mock_service, mock_check_done
    ):
        """In-memory corrections survive even when pushing to GitHub fails."""
        from src.services.agent_tracking import STATE_DONE, parse_tracking_from_body

        mock_service.update_issue_body = AsyncMock(side_effect=RuntimeError("API error"))

        steps = parse_tracking_from_body(self.BODY_ACTIVE_PENDING)
        _updated_body, updated_steps, corrected = await _validate_and_reconcile_tracking_table(
            access_token="token",
            owner="owner",
            repo="repo",
            issue_number=100,
            body=self.BODY_ACTIVE_PENDING,
            steps=steps,
            pipeline=None,
        )

        assert corrected is True
        assert all(STATE_DONE in s.state for s in updated_steps)

    @pytest.mark.asyncio
    @patch(
        "src.services.copilot_polling._check_agent_done_on_sub_or_parent",
        new_callable=AsyncMock,
        return_value=True,
    )
    @patch("src.services.copilot_polling.github_projects_service")
    async def test_skips_already_done_agents(self, mock_service, mock_check_done):
        """Agents already marked Done should not be re-corrected."""
        from src.services.agent_tracking import parse_tracking_from_body

        body = (
            "## Issue Body\n\n"
            "---\n\n"
            "## 🤖 Agents Pipelines\n\n"
            "| # | Status | Agent | Model | State |\n"
            "|---|--------|-------|-------|-------|\n"
            "| 1 | Backlog | `speckit.specify` | gpt-4o | ✅ Done |\n"
            "| 2 | Ready | `speckit.plan` | gpt-4o | ✅ Done |\n"
        )
        steps = parse_tracking_from_body(body)
        updated_body, _updated_steps, corrected = await _validate_and_reconcile_tracking_table(
            access_token="token",
            owner="owner",
            repo="repo",
            issue_number=100,
            body=body,
            steps=steps,
            pipeline=None,
        )

        assert corrected is False
        assert updated_body == body
        mock_service.update_issue_body.assert_not_called()

    @pytest.mark.asyncio
    @patch(
        "src.services.copilot_polling._check_agent_done_on_sub_or_parent",
        new_callable=AsyncMock,
    )
    @patch("src.services.copilot_polling.github_projects_service")
    async def test_end_to_end_recovery_with_stale_table(self, mock_service, mock_check_done):
        """Integration: stale table gets reconciled then recovery assigns correct agent.

        Table shows all Pending but first 3 agents are Done in GitHub.
        Recovery should correct the table and re-assign the 4th agent (judge).
        """
        mock_config = MagicMock(
            status_in_review="In Review",
            status_done="Done",
            agent_mappings={
                "In Progress": ["speckit.tasks", "speckit.implement", "copilot-review", "judge"],
            },
        )
        mock_service.get_issue_with_comments = AsyncMock(
            return_value={"body": self.BODY_ALL_PENDING}
        )
        mock_service.update_issue_body = AsyncMock()
        mock_service.is_copilot_assigned_to_issue = AsyncMock(return_value=False)
        mock_service.get_linked_pull_requests = AsyncMock(return_value=[])

        async def done_side_effect(*, agent_name, **kwargs):
            return agent_name in {"speckit.tasks", "speckit.implement", "copilot-review"}

        mock_check_done.side_effect = done_side_effect

        mock_orchestrator = MagicMock()
        mock_orchestrator.assign_agent_for_status = AsyncMock(return_value=True)

        task = MagicMock()
        task.github_item_id = "PVTI_E2E"
        task.github_content_id = "I_E2E"
        task.issue_number = 500
        task.repository_owner = "owner"
        task.repository_name = "repo"
        task.title = "E2E stale table"
        task.status = "In Progress"

        _recovery_last_attempt.clear()
        _pending_agent_assignments.clear()

        with (
            patch(
                "src.services.copilot_polling.get_workflow_config",
                new_callable=AsyncMock,
                return_value=mock_config,
            ),
            patch(
                "src.services.copilot_polling.get_issue_main_branch",
                return_value=None,
            ),
            patch(
                "src.services.copilot_polling.get_workflow_orchestrator",
                return_value=mock_orchestrator,
            ),
        ):
            results = await recover_stalled_issues(
                access_token="token",
                project_id="PVT_1",
                owner="owner",
                repo="repo",
                tasks=[task],
            )

        assert len(results) == 1
        assert results[0]["agent_name"] == "judge"
        assert results[0]["status"] == "recovered"
        # The orchestrator should assign judge (index 3 in the In Progress mapping)
        mock_orchestrator.assign_agent_for_status.assert_awaited_once()
        kwargs = mock_orchestrator.assign_agent_for_status.await_args.kwargs
        assert kwargs["agent_index"] == 3

        _recovery_last_attempt.clear()
        _pending_agent_assignments.clear()


# ────────────────────────────────────────────────────────────────────
# ensure_copilot_review_requested  (~80 uncovered lines)
# ────────────────────────────────────────────────────────────────────


class TestEnsureCopilotReviewRequested:
    """Tests for ensure_copilot_review_requested."""

    @pytest.fixture(autouse=True)
    def _clear(self):
        from src.services.copilot_polling.state import _review_requested_cache

        _processed_issue_prs.clear()
        _review_requested_cache.clear()
        yield
        _processed_issue_prs.clear()
        _review_requested_cache.clear()

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    async def test_already_cached_returns_none(self, mock_service):
        from src.services.copilot_polling import cache_key_review_requested

        key = cache_key_review_requested(42, "PVT_1")
        _processed_issue_prs.add(key)
        result = await ensure_copilot_review_requested("tok", "o", "r", "PVT_1", 42, "title")
        assert result is None

    @pytest.mark.asyncio
    @patch(
        "src.services.copilot_polling.helpers._discover_main_pr_for_review", new_callable=AsyncMock
    )
    @patch("src.services.copilot_polling.github_projects_service")
    async def test_no_pr_discovered_returns_none(self, mock_service, mock_discover):
        mock_discover.return_value = None
        result = await ensure_copilot_review_requested("tok", "o", "r", "PVT_1", 42, "title")
        assert result is None

    @pytest.mark.asyncio
    @patch(
        "src.services.copilot_polling.helpers._discover_main_pr_for_review", new_callable=AsyncMock
    )
    @patch("src.services.copilot_polling.github_projects_service")
    async def test_missing_pr_number_returns_none(self, mock_service, mock_discover):
        mock_discover.return_value = {"pr_number": None, "pr_id": "PR_N", "is_draft": False}
        result = await ensure_copilot_review_requested("tok", "o", "r", "PVT_1", 42, "title")
        assert result is None

    @pytest.mark.asyncio
    @patch(
        "src.services.copilot_polling.helpers._discover_main_pr_for_review", new_callable=AsyncMock
    )
    @patch("src.services.copilot_polling.github_projects_service")
    async def test_dismisses_auto_triggered_before_requesting(self, mock_service, mock_discover):
        """Auto-triggered reviews are dismissed before Solune requests its own review."""
        mock_discover.return_value = {
            "pr_number": 10,
            "pr_id": "PR_N",
            "is_draft": False,
            "head_ref": "b",
        }
        mock_service.dismiss_copilot_reviews = AsyncMock(return_value=1)
        mock_service.request_copilot_review = AsyncMock(return_value=True)
        mock_service.get_issue_with_comments = AsyncMock(
            return_value={"title": "", "body": "", "comments": [], "user": {"login": ""}}
        )
        mock_service.update_issue_body = AsyncMock(return_value=True)

        result = await ensure_copilot_review_requested("tok", "o", "r", "PVT_1", 42, "title")
        assert result is not None
        assert result["action"] == "copilot_review_requested"
        # Dismiss should be called before the review request
        mock_service.dismiss_copilot_reviews.assert_awaited_once()
        mock_service.request_copilot_review.assert_awaited_once()

    @pytest.mark.asyncio
    @patch(
        "src.services.copilot_polling.helpers._discover_main_pr_for_review", new_callable=AsyncMock
    )
    @patch("src.services.copilot_polling.github_projects_service")
    async def test_review_requested_successfully(self, mock_service, mock_discover):
        mock_discover.return_value = {
            "pr_number": 10,
            "pr_id": "PR_N",
            "is_draft": False,
            "head_ref": "b",
        }
        mock_service.dismiss_copilot_reviews = AsyncMock(return_value=0)
        mock_service.request_copilot_review = AsyncMock(return_value=True)
        mock_service.get_issue_with_comments = AsyncMock(
            return_value={"title": "", "body": "", "comments": [], "user": {"login": ""}}
        )
        mock_service.update_issue_body = AsyncMock(return_value=True)

        result = await ensure_copilot_review_requested("tok", "o", "r", "PVT_1", 42, "my task")
        assert result is not None
        assert result["action"] == "copilot_review_requested"
        assert result["pr_number"] == 10

    @pytest.mark.asyncio
    @patch(
        "src.services.copilot_polling.helpers._discover_main_pr_for_review", new_callable=AsyncMock
    )
    @patch("src.services.copilot_polling.github_projects_service")
    async def test_review_request_fails(self, mock_service, mock_discover):
        mock_discover.return_value = {
            "pr_number": 10,
            "pr_id": "PR_N",
            "is_draft": False,
            "head_ref": "b",
        }
        mock_service.dismiss_copilot_reviews = AsyncMock(return_value=0)
        mock_service.request_copilot_review = AsyncMock(return_value=False)

        result = await ensure_copilot_review_requested("tok", "o", "r", "PVT_1", 42, "my task")
        assert result is not None
        assert result["status"] == "error"

    @pytest.mark.asyncio
    @patch(
        "src.services.copilot_polling.helpers._discover_main_pr_for_review", new_callable=AsyncMock
    )
    @patch("src.services.copilot_polling.github_projects_service")
    async def test_exception_returns_none(self, mock_service, mock_discover):
        mock_discover.side_effect = Exception("boom")
        result = await ensure_copilot_review_requested("tok", "o", "r", "PVT_1", 42, "title")
        assert result is None

    @pytest.mark.asyncio
    @patch(
        "src.services.copilot_polling.helpers._discover_main_pr_for_review", new_callable=AsyncMock
    )
    @patch("src.services.copilot_polling.github_projects_service")
    async def test_draft_pr_converted_to_ready(self, mock_service, mock_discover):
        """When the discovered PR is draft, it should be converted to ready before review."""
        mock_discover.return_value = {
            "pr_number": 10,
            "pr_id": "PR_N",
            "is_draft": True,
            "head_ref": "b",
        }
        mock_service.mark_pr_ready_for_review = AsyncMock(return_value=True)
        mock_service.dismiss_copilot_reviews = AsyncMock(return_value=0)
        mock_service.request_copilot_review = AsyncMock(return_value=True)
        mock_service.get_issue_with_comments = AsyncMock(
            return_value={"title": "", "body": "", "comments": [], "user": {"login": ""}}
        )
        mock_service.update_issue_body = AsyncMock(return_value=True)

        result = await ensure_copilot_review_requested("tok", "o", "r", "PVT_1", 42, "task")
        assert result is not None
        assert result["action"] == "copilot_review_requested"
        mock_service.mark_pr_ready_for_review.assert_awaited_once()


# ────────────────────────────────────────────────────────────────────
# check_in_review_issues_for_copilot_review  (~41 uncovered lines)
# ────────────────────────────────────────────────────────────────────


class TestCheckInReviewIssues:
    """Tests for check_in_review_issues_for_copilot_review."""

    @pytest.mark.asyncio
    @patch(
        "src.services.copilot_polling.completion._cp.get_workflow_config", new_callable=AsyncMock
    )
    @patch(
        "src.services.copilot_polling.completion._cp._get_or_reconstruct_pipeline",
        new_callable=AsyncMock,
    )
    @patch("src.services.copilot_polling.completion.ensure_copilot_review_requested")
    @patch("src.services.copilot_polling.github_projects_service")
    async def test_no_in_review_tasks(
        self,
        mock_service,
        mock_ensure,
        mock_get_pipeline,
        mock_get_config,
    ):
        task = MagicMock(status="In Progress", issue_number=1)
        mock_service.get_project_items = AsyncMock(return_value=[task])
        mock_get_config.return_value = MagicMock(status_in_review="In Review")

        results = await check_in_review_issues_for_copilot_review("tok", "P1", "o", "r")
        assert results == []
        mock_ensure.assert_not_awaited()
        mock_get_pipeline.assert_not_awaited()

    @pytest.mark.asyncio
    @patch(
        "src.services.copilot_polling.completion._cp.get_workflow_config", new_callable=AsyncMock
    )
    @patch(
        "src.services.copilot_polling.completion._cp._get_or_reconstruct_pipeline",
        new_callable=AsyncMock,
    )
    @patch("src.services.copilot_polling.completion.ensure_copilot_review_requested")
    @patch("src.services.copilot_polling.github_projects_service")
    async def test_processes_in_review_tasks(
        self,
        mock_service,
        mock_ensure,
        mock_get_pipeline,
        mock_get_config,
    ):
        task = MagicMock(
            status="In Review",
            issue_number=42,
            repository_owner="o",
            repository_name="r",
            title="My Task",
            labels=[],
        )
        mock_service.get_project_items = AsyncMock(return_value=[task])
        mock_ensure.return_value = {"action": "copilot_review_requested"}
        mock_get_config.return_value = MagicMock(
            status_in_review="In Review",
            agent_mappings={"In Review": [MagicMock(slug="human")]},
        )
        mock_get_pipeline.return_value = PipelineState(
            issue_number=42,
            project_id="P1",
            status="In Progress",
            agents=["speckit.implement", "copilot-review", "linter", "judge"],
            current_agent_index=1,
            completed_agents=["speckit.implement"],
        )

        results = await check_in_review_issues_for_copilot_review("tok", "P1", "o", "r")
        assert len(results) == 1
        mock_ensure.assert_awaited_once()

    @pytest.mark.asyncio
    @patch(
        "src.services.copilot_polling.completion._cp.get_workflow_config", new_callable=AsyncMock
    )
    @patch(
        "src.services.copilot_polling.completion._cp._get_or_reconstruct_pipeline",
        new_callable=AsyncMock,
    )
    @patch("src.services.copilot_polling.completion.ensure_copilot_review_requested")
    @patch("src.services.copilot_polling.github_projects_service")
    async def test_none_results_filtered_out(
        self,
        mock_service,
        mock_ensure,
        mock_get_pipeline,
        mock_get_config,
    ):
        task = MagicMock(
            status="In Review",
            issue_number=42,
            repository_owner="o",
            repository_name="r",
            title="T",
            labels=[],
        )
        mock_service.get_project_items = AsyncMock(return_value=[task])
        mock_ensure.return_value = None  # already processed
        mock_get_config.return_value = MagicMock(
            status_in_review="In Review",
            agent_mappings={"In Review": [MagicMock(slug="human")]},
        )
        mock_get_pipeline.return_value = PipelineState(
            issue_number=42,
            project_id="P1",
            status="In Progress",
            agents=["copilot-review", "judge"],
            current_agent_index=0,
        )

        results = await check_in_review_issues_for_copilot_review("tok", "P1", "o", "r")
        assert results == []

    @pytest.mark.asyncio
    @patch(
        "src.services.copilot_polling.completion._cp.get_workflow_config", new_callable=AsyncMock
    )
    @patch("src.services.copilot_polling.github_projects_service")
    async def test_exception_returns_empty(self, mock_service, mock_get_config):
        mock_service.get_project_items = AsyncMock(side_effect=Exception("err"))
        mock_get_config.return_value = MagicMock(status_in_review="In Review")
        results = await check_in_review_issues_for_copilot_review("tok", "P1", "o", "r")
        assert results == []

    @pytest.mark.asyncio
    @patch(
        "src.services.copilot_polling.completion._cp.get_workflow_config", new_callable=AsyncMock
    )
    @patch(
        "src.services.copilot_polling.completion._cp._get_or_reconstruct_pipeline",
        new_callable=AsyncMock,
    )
    @patch("src.services.copilot_polling.completion.ensure_copilot_review_requested")
    @patch("src.services.copilot_polling.github_projects_service")
    async def test_skips_tasks_without_issue_number(
        self,
        mock_service,
        mock_ensure,
        mock_get_pipeline,
        mock_get_config,
    ):
        task = MagicMock(status="In Review", issue_number=None)
        mock_service.get_project_items = AsyncMock(return_value=[task])
        mock_get_config.return_value = MagicMock(status_in_review="In Review")
        results = await check_in_review_issues_for_copilot_review("tok", "P1", "o", "r")
        assert results == []
        mock_ensure.assert_not_awaited()
        mock_get_pipeline.assert_not_awaited()

    @pytest.mark.asyncio
    @patch(
        "src.services.copilot_polling.completion._cp.get_workflow_config", new_callable=AsyncMock
    )
    @patch(
        "src.services.copilot_polling.completion._cp._get_or_reconstruct_pipeline",
        new_callable=AsyncMock,
    )
    @patch("src.services.copilot_polling.completion.ensure_copilot_review_requested")
    @patch("src.services.copilot_polling.github_projects_service")
    async def test_skips_when_board_is_in_review_but_pipeline_has_not_reached_copilot_review(
        self,
        mock_service,
        mock_ensure,
        mock_get_pipeline,
        mock_get_config,
    ):
        task = MagicMock(
            status="In Review",
            issue_number=4728,
            repository_owner="o",
            repository_name="r",
            title="My Task",
            labels=[],
        )
        mock_service.get_project_items = AsyncMock(return_value=[task])
        mock_get_config.return_value = MagicMock(
            status_in_review="In Review",
            agent_mappings={"In Review": [MagicMock(slug="human")]},
        )
        mock_get_pipeline.return_value = PipelineState(
            issue_number=4728,
            project_id="P1",
            status="In Progress",
            agents=["speckit.implement", "copilot-review", "linter", "judge"],
            current_agent_index=3,
            completed_agents=["speckit.implement", "copilot-review", "linter"],
        )

        results = await check_in_review_issues_for_copilot_review("tok", "P1", "o", "r")

        assert results == []
        mock_ensure.assert_not_awaited()

    @pytest.mark.asyncio
    @patch(
        "src.services.copilot_polling.completion._cp.get_workflow_config", new_callable=AsyncMock
    )
    @patch(
        "src.services.copilot_polling.completion._cp._get_or_reconstruct_pipeline",
        new_callable=AsyncMock,
    )
    @patch("src.services.copilot_polling.completion.ensure_copilot_review_requested")
    @patch("src.services.copilot_polling.github_projects_service")
    async def test_requests_when_copilot_review_is_in_active_parallel_group(
        self,
        mock_service,
        mock_ensure,
        mock_get_pipeline,
        mock_get_config,
    ):
        from src.services.workflow_orchestrator.models import PipelineGroupInfo

        task = MagicMock(
            status="In Review",
            issue_number=4728,
            repository_owner="o",
            repository_name="r",
            title="My Task",
            labels=[],
        )
        mock_service.get_project_items = AsyncMock(return_value=[task])
        mock_get_config.return_value = MagicMock(
            status_in_review="In Review",
            agent_mappings={"In Review": [MagicMock(slug="human")]},
        )
        mock_ensure.return_value = {"action": "copilot_review_requested"}
        mock_get_pipeline.return_value = PipelineState(
            issue_number=4728,
            project_id="P1",
            status="In Progress",
            agents=["speckit.implement", "copilot-review", "linter", "judge"],
            current_agent_index=1,
            completed_agents=["speckit.implement"],
            groups=[
                PipelineGroupInfo(
                    group_id="g1",
                    execution_mode="sequential",
                    agents=["speckit.implement"],
                ),
                PipelineGroupInfo(
                    group_id="g2",
                    execution_mode="parallel",
                    agents=["copilot-review", "linter"],
                    agent_statuses={"copilot-review": "active", "linter": "active"},
                ),
                PipelineGroupInfo(
                    group_id="g3",
                    execution_mode="sequential",
                    agents=["judge"],
                ),
            ],
            current_group_index=1,
            current_agent_index_in_group=0,
        )

        results = await check_in_review_issues_for_copilot_review("tok", "P1", "o", "r")

        assert len(results) == 1
        mock_ensure.assert_awaited_once()


# ────────────────────────────────────────────────────────────────────
# _check_main_pr_completion — commit-based detection  (~114 uncovered lines)
# ────────────────────────────────────────────────────────────────────


class TestCheckMainPrCompletionCommitBased:
    """Tests for _check_main_pr_completion commit-based + Copilot-unassigned detection."""

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    async def test_new_commits_copilot_unassigned(self, mock_service):
        """New commits + Copilot unassigned → True."""
        mock_service.get_pull_request = AsyncMock(
            return_value={
                "is_draft": True,
                "state": "OPEN",
                "last_commit": {"sha": "new_sha_abc"},
            }
        )
        mock_service.get_pr_timeline_events = AsyncMock(return_value=[])
        mock_service.check_copilot_finished_events = Mock(return_value=False)
        mock_service.is_copilot_assigned_to_issue = AsyncMock(return_value=False)

        result = await _check_main_pr_completion(
            access_token="tok",
            owner="o",
            repo="r",
            main_pr_number=10,
            issue_number=42,
            agent_name="myagent",
            pipeline_started_at=utcnow(),
            agent_assigned_sha="old_sha_xyz",
        )
        assert result is True

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    async def test_new_commits_copilot_still_assigned(self, mock_service):
        """New commits but Copilot still assigned → False (still working)."""
        mock_service.get_pull_request = AsyncMock(
            return_value={
                "is_draft": True,
                "state": "OPEN",
                "last_commit": {"sha": "new_sha"},
            }
        )
        mock_service.get_pr_timeline_events = AsyncMock(return_value=[])
        mock_service.check_copilot_finished_events = Mock(return_value=False)
        mock_service.is_copilot_assigned_to_issue = AsyncMock(return_value=True)

        result = await _check_main_pr_completion(
            "tok",
            "o",
            "r",
            10,
            42,
            "myagent",
            pipeline_started_at=utcnow(),
            agent_assigned_sha="old_sha",
        )
        assert result is False

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    async def test_sha_unchanged_copilot_unassigned(self, mock_service):
        """SHA unchanged but Copilot unassigned → False (no code committed, FR-007)."""
        mock_service.get_pull_request = AsyncMock(
            return_value={
                "is_draft": True,
                "state": "OPEN",
                "last_commit": {"sha": "same_sha"},
            }
        )
        mock_service.get_pr_timeline_events = AsyncMock(return_value=[])
        mock_service.check_copilot_finished_events = Mock(return_value=False)
        mock_service.is_copilot_assigned_to_issue = AsyncMock(return_value=False)

        result = await _check_main_pr_completion(
            "tok",
            "o",
            "r",
            10,
            42,
            "myagent",
            pipeline_started_at=utcnow(),
            agent_assigned_sha="same_sha",
        )
        assert result is False

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    async def test_sha_unchanged_copilot_still_assigned(self, mock_service):
        """SHA unchanged + Copilot still assigned → False."""
        mock_service.get_pull_request = AsyncMock(
            return_value={
                "is_draft": True,
                "state": "OPEN",
                "last_commit": {"sha": "same_sha"},
            }
        )
        mock_service.get_pr_timeline_events = AsyncMock(return_value=[])
        mock_service.check_copilot_finished_events = Mock(return_value=False)
        mock_service.is_copilot_assigned_to_issue = AsyncMock(return_value=True)

        result = await _check_main_pr_completion(
            "tok",
            "o",
            "r",
            10,
            42,
            "myagent",
            pipeline_started_at=utcnow(),
            agent_assigned_sha="same_sha",
        )
        assert result is False

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    async def test_no_sha_copilot_unassigned_fresh_commit(self, mock_service):
        """No assigned SHA + Copilot unassigned + fresh commit → True."""
        recent = (datetime.now(UTC) + timedelta(hours=1)).isoformat()
        mock_service.get_pull_request = AsyncMock(
            return_value={
                "is_draft": True,
                "state": "OPEN",
                "last_commit": {"sha": "abc", "committed_date": recent},
            }
        )
        mock_service.get_pr_timeline_events = AsyncMock(return_value=[])
        mock_service.check_copilot_finished_events = Mock(return_value=False)
        mock_service.is_copilot_assigned_to_issue = AsyncMock(return_value=False)

        result = await _check_main_pr_completion(
            "tok",
            "o",
            "r",
            10,
            42,
            "myagent",
            pipeline_started_at=utcnow() - timedelta(hours=2),
            agent_assigned_sha="",
        )
        assert result is True

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    async def test_no_sha_copilot_unassigned_stale_commit(self, mock_service):
        """No assigned SHA + Copilot unassigned + stale commit → False."""
        old_time = (datetime.now(UTC) - timedelta(days=5)).isoformat()
        mock_service.get_pull_request = AsyncMock(
            return_value={
                "is_draft": True,
                "state": "OPEN",
                "last_commit": {"sha": "abc", "committed_date": old_time},
            }
        )
        mock_service.get_pr_timeline_events = AsyncMock(return_value=[])
        mock_service.check_copilot_finished_events = Mock(return_value=False)
        mock_service.is_copilot_assigned_to_issue = AsyncMock(return_value=False)

        result = await _check_main_pr_completion(
            "tok",
            "o",
            "r",
            10,
            42,
            "myagent",
            pipeline_started_at=utcnow(),
            agent_assigned_sha="",
        )
        assert result is False

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    async def test_no_sha_copilot_still_assigned(self, mock_service):
        """No assigned SHA + Copilot still assigned → False."""
        mock_service.get_pull_request = AsyncMock(
            return_value={
                "is_draft": True,
                "state": "OPEN",
                "last_commit": {"sha": "abc"},
            }
        )
        mock_service.get_pr_timeline_events = AsyncMock(return_value=[])
        mock_service.check_copilot_finished_events = Mock(return_value=False)
        mock_service.is_copilot_assigned_to_issue = AsyncMock(return_value=True)

        result = await _check_main_pr_completion(
            "tok",
            "o",
            "r",
            10,
            42,
            "myagent",
            pipeline_started_at=utcnow(),
            agent_assigned_sha="",
        )
        assert result is False

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    async def test_no_pr_details_returns_false(self, mock_service):
        mock_service.get_pull_request = AsyncMock(return_value=None)
        result = await _check_main_pr_completion(
            "tok",
            "o",
            "r",
            10,
            42,
            "myagent",
        )
        assert result is False


# ────────────────────────────────────────────────────────────────────
# _poll_loop  (~89 uncovered lines)
# ────────────────────────────────────────────────────────────────────


class TestPollLoop:
    """Tests for _poll_loop."""

    @pytest.fixture(autouse=True)
    def _reset_state(self):
        from src.services.copilot_polling import _monitored_projects, _polling_state

        _polling_state.is_running = False
        _polling_state.poll_count = 0
        _polling_state.errors_count = 0
        _polling_state.last_error = None
        _polling_state.last_poll_time = None
        _monitored_projects.clear()
        yield
        _polling_state.is_running = False
        _monitored_projects.clear()

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.recover_stalled_issues", new_callable=AsyncMock)
    @patch(
        "src.services.copilot_polling.check_in_review_issues_for_copilot_review",
        new_callable=AsyncMock,
    )
    @patch("src.services.copilot_polling.check_in_progress_issues", new_callable=AsyncMock)
    @patch("src.services.copilot_polling.check_ready_issues", new_callable=AsyncMock)
    @patch("src.services.copilot_polling.check_backlog_issues", new_callable=AsyncMock)
    @patch("src.services.copilot_polling.post_agent_outputs_from_pr", new_callable=AsyncMock)
    @patch("src.services.copilot_polling.github_projects_service")
    @patch("asyncio.sleep", new_callable=AsyncMock)
    async def test_single_poll_cycle(
        self,
        mock_sleep,
        mock_service,
        mock_output,
        mock_backlog,
        mock_ready,
        mock_progress,
        mock_review,
        mock_recover,
    ):
        from src.services.copilot_polling import _polling_state

        _polling_state.is_running = True
        mock_service.get_project_items = AsyncMock(return_value=[])
        mock_service.get_last_rate_limit.return_value = None
        mock_output.return_value = []
        mock_backlog.return_value = []
        mock_ready.return_value = []
        mock_progress.return_value = []
        mock_review.return_value = []
        mock_recover.return_value = []

        # Stop after one cycle
        async def stop_after_one(*a, **kw):
            _polling_state.is_running = False

        mock_sleep.side_effect = stop_after_one

        await _poll_loop("tok", "P1", "o", "r", 60)

        assert _polling_state.poll_count == 1
        assert _polling_state.last_poll_time is not None
        mock_service.get_project_items.assert_awaited_once()

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    @patch("asyncio.sleep", new_callable=AsyncMock)
    async def test_exception_increments_errors(self, mock_sleep, mock_service):
        from src.services.copilot_polling import _polling_state

        _polling_state.is_running = True
        mock_service.get_project_items = AsyncMock(side_effect=Exception("net err"))
        mock_service.get_last_rate_limit.return_value = None

        async def stop_after_one(*a, **kw):
            _polling_state.is_running = False

        mock_sleep.side_effect = stop_after_one

        await _poll_loop("tok", "P1", "o", "r", 60)

        assert _polling_state.errors_count == 1
        assert _polling_state.last_error == "net err"

    @pytest.mark.asyncio
    async def test_not_running_exits_immediately(self):
        from src.services.copilot_polling import _polling_state

        _polling_state.is_running = False
        await _poll_loop("tok", "P1", "o", "r", 60)
        assert _polling_state.poll_count == 0


# ────────────────────────────────────────────────────────────────────
# ────────────────────────────────────────────────────────────────────
# Rate-limit-aware polling
# ────────────────────────────────────────────────────────────────────


class TestRateLimitAwarePolling:
    """Tests for rate-limit budget checks in the polling loop."""

    @pytest.fixture(autouse=True)
    def _reset_state(self):
        from src.services.copilot_polling import _monitored_projects, _polling_state

        _polling_state.is_running = False
        _polling_state.poll_count = 0
        _polling_state.errors_count = 0
        _polling_state.last_error = None
        _polling_state.last_poll_time = None
        _monitored_projects.clear()
        yield
        _polling_state.is_running = False
        _monitored_projects.clear()

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    async def test_check_rate_limit_budget_returns_remaining(self, mock_service):
        """_check_rate_limit_budget should return (remaining, reset_at)."""
        from src.services.copilot_polling.polling_loop import _check_rate_limit_budget

        mock_service.get_last_rate_limit.return_value = {
            "limit": 5000,
            "remaining": 3000,
            "reset_at": 1700000000,
            "used": 2000,
        }
        remaining, reset_at = await _check_rate_limit_budget()
        assert remaining == 3000
        assert reset_at == 1700000000

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    async def test_check_rate_limit_budget_returns_none_when_no_data(self, mock_service):
        """_check_rate_limit_budget should return (None, None) when no rate limit data."""
        from src.services.copilot_polling.polling_loop import _check_rate_limit_budget

        mock_service.get_last_rate_limit.return_value = None
        remaining, reset_at = await _check_rate_limit_budget()
        assert remaining is None
        assert reset_at is None

    @pytest.mark.asyncio
    @patch("asyncio.sleep", new_callable=AsyncMock)
    @patch("src.services.copilot_polling.github_projects_service")
    async def test_pause_if_rate_limited_pauses_when_exhausted(self, mock_service, mock_sleep):
        """_pause_if_rate_limited should sleep and return True when remaining <= threshold."""
        from src.services.copilot_polling.polling_loop import _pause_if_rate_limited

        mock_service.get_last_rate_limit.return_value = {
            "limit": 5000,
            "remaining": 20,
            "reset_at": int(utcnow().timestamp()) + 120,
            "used": 4980,
        }
        result = await _pause_if_rate_limited("test-step")
        assert result is True
        mock_sleep.assert_awaited_once()

    @pytest.mark.asyncio
    @patch("asyncio.sleep", new_callable=AsyncMock)
    @patch("src.services.copilot_polling.github_projects_service")
    async def test_pause_if_rate_limited_returns_false_when_healthy(self, mock_service, mock_sleep):
        """_pause_if_rate_limited should return False when remaining is healthy."""
        from src.services.copilot_polling.polling_loop import _pause_if_rate_limited

        mock_service.get_last_rate_limit.return_value = {
            "limit": 5000,
            "remaining": 4000,
            "reset_at": int(utcnow().timestamp()) + 3600,
            "used": 1000,
        }
        result = await _pause_if_rate_limited("test-step")
        assert result is False
        mock_sleep.assert_not_awaited()

    @pytest.mark.asyncio
    @patch("asyncio.sleep", new_callable=AsyncMock)
    @patch("src.services.copilot_polling.github_projects_service")
    async def test_pause_if_rate_limited_clears_stale_when_reset_passed(
        self, mock_service, mock_sleep
    ):
        """When remaining=0 but reset_at is in the past, clear stale data and return False.

        This prevents the infinite sleep-10s deadlock where stale cached
        rate-limit data (remaining=0, reset_at already passed) causes the
        loop to never make a fresh API call to update headers.
        """
        from src.services.copilot_polling.polling_loop import _pause_if_rate_limited

        past_reset = int(utcnow().timestamp()) - 600  # 10 minutes ago
        mock_service.get_last_rate_limit.return_value = {
            "limit": 5000,
            "remaining": 0,
            "reset_at": past_reset,
            "used": 5000,
        }
        mock_service._last_rate_limit = {"remaining": 0}  # will be cleared

        result = await _pause_if_rate_limited("test-stale")

        assert result is False  # should NOT block
        mock_sleep.assert_not_awaited()  # should NOT sleep
        # clear_last_rate_limit() should have been called to wipe both
        # the contextvar and instance-level caches.
        mock_service.clear_last_rate_limit.assert_called_once()

    @pytest.mark.asyncio
    @patch("asyncio.sleep", new_callable=AsyncMock)
    @patch("src.services.copilot_polling.github_projects_service")
    async def test_pause_if_rate_limited_sleeps_when_reset_in_future(
        self, mock_service, mock_sleep
    ):
        """When remaining=0 and reset_at is in the future, should still sleep normally."""
        from src.services.copilot_polling.polling_loop import _pause_if_rate_limited

        future_reset = int(utcnow().timestamp()) + 120  # 2 minutes from now
        mock_service.get_last_rate_limit.return_value = {
            "limit": 5000,
            "remaining": 0,
            "reset_at": future_reset,
            "used": 5000,
        }
        result = await _pause_if_rate_limited("test-future")
        assert result is True  # should block
        mock_sleep.assert_awaited_once()  # should sleep

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    @patch("asyncio.sleep", new_callable=AsyncMock)
    async def test_error_handler_clears_stale_rate_limit(self, mock_sleep, mock_service):
        """After an exception with stale rate-limit data, the error handler should clear it.

        Scenario: pre-cycle check sees no rate data (returns None) so it passes.
        get_project_items raises. The error triggers a 403 that populates stale
        cached headers (remaining=0, reset_at in the past).  The error handler
        should detect the stale data and clear it.
        """
        from src.services.copilot_polling import _polling_state

        _polling_state.is_running = True

        past_reset = int(utcnow().timestamp()) - 60  # 1 minute ago
        stale_rl = {
            "limit": 5000,
            "remaining": 0,
            "reset_at": past_reset,
            "used": 5000,
        }

        # Pre-cycle: no rate-limit data → passes check
        # After error: stale data appears (simulating 403 populating headers)
        call_count = 0

        def rl_side_effect():
            nonlocal call_count
            call_count += 1
            # First call is from pre-cycle _pause_if_rate_limited
            if call_count <= 1:
                return None
            return stale_rl

        mock_service.get_last_rate_limit.side_effect = rl_side_effect
        mock_service.get_project_items = AsyncMock(side_effect=Exception("rate limit 403"))
        mock_service._last_rate_limit = {"remaining": 0}

        async def stop_after_one(*a, **kw):
            _polling_state.is_running = False

        mock_sleep.side_effect = stop_after_one

        await _poll_loop("tok", "P1", "o", "r", 60)

        assert _polling_state.errors_count == 1
        # clear_last_rate_limit() should have been called to wipe both
        # the contextvar and instance-level caches.
        mock_service.clear_last_rate_limit.assert_called()

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    @patch("asyncio.sleep", new_callable=AsyncMock)
    async def test_error_handler_preserves_fresh_rate_limit(self, mock_sleep, mock_service):
        """After an exception with fresh (future) rate-limit data, handler should NOT clear it.

        Same setup as above but the cached headers have a future reset_at,
        so the error handler should leave them alone.
        """
        from src.services.copilot_polling import _polling_state

        _polling_state.is_running = True

        future_reset = int(utcnow().timestamp()) + 300  # 5 minutes from now
        fresh_rl = {
            "limit": 5000,
            "remaining": 10,
            "reset_at": future_reset,
            "used": 4990,
        }

        call_count = 0

        def rl_side_effect():
            nonlocal call_count
            call_count += 1
            if call_count <= 1:
                return None  # pre-cycle sees no data
            return fresh_rl

        mock_service.get_last_rate_limit.side_effect = rl_side_effect
        mock_service.get_project_items = AsyncMock(side_effect=Exception("server error"))
        mock_service._last_rate_limit = {"remaining": 10}

        async def stop_after_one(*a, **kw):
            _polling_state.is_running = False

        mock_sleep.side_effect = stop_after_one

        await _poll_loop("tok", "P1", "o", "r", 60)

        assert _polling_state.errors_count == 1
        # Fresh data should NOT be cleared
        assert mock_service._last_rate_limit == {"remaining": 10}

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.recover_stalled_issues", new_callable=AsyncMock)
    @patch(
        "src.services.copilot_polling.check_in_review_issues",
        new_callable=AsyncMock,
    )
    @patch(
        "src.services.copilot_polling.check_in_review_issues_for_copilot_review",
        new_callable=AsyncMock,
    )
    @patch("src.services.copilot_polling.check_in_progress_issues", new_callable=AsyncMock)
    @patch("src.services.copilot_polling.check_ready_issues", new_callable=AsyncMock)
    @patch("src.services.copilot_polling.check_backlog_issues", new_callable=AsyncMock)
    @patch("src.services.copilot_polling.post_agent_outputs_from_pr", new_callable=AsyncMock)
    @patch("src.services.copilot_polling.github_projects_service")
    @patch("asyncio.sleep", new_callable=AsyncMock)
    async def test_poll_loop_skips_step0_when_budget_low(
        self,
        mock_sleep,
        mock_service,
        mock_output,
        mock_backlog,
        mock_ready,
        mock_progress,
        mock_review_copilot,
        mock_review,
        mock_recover,
    ):
        """When rate limit is below RATE_LIMIT_SKIP_EXPENSIVE_THRESHOLD,
        Step 0 (post_agent_outputs_from_pr) should be skipped."""
        from src.services.copilot_polling import _polling_state

        _polling_state.is_running = True
        mock_service.get_project_items = AsyncMock(return_value=[])
        mock_service.get_last_rate_limit.return_value = {
            "limit": 5000,
            "remaining": 80,  # below RATE_LIMIT_SKIP_EXPENSIVE_THRESHOLD (100)
            "reset_at": int(utcnow().timestamp()) + 300,
            "used": 4920,
        }
        mock_output.return_value = []
        mock_backlog.return_value = []
        mock_ready.return_value = []
        mock_progress.return_value = []
        mock_review_copilot.return_value = []
        mock_review.return_value = []
        mock_recover.return_value = []

        async def stop_after_one(*a, **kw):
            _polling_state.is_running = False

        mock_sleep.side_effect = stop_after_one

        await _poll_loop("tok", "P1", "o", "r", 60)

        # Step 0 should NOT have been called
        mock_output.assert_not_awaited()
        # Step 5 (recovery) should also be skipped
        mock_recover.assert_not_awaited()
        # Other steps should still run
        mock_backlog.assert_awaited_once()

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.recover_stalled_issues", new_callable=AsyncMock)
    @patch(
        "src.services.copilot_polling.check_in_review_issues",
        new_callable=AsyncMock,
    )
    @patch(
        "src.services.copilot_polling.check_in_review_issues_for_copilot_review",
        new_callable=AsyncMock,
    )
    @patch("src.services.copilot_polling.check_in_progress_issues", new_callable=AsyncMock)
    @patch("src.services.copilot_polling.check_ready_issues", new_callable=AsyncMock)
    @patch("src.services.copilot_polling.check_backlog_issues", new_callable=AsyncMock)
    @patch("src.services.copilot_polling.post_agent_outputs_from_pr", new_callable=AsyncMock)
    @patch("src.services.copilot_polling.github_projects_service")
    @patch("asyncio.sleep", new_callable=AsyncMock)
    async def test_poll_loop_doubles_interval_when_budget_low(
        self,
        mock_sleep,
        mock_service,
        mock_output,
        mock_backlog,
        mock_ready,
        mock_progress,
        mock_review_copilot,
        mock_review,
        mock_recover,
    ):
        """When remaining is below RATE_LIMIT_SLOW_THRESHOLD at end of cycle,
        the sleep interval should be doubled."""
        from src.services.copilot_polling import _polling_state

        _polling_state.is_running = True
        mock_service.get_project_items = AsyncMock(return_value=[])
        mock_service.get_last_rate_limit.return_value = {
            "limit": 5000,
            "remaining": 150,  # below RATE_LIMIT_SLOW_THRESHOLD (200) but above skip
            "reset_at": int(utcnow().timestamp()) + 3600,
            "used": 4850,
        }
        mock_output.return_value = []
        mock_backlog.return_value = []
        mock_ready.return_value = []
        mock_progress.return_value = []
        mock_review_copilot.return_value = []
        mock_review.return_value = []
        mock_recover.return_value = []

        call_count = 0

        async def stop_after_one(seconds):
            nonlocal call_count
            call_count += 1
            if call_count >= 2:
                _polling_state.is_running = False

        mock_sleep.side_effect = stop_after_one

        await _poll_loop("tok", "P1", "o", "r", 60)

        # The final sleep should use the doubled interval (120s)
        sleep_calls = [c.args[0] for c in mock_sleep.call_args_list]
        assert 120 in sleep_calls, f"Expected 120s sleep, got: {sleep_calls}"

    def test_get_polling_status_includes_rate_limit(self):
        """get_polling_status should include rate_limit info when available."""
        with patch("src.services.copilot_polling.polling_loop._cp") as mock_cp:
            mock_cp.github_projects_service.get_last_rate_limit.return_value = {
                "limit": 5000,
                "remaining": 3000,
                "reset_at": 1700000000,
                "used": 2000,
            }
            # We also need _polling_state and _processed_issue_prs accessible
            mock_cp._polling_task = None
            from src.services.copilot_polling.polling_loop import get_polling_status as _gs

            status = _gs()
            assert "rate_limit" in status
            assert status["rate_limit"]["remaining"] == 3000
            assert status["rate_limit"]["limit"] == 5000


# ────────────────────────────────────────────────────────────────────
# Pipeline rate-limit awareness
# ────────────────────────────────────────────────────────────────────


class TestPipelineRateLimitAwareness:
    """Tests for rate-limit budget checks in pipeline agent assignments."""

    @pytest.mark.asyncio
    @patch("asyncio.sleep", new_callable=AsyncMock)
    @patch("src.services.copilot_polling.github_projects_service")
    async def test_wait_if_rate_limited_waits_when_budget_low(self, mock_service, mock_sleep):
        """_wait_if_rate_limited should sleep and return True when budget is critically low."""
        from src.services.copilot_polling.pipeline import _wait_if_rate_limited

        mock_service.get_last_rate_limit.return_value = {
            "remaining": 10,
            "reset_at": int(utcnow().timestamp()) + 60,
        }
        result = await _wait_if_rate_limited("test-assignment")
        assert result is True
        mock_sleep.assert_awaited_once()

    @pytest.mark.asyncio
    @patch("asyncio.sleep", new_callable=AsyncMock)
    @patch("src.services.copilot_polling.github_projects_service")
    async def test_wait_if_rate_limited_proceeds_when_budget_healthy(
        self, mock_service, mock_sleep
    ):
        """_wait_if_rate_limited should return False when budget is healthy."""
        from src.services.copilot_polling.pipeline import _wait_if_rate_limited

        mock_service.get_last_rate_limit.return_value = {
            "remaining": 4000,
            "reset_at": int(utcnow().timestamp()) + 3600,
        }
        result = await _wait_if_rate_limited("test-assignment")
        assert result is False
        mock_sleep.assert_not_awaited()

    @pytest.mark.asyncio
    @patch("asyncio.sleep", new_callable=AsyncMock)
    @patch("src.services.copilot_polling.github_projects_service")
    async def test_wait_if_rate_limited_clears_stale_data(self, mock_service, mock_sleep):
        """_wait_if_rate_limited should clear stale data and continue when reset_at is past."""
        from src.services.copilot_polling.pipeline import _wait_if_rate_limited

        mock_service.get_last_rate_limit.return_value = {
            "remaining": 0,
            "reset_at": int(utcnow().timestamp()) - 60,  # already past
        }
        result = await _wait_if_rate_limited("test-assignment")
        assert result is False
        mock_service.clear_last_rate_limit.assert_called_once()
        mock_sleep.assert_not_awaited()

    @pytest.mark.asyncio
    @patch("asyncio.sleep", new_callable=AsyncMock)
    @patch("src.services.copilot_polling.github_projects_service")
    async def test_wait_if_rate_limited_proceeds_when_no_data(self, mock_service, mock_sleep):
        """_wait_if_rate_limited should return False when no rate limit data available."""
        from src.services.copilot_polling.pipeline import _wait_if_rate_limited

        mock_service.get_last_rate_limit.return_value = None
        result = await _wait_if_rate_limited("test-assignment")
        assert result is False
        mock_sleep.assert_not_awaited()

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    async def test_get_rate_limit_remaining_returns_values(self, mock_service):
        """_get_rate_limit_remaining should return (remaining, reset_at)."""
        from src.services.copilot_polling.pipeline import _get_rate_limit_remaining

        mock_service.get_last_rate_limit.return_value = {
            "remaining": 500,
            "reset_at": 1700000000,
        }
        remaining, reset_at = _get_rate_limit_remaining()
        assert remaining == 500
        assert reset_at == 1700000000

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    async def test_get_rate_limit_remaining_returns_none_when_no_data(self, mock_service):
        """_get_rate_limit_remaining should return (None, None) when no data."""
        from src.services.copilot_polling.pipeline import _get_rate_limit_remaining

        mock_service.get_last_rate_limit.return_value = None
        remaining, reset_at = _get_rate_limit_remaining()
        assert remaining is None
        assert reset_at is None


# ────────────────────────────────────────────────────────────────────
# GraphQL rate limit extraction
# ────────────────────────────────────────────────────────────────────


class TestGraphQLRateLimitExtraction:
    """Tests for rate limit header extraction from GraphQL responses."""

    def test_extract_rate_limit_headers_sets_values(self):
        """_extract_rate_limit_headers should parse and store rate limit info."""
        from src.services.github_projects.service import GitHubProjectsService

        svc = GitHubProjectsService.__new__(GitHubProjectsService)
        svc._last_rate_limit = None

        response = MagicMock()
        response.headers = {
            "X-RateLimit-Limit": "5000",
            "X-RateLimit-Remaining": "4500",
            "X-RateLimit-Reset": "1700000000",
        }
        svc._extract_rate_limit_headers(response)
        assert svc._last_rate_limit is not None
        assert svc._last_rate_limit["remaining"] == 4500
        assert svc._last_rate_limit["limit"] == 5000
        assert svc._last_rate_limit["reset_at"] == 1700000000
        assert svc._last_rate_limit["used"] == 500

    def test_extract_rate_limit_headers_ignores_missing(self):
        """_extract_rate_limit_headers should not crash when headers are missing."""
        from src.services.github_projects.service import GitHubProjectsService

        svc = GitHubProjectsService.__new__(GitHubProjectsService)
        svc._last_rate_limit = None

        response = MagicMock()
        response.headers = {}
        svc._extract_rate_limit_headers(response)
        assert svc._last_rate_limit is None

    def test_extract_rate_limit_headers_tolerates_bad_values(self):
        """_extract_rate_limit_headers should not crash on non-numeric values."""
        from src.services.github_projects.service import GitHubProjectsService

        svc = GitHubProjectsService.__new__(GitHubProjectsService)
        svc._last_rate_limit = None

        response = MagicMock()
        response.headers = {
            "X-RateLimit-Limit": "abc",
            "X-RateLimit-Remaining": "xyz",
            "X-RateLimit-Reset": "bad",
        }
        svc._extract_rate_limit_headers(response)
        assert svc._last_rate_limit is None


# ────────────────────────────────────────────────────────────────────
# stop_polling
# ────────────────────────────────────────────────────────────────────


class TestStopPolling:
    """Tests for stop_polling."""

    def test_sets_is_running_false(self):
        from src.services.copilot_polling import _polling_state

        _polling_state.is_running = True
        stop_polling()
        assert _polling_state.is_running is False

    def test_cancels_polling_task(self):
        import src.services.copilot_polling as cp

        task = MagicMock()
        task.done.return_value = False
        cp._polling_task = task
        cp._polling_state.is_running = True

        stop_polling()

        task.cancel.assert_called_once()
        assert cp._polling_task is None

    def test_no_task_no_error(self):
        import src.services.copilot_polling as cp

        cp._polling_task = None
        stop_polling()  # should not raise


# ────────────────────────────────────────────────────────────────────
# _check_agent_done_on_parent  (line 177)
# ────────────────────────────────────────────────────────────────────


class TestCheckAgentDoneOnParent:
    """Tests for _check_agent_done_on_parent."""

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    async def test_delegates_to_check_completion_comment(self, mock_service):
        """Should delegate directly to check_agent_completion_comment on parent issue."""
        mock_service.check_agent_completion_comment = AsyncMock(return_value=True)

        result = await _check_agent_done_on_parent(
            access_token="token",
            owner="owner",
            repo="repo",
            parent_issue_number=42,
            agent_name="speckit.specify",
        )

        assert result is True
        mock_service.check_agent_completion_comment.assert_called_once_with(
            access_token="token",
            owner="owner",
            repo="repo",
            issue_number=42,
            agent_name="speckit.specify",
        )

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    async def test_returns_false_when_no_marker(self, mock_service):
        mock_service.check_agent_completion_comment = AsyncMock(return_value=False)

        result = await _check_agent_done_on_parent(
            access_token="token",
            owner="owner",
            repo="repo",
            parent_issue_number=42,
            agent_name="speckit.specify",
        )

        assert result is False


# ────────────────────────────────────────────────────────────────────
# _check_human_agent_done (Human dual-signal completion)
# ────────────────────────────────────────────────────────────────────


class TestCheckHumanAgentDone:
    """Tests for Human agent dual-signal completion detection.

    Two signals can complete a Human step:
      1. The Human sub-issue has been closed.
      2. The assigned user commented exactly ``Done!`` on the parent issue.

    Authorization rules:
      - Only the known assignee (or parent issue author fallback) can trigger.
      - ``Done!`` from a non-assignee is silently ignored.
      - Whitespace variants like ``Done! `` or ``done!`` must NOT complete.
      - When no authorized user can be determined, fail closed (no completion).
    """

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    async def test_closed_sub_issue_returns_true(self, mock_service):
        """Signal 1: A closed Human sub-issue completes the step."""
        pipeline = MagicMock()
        pipeline.agent_sub_issues = {"human": {"number": 99, "assignee": "creator"}}

        mock_service.check_issue_closed = AsyncMock(return_value=True)

        result = await _check_agent_done_on_sub_or_parent(
            access_token="token",
            owner="owner",
            repo="repo",
            parent_issue_number=42,
            agent_name="human",
            pipeline=pipeline,
        )

        assert result is True
        mock_service.check_issue_closed.assert_awaited_once_with(
            access_token="token",
            owner="owner",
            repo="repo",
            issue_number=99,
        )

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    async def test_done_comment_from_assignee_returns_true(self, mock_service):
        """Signal 2: Exact 'Done!' from the assigned user completes the step."""
        pipeline = MagicMock()
        pipeline.agent_sub_issues = {"human": {"number": 99, "assignee": "creator"}}

        mock_service.check_issue_closed = AsyncMock(return_value=False)
        mock_service.get_issue_with_comments = AsyncMock(
            return_value={
                "comments": [
                    {"author": "someone-else", "body": "Still working on it"},
                    {"author": "creator", "body": "Done!"},
                ],
                "user": {"login": "creator"},
            }
        )

        result = await _check_agent_done_on_sub_or_parent(
            access_token="token",
            owner="owner",
            repo="repo",
            parent_issue_number=42,
            agent_name="human",
            pipeline=pipeline,
        )

        assert result is True

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    async def test_done_comment_from_non_assignee_returns_false(self, mock_service):
        """'Done!' from an unauthorized user must NOT complete the step."""
        pipeline = MagicMock()
        pipeline.agent_sub_issues = {"human": {"number": 99, "assignee": "creator"}}

        mock_service.check_issue_closed = AsyncMock(return_value=False)
        mock_service.get_issue_with_comments = AsyncMock(
            return_value={
                "comments": [
                    {"author": "intruder", "body": "Done!"},
                ],
                "user": {"login": "creator"},
            }
        )

        result = await _check_agent_done_on_sub_or_parent(
            access_token="token",
            owner="owner",
            repo="repo",
            parent_issue_number=42,
            agent_name="human",
            pipeline=pipeline,
        )

        assert result is False

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    async def test_done_with_trailing_whitespace_does_not_complete(self, mock_service):
        """'Done! ' (with trailing space) must NOT match — exact string only."""
        pipeline = MagicMock()
        pipeline.agent_sub_issues = {"human": {"number": 99, "assignee": "creator"}}

        mock_service.check_issue_closed = AsyncMock(return_value=False)
        mock_service.get_issue_with_comments = AsyncMock(
            return_value={
                "comments": [
                    {"author": "creator", "body": "Done! "},
                ],
                "user": {"login": "creator"},
            }
        )

        result = await _check_agent_done_on_sub_or_parent(
            access_token="token",
            owner="owner",
            repo="repo",
            parent_issue_number=42,
            agent_name="human",
            pipeline=pipeline,
        )

        assert result is False

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    async def test_lowercase_done_does_not_complete(self, mock_service):
        """'done!' (case mismatch) must NOT match — case-sensitive exact string."""
        pipeline = MagicMock()
        pipeline.agent_sub_issues = {"human": {"number": 99, "assignee": "creator"}}

        mock_service.check_issue_closed = AsyncMock(return_value=False)
        mock_service.get_issue_with_comments = AsyncMock(
            return_value={
                "comments": [
                    {"author": "creator", "body": "done!"},
                ],
                "user": {"login": "creator"},
            }
        )

        result = await _check_agent_done_on_sub_or_parent(
            access_token="token",
            owner="owner",
            repo="repo",
            parent_issue_number=42,
            agent_name="human",
            pipeline=pipeline,
        )

        assert result is False

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    async def test_no_assignee_falls_back_to_parent_author(self, mock_service):
        """When no assignee is stored, the parent issue author should be used."""
        pipeline = MagicMock()
        # No assignee recorded in the pipeline sub-issue info
        pipeline.agent_sub_issues = {"human": {"number": 99}}

        mock_service.check_issue_closed = AsyncMock(return_value=False)
        mock_service.get_issue_with_comments = AsyncMock(
            return_value={
                "comments": [
                    {"author": "issue-author", "body": "Done!"},
                ],
                "user": {"login": "issue-author"},
            }
        )

        result = await _check_agent_done_on_sub_or_parent(
            access_token="token",
            owner="owner",
            repo="repo",
            parent_issue_number=42,
            agent_name="human",
            pipeline=pipeline,
        )

        assert result is True

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    async def test_no_assignee_no_author_fails_closed(self, mock_service):
        """When neither assignee nor parent author is known, fail closed."""
        pipeline = MagicMock()
        pipeline.agent_sub_issues = {"human": {"number": 99}}

        mock_service.check_issue_closed = AsyncMock(return_value=False)
        mock_service.get_issue_with_comments = AsyncMock(
            return_value={
                "comments": [
                    {"author": "someone", "body": "Done!"},
                ],
                # No author information available
                "user": {"login": ""},
            }
        )

        result = await _check_agent_done_on_sub_or_parent(
            access_token="token",
            owner="owner",
            repo="repo",
            parent_issue_number=42,
            agent_name="human",
            pipeline=pipeline,
        )

        # Must fail closed — no authorized user could be determined
        assert result is False

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    async def test_no_signals_returns_false(self, mock_service):
        """When sub-issue is open and no 'Done!' comment exists, return False."""
        pipeline = MagicMock()
        pipeline.agent_sub_issues = {"human": {"number": 99, "assignee": "creator"}}

        mock_service.check_issue_closed = AsyncMock(return_value=False)
        mock_service.get_issue_with_comments = AsyncMock(
            return_value={
                "comments": [
                    {"author": "creator", "body": "Still working on it"},
                ],
                "user": {"login": "creator"},
            }
        )

        result = await _check_agent_done_on_sub_or_parent(
            access_token="token",
            owner="owner",
            repo="repo",
            parent_issue_number=42,
            agent_name="human",
            pipeline=pipeline,
        )

        assert result is False


# ────────────────────────────────────────────────────────────────────
# _update_issue_tracking  (lines 217-245)
# ────────────────────────────────────────────────────────────────────


class TestUpdateIssueTracking:
    """Tests for _update_issue_tracking — updates agent state in issue body."""

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    async def test_returns_false_for_empty_body(self, mock_service):
        """Should return False when issue body is empty."""
        mock_service.get_issue_with_comments = AsyncMock(return_value={"body": "", "comments": []})

        result = await _update_issue_tracking(
            access_token="token",
            owner="owner",
            repo="repo",
            issue_number=42,
            agent_name="speckit.specify",
            new_state="active",
        )

        assert result is False
        mock_service.update_issue_body.assert_not_called()

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    async def test_returns_false_for_invalid_state(self, mock_service):
        """Should return False for an unrecognized new_state value."""
        mock_service.get_issue_with_comments = AsyncMock(
            return_value={"body": "some body text", "comments": []}
        )

        result = await _update_issue_tracking(
            access_token="token",
            owner="owner",
            repo="repo",
            issue_number=42,
            agent_name="speckit.specify",
            new_state="invalid_state",
        )

        assert result is False
        mock_service.update_issue_body.assert_not_called()

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.mark_agent_active")
    @patch("src.services.copilot_polling.github_projects_service")
    async def test_returns_true_when_no_change_needed(self, mock_service, mock_mark):
        """Should return True without calling update_issue_body when body unchanged."""
        original_body = "| 1 | Backlog | `speckit.specify` | 🔄 Active |"
        mock_service.get_issue_with_comments = AsyncMock(
            return_value={"body": original_body, "comments": []}
        )
        mock_mark.return_value = original_body  # No change

        result = await _update_issue_tracking(
            access_token="token",
            owner="owner",
            repo="repo",
            issue_number=42,
            agent_name="speckit.specify",
            new_state="active",
        )

        assert result is True
        mock_service.update_issue_body.assert_not_called()

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.mark_agent_active")
    @patch("src.services.copilot_polling.github_projects_service")
    async def test_marks_agent_active_and_updates(self, mock_service, mock_mark):
        """Should call mark_agent_active and push updated body when state is 'active'."""
        mock_service.get_issue_with_comments = AsyncMock(
            return_value={"body": "old body", "comments": []}
        )
        mock_mark.return_value = "updated body"
        mock_service.update_issue_body = AsyncMock(return_value=True)

        result = await _update_issue_tracking(
            access_token="token",
            owner="owner",
            repo="repo",
            issue_number=42,
            agent_name="speckit.specify",
            new_state="active",
        )

        assert result is True
        mock_mark.assert_called_once_with("old body", "speckit.specify")
        mock_service.update_issue_body.assert_called_once_with(
            access_token="token",
            owner="owner",
            repo="repo",
            issue_number=42,
            body="updated body",
        )

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.mark_agent_done")
    @patch("src.services.copilot_polling.github_projects_service")
    async def test_marks_agent_done_and_updates(self, mock_service, mock_mark):
        """Should call mark_agent_done and push updated body when state is 'done'."""
        mock_service.get_issue_with_comments = AsyncMock(
            return_value={"body": "old body", "comments": []}
        )
        mock_mark.return_value = "done body"
        mock_service.update_issue_body = AsyncMock(return_value=True)

        result = await _update_issue_tracking(
            access_token="token",
            owner="owner",
            repo="repo",
            issue_number=42,
            agent_name="speckit.specify",
            new_state="done",
        )

        assert result is True
        mock_mark.assert_called_once_with("old body", "speckit.specify")

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    async def test_returns_false_on_exception(self, mock_service):
        """Should catch exceptions and return False."""
        mock_service.get_issue_with_comments = AsyncMock(side_effect=Exception("API error"))

        result = await _update_issue_tracking(
            access_token="token",
            owner="owner",
            repo="repo",
            issue_number=42,
            agent_name="speckit.specify",
            new_state="active",
        )

        assert result is False


# ────────────────────────────────────────────────────────────────────
# _get_tracking_state_from_issue  (lines 263-269)
# ────────────────────────────────────────────────────────────────────


class TestGetTrackingStateFromIssue:
    """Tests for _get_tracking_state_from_issue — fetches issue body + comments."""

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    async def test_returns_body_and_comments(self, mock_service):
        """Should return (body, comments) tuple from issue data."""
        mock_service.get_issue_with_comments = AsyncMock(
            return_value={
                "body": "Issue body text",
                "comments": [{"body": "comment 1"}],
            }
        )

        body, comments = await _get_tracking_state_from_issue(
            access_token="token",
            owner="owner",
            repo="repo",
            issue_number=42,
        )

        assert body == "Issue body text"
        assert len(comments) == 1
        assert comments[0]["body"] == "comment 1"

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    async def test_returns_defaults_for_missing_keys(self, mock_service):
        """Should return empty defaults when body/comments are missing."""
        mock_service.get_issue_with_comments = AsyncMock(return_value={})

        body, comments = await _get_tracking_state_from_issue(
            access_token="token",
            owner="owner",
            repo="repo",
            issue_number=42,
        )

        assert body == ""
        assert comments == []


# ────────────────────────────────────────────────────────────────────
# _reconstruct_sub_issue_mappings  (lines 290-306)
# ────────────────────────────────────────────────────────────────────


class TestReconstructSubIssueMappings:
    """Tests for _reconstruct_sub_issue_mappings — builds agent→sub-issue mapping."""

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    async def test_parses_bracketed_agent_names(self, mock_service):
        """Should parse [agent-name] prefix from sub-issue titles."""
        mock_service.get_sub_issues = AsyncMock(
            return_value=[
                {
                    "title": "[speckit.specify] Write the specification",
                    "number": 101,
                    "node_id": "I_101",
                    "html_url": "https://github.com/owner/repo/issues/101",
                },
                {
                    "title": "[speckit.plan] Create the plan",
                    "number": 102,
                    "node_id": "I_102",
                    "html_url": "https://github.com/owner/repo/issues/102",
                },
            ]
        )

        result = await _reconstruct_sub_issue_mappings(
            access_token="token",
            owner="owner",
            repo="repo",
            issue_number=42,
        )

        assert len(result) == 2
        assert result["speckit.specify"]["number"] == 101
        assert result["speckit.specify"]["node_id"] == "I_101"
        assert result["speckit.plan"]["number"] == 102

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    async def test_skips_titles_without_brackets(self, mock_service):
        """Should skip sub-issues whose titles don't match [agent] pattern."""
        mock_service.get_sub_issues = AsyncMock(
            return_value=[
                {"title": "No brackets here", "number": 103},
                {"title": "[speckit.plan] Valid one", "number": 104, "node_id": "", "html_url": ""},
            ]
        )

        result = await _reconstruct_sub_issue_mappings(
            access_token="token",
            owner="owner",
            repo="repo",
            issue_number=42,
        )

        assert len(result) == 1
        assert "speckit.plan" in result

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    async def test_returns_empty_on_exception(self, mock_service):
        """Should return empty dict on API error."""
        mock_service.get_sub_issues = AsyncMock(side_effect=Exception("API error"))

        result = await _reconstruct_sub_issue_mappings(
            access_token="token",
            owner="owner",
            repo="repo",
            issue_number=42,
        )

        assert result == {}

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    async def test_returns_empty_for_no_sub_issues(self, mock_service):
        """Should return empty dict when there are no sub-issues."""
        mock_service.get_sub_issues = AsyncMock(return_value=[])

        result = await _reconstruct_sub_issue_mappings(
            access_token="token",
            owner="owner",
            repo="repo",
            issue_number=42,
        )

        assert result == {}

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    async def test_persists_to_global_sub_issue_store(self, mock_service):
        """Reconstructed mappings should be persisted to the global sub-issue store."""
        from src.services.workflow_orchestrator import (
            _issue_sub_issue_map,
            get_issue_sub_issues,
        )

        _issue_sub_issue_map.clear()

        mock_service.get_sub_issues = AsyncMock(
            return_value=[
                {"title": "[speckit.plan] Feature X", "number": 101, "node_id": "I_101"},
                {"title": "[speckit.tasks] Feature X", "number": 102, "node_id": "I_102"},
            ]
        )

        result = await _reconstruct_sub_issue_mappings(
            access_token="token",
            owner="owner",
            repo="repo",
            issue_number=42,
        )

        assert len(result) == 2

        # Verify persisted to global store
        global_subs = get_issue_sub_issues(42)
        assert "speckit.plan" in global_subs
        assert "speckit.tasks" in global_subs
        assert global_subs["speckit.plan"]["number"] == 101
        assert global_subs["speckit.tasks"]["number"] == 102

        _issue_sub_issue_map.clear()


class TestAdvancePipelineClosesSubIssueFromGlobalStore:
    """Tests that _advance_pipeline closes sub-issues using the global store."""

    @pytest.fixture(autouse=True)
    def clear_states(self):
        """Clear global states between tests."""
        from src.services.workflow_orchestrator import (
            _issue_sub_issue_map,
            _pipeline_states,
        )

        _pipeline_states.clear()
        _issue_sub_issue_map.clear()
        yield
        _pipeline_states.clear()
        _issue_sub_issue_map.clear()

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling._update_issue_tracking", new_callable=AsyncMock)
    @patch("src.services.copilot_polling.github_projects_service")
    @patch("src.services.copilot_polling.connection_manager")
    @patch("src.services.copilot_polling.get_workflow_orchestrator")
    @patch("src.services.copilot_polling.get_workflow_config", new_callable=AsyncMock)
    @patch("src.services.copilot_polling.set_pipeline_state")
    async def test_closes_sub_issue_from_global_store_when_pipeline_has_none(
        self,
        mock_set_state,
        mock_config,
        mock_get_orchestrator,
        mock_ws,
        mock_service,
        mock_update_tracking,
    ):
        """When pipeline.agent_sub_issues is empty but the global store has
        the mapping, _advance_pipeline should still close the sub-issue."""
        from src.services.workflow_orchestrator import set_issue_sub_issues

        # Global store has the sub-issue mapping
        set_issue_sub_issues(
            42,
            {
                "speckit.plan": {"number": 101, "node_id": "I_101", "url": ""},
                "speckit.tasks": {"number": 102, "node_id": "I_102", "url": ""},
            },
        )

        # Pipeline has NO agent_sub_issues (lost after status transition)
        pipeline = PipelineState(
            issue_number=42,
            project_id="PVT_123",
            status="Ready",
            agents=["speckit.plan", "speckit.tasks"],
            current_agent_index=0,
            completed_agents=[],
            agent_sub_issues={},
        )

        mock_ws.broadcast_to_project = AsyncMock()
        mock_service.update_issue_state = AsyncMock(return_value=True)
        mock_service.update_sub_issue_project_status = AsyncMock()
        mock_orchestrator = MagicMock()
        mock_orchestrator.assign_agent_for_status = AsyncMock(return_value=True)
        mock_get_orchestrator.return_value = mock_orchestrator
        mock_config.return_value = MagicMock()

        result = await _advance_pipeline(
            access_token="token",
            project_id="PVT_123",
            item_id="PVTI_123",
            owner="owner",
            repo="repo",
            issue_number=42,
            issue_node_id="I_123",
            pipeline=pipeline,
            from_status="Ready",
            to_status="In Progress",
            task_title="Test Issue",
        )

        assert result["status"] == "success"
        assert result["completed_agent"] == "speckit.plan"

        # Verify sub-issue #101 was closed
        mock_service.update_issue_state.assert_called_once_with(
            access_token="token",
            owner="owner",
            repo="repo",
            issue_number=101,
            state="closed",
            state_reason="completed",
            labels_add=["done"],
            labels_remove=["in-progress"],
        )

        # Verify sub-issue project board status updated to Done
        mock_service.update_sub_issue_project_status.assert_called_once_with(
            access_token="token",
            project_id="PVT_123",
            sub_issue_node_id="I_101",
            status_name="Done",
        )

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling._update_issue_tracking", new_callable=AsyncMock)
    @patch("src.services.copilot_polling.github_projects_service")
    @patch("src.services.copilot_polling.connection_manager")
    @patch("src.services.copilot_polling.get_workflow_orchestrator")
    @patch("src.services.copilot_polling.get_workflow_config", new_callable=AsyncMock)
    @patch("src.services.copilot_polling.set_pipeline_state")
    async def test_pipeline_sub_issues_take_precedence_over_global(
        self,
        mock_set_state,
        mock_config,
        mock_get_orchestrator,
        mock_ws,
        mock_service,
        mock_update_tracking,
    ):
        """When pipeline has sub-issue info, it should be used instead of global store."""
        from src.services.workflow_orchestrator import set_issue_sub_issues

        # Global store has different sub-issue numbers (stale)
        set_issue_sub_issues(
            42,
            {
                "speckit.plan": {"number": 999, "node_id": "I_999", "url": ""},
            },
        )

        # Pipeline has the correct/current mapping
        pipeline = PipelineState(
            issue_number=42,
            project_id="PVT_123",
            status="Ready",
            agents=["speckit.plan", "speckit.tasks"],
            current_agent_index=0,
            completed_agents=[],
            agent_sub_issues={
                "speckit.plan": {"number": 101, "node_id": "I_101", "url": ""},
            },
        )

        mock_ws.broadcast_to_project = AsyncMock()
        mock_service.update_issue_state = AsyncMock(return_value=True)
        mock_service.update_sub_issue_project_status = AsyncMock()
        mock_orchestrator = MagicMock()
        mock_orchestrator.assign_agent_for_status = AsyncMock(return_value=True)
        mock_get_orchestrator.return_value = mock_orchestrator
        mock_config.return_value = MagicMock()

        await _advance_pipeline(
            access_token="token",
            project_id="PVT_123",
            item_id="PVTI_123",
            owner="owner",
            repo="repo",
            issue_number=42,
            issue_node_id="I_123",
            pipeline=pipeline,
            from_status="Ready",
            to_status="In Progress",
            task_title="Test Issue",
        )

        # Should use pipeline's sub-issue #101, NOT global store's #999
        mock_service.update_issue_state.assert_called_once()
        call_args = mock_service.update_issue_state.call_args
        assert call_args.kwargs["issue_number"] == 101


class TestCloseCompletedSubIssuesSweep:
    """Tests that _close_completed_sub_issues sweeps ALL completed agents."""

    @pytest.fixture(autouse=True)
    def clear_states(self):
        from src.services.workflow_orchestrator import (
            _issue_sub_issue_map,
            _pipeline_states,
        )

        _pipeline_states.clear()
        _issue_sub_issue_map.clear()
        yield
        _pipeline_states.clear()
        _issue_sub_issue_map.clear()

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    async def test_sweeps_all_completed_agents(self, mock_service):
        """_close_completed_sub_issues should close sub-issues for ALL
        completed agents, not just the most recent one."""
        from src.services.workflow_orchestrator import set_issue_sub_issues

        set_issue_sub_issues(
            42,
            {
                "speckit.specify": {"number": 100, "node_id": "I_100", "url": ""},
                "speckit.plan": {"number": 101, "node_id": "I_101", "url": ""},
                "speckit.tasks": {"number": 102, "node_id": "I_102", "url": ""},
            },
        )

        pipeline = PipelineState(
            issue_number=42,
            project_id="PVT_123",
            status="Ready",
            agents=["speckit.specify", "speckit.plan", "speckit.tasks"],
            current_agent_index=3,
            completed_agents=["speckit.specify", "speckit.plan", "speckit.tasks"],
            agent_sub_issues={},
        )

        mock_service.update_issue_state = AsyncMock(return_value=True)
        mock_service.update_sub_issue_project_status = AsyncMock()

        await _close_completed_sub_issues(
            access_token="token",
            project_id="PVT_123",
            owner="owner",
            repo="repo",
            issue_number=42,
            completed_agents=list(pipeline.completed_agents),
            pipeline=pipeline,
        )

        # All 3 sub-issues should be closed
        assert mock_service.update_issue_state.call_count == 3
        closed_numbers = sorted(
            call.kwargs["issue_number"] for call in mock_service.update_issue_state.call_args_list
        )
        assert closed_numbers == [100, 101, 102]

        # All 3 sub-issues should have board status updated
        assert mock_service.update_sub_issue_project_status.call_count == 3

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    async def test_skips_agents_without_sub_info(self, mock_service):
        """Agents with no sub-issue mapping should be skipped gracefully."""
        from src.services.workflow_orchestrator import set_issue_sub_issues

        # Only one of three agents has a sub-issue
        set_issue_sub_issues(
            42,
            {
                "speckit.plan": {"number": 101, "node_id": "I_101", "url": ""},
            },
        )

        pipeline = PipelineState(
            issue_number=42,
            project_id="PVT_123",
            status="Ready",
            agents=["speckit.specify", "speckit.plan", "speckit.tasks"],
            current_agent_index=3,
            completed_agents=["speckit.specify", "speckit.plan", "speckit.tasks"],
            agent_sub_issues={},
        )

        mock_service.update_issue_state = AsyncMock(return_value=True)
        mock_service.update_sub_issue_project_status = AsyncMock()

        await _close_completed_sub_issues(
            access_token="token",
            project_id="PVT_123",
            owner="owner",
            repo="repo",
            issue_number=42,
            completed_agents=list(pipeline.completed_agents),
            pipeline=pipeline,
        )

        # Only 1 sub-issue should be closed (the one with mapping)
        mock_service.update_issue_state.assert_called_once_with(
            access_token="token",
            owner="owner",
            repo="repo",
            issue_number=101,
            state="closed",
            state_reason="completed",
            labels_add=["done"],
            labels_remove=["in-progress"],
        )

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    async def test_skips_sub_issue_matching_parent(self, mock_service):
        """Sub-issues whose number matches the parent issue should be skipped."""
        from src.services.workflow_orchestrator import set_issue_sub_issues

        set_issue_sub_issues(
            42,
            {
                "speckit.plan": {"number": 42, "node_id": "I_42", "url": ""},
            },
        )

        pipeline = PipelineState(
            issue_number=42,
            project_id="PVT_123",
            status="Ready",
            agents=["speckit.plan"],
            current_agent_index=1,
            completed_agents=["speckit.plan"],
            agent_sub_issues={},
        )

        mock_service.update_issue_state = AsyncMock(return_value=True)
        mock_service.update_sub_issue_project_status = AsyncMock()

        await _close_completed_sub_issues(
            access_token="token",
            project_id="PVT_123",
            owner="owner",
            repo="repo",
            issue_number=42,
            completed_agents=list(pipeline.completed_agents),
            pipeline=pipeline,
        )

        # Should NOT close — sub-issue number == parent issue number
        mock_service.update_issue_state.assert_not_called()

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    async def test_pipeline_sub_issues_used_over_global(self, mock_service):
        """Pipeline's agent_sub_issues should take precedence over global store."""
        from src.services.workflow_orchestrator import set_issue_sub_issues

        set_issue_sub_issues(
            42,
            {
                "speckit.plan": {"number": 999, "node_id": "I_999", "url": ""},
            },
        )

        pipeline = PipelineState(
            issue_number=42,
            project_id="PVT_123",
            status="Ready",
            agents=["speckit.plan"],
            current_agent_index=1,
            completed_agents=["speckit.plan"],
            agent_sub_issues={
                "speckit.plan": {"number": 101, "node_id": "I_101", "url": ""},
            },
        )

        mock_service.update_issue_state = AsyncMock(return_value=True)
        mock_service.update_sub_issue_project_status = AsyncMock()

        await _close_completed_sub_issues(
            access_token="token",
            project_id="PVT_123",
            owner="owner",
            repo="repo",
            issue_number=42,
            completed_agents=list(pipeline.completed_agents),
            pipeline=pipeline,
        )

        call_args = mock_service.update_issue_state.call_args
        assert call_args.kwargs["issue_number"] == 101

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    async def test_continues_on_individual_close_failure(self, mock_service):
        """If closing one sub-issue fails, the others should still be attempted."""
        from src.services.workflow_orchestrator import set_issue_sub_issues

        set_issue_sub_issues(
            42,
            {
                "speckit.specify": {"number": 100, "node_id": "I_100", "url": ""},
                "speckit.plan": {"number": 101, "node_id": "I_101", "url": ""},
            },
        )

        pipeline = PipelineState(
            issue_number=42,
            project_id="PVT_123",
            status="Ready",
            agents=["speckit.specify", "speckit.plan"],
            current_agent_index=2,
            completed_agents=["speckit.specify", "speckit.plan"],
            agent_sub_issues={},
        )

        # First call fails, second succeeds
        mock_service.update_issue_state = AsyncMock(side_effect=[Exception("API error"), True])
        mock_service.update_sub_issue_project_status = AsyncMock()

        # Should NOT raise
        await _close_completed_sub_issues(
            access_token="token",
            project_id="PVT_123",
            owner="owner",
            repo="repo",
            issue_number=42,
            completed_agents=list(pipeline.completed_agents),
            pipeline=pipeline,
        )

        # Both agents were attempted
        assert mock_service.update_issue_state.call_count == 2
        # Board status update is in a separate try/except, so it's called
        # for both agents regardless of the close failure.
        assert mock_service.update_sub_issue_project_status.call_count == 2


class TestProcessPipelineCompletionClosesSubIssues:
    """Tests that _process_pipeline_completion closes sub-issues when
    pipeline.is_complete (e.g. after a server restart reconstruction)."""

    @pytest.fixture(autouse=True)
    def clear_states(self):
        from src.services.workflow_orchestrator import (
            _issue_sub_issue_map,
            _pipeline_states,
        )

        _pipeline_states.clear()
        _issue_sub_issue_map.clear()
        yield
        _pipeline_states.clear()
        _issue_sub_issue_map.clear()

    @pytest.mark.asyncio
    @patch(
        "src.services.copilot_polling.pipeline._close_completed_sub_issues", new_callable=AsyncMock
    )
    @patch("src.services.copilot_polling.github_projects_service")
    @patch("src.services.copilot_polling.connection_manager")
    @patch("src.services.copilot_polling.get_workflow_orchestrator")
    @patch("src.services.copilot_polling.get_workflow_config", new_callable=AsyncMock)
    async def test_is_complete_branch_calls_close_sub_issues(
        self,
        mock_config,
        mock_get_orchestrator,
        mock_ws,
        mock_service,
        mock_close_subs,
    ):
        """When pipeline.is_complete, _process_pipeline_completion should
        call _close_completed_sub_issues before transitioning status."""
        from src.services.copilot_polling import _process_pipeline_completion

        pipeline = PipelineState(
            issue_number=42,
            project_id="PVT_123",
            status="Ready",
            agents=["speckit.plan", "speckit.tasks"],
            current_agent_index=2,
            completed_agents=["speckit.plan", "speckit.tasks"],
        )

        task = MagicMock()
        task.issue_number = 42
        task.github_item_id = "PVTI_123"
        task.github_content_id = "I_123"
        task.repository_owner = "owner"
        task.repository_name = "repo"
        task.title = "Test Issue"

        body = (
            "Issue body\n\n---\n\n## 🤖 Agent Pipeline\n\n"
            "| # | Status | Agent | Model | State |\n"
            "|---|--------|-------|-------|-------|\n"
            "| 1 | Ready | `speckit.plan` | gpt-4o | 🔄 Active |\n"
            "| 2 | Ready | `speckit.tasks` | gpt-4o | 🔄 Active |\n"
        )

        mock_service.get_issue_with_comments = AsyncMock(
            return_value={"body": body, "comments": []}
        )
        mock_service.update_issue_body = AsyncMock(return_value=True)
        mock_service.update_item_status_by_name = AsyncMock(return_value=True)
        mock_ws.broadcast_to_project = AsyncMock()

        mock_orchestrator = MagicMock()
        mock_orchestrator.assign_agent_for_status = AsyncMock(return_value=True)
        mock_get_orchestrator.return_value = mock_orchestrator
        mock_config.return_value = MagicMock(
            status_backlog="Backlog",
            status_ready="Ready",
            status_in_progress="In Progress",
            status_in_review="In Review",
            agent_mappings={},
        )

        await _process_pipeline_completion(
            access_token="token",
            project_id="PVT_123",
            task=task,
            owner="owner",
            repo="repo",
            pipeline=pipeline,
            from_status="Ready",
            to_status="In Progress",
        )

        # _close_completed_sub_issues should have been called
        mock_close_subs.assert_called_once()
        call_kwargs = mock_close_subs.call_args.kwargs
        assert sorted(call_kwargs["completed_agents"]) == ["speckit.plan", "speckit.tasks"]
        assert call_kwargs["issue_number"] == 42


class TestProcessPipelineCompletionBatchTracking:
    """Tests that _process_pipeline_completion batch-updates the tracking
    table when pipeline.is_complete is True (e.g. after reconstruction)."""

    @pytest.fixture(autouse=True)
    def clear_states(self):
        from src.services.workflow_orchestrator import _pipeline_states

        _pipeline_states.clear()
        yield
        _pipeline_states.clear()

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    @patch("src.services.copilot_polling.connection_manager")
    @patch("src.services.copilot_polling.get_workflow_orchestrator")
    @patch("src.services.copilot_polling.get_workflow_config", new_callable=AsyncMock)
    async def test_batch_marks_all_completed_agents_done(
        self,
        mock_config,
        mock_get_orchestrator,
        mock_ws,
        mock_service,
    ):
        """When pipeline.is_complete, _process_pipeline_completion should
        batch-update all completed agents to ✅ Done in a single API call."""
        from src.services.copilot_polling import _process_pipeline_completion

        pipeline = PipelineState(
            issue_number=42,
            project_id="PVT_123",
            status="Ready",
            agents=["speckit.plan", "speckit.tasks"],
            current_agent_index=2,
            completed_agents=["speckit.plan", "speckit.tasks"],
        )

        task = MagicMock()
        task.issue_number = 42
        task.github_item_id = "PVTI_123"
        task.github_content_id = "I_123"
        task.repository_owner = "owner"
        task.repository_name = "repo"
        task.title = "Test Issue"

        body_with_active = (
            "Issue body\n\n---\n\n## 🤖 Agent Pipeline\n\n"
            "| # | Status | Agent | Model | State |\n"
            "|---|--------|-------|-------|-------|\n"
            "| 1 | Ready | `speckit.plan` | gpt-4o | 🔄 Active |\n"
            "| 2 | Ready | `speckit.tasks` | gpt-4o | 🔄 Active |\n"
        )

        mock_service.get_issue_with_comments = AsyncMock(
            return_value={"body": body_with_active, "comments": []}
        )
        mock_service.update_issue_body = AsyncMock(return_value=True)
        mock_service.update_item_status_by_name = AsyncMock(return_value=True)
        mock_ws.broadcast_to_project = AsyncMock()

        mock_orchestrator = MagicMock()
        mock_orchestrator.assign_agent_for_status = AsyncMock(return_value=True)
        mock_get_orchestrator.return_value = mock_orchestrator
        mock_config.return_value = MagicMock(
            status_backlog="Backlog",
            status_ready="Ready",
            status_in_progress="In Progress",
            status_in_review="In Review",
            agent_mappings={},
        )

        await _process_pipeline_completion(
            access_token="token",
            project_id="PVT_123",
            task=task,
            owner="owner",
            repo="repo",
            pipeline=pipeline,
            from_status="Ready",
            to_status="In Progress",
        )

        # Verify the tracking table was batch-updated
        mock_service.update_issue_body.assert_called_once()
        pushed_body = mock_service.update_issue_body.call_args.kwargs["body"]
        assert "✅ Done" in pushed_body
        assert "🔄 Active" not in pushed_body

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    @patch("src.services.copilot_polling.connection_manager")
    @patch("src.services.copilot_polling.get_workflow_orchestrator")
    @patch("src.services.copilot_polling.get_workflow_config", new_callable=AsyncMock)
    async def test_batch_update_is_single_round_trip(
        self,
        mock_config,
        mock_get_orchestrator,
        mock_ws,
        mock_service,
    ):
        """The batch tracking update should fetch + push only once, not once per agent."""
        from src.services.copilot_polling import _process_pipeline_completion

        pipeline = PipelineState(
            issue_number=42,
            project_id="PVT_123",
            status="Ready",
            agents=["speckit.plan", "speckit.tasks"],
            current_agent_index=2,
            completed_agents=["speckit.plan", "speckit.tasks"],
        )

        task = MagicMock()
        task.issue_number = 42
        task.github_item_id = "PVTI_123"
        task.github_content_id = "I_123"
        task.repository_owner = "owner"
        task.repository_name = "repo"
        task.title = "Test"

        body_with_active = (
            "Body\n\n---\n\n## 🤖 Agent Pipeline\n\n"
            "| # | Status | Agent | Model | State |\n"
            "|---|--------|-------|-------|-------|\n"
            "| 1 | Ready | `speckit.plan` | gpt-4o | 🔄 Active |\n"
            "| 2 | Ready | `speckit.tasks` | gpt-4o | 🔄 Active |\n"
        )

        mock_service.get_issue_with_comments = AsyncMock(
            return_value={"body": body_with_active, "comments": []}
        )
        mock_service.update_issue_body = AsyncMock(return_value=True)
        mock_service.update_item_status_by_name = AsyncMock(return_value=True)
        mock_ws.broadcast_to_project = AsyncMock()
        mock_orchestrator = MagicMock()
        mock_orchestrator.assign_agent_for_status = AsyncMock(return_value=True)
        mock_get_orchestrator.return_value = mock_orchestrator
        mock_config.return_value = MagicMock(
            status_backlog="Backlog",
            status_ready="Ready",
            status_in_progress="In Progress",
            status_in_review="In Review",
            agent_mappings={},
        )

        await _process_pipeline_completion(
            access_token="token",
            project_id="PVT_123",
            task=task,
            owner="owner",
            repo="repo",
            pipeline=pipeline,
            from_status="Ready",
            to_status="In Progress",
        )

        # Single fetch + single push (not one per completed agent)
        assert mock_service.get_issue_with_comments.call_count == 1
        mock_service.update_issue_body.assert_called_once()

        # The pushed body should have both agents as ✅ Done
        pushed_body = mock_service.update_issue_body.call_args.kwargs["body"]
        assert "✅ Done" in pushed_body
        assert "🔄 Active" not in pushed_body


# ────────────────────────────────────────────────────────────────────
# Regression: pipeline stall after copilot-review (T-judge-stall)
# ────────────────────────────────────────────────────────────────────


class TestPipelineAdvancesAfterCopilotReview:
    """Regression test: after copilot-review completes, judge must be
    assigned even when child PRs from prior statuses exist.

    Root cause: the "never assigned" heuristic compared total Copilot-
    authored child PRs against completed-agents-in-current-status + 1.
    Child PRs from previous statuses (speckit.plan, speckit.tasks,
    speckit.implement) inflated the actual count, making the code
    believe judge was already assigned.
    """

    @pytest.fixture(autouse=True)
    def clear_states(self):
        from src.services.workflow_orchestrator import _pipeline_states

        _pipeline_states.clear()
        _pending_agent_assignments.clear()
        yield
        _pipeline_states.clear()
        _pending_agent_assignments.clear()

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.get_workflow_config", new_callable=AsyncMock)
    @patch("src.services.copilot_polling.get_workflow_orchestrator")
    @patch("src.services.copilot_polling.connection_manager")
    @patch("src.services.copilot_polling.github_projects_service")
    async def test_judge_assigned_despite_prior_child_prs(
        self,
        mock_service,
        mock_ws,
        mock_get_orch,
        mock_get_config,
    ):
        """When pipeline is reconstructed after copilot-review Done!, judge
        must be assigned even if child PRs from prior agents exist."""
        from src.services.copilot_polling import _process_pipeline_completion

        # Pipeline reconstructed: copilot-review done, judge is next
        pipeline = PipelineState(
            issue_number=42,
            project_id="PVT_123",
            status="In Review",
            agents=["copilot-review", "judge", "linter"],
            current_agent_index=1,
            completed_agents=["copilot-review"],
            started_at=utcnow() - timedelta(minutes=10),  # well past grace period
        )

        task = MagicMock()
        task.issue_number = 42
        task.github_item_id = "PVTI_123"
        task.github_content_id = "I_123"
        task.repository_owner = "owner"
        task.repository_name = "repo"
        task.title = "Test Issue"

        # judge has NOT completed (no Done! marker)
        mock_service.check_agent_completion_comment = AsyncMock(return_value=False)

        # Tracking table shows judge as ⏳ Pending (not 🔄 Active)
        body_pending = (
            "Body\n\n---\n\n## 🤖 Agent Pipeline\n\n"
            "| # | Status | Agent | Model | State |\n"
            "|---|--------|-------|-------|-------|\n"
            "| 5 | In Review | `copilot-review` | gpt-4o | ✅ Done |\n"
            "| 6 | In Review | `judge` | gpt-4o | ⏳ Pending |\n"
            "| 7 | In Review | `linter` | gpt-4o | ⏳ Pending |\n"
        )
        mock_service.get_issue_with_comments = AsyncMock(
            return_value={"body": body_pending, "comments": []}
        )

        # Set up orchestrator mock
        mock_orchestrator = MagicMock()
        mock_orchestrator.assign_agent_for_status = AsyncMock(return_value=True)
        mock_get_orch.return_value = mock_orchestrator
        mock_get_config.return_value = MagicMock()
        mock_ws.broadcast_to_project = AsyncMock()

        result = await _process_pipeline_completion(
            access_token="token",
            project_id="PVT_123",
            task=task,
            owner="owner",
            repo="repo",
            pipeline=pipeline,
            from_status="In Review",
            to_status="Done",
        )

        # judge MUST be assigned
        assert result is not None
        assert result["action"] == "agent_assigned_after_reconstruction"
        assert result["agent_name"] == "judge"
        mock_orchestrator.assign_agent_for_status.assert_awaited_once()


# ────────────────────────────────────────────────────────────────────
# _discover_main_pr_for_review  (new helper for sub-issue PR discovery)
# ────────────────────────────────────────────────────────────────────


class TestDiscoverMainPrForReview:
    """Tests for _discover_main_pr_for_review — comprehensive main PR discovery."""

    @pytest.fixture(autouse=True)
    def _clear(self):
        _issue_main_branches.clear()
        yield
        _issue_main_branches.clear()

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    @patch("src.services.copilot_polling.get_issue_main_branch")
    async def test_strategy1_in_memory_cache(self, mock_main_branch, mock_service):
        """Strategy 1: returns PR from in-memory cache."""
        mock_main_branch.return_value = {
            "branch": "copilot/feature",
            "pr_number": 100,
            "head_sha": "abc",
        }
        mock_service.get_pull_request = AsyncMock(
            return_value={"id": "PR_node_100", "is_draft": False, "last_commit": {"sha": "abc"}}
        )

        result = await _discover_main_pr_for_review("tok", "o", "r", 42)

        assert result is not None
        assert result["pr_number"] == 100
        assert result["pr_id"] == "PR_node_100"
        assert result["is_draft"] is False

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    @patch("src.services.copilot_polling.get_issue_main_branch")
    async def test_strategy2_find_existing_pr(self, mock_main_branch, mock_service):
        """Strategy 2: finds PR via find_existing_pr_for_issue on parent issue."""
        mock_main_branch.return_value = None
        mock_service.find_existing_pr_for_issue = AsyncMock(
            return_value={"number": 200, "head_ref": "feature/issue-42"}
        )
        mock_service.get_pull_request = AsyncMock(
            return_value={"id": "PR_node_200", "is_draft": True, "last_commit": {"sha": "def456"}}
        )

        result = await _discover_main_pr_for_review("tok", "o", "r", 42)

        assert result is not None
        assert result["pr_number"] == 200
        assert result["pr_id"] == "PR_node_200"
        assert result["is_draft"] is True
        mock_service.find_existing_pr_for_issue.assert_awaited_once()

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.get_issue_sub_issues")
    @patch("src.services.copilot_polling.github_projects_service")
    @patch("src.services.copilot_polling.get_issue_main_branch")
    async def test_strategy3_sub_issue_discovery(
        self, mock_main_branch, mock_service, mock_get_subs
    ):
        """Strategy 3: discovers main PR via speckit.specify sub-issue."""
        mock_main_branch.return_value = None
        mock_service.find_existing_pr_for_issue = AsyncMock(return_value=None)

        # Sub-issue mappings point to sub-issue #50
        mock_get_subs.return_value = {"speckit.specify": {"number": 50, "node_id": "I_50"}}

        # Sub-issue #50 has a linked PR #300 targeting default branch
        mock_service.get_linked_pull_requests = AsyncMock(
            return_value=[{"number": 300, "state": "OPEN", "head_ref": "copilot/fix-50"}]
        )
        mock_service.get_pull_request = AsyncMock(
            return_value={
                "id": "PR_node_300",
                "is_draft": True,
                "base_ref": "main",
                "last_commit": {"sha": "ghi"},
            }
        )
        mock_service.get_repository_info = AsyncMock(
            return_value={"repository_id": "R_123", "default_branch": "main", "head_oid": "xyz"}
        )
        mock_service.link_pull_request_to_issue = AsyncMock()

        result = await _discover_main_pr_for_review("tok", "o", "r", 42)

        assert result is not None
        assert result["pr_number"] == 300
        assert result["pr_id"] == "PR_node_300"
        assert result["head_ref"] == "copilot/fix-50"
        assert result["is_draft"] is True
        # Should have linked the PR to the parent issue
        mock_service.link_pull_request_to_issue.assert_awaited()

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.get_issue_sub_issues")
    @patch("src.services.copilot_polling.github_projects_service")
    @patch("src.services.copilot_polling.get_issue_main_branch")
    async def test_strategy3_skips_child_prs(self, mock_main_branch, mock_service, mock_get_subs):
        """Strategy 3 should skip child PRs (targeting feature branch, not default)."""
        mock_main_branch.return_value = None
        mock_service.find_existing_pr_for_issue = AsyncMock(return_value=None)
        mock_get_subs.return_value = {"speckit.specify": {"number": 50, "node_id": "I_50"}}

        # The PR targets a feature branch, not the default branch
        mock_service.get_linked_pull_requests = AsyncMock(
            return_value=[{"number": 301, "state": "OPEN", "head_ref": "copilot/plan-50"}]
        )
        mock_service.get_pull_request = AsyncMock(
            return_value={
                "id": "PR_node_301",
                "is_draft": True,
                "base_ref": "copilot/fix-50",
                "last_commit": {"sha": "xyz"},
            }
        )
        mock_service.get_repository_info = AsyncMock(
            return_value={"repository_id": "R_123", "default_branch": "main", "head_oid": "xyz"}
        )
        mock_service.get_sub_issues = AsyncMock(return_value=[])
        # Strategy 5: REST search also returns nothing
        mock_service._search_open_prs_for_issue_rest = AsyncMock(return_value=[])

        result = await _discover_main_pr_for_review("tok", "o", "r", 42)

        assert result is None

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.get_issue_sub_issues")
    @patch("src.services.copilot_polling.github_projects_service")
    @patch("src.services.copilot_polling.get_issue_main_branch")
    async def test_strategy5_rest_search_finds_pr(
        self, mock_main_branch, mock_service, mock_get_subs
    ):
        """Strategy 5: discovers PR via REST search by branch pattern / body reference."""
        mock_main_branch.return_value = None
        mock_service.find_existing_pr_for_issue = AsyncMock(return_value=None)
        mock_get_subs.return_value = {}
        mock_service.get_sub_issues = AsyncMock(return_value=[])

        # Strategy 5: REST search for open PRs matching the issue
        mock_service._search_open_prs_for_issue_rest = AsyncMock(
            return_value=[
                {
                    "number": 350,
                    "state": "OPEN",
                    "head_ref": "copilot/fix-42-feature",
                    "id": "PR_node_350",
                    "is_draft": True,
                }
            ]
        )
        mock_service.get_repository_info = AsyncMock(
            return_value={"repository_id": "R_123", "default_branch": "main", "head_oid": "xyz"}
        )
        mock_service.get_pull_request = AsyncMock(
            return_value={
                "id": "PR_node_350",
                "is_draft": True,
                "base_ref": "main",
                "last_commit": {"sha": "rst"},
            }
        )

        result = await _discover_main_pr_for_review("tok", "o", "r", 42)

        assert result is not None
        assert result["pr_number"] == 350
        assert result["pr_id"] == "PR_node_350"
        assert result["is_draft"] is True
        mock_service._search_open_prs_for_issue_rest.assert_awaited_once()

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.get_issue_sub_issues")
    @patch("src.services.copilot_polling.github_projects_service")
    @patch("src.services.copilot_polling.get_issue_main_branch")
    async def test_strategy5_skips_prs_not_targeting_default(
        self, mock_main_branch, mock_service, mock_get_subs
    ):
        """Strategy 5 should skip PRs that don't target the default branch."""
        mock_main_branch.return_value = None
        mock_service.find_existing_pr_for_issue = AsyncMock(return_value=None)
        mock_get_subs.return_value = {}
        mock_service.get_sub_issues = AsyncMock(return_value=[])

        # REST search finds a PR but it targets a feature branch
        mock_service._search_open_prs_for_issue_rest = AsyncMock(
            return_value=[
                {
                    "number": 360,
                    "state": "OPEN",
                    "head_ref": "copilot/child-42",
                }
            ]
        )
        mock_service.get_repository_info = AsyncMock(
            return_value={"repository_id": "R_123", "default_branch": "main", "head_oid": "xyz"}
        )
        mock_service.get_pull_request = AsyncMock(
            return_value={
                "id": "PR_node_360",
                "is_draft": False,
                "base_ref": "copilot/fix-42",  # targets feature branch, not main
                "last_commit": {"sha": "uvw"},
            }
        )

        result = await _discover_main_pr_for_review("tok", "o", "r", 42)

        assert result is None

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.get_issue_sub_issues")
    @patch("src.services.copilot_polling.github_projects_service")
    @patch("src.services.copilot_polling.get_issue_main_branch")
    async def test_strategy6_creates_pr_from_branch(
        self, mock_main_branch, mock_service, mock_get_subs
    ):
        """Strategy 6: creates a PR when a branch exists but no open PR."""
        mock_main_branch.return_value = None
        mock_service.find_existing_pr_for_issue = AsyncMock(return_value=None)
        mock_get_subs.return_value = {"speckit.specify": {"number": 50, "node_id": "I_50"}}

        # Sub-issue has a MERGED PR (branch exists, no open PR)
        mock_service.get_linked_pull_requests = AsyncMock(
            return_value=[{"number": 400, "state": "MERGED", "head_ref": "copilot/fix-50"}]
        )
        mock_service.get_pull_request = AsyncMock(
            return_value={
                "id": "PR_node_400",
                "is_draft": False,
                "base_ref": "main",
                "last_commit": {"sha": "abc"},
            }
        )
        mock_service.get_repository_info = AsyncMock(
            return_value={"repository_id": "R_123", "default_branch": "main", "head_oid": "xyz"}
        )
        mock_service.get_issue_with_comments = AsyncMock(
            return_value={"title": "My Feature", "body": "Body text", "comments": []}
        )
        mock_service.create_pull_request = AsyncMock(
            return_value={
                "id": "PR_new_401",
                "number": 401,
                "url": "https://github.com/o/r/pull/401",
            }
        )
        # Strategy 5 returns nothing (branch was from sub-issue, not matching by REST search)
        mock_service._search_open_prs_for_issue_rest = AsyncMock(return_value=[])

        result = await _discover_main_pr_for_review("tok", "o", "r", 42)

        assert result is not None
        assert result["pr_number"] == 401
        assert result["pr_id"] == "PR_new_401"
        assert result["is_draft"] is False
        mock_service.create_pull_request.assert_awaited_once()

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.get_issue_sub_issues")
    @patch("src.services.copilot_polling.github_projects_service")
    @patch("src.services.copilot_polling.get_issue_main_branch")
    async def test_all_strategies_fail_returns_none(
        self, mock_main_branch, mock_service, mock_get_subs
    ):
        """When all strategies fail, returns None."""
        mock_main_branch.return_value = None
        mock_service.find_existing_pr_for_issue = AsyncMock(return_value=None)
        mock_get_subs.return_value = {}
        mock_service.get_sub_issues = AsyncMock(return_value=[])
        # Strategy 5 also returns nothing
        mock_service._search_open_prs_for_issue_rest = AsyncMock(return_value=[])

        result = await _discover_main_pr_for_review("tok", "o", "r", 42)

        assert result is None


class TestCheckCopilotReviewDone:
    """Tests for the copilot-review completion detection.

    copilot-review is NOT a coding agent — it never posts a Done! comment.
    Completion is detected by checking whether Copilot has submitted a code
    review on the main PR.  A confirmation delay ensures the detection is
    stable across two consecutive poll cycles.
    """

    @pytest.fixture(autouse=True)
    def _clear_review_detection_state(self):
        """Ensure the confirmation-delay dict and main-branch cache are clean between tests."""
        _copilot_review_first_detected.clear()
        _copilot_review_requested_at.clear()
        _issue_main_branches.clear()
        yield
        _copilot_review_first_detected.clear()
        _copilot_review_requested_at.clear()
        _issue_main_branches.clear()

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    @patch("src.services.copilot_polling.get_issue_main_branch")
    async def test_review_submitted_returns_true(self, mock_main_branch, mock_service):
        """When Copilot has submitted a PR review and confirmation delay elapsed, the step is done."""
        mock_main_branch.return_value = {"branch": "feature/issue-42", "pr_number": 100}
        mock_service.get_issue_with_comments = AsyncMock(
            return_value={"title": "", "body": "", "comments": [], "user": {"login": ""}}
        )
        mock_service.get_pull_request = AsyncMock(
            return_value={"id": "PR_node_1", "is_draft": False}
        )
        mock_service.has_copilot_reviewed_pr = AsyncMock(return_value=True)
        mock_service.create_issue_comment = AsyncMock(return_value={"id": 1})

        # Pre-populate: Solune requested the review
        request_ts = utcnow() - timedelta(minutes=5)
        _copilot_review_requested_at[42] = request_ts

        # Pre-populate first-detection to simulate prior poll cycle
        _copilot_review_first_detected[42] = utcnow() - timedelta(
            seconds=COPILOT_REVIEW_CONFIRMATION_DELAY_SECONDS + 1
        )

        result = await _check_copilot_review_done(
            access_token="token", owner="owner", repo="repo", parent_issue_number=42
        )

        assert result is True
        from src.services.copilot_polling.state import COPILOT_REVIEW_REQUEST_BUFFER_SECONDS

        expected_min_after = request_ts + timedelta(seconds=COPILOT_REVIEW_REQUEST_BUFFER_SECONDS)
        mock_service.has_copilot_reviewed_pr.assert_awaited_once_with(
            access_token="token",
            owner="owner",
            repo="repo",
            pr_number=100,
            min_submitted_after=expected_min_after,
        )

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    @patch("src.services.copilot_polling.get_issue_main_branch")
    async def test_review_first_detection_returns_false(self, mock_main_branch, mock_service):
        """On first detection of a Copilot review, return False (await confirmation)."""
        mock_main_branch.return_value = {"branch": "feature/issue-42", "pr_number": 100}
        mock_service.get_issue_with_comments = AsyncMock(
            return_value={"title": "", "body": "", "comments": [], "user": {"login": ""}}
        )
        mock_service.get_pull_request = AsyncMock(
            return_value={"id": "PR_node_1", "is_draft": False}
        )
        mock_service.has_copilot_reviewed_pr = AsyncMock(return_value=True)

        # Solune requested the review
        _copilot_review_requested_at[42] = utcnow() - timedelta(minutes=5)

        result = await _check_copilot_review_done(
            access_token="token", owner="owner", repo="repo", parent_issue_number=42
        )

        assert result is False
        # Should have recorded the first-detection timestamp
        assert 42 in _copilot_review_first_detected

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    @patch("src.services.copilot_polling.get_issue_main_branch")
    async def test_review_confirmation_delay_not_elapsed(self, mock_main_branch, mock_service):
        """While confirmation delay has not elapsed, return False."""
        mock_main_branch.return_value = {"branch": "feature/issue-42", "pr_number": 100}
        mock_service.get_issue_with_comments = AsyncMock(
            return_value={"title": "", "body": "", "comments": [], "user": {"login": ""}}
        )
        mock_service.get_pull_request = AsyncMock(
            return_value={"id": "PR_node_1", "is_draft": False}
        )
        mock_service.has_copilot_reviewed_pr = AsyncMock(return_value=True)

        # Solune requested the review
        _copilot_review_requested_at[42] = utcnow() - timedelta(minutes=5)

        # First detection was recent — delay not elapsed
        _copilot_review_first_detected[42] = utcnow() - timedelta(seconds=5)

        result = await _check_copilot_review_done(
            access_token="token", owner="owner", repo="repo", parent_issue_number=42
        )

        assert result is False
        # Timestamp should NOT be cleared
        assert 42 in _copilot_review_first_detected

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    @patch("src.services.copilot_polling.get_issue_main_branch")
    async def test_no_review_returns_false(self, mock_main_branch, mock_service):
        """When Copilot has not yet submitted a review, the step is not done."""
        mock_main_branch.return_value = {"branch": "feature/issue-42", "pr_number": 100}
        mock_service.get_issue_with_comments = AsyncMock(
            return_value={"title": "", "body": "", "comments": [], "user": {"login": ""}}
        )
        mock_service.get_pull_request = AsyncMock(
            return_value={"id": "PR_node_1", "is_draft": False}
        )
        mock_service.has_copilot_reviewed_pr = AsyncMock(return_value=False)
        mock_service.request_copilot_review = AsyncMock(return_value=True)

        # Solune requested the review
        _copilot_review_requested_at[42] = utcnow() - timedelta(minutes=5)

        result = await _check_copilot_review_done(
            access_token="token", owner="owner", repo="repo", parent_issue_number=42
        )

        assert result is False
        # Self-healing: should re-request the review since not yet reviewed
        mock_service.request_copilot_review.assert_awaited_once()

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    @patch("src.services.copilot_polling.get_issue_main_branch")
    async def test_no_main_branch_falls_back_to_api(self, mock_main_branch, mock_service):
        """When main branch is not cached, fall back to API to find the PR."""
        mock_main_branch.return_value = None
        mock_service.get_issue_with_comments = AsyncMock(
            return_value={"title": "", "body": "", "comments": [], "user": {"login": ""}}
        )
        mock_service.find_existing_pr_for_issue = AsyncMock(
            return_value={"number": 200, "head_ref": "feature/issue-42"}
        )
        mock_service.get_pull_request = AsyncMock(
            return_value={
                "id": "PR_node_2",
                "is_draft": False,
                "last_commit": {"sha": "abc123"},
            }
        )
        mock_service.has_copilot_reviewed_pr = AsyncMock(return_value=True)
        mock_service.create_issue_comment = AsyncMock(return_value={"id": 1})

        # Solune requested the review
        request_ts = utcnow() - timedelta(minutes=5)
        _copilot_review_requested_at[42] = request_ts

        # Pre-populate first-detection to simulate prior poll cycle
        _copilot_review_first_detected[42] = utcnow() - timedelta(
            seconds=COPILOT_REVIEW_CONFIRMATION_DELAY_SECONDS + 1
        )

        result = await _check_copilot_review_done(
            access_token="token", owner="owner", repo="repo", parent_issue_number=42
        )

        assert result is True
        mock_service.find_existing_pr_for_issue.assert_awaited_once()
        from src.services.copilot_polling.state import COPILOT_REVIEW_REQUEST_BUFFER_SECONDS

        expected_min_after = request_ts + timedelta(seconds=COPILOT_REVIEW_REQUEST_BUFFER_SECONDS)
        mock_service.has_copilot_reviewed_pr.assert_awaited_once_with(
            access_token="token",
            owner="owner",
            repo="repo",
            pr_number=200,
            min_submitted_after=expected_min_after,
        )

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    @patch("src.services.copilot_polling.get_issue_main_branch")
    async def test_no_pr_found_returns_false(self, mock_main_branch, mock_service):
        """When no main PR can be found, return False."""
        mock_main_branch.return_value = None
        mock_service.get_issue_with_comments = AsyncMock(
            return_value={"title": "", "body": "", "comments": [], "user": {"login": ""}}
        )
        mock_service.find_existing_pr_for_issue = AsyncMock(return_value=None)
        mock_service.get_sub_issues = AsyncMock(return_value=[])

        result = await _check_copilot_review_done(
            access_token="token", owner="owner", repo="repo", parent_issue_number=42
        )

        assert result is False

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    @patch("src.services.copilot_polling.get_issue_main_branch")
    async def test_false_positive_cleared_when_review_vanishes(
        self, mock_main_branch, mock_service
    ):
        """If review detected then vanishes on next cycle, first-detection timestamp is cleared."""
        mock_main_branch.return_value = {"branch": "feature/issue-42", "pr_number": 100}
        mock_service.get_issue_with_comments = AsyncMock(
            return_value={"title": "", "body": "", "comments": [], "user": {"login": ""}}
        )
        mock_service.get_pull_request = AsyncMock(
            return_value={"id": "PR_node_1", "is_draft": False}
        )
        mock_service.request_copilot_review = AsyncMock(return_value=True)

        # Solune requested the review
        _copilot_review_requested_at[42] = utcnow() - timedelta(minutes=5)

        # First cycle: review detected (sets timestamp)
        mock_service.has_copilot_reviewed_pr = AsyncMock(return_value=True)
        await _check_copilot_review_done(
            access_token="token", owner="owner", repo="repo", parent_issue_number=42
        )
        assert 42 in _copilot_review_first_detected

        # Second cycle: review vanished (false positive) — timestamp cleared
        mock_service.has_copilot_reviewed_pr = AsyncMock(return_value=False)
        result = await _check_copilot_review_done(
            access_token="token", owner="owner", repo="repo", parent_issue_number=42
        )
        assert result is False
        assert 42 not in _copilot_review_first_detected

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    @patch("src.services.copilot_polling.get_issue_main_branch")
    async def test_two_cycle_confirmation_flow(self, mock_main_branch, mock_service):
        """Full two-cycle flow: first detection returns False, after delay returns True."""
        mock_main_branch.return_value = {"branch": "feature/issue-42", "pr_number": 100}
        mock_service.get_issue_with_comments = AsyncMock(
            return_value={"title": "", "body": "", "comments": [], "user": {"login": ""}}
        )
        mock_service.get_pull_request = AsyncMock(
            return_value={"id": "PR_node_1", "is_draft": False}
        )
        mock_service.has_copilot_reviewed_pr = AsyncMock(return_value=True)
        mock_service.create_issue_comment = AsyncMock(return_value={"id": 1})

        # Solune requested the review
        _copilot_review_requested_at[42] = utcnow() - timedelta(minutes=5)

        # Cycle 1: first detection — sets timestamp, returns False
        result1 = await _check_copilot_review_done(
            access_token="token", owner="owner", repo="repo", parent_issue_number=42
        )
        assert result1 is False
        assert 42 in _copilot_review_first_detected

        # Simulate delay elapsed
        _copilot_review_first_detected[42] = utcnow() - timedelta(
            seconds=COPILOT_REVIEW_CONFIRMATION_DELAY_SECONDS + 1
        )

        # Cycle 2: confirmed — returns True and posts Done! marker
        result2 = await _check_copilot_review_done(
            access_token="token", owner="owner", repo="repo", parent_issue_number=42
        )
        assert result2 is True
        mock_service.create_issue_comment.assert_awaited_once()
        # Timestamp should be cleaned up
        assert 42 not in _copilot_review_first_detected

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    async def test_copilot_review_agent_routed_to_review_check(self, mock_service):
        """_check_agent_done_on_sub_or_parent should route copilot-review to PR review check."""
        with patch("src.services.copilot_polling.get_issue_main_branch") as mock_main_branch:
            mock_main_branch.return_value = {"branch": "feature/issue-42", "pr_number": 100}
            mock_service.get_issue_with_comments = AsyncMock(
                return_value={"title": "", "body": "", "comments": [], "user": {"login": ""}}
            )
            mock_service.get_pull_request = AsyncMock(
                return_value={"id": "PR_node_1", "is_draft": False}
            )
            mock_service.has_copilot_reviewed_pr = AsyncMock(return_value=True)
            mock_service.create_issue_comment = AsyncMock(return_value={"id": 1})

            # Solune requested the review
            _copilot_review_requested_at[42] = utcnow() - timedelta(minutes=5)

            # Pre-populate first-detection to simulate prior poll cycle
            _copilot_review_first_detected[42] = utcnow() - timedelta(
                seconds=COPILOT_REVIEW_CONFIRMATION_DELAY_SECONDS + 1
            )

            result = await _check_agent_done_on_sub_or_parent(
                access_token="token",
                owner="owner",
                repo="repo",
                parent_issue_number=42,
                agent_name="copilot-review",
            )

            assert result is True
            # get_issue_with_comments IS called (for Done! marker check)
            # but the actual completion is detected via has_copilot_reviewed_pr
            mock_service.has_copilot_reviewed_pr.assert_awaited_once()

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    async def test_copilot_review_not_done_returns_false(self, mock_service):
        """_check_agent_done_on_sub_or_parent returns False when review not submitted."""
        with patch("src.services.copilot_polling.get_issue_main_branch") as mock_main_branch:
            mock_main_branch.return_value = {"branch": "feature/issue-42", "pr_number": 100}
            mock_service.get_issue_with_comments = AsyncMock(
                return_value={"title": "", "body": "", "comments": [], "user": {"login": ""}}
            )
            mock_service.get_pull_request = AsyncMock(
                return_value={"id": "PR_node_1", "is_draft": False}
            )
            mock_service.has_copilot_reviewed_pr = AsyncMock(return_value=False)
            mock_service.request_copilot_review = AsyncMock(return_value=True)

            # Solune requested the review
            _copilot_review_requested_at[42] = utcnow() - timedelta(minutes=5)

            result = await _check_agent_done_on_sub_or_parent(
                access_token="token",
                owner="owner",
                repo="repo",
                parent_issue_number=42,
                agent_name="copilot-review",
            )

            assert result is False
            # get_issue_with_comments IS called (for Done! marker)
            # but has_copilot_reviewed_pr returned False so step is not done
            mock_service.has_copilot_reviewed_pr.assert_awaited_once()


# ────────────────────────────────────────────────────────────────────
# check_in_review_issues
# ────────────────────────────────────────────────────────────────────


class TestCheckInReviewIssuesPipeline:
    """Tests for check_in_review_issues — detects completed Copilot reviews
    and advances the pipeline to Done."""

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.get_workflow_config")
    @patch("src.services.copilot_polling.github_projects_service")
    async def test_no_in_review_issues_returns_empty(self, mock_service, mock_config):
        """When no issues are in 'In Review', return empty list."""
        mock_config.return_value = MagicMock(
            status_in_review="In Review",
            agent_mappings={"In Review": [MagicMock(slug="copilot-review")]},
        )

        task = MagicMock()
        task.status = "Backlog"
        task.issue_number = 42
        mock_service.get_project_items = AsyncMock(return_value=[task])

        results = await check_in_review_issues(
            access_token="token",
            project_id="PVT_123",
            owner="owner",
            repo="repo",
        )

        assert results == []

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.get_workflow_config")
    @patch("src.services.copilot_polling.github_projects_service")
    async def test_no_config_returns_empty(self, mock_service, mock_config):
        """When no workflow config exists, return empty list."""
        mock_config.return_value = None

        results = await check_in_review_issues(
            access_token="token",
            project_id="PVT_123",
            owner="owner",
            repo="repo",
        )

        assert results == []


# ────────────────────────────────────────────────────────────────────
# Regression: WIP child PR false completion (T-wip-false-positive)
# ────────────────────────────────────────────────────────────────────


class TestWipChildPrFalsePositive:
    """Regression tests: child PRs with [WIP] title and only 1 commit
    (the 'Initial plan' placeholder) must NOT be treated as complete,
    even if draft=False.

    Root cause: _find_completed_child_pr treated any non-draft child PR
    as completed by Copilot.  But Copilot sometimes creates child PRs
    as non-draft immediately, or marks them ready before doing real work.
    """

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    async def test_wip_non_draft_1_commit_not_complete(self, mock_service):
        """A non-draft child PR with [WIP] title and 1 commit is NOT complete."""
        mock_service.is_copilot_author.return_value = True
        mock_service.get_linked_pull_requests = AsyncMock(
            return_value=[
                {"number": 200, "state": "OPEN", "author": "Copilot"},
            ]
        )
        mock_service.get_pull_request = AsyncMock(
            return_value={
                "id": "PR_200",
                "base_ref": "copilot/feature-branch",
                "head_ref": "copilot/feature-branch-again",
                "title": "[WIP] Implement feature",
                "is_draft": False,
                "commits": 1,
                "last_commit": {"sha": "abc123"},
            }
        )
        # Timeline has no copilot_finished events
        mock_service.get_pr_timeline_events = AsyncMock(return_value=[])
        mock_service.check_copilot_finished_events.return_value = False

        result = await _find_completed_child_pr(
            access_token="token",
            owner="owner",
            repo="repo",
            issue_number=42,
            main_branch="copilot/feature-branch",
            main_pr_number=100,
            agent_name="linter",
        )

        # Must NOT be detected as complete
        assert result is None

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    async def test_non_draft_no_wip_is_complete(self, mock_service):
        """A non-draft child PR WITHOUT [WIP] title is considered complete."""
        mock_service.is_copilot_author.return_value = True
        mock_service.get_linked_pull_requests = AsyncMock(
            return_value=[
                {"number": 200, "state": "OPEN", "author": "Copilot"},
            ]
        )
        mock_service.get_pull_request = AsyncMock(
            return_value={
                "id": "PR_200",
                "base_ref": "copilot/feature-branch",
                "head_ref": "copilot/feature-branch-again",
                "title": "Implement feature",
                "is_draft": False,
                "commits": 3,
                "last_commit": {"sha": "abc123"},
            }
        )

        result = await _find_completed_child_pr(
            access_token="token",
            owner="owner",
            repo="repo",
            issue_number=42,
            main_branch="copilot/feature-branch",
            main_pr_number=100,
            agent_name="linter",
        )

        # Should be detected as complete (no [WIP], multiple commits)
        assert result is not None
        assert result["copilot_finished"] is True

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    async def test_wip_with_multiple_commits_is_complete(self, mock_service):
        """A non-draft PR with [WIP] title but >1 commits IS complete
        (Copilot pushed real work but title wasn't updated)."""
        mock_service.is_copilot_author.return_value = True
        mock_service.get_linked_pull_requests = AsyncMock(
            return_value=[
                {"number": 200, "state": "OPEN", "author": "Copilot"},
            ]
        )
        mock_service.get_pull_request = AsyncMock(
            return_value={
                "id": "PR_200",
                "base_ref": "copilot/feature-branch",
                "head_ref": "copilot/feature-branch-again",
                "title": "[WIP] Implement feature",
                "is_draft": False,
                "commits": 4,
                "last_commit": {"sha": "abc123"},
            }
        )

        result = await _find_completed_child_pr(
            access_token="token",
            owner="owner",
            repo="repo",
            issue_number=42,
            main_branch="copilot/feature-branch",
            main_pr_number=100,
            agent_name="linter",
        )

        # Multiple commits = real work done, treat as complete
        assert result is not None
        assert result["copilot_finished"] is True


# ────────────────────────────────────────────────────────────────────
# Polling watchdog
# ────────────────────────────────────────────────────────────────────


class TestPollingWatchdog:
    """Tests for the _polling_watchdog_loop watchdog in main.py.

    The watchdog ensures the agent pipeline always recovers even when
    the polling loop stops unexpectedly (crash, task cancellation, etc.).
    """

    @pytest.mark.asyncio
    @patch("asyncio.sleep", new_callable=AsyncMock)
    async def test_watchdog_restarts_stopped_polling(self, mock_sleep):
        """When is_running=False the watchdog calls _auto_start_copilot_polling."""
        import asyncio

        sleep_calls = 0

        async def sleep_side_effect(*a, **kw):
            nonlocal sleep_calls
            sleep_calls += 1
            # Allow first cycle to run, then exit via CancelledError
            if sleep_calls > 1:
                raise asyncio.CancelledError()

        mock_sleep.side_effect = sleep_side_effect

        with patch("src.main._auto_start_copilot_polling", new_callable=AsyncMock) as mock_restart:
            with patch(
                "src.services.copilot_polling.get_polling_status",
                return_value={"is_running": False, "errors_count": 1, "last_error": "crash"},
            ):
                mock_restart.return_value = True
                from src.main import _polling_watchdog_loop

                await _polling_watchdog_loop()

        mock_restart.assert_awaited_once()

    @pytest.mark.asyncio
    @patch("asyncio.sleep", new_callable=AsyncMock)
    async def test_watchdog_does_not_restart_when_running(self, mock_sleep):
        """When is_running=True the watchdog does NOT call _auto_start_copilot_polling."""
        import asyncio

        sleep_calls = 0

        async def sleep_side_effect(*a, **kw):
            nonlocal sleep_calls
            sleep_calls += 1
            if sleep_calls > 1:
                raise asyncio.CancelledError()

        mock_sleep.side_effect = sleep_side_effect

        with patch("src.main._auto_start_copilot_polling", new_callable=AsyncMock) as mock_restart:
            with patch(
                "src.services.copilot_polling.get_polling_status",
                return_value={"is_running": True, "errors_count": 0, "last_error": None},
            ):
                from src.main import _polling_watchdog_loop

                await _polling_watchdog_loop()

        mock_restart.assert_not_awaited()

    @pytest.mark.asyncio
    @patch("asyncio.sleep", new_callable=AsyncMock)
    async def test_watchdog_tolerates_restart_failure(self, mock_sleep):
        """A failed restart attempt should not crash the watchdog loop."""
        import asyncio

        sleep_calls = 0

        async def sleep_side_effect(*a, **kw):
            nonlocal sleep_calls
            sleep_calls += 1
            if sleep_calls > 1:
                raise asyncio.CancelledError()

        mock_sleep.side_effect = sleep_side_effect

        with patch("src.main._auto_start_copilot_polling", new_callable=AsyncMock) as mock_restart:
            mock_restart.side_effect = RuntimeError("DB unavailable")
            with patch(
                "src.services.copilot_polling.get_polling_status",
                return_value={"is_running": False, "errors_count": 5, "last_error": "db error"},
            ):
                from src.main import _polling_watchdog_loop

                # Should complete normally even though restart raised
                await _polling_watchdog_loop()


# ────────────────────────────────────────────────────────────────────
# Recovery forced transition
# ────────────────────────────────────────────────────────────────────


class TestRecoveryForcedTransition:
    """Tests that recover_stalled_issues forces a status transition when all
    agents are ✅ Done but the issue has not yet advanced to the next status.

    Root cause of the issue #1474 regression: the polling loop stopped
    between the 'speckit.implement: Done!' comment and the 'In Progress'→
    'In Review' status update.  The next recovery cycle must detect this
    and trigger the transition unconditionally.
    """

    TRACKING_BODY_ALL_DONE = (
        "## Issue Body\n\n"
        "---\n\n"
        "## 🤖 Agent Pipeline\n\n"
        "| # | Status | Agent | Model | State |\n"
        "|---|--------|-------|-------|-------|\n"
        "| 1 | In Progress | `speckit.plan` | gpt-4o | ✅ Done |\n"
        "| 2 | In Progress | `speckit.tasks` | gpt-4o | ✅ Done |\n"
        "| 3 | In Progress | `speckit.implement` | gpt-4o | ✅ Done |\n"
    )

    @pytest.fixture(autouse=True)
    def clear_recovery_state(self):
        _recovery_last_attempt.clear()
        _pending_agent_assignments.clear()
        yield
        _recovery_last_attempt.clear()
        _pending_agent_assignments.clear()

    @pytest.fixture
    def mock_in_progress_task(self):
        task = MagicMock()
        task.github_item_id = "PVTI_1474"
        task.github_content_id = "I_1474"
        task.issue_number = 1474
        task.repository_owner = "Boykai"
        task.repository_name = "github-workflows"
        task.title = "Audit & Refactor"
        task.status = "In Progress"
        return task

    @pytest.mark.asyncio
    @patch(
        "src.services.copilot_polling.pipeline._transition_after_pipeline_complete",
        new_callable=AsyncMock,
    )
    @patch("src.services.copilot_polling.get_next_status")
    @patch("src.services.copilot_polling.github_projects_service")
    @patch("src.services.copilot_polling.get_workflow_config", new_callable=AsyncMock)
    async def test_forces_transition_when_all_done_not_yet_transitioned(
        self,
        mock_config,
        mock_service,
        mock_next_status,
        mock_transition,
        mock_in_progress_task,
    ):
        """All agents Done + non-terminal status → _transition_after_pipeline_complete called."""
        mock_config.return_value = MagicMock(
            status_in_review="In Review",
            agent_mappings={"In Progress": ["speckit.plan", "speckit.tasks", "speckit.implement"]},
        )
        mock_service.get_issue_with_comments = AsyncMock(
            return_value={"body": self.TRACKING_BODY_ALL_DONE}
        )
        mock_service.check_agent_completion_comment = AsyncMock(return_value=True)
        mock_next_status.return_value = "In Review"
        mock_transition.return_value = {"status": "success", "issue_number": 1474}

        results = await recover_stalled_issues(
            access_token="token",
            project_id="PVT_1",
            owner="Boykai",
            repo="github-workflows",
            tasks=[mock_in_progress_task],
        )

        mock_transition.assert_awaited_once_with(
            access_token="token",
            project_id="PVT_1",
            item_id="PVTI_1474",
            owner="Boykai",
            repo="github-workflows",
            issue_number=1474,
            issue_node_id="I_1474",
            from_status="In Progress",
            to_status="In Review",
            task_title="Audit & Refactor",
        )
        assert len(results) == 1
        assert results[0]["status"] == "recovered_transition"
        assert results[0]["from_status"] == "In Progress"
        assert results[0]["to_status"] == "In Review"

    @pytest.mark.asyncio
    @patch(
        "src.services.copilot_polling.pipeline._transition_after_pipeline_complete",
        new_callable=AsyncMock,
    )
    @patch("src.services.copilot_polling.get_next_status")
    @patch("src.services.copilot_polling.github_projects_service")
    @patch("src.services.copilot_polling.get_workflow_config", new_callable=AsyncMock)
    async def test_skips_transition_when_no_next_status(
        self,
        mock_config,
        mock_service,
        mock_next_status,
        mock_transition,
        mock_in_progress_task,
    ):
        """When get_next_status returns None, no transition is attempted."""
        mock_config.return_value = MagicMock(
            status_in_review="In Review",
            agent_mappings={"In Progress": ["speckit.plan"]},
        )
        mock_service.get_issue_with_comments = AsyncMock(
            return_value={"body": self.TRACKING_BODY_ALL_DONE}
        )
        mock_next_status.return_value = None

        results = await recover_stalled_issues(
            access_token="token",
            project_id="PVT_1",
            owner="Boykai",
            repo="github-workflows",
            tasks=[mock_in_progress_task],
        )

        mock_transition.assert_not_awaited()
        assert results == []

    @pytest.mark.asyncio
    @patch(
        "src.services.copilot_polling.pipeline._transition_after_pipeline_complete",
        new_callable=AsyncMock,
    )
    @patch("src.services.copilot_polling.get_next_status")
    @patch("src.services.copilot_polling.github_projects_service")
    @patch("src.services.copilot_polling.get_workflow_config", new_callable=AsyncMock)
    async def test_skips_transition_when_on_cooldown(
        self,
        mock_config,
        mock_service,
        mock_next_status,
        mock_transition,
        mock_in_progress_task,
    ):
        """Issues on recovery cooldown should not trigger another transition attempt."""
        from datetime import UTC, datetime

        mock_config.return_value = MagicMock(
            status_in_review="In Review",
            agent_mappings={"In Progress": ["speckit.plan"]},
        )
        mock_service.get_issue_with_comments = AsyncMock(
            return_value={"body": self.TRACKING_BODY_ALL_DONE}
        )
        mock_next_status.return_value = "In Review"
        # Simulate a very recent recovery attempt (still within cooldown)
        _recovery_last_attempt[1474] = datetime.now(UTC)

        results = await recover_stalled_issues(
            access_token="token",
            project_id="PVT_1",
            owner="Boykai",
            repo="github-workflows",
            tasks=[mock_in_progress_task],
        )

        mock_transition.assert_not_awaited()
        assert results == []

    @pytest.mark.asyncio
    @patch(
        "src.services.copilot_polling.pipeline._transition_after_pipeline_complete",
        new_callable=AsyncMock,
    )
    @patch("src.services.copilot_polling.get_next_status")
    @patch("src.services.copilot_polling.github_projects_service")
    @patch("src.services.copilot_polling.get_workflow_config", new_callable=AsyncMock)
    async def test_result_empty_when_transition_returns_none(
        self,
        mock_config,
        mock_service,
        mock_next_status,
        mock_transition,
        mock_in_progress_task,
    ):
        """When _transition_after_pipeline_complete returns None, results stay empty."""
        mock_config.return_value = MagicMock(
            status_in_review="In Review",
            agent_mappings={"In Progress": ["speckit.plan"]},
        )
        mock_service.get_issue_with_comments = AsyncMock(
            return_value={"body": self.TRACKING_BODY_ALL_DONE}
        )
        mock_service.check_agent_completion_comment = AsyncMock(return_value=True)
        mock_next_status.return_value = "In Review"
        mock_transition.return_value = None  # transition returned nothing

        results = await recover_stalled_issues(
            access_token="token",
            project_id="PVT_1",
            owner="Boykai",
            repo="github-workflows",
            tasks=[mock_in_progress_task],
        )

        mock_transition.assert_awaited_once()
        # No result appended when transition returns None
        assert results == []


# ────────────────────────────────────────────────────────────────────
# _check_copilot_review_done — Self-Healing
# ────────────────────────────────────────────────────────────────────


class TestCopilotReviewSelfHealing:
    """Tests for the self-healing behaviour in _check_copilot_review_done.

    When the initial copilot-review assignment fails to un-draft the PR
    or request the review, the completion-check function should retry
    those operations on every poll cycle.
    """

    @pytest.fixture(autouse=True)
    def _clear_review_detection_state(self):
        """Ensure the confirmation-delay dict is clean between tests."""
        _copilot_review_first_detected.clear()
        _copilot_review_requested_at.clear()
        yield
        _copilot_review_first_detected.clear()
        _copilot_review_requested_at.clear()

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.helpers._cp.github_projects_service")
    @patch("src.services.copilot_polling.helpers._cp.get_issue_main_branch")
    async def test_undrafts_pr_before_checking_review(self, mock_main_branch, mock_service):
        """When the main PR is still a draft, self-healing converts it to ready."""
        mock_main_branch.return_value = {"branch": "copilot/issue-99", "pr_number": 300}
        mock_service.get_issue_with_comments = AsyncMock(
            return_value={"title": "", "body": "", "comments": [], "user": {"login": ""}}
        )
        mock_service.get_pull_request = AsyncMock(
            return_value={"id": "PR_node_300", "is_draft": True}
        )
        mock_service.mark_pr_ready_for_review = AsyncMock(return_value=True)
        mock_service.has_copilot_reviewed_pr = AsyncMock(return_value=False)
        mock_service.request_copilot_review = AsyncMock(return_value=True)
        mock_service.dismiss_copilot_reviews = AsyncMock(return_value=0)

        result = await _check_copilot_review_done(
            access_token="token", owner="owner", repo="repo", parent_issue_number=99
        )

        assert result is False  # Review not yet submitted
        mock_service.mark_pr_ready_for_review.assert_awaited_once_with(
            access_token="token", pr_node_id="PR_node_300"
        )
        # Should dismiss auto-triggered reviews and re-request
        mock_service.dismiss_copilot_reviews.assert_awaited_once()
        mock_service.request_copilot_review.assert_awaited_once()

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.helpers._cp.github_projects_service")
    @patch("src.services.copilot_polling.helpers._cp.get_issue_main_branch")
    async def test_undraft_failure_returns_false(self, mock_main_branch, mock_service):
        """When un-drafting fails, return False without checking review status."""
        mock_main_branch.return_value = {"branch": "copilot/issue-99", "pr_number": 300}
        mock_service.get_issue_with_comments = AsyncMock(
            return_value={"title": "", "body": "", "comments": [], "user": {"login": ""}}
        )
        mock_service.get_pull_request = AsyncMock(
            return_value={"id": "PR_node_300", "is_draft": True}
        )
        mock_service.mark_pr_ready_for_review = AsyncMock(return_value=False)
        mock_service.has_copilot_reviewed_pr = AsyncMock(return_value=False)

        result = await _check_copilot_review_done(
            access_token="token", owner="owner", repo="repo", parent_issue_number=99
        )

        assert result is False
        mock_service.mark_pr_ready_for_review.assert_awaited_once()
        # Should NOT check review status since PR is still a draft
        mock_service.has_copilot_reviewed_pr.assert_not_awaited()

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.helpers._cp.github_projects_service")
    @patch("src.services.copilot_polling.helpers._cp.get_issue_main_branch")
    async def test_re_requests_review_when_not_reviewed(self, mock_main_branch, mock_service):
        """When PR is ready but not yet reviewed, re-request the Copilot review."""
        mock_main_branch.return_value = {"branch": "copilot/issue-99", "pr_number": 300}
        mock_service.get_issue_with_comments = AsyncMock(
            return_value={"title": "", "body": "", "comments": [], "user": {"login": ""}}
        )
        mock_service.get_pull_request = AsyncMock(
            return_value={"id": "PR_node_300", "is_draft": False}
        )
        mock_service.has_copilot_reviewed_pr = AsyncMock(return_value=False)
        mock_service.request_copilot_review = AsyncMock(return_value=True)
        mock_service.dismiss_copilot_reviews = AsyncMock(return_value=0)

        result = await _check_copilot_review_done(
            access_token="token", owner="owner", repo="repo", parent_issue_number=99
        )

        assert result is False
        # Should NOT try to un-draft (already ready)
        mock_service.mark_pr_ready_for_review.assert_not_called()
        # Should dismiss auto-triggered reviews and re-request
        mock_service.dismiss_copilot_reviews.assert_awaited_once()
        mock_service.request_copilot_review.assert_awaited_once_with(
            access_token="token",
            pr_node_id="PR_node_300",
            pr_number=300,
            owner="owner",
            repo="repo",
        )

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.helpers._cp.github_projects_service")
    @patch("src.services.copilot_polling.helpers._cp.get_issue_main_branch")
    async def test_skips_self_healing_when_already_reviewed(self, mock_main_branch, mock_service):
        """When Copilot has already reviewed, no self-healing calls are made."""
        mock_main_branch.return_value = {"branch": "copilot/issue-99", "pr_number": 300}
        mock_service.get_issue_with_comments = AsyncMock(
            return_value={"title": "", "body": "", "comments": [], "user": {"login": ""}}
        )
        mock_service.get_pull_request = AsyncMock(
            return_value={"id": "PR_node_300", "is_draft": False}
        )
        mock_service.has_copilot_reviewed_pr = AsyncMock(return_value=True)
        mock_service.create_issue_comment = AsyncMock(return_value={"id": 1})

        # Solune requested the review
        _copilot_review_requested_at[99] = utcnow() - timedelta(minutes=5)

        # Pre-populate first-detection to simulate prior poll cycle
        _copilot_review_first_detected[99] = utcnow() - timedelta(
            seconds=COPILOT_REVIEW_CONFIRMATION_DELAY_SECONDS + 1
        )

        result = await _check_copilot_review_done(
            access_token="token", owner="owner", repo="repo", parent_issue_number=99
        )

        assert result is True
        mock_service.mark_pr_ready_for_review.assert_not_called()
        mock_service.request_copilot_review.assert_not_called()


# ────────────────────────────────────────────────────────────────────
# _check_copilot_review_done — Auto-Trigger Protection
# ────────────────────────────────────────────────────────────────────


class TestCopilotReviewAutoTriggerProtection:
    """Tests that GitHub auto-triggered Copilot reviews are ignored.

    GitHub.com may automatically trigger a Copilot code review when a PR
    is opened.  Such reviews are ignored by _check_copilot_review_done
    unless Solune has explicitly requested the review (recorded in
    ``_copilot_review_requested_at``).
    """

    @pytest.fixture(autouse=True)
    def _clear_review_detection_state(self):
        _copilot_review_first_detected.clear()
        _copilot_review_requested_at.clear()
        _issue_main_branches.clear()
        yield
        _copilot_review_first_detected.clear()
        _copilot_review_requested_at.clear()
        _issue_main_branches.clear()

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.helpers._cp.github_projects_service")
    @patch("src.services.copilot_polling.helpers._cp.get_issue_main_branch")
    async def test_auto_triggered_review_ignored_when_not_requested(
        self, mock_main_branch, mock_service
    ):
        """When Solune never requested copilot-review, an existing review is ignored."""
        mock_main_branch.return_value = {"branch": "copilot/issue-50", "pr_number": 500}
        mock_service.get_issue_with_comments = AsyncMock(
            return_value={"title": "", "body": "", "comments": [], "user": {"login": ""}}
        )
        mock_service.get_pull_request = AsyncMock(
            return_value={"id": "PR_node_500", "is_draft": False}
        )
        # An auto-triggered review IS present on the PR
        mock_service.has_copilot_reviewed_pr = AsyncMock(return_value=True)
        mock_service.request_copilot_review = AsyncMock(return_value=True)
        mock_service.dismiss_copilot_reviews = AsyncMock(return_value=1)

        # _copilot_review_requested_at is EMPTY — Solune never requested this

        result = await _check_copilot_review_done(
            access_token="token", owner="owner", repo="repo", parent_issue_number=50
        )

        assert result is False
        # Should NOT call has_copilot_reviewed_pr (gate short-circuits before it)
        mock_service.has_copilot_reviewed_pr.assert_not_awaited()
        # Self-healing should dismiss auto-triggered reviews before requesting
        mock_service.dismiss_copilot_reviews.assert_awaited_once()
        mock_service.request_copilot_review.assert_awaited_once()
        assert 50 in _copilot_review_requested_at

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.helpers._cp.github_projects_service")
    @patch("src.services.copilot_polling.helpers._cp.get_issue_main_branch")
    async def test_review_detected_after_solune_request(self, mock_main_branch, mock_service):
        """When Solune requested the review and a review exists, step completes."""
        mock_main_branch.return_value = {"branch": "copilot/issue-50", "pr_number": 500}
        mock_service.get_issue_with_comments = AsyncMock(
            return_value={"title": "", "body": "", "comments": [], "user": {"login": ""}}
        )
        mock_service.get_pull_request = AsyncMock(
            return_value={"id": "PR_node_500", "is_draft": False}
        )
        mock_service.has_copilot_reviewed_pr = AsyncMock(return_value=True)
        mock_service.create_issue_comment = AsyncMock(return_value={"id": 1})

        # Solune requested the review 5 minutes ago
        _copilot_review_requested_at[50] = utcnow() - timedelta(minutes=5)
        # Confirmation delay elapsed
        _copilot_review_first_detected[50] = utcnow() - timedelta(
            seconds=COPILOT_REVIEW_CONFIRMATION_DELAY_SECONDS + 1
        )

        result = await _check_copilot_review_done(
            access_token="token", owner="owner", repo="repo", parent_issue_number=50
        )

        assert result is True
        mock_service.has_copilot_reviewed_pr.assert_awaited_once()

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.helpers._cp.github_projects_service")
    @patch("src.services.copilot_polling.helpers._cp.get_issue_main_branch")
    async def test_self_healing_records_timestamp_and_returns_false(
        self, mock_main_branch, mock_service
    ):
        """Self-healing dismisses, requests the review, records timestamp, returns False."""
        mock_main_branch.return_value = {"branch": "copilot/issue-50", "pr_number": 500}
        mock_service.get_issue_with_comments = AsyncMock(
            return_value={"title": "", "body": "", "comments": [], "user": {"login": ""}}
        )
        mock_service.get_pull_request = AsyncMock(
            return_value={"id": "PR_node_500", "is_draft": False}
        )
        mock_service.request_copilot_review = AsyncMock(return_value=True)
        mock_service.dismiss_copilot_reviews = AsyncMock(return_value=0)

        result = await _check_copilot_review_done(
            access_token="token", owner="owner", repo="repo", parent_issue_number=50
        )

        assert result is False
        assert 50 in _copilot_review_requested_at
        # Stale first-detection data should be cleared
        assert 50 not in _copilot_review_first_detected
        # Dismiss should be called before requesting
        mock_service.dismiss_copilot_reviews.assert_awaited_once()

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.helpers._cp.github_projects_service")
    @patch("src.services.copilot_polling.helpers._cp.get_issue_main_branch")
    async def test_self_healing_request_fails_no_timestamp_recorded(
        self, mock_main_branch, mock_service
    ):
        """If self-healing request_copilot_review fails, timestamp is not recorded."""
        mock_main_branch.return_value = {"branch": "copilot/issue-50", "pr_number": 500}
        mock_service.get_issue_with_comments = AsyncMock(
            return_value={"title": "", "body": "", "comments": [], "user": {"login": ""}}
        )
        mock_service.get_pull_request = AsyncMock(
            return_value={"id": "PR_node_500", "is_draft": False}
        )
        mock_service.request_copilot_review = AsyncMock(return_value=False)
        mock_service.dismiss_copilot_reviews = AsyncMock(return_value=0)

        result = await _check_copilot_review_done(
            access_token="token", owner="owner", repo="repo", parent_issue_number=50
        )

        assert result is False
        # Timestamp NOT recorded since request failed
        assert 50 not in _copilot_review_requested_at
        # Dismiss should still be called before the failed request
        mock_service.dismiss_copilot_reviews.assert_awaited_once()

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.helpers._cp.github_projects_service")
    @patch("src.services.copilot_polling.helpers._cp.get_issue_main_branch")
    async def test_min_submitted_after_includes_buffer(self, mock_main_branch, mock_service):
        """min_submitted_after = request_ts + buffer is passed to has_copilot_reviewed_pr."""
        mock_main_branch.return_value = {"branch": "copilot/issue-50", "pr_number": 500}
        mock_service.get_issue_with_comments = AsyncMock(
            return_value={"title": "", "body": "", "comments": [], "user": {"login": ""}}
        )
        mock_service.get_pull_request = AsyncMock(
            return_value={"id": "PR_node_500", "is_draft": False}
        )
        mock_service.has_copilot_reviewed_pr = AsyncMock(return_value=False)
        mock_service.request_copilot_review = AsyncMock(return_value=True)

        request_ts = utcnow() - timedelta(minutes=3)
        _copilot_review_requested_at[50] = request_ts

        await _check_copilot_review_done(
            access_token="token", owner="owner", repo="repo", parent_issue_number=50
        )

        expected_min_after = request_ts + timedelta(seconds=COPILOT_REVIEW_REQUEST_BUFFER_SECONDS)
        mock_service.has_copilot_reviewed_pr.assert_awaited_once_with(
            access_token="token",
            owner="owner",
            repo="repo",
            pr_number=500,
            min_submitted_after=expected_min_after,
        )

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.helpers._cp.github_projects_service")
    @patch("src.services.copilot_polling.helpers._cp.get_issue_main_branch")
    async def test_review_within_buffer_window_rejected(self, mock_main_branch, mock_service):
        """A review submitted within the buffer window after Solune's request is rejected."""
        mock_main_branch.return_value = {"branch": "copilot/issue-50", "pr_number": 500}
        mock_service.get_issue_with_comments = AsyncMock(
            return_value={"title": "", "body": "", "comments": [], "user": {"login": ""}}
        )
        mock_service.get_pull_request = AsyncMock(
            return_value={"id": "PR_node_500", "is_draft": False}
        )
        # has_copilot_reviewed_pr returns False because the review is within buffer
        mock_service.has_copilot_reviewed_pr = AsyncMock(return_value=False)
        mock_service.request_copilot_review = AsyncMock(return_value=True)

        # Request was 30s ago — well within the 120s buffer
        _copilot_review_requested_at[50] = utcnow() - timedelta(seconds=30)

        result = await _check_copilot_review_done(
            access_token="token", owner="owner", repo="repo", parent_issue_number=50
        )

        assert result is False

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.helpers._cp.github_projects_service")
    @patch("src.services.copilot_polling.helpers._cp.get_issue_main_branch")
    async def test_done_marker_ignored_when_no_request_timestamp(
        self, mock_main_branch, mock_service
    ):
        """A Done! marker alone is not enough without a recorded review request."""
        mock_main_branch.return_value = {"branch": "copilot/issue-50", "pr_number": 500}
        mock_service.get_issue_with_comments = AsyncMock(
            return_value={
                "title": "",
                "body": "",
                "user": {"login": ""},
                "comments": [
                    {
                        "body": "copilot-review: Done!",
                        "created_at": "2026-03-18T20:00:00Z",
                        "database_id": 123,
                        "node_id": "IC_1",
                        "author": "solune-bot",
                    },
                ],
            }
        )
        mock_service.get_pull_request = AsyncMock(
            return_value={"id": "PR_node_500", "is_draft": False}
        )
        mock_service.has_copilot_reviewed_pr = AsyncMock(return_value=False)
        mock_service.request_copilot_review = AsyncMock(return_value=True)
        mock_service.dismiss_copilot_reviews = AsyncMock(return_value=1)

        # No request timestamp (simulates server restart)
        result = await _check_copilot_review_done(
            access_token="token", owner="owner", repo="repo", parent_issue_number=50
        )

        assert result is False
        mock_service.dismiss_copilot_reviews.assert_awaited_once()
        mock_service.request_copilot_review.assert_awaited_once()

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.helpers._cp.github_projects_service")
    @patch("src.services.copilot_polling.helpers._cp.get_issue_main_branch")
    async def test_done_marker_rejected_when_older_than_request_timestamp(
        self, mock_main_branch, mock_service
    ):
        """A marker that predates Solune's explicit request is stale even without other Done! comments."""
        mock_main_branch.return_value = {"branch": "copilot/issue-50", "pr_number": 500}
        mock_service.get_issue_with_comments = AsyncMock(
            return_value={
                "title": "",
                "body": "",
                "user": {"login": ""},
                "comments": [
                    {
                        "body": "copilot-review: Done!",
                        "created_at": "2026-03-18T20:00:00Z",
                        "database_id": 123,
                        "node_id": "IC_1",
                        "author": "solune-bot",
                    },
                ],
            }
        )
        mock_service.get_pull_request = AsyncMock(
            return_value={"id": "PR_node_500", "is_draft": False}
        )
        mock_service.has_copilot_reviewed_pr = AsyncMock(return_value=False)
        mock_service.request_copilot_review = AsyncMock(return_value=True)
        mock_service.delete_issue_comment = AsyncMock(return_value=True)

        _copilot_review_requested_at[50] = utcnow()

        result = await _check_copilot_review_done(
            access_token="token", owner="owner", repo="repo", parent_issue_number=50
        )

        assert result is False
        mock_service.delete_issue_comment.assert_awaited_once_with(
            access_token="token",
            owner="owner",
            repo="repo",
            comment_database_id=123,
            issue_number=50,
        )
        mock_service.has_copilot_reviewed_pr.assert_awaited_once()

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.helpers._cp.github_projects_service")
    @patch("src.services.copilot_polling.helpers._cp.get_issue_main_branch")
    async def test_stale_done_marker_rejected_and_deleted(self, mock_main_branch, mock_service):
        """A Done! marker older than the latest agent Done! is stale — rejected and deleted."""
        mock_main_branch.return_value = {"branch": "copilot/issue-50", "pr_number": 500}
        mock_service.get_issue_with_comments = AsyncMock(
            return_value={
                "title": "",
                "body": "",
                "user": {"login": ""},
                "comments": [
                    # Stale copilot-review marker from auto-triggered review
                    {
                        "body": "copilot-review: Done!",
                        "created_at": "2026-03-18T17:00:00Z",
                        "database_id": 100,
                        "node_id": "IC_stale",
                        "author": "solune-bot",
                    },
                    # Agent that completed AFTER the stale marker
                    {
                        "body": "speckit.implement: Done!",
                        "created_at": "2026-03-18T19:00:00Z",
                        "database_id": 200,
                        "node_id": "IC_impl",
                        "author": "copilot-bot",
                    },
                ],
            }
        )
        mock_service.get_pull_request = AsyncMock(
            return_value={"id": "PR_node_500", "is_draft": False}
        )
        mock_service.has_copilot_reviewed_pr = AsyncMock(return_value=False)
        mock_service.request_copilot_review = AsyncMock(return_value=True)
        mock_service.dismiss_copilot_reviews = AsyncMock(return_value=0)
        mock_service.delete_issue_comment = AsyncMock(return_value=True)

        result = await _check_copilot_review_done(
            access_token="token", owner="owner", repo="repo", parent_issue_number=50
        )

        assert result is False
        # Stale marker should be deleted
        mock_service.delete_issue_comment.assert_awaited_once_with(
            access_token="token",
            owner="owner",
            repo="repo",
            comment_database_id=100,
            issue_number=50,
        )

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.helpers._cp.github_projects_service")
    @patch("src.services.copilot_polling.helpers._cp.get_issue_main_branch")
    async def test_valid_done_marker_accepted_when_newer_than_agents(
        self, mock_main_branch, mock_service
    ):
        """A Done! marker newer than all other agent Done! comments is valid."""
        mock_main_branch.return_value = {"branch": "copilot/issue-50", "pr_number": 500}
        mock_service.get_issue_with_comments = AsyncMock(
            return_value={
                "title": "",
                "body": "",
                "user": {"login": ""},
                "comments": [
                    # Agent completed first
                    {
                        "body": "speckit.implement: Done!",
                        "created_at": "2026-03-18T19:00:00Z",
                        "database_id": 200,
                        "node_id": "IC_impl",
                        "author": "copilot-bot",
                    },
                    # Valid copilot-review marker posted AFTER
                    {
                        "body": "copilot-review: Done!",
                        "created_at": "2026-03-18T20:00:00Z",
                        "database_id": 300,
                        "node_id": "IC_valid",
                        "author": "solune-bot",
                    },
                ],
            }
        )

        _copilot_review_requested_at[50] = datetime(2026, 3, 18, 18, 0, tzinfo=UTC)
        mock_service.delete_issue_comment = AsyncMock(return_value=True)

        result = await _check_copilot_review_done(
            access_token="token", owner="owner", repo="repo", parent_issue_number=50
        )

        assert result is True
        # Should not attempt to delete or discover PR
        mock_service.delete_issue_comment.assert_not_called()
        mock_service.get_pull_request.assert_not_called()

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.helpers._cp.github_projects_service")
    @patch("src.services.copilot_polling.helpers._cp.get_issue_main_branch")
    async def test_done_marker_metadata_restores_request_timestamp_after_restart(
        self, mock_main_branch, mock_service
    ):
        """Embedded marker metadata should restore the request timestamp after restart."""
        mock_main_branch.return_value = {"branch": "copilot/issue-50", "pr_number": 500}
        mock_service.get_issue_with_comments = AsyncMock(
            return_value={
                "title": "",
                "body": "",
                "user": {"login": ""},
                "comments": [
                    {
                        "body": (
                            "copilot-review: Done!\n"
                            "<!-- solune:copilot-review-requested-at=2026-03-18T19:05:00Z "
                            "detected-at=2026-03-18T20:00:00Z -->"
                        ),
                        "created_at": "2026-03-18T20:00:00Z",
                        "database_id": 300,
                        "node_id": "IC_valid",
                        "author": "solune-bot",
                    },
                ],
            }
        )

        result = await _check_copilot_review_done(
            access_token="token", owner="owner", repo="repo", parent_issue_number=50
        )

        assert result is True
        assert _copilot_review_requested_at[50] == datetime(2026, 3, 18, 19, 5, tzinfo=UTC)
        mock_service.get_pull_request.assert_not_called()


# ── Fix: _advance_pipeline uses pipeline.status for agent lookup ─────────


class TestAdvancePipelineUsePipelineStatus:
    """Tests that _advance_pipeline uses the pipeline's own status (not
    the board-level from_status) when assigning the next agent.

    Regression test for the bug where GitHub project automation moved an
    issue to 'In Review' while 'In Progress' agents were still running,
    causing judge/linter agents to be skipped because the agent lookup
    resolved agents for the wrong status.
    """

    @pytest.fixture(autouse=True)
    def clear_states(self):
        from src.services.workflow_orchestrator import _pipeline_states

        _pipeline_states.clear()
        yield
        _pipeline_states.clear()

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling._update_issue_tracking", new_callable=AsyncMock)
    @patch("src.services.copilot_polling.github_projects_service")
    @patch("src.services.copilot_polling.connection_manager")
    @patch("src.services.copilot_polling.get_issue_main_branch")
    @patch("src.services.copilot_polling._merge_child_pr_if_applicable")
    @patch("src.services.copilot_polling.get_workflow_orchestrator")
    @patch("src.services.copilot_polling.get_workflow_config", new_callable=AsyncMock)
    @patch("src.services.copilot_polling.set_pipeline_state")
    async def test_uses_pipeline_status_not_from_status_for_agent_lookup(
        self,
        mock_set_state,
        mock_config,
        mock_get_orchestrator,
        mock_merge,
        mock_get_branch,
        mock_ws,
        mock_service,
        mock_update_tracking,
    ):
        """When the board status differs from the pipeline status (e.g. the
        board jumped to 'In Review' but the pipeline is still 'In Progress'),
        _advance_pipeline must pass the PIPELINE status to
        assign_agent_for_status so the correct agents are resolved.

        Without this fix, passing the board status ('In Review') would cause
        assign_agent_for_status to look up 'In Review' agents (['human']),
        and agent_index=2 would be out of range — silently skipping
        judge and linter.
        """
        # Pipeline is for "In Progress" with 4 agents, copilot-review just completed
        pipeline = PipelineState(
            issue_number=1538,
            project_id="PVT_123",
            status="In Progress",
            agents=["speckit.implement", "copilot-review", "judge", "linter"],
            current_agent_index=1,  # copilot-review is the current agent
            completed_agents=["speckit.implement"],
        )

        mock_get_branch.return_value = None
        mock_merge.return_value = None
        mock_ws.broadcast_to_project = AsyncMock()
        mock_orchestrator = MagicMock()
        mock_orchestrator.assign_agent_for_status = AsyncMock(return_value=True)
        mock_get_orchestrator.return_value = mock_orchestrator
        mock_config.return_value = MagicMock()
        mock_update_tracking.return_value = True

        result = await _advance_pipeline(
            access_token="token",
            project_id="PVT_123",
            item_id="PVTI_123",
            owner="owner",
            repo="repo",
            issue_number=1538,
            issue_node_id="I_1538",
            pipeline=pipeline,
            from_status="In Review",  # Board status is ahead of pipeline!
            to_status="Done",
            task_title="Add Pink Color",
        )

        assert result["status"] == "success"
        assert result["agent_name"] == "judge"
        assert result["completed_agent"] == "copilot-review"

        # Crucially: assign_agent_for_status must be called with
        # "In Progress" (pipeline status), NOT "In Review" (board status).
        call_args = mock_orchestrator.assign_agent_for_status.call_args
        assert call_args is not None
        status_arg = call_args[0][1]  # second positional arg = status
        assert status_arg == "In Progress", (
            f"Expected 'In Progress' (pipeline status) but got '{status_arg}' — "
            "this would cause agents to be looked up for the wrong status, "
            "skipping judge and linter"
        )
        agent_index_kwarg = call_args[1].get(
            "agent_index", call_args[0][2] if len(call_args[0]) > 2 else None
        )
        assert agent_index_kwarg == 2  # judge is at index 2


# ── Fix: check_in_review_issues handles pipeline status mismatch ─────────


class TestCheckInReviewPipelineStatusMismatch:
    """Tests that check_in_review_issues correctly handles issues whose
    cached pipeline is for a different status (e.g., 'In Progress').

    When GitHub project automation moves an issue to 'In Review' before
    the 'In Progress' pipeline completes, check_in_review_issues must
    detect the mismatch and use the pipeline's own status/transition
    targets instead of hardcoding 'In Review' → 'Done'.
    """

    @pytest.fixture(autouse=True)
    def clear_states(self):
        from src.services.copilot_polling.state import _polling_state
        from src.services.workflow_orchestrator import _pipeline_states

        _pipeline_states.clear()
        old_err = _polling_state.errors_count
        yield
        _pipeline_states.clear()
        _polling_state.errors_count = old_err

    @pytest.mark.asyncio
    @patch(
        "src.services.copilot_polling.pipeline._process_pipeline_completion",
        new_callable=AsyncMock,
    )
    @patch("src.services.copilot_polling.pipeline._cp.get_workflow_config", new_callable=AsyncMock)
    @patch("src.services.copilot_polling.pipeline._cp.github_projects_service")
    async def test_uses_pipeline_status_for_mismatched_cached_pipeline(
        self,
        mock_service,
        mock_config,
        mock_process,
    ):
        """When the cached pipeline is for 'In Progress' but the issue is
        on the 'In Review' column, check_in_review_issues should pass
        'In Progress' as from_status (not 'In Review') to
        _process_pipeline_completion.
        """
        from src.models.agent import AgentAssignment
        from src.services.copilot_polling import set_pipeline_state

        # Set up a cached pipeline for "In Progress"
        pipeline = PipelineState(
            issue_number=1538,
            project_id="PVT_123",
            status="In Progress",
            agents=["speckit.implement", "copilot-review", "judge", "linter"],
            current_agent_index=2,  # judge is next
            completed_agents=["speckit.implement", "copilot-review"],
        )
        set_pipeline_state(1538, pipeline)

        # Mock config
        config = MagicMock()
        config.status_in_review = "In Review"
        config.status_in_progress = "In Progress"
        config.agent_mappings = {
            "In Review": [AgentAssignment(slug="human")],
            "In Progress": [
                AgentAssignment(slug="speckit.implement"),
                AgentAssignment(slug="copilot-review"),
                AgentAssignment(slug="judge"),
                AgentAssignment(slug="linter"),
            ],
        }
        mock_config.return_value = config

        # Create a mock task in "In Review" status
        task = MagicMock()
        task.github_item_id = "PVTI_1538"
        task.github_content_id = "I_1538"
        task.issue_number = 1538
        task.repository_owner = "owner"
        task.repository_name = "repo"
        task.title = "Add Pink Color"
        task.status = "In Review"

        mock_service.get_project_items = AsyncMock(return_value=[task])
        mock_process.return_value = {"status": "success"}

        await check_in_review_issues(
            access_token="token",
            project_id="PVT_123",
            owner="owner",
            repo="repo",
        )

        # _process_pipeline_completion should have been called with
        # from_status="In Progress" (pipeline's status) and
        # to_status="In Review" (next status after In Progress),
        # NOT from_status="In Review" and to_status="Done".
        mock_process.assert_called_once()
        call_kwargs = mock_process.call_args[1]
        assert call_kwargs["from_status"] == "In Progress", (
            f"Expected from_status='In Progress' but got '{call_kwargs['from_status']}'"
        )
        assert call_kwargs["to_status"] == "In Review", (
            f"Expected to_status='In Review' but got '{call_kwargs['to_status']}'"
        )


class TestCopilotReviewGroupedPipelineRace:
    """Regression coverage for stale auto-triggered review completion in grouped pipelines."""

    @pytest.fixture(autouse=True)
    def clear_states(self):
        from src.services.workflow_orchestrator import _pipeline_states

        _pipeline_states.clear()
        _copilot_review_first_detected.clear()
        _copilot_review_requested_at.clear()
        yield
        _pipeline_states.clear()
        _copilot_review_first_detected.clear()
        _copilot_review_requested_at.clear()

    @pytest.mark.asyncio
    @patch(
        "src.services.copilot_polling.helpers._discover_main_pr_for_review",
        new_callable=AsyncMock,
    )
    @patch("src.services.copilot_polling.pipeline._cp.get_workflow_config", new_callable=AsyncMock)
    @patch("src.services.copilot_polling.pipeline._cp.github_projects_service")
    async def test_stale_auto_triggered_review_does_not_advance_grouped_pipeline(
        self,
        mock_service,
        mock_config,
        mock_discover,
    ):
        """A stale auto-triggered review must not complete a later copilot-review group."""
        from src.models.agent import AgentAssignment
        from src.services.copilot_polling import set_pipeline_state
        from src.services.workflow_orchestrator.models import PipelineGroupInfo

        pipeline = PipelineState(
            issue_number=4642,
            project_id="PVT_123",
            status="In Progress",
            agents=["speckit.implement", "copilot-review", "judge"],
            current_agent_index=1,
            completed_agents=["speckit.implement"],
            groups=[
                PipelineGroupInfo(
                    group_id="g1",
                    execution_mode="sequential",
                    agents=["speckit.implement"],
                ),
                PipelineGroupInfo(
                    group_id="g2",
                    execution_mode="sequential",
                    agents=["copilot-review"],
                ),
                PipelineGroupInfo(
                    group_id="g3",
                    execution_mode="sequential",
                    agents=["judge"],
                ),
            ],
            current_group_index=1,
            current_agent_index_in_group=0,
        )
        set_pipeline_state(4642, pipeline)

        config = MagicMock(
            status_backlog="Backlog",
            status_ready="Ready",
            status_in_progress="In Progress",
            status_in_review="In Review",
        )
        config.agent_mappings = {
            "In Review": [AgentAssignment(slug="human")],
            "In Progress": [
                AgentAssignment(slug="speckit.implement"),
                AgentAssignment(slug="copilot-review"),
                AgentAssignment(slug="judge"),
            ],
        }
        mock_config.return_value = config

        task = MagicMock()
        task.github_item_id = "PVTI_4642"
        task.github_content_id = "I_4642"
        task.issue_number = 4642
        task.repository_owner = "owner"
        task.repository_name = "repo"
        task.title = "Regression issue"
        task.status = "In Review"
        task.labels = []

        mock_service.get_issue_with_comments = AsyncMock(
            return_value={
                "title": "Regression issue",
                "body": (
                    "Body\n\n<!-- solune:copilot-review-requested-at=2026-03-18T19:05:00Z -->"
                ),
                "user": {"login": "owner"},
                "comments": [
                    {
                        "body": "speckit.implement: Done!",
                        "created_at": "2026-03-18T19:00:00Z",
                        "database_id": 200,
                        "node_id": "IC_impl",
                        "author": "copilot-bot",
                    },
                    {
                        "body": (
                            "copilot-review: Done!\n"
                            "<!-- solune:copilot-review-requested-at=2026-03-18T18:00:00Z "
                            "detected-at=2026-03-18T18:30:00Z -->"
                        ),
                        "created_at": "2026-03-18T18:30:00Z",
                        "database_id": 100,
                        "node_id": "IC_stale",
                        "author": "solune-bot",
                    },
                ],
            }
        )
        mock_service.get_pull_request = AsyncMock(
            return_value={"id": "PR_node_500", "is_draft": False}
        )
        mock_service.delete_issue_comment = AsyncMock(return_value=True)
        mock_service.has_copilot_reviewed_pr = AsyncMock(return_value=False)
        mock_service.request_copilot_review = AsyncMock(return_value=True)
        mock_discover.return_value = {
            "pr_number": 500,
            "pr_id": "PR_node_500",
            "is_draft": False,
            "head_ref": "copilot/issue-4642",
        }

        results = await check_in_review_issues(
            access_token="token",
            project_id="PVT_123",
            owner="owner",
            repo="repo",
            tasks=[task],
        )

        assert len(results) == 1
        assert results[0]["action"] == "agent_assigned_after_reconstruction"
        assert results[0]["agent_name"] == "copilot-review"
        assert pipeline.current_agent_index == 1
        assert pipeline.current_group_index == 1
        assert pipeline.completed_agents == ["speckit.implement"]
        mock_service.delete_issue_comment.assert_awaited_once_with(
            access_token="token",
            owner="owner",
            repo="repo",
            comment_database_id=100,
            issue_number=4642,
        )
        mock_service.has_copilot_reviewed_pr.assert_awaited_once()


# ── Fix: _get_or_reconstruct_pipeline uses tracking table agents ─────────


class TestGetOrReconstructPipelineTrackingTable:
    """Tests that _get_or_reconstruct_pipeline checks the tracking table
    in the issue body when reconstructing, and uses agents from a previous
    status if they are still incomplete.

    This handles the server-restart scenario where in-memory pipeline state
    is lost, and the reconstruction function would otherwise create a
    pipeline with only the current board status's agents, skipping
    incomplete agents from a prior status.
    """

    @pytest.fixture(autouse=True)
    def clear_states(self):
        from src.services.workflow_orchestrator import _pipeline_states

        _pipeline_states.clear()
        yield
        _pipeline_states.clear()

    @pytest.mark.asyncio
    @patch(
        "src.services.copilot_polling.pipeline._reconstruct_pipeline_state", new_callable=AsyncMock
    )
    @patch("src.services.copilot_polling.pipeline._cp.parse_tracking_from_body")
    @patch("src.services.copilot_polling.pipeline._cp.github_projects_service")
    async def test_reconstructs_for_earlier_status_when_tracking_shows_pending(
        self,
        mock_service,
        mock_parse_tracking,
        mock_reconstruct,
    ):
        """When the tracking table shows pending agents in 'In Progress' but
        the board shows 'In Review', reconstruction should use the
        'In Progress' agents, not the 'In Review' agents.
        """
        from src.services.agent_tracking import AgentStep
        from src.services.copilot_polling import _get_or_reconstruct_pipeline

        # Simulate tracking table: judge and linter are still pending
        mock_parse_tracking.return_value = [
            AgentStep(index=1, status="Backlog", agent_name="speckit.specify", state="✅ Done"),
            AgentStep(index=2, status="Ready", agent_name="speckit.plan", state="✅ Done"),
            AgentStep(index=3, status="Ready", agent_name="speckit.tasks", state="✅ Done"),
            AgentStep(
                index=4, status="In Progress", agent_name="speckit.implement", state="✅ Done"
            ),
            AgentStep(index=5, status="In Progress", agent_name="copilot-review", state="✅ Done"),
            AgentStep(index=6, status="In Progress", agent_name="judge", state="⏳ Pending"),
            AgentStep(index=7, status="In Progress", agent_name="linter", state="⏳ Pending"),
            AgentStep(index=8, status="In Review", agent_name="human", state="⏳ Pending"),
        ]

        mock_service.get_issue_with_comments = AsyncMock(
            return_value={"body": "...tracking table...", "comments": []}
        )

        # Reconstruction should return a pipeline for "In Progress"
        mock_reconstruct.return_value = PipelineState(
            issue_number=1538,
            project_id="PVT_123",
            status="In Progress",
            agents=["speckit.implement", "copilot-review", "judge", "linter"],
            current_agent_index=2,
            completed_agents=["speckit.implement", "copilot-review"],
        )

        result = await _get_or_reconstruct_pipeline(
            access_token="token",
            owner="owner",
            repo="repo",
            issue_number=1538,
            project_id="PVT_123",
            status="In Review",  # Board says "In Review"
            agents=["human"],  # "In Review" agents from config
        )

        # _reconstruct_pipeline_state should have been called with
        # "In Progress" agents (from tracking table), NOT "In Review" agents.
        mock_reconstruct.assert_called_once()
        call_kwargs = mock_reconstruct.call_args[1]
        assert call_kwargs["status"] == "In Progress"
        assert call_kwargs["agents"] == [
            "speckit.implement",
            "copilot-review",
            "judge",
            "linter",
        ]
        assert result.status == "In Progress"


# ---------------------------------------------------------------------------
# Regression tests for copilot-review false-positive child-PR detection
# (GitHub Issue #1584)
# ---------------------------------------------------------------------------


class TestCopilotReviewChildPrFalsePositive:
    """Regression tests for the bug where agent_output.py detected an
    inadvertent Copilot coding-agent PR on the copilot-review sub-issue
    as a legitimate completion signal, posting a premature "copilot-review:
    Done!" marker before the actual Copilot code review was submitted.

    See: https://github.com/Boykai/github-workflows/issues/1584
    """

    @pytest.fixture(autouse=True)
    def clear_caches(self):
        _posted_agent_outputs.clear()
        _issue_main_branches.clear()
        _claimed_child_prs.clear()
        yield
        _posted_agent_outputs.clear()
        _issue_main_branches.clear()
        _claimed_child_prs.clear()

    @pytest.fixture
    def mock_task_in_progress(self):
        task = MagicMock()
        task.github_item_id = "PVTI_1584"
        task.github_content_id = "I_1584"
        task.issue_number = 1584
        task.repository_owner = "Boykai"
        task.repository_name = "github-workflows"
        task.title = "Add Bronze Background Theme to App"
        task.status = "In Progress"
        return task

    # -- Test 1: agent_output.py skips copilot-review entirely in Step 0 --

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    @patch("src.services.copilot_polling.get_workflow_config", new_callable=AsyncMock)
    @patch("src.services.copilot_polling.get_pipeline_state")
    async def test_agent_output_skips_copilot_review_step0(
        self, mock_pipeline, mock_config, mock_service, mock_task_in_progress
    ):
        """post_agent_outputs_from_pr must NOT invoke child-PR detection
        when the current agent is copilot-review.  Without the guard,
        a Copilot coding-agent PR on the sub-issue would trigger a false
        'copilot-review: Done!' marker.
        """
        mock_config.return_value = MagicMock()

        pipeline = PipelineState(
            issue_number=1584,
            project_id="PVT_1",
            status="In Progress",
            agents=["speckit.implement", "copilot-review", "judge", "linter"],
            current_agent_index=1,  # copilot-review is the active agent
            completed_agents=["speckit.implement"],
        )
        pipeline.agent_sub_issues = {
            "copilot-review": {"number": 1589, "node_id": "I_1589"},
        }
        mock_pipeline.return_value = pipeline

        # _check_agent_done_on_sub_or_parent returns False (no Done! marker yet)
        mock_service.check_agent_completion_comment = AsyncMock(return_value=False)
        mock_service.get_issue_with_comments = AsyncMock(return_value={"body": "", "comments": []})

        # _find_completed_child_pr would find PR #1599 if called — but
        # the guard should prevent it from running at all.
        mock_service.get_linked_pull_requests = AsyncMock(
            return_value=[
                {"number": 1593, "state": "OPEN", "author": "copilot[bot]"},
                {"number": 1599, "state": "OPEN", "author": "copilot[bot]"},
            ]
        )
        mock_service.get_pull_request = AsyncMock(
            return_value={
                "id": "PR_1599",
                "base_ref": "copilot/add-bronze-background-theme",
                "head_ref": "copilot/copilot-review-bronze",
                "is_draft": False,
                "last_commit": {"sha": "dead1234"},
            }
        )
        mock_service.get_pr_timeline_events = AsyncMock(
            return_value=[{"event": "copilot_work_finished"}]
        )
        mock_service.check_copilot_finished_events = MagicMock(return_value=True)

        # Register main branch so the child-PR path would normally trigger
        _issue_main_branches[1584] = {
            "branch": "copilot/add-bronze-background-theme",
            "pr_number": 1593,
        }

        await post_agent_outputs_from_pr(
            access_token="token",
            project_id="PVT_1",
            owner="Boykai",
            repo="github-workflows",
            tasks=[mock_task_in_progress],
        )

        # No "Done!" marker should have been posted
        for call in mock_service.create_issue_comment.call_args_list:
            body = call.kwargs.get("body") or call[1].get("body", "")
            assert "copilot-review: Done!" not in body, (
                "copilot-review: Done! was falsely posted via child-PR detection"
            )

    # -- Test 2: _find_completed_child_pr returns None for copilot-review --

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    async def test_find_completed_child_pr_returns_none_for_copilot_review(self, mock_service):
        """_find_completed_child_pr must short-circuit and return None
        when agent_name is 'copilot-review', regardless of linked PRs.
        """
        # Mock a linked PR that would match if the agent were a coding agent
        mock_service.get_linked_pull_requests = AsyncMock(
            return_value=[
                {"number": 1599, "state": "OPEN", "author": "copilot[bot]"},
            ]
        )
        mock_service.get_pull_request = AsyncMock(
            return_value={
                "id": "PR_1599",
                "base_ref": "copilot/add-bronze-background-theme",
                "head_ref": "copilot/copilot-review-bronze",
                "is_draft": False,
                "last_commit": {"sha": "dead1234"},
            }
        )
        mock_service.get_pr_timeline_events = AsyncMock(
            return_value=[{"event": "copilot_work_finished"}]
        )
        mock_service.check_copilot_finished_events = MagicMock(return_value=True)

        result = await _find_completed_child_pr(
            access_token="token",
            owner="Boykai",
            repo="github-workflows",
            issue_number=1584,
            main_branch="copilot/add-bronze-background-theme",
            main_pr_number=1593,
            agent_name="copilot-review",
        )

        assert result is None
        # Should not even attempt to fetch linked PRs
        mock_service.get_linked_pull_requests.assert_not_called()

    # -- Test 3: regular agents still detected normally --

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    async def test_find_completed_child_pr_still_works_for_coding_agents(self, mock_service):
        """_find_completed_child_pr must still detect child PRs for regular
        coding agents (e.g. speckit.implement, judge) — only copilot-review
        is excluded.
        """
        mock_service.get_linked_pull_requests = AsyncMock(
            return_value=[
                {"number": 1593, "state": "OPEN", "author": "copilot[bot]"},
                {"number": 1600, "state": "OPEN", "author": "copilot[bot]"},
            ]
        )
        mock_service.get_pull_request = AsyncMock(
            return_value={
                "id": "PR_1600",
                "base_ref": "copilot/add-bronze-background-theme",
                "head_ref": "copilot/judge-bronze",
                "is_draft": True,
                "last_commit": {"sha": "beef5678"},
            }
        )
        mock_service.get_pr_timeline_events = AsyncMock(
            return_value=[{"event": "copilot_work_finished"}]
        )
        mock_service.check_copilot_finished_events = MagicMock(return_value=True)

        result = await _find_completed_child_pr(
            access_token="token",
            owner="Boykai",
            repo="github-workflows",
            issue_number=1584,
            main_branch="copilot/add-bronze-background-theme",
            main_pr_number=1593,
            agent_name="judge",
        )

        assert result is not None
        assert result["number"] == 1600


# ────────────────────────────────────────────────────────────────────
# _check_main_pr_completion — sub-issue Copilot check (issue #1624)
# ────────────────────────────────────────────────────────────────────


class TestCheckMainPrSubIssueCheck:
    """
    Regression tests for issue #1624: _check_main_pr_completion must check
    Copilot assignment on the SUB-ISSUE (where Copilot is actually assigned),
    not the parent issue.  Without sub_issue_number, the function would
    always see 'Copilot not assigned' on the parent and fire prematurely.
    """

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    async def test_sub_issue_copilot_still_assigned_blocks_completion(self, mock_service):
        """Copilot still assigned on sub-issue → False even with new SHA."""
        mock_service.get_pull_request = AsyncMock(
            return_value={
                "is_draft": True,
                "state": "OPEN",
                "last_commit": {"sha": "new_sha_999"},
            }
        )
        mock_service.get_pr_timeline_events = AsyncMock(return_value=[])
        mock_service.check_copilot_finished_events = Mock(return_value=False)
        # Copilot is still assigned on the sub-issue
        mock_service.is_copilot_assigned_to_issue = AsyncMock(return_value=True)

        result = await _check_main_pr_completion(
            access_token="tok",
            owner="o",
            repo="r",
            main_pr_number=100,
            issue_number=1624,
            agent_name="speckit.specify",
            pipeline_started_at=utcnow(),
            agent_assigned_sha="old_sha_aaa",
            sub_issue_number=1625,
        )
        assert result is False
        # ALL Copilot assignment checks must target the sub-issue, not the parent
        for call_args in mock_service.is_copilot_assigned_to_issue.call_args_list:
            assert call_args.kwargs["issue_number"] == 1625

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    async def test_sub_issue_copilot_unassigned_allows_completion(self, mock_service):
        """Copilot unassigned on sub-issue + new SHA → True."""
        mock_service.get_pull_request = AsyncMock(
            return_value={
                "is_draft": True,
                "state": "OPEN",
                "last_commit": {"sha": "new_sha_bbb"},
            }
        )
        mock_service.get_pr_timeline_events = AsyncMock(return_value=[])
        mock_service.check_copilot_finished_events = Mock(return_value=False)
        mock_service.is_copilot_assigned_to_issue = AsyncMock(return_value=False)

        result = await _check_main_pr_completion(
            access_token="tok",
            owner="o",
            repo="r",
            main_pr_number=100,
            issue_number=1624,
            agent_name="speckit.specify",
            pipeline_started_at=utcnow(),
            agent_assigned_sha="old_sha_ccc",
            sub_issue_number=1625,
        )
        assert result is True
        # Must check the sub-issue, not the parent
        for call_args in mock_service.is_copilot_assigned_to_issue.call_args_list:
            assert call_args.kwargs["issue_number"] == 1625

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    async def test_no_sub_issue_falls_back_to_parent(self, mock_service):
        """Without sub_issue_number, check falls back to parent issue."""
        mock_service.get_pull_request = AsyncMock(
            return_value={
                "is_draft": True,
                "state": "OPEN",
                "last_commit": {"sha": "new_sha_ddd"},
            }
        )
        mock_service.get_pr_timeline_events = AsyncMock(return_value=[])
        mock_service.check_copilot_finished_events = Mock(return_value=False)
        mock_service.is_copilot_assigned_to_issue = AsyncMock(return_value=False)

        result = await _check_main_pr_completion(
            access_token="tok",
            owner="o",
            repo="r",
            main_pr_number=100,
            issue_number=1624,
            agent_name="speckit.specify",
            pipeline_started_at=utcnow(),
            agent_assigned_sha="old_sha_eee",
            # No sub_issue_number passed
        )
        assert result is True
        # Falls back to parent issue
        for call_args in mock_service.is_copilot_assigned_to_issue.call_args_list:
            assert call_args.kwargs["issue_number"] == 1624

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    async def test_no_sha_sub_issue_copilot_still_working(self, mock_service):
        """No assigned SHA + Copilot still on sub-issue → no false completion."""
        mock_service.get_pull_request = AsyncMock(
            return_value={
                "is_draft": True,
                "state": "OPEN",
                "last_commit": {
                    "sha": "abc123",
                    "committed_date": "2026-03-05T04:02:02Z",
                },
            }
        )
        mock_service.get_pr_timeline_events = AsyncMock(return_value=[])
        mock_service.check_copilot_finished_events = Mock(return_value=False)
        # Copilot still working on the sub-issue
        mock_service.is_copilot_assigned_to_issue = AsyncMock(return_value=True)

        result = await _check_main_pr_completion(
            access_token="tok",
            owner="o",
            repo="r",
            main_pr_number=100,
            issue_number=1624,
            agent_name="speckit.specify",
            pipeline_started_at=datetime(2026, 3, 5, 4, 0, 0),
            agent_assigned_sha="",  # No SHA — simulates post-restart
            sub_issue_number=1625,
        )
        assert result is False
        # Must check sub-issue, not parent
        for call_args in mock_service.is_copilot_assigned_to_issue.call_args_list:
            assert call_args.kwargs["issue_number"] == 1625


# ────────────────────────────────────────────────────────────────────
# Fix: _get_or_reconstruct_pipeline uses tracking table agents for
# the CURRENT status (not just earlier statuses) — issue #1655
# ────────────────────────────────────────────────────────────────────


class TestGetOrReconstructPipelineCurrentStatusOverride:
    """When the tracking table exists and its agent list for the CURRENT
    status differs from the DB config, reconstruction should use the
    tracking table's agents.  This prevents agents like judge/linter
    from being silently skipped when the DB config is modified after
    issue creation.
    """

    @pytest.fixture(autouse=True)
    def clear_states(self):
        from src.services.workflow_orchestrator import _pipeline_states

        _pipeline_states.clear()
        yield
        _pipeline_states.clear()

    @pytest.mark.asyncio
    @patch(
        "src.services.copilot_polling.pipeline._reconstruct_pipeline_state", new_callable=AsyncMock
    )
    @patch("src.services.copilot_polling.pipeline._cp.parse_tracking_from_body")
    @patch("src.services.copilot_polling.pipeline._cp.github_projects_service")
    async def test_overrides_agents_for_current_status_from_tracking_table(
        self,
        mock_service,
        mock_parse_tracking,
        mock_reconstruct,
    ):
        """When the DB config only has ['speckit.implement'] for In Progress
        but the tracking table shows ['speckit.implement', 'judge', 'linter'],
        reconstruction must use the tracking table's list.
        """
        from src.services.agent_tracking import AgentStep
        from src.services.copilot_polling import _get_or_reconstruct_pipeline

        mock_parse_tracking.return_value = [
            AgentStep(index=1, status="Backlog", agent_name="speckit.specify", state="✅ Done"),
            AgentStep(index=2, status="Ready", agent_name="speckit.plan", state="✅ Done"),
            AgentStep(index=3, status="Ready", agent_name="speckit.tasks", state="✅ Done"),
            AgentStep(
                index=4, status="In Progress", agent_name="speckit.implement", state="✅ Done"
            ),
            AgentStep(index=5, status="In Progress", agent_name="judge", state="⏳ Pending"),
            AgentStep(index=6, status="In Progress", agent_name="linter", state="⏳ Pending"),
            AgentStep(index=7, status="In Review", agent_name="copilot-review", state="⏳ Pending"),
            AgentStep(index=8, status="In Review", agent_name="human", state="⏳ Pending"),
        ]

        mock_service.get_issue_with_comments = AsyncMock(
            return_value={"body": "...tracking table...", "comments": []}
        )

        mock_reconstruct.return_value = PipelineState(
            issue_number=1655,
            project_id="PVT_123",
            status="In Progress",
            agents=["speckit.implement", "judge", "linter"],
            current_agent_index=1,
            completed_agents=["speckit.implement"],
        )

        # DB config says only ["speckit.implement"] for In Progress
        await _get_or_reconstruct_pipeline(
            access_token="token",
            owner="owner",
            repo="repo",
            issue_number=1655,
            project_id="PVT_123",
            status="In Progress",
            agents=["speckit.implement"],  # shortened DB config
        )

        # _reconstruct_pipeline_state should have been called with
        # the tracking table's full agent list for "In Progress"
        mock_reconstruct.assert_called_once()
        call_kwargs = mock_reconstruct.call_args[1]
        assert call_kwargs["status"] == "In Progress"
        assert call_kwargs["agents"] == ["speckit.implement", "judge", "linter"]

    @pytest.mark.asyncio
    @patch(
        "src.services.copilot_polling.pipeline._reconstruct_pipeline_state", new_callable=AsyncMock
    )
    @patch("src.services.copilot_polling.pipeline._cp.parse_tracking_from_body")
    @patch("src.services.copilot_polling.pipeline._cp.github_projects_service")
    async def test_no_override_when_tracking_matches_config(
        self,
        mock_service,
        mock_parse_tracking,
        mock_reconstruct,
    ):
        """When the tracking table agents match the DB config, no override occurs."""
        from src.services.agent_tracking import AgentStep
        from src.services.copilot_polling import _get_or_reconstruct_pipeline

        mock_parse_tracking.return_value = [
            AgentStep(
                index=1, status="In Progress", agent_name="speckit.implement", state="✅ Done"
            ),
        ]

        mock_service.get_issue_with_comments = AsyncMock(
            return_value={"body": "...tracking...", "comments": []}
        )

        mock_reconstruct.return_value = PipelineState(
            issue_number=1655,
            project_id="PVT_123",
            status="In Progress",
            agents=["speckit.implement"],
            current_agent_index=1,
            completed_agents=["speckit.implement"],
        )

        await _get_or_reconstruct_pipeline(
            access_token="token",
            owner="owner",
            repo="repo",
            issue_number=1655,
            project_id="PVT_123",
            status="In Progress",
            agents=["speckit.implement"],
        )

        # Agents should be passed through unchanged
        call_kwargs = mock_reconstruct.call_args[1]
        assert call_kwargs["agents"] == ["speckit.implement"]

    @pytest.mark.asyncio
    @patch(
        "src.services.copilot_polling.pipeline._reconstruct_pipeline_state", new_callable=AsyncMock
    )
    @patch("src.services.copilot_polling.pipeline._cp.github_projects_service")
    async def test_no_override_when_no_tracking_table(
        self,
        mock_service,
        mock_reconstruct,
    ):
        """When there is no tracking table in the issue body, reconstruction
        uses the caller-provided agents from DB config (no crash, no override).
        """
        from src.services.copilot_polling import _get_or_reconstruct_pipeline

        mock_service.get_issue_with_comments = AsyncMock(
            return_value={"body": "No tracking table here.", "comments": []}
        )

        mock_reconstruct.return_value = PipelineState(
            issue_number=1655,
            project_id="PVT_123",
            status="In Progress",
            agents=["speckit.implement"],
            current_agent_index=1,
            completed_agents=["speckit.implement"],
        )

        await _get_or_reconstruct_pipeline(
            access_token="token",
            owner="owner",
            repo="repo",
            issue_number=1655,
            project_id="PVT_123",
            status="In Progress",
            agents=["speckit.implement"],
        )

        # Should use the caller's agents since no tracking table exists
        call_kwargs = mock_reconstruct.call_args[1]
        assert call_kwargs["agents"] == ["speckit.implement"]


# ────────────────────────────────────────────────────────────────────
# Fix: post_agent_outputs_from_pr skips 'human' agent in Step 0
# (issue #1655 — human agent auto-completed by stale merged child PR)
# ────────────────────────────────────────────────────────────────────


class TestAgentOutputSkipsHumanStep0:
    """Regression tests for the bug where post_agent_outputs_from_pr found
    a stale merged child PR from a previous agent and misattributed it to
    the 'human' agent, auto-posting 'human: Done!' before a human actually
    reviewed and closed the sub-issue.

    The human agent is not a coding agent — it never creates child PRs.
    Step 0 must skip it entirely, just like copilot-review.
    """

    @pytest.fixture(autouse=True)
    def clear_caches(self):
        _posted_agent_outputs.clear()
        _issue_main_branches.clear()
        _claimed_child_prs.clear()
        yield
        _posted_agent_outputs.clear()
        _issue_main_branches.clear()
        _claimed_child_prs.clear()

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    @patch("src.services.copilot_polling.get_workflow_config", new_callable=AsyncMock)
    @patch("src.services.copilot_polling.get_pipeline_state")
    async def test_agent_output_skips_human_step0(self, mock_pipeline, mock_config, mock_service):
        """post_agent_outputs_from_pr must NOT invoke child-PR detection
        when the current agent is 'human'.  Without this guard, a stale
        merged child PR would trigger a false 'human: Done!' marker.
        """
        mock_config.return_value = MagicMock()

        pipeline = PipelineState(
            issue_number=1655,
            project_id="PVT_1",
            status="In Review",
            agents=["copilot-review", "human"],
            current_agent_index=1,  # human is the active agent
            completed_agents=["copilot-review"],
        )
        pipeline.agent_sub_issues = {
            "human": {"number": 1663, "node_id": "I_1663", "assignee": "Boykai"},
        }
        mock_pipeline.return_value = pipeline

        # _check_agent_done_on_sub_or_parent returns False (sub-issue not closed)
        mock_service.check_issue_closed = AsyncMock(return_value=False)
        mock_service.get_issue_with_comments = AsyncMock(
            return_value={"body": "", "comments": [], "user": {"login": "Boykai"}}
        )

        # A merged child PR exists (stale PR from a previous agent)
        _issue_main_branches[1655] = {
            "branch": "copilot/audit-refactor-fastapi-react",
            "pr_number": 1664,
        }
        mock_service.get_linked_pull_requests = AsyncMock(
            return_value=[
                {"number": 1664, "state": "OPEN"},
                {"number": 1686, "state": "MERGED"},
            ]
        )
        mock_service.get_pull_request = AsyncMock(
            return_value={
                "id": "PR_1686",
                "base_ref": "copilot/audit-refactor-fastapi-react",
                "head_ref": "copilot/human-audit",
                "is_draft": False,
            }
        )

        task = MagicMock()
        task.github_item_id = "PVTI_1655"
        task.github_content_id = "I_1655"
        task.issue_number = 1655
        task.repository_owner = "Boykai"
        task.repository_name = "github-workflows"
        task.title = "Audit & Refactor"
        task.status = "In Review"

        await post_agent_outputs_from_pr(
            access_token="token",
            project_id="PVT_1",
            owner="Boykai",
            repo="github-workflows",
            tasks=[task],
        )

        # No "human: Done!" marker should have been posted
        for call in mock_service.create_issue_comment.call_args_list:
            body = call.kwargs.get("body") or call[1].get("body", "")
            assert "human: Done!" not in body, (
                "human: Done! was falsely posted via child-PR detection"
            )


# ────────────────────────────────────────────────────────────────────
# Fix: _check_human_agent_done accepts "human: Done!" marker
# (issue #1655 — standard {agent}: Done! format for human step)
# ────────────────────────────────────────────────────────────────────


class TestCheckHumanAgentDoneMarkerFormat:
    """Tests that the human agent completion check accepts both
    'Done!' and 'human: Done!' as valid completion signals.
    """

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    async def test_human_done_marker_format_accepted(self, mock_service):
        """'human: Done!' from the assignee should complete the human step."""
        pipeline = MagicMock()
        pipeline.agent_sub_issues = {"human": {"number": 99, "assignee": "Boykai"}}

        mock_service.check_issue_closed = AsyncMock(return_value=False)
        mock_service.get_issue_with_comments = AsyncMock(
            return_value={
                "comments": [
                    {"author": "Boykai", "body": "human: Done!"},
                ],
                "user": {"login": "Boykai"},
            }
        )

        result = await _check_agent_done_on_sub_or_parent(
            access_token="token",
            owner="owner",
            repo="repo",
            parent_issue_number=42,
            agent_name="human",
            pipeline=pipeline,
        )

        assert result is True

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    async def test_human_done_marker_from_non_assignee_rejected(self, mock_service):
        """'human: Done!' from a non-assignee must NOT complete the step."""
        pipeline = MagicMock()
        pipeline.agent_sub_issues = {"human": {"number": 99, "assignee": "Boykai"}}

        mock_service.check_issue_closed = AsyncMock(return_value=False)
        mock_service.get_issue_with_comments = AsyncMock(
            return_value={
                "comments": [
                    {"author": "intruder", "body": "human: Done!"},
                ],
                "user": {"login": "Boykai"},
            }
        )

        result = await _check_agent_done_on_sub_or_parent(
            access_token="token",
            owner="owner",
            repo="repo",
            parent_issue_number=42,
            agent_name="human",
            pipeline=pipeline,
        )

        assert result is False

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    async def test_done_excl_still_accepted(self, mock_service):
        """The original 'Done!' format should still work (backward compat)."""
        pipeline = MagicMock()
        pipeline.agent_sub_issues = {"human": {"number": 99, "assignee": "Boykai"}}

        mock_service.check_issue_closed = AsyncMock(return_value=False)
        mock_service.get_issue_with_comments = AsyncMock(
            return_value={
                "comments": [
                    {"author": "Boykai", "body": "Done!"},
                ],
                "user": {"login": "Boykai"},
            }
        )

        result = await _check_agent_done_on_sub_or_parent(
            access_token="token",
            owner="owner",
            repo="repo",
            parent_issue_number=42,
            agent_name="human",
            pipeline=pipeline,
        )

        assert result is True


# ── Fix: _get_or_reconstruct_pipeline advances when first incomplete
#    agent is in a LATER status than the board's current status ───────────


class TestGetOrReconstructPipelineLaterStatus:
    """Tests that _get_or_reconstruct_pipeline correctly handles the case
    where ALL agents for the board's current status are done, and the first
    incomplete agent is in a LATER status.

    Bug scenario: Issue #2912 has Backlog agents [speckit.specify, designer]
    all Done, but the board still shows "Backlog".  The first incomplete
    agent is "judge" at "In Progress".  The old code would reconstruct
    for "In Progress" and the pipeline would never trigger status
    advancement from Backlog → Ready.
    """

    @pytest.fixture(autouse=True)
    def clear_states(self):
        from src.services.workflow_orchestrator import _pipeline_states

        _pipeline_states.clear()
        yield
        _pipeline_states.clear()

    @pytest.mark.asyncio
    @patch(
        "src.services.copilot_polling.pipeline._reconstruct_pipeline_state",
        new_callable=AsyncMock,
    )
    @patch("src.services.copilot_polling.pipeline._cp.parse_tracking_from_body")
    @patch("src.services.copilot_polling.pipeline._cp.github_projects_service")
    async def test_reconstructs_for_requested_status_when_first_incomplete_is_later(
        self,
        mock_service,
        mock_parse_tracking,
        mock_reconstruct,
    ):
        """When the board says 'Backlog' but all Backlog agents are done
        and the first incomplete is at 'In Progress', reconstruction should
        be for 'Backlog' (showing pipeline as complete) — NOT 'In Progress'.
        """
        from src.services.agent_tracking import AgentStep
        from src.services.copilot_polling import _get_or_reconstruct_pipeline

        mock_parse_tracking.return_value = [
            AgentStep(index=1, status="Backlog", agent_name="speckit.specify", state="✅ Done"),
            AgentStep(index=2, status="Backlog", agent_name="designer", state="✅ Done"),
            AgentStep(index=3, status="Ready", agent_name="speckit.plan", state="✅ Done"),
            AgentStep(index=4, status="Ready", agent_name="speckit.tasks", state="✅ Done"),
            AgentStep(
                index=5, status="In Progress", agent_name="speckit.implement", state="✅ Done"
            ),
            AgentStep(index=6, status="In Progress", agent_name="copilot-review", state="✅ Done"),
            AgentStep(index=7, status="In Progress", agent_name="judge", state="🔄 Active"),
            AgentStep(
                index=8, status="In Progress", agent_name="quality-assurance", state="⏳ Pending"
            ),
            AgentStep(index=9, status="In Review", agent_name="human", state="⏳ Pending"),
        ]

        mock_service.get_issue_with_comments = AsyncMock(
            return_value={"body": "...tracking table...", "comments": []}
        )

        # Reconstruction should return a COMPLETE pipeline for "Backlog"
        mock_reconstruct.return_value = PipelineState(
            issue_number=2912,
            project_id="PVT_123",
            status="Backlog",
            agents=["speckit.specify", "designer"],
            current_agent_index=2,
            completed_agents=["speckit.specify", "designer"],
        )

        result = await _get_or_reconstruct_pipeline(
            access_token="token",
            owner="owner",
            repo="repo",
            issue_number=2912,
            project_id="PVT_123",
            status="Backlog",
            agents=["speckit.specify", "designer"],
        )

        # Should reconstruct for "Backlog" (the requested status), NOT "In Progress"
        mock_reconstruct.assert_called_once()
        call_kwargs = mock_reconstruct.call_args[1]
        assert call_kwargs["status"] == "Backlog"
        assert call_kwargs["agents"] == ["speckit.specify", "designer"]
        assert result.status == "Backlog"
        assert result.is_complete

    @pytest.mark.asyncio
    @patch(
        "src.services.copilot_polling.pipeline._reconstruct_pipeline_state",
        new_callable=AsyncMock,
    )
    @patch("src.services.copilot_polling.pipeline._cp.parse_tracking_from_body")
    @patch("src.services.copilot_polling.pipeline._cp.github_projects_service")
    async def test_still_reconstructs_for_earlier_status_when_requested_has_incomplete(
        self,
        mock_service,
        mock_parse_tracking,
        mock_reconstruct,
    ):
        """Original behavior preserved: when the board says 'In Review' but
        In Progress still has pending agents, reconstruction should use
        'In Progress' agents (the first incomplete is in an earlier status).
        """
        from src.services.agent_tracking import AgentStep
        from src.services.copilot_polling import _get_or_reconstruct_pipeline

        mock_parse_tracking.return_value = [
            AgentStep(index=1, status="Backlog", agent_name="speckit.specify", state="✅ Done"),
            AgentStep(index=2, status="Ready", agent_name="speckit.plan", state="✅ Done"),
            AgentStep(
                index=3, status="In Progress", agent_name="speckit.implement", state="✅ Done"
            ),
            AgentStep(index=4, status="In Progress", agent_name="judge", state="⏳ Pending"),
            AgentStep(index=5, status="In Review", agent_name="human", state="⏳ Pending"),
        ]

        mock_service.get_issue_with_comments = AsyncMock(
            return_value={"body": "...tracking table...", "comments": []}
        )

        mock_reconstruct.return_value = PipelineState(
            issue_number=1538,
            project_id="PVT_123",
            status="In Progress",
            agents=["speckit.implement", "judge"],
            current_agent_index=1,
            completed_agents=["speckit.implement"],
        )

        result = await _get_or_reconstruct_pipeline(
            access_token="token",
            owner="owner",
            repo="repo",
            issue_number=1538,
            project_id="PVT_123",
            status="In Review",
            agents=["human"],
        )

        # Should reconstruct for "In Progress" (earlier status with pending agents)
        mock_reconstruct.assert_called_once()
        call_kwargs = mock_reconstruct.call_args[1]
        assert call_kwargs["status"] == "In Progress"
        assert call_kwargs["agents"] == ["speckit.implement", "judge"]
        assert result.status == "In Progress"


# ── Fix: _self_heal_tracking_table ───────────────────────────────────────


class TestSelfHealTrackingTable:
    """Tests for _self_heal_tracking_table: building and embedding a tracking
    table from sub-issues when the issue body has none.

    This prevents pipeline agent skipping after a container restart when the
    per-status DB config doesn't cover agents from other statuses.
    """

    @pytest.fixture(autouse=True)
    def clear_states(self):
        from src.services.workflow_orchestrator import _pipeline_states

        _pipeline_states.clear()
        yield
        _pipeline_states.clear()

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.pipeline._cp.github_projects_service")
    @patch("src.services.copilot_polling.pipeline._cp.get_workflow_config", new_callable=AsyncMock)
    async def test_builds_tracking_table_from_sub_issues(
        self,
        mock_get_config,
        mock_service,
    ):
        """When sub-issues exist, builds a tracking table and embeds it."""
        config = MagicMock()
        config.status_backlog = "Backlog"
        config.status_ready = "Ready"
        config.status_in_progress = "In Progress"
        config.status_in_review = "In Review"
        config.agent_mappings = {
            "Backlog": [MagicMock(slug="speckit.specify")],
            "Ready": [MagicMock(slug="designer"), MagicMock(slug="speckit.plan")],
            "In Progress": [MagicMock(slug="speckit.implement")],
            "In Review": [MagicMock(slug="copilot-review")],
        }
        mock_get_config.return_value = config

        mock_service.get_sub_issues = AsyncMock(
            return_value=[
                {"number": 100, "title": "[speckit.specify] My Issue"},
                {"number": 101, "title": "[designer] My Issue"},
                {"number": 102, "title": "[speckit.plan] My Issue"},
                {"number": 103, "title": "[speckit.implement] My Issue"},
                {"number": 104, "title": "[copilot-review] My Issue"},
            ]
        )
        mock_service.update_issue_body = AsyncMock()

        result = await _self_heal_tracking_table(
            access_token="token",
            owner="owner",
            repo="repo",
            issue_number=42,
            project_id="PVT_123",
            body="Original body text",
        )

        assert result is not None
        assert len(result) == 5
        assert result[0].agent_name == "speckit.specify"
        assert result[0].status == "Backlog"
        assert result[1].agent_name == "designer"
        assert result[1].status == "Ready"
        assert result[2].agent_name == "speckit.plan"
        assert result[2].status == "Ready"
        assert result[3].agent_name == "speckit.implement"
        assert result[3].status == "In Progress"
        assert result[4].agent_name == "copilot-review"
        assert result[4].status == "In Review"

        # Should have updated the issue body
        mock_service.update_issue_body.assert_called_once()
        call_kwargs = mock_service.update_issue_body.call_args[1]
        assert "Agents Pipelines" in call_kwargs["body"]

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.pipeline._cp.github_projects_service")
    @patch("src.services.copilot_polling.pipeline._cp.get_workflow_config", new_callable=AsyncMock)
    async def test_returns_none_when_no_sub_issues(
        self,
        mock_get_config,
        mock_service,
    ):
        """Returns None when no sub-issues exist."""
        config = MagicMock()
        config.status_backlog = "Backlog"
        config.status_ready = "Ready"
        config.status_in_progress = "In Progress"
        config.status_in_review = "In Review"
        config.agent_mappings = {"Backlog": [MagicMock(slug="speckit.specify")]}
        mock_get_config.return_value = config

        mock_service.get_sub_issues = AsyncMock(return_value=[])

        result = await _self_heal_tracking_table(
            access_token="token",
            owner="owner",
            repo="repo",
            issue_number=42,
            project_id="PVT_123",
            body="Original body",
        )

        assert result is None

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.pipeline._cp.github_projects_service")
    @patch("src.services.copilot_polling.pipeline._cp.get_workflow_config", new_callable=AsyncMock)
    async def test_returns_none_when_no_config(
        self,
        mock_get_config,
        mock_service,
    ):
        """Returns None when no workflow config exists."""
        mock_get_config.return_value = None

        result = await _self_heal_tracking_table(
            access_token="token",
            owner="owner",
            repo="repo",
            issue_number=42,
            project_id="PVT_123",
            body="body",
        )

        assert result is None

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.pipeline._cp.github_projects_service")
    @patch("src.services.copilot_polling.pipeline._cp.get_workflow_config", new_callable=AsyncMock)
    async def test_unknown_agents_inherit_previous_status(
        self,
        mock_get_config,
        mock_service,
    ):
        """Agents not in DB config inherit the previous agent's status."""
        config = MagicMock()
        config.status_backlog = "Backlog"
        config.status_ready = "Ready"
        config.status_in_progress = "In Progress"
        config.status_in_review = "In Review"
        # Config only knows speckit.specify and speckit.implement
        config.agent_mappings = {
            "Backlog": [MagicMock(slug="speckit.specify")],
            "In Progress": [MagicMock(slug="speckit.implement")],
        }
        mock_get_config.return_value = config

        mock_service.get_sub_issues = AsyncMock(
            return_value=[
                {"number": 100, "title": "[speckit.specify] Title"},
                {"number": 101, "title": "[designer] Title"},
                {"number": 102, "title": "[speckit.implement] Title"},
            ]
        )
        mock_service.update_issue_body = AsyncMock()

        result = await _self_heal_tracking_table(
            access_token="token",
            owner="owner",
            repo="repo",
            issue_number=42,
            project_id="PVT_123",
            body="body",
        )

        assert result is not None
        assert len(result) == 3
        assert result[0].status == "Backlog"  # speckit.specify in config
        assert result[1].status == "Backlog"  # designer not in config, inherits Backlog
        assert result[2].status == "In Progress"  # speckit.implement in config

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.pipeline._cp.github_projects_service")
    @patch("src.services.copilot_polling.pipeline._cp.get_workflow_config", new_callable=AsyncMock)
    async def test_still_returns_steps_when_body_update_fails(
        self,
        mock_get_config,
        mock_service,
    ):
        """Returns steps even if updating the issue body fails."""
        config = MagicMock()
        config.status_backlog = "Backlog"
        config.status_ready = "Ready"
        config.status_in_progress = "In Progress"
        config.status_in_review = "In Review"
        config.agent_mappings = {
            "Backlog": [MagicMock(slug="speckit.specify")],
        }
        mock_get_config.return_value = config

        mock_service.get_sub_issues = AsyncMock(
            return_value=[
                {"number": 100, "title": "[speckit.specify] Title"},
            ]
        )
        mock_service.update_issue_body = AsyncMock(side_effect=Exception("API error"))

        result = await _self_heal_tracking_table(
            access_token="token",
            owner="owner",
            repo="repo",
            issue_number=42,
            project_id="PVT_123",
            body="body",
        )

        # Should still return the steps for this cycle
        assert result is not None
        assert len(result) == 1
        assert result[0].agent_name == "speckit.specify"


class TestGetOrReconstructPipelineSelfHeal:
    """Integration tests: _get_or_reconstruct_pipeline invokes
    _self_heal_tracking_table when the issue body has no tracking table
    but sub-issues exist.
    """

    @pytest.fixture(autouse=True)
    def clear_states(self):
        from src.services.workflow_orchestrator import _pipeline_states

        _pipeline_states.clear()
        yield
        _pipeline_states.clear()

    @pytest.mark.asyncio
    @patch(
        "src.services.copilot_polling.pipeline._reconstruct_pipeline_state", new_callable=AsyncMock
    )
    @patch(
        "src.services.copilot_polling.pipeline._self_heal_tracking_table", new_callable=AsyncMock
    )
    @patch("src.services.copilot_polling.pipeline._cp.parse_tracking_from_body")
    @patch("src.services.copilot_polling.pipeline._cp.github_projects_service")
    async def test_self_heals_when_no_tracking_table(
        self,
        mock_service,
        mock_parse_tracking,
        mock_heal,
        mock_reconstruct,
    ):
        """When parse_tracking returns None, self-healing is attempted.
        If it produces steps, they are used for reconstruction.
        """
        from src.services.agent_tracking import AgentStep
        from src.services.copilot_polling import _get_or_reconstruct_pipeline

        # No tracking table in body
        mock_parse_tracking.return_value = None

        # Self-healing produces steps from sub-issues
        mock_heal.return_value = [
            AgentStep(index=1, status="Backlog", agent_name="speckit.specify", state="⏳ Pending"),
            AgentStep(index=2, status="Ready", agent_name="designer", state="⏳ Pending"),
            AgentStep(
                index=3, status="In Progress", agent_name="speckit.implement", state="⏳ Pending"
            ),
        ]

        mock_service.get_issue_with_comments = AsyncMock(
            return_value={"body": "no tracking table here", "comments": []}
        )

        mock_reconstruct.return_value = PipelineState(
            issue_number=42,
            project_id="PVT_123",
            status="Backlog",
            agents=["speckit.specify"],
            current_agent_index=0,
            completed_agents=[],
        )

        await _get_or_reconstruct_pipeline(
            access_token="token",
            owner="owner",
            repo="repo",
            issue_number=42,
            project_id="PVT_123",
            status="In Progress",
            agents=["speckit.implement"],
        )

        # Self-healing should have been called
        mock_heal.assert_called_once()
        # Reconstruction should use tracking table agents, not per-status
        mock_reconstruct.assert_called_once()

    @pytest.mark.asyncio
    @patch(
        "src.services.copilot_polling.pipeline._reconstruct_pipeline_state", new_callable=AsyncMock
    )
    @patch(
        "src.services.copilot_polling.pipeline._self_heal_tracking_table", new_callable=AsyncMock
    )
    @patch("src.services.copilot_polling.pipeline._cp.parse_tracking_from_body")
    @patch("src.services.copilot_polling.pipeline._cp.github_projects_service")
    async def test_falls_through_when_heal_returns_none(
        self,
        mock_service,
        mock_parse_tracking,
        mock_heal,
        mock_reconstruct,
    ):
        """When self-healing returns None, reconstruction uses original agents."""
        from src.services.copilot_polling import _get_or_reconstruct_pipeline

        mock_parse_tracking.return_value = None
        mock_heal.return_value = None  # No sub-issues found

        mock_service.get_issue_with_comments = AsyncMock(
            return_value={"body": "plain body", "comments": []}
        )

        mock_reconstruct.return_value = PipelineState(
            issue_number=42,
            project_id="PVT_123",
            status="In Progress",
            agents=["speckit.implement"],
            current_agent_index=0,
            completed_agents=[],
        )

        await _get_or_reconstruct_pipeline(
            access_token="token",
            owner="owner",
            repo="repo",
            issue_number=42,
            project_id="PVT_123",
            status="In Progress",
            agents=["speckit.implement"],
        )

        mock_heal.assert_called_once()
        # Should fall through to default reconstruction with original agents
        mock_reconstruct.assert_called_once()
        call_kwargs = mock_reconstruct.call_args[1]
        assert call_kwargs["agents"] == ["speckit.implement"]


# ────────────────────────────────────────────────────────────────────
# Recovery: "In Review" issues are now recoverable  (Bug E / Gap 2)
# ────────────────────────────────────────────────────────────────────


class TestRecoveryIncludesInReview:
    """Verify that recover_stalled_issues processes 'In Review' issues."""

    TRACKING_IN_REVIEW = (
        "## Issue Body\n\n"
        "---\n\n"
        "## 🤖 Agent Pipeline\n\n"
        "| # | Status | Agent | Model | State |\n"
        "|---|--------|-------|-------|-------|\n"
        "| 1 | In Review | `copilot-review` | gpt-4o | 🔄 Active |\n"
    )

    @pytest.fixture(autouse=True)
    def _clear(self):
        _recovery_last_attempt.clear()
        _pending_agent_assignments.clear()
        yield
        _recovery_last_attempt.clear()
        _pending_agent_assignments.clear()

    @pytest.fixture
    def mock_in_review_task(self):
        task = MagicMock()
        task.github_item_id = "PVTI_200"
        task.github_content_id = "I_200"
        task.issue_number = 200
        task.repository_owner = "owner"
        task.repository_name = "repo"
        task.title = "Review Issue"
        task.status = "In Review"
        return task

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.get_issue_main_branch")
    @patch("src.services.copilot_polling.github_projects_service")
    @patch("src.services.copilot_polling.get_workflow_config", new_callable=AsyncMock)
    async def test_in_review_issue_not_skipped(
        self, mock_config, mock_service, mock_get_branch, mock_in_review_task
    ):
        """An 'In Review' issue with a healthy active agent should be checked (not skipped)."""
        mock_config.return_value = MagicMock(
            status_in_review="In Review",
            agent_mappings={"In Review": ["copilot-review"]},
        )
        mock_service.get_issue_with_comments = AsyncMock(
            return_value={
                "body": self.TRACKING_IN_REVIEW,
                "title": "",
                "comments": [],
                "user": {"login": ""},
            }
        )
        # Copilot-review is a non-coding agent — recovery only checks completion
        mock_service.is_copilot_assigned_to_issue = AsyncMock(return_value=True)
        mock_service.get_linked_pull_requests = AsyncMock(return_value=[])
        mock_get_branch.return_value = None

        await recover_stalled_issues(
            access_token="token",
            project_id="PVT_1",
            owner="owner",
            repo="repo",
            tasks=[mock_in_review_task],
        )

        # The issue was PROCESSED (not skipped) — get_issue_with_comments was called
        assert mock_service.get_issue_with_comments.call_count >= 1

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.get_workflow_orchestrator")
    @patch("src.services.copilot_polling.get_issue_main_branch")
    @patch("src.services.copilot_polling.github_projects_service")
    @patch("src.services.copilot_polling.get_workflow_config", new_callable=AsyncMock)
    async def test_in_review_stalled_agent_gets_recovered(
        self, mock_config, mock_service, mock_get_branch, mock_get_orch, mock_in_review_task
    ):
        """An 'In Review' issue with unassigned/stalled coding agent should be recovered."""
        tracking_body = (
            "## Issue Body\n\n"
            "---\n\n"
            "## 🤖 Agent Pipeline\n\n"
            "| # | Status | Agent | Model | State |\n"
            "|---|--------|-------|-------|-------|\n"
            "| 1 | In Progress | `speckit.implement` | gpt-4o | 🔄 Active |\n"
            "| 2 | In Review | `copilot-review` | gpt-4o | ⏳ Pending |\n"
        )
        mock_config.return_value = MagicMock(
            status_in_review="In Review",
            agent_mappings={"In Progress": ["speckit.implement"], "In Review": ["copilot-review"]},
        )
        mock_service.get_issue_with_comments = AsyncMock(return_value={"body": tracking_body})
        mock_service.is_copilot_assigned_to_issue = AsyncMock(return_value=False)
        mock_service.get_linked_pull_requests = AsyncMock(return_value=[])
        mock_service.check_agent_completion_comment = AsyncMock(return_value=False)
        mock_get_branch.return_value = None

        mock_orchestrator = MagicMock()
        mock_orchestrator.assign_agent_for_status = AsyncMock(return_value=True)
        mock_get_orch.return_value = mock_orchestrator

        results = await recover_stalled_issues(
            access_token="token",
            project_id="PVT_1",
            owner="owner",
            repo="repo",
            tasks=[mock_in_review_task],
        )

        assert len(results) == 1
        assert results[0]["status"] == "recovered"
        assert results[0]["issue_number"] == 200
        assert results[0]["agent_name"] == "speckit.implement"


# ────────────────────────────────────────────────────────────────────
# Recovery: self-heal tracking table from sub-issues  (Bug E / Gap 3)
# ────────────────────────────────────────────────────────────────────


class TestRecoverySelfHealTracking:
    """Recovery should build a tracking table from sub-issues when missing."""

    @pytest.fixture(autouse=True)
    def _clear(self):
        _recovery_last_attempt.clear()
        _pending_agent_assignments.clear()
        yield
        _recovery_last_attempt.clear()
        _pending_agent_assignments.clear()

    @pytest.fixture
    def mock_backlog_task(self):
        task = MagicMock()
        task.github_item_id = "PVTI_100"
        task.github_content_id = "I_100"
        task.issue_number = 100
        task.repository_owner = "owner"
        task.repository_name = "repo"
        task.title = "Issue Without Tracking"
        task.status = "Backlog"
        return task

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.get_workflow_orchestrator")
    @patch("src.services.copilot_polling.get_issue_main_branch")
    @patch(
        "src.services.copilot_polling._check_agent_done_on_sub_or_parent",
        new_callable=AsyncMock,
    )
    @patch(
        "src.services.copilot_polling.pipeline._self_heal_tracking_table", new_callable=AsyncMock
    )
    @patch("src.services.copilot_polling.github_projects_service")
    @patch("src.services.copilot_polling.get_workflow_config", new_callable=AsyncMock)
    async def test_self_heals_and_recovers(
        self,
        mock_config,
        mock_service,
        mock_heal,
        mock_check_done,
        mock_get_branch,
        mock_get_orch,
        mock_backlog_task,
    ):
        """When no tracking table exists, self-heal from sub-issues then recover."""
        from src.services.agent_tracking import AgentStep

        mock_config.return_value = MagicMock(
            status_in_review="In Review",
            agent_mappings={"Backlog": ["speckit.specify"]},
        )
        # First call: no tracking table
        mock_service.get_issue_with_comments = AsyncMock(
            side_effect=[
                {"body": "Plain body without tracking table."},
                # Second call after self-heal: re-read shows the embedded table
                # (must match render_tracking_markdown format: --- separator, 5-col)
                {
                    "body": (
                        "Plain body without tracking table.\n"
                        "---\n\n"
                        "## 🤖 Agents Pipelines\n\n"
                        "| # | Status | Agent | Model | State |\n"
                        "|---|--------|-------|-------|-------|\n"
                        "| 1 | Backlog | `speckit.specify` | TBD | ⏳ Pending |\n"
                    )
                },
            ]
        )
        # Self-heal returns steps
        mock_heal.return_value = [
            AgentStep(index=1, status="Backlog", agent_name="speckit.specify"),
        ]
        mock_service.is_copilot_assigned_to_issue = AsyncMock(return_value=False)
        mock_service.get_linked_pull_requests = AsyncMock(return_value=[])
        mock_check_done.return_value = False
        mock_get_branch.return_value = None

        mock_orchestrator = MagicMock()
        mock_orchestrator.assign_agent_for_status = AsyncMock(return_value=True)
        mock_get_orch.return_value = mock_orchestrator

        results = await recover_stalled_issues(
            access_token="token",
            project_id="PVT_1",
            owner="owner",
            repo="repo",
            tasks=[mock_backlog_task],
        )

        mock_heal.assert_called_once()
        assert len(results) == 1
        assert results[0]["status"] == "recovered"
        assert results[0]["agent_name"] == "speckit.specify"


# ────────────────────────────────────────────────────────────────────
# Pipeline: first agent recovery  (Bug E / Gap 1)
# ────────────────────────────────────────────────────────────────────


class TestProcessPipelineCompletionFirstAgent:
    """_process_pipeline_completion should assign the first agent in a pipeline
    when completed_agents is empty and the agent was never assigned."""

    @pytest.fixture(autouse=True)
    def _clear(self):
        from src.services.workflow_orchestrator import _pipeline_states

        _pending_agent_assignments.clear()
        _pipeline_states.clear()
        yield
        _pending_agent_assignments.clear()
        _pipeline_states.clear()

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.get_workflow_orchestrator")
    @patch("src.services.copilot_polling.get_workflow_config", new_callable=AsyncMock)
    @patch("src.services.copilot_polling.github_projects_service")
    @patch(
        "src.services.copilot_polling._check_agent_done_on_sub_or_parent",
        new_callable=AsyncMock,
    )
    @patch("src.services.copilot_polling._get_tracking_state_from_issue", new_callable=AsyncMock)
    async def test_assigns_first_agent_with_empty_completed_agents(
        self,
        mock_tracking,
        mock_check_done,
        mock_service,
        mock_config,
        mock_get_orch,
    ):
        """When completed_agents is empty and current agent is not done, it
        should still be assigned (not silently skipped)."""
        from src.services.copilot_polling import _process_pipeline_completion

        pipeline = PipelineState(
            issue_number=42,
            project_id="PVT_123",
            status="Backlog",
            agents=["speckit.specify", "speckit.plan"],
            current_agent_index=0,
            completed_agents=[],  # No prior completions
            started_at=datetime(2025, 1, 1, tzinfo=UTC),  # Well past grace period
        )

        task = MagicMock()
        task.issue_number = 42
        task.github_item_id = "PVTI_123"
        task.github_content_id = "I_123"
        task.repository_owner = "owner"
        task.repository_name = "repo"
        task.title = "Test Issue"

        # Agent not done
        mock_check_done.return_value = False
        # Tracking shows ⏳ Pending (agent was never assigned)
        tracking_body = (
            "---\n\n"
            "## 🤖 Agents Pipelines\n\n"
            "| # | Status | Agent | Model | State |\n"
            "|---|--------|-------|-------|-------|\n"
            "| 1 | Backlog | `speckit.specify` | TBD | ⏳ Pending |\n"
            "| 2 | Backlog | `speckit.plan` | TBD | ⏳ Pending |\n"
        )
        mock_tracking.return_value = (tracking_body, [])

        mock_orchestrator = MagicMock()
        mock_orchestrator.assign_agent_for_status = AsyncMock(return_value=True)
        mock_get_orch.return_value = mock_orchestrator
        mock_config.return_value = MagicMock()

        result = await _process_pipeline_completion(
            access_token="token",
            project_id="PVT_123",
            task=task,
            owner="owner",
            repo="repo",
            pipeline=pipeline,
            from_status="Backlog",
            to_status="Ready",
        )

        assert result is not None
        assert result["action"] == "agent_assigned_after_reconstruction"
        assert result["agent_name"] == "speckit.specify"
        mock_orchestrator.assign_agent_for_status.assert_called_once()

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.get_workflow_config", new_callable=AsyncMock)
    @patch("src.services.copilot_polling.github_projects_service")
    @patch(
        "src.services.copilot_polling._check_agent_done_on_sub_or_parent",
        new_callable=AsyncMock,
    )
    @patch("src.services.copilot_polling._get_tracking_state_from_issue", new_callable=AsyncMock)
    async def test_respects_grace_period_for_first_agent(
        self,
        mock_tracking,
        mock_check_done,
        mock_service,
        mock_config,
    ):
        """First agent should NOT be assigned during grace period even with
        empty completed_agents."""
        from src.services.copilot_polling import _process_pipeline_completion

        pipeline = PipelineState(
            issue_number=42,
            project_id="PVT_123",
            status="Backlog",
            agents=["speckit.specify"],
            current_agent_index=0,
            completed_agents=[],
            started_at=utcnow(),  # Just started — within grace period
        )

        task = MagicMock()
        task.issue_number = 42
        task.github_item_id = "PVTI_123"
        task.github_content_id = "I_123"
        task.repository_owner = "owner"
        task.repository_name = "repo"
        task.title = "Test"

        mock_check_done.return_value = False

        result = await _process_pipeline_completion(
            access_token="token",
            project_id="PVT_123",
            task=task,
            owner="owner",
            repo="repo",
            pipeline=pipeline,
            from_status="Backlog",
            to_status="Ready",
        )

        # Should return None (waiting for grace period), NOT assign
        assert result is None
        mock_tracking.assert_not_called()

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.get_workflow_config", new_callable=AsyncMock)
    @patch("src.services.copilot_polling.github_projects_service")
    @patch(
        "src.services.copilot_polling._check_agent_done_on_sub_or_parent",
        new_callable=AsyncMock,
    )
    @patch("src.services.copilot_polling._get_tracking_state_from_issue", new_callable=AsyncMock)
    async def test_skips_when_first_agent_already_active_in_tracking(
        self,
        mock_tracking,
        mock_check_done,
        mock_service,
        mock_config,
    ):
        """First agent with 🔄 Active in tracking table should NOT be re-assigned."""
        from src.services.copilot_polling import _process_pipeline_completion

        pipeline = PipelineState(
            issue_number=42,
            project_id="PVT_123",
            status="Backlog",
            agents=["speckit.specify"],
            current_agent_index=0,
            completed_agents=[],
            started_at=datetime(2025, 1, 1, tzinfo=UTC),
        )

        task = MagicMock()
        task.issue_number = 42
        task.github_item_id = "PVTI_123"
        task.github_content_id = "I_123"
        task.repository_owner = "owner"
        task.repository_name = "repo"
        task.title = "Test"

        mock_check_done.return_value = False
        # Tracking shows 🔄 Active — already assigned
        tracking_body = (
            "---\n\n"
            "## 🤖 Agents Pipelines\n\n"
            "| # | Status | Agent | Model | State |\n"
            "|---|--------|-------|-------|-------|\n"
            "| 1 | Backlog | `speckit.specify` | TBD | 🔄 Active |\n"
        )
        mock_tracking.return_value = (tracking_body, [])

        result = await _process_pipeline_completion(
            access_token="token",
            project_id="PVT_123",
            task=task,
            owner="owner",
            repo="repo",
            pipeline=pipeline,
            from_status="Backlog",
            to_status="Ready",
        )

        assert result is None  # Already assigned, wait


# ── Fix: _advance_pipeline uses original_status for agent lookup ─────────


class TestAdvancePipelineUsesOriginalStatus:
    """Tests that _advance_pipeline uses pipeline.original_status (not
    pipeline.status) for agent lookup when the board was moved externally.

    Regression test for the bug where GitHub randomly moved an issue to
    'In Progress' while 'Ready' agents were running.  The pipeline's status
    was updated to 'In Progress' to match the board, but _advance_pipeline
    then looked up 'In Progress' agents instead of 'Ready' agents — causing
    the second Ready agent (speckit.tasks) to be silently skipped.
    """

    @pytest.fixture(autouse=True)
    def clear_states(self):
        from src.services.workflow_orchestrator import _pipeline_states

        _pipeline_states.clear()
        yield
        _pipeline_states.clear()

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling._update_issue_tracking", new_callable=AsyncMock)
    @patch("src.services.copilot_polling.github_projects_service")
    @patch("src.services.copilot_polling.connection_manager")
    @patch("src.services.copilot_polling.get_issue_main_branch")
    @patch("src.services.copilot_polling._merge_child_pr_if_applicable")
    @patch("src.services.copilot_polling.get_workflow_orchestrator")
    @patch("src.services.copilot_polling.get_workflow_config", new_callable=AsyncMock)
    @patch("src.services.copilot_polling.set_pipeline_state")
    async def test_uses_original_status_when_board_moved_ahead(
        self,
        mock_set_state,
        mock_config,
        mock_get_orchestrator,
        mock_merge,
        mock_get_branch,
        mock_ws,
        mock_service,
        mock_update_tracking,
    ):
        """When pipeline.original_status='Ready' but pipeline.status='In Progress'
        (because GitHub moved the issue), agent lookup must use 'Ready' so
        speckit.tasks is found at the correct index."""
        pipeline = PipelineState(
            issue_number=99,
            project_id="PVT_123",
            status="In Progress",  # Board-updated status
            agents=["speckit.plan", "speckit.tasks"],  # Ready agents
            current_agent_index=0,  # speckit.plan just completed
            completed_agents=[],
            original_status="Ready",  # The REAL pipeline origin
            target_status="In Progress",
        )

        mock_get_branch.return_value = None
        mock_merge.return_value = None
        mock_ws.broadcast_to_project = AsyncMock()
        mock_orchestrator = MagicMock()
        mock_orchestrator.assign_agent_for_status = AsyncMock(return_value=True)
        mock_get_orchestrator.return_value = mock_orchestrator
        mock_config.return_value = MagicMock()
        mock_update_tracking.return_value = True

        result = await _advance_pipeline(
            access_token="token",
            project_id="PVT_123",
            item_id="PVTI_99",
            owner="owner",
            repo="repo",
            issue_number=99,
            issue_node_id="I_99",
            pipeline=pipeline,
            from_status="Ready",
            to_status="In Progress",
            task_title="Test Issue",
        )

        assert result["status"] == "success"
        assert result["completed_agent"] == "speckit.plan"
        assert result["agent_name"] == "speckit.tasks"

        # Crucially: assign_agent_for_status must be called with
        # "Ready" (original_status), NOT "In Progress" (pipeline.status).
        call_args = mock_orchestrator.assign_agent_for_status.call_args
        assert call_args is not None
        status_arg = call_args[0][1]  # second positional arg = status
        assert status_arg == "Ready", (
            f"Expected 'Ready' (original_status) but got '{status_arg}' — "
            "this would cause speckit.tasks to be skipped because 'In Progress' "
            "agents don't include it"
        )

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling._update_issue_tracking", new_callable=AsyncMock)
    @patch("src.services.copilot_polling.github_projects_service")
    @patch("src.services.copilot_polling.connection_manager")
    @patch("src.services.copilot_polling.get_issue_main_branch")
    @patch("src.services.copilot_polling._merge_child_pr_if_applicable")
    @patch("src.services.copilot_polling.get_workflow_orchestrator")
    @patch("src.services.copilot_polling.get_workflow_config", new_callable=AsyncMock)
    @patch("src.services.copilot_polling.set_pipeline_state")
    async def test_falls_back_to_pipeline_status_when_no_original(
        self,
        mock_set_state,
        mock_config,
        mock_get_orchestrator,
        mock_merge,
        mock_get_branch,
        mock_ws,
        mock_service,
        mock_update_tracking,
    ):
        """When original_status is not set, pipeline.status should be used
        for agent lookup (existing behavior preserved)."""
        pipeline = PipelineState(
            issue_number=100,
            project_id="PVT_123",
            status="In Progress",
            agents=["speckit.implement", "judge"],
            current_agent_index=0,
            completed_agents=[],
            # original_status NOT set — normal pipeline
        )

        mock_get_branch.return_value = None
        mock_merge.return_value = None
        mock_ws.broadcast_to_project = AsyncMock()
        mock_orchestrator = MagicMock()
        mock_orchestrator.assign_agent_for_status = AsyncMock(return_value=True)
        mock_get_orchestrator.return_value = mock_orchestrator
        mock_config.return_value = MagicMock()
        mock_update_tracking.return_value = True

        result = await _advance_pipeline(
            access_token="token",
            project_id="PVT_123",
            item_id="PVTI_100",
            owner="owner",
            repo="repo",
            issue_number=100,
            issue_node_id="I_100",
            pipeline=pipeline,
            from_status="In Progress",
            to_status="In Review",
            task_title="Normal Issue",
        )

        assert result["status"] == "success"
        call_args = mock_orchestrator.assign_agent_for_status.call_args
        status_arg = call_args[0][1]
        assert status_arg == "In Progress"


# ── Fix: _process_pipeline_completion uses original_status for reassignment ──


class TestProcessPipelineCompletionUsesOriginalStatus:
    """Tests that the 'agent never assigned' path in _process_pipeline_completion
    uses pipeline.original_status for the assign_agent_for_status call."""

    @pytest.fixture(autouse=True)
    def clear_states(self):
        from src.services.copilot_polling.state import (
            _pending_agent_assignments,
            _polling_state,
        )
        from src.services.workflow_orchestrator import _pipeline_states

        _pipeline_states.clear()
        _pending_agent_assignments.clear()
        old_err = _polling_state.errors_count
        yield
        _pipeline_states.clear()
        _pending_agent_assignments.clear()
        _polling_state.errors_count = old_err

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.get_workflow_config", new_callable=AsyncMock)
    @patch("src.services.copilot_polling.get_workflow_orchestrator")
    @patch(
        "src.services.copilot_polling._check_agent_done_on_sub_or_parent", new_callable=AsyncMock
    )
    @patch("src.services.copilot_polling._get_tracking_state_from_issue", new_callable=AsyncMock)
    @patch("src.services.copilot_polling.get_current_agent_from_tracking")
    @patch("src.services.copilot_polling.github_projects_service")
    async def test_uses_original_status_for_never_assigned_agent(
        self,
        mock_service,
        mock_get_tracking,
        mock_tracking_state,
        mock_check_done,
        mock_get_orchestrator,
        mock_config,
    ):
        """When pipeline.original_status='Ready' and from_status='In Progress'
        (board moved), the assign call should use 'Ready' so the correct
        agent list is resolved."""
        from datetime import timedelta

        from src.utils import utcnow

        pipeline = PipelineState(
            issue_number=55,
            project_id="PVT_123",
            status="In Progress",
            agents=["speckit.plan", "speckit.tasks"],
            current_agent_index=1,  # speckit.tasks needs assignment
            completed_agents=["speckit.plan"],
            started_at=utcnow() - timedelta(seconds=300),  # past grace period
            original_status="Ready",
            target_status="In Progress",
        )

        task = MagicMock()
        task.issue_number = 55
        task.github_item_id = "PVTI_55"
        task.github_content_id = "I_55"
        task.repository_owner = "owner"
        task.repository_name = "repo"
        task.title = "Test"

        mock_check_done.return_value = False
        # Tracking shows ⏳ Pending — agent was never assigned
        mock_tracking_state.return_value = ("body", [])
        mock_get_tracking.return_value = None  # Not active in tracking

        mock_orchestrator = MagicMock()
        mock_orchestrator.assign_agent_for_status = AsyncMock(return_value=True)
        mock_get_orchestrator.return_value = mock_orchestrator
        mock_config.return_value = MagicMock()

        result = await _process_pipeline_completion(
            access_token="token",
            project_id="PVT_123",
            task=task,
            owner="owner",
            repo="repo",
            pipeline=pipeline,
            from_status="In Progress",  # Board status
            to_status="In Review",
        )

        assert result is not None
        assert result["action"] == "agent_assigned_after_reconstruction"

        # The assign call must use "Ready" (original_status), not "In Progress"
        call_args = mock_orchestrator.assign_agent_for_status.call_args
        status_arg = call_args[0][1]
        assert status_arg == "Ready", f"Expected 'Ready' (original_status) but got '{status_arg}'"


# ── Fix: copilot-review request timestamps recorded ─────────────────────


class TestCopilotReviewRequestTimestamp:
    """Tests that copilot-review request timestamps are recorded in
    _copilot_review_requested_at so _check_copilot_review_done can
    filter out random/auto-triggered GitHub reviews."""

    @pytest.fixture(autouse=True)
    def clear_states(self):
        from src.services.copilot_polling.state import (
            _copilot_review_requested_at,
            _review_requested_cache,
        )

        _copilot_review_requested_at.clear()
        _processed_issue_prs.clear()
        _review_requested_cache.clear()
        yield
        _copilot_review_requested_at.clear()
        _processed_issue_prs.clear()
        _review_requested_cache.clear()

    @pytest.mark.asyncio
    @patch(
        "src.services.copilot_polling.helpers._discover_main_pr_for_review",
        new_callable=AsyncMock,
    )
    @patch("src.services.copilot_polling.github_projects_service")
    async def test_ensure_copilot_review_records_timestamp(self, mock_service, mock_discover):
        """ensure_copilot_review_requested should record a timestamp in
        _copilot_review_requested_at when it successfully requests a review."""
        from src.services.copilot_polling.state import _copilot_review_requested_at

        mock_discover.return_value = {
            "pr_number": 10,
            "pr_id": "PR_N",
            "is_draft": False,
            "head_ref": "b",
        }
        mock_service.dismiss_copilot_reviews = AsyncMock(return_value=0)
        mock_service.request_copilot_review = AsyncMock(return_value=True)
        mock_service.get_issue_with_comments = AsyncMock(
            return_value={"title": "", "body": "Issue body", "comments": [], "user": {"login": ""}}
        )
        mock_service.update_issue_body = AsyncMock(return_value=True)

        result = await ensure_copilot_review_requested("tok", "o", "r", "PVT_1", 42, "task")
        assert result is not None
        assert result["action"] == "copilot_review_requested"

        # Timestamp must be recorded
        assert 42 in _copilot_review_requested_at
        assert _copilot_review_requested_at[42] is not None
        mock_service.update_issue_body.assert_awaited_once()
        persisted_body = mock_service.update_issue_body.await_args.kwargs["body"]
        assert "<!-- solune:copilot-review-requested-at=" in persisted_body

    @pytest.mark.asyncio
    @patch(
        "src.services.copilot_polling.helpers._discover_main_pr_for_review",
        new_callable=AsyncMock,
    )
    @patch("src.services.copilot_polling.github_projects_service")
    async def test_ensure_copilot_review_no_timestamp_on_failure(self, mock_service, mock_discover):
        """When the review request fails, no timestamp should be recorded."""
        from src.services.copilot_polling.state import _copilot_review_requested_at

        mock_discover.return_value = {
            "pr_number": 10,
            "pr_id": "PR_N",
            "is_draft": False,
            "head_ref": "b",
        }
        mock_service.dismiss_copilot_reviews = AsyncMock(return_value=0)
        mock_service.request_copilot_review = AsyncMock(return_value=False)
        mock_service.get_issue_with_comments = AsyncMock(
            return_value={"title": "", "body": "Issue body", "comments": [], "user": {"login": ""}}
        )
        mock_service.update_issue_body = AsyncMock(return_value=True)

        result = await ensure_copilot_review_requested("tok", "o", "r", "PVT_1", 42, "task")
        assert result["status"] == "error"
        assert 42 not in _copilot_review_requested_at
        mock_service.update_issue_body.assert_not_called()


# ── T043: Cache semantics supporting polling cycle cost (SC-005) ───────────


class TestCacheSemanticsForPolling:
    """Verify InMemoryCache warm-hit and stale-fallback semantics that
    underpin polling cycle cost guarantees (SC-005).
    NOTE: These tests cover cache-layer behavior only, not the actual
    polling endpoint or loop.  End-to-end polling tests are needed to
    fully verify SC-005."""

    def test_warm_cache_prevents_redundant_api_calls(self):
        """When project items cache is warm, polling should not trigger
        expensive external API calls for unchanged data."""
        from src.services.cache import cache, get_project_items_cache_key

        project_id = "PVT_idle"
        cache_key = get_project_items_cache_key(project_id)

        # Populate cache so it's "warm"
        cached_items = [{"id": "1", "title": "cached task"}]
        cache.set(cache_key, cached_items)

        # Verify cache hit prevents the need for external calls
        result = cache.get(cache_key)
        assert result is not None
        assert result == cached_items

    def test_stale_cache_serves_data_without_fetch(self):
        """When cache is expired but stale data exists, get_stale() should
        serve data without requiring an external API call."""
        from src.services.cache import cache, get_project_items_cache_key

        project_id = "PVT_stale"
        cache_key = get_project_items_cache_key(project_id)

        # Set with a short TTL
        cached_items = [{"id": "1", "title": "stale task"}]
        cache.set(cache_key, cached_items, ttl_seconds=1)

        # Manually expire the entry by setting expires_at in the past
        entry = cache.get_entry(cache_key)
        assert entry is not None
        from datetime import timedelta

        from src.utils import utcnow

        entry.expires_at = utcnow() - timedelta(seconds=10)

        # get_stale should still return the expired data (degraded-mode fallback)
        stale = cache.get_stale(cache_key)
        assert stale is not None
        assert stale == cached_items

    def test_unchanged_items_hash_preserves_existing_board_cache_entry(self):
        """Recomputing an unchanged items hash should not disturb an existing
        board cache entry.

        This is a cache-layer invariant used by the no-change polling path,
        not an end-to-end polling-loop test.
        """
        from uuid import uuid4

        from src.services.cache import cache, compute_data_hash, get_project_items_cache_key

        project_id = f"PVT_noop_{uuid4().hex}"
        items_key = get_project_items_cache_key(project_id)
        board_key = f"board_data:{project_id}"

        try:
            # Populate both caches
            items = [{"id": "1", "title": "unchanged task"}]
            items_hash = compute_data_hash(items)
            cache.set(items_key, items, data_hash=items_hash)
            cache.set(board_key, {"columns": []}, ttl_seconds=300)

            cached_items = cache.get(items_key)
            assert cached_items == items

            new_hash = compute_data_hash(cached_items)
            assert new_hash == items_hash, "unchanged data must produce same hash"

            board_data = cache.get(board_key)
            assert board_data is not None, "unrelated board cache entries should remain intact"
        finally:
            cache.delete(items_key)
            cache.delete(board_key)
