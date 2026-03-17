"""Unit tests for CopilotMixin (copilot.py)."""

from unittest.mock import AsyncMock

import pytest

from src.services.github_projects.service import GitHubProjectsService


@pytest.fixture
def service():
    svc = GitHubProjectsService()
    svc._graphql = AsyncMock()
    svc._rest = AsyncMock()
    svc._rest_response = AsyncMock()
    svc.get_issue_with_comments = AsyncMock()
    svc.get_linked_pull_requests = AsyncMock()
    svc.get_pull_request = AsyncMock()
    svc.get_pr_timeline_events = AsyncMock()
    return svc


# ═══════════════════════════════════════════════════════════════════════════
# get_copilot_bot_id
# ═══════════════════════════════════════════════════════════════════════════


class TestGetCopilotBotId:
    @pytest.mark.asyncio
    async def test_success_finds_bot(self, service):
        """Should return (bot_id, repo_id) when copilot-swe-agent Bot is present."""
        service._graphql.return_value = {
            "repository": {
                "id": "R_abc",
                "suggestedActors": {
                    "nodes": [
                        {"login": "dependabot", "__typename": "Bot", "id": "B_dep"},
                        {"login": "copilot-swe-agent", "__typename": "Bot", "id": "B_cop"},
                    ]
                },
            }
        }

        bot_id, repo_id = await service.get_copilot_bot_id("tok", "owner", "repo")

        assert bot_id == "B_cop"
        assert repo_id == "R_abc"

    @pytest.mark.asyncio
    async def test_no_bot_found(self, service):
        """Should return (None, repo_id) when no copilot-swe-agent actor exists."""
        service._graphql.return_value = {
            "repository": {
                "id": "R_abc",
                "suggestedActors": {
                    "nodes": [
                        {"login": "dependabot", "__typename": "Bot", "id": "B_dep"},
                    ]
                },
            }
        }

        bot_id, repo_id = await service.get_copilot_bot_id("tok", "owner", "repo")

        assert bot_id is None
        assert repo_id == "R_abc"

    @pytest.mark.asyncio
    async def test_exception_returns_none_none(self, service):
        """Should return (None, None) on any exception."""
        service._graphql.side_effect = RuntimeError("network failure")

        bot_id, repo_id = await service.get_copilot_bot_id("tok", "owner", "repo")

        assert bot_id is None
        assert repo_id is None


# ═══════════════════════════════════════════════════════════════════════════
# check_agent_completion_comment
# ═══════════════════════════════════════════════════════════════════════════


class TestCheckAgentCompletionComment:
    @pytest.mark.asyncio
    async def test_found_done_marker(self, service):
        """Should return True when an exact-line 'agent: Done!' marker is found."""
        service.get_issue_with_comments.return_value = {
            "comments": [
                {"body": "Some other comment"},
                {"body": "speckit.specify: Done!"},
            ]
        }

        result = await service.check_agent_completion_comment(
            "tok", "owner", "repo", 1, "speckit.specify"
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_marker_not_found(self, service):
        """Should return False when no matching marker exists."""
        service.get_issue_with_comments.return_value = {
            "comments": [
                {"body": "Work in progress"},
            ]
        }

        result = await service.check_agent_completion_comment(
            "tok", "owner", "repo", 1, "speckit.specify"
        )
        assert result is False

    @pytest.mark.asyncio
    async def test_marker_embedded_in_narrative_not_matched(self, service):
        """Marker text appearing mid-line (not on its own line) should NOT match."""
        service.get_issue_with_comments.return_value = {
            "comments": [
                {"body": "I noticed that speckit.specify: Done! was logged previously."},
            ]
        }

        result = await service.check_agent_completion_comment(
            "tok", "owner", "repo", 1, "speckit.specify"
        )
        assert result is False

    @pytest.mark.asyncio
    async def test_no_issue_data(self, service):
        """Should return False when get_issue_with_comments returns falsy."""
        service.get_issue_with_comments.return_value = None

        result = await service.check_agent_completion_comment("tok", "owner", "repo", 1, "agent")
        assert result is False

    @pytest.mark.asyncio
    async def test_exception_returns_false(self, service):
        """Should return False on exception."""
        service.get_issue_with_comments.side_effect = RuntimeError("boom")

        result = await service.check_agent_completion_comment("tok", "owner", "repo", 1, "agent")
        assert result is False


# ═══════════════════════════════════════════════════════════════════════════
# assign_copilot (via _assign_copilot_graphql)
# ═══════════════════════════════════════════════════════════════════════════


class TestAssignCopilotGraphQL:
    @pytest.mark.asyncio
    async def test_success(self, service):
        """GraphQL assignment succeeds when get_copilot_bot_id and _graphql work."""
        service.get_copilot_bot_id = AsyncMock(return_value=("B_cop", "R_abc"))
        service._graphql.return_value = {
            "addAssigneesToAssignable": {
                "assignable": {"assignees": {"nodes": [{"login": "copilot-swe-agent[bot]"}]}}
            }
        }

        result = await service._assign_copilot_graphql(
            "tok", "owner", "repo", "I_node", base_ref="main"
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_failure_no_bot(self, service):
        """Should return False when Copilot bot is not available."""
        service.get_copilot_bot_id = AsyncMock(return_value=(None, "R_abc"))

        result = await service._assign_copilot_graphql("tok", "owner", "repo", "I_node")
        assert result is False

    @pytest.mark.asyncio
    async def test_failure_no_repo_id(self, service):
        """Should return False when repo ID is missing."""
        service.get_copilot_bot_id = AsyncMock(return_value=("B_cop", None))

        result = await service._assign_copilot_graphql("tok", "owner", "repo", "I_node")
        assert result is False

    @pytest.mark.asyncio
    async def test_failure_graphql_exception(self, service):
        """Should return False when GraphQL mutation raises."""
        service.get_copilot_bot_id = AsyncMock(return_value=("B_cop", "R_abc"))
        service._graphql.side_effect = RuntimeError("mutation failed")

        result = await service._assign_copilot_graphql("tok", "owner", "repo", "I_node")
        assert result is False


# ═══════════════════════════════════════════════════════════════════════════
# request_copilot_review
# ═══════════════════════════════════════════════════════════════════════════


class TestRequestCopilotReview:
    @pytest.mark.asyncio
    async def test_rest_success(self, service):
        """Should return True when REST API returns 201."""
        mock_resp = AsyncMock()
        mock_resp.status_code = 201
        service._rest_response.return_value = mock_resp

        result = await service.request_copilot_review(
            "tok", "PR_node", pr_number=10, owner="o", repo="r"
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_graphql_fallback_success(self, service):
        """Should fall back to GraphQL and succeed when REST fails."""
        # REST path: no pr_number/owner/repo → skip REST
        service._graphql.return_value = {
            "requestReviews": {
                "pullRequest": {"number": 10, "url": "https://github.com/o/r/pull/10"}
            }
        }

        result = await service.request_copilot_review("tok", "PR_node")
        assert result is True

    @pytest.mark.asyncio
    async def test_graphql_fallback_failure(self, service):
        """Should return False when GraphQL fallback fails."""
        service._graphql.return_value = {"requestReviews": {"pullRequest": None}}

        result = await service.request_copilot_review("tok", "PR_node")
        assert result is False

    @pytest.mark.asyncio
    async def test_graphql_exception(self, service):
        """Should return False when both REST and GraphQL fail."""
        service._graphql.side_effect = RuntimeError("fail")

        result = await service.request_copilot_review("tok", "PR_node")
        assert result is False


# ═══════════════════════════════════════════════════════════════════════════
# check_copilot_pr_completion
# ═══════════════════════════════════════════════════════════════════════════


class TestCheckCopilotPrCompletion:
    @pytest.mark.asyncio
    async def test_open_pr_not_draft_returns_finished(self, service):
        """An open, non-draft PR by Copilot should be detected as finished."""
        service.get_linked_pull_requests.return_value = [
            {
                "author": "copilot-swe-agent[bot]",
                "state": "OPEN",
                "is_draft": False,
                "number": 5,
            }
        ]
        service.get_pull_request.return_value = {"id": "PR_node5"}

        result = await service.check_copilot_pr_completion("tok", "o", "r", 1)

        assert result is not None
        assert result["copilot_finished"] is True
        assert result["number"] == 5

    @pytest.mark.asyncio
    async def test_draft_pr_with_finished_event(self, service):
        """A draft PR should be detected as finished if timeline has copilot_work_finished."""
        service.get_linked_pull_requests.return_value = [
            {
                "author": "copilot-swe-agent[bot]",
                "state": "OPEN",
                "is_draft": True,
                "number": 5,
            }
        ]
        service.get_pull_request.return_value = {"id": "PR_node5", "title": "[WIP] stuff"}
        service.get_pr_timeline_events.return_value = [
            {"event": "copilot_work_finished", "created_at": "2025-01-01T00:00:00Z"}
        ]

        result = await service.check_copilot_pr_completion("tok", "o", "r", 1)

        assert result is not None
        assert result["copilot_finished"] is True

    @pytest.mark.asyncio
    async def test_draft_pr_still_in_progress(self, service):
        """A draft PR with no finish events should return None (still working)."""
        service.get_linked_pull_requests.return_value = [
            {
                "author": "copilot-swe-agent[bot]",
                "state": "OPEN",
                "is_draft": True,
                "number": 5,
            }
        ]
        service.get_pull_request.return_value = {"id": "PR_node5", "title": "[WIP] stuff"}
        service.get_pr_timeline_events.return_value = [
            {"event": "labeled", "created_at": "2025-01-01T00:00:00Z"}
        ]

        result = await service.check_copilot_pr_completion("tok", "o", "r", 1)
        assert result is None

    @pytest.mark.asyncio
    async def test_closed_pr_skipped(self, service):
        """A closed/merged PR should be skipped (state != OPEN)."""
        service.get_linked_pull_requests.return_value = [
            {
                "author": "copilot-swe-agent[bot]",
                "state": "MERGED",
                "is_draft": False,
                "number": 5,
            }
        ]

        result = await service.check_copilot_pr_completion("tok", "o", "r", 1)
        assert result is None

    @pytest.mark.asyncio
    async def test_no_linked_prs(self, service):
        """Should return None when there are no linked PRs."""
        service.get_linked_pull_requests.return_value = []

        result = await service.check_copilot_pr_completion("tok", "o", "r", 1)
        assert result is None

    @pytest.mark.asyncio
    async def test_exception_returns_none(self, service):
        """Should return None on exception."""
        service.get_linked_pull_requests.side_effect = RuntimeError("fail")

        result = await service.check_copilot_pr_completion("tok", "o", "r", 1)
        assert result is None

    @pytest.mark.asyncio
    async def test_title_based_fallback_when_no_timeline_events(self, service):
        """When timeline returns empty and title has no [WIP], treat as completed."""
        service.get_linked_pull_requests.return_value = [
            {
                "author": "copilot-swe-agent[bot]",
                "state": "OPEN",
                "is_draft": True,
                "number": 5,
            }
        ]
        service.get_pull_request.return_value = {
            "id": "PR_node5",
            "title": "Add OAuth flow",
        }
        service.get_pr_timeline_events.return_value = []

        result = await service.check_copilot_pr_completion("tok", "o", "r", 1)

        assert result is not None
        assert result["copilot_finished"] is True


# ═══════════════════════════════════════════════════════════════════════════
# check_copilot_finished_events
# ═══════════════════════════════════════════════════════════════════════════


class TestCheckCopilotFinishedEvents:
    def test_copilot_work_finished_event(self, service):
        """Should return True for copilot_work_finished event."""
        events = [{"event": "copilot_work_finished"}]
        assert service.check_copilot_finished_events(events) is True

    def test_review_requested_by_swe_agent(self, service):
        """Should return True when review_requested by copilot-swe-agent."""
        events = [
            {
                "event": "review_requested",
                "review_requester": {"login": "copilot-swe-agent[bot]"},
                "requested_reviewer": {"login": "octocat"},
            }
        ]
        assert service.check_copilot_finished_events(events) is True

    def test_review_requested_by_other_bot_ignored(self, service):
        """review_requested by non-SWE-agent bot should NOT count as finished."""
        events = [
            {
                "event": "review_requested",
                "review_requester": {"login": "copilot-pull-request-reviewer[bot]"},
                "requested_reviewer": {"login": "octocat"},
            }
        ]
        assert service.check_copilot_finished_events(events) is False

    def test_no_relevant_events(self, service):
        """Should return False when no relevant events exist."""
        events = [{"event": "labeled"}, {"event": "assigned"}]
        assert service.check_copilot_finished_events(events) is False

    def test_empty_events(self, service):
        """Should return False for an empty event list."""
        assert service.check_copilot_finished_events([]) is False


# ═══════════════════════════════════════════════════════════════════════════
# check_copilot_stopped_events
# ═══════════════════════════════════════════════════════════════════════════


class TestCheckCopilotStoppedEvents:
    def test_stopped_event_found(self, service):
        """Should return True when copilot_work_stopped is present."""
        events = [{"event": "copilot_work_stopped"}]
        assert service.check_copilot_stopped_events(events) is True

    def test_no_stopped_event(self, service):
        """Should return False when no stopped event exists."""
        events = [{"event": "copilot_work_finished"}]
        assert service.check_copilot_stopped_events(events) is False
