"""Tests for issue creation via SDK client.

The create_issue method delegates to self._rest() which uses the githubkit
SDK client with built-in retry logic (auto_retry). These tests verify the
method's interface and error handling.

Covers: FR-008
"""

from unittest.mock import AsyncMock

import pytest

from src.services.github_projects.service import GitHubProjectsService


class TestIssueCreationRetry:
    """create_issue should delegate to SDK client via _rest()."""

    @pytest.fixture
    def service(self):
        """Create a GitHubProjectsService instance."""
        return GitHubProjectsService()

    @pytest.mark.asyncio
    async def test_create_issue_success(self, service):
        """Issue creation succeeds on first attempt."""
        mock_issue = {
            "id": 3,
            "node_id": "I_3",
            "number": 44,
            "html_url": "https://github.com/o/r/issues/44",
        }
        service._rest = AsyncMock(return_value=mock_issue)

        result = await service.create_issue(
            access_token="test-token",
            owner="o",
            repo="r",
            title="Test Issue",
            body="Test body",
        )

        assert result["number"] == 44
        service._rest.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_create_issue_raises_on_sdk_error(self, service):
        """Issue creation raises when SDK exhausts retries."""
        service._rest = AsyncMock(side_effect=Exception("SDK retry exhausted"))

        with pytest.raises(Exception, match="SDK retry exhausted"):
            await service.create_issue(
                access_token="test-token",
                owner="o",
                repo="r",
                title="Test Issue",
                body="Test body",
            )
