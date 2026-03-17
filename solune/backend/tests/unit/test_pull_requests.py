"""Unit tests for PullRequestsMixin (search, get, merge, timeline, files)."""

from unittest.mock import AsyncMock, Mock

import pytest

from src.services.github_projects import GitHubProjectsService

# ---------------------------------------------------------------------------
# _search_open_prs_for_issue_rest
# ---------------------------------------------------------------------------


class TestSearchOpenPrsForIssueRest:
    """Tests for _search_open_prs_for_issue_rest."""

    @pytest.fixture
    def service(self):
        return GitHubProjectsService()

    @pytest.mark.asyncio
    async def test_matches_pr_by_title(self, service):
        """PR with issue ref in title is returned."""
        pr = {
            "node_id": "PR_1",
            "number": 5,
            "title": "Fix #42",
            "body": "",
            "draft": False,
            "html_url": "https://github.com/o/r/pull/5",
            "user": {"login": "alice"},
            "head": {"ref": "feature/fix"},
        }
        mock_resp = Mock(status_code=200, json=Mock(return_value=[pr]))
        service._rest_response = AsyncMock(return_value=mock_resp)
        result = await service._search_open_prs_for_issue_rest("tok", "o", "r", 42)
        assert len(result) == 1
        assert result[0]["number"] == 5

    @pytest.mark.asyncio
    async def test_matches_pr_by_body(self, service):
        """PR with issue ref in body is returned."""
        pr = {
            "node_id": "PR_2",
            "number": 6,
            "title": "Some fix",
            "body": "Closes #42",
            "draft": True,
            "html_url": "https://github.com/o/r/pull/6",
            "user": {"login": "bob"},
            "head": {"ref": "fix-stuff"},
        }
        mock_resp = Mock(status_code=200, json=Mock(return_value=[pr]))
        service._rest_response = AsyncMock(return_value=mock_resp)
        result = await service._search_open_prs_for_issue_rest("tok", "o", "r", 42)
        assert len(result) == 1
        assert result[0]["is_draft"] is True

    @pytest.mark.asyncio
    async def test_matches_pr_by_branch_name(self, service):
        """PR with issue number in branch name is returned."""
        pr = {
            "node_id": "PR_3",
            "number": 7,
            "title": "Work",
            "body": "",
            "draft": False,
            "html_url": "",
            "user": {"login": "carol"},
            "head": {"ref": "copilot/fix-42"},
        }
        mock_resp = Mock(status_code=200, json=Mock(return_value=[pr]))
        service._rest_response = AsyncMock(return_value=mock_resp)
        result = await service._search_open_prs_for_issue_rest("tok", "o", "r", 42)
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_no_match_returns_empty(self, service):
        """PRs that don't reference the issue are excluded."""
        pr = {
            "node_id": "PR_4",
            "number": 8,
            "title": "Unrelated",
            "body": "Nothing here",
            "draft": False,
            "html_url": "",
            "user": {"login": "dave"},
            "head": {"ref": "unrelated-branch"},
        }
        mock_resp = Mock(status_code=200, json=Mock(return_value=[pr]))
        service._rest_response = AsyncMock(return_value=mock_resp)
        result = await service._search_open_prs_for_issue_rest("tok", "o", "r", 42)
        assert result == []

    @pytest.mark.asyncio
    async def test_non_200_returns_empty(self, service):
        """Non-200 status code returns empty list."""
        mock_resp = Mock(status_code=403)
        service._rest_response = AsyncMock(return_value=mock_resp)
        result = await service._search_open_prs_for_issue_rest("tok", "o", "r", 42)
        assert result == []

    @pytest.mark.asyncio
    async def test_exception_returns_empty(self, service):
        """Network exception returns empty list."""
        service._rest_response = AsyncMock(side_effect=RuntimeError("timeout"))
        result = await service._search_open_prs_for_issue_rest("tok", "o", "r", 42)
        assert result == []


# ---------------------------------------------------------------------------
# get_pull_request
# ---------------------------------------------------------------------------


class TestGetPullRequest:
    """Tests for get_pull_request."""

    @pytest.fixture
    def service(self):
        return GitHubProjectsService()

    @pytest.mark.asyncio
    async def test_success_returns_pr_dict(self, service):
        """Successful query returns a formatted PR dict."""
        service._graphql = AsyncMock(
            return_value={
                "repository": {
                    "pullRequest": {
                        "id": "PR_node",
                        "number": 10,
                        "title": "Add feature",
                        "body": "Description",
                        "state": "OPEN",
                        "isDraft": False,
                        "url": "https://github.com/o/r/pull/10",
                        "headRefName": "feature/x",
                        "baseRefName": "main",
                        "author": {"login": "alice"},
                        "createdAt": "2024-01-01",
                        "updatedAt": "2024-01-02",
                        "changedFiles": 3,
                        "commits": {
                            "nodes": [
                                {
                                    "commit": {
                                        "oid": "abc123",
                                        "committedDate": "2024-01-02",
                                        "statusCheckRollup": {"state": "SUCCESS"},
                                    }
                                }
                            ]
                        },
                    }
                }
            }
        )
        result = await service.get_pull_request("tok", "o", "r", 10)
        assert result is not None
        assert result["number"] == 10
        assert result["head_ref"] == "feature/x"
        assert result["check_status"] == "SUCCESS"
        assert result["last_commit"]["sha"] == "abc123"

    @pytest.mark.asyncio
    async def test_returns_none_when_pr_not_found(self, service):
        """Returns None when pullRequest is None."""
        service._graphql = AsyncMock(return_value={"repository": {"pullRequest": None}})
        result = await service.get_pull_request("tok", "o", "r", 999)
        assert result is None

    @pytest.mark.asyncio
    async def test_returns_none_on_exception(self, service):
        """Returns None when GraphQL raises."""
        service._graphql = AsyncMock(side_effect=RuntimeError("fail"))
        result = await service.get_pull_request("tok", "o", "r", 10)
        assert result is None

    @pytest.mark.asyncio
    async def test_caches_result(self, service):
        """Result is stored in the cycle cache."""
        service._graphql = AsyncMock(
            return_value={
                "repository": {
                    "pullRequest": {
                        "id": "PR_1",
                        "number": 10,
                        "title": "T",
                        "body": "",
                        "state": "OPEN",
                        "isDraft": False,
                        "url": "",
                        "headRefName": "h",
                        "baseRefName": "b",
                        "author": {"login": "u"},
                        "createdAt": "",
                        "updatedAt": "",
                        "changedFiles": 0,
                        "commits": {"nodes": []},
                    }
                }
            }
        )
        await service.get_pull_request("tok", "o", "r", 10)
        assert "pr:o/r/10" in service._cycle_cache

    @pytest.mark.asyncio
    async def test_returns_cached(self, service):
        """Returns cached result without calling GraphQL."""
        cached = {"number": 10, "title": "Cached"}
        service._cycle_cache["pr:o/r/10"] = cached
        service._graphql = AsyncMock()
        result = await service.get_pull_request("tok", "o", "r", 10)
        assert result == cached
        service._graphql.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_no_commits(self, service):
        """PR with no commits has None last_commit and check_status."""
        service._graphql = AsyncMock(
            return_value={
                "repository": {
                    "pullRequest": {
                        "id": "PR_2",
                        "number": 11,
                        "title": "T",
                        "body": "",
                        "state": "OPEN",
                        "isDraft": True,
                        "url": "",
                        "headRefName": "h",
                        "baseRefName": "b",
                        "author": {"login": "u"},
                        "createdAt": "",
                        "updatedAt": "",
                        "changedFiles": 0,
                        "commits": {"nodes": []},
                    }
                }
            }
        )
        result = await service.get_pull_request("tok", "o", "r", 11)
        assert result["last_commit"] is None
        assert result["check_status"] is None


# ---------------------------------------------------------------------------
# get_linked_pull_requests
# ---------------------------------------------------------------------------


class TestGetLinkedPullRequests:
    """Tests for get_linked_pull_requests."""

    @pytest.fixture
    def service(self):
        return GitHubProjectsService()

    @pytest.mark.asyncio
    async def test_extracts_prs_from_timeline(self, service):
        """Extracts PRs from ConnectedEvent timeline items."""
        service._graphql = AsyncMock(
            return_value={
                "repository": {
                    "issue": {
                        "timelineItems": {
                            "nodes": [
                                {
                                    "subject": {
                                        "__typename": "PullRequest",
                                        "id": "PR_1",
                                        "number": 5,
                                        "title": "Fix",
                                        "state": "OPEN",
                                        "isDraft": False,
                                        "url": "https://pr",
                                        "headRefName": "fix-branch",
                                        "author": {"login": "alice"},
                                        "createdAt": "",
                                        "updatedAt": "",
                                    }
                                }
                            ]
                        }
                    }
                }
            }
        )
        result = await service.get_linked_pull_requests("tok", "o", "r", 1)
        assert len(result) == 1
        assert result[0]["number"] == 5
        assert result[0]["head_ref"] == "fix-branch"

    @pytest.mark.asyncio
    async def test_deduplicates_by_number(self, service):
        """Duplicate PR numbers are removed."""
        pr_node = {
            "__typename": "PullRequest",
            "id": "PR_1",
            "number": 5,
            "title": "Fix",
            "state": "OPEN",
            "isDraft": False,
            "url": "",
            "headRefName": "branch",
            "author": {"login": "u"},
            "createdAt": "",
            "updatedAt": "",
        }
        service._graphql = AsyncMock(
            return_value={
                "repository": {
                    "issue": {
                        "timelineItems": {
                            "nodes": [
                                {"subject": pr_node},
                                {"source": pr_node},
                            ]
                        }
                    }
                }
            }
        )
        result = await service.get_linked_pull_requests("tok", "o", "r", 1)
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_returns_empty_on_exception(self, service):
        """Returns empty list on exception."""
        service._graphql = AsyncMock(side_effect=RuntimeError("fail"))
        result = await service.get_linked_pull_requests("tok", "o", "r", 1)
        assert result == []

    @pytest.mark.asyncio
    async def test_returns_cached(self, service):
        """Returns cached linked PRs."""
        cached = [{"number": 5}]
        service._cycle_cache["linked_prs:o/r/1"] = cached
        service._graphql = AsyncMock()
        result = await service.get_linked_pull_requests("tok", "o", "r", 1)
        assert result == cached
        service._graphql.assert_not_awaited()


# ---------------------------------------------------------------------------
# mark_pr_ready_for_review
# ---------------------------------------------------------------------------


class TestMarkPrReadyForReview:
    """Tests for mark_pr_ready_for_review."""

    @pytest.fixture
    def service(self):
        return GitHubProjectsService()

    @pytest.mark.asyncio
    async def test_success_returns_true(self, service):
        """Returns True when PR is successfully marked ready."""
        service._graphql = AsyncMock(
            return_value={
                "markPullRequestReadyForReview": {
                    "pullRequest": {
                        "isDraft": False,
                        "number": 10,
                        "url": "https://pr",
                    }
                }
            }
        )
        result = await service.mark_pr_ready_for_review("tok", "PR_node_1")
        assert result is True

    @pytest.mark.asyncio
    async def test_returns_false_when_still_draft(self, service):
        """Returns False when PR is still a draft after mutation."""
        service._graphql = AsyncMock(
            return_value={
                "markPullRequestReadyForReview": {
                    "pullRequest": {
                        "isDraft": True,
                        "number": 10,
                    }
                }
            }
        )
        result = await service.mark_pr_ready_for_review("tok", "PR_node_1")
        assert result is False

    @pytest.mark.asyncio
    async def test_returns_false_on_exception(self, service):
        """Returns False on exception."""
        service._graphql = AsyncMock(side_effect=RuntimeError("boom"))
        result = await service.mark_pr_ready_for_review("tok", "PR_node_1")
        assert result is False

    @pytest.mark.asyncio
    async def test_invalidates_cache(self, service):
        """Invalidates the cycle cache for the PR on success."""
        service._cycle_cache["pr:o/r/10"] = {"number": 10}
        service._graphql = AsyncMock(
            return_value={
                "markPullRequestReadyForReview": {
                    "pullRequest": {
                        "isDraft": False,
                        "number": 10,
                        "url": "",
                    }
                }
            }
        )
        await service.mark_pr_ready_for_review("tok", "PR_node_1")
        assert "pr:o/r/10" not in service._cycle_cache


# ---------------------------------------------------------------------------
# merge_pull_request
# ---------------------------------------------------------------------------


class TestMergePullRequest:
    """Tests for merge_pull_request."""

    @pytest.fixture
    def service(self):
        return GitHubProjectsService()

    @pytest.mark.asyncio
    async def test_success_returns_merge_details(self, service):
        """Successful merge returns a result dict."""
        service._graphql = AsyncMock(
            return_value={
                "mergePullRequest": {
                    "pullRequest": {
                        "number": 10,
                        "state": "MERGED",
                        "merged": True,
                        "mergedAt": "2024-01-01T00:00:00Z",
                        "mergeCommit": {"oid": "abc123def456"},
                        "url": "https://github.com/o/r/pull/10",
                    }
                }
            }
        )
        result = await service.merge_pull_request("tok", "PR_node", pr_number=10)
        assert result is not None
        assert result["merged"] is True
        assert result["merge_commit"] == "abc123def456"

    @pytest.mark.asyncio
    async def test_returns_none_when_not_merged(self, service):
        """Returns None when PR was not actually merged."""
        service._graphql = AsyncMock(
            return_value={
                "mergePullRequest": {
                    "pullRequest": {
                        "number": 10,
                        "state": "OPEN",
                        "merged": False,
                    }
                }
            }
        )
        result = await service.merge_pull_request("tok", "PR_node", pr_number=10)
        assert result is None

    @pytest.mark.asyncio
    async def test_returns_none_on_exception(self, service):
        """Returns None on exception."""
        service._graphql = AsyncMock(side_effect=RuntimeError("conflict"))
        result = await service.merge_pull_request("tok", "PR_node", pr_number=10)
        assert result is None

    @pytest.mark.asyncio
    async def test_passes_merge_method_and_headline(self, service):
        """Passes mergeMethod and commitHeadline variables."""
        service._graphql = AsyncMock(
            return_value={
                "mergePullRequest": {
                    "pullRequest": {
                        "number": 10,
                        "state": "MERGED",
                        "merged": True,
                        "mergedAt": "",
                        "mergeCommit": {"oid": "abc"},
                        "url": "",
                    }
                }
            }
        )
        await service.merge_pull_request(
            "tok",
            "PR_node",
            pr_number=10,
            commit_headline="Custom message",
            merge_method="MERGE",
        )
        variables = service._graphql.call_args[0][2]
        assert variables["mergeMethod"] == "MERGE"
        assert variables["commitHeadline"] == "Custom message"

    @pytest.mark.asyncio
    async def test_invalidates_cache_on_merge(self, service):
        """Invalidates cached PR data after a successful merge."""
        service._cycle_cache["pr:o/r/10"] = {"number": 10}
        service._graphql = AsyncMock(
            return_value={
                "mergePullRequest": {
                    "pullRequest": {
                        "number": 10,
                        "state": "MERGED",
                        "merged": True,
                        "mergedAt": "",
                        "mergeCommit": {"oid": "abc"},
                        "url": "",
                    }
                }
            }
        )
        await service.merge_pull_request("tok", "PR_node", pr_number=10)
        assert "pr:o/r/10" not in service._cycle_cache


# ---------------------------------------------------------------------------
# get_pr_timeline_events
# ---------------------------------------------------------------------------


class TestGetPrTimelineEvents:
    """Tests for get_pr_timeline_events."""

    @pytest.fixture
    def service(self):
        return GitHubProjectsService()

    @pytest.mark.asyncio
    async def test_returns_events_list(self, service):
        """Returns list of timeline events."""
        events = [{"event": "labeled"}, {"event": "closed"}]
        service._rest = AsyncMock(return_value=events)
        result = await service.get_pr_timeline_events("tok", "o", "r", 1)
        assert result == events

    @pytest.mark.asyncio
    async def test_returns_empty_on_non_list(self, service):
        """Returns empty list when response is not a list."""
        service._rest = AsyncMock(return_value={"error": "bad"})
        result = await service.get_pr_timeline_events("tok", "o", "r", 1)
        assert result == []

    @pytest.mark.asyncio
    async def test_returns_empty_on_exception(self, service):
        """Returns empty list on exception."""
        service._rest = AsyncMock(side_effect=RuntimeError("timeout"))
        result = await service.get_pr_timeline_events("tok", "o", "r", 1)
        assert result == []

    @pytest.mark.asyncio
    async def test_caches_result(self, service):
        """Timeline events are cached."""
        events = [{"event": "referenced"}]
        service._rest = AsyncMock(return_value=events)
        await service.get_pr_timeline_events("tok", "o", "r", 1)
        assert "timeline:o/r/1" in service._cycle_cache

    @pytest.mark.asyncio
    async def test_returns_cached(self, service):
        """Returns cached timeline events."""
        cached = [{"event": "cached"}]
        service._cycle_cache["timeline:o/r/1"] = cached
        service._rest = AsyncMock()
        result = await service.get_pr_timeline_events("tok", "o", "r", 1)
        assert result == cached
        service._rest.assert_not_awaited()


# ---------------------------------------------------------------------------
# get_pr_changed_files
# ---------------------------------------------------------------------------


class TestGetPrChangedFiles:
    """Tests for get_pr_changed_files."""

    @pytest.fixture
    def service(self):
        return GitHubProjectsService()

    @pytest.mark.asyncio
    async def test_success_returns_files(self, service):
        """200 response returns list of changed files."""
        files = [
            {"filename": "a.py", "status": "modified", "additions": 5, "deletions": 2},
            {"filename": "b.py", "status": "added", "additions": 10, "deletions": 0},
        ]
        mock_resp = Mock(status_code=200, json=Mock(return_value=files))
        service._rest_response = AsyncMock(return_value=mock_resp)
        result = await service.get_pr_changed_files("tok", "o", "r", 10)
        assert len(result) == 2
        assert result[0]["filename"] == "a.py"

    @pytest.mark.asyncio
    async def test_non_200_returns_empty(self, service):
        """Non-200 status returns empty list."""
        mock_resp = Mock(status_code=404)
        service._rest_response = AsyncMock(return_value=mock_resp)
        result = await service.get_pr_changed_files("tok", "o", "r", 10)
        assert result == []

    @pytest.mark.asyncio
    async def test_exception_returns_empty(self, service):
        """Exception returns empty list."""
        service._rest_response = AsyncMock(side_effect=RuntimeError("fail"))
        result = await service.get_pr_changed_files("tok", "o", "r", 10)
        assert result == []


# ---------------------------------------------------------------------------
# update_pr_base
# ---------------------------------------------------------------------------


class TestUpdatePrBase:
    """Tests for update_pr_base."""

    @pytest.fixture
    def service(self):
        return GitHubProjectsService()

    @pytest.mark.asyncio
    async def test_success_returns_true(self, service):
        """200 response returns True."""
        mock_resp = Mock(status_code=200)
        service._rest_response = AsyncMock(return_value=mock_resp)
        result = await service.update_pr_base("tok", "o", "r", 10, "develop")
        assert result is True

    @pytest.mark.asyncio
    async def test_non_200_returns_false(self, service):
        """Non-200 returns False."""
        mock_resp = Mock(status_code=422, text="Unprocessable")
        service._rest_response = AsyncMock(return_value=mock_resp)
        result = await service.update_pr_base("tok", "o", "r", 10, "develop")
        assert result is False

    @pytest.mark.asyncio
    async def test_exception_returns_false(self, service):
        """Exception returns False."""
        service._rest_response = AsyncMock(side_effect=RuntimeError("oops"))
        result = await service.update_pr_base("tok", "o", "r", 10, "develop")
        assert result is False


# ---------------------------------------------------------------------------
# create_pull_request
# ---------------------------------------------------------------------------


class TestCreatePullRequest:
    """Tests for create_pull_request."""

    @pytest.fixture
    def service(self):
        return GitHubProjectsService()

    @pytest.mark.asyncio
    async def test_success_returns_pr_info(self, service):
        """Returns PR id, number, url on success."""
        service._graphql = AsyncMock(
            return_value={
                "createPullRequest": {
                    "pullRequest": {
                        "id": "PR_1",
                        "number": 42,
                        "url": "https://github.com/o/r/pull/42",
                    }
                }
            }
        )
        result = await service.create_pull_request(
            "tok",
            "REPO_ID",
            "Title",
            "Body",
            "feature",
            "main",
        )
        assert result is not None
        assert result["number"] == 42

    @pytest.mark.asyncio
    async def test_already_exists_returns_existing_flag(self, service):
        """Returns existing=True when PR already exists."""
        service._graphql = AsyncMock(
            side_effect=ValueError("A pull request already exists for this head/base")
        )
        result = await service.create_pull_request(
            "tok",
            "REPO_ID",
            "Title",
            "Body",
            "feature",
            "main",
        )
        assert result is not None
        assert result.get("existing") is True

    @pytest.mark.asyncio
    async def test_other_value_error_returns_none(self, service):
        """Non-duplicate ValueError returns None."""
        service._graphql = AsyncMock(side_effect=ValueError("Something else"))
        result = await service.create_pull_request(
            "tok",
            "REPO_ID",
            "Title",
            "Body",
            "feature",
            "main",
        )
        assert result is None
