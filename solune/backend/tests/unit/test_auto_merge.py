"""Unit tests for _attempt_auto_merge() and related auto-merge logic."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from src.services.copilot_polling.auto_merge import (
    AutoMergeResult,
    _attempt_auto_merge,
    dispatch_devops_agent,
)


@pytest.fixture()
def mock_service():
    """Mock the GitHub projects service used by auto_merge."""
    with patch("src.services.copilot_polling.github_projects_service") as svc:
        yield svc


@pytest.fixture()
def mock_discover():
    """Mock _discover_main_pr_for_review."""
    with patch(
        "src.services.copilot_polling.helpers._discover_main_pr_for_review",
        new_callable=AsyncMock,
    ) as discover:
        yield discover


@pytest.fixture()
def mock_ws():
    """Mock the WebSocket connection manager."""
    with patch("src.services.copilot_polling.connection_manager") as ws:
        ws.broadcast_to_project = AsyncMock()
        yield ws


class TestAttemptAutoMerge:
    """Tests for _attempt_auto_merge()."""

    @pytest.mark.asyncio
    async def test_success_path(self, mock_service, mock_discover):
        """CI passes, PR mergeable, squash merge succeeds → merged."""
        mock_discover.return_value = {
            "pr_number": 42,
            "pr_id": "PR_node_42",
            "head_ref": "feature-branch",
            "is_draft": False,
        }
        mock_service.get_check_runs_for_ref = AsyncMock(
            return_value=[
                {"status": "completed", "conclusion": "success", "name": "ci"},
            ]
        )
        mock_service.get_pr_mergeable_state = AsyncMock(return_value="MERGEABLE")
        mock_service.merge_pull_request = AsyncMock(
            return_value={"merged": True, "merge_commit": "abc123def456"}
        )

        result = await _attempt_auto_merge(
            access_token="token",
            owner="owner",
            repo="repo",
            issue_number=10,
        )

        assert result.status == "merged"
        assert result.pr_number == 42
        assert result.merge_commit == "abc123def456"
        mock_service.merge_pull_request.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_ci_failure_returns_devops_needed(self, mock_service, mock_discover):
        """CI failure → devops_needed."""
        mock_discover.return_value = {
            "pr_number": 42,
            "pr_id": "PR_node_42",
            "head_ref": "feature-branch",
            "is_draft": False,
        }
        mock_service.get_check_runs_for_ref = AsyncMock(
            return_value=[
                {
                    "status": "completed",
                    "conclusion": "failure",
                    "name": "ci-test",
                },
            ]
        )

        result = await _attempt_auto_merge(
            access_token="token",
            owner="owner",
            repo="repo",
            issue_number=10,
        )

        assert result.status == "devops_needed"
        assert result.pr_number == 42
        assert result.context is not None
        assert result.context["reason"] == "ci_failure"

    @pytest.mark.asyncio
    async def test_conflicting_returns_devops_needed(self, mock_service, mock_discover):
        """CONFLICTING mergeability state → devops_needed."""
        mock_discover.return_value = {
            "pr_number": 42,
            "pr_id": "PR_node_42",
            "head_ref": "feature-branch",
            "is_draft": False,
        }
        mock_service.get_check_runs_for_ref = AsyncMock(
            return_value=[
                {"status": "completed", "conclusion": "success", "name": "ci"},
            ]
        )
        mock_service.get_pr_mergeable_state = AsyncMock(return_value="CONFLICTING")

        result = await _attempt_auto_merge(
            access_token="token",
            owner="owner",
            repo="repo",
            issue_number=10,
        )

        assert result.status == "devops_needed"
        assert result.context is not None
        assert result.context["reason"] == "conflicting"

    @pytest.mark.asyncio
    async def test_merge_api_failure_returns_merge_failed(self, mock_service, mock_discover):
        """Merge API call fails → merge_failed."""
        mock_discover.return_value = {
            "pr_number": 42,
            "pr_id": "PR_node_42",
            "head_ref": "feature-branch",
            "is_draft": False,
        }
        mock_service.get_check_runs_for_ref = AsyncMock(
            return_value=[
                {"status": "completed", "conclusion": "success", "name": "ci"},
            ]
        )
        mock_service.get_pr_mergeable_state = AsyncMock(return_value="MERGEABLE")
        mock_service.merge_pull_request = AsyncMock(side_effect=Exception("API error"))

        result = await _attempt_auto_merge(
            access_token="token",
            owner="owner",
            repo="repo",
            issue_number=10,
        )

        assert result.status == "merge_failed"
        assert result.pr_number == 42
        assert "API error" in (result.error or "")

    @pytest.mark.asyncio
    async def test_draft_pr_marked_ready(self, mock_service, mock_discover):
        """Draft PR should be marked ready-for-review before merge."""
        mock_discover.return_value = {
            "pr_number": 42,
            "pr_id": "PR_node_42",
            "head_ref": "feature-branch",
            "is_draft": True,
        }
        mock_service.mark_pr_ready_for_review = AsyncMock(return_value=True)
        mock_service.get_check_runs_for_ref = AsyncMock(
            return_value=[
                {"status": "completed", "conclusion": "success", "name": "ci"},
            ]
        )
        mock_service.get_pr_mergeable_state = AsyncMock(return_value="MERGEABLE")
        mock_service.merge_pull_request = AsyncMock(
            return_value={"merged": True, "merge_commit": "abc123"}
        )

        result = await _attempt_auto_merge(
            access_token="token",
            owner="owner",
            repo="repo",
            issue_number=10,
        )

        assert result.status == "merged"
        mock_service.mark_pr_ready_for_review.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_no_pr_found_returns_merge_failed(self, mock_service, mock_discover):
        """No main PR found → merge_failed."""
        mock_discover.return_value = None

        result = await _attempt_auto_merge(
            access_token="token",
            owner="owner",
            repo="repo",
            issue_number=10,
        )

        assert result.status == "merge_failed"
        assert "No main PR found" in (result.error or "")

    @pytest.mark.asyncio
    async def test_pending_checks_returns_retry_later(self, mock_service, mock_discover):
        """Checks still running → retry_later (not devops_needed)."""
        mock_discover.return_value = {
            "pr_number": 42,
            "pr_id": "PR_node_42",
            "head_ref": "feature-branch",
            "is_draft": False,
        }
        mock_service.get_check_runs_for_ref = AsyncMock(
            return_value=[
                {"status": "in_progress", "conclusion": None, "name": "ci"},
            ]
        )

        result = await _attempt_auto_merge(
            access_token="token",
            owner="owner",
            repo="repo",
            issue_number=10,
        )

        assert result.status == "retry_later"
        assert result.context is not None
        assert result.context["reason"] == "checks_pending"

    @pytest.mark.asyncio
    async def test_missing_head_ref_returns_retry_later(self, mock_service, mock_discover):
        """Missing head_ref → retry_later (fail closed)."""
        mock_discover.return_value = {
            "pr_number": 42,
            "pr_id": "PR_node_42",
            "head_ref": "",
            "is_draft": False,
        }

        result = await _attempt_auto_merge(
            access_token="token",
            owner="owner",
            repo="repo",
            issue_number=10,
        )

        assert result.status == "retry_later"
        assert result.context is not None
        assert result.context["reason"] == "ci_status_unavailable"

    @pytest.mark.asyncio
    async def test_check_runs_fetch_failure_returns_retry_later(self, mock_service, mock_discover):
        """Failed to fetch check runs → retry_later (fail closed)."""
        mock_discover.return_value = {
            "pr_number": 42,
            "pr_id": "PR_node_42",
            "head_ref": "feature-branch",
            "is_draft": False,
        }
        mock_service.get_check_runs_for_ref = AsyncMock(return_value=None)

        result = await _attempt_auto_merge(
            access_token="token",
            owner="owner",
            repo="repo",
            issue_number=10,
        )

        assert result.status == "retry_later"
        assert result.context is not None
        assert result.context["reason"] == "ci_status_unavailable"

    @pytest.mark.asyncio
    async def test_unknown_mergeability_returns_retry_later(self, mock_service, mock_discover):
        """UNKNOWN mergeability → retry_later (not devops_needed)."""
        mock_discover.return_value = {
            "pr_number": 42,
            "pr_id": "PR_node_42",
            "head_ref": "feature-branch",
            "is_draft": False,
        }
        mock_service.get_check_runs_for_ref = AsyncMock(
            return_value=[
                {"status": "completed", "conclusion": "success", "name": "ci"},
            ]
        )
        mock_service.get_pr_mergeable_state = AsyncMock(return_value="UNKNOWN")

        result = await _attempt_auto_merge(
            access_token="token",
            owner="owner",
            repo="repo",
            issue_number=10,
        )

        assert result.status == "retry_later"
        assert result.context is not None
        assert result.context["reason"] == "unknown_mergeability"


class TestDispatchDevopsAgent:
    """Tests for dispatch_devops_agent()."""

    @pytest.mark.asyncio
    async def test_dispatch_succeeds(self, mock_ws, mock_service):
        """First dispatch should succeed."""
        mock_service.get_issue_node_and_project_item = AsyncMock(
            return_value=("ISSUE_NODE_ID", "ITEM_ID")
        )
        mock_service.assign_copilot_to_issue = AsyncMock(return_value=True)
        metadata: dict = {}

        result = await dispatch_devops_agent(
            access_token="token",
            owner="owner",
            repo="repo",
            issue_number=10,
            pipeline_metadata=metadata,
            project_id="PVT_123",
        )

        assert result is True
        assert metadata["devops_active"] is True
        assert metadata["devops_attempts"] == 1
        mock_service.assign_copilot_to_issue.assert_awaited_once()
        call_kwargs = mock_service.assign_copilot_to_issue.call_args[1]
        assert call_kwargs["custom_agent"] == "devops"

    @pytest.mark.asyncio
    async def test_dedup_skips_when_active(self, mock_ws):
        """Should skip dispatch when DevOps is already active."""
        metadata: dict = {"devops_active": True, "devops_attempts": 1}

        result = await dispatch_devops_agent(
            access_token="token",
            owner="owner",
            repo="repo",
            issue_number=10,
            pipeline_metadata=metadata,
            project_id="PVT_123",
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_retry_cap(self, mock_ws):
        """Should not dispatch after 2 attempts."""
        metadata: dict = {"devops_active": False, "devops_attempts": 2}

        result = await dispatch_devops_agent(
            access_token="token",
            owner="owner",
            repo="repo",
            issue_number=10,
            pipeline_metadata=metadata,
            project_id="PVT_123",
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_broadcasts_devops_triggered(self, mock_ws, mock_service):
        """Should broadcast devops_triggered event."""
        mock_service.get_issue_node_and_project_item = AsyncMock(
            return_value=("ISSUE_NODE_ID", "ITEM_ID")
        )
        mock_service.assign_copilot_to_issue = AsyncMock(return_value=True)
        metadata: dict = {}

        await dispatch_devops_agent(
            access_token="token",
            owner="owner",
            repo="repo",
            issue_number=10,
            pipeline_metadata=metadata,
            project_id="PVT_123",
        )

        mock_ws.broadcast_to_project.assert_awaited_once()
        call_args = mock_ws.broadcast_to_project.call_args
        assert call_args[0][1]["type"] == "devops_triggered"


class TestAutoMergeResult:
    """Tests for AutoMergeResult dataclass."""

    def test_merged_result(self):
        result = AutoMergeResult(status="merged", pr_number=42, merge_commit="abc123")
        assert result.status == "merged"
        assert result.pr_number == 42
        assert result.merge_commit == "abc123"
        assert result.error is None

    def test_devops_needed_result(self):
        result = AutoMergeResult(
            status="devops_needed",
            pr_number=42,
            context={"reason": "ci_failure"},
        )
        assert result.status == "devops_needed"
        assert result.context is not None

    def test_merge_failed_result(self):
        result = AutoMergeResult(status="merge_failed", error="Branch protection")
        assert result.status == "merge_failed"
        assert result.error == "Branch protection"
