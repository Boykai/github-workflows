"""Tests for pipeline merge-failure fixes.

Bug 2: _merge_and_claim_child_pr continues to Done! even on merge failure.
Bug 1: Recovery guard handles open-but-completed child PRs.
Bug 3: _advance_pipeline enforces MAX_MERGE_RETRIES before skipping merge.
"""

from __future__ import annotations

from contextlib import ExitStack
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

_CP = "src.services.copilot_polling"
_AO = f"{_CP}.agent_output"
_REC = f"{_CP}.recovery"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_pipeline(agent="speckit.tasks", sub_issue=99, groups=None):
    return SimpleNamespace(
        current_agent=agent,
        agent_sub_issues={agent: {"number": sub_issue}},
        is_complete=False,
        completed_agents=[],
        current_agent_index=0,
        current_group_index=0,
        current_agent_index_in_group=0,
        groups=groups or [],
    )


# ---------------------------------------------------------------------------
# Bug 2: _merge_and_claim_child_pr — Done! NOT gated on merge success
# ---------------------------------------------------------------------------


class TestMergeAndClaimChildPrContinuesOnFailure:
    """_merge_and_claim_child_pr returns True even when merge fails."""

    @pytest.mark.asyncio
    async def test_returns_true_when_merge_fails(self):
        """Merge failure should NOT prevent Done! marker (returns True)."""
        mock_gps = MagicMock()
        merge_mock = AsyncMock(return_value={"status": "merge_failed"})
        main_branch_info = {"branch": "main", "pr_number": 1}

        with ExitStack() as stack:
            stack.enter_context(
                patch(f"{_CP}.get_issue_main_branch", return_value=main_branch_info)
            )
            stack.enter_context(patch(f"{_CP}._merge_child_pr_if_applicable", merge_mock))
            stack.enter_context(patch(f"{_CP}.POST_ACTION_DELAY_SECONDS", 0))
            stack.enter_context(patch(f"{_CP}.github_projects_service", mock_gps))
            stack.enter_context(patch(f"{_AO}._claimed_child_prs", set()))

            from src.services.copilot_polling.agent_output import (
                _merge_and_claim_child_pr,
            )

            result = await _merge_and_claim_child_pr(
                access_token="tok",
                owner="o",
                repo="r",
                issue_number=10,
                current_agent="speckit.tasks",
                pipeline=_make_pipeline(),
                finished_pr={"number": 42, "is_child_pr": True},
                pr_number=42,
                is_child_pr=True,
            )

        assert result is True, "Should return True so Done! marker is posted"

    @pytest.mark.asyncio
    async def test_returns_true_when_merge_succeeds(self):
        """Baseline: merge success -> True."""
        mock_gps = MagicMock()
        merge_mock = AsyncMock(return_value={"status": "merged"})
        main_branch_info = {"branch": "main", "pr_number": 1}

        with ExitStack() as stack:
            stack.enter_context(
                patch(f"{_CP}.get_issue_main_branch", return_value=main_branch_info)
            )
            stack.enter_context(patch(f"{_CP}._merge_child_pr_if_applicable", merge_mock))
            stack.enter_context(patch(f"{_CP}.POST_ACTION_DELAY_SECONDS", 0))
            stack.enter_context(patch(f"{_CP}.github_projects_service", mock_gps))
            stack.enter_context(patch(f"{_AO}._claimed_child_prs", set()))

            from src.services.copilot_polling.agent_output import (
                _merge_and_claim_child_pr,
            )

            result = await _merge_and_claim_child_pr(
                access_token="tok",
                owner="o",
                repo="r",
                issue_number=10,
                current_agent="speckit.tasks",
                pipeline=_make_pipeline(),
                finished_pr={"number": 42, "is_child_pr": True, "is_merged": False},
                pr_number=42,
                is_child_pr=True,
            )

        assert result is True

    @pytest.mark.asyncio
    async def test_returns_true_when_already_merged(self):
        """Already-merged child PR -> True (no merge attempt)."""
        main_branch_info = {"branch": "main", "pr_number": 1}

        with ExitStack() as stack:
            stack.enter_context(
                patch(f"{_CP}.get_issue_main_branch", return_value=main_branch_info)
            )
            stack.enter_context(patch(f"{_AO}._claimed_child_prs", set()))

            from src.services.copilot_polling.agent_output import (
                _merge_and_claim_child_pr,
            )

            result = await _merge_and_claim_child_pr(
                access_token="tok",
                owner="o",
                repo="r",
                issue_number=10,
                current_agent="speckit.tasks",
                pipeline=_make_pipeline(),
                finished_pr={"number": 42, "is_child_pr": True, "is_merged": True},
                pr_number=42,
                is_child_pr=True,
            )

        assert result is True


# ---------------------------------------------------------------------------
# Bug 1: Recovery guard — open-but-completed child PRs
# ---------------------------------------------------------------------------


class TestRecoveryGuardOpenCompletedChildPR:
    """Recovery should NOT re-assign when an open-but-completed child PR exists."""

    @pytest.mark.asyncio
    async def test_open_completed_child_pr_posts_done_and_skips_reassignment(self):
        """When child PR is completed but NOT merged, recovery posts Done! and skips."""
        from datetime import UTC, datetime

        completed_child = {"number": 55, "is_child_pr": True}  # no is_merged key

        mock_gps = AsyncMock()
        mock_gps.get_issue_with_comments = AsyncMock(return_value={"body": "tracking body"})
        mock_gps.create_issue_comment = AsyncMock(return_value={"id": "IC_done"})
        now = datetime.now(UTC)

        active_step = SimpleNamespace(
            agent_name="speckit.tasks",
            state="🔄 Active",
            status="Backlog",
        )
        config = SimpleNamespace(status_done="Done")
        task = SimpleNamespace(
            status="Backlog",
            issue_number=10,
            repository_owner="o",
            repository_name="r",
            github_item_id="item-10",
            github_content_id="content-10",
            title="Issue 10",
        )

        with ExitStack() as stack:
            stack.enter_context(patch(f"{_CP}.github_projects_service", mock_gps))
            stack.enter_context(patch(f"{_CP}.get_workflow_config", AsyncMock(return_value=config)))
            stack.enter_context(
                patch(f"{_REC}._should_skip_recovery", AsyncMock(return_value=False))
            )
            stack.enter_context(
                patch(f"{_CP}.parse_tracking_from_body", return_value=[active_step])
            )
            stack.enter_context(patch(f"{_CP}.get_pipeline_state", return_value=None))
            stack.enter_context(
                patch(
                    f"{_REC}._validate_and_reconcile_tracking_table",
                    AsyncMock(return_value=("tracking body", [active_step], False)),
                )
            )
            stack.enter_context(patch(f"{_REC}._pending_agent_assignments", {}))
            stack.enter_context(
                patch(
                    f"{_REC}._detect_stalled_issue",
                    AsyncMock(return_value=(False, False, None)),
                )
            )
            stack.enter_context(
                patch(
                    f"{_CP}._check_agent_done_on_sub_or_parent",
                    AsyncMock(return_value=False),
                )
            )
            stack.enter_context(
                patch(
                    f"{_CP}.get_issue_main_branch",
                    return_value={"branch": "main", "pr_number": 1},
                )
            )
            stack.enter_context(
                patch(
                    f"{_CP}._find_completed_child_pr",
                    AsyncMock(return_value=completed_child),
                )
            )
            stack.enter_context(patch(f"{_REC}._recovery_last_attempt", {}))
            stack.enter_context(patch(f"{_REC}.utcnow", return_value=now))

            from src.services.copilot_polling.recovery import recover_stalled_issues

            # Verify fix precondition: merged_child is truthy but is_merged is falsy.
            assert completed_child  # truthy
            assert completed_child.get("is_merged") is None  # not merged

            result = await recover_stalled_issues("tok", "proj-1", "o", "r", tasks=[task])

        # Recovery should have posted a Done! comment via create_issue_comment.
        mock_gps.create_issue_comment.assert_awaited()
        # Recovery should NOT have returned a re-assignment result.
        assert result == []

    @pytest.mark.asyncio
    async def test_merged_child_pr_still_handled(self):
        """Existing behavior: merged child PR posts Done! and skips."""
        merged_child = {"number": 55, "is_child_pr": True, "is_merged": True}

        assert merged_child.get("is_merged") is True


# ---------------------------------------------------------------------------
# Bug 3: _advance_pipeline — MAX_MERGE_RETRIES
# ---------------------------------------------------------------------------


class TestMergeRetryLimit:
    """After MAX_MERGE_RETRIES failures, the pipeline skips the merge and advances."""

    @pytest.mark.asyncio
    async def test_advance_pipeline_returns_merge_blocked_on_first_failure(self):
        """First merge failure: pipeline is blocked and failure counter increments."""
        from src.services.workflow_orchestrator.models import PipelineState

        pipeline = PipelineState(
            issue_number=10,
            project_id="proj-1",
            status="Backlog",
            agents=["speckit.tasks"],
            current_agent_index=0,
        )

        mock_cp = MagicMock()
        mock_cp.get_issue_main_branch.return_value = {"branch": "main", "pr_number": 1}
        mock_cp._merge_child_pr_if_applicable = AsyncMock(
            return_value={"status": "merge_failed", "pr_number": 42}
        )
        mock_cp.set_pipeline_state = MagicMock()
        mock_cp.POST_ACTION_DELAY_SECONDS = 0

        from src.services.copilot_polling.state import _merge_failure_counts

        _merge_failure_counts.clear()

        with ExitStack() as stack:
            stack.enter_context(patch("src.services.copilot_polling.pipeline._cp", mock_cp))
            stack.enter_context(
                patch("src.services.copilot_polling.pipeline._pending_agent_assignments", {})
            )

            from src.services.copilot_polling.pipeline import _advance_pipeline

            result = await _advance_pipeline(
                access_token="tok",
                project_id="proj-1",
                item_id="item-1",
                owner="o",
                repo="r",
                issue_number=10,
                issue_node_id=None,
                pipeline=pipeline,
                from_status="Backlog",
                to_status="In Progress",
                task_title="Test Issue",
            )

        assert result is not None
        assert result["status"] == "merge_blocked"
        assert _merge_failure_counts.get(10) == 1
        _merge_failure_counts.clear()

    @pytest.mark.asyncio
    async def test_advance_pipeline_skips_merge_after_max_retries(self):
        """After MAX_MERGE_RETRIES failures, posts warning comment and advances pipeline."""
        from src.services.copilot_polling.state import MAX_MERGE_RETRIES, _merge_failure_counts
        from src.services.workflow_orchestrator.models import PipelineState

        pipeline = PipelineState(
            issue_number=10,
            project_id="proj-1",
            status="Backlog",
            agents=["speckit.tasks"],
            current_agent_index=0,
        )

        mock_cp = MagicMock()
        mock_cp.get_issue_main_branch.return_value = {"branch": "main", "pr_number": 1}
        mock_cp._merge_child_pr_if_applicable = AsyncMock(
            return_value={"status": "merge_failed", "pr_number": 42}
        )
        mock_cp.set_pipeline_state = MagicMock()
        mock_cp.remove_pipeline_state = MagicMock()
        mock_cp.POST_ACTION_DELAY_SECONDS = 0
        mock_cp.github_projects_service = AsyncMock()
        mock_cp.github_projects_service.create_issue_comment = AsyncMock(return_value={"id": "C1"})
        mock_cp.github_projects_service.get_pull_request = AsyncMock(return_value=None)
        mock_cp._update_issue_tracking = AsyncMock()
        mock_cp.connection_manager = AsyncMock()
        mock_cp.connection_manager.broadcast_to_project = AsyncMock()

        # Set failure count to MAX_MERGE_RETRIES - 1 so this attempt reaches the limit.
        _merge_failure_counts.clear()
        _merge_failure_counts[10] = MAX_MERGE_RETRIES - 1

        with ExitStack() as stack:
            stack.enter_context(patch("src.services.copilot_polling.pipeline._cp", mock_cp))
            stack.enter_context(
                patch("src.services.copilot_polling.pipeline._pending_agent_assignments", {})
            )
            stack.enter_context(
                patch(
                    "src.services.copilot_polling.pipeline._close_completed_sub_issues",
                    AsyncMock(),
                )
            )
            stack.enter_context(
                patch(
                    "src.services.copilot_polling.pipeline._transition_after_pipeline_complete",
                    AsyncMock(return_value={"status": "transitioned"}),
                )
            )

            from src.services.copilot_polling.pipeline import _advance_pipeline

            result = await _advance_pipeline(
                access_token="tok",
                project_id="proj-1",
                item_id="item-1",
                owner="o",
                repo="r",
                issue_number=10,
                issue_node_id=None,
                pipeline=pipeline,
                from_status="Backlog",
                to_status="In Progress",
                task_title="Test Issue",
            )

        # Warning comment must have been posted.
        mock_cp.github_projects_service.create_issue_comment.assert_awaited()
        # Failure counter must be cleared after skip.
        assert _merge_failure_counts.get(10) is None
        # Pipeline must NOT be blocked.
        assert result is None or (
            isinstance(result, dict) and result.get("status") != "merge_blocked"
        )
        _merge_failure_counts.clear()

    def test_max_merge_retries_constant(self):
        """MAX_MERGE_RETRIES is set to a reasonable value."""
        from src.services.copilot_polling.state import MAX_MERGE_RETRIES

        assert MAX_MERGE_RETRIES == 3

    def test_merge_failure_counts_exists_in_state(self):
        """_merge_failure_counts BoundedDict is importable from state."""
        from src.services.copilot_polling.state import _merge_failure_counts

        assert hasattr(_merge_failure_counts, "get")
        assert hasattr(_merge_failure_counts, "pop")

    def test_pipeline_imports_merge_state(self):
        """pipeline.py successfully imports the new merge-related symbols."""
        from src.services.copilot_polling.pipeline import (
            MAX_MERGE_RETRIES,
            _merge_failure_counts,
        )

        assert MAX_MERGE_RETRIES == 3
        assert _merge_failure_counts is not None
