"""Tests for the shared GitHub commit workflow — branch → commit → PR pipeline.

Covers:
- Full successful workflow (all 6 steps)
- Partial failures (each step failing independently)
- Optional step skipping (no issue, no project board)
- Edge cases (empty files, create_branch returns None)
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from src.services.github_commit_workflow import CommitWorkflowResult, commit_files_workflow

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

REPO_INFO = {
    "repository_id": "R_abc123",
    "head_oid": "abc123def456",
    "default_branch": "main",
}

ISSUE_RESPONSE = {
    "id": 300042,
    "number": 42,
    "node_id": "I_abc",
    "html_url": "https://github.com/owner/repo/issues/42",
}

PR_RESPONSE = {
    "number": 99,
    "url": "https://github.com/owner/repo/pull/99",
}

COMMON_KWARGS = {
    "access_token": "test-token",
    "owner": "owner",
    "repo": "repo",
    "branch_name": "feat/test-branch",
    "files": [{"path": "README.md", "content": "# Hello"}],
    "commit_message": "chore: add file",
    "pr_title": "Add file",
    "pr_body": "Adds a readme",
}


@pytest.fixture
def mock_svc():
    """Provide an AsyncMock of github_projects_service for workflow tests."""
    svc = AsyncMock()
    svc.get_repository_info.return_value = REPO_INFO
    svc.create_issue.return_value = ISSUE_RESPONSE
    svc.create_branch.return_value = "ref_id_123"
    svc.commit_files.return_value = "new_commit_oid"
    svc.create_pull_request.return_value = PR_RESPONSE
    svc.add_issue_to_project.return_value = "PVTI_new"
    svc.update_item_status_by_name.return_value = None
    return svc


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------


class TestCommitWorkflowSuccess:
    """Full successful workflow — all steps complete."""

    async def test_full_workflow_without_issue(self, mock_svc):
        """Branch → commit → PR succeeds when no issue is requested."""
        with patch("src.services.github_commit_workflow.github_projects_service", mock_svc):
            result = await commit_files_workflow(**COMMON_KWARGS)

        assert result.success is True
        assert result.branch_name == "feat/test-branch"
        assert result.commit_oid == "new_commit_oid"
        assert result.pr_number == 99
        assert result.pr_url == "https://github.com/owner/repo/pull/99"
        assert result.issue_number is None
        assert result.errors == []

        mock_svc.get_repository_info.assert_awaited_once()
        mock_svc.create_issue.assert_not_awaited()
        mock_svc.create_branch.assert_awaited_once()
        mock_svc.commit_files.assert_awaited_once()
        mock_svc.create_pull_request.assert_awaited_once()

    async def test_full_workflow_with_issue_and_project(self, mock_svc):
        """All 6 steps complete: issue → branch → commit → PR → board."""
        with patch("src.services.github_commit_workflow.github_projects_service", mock_svc):
            result = await commit_files_workflow(
                **COMMON_KWARGS,
                issue_title="Tracking issue",
                issue_body="Body text",
                issue_labels=["enhancement"],
                project_id="PVT_proj",
                target_status="In Progress",
            )

        assert result.success is True
        assert result.issue_number == 42
        assert result.issue_node_id == "I_abc"
        assert result.pr_number == 99
        assert result.errors == []

        # PR body should include "Closes #42"
        call_kwargs = mock_svc.create_pull_request.call_args
        assert "Closes #42" in call_kwargs.kwargs.get("body", call_kwargs[1].get("body", ""))

        mock_svc.add_issue_to_project.assert_awaited_once()
        mock_svc.update_item_status_by_name.assert_awaited_once()

    async def test_workflow_with_delete_files(self, mock_svc):
        """Deletion paths are forwarded to commit_files."""
        with patch("src.services.github_commit_workflow.github_projects_service", mock_svc):
            result = await commit_files_workflow(
                **COMMON_KWARGS,
                delete_files=["old-file.txt"],
            )

        assert result.success is True
        call_kwargs = mock_svc.commit_files.call_args
        assert call_kwargs.kwargs.get("deletions") == ["old-file.txt"]


# ---------------------------------------------------------------------------
# Step 1 failure — get_repository_info
# ---------------------------------------------------------------------------


class TestStep1RepositoryInfoFailure:
    async def test_repo_info_failure_aborts(self, mock_svc):
        """Workflow aborts immediately if repo info cannot be fetched."""
        mock_svc.get_repository_info.side_effect = RuntimeError("API unreachable")

        with patch("src.services.github_commit_workflow.github_projects_service", mock_svc):
            result = await commit_files_workflow(**COMMON_KWARGS)

        assert result.success is False
        assert any("Get repository info failed" in e for e in result.errors)
        mock_svc.create_branch.assert_not_awaited()


# ---------------------------------------------------------------------------
# Step 2 failure — create_issue (optional, non-fatal)
# ---------------------------------------------------------------------------


class TestStep2CreateIssueFailure:
    async def test_issue_failure_is_non_fatal(self, mock_svc):
        """Issue creation failure does not block the rest of the workflow."""
        mock_svc.create_issue.side_effect = RuntimeError("Rate limited")

        with patch("src.services.github_commit_workflow.github_projects_service", mock_svc):
            result = await commit_files_workflow(
                **COMMON_KWARGS,
                issue_title="Track this",
                issue_body="Body",
            )

        assert result.success is True
        assert result.issue_number is None
        assert any("Create issue failed" in e for e in result.errors)
        # PR should still be created
        mock_svc.create_pull_request.assert_awaited_once()
        # PR body should NOT contain "Closes #None"
        call_kwargs = mock_svc.create_pull_request.call_args
        pr_body = call_kwargs.kwargs.get("body", call_kwargs[1].get("body", ""))
        assert "Closes #" not in pr_body


# ---------------------------------------------------------------------------
# Step 3 failure — create_branch
# ---------------------------------------------------------------------------


class TestStep3CreateBranchFailure:
    async def test_branch_creation_failure_aborts(self, mock_svc):
        """Workflow aborts if branch creation raises."""
        mock_svc.create_branch.side_effect = RuntimeError("Branch exists")

        with patch("src.services.github_commit_workflow.github_projects_service", mock_svc):
            result = await commit_files_workflow(**COMMON_KWARGS)

        assert result.success is False
        assert any("Create branch failed" in e for e in result.errors)
        mock_svc.commit_files.assert_not_awaited()

    async def test_branch_returns_none_aborts(self, mock_svc):
        """Workflow aborts if create_branch returns None."""
        mock_svc.create_branch.return_value = None

        with patch("src.services.github_commit_workflow.github_projects_service", mock_svc):
            result = await commit_files_workflow(**COMMON_KWARGS)

        assert result.success is False
        assert any("create_branch returned None" in e for e in result.errors)


# ---------------------------------------------------------------------------
# Step 4 failure — commit_files
# ---------------------------------------------------------------------------


class TestStep4CommitFilesFailure:
    async def test_commit_failure_aborts(self, mock_svc):
        """Workflow aborts if commit raises."""
        mock_svc.commit_files.side_effect = RuntimeError("Conflict")

        with patch("src.services.github_commit_workflow.github_projects_service", mock_svc):
            result = await commit_files_workflow(**COMMON_KWARGS)

        assert result.success is False
        assert any("Commit files failed" in e for e in result.errors)
        mock_svc.create_pull_request.assert_not_awaited()

    async def test_commit_returns_none_aborts(self, mock_svc):
        """Workflow aborts if commit_files returns None."""
        mock_svc.commit_files.return_value = None

        with patch("src.services.github_commit_workflow.github_projects_service", mock_svc):
            result = await commit_files_workflow(**COMMON_KWARGS)

        assert result.success is False
        assert any("commit_files returned None" in e for e in result.errors)


# ---------------------------------------------------------------------------
# Step 5 failure — create_pull_request
# ---------------------------------------------------------------------------


class TestStep5PullRequestFailure:
    async def test_pr_creation_failure_aborts(self, mock_svc):
        """Workflow aborts if PR creation raises."""
        mock_svc.create_pull_request.side_effect = RuntimeError("Server error")

        with patch("src.services.github_commit_workflow.github_projects_service", mock_svc):
            result = await commit_files_workflow(**COMMON_KWARGS)

        assert result.success is False
        assert any("Create PR failed" in e for e in result.errors)

    async def test_pr_returns_none_aborts(self, mock_svc):
        """Workflow aborts if create_pull_request returns None."""
        mock_svc.create_pull_request.return_value = None

        with patch("src.services.github_commit_workflow.github_projects_service", mock_svc):
            result = await commit_files_workflow(**COMMON_KWARGS)

        assert result.success is False
        assert any("create_pull_request returned None" in e for e in result.errors)


# ---------------------------------------------------------------------------
# Step 6 failure — add_issue_to_project (optional, non-fatal)
# ---------------------------------------------------------------------------


class TestStep6ProjectBoardFailure:
    async def test_board_add_failure_is_non_fatal(self, mock_svc):
        """Board integration failure does not mark workflow as failed."""
        mock_svc.add_issue_to_project.side_effect = RuntimeError("Project not found")

        with patch("src.services.github_commit_workflow.github_projects_service", mock_svc):
            result = await commit_files_workflow(
                **COMMON_KWARGS,
                issue_title="Track",
                issue_body="Body",
                project_id="PVT_proj",
                target_status="In Progress",
            )

        assert result.success is True
        assert any("Move issue to board failed" in e for e in result.errors)

    async def test_board_skipped_without_project_id(self, mock_svc):
        """Board step is skipped entirely when project_id is not provided."""
        with patch("src.services.github_commit_workflow.github_projects_service", mock_svc):
            result = await commit_files_workflow(
                **COMMON_KWARGS,
                issue_title="Track",
                issue_body="Body",
            )

        assert result.success is True
        mock_svc.add_issue_to_project.assert_not_awaited()

    async def test_board_skipped_when_add_returns_none(self, mock_svc):
        """Status update is skipped when add_issue_to_project returns None."""
        mock_svc.add_issue_to_project.return_value = None

        with patch("src.services.github_commit_workflow.github_projects_service", mock_svc):
            result = await commit_files_workflow(
                **COMMON_KWARGS,
                issue_title="Track",
                issue_body="Body",
                project_id="PVT_proj",
                target_status="In Progress",
            )

        assert result.success is True
        mock_svc.update_item_status_by_name.assert_not_awaited()


# ---------------------------------------------------------------------------
# Data class
# ---------------------------------------------------------------------------


class TestCommitWorkflowResult:
    def test_defaults(self):
        """CommitWorkflowResult has safe defaults."""
        r = CommitWorkflowResult()
        assert r.success is False
        assert r.branch_name is None
        assert r.commit_oid is None
        assert r.pr_number is None
        assert r.pr_url is None
        assert r.issue_number is None
        assert r.issue_node_id is None
        assert r.errors == []

    def test_with_branch(self):
        """Branch name can be set on init."""
        r = CommitWorkflowResult(branch_name="feat/x")
        assert r.branch_name == "feat/x"
        assert r.success is False
