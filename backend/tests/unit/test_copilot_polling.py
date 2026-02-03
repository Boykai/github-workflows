"""Unit tests for Copilot PR polling service."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.services.copilot_polling import (
    check_in_progress_issues,
    process_in_progress_issue,
    check_issue_for_copilot_completion,
    get_polling_status,
    _processed_issue_prs,
)


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
    yield
    _processed_issue_prs.clear()


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
    @patch("src.services.copilot_polling.process_in_progress_issue")
    async def test_filters_in_progress_with_issue_numbers(
        self, mock_process, mock_service, mock_task, mock_task_no_issue
    ):
        """Test that only in-progress issues with issue numbers are processed."""
        mock_service.get_project_items = AsyncMock(
            return_value=[mock_task, mock_task_no_issue]
        )
        mock_process.return_value = {"status": "success"}
        
        results = await check_in_progress_issues(
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
        
        with patch("src.services.copilot_polling.process_in_progress_issue") as mock_process:
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
    @patch("src.services.copilot_polling.process_in_progress_issue")
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
        
        with patch("src.services.copilot_polling.process_in_progress_issue") as mock_process:
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
        
        with patch("src.services.copilot_polling.process_in_progress_issue") as mock_process:
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
    @patch("src.services.copilot_polling.process_in_progress_issue")
    async def test_collects_all_results(self, mock_process, mock_service, mock_task):
        """Test that results from all processed issues are collected."""
        task1 = MagicMock(**{
            "github_item_id": "PVTI_1",
            "issue_number": 1,
            "repository_owner": "owner",
            "repository_name": "repo",
            "title": "Issue 1",
            "status": "In Progress",
        })
        task2 = MagicMock(**{
            "github_item_id": "PVTI_2",
            "issue_number": 2,
            "repository_owner": "owner",
            "repository_name": "repo",
            "title": "Issue 2",
            "status": "In Progress",
        })
        
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
    @patch("src.services.copilot_polling.asyncio.sleep")
    async def test_updates_status_when_copilot_pr_ready(
        self, mock_sleep, mock_service
    ):
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
    @patch("src.services.copilot_polling.asyncio.sleep")
    async def test_skips_mark_ready_when_already_not_draft(
        self, mock_sleep, mock_service
    ):
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
    @patch("src.services.copilot_polling.asyncio.sleep")
    async def test_returns_error_when_status_update_fails(
        self, mock_sleep, mock_service
    ):
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
    @patch("src.services.copilot_polling.asyncio.sleep")
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
    async def test_returns_skipped_when_not_in_progress(
        self, mock_service, mock_task
    ):
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
    async def test_processes_in_progress_issue(
        self, mock_process, mock_service, mock_task
    ):
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
