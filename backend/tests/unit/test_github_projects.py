"""Unit tests for GitHub Projects service - Copilot custom agent assignment."""

import pytest
from unittest.mock import AsyncMock, Mock, patch, MagicMock
import httpx

from src.services.github_projects import GitHubProjectsService


class TestGetIssueWithComments:
    """Tests for fetching issue details with comments."""

    @pytest.fixture
    def service(self):
        """Create a GitHubProjectsService instance."""
        return GitHubProjectsService()

    @pytest.mark.asyncio
    async def test_get_issue_with_comments_success(self, service):
        """Should fetch issue title, body, and comments."""
        mock_response = {
            "repository": {
                "issue": {
                    "id": "I_123",
                    "title": "Test Issue",
                    "body": "Issue description here",
                    "comments": {
                        "nodes": [
                            {
                                "id": "C_1",
                                "author": {"login": "user1"},
                                "body": "First comment",
                                "createdAt": "2026-01-01T10:00:00Z",
                            },
                            {
                                "id": "C_2",
                                "author": {"login": "user2"},
                                "body": "Second comment",
                                "createdAt": "2026-01-02T10:00:00Z",
                            },
                        ]
                    },
                }
            }
        }

        with patch.object(service, "_graphql", new_callable=AsyncMock) as mock_graphql:
            mock_graphql.return_value = mock_response

            result = await service.get_issue_with_comments(
                access_token="test-token",
                owner="test-owner",
                repo="test-repo",
                issue_number=42,
            )

            assert result["title"] == "Test Issue"
            assert result["body"] == "Issue description here"
            assert len(result["comments"]) == 2
            assert result["comments"][0]["author"] == "user1"
            assert result["comments"][0]["body"] == "First comment"
            assert result["comments"][1]["author"] == "user2"

    @pytest.mark.asyncio
    async def test_get_issue_with_comments_no_comments(self, service):
        """Should handle issues with no comments."""
        mock_response = {
            "repository": {
                "issue": {
                    "id": "I_123",
                    "title": "No Comments Issue",
                    "body": "Just a description",
                    "comments": {"nodes": []},
                }
            }
        }

        with patch.object(service, "_graphql", new_callable=AsyncMock) as mock_graphql:
            mock_graphql.return_value = mock_response

            result = await service.get_issue_with_comments(
                access_token="test-token",
                owner="test-owner",
                repo="test-repo",
                issue_number=1,
            )

            assert result["title"] == "No Comments Issue"
            assert result["comments"] == []

    @pytest.mark.asyncio
    async def test_get_issue_with_comments_error_returns_empty(self, service):
        """Should return empty dict on error."""
        with patch.object(service, "_graphql", new_callable=AsyncMock) as mock_graphql:
            mock_graphql.side_effect = Exception("GraphQL error")

            result = await service.get_issue_with_comments(
                access_token="test-token",
                owner="test-owner",
                repo="test-repo",
                issue_number=42,
            )

            assert result == {"title": "", "body": "", "comments": []}


class TestFormatIssueContextAsPrompt:
    """Tests for formatting issue context as agent prompt."""

    @pytest.fixture
    def service(self):
        """Create a GitHubProjectsService instance."""
        return GitHubProjectsService()

    def test_format_with_all_fields(self, service):
        """Should format title, body, and comments into prompt."""
        issue_data = {
            "title": "Add feature X",
            "body": "We need to implement feature X for users.",
            "comments": [
                {
                    "author": "alice",
                    "body": "I think we should use approach A",
                    "created_at": "2026-01-01T10:00:00Z",
                },
                {
                    "author": "bob",
                    "body": "Agreed, let's also consider edge cases",
                    "created_at": "2026-01-02T10:00:00Z",
                },
            ],
        }

        result = service.format_issue_context_as_prompt(issue_data)

        assert "## Issue Title" in result
        assert "Add feature X" in result
        assert "## Issue Description" in result
        assert "We need to implement feature X" in result
        assert "## Comments and Discussion" in result
        assert "Comment 1 by @alice" in result
        assert "approach A" in result
        assert "Comment 2 by @bob" in result
        assert "edge cases" in result

    def test_format_with_empty_body(self, service):
        """Should handle empty body gracefully."""
        issue_data = {
            "title": "Quick fix",
            "body": "",
            "comments": [],
        }

        result = service.format_issue_context_as_prompt(issue_data)

        assert "## Issue Title" in result
        assert "Quick fix" in result
        assert "## Issue Description" not in result

    def test_format_with_no_comments(self, service):
        """Should not include comments section when empty."""
        issue_data = {
            "title": "New feature",
            "body": "Description here",
            "comments": [],
        }

        result = service.format_issue_context_as_prompt(issue_data)

        assert "## Issue Title" in result
        assert "## Issue Description" in result
        assert "## Comments and Discussion" not in result


class TestAssignCopilotToIssue:
    """Tests for assigning Copilot with custom agents."""

    @pytest.fixture
    def service(self):
        """Create a GitHubProjectsService instance."""
        return GitHubProjectsService()

    @pytest.mark.asyncio
    async def test_assign_copilot_rest_api_success(self, service):
        """Should successfully assign Copilot via REST API."""
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "assignees": [{"login": "copilot-swe-agent[bot]"}]
        }

        with patch.object(service, "_client") as mock_client:
            mock_client.post = AsyncMock(return_value=mock_response)

            result = await service.assign_copilot_to_issue(
                access_token="test-token",
                owner="test-owner",
                repo="test-repo",
                issue_node_id="I_123",
                issue_number=42,
                custom_agent="speckit.specify",
                custom_instructions="Test instructions",
            )

            assert result is True
            mock_client.post.assert_called_once()
            call_args = mock_client.post.call_args
            assert "assignees" in call_args.kwargs["json"]
            assert call_args.kwargs["json"]["assignees"] == ["copilot-swe-agent[bot]"]
            assert call_args.kwargs["json"]["agent_assignment"]["custom_agent"] == "speckit.specify"

    @pytest.mark.asyncio
    async def test_assign_copilot_rest_api_with_custom_instructions(self, service):
        """Should include custom instructions in payload."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "assignees": [{"login": "copilot-swe-agent[bot]"}]
        }

        with patch.object(service, "_client") as mock_client:
            mock_client.post = AsyncMock(return_value=mock_response)

            await service.assign_copilot_to_issue(
                access_token="test-token",
                owner="owner",
                repo="repo",
                issue_node_id="I_123",
                issue_number=1,
                custom_agent="speckit.specify",
                custom_instructions="## Issue Title\nTest\n\n## Description\nContent",
            )

            call_args = mock_client.post.call_args
            payload = call_args.kwargs["json"]
            assert payload["agent_assignment"]["custom_instructions"] == "## Issue Title\nTest\n\n## Description\nContent"
            assert payload["agent_assignment"]["custom_agent"] == "speckit.specify"

    @pytest.mark.asyncio
    async def test_assign_copilot_falls_back_to_graphql_on_rest_failure(self, service):
        """Should fall back to GraphQL when REST API fails."""
        mock_rest_response = Mock()
        mock_rest_response.status_code = 422
        mock_rest_response.text = "Validation failed"
        mock_rest_response.headers = {"X-Request-Id": "123"}

        with patch.object(service, "_client") as mock_client:
            mock_client.post = AsyncMock(return_value=mock_rest_response)

            with patch.object(
                service, "_assign_copilot_graphql", new_callable=AsyncMock
            ) as mock_graphql:
                mock_graphql.return_value = True

                result = await service.assign_copilot_to_issue(
                    access_token="test-token",
                    owner="owner",
                    repo="repo",
                    issue_node_id="I_123",
                    issue_number=42,
                    custom_agent="speckit.specify",
                )

                assert result is True
                mock_graphql.assert_called_once()

    @pytest.mark.asyncio
    async def test_assign_copilot_without_issue_number_uses_graphql(self, service):
        """Should use GraphQL directly when issue_number is not provided."""
        with patch.object(
            service, "_assign_copilot_graphql", new_callable=AsyncMock
        ) as mock_graphql:
            mock_graphql.return_value = True

            result = await service.assign_copilot_to_issue(
                access_token="test-token",
                owner="owner",
                repo="repo",
                issue_node_id="I_123",
                issue_number=None,  # No issue number
                custom_agent="speckit.specify",
            )

            assert result is True
            mock_graphql.assert_called_once()


class TestAssignCopilotGraphQL:
    """Tests for GraphQL-based Copilot assignment."""

    @pytest.fixture
    def service(self):
        """Create a GitHubProjectsService instance."""
        return GitHubProjectsService()

    @pytest.mark.asyncio
    async def test_graphql_assign_success(self, service):
        """Should successfully assign via GraphQL."""
        with patch.object(
            service, "get_copilot_bot_id", new_callable=AsyncMock
        ) as mock_get_bot:
            mock_get_bot.return_value = ("BOT_ID_123", "REPO_ID_456")

            with patch.object(service, "_graphql", new_callable=AsyncMock) as mock_graphql:
                mock_graphql.return_value = {
                    "addAssigneesToAssignable": {
                        "assignable": {
                            "assignees": {"nodes": [{"login": "copilot-swe-agent"}]}
                        }
                    }
                }

                result = await service._assign_copilot_graphql(
                    access_token="test-token",
                    owner="owner",
                    repo="repo",
                    issue_node_id="I_123",
                    custom_agent="speckit.specify",
                    custom_instructions="Test prompt",
                )

                assert result is True

    @pytest.mark.asyncio
    async def test_graphql_assign_no_bot_available(self, service):
        """Should return False when Copilot bot is not available."""
        with patch.object(
            service, "get_copilot_bot_id", new_callable=AsyncMock
        ) as mock_get_bot:
            mock_get_bot.return_value = (None, "REPO_ID_456")

            result = await service._assign_copilot_graphql(
                access_token="test-token",
                owner="owner",
                repo="repo",
                issue_node_id="I_123",
            )

            assert result is False

    @pytest.mark.asyncio
    async def test_graphql_assign_no_repo_id(self, service):
        """Should return False when repository ID is not found."""
        with patch.object(
            service, "get_copilot_bot_id", new_callable=AsyncMock
        ) as mock_get_bot:
            mock_get_bot.return_value = ("BOT_ID_123", None)

            result = await service._assign_copilot_graphql(
                access_token="test-token",
                owner="owner",
                repo="repo",
                issue_node_id="I_123",
            )

            assert result is False


class TestGetCopilotBotId:
    """Tests for getting Copilot bot ID."""

    @pytest.fixture
    def service(self):
        """Create a GitHubProjectsService instance."""
        return GitHubProjectsService()

    @pytest.mark.asyncio
    async def test_get_copilot_bot_id_found(self, service):
        """Should return bot ID when Copilot is available."""
        mock_response = {
            "repository": {
                "id": "REPO_123",
                "suggestedActors": {
                    "nodes": [
                        {"login": "copilot-swe-agent", "__typename": "Bot", "id": "BOT_456"},
                        {"login": "other-user", "__typename": "User", "id": "USER_789"},
                    ]
                },
            }
        }

        with patch.object(service, "_graphql", new_callable=AsyncMock) as mock_graphql:
            mock_graphql.return_value = mock_response

            bot_id, repo_id = await service.get_copilot_bot_id(
                access_token="test-token",
                owner="owner",
                repo="repo",
            )

            assert bot_id == "BOT_456"
            assert repo_id == "REPO_123"

    @pytest.mark.asyncio
    async def test_get_copilot_bot_id_not_available(self, service):
        """Should return None when Copilot is not in suggested actors."""
        mock_response = {
            "repository": {
                "id": "REPO_123",
                "suggestedActors": {
                    "nodes": [
                        {"login": "some-user", "__typename": "User", "id": "USER_123"},
                    ]
                },
            }
        }

        with patch.object(service, "_graphql", new_callable=AsyncMock) as mock_graphql:
            mock_graphql.return_value = mock_response

            bot_id, repo_id = await service.get_copilot_bot_id(
                access_token="test-token",
                owner="owner",
                repo="repo",
            )

            assert bot_id is None
            assert repo_id == "REPO_123"

    @pytest.mark.asyncio
    async def test_get_copilot_bot_id_error(self, service):
        """Should return None on error."""
        with patch.object(service, "_graphql", new_callable=AsyncMock) as mock_graphql:
            mock_graphql.side_effect = Exception("GraphQL error")

            bot_id, repo_id = await service.get_copilot_bot_id(
                access_token="test-token",
                owner="owner",
                repo="repo",
            )

            assert bot_id is None
            assert repo_id is None


class TestLinkedPullRequests:
    """Tests for getting linked pull requests."""

    @pytest.fixture
    def service(self):
        """Create a GitHubProjectsService instance."""
        return GitHubProjectsService()

    @pytest.mark.asyncio
    async def test_get_linked_prs_success(self, service):
        """Should return linked PRs for an issue."""
        mock_response = {
            "repository": {
                "issue": {
                    "id": "I_123",
                    "title": "Test Issue",
                    "state": "OPEN",
                    "timelineItems": {
                        "nodes": [
                            {
                                "subject": {
                                    "id": "PR_1",
                                    "number": 42,
                                    "title": "Fix issue",
                                    "state": "OPEN",
                                    "isDraft": False,
                                    "url": "https://github.com/owner/repo/pull/42",
                                    "author": {"login": "copilot-swe-agent[bot]"},
                                    "createdAt": "2026-01-01T10:00:00Z",
                                    "updatedAt": "2026-01-02T10:00:00Z",
                                }
                            }
                        ]
                    },
                }
            }
        }

        with patch.object(service, "_graphql", new_callable=AsyncMock) as mock_graphql:
            mock_graphql.return_value = mock_response

            prs = await service.get_linked_pull_requests(
                access_token="test-token",
                owner="owner",
                repo="repo",
                issue_number=1,
            )

            assert len(prs) == 1
            assert prs[0]["number"] == 42
            assert prs[0]["is_draft"] is False
            assert prs[0]["author"] == "copilot-swe-agent[bot]"

    @pytest.mark.asyncio
    async def test_get_linked_prs_no_prs(self, service):
        """Should return empty list when no PRs linked."""
        mock_response = {
            "repository": {
                "issue": {
                    "id": "I_123",
                    "timelineItems": {"nodes": []},
                }
            }
        }

        with patch.object(service, "_graphql", new_callable=AsyncMock) as mock_graphql:
            mock_graphql.return_value = mock_response

            prs = await service.get_linked_pull_requests(
                access_token="test-token",
                owner="owner",
                repo="repo",
                issue_number=1,
            )

            assert prs == []

    @pytest.mark.asyncio
    async def test_get_linked_prs_error(self, service):
        """Should return empty list on error."""
        with patch.object(service, "_graphql", new_callable=AsyncMock) as mock_graphql:
            mock_graphql.side_effect = Exception("GraphQL error")

            prs = await service.get_linked_pull_requests(
                access_token="test-token",
                owner="owner",
                repo="repo",
                issue_number=1,
            )

            assert prs == []


class TestMarkPrReadyForReview:
    """Tests for marking PR ready for review."""

    @pytest.fixture
    def service(self):
        """Create a GitHubProjectsService instance."""
        return GitHubProjectsService()

    @pytest.mark.asyncio
    async def test_mark_pr_ready_success(self, service):
        """Should successfully mark PR as ready."""
        mock_response = {
            "markPullRequestReadyForReview": {
                "pullRequest": {
                    "id": "PR_123",
                    "number": 42,
                    "isDraft": False,
                    "state": "OPEN",
                    "url": "https://github.com/owner/repo/pull/42",
                }
            }
        }

        with patch.object(service, "_graphql", new_callable=AsyncMock) as mock_graphql:
            mock_graphql.return_value = mock_response

            result = await service.mark_pr_ready_for_review(
                access_token="test-token",
                pr_node_id="PR_123",
            )

            assert result is True

    @pytest.mark.asyncio
    async def test_mark_pr_ready_failure(self, service):
        """Should return False on failure."""
        mock_response = {
            "markPullRequestReadyForReview": {
                "pullRequest": {
                    "id": "PR_123",
                    "number": 42,
                    "isDraft": True,  # Still draft
                    "state": "OPEN",
                }
            }
        }

        with patch.object(service, "_graphql", new_callable=AsyncMock) as mock_graphql:
            mock_graphql.return_value = mock_response

            result = await service.mark_pr_ready_for_review(
                access_token="test-token",
                pr_node_id="PR_123",
            )

            assert result is False

    @pytest.mark.asyncio
    async def test_mark_pr_ready_error(self, service):
        """Should return False on error."""
        with patch.object(service, "_graphql", new_callable=AsyncMock) as mock_graphql:
            mock_graphql.side_effect = Exception("GraphQL error")

            result = await service.mark_pr_ready_for_review(
                access_token="test-token",
                pr_node_id="PR_123",
            )

            assert result is False


class TestCheckCopilotFinishedEvents:
    """Tests for _check_copilot_finished_events helper method."""

    @pytest.fixture
    def service(self):
        """Create a GitHubProjectsService instance."""
        return GitHubProjectsService()

    def test_returns_true_for_copilot_work_finished_event(self, service):
        """Should return True when copilot_work_finished event exists."""
        events = [
            {"event": "copilot_work_started"},
            {"event": "committed"},
            {"event": "copilot_work_finished"},
        ]
        assert service._check_copilot_finished_events(events) is True

    def test_returns_true_for_review_requested_from_copilot(self, service):
        """Should return True when review_requested event from Copilot exists."""
        events = [
            {"event": "copilot_work_started"},
            {
                "event": "review_requested",
                "review_requester": {"login": "Copilot"},
                "requested_reviewer": {"login": "some-user"},
            },
        ]
        assert service._check_copilot_finished_events(events) is True

    def test_returns_false_for_no_finish_events(self, service):
        """Should return False when no finish events exist."""
        events = [
            {"event": "copilot_work_started"},
            {"event": "committed"},
            {"event": "assigned"},
        ]
        assert service._check_copilot_finished_events(events) is False

    def test_returns_false_for_review_requested_not_from_copilot(self, service):
        """Should return False when review_requested is from a user, not Copilot."""
        events = [
            {
                "event": "review_requested",
                "review_requester": {"login": "some-user"},  # Not Copilot
                "requested_reviewer": {"login": "another-user"},
            },
        ]
        assert service._check_copilot_finished_events(events) is False

    def test_returns_false_for_empty_events(self, service):
        """Should return False for empty events list."""
        assert service._check_copilot_finished_events([]) is False

    def test_handles_missing_login_gracefully(self, service):
        """Should handle missing login field gracefully."""
        events = [
            {
                "event": "review_requested",
                "review_requester": {},  # Missing login
            },
        ]
        assert service._check_copilot_finished_events(events) is False


class TestCheckCopilotPrCompletion:
    """Tests for checking Copilot PR completion.
    
    Copilot is detected as "finished work" when timeline has:
    - 'copilot_work_finished' event, OR
    - 'review_requested' event where review_requester is Copilot
    """

    @pytest.fixture
    def service(self):
        """Create a GitHubProjectsService instance."""
        return GitHubProjectsService()

    @pytest.mark.asyncio
    async def test_copilot_draft_pr_with_commits_is_finished(self, service):
        """Should detect finished Copilot PR (draft + has finish events)."""
        linked_prs = [
            {
                "id": "PR_123",
                "number": 42,
                "title": "Fix issue",
                "state": "OPEN",
                "is_draft": True,  # Still draft (Copilot doesn't mark ready)
                "url": "https://github.com/owner/repo/pull/42",
                "author": "copilot-swe-agent[bot]",
            }
        ]
        
        pr_details = {
            "id": "PR_123",
            "number": 42,
            "last_commit": {"sha": "abc1234567890"},
        }
        
        # Timeline events indicating Copilot finished work
        timeline_events = [
            {"event": "copilot_work_finished"}
        ]

        with patch.object(
            service, "get_linked_pull_requests", new_callable=AsyncMock
        ) as mock_get_prs, patch.object(
            service, "get_pull_request", new_callable=AsyncMock
        ) as mock_get_pr, patch.object(
            service, "get_pr_timeline_events", new_callable=AsyncMock
        ) as mock_get_timeline:
            mock_get_prs.return_value = linked_prs
            mock_get_pr.return_value = pr_details
            mock_get_timeline.return_value = timeline_events

            result = await service.check_copilot_pr_completion(
                access_token="test-token",
                owner="owner",
                repo="repo",
                issue_number=1,
            )

            assert result is not None
            assert result["number"] == 42
            assert result["is_draft"] is True
            assert result["copilot_finished"] is True

    @pytest.mark.asyncio
    async def test_copilot_finished_via_review_requested_event(self, service):
        """Should detect Copilot finished when review_requested event from Copilot exists."""
        linked_prs = [
            {
                "id": "PR_123",
                "number": 42,
                "title": "Fix issue",
                "state": "OPEN",
                "is_draft": True,
                "url": "https://github.com/owner/repo/pull/42",
                "author": "copilot-swe-agent[bot]",
            }
        ]
        
        pr_details = {
            "id": "PR_123",
            "number": 42,
            "last_commit": {"sha": "abc1234567890"},
        }
        
        # Timeline events with review_requested from Copilot
        timeline_events = [
            {"event": "copilot_work_started"},
            {
                "event": "review_requested",
                "review_requester": {"login": "Copilot"},
                "requested_reviewer": {"login": "some-user"},
            }
        ]

        with patch.object(
            service, "get_linked_pull_requests", new_callable=AsyncMock
        ) as mock_get_prs, patch.object(
            service, "get_pull_request", new_callable=AsyncMock
        ) as mock_get_pr, patch.object(
            service, "get_pr_timeline_events", new_callable=AsyncMock
        ) as mock_get_timeline:
            mock_get_prs.return_value = linked_prs
            mock_get_pr.return_value = pr_details
            mock_get_timeline.return_value = timeline_events

            result = await service.check_copilot_pr_completion(
                access_token="test-token",
                owner="owner",
                repo="repo",
                issue_number=1,
            )

            assert result is not None
            assert result["number"] == 42
            assert result["copilot_finished"] is True

    @pytest.mark.asyncio
    async def test_copilot_pr_already_ready_is_finished(self, service):
        """Should detect already-ready Copilot PR (edge case)."""
        linked_prs = [
            {
                "id": "PR_123",
                "number": 42,
                "title": "Fix issue",
                "state": "OPEN",
                "is_draft": False,  # Already marked ready (manual or edge case)
                "url": "https://github.com/owner/repo/pull/42",
                "author": "copilot-swe-agent[bot]",
            }
        ]
        
        pr_details = {
            "id": "PR_123",
            "number": 42,
        }

        with patch.object(
            service, "get_linked_pull_requests", new_callable=AsyncMock
        ) as mock_get_prs, patch.object(
            service, "get_pull_request", new_callable=AsyncMock
        ) as mock_get_pr:
            mock_get_prs.return_value = linked_prs
            mock_get_pr.return_value = pr_details

            result = await service.check_copilot_pr_completion(
                access_token="test-token",
                owner="owner",
                repo="repo",
                issue_number=1,
            )

            assert result is not None
            assert result["number"] == 42
            assert result["is_draft"] is False

    @pytest.mark.asyncio
    async def test_no_copilot_pr(self, service):
        """Should return None when no Copilot PR exists."""
        linked_prs = [
            {
                "id": "PR_123",
                "number": 42,
                "state": "OPEN",
                "is_draft": False,
                "author": "human-user",  # Not Copilot
            }
        ]

        with patch.object(
            service, "get_linked_pull_requests", new_callable=AsyncMock
        ) as mock_get_prs:
            mock_get_prs.return_value = linked_prs

            result = await service.check_copilot_pr_completion(
                access_token="test-token",
                owner="owner",
                repo="repo",
                issue_number=1,
            )

            assert result is None

    @pytest.mark.asyncio
    async def test_copilot_pr_closed(self, service):
        """Should return None when Copilot PR is closed/merged."""
        linked_prs = [
            {
                "id": "PR_123",
                "number": 42,
                "state": "MERGED",  # Already merged
                "is_draft": False,
                "author": "copilot-swe-agent[bot]",
            }
        ]

        with patch.object(
            service, "get_linked_pull_requests", new_callable=AsyncMock
        ) as mock_get_prs:
            mock_get_prs.return_value = linked_prs

            result = await service.check_copilot_pr_completion(
                access_token="test-token",
                owner="owner",
                repo="repo",
                issue_number=1,
            )

            assert result is None

    @pytest.mark.asyncio
    async def test_copilot_draft_pr_no_commits_not_finished(self, service):
        """Should return None when Copilot PR has no finish events yet."""
        linked_prs = [
            {
                "id": "PR_123",
                "number": 42,
                "title": "WIP: Fix issue",
                "state": "OPEN",
                "is_draft": True,
                "url": "https://github.com/owner/repo/pull/42",
                "author": "copilot-swe-agent[bot]",
            }
        ]
        
        pr_details = {
            "id": "PR_123",
            "number": 42,
            "check_status": None,
            "last_commit": None,
        }
        
        # No finish events yet - Copilot still working
        timeline_events = [
            {"event": "copilot_work_started"},
            {"event": "committed"},
        ]

        with patch.object(
            service, "get_linked_pull_requests", new_callable=AsyncMock
        ) as mock_get_prs, patch.object(
            service, "get_pull_request", new_callable=AsyncMock
        ) as mock_get_pr, patch.object(
            service, "get_pr_timeline_events", new_callable=AsyncMock
        ) as mock_get_timeline:
            mock_get_prs.return_value = linked_prs
            mock_get_pr.return_value = pr_details
            mock_get_timeline.return_value = timeline_events

            result = await service.check_copilot_pr_completion(
                access_token="test-token",
                owner="owner",
                repo="repo",
                issue_number=1,
            )

            assert result is None

    @pytest.mark.asyncio
    async def test_copilot_with_alternative_bot_name(self, service):
        """Should detect Copilot PR with 'copilot' in author name."""
        linked_prs = [
            {
                "id": "PR_123",
                "number": 42,
                "title": "Fix issue",
                "state": "OPEN",
                "is_draft": False,
                "url": "https://github.com/owner/repo/pull/42",
                "author": "copilot[bot]",  # Alternative Copilot bot name
            }
        ]
        
        pr_details = {
            "id": "PR_123",
            "number": 42,
        }

        with patch.object(
            service, "get_linked_pull_requests", new_callable=AsyncMock
        ) as mock_get_prs, patch.object(
            service, "get_pull_request", new_callable=AsyncMock
        ) as mock_get_pr:
            mock_get_prs.return_value = linked_prs
            mock_get_pr.return_value = pr_details

            result = await service.check_copilot_pr_completion(
                access_token="test-token",
                owner="owner",
                repo="repo",
                issue_number=1,
            )

            assert result is not None
            assert result["number"] == 42

    @pytest.mark.asyncio
    async def test_multiple_prs_finds_first_copilot_finished(self, service):
        """Should find first finished Copilot PR when multiple PRs exist."""
        linked_prs = [
            {
                "id": "PR_1",
                "number": 10,
                "state": "OPEN",
                "is_draft": True,
                "author": "human-user",  # Not Copilot
            },
            {
                "id": "PR_2",
                "number": 20,
                "state": "MERGED",
                "is_draft": False,
                "author": "copilot-swe-agent[bot]",  # Merged, not processable
            },
            {
                "id": "PR_3",
                "number": 30,
                "state": "OPEN",
                "is_draft": True,
                "author": "copilot-swe-agent[bot]",  # This is the one
            },
        ]
        
        pr_details = {
            "id": "PR_3",
            "number": 30,
            "check_status": "SUCCESS",
            "last_commit": {"sha": "abc123"},
        }
        
        # Timeline events indicating Copilot finished work
        timeline_events = [
            {"event": "copilot_work_finished"}
        ]

        with patch.object(
            service, "get_linked_pull_requests", new_callable=AsyncMock
        ) as mock_get_prs, patch.object(
            service, "get_pull_request", new_callable=AsyncMock
        ) as mock_get_pr, patch.object(
            service, "get_pr_timeline_events", new_callable=AsyncMock
        ) as mock_get_timeline:
            mock_get_prs.return_value = linked_prs
            mock_get_pr.return_value = pr_details
            mock_get_timeline.return_value = timeline_events

            result = await service.check_copilot_pr_completion(
                access_token="test-token",
                owner="owner",
                repo="repo",
                issue_number=1,
            )

            assert result is not None
            assert result["number"] == 30
            assert result["copilot_finished"] is True

    @pytest.mark.asyncio
    async def test_returns_none_when_no_linked_prs(self, service):
        """Should return None when issue has no linked PRs."""
        with patch.object(
            service, "get_linked_pull_requests", new_callable=AsyncMock
        ) as mock_get_prs:
            mock_get_prs.return_value = []

            result = await service.check_copilot_pr_completion(
                access_token="test-token",
                owner="owner",
                repo="repo",
                issue_number=1,
            )

            assert result is None

    @pytest.mark.asyncio
    async def test_handles_exception_gracefully(self, service):
        """Should return None when an exception occurs."""
        with patch.object(
            service, "get_linked_pull_requests", new_callable=AsyncMock
        ) as mock_get_prs:
            mock_get_prs.side_effect = Exception("API Error")

            result = await service.check_copilot_pr_completion(
                access_token="test-token",
                owner="owner",
                repo="repo",
                issue_number=1,
            )

            assert result is None

    @pytest.mark.asyncio
    async def test_handles_get_pull_request_returning_none(self, service):
        """Should continue to next PR when get_pull_request returns None."""
        linked_prs = [
            {
                "id": "PR_1",
                "number": 10,
                "state": "OPEN",
                "is_draft": True,
                "author": "copilot-swe-agent[bot]",
            },
            {
                "id": "PR_2",
                "number": 20,
                "state": "OPEN",
                "is_draft": False,  # Already ready
                "author": "copilot-swe-agent[bot]",
            },
        ]
        
        pr_details_2 = {
            "id": "PR_2",
            "number": 20,
        }

        with patch.object(
            service, "get_linked_pull_requests", new_callable=AsyncMock
        ) as mock_get_prs, patch.object(
            service, "get_pull_request", new_callable=AsyncMock
        ) as mock_get_pr:
            mock_get_prs.return_value = linked_prs
            # First call returns None, second returns details
            mock_get_pr.side_effect = [None, pr_details_2]

            result = await service.check_copilot_pr_completion(
                access_token="test-token",
                owner="owner",
                repo="repo",
                issue_number=1,
            )

            # Should still find the second PR which is already ready
            assert result is not None
            assert result["number"] == 20
