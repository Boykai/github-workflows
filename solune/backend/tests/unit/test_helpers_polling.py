"""Tests for copilot_polling/helpers.py — pure functions + async helpers.

Covers:
- is_sub_issue() title/label detection
- _get_sub_issue_number() pipeline lookup + fallback
- _get_human_sub_issue_assignee() pipeline + global store lookup
- _get_sub_issue_numbers_for_issue() deduplication across sources
- _check_agent_done_on_sub_or_parent() dispatch + parent/sub fallback
- _check_human_agent_done() 3 completion signals
- _update_issue_tracking() body mutation round-trip
- _reconstruct_sub_issue_mappings() title parsing + global store persist
"""

from contextlib import ExitStack
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

# ── Patch targets ──────────────────────────────────────────────────
_GPS = "src.services.copilot_polling.github_projects_service"
_GET_SUB_ISSUES = "src.services.copilot_polling.get_issue_sub_issues"
_SET_SUB_ISSUES = "src.services.copilot_polling.set_issue_sub_issues"
_MARK_ACTIVE = "src.services.copilot_polling.mark_agent_active"
_MARK_DONE = "src.services.copilot_polling.mark_agent_done"


# ══════════════════════════════════════════════════════════════════
# Pure functions
# ══════════════════════════════════════════════════════════════════


class TestIsSubIssue:
    """is_sub_issue() — title regex + label fallback."""

    def test_title_with_bracket_prefix(self):
        from src.services.copilot_polling.helpers import is_sub_issue

        task = SimpleNamespace(title="[speckit.specify] Build widget", labels=[])
        assert is_sub_issue(task) is True

    def test_title_without_bracket_prefix(self):
        from src.services.copilot_polling.helpers import is_sub_issue

        task = SimpleNamespace(title="Build widget", labels=[])
        assert is_sub_issue(task) is False

    def test_sub_issue_label_dict(self):
        from src.services.copilot_polling.helpers import is_sub_issue

        task = SimpleNamespace(title="Build widget", labels=[{"name": "sub-issue"}])
        assert is_sub_issue(task) is True

    def test_sub_issue_label_string(self):
        from src.services.copilot_polling.helpers import is_sub_issue

        task = SimpleNamespace(title="Build widget", labels=["sub-issue"])
        assert is_sub_issue(task) is True

    def test_no_title_no_labels(self):
        from src.services.copilot_polling.helpers import is_sub_issue

        task = SimpleNamespace(title=None, labels=None)
        assert is_sub_issue(task) is False

    def test_empty_bracket_not_matched(self):
        from src.services.copilot_polling.helpers import is_sub_issue

        task = SimpleNamespace(title="[] something", labels=[])
        # regex requires \S+ inside brackets — empty brackets don't match
        assert is_sub_issue(task) is False

    def test_unrelated_label_ignored(self):
        from src.services.copilot_polling.helpers import is_sub_issue

        task = SimpleNamespace(title="Build widget", labels=[{"name": "bug"}])
        assert is_sub_issue(task) is False


class TestGetSubIssueNumber:
    """_get_sub_issue_number() — pipeline lookup + parent fallback."""

    def test_returns_sub_issue_from_pipeline(self):
        from src.services.copilot_polling.helpers import _get_sub_issue_number

        pipeline = SimpleNamespace(agent_sub_issues={"architect": {"number": 42}})
        assert _get_sub_issue_number(pipeline, "architect", parent_issue_number=10) == 42

    def test_falls_back_to_parent_when_agent_not_in_pipeline(self):
        from src.services.copilot_polling.helpers import _get_sub_issue_number

        pipeline = SimpleNamespace(agent_sub_issues={"architect": {"number": 42}})
        assert _get_sub_issue_number(pipeline, "tester", parent_issue_number=10) == 10

    def test_falls_back_when_pipeline_is_none(self):
        from src.services.copilot_polling.helpers import _get_sub_issue_number

        assert _get_sub_issue_number(None, "architect", parent_issue_number=10) == 10

    def test_falls_back_when_number_is_zero(self):
        from src.services.copilot_polling.helpers import _get_sub_issue_number

        pipeline = SimpleNamespace(agent_sub_issues={"architect": {"number": 0}})
        assert _get_sub_issue_number(pipeline, "architect", parent_issue_number=10) == 10


class TestGetHumanSubIssueAssignee:
    """_get_human_sub_issue_assignee() — pipeline + global store."""

    def test_returns_assignee_from_pipeline(self):
        from src.services.copilot_polling.helpers import _get_human_sub_issue_assignee

        pipeline = SimpleNamespace(agent_sub_issues={"human": {"assignee": "alice", "number": 5}})
        assert _get_human_sub_issue_assignee(pipeline, 10) == "alice"

    def test_falls_back_to_global_store(self):
        from src.services.copilot_polling.helpers import _get_human_sub_issue_assignee

        with patch(_GET_SUB_ISSUES, return_value={"human": {"assignee": "bob"}}):
            result = _get_human_sub_issue_assignee(None, 10)
        assert result == "bob"

    def test_returns_empty_when_no_assignee(self):
        from src.services.copilot_polling.helpers import _get_human_sub_issue_assignee

        with patch(_GET_SUB_ISSUES, return_value={}):
            result = _get_human_sub_issue_assignee(None, 10)
        assert result == ""


class TestGetSubIssueNumbersForIssue:
    """_get_sub_issue_numbers_for_issue() — merge + dedup from two sources."""

    def test_merges_pipeline_and_global(self):
        from src.services.copilot_polling.helpers import _get_sub_issue_numbers_for_issue

        pipeline = SimpleNamespace(agent_sub_issues={"a": {"number": 5}})
        with patch(_GET_SUB_ISSUES, return_value={"b": {"number": 7}}):
            result = _get_sub_issue_numbers_for_issue(10, pipeline)
        assert result == [5, 7]

    def test_deduplicates(self):
        from src.services.copilot_polling.helpers import _get_sub_issue_numbers_for_issue

        pipeline = SimpleNamespace(agent_sub_issues={"a": {"number": 5}})
        with patch(_GET_SUB_ISSUES, return_value={"a": {"number": 5}}):
            result = _get_sub_issue_numbers_for_issue(10, pipeline)
        assert result == [5]

    def test_excludes_parent_number(self):
        from src.services.copilot_polling.helpers import _get_sub_issue_numbers_for_issue

        pipeline = SimpleNamespace(agent_sub_issues={"a": {"number": 10}})
        with patch(_GET_SUB_ISSUES, return_value={}):
            result = _get_sub_issue_numbers_for_issue(10, pipeline)
        assert result == []

    def test_no_pipeline(self):
        from src.services.copilot_polling.helpers import _get_sub_issue_numbers_for_issue

        with patch(_GET_SUB_ISSUES, return_value={"x": {"number": 3}}):
            result = _get_sub_issue_numbers_for_issue(10, None)
        assert result == [3]


# ══════════════════════════════════════════════════════════════════
# Async helpers
# ══════════════════════════════════════════════════════════════════


def _base_patches(mock_gps):
    """Stack patches for _cp.github_projects_service and common deps."""
    stack = ExitStack()
    stack.enter_context(patch(_GPS, mock_gps))
    return stack


class TestCheckAgentDoneOnSubOrParent:
    """_check_agent_done_on_sub_or_parent() — dispatch + parent/sub fallback."""

    async def test_dispatches_to_human_handler(self):
        mock_gps = MagicMock()
        with _base_patches(mock_gps):
            with patch(
                "src.services.copilot_polling.helpers._check_human_agent_done",
                new_callable=AsyncMock,
                return_value=True,
            ) as mock_human:
                from src.services.copilot_polling.helpers import (
                    _check_agent_done_on_sub_or_parent,
                )

                result = await _check_agent_done_on_sub_or_parent("tok", "o", "r", 10, "human")
        assert result is True
        mock_human.assert_awaited_once()

    async def test_dispatches_to_copilot_review_handler(self):
        mock_gps = MagicMock()
        with _base_patches(mock_gps):
            with patch(
                "src.services.copilot_polling.helpers._check_copilot_review_done",
                new_callable=AsyncMock,
                return_value=False,
            ) as mock_cr:
                from src.services.copilot_polling.helpers import (
                    _check_agent_done_on_sub_or_parent,
                )

                result = await _check_agent_done_on_sub_or_parent(
                    "tok", "o", "r", 10, "copilot-review"
                )
        assert result is False
        mock_cr.assert_awaited_once()

    async def test_checks_parent_then_sub(self):
        """For a regular agent: checks parent first, falls back to sub."""
        mock_gps = MagicMock()
        mock_gps.check_agent_completion_comment = AsyncMock(
            side_effect=[False, True]  # parent=False, sub=True
        )
        pipeline = SimpleNamespace(agent_sub_issues={"architect": {"number": 42}})

        with _base_patches(mock_gps):
            from src.services.copilot_polling.helpers import (
                _check_agent_done_on_sub_or_parent,
            )

            result = await _check_agent_done_on_sub_or_parent(
                "tok", "o", "r", 10, "architect", pipeline=pipeline
            )
        assert result is True
        assert mock_gps.check_agent_completion_comment.await_count == 2

    async def test_returns_true_if_done_on_parent(self):
        """Returns True immediately when parent has Done! marker."""
        mock_gps = MagicMock()
        mock_gps.check_agent_completion_comment = AsyncMock(return_value=True)

        with _base_patches(mock_gps):
            from src.services.copilot_polling.helpers import (
                _check_agent_done_on_sub_or_parent,
            )

            result = await _check_agent_done_on_sub_or_parent("tok", "o", "r", 10, "architect")
        assert result is True
        # Only called once — didn't need to check sub
        mock_gps.check_agent_completion_comment.assert_awaited_once()

    async def test_returns_false_when_no_sub_and_parent_not_done(self):
        """When sub == parent and parent is not done, returns False."""
        mock_gps = MagicMock()
        mock_gps.check_agent_completion_comment = AsyncMock(return_value=False)

        with _base_patches(mock_gps):
            from src.services.copilot_polling.helpers import (
                _check_agent_done_on_sub_or_parent,
            )

            result = await _check_agent_done_on_sub_or_parent("tok", "o", "r", 10, "architect")
        assert result is False


class TestCheckHumanAgentDone:
    """_check_human_agent_done() — 3 completion signals."""

    async def test_signal1_sub_issue_closed(self):
        """Human sub-issue closed → complete."""
        mock_gps = MagicMock()
        mock_gps.check_issue_closed = AsyncMock(return_value=True)
        pipeline = SimpleNamespace(agent_sub_issues={"human": {"number": 42}})

        with _base_patches(mock_gps):
            from src.services.copilot_polling.helpers import _check_human_agent_done

            result = await _check_human_agent_done("tok", "o", "r", 10, pipeline)
        assert result is True
        mock_gps.check_issue_closed.assert_awaited_once()

    async def test_signal2_done_comment_by_assignee(self):
        """Authorized user commented 'Done!' → complete."""
        mock_gps = MagicMock()
        mock_gps.check_issue_closed = AsyncMock(return_value=False)
        mock_gps.get_issue_with_comments = AsyncMock(
            return_value={
                "user": {"login": "alice"},
                "comments": [
                    {"body": "Done!", "author": "alice"},
                ],
            }
        )
        pipeline = SimpleNamespace(agent_sub_issues={"human": {"number": 42, "assignee": "alice"}})

        with _base_patches(mock_gps):
            from src.services.copilot_polling.helpers import _check_human_agent_done

            result = await _check_human_agent_done("tok", "o", "r", 10, pipeline)
        assert result is True

    async def test_signal2_human_done_format(self):
        """Authorized user commented 'human: Done!' → complete."""
        mock_gps = MagicMock()
        mock_gps.check_issue_closed = AsyncMock(return_value=False)
        mock_gps.get_issue_with_comments = AsyncMock(
            return_value={
                "user": {"login": "alice"},
                "comments": [
                    {"body": "human: Done!", "author": "alice"},
                ],
            }
        )
        pipeline = SimpleNamespace(agent_sub_issues={"human": {"number": 42, "assignee": "alice"}})

        with _base_patches(mock_gps):
            from src.services.copilot_polling.helpers import _check_human_agent_done

            result = await _check_human_agent_done("tok", "o", "r", 10, pipeline)
        assert result is True

    async def test_rejects_done_from_wrong_user(self):
        """Done! from a different user is rejected (fail closed)."""
        mock_gps = MagicMock()
        mock_gps.check_issue_closed = AsyncMock(return_value=False)
        mock_gps.get_issue_with_comments = AsyncMock(
            return_value={
                "user": {"login": "alice"},
                "comments": [
                    {"body": "Done!", "author": "mallory"},
                ],
            }
        )
        pipeline = SimpleNamespace(agent_sub_issues={"human": {"number": 42, "assignee": "alice"}})

        with _base_patches(mock_gps):
            from src.services.copilot_polling.helpers import _check_human_agent_done

            result = await _check_human_agent_done("tok", "o", "r", 10, pipeline)
        assert result is False

    async def test_no_sub_issue_skips_signal1(self):
        """When sub == parent, signal 1 (closed sub-issue) is skipped."""
        mock_gps = MagicMock()
        mock_gps.get_issue_with_comments = AsyncMock(
            return_value={
                "user": {"login": "alice"},
                "comments": [{"body": "Done!", "author": "alice"}],
            }
        )

        with _base_patches(mock_gps):
            with patch(_GET_SUB_ISSUES, return_value={}):
                from src.services.copilot_polling.helpers import _check_human_agent_done

                result = await _check_human_agent_done("tok", "o", "r", 10, None)
        assert result is True
        # check_issue_closed should NOT have been called
        mock_gps.check_issue_closed.assert_not_called()

    async def test_returns_false_when_no_assignee_and_no_author(self):
        """When no assignee can be determined, fail closed."""
        mock_gps = MagicMock()
        mock_gps.check_issue_closed = AsyncMock(return_value=False)
        mock_gps.get_issue_with_comments = AsyncMock(
            return_value={
                "user": {},  # no login
                "comments": [{"body": "Done!", "author": "someone"}],
            }
        )
        pipeline = SimpleNamespace(agent_sub_issues={"human": {"number": 42}})

        with _base_patches(mock_gps):
            with patch(_GET_SUB_ISSUES, return_value={}):
                from src.services.copilot_polling.helpers import _check_human_agent_done

                result = await _check_human_agent_done("tok", "o", "r", 10, pipeline)
        assert result is False


class TestUpdateIssueTracking:
    """_update_issue_tracking() — body mutation round-trip."""

    async def test_updates_body_to_active(self):
        mock_gps = MagicMock()
        mock_gps.get_issue_with_comments = AsyncMock(return_value={"body": "old-body"})
        mock_gps.update_issue_body = AsyncMock(return_value=True)

        with _base_patches(mock_gps):
            with patch(_MARK_ACTIVE, return_value="new-body"):
                from src.services.copilot_polling.helpers import _update_issue_tracking

                result = await _update_issue_tracking("tok", "o", "r", 10, "arch", "active")
        assert result is True
        mock_gps.update_issue_body.assert_awaited_once_with(
            access_token="tok", owner="o", repo="r", issue_number=10, body="new-body"
        )

    async def test_updates_body_to_done(self):
        mock_gps = MagicMock()
        mock_gps.get_issue_with_comments = AsyncMock(return_value={"body": "old-body"})
        mock_gps.update_issue_body = AsyncMock(return_value=True)

        with _base_patches(mock_gps):
            with patch(_MARK_DONE, return_value="new-body"):
                from src.services.copilot_polling.helpers import _update_issue_tracking

                result = await _update_issue_tracking("tok", "o", "r", 10, "arch", "done")
        assert result is True

    async def test_skips_update_when_body_unchanged(self):
        mock_gps = MagicMock()
        mock_gps.get_issue_with_comments = AsyncMock(return_value={"body": "same-body"})

        with _base_patches(mock_gps):
            with patch(_MARK_ACTIVE, return_value="same-body"):
                from src.services.copilot_polling.helpers import _update_issue_tracking

                result = await _update_issue_tracking("tok", "o", "r", 10, "arch", "active")
        assert result is True
        mock_gps.update_issue_body.assert_not_called()

    async def test_returns_false_on_empty_body(self):
        mock_gps = MagicMock()
        mock_gps.get_issue_with_comments = AsyncMock(return_value={"body": ""})

        with _base_patches(mock_gps):
            from src.services.copilot_polling.helpers import _update_issue_tracking

            result = await _update_issue_tracking("tok", "o", "r", 10, "arch", "active")
        assert result is False

    async def test_returns_false_on_invalid_state(self):
        mock_gps = MagicMock()
        mock_gps.get_issue_with_comments = AsyncMock(return_value={"body": "has-body"})

        with _base_patches(mock_gps):
            from src.services.copilot_polling.helpers import _update_issue_tracking

            result = await _update_issue_tracking("tok", "o", "r", 10, "arch", "invalid")
        assert result is False

    async def test_returns_false_on_exception(self):
        mock_gps = MagicMock()
        mock_gps.get_issue_with_comments = AsyncMock(side_effect=RuntimeError("API down"))

        with _base_patches(mock_gps):
            from src.services.copilot_polling.helpers import _update_issue_tracking

            result = await _update_issue_tracking("tok", "o", "r", 10, "arch", "active")
        assert result is False


class TestReconstructSubIssueMappings:
    """_reconstruct_sub_issue_mappings() — title parsing + global store persist."""

    async def test_parses_agent_from_title(self):
        mock_gps = MagicMock()
        mock_gps.get_sub_issues = AsyncMock(
            return_value=[
                {"title": "[architect] Design system", "number": 5, "node_id": "n1"},
                {"title": "[tester] Write tests", "number": 6, "node_id": "n2"},
            ]
        )

        with _base_patches(mock_gps):
            with patch(_SET_SUB_ISSUES) as mock_set:
                from src.services.copilot_polling.helpers import (
                    _reconstruct_sub_issue_mappings,
                )

                result = await _reconstruct_sub_issue_mappings("tok", "o", "r", 10)
        assert "architect" in result
        assert result["architect"]["number"] == 5
        assert "tester" in result
        mock_set.assert_called_once()

    async def test_ignores_titles_without_brackets(self):
        mock_gps = MagicMock()
        mock_gps.get_sub_issues = AsyncMock(
            return_value=[
                {"title": "Regular issue", "number": 5},
            ]
        )

        with _base_patches(mock_gps):
            with patch(_SET_SUB_ISSUES) as mock_set:
                from src.services.copilot_polling.helpers import (
                    _reconstruct_sub_issue_mappings,
                )

                result = await _reconstruct_sub_issue_mappings("tok", "o", "r", 10)
        assert result == {}
        mock_set.assert_not_called()

    async def test_returns_empty_on_exception(self):
        mock_gps = MagicMock()
        mock_gps.get_sub_issues = AsyncMock(side_effect=RuntimeError("API down"))

        with _base_patches(mock_gps):
            from src.services.copilot_polling.helpers import (
                _reconstruct_sub_issue_mappings,
            )

            result = await _reconstruct_sub_issue_mappings("tok", "o", "r", 10)
        assert result == {}


class TestCheckCopilotReviewDonePipelineGuard:
    """_check_copilot_review_done() — pipeline-position guard."""

    async def test_returns_false_when_pipeline_agent_is_not_copilot_review(self):
        """When pipeline.current_agent != 'copilot-review', return False without API calls."""
        mock_gps = MagicMock()
        pipeline = SimpleNamespace(current_agent="speckit.implement")

        with _base_patches(mock_gps):
            from src.services.copilot_polling.helpers import _check_copilot_review_done

            result = await _check_copilot_review_done("tok", "o", "r", 10, pipeline=pipeline)

        assert result is False
        # No API calls should have been made — the guard short-circuited
        mock_gps.get_issue_with_comments.assert_not_called()

    async def test_proceeds_when_pipeline_agent_is_copilot_review(self):
        """When pipeline.current_agent == 'copilot-review', proceed normally."""
        mock_gps = MagicMock()
        mock_gps.get_issue_with_comments = AsyncMock(return_value={"body": "", "comments": []})
        pipeline = SimpleNamespace(current_agent="copilot-review")

        with _base_patches(mock_gps):
            with patch(
                "src.services.copilot_polling.helpers._discover_main_pr_for_review",
                new_callable=AsyncMock,
                return_value=None,
            ):
                from src.services.copilot_polling.helpers import _check_copilot_review_done

                result = await _check_copilot_review_done("tok", "o", "r", 10, pipeline=pipeline)

        assert result is False
        # API calls SHOULD have been made — the guard did not short-circuit
        mock_gps.get_issue_with_comments.assert_awaited_once()

    async def test_proceeds_when_no_pipeline_provided(self):
        """When pipeline is None (backward compat), proceed normally."""
        mock_gps = MagicMock()
        mock_gps.get_issue_with_comments = AsyncMock(return_value={"body": "", "comments": []})

        with _base_patches(mock_gps):
            with patch(
                "src.services.copilot_polling.helpers._discover_main_pr_for_review",
                new_callable=AsyncMock,
                return_value=None,
            ):
                from src.services.copilot_polling.helpers import _check_copilot_review_done

                result = await _check_copilot_review_done("tok", "o", "r", 10)

        assert result is False
        mock_gps.get_issue_with_comments.assert_awaited_once()


class TestCheckAgentDonePassesPipeline:
    """_check_agent_done_on_sub_or_parent() passes pipeline to _check_copilot_review_done."""

    async def test_passes_pipeline_to_copilot_review_handler(self):
        mock_gps = MagicMock()
        pipeline = SimpleNamespace(
            current_agent="speckit.implement",
            agent_sub_issues=None,
        )

        with _base_patches(mock_gps):
            with patch(
                "src.services.copilot_polling.helpers._check_copilot_review_done",
                new_callable=AsyncMock,
                return_value=False,
            ) as mock_cr:
                from src.services.copilot_polling.helpers import (
                    _check_agent_done_on_sub_or_parent,
                )

                result = await _check_agent_done_on_sub_or_parent(
                    "tok", "o", "r", 10, "copilot-review", pipeline=pipeline
                )

        assert result is False
        mock_cr.assert_awaited_once_with(
            access_token="tok",
            owner="o",
            repo="r",
            parent_issue_number=10,
            pipeline=pipeline,
        )
