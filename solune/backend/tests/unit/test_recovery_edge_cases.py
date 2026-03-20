"""Additional edge-case coverage for recovery re-assignment flows."""

from __future__ import annotations

from contextlib import ExitStack
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

_CP = "src.services.copilot_polling"
_REC = f"{_CP}.recovery"


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _task() -> SimpleNamespace:
    return SimpleNamespace(
        repository_owner="octo",
        repository_name="repo",
        github_content_id="content-1",
        github_item_id="item-1",
    )


def _config() -> SimpleNamespace:
    return SimpleNamespace()


class TestAttemptReassignment:
    async def test_returns_none_when_agent_missing_from_status_mapping(self):
        with patch(f"{_CP}.get_agent_slugs", return_value=["other-agent"]):
            from src.services.copilot_polling.recovery import _attempt_reassignment

            result = await _attempt_reassignment(
                access_token="tok",
                project_id="proj-1",
                issue_number=42,
                task=_task(),
                agent_name="builder",
                agent_status="In Progress",
                active_step=None,
                missing=["no WIP PR found"],
                config=_config(),
                now=_utcnow(),
            )

        assert result is None

    async def test_rate_limited_reassignment_defers_after_label_update(self):
        mock_github = MagicMock()
        mock_github.update_issue_state = AsyncMock()
        mock_orchestrator = MagicMock()
        mock_orchestrator.assign_agent_for_status = AsyncMock()

        with ExitStack() as stack:
            stack.enter_context(patch(f"{_CP}.get_agent_slugs", return_value=["builder"]))
            stack.enter_context(patch(f"{_CP}.github_projects_service", mock_github))
            stack.enter_context(
                patch(f"{_CP}.get_workflow_orchestrator", return_value=mock_orchestrator)
            )
            stack.enter_context(
                patch(f"{_REC}._wait_if_rate_limited", AsyncMock(return_value=True))
            )

            from src.services.copilot_polling.recovery import _attempt_reassignment

            result = await _attempt_reassignment(
                access_token="tok",
                project_id="proj-1",
                issue_number=42,
                task=_task(),
                agent_name="builder",
                agent_status="In Progress",
                active_step=None,
                missing=["Copilot NOT assigned"],
                config=_config(),
                now=_utcnow(),
            )

        assert result is None
        mock_github.update_issue_state.assert_awaited_once()
        mock_orchestrator.assign_agent_for_status.assert_not_called()

    async def test_assignment_exception_sets_recovery_cooldown(self):
        now = _utcnow()
        recovery_last_attempt: dict[int, datetime] = {}
        mock_github = MagicMock()
        mock_github.update_issue_state = AsyncMock()
        mock_orchestrator = MagicMock()
        mock_orchestrator.assign_agent_for_status = AsyncMock(
            side_effect=RuntimeError("assign failed")
        )

        with ExitStack() as stack:
            stack.enter_context(patch(f"{_CP}.get_agent_slugs", return_value=["builder"]))
            stack.enter_context(patch(f"{_CP}.github_projects_service", mock_github))
            stack.enter_context(
                patch(f"{_CP}.get_workflow_orchestrator", return_value=mock_orchestrator)
            )
            stack.enter_context(
                patch(f"{_REC}._wait_if_rate_limited", AsyncMock(return_value=False))
            )
            stack.enter_context(patch(f"{_REC}._recovery_last_attempt", recovery_last_attempt))

            from src.services.copilot_polling.recovery import _attempt_reassignment

            result = await _attempt_reassignment(
                access_token="tok",
                project_id="proj-1",
                issue_number=42,
                task=_task(),
                agent_name="builder",
                agent_status="In Progress",
                active_step=None,
                missing=["Copilot NOT assigned"],
                config=_config(),
                now=now,
            )

        assert result is None
        assert recovery_last_attempt[42] == now

    async def test_success_records_pending_assignment_and_result_metadata(self):
        now = _utcnow()
        pending_assignments: dict[str, datetime] = {}
        recovery_last_attempt: dict[int, datetime] = {}
        mock_github = MagicMock()
        mock_github.update_issue_state = AsyncMock()
        mock_orchestrator = MagicMock()
        mock_orchestrator.assign_agent_for_status = AsyncMock(return_value=True)

        with ExitStack() as stack:
            stack.enter_context(patch(f"{_CP}.get_agent_slugs", return_value=["builder"]))
            stack.enter_context(patch(f"{_CP}.github_projects_service", mock_github))
            stack.enter_context(
                patch(f"{_CP}.get_workflow_orchestrator", return_value=mock_orchestrator)
            )
            stack.enter_context(
                patch(f"{_REC}._wait_if_rate_limited", AsyncMock(return_value=False))
            )
            stack.enter_context(patch(f"{_REC}._pending_agent_assignments", pending_assignments))
            stack.enter_context(patch(f"{_REC}._recovery_last_attempt", recovery_last_attempt))

            from src.services.copilot_polling.recovery import _attempt_reassignment

            result = await _attempt_reassignment(
                access_token="tok",
                project_id="proj-1",
                issue_number=42,
                task=_task(),
                agent_name="builder",
                agent_status="In Progress",
                active_step=SimpleNamespace(agent_name="builder"),
                missing=["no WIP PR found"],
                config=_config(),
                now=now,
            )

        assert result == {
            "status": "recovered",
            "issue_number": 42,
            "agent_name": "builder",
            "agent_status": "In Progress",
            "was_active": True,
            "missing": ["no WIP PR found"],
        }
        assert pending_assignments["42:builder"] == now
        assert recovery_last_attempt[42] == now

    async def test_false_assignment_still_records_last_attempt(self):
        now = _utcnow()
        recovery_last_attempt: dict[int, datetime] = {}
        mock_github = MagicMock()
        mock_github.update_issue_state = AsyncMock()
        mock_orchestrator = MagicMock()
        mock_orchestrator.assign_agent_for_status = AsyncMock(return_value=False)

        with ExitStack() as stack:
            stack.enter_context(patch(f"{_CP}.get_agent_slugs", return_value=["builder"]))
            stack.enter_context(patch(f"{_CP}.github_projects_service", mock_github))
            stack.enter_context(
                patch(f"{_CP}.get_workflow_orchestrator", return_value=mock_orchestrator)
            )
            stack.enter_context(
                patch(f"{_REC}._wait_if_rate_limited", AsyncMock(return_value=False))
            )
            stack.enter_context(patch(f"{_REC}._recovery_last_attempt", recovery_last_attempt))

            from src.services.copilot_polling.recovery import _attempt_reassignment

            result = await _attempt_reassignment(
                access_token="tok",
                project_id="proj-1",
                issue_number=42,
                task=_task(),
                agent_name="builder",
                agent_status="In Progress",
                active_step=None,
                missing=["no WIP PR found"],
                config=_config(),
                now=now,
            )

        assert result is None
        assert recovery_last_attempt[42] == now


class TestDetectStalledIssueEdgeCases:
    async def test_main_branch_draft_without_head_sha_counts_as_wip(self):
        mock_github = MagicMock()
        mock_github.is_copilot_assigned_to_issue = AsyncMock(return_value=True)
        mock_github.get_linked_pull_requests = AsyncMock(
            return_value=[{"number": 100, "state": "OPEN", "author": "copilot[bot]"}]
        )
        mock_github.get_pull_request = AsyncMock(
            return_value={"is_draft": True, "base_ref": "feature/42"}
        )

        with ExitStack() as stack:
            stack.enter_context(patch(f"{_CP}.github_projects_service", mock_github))
            stack.enter_context(patch(f"{_REC}._get_sub_issue_number", return_value=42))
            stack.enter_context(
                patch(
                    f"{_CP}.get_issue_main_branch",
                    return_value={"branch": "feature/42", "pr_number": 100, "head_sha": ""},
                )
            )

            from src.services.copilot_polling.recovery import _detect_stalled_issue

            assigned, has_wip, pr_number = await _detect_stalled_issue(
                "tok", "octo", "repo", 42, "builder", SimpleNamespace(agent_sub_issues={})
            )

        assert assigned is True
        assert has_wip is True
        assert pr_number == 100


class TestRecoverStalledIssues:
    async def test_bootstraps_default_config_when_missing(self):
        set_workflow_config = AsyncMock()
        mock_github = MagicMock()
        mock_github.get_project_items = AsyncMock(return_value=[])

        with ExitStack() as stack:
            stack.enter_context(patch(f"{_CP}.github_projects_service", mock_github))
            stack.enter_context(patch(f"{_CP}.get_workflow_config", AsyncMock(return_value=None)))
            stack.enter_context(
                patch(
                    f"{_CP}.WorkflowConfiguration",
                    side_effect=lambda **kwargs: SimpleNamespace(status_done="Done", **kwargs),
                )
            )
            stack.enter_context(patch(f"{_CP}.set_workflow_config", set_workflow_config))

            from src.services.copilot_polling.recovery import recover_stalled_issues

            result = await recover_stalled_issues("tok", "proj-1", "octo", "repo")

        assert result == []
        set_workflow_config.assert_awaited_once()

    async def test_done_only_issue_without_forward_transition_sets_cooldown(self):
        now = _utcnow()
        recovery_last_attempt: dict[int, datetime] = {}
        mock_github = MagicMock()
        mock_github.get_issue_with_comments = AsyncMock(return_value={"body": "tracking body"})
        task = SimpleNamespace(
            status="Backlog",
            issue_number=42,
            repository_owner="octo",
            repository_name="repo",
            github_item_id="item-42",
            github_content_id="content-42",
            title="Issue 42",
        )
        steps = [SimpleNamespace(agent_name="builder", state="✅ Done")]
        config = SimpleNamespace(status_done="Done")

        with ExitStack() as stack:
            stack.enter_context(patch(f"{_CP}.github_projects_service", mock_github))
            stack.enter_context(patch(f"{_CP}.get_workflow_config", AsyncMock(return_value=config)))
            stack.enter_context(
                patch(f"{_REC}._should_skip_recovery", AsyncMock(return_value=False))
            )
            stack.enter_context(patch(f"{_CP}.parse_tracking_from_body", return_value=steps))
            stack.enter_context(patch(f"{_CP}.get_pipeline_state", return_value=None))
            stack.enter_context(
                patch(
                    f"{_REC}._validate_and_reconcile_tracking_table",
                    AsyncMock(return_value=("tracking body", steps, False)),
                )
            )
            stack.enter_context(patch(f"{_CP}.get_next_status", return_value=None))
            stack.enter_context(patch(f"{_REC}.utcnow", return_value=now))
            stack.enter_context(patch(f"{_REC}._recovery_last_attempt", recovery_last_attempt))

            from src.services.copilot_polling.recovery import recover_stalled_issues

            result = await recover_stalled_issues("tok", "proj-1", "octo", "repo", tasks=[task])

        assert result == []
        assert recovery_last_attempt[42] == now
