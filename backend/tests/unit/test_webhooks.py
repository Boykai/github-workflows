"""Unit tests for GitHub webhooks."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from src.api.webhooks import (
    _processed_delivery_ids,
    extract_issue_number_from_pr,
    handle_copilot_pr_ready,
    handle_pull_request_event,
    update_issue_status_for_copilot_pr,
    verify_webhook_signature,
)


@pytest.fixture(autouse=True)
def _clear_delivery_ids():
    """Clear processed delivery IDs before each test."""
    _processed_delivery_ids.clear()
    yield
    _processed_delivery_ids.clear()


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
    """Tests for handle_copilot_pr_ready function."""

    @pytest.mark.asyncio
    async def test_no_linked_issue(self):
        """Should return skipped when no linked issue found."""
        pr_data = {
            "number": 10,
            "user": {"login": "copilot[bot]"},
            "body": "No issue reference here",
            "head": {"ref": "some-branch"},
        }

        result = await handle_copilot_pr_ready(pr_data, "owner", "repo", "token123")

        assert result["status"] == "skipped"
        assert result["reason"] == "no_linked_issue"
        assert result["pr_number"] == 10

    @pytest.mark.asyncio
    @patch("src.api.webhooks.github_projects_service")
    async def test_with_linked_issue_success(self, mock_service):
        """Should return processed when issue is found and linked PRs fetched."""
        mock_service.get_linked_pull_requests = AsyncMock(return_value=[{"number": 10}])

        pr_data = {
            "number": 10,
            "user": {"login": "copilot[bot]"},
            "body": "Fixes #5",
            "head": {"ref": "fix-branch"},
        }

        result = await handle_copilot_pr_ready(pr_data, "owner", "repo", "token123")

        assert result["status"] == "processed"
        assert result["pr_number"] == 10
        assert result["issue_number"] == 5
        mock_service.get_linked_pull_requests.assert_awaited_once()

    @pytest.mark.asyncio
    @patch("src.api.webhooks.github_projects_service")
    async def test_with_linked_issue_service_error(self, mock_service):
        """Should return error when service call fails."""
        mock_service.get_linked_pull_requests = AsyncMock(side_effect=RuntimeError("API failure"))

        pr_data = {
            "number": 10,
            "user": {"login": "copilot[bot]"},
            "body": "Fixes #5",
            "head": {"ref": "fix-branch"},
        }

        result = await handle_copilot_pr_ready(pr_data, "owner", "repo", "token123")

        assert result["status"] == "error"
        assert result["pr_number"] == 10
        assert "API failure" in result["error"]


class TestUpdateIssueStatusForCopilotPr:
    """Tests for update_issue_status_for_copilot_pr function."""

    @pytest.mark.asyncio
    @patch("src.api.webhooks.get_settings")
    async def test_no_linked_issue(self, mock_settings):
        """Should return detected with no_linked_issue_found when no issue found."""
        pr_data = {
            "body": "No issue reference",
            "head": {"ref": "branch"},
        }

        result = await update_issue_status_for_copilot_pr(
            pr_data=pr_data,
            repo_owner="owner",
            repo_name="repo",
            pr_number=42,
            pr_author="copilot[bot]",
        )

        assert result["status"] == "detected"
        assert result["action"] == "no_linked_issue_found"
        assert result["pr_number"] == 42

    @pytest.mark.asyncio
    @patch("src.api.webhooks.get_settings")
    async def test_no_webhook_token(self, mock_settings):
        """Should return detected with action_needed when no webhook token configured."""
        mock_settings.return_value.github_webhook_token = None

        pr_data = {
            "body": "Fixes #10",
            "head": {"ref": "branch"},
        }

        result = await update_issue_status_for_copilot_pr(
            pr_data=pr_data,
            repo_owner="owner",
            repo_name="repo",
            pr_number=42,
            pr_author="copilot[bot]",
        )

        assert result["status"] == "detected"
        assert result["issue_number"] == 10
        assert "action_needed" in result

    @pytest.mark.asyncio
    @patch("src.api.webhooks.github_projects_service")
    @patch("src.api.webhooks.get_settings")
    async def test_auth_failure(self, mock_settings, mock_service):
        """Should return error when webhook token auth fails."""
        mock_settings.return_value.github_webhook_token = "test-token"

        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_service._client = MagicMock()
        mock_service._client.get = AsyncMock(return_value=mock_response)

        pr_data = {
            "body": "Fixes #10",
            "head": {"ref": "branch"},
        }

        result = await update_issue_status_for_copilot_pr(
            pr_data=pr_data,
            repo_owner="owner",
            repo_name="repo",
            pr_number=42,
            pr_author="copilot[bot]",
        )

        assert result["status"] == "error"
        assert "authenticate" in result["error"].lower() or "Failed" in result["error"]

    @pytest.mark.asyncio
    @patch("src.api.webhooks.github_projects_service")
    @patch("src.api.webhooks.get_settings")
    async def test_issue_not_in_any_project(self, mock_settings, mock_service):
        """Should return detected with issue_not_in_project when issue not found in projects."""
        mock_settings.return_value.github_webhook_token = "test-token"

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"login": "testuser"}
        mock_service._client = MagicMock()
        mock_service._client.get = AsyncMock(return_value=mock_response)

        # Return projects with no matching items
        mock_project = MagicMock()
        mock_project.project_id = "proj-1"
        mock_service.list_user_projects = AsyncMock(return_value=[mock_project])

        mock_item = MagicMock()
        mock_item.github_item_id = "999"
        mock_item.title = "Unrelated issue"
        mock_service.get_project_items = AsyncMock(return_value=[mock_item])

        pr_data = {
            "body": "Fixes #10",
            "head": {"ref": "branch"},
        }

        result = await update_issue_status_for_copilot_pr(
            pr_data=pr_data,
            repo_owner="owner",
            repo_name="repo",
            pr_number=42,
            pr_author="copilot[bot]",
        )

        assert result["status"] == "detected"
        assert result["action"] == "issue_not_in_project"

    @pytest.mark.asyncio
    @patch("src.api.webhooks.github_projects_service")
    @patch("src.api.webhooks.get_settings")
    async def test_successful_status_update(self, mock_settings, mock_service):
        """Should return success when issue status is updated to In Review."""
        mock_settings.return_value.github_webhook_token = "test-token"

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"login": "testuser"}
        mock_service._client = MagicMock()
        mock_service._client.get = AsyncMock(return_value=mock_response)

        mock_project = MagicMock()
        mock_project.project_id = "proj-1"
        mock_service.list_user_projects = AsyncMock(return_value=[mock_project])

        mock_item = MagicMock()
        mock_item.github_item_id = "item-10"
        mock_item.title = "Issue #10: Fix bug"
        mock_service.get_project_items = AsyncMock(return_value=[mock_item])
        mock_service.update_item_status_by_name = AsyncMock(return_value=True)

        pr_data = {
            "body": "Fixes #10",
            "head": {"ref": "branch"},
        }

        result = await update_issue_status_for_copilot_pr(
            pr_data=pr_data,
            repo_owner="owner",
            repo_name="repo",
            pr_number=42,
            pr_author="copilot[bot]",
        )

        assert result["status"] == "success"
        assert result["new_status"] == "In Review"
        assert result["issue_number"] == 10
        mock_service.update_item_status_by_name.assert_awaited_once_with(
            access_token="test-token",
            project_id="proj-1",
            item_id="item-10",
            status_name="In Review",
        )

    @pytest.mark.asyncio
    @patch("src.api.webhooks.github_projects_service")
    @patch("src.api.webhooks.get_settings")
    async def test_failed_status_update(self, mock_settings, mock_service):
        """Should return error when status update fails."""
        mock_settings.return_value.github_webhook_token = "test-token"

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"login": "testuser"}
        mock_service._client = MagicMock()
        mock_service._client.get = AsyncMock(return_value=mock_response)

        mock_project = MagicMock()
        mock_project.project_id = "proj-1"
        mock_service.list_user_projects = AsyncMock(return_value=[mock_project])

        # Match by github_item_id containing issue number
        mock_item = MagicMock()
        mock_item.github_item_id = "10"
        mock_item.title = "Some title"
        mock_service.get_project_items = AsyncMock(return_value=[mock_item])
        mock_service.update_item_status_by_name = AsyncMock(return_value=False)

        pr_data = {
            "body": "Fixes #10",
            "head": {"ref": "branch"},
        }

        result = await update_issue_status_for_copilot_pr(
            pr_data=pr_data,
            repo_owner="owner",
            repo_name="repo",
            pr_number=42,
            pr_author="copilot[bot]",
        )

        assert result["status"] == "error"
        assert "Failed to update" in result["error"]

    @pytest.mark.asyncio
    @patch("src.api.webhooks.github_projects_service")
    @patch("src.api.webhooks.get_settings")
    async def test_exception_during_project_lookup(self, mock_settings, mock_service):
        """Should return error when exception occurs during project lookup."""
        mock_settings.return_value.github_webhook_token = "test-token"

        mock_service._client = MagicMock()
        mock_service._client.get = AsyncMock(side_effect=RuntimeError("Network error"))

        pr_data = {
            "body": "Fixes #10",
            "head": {"ref": "branch"},
        }

        result = await update_issue_status_for_copilot_pr(
            pr_data=pr_data,
            repo_owner="owner",
            repo_name="repo",
            pr_number=42,
            pr_author="copilot[bot]",
        )

        assert result["status"] == "error"
        assert "Network error" in result["error"]

    @pytest.mark.asyncio
    @patch("src.api.webhooks.github_projects_service")
    @patch("src.api.webhooks.get_settings")
    async def test_get_project_items_error_continues(self, mock_settings, mock_service):
        """Should continue to next project when get_project_items fails for one."""
        mock_settings.return_value.github_webhook_token = "test-token"

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"login": "testuser"}
        mock_service._client = MagicMock()
        mock_service._client.get = AsyncMock(return_value=mock_response)

        mock_project1 = MagicMock()
        mock_project1.project_id = "proj-1"
        mock_project2 = MagicMock()
        mock_project2.project_id = "proj-2"
        mock_service.list_user_projects = AsyncMock(return_value=[mock_project1, mock_project2])

        # First project fails, second has no matching items
        mock_service.get_project_items = AsyncMock(side_effect=[RuntimeError("API error"), []])

        pr_data = {
            "body": "Fixes #10",
            "head": {"ref": "branch"},
        }

        result = await update_issue_status_for_copilot_pr(
            pr_data=pr_data,
            repo_owner="owner",
            repo_name="repo",
            pr_number=42,
            pr_author="copilot[bot]",
        )

        assert result["status"] == "detected"
        assert result["action"] == "issue_not_in_project"

    @pytest.mark.asyncio
    @patch("src.api.webhooks.github_projects_service")
    @patch("src.api.webhooks.get_settings")
    async def test_no_projects_found(self, mock_settings, mock_service):
        """Should return issue_not_in_project when user has no projects."""
        mock_settings.return_value.github_webhook_token = "test-token"

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"login": "testuser"}
        mock_service._client = MagicMock()
        mock_service._client.get = AsyncMock(return_value=mock_response)

        mock_service.list_user_projects = AsyncMock(return_value=[])

        pr_data = {
            "body": "Fixes #10",
            "head": {"ref": "branch"},
        }

        result = await update_issue_status_for_copilot_pr(
            pr_data=pr_data,
            repo_owner="owner",
            repo_name="repo",
            pr_number=42,
            pr_author="copilot[bot]",
        )

        assert result["status"] == "detected"
        assert result["action"] == "issue_not_in_project"


class TestGitHubWebhookEndpoint:
    """Tests for the github_webhook endpoint."""

    @pytest.mark.asyncio
    @patch("src.api.webhooks.get_settings")
    async def test_invalid_signature_raises_401(self, mock_settings):
        """Should raise 401 when signature verification fails."""
        mock_settings.return_value.github_webhook_secret = "my-secret"

        from src.api.webhooks import github_webhook

        mock_request = AsyncMock()
        mock_request.body = AsyncMock(return_value=b'{"test": true}')

        with pytest.raises(HTTPException) as exc_info:
            await github_webhook(
                request=mock_request,
                x_github_event="push",
                x_github_delivery="delivery-1",
                x_hub_signature_256="sha256=invalid",
            )

        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    @patch("src.api.webhooks.get_settings")
    async def test_duplicate_delivery_returns_duplicate(self, mock_settings):
        """Should return duplicate status for already processed delivery ID."""
        mock_settings.return_value.github_webhook_secret = None

        from src.api.webhooks import github_webhook

        _processed_delivery_ids.add("delivery-dup")

        mock_request = AsyncMock()
        mock_request.body = AsyncMock(return_value=b"{}")

        result = await github_webhook(
            request=mock_request,
            x_github_event="push",
            x_github_delivery="delivery-dup",
            x_hub_signature_256=None,
        )

        assert result["status"] == "duplicate"

    @pytest.mark.asyncio
    @patch("src.api.webhooks.get_settings")
    async def test_invalid_json_raises_400(self, mock_settings):
        """Should raise 400 for invalid JSON payload."""
        mock_settings.return_value.github_webhook_secret = None

        from src.api.webhooks import github_webhook

        mock_request = AsyncMock()
        mock_request.body = AsyncMock(return_value=b"not json")
        mock_request.json = AsyncMock(side_effect=ValueError("Invalid JSON"))

        with pytest.raises(HTTPException) as exc_info:
            await github_webhook(
                request=mock_request,
                x_github_event="push",
                x_github_delivery="delivery-json",
                x_hub_signature_256=None,
            )

        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    @patch("src.api.webhooks.get_settings")
    async def test_unhandled_event_returns_ignored(self, mock_settings):
        """Should return ignored for unhandled event types."""
        mock_settings.return_value.github_webhook_secret = None

        from src.api.webhooks import github_webhook

        mock_request = AsyncMock()
        mock_request.body = AsyncMock(return_value=b'{"action": "created"}')
        mock_request.json = AsyncMock(return_value={"action": "created"})

        result = await github_webhook(
            request=mock_request,
            x_github_event="issues",
            x_github_delivery="delivery-issues",
            x_hub_signature_256=None,
        )

        assert result["status"] == "ignored"
        assert result["event"] == "issues"

    @pytest.mark.asyncio
    @patch("src.api.webhooks.handle_pull_request_event", new_callable=AsyncMock)
    @patch("src.api.webhooks.get_settings")
    async def test_pull_request_event_dispatches(self, mock_settings, mock_handler):
        """Should dispatch pull_request events to the handler."""
        mock_settings.return_value.github_webhook_secret = None
        mock_handler.return_value = {"status": "processed"}

        from src.api.webhooks import github_webhook

        payload = {"action": "opened", "pull_request": {"number": 1}}
        mock_request = AsyncMock()
        mock_request.body = AsyncMock(return_value=json.dumps(payload).encode())
        mock_request.json = AsyncMock(return_value=payload)

        result = await github_webhook(
            request=mock_request,
            x_github_event="pull_request",
            x_github_delivery="delivery-pr",
            x_hub_signature_256=None,
        )

        assert result["status"] == "processed"
        mock_handler.assert_awaited_once_with(payload)

    @pytest.mark.asyncio
    @patch("src.api.webhooks.get_settings")
    async def test_valid_signature_passes(self, mock_settings):
        """Should proceed when signature is valid."""
        import hashlib
        import hmac

        secret = "test-secret"
        mock_settings.return_value.github_webhook_secret = secret

        from src.api.webhooks import github_webhook

        payload_bytes = b'{"action": "ping"}'
        expected = hmac.new(secret.encode(), payload_bytes, hashlib.sha256).hexdigest()
        signature = f"sha256={expected}"

        mock_request = AsyncMock()
        mock_request.body = AsyncMock(return_value=payload_bytes)
        mock_request.json = AsyncMock(return_value={"action": "ping"})

        result = await github_webhook(
            request=mock_request,
            x_github_event="ping",
            x_github_delivery="delivery-valid",
            x_hub_signature_256=signature,
        )

        assert result["status"] == "ignored"
        assert result["event"] == "ping"

    @pytest.mark.asyncio
    @patch("src.api.webhooks.get_settings")
    async def test_delivery_id_memory_cleanup(self, mock_settings):
        """Should trim delivery IDs when exceeding MAX_DELIVERY_IDS."""
        mock_settings.return_value.github_webhook_secret = None

        from src.api.webhooks import MAX_DELIVERY_IDS, github_webhook

        # Pre-fill with enough IDs to trigger cleanup
        for i in range(MAX_DELIVERY_IDS + 1):
            _processed_delivery_ids.add(f"old-{i}")

        mock_request = AsyncMock()
        mock_request.body = AsyncMock(return_value=b'{"action": "ping"}')
        mock_request.json = AsyncMock(return_value={"action": "ping"})

        await github_webhook(
            request=mock_request,
            x_github_event="ping",
            x_github_delivery="new-delivery",
            x_hub_signature_256=None,
        )

        # Should have trimmed some entries
        assert len(_processed_delivery_ids) <= MAX_DELIVERY_IDS + 1

    @pytest.mark.asyncio
    @patch("src.api.webhooks.get_settings")
    async def test_no_delivery_id_still_processes(self, mock_settings):
        """Should process event even without delivery ID."""
        mock_settings.return_value.github_webhook_secret = None

        from src.api.webhooks import github_webhook

        mock_request = AsyncMock()
        mock_request.body = AsyncMock(return_value=b'{"action": "created"}')
        mock_request.json = AsyncMock(return_value={"action": "created"})

        result = await github_webhook(
            request=mock_request,
            x_github_event="issues",
            x_github_delivery=None,
            x_hub_signature_256=None,
        )

        assert result["status"] == "ignored"
