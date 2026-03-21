"""Unit tests for GitHub webhooks."""

import hashlib
import hmac
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.api.webhooks import (
    extract_issue_number_from_pr,
    handle_copilot_pr_ready,
    handle_pull_request_event,
    update_issue_status_for_copilot_pr,
    verify_webhook_signature,
)
from src.services.cache import cache, get_repo_agents_cache_key


class TestWebhookSignatureVerification:
    """Tests for webhook signature verification."""

    def test_verify_valid_signature(self):
        """Test that valid signature passes verification."""
        payload = b'{"test": "payload"}'
        secret = "test-secret"

        # Generate valid signature
        import hashlib
        import hmac

        expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
        signature = f"sha256={expected}"

        assert verify_webhook_signature(payload, signature, secret) is True

    def test_verify_invalid_signature(self):
        """Test that invalid signature fails verification."""
        payload = b'{"test": "payload"}'
        secret = "test-secret"
        signature = "sha256=invalid"

        assert verify_webhook_signature(payload, signature, secret) is False

    def test_verify_missing_signature(self):
        """Test that missing signature fails verification."""
        payload = b'{"test": "payload"}'
        secret = "test-secret"

        assert verify_webhook_signature(payload, None, secret) is False

    def test_verify_wrong_prefix(self):
        """Test that wrong signature prefix fails verification."""
        payload = b'{"test": "payload"}'
        secret = "test-secret"
        signature = "sha1=somehash"

        assert verify_webhook_signature(payload, signature, secret) is False


class TestIssueNumberExtraction:
    """Tests for extracting issue numbers from PR data."""

    def test_extract_from_fixes_in_body(self):
        """Test extraction from 'Fixes #123' in PR body."""
        pr_data = {
            "body": "This PR fixes #42 by adding error handling",
            "head": {"ref": "feature-branch"},
        }
        assert extract_issue_number_from_pr(pr_data) == 42

    def test_extract_from_closes_in_body(self):
        """Test extraction from 'Closes #123' in PR body."""
        pr_data = {
            "body": "Closes #99\n\nAdded new feature",
            "head": {"ref": "feature-branch"},
        }
        assert extract_issue_number_from_pr(pr_data) == 99

    def test_extract_from_resolves_in_body(self):
        """Test extraction from 'Resolves #123' in PR body."""
        pr_data = {
            "body": "This resolves #7",
            "head": {"ref": "feature-branch"},
        }
        assert extract_issue_number_from_pr(pr_data) == 7

    def test_extract_from_branch_name_issue_prefix(self):
        """Test extraction from branch name like 'issue-123-...'."""
        pr_data = {
            "body": "Some description without issue reference",
            "head": {"ref": "issue-55-add-feature"},
        }
        assert extract_issue_number_from_pr(pr_data) == 55

    def test_extract_from_branch_name_number_prefix(self):
        """Test extraction from branch name like '123-feature'."""
        pr_data = {
            "body": "",
            "head": {"ref": "123-new-feature"},
        }
        assert extract_issue_number_from_pr(pr_data) == 123

    def test_extract_from_branch_name_with_folder(self):
        """Test extraction from branch name like 'feature/123-description'."""
        pr_data = {
            "body": None,
            "head": {"ref": "feature/88-implement-login"},
        }
        assert extract_issue_number_from_pr(pr_data) == 88

    def test_extract_bare_issue_reference(self):
        """Test extraction from bare '#123' reference."""
        pr_data = {
            "body": "Related to #33",
            "head": {"ref": "some-branch"},
        }
        assert extract_issue_number_from_pr(pr_data) == 33

    def test_extract_no_issue_found(self):
        """Test that None is returned when no issue reference found."""
        pr_data = {
            "body": "Just a simple PR",
            "head": {"ref": "feature-branch"},
        }
        assert extract_issue_number_from_pr(pr_data) is None

    def test_extract_empty_pr_data(self):
        """Test extraction with minimal PR data."""
        pr_data = {}
        assert extract_issue_number_from_pr(pr_data) is None


class TestPullRequestEventHandling:
    """Tests for handling pull request webhook events."""

    @pytest.mark.asyncio
    async def test_ignores_non_copilot_pr(self):
        """Test that non-Copilot PRs are ignored."""
        payload = {
            "action": "ready_for_review",
            "pull_request": {
                "number": 1,
                "user": {"login": "regular-user"},
                "draft": False,
            },
            "repository": {
                "owner": {"login": "test-owner"},
                "name": "test-repo",
            },
        }

        result = await handle_pull_request_event(payload)

        assert result["status"] == "ignored"
        assert result["reason"] == "not_copilot_ready_event"

    @pytest.mark.asyncio
    async def test_ignores_non_ready_action(self):
        """Test that non-ready actions are ignored."""
        payload = {
            "action": "synchronize",
            "pull_request": {
                "number": 1,
                "user": {"login": "copilot-swe-agent[bot]"},
                "draft": True,
            },
            "repository": {
                "owner": {"login": "test-owner"},
                "name": "test-repo",
            },
        }

        result = await handle_pull_request_event(payload)

        assert result["status"] == "ignored"
        assert result["reason"] == "not_copilot_ready_event"

    @pytest.mark.asyncio
    async def test_invalidates_repo_agent_cache_on_merged_pr(self):
        cache_key = get_repo_agents_cache_key("test-owner", "test-repo")
        cache.set(cache_key, [{"name": "cached"}], ttl_seconds=60)

        payload = {
            "action": "closed",
            "pull_request": {
                "number": 9,
                "user": {"login": "regular-user"},
                "draft": False,
                "merged": True,
            },
            "repository": {
                "owner": {"login": "test-owner"},
                "name": "test-repo",
            },
        }

        result = await handle_pull_request_event(payload)

        assert result["status"] == "processed"
        assert result["cache_invalidated"] is True
        assert cache.get(cache_key) is None

    @pytest.mark.asyncio
    @patch("src.api.webhooks.get_settings")
    async def test_detects_copilot_pr_ready_no_token(self, mock_settings):
        """Test detection of Copilot PR ready for review without webhook token."""
        mock_settings.return_value.github_webhook_token = None

        payload = {
            "action": "ready_for_review",
            "pull_request": {
                "number": 42,
                "user": {"login": "copilot-swe-agent[bot]"},
                "draft": False,
                "body": "Fixes #10",
                "head": {"ref": "copilot-branch"},
            },
            "repository": {
                "owner": {"login": "test-owner"},
                "name": "test-repo",
            },
        }

        result = await handle_pull_request_event(payload)

        assert result["status"] == "detected"
        assert result["event"] == "copilot_pr_ready"
        assert result["pr_number"] == 42
        assert result["issue_number"] == 10
        assert "action_needed" in result

    @pytest.mark.asyncio
    @patch("src.api.webhooks.get_settings")
    async def test_detects_copilot_opened_non_draft(self, mock_settings):
        """Test detection of Copilot opening a non-draft PR."""
        mock_settings.return_value.github_webhook_token = None

        payload = {
            "action": "opened",
            "pull_request": {
                "number": 55,
                "user": {"login": "copilot[bot]"},
                "draft": False,
                "body": "Closes #20",
                "head": {"ref": "fix-branch"},
            },
            "repository": {
                "owner": {"login": "test-owner"},
                "name": "test-repo",
            },
        }

        result = await handle_pull_request_event(payload)

        assert result["status"] == "detected"
        assert result["event"] == "copilot_pr_ready"
        assert result["pr_number"] == 55
        assert result["issue_number"] == 20

    @pytest.mark.asyncio
    async def test_ignores_copilot_draft_opened(self):
        """Test that Copilot opening a draft PR is ignored."""
        payload = {
            "action": "opened",
            "pull_request": {
                "number": 1,
                "user": {"login": "copilot-swe-agent[bot]"},
                "draft": True,
            },
            "repository": {
                "owner": {"login": "test-owner"},
                "name": "test-repo",
            },
        }

        result = await handle_pull_request_event(payload)

        assert result["status"] == "ignored"
        assert result["reason"] == "not_copilot_ready_event"


class TestHandleCopilotPrReady:
    """Tests for handle_copilot_pr_ready."""

    @pytest.mark.asyncio
    async def test_no_linked_issue(self):
        pr_data = {"number": 1, "user": {"login": "copilot"}, "body": "", "head": {"ref": "branch"}}
        result = await handle_copilot_pr_ready(pr_data, "owner", "repo", "token")
        assert result["status"] == "skipped"
        assert result["reason"] == "no_linked_issue"

    @pytest.mark.asyncio
    @patch("src.api.webhooks.github_projects_service")
    async def test_linked_issue_found(self, mock_gps):
        mock_gps.get_linked_pull_requests = AsyncMock(return_value=[])
        pr_data = {
            "number": 5,
            "user": {"login": "copilot"},
            "body": "Fixes #10",
            "head": {"ref": "b"},
        }
        result = await handle_copilot_pr_ready(pr_data, "owner", "repo", "token")
        assert result["status"] == "processed"
        assert result["issue_number"] == 10

    @pytest.mark.asyncio
    @patch("src.api.webhooks.github_projects_service")
    async def test_error_handling(self, mock_gps):
        mock_gps.get_linked_pull_requests = AsyncMock(side_effect=Exception("API fail"))
        pr_data = {
            "number": 5,
            "user": {"login": "copilot"},
            "body": "Fixes #10",
            "head": {"ref": "b"},
        }
        result = await handle_copilot_pr_ready(pr_data, "owner", "repo", "token")
        assert result["status"] == "error"


class TestUpdateIssueStatusForCopilotPr:
    """Tests for update_issue_status_for_copilot_pr."""

    @pytest.mark.asyncio
    @patch("src.api.webhooks.get_settings")
    async def test_no_linked_issue(self, mock_settings):
        mock_settings.return_value.github_webhook_token = "tok"
        pr_data = {"number": 1, "body": "", "head": {"ref": "branch"}}
        result = await update_issue_status_for_copilot_pr(pr_data, "o", "r", 1, "copilot")
        assert result["action"] == "no_linked_issue_found"

    @pytest.mark.asyncio
    @patch("src.api.webhooks.get_settings")
    async def test_no_webhook_token(self, mock_settings):
        mock_settings.return_value.github_webhook_token = None
        pr_data = {"number": 1, "body": "Fixes #5", "head": {"ref": "b"}}
        result = await update_issue_status_for_copilot_pr(pr_data, "o", "r", 1, "copilot")
        assert result["status"] == "detected"
        assert "action_needed" in result

    @pytest.mark.asyncio
    @patch("src.api.webhooks.github_projects_service")
    @patch("src.api.webhooks.get_settings")
    async def test_auth_failure(self, mock_settings, mock_gps):
        """Webhook token present but auth fails."""
        mock_settings.return_value.github_webhook_token = "bad-token"
        mock_resp = MagicMock(status_code=401, json=lambda: {})
        mock_gps.rest_request = AsyncMock(return_value=mock_resp)
        pr_data = {"number": 1, "body": "Fixes #5", "head": {"ref": "b"}}
        result = await update_issue_status_for_copilot_pr(pr_data, "o", "r", 1, "copilot")
        assert result["status"] == "error"
        assert "authenticate" in result["error"].lower()

    @pytest.mark.asyncio
    @patch("src.api.webhooks.github_projects_service")
    @patch("src.api.webhooks.get_settings")
    async def test_issue_not_in_any_project(self, mock_settings, mock_gps):
        """Token works but issue not found in any project."""
        mock_settings.return_value.github_webhook_token = "tok"
        mock_resp = MagicMock(status_code=200, json=lambda: {"login": "user"})
        mock_gps.rest_request = AsyncMock(return_value=mock_resp)
        mock_project = MagicMock(project_id="proj-1")
        mock_gps.list_user_projects = AsyncMock(return_value=[mock_project])
        mock_item = MagicMock(github_item_id="999", title="Unrelated")
        mock_gps.get_project_items = AsyncMock(return_value=[mock_item])
        pr_data = {"number": 1, "body": "Fixes #5", "head": {"ref": "b"}}
        result = await update_issue_status_for_copilot_pr(pr_data, "o", "r", 1, "copilot")
        assert result["action"] == "issue_not_in_project"

    @pytest.mark.asyncio
    @patch("src.api.webhooks.github_projects_service")
    @patch("src.api.webhooks.get_settings")
    async def test_status_updated_success(self, mock_settings, mock_gps):
        """Full happy path - issue found and status updated."""
        mock_settings.return_value.github_webhook_token = "tok"
        mock_resp = MagicMock(status_code=200, json=lambda: {"login": "user"})
        mock_gps.rest_request = AsyncMock(return_value=mock_resp)
        mock_project = MagicMock(project_id="proj-1")
        mock_gps.list_user_projects = AsyncMock(return_value=[mock_project])
        mock_item = MagicMock(github_item_id="5", title="Issue #5")
        mock_gps.get_project_items = AsyncMock(return_value=[mock_item])
        mock_gps.update_item_status_by_name = AsyncMock(return_value=True)
        pr_data = {"number": 1, "body": "Fixes #5", "head": {"ref": "b"}}
        result = await update_issue_status_for_copilot_pr(pr_data, "o", "r", 1, "copilot")
        assert result["status"] == "success"
        assert result["new_status"] == "In Review"

    @pytest.mark.asyncio
    @patch("src.api.webhooks.github_projects_service")
    @patch("src.api.webhooks.get_settings")
    async def test_status_update_fails(self, mock_settings, mock_gps):
        """Issue found but update_item_status_by_name returns False."""
        mock_settings.return_value.github_webhook_token = "tok"
        mock_resp = MagicMock(status_code=200, json=lambda: {"login": "user"})
        mock_gps.rest_request = AsyncMock(return_value=mock_resp)
        mock_project = MagicMock(project_id="proj-1")
        mock_gps.list_user_projects = AsyncMock(return_value=[mock_project])
        mock_item = MagicMock(github_item_id="5", title="Issue #5")
        mock_gps.get_project_items = AsyncMock(return_value=[mock_item])
        mock_gps.update_item_status_by_name = AsyncMock(return_value=False)
        pr_data = {"number": 1, "body": "Fixes #5", "head": {"ref": "b"}}
        result = await update_issue_status_for_copilot_pr(pr_data, "o", "r", 1, "copilot")
        assert result["status"] == "error"
        assert "Failed to update" in result["error"]

    @pytest.mark.asyncio
    @patch("src.api.webhooks.github_projects_service")
    @patch("src.api.webhooks.get_settings")
    async def test_exception_during_project_lookup(self, mock_settings, mock_gps):
        """Exception raised during the whole project lookup flow."""
        mock_settings.return_value.github_webhook_token = "tok"
        mock_gps.rest_request = AsyncMock(side_effect=Exception("Network error"))
        pr_data = {"number": 1, "body": "Fixes #5", "head": {"ref": "b"}}
        result = await update_issue_status_for_copilot_pr(pr_data, "o", "r", 1, "copilot")
        assert result["status"] == "error"

    @pytest.mark.asyncio
    @patch("src.api.webhooks.github_projects_service")
    @patch("src.api.webhooks.get_settings")
    async def test_project_items_error_continues(self, mock_settings, mock_gps):
        """When get_project_items fails for one project, continues to next."""
        mock_settings.return_value.github_webhook_token = "tok"
        mock_resp = MagicMock(status_code=200, json=lambda: {"login": "user"})
        mock_gps.rest_request = AsyncMock(return_value=mock_resp)
        proj1 = MagicMock(project_id="proj-1")
        proj2 = MagicMock(project_id="proj-2")
        mock_gps.list_user_projects = AsyncMock(return_value=[proj1, proj2])
        mock_item = MagicMock(github_item_id="5", title="Issue #5")
        mock_gps.get_project_items = AsyncMock(side_effect=[Exception("fail"), [mock_item]])
        mock_gps.update_item_status_by_name = AsyncMock(return_value=True)
        pr_data = {"number": 1, "body": "Fixes #5", "head": {"ref": "b"}}
        result = await update_issue_status_for_copilot_pr(pr_data, "o", "r", 1, "copilot")
        assert result["status"] == "success"

    @pytest.mark.asyncio
    @patch("src.api.webhooks.github_projects_service")
    @patch("src.api.webhooks.get_settings")
    async def test_issue_found_by_title_match(self, mock_settings, mock_gps):
        """Issue matched by title containing '#N'."""
        mock_settings.return_value.github_webhook_token = "tok"
        mock_resp = MagicMock(status_code=200, json=lambda: {"login": "user"})
        mock_gps.rest_request = AsyncMock(return_value=mock_resp)
        mock_project = MagicMock(project_id="proj-1")
        mock_gps.list_user_projects = AsyncMock(return_value=[mock_project])
        # github_item_id doesn't contain "5" but title does
        mock_item = MagicMock(github_item_id="ITEM_999", title="Bug fix #5 - typo")
        mock_gps.get_project_items = AsyncMock(return_value=[mock_item])
        mock_gps.update_item_status_by_name = AsyncMock(return_value=True)
        pr_data = {"number": 1, "body": "Fixes #5", "head": {"ref": "b"}}
        result = await update_issue_status_for_copilot_pr(pr_data, "o", "r", 1, "copilot")
        assert result["status"] == "success"

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.get_pipeline_state")
    @patch("src.api.webhooks.github_projects_service")
    @patch("src.api.webhooks.get_settings")
    async def test_skips_status_move_when_pipeline_agent_not_copilot_review(
        self, mock_settings, mock_gps, mock_get_pipeline
    ):
        """Pipeline exists with current_agent != 'copilot-review' → skip status move."""
        mock_settings.return_value.github_webhook_token = "tok"
        mock_resp = MagicMock(status_code=200, json=lambda: {"login": "user"})
        mock_gps.rest_request = AsyncMock(return_value=mock_resp)
        mock_project = MagicMock(project_id="proj-1")
        mock_gps.list_user_projects = AsyncMock(return_value=[mock_project])
        mock_item = MagicMock(github_item_id="5", title="Issue #5", issue_number=5)
        mock_gps.get_project_items = AsyncMock(return_value=[mock_item])
        # Pipeline says current agent is speckit.implement — NOT copilot-review
        mock_get_pipeline.return_value = SimpleNamespace(current_agent="speckit.implement")

        pr_data = {"number": 1, "body": "Fixes #5", "head": {"ref": "b"}}
        result = await update_issue_status_for_copilot_pr(pr_data, "o", "r", 1, "copilot")

        assert result["status"] == "skipped"
        assert result["reason"] == "pipeline_agent_not_copilot_review"
        assert result["current_agent"] == "speckit.implement"
        # update_item_status_by_name must NOT have been called
        mock_gps.update_item_status_by_name.assert_not_called()

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.get_pipeline_state")
    @patch("src.api.webhooks.github_projects_service")
    @patch("src.api.webhooks.get_settings")
    async def test_proceeds_when_pipeline_agent_is_copilot_review(
        self, mock_settings, mock_gps, mock_get_pipeline
    ):
        """Pipeline exists with current_agent == 'copilot-review' → proceed normally."""
        mock_settings.return_value.github_webhook_token = "tok"
        mock_resp = MagicMock(status_code=200, json=lambda: {"login": "user"})
        mock_gps.rest_request = AsyncMock(return_value=mock_resp)
        mock_project = MagicMock(project_id="proj-1")
        mock_gps.list_user_projects = AsyncMock(return_value=[mock_project])
        mock_item = MagicMock(github_item_id="5", title="Issue #5", issue_number=5)
        mock_gps.get_project_items = AsyncMock(return_value=[mock_item])
        mock_gps.update_item_status_by_name = AsyncMock(return_value=True)
        mock_get_pipeline.return_value = SimpleNamespace(current_agent="copilot-review")

        pr_data = {"number": 1, "body": "Fixes #5", "head": {"ref": "b"}}
        result = await update_issue_status_for_copilot_pr(pr_data, "o", "r", 1, "copilot")

        assert result["status"] == "success"
        assert result["new_status"] == "In Review"

    @pytest.mark.asyncio
    @patch("src.services.copilot_polling.get_pipeline_state")
    @patch("src.api.webhooks.github_projects_service")
    @patch("src.api.webhooks.get_settings")
    async def test_proceeds_when_no_pipeline_exists(
        self, mock_settings, mock_gps, mock_get_pipeline
    ):
        """No pipeline for issue → proceed normally (backward compat)."""
        mock_settings.return_value.github_webhook_token = "tok"
        mock_resp = MagicMock(status_code=200, json=lambda: {"login": "user"})
        mock_gps.rest_request = AsyncMock(return_value=mock_resp)
        mock_project = MagicMock(project_id="proj-1")
        mock_gps.list_user_projects = AsyncMock(return_value=[mock_project])
        mock_item = MagicMock(github_item_id="5", title="Issue #5", issue_number=5)
        mock_gps.get_project_items = AsyncMock(return_value=[mock_item])
        mock_gps.update_item_status_by_name = AsyncMock(return_value=True)
        mock_get_pipeline.return_value = None

        pr_data = {"number": 1, "body": "Fixes #5", "head": {"ref": "b"}}
        result = await update_issue_status_for_copilot_pr(pr_data, "o", "r", 1, "copilot")

        assert result["status"] == "success"
        assert result["new_status"] == "In Review"


class TestGithubWebhookEndpoint:
    """Integration tests for the webhook endpoint via client."""

    @pytest.fixture
    def webhook_secret(self):
        return "test-webhook-secret"

    def _sign(self, body: bytes, secret: str) -> str:
        return "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()

    async def test_webhook_invalid_signature(self, client):
        with patch("src.api.webhooks.get_settings") as mock_s:
            mock_s.return_value = MagicMock(github_webhook_secret="secret")
            resp = await client.post(
                "/api/v1/webhooks/github",
                content=b'{"test": true}',
                headers={
                    "X-GitHub-Event": "push",
                    "X-Hub-Signature-256": "sha256=invalid",
                },
            )
        assert resp.status_code == 401

    async def test_webhook_ignores_unhandled_event(self, client, webhook_secret):
        with (
            patch("src.api.webhooks.get_settings") as mock_s,
            patch("src.api.webhooks.verify_webhook_signature", return_value=True),
        ):
            mock_s.return_value = MagicMock(github_webhook_secret=webhook_secret)
            resp = await client.post(
                "/api/v1/webhooks/github",
                json={"action": "ping"},
                headers={"X-GitHub-Event": "ping"},
            )
        assert resp.status_code == 200
        assert resp.json()["status"] == "ignored"

    async def test_webhook_deduplication(self, client, webhook_secret):
        with (
            patch("src.api.webhooks.get_settings") as mock_s,
            patch("src.api.webhooks.verify_webhook_signature", return_value=True),
        ):
            mock_s.return_value = MagicMock(github_webhook_secret=webhook_secret)
            # Clear processed IDs for test isolation
            from src.api.webhooks import _processed_delivery_ids

            _processed_delivery_ids.discard("dedup-test-id")

            resp1 = await client.post(
                "/api/v1/webhooks/github",
                json={"action": "ping"},
                headers={
                    "X-GitHub-Event": "ping",
                    "X-GitHub-Delivery": "dedup-test-id",
                },
            )
            resp2 = await client.post(
                "/api/v1/webhooks/github",
                json={"action": "ping"},
                headers={
                    "X-GitHub-Event": "ping",
                    "X-GitHub-Delivery": "dedup-test-id",
                },
            )
        assert resp1.status_code == 200
        assert resp2.json()["status"] == "duplicate"
        _processed_delivery_ids.discard("dedup-test-id")

    async def test_webhook_pull_request_routing(self, client, webhook_secret):
        """Pull request events are routed to handle_pull_request_event."""
        with (
            patch("src.api.webhooks.get_settings") as mock_s,
            patch("src.api.webhooks.verify_webhook_signature", return_value=True),
        ):
            mock_s.return_value = MagicMock(github_webhook_secret=webhook_secret)
            resp = await client.post(
                "/api/v1/webhooks/github",
                json={
                    "action": "synchronize",
                    "pull_request": {
                        "number": 99,
                        "user": {"login": "someone"},
                        "draft": False,
                    },
                    "repository": {"owner": {"login": "o"}, "name": "r"},
                },
                headers={"X-GitHub-Event": "pull_request"},
            )
        assert resp.status_code == 200
        assert resp.json()["event"] == "pull_request"

    async def test_webhook_valid_signature(self, client, webhook_secret):
        """Valid signature passes verification."""
        import json as json_mod

        body = json_mod.dumps({"action": "ping"}).encode()
        sig = self._sign(body, webhook_secret)
        with patch("src.api.webhooks.get_settings") as mock_s:
            mock_s.return_value = MagicMock(github_webhook_secret=webhook_secret)
            resp = await client.post(
                "/api/v1/webhooks/github",
                content=body,
                headers={
                    "X-GitHub-Event": "ping",
                    "X-Hub-Signature-256": sig,
                    "Content-Type": "application/json",
                },
            )
        assert resp.status_code == 200


# ── Regression: deduplication uses BoundedSet (insertion-ordered eviction) ──


class TestDeduplicationBoundedSet:
    """Bug-bash regression: webhook deduplication must evict oldest entries
    when capacity is reached, using BoundedSet instead of an unordered set."""

    def test_module_uses_bounded_set(self):
        """Verify the module-level variable is actually a BoundedSet."""
        from src.api.webhooks import _processed_delivery_ids
        from src.utils import BoundedSet

        assert isinstance(_processed_delivery_ids, BoundedSet)

    def test_deduplication_set_rejects_duplicates(self):
        """Adding a known delivery ID should be detected as duplicate."""
        from src.api import webhooks as wh_mod
        from src.utils import BoundedSet

        original = wh_mod._processed_delivery_ids
        wh_mod._processed_delivery_ids = BoundedSet(maxlen=5)
        try:
            wh_mod._processed_delivery_ids.add("d-1")
            wh_mod._processed_delivery_ids.add("d-2")
            assert "d-1" in wh_mod._processed_delivery_ids
            assert "d-2" in wh_mod._processed_delivery_ids
            assert "d-3" not in wh_mod._processed_delivery_ids
        finally:
            wh_mod._processed_delivery_ids = original

    def test_bounded_set_evicts_in_fifo_order(self):
        """When capacity is exceeded, the FIRST-inserted entry is evicted."""
        from src.utils import BoundedSet

        bs = BoundedSet(maxlen=3)
        bs.add("a")
        bs.add("b")
        bs.add("c")
        bs.add("d")
        assert "a" not in bs
        assert "b" in bs
        assert "c" in bs
        assert "d" in bs


# ── Regression: issue matching uses issue_number, not github_item_id ────────


class TestIssueMatchingByNumber:
    """Bug-bash regression: webhook issue matching must compare
    item.issue_number (int) instead of item.github_item_id (GraphQL node ID)."""

    def test_matches_issue_by_number_not_node_id(self):
        """Verify that Task.issue_number is the correct field to match on,
        and that github_item_id (a GraphQL node ID) would NOT work."""
        from src.models.task import Task

        task = Task(
            project_id="PVT_1",
            github_item_id="PVTI_lADOABCDEF",
            title="Fix login flow",
            status="In Progress",
            status_option_id="opt1",
            issue_number=42,
        )

        assert task.issue_number == 42
        # The old buggy comparison would have FAILED
        assert str(42) not in str(task.github_item_id)


# ── Regression: webhook response must not echo user-controlled input ────


class TestWebhookResponseSanitization:
    """Bug-bash regression: user-controlled header values must not be echoed
    back in webhook API responses."""

    async def test_unhandled_event_does_not_echo_event_type(self, client):
        """The 'ignored' response for unhandled events must not reflect the
        X-GitHub-Event header value, as it is user-controlled input."""
        from src.api.webhooks import _processed_delivery_ids

        with (
            patch("src.api.webhooks.get_settings") as mock_settings,
            patch("src.api.webhooks.verify_webhook_signature", return_value=True),
        ):
            mock_settings.return_value = MagicMock(
                github_webhook_secret="test-secret",
                debug=True,
            )
            resp = await client.post(
                "/api/v1/webhooks/github",
                json={"action": "test"},
                headers={
                    "X-GitHub-Event": "<script>alert(1)</script>",
                    "X-GitHub-Delivery": "unique-delivery-sanitize-test",
                },
            )

        assert resp.status_code == 200
        body = resp.json()
        assert "<script>" not in body.get("message", "")
        # Verify the response does not echo user-controlled header values in any field
        assert "event" not in body, (
            "Response must not include 'event' field that echoes user-controlled header"
        )
        for value in body.values():
            assert "<script>" not in str(value), (
                "No user-controlled input should appear anywhere in response"
            )
        # Cleanup delivery ID to avoid side-effects on other tests
        _processed_delivery_ids.discard("unique-delivery-sanitize-test")
