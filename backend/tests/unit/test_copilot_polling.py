"""Unit tests for Copilot PR polling service."""

from datetime import UTC, datetime, timedelta
from src.utils import utcnow
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from src.services.copilot_polling import (
    _advance_pipeline,
    _check_agent_done_on_parent,
    _check_child_pr_completion,
    _check_main_pr_completion,
    _claimed_child_prs,
    _filter_events_after,
    _find_completed_child_pr,
    _get_tracking_state_from_issue,
    _merge_child_pr_if_applicable,
    _pending_agent_assignments,
    _poll_loop,
    _posted_agent_outputs,
    _processed_issue_prs,
    _reconstruct_pipeline_state,
    _reconstruct_sub_issue_mappings,
    _recovery_last_attempt,
    _transition_after_pipeline_complete,
    _update_issue_tracking,
    check_backlog_issues,
    check_in_progress_issues,
    check_in_review_issues_for_copilot_review,
    check_issue_for_copilot_completion,
    check_ready_issues,
    ensure_copilot_review_requested,
    get_polling_status,
    post_agent_outputs_from_pr,
    process_in_progress_issue,
    recover_stalled_issues,
    stop_polling,
)
from src.services.workflow_orchestrator import PipelineState, _issue_main_branches


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


class TestGetPollingStatus:
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

        with patch("src.services.copilot_polling.pipeline.process_in_progress_issue") as mock_process:
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

        with patch("src.services.copilot_polling.pipeline.process_in_progress_issue") as mock_process:
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

        with patch("src.services.copilot_polling.pipeline.process_in_progress_issue") as mock_process:
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
        _processed_issue_prs.add("42:100")

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

        assert "42:100" in _processed_issue_prs


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
            "| # | Status | Agent | State |\n"
            "|---|--------|-------|-------|\n"
            "| 1 | Backlog | `speckit.specify` | 🔄 Active |\n"
            "| 2 | Ready | `speckit.plan` | ⏳ Pending |\n"
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
            "| # | Status | Agent | State |\n"
            "|---|--------|-------|-------|\n"
            "| 1 | Backlog | `speckit.specify` | ✅ Done |\n"
            "| 2 | Ready | `speckit.plan` | ⏳ Pending |\n"
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
        mock_service._check_copilot_finished_events = MagicMock(return_value=True)

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
        mock_service._check_copilot_finished_events = MagicMock(return_value=False)

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
        mock_service._check_copilot_finished_events = MagicMock(return_value=True)

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
        call_args = mock_service._check_copilot_finished_events.call_args[0][0]
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
        mock_service._check_copilot_finished_events = MagicMock(return_value=False)

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
        call_args = mock_service._check_copilot_finished_events.call_args[0][0]
        assert len(call_args) == 0

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    async def test_uses_all_events_when_no_pipeline_start(self, mock_service):
        """Should use all events when no pipeline start time is available."""
        mock_service.get_pull_request = AsyncMock(return_value={"state": "OPEN", "is_draft": True})
        mock_service.get_pr_timeline_events = AsyncMock(
            return_value=[{"event": "copilot_work_finished", "created_at": "2025-01-15T16:00:00Z"}]
        )
        mock_service._check_copilot_finished_events = MagicMock(return_value=True)

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
        call_args = mock_service._check_copilot_finished_events.call_args[0][0]
        assert len(call_args) == 1

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    async def test_returns_false_when_no_completion_signals(self, mock_service):
        """Should return False when main PR is draft and no completion events."""
        mock_service.get_pull_request = AsyncMock(return_value={"state": "OPEN", "is_draft": True})
        mock_service.get_pr_timeline_events = AsyncMock(return_value=[])
        mock_service._check_copilot_finished_events = MagicMock(return_value=False)

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
        mock_service._check_copilot_finished_events = MagicMock(return_value=True)

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
            }
        )
        mock_service.get_pr_timeline_events = AsyncMock(return_value=[])
        mock_service._check_copilot_finished_events = MagicMock(return_value=False)

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


# ──────────────────────────────────────────────────────────────────────────────
# Self-Healing Recovery Tests
# ──────────────────────────────────────────────────────────────────────────────


class TestRecoverStalledIssues:
    """Tests for the self-healing recover_stalled_issues function."""

    TRACKING_BODY = (
        "## Issue Body\n\n"
        "---\n\n"
        "## 🤖 Agent Pipeline\n\n"
        "| # | Status | Agent | State |\n"
        "|---|--------|-------|-------|\n"
        "| 1 | Backlog | `speckit.specify` | 🔄 Active |\n"
        "| 2 | Ready | `speckit.plan` | ⏳ Pending |\n"
    )

    TRACKING_BODY_ALL_DONE = (
        "## Issue Body\n\n"
        "---\n\n"
        "## 🤖 Agent Pipeline\n\n"
        "| # | Status | Agent | State |\n"
        "|---|--------|-------|-------|\n"
        "| 1 | Backlog | `speckit.specify` | ✅ Done |\n"
        "| 2 | Ready | `speckit.plan` | ✅ Done |\n"
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
    async def test_skips_terminal_statuses(self, mock_config, mock_in_review_task):
        """Should skip issues that are In Review or Done."""
        mock_config.return_value = MagicMock(
            status_in_review="In Review",
            agent_mappings={"Backlog": ["speckit.specify"]},
        )

        results = await recover_stalled_issues(
            access_token="token",
            project_id="PVT_1",
            owner="owner",
            repo="repo",
            tasks=[mock_in_review_task],
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
    @patch("src.services.copilot_polling.github_projects_service")
    @patch("src.services.copilot_polling.get_workflow_config", new_callable=AsyncMock)
    async def test_skips_issues_without_tracking_table(
        self, mock_config, mock_service, mock_backlog_task
    ):
        """Should skip issues that don't have a tracking table."""
        mock_config.return_value = MagicMock(
            status_in_review="In Review",
            agent_mappings={"Backlog": ["speckit.specify"]},
        )
        mock_service.get_issue_with_comments = AsyncMock(
            return_value={"body": "Just a plain issue body with no tracking table."}
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
        """Should NOT re-assign when the agent already has a Done! marker.

        This guards against the double-trigger bug: after a container restart
        the volatile state is lost but the Done! comment persists.  Recovery
        should see the marker and skip re-assignment.
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
        # Done! marker IS present — agent already completed
        mock_service.check_agent_completion_comment = AsyncMock(return_value=True)

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


# ────────────────────────────────────────────────────────────────────
# ensure_copilot_review_requested  (~80 uncovered lines)
# ────────────────────────────────────────────────────────────────────


class TestEnsureCopilotReviewRequested:
    """Tests for ensure_copilot_review_requested."""

    @pytest.fixture(autouse=True)
    def _clear(self):
        _processed_issue_prs.clear()
        yield
        _processed_issue_prs.clear()

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    async def test_already_cached_returns_none(self, mock_service):
        from src.services.copilot_polling import cache_key_review_requested

        key = cache_key_review_requested(42)
        _processed_issue_prs.add(key)
        result = await ensure_copilot_review_requested("tok", "o", "r", 42, "title")
        assert result is None

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    async def test_no_completed_pr_returns_none(self, mock_service):
        mock_service.check_copilot_pr_completion = AsyncMock(return_value=None)
        result = await ensure_copilot_review_requested("tok", "o", "r", 42, "title")
        assert result is None

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    async def test_copilot_not_finished_returns_none(self, mock_service):
        mock_service.check_copilot_pr_completion = AsyncMock(
            return_value={"copilot_finished": False}
        )
        result = await ensure_copilot_review_requested("tok", "o", "r", 42, "title")
        assert result is None

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    async def test_missing_pr_number_returns_none(self, mock_service):
        mock_service.check_copilot_pr_completion = AsyncMock(
            return_value={"copilot_finished": True, "number": None, "id": None}
        )
        result = await ensure_copilot_review_requested("tok", "o", "r", 42, "title")
        assert result is None

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    async def test_already_reviewed_returns_none(self, mock_service):
        mock_service.check_copilot_pr_completion = AsyncMock(
            return_value={"copilot_finished": True, "pr_number": 10, "id": "PR_N"}
        )
        mock_service.has_copilot_reviewed_pr = AsyncMock(return_value=True)
        result = await ensure_copilot_review_requested("tok", "o", "r", 42, "title")
        assert result is None
        # Should have been cached
        from src.services.copilot_polling import cache_key_review_requested

        assert cache_key_review_requested(42) in _processed_issue_prs

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    async def test_review_requested_successfully(self, mock_service):
        mock_service.check_copilot_pr_completion = AsyncMock(
            return_value={"copilot_finished": True, "pr_number": 10, "id": "PR_N"}
        )
        mock_service.has_copilot_reviewed_pr = AsyncMock(return_value=False)
        mock_service.request_copilot_review = AsyncMock(return_value=True)

        result = await ensure_copilot_review_requested("tok", "o", "r", 42, "my task")
        assert result is not None
        assert result["action"] == "copilot_review_requested"
        assert result["pr_number"] == 10

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    async def test_review_request_fails(self, mock_service):
        mock_service.check_copilot_pr_completion = AsyncMock(
            return_value={"copilot_finished": True, "pr_number": 10, "id": "PR_N"}
        )
        mock_service.has_copilot_reviewed_pr = AsyncMock(return_value=False)
        mock_service.request_copilot_review = AsyncMock(return_value=False)

        result = await ensure_copilot_review_requested("tok", "o", "r", 42, "my task")
        assert result is not None
        assert result["status"] == "error"

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    async def test_exception_returns_none(self, mock_service):
        mock_service.check_copilot_pr_completion = AsyncMock(side_effect=Exception("boom"))
        result = await ensure_copilot_review_requested("tok", "o", "r", 42, "title")
        assert result is None


# ────────────────────────────────────────────────────────────────────
# check_in_review_issues_for_copilot_review  (~41 uncovered lines)
# ────────────────────────────────────────────────────────────────────


class TestCheckInReviewIssues:
    """Tests for check_in_review_issues_for_copilot_review."""

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.completion.ensure_copilot_review_requested")
    @patch("src.services.copilot_polling.github_projects_service")
    async def test_no_in_review_tasks(self, mock_service, mock_ensure):
        task = MagicMock(status="In Progress", issue_number=1)
        mock_service.get_project_items = AsyncMock(return_value=[task])

        results = await check_in_review_issues_for_copilot_review("tok", "P1", "o", "r")
        assert results == []
        mock_ensure.assert_not_awaited()

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.completion.ensure_copilot_review_requested")
    @patch("src.services.copilot_polling.github_projects_service")
    async def test_processes_in_review_tasks(self, mock_service, mock_ensure):
        task = MagicMock(
            status="In Review",
            issue_number=42,
            repository_owner="o",
            repository_name="r",
            title="My Task",
        )
        mock_service.get_project_items = AsyncMock(return_value=[task])
        mock_ensure.return_value = {"action": "copilot_review_requested"}

        results = await check_in_review_issues_for_copilot_review("tok", "P1", "o", "r")
        assert len(results) == 1
        mock_ensure.assert_awaited_once()

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.completion.ensure_copilot_review_requested")
    @patch("src.services.copilot_polling.github_projects_service")
    async def test_none_results_filtered_out(self, mock_service, mock_ensure):
        task = MagicMock(
            status="In Review",
            issue_number=42,
            repository_owner="o",
            repository_name="r",
            title="T",
        )
        mock_service.get_project_items = AsyncMock(return_value=[task])
        mock_ensure.return_value = None  # already processed

        results = await check_in_review_issues_for_copilot_review("tok", "P1", "o", "r")
        assert results == []

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.github_projects_service")
    async def test_exception_returns_empty(self, mock_service):
        mock_service.get_project_items = AsyncMock(side_effect=Exception("err"))
        results = await check_in_review_issues_for_copilot_review("tok", "P1", "o", "r")
        assert results == []

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.completion.ensure_copilot_review_requested")
    @patch("src.services.copilot_polling.github_projects_service")
    async def test_skips_tasks_without_issue_number(self, mock_service, mock_ensure):
        task = MagicMock(status="In Review", issue_number=None)
        mock_service.get_project_items = AsyncMock(return_value=[task])
        results = await check_in_review_issues_for_copilot_review("tok", "P1", "o", "r")
        assert results == []
        mock_ensure.assert_not_awaited()


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
        mock_service._check_copilot_finished_events = Mock(return_value=False)
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
        mock_service._check_copilot_finished_events = Mock(return_value=False)
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
        """SHA unchanged but Copilot unassigned → True (agent finished w/o changes)."""
        mock_service.get_pull_request = AsyncMock(
            return_value={
                "is_draft": True,
                "state": "OPEN",
                "last_commit": {"sha": "same_sha"},
            }
        )
        mock_service.get_pr_timeline_events = AsyncMock(return_value=[])
        mock_service._check_copilot_finished_events = Mock(return_value=False)
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
        assert result is True

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
        mock_service._check_copilot_finished_events = Mock(return_value=False)
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
        mock_service._check_copilot_finished_events = Mock(return_value=False)
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
        mock_service._check_copilot_finished_events = Mock(return_value=False)
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
        mock_service._check_copilot_finished_events = Mock(return_value=False)
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
        from src.services.copilot_polling import _polling_state

        _polling_state.is_running = False
        _polling_state.poll_count = 0
        _polling_state.errors_count = 0
        _polling_state.last_error = None
        _polling_state.last_poll_time = None
        yield
        _polling_state.is_running = False

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
