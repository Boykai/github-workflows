"""Unit tests for GitHub webhooks."""

import pytest
from unittest.mock import AsyncMock, patch

from src.api.webhooks import (
    verify_webhook_signature,
    extract_issue_number_from_pr,
    handle_pull_request_event,
)


class TestWebhookSignatureVerification:
    """Tests for webhook signature verification."""

    def test_verify_valid_signature(self):
        """Test that valid signature passes verification."""
        payload = b'{"test": "payload"}'
        secret = "test-secret"
        
        # Generate valid signature
        import hmac
        import hashlib
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
