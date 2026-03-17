"""Unit tests for IssuesMixin (create, update, comment, project ops)."""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from githubkit.exception import RequestFailed

from src.exceptions import ValidationError
from src.services.github_projects import GitHubProjectsService

# ---------------------------------------------------------------------------
# create_issue
# ---------------------------------------------------------------------------


class TestCreateIssue:
    """Tests for create_issue."""

    @pytest.fixture
    def service(self):
        return GitHubProjectsService()

    @pytest.mark.asyncio
    async def test_success_returns_issue_dict(self, service):
        """Successful creation returns the issue dict."""
        issue = {"number": 42, "id": 1, "node_id": "I_abc"}
        service._rest = AsyncMock(return_value=issue)
        result = await service.create_issue("tok", "owner", "repo", "Title", "Body")
        assert result == issue
        service._rest.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_passes_labels_and_milestone(self, service):
        """Should include labels, milestone, and assignees in the payload."""
        service._rest = AsyncMock(return_value={"number": 1})
        await service.create_issue(
            "tok",
            "owner",
            "repo",
            "T",
            "B",
            labels=["bug"],
            milestone=5,
            assignees=["alice"],
        )
        call_kwargs = service._rest.call_args
        payload = call_kwargs.kwargs.get("json") or call_kwargs[1].get("json")
        assert payload["labels"] == ["bug"]
        assert payload["milestone"] == 5
        assert payload["assignees"] == ["alice"]

    @pytest.mark.asyncio
    async def test_404_raises_validation_error(self, service):
        """A 404 RequestFailed is re-raised as ValidationError."""
        resp = Mock(status_code=404)
        service._rest = AsyncMock(side_effect=RequestFailed(resp))
        with pytest.raises(ValidationError, match="missing repository write access"):
            await service.create_issue("tok", "owner", "repo", "T", "B")

    @pytest.mark.asyncio
    async def test_non_404_request_failed_re_raised(self, service):
        """Non-404 RequestFailed is re-raised as-is."""
        resp = Mock(status_code=500)
        service._rest = AsyncMock(side_effect=RequestFailed(resp))
        with pytest.raises(RequestFailed):
            await service.create_issue("tok", "owner", "repo", "T", "B")

    @pytest.mark.asyncio
    async def test_default_labels_empty_list(self, service):
        """When no labels are provided, an empty list is sent."""
        service._rest = AsyncMock(return_value={"number": 1})
        await service.create_issue("tok", "o", "r", "T", "B")
        payload = service._rest.call_args.kwargs.get("json") or service._rest.call_args[1]["json"]
        assert payload["labels"] == []


# ---------------------------------------------------------------------------
# update_issue_body
# ---------------------------------------------------------------------------


class TestUpdateIssueBody:
    """Tests for update_issue_body."""

    @pytest.fixture
    def service(self):
        return GitHubProjectsService()

    @pytest.mark.asyncio
    async def test_success_returns_true(self, service):
        """Successful PATCH returns True."""
        service._rest = AsyncMock(return_value={})
        service._invalidate_cycle_cache = Mock()
        result = await service.update_issue_body("tok", "owner", "repo", 42, "new body")
        assert result is True

    @pytest.mark.asyncio
    async def test_invalidates_cache(self, service):
        """Should invalidate cycle cache for the issue."""
        service._rest = AsyncMock(return_value={})
        service._invalidate_cycle_cache = Mock()
        await service.update_issue_body("tok", "owner", "repo", 42, "new")
        service._invalidate_cycle_cache.assert_called_once_with("issue:owner/repo/42")

    @pytest.mark.asyncio
    async def test_exception_returns_false(self, service):
        """Any exception is caught and returns False."""
        service._rest = AsyncMock(side_effect=RuntimeError("boom"))
        result = await service.update_issue_body("tok", "owner", "repo", 42, "body")
        assert result is False


# ---------------------------------------------------------------------------
# update_issue_state
# ---------------------------------------------------------------------------


class TestUpdateIssueState:
    """Tests for update_issue_state."""

    @pytest.fixture
    def service(self):
        return GitHubProjectsService()

    @pytest.mark.asyncio
    async def test_state_change_calls_rest_patch(self, service):
        """Changing state sends a PATCH request."""
        service._rest = AsyncMock(return_value={})
        service._invalidate_cycle_cache = Mock()
        result = await service.update_issue_state(
            "tok",
            "owner",
            "repo",
            1,
            state="closed",
            state_reason="completed",
        )
        assert result is True
        # First call should be the PATCH
        call = service._rest.call_args_list[0]
        assert call[0][1] == "PATCH"

    @pytest.mark.asyncio
    async def test_labels_add(self, service):
        """Adding labels makes a POST to the labels endpoint."""
        service._rest = AsyncMock(return_value={})
        service._invalidate_cycle_cache = Mock()
        await service.update_issue_state(
            "tok",
            "owner",
            "repo",
            1,
            labels_add=["bug", "urgent"],
        )
        # No state payload → skip PATCH; one POST for labels
        assert service._rest.await_count == 1
        call = service._rest.call_args_list[0]
        assert call[0][1] == "POST"
        assert "labels" in (call[1].get("json") or call.kwargs.get("json", {}))

    @pytest.mark.asyncio
    async def test_labels_remove(self, service):
        """Removing labels makes DELETE requests per label."""
        service._rest = AsyncMock(return_value={})
        service._invalidate_cycle_cache = Mock()
        await service.update_issue_state(
            "tok",
            "owner",
            "repo",
            1,
            labels_remove=["stale", "wontfix"],
        )
        # Two DELETE calls (one per label)
        assert service._rest.await_count == 2

    @pytest.mark.asyncio
    async def test_label_remove_404_ignored(self, service):
        """404 on label removal is silently ignored."""
        resp_404 = Mock(status_code=404)
        service._rest = AsyncMock(side_effect=RequestFailed(resp_404))
        service._invalidate_cycle_cache = Mock()
        result = await service.update_issue_state(
            "tok",
            "owner",
            "repo",
            1,
            labels_remove=["gone"],
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_label_remove_non_404_causes_failure(self, service):
        """Non-404 RequestFailed on label removal returns False."""
        resp_500 = Mock(status_code=500)
        service._rest = AsyncMock(side_effect=RequestFailed(resp_500))
        service._invalidate_cycle_cache = Mock()
        result = await service.update_issue_state(
            "tok",
            "owner",
            "repo",
            1,
            labels_remove=["oops"],
        )
        assert result is False

    @pytest.mark.asyncio
    async def test_state_and_labels_combined(self, service):
        """State change + label add + label remove in one call."""
        service._rest = AsyncMock(return_value={})
        service._invalidate_cycle_cache = Mock()
        result = await service.update_issue_state(
            "tok",
            "owner",
            "repo",
            10,
            state="open",
            labels_add=["reopened"],
            labels_remove=["done"],
        )
        assert result is True
        # PATCH (state) + POST (labels_add) + DELETE (labels_remove)
        assert service._rest.await_count == 3

    @pytest.mark.asyncio
    async def test_exception_returns_false(self, service):
        """Unexpected exceptions return False."""
        service._rest = AsyncMock(side_effect=RuntimeError("oops"))
        result = await service.update_issue_state("tok", "o", "r", 1, state="closed")
        assert result is False


# ---------------------------------------------------------------------------
# create_issue_comment
# ---------------------------------------------------------------------------


class TestCreateIssueComment:
    """Tests for create_issue_comment."""

    @pytest.fixture
    def service(self):
        return GitHubProjectsService()

    @pytest.mark.asyncio
    async def test_success_returns_comment_dict(self, service):
        """201 response returns the comment dict."""
        comment = {"id": 99, "body": "hello"}
        mock_resp = Mock(status_code=201, json=Mock(return_value=comment))
        service._rest_response = AsyncMock(return_value=mock_resp)
        service._invalidate_cycle_cache = Mock()
        result = await service.create_issue_comment("tok", "o", "r", 1, "hello")
        assert result == comment

    @pytest.mark.asyncio
    async def test_200_also_returns_comment(self, service):
        """200 response is also accepted."""
        comment = {"id": 100}
        mock_resp = Mock(status_code=200, json=Mock(return_value=comment))
        service._rest_response = AsyncMock(return_value=mock_resp)
        service._invalidate_cycle_cache = Mock()
        result = await service.create_issue_comment("tok", "o", "r", 1, "hi")
        assert result == comment

    @pytest.mark.asyncio
    async def test_non_success_status_returns_none(self, service):
        """Non-success status returns None."""
        mock_resp = Mock(status_code=403, text="Forbidden")
        service._rest_response = AsyncMock(return_value=mock_resp)
        result = await service.create_issue_comment("tok", "o", "r", 1, "nope")
        assert result is None

    @pytest.mark.asyncio
    async def test_exception_returns_none(self, service):
        """Network exception returns None."""
        service._rest_response = AsyncMock(side_effect=RuntimeError("timeout"))
        result = await service.create_issue_comment("tok", "o", "r", 1, "x")
        assert result is None

    @pytest.mark.asyncio
    async def test_invalidates_cache_on_success(self, service):
        """Cache should be invalidated on successful comment."""
        mock_resp = Mock(status_code=201, json=Mock(return_value={"id": 1}))
        service._rest_response = AsyncMock(return_value=mock_resp)
        service._invalidate_cycle_cache = Mock()
        await service.create_issue_comment("tok", "owner", "repo", 5, "c")
        service._invalidate_cycle_cache.assert_called_once_with("issue:owner/repo/5")


# ---------------------------------------------------------------------------
# add_issue_to_project
# ---------------------------------------------------------------------------


class TestAddIssueToProject:
    """Tests for add_issue_to_project."""

    @pytest.fixture
    def service(self):
        return GitHubProjectsService()

    @pytest.mark.asyncio
    async def test_returns_item_id_when_verified(self, service):
        """Returns GraphQL item ID when verification passes."""
        service._graphql = AsyncMock(
            return_value={
                "addProjectV2ItemById": {"item": {"id": "PVTI_abc"}},
            }
        )
        service._verify_item_on_project = AsyncMock(return_value=True)
        result = await service.add_issue_to_project("tok", "PVT_1", "I_1")
        assert result == "PVTI_abc"

    @pytest.mark.asyncio
    async def test_falls_back_to_rest_when_not_verified(self, service):
        """Falls back to REST when verification fails and database_id provided."""
        service._graphql = AsyncMock(
            return_value={
                "addProjectV2ItemById": {"item": {"id": "PVTI_gql"}},
            }
        )
        service._verify_item_on_project = AsyncMock(return_value=False)
        service._add_issue_to_project_rest = AsyncMock(return_value="PVTI_rest")
        result = await service.add_issue_to_project("tok", "PVT_1", "I_1", issue_database_id=42)
        assert result == "PVTI_rest"

    @pytest.mark.asyncio
    async def test_returns_gql_id_when_no_database_id_and_not_verified(self, service):
        """Returns GraphQL item ID when not verified but no database_id for fallback."""
        service._graphql = AsyncMock(
            return_value={
                "addProjectV2ItemById": {"item": {"id": "PVTI_only"}},
            }
        )
        service._verify_item_on_project = AsyncMock(return_value=False)
        result = await service.add_issue_to_project("tok", "PVT_1", "I_1")
        assert result == "PVTI_only"


# ---------------------------------------------------------------------------
# _verify_item_on_project
# ---------------------------------------------------------------------------


class TestVerifyItemOnProject:
    """Tests for _verify_item_on_project."""

    @pytest.fixture
    def service(self):
        return GitHubProjectsService()

    @pytest.mark.asyncio
    async def test_returns_true_when_item_found(self, service):
        """Returns True when the issue is on the project."""
        service._graphql = AsyncMock(
            return_value={
                "node": {
                    "projectItems": {
                        "nodes": [
                            {
                                "isArchived": False,
                                "project": {"id": "PVT_1"},
                            }
                        ]
                    }
                }
            }
        )
        with patch("src.services.github_projects.issues.asyncio.sleep", new_callable=AsyncMock):
            result = await service._verify_item_on_project("tok", "I_1", "PVT_1")
        assert result is True

    @pytest.mark.asyncio
    async def test_returns_false_when_wrong_project(self, service):
        """Returns False when the issue is on a different project."""
        service._graphql = AsyncMock(
            return_value={
                "node": {
                    "projectItems": {
                        "nodes": [
                            {
                                "isArchived": False,
                                "project": {"id": "PVT_other"},
                            }
                        ]
                    }
                }
            }
        )
        with patch("src.services.github_projects.issues.asyncio.sleep", new_callable=AsyncMock):
            result = await service._verify_item_on_project("tok", "I_1", "PVT_1")
        assert result is False

    @pytest.mark.asyncio
    async def test_returns_false_when_archived(self, service):
        """Returns False when the matching item is archived."""
        service._graphql = AsyncMock(
            return_value={
                "node": {
                    "projectItems": {
                        "nodes": [
                            {
                                "isArchived": True,
                                "project": {"id": "PVT_1"},
                            }
                        ]
                    }
                }
            }
        )
        with patch("src.services.github_projects.issues.asyncio.sleep", new_callable=AsyncMock):
            result = await service._verify_item_on_project("tok", "I_1", "PVT_1")
        assert result is False

    @pytest.mark.asyncio
    async def test_returns_false_when_no_items(self, service):
        """Returns False when projectItems is empty."""
        service._graphql = AsyncMock(return_value={"node": {"projectItems": {"nodes": []}}})
        with patch("src.services.github_projects.issues.asyncio.sleep", new_callable=AsyncMock):
            result = await service._verify_item_on_project("tok", "I_1", "PVT_1")
        assert result is False

    @pytest.mark.asyncio
    async def test_returns_false_on_exception(self, service):
        """Returns False when the GraphQL call fails."""
        service._graphql = AsyncMock(side_effect=RuntimeError("boom"))
        with patch("src.services.github_projects.issues.asyncio.sleep", new_callable=AsyncMock):
            result = await service._verify_item_on_project("tok", "I_1", "PVT_1")
        assert result is False


# ---------------------------------------------------------------------------
# get_issue_with_comments
# ---------------------------------------------------------------------------


class TestGetIssueWithComments:
    """Tests for get_issue_with_comments."""

    @pytest.fixture
    def service(self):
        return GitHubProjectsService()

    @pytest.mark.asyncio
    async def test_single_page(self, service):
        """Fetches title, body, and comments from a single page."""
        service._graphql = AsyncMock(
            return_value={
                "repository": {
                    "issue": {
                        "title": "Bug",
                        "body": "Details",
                        "author": {"login": "alice"},
                        "comments": {
                            "nodes": [
                                {
                                    "author": {"login": "bob"},
                                    "body": "Fix it",
                                    "createdAt": "2024-01-01",
                                },
                            ],
                            "pageInfo": {"hasNextPage": False, "endCursor": None},
                        },
                    }
                }
            }
        )
        result = await service.get_issue_with_comments("tok", "o", "r", 1)
        assert result["title"] == "Bug"
        assert result["body"] == "Details"
        assert len(result["comments"]) == 1
        assert result["user"]["login"] == "alice"

    @pytest.mark.asyncio
    async def test_pagination(self, service):
        """Paginated comments across two pages."""
        page1 = {
            "repository": {
                "issue": {
                    "title": "Issue",
                    "body": "Body",
                    "author": {"login": "u"},
                    "comments": {
                        "nodes": [{"author": {"login": "a"}, "body": "c1", "createdAt": ""}],
                        "pageInfo": {"hasNextPage": True, "endCursor": "cur1"},
                    },
                }
            }
        }
        page2 = {
            "repository": {
                "issue": {
                    "title": "Issue",
                    "body": "Body",
                    "author": {"login": "u"},
                    "comments": {
                        "nodes": [{"author": {"login": "b"}, "body": "c2", "createdAt": ""}],
                        "pageInfo": {"hasNextPage": False, "endCursor": None},
                    },
                }
            }
        }
        service._graphql = AsyncMock(side_effect=[page1, page2])
        result = await service.get_issue_with_comments("tok", "o", "r", 1)
        assert len(result["comments"]) == 2

    @pytest.mark.asyncio
    async def test_returns_cached_result(self, service):
        """Returns cached result without calling GraphQL."""
        service._cycle_cache["issue:o/r/1"] = {
            "title": "cached",
            "body": "",
            "comments": [],
            "user": {"login": ""},
        }
        service._graphql = AsyncMock()
        result = await service.get_issue_with_comments("tok", "o", "r", 1)
        assert result["title"] == "cached"
        service._graphql.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_exception_returns_empty_dict(self, service):
        """Exception returns a dict with empty fields."""
        service._graphql = AsyncMock(side_effect=RuntimeError("fail"))
        result = await service.get_issue_with_comments("tok", "o", "r", 1)
        assert result["title"] == ""
        assert result["comments"] == []


# ---------------------------------------------------------------------------
# create_sub_issue
# ---------------------------------------------------------------------------


class TestCreateSubIssue:
    """Tests for create_sub_issue."""

    @pytest.fixture
    def service(self):
        return GitHubProjectsService()

    @pytest.mark.asyncio
    async def test_creates_and_attaches_sub_issue(self, service):
        """Creates issue then attaches as sub-issue."""
        sub = {"number": 10, "id": 100, "node_id": "I_sub"}
        service.create_issue = AsyncMock(return_value=sub)
        service._rest = AsyncMock(return_value={})
        result = await service.create_sub_issue(
            "tok",
            "owner",
            "repo",
            parent_issue_number=1,
            title="Sub",
            body="Detail",
            labels=["task"],
        )
        assert result == sub
        service.create_issue.assert_awaited_once()
        # Verify sub-issue attachment call
        service._rest.assert_awaited_once()
        call_args = service._rest.call_args
        assert "/sub_issues" in call_args[0][2]

    @pytest.mark.asyncio
    async def test_returns_issue_even_when_attach_fails(self, service):
        """Returns the created issue even if sub-issue attachment fails."""
        sub = {"number": 11, "id": 101}
        service.create_issue = AsyncMock(return_value=sub)
        service._rest = AsyncMock(side_effect=RuntimeError("attach failed"))
        result = await service.create_sub_issue(
            "tok",
            "o",
            "r",
            parent_issue_number=1,
            title="S",
            body="B",
        )
        assert result == sub


# ---------------------------------------------------------------------------
# assign_issue
# ---------------------------------------------------------------------------


class TestAssignIssue:
    """Tests for assign_issue."""

    @pytest.fixture
    def service(self):
        return GitHubProjectsService()

    @pytest.mark.asyncio
    async def test_success_returns_true(self, service):
        """200 status means assignment succeeded."""
        mock_resp = Mock(status_code=200)
        service._rest_response = AsyncMock(return_value=mock_resp)
        result = await service.assign_issue("tok", "o", "r", 1, ["alice"])
        assert result is True

    @pytest.mark.asyncio
    async def test_failure_returns_false(self, service):
        """Non-200 returns False."""
        mock_resp = Mock(status_code=422, text="Unprocessable")
        service._rest_response = AsyncMock(return_value=mock_resp)
        result = await service.assign_issue("tok", "o", "r", 1, ["ghost"])
        assert result is False


# ---------------------------------------------------------------------------
# check_issue_closed
# ---------------------------------------------------------------------------


class TestCheckIssueClosed:
    """Tests for check_issue_closed."""

    @pytest.fixture
    def service(self):
        return GitHubProjectsService()

    @pytest.mark.asyncio
    async def test_closed_issue_returns_true(self, service):
        service._rest = AsyncMock(return_value={"state": "closed"})
        assert await service.check_issue_closed("tok", "o", "r", 1) is True

    @pytest.mark.asyncio
    async def test_open_issue_returns_false(self, service):
        service._rest = AsyncMock(return_value={"state": "open"})
        assert await service.check_issue_closed("tok", "o", "r", 1) is False

    @pytest.mark.asyncio
    async def test_404_treated_as_closed(self, service):
        resp = Mock(status_code=404)
        service._rest = AsyncMock(side_effect=RequestFailed(resp))
        assert await service.check_issue_closed("tok", "o", "r", 1) is True

    @pytest.mark.asyncio
    async def test_410_treated_as_closed(self, service):
        resp = Mock(status_code=410)
        service._rest = AsyncMock(side_effect=RequestFailed(resp))
        assert await service.check_issue_closed("tok", "o", "r", 1) is True

    @pytest.mark.asyncio
    async def test_500_returns_false(self, service):
        resp = Mock(status_code=500)
        service._rest = AsyncMock(side_effect=RequestFailed(resp))
        assert await service.check_issue_closed("tok", "o", "r", 1) is False


# ---------------------------------------------------------------------------
# validate_assignee
# ---------------------------------------------------------------------------


class TestValidateAssignee:
    """Tests for validate_assignee."""

    @pytest.fixture
    def service(self):
        return GitHubProjectsService()

    @pytest.mark.asyncio
    async def test_204_means_valid(self, service):
        mock_resp = Mock(status_code=204)
        service._rest_response = AsyncMock(return_value=mock_resp)
        assert await service.validate_assignee("tok", "o", "r", "alice") is True

    @pytest.mark.asyncio
    async def test_404_means_invalid(self, service):
        mock_resp = Mock(status_code=404)
        service._rest_response = AsyncMock(return_value=mock_resp)
        assert await service.validate_assignee("tok", "o", "r", "ghost") is False
